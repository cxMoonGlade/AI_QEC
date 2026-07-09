"""Stage-D batch ``artifacts`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.artifacts`` (7 CPU-pure public units: the on-disk
artifact writers/summaries ``artifact_paths`` / ``write_b8`` / ``write_b8_optional`` /
``write_json`` / ``clear_known_artifacts`` / ``file_sha256`` / ``record_summary``; the
frozen dataclass ``ArtifactPaths`` has NO methods and NO ``__post_init__`` so it
contributes no units; ``_jsonable`` is a PRIVATE helper -- not a scored unit, but it is
mutated by mutmut and is exercised end-to-end + pinned through ``write_json`` (all six of
its type arms). The module imports numpy + ``qec_twin.hardware.b8_io`` + stdlib json/
hashlib/pathlib -- NEITHER torch NOR quimb -- so every unit is CPU-pure and out_of_scope
is empty).

Full-coverage program (docs/twin_validation/wave2_6_unit_test_contract.md SS12.3/12.4;
work-list docs/twin_validation/l3_release_package_unit_inventory.md D27).
``frontend/artifacts.py`` owns the frontend's on-disk artifact layer: it builds the fixed
per-run path set (``artifact_paths`` -> ``ArtifactPaths``), packs unpacked bool records into
Stim-compatible ``.b8`` (``write_b8`` / ``write_b8_optional``), serializes a numpy-aware
JSON manifest (``write_json`` + ``_jsonable``), clears a prior run's known outputs
(``clear_known_artifacts``), content-hashes a file (``file_sha256``), and summarizes sampled
detector/observable records (``record_summary``).

L2 DISCIPLINE (100% coverage != discrimination). The load-bearing pins:
  * ``artifact_paths`` -- EVERY one of the 16 fields is pinned to the EXACT ``root/<name>``
    against an INDEPENDENT filename table (reconstructed literally, NOT from the module's own
    expressions); a str out_dir input still returns Path-typed fields (kills a removed
    ``Path(out_dir)`` coercion; a string-literal filename mutant shifts the pinned path).
  * ``write_b8`` / ``write_b8_optional`` -- the written FILE BYTES are pinned vs an
    INDEPENDENT ``np.packbits(..., bitorder='little')`` recompute of the b8 wire format (NOT
    via ``b8_io``); both raising guards (ndim!=2, zero-bit width) are tripped through the
    PUBLIC entry with the EXACT message; ``write_b8_optional``'s zero-width SKIP branch is
    tripped both when a stale file EXISTS (removed -> None) and when it is ABSENT (no raise ->
    None, killing a ``missing_ok=True``->False); a width-1 write kills a ``0``->``1`` boundary
    mutant on both guards.
  * ``write_json`` + ``_jsonable`` -- one payload pins the EXACT serialized text (indent=2 /
    sort_keys=True / trailing ``\\n`` all load-bearing) and a second payload drives all six
    ``_jsonable`` arms (ndarray/generic/Path/dict/list/tuple/passthrough) pinned via an
    INDEPENDENT native structure; a numpy scalar buried inside the tuple makes the tuple arm
    load-bearing (dropping it -> json.dumps chokes on the np scalar -> raise).
  * ``clear_known_artifacts`` -- writes all 15 file artifacts, clears, asserts each is GONE
    yet the ``out_dir`` DIRECTORY survives (an ``and``->``or`` / ``!=``->``==`` / ``"out_dir"``
    string mutant would ``unlink`` the directory -> IsADirectoryError); a second clear on the
    now-missing files is a no-op (kills ``missing_ok=True``->False).
  * ``file_sha256`` -- pinned == an INDEPENDENT ``hashlib.sha256(path.read_bytes())`` digest
    (64 lowercase hex), with the ``None`` arm (-> None) and the missing-file arm (-> None) each
    tripped through the public entry; a str path input still hashes (kills a removed ``Path``
    coercion).
  * ``record_summary`` -- the EXACT summary dict is pinned vs a from-scratch independent
    recompute over a fixture whose four counts (shots 5, detectors 3, observables 2) and two
    any-rates (0.6 vs 0.4) are ALL DISTINCT (so an axis/index/shape swap is caught), plus the
    all-empty arc (ndim!=2 -> 0, size==0 -> [] / 0.0) and a discriminating wrong-array.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import fields
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

from _support.faithfulness import assert_discriminates, assert_pins, assert_raises_exact

from error_coupling_simulator.frontend.artifacts import (
    ArtifactPaths,
    artifact_paths,
    clear_known_artifacts,
    file_sha256,
    record_summary,
    write_b8,
    write_b8_optional,
    write_json,
)


# --------------------------------------------------------------------------- #
# INDEPENDENT references (reconstructed from the SPEC, never the module's own  #
# expressions).                                                                #
# --------------------------------------------------------------------------- #
# The fixed artifact filename table -- typed out literally here, NOT read from the
# module. ``artifact_paths`` must produce exactly ``root / <name>`` for each.
_EXPECTED_FILENAMES = {
    "circuit_ideal": "circuit_ideal.stim",
    "circuit_noisy_pauli": "circuit_noisy_pauli.stim",
    "detector_error_model": "detector_error_model.dem",
    "detection_events": "detection_events.b8",
    "obs_flips_actual": "obs_flips_actual.b8",
    "obs_flips_predicted": "obs_flips_predicted.b8",
    "ideal_detection_events": "ideal_detection_events.b8",
    "ideal_obs_flips_actual": "ideal_obs_flips_actual.b8",
    "sample_summary_ideal": "sample_summary_ideal.json",
    "sample_summary_noisy": "sample_summary_noisy.json",
    "theory_prediction": "theory_prediction.json",
    "decoder_results": "decoder_results.json",
    "source_timeline": "source_timeline.npz",
    "source_timeline_binding": "source_timeline_binding.json",
    "manifest": "manifest.json",
}


def _independent_b8_bytes(bits) -> bytes:
    """The b8 wire format from its documented SPEC (little-endian bit packing, each shot
    padded to a byte boundary) -- an INDEPENDENT recompute, NOT a call into b8_io."""
    arr = np.asarray(bits)
    return np.packbits(arr.astype(np.uint8), axis=1, bitorder="little").tobytes()


def _independent_sha256(path) -> str:
    """Digest the WHOLE file in one shot (independent of the module's chunked loop)."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# =========================================================================== #
# artifact_paths -- every field pinned to root/<name> (INDEPENDENT table)      #
# =========================================================================== #
def test_L0_artifact_paths_all_fields_exact(tmp_path):
    root = tmp_path
    # str INPUT (not Path): every returned field must still be Path-typed -> kills a removed
    # Path(out_dir) coercion (a str root would give str fields / raise on `root / name`).
    paths = artifact_paths(str(root))
    assert isinstance(paths, ArtifactPaths)
    assert paths.out_dir == root and isinstance(paths.out_dir, Path)

    for field_name, filename in _EXPECTED_FILENAMES.items():
        got = getattr(paths, field_name)
        assert isinstance(got, Path), f"{field_name} is not a Path"
        assert got == root / filename, f"{field_name}: {got} != {root / filename}"
        assert got.parent == root
        assert got.name == filename

    # the field set is exactly out_dir + the 15 known filenames (no missing/extra artifact).
    all_names = {f.name for f in fields(paths)}
    assert all_names == {"out_dir", *_EXPECTED_FILENAMES}

    # a Path INPUT gives identical results (both coercion routes exercised).
    assert artifact_paths(root) == paths

    def prop(p):
        assert p.manifest == root / "manifest.json"

    # a wrong-filename variant must fail the pin -> the manifest literal has teeth.
    wrong = artifact_paths(root)
    object.__setattr__(wrong, "manifest", root / "WRONG.json")
    assert_discriminates(prop, paths, wrong, label="artifact_paths.manifest")


# =========================================================================== #
# write_b8 -- packed bytes pinned vs independent packbits + both raising guards #
# =========================================================================== #
def test_L0_write_b8_writes_independent_packed_bytes(tmp_path):
    bits = np.array([[1, 0, 1, 1, 0],
                     [0, 1, 1, 0, 1],
                     [1, 1, 0, 0, 0]], dtype=bool)   # shots=3, bits=5
    dest = tmp_path / "det.b8"
    # str path INPUT -> still returns a Path (kills a removed Path(path) coercion).
    ret = write_b8(str(dest), bits)
    assert ret == dest and isinstance(ret, Path)
    assert dest.exists()
    # the file bytes are EXACTLY the independent little-endian packbits of the records.
    assert dest.read_bytes() == _independent_b8_bytes(bits)

    def prop(raw):
        assert raw == _independent_b8_bytes(bits)

    # a different record set produces different bytes -> the write is load-bearing.
    other = np.array([[0, 0, 0, 0, 0]] * 3, dtype=bool)
    assert_discriminates(prop, dest.read_bytes(), _independent_b8_bytes(other),
                         label="write_b8 packed bytes")


def test_L0_write_b8_width_one_write(tmp_path):
    # a WIDTH-1 record: shape[1]==1, so `shape[1] <= 0` is False (writes) but a `0`->`1`
    # mutant (`<= 1`) would raise -> this happy width-1 write kills that boundary mutant.
    bits = np.array([[1], [0], [1], [1]], dtype=bool)   # shots=4, bits=1
    dest = tmp_path / "w1.b8"
    ret = write_b8(dest, bits)
    assert ret == dest and dest.exists()
    assert dest.read_bytes() == _independent_b8_bytes(bits)


def test_L0_write_b8_wrong_ndim_raises_exact(tmp_path):
    # a 1D array -> ndim!=2 guard fires with the EXACT (shape-carrying) message.
    assert_raises_exact(
        ValueError,
        "expected [shots, bits] array, got shape (3,)",
        lambda: write_b8(tmp_path / "x.b8", np.array([1, 0, 1])),
        label="write_b8 ndim guard")


def test_L0_write_b8_zero_bits_raises_exact(tmp_path):
    # a 2D array of width 0 -> the zero-bit guard fires with the EXACT message.
    assert_raises_exact(
        ValueError,
        "cannot write readable .b8 for zero-bit records",
        lambda: write_b8(tmp_path / "x.b8", np.zeros((4, 0), dtype=bool)),
        label="write_b8 zero-bit guard")


# =========================================================================== #
# write_b8_optional -- write branch, skip branch (exists + absent), guards      #
# =========================================================================== #
def test_L0_write_b8_optional_write_branch(tmp_path):
    # positive width -> delegates to write_b8: file written, returns a Path (width 3).
    bits = np.array([[1, 0, 1], [0, 1, 1]], dtype=bool)
    dest = tmp_path / "opt.b8"
    ret = write_b8_optional(dest, bits)
    assert ret == dest and isinstance(ret, Path)
    assert dest.exists()
    assert dest.read_bytes() == _independent_b8_bytes(bits)

    # a WIDTH-1 write returns a Path too (shape[1]==1: `== 0` False -> writes) -> kills a
    # `0`->`1` mutant (which would take the skip branch and return None here).
    w1 = np.array([[1], [0]], dtype=bool)
    dest1 = tmp_path / "opt1.b8"
    ret1 = write_b8_optional(dest1, w1)
    assert ret1 == dest1 and isinstance(ret1, Path) and dest1.exists()
    assert dest1.read_bytes() == _independent_b8_bytes(w1)


def test_L0_write_b8_optional_zero_width_removes_stale_returns_none(tmp_path):
    # a stale file exists; a zero-width record -> it is REMOVED and None is returned.
    dest = tmp_path / "stale.b8"
    dest.write_bytes(b"stale-content")
    assert dest.exists()
    ret = write_b8_optional(dest, np.zeros((5, 0), dtype=bool))
    assert ret is None
    assert not dest.exists()   # the skip branch unlinked the stale file


def test_L0_write_b8_optional_zero_width_missing_file_is_noop(tmp_path):
    # zero-width record on a NON-existent path -> unlink(missing_ok=True) is a no-op, returns
    # None WITHOUT raising (kills a `missing_ok=True`->False mutant, which would raise here).
    dest = tmp_path / "never_written.b8"
    assert not dest.exists()
    ret = write_b8_optional(dest, np.zeros((2, 0), dtype=bool))
    assert ret is None
    assert not dest.exists()


def test_L0_write_b8_optional_wrong_ndim_raises_exact(tmp_path):
    assert_raises_exact(
        ValueError,
        "expected [shots, bits] array, got shape (2, 2, 2)",
        lambda: write_b8_optional(tmp_path / "x.b8", np.zeros((2, 2, 2), dtype=bool)),
        label="write_b8_optional ndim guard")


# =========================================================================== #
# write_json + _jsonable -- exact text pin (indent/sort/newline) + all arms     #
# =========================================================================== #
def test_L0_write_json_exact_serialized_text(tmp_path):
    # insertion order b,a (!= sorted a,b) so sort_keys=True is load-bearing; numpy scalars
    # exercise the generic arm; the list exercises the list arm + a nested generic.
    payload = {"b": np.int64(2), "a": [np.int64(1), 2.5]}
    dest = tmp_path / "m.json"
    ret = write_json(str(dest), payload)          # str INPUT -> Path return
    assert ret == dest and isinstance(ret, Path)
    # EXACT text: indent=2, keys SORTED (a before b), trailing newline. A mutated
    # indent/sort_keys/`+ "\n"` all change this string.
    expected = (
        "{\n"
        '  "a": [\n'
        "    1,\n"
        "    2.5\n"
        "  ],\n"
        '  "b": 2\n'
        "}\n"
    )
    assert dest.read_text() == expected

    def prop(text):
        assert text == expected

    # sort_keys OFF would emit b before a (insertion order) -> a discriminating variant.
    unsorted = json.dumps({"b": 2, "a": [1, 2.5]}, indent=2, sort_keys=False) + "\n"
    assert unsorted != expected  # sanity: the variant really differs
    assert_discriminates(prop, dest.read_text(), unsorted, label="write_json exact text")


def test_L0_write_json_jsonable_all_arms(tmp_path):
    # drive EVERY _jsonable arm: ndarray / np.generic / Path / dict-recurse / list / tuple /
    # passthrough. The np.int64 buried in the TUPLE makes the tuple arm load-bearing: if the
    # tuple were NOT recursed (fell through to `return value`) json.dumps would choke on the
    # raw np.int64 -> raise. Pin the parsed structure vs an INDEPENDENT native recompute.
    payload = {
        "arr": np.array([[1, 0], [0, 1]]),       # ndarray -> tolist
        "gen": np.float64(1.5),                  # np.generic -> item()
        "p": Path("/tmp/some/where"),            # Path -> str
        "nested": {"inner": np.int64(9)},        # dict -> recurse (generic inside)
        "lst": [np.int64(7), "s"],               # list -> recurse (generic inside)
        "tup": ("t", np.int64(3)),               # tuple -> list, generic inside (LOAD-BEARING)
        "plain": "hello",                        # passthrough
    }
    dest = write_json(tmp_path / "all.json", payload)
    loaded = json.loads(dest.read_text())
    expected = {
        "arr": [[1, 0], [0, 1]],
        "gen": 1.5,
        "p": str(Path("/tmp/some/where")),
        "nested": {"inner": 9},
        "lst": [7, "s"],
        "tup": ["t", 3],
        "plain": "hello",
    }
    assert loaded == expected

    def prop(obj):
        assert obj == expected

    # a single wrong leaf (ndarray transposed) must fail the pin.
    wrong = dict(expected, arr=[[1, 0], [1, 0]])
    assert_discriminates(prop, loaded, wrong, label="write_json _jsonable arms")


# =========================================================================== #
# clear_known_artifacts -- remove all files, keep out_dir, idempotent           #
# =========================================================================== #
def test_L0_clear_known_artifacts_removes_files_keeps_out_dir(tmp_path):
    paths = artifact_paths(tmp_path)
    file_fields = [f.name for f in fields(paths) if f.name != "out_dir"]
    assert len(file_fields) == 15

    # write content to every known artifact file.
    for name in file_fields:
        getattr(paths, name).write_bytes(b"payload")
    for name in file_fields:
        assert getattr(paths, name).exists()

    clear_known_artifacts(paths)

    # every artifact file is GONE ...
    for name in file_fields:
        assert not getattr(paths, name).exists(), f"{name} was not cleared"
    # ... but the out_dir DIRECTORY survives (an and->or / !=->== / "out_dir" string mutant
    # would unlink() the directory -> IsADirectoryError; a mutant that never unlinks leaves
    # the files -> the assertions above fire).
    assert paths.out_dir.exists() and paths.out_dir.is_dir()

    # a SECOND clear on the now-missing files is a no-op (kills missing_ok=True->False).
    clear_known_artifacts(paths)
    assert paths.out_dir.is_dir()


# =========================================================================== #
# file_sha256 -- independent digest + None arm + missing-file arm               #
# =========================================================================== #
def test_L0_file_sha256_matches_independent_digest(tmp_path):
    dest = tmp_path / "blob.bin"
    dest.write_bytes(b"the quick brown fox" * 100)
    # str path INPUT -> still hashes (kills a removed Path(path) coercion).
    got = file_sha256(str(dest))
    ref = _independent_sha256(dest)
    assert got == ref
    assert len(got) == 64 and all(c in "0123456789abcdef" for c in got)
    # Path input identical.
    assert file_sha256(dest) == ref

    def prop(h):
        assert h == ref

    # a DIFFERENT file has a different digest -> the hash is load-bearing.
    other = tmp_path / "other.bin"
    other.write_bytes(b"the quick brown fox" * 100 + b"!")
    assert_discriminates(prop, got, _independent_sha256(other), label="file_sha256 digest")


def test_L0_file_sha256_content_equal_to_read_sentinel(tmp_path):
    # a file whose ENTIRE content equals the mutmut XX-wrapped sentinel bytes b"XXXX": the
    # real loop reads b"XXXX" (!= the real sentinel b"") -> updates -> then reads b"" (== b"")
    # -> stops -> digest = sha256(b"XXXX"). A mutant that flips the iter sentinel b"" -> b"XXXX"
    # would MATCH on the first read and stop BEFORE updating -> digest = sha256(b"") -- so this
    # pins the sentinel is the empty-bytes EOF marker, not a content string.
    dest = tmp_path / "xxxx.bin"
    dest.write_bytes(b"XXXX")
    got = file_sha256(dest)
    assert got == hashlib.sha256(b"XXXX").hexdigest()
    assert got != hashlib.sha256(b"").hexdigest()   # the early-stop mutant would give this


def test_L0_file_sha256_none_and_missing_return_none(tmp_path):
    # the None arm (`path is None` -> None) ...
    assert file_sha256(None) is None
    # ... and the missing-file arm (`not p.exists()` -> None), tripped through the public
    # entry with a real absent path.
    assert file_sha256(tmp_path / "does_not_exist.bin") is None
    assert file_sha256(str(tmp_path / "also_missing")) is None


# =========================================================================== #
# record_summary -- exact dict vs independent recompute + empty arc + wrong-arr  #
# =========================================================================== #
def _summary_fixture():
    # shots=5, detectors=3, observables=2 -- ALL distinct so a shape/index swap is caught.
    det = np.array([[1, 0, 0],
                    [1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 0],
                    [0, 0, 0]], dtype=bool)     # col sums 2,1,0 -> marginals .4,.2,.0
    obs = np.array([[0, 1],
                    [0, 0],
                    [1, 1],
                    [0, 0],
                    [0, 0]], dtype=bool)         # col sums 1,2 -> marginals .2,.4
    return det, obs


def test_L0_record_summary_exact_dict(tmp_path):
    det, obs = _summary_fixture()
    got = record_summary(det, obs)
    # INDEPENDENT recompute (literal fractions of 5; any-rate = rows-with-a-True / shots).
    expected = {
        "num_shots": 5,
        "num_detectors": 3,
        "num_observables": 2,
        "detector_marginals": [0.4, 0.2, 0.0],     # cols 2/5, 1/5, 0/5
        "observable_marginals": [0.2, 0.4],        # cols 1/5, 2/5
        "any_detector_rate": 0.6,                  # rows {0,1,2} of 5
        "any_observable_rate": 0.4,                # rows {0,2} of 5
    }
    assert got == expected
    # value TYPES are pinned (int / list / float coercions).
    assert isinstance(got["num_shots"], int)
    assert isinstance(got["detector_marginals"], list)
    assert all(isinstance(x, float) for x in got["detector_marginals"])
    assert isinstance(got["any_detector_rate"], float)
    # the whole summary is JSON-safe.
    json.dumps(got)

    def prop(m):
        assert m == expected

    # a wrong-array (different detector column sums) must fail the pin.
    wrong_det = np.array([[1, 1, 1]] + [[0, 0, 0]] * 4, dtype=bool)  # marginals .2,.2,.2
    assert_discriminates(prop, got, record_summary(wrong_det, obs),
                         label="record_summary exact dict")


def test_L0_record_summary_coerces_records_to_bool():
    # non-0/1 INTEGER records: the `dtype=np.bool_` coercion clamps any nonzero -> True
    # BEFORE mean(). det col0 = [2,0,0] -> bool mean 1/3 (NOT the raw int mean 2/3); obs col0
    # = [3,0,0] -> bool mean 1/3 (NOT 3/3=1.0). A mutant that drops/nulls the dtype=np.bool_
    # (keeping the int dtype) yields the raw means -> killed by the marginals pin.
    det = np.array([[2, 0], [0, 0], [0, 0]], dtype=np.int64)
    obs = np.array([[3], [0], [0]], dtype=np.int64)
    got = record_summary(det, obs)
    assert got["detector_marginals"] == pytest.approx([1 / 3, 0.0])     # bool, not [2/3, 0.0]
    assert got["observable_marginals"] == pytest.approx([1 / 3])        # bool, not [1.0]
    # a raw-int (un-coerced) summary would differ -> discriminates the coercion.
    assert got["detector_marginals"] != pytest.approx([2 / 3, 0.0])
    assert got["observable_marginals"] != pytest.approx([1.0])


def test_L0_record_summary_empty_arc():
    # empty 1D inputs: ndim!=2 -> num_detectors/observables 0 (the `else 0` arc); size==0 ->
    # marginals [] and any-rate 0.0 (the `else []`/`else 0.0` arcs). No crash (size is falsy
    # BEFORE any(axis=1) is reached).
    got = record_summary(np.array([], dtype=bool), np.array([], dtype=bool))
    assert got == {
        "num_shots": 0,
        "num_detectors": 0,
        "num_observables": 0,
        "detector_marginals": [],
        "observable_marginals": [],
        "any_detector_rate": 0.0,
        "any_observable_rate": 0.0,
    }


# =========================================================================== #
# L1 PROPERTIES (Hypothesis)                                                    #
# =========================================================================== #
@settings(max_examples=60, deadline=None)
@given(name=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122),
                    min_size=1, max_size=8))
