"""Partition and property tests for the current experiment-preset facade.

The module covers dataset resolution, frozen preset validation, numerical-provenance
binding, run-spec construction, and qutrit leakage-table construction.  Validation
and routing cases are CPU-only; carrier construction remains GPU-gated.
"""

from __future__ import annotations

import dataclasses
import json
from types import SimpleNamespace

import pytest
import torch

from error_coupling_simulator.carrier.within_cycle import (
    FusedWithinCycleSampler,
    SV_ARMS,
    SV_READOUT_CONVENTIONS,
    RunSpec,
)
from error_coupling_simulator.frontend import xzzx_parser as xp

# Shared device/data markers and adversarial-test helpers.
from conftest import DEVICE, requires_cuda, requires_data
from _support.fixtures import assert_control_trips, require_precondition

# hypothesis for the L1 property layer (§12.1); confirmed installed in the aiqec env.
from hypothesis import given, settings
from hypothesis import strategies as st

# the A1 facade + its module-internal load-bearing symbol.
from error_coupling_simulator.frontend import experiments
from error_coupling_simulator.frontend.experiments import (
    ExperimentPreset,
    LEAKED_READOUT_BIAS_SWEEP,
    PRESET_LEAK_THETA_0P30,
    PRESET_LEAK_WG_L1_5E3,
    _dataset_files,
    leak_slice_table,
    load_xzzx_d3,
    resolve_theta,
    run_spec_from_preset,
)

#: ratified decision 7 -- the ONE dataset-root env var name.
_ENV = "ECS_D3_DATA_ROOT"

#: the p2 cell knobs (the RAW registered preset's PINNED values; contract A1: presets
#: are frozen + named, NO silent physics defaults). These are the value-pin regression
#: constants for §3.4 (a silent edit to any of them is a K-8 knob-drift failure).
_THETA_RAW, _G_SEEP, _B_BIAS, _ARM = 0.30, 0.09, 0.9, "A"
_G_HEAT, _READOUT_CONV = 0.0, "biased_b"
_WG_L1_TARGET = 5.0e-3
#: a grossly-different discriminator cell (distinct seep so leak tables differ).
_THETA_HI, _G_SEEP_HI = 1.2, 0.5


@pytest.fixture(autouse=True)
def _no_d3_env_override(monkeypatch):
    """Env isolation. The facade honors ``ECS_D3_DATA_ROOT``; the default-root happy
    paths compared here read the parser DEFAULT paths (env-blind). A legitimately-set
    env var must never make a CORRECT facade fail a default-root comparison, so it is
    deleted per-test (monkeypatch restores on teardown). Raise-leg tests re-``setenv``
    explicitly AFTER this fixture runs."""
    monkeypatch.delenv(_ENV, raising=False)


def _mk_preset(**kw) -> ExperimentPreset:
    """Build an ``ExperimentPreset`` with the RAW-cell knobs as EXPLICIT (never
    silent) test-side fill-ins (the preset class itself has NO physics defaults).
    Callers override exactly the field(s) under test."""
    base = dict(name="unit_test_preset", theta_rad=None, wg_l1_target=None,
                g_seep=_G_SEEP, g_heat=_G_HEAT, b_bias=_B_BIAS, arm=_ARM,
                readout_conv=_READOUT_CONV)
    base.update(kw)
    return ExperimentPreset(**base)


# =========================================================================== #
# §3.1  _dataset_files(dataset_root) -- module-internal, load-bearing          #
# =========================================================================== #
# NORMAL ---------------------------------------------------------------------
@requires_data
def test_dataset_files_default_root_resolves_four(monkeypatch):
    """§3.1 NORMAL: arg=None + env-absent -> the four shipped default paths.
    Defends K-1 (the resolver actually returns the four logical files, not a subset).

    Reference: the parser's ``default_*_paths()`` directly (independent of the facade
    -- the facade REBASES these, so on the default root they must be identical)."""
    monkeypatch.delenv(_ENV, raising=False)
    files = _dataset_files(None)
    assert set(files) == {"r01_circ", "r01_meta", "r10_circ", "r10_meta"}, \
        f"_dataset_files did not resolve all four logical files: {sorted(files)}"
    r01_circ, r01_meta = xp.default_r01_paths()
    r10_circ, r10_meta = xp.default_r10_paths()
    assert files["r01_circ"] == r01_circ and files["r01_meta"] == r01_meta
    assert files["r10_circ"] == r10_circ and files["r10_meta"] == r10_meta
    for name, p in files.items():
        assert p.is_file(), f"{name} -> {p} is not a file"


@requires_data
def test_dataset_files_arg_root_rebases_layout(monkeypatch, tmp_path):
    """§3.1 NORMAL: arg=real root -> the same four files REBASED under that root.
    Defends K-1 (the ``dataset_root`` arg is live -- a dead arg would ignore it and
    resolve the default paths), K-8 (the rebase preserves the patch/basis layout via
    ``relative_to(DEFAULT_DATASET_ROOT)``, never a re-derived layout).

    Reference: a tmp root replicating the RELATIVE layout (derived from
    ``relative_to``, never hardcoded), all four files copied in."""
    import shutil
    monkeypatch.delenv(_ENV, raising=False)
    real = {}
    real["r01_circ"], real["r01_meta"] = xp.default_r01_paths()
    real["r10_circ"], real["r10_meta"] = xp.default_r10_paths()
    rel = {k: p.relative_to(xp.DEFAULT_DATASET_ROOT) for k, p in real.items()}
    root = tmp_path / "full_d3_root"
    for name, src in real.items():
        require_precondition(src.stat().st_size < (1 << 20),
                             f"shipped file {src} too large for a tmp copy",
                             remedy="symlink instead of copying")
        dst = root / rel[name]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    files = _dataset_files(root)
    for name in ("r01_circ", "r01_meta", "r10_circ", "r10_meta"):
        assert files[name] == root / rel[name], \
            f"{name} not rebased under the arg root: {files[name]} != {root / rel[name]}"
        assert files[name].is_file()


@requires_data
def test_dataset_files_env_root_resolves_when_arg_none(monkeypatch, tmp_path):
    """§3.1 NORMAL: env=real root, arg=None -> resolves UNDER the env root.
    Defends K-1 (the env var is live when the arg is absent).

    Reference: a tmp root replicating the RELATIVE layout with all four files."""
    import shutil
    real = {}
    real["r01_circ"], real["r01_meta"] = xp.default_r01_paths()
    real["r10_circ"], real["r10_meta"] = xp.default_r10_paths()
    rel = {k: p.relative_to(xp.DEFAULT_DATASET_ROOT) for k, p in real.items()}
    root = tmp_path / "env_d3_root"
    for name, src in real.items():
        dst = root / rel[name]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    monkeypatch.setenv(_ENV, str(root))
    files = _dataset_files(None)
    for name in ("r01_circ", "r01_meta", "r10_circ", "r10_meta"):
        assert files[name] == root / rel[name], \
            f"env root not honored for {name}: {files[name]}"


