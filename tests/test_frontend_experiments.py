"""Current acceptance tests for ``error_coupling_simulator.frontend.experiments``.

The tests cover independent d3 schedule loading, dataset-root resolution and
precedence, explicit leakage presets, ``RunSpec`` construction, and exact leakage
table agreement with the fused carrier builder. Each comparison includes a
non-vacuity or corruption falsifier appropriate to the behavior under test.

Tests are CPU-only wherever possible. ``requires_data`` is used only where real
dataset paths must resolve, and ``requires_cuda`` only where a leakage table is
actually built by the GPU-hosted carrier.

Current API shapes, verified against
``src/error_coupling_simulator/frontend/experiments.py``:
  * ``load_xzzx_d3(dataset_root=None, *, with_interior_streams=True)`` -> the parsed
    r01 ``XZZXSchedule`` with the r10 interior streams attached. Root resolution:
    ``dataset_root`` argument > ``ECS_D3_DATA_ROOT`` env (when the key is SET; a
    SET-but-empty/whitespace value raises ``ValueError`` -- fail loud, never
    indistinguishable from unset) > the parser default. Override roots REBASE the
    ``default_*_paths()`` layout (``relative_to(DEFAULT_DATASET_ROOT)``); a missing
    root/file raises ``FileNotFoundError`` NAMING the missing path UNDER THE
    RESOLVED ROOT (never a silent fallback to the default).
  * ``ExperimentPreset(name=..., theta_rad=..., leakage_rate_target=..., g_seep=...,
    g_heat=..., b_bias=..., arm=..., readout_conv=...)`` -- frozen kw-only dataclass;
    exactly one of ``theta_rad`` / ``leakage_rate_target`` set (``ValueError`` otherwise).
  * ``run_spec_from_preset(preset, *, n_shots, n_rounds, seed, m=0,
    dataset_root=None)`` -> a package-local ``carrier.within_cycle.RunSpec``; the
    rate-target preset's theta resolves through ``solve_exchange_angle_for_leakage_rate`` (the
    error_coupling_simulator ``mechanisms.qutrit_leakage`` resolver -- same package
    as the facade).
  * ``leak_slice_table(preset_or_params, *, device, as_list=False)`` -> the stacked
    ``(n_kraus, 3, 3)`` table (``as_list=True`` -> the list form); accepts an
    ``ExperimentPreset`` (theta resolved via ``resolve_theta``; sentinel circuit
    path, so no dataset is needed on that arm) OR an explicit ``RunSpec``.
"""

from __future__ import annotations

import pytest
import torch

from error_coupling_simulator.frontend import experiments
from error_coupling_simulator.frontend import xzzx_parser as xp

# Shared execution markers/constants and precondition helpers.
from conftest import DEVICE, requires_cuda, requires_data
from _support.fixtures import require_precondition

#: The single dataset-root environment variable exposed by the current frontend.
_ENV = "ECS_D3_DATA_ROOT"

# Explicit knobs pinned by the registered RAW preset; presets are frozen and named,
# with no silent physics defaults.
_THETA_RAW, _G_SEEP, _B_BIAS, _ARM = 0.30, 0.09, 0.9, "A"
_G_HEAT, _READOUT_CONV = 0.0, "biased_b"
_LEAKAGE_RATE_TARGET = 5.0e-3
# A deliberately different cell used to reject constant-table implementations.
_THETA_HI, _G_SEEP_HI = 1.2, 0.5


@pytest.fixture(autouse=True)
def _no_d3_env_override(monkeypatch):
    """Isolate the environment-aware facade from the default-path reference.

    The facade honors ``ECS_D3_DATA_ROOT``; the independent parse used as its
    reference reads the parser's default paths. A legitimately set variable must not
    make a correct facade fail a default-root comparison, so it is deleted per-test
    (monkeypatch restores it on teardown). Override tests re-``setenv`` explicitly
    after this fixture runs."""
    monkeypatch.delenv(_ENV, raising=False)


