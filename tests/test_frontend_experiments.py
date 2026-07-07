"""Wave-2 gates for the A1 experiments facade
(``error_coupling_simulator.frontend.experiments``).

Binding contract: ``docs/twin_validation/api_hardening_ownership_design.md`` row A1,
the NAMING STANDARD rename table (``load_xzzx_d3`` / ``ExperimentPreset`` /
``PRESET_LEAK_THETA_0P30`` / ``PRESET_LEAK_WG_L1_5E3`` / ``run_spec_from_preset`` /
``leak_slice_table``), ratified decision 7 (dataset-root env var =
``QEC_TWIN_D3_DATA``), and the DEVIOUS-TEST STANDARD (KILLER requirement + K-catalog).

Gate -> test map (K-classes each test defends are declared in its docstring):

  A1 loader        : test_load_xzzx_d3_equals_hand_ritual        (K-1, K-5, K-8)
  A1 env override  : test_env_override_missing_root_fails_loud   (K-1, K-5)
  A1 env override  : test_env_override_partial_root_resolves_under_override (K-1, K-5)
  A1 root-beats-env: test_dataset_root_argument_beats_env        (K-1, K-3)
  A1 presets       : test_experiment_preset_validation_killers   (K-1, K-8)
  A1 run spec      : test_run_spec_from_preset_raw_and_wg        (K-1, K-8)
  A1 leak table    : test_leak_slice_table_matches_sv_sampler    (K-1, K-5)
  A1 leak table    : test_leak_slice_table_preset_arm_matches_spec_arm (K-1)

CPU-only wherever possible; ``requires_data`` only where real dataset paths must
resolve; ``requires_cuda`` only where the leak table is actually built (the C1
builder is GPU-hosted).

The facade LANDED (Wave-2 src build); the module-level ``importorskip`` remains only
as an import-environment guard.

API SHAPES (the LANDED signatures, verified against
``src/error_coupling_simulator/frontend/experiments.py``):
  * ``load_xzzx_d3(dataset_root=None, *, with_interior_streams=True)`` -> the parsed
    r01 ``XZZXSchedule`` with the r10 interior streams attached. Root resolution:
    ``dataset_root`` argument > ``QEC_TWIN_D3_DATA`` env (when the key is SET; a
    SET-but-empty/whitespace value raises ``ValueError`` -- fail loud, never
    indistinguishable from unset) > the parser default. Override roots REBASE the
    ``default_*_paths()`` layout (``relative_to(DEFAULT_DATASET_ROOT)``); a missing
    root/file raises ``FileNotFoundError`` NAMING the missing path UNDER THE
    RESOLVED ROOT (never a silent fallback to the default).
  * ``ExperimentPreset(name=..., theta_rad=..., wg_l1_target=..., g_seep=...,
    g_heat=..., b_bias=..., arm=..., readout_conv=...)`` -- frozen kw-only dataclass;
    exactly ONE of ``theta_rad`` / ``wg_l1_target`` set (``ValueError`` otherwise).
  * ``run_spec_from_preset(preset, *, n_shots, n_rounds, seed, m=0,
    dataset_root=None)`` -> a ``qec_twin.forward.scalable.sv_sampler.RunSpec``; the
    WG preset's theta resolves through ``calibrate_theta_for_wg_l1`` (the
    error_coupling_simulator ``mechanisms.qutrit_teachers`` resolver -- same package
    as the facade).
  * ``leak_slice_table(preset_or_params, *, device, as_list=False)`` -> the stacked
    ``(n_kraus, 3, 3)`` table (``as_list=True`` -> the list form); accepts an
    ``ExperimentPreset`` (theta resolved via ``resolve_theta``; sentinel circuit
    path, so no dataset is needed on that arm) OR an explicit ``RunSpec``.
"""

from __future__ import annotations

import pytest
import torch

from qec_twin.forward.exact import xzzx_parser as xp

# Wave-1 canon: markers/constants from tests/conftest.py (contract C1), guard helpers
# from tests/_support/fixtures.py (contract C2).
from conftest import DEVICE, requires_cuda, requires_data
from _support.fixtures import require_precondition