# BOUNDARY -------------------------------------------------------------------
@requires_data
def test_dataset_files_arg_beats_bogus_env(monkeypatch, tmp_path):
    """§3.1 BOUNDARY (precedence, K-3): a real ``dataset_root`` arg WINS over a bogus
    env (arg > env > default). Defends K-3 (resolution-order drift) + K-1 (dead arg).

    Leg: env = bogus nonexistent root, arg = the real shipped default root -> resolves
    fine (an env-preferring resolver would raise on the bogus env). The KILLER
    direction (arg=bogus with a GOOD env still raises) lives in
    ``test_dataset_files_nonexistent_root_raises`` via the arg branch."""
    bogus = tmp_path / "bogus_env_root"
    assert not bogus.exists()
    monkeypatch.setenv(_ENV, str(bogus))
    files = _dataset_files(xp.DEFAULT_DATASET_ROOT)  # arg wins
    r01_circ, _ = xp.default_r01_paths()
    assert files["r01_circ"] == r01_circ and files["r01_circ"].is_file(), \
        "arg root did not beat the bogus env (K-3 precedence)"


# EXCEPTION (a): env SET but empty/whitespace -> ValueError (LINE 110) --------
def test_dataset_files_empty_env_raises_value_error(monkeypatch):
    """§3.1 EXCEPTION (a) / LINE 110 (the measured miss): env SET but empty/whitespace
    -> ``ValueError`` naming the env var -- NEVER a silent fallback to the default.
    Defends K-1 (a broken shell expansion, ``ECS_D3_DATA_ROOT=""``, must NOT be
    indistinguishable from unset; a fall-through would make every override run vacuous).

    Direct call on the private symbol (contract §10 decision 2: the empty-env leg is
    tested through public callers AND one direct call for LINE 110 isolation). Both an
    empty string and a whitespace-only string exercise the ``strip()`` guard."""
    for bad in ("", "   ", "\t "):
        monkeypatch.setenv(_ENV, bad)
        with pytest.raises(ValueError) as ei:
            _dataset_files(None)
        assert _ENV in str(ei.value), \
            f"empty-env ValueError must NAME {_ENV} (got {str(ei.value)!r})"


@requires_data
def test_dataset_files_empty_env_raises_via_public_caller(monkeypatch):
    """§3.1 EXCEPTION (a) via the PUBLIC caller (contract §10 decision 2: the leg is
    reachable both ways). ``load_xzzx_d3()`` with an empty env must surface the same
    ``ValueError`` -- the facade does not swallow it. Defends K-1.

    requires_data only so the surrounding suite parity holds; the raise fires BEFORE
    any file read, so the dataset is not actually touched."""
    monkeypatch.setenv(_ENV, "")
    with pytest.raises(ValueError) as ei:
        load_xzzx_d3()
    assert _ENV in str(ei.value)


# EXCEPTION (b): override root not a directory -> FileNotFoundError (LINE 128)-
def test_dataset_files_nonexistent_root_raises(monkeypatch, tmp_path):
    """§3.1 EXCEPTION (b) / LINE 128: a nonexistent override ROOT (arg) ->
    ``FileNotFoundError`` NAMING the root, refusing to fall back. Defends K-1 (silent
    default fallback) + K-5 (the raise NAMES our resolved root, so it is provably about
    OUR root, not an unrelated failure).

    CPU-only: no dataset needed -- the root does not exist, so the ``is_dir()`` check
    fails before any file resolution."""
    bogus = tmp_path / "not_a_dir_root"
    assert not bogus.exists()
    with pytest.raises(FileNotFoundError) as ei:
        _dataset_files(bogus)
    msg = str(ei.value)
    assert str(bogus) in msg, \
        f"FileNotFoundError must NAME the nonexistent root {bogus} (got {msg!r})"
    # K-5: NEVER a silent fallback -- the default root must NOT be the resolved one.
    assert "Refusing to fall back" in msg or "silent fallback" in msg or str(bogus) in msg


# EXCEPTION (c): root is a dir but a required file missing -> FNF (LINE 138) --
@requires_data
def test_dataset_files_partial_root_missing_file_raises(monkeypatch, tmp_path):
    """§3.1 EXCEPTION (c) / LINE 138: an override root that IS a directory (passes the
    ``is_dir()`` check) but OMITS one required file -> ``FileNotFoundError`` LISTING the
    missing file UNDER the override root. Defends K-1 (the existence-check-only devious
    resolver: verifies the root is a dir, then silently reads the DEFAULT root's files),
    K-5 (the raise is pinned to the override root's missing path).

    Construction: a tmp root replicating the RELATIVE layout (derived from
    ``relative_to``, never hardcoded) with THREE of the four files (r10 metadata
    OMITTED). All four DO exist under the default root, so a fall-through impl would
    SUCCEED silently."""
    import shutil
    real = {}
    real["r01_circ"], real["r01_meta"] = xp.default_r01_paths()
    real["r10_circ"], real["r10_meta"] = xp.default_r10_paths()
    rel = {k: p.relative_to(xp.DEFAULT_DATASET_ROOT) for k, p in real.items()}
    root = tmp_path / "partial_d3_root"
    omitted = "r10_meta"
    for name, src in real.items():
        if name == omitted:
            continue
        dst = root / rel[name]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    assert root.is_dir()  # the devious existence-only check would PASS here
    with pytest.raises(FileNotFoundError) as ei:
        _dataset_files(root)
    msg = str(ei.value)
    assert str(root / rel[omitted]) in msg, \
        f"FileNotFoundError must LIST the missing {omitted} under the override root " \
        f"{root} (got {msg!r})"


# =========================================================================== #
# §3.2  load_xzzx_d3(dataset_root=None, *, with_interior_streams=True)         #
# =========================================================================== #
@requires_data
def test_load_xzzx_d3_default_attaches_streams():
    """§3.2 NORMAL: default parse ATTACHES the r10 interior streams. Defends K-1 (a
    facade returning geometry-only when streams were requested).

    Reference: the hand ritual -- parse r01 (verify) + attach r10 streams -- kept as
    the independent transcription. The stream count must equal ``n_data`` and be
    non-empty (K-5 precondition)."""
    sched = load_xzzx_d3()  # with_interior_streams=True default
    streams = list(sched.within_cycle_streams)
    require_precondition(len(streams) > 0,
                         "hand-parsed r10 interior streams are empty",
                         remedy="check the shipped r10 patch")
    assert len(streams) == int(sched.n_data), \
        f"streams attached count {len(streams)} != n_data {sched.n_data} (K-1)"


@requires_data
def test_load_xzzx_d3_no_interior_streams_branch():
    """§3.2 BOUNDARY / branch 166->169 (the measured uncovered leg):
    ``with_interior_streams=False`` returns geometry WITHOUT interior streams.
    Defends K-1 + the FALSE-branch KILLER (streams-attached vs streams-absent must be
    DISTINGUISHABLE -- a facade that ALWAYS attaches fails this leg).

    Discriminator: the True-branch sibling
    (``test_load_xzzx_d3_default_attaches_streams``) has non-empty streams; here the
    same geometry must have NONE."""
    sched = load_xzzx_d3(with_interior_streams=False)
    # geometry PRESERVED (d3 XZZX has 9 data qutrits; the verified parse still ran).
    assert int(sched.n_data) == 9, \
        f"geometry lost when streams suppressed: n_data={sched.n_data}"
    assert len(sched.stab_paulis()) > 0, \
        "geometry-only schedule lost its stabilizers"
    # but the interior streams must be ABSENT (branch 166->169, the FALSE leg).
    assert len(list(sched.within_cycle_streams)) == 0, \
        "with_interior_streams=False still attached streams (branch 166->169 not taken)"