def test_L1_artifact_paths_layout(name):
    root = Path("/base") / name
    paths = artifact_paths(root)
    assert paths.out_dir == root
    for field_name, filename in _EXPECTED_FILENAMES.items():
        got = getattr(paths, field_name)
        assert got == root / filename
        assert got.parent == root and got.name == filename


_BITS2D = hnp.arrays(
    np.bool_, hnp.array_shapes(min_dims=2, max_dims=2, min_side=1, max_side=7))


@settings(max_examples=80, deadline=None)
@given(bits=_BITS2D)
def test_L1_write_b8_matches_independent_packbits(bits, tmp_path_factory):
    dest = tmp_path_factory.mktemp("b8") / "r.b8"
    ret = write_b8(dest, bits)
    assert ret == dest and dest.exists()
    assert dest.read_bytes() == _independent_b8_bytes(bits)


@settings(max_examples=60, deadline=None)
@given(content=st.binary(min_size=0, max_size=4096))
def test_L1_file_sha256_matches_hashlib(content, tmp_path_factory):
    dest = tmp_path_factory.mktemp("h") / "blob"
    dest.write_bytes(content)
    got = file_sha256(dest)
    assert got == hashlib.sha256(content).hexdigest()
    assert len(got) == 64
    # None and missing always map to None regardless of content.
    assert file_sha256(None) is None
    assert file_sha256(dest.parent / "nope") is None


