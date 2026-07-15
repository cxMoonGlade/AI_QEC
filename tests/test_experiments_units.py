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

# Generated property tests for the preset validation surface.
from hypothesis import given, settings
from hypothesis import strategies as st

# Experiment facade and its module-internal dataset resolver.
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

#: Dataset-root environment variable.
_ENV = "ECS_D3_DATA_ROOT"

#: Explicit registered-preset values used by the regression checks.
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
# _dataset_files(dataset_root)                                                 #
# =========================================================================== #
# NORMAL ---------------------------------------------------------------------
@requires_data
def test_dataset_files_default_root_resolves_four(monkeypatch):
    """No argument or environment override resolves all four shipped files.

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
    """An explicit root rebases all four files while preserving relative layout.

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
    """The environment root is used when the explicit argument is absent.

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
    """An explicit ``dataset_root`` takes precedence over the environment.

    Leg: env = bogus nonexistent root, arg = the real shipped default root -> resolves
    fine. The opposite direction, a bogus argument with a valid environment, is covered by
    ``test_dataset_files_nonexistent_root_raises`` via the arg branch."""
    bogus = tmp_path / "bogus_env_root"
    assert not bogus.exists()
    monkeypatch.setenv(_ENV, str(bogus))
    files = _dataset_files(xp.DEFAULT_DATASET_ROOT)  # arg wins
    r01_circ, _ = xp.default_r01_paths()
    assert files["r01_circ"] == r01_circ and files["r01_circ"].is_file(), \
        "argument root did not take precedence over the bogus environment"


# Empty or whitespace environment override                                    #
def test_dataset_files_empty_env_raises_value_error(monkeypatch):
    """An empty environment override raises instead of falling back.

    A broken shell expansion, ``ECS_D3_DATA_ROOT=""``, must not be
    indistinguishable from an unset variable; otherwise the override path would be
    vacuous. Both an empty string and a whitespace-only string exercise the
    ``strip()`` guard."""
    for bad in ("", "   ", "\t "):
        monkeypatch.setenv(_ENV, bad)
        with pytest.raises(ValueError) as ei:
            _dataset_files(None)
        assert _ENV in str(ei.value), \
            f"empty-env ValueError must NAME {_ENV} (got {str(ei.value)!r})"


@requires_data
def test_dataset_files_empty_env_raises_via_public_caller(monkeypatch):
    """The public loader propagates an empty-environment ``ValueError``.

    requires_data only so the surrounding suite parity holds; the raise fires BEFORE
    any file read, so the dataset is not actually touched."""
    monkeypatch.setenv(_ENV, "")
    with pytest.raises(ValueError) as ei:
        load_xzzx_d3()
    assert _ENV in str(ei.value)


# Override root is not a directory                                             #
def test_dataset_files_nonexistent_root_raises(monkeypatch, tmp_path):
    """A nonexistent explicit root raises ``FileNotFoundError`` naming that root.

    CPU-only: no dataset needed -- the root does not exist, so the ``is_dir()`` check
    fails before any file resolution."""
    bogus = tmp_path / "not_a_dir_root"
    assert not bogus.exists()
    with pytest.raises(FileNotFoundError) as ei:
        _dataset_files(bogus)
    msg = str(ei.value)
    assert str(bogus) in msg, \
        f"FileNotFoundError must NAME the nonexistent root {bogus} (got {msg!r})"
    # Never silently fall back to the default root.
    assert "Refusing to fall back" in msg or "silent fallback" in msg or str(bogus) in msg


# Override root is missing a required file                                     #
@requires_data
def test_dataset_files_partial_root_missing_file_raises(monkeypatch, tmp_path):
    """A partial explicit root reports its missing required file.

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
# load_xzzx_d3(dataset_root=None, *, with_interior_streams=True)               #
# =========================================================================== #
@requires_data
def test_load_xzzx_d3_default_attaches_streams():
    """The default parse attaches the r10 interior streams.

    Reference: the hand ritual -- parse r01 (verify) + attach r10 streams -- kept as
    the independent transcription. The stream count must equal ``n_data`` and be
    non-empty."""
    sched = load_xzzx_d3()  # with_interior_streams=True default
    streams = list(sched.within_cycle_streams)
    require_precondition(len(streams) > 0,
                         "hand-parsed r10 interior streams are empty",
                         remedy="check the shipped r10 patch")
    assert len(streams) == int(sched.n_data), \
        f"streams attached count {len(streams)} != n_data {sched.n_data}"