def test_load_xzzx_d3_propagates_dataset_files_raise(monkeypatch):
    """§3.2 EXCEPTION: ``load_xzzx_d3`` propagates a ``_dataset_files`` raise UNCHANGED
    (it does not swallow it into a silent default). Defends K-1.

    CPU-only: an empty env raises before any file read."""
    monkeypatch.setenv(_ENV, "   ")
    with pytest.raises(ValueError) as ei:
        load_xzzx_d3()
    assert _ENV in str(ei.value), "load_xzzx_d3 must propagate the empty-env ValueError"


def test_load_xzzx_d3_dataset_root_arg_is_used(tmp_path):
    """§3.2 EXCEPTION (K-1 dead-parameter): the ``dataset_root`` ARGUMENT must actually
    reach ``_dataset_files`` -- a facade that drops it and always uses the default root
    (the L2 mutmut survivor ``x_load_xzzx_d3__mutmut_3``: ``_dataset_files(None)``) would
    NOT raise on a bogus argument-root. A nonexistent ``dataset_root`` must raise
    FileNotFoundError naming it, proving the argument is threaded through (the existing
    tests only pass the DEFAULT None, so the parameter path was never exercised -- a 100%
    structural-coverage blind spot mutation testing surfaced). CPU-only."""
    bogus = tmp_path / "no_such_dataset_root_xyz"
    with pytest.raises(FileNotFoundError) as ei:
        load_xzzx_d3(dataset_root=str(bogus))
    assert str(bogus) in str(ei.value), \
        "dataset_root argument was ignored (not threaded to _dataset_files)"


# =========================================================================== #
# §3.3  ExperimentPreset + __post_init__ -- the 7 field validations           #
# =========================================================================== #
# --- one VALID representative per convention (the passing anchors) -----------
def test_experiment_preset_valid_raw_angle_constructs():
    """§3.3 NORMAL: a raw-angle preset (theta_rad set, wg_l1_target None) constructs.
    The passing anchor that proves the validator is not a blanket-reject (K-1's
    complement)."""
    p = _mk_preset(theta_rad=_THETA_RAW)
    assert p.theta_rad == _THETA_RAW and p.wg_l1_target is None


def test_experiment_preset_valid_wg_rate_constructs():
    """§3.3 NORMAL: a model-rate-solved preset (wg_l1_target set, theta_rad None)
    constructs. The second passing anchor."""
    p = _mk_preset(wg_l1_target=_WG_L1_TARGET)
    assert p.wg_l1_target == _WG_L1_TARGET and p.theta_rad is None


# --- E1: empty name -> ValueError (LINE 200) --------------------------------
def test_experiment_preset_empty_name_raises():
    """§3.3 E1 / LINE 200 (K-1): ``name=""`` -> ``ValueError`` "non-empty". The
    validator must FIRE on an empty name (a no-op validator would accept it)."""
    with pytest.raises(ValueError, match="non-empty"):
        _mk_preset(name="", theta_rad=_THETA_RAW)


# --- E2 / E2': the exactly-ONE-convention branch (LINE 201-206) -------------
def test_experiment_preset_both_conventions_raises():
    """§3.3 E2 / LINE 201-206 (K-8): BOTH ``theta_rad`` AND ``wg_l1_target`` set ->
    ``ValueError`` "exactly ONE". The two theta conventions are DISTINCT presets, never
    merged into one default."""
    with pytest.raises(ValueError, match="exactly ONE"):
        _mk_preset(theta_rad=_THETA_RAW, wg_l1_target=_WG_L1_TARGET)


def test_experiment_preset_neither_convention_raises():
    """§3.3 E2' / same branch (K-1): NEITHER ``theta_rad`` NOR ``wg_l1_target`` set ->
    ``ValueError`` "exactly ONE". No silent physics default -- the mandatory-choice
    surface (the ``_mk_preset`` base leaves both None)."""
    with pytest.raises(ValueError, match="exactly ONE"):
        _mk_preset()


# --- E3: theta_rad < 0 -> ValueError (LINE 208) -----------------------------
def test_experiment_preset_negative_theta_rad_raises():
    """§3.3 E3 / LINE 208 (K-1): ``theta_rad = -0.1`` -> ``ValueError`` ">= 0". A
    negative exchange angle is unphysical; the validator must fire."""
    with pytest.raises(ValueError, match=">= 0"):
        _mk_preset(theta_rad=-0.1)


def test_experiment_preset_theta_rad_zero_passes():
    """§3.3 E3 BOUNDARY: ``theta_rad = 0.0`` is the CLOSED lower edge -> PASSES (the
    ``< 0.0`` check is strict). Pins the edge so a ``<=`` drift is caught."""
    p = _mk_preset(theta_rad=0.0)
    assert p.theta_rad == 0.0


# --- E4: wg_l1_target out of (0, 0.5) -> ValueError (LINE 211) ---------------
@pytest.mark.parametrize("bad", [0.0, 0.5, 0.6, -0.01])
def test_experiment_preset_wg_l1_target_out_of_open_interval_raises(bad):
    """§3.3 E4 / LINE 211 (K-4, open-interval edges): ``wg_l1_target`` uses STRICT
    ``0.0 < x < 0.5``. The edges ``0.0`` and ``0.5`` must BOTH raise (strict, not
    ``<=``), plus over (``0.6``) and under (``-0.01``). A ``<=``/``>=`` drift on either
    bound is caught by the edge values, NOT by a mid-interval value."""
    with pytest.raises(ValueError, match=r"\(0, 0\.5\)"):
        _mk_preset(wg_l1_target=bad)


@pytest.mark.parametrize("ok", [1e-9, 0.4999])
def test_experiment_preset_wg_l1_target_interior_passes(ok):
    """§3.3 E4 BOUNDARY (the interior side of the strict edges): ``1e-9`` and
    ``0.4999`` are strictly inside ``(0, 0.5)`` -> PASS. Together with the edge-raise
    test above this pins the open-interval convention (K-4)."""
    p = _mk_preset(wg_l1_target=ok)
    assert p.wg_l1_target == ok


# --- E5: g_seep / g_heat < 0 -> ValueError (LINE 214) -----------------------
def test_experiment_preset_negative_g_seep_raises():
    """§3.3 E5 / LINE 214 (K-1): ``g_seep = -1e-9`` -> ``ValueError`` ">= 0". Negative
    seep rate is unphysical."""
    with pytest.raises(ValueError, match=">= 0"):
        _mk_preset(theta_rad=_THETA_RAW, g_seep=-1e-9)