@settings(max_examples=80, deadline=None)
@given(det=_BITS2D, obs=_BITS2D)
def test_L1_record_summary_matches_independent_recompute(det, obs):
    s = record_summary(det, obs)
    assert s["num_shots"] == det.shape[0]
    assert s["num_detectors"] == det.shape[1]
    assert s["num_observables"] == obs.shape[1]
    # INDEPENDENT recompute of the marginals + any-rates.
    assert_pins(s["detector_marginals"], det.mean(axis=0).tolist(),
                label="detector_marginals")
    assert_pins(s["observable_marginals"], obs.mean(axis=0).tolist(),
                label="observable_marginals")
    assert s["any_detector_rate"] == pytest.approx(float(det.any(axis=1).mean()))
    assert s["any_observable_rate"] == pytest.approx(float(obs.any(axis=1).mean()))
    json.dumps(s)  # always JSON-safe


@settings(max_examples=60, deadline=None)
@given(payload=st.dictionaries(
    st.text(min_size=1, max_size=5),
    st.integers() | st.text(max_size=5) | st.booleans(),
    max_size=6))
def test_L1_write_json_roundtrips_native_payloads(payload, tmp_path_factory):
    dest = tmp_path_factory.mktemp("j") / "p.json"
    ret = write_json(dest, payload)
    assert ret == dest
    assert json.loads(dest.read_text()) == payload
    assert dest.read_text().endswith("\n")   # the trailing newline invariant