# the A1 facade is a parallel Wave-2 src build -- loud module-level skip until it lands.
experiments = pytest.importorskip(
    "error_coupling_simulator.frontend.experiments",
    reason="Wave-2 A1 facade (frontend/experiments.py) not landed yet (parallel src build)")

#: ratified decision 7 -- the ONE dataset-root env var name.
_ENV = "QEC_TWIN_D3_DATA"

# the p2 cell knobs (the RAW registered preset's pinned values, contract A1: presets
# are frozen + named, NO silent physics defaults).
_THETA_RAW, _G_SEEP, _B_BIAS, _ARM = 0.30, 0.09, 0.9, "A"
_G_HEAT, _READOUT_CONV = 0.0, "biased_b"
_WG_L1_TARGET = 5.0e-3
# the grossly-different discriminator cell (test_p2_mps_per_round_leak.py precedent).
_THETA_HI, _G_SEEP_HI = 1.2, 0.5


@pytest.fixture(autouse=True)
def _no_d3_env_override(monkeypatch):
    """Env isolation (review finding: env-honoring facade vs env-blind reference).

    The facade honors ``QEC_TWIN_D3_DATA``; the hand rituals it is compared against
    read the parser DEFAULT paths (env-blind). A legitimately-set env var must never
    make a CORRECT facade fail a default-root comparison, so it is deleted per-test
    (monkeypatch restores it on teardown). Override tests re-``setenv`` explicitly
    after this fixture runs."""
    monkeypatch.delenv(_ENV, raising=False)


# --------------------------------------------------------------------------- #
# Adapters -- ONE place to fix if a parallel-build signature detail differs.   #
# --------------------------------------------------------------------------- #
def _load_d3(**kw):
    return _as_schedule(experiments.load_xzzx_d3(**kw))


def _as_schedule(ret):
    """Tolerate the contract-allowed provenance wrappers around the schedule."""
    if hasattr(ret, "n_data"):
        return ret
    if isinstance(ret, tuple) and ret and hasattr(ret[0], "n_data"):
        return ret[0]
    if hasattr(ret, "schedule") and hasattr(ret.schedule, "n_data"):
        return ret.schedule
    raise AssertionError(
        f"load_xzzx_d3 return shape unrecognized (adapter _as_schedule): {type(ret)!r}")


def _mk_preset(**kw):
    """Build an ExperimentPreset with the RAW-cell knobs as explicit (never silent)
    test-side fill-ins (the preset class itself has NO physics defaults)."""
    base = dict(name="adapter_test_preset", theta_rad=None, wg_l1_target=None,
                g_seep=_G_SEEP, g_heat=_G_HEAT, b_bias=_B_BIAS, arm=_ARM,
                readout_conv=_READOUT_CONV)
    base.update(kw)
    return experiments.ExperimentPreset(**base)


def _run_spec(preset, *, N=1, R=1, base_seed=0, m=0):
    return experiments.run_spec_from_preset(
        preset, n_shots=N, n_rounds=R, seed=base_seed, m=m)


def _leak_table(spec, *, stacked=True):
    return experiments.leak_slice_table(spec, device=DEVICE, as_list=not stacked)


def _stream_tokens(sched) -> dict:
    """{engine pos -> interior token tuple} from a parsed schedule."""
    return {int(s.pos): tuple(s.tokens) for s in sched.within_cycle_streams}