def test_experiment_preset_negative_g_heat_raises():
    """§3.3 E5 / LINE 214 (K-1), the OTHER conjunct: ``g_heat = -1e-9`` also fires the
    same raise. Both operands of the ``or`` must be live (a validator checking only
    g_seep would miss this)."""
    with pytest.raises(ValueError, match=">= 0"):
        _mk_preset(theta_rad=_THETA_RAW, g_heat=-1e-9)


def test_experiment_preset_zero_rates_pass():
    """§3.3 E5 BOUNDARY: ``g_seep = g_heat = 0.0`` is the CLOSED lower edge -> PASSES
    (``< 0.0`` strict). Pins the edge against a ``<=`` drift."""
    p = _mk_preset(theta_rad=_THETA_RAW, g_seep=0.0, g_heat=0.0)
    assert p.g_seep == 0.0 and p.g_heat == 0.0


# --- E6: b_bias out of [0, 1] -> ValueError (LINE 217) ----------------------
@pytest.mark.parametrize("bad", [-0.01, 1.01])
def test_experiment_preset_b_bias_out_of_closed_interval_raises(bad):
    """§3.3 E6 / LINE 217 (K-4, closed-interval edges): ``b_bias`` uses CLOSED
    ``0.0 <= x <= 1.0``. Just OUTSIDE either bound (``-0.01`` / ``1.01``) must raise;
    the closed edges themselves must PASS (next test). A strict-vs-closed drift is
    caught by these edges, not by a mid-interval value."""
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        _mk_preset(theta_rad=_THETA_RAW, b_bias=bad)


@pytest.mark.parametrize("ok", [0.0, 1.0])
def test_experiment_preset_b_bias_closed_edges_pass(ok):
    """§3.3 E6 BOUNDARY: ``b_bias = 0.0`` and ``= 1.0`` are the CLOSED edges -> PASS
    (``<=``, not ``<``). Pins the closed convention (K-4)."""
    p = _mk_preset(theta_rad=_THETA_RAW, b_bias=ok)
    assert p.b_bias == ok


# --- E7: arm not in SV_ARMS -> ValueError (LINE 220) ------------------------
def test_experiment_preset_bad_arm_raises():
    """§3.3 E7 / LINE 220 (K-8): ``arm = "Z"`` (not in ``SV_ARMS``) -> ``ValueError``
    "one of". Enum-membership validator must fire."""
    require_precondition("Z" not in SV_ARMS,
                         "'Z' unexpectedly a valid arm -- pick another invalid token",
                         remedy="update the invalid arm token")
    with pytest.raises(ValueError, match="one of"):
        _mk_preset(theta_rad=_THETA_RAW, arm="Z")


def test_experiment_preset_arm_lowercase_normalizes_and_passes():
    """§3.3 E7 KILLER (K-8 normalization pin): ``arm`` is validated via ``.upper()``,
    so lower-case ``"a"`` must PASS (normalized to ``"A"``). Pins the normalization --
    a validator dropping the ``.upper()`` would REJECT ``"a"`` and fail this leg."""
    require_precondition("A" in SV_ARMS and "a" not in SV_ARMS,
                         "SV_ARMS shape changed -- 'a' vs 'A' normalization pin stale",
                         remedy="re-derive the arm normalization case")
    p = _mk_preset(theta_rad=_THETA_RAW, arm="a")
    assert str(p.arm) == "a", "the preset stores the raw arm string; validation upper-cases"


# --- E8: readout_conv not in SV_READOUT_CONVENTIONS -> ValueError (LINE 223)-
def test_experiment_preset_bad_readout_conv_raises():
    """§3.3 E8 / LINE 223 (K-8): ``readout_conv = "raw"`` (not in
    ``SV_READOUT_CONVENTIONS``) -> ``ValueError`` "one of"."""
    require_precondition("raw" not in SV_READOUT_CONVENTIONS,
                         "'raw' unexpectedly a valid readout_conv",
                         remedy="update the invalid readout token")
    with pytest.raises(ValueError, match="one of"):
        _mk_preset(theta_rad=_THETA_RAW, readout_conv="raw")


def test_experiment_preset_readout_conv_is_case_sensitive():
    """§3.3 E8 KILLER (K-8 convention pin): ``readout_conv`` is NOT upper-cased (unlike
    ``arm``) -- membership is EXACT. Upper-case ``"BIASED_B"`` must RAISE, pinning the
    (deliberate) asymmetry with the ``arm`` normalization."""
    require_precondition("BIASED_B" not in SV_READOUT_CONVENTIONS,
                         "readout_conv membership unexpectedly case-insensitive",
                         remedy="re-check the SV_READOUT_CONVENTIONS convention")
    with pytest.raises(ValueError, match="one of"):
        _mk_preset(theta_rad=_THETA_RAW, readout_conv="BIASED_B")


# --- frozen-instance assignment (the §3.3 boundary at 305-306) --------------
def test_experiment_preset_is_frozen():
    """§3.3 BOUNDARY: the dataclass is frozen -- post-construction assignment raises
    ``FrozenInstanceError``. A preset is a REGISTRATION, never an ad-hoc mutation."""
    p = _mk_preset(theta_rad=_THETA_RAW)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        p.theta_rad = 0.99  # type: ignore[misc]


# =========================================================================== #
# §3.4  PRESET_LEAK_THETA_0P30 / PRESET_LEAK_WG_L1_5E3 -- registered-value pins#
# =========================================================================== #
def test_preset_leak_theta_0p30_value_pins():
    """§3.4 (K-8 knob-drift regression pin): ``PRESET_LEAK_THETA_0P30`` -- EXACT ``==``
    on EVERY field. A silent edit to any pinned value fails. This is a REGRESSION PIN,
    not a logic test."""
    p = PRESET_LEAK_THETA_0P30
    assert p.name == "leak_theta_0p30"
    assert p.theta_rad == 0.30
    assert p.wg_l1_target is None
    assert p.g_seep == 0.09
    assert p.g_heat == 0.0
    assert p.b_bias == 0.9
    assert p.arm == "A"
    assert p.readout_conv == "biased_b"


def test_preset_leak_wg_l1_5e3_value_pins():
    """§3.4 (K-8): ``PRESET_LEAK_WG_L1_5E3`` -- EXACT ``==`` on every field. Same other
    knobs as the RAW preset; the ONLY difference is the model-rate-solved convention
    (wg_l1_target set, theta_rad None)."""
    p = PRESET_LEAK_WG_L1_5E3
    assert p.name == "leak_wg_l1_5e3"
    assert p.wg_l1_target == 5.0e-3
    assert p.theta_rad is None
    assert p.g_seep == 0.09
    assert p.g_heat == 0.0
    assert p.b_bias == 0.9
    assert p.arm == "A"
    assert p.readout_conv == "biased_b"