# --------------------------------------------------------------------------- #
# Adapters centralize the accepted frontend return shapes.                     #
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
    base = dict(name="adapter_test_preset", theta_rad=None, leakage_rate_target=None,
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
# Loader: load_xzzx_d3 equals an independent parse                             #
# =========================================================================== #
@requires_data
def test_load_xzzx_d3_equals_hand_ritual():
    """Require the loader to match an independent parse of the shipped dataset.

    The non-empty-stream precondition rejects geometry-only returns and makes the
    stream comparison non-vacuous. Ordered stabilizer supports and stream tokens
    catch convention drift.

    The independent reference parses r01 geometry and attaches the r10 interior
    streams directly through ``xzzx_parser``.
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
        "stabilizer supports != hand-parsed r01 geometry"
    # Interior streams must be attached, and the independent reference must be
    # non-empty so a geometry-only return cannot pass vacuously.
    hand_tokens = _stream_tokens(hand)
    got_tokens = _stream_tokens(got)
    require_precondition(len(hand_tokens) == int(hand.n_data) and
                         all(len(t) > 0 for t in hand_tokens.values()),
                         "hand-parsed r10 interior streams are empty",
                         remedy="check the shipped r10 patch")
    assert len(got_tokens) == len(hand_tokens), \
        "facade schedule has no or only partial interior streams"
    # Spell out one qutrit before comparing all positions.
    assert got_tokens[0] == hand_tokens[0], \
        f"qutrit-0 stream tokens differ: {got_tokens[0]} != {hand_tokens[0]}"
    assert got_tokens == hand_tokens, "interior stream tokens differ"


# =========================================================================== #
# Dataset-root environment overrides                                           #
# =========================================================================== #
def test_env_override_missing_root_fails_loud(monkeypatch, tmp_path):
    """Require a nonexistent environment root to fail without a silent fallback.

    The ``FileNotFoundError`` must name the bogus path, proving that the failure is
    caused by resolution under the supplied root rather than an unrelated error.
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
    """Require resolution precedence ``argument > environment > default``.

    Leg 1: env = bogus, ``dataset_root`` = the real shipped root -> loads fine and
    matches the hand parse (an env-preferring implementation raises here).
    Leg 2: env = the REAL root, ``dataset_root`` = bogus -> raises naming the bogus
    path (an env-preferring implementation would silently succeed).
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
        "dataset_root argument did not resolve to the real shipped patch"

    # Leg 2: the argument overrides a valid environment root.
    monkeypatch.setenv(_ENV, str(real_root))
    with pytest.raises(FileNotFoundError) as excinfo:
        _load_d3(dataset_root=bogus)
    assert str(bogus) in str(excinfo.value), \
        "dataset_root=bogus with a GOOD env must still fail, naming the bogus path " \
        "(argument beats env; an env-preferring resolution order passes silently)"


@requires_data
def test_env_override_partial_root_resolves_under_override(monkeypatch, tmp_path):
    """Require every dataset path to resolve beneath the supplied override root.

    This rejects an existence-check-only implementation that validates the root and
    then silently reads files from the default location. The raised error is pinned
    to the override path so the failure cannot be mistaken for an unrelated error.

    Construction: a tmp override root replicating the dataset's RELATIVE layout --
    derived from ``default_*_paths().relative_to(DEFAULT_DATASET_ROOT)``, never a
    hardcoded layout -- holding THREE of the four files (r10 metadata OMITTED).
    Plain copies are guarded by a <1 MiB source-size precondition.
    All four files exist under the default root, so an incorrect fallback would
    succeed silently; the correct implementation must raise ``FileNotFoundError``
    naming the missing path under the override root.
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
    assert override_root.is_dir()  # A root-only existence check passes here.

    monkeypatch.setenv(_ENV, str(override_root))
    with pytest.raises(FileNotFoundError) as excinfo:
        _load_d3()
    msg = str(excinfo.value)
    assert str(override_root / rel[omitted]) in msg, \
        f"FileNotFoundError must NAME the missing {omitted} path UNDER the override " \
        f"root {override_root} (resolution must actually happen there -- a default-" \
        f"root fallback would have succeeded silently; got: {msg!r})"


# =========================================================================== #
# ExperimentPreset validation                                                  #
# =========================================================================== #
def test_experiment_preset_validation_killers():
    """Require explicit, immutable presets with one theta convention per preset.

    Both invalid combinations are exercised so validation cannot pass vacuously.
    The two theta conventions remain distinct registered presets with pinned knob
    values and the explicit unit tag ``theta_rad``. Exactly one of
    ``theta_rad`` / ``leakage_rate_target`` is set; the preset is frozen (assignment
    raises); and both registered presets carry their knobs explicitly.
    """
    import dataclasses

    # both conventions set -> raises.
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, leakage_rate_target=_LEAKAGE_RATE_TARGET)
    # neither set -> raises (no silent physics default).
    with pytest.raises(ValueError):
        _mk_preset()
    # a valid single-convention preset builds, and is FROZEN.
    preset = _mk_preset(theta_rad=_THETA_RAW)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        preset.theta_rad = 0.99  # type: ignore[misc]

    # the two REGISTERED presets exist as distinct named cells with pinned knobs.
    raw = experiments.PRESET_LEAK_THETA_0P30
    rate_target = experiments.PRESET_LEAKAGE_RATE_5E3
    assert raw.theta_rad == _THETA_RAW and raw.leakage_rate_target is None, \
        f"RAW preset knobs drifted: theta_rad={raw.theta_rad!r}, " \
        f"leakage_rate_target={raw.leakage_rate_target!r}"
    assert rate_target.leakage_rate_target == _LEAKAGE_RATE_TARGET and rate_target.theta_rad is None, \
        f"rate-target preset knobs drifted: leakage_rate_target=" \
        f"{rate_target.leakage_rate_target!r}, theta_rad={rate_target.theta_rad!r}"
    for p, tag in ((raw, "RAW"), (rate_target, "RATE_TARGET")):
        assert p.g_seep == _G_SEEP, f"{tag} preset g_seep {p.g_seep} != {_G_SEEP}"
        assert p.g_heat == _G_HEAT, f"{tag} preset g_heat {p.g_heat} != {_G_HEAT}"
        assert p.b_bias == _B_BIAS, f"{tag} preset b_bias {p.b_bias} != {_B_BIAS}"
        assert str(p.arm) == _ARM, f"{tag} preset arm {p.arm!r} != {_ARM!r}"
        assert str(p.readout_conv) == _READOUT_CONV, \
            f"{tag} preset readout_conv {p.readout_conv!r} != {_READOUT_CONV!r}"