# =========================================================================== #
# A1 loader: load_xzzx_d3 == the hand ritual                                   #
# =========================================================================== #
@requires_data
def test_load_xzzx_d3_equals_hand_ritual():
    """A1 loader gate. Defends: K-1 (a facade that returns geometry WITHOUT the r10
    interior streams -- the non-empty-streams leg; a facade ignoring the shipped
    dataset -- the hand-parse comparison), K-8 (stabilizer-support / stream-token
    convention drift), K-5 (the stream comparison is preconditioned non-empty, so it
    cannot pass vacuously).

    Reference: the HAND RITUAL on the shipped dataset -- parse r01 geometry +
    attach the r10 interior streams (the exact _sched_and_spec construction of
    tests/test_p2_mps_per_round_leak.py, kept here as the independent transcription).
    """
    r01_circ, r01_meta = xp.default_r01_paths()
    r10_circ, r10_meta = xp.default_r10_paths()
    hand = xp.parse_xzzx_circuit(r01_circ, r01_meta, verify=True)
    hand = hand.with_within_cycle_streams(
        xp.parse_within_cycle_streams(r10_circ, r10_meta))

    got = _load_d3()

    assert int(got.n_data) == int(hand.n_data), \
        f"n_data {got.n_data} != hand-parsed {hand.n_data}"
    # stabilizer supports (ordered pauli dicts -- the geometry authority).
    assert got.stab_paulis() == hand.stab_paulis(), \
        "stabilizer supports != hand-parsed r01 geometry (K-8)"
    # interior streams MUST be attached (K-1: a geometry-only return is the devious
    # implementation this leg kills) and non-empty (K-5 precondition on the hand side).
    hand_tokens = _stream_tokens(hand)
    got_tokens = _stream_tokens(got)
    require_precondition(len(hand_tokens) == int(hand.n_data) and
                         all(len(t) > 0 for t in hand_tokens.values()),
                         "hand-parsed r10 interior streams are empty",
                         remedy="check the shipped r10 patch")
    assert len(got_tokens) == len(hand_tokens), \
        "facade schedule has no / partial interior streams (K-1: streams not attached)"
    # one qutrit spelled out (the task's registered comparison) + all positions.
    assert got_tokens[0] == hand_tokens[0], \
        f"qutrit-0 stream tokens differ: {got_tokens[0]} != {hand_tokens[0]} (K-8)"
    assert got_tokens == hand_tokens, "interior stream tokens differ (K-8)"


# =========================================================================== #
# A1 env override killers                                                      #
# =========================================================================== #
def test_env_override_missing_root_fails_loud(monkeypatch, tmp_path):
    """A1 env-override KILLER. Defends: K-1 (a dead ``QEC_TWIN_D3_DATA`` env
    parameter -- an implementation that silently falls back to the shipped default
    would SUCCEED here and fail the raises), K-5 (the error must NAME the bogus path,
    so the raise is provably about OUR root, not an unrelated failure).

    Contract row A1 / ratified decision 7: a nonexistent env root raises
    ``FileNotFoundError`` naming the missing file -- NEVER a silent fallback.
    """
    bogus = tmp_path / "nonexistent_d3_root"
    assert not bogus.exists()
    monkeypatch.setenv(_ENV, str(bogus))
    with pytest.raises(FileNotFoundError) as excinfo:
        _load_d3()
    msg = str(excinfo.value)
    assert str(bogus) in msg, \
        f"FileNotFoundError must NAME the missing path under the bogus env root " \
        f"{bogus} (got: {msg!r})"


@requires_data
def test_dataset_root_argument_beats_env(monkeypatch, tmp_path):
    """A1 precedence KILLER (both directions). Defends: K-1 (dead ``dataset_root``
    argument), K-3 (resolution-order drift: argument > env > default).

    Leg 1: env = bogus, ``dataset_root`` = the real shipped root -> loads fine and
    matches the hand parse (an env-preferring implementation raises here).
    Leg 2: env = the REAL root, ``dataset_root`` = bogus -> raises naming the bogus
    path (an env-preferring implementation would silently succeed -- the killer).
    """
    real_root = xp.DEFAULT_DATASET_ROOT
    bogus = tmp_path / "bogus_d3_root"
    assert not bogus.exists()

    # Leg 1: argument rescues a bogus env.
    monkeypatch.setenv(_ENV, str(bogus))
    got = _load_d3(dataset_root=real_root)
    hand = xp.parse_xzzx_circuit(*xp.default_r01_paths(), verify=True)
    assert int(got.n_data) == int(hand.n_data)
    assert got.stab_paulis() == hand.stab_paulis(), \
        "dataset_root argument did not resolve to the real shipped patch (K-1)"

    # Leg 2: argument OVERRIDES a good env (the resolution-order killer, K-3).
    monkeypatch.setenv(_ENV, str(real_root))
    with pytest.raises(FileNotFoundError) as excinfo:
        _load_d3(dataset_root=bogus)
    assert str(bogus) in str(excinfo.value), \
        "dataset_root=bogus with a GOOD env must still fail, naming the bogus path " \
        "(argument beats env; an env-preferring resolution order passes silently)"