def test_registered_preset_provenance_is_json_safe_and_field_complete():
    """Per-field provenance is machine-readable without promoting a physical cell."""
    expected_fields = {
        "name", "theta_rad", "wg_l1_target", "g_seep", "g_heat", "b_bias",
        "arm", "readout_conv",
    }
    for preset in (PRESET_LEAK_THETA_0P30, PRESET_LEAK_WG_L1_5E3):
        manifest = preset.provenance_manifest
        assert manifest is not None
        json.dumps(manifest, sort_keys=True)
        assert manifest["schema"] == \
            "error_coupling_simulator.frontend.experiment_preset_provenance.v1"
        whole = manifest["whole_preset"]
        assert whole["claim_scope"] == \
            "registered_synthetic_cross_source_benchmark_only"
        assert whole["device_calibrated"] is False
        assert whole["physical_cell_validated_by_literature"] is False
        assert whole["direct_whole_cell_literature_support_count"] == 0

        fields = manifest["fields"]
        assert set(fields) == expected_fields
        for field_name in expected_fields:
            assert fields[field_name]["value"] == getattr(preset, field_name)
            assert fields[field_name]["device_calibrated"] is False
            assert "claim_scope" in fields[field_name]
            assert "source_kind" in fields[field_name]
            assert isinstance(fields[field_name]["literature_references"], list)
            assert fields[field_name]["provenance_kind"] in {
                "paper-measured", "paper-derived", "dataset-measured",
                "calibrated-to-paper", "project-design", "convenience-default",
                "numerical-only",
            }

        dataset = manifest["dataset_source"]
        assert dataset["claim_scope"] == "geometry_and_schedule_only"
        assert dataset["supplies_physical_noise_parameters"] is False
        assert dataset["uses_measurements_b8"] is False
        assert dataset["uses_circuit_noisy_si1000"] is False


def test_registered_b_0p9_is_synthetic_point_and_sweep_is_exposed():
    """b=.9 has no magnitude support and cannot replace the registered bracket."""
    assert LEAKED_READOUT_BIAS_SWEEP == (0.5, 0.75, 1.0)
    for preset in (PRESET_LEAK_THETA_0P30, PRESET_LEAK_WG_L1_5E3):
        manifest = preset.provenance_manifest
        assert manifest is not None
        b_field = manifest["fields"]["b_bias"]
        assert b_field["value"] == 0.9
        assert b_field["source_kind"] == "registered_synthetic_nuisance_point"
        assert b_field["claim_scope"] == "synthetic_nuisance_sweep_point_only"
        assert b_field["magnitude_supported_by_literature"] is False
        assert b_field["literature_references"] == []
        assert b_field["required_sweep"] == [0.5, 0.75, 1.0]
        assert manifest["required_leaked_readout_bias_sweep"] == [0.5, 0.75, 1.0]


def test_wg_preset_sources_are_atomic_not_whole_cell_support():
    """Miao and McEwen anchor separate fields; neither validates the composition."""
    manifest = PRESET_LEAK_WG_L1_5E3.provenance_manifest
    assert manifest is not None
    fields = manifest["fields"]
    l1 = fields["wg_l1_target"]
    seep = fields["g_seep"]
    assert l1["source_kind"] == "single_paper_magnitude_anchor"
    assert l1["provenance_kind"] == "paper-measured"
    assert l1["claim_scope"] == "reported_device_protocol_scale_only"
    assert [ref["identifier"] for ref in l1["literature_references"]] == [
        "arXiv:2211.04728"]
    assert l1["literature_references"][0]["exact_locator"] == "Fig. 3c"
    assert l1["literature_references"][0]["doi"] == "10.1038/s41567-023-02226-w"
    assert l1["whole_project_channel_supported"] is False
    assert seep["source_kind"] == "cross_device_scale_anchor"
    assert seep["provenance_kind"] == "project-design"
    assert seep["claim_scope"] == \
        "project_channel_coordinate_near_reported_seepage_scale_only"
    assert [ref["identifier"] for ref in seep["literature_references"]] == [
        "arXiv:2102.06131"]
    assert seep["literature_references"][0]["exact_locator"] == "Supplementary Table S1"
    assert seep["literature_references"][0]["doi"] == "10.1038/s41467-021-21982-y"
    assert seep["direct_parameter_fit"] is False
    assert manifest["whole_preset"]["direct_whole_cell_literature_support_count"] == 0


# =========================================================================== #
# §3.5  resolve_theta(preset)                                                  #
# =========================================================================== #
def test_resolve_theta_raw_angle_passthrough():
    """§3.5 NORMAL (raw branch, K-8): a raw-angle preset returns the PINNED
    ``theta_rad`` with NO unit munging -- EXACT float identity."""
    p = _mk_preset(theta_rad=_THETA_RAW)
    assert resolve_theta(p) == _THETA_RAW


def test_resolve_theta_wg_rate_solves_model_coordinate():
    """§3.5 NORMAL (wg branch, K-1): a model-rate-solved preset returns
    ``solve_theta_for_wg_l1(wg_l1_target, g_seep=, g_heat=)`` at the preset's rates
    -- and it must DIFFER from the raw cell / zero (a dead passthrough is killed).

    Independent conformance: the resolved theta actually HITS the registered WG_L1 on
    the exact channel rate (checked via the calibrator + ``wg_rates``, both CPU)."""
    from error_coupling_simulator.mechanisms.qutrit_leakage import (
        solve_theta_for_wg_l1,
        wg_rates,
    )
    p = _mk_preset(wg_l1_target=_WG_L1_TARGET)
    theta = resolve_theta(p)
    expected = solve_theta_for_wg_l1(_WG_L1_TARGET, g_seep=_G_SEEP, g_heat=_G_HEAT)
    assert abs(theta - expected) <= 1e-12, \
        f"resolve_theta wg branch {theta!r} != calibrator {expected!r}"
    # K-1: not a dead passthrough of some raw theta.
    assert theta > 0.0 and abs(theta - _THETA_RAW) > 1e-3, \
        "wg-resolved theta suspiciously equals the raw cell / zero (dead resolve, K-1)"
    # independent: it HITS the registered rate on the exact channel.
    assert abs(wg_rates(theta, _G_SEEP, _G_HEAT)[0] - _WG_L1_TARGET) <= 1e-8, \
        "resolved theta does not hit WG_L1 = 5e-3 on the exact channel rate"


def test_resolve_theta_both_branches_distinct():
    """§3.5 BOUNDARY: both branches of the ``preset.theta_rad is not None`` if are
    taken (raw -> passthrough, wg -> calibrate) and they yield DISTINCT values on the
    registered presets. Defends K-1 (a branch that always takes the same leg)."""
    raw = resolve_theta(PRESET_LEAK_THETA_0P30)
    wg = resolve_theta(PRESET_LEAK_WG_L1_5E3)
    assert raw == 0.30
    assert wg != raw, "raw and wg conventions resolved to the same theta (dead branch)"