@requires_data
def test_load_xzzx_d3_no_interior_streams_branch():
    """``with_interior_streams=False`` returns geometry without streams.

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
    """``load_xzzx_d3`` propagates dataset-resolution failures unchanged.

    CPU-only: an empty env raises before any file read."""
    monkeypatch.setenv(_ENV, "   ")
    with pytest.raises(ValueError) as ei:
        load_xzzx_d3()
    assert _ENV in str(ei.value), "load_xzzx_d3 must propagate the empty-env ValueError"


def test_load_xzzx_d3_dataset_root_arg_is_used(tmp_path):
    """The public loader threads ``dataset_root`` to the resolver."""
    bogus = tmp_path / "no_such_dataset_root_xyz"
    with pytest.raises(FileNotFoundError) as ei:
        load_xzzx_d3(dataset_root=str(bogus))
    assert str(bogus) in str(ei.value), \
        "dataset_root argument was ignored (not threaded to _dataset_files)"


# =========================================================================== #
# ExperimentPreset field validation                                            #
# =========================================================================== #
# --- one VALID representative per convention (the passing anchors) -----------
def test_experiment_preset_valid_raw_angle_constructs():
    """A raw-angle preset constructs with no model-rate target."""
    p = _mk_preset(theta_rad=_THETA_RAW)
    assert p.theta_rad == _THETA_RAW and p.wg_l1_target is None


def test_experiment_preset_valid_wg_rate_constructs():
    """A model-rate-target preset constructs with no raw angle."""
    p = _mk_preset(wg_l1_target=_WG_L1_TARGET)
    assert p.wg_l1_target == _WG_L1_TARGET and p.theta_rad is None


# --- empty name --------------------------------------------------------------
def test_experiment_preset_empty_name_raises():
    """An empty preset name raises ``ValueError``."""
    with pytest.raises(ValueError, match="non-empty"):
        _mk_preset(name="", theta_rad=_THETA_RAW)


# --- exactly-one coordinate convention --------------------------------------
def test_experiment_preset_both_conventions_raises():
    """Raw angle and model-rate target cannot be set together."""
    with pytest.raises(ValueError, match="exactly ONE"):
        _mk_preset(theta_rad=_THETA_RAW, wg_l1_target=_WG_L1_TARGET)


def test_experiment_preset_neither_convention_raises():
    """A preset must declare either a raw angle or model-rate target."""
    with pytest.raises(ValueError, match="exactly ONE"):
        _mk_preset()


# --- exchange-angle lower bound ---------------------------------------------
def test_experiment_preset_negative_theta_rad_raises():
    """A negative exchange angle raises ``ValueError``."""
    with pytest.raises(ValueError, match=">= 0"):
        _mk_preset(theta_rad=-0.1)


def test_experiment_preset_theta_rad_zero_passes():
    """Zero is included in the exchange-angle domain."""
    p = _mk_preset(theta_rad=0.0)
    assert p.theta_rad == 0.0


# --- model-rate-target open interval -----------------------------------------
@pytest.mark.parametrize("bad", [0.0, 0.5, 0.6, -0.01])
def test_experiment_preset_wg_l1_target_out_of_open_interval_raises(bad):
    """``wg_l1_target`` uses the open interval ``(0, 0.5)``."""
    with pytest.raises(ValueError, match=r"\(0, 0\.5\)"):
        _mk_preset(wg_l1_target=bad)


@pytest.mark.parametrize("ok", [1e-9, 0.4999])
def test_experiment_preset_wg_l1_target_interior_passes(ok):
    """Values strictly inside ``(0, 0.5)`` pass."""
    p = _mk_preset(wg_l1_target=ok)
    assert p.wg_l1_target == ok


# --- nonnegative seepage and heating rates ----------------------------------
def test_experiment_preset_negative_g_seep_raises():
    """A negative seep rate raises ``ValueError``."""
    with pytest.raises(ValueError, match=">= 0"):
        _mk_preset(theta_rad=_THETA_RAW, g_seep=-1e-9)


def test_experiment_preset_negative_g_heat_raises():
    """A negative heating rate raises ``ValueError`` independently of seepage."""
    with pytest.raises(ValueError, match=">= 0"):
        _mk_preset(theta_rad=_THETA_RAW, g_heat=-1e-9)


def test_experiment_preset_zero_rates_pass():
    """Zero seepage and heating rates are valid."""
    p = _mk_preset(theta_rad=_THETA_RAW, g_seep=0.0, g_heat=0.0)
    assert p.g_seep == 0.0 and p.g_heat == 0.0


# --- readout-bias closed interval -------------------------------------------
@pytest.mark.parametrize("bad", [-0.01, 1.01])
def test_experiment_preset_b_bias_out_of_closed_interval_raises(bad):
    """Readout bias rejects values outside the closed interval ``[0, 1]``."""
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        _mk_preset(theta_rad=_THETA_RAW, b_bias=bad)


@pytest.mark.parametrize("ok", [0.0, 1.0])
def test_experiment_preset_b_bias_closed_edges_pass(ok):
    """Both endpoints of the readout-bias interval are valid."""
    p = _mk_preset(theta_rad=_THETA_RAW, b_bias=ok)
    assert p.b_bias == ok


# --- measurement-arm membership ---------------------------------------------
def test_experiment_preset_bad_arm_raises():
    """An arm outside ``SV_ARMS`` raises ``ValueError``."""
    require_precondition("Z" not in SV_ARMS,
                         "'Z' unexpectedly a valid arm -- pick another invalid token",
                         remedy="update the invalid arm token")
    with pytest.raises(ValueError, match="one of"):
        _mk_preset(theta_rad=_THETA_RAW, arm="Z")


def test_experiment_preset_arm_lowercase_normalizes_and_passes():
    """Arm validation is case-insensitive through ``.upper()``."""
    require_precondition("A" in SV_ARMS and "a" not in SV_ARMS,
                         "SV_ARMS shape changed -- 'a' vs 'A' normalization pin stale",
                         remedy="re-derive the arm normalization case")
    p = _mk_preset(theta_rad=_THETA_RAW, arm="a")
    assert str(p.arm) == "a", "the preset stores the raw arm string; validation upper-cases"


# --- readout-convention membership ------------------------------------------
def test_experiment_preset_bad_readout_conv_raises():
    """A readout convention outside the declared set raises ``ValueError``."""
    require_precondition("raw" not in SV_READOUT_CONVENTIONS,
                         "'raw' unexpectedly a valid readout_conv",
                         remedy="update the invalid readout token")
    with pytest.raises(ValueError, match="one of"):
        _mk_preset(theta_rad=_THETA_RAW, readout_conv="raw")


def test_experiment_preset_readout_conv_is_case_sensitive():
    """Readout-convention membership is case-sensitive, unlike arm validation."""
    require_precondition("BIASED_B" not in SV_READOUT_CONVENTIONS,
                         "readout_conv membership unexpectedly case-insensitive",
                         remedy="re-check the SV_READOUT_CONVENTIONS convention")
    with pytest.raises(ValueError, match="one of"):
        _mk_preset(theta_rad=_THETA_RAW, readout_conv="BIASED_B")


# --- frozen-instance assignment ---------------------------------------------
def test_experiment_preset_is_frozen():
    """A preset is immutable after construction."""
    p = _mk_preset(theta_rad=_THETA_RAW)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        p.theta_rad = 0.99  # type: ignore[misc]


# =========================================================================== #
# Registered preset value checks                                               #
# =========================================================================== #
def test_preset_leak_theta_0p30_value_pins():
    """``PRESET_LEAK_THETA_0P30`` exposes the declared field values."""
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
    """``PRESET_LEAK_WG_L1_5E3`` exposes its declared model-rate target."""
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
    assert l1["source_kind"] == "project_target_with_literature_scale_context"
    assert l1["provenance_kind"] == "project-design"
    assert l1["claim_scope"] == "project_channel_target_only"
    assert [ref["identifier"] for ref in l1["literature_references"]] == [
        "arXiv:2211.04728"]
    assert l1["literature_references"][0]["exact_locator"] == "Fig. 3c"
    assert l1["literature_references"][0]["doi"] == "10.1038/s41567-023-02226-w"
    assert l1["whole_project_channel_supported"] is False
    assert l1["direct_observable_match"] is False
    assert l1["transformation_supported"] is False
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
# resolve_theta(preset)                                                        #
# =========================================================================== #
def test_resolve_theta_raw_angle_passthrough():
    """A raw-angle preset returns ``theta_rad`` unchanged."""
    p = _mk_preset(theta_rad=_THETA_RAW)
    assert resolve_theta(p) == _THETA_RAW


def test_resolve_theta_wg_rate_solves_model_coordinate():
    """A model-rate-target preset solves the project channel coordinate.

    It returns ``solve_theta_for_wg_l1(wg_l1_target, g_seep=, g_heat=)`` at the
    preset's rates and differs from both the raw-angle cell and zero.

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
    # The resolved value is not a dead passthrough of the raw-angle preset.
    assert theta > 0.0 and abs(theta - _THETA_RAW) > 1e-3, \
        "wg-resolved theta suspiciously equals the raw cell or zero"
    # independent: it HITS the registered rate on the exact channel.
    assert abs(wg_rates(theta, _G_SEEP, _G_HEAT)[0] - _WG_L1_TARGET) <= 1e-8, \
        "resolved theta does not hit WG_L1 = 5e-3 on the exact channel rate"


