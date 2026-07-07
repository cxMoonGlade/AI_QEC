"""Wave-2.6 ISOLATED per-unit tests for the A2 ``ShotSet`` record accessors (§4).

Binding contract: ``docs/twin_validation/wave2_6_unit_test_contract.md`` §4 (A2),
the K-catalog (§1), the DEVIOUS-TEST STANDARD (KILLER + margin discipline). These
are ADDITIVE to the KEPT integration gates in ``tests/test_shotset_records.py``
(which drive the REAL d3 dataset through ``sample()``): the units here reach the
exception surfaces (``_require_shots`` ValueError, ``_header_geometry`` KeyError) and
the branch legs (``prefix_bits==0``, byte-aligned vs mid-byte) that the equivalence
gates structurally cannot enter -- they only ever pass VALID, materialized ShotSets.

ALL CPU-ONLY (numpy pack/unpack -- no CUDA, no dataset). The reference ShotSet is
built by ``SvSampler.pack_shots`` (the INVERSE of the accessors -- K-5 anti-vacuity:
the round-trip reference shares no code with the accessor under test), and the
hand-transcriptions inline ``np.unpackbits``/``np.packbits`` straight off the header's
pinned layout text, sharing NO ``SvSampler.unpack_shots`` code.

Units covered (§4.1/4.2/4.3):
  * ``ShotSet.to_det_obs``            -> {"det": (N, R*n_stab) uint8, "obs": (N,)}
  * ``ShotSet.packed_bytes``          -> the contiguous packed buffer as bytes
  * ``ShotSet.syndrome_prefix_bytes`` -> per-shot leading n_rounds*n_stab syn bits

Exception rows (grounded in the measured coverage gap; source lines cited per test):
  * ``_require_shots`` None-guard ValueError (sv_sampler.py:436-441) -- reached
    through ALL THREE accessors.
  * ``_header_geometry`` KeyError naming the missing keys (sv_sampler.py:445-451) --
    reached through ``to_det_obs`` and ``syndrome_prefix_bytes``.
  * ``syndrome_prefix_bytes`` range raise ValueError (sv_sampler.py:508-510) at
    n_rounds in {R+1, -1}.

L1 (Hypothesis) properties (§12.1):
  * byte round-trip: ``pack_shots -> unpack_shots -> pack_shots`` identity over
    generated random syndrome+flip arrays.
  * ``to_det_obs`` vs the layout transcription: the accessor equals the inline
    header-layout ``unpackbits`` transcription for every generated packed buffer.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

from qec_twin.forward.scalable.sv_sampler import ShotSet, SvSampler

# Wave-1 canon: the anti-vacuous control SHAPE + the greppable precondition helper.
from _support.fixtures import assert_control_trips, require_precondition


# --------------------------------------------------------------------------- #
# Synthetic-ShotSet builder (CPU; the reference INVERSE of the accessors).     #
# ``pack_shots(syndromes (N, n_stab*R), flips (N,))`` is the single inverse of #
# unpack_shots; a header-shaped ShotSet carries exactly the fields the          #
# accessors read (``header["n_stab"]``/``header["R"]`` + ``shots``).            #
# --------------------------------------------------------------------------- #
def _make_shotset(syndromes: np.ndarray, flips: np.ndarray, n_stab: int, R: int,
                  *, header_extra: dict | None = None, with_shots: bool = True) -> ShotSet:
    """A synthetic ShotSet for ``(N, n_stab, R)`` -- packed via ``pack_shots``.

    ``with_shots=False`` builds the shots-None case (the ``_require_shots`` guard);
    ``header_extra`` REPLACES the default ``{"n_stab", "R"}`` header (used to drop
    keys for the ``_header_geometry`` KeyError legs).
    """
    N = int(syndromes.shape[0])
    packed = SvSampler.pack_shots(syndromes, flips) if with_shots else None
    header = {"n_stab": int(n_stab), "R": int(R)} if header_extra is None else dict(header_extra)
    return ShotSet(header=header, path=None, header_path=None, n_shots=N,
                   syndrome_bits_per_shot=int(n_stab) * int(R),
                   shots=packed if with_shots else None)


def _rng_syndrome(n_stab: int, R: int, N: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    syn = rng.integers(0, 2, size=(N, n_stab * R), dtype=np.uint8)
    flips = rng.integers(0, 2, size=(N,), dtype=np.uint8)
    return syn, flips


# =========================================================================== #
# §4.1  ShotSet.to_det_obs                                                     #
# =========================================================================== #
def test_to_det_obs_roundmajor_equals_hand_unpack():
    """§4.1 NORMAL: ``to_det_obs`` equals the INLINE header-layout unpack+reshape on a
    seeded ShotSet (round-major ``det[i, r*n_stab+s]`` pinned). Defends K-5 (the
    reference is ``pack_shots`` + an inline ``unpackbits`` transcription, sharing NO
    ``unpack_shots`` code with the accessor), K-8 (round-major, LSB-first convention).

    ASYMMETRIC geometry ``n_stab=3 != R=2`` so a stab-major transpose is detectable
    (K-2, the AM-3 transpose bug class): the (R, n_stab) per-shot matrix is
    non-square, so the transposed layout has a DIFFERENT shape.
    """
    n_stab, R, N = 3, 2, 5
    syn, flips = _rng_syndrome(n_stab, R, N, seed=101)
    ss = _make_shotset(syn, flips, n_stab, R)

    out = ss.to_det_obs()
    assert set(out.keys()) >= {"det", "obs"}, f"payload keys drifted: {sorted(out)}"
    det = np.asarray(out["det"])
    obs = np.asarray(out["obs"])
    assert det.dtype == np.uint8, f"det dtype {det.dtype} != uint8"
    assert det.shape == (N, R * n_stab), f"det shape {det.shape} != {(N, R * n_stab)}"
    assert obs.shape == (N,), f"obs shape {obs.shape} != {(N,)}"

    # round-major: det == the input syndromes (round outer, then stab), obs == flips.
    assert np.array_equal(det, syn), "to_det_obs det != round-major input syndromes (K-8)"
    assert np.array_equal(obs, flips), "to_det_obs obs != input flips"

    # KILLER (K-2): the stab-major TRANSPOSE of the (R, n_stab) per-shot matrix must
    # DIFFER (asymmetric geometry -> distinct pattern). Demonstrated to trip equality.
    det_transposed = syn.reshape(N, R, n_stab).transpose(0, 2, 1).reshape(N, R * n_stab)
    require_precondition(
        not np.array_equal(det_transposed, syn),
        "the drawn syndrome is transpose-symmetric (the K-2 layout killer would be "
        "vacuous)", remedy="re-seed the syndrome array")

    def _det_check(candidate, _tol):
        assert np.array_equal(np.asarray(candidate), det), "candidate det layout mismatch"
    assert_control_trips(_det_check, det_transposed, 0.0)


def test_to_det_obs_single_shot_boundary():
    """§4.1 BOUNDARY: single shot (N=1) round-trips; the trailing flip byte NEVER
    appears in ``det`` (it is ``obs``). Defends K-2 (the flip byte must not leak into
    the detector block)."""
    n_stab, R, N = 3, 2, 1
    syn, flips = _rng_syndrome(n_stab, R, N, seed=202)
    ss = _make_shotset(syn, flips, n_stab, R)
    out = ss.to_det_obs()
    det = np.asarray(out["det"])
    assert det.shape == (1, R * n_stab)
    assert np.array_equal(det, syn), "single-shot det != input syndromes"
    assert int(np.asarray(out["obs"])[0]) == int(flips[0]), "single-shot obs != flip"


def test_to_det_obs_R1_boundary():
    """§4.1 BOUNDARY: R=1 (one round) -- det is exactly one round of n_stab bits."""
    n_stab, R, N = 5, 1, 4
    syn, flips = _rng_syndrome(n_stab, R, N, seed=303)
    ss = _make_shotset(syn, flips, n_stab, R)
    det = np.asarray(ss.to_det_obs()["det"])
    assert det.shape == (N, n_stab), f"R=1 det shape {det.shape} != {(N, n_stab)}"
    assert np.array_equal(det, syn), "R=1 det != input syndromes"


def test_to_det_obs_shots_none_raises_valueerror():
    """§4.1 EXCEPTION: ``shots is None`` -> ``ValueError`` via ``_require_shots``
    (sv_sampler.py:436-441). Defends K-1 (the None-guard must FIRE, never a silent
    None). The error message NAMES the method (provenance)."""
    ss = _make_shotset(np.zeros((1, 6), np.uint8), np.zeros((1,), np.uint8),
                       3, 2, with_shots=False)
    with pytest.raises(ValueError, match="to_det_obs"):
        ss.to_det_obs()


def test_to_det_obs_header_missing_nstab_raises_keyerror():
    """§4.1 EXCEPTION: header lacks ``n_stab`` -> ``KeyError`` via ``_header_geometry``
    (sv_sampler.py:445-451), NAMING the missing key. Defends K-1 (the guard fires,
    never a silent geometry guess)."""
    syn, flips = _rng_syndrome(3, 2, 2, seed=404)
    ss = _make_shotset(syn, flips, 3, 2, header_extra={"R": 2})  # n_stab dropped
    with pytest.raises(KeyError, match="n_stab"):
        ss.to_det_obs()


def test_to_det_obs_header_missing_both_raises_keyerror():
    """§4.1 EXCEPTION: header lacks BOTH ``n_stab`` and ``R`` -> ``KeyError`` naming
    both (sv_sampler.py:445-451)."""
    syn, flips = _rng_syndrome(3, 2, 2, seed=505)
    ss = _make_shotset(syn, flips, 3, 2, header_extra={"format": "x"})
    with pytest.raises(KeyError, match="n_stab"):
        ss.to_det_obs()


# =========================================================================== #
# §4.2  ShotSet.packed_bytes                                                   #
# =========================================================================== #
def test_packed_bytes_equals_contiguous_buffer():
    """§4.2 NORMAL: ``packed_bytes`` == ``np.ascontiguousarray(ss.shots).tobytes()``.
    Defends K-1 (a byte surface that dropped bytes / re-ordered would differ)."""
    syn, flips = _rng_syndrome(3, 3, 4, seed=606)
    ss = _make_shotset(syn, flips, 3, 3)
    assert ss.packed_bytes() == np.ascontiguousarray(ss.shots).tobytes(), \
        "packed_bytes != contiguous ss.shots buffer"


def test_packed_bytes_noncontiguous_view():
    """§4.2 BOUNDARY: packed_bytes() returns the correct LOGICAL bytes even for a
    NON-contiguous ``shots`` view. NO K-9 KILLER exists via a bytes comparison (first
    gate run 2026-07-07): numpy ``ndarray.tobytes()`` returns C-order logical bytes
    REGARDLESS of memory layout, so a strided view's raw ``.tobytes()`` already equals
    the contiguous bytes — the ``ascontiguousarray`` inside packed_bytes is a semantic
    no-op w.r.t. ``.tobytes()`` (defensive, harmless), and the original 'raw != contig'
    precondition correctly fired as vacuous. The forward assertion still confirms a
    strided view yields the correct bytes; the layout-independence is asserted directly
    as the documented no-killer fact."""
    syn, flips = _rng_syndrome(3, 3, 6, seed=707)
    ss_full = _make_shotset(syn, flips, 3, 3)
    contiguous = ss_full.shots
    # a strided view: every other shot (rows), non-contiguous in memory.
    strided = contiguous[::2]
    require_precondition(
        not strided.flags["C_CONTIGUOUS"],
        "the strided view is unexpectedly contiguous",
        remedy="use a stride that breaks C-contiguity")
    ss_view = ShotSet(header={"n_stab": 3, "R": 3}, path=None, header_path=None,
                      n_shots=int(strided.shape[0]),
                      syndrome_bits_per_shot=9, shots=strided)
    expected = np.ascontiguousarray(strided).tobytes()
    assert ss_view.packed_bytes() == expected, \
        "packed_bytes did not return the correct logical bytes for a strided view"
    # documented no-killer fact: .tobytes() is layout-independent, so raw == contiguous.
    assert strided.tobytes() == expected


def test_packed_bytes_shots_none_raises_valueerror():
    """§4.2 EXCEPTION: ``shots is None`` -> ``ValueError`` via
    ``_require_shots("packed_bytes")`` (sv_sampler.py:436-441). Defends K-1."""
    ss = _make_shotset(np.zeros((1, 6), np.uint8), np.zeros((1,), np.uint8),
                       3, 2, with_shots=False)
    with pytest.raises(ValueError, match="packed_bytes"):
        ss.packed_bytes()


# =========================================================================== #
# §4.3  ShotSet.syndrome_prefix_bytes                                          #
# =========================================================================== #
def _hand_prefix(packed: np.ndarray, n_stab: int, R: int, n_rounds: int) -> bytes:
    """INLINE unpack(LSB) + truncate-at-round-boundary + repack(LSB). Shares NO
    ``SvSampler.unpack_shots`` code (K-5 independence)."""
    syn_nbytes = (n_stab * R + 7) // 8
    bits = np.unpackbits(packed[:, :syn_nbytes], axis=1,
                         bitorder="little")[:, : n_rounds * n_stab]
    return np.packbits(bits, axis=1, bitorder="little").tobytes()


def test_syndrome_prefix_bytes_zero_returns_empty():
    """§4.3 BOUNDARY: ``n_rounds=0`` -> ``b""`` (the ``prefix_bits==0`` early return,
    sv_sampler.py:512-513)."""
    syn, flips = _rng_syndrome(3, 3, 4, seed=808)
    ss = _make_shotset(syn, flips, 3, 3)
    assert ss.syndrome_prefix_bytes(0) == b"", "n_rounds=0 must return b''"


def test_syndrome_prefix_bytes_byte_aligned_branch():
    """§4.3 BYTE-ALIGNED branch (sv_sampler.py:514-517): ``n_stab=8, n_rounds=1``
    (8 bits = 1 byte) hits the raw per-shot byte slice. Assert it EQUALS the
    unpack+repack hand transcription (the two branches must AGREE where both valid,
    K-5). Defends K-2 (byte-slice arithmetic)."""
    n_stab, R, N = 8, 3, 4
    syn, flips = _rng_syndrome(n_stab, R, N, seed=909)
    ss = _make_shotset(syn, flips, n_stab, R)
    require_precondition(
        (1 * n_stab) % 8 == 0,
        "n_rounds=1 boundary is NOT byte-aligned (the byte-slice branch is not "
        "exercised)", remedy="use n_stab a multiple of 8")
    got = ss.syndrome_prefix_bytes(1)
    hand = _hand_prefix(ss.shots, n_stab, R, 1)
    assert got == hand, "byte-aligned prefix != unpack+repack transcription (branches disagree)"
    # length == N * (n_stab/8) bytes, and STRICTLY less than the full packed buffer.
    assert len(got) == N * (n_stab // 8), f"byte-aligned prefix length {len(got)} wrong"
    assert len(got) < len(ss.packed_bytes()), "prefix must exclude the trailing flip byte"


def test_syndrome_prefix_bytes_byte_aligned_nstab4_r2():
    """§4.3 BYTE-ALIGNED via ``n_stab=4, n_rounds=2`` (8 bits): the alternate
    byte-aligned trigger named in the contract. Equals the hand transcription."""
    n_stab, R, N = 4, 3, 5
    syn, flips = _rng_syndrome(n_stab, R, N, seed=1010)
    ss = _make_shotset(syn, flips, n_stab, R)
    require_precondition((2 * n_stab) % 8 == 0, "not byte-aligned", remedy="use n_stab=4")
    assert ss.syndrome_prefix_bytes(2) == _hand_prefix(ss.shots, n_stab, R, 2), \
        "byte-aligned (n_stab=4,n_rounds=2) prefix != transcription"


def test_syndrome_prefix_bytes_midbyte_no_leak():
    """§4.3 MID-BYTE branch (sv_sampler.py:518-520): a SYNTHETIC ``n_stab=3`` geometry
    (the shipped d3 ``n_stab=8`` is ALWAYS byte-aligned) makes ``n_rounds*n_stab`` land
    mid-byte, forcing the unpack+truncate+repack branch. Defends K-2 (a raw byte slice
    LEAKS round-``n_rounds``'s bits sharing the boundary byte) and K-8 (LSB-first).

    KILLER (K-2): the devious raw-byte-slice implementation is DEMONSTRATED to fail --
    the crafted bits set positions inside the pad region of the boundary byte, so the
    raw slice carries leaked bits a zero-padded 3-bit repack does not.
    """
    n_stab, R, N = 3, 3, 4
    # crafted so bit positions 3..7 of the first packed byte (rounds 1-2) are nonzero:
    # a raw byte slice CANNOT match a zero-padded 3-bit (round-0) repack.
    syndromes = np.array([
        [1, 0, 1, 1, 1, 0, 0, 1, 1],
        [0, 1, 0, 0, 0, 1, 1, 0, 0],
        [1, 1, 1, 0, 0, 0, 1, 1, 0],
        [0, 0, 0, 1, 0, 1, 0, 1, 1],
    ], dtype=np.uint8)
    flips = np.array([1, 0, 1, 0], dtype=np.uint8)
    ss = _make_shotset(syndromes, flips, n_stab, R)

    for n_rounds in (1, 2, 3):
        require_precondition(
            (n_rounds * n_stab) % 8 != 0 or n_rounds == 3,
            f"n_rounds={n_rounds} unexpectedly byte-aligned", remedy="re-pick n_stab")
        assert ss.syndrome_prefix_bytes(n_rounds) == _hand_prefix(ss.shots, n_stab, R, n_rounds), \
            f"prefix({n_rounds}) != unpack/truncate/repack transcription (mid-byte, K-2)"

    # KILLER: raw byte-slice at n_rounds=1 (3 bits, mid-byte) must FAIL.
    raw_slice = np.ascontiguousarray(ss.shots[:, : (1 * n_stab + 7) // 8]).tobytes()
    require_precondition(
        raw_slice != _hand_prefix(ss.shots, n_stab, R, 1),
        "the crafted bits do not discriminate the raw byte slice (no round-1/2 bits "
        "share the boundary byte)", remedy="set a bit in positions 3..7 of some shot")

    def _midbyte_check(candidate, _tol):
        assert bytes(candidate) == ss.syndrome_prefix_bytes(1), "candidate mid-byte mismatch"
    assert_control_trips(_midbyte_check, raw_slice, 0.0)


def test_syndrome_prefix_bytes_full_R_excludes_flip():
    """§4.3 BOUNDARY: ``n_rounds=R`` -> ALL syndrome bits, but NEVER the trailing flip
    byte. Defends K-2 (the flip byte is outside the syndrome block)."""
    n_stab, R, N = 3, 3, 4
    syn, flips = _rng_syndrome(n_stab, R, N, seed=1111)
    ss = _make_shotset(syn, flips, n_stab, R)
    got = ss.syndrome_prefix_bytes(R)
    assert got == _hand_prefix(ss.shots, n_stab, R, R), "prefix(R) != full syndrome block"
    assert len(got) < len(ss.packed_bytes()), "prefix(R) must exclude the flip byte"


def test_syndrome_prefix_bytes_above_R_raises():
    """§4.3 EXCEPTION: ``n_rounds = R+1`` -> ``ValueError`` (sv_sampler.py:508-510,
    upper edge). Defends K-3 (the range guard fires at the boundary)."""
    n_stab, R, N = 3, 2, 3
    syn, flips = _rng_syndrome(n_stab, R, N, seed=1212)
    ss = _make_shotset(syn, flips, n_stab, R)
    with pytest.raises(ValueError, match="n_rounds"):
        ss.syndrome_prefix_bytes(R + 1)


def test_syndrome_prefix_bytes_negative_raises():
    """§4.3 EXCEPTION: ``n_rounds = -1`` -> ``ValueError`` (sv_sampler.py:508-510,
    lower edge). Defends K-3."""
    n_stab, R, N = 3, 2, 3
    syn, flips = _rng_syndrome(n_stab, R, N, seed=1313)
    ss = _make_shotset(syn, flips, n_stab, R)
    with pytest.raises(ValueError, match="n_rounds"):
        ss.syndrome_prefix_bytes(-1)


def test_syndrome_prefix_bytes_shots_none_raises_valueerror():
    """§4.3 EXCEPTION: ``shots is None`` -> ``ValueError`` via ``_require_shots``
    (sv_sampler.py:436-441). Defends K-1."""
    ss = _make_shotset(np.zeros((1, 6), np.uint8), np.zeros((1,), np.uint8),
                       3, 2, with_shots=False)
    with pytest.raises(ValueError, match="syndrome_prefix_bytes"):
        ss.syndrome_prefix_bytes(1)


def test_syndrome_prefix_bytes_header_missing_raises_keyerror():
    """§4.3 EXCEPTION: header lacks ``n_stab``/``R`` -> ``KeyError`` via
    ``_header_geometry`` (sv_sampler.py:445-451). NOTE the guard fires BEFORE the
    range check, so a header miss surfaces as KeyError even at an out-of-range
    ``n_rounds``."""
    syn, flips = _rng_syndrome(3, 2, 2, seed=1414)
    ss = _make_shotset(syn, flips, 3, 2, header_extra={"n_stab": 3})  # R dropped
    with pytest.raises(KeyError, match="R"):
        ss.syndrome_prefix_bytes(1)


# =========================================================================== #
# L1 (Hypothesis) property tests (§12.1)                                       #
# =========================================================================== #
# geometry: small n_stab/R so packed buffers stay tiny; N>=1 (RunSpec requires N>=1).
_NSTAB = st.integers(min_value=1, max_value=6)
_R = st.integers(min_value=1, max_value=5)
_N = st.integers(min_value=1, max_value=8)


@settings(max_examples=200, deadline=None)
@given(data=st.data())
def test_prop_pack_unpack_pack_identity(data):
    """L1 PROPERTY (byte round-trip): ``pack_shots -> unpack_shots -> pack_shots`` is
    the identity on the packed bytes, for EVERY generated (N, n_stab, R) syndrome+flip
    array. This is the byte-round-trip invariant the faithfulness protocol names;
    Hypothesis generates + shrinks (the cure for the hand-picked-'random'-that-was-
    secretly-the-identity failure mode)."""
    n_stab = data.draw(_NSTAB)
    R = data.draw(_R)
    N = data.draw(_N)
    syn = data.draw(hnp.arrays(np.uint8, (N, n_stab * R),
                               elements=st.integers(0, 1)))
    flips = data.draw(hnp.arrays(np.uint8, (N,), elements=st.integers(0, 1)))

    packed = SvSampler.pack_shots(syn, flips)
    syn2, flips2 = SvSampler.unpack_shots(packed, n_stab, R)
    repacked = SvSampler.pack_shots(syn2, flips2)
    # the decoded bits + flips must equal the originals (unpack is a true inverse)...
    assert np.array_equal(syn2, syn), "unpack(pack(syn)) != syn"
    assert np.array_equal(flips2, flips), "unpack(pack(flips)) != flips"
    # ...and the byte buffer is a fixed point of pack->unpack->pack.
    assert np.array_equal(repacked, packed), "pack(unpack(pack(x))) != pack(x) (byte round-trip)"


@settings(max_examples=200, deadline=None)
@given(data=st.data())
def test_prop_to_det_obs_matches_layout_transcription(data):
    """L1 PROPERTY (to_det_obs vs layout transcription): for EVERY generated ShotSet,
    ``to_det_obs`` equals the inline header-layout unpackbits transcription (round-
    major det, LSB-first) -- the accessor never drifts from the pinned convention.
    The transcription shares NO ``SvSampler.unpack_shots`` code (K-5 independence)."""
    n_stab = data.draw(_NSTAB)
    R = data.draw(_R)
    N = data.draw(_N)
    syn = data.draw(hnp.arrays(np.uint8, (N, n_stab * R),
                               elements=st.integers(0, 1)))
    flips = data.draw(hnp.arrays(np.uint8, (N,), elements=st.integers(0, 1)))
    ss = _make_shotset(syn, flips, n_stab, R)

    out = ss.to_det_obs()
    det = np.asarray(out["det"])
    obs = np.asarray(out["obs"])

    # inline transcription off the header layout (round-major, LSB-first) -- no unpack_shots.
    packed = ss.shots
    syn_nbytes = (n_stab * R + 7) // 8
    det_hand = np.unpackbits(packed[:, :syn_nbytes], axis=1,
                             bitorder="little")[:, : R * n_stab].astype(np.uint8)
    obs_hand = packed[:, syn_nbytes].astype(np.uint8)

    assert det.shape == (N, R * n_stab), f"det shape {det.shape} != {(N, R * n_stab)}"
    assert np.array_equal(det, det_hand), "to_det_obs det != layout transcription"
    assert np.array_equal(obs, obs_hand), "to_det_obs obs != trailing flip byte"
    # the transcription must also equal the ORIGINAL generated syndromes (K-5 anchor).
    assert np.array_equal(det, syn), "to_det_obs det != generated syndromes (round-major)"