# =========================================================================== #
# §3.6  run_spec_from_preset(preset, *, n_shots, n_rounds, seed, m=0, ...)     #
# =========================================================================== #
@requires_data
def test_run_spec_from_preset_raw_passthrough():
    """§3.6 NORMAL (raw, K-1 dead-plumbing + K-8): every run-shape kwarg passes through
    to the ``RunSpec`` (all four DISTINCT from RunSpec defaults AND from each other, so
    a swap is caught); RAW theta is EXACT identity; physics knobs carry through.

    requires_data: resolves the shipped r01 circuit/metadata paths."""
    rs = run_spec_from_preset(PRESET_LEAK_THETA_0P30, n_shots=3, n_rounds=2,
                              seed=17, m=1)
    assert isinstance(rs, RunSpec)
    assert (rs.N, rs.R, rs.base_seed, rs.m) == (3, 2, 17, 1), \
        f"run-shape did not pass through: (N,R,base_seed,m)=" \
        f"({rs.N},{rs.R},{rs.base_seed},{rs.m}) != (3,2,17,1) (K-1)"
    assert rs.theta == _THETA_RAW, f"RAW theta {rs.theta!r} != {_THETA_RAW!r} EXACTLY (K-8)"
    assert rs.g_seep == _G_SEEP and rs.b == _B_BIAS and rs.arm == _ARM \
        and rs.readout_conv == _READOUT_CONV, "physics knobs did not carry (K-1)"
    assert rs.dtype == "c128", f"dtype not pinned to c128 (got {rs.dtype!r})"
    provenance = rs.numerical_provenance
    assert provenance is not None
    assert provenance["status"] == "complete_for_registered_preset"
    assert provenance["run_binding"]["resolved_theta_rad"] == {
        "value": _THETA_RAW,
        "provenance_kind": "project-design",
        "transformation": "identity_from_registered_theta_rad",
        "claims_device_calibration": False,
    }
    assert provenance["run_binding"]["dataset_files"][
        "supplies_physical_noise_parameters"] is False


@requires_data
def test_run_spec_from_preset_wg_solves_model_coordinate_here():
    """§3.6 NORMAL (wg): the WG preset's theta is model-rate-solved at build time.
    Defends K-1 (the wg resolve is live inside ``run_spec_from_preset``)."""
    from error_coupling_simulator.mechanisms.qutrit_leakage import (
        solve_theta_for_wg_l1,
    )
    rs = run_spec_from_preset(PRESET_LEAK_WG_L1_5E3, n_shots=1, n_rounds=1, seed=0)
    expected = solve_theta_for_wg_l1(_WG_L1_TARGET, g_seep=_G_SEEP, g_heat=_G_HEAT)
    assert abs(rs.theta - expected) <= 1e-12
    assert rs.theta > 0.0 and abs(rs.theta - _THETA_RAW) > 1e-3, \
        "wg run-spec theta equals the raw cell / zero (dead resolve, K-1)"
    provenance = rs.numerical_provenance
    assert provenance is not None
    resolved = provenance["run_binding"]["resolved_theta_rad"]
    assert resolved["value"] == pytest.approx(expected)
    assert resolved["provenance_kind"] == "calibrated-to-paper"
    assert resolved["claims_device_calibration"] is False


@requires_data
def test_run_spec_from_preset_m_default_vs_explicit():
    """§3.6 BOUNDARY: ``m=0`` default vs ``m=1`` explicit both plumb through. Defends
    K-1 (a dead ``m`` kwarg would collapse both to the same value)."""
    rs0 = run_spec_from_preset(PRESET_LEAK_THETA_0P30, n_shots=1, n_rounds=1, seed=0)
    rs1 = run_spec_from_preset(PRESET_LEAK_THETA_0P30, n_shots=1, n_rounds=1, seed=0,
                               m=1)
    assert rs0.m == 0 and rs1.m == 1, f"m plumbing dead: {rs0.m}, {rs1.m}"


def test_run_spec_from_preset_propagates_bogus_root(tmp_path):
    """§3.6 EXCEPTION: a bogus ``dataset_root`` propagates the ``_dataset_files``
    ``FileNotFoundError`` UNCHANGED (defense-in-depth: the run-spec builder does not
    swallow it). Defends K-1.

    CPU-only: the nonexistent root raises before any RunSpec construction."""
    bogus = tmp_path / "bogus_runspec_root"
    assert not bogus.exists()
    with pytest.raises(FileNotFoundError) as ei:
        run_spec_from_preset(PRESET_LEAK_THETA_0P30, n_shots=1, n_rounds=1, seed=0,
                             dataset_root=bogus)
    assert str(bogus) in str(ei.value)


def test_custom_or_spoofed_preset_fails_closed_to_implementation_only(monkeypatch):
    """Caller metadata and copied registered values cannot forge complete provenance."""
    monkeypatch.setattr(
        experiments,
        "_dataset_files",
        lambda _root: {
            "r01_circ": xp.DEFAULT_DATASET_ROOT / "synthetic_circuit.stim",
            "r01_meta": xp.DEFAULT_DATASET_ROOT / "synthetic_metadata.json",
        },
    )
    custom = ExperimentPreset(
        name="custom_unregistered",
        theta_rad=0.1,
        g_seep=0.0,
        g_heat=0.0,
        b_bias=0.5,
        arm="A",
        readout_conv="biased_b",
        provenance_manifest={
            "schema": "error_coupling_simulator.frontend.experiment_preset_provenance.v1",
            "status": "complete_for_registered_preset",
            "fields": {},
        },
    )
    spoof = dataclasses.replace(
        PRESET_LEAK_THETA_0P30,
        provenance_manifest=PRESET_LEAK_THETA_0P30.provenance_manifest,
    )
    for preset in (custom, spoof):
        spec = run_spec_from_preset(preset, n_shots=2, n_rounds=3, seed=4)
        provenance = spec.numerical_provenance
        assert provenance is not None
        assert provenance["status"] == "missing"
        assert provenance["claim_scope"] == "implementation_only"
        assert "not trusted" in provenance["reason"]
        assert provenance["run_binding"]["dataset_files"]["claim_scope"] == \
            "geometry_and_schedule_only"


def test_registered_facade_binding_survives_public_dict_mutation(monkeypatch):
    """Only the canonical object binds complete status; header uses its frozen snapshot."""
    monkeypatch.setattr(
        experiments,
        "_dataset_files",
        lambda _root: {
            "r01_circ": xp.DEFAULT_DATASET_ROOT / "synthetic_circuit.stim",
            "r01_meta": xp.DEFAULT_DATASET_ROOT / "synthetic_metadata.json",
        },
    )
    spec = run_spec_from_preset(
        PRESET_LEAK_THETA_0P30, n_shots=2, n_rounds=3, seed=4)
    assert spec.numerical_provenance["status"] == \
        "complete_for_registered_preset"
    assert len(spec.numerical_provenance["preset_manifest_sha256"]) == 64

    spec.numerical_provenance["status"] = "mutated_spec_dict"
    marsh = SimpleNamespace(
        n_data=4,
        n_stab=2,
        R=3,
        log_supp=SimpleNamespace(tolist=lambda: [0, 2]),
        leak_kraus=torch.eye(3, dtype=torch.complex128).unsqueeze(0),
        gate_unitaries=torch.eye(3, dtype=torch.complex128).unsqueeze(0),
    )
    header = object.__new__(FusedWithinCycleSampler).build_header(
        spec, marsh, SimpleNamespace(logical_kind="Z"))
    assert header["numerical_provenance"]["status"] == \
        "complete_for_registered_preset"