def test_resolve_theta_both_branches_distinct():
    """Raw-angle and model-rate-target branches produce distinct values."""
    raw = resolve_theta(PRESET_LEAK_THETA_0P30)
    wg = resolve_theta(PRESET_LEAK_WG_L1_5E3)
    assert raw == 0.30
    assert wg != raw, "raw and wg conventions resolved to the same theta (dead branch)"


# =========================================================================== #
# run_spec_from_preset                                                         #
# =========================================================================== #
@requires_data
def test_run_spec_from_preset_raw_passthrough():
    """Every run-shape argument and raw preset field reaches the ``RunSpec``.

    The four run-shape values are distinct from the ``RunSpec`` defaults and from
    each other, so a dropped or swapped argument is observable. The raw angle is
    preserved exactly and the remaining physics parameters carry through.

    requires_data: resolves the shipped r01 circuit/metadata paths."""
    rs = run_spec_from_preset(PRESET_LEAK_THETA_0P30, n_shots=3, n_rounds=2,
                              seed=17, m=1)
    assert isinstance(rs, RunSpec)
    assert (rs.N, rs.R, rs.base_seed, rs.m) == (3, 2, 17, 1), \
        f"run-shape did not pass through: (N,R,base_seed,m)=" \
        f"({rs.N},{rs.R},{rs.base_seed},{rs.m}) != (3,2,17,1)"
    assert rs.theta == _THETA_RAW, f"RAW theta {rs.theta!r} != {_THETA_RAW!r}"
    assert rs.g_seep == _G_SEEP and rs.b == _B_BIAS and rs.arm == _ARM \
        and rs.readout_conv == _READOUT_CONV, "physics knobs did not carry"
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
    """The WG preset's theta is model-rate-solved while building the run spec."""
    from error_coupling_simulator.mechanisms.qutrit_leakage import (
        solve_theta_for_wg_l1,
    )
    rs = run_spec_from_preset(PRESET_LEAK_WG_L1_5E3, n_shots=1, n_rounds=1, seed=0)
    expected = solve_theta_for_wg_l1(_WG_L1_TARGET, g_seep=_G_SEEP, g_heat=_G_HEAT)
    assert abs(rs.theta - expected) <= 1e-12
    assert rs.theta > 0.0 and abs(rs.theta - _THETA_RAW) > 1e-3, \
        "wg run-spec theta equals the raw cell or zero"
    provenance = rs.numerical_provenance
    assert provenance is not None
    resolved = provenance["run_binding"]["resolved_theta_rad"]
    assert resolved["value"] == pytest.approx(expected)
    assert resolved["provenance_kind"] == "project-design"
    assert resolved["claims_device_calibration"] is False