# =========================================================================== #
# RunSpec construction from registered presets                                 #
# =========================================================================== #
@requires_data
def test_run_spec_from_preset_raw_and_rate_target():
    """Require preset values to produce the declared ``RunSpec`` exactly.

    The raw theta passes through unchanged. The rate-target theta is checked against the
    independent resolver and against the resulting channel rate, rejecting a dead
    passthrough without conflating theta conventions.

    RAW preset: ``RunSpec.theta == theta_rad`` EXACTLY (float identity, contract).
    Rate-target preset: theta resolves through ``solve_exchange_angle_for_leakage_rate`` at the preset's
    g_seep/g_heat; conformance is ALSO checked independently on the exact channel
    rate ``leakage_seepage_rates(theta)[0] == 5e-3`` (the resolver's own registered tolerance is
    1e-10; 1e-8 leaves slack for the bisection terminal bracket).
    """
    from error_coupling_simulator.mechanisms.qutrit_leakage import (
        solve_exchange_angle_for_leakage_rate,
        leakage_seepage_rates,
    )
    from error_coupling_simulator.carrier.within_cycle import RunSpec

    # distinct, non-default run-shape values so the passthrough asserts discriminate
    # (all four differ from the RunSpec defaults AND from each other).
    rs_raw = _run_spec(experiments.PRESET_LEAK_THETA_0P30, N=3, R=2, base_seed=17, m=1)
    assert isinstance(rs_raw, RunSpec)
    assert (rs_raw.N, rs_raw.R, rs_raw.base_seed, rs_raw.m) == (3, 2, 17, 1), \
        f"run-shape knobs (n_shots/n_rounds/seed/m) did not pass through to the " \
        f"RunSpec: (N,R,base_seed,m)=({rs_raw.N},{rs_raw.R},{rs_raw.base_seed}," \
        f"{rs_raw.m}) != (3,2,17,1)"
    assert rs_raw.theta == _THETA_RAW, \
        f"RAW preset theta {rs_raw.theta!r} != theta_rad {_THETA_RAW!r} exactly"
    assert rs_raw.g_seep == _G_SEEP and rs_raw.b == _B_BIAS and rs_raw.arm == _ARM, \
        "RAW preset knobs did not carry into the RunSpec"

    rs_rate = _run_spec(experiments.PRESET_LEAKAGE_RATE_5E3, N=1, R=1)
    assert rs_rate.g_seep == _G_SEEP and rs_rate.b == _B_BIAS and rs_rate.arm == _ARM
    expected = solve_exchange_angle_for_leakage_rate(_LEAKAGE_RATE_TARGET, g_seep=_G_SEEP, g_heat=0.0)
    assert abs(rs_rate.theta - expected) <= 1e-12, \
        f"rate-target preset theta {rs_rate.theta!r} != solve_exchange_angle_for_leakage_rate " \
        f"resolve {expected!r}"
    # independent conformance: the resolved theta actually HITS the registered rate.
    assert abs(leakage_seepage_rates(rs_rate.theta, _G_SEEP, 0.0)[0] - _LEAKAGE_RATE_TARGET) <= 1e-8, \
        "resolved theta does not hit 5e-3 on the exact channel rate"
    # The rate-resolved value must not be a dead passthrough of a raw theta.
    assert rs_rate.theta > 0.0 and abs(rs_rate.theta - _THETA_RAW) > 1e-3, \
        "rate-target preset theta suspiciously equals the raw cell or zero"