@requires_data
def test_env_override_partial_root_resolves_under_override(monkeypatch, tmp_path):
    """A1 override-RESOLUTION killer. Defends: K-1 (the existence-check-only devious
    implementation: it verifies the override ROOT is a directory, then silently reads
    the DEFAULT root's files -- every other override gate here passes it, because
    their bogus roots fail the very existence check), K-5 (the raise is pinned to the
    OVERRIDE root's path, so it is provably about resolution under our root).

    Construction: a tmp override root replicating the dataset's RELATIVE layout --
    derived from ``default_*_paths().relative_to(DEFAULT_DATASET_ROOT)``, never a
    hardcoded layout -- holding THREE of the four files (r10 metadata OMITTED). The
    shipped files are tiny (measured 2026-07-07: circuits 1.3/8.2 KiB, metadata
    ~240 B), so plain copies are used (a <1 MiB size precondition guards that call).
    All four files DO exist under the default root, so the devious impl SUCCEEDS
    silently; the correct impl must raise ``FileNotFoundError`` NAMING the missing
    path UNDER THE OVERRIDE root (proof that resolution actually happened there).
    """
    import shutil

    real = {}
    real["r01_circ"], real["r01_meta"] = xp.default_r01_paths()
    real["r10_circ"], real["r10_meta"] = xp.default_r10_paths()
    rel = {name: p.relative_to(xp.DEFAULT_DATASET_ROOT) for name, p in real.items()}

    override_root = tmp_path / "partial_d3_root"
    omitted = "r10_meta"
    for name, src in real.items():
        if name == omitted:
            continue
        require_precondition(
            src.stat().st_size < (1 << 20),
            f"shipped file {src} unexpectedly large for a tmp copy "
            f"({src.stat().st_size} B)", remedy="symlink instead of copying")
        dst = override_root / rel[name]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    assert override_root.is_dir()  # the devious existence check would PASS here

    monkeypatch.setenv(_ENV, str(override_root))
    with pytest.raises(FileNotFoundError) as excinfo:
        _load_d3()
    msg = str(excinfo.value)
    assert str(override_root / rel[omitted]) in msg, \
        f"FileNotFoundError must NAME the missing {omitted} path UNDER the override " \
        f"root {override_root} (resolution must actually happen there -- a default-" \
        f"root fallback would have succeeded silently; got: {msg!r})"


# =========================================================================== #
# A1 ExperimentPreset validation killers                                       #
# =========================================================================== #
def test_experiment_preset_validation_killers():
    """A1 preset-contract KILLERS. Defends: K-1 (a validator that never fires --
    both raises are demonstrated), K-8 (theta-convention drift: the two theta
    conventions are DISTINCT registered presets with pinned knob values, N-4 unit
    tag ``theta_rad``).

    Contract row A1: exactly ONE of ``theta_rad`` / ``wg_l1_target`` is set; the
    preset is frozen (assignment raises); the two registered presets carry the
    p2-cell knobs explicitly (no silent physics defaults).
    """
    import dataclasses

    # both conventions set -> raises.
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, wg_l1_target=_WG_L1_TARGET)
    # neither set -> raises (no silent physics default).
    with pytest.raises(ValueError):
        _mk_preset()
    # a valid single-convention preset builds, and is FROZEN.
    preset = _mk_preset(theta_rad=_THETA_RAW)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        preset.theta_rad = 0.99  # type: ignore[misc]

    # the two REGISTERED presets exist as distinct named cells with pinned knobs.
    raw = experiments.PRESET_LEAK_THETA_0P30
    wg = experiments.PRESET_LEAK_WG_L1_5E3
    assert raw.theta_rad == _THETA_RAW and raw.wg_l1_target is None, \
        f"RAW preset knobs drifted: theta_rad={raw.theta_rad!r}, " \
        f"wg_l1_target={raw.wg_l1_target!r} (K-8)"
    assert wg.wg_l1_target == _WG_L1_TARGET and wg.theta_rad is None, \
        f"WG preset knobs drifted: wg_l1_target={wg.wg_l1_target!r}, " \
        f"theta_rad={wg.theta_rad!r} (K-8)"
    for p, tag in ((raw, "RAW"), (wg, "WG")):
        assert p.g_seep == _G_SEEP, f"{tag} preset g_seep {p.g_seep} != {_G_SEEP} (K-8)"
        assert p.g_heat == _G_HEAT, f"{tag} preset g_heat {p.g_heat} != {_G_HEAT} (K-8)"
        assert p.b_bias == _B_BIAS, f"{tag} preset b_bias {p.b_bias} != {_B_BIAS} (K-8)"
        assert str(p.arm) == _ARM, f"{tag} preset arm {p.arm!r} != {_ARM!r} (K-8)"
        assert str(p.readout_conv) == _READOUT_CONV, \
            f"{tag} preset readout_conv {p.readout_conv!r} != {_READOUT_CONV!r} (K-8)"