def test_run_spec_numerical_provenance_is_json_safe_and_enters_shot_header():
    """The auditable preset ledger must survive the final shot-header emission seam."""
    with pytest.raises(ValueError, match="numerical_provenance must be JSON-safe"):
        RunSpec(circuit_path="unused.stim", numerical_provenance={"bad": {1, 2}})

    with pytest.raises(ValueError, match="only from the registered facade"):
        RunSpec(
            circuit_path="unused.stim",
            numerical_provenance={
                "schema": "error_coupling_simulator.frontend.run_numerical_provenance.v1",
                "status": "complete_for_registered_preset",
            },
        )

    ledger = {
        "schema": "error_coupling_simulator.frontend.run_numerical_provenance.v1",
        "status": "missing",
        "claim_scope": "implementation_only",
        "reason": "direct RunSpec has no trusted registered facade",
        "run_binding": {
            "resolved_theta_rad": {
                "value": 0.0,
                "claims_device_calibration": False,
            },
            "dataset_files": {
                "circuit": "unused.stim",
                "metadata": None,
                "supplies_physical_noise_parameters": False,
            },
            "run_shape": {
                "n_shots": 2,
                "n_rounds": 3,
                "seed": 0,
                "logical_input_m": 0,
            },
            "precision": {
                "policy": "optimization_c64_final_certification_c128_v1",
                "run_purpose": "final",
                "dtype": "c128",
                "evidence_eligibility": "c128_candidate",
            },
        },
    }
    spec = RunSpec(circuit_path="unused.stim", N=2, R=3, numerical_provenance=ledger)
    ledger["status"] = "mutated_after_construction"
    assert spec.numerical_provenance["status"] == "missing"
    marsh = SimpleNamespace(
        n_data=4,
        n_stab=2,
        R=3,
        log_supp=SimpleNamespace(tolist=lambda: [0, 2]),
        leak_kraus=torch.eye(3, dtype=torch.complex128).unsqueeze(0),
        gate_unitaries=torch.eye(3, dtype=torch.complex128).unsqueeze(0),
    )
    sched = SimpleNamespace(logical_kind="Z")
    host = object.__new__(FusedWithinCycleSampler)
    spec.numerical_provenance["status"] = "mutated_spec_dict"
    header = host.build_header(spec, marsh, sched)
    assert header["numerical_provenance"]["status"] == "missing"
    assert header["numerical_provenance"] is not spec.numerical_provenance
    header["numerical_provenance"]["status"] = "mutated_header"
    assert spec.numerical_provenance["status"] == "mutated_spec_dict"


# =========================================================================== #
# §3.7  leak_slice_table(preset_or_params, *, device, as_list=False) -- arms   #
# =========================================================================== #
# EXCEPTION: wrong-type arg -> TypeError (LINE 330, CPU-only) -----------------
@pytest.mark.parametrize("bad", [None, {"theta": 0.3}, 0.30, "preset", [1, 2, 3]])
def test_leak_slice_table_wrong_type_raises_type_error(bad):
    """§3.7 EXCEPTION / LINE 330 (CPU-only, the measured miss): ``preset_or_params``
    that is NEITHER an ``ExperimentPreset`` NOR a ``RunSpec`` -> ``TypeError`` naming
    the received type. Defends K-1 (the type guard must fire).

    CPU-only: the ``isinstance`` chain runs before carrier construction
    construction or GPU work (§3.7 (5): the TypeError branch is CPU-reachable; the
    builder arms are the GPU-gated, NAMED-exempt legs -- see the module docstring /
    §11 BL-1). ``device`` is passed but never reached on this path."""
    with pytest.raises(TypeError) as ei:
        leak_slice_table(bad, device=DEVICE)
    assert type(bad).__name__ in str(ei.value), \
        f"TypeError must NAME the received type {type(bad).__name__} (got {str(ei.value)!r})"


def test_leak_slice_table_type_guard_is_live_control():
    """§3.7 KILLER (K-1): the type guard is a LIVE control -- demonstrated to trip on a
    broken (wrong-type) input via ``assert_control_trips``. A guard that has never been
    shown to fail is unproven (scrutinize-vacuous-checks).

    CPU-only (the TypeError fires before any GPU work). The check_fn adapts
    ``leak_slice_table`` to the ``(broken_input, gate_tol)`` shape; ``gate_tol`` is
    unused here (a type raise, not a tolerance gate) but the control SHAPE is kept
    uniform. Note: the helper asserts an ``AssertionError`` is raised, so we wrap the
    ``TypeError`` into one."""
    def _check(broken, _tol):
        try:
            leak_slice_table(broken, device=DEVICE)
        except TypeError:
            raise AssertionError("type guard tripped (expected)")
    assert_control_trips(_check, object(), gate_tol=None)


# NAMED GPU EXEMPTION (§11 BL-1): the stacked / list builder arms (source lines
# 333-337, ALL after the GPU build_within_cycle_leak call) are requires_cuda and
# covered by the existing integration gate test_leak_slice_table_matches_sv_sampler
# (KEPT). The unit tests below assert only the ROUTING + return-SHAPE there, never
# re-derive the builder's CPTP/composition asserts.
@requires_cuda
@requires_data
def test_leak_slice_table_preset_arm_stacked_shape():
    """§3.7 NORMAL (preset arm, stacked): the ``ExperimentPreset`` arm returns a
    stacked ``(n_kraus, 3, 3)`` device tensor. Defends the ROUTING (K-1: the preset arm
    was previously dead); the builder's interior asserts are the NAMED-exempt GPU legs.

    requires_cuda: ``build_within_cycle_leak`` is GPU-hosted."""
    import torch
    table = leak_slice_table(PRESET_LEAK_THETA_0P30, device=DEVICE)
    assert isinstance(table, torch.Tensor)
    assert table.dim() == 3 and tuple(table.shape[-2:]) == (3, 3), \
        f"preset-arm table shape {tuple(table.shape)} not (n_kraus, 3, 3)"


@requires_cuda
@requires_data
def test_leak_slice_table_as_list_return_shape():
    """§3.7 BOUNDARY (the ``as_list`` return-shape branch, lines 335->336/337): the
    list form stacks back to the stacked form. Defends the return-shape routing.

    requires_cuda: builder arms are GPU-hosted."""
    import torch
    stacked = leak_slice_table(PRESET_LEAK_THETA_0P30, device=DEVICE, as_list=False)
    lst = leak_slice_table(PRESET_LEAK_THETA_0P30, device=DEVICE, as_list=True)
    assert isinstance(lst, list) and len(lst) == int(stacked.shape[0])
    assert torch.equal(torch.stack(lst), stacked), \
        "as_list form does not stack back to the stacked table"