# =========================================================================== #
# leak_slice_table equals the fused carrier builder byte-for-byte              #
# =========================================================================== #
@requires_cuda
@requires_data
def test_leak_slice_table_matches_sv_sampler():
    """Require the facade table to equal the fused carrier builder exactly.

    A distinct parameter cell must produce a different table, preventing a cached or
    constant result from satisfying the reference comparison vacuously.

    Gate: ``leak_slice_table`` on the RAW-preset spec equals
    ``FusedWithinCycleSampler.build_within_cycle_leak`` on the SAME spec byte-for-byte
    (``torch.equal`` -- exact, no tolerance); the list form stacks back to the same
    table. The deliberately different high-parameter cell must produce a different
    table.
    """
    from error_coupling_simulator.carrier.within_cycle import FusedWithinCycleSampler

    spec = _run_spec(experiments.PRESET_LEAK_THETA_0P30, N=1, R=1)
    table = _leak_table(spec)
    ref, _ = FusedWithinCycleSampler(device=DEVICE).build_within_cycle_leak(spec)
    assert isinstance(table, torch.Tensor)
    assert tuple(table.shape) == tuple(ref.shape) and table.dim() == 3 \
        and table.shape[-2:] == (3, 3), \
        f"leak table shape {tuple(table.shape)} != builder {tuple(ref.shape)}"
    assert torch.equal(table, ref), \
        "leak_slice_table != fused carrier build_within_cycle_leak byte-for-byte"

    # Both stacked [K,3,3] and list forms are part of the current API.
    lst = _leak_table(spec, stacked=False)
    assert isinstance(lst, (list, tuple)) and len(lst) == int(ref.shape[0])
    assert torch.equal(torch.stack(list(lst)), ref), \
        "list-form leak table does not stack back to the builder table"

    # A distinct cell's table must differ so the spec cannot be ignored.
    spec_hi = _run_spec(_mk_preset(theta_rad=_THETA_HI, g_seep=_G_SEEP_HI), N=1, R=1)
    table_hi = _leak_table(spec_hi)
    require_precondition(tuple(table_hi.shape) == tuple(table.shape),
                         "retained Choi rank differs between the two cells",
                         remedy="re-pick the discriminator cell")
    assert not torch.equal(table_hi, table), \
        "hi-cell leak table == RAW-cell table: the spec is a dead parameter"


@requires_cuda
@requires_data
def test_leak_slice_table_preset_arm_matches_spec_arm():
    """Require preset and derived-spec inputs to build the same leakage table.

    Distinct seep and heat rates ensure that swapping those fields changes the table
    and therefore fails the exact comparison.

    Gate: ``leak_slice_table(PRESET)`` equals ``leak_slice_table(run_spec_from_preset
    (PRESET, n_shots=1, n_rounds=1, seed=0))`` via ``torch.equal`` (exact -- both
    arms route through the same ``build_within_cycle_leak`` implementation).
    """
    preset = experiments.PRESET_LEAK_THETA_0P30
    require_precondition(
        preset.g_seep != preset.g_heat,
        "preset g_seep == g_heat (a seep/heat field swap would be undetectable)",
        remedy="gate on a preset with distinct seep/heat rates")
    table_preset = experiments.leak_slice_table(preset, device=DEVICE)
    spec = experiments.run_spec_from_preset(preset, n_shots=1, n_rounds=1, seed=0)
    table_spec = experiments.leak_slice_table(spec, device=DEVICE)
    assert isinstance(table_preset, torch.Tensor)
    assert torch.equal(table_preset, table_spec), \
        "leak_slice_table(ExperimentPreset) != leak_slice_table(RunSpec from the " \
        "SAME preset): the preset arm drifts from the spec arm"