@requires_data
def test_run_spec_from_preset_m_default_vs_explicit():
    """Both the default and explicit logical-input values reach the run spec."""
    rs0 = run_spec_from_preset(PRESET_LEAK_THETA_0P30, n_shots=1, n_rounds=1, seed=0)
    rs1 = run_spec_from_preset(PRESET_LEAK_THETA_0P30, n_shots=1, n_rounds=1, seed=0,
                               m=1)
    assert rs0.m == 0 and rs1.m == 1, f"m plumbing dead: {rs0.m}, {rs1.m}"


def test_run_spec_from_preset_propagates_bogus_root(tmp_path):
    """The run-spec builder propagates dataset-resolution failures unchanged.

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
# leak_slice_table(preset_or_params, *, device, as_list=False)                 #
# =========================================================================== #
# Wrong-type input raises before GPU work                                     #
@pytest.mark.parametrize("bad", [None, {"theta": 0.3}, 0.30, "preset", [1, 2, 3]])
def test_leak_slice_table_wrong_type_raises_type_error(bad):
    """A value that is neither ``ExperimentPreset`` nor ``RunSpec`` raises.

    CPU-only: the ``isinstance`` chain runs before carrier construction or GPU
    work. ``device`` is passed but never reached on this path."""
    with pytest.raises(TypeError) as ei:
        leak_slice_table(bad, device=DEVICE)
    assert type(bad).__name__ in str(ei.value), \
        f"TypeError must NAME the received type {type(bad).__name__} (got {str(ei.value)!r})"


def test_leak_slice_table_type_guard_is_live_control():
    """The type guard trips on an explicit wrong-type corruption input.

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