@requires_cuda
@requires_data
def test_leak_slice_table_runspec_arm_matches_preset_arm():
    """§3.7 NORMAL (RunSpec arm == preset arm, K-5): both arms route to the SAME C1
    builder, so ``leak_slice_table(preset)`` == ``leak_slice_table(run_spec_from_preset
    (preset))`` byte-for-byte. Defends K-5 (self-comparison vacuity: also shown to
    CHANGE across cells) + K-1 (a g_seep<->g_heat swap on the preset arm would build a
    DIFFERENT table).

    requires_cuda + requires_data (the RunSpec arm resolves the shipped paths)."""
    import torch
    require_precondition(
        PRESET_LEAK_THETA_0P30.g_seep != PRESET_LEAK_THETA_0P30.g_heat,
        "preset g_seep == g_heat -- the knob-swap devious arm would be undetectable",
        remedy="gate on a preset with distinct seep/heat")
    t_preset = leak_slice_table(PRESET_LEAK_THETA_0P30, device=DEVICE)
    spec = run_spec_from_preset(PRESET_LEAK_THETA_0P30, n_shots=1, n_rounds=1, seed=0)
    t_spec = leak_slice_table(spec, device=DEVICE)
    assert torch.equal(t_preset, t_spec), \
        "preset arm != RunSpec-from-same-preset arm (the preset arm drifts, K-1)"
    # K-5: a grossly-different cell must CHANGE the table (not a cached constant).
    t_hi = leak_slice_table(_mk_preset(theta_rad=_THETA_HI, g_seep=_G_SEEP_HI),
                            device=DEVICE)
    require_precondition(tuple(t_hi.shape) == tuple(t_preset.shape),
                         "retained Choi rank differs between cells",
                         remedy="re-pick the discriminator cell")
    assert not torch.equal(t_hi, t_preset), \
        "hi-cell table == RAW-cell table: the spec is a dead parameter (K-1/K-5)"


# =========================================================================== #
# L1 — Hypothesis property test for ExperimentPreset validation (§12.1)        #
# =========================================================================== #
# The faithfulness invariant encoded here (§12.1 "preset validation"): a generated
# IN-RANGE config constructs; a generated OUT-OF-RANGE value on ANY single field
# raises. Hypothesis generates thousands of inputs + shrinks to a minimal
# counterexample -- the cure for the hand-picked-'random'-that-was-secretly-valid
# failure mode. CPU-only (pure dataclass validation). All property tests use the
# raw-angle convention as the base so exactly-ONE-convention holds by construction,
# then push ONE field out of range.

# in-range strategies, one per field (kept strictly inside the validated ranges).
_st_theta = st.floats(min_value=0.0, max_value=3.14, allow_nan=False,
                      allow_infinity=False)
_st_rate = st.floats(min_value=1e-6, max_value=0.4999, allow_nan=False,
                     allow_infinity=False)
_st_nonneg = st.floats(min_value=0.0, max_value=5.0, allow_nan=False,
                       allow_infinity=False)
_st_bias = st.floats(min_value=0.0, max_value=1.0, allow_nan=False,
                     allow_infinity=False)
_st_arm = st.sampled_from(list(SV_ARMS))
_st_conv = st.sampled_from(list(SV_READOUT_CONVENTIONS))
_st_name = st.text(min_size=1, max_size=8).filter(lambda s: bool(str(s)))


@settings(max_examples=200)
@given(theta=_st_theta, g_seep=_st_nonneg, g_heat=_st_nonneg, b_bias=_st_bias,
       arm=_st_arm, conv=_st_conv, name=_st_name)
def test_property_in_range_raw_preset_constructs(theta, g_seep, g_heat, b_bias,
                                                 arm, conv, name):
    """§12.1 L1 property (LIVENESS): any raw-angle config with EVERY field in its
    validated range constructs without raising. The complement of the raise-side
    property -- proves the validator is not a blanket-reject (the L1 half of the
    defensive-assert / "legitimate path preserves the invariant" discipline)."""
    p = ExperimentPreset(name=name, theta_rad=theta, wg_l1_target=None,
                         g_seep=g_seep, g_heat=g_heat, b_bias=b_bias,
                         arm=arm, readout_conv=conv)
    # the invariant HOLDS: exactly one convention, ranges respected.
    assert (p.theta_rad is None) != (p.wg_l1_target is None)
    assert p.theta_rad >= 0.0 and p.g_seep >= 0.0 and p.g_heat >= 0.0
    assert 0.0 <= p.b_bias <= 1.0
    assert str(p.arm).upper() in SV_ARMS and str(p.readout_conv) in SV_READOUT_CONVENTIONS


@settings(max_examples=200)
@given(bad_theta=st.floats(max_value=-1e-6, allow_nan=False, allow_infinity=False))
def test_property_negative_theta_always_raises(bad_theta):
    """§12.1 L1 property (SOUNDNESS, field=theta_rad): ANY strictly-negative
    ``theta_rad`` raises ``ValueError``. Hypothesis shrinks to the minimal
    counterexample if the strict-``< 0`` boundary ever drifts."""
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=bad_theta)


@settings(max_examples=200)
@given(bad_rate=st.one_of(
    st.floats(max_value=0.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.5, max_value=1e6, allow_nan=False, allow_infinity=False)))
def test_property_wg_l1_target_out_of_open_interval_always_raises(bad_rate):
    """§12.1 L1 property (SOUNDNESS, field=wg_l1_target): ANY value <= 0 or >= 0.5
    raises. Covers the STRICT open-interval convention over a generated range (the
    edges 0.0 and 0.5 included, being non-strict-min/max of the two sub-strategies)."""
    with pytest.raises(ValueError):
        _mk_preset(wg_l1_target=bad_rate)


@settings(max_examples=200)
@given(bad=st.floats(max_value=-1e-9, allow_nan=False, allow_infinity=False))
def test_property_negative_rate_always_raises(bad):
    """§12.1 L1 property (SOUNDNESS, field=g_seep/g_heat): ANY strictly-negative seep
    OR heat rate raises. Parametrized over BOTH operands of the ``or`` via two draws."""
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, g_seep=bad)
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, g_heat=bad)


@settings(max_examples=200)
@given(bad_b=st.one_of(
    st.floats(max_value=-1e-9, allow_nan=False, allow_infinity=False),
    st.floats(min_value=1.0 + 1e-9, max_value=1e6, allow_nan=False,
              allow_infinity=False)))
def test_property_b_bias_out_of_closed_interval_always_raises(bad_b):
    """§12.1 L1 property (SOUNDNESS, field=b_bias): ANY value strictly below 0 or
    strictly above 1 raises. Pins the CLOSED-interval convention (the edges 0.0/1.0
    are excluded from both sub-strategies, so they are never generated as failures)."""
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, b_bias=bad_b)


@settings(max_examples=100)
@given(bad_arm=st.text(min_size=1, max_size=6).filter(
    lambda s: str(s).upper() not in SV_ARMS))
def test_property_bad_arm_always_raises(bad_arm):
    """§12.1 L1 property (SOUNDNESS, field=arm): ANY string whose upper-case is not in
    ``SV_ARMS`` raises. The ``.upper()`` normalization is baked into the filter, so the
    property respects the (deliberate) case-insensitive arm convention."""
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, arm=bad_arm)


@settings(max_examples=100)
@given(bad_conv=st.text(min_size=1, max_size=8).filter(
    lambda s: str(s) not in SV_READOUT_CONVENTIONS))
def test_property_bad_readout_conv_always_raises(bad_conv):
    """§12.1 L1 property (SOUNDNESS, field=readout_conv): ANY string not EXACTLY in
    ``SV_READOUT_CONVENTIONS`` raises (case-SENSITIVE membership -- no ``.upper()``,
    unlike arm)."""
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, readout_conv=bad_conv)