# =========================================================================== #
# A1 run_spec_from_preset                                                      #
# =========================================================================== #
@requires_data
def test_run_spec_from_preset_raw_and_wg():
    """A1 run-spec gate. Defends: K-1 (a dead WG resolve -- a passthrough that never
    calls the calibrator is killed by the theta != 0.30 leg AND the independent
    wg_rates conformance leg), K-8 (RAW theta must pass through EXACTLY -- no unit /
    convention munging of ``theta_rad``).

    RAW preset: ``RunSpec.theta == theta_rad`` EXACTLY (float identity, contract).
    WG preset: theta resolves through ``calibrate_theta_for_wg_l1`` at the preset's
    g_seep/g_heat; conformance is ALSO checked independently on the exact channel
    rate ``wg_rates(theta)[0] == 5e-3`` (the resolver's own registered tolerance is
    1e-10; 1e-8 leaves slack for the bisection terminal bracket).
    """
    from error_coupling_simulator.mechanisms.qutrit_teachers import (
        calibrate_theta_for_wg_l1,
        wg_rates,
    )
    from qec_twin.forward.scalable.sv_sampler import RunSpec

    # distinct, non-default run-shape values so the passthrough asserts discriminate
    # (all four differ from the RunSpec defaults AND from each other).
    rs_raw = _run_spec(experiments.PRESET_LEAK_THETA_0P30, N=3, R=2, base_seed=17, m=1)
    assert isinstance(rs_raw, RunSpec)
    assert (rs_raw.N, rs_raw.R, rs_raw.base_seed, rs_raw.m) == (3, 2, 17, 1), \
        f"run-shape knobs (n_shots/n_rounds/seed/m) did not pass through to the " \
        f"RunSpec: (N,R,base_seed,m)=({rs_raw.N},{rs_raw.R},{rs_raw.base_seed}," \
        f"{rs_raw.m}) != (3,2,17,1) (K-1 dead plumbing)"
    assert rs_raw.theta == _THETA_RAW, \
        f"RAW preset theta {rs_raw.theta!r} != theta_rad {_THETA_RAW!r} EXACTLY (K-8)"
    assert rs_raw.g_seep == _G_SEEP and rs_raw.b == _B_BIAS and rs_raw.arm == _ARM, \
        "RAW preset knobs did not carry into the RunSpec (K-1 dead plumbing)"

    rs_wg = _run_spec(experiments.PRESET_LEAK_WG_L1_5E3, N=1, R=1)
    assert rs_wg.g_seep == _G_SEEP and rs_wg.b == _B_BIAS and rs_wg.arm == _ARM
    expected = calibrate_theta_for_wg_l1(_WG_L1_TARGET, g_seep=_G_SEEP, g_heat=0.0)
    assert abs(rs_wg.theta - expected) <= 1e-12, \
        f"WG preset theta {rs_wg.theta!r} != calibrate_theta_for_wg_l1 " \
        f"resolve {expected!r} (contract A1 resolver)"
    # independent conformance: the resolved theta actually HITS the registered rate.
    assert abs(wg_rates(rs_wg.theta, _G_SEEP, 0.0)[0] - _WG_L1_TARGET) <= 1e-8, \
        "resolved theta does not hit WG_L1 = 5e-3 on the exact channel rate"
    # KILLER (K-1): the WG resolve must not be a dead passthrough of some raw theta.
    assert rs_wg.theta > 0.0 and abs(rs_wg.theta - _THETA_RAW) > 1e-3, \
        "WG preset theta suspiciously equals the RAW cell / zero (dead resolve, K-1)"