# The stacked and list builder routes require CUDA. These tests check routing and
# return shape without re-deriving the builder's CPTP/composition assertions.
@requires_cuda
@requires_data
def test_leak_slice_table_preset_arm_stacked_shape():
    """The preset route returns a stacked ``(n_kraus, 3, 3)`` device tensor.

    requires_cuda: ``build_within_cycle_leak`` is GPU-hosted."""
    import torch
    table = leak_slice_table(PRESET_LEAK_THETA_0P30, device=DEVICE)
    assert isinstance(table, torch.Tensor)
    assert table.dim() == 3 and tuple(table.shape[-2:]) == (3, 3), \
        f"preset-arm table shape {tuple(table.shape)} not (n_kraus, 3, 3)"


@requires_cuda
@requires_data
def test_leak_slice_table_as_list_return_shape():
    """The list form stacks back to the tensor form.

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
    """Preset and run-spec routes produce the same leakage table.

    A distinct parameter cell is also required to change the result.

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
        "preset arm != RunSpec-from-same-preset arm"
    # A grossly different cell must change the table; the result is not cached constant.
    t_hi = leak_slice_table(_mk_preset(theta_rad=_THETA_HI, g_seep=_G_SEEP_HI),
                            device=DEVICE)
    require_precondition(tuple(t_hi.shape) == tuple(t_preset.shape),
                         "retained Choi rank differs between cells",
                         remedy="re-pick the discriminator cell")
    assert not torch.equal(t_hi, t_preset), \
        "hi-cell table == RAW-cell table: the spec is a dead parameter"


# =========================================================================== #
# Generated properties for ExperimentPreset validation                         #
# =========================================================================== #
# Generated in-range configurations construct, while an out-of-range value on any
# single field raises. Hypothesis shrinks failures to a minimal counterexample.
# These CPU-only tests use the raw-angle convention as the base so exactly one
# parameter convention holds by construction, then push one field out of range.

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
    """Any raw-angle configuration with every field in range constructs."""
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
    """Any strictly negative ``theta_rad`` raises ``ValueError``.

    Hypothesis shrinks to the minimal
    counterexample if the strict-``< 0`` boundary ever drifts."""
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=bad_theta)


@settings(max_examples=200)
@given(bad_rate=st.one_of(
    st.floats(max_value=0.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.5, max_value=1e6, allow_nan=False, allow_infinity=False)))
def test_property_wg_l1_target_out_of_open_interval_always_raises(bad_rate):
    """Any model-rate target less than or equal to zero or at least 0.5
    raises. Covers the STRICT open-interval convention over a generated range (the
    edges 0.0 and 0.5 included, being non-strict-min/max of the two sub-strategies)."""
    with pytest.raises(ValueError):
        _mk_preset(wg_l1_target=bad_rate)


@settings(max_examples=200)
@given(bad=st.floats(max_value=-1e-9, allow_nan=False, allow_infinity=False))
def test_property_negative_rate_always_raises(bad):
    """Any strictly negative seepage or heat rate raises."""
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
    """Any readout bias strictly below zero or strictly above 1 raises.

    Pins the closed-interval convention (the edges 0.0/1.0
    are excluded from both sub-strategies, so they are never generated as failures)."""
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, b_bias=bad_b)


@settings(max_examples=100)
@given(bad_arm=st.text(min_size=1, max_size=6).filter(
    lambda s: str(s).upper() not in SV_ARMS))
def test_property_bad_arm_always_raises(bad_arm):
    """Any string whose uppercase form is not in ``SV_ARMS`` raises.

    The ``.upper()`` normalization is baked into the filter, so the
    property respects the (deliberate) case-insensitive arm convention."""
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, arm=bad_arm)


@settings(max_examples=100)
@given(bad_conv=st.text(min_size=1, max_size=8).filter(
    lambda s: str(s) not in SV_READOUT_CONVENTIONS))
def test_property_bad_readout_conv_always_raises(bad_conv):
    """Any string not exactly in ``SV_READOUT_CONVENTIONS`` raises.

    Membership is case-sensitive; unlike the arm field, no ``.upper()``
    normalization is applied here."""
    with pytest.raises(ValueError):
        _mk_preset(theta_rad=_THETA_RAW, readout_conv=bad_conv)