# =========================================================================== #
# A1 leak_slice_table == SvSampler.build_within_cycle_leak (byte-for-byte)     #
# =========================================================================== #
@requires_cuda
@requires_data
def test_leak_slice_table_matches_sv_sampler():
    """A1 leak-table gate. Defends: K-5 (self-comparison vacuity: the facade table is
    checked against the C1 builder AND shown to CHANGE across cells), K-1 (a dead
    spec parameter: a facade returning a cached/constant table is killed by the
    distinct-cell leg).

    Gate: ``leak_slice_table`` on the RAW-preset spec equals
    ``SvSampler.build_within_cycle_leak`` on the SAME spec byte-for-byte
    (``torch.equal`` -- exact, no tolerance); the list form stacks back to the same
    table. KILLER: the grossly-different hi cell's table must DIFFER.
    """
    from qec_twin.forward.scalable.sv_sampler import SvSampler

    spec = _run_spec(experiments.PRESET_LEAK_THETA_0P30, N=1, R=1)
    table = _leak_table(spec)
    ref, _ = SvSampler(device=DEVICE).build_within_cycle_leak(spec)
    assert isinstance(table, torch.Tensor)
    assert tuple(table.shape) == tuple(ref.shape) and table.dim() == 3 \
        and table.shape[-2:] == (3, 3), \
        f"leak table shape {tuple(table.shape)} != builder {tuple(ref.shape)}"
    assert torch.equal(table, ref), \
        "leak_slice_table != SvSampler.build_within_cycle_leak byte-for-byte"

    # list form (contract A1: stacked [K,3,3] and list forms).
    lst = _leak_table(spec, stacked=False)
    assert isinstance(lst, (list, tuple)) and len(lst) == int(ref.shape[0])
    assert torch.equal(torch.stack(list(lst)), ref), \
        "list-form leak table does not stack back to the builder table"

    # KILLER (K-1/K-5): a distinct cell's table must differ (dead-spec guard).
    spec_hi = _run_spec(_mk_preset(theta_rad=_THETA_HI, g_seep=_G_SEEP_HI), N=1, R=1)
    table_hi = _leak_table(spec_hi)
    require_precondition(tuple(table_hi.shape) == tuple(table.shape),
                         "retained Choi rank differs between the two cells",
                         remedy="re-pick the discriminator cell")
    assert not torch.equal(table_hi, table), \
        "hi-cell leak table == RAW-cell table: the spec is a dead parameter (K-1)"


@requires_cuda
@requires_data
def test_leak_slice_table_preset_arm_matches_spec_arm():
    """A1 preset-arm gate. Defends: K-1 (the ``ExperimentPreset`` arm of
    ``leak_slice_table`` was previously exercised by NO test -- dead code; and a
    devious preset arm that swaps ``g_seep <-> g_heat`` builds from (0.0, 0.09)
    instead of (0.09, 0.0) here -- a DIFFERENT table, so it fails the exact
    equality).

    Gate: ``leak_slice_table(PRESET)`` equals ``leak_slice_table(run_spec_from_preset
    (PRESET, n_shots=1, n_rounds=1, seed=0))`` via ``torch.equal`` (exact -- both
    arms route through the same C1-asserted ``build_within_cycle_leak``).
    """
    preset = experiments.PRESET_LEAK_THETA_0P30
    require_precondition(
        preset.g_seep != preset.g_heat,
        "preset g_seep == g_heat (the knob-swap devious arm would be undetectable)",
        remedy="gate on a preset with distinct seep/heat rates")
    table_preset = experiments.leak_slice_table(preset, device=DEVICE)
    spec = experiments.run_spec_from_preset(preset, n_shots=1, n_rounds=1, seed=0)
    table_spec = experiments.leak_slice_table(spec, device=DEVICE)
    assert isinstance(table_preset, torch.Tensor)
    assert torch.equal(table_preset, table_spec), \
        "leak_slice_table(ExperimentPreset) != leak_slice_table(RunSpec from the " \
        "SAME preset): the preset arm drifts from the spec arm (K-1)"
