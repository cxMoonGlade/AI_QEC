"""d3 XZZX experiment presets + run-spec facade (the product experiment entry point).

GLOSSARY -- *preset*: a named, FROZEN, REGISTERED experiment configuration
(:class:`ExperimentPreset`). A preset is the public replacement for the test-suite
"cell" ritual: every physics knob (leak angle or leak-rate target, seepage/heating
rates, leaked-readout bias, measurement-instrument arm, terminal-readout convention)
is EXPLICIT on the preset -- there are NO silent physics defaults (the registered-sweep
rule: knobs are always explicit per registered configuration, never defaulted to a
headline point). Presets are module-level frozen dataclass instances; adding one is a
REGISTRATION event (name it, pin every knob, commit it), never an ad-hoc mutation.

THE TWO THETA CONVENTIONS ARE TWO DISTINCT PRESETS (never a merged default):

* :data:`PRESET_LEAK_THETA_0P30` -- the RAW-ANGLE convention: the Wood-Gambetta
  coherent |1><->|2> exchange angle ``theta_rad`` is pinned directly (0.30 rad).
* :data:`PRESET_LEAK_WG_L1_5E3` -- the MODEL-RATE-SOLVED convention: ``theta_rad`` is
  SOLVED so the exact project WG channel's per-cycle leak rate ``WG_L1`` hits the
  registered target (5.0e-3, a single-paper magnitude anchor from Miao) via
  :func:`~error_coupling_simulator.mechanisms.qutrit_leakage.solve_theta_for_wg_l1`
  (a monotone model-rate solver, not device calibration).

Neither preset is a paper-validated physical cell. ``theta_rad=0.30``, ``g_heat=0``,
``b_bias=0.9``, arm A, and ``biased_b`` are registered project choices;
``WG_L1=5e-3`` and ``g_seep=0.09`` have separate Miao/McEwen scale context from
different devices/protocols. Their composition is a synthetic benchmark. In
particular, ``b_bias=0.9`` is one registered synthetic nuisance point, not a measured
readout magnitude; physical conclusions must bracket the exported
``LEAKED_READOUT_BIAS_SWEEP = (0.5, 0.75, 1.0)``.

Exactly ONE of ``theta_rad`` / ``wg_l1_target`` is set on any preset (validated);
:func:`resolve_theta` maps either convention to the operative angle.

DATASET RESOLUTION (fail closed). :func:`load_xzzx_d3` / :func:`run_spec_from_preset`
resolve the caller-supplied Google ``d3_at_q6_7`` patch as a GEOMETRY/SCHEDULE source only through
``error_coupling_simulator.frontend.xzzx_parser.default_r01_paths`` /
``default_r10_paths``
(layout: ``<root>/<patch>/<basis>/<r01|r10>/{circuit_ideal.stim, metadata.json}``).
Root precedence: the ``dataset_root`` argument > the ``ECS_D3_DATA_ROOT`` env var
(if the key is SET) > the parser's built-in ``DEFAULT_DATASET_ROOT`` (env key
ABSENT only). A SET-but-empty/whitespace ``ECS_D3_DATA_ROOT`` raises
:class:`ValueError` (fail loud: a broken shell expansion must never be
indistinguishable from unset). A nonexistent override root or a missing file
raises :class:`FileNotFoundError` NAMING the missing path -- NEVER a silent
fallback to the default root (a fallback would make every env-override probe
vacuous: the run would "pass" on the wrong data).

Current ownership and external-input rules are binding in ``docs/SIMULATOR.md``,
this module's README, and the registered frontend tests.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from error_coupling_simulator.mechanisms.qutrit_leakage import (
    LEAKED_READOUT_BIAS_SWEEP,
    solve_theta_for_wg_l1,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    import torch
    from error_coupling_simulator.carrier.within_cycle import RunSpec

    from .xzzx_parser import XZZXSchedule

__all__ = [
    "ExperimentPreset",
    "LEAKED_READOUT_BIAS_SWEEP",
    "PRESET_LEAK_THETA_0P30",
    "PRESET_LEAK_WG_L1_5E3",
    "leak_slice_table",
    "load_xzzx_d3",
    "resolve_theta",
    "run_spec_from_preset",
]

#: Dataset-root override env var (ratified decision 7 of the ownership contract).
ECS_D3_DATA_ENV = "ECS_D3_DATA_ROOT"

#: Stable compatibility vocabulary used by the frozen preset contract.  These values
#: are package-local so importing/validating a preset does not load the GPU carrier.
#: The lazy runtime adapter verifies exact equality with the active carrier before use.
SV_ARMS: tuple[str, ...] = ("A", "C", "B1", "B2")
SV_READOUT_CONVENTIONS: tuple[str, ...] = ("biased_b", "half")
RUN_PURPOSES: tuple[str, ...] = ("optimization", "final", "certification")
PRECISION_POLICY = "optimization_c64_final_certification_c128_v1"
_RUN_PURPOSE_DTYPE = {
    "optimization": "c64",
    "final": "c128",
    "certification": "c128",
}
_RUN_PURPOSE_EVIDENCE = {
    "optimization": "screening_only",
    "final": "c128_candidate",
    "certification": "c128_candidate",
}

#: The four required external d3_at_q6_7 files, keyed by logical name (the same logical names
#: used by the test dataset probe and test-only mask hook).
_D3_LOGICAL_NAMES = ("r01_circ", "r01_meta", "r10_circ", "r10_meta")


def _xzzx_parser():
    """Load the package-local dataset parser only for dataset/schedule operations."""
    from . import xzzx_parser

    return xzzx_parser


def _sv_runtime():
    """Load the package-local carrier host only for run/leak operations."""
    from error_coupling_simulator.carrier.within_cycle import (
        SV_ARMS as carrier_arms,
        SV_READOUT_CONVENTIONS as carrier_readout_conventions,
        PRECISION_POLICY as carrier_precision_policy,
        RUN_PURPOSES as carrier_run_purposes,
        FusedWithinCycleSampler,
        RunSpec,
        _bind_registered_numerical_provenance,
    )

    if tuple(carrier_arms) != SV_ARMS:
        raise RuntimeError(
            "carrier arm vocabulary drifted from the experiments contract: "
            f"expected {SV_ARMS}, got {tuple(carrier_arms)}")
    if tuple(carrier_readout_conventions) != SV_READOUT_CONVENTIONS:
        raise RuntimeError(
            "carrier readout vocabulary drifted from the experiments contract: "
            f"expected {SV_READOUT_CONVENTIONS}, "
            f"got {tuple(carrier_readout_conventions)}")
    if tuple(carrier_run_purposes) != RUN_PURPOSES:
        raise RuntimeError(
            "carrier run-purpose vocabulary drifted from the experiments contract: "
            f"expected {RUN_PURPOSES}, got {tuple(carrier_run_purposes)}")
    if str(carrier_precision_policy) != PRECISION_POLICY:
        raise RuntimeError(
            "carrier precision policy drifted from the experiments contract: "
            f"expected {PRECISION_POLICY!r}, got {carrier_precision_policy!r}")
    return RunSpec, FusedWithinCycleSampler, _bind_registered_numerical_provenance


def _precision_for_purpose(purpose: str) -> tuple[str, str]:
    key = str(purpose)
    if key not in RUN_PURPOSES:
        raise ValueError(
            f"run_purpose must be one of {RUN_PURPOSES} (got {purpose!r})")
    return _RUN_PURPOSE_DTYPE[key], _RUN_PURPOSE_EVIDENCE[key]


def _dataset_files(dataset_root: "str | Path | None") -> "dict[str, Path]":
    """Resolve the four external ``d3_at_q6_7`` files (r01/r10 circuit + metadata).

    Root precedence: ``dataset_root`` argument > ``ECS_D3_DATA_ROOT`` env var (if the
    key is SET; SET-but-empty/whitespace raises :class:`ValueError`, fail loud) > the
    parser's built-in ``DEFAULT_DATASET_ROOT`` (env key absent only). The default
    paths are BUILT by
    ``default_r01_paths()`` / ``default_r10_paths()`` as
    ``DEFAULT_DATASET_ROOT / patch / basis / rXX / file``; an override root is applied
    by REBASING those exact paths (``path.relative_to(DEFAULT_DATASET_ROOT)`` onto the
    override root), so this facade never re-derives the patch/basis layout and cannot
    drift from the parser's.

    Every resolved file is existence-checked. A nonexistent override root, or any
    missing file, raises :class:`FileNotFoundError` naming the offending path --
    NEVER a silent fallback to the default root: a fallback would make the check vacuous
    by allowing an environment-override run to read the wrong data and still "pass".
    """
    xp = _xzzx_parser()
    root: "Path | None"
    if dataset_root is not None:
        root, source = Path(dataset_root), "dataset_root argument"
    elif ECS_D3_DATA_ENV in os.environ:
        # SET-but-empty/whitespace is a distinct, LOUD error: a broken shell
        # expansion (e.g. ECS_D3_DATA_ROOT="$UNSET_VAR") would otherwise be
        # indistinguishable from unset and silently fall back to the default
        # root -- exactly the silent-fallback class this module forbids.
        env_root = os.environ[ECS_D3_DATA_ENV].strip()
        if not env_root:
            raise ValueError(
                f"env var {ECS_D3_DATA_ENV} is SET but empty/whitespace; "
                f"empty values are not allowed (a broken shell expansion would "
                f"be indistinguishable from unset). Unset it to use the default "
                f"root {xp.DEFAULT_DATASET_ROOT}, or set it to a real dataset "
                f"root. Never falling back silently.")
        root, source = Path(env_root), f"env {ECS_D3_DATA_ENV}"
    else:
        root, source = None, f"default root {xp.DEFAULT_DATASET_ROOT}"

    r01_circ, r01_meta = xp.default_r01_paths()
    r10_circ, r10_meta = xp.default_r10_paths()
    files: "dict[str, Path]" = {
        "r01_circ": r01_circ, "r01_meta": r01_meta,
        "r10_circ": r10_circ, "r10_meta": r10_meta,
    }
    if root is not None:
        if not root.is_dir():
            raise FileNotFoundError(
                f"d3 dataset root {root} ({source}) does not exist or is not a "
                f"directory. Refusing to fall back to the default root "
                f"{xp.DEFAULT_DATASET_ROOT} (a silent fallback would make the "
                f"override vacuous).")
        files = {name: root / p.relative_to(xp.DEFAULT_DATASET_ROOT)
                 for name, p in files.items()}
    missing = [f"{name}: {files[name]}" for name in _D3_LOGICAL_NAMES
               if not files[name].is_file()]
    if missing:
        raise FileNotFoundError(
            f"external d3_at_q6_7 file(s) missing (root from {source}): "
            f"{missing}. Never falling back to the default root.")
    return files


def load_xzzx_d3(dataset_root: "str | Path | None" = None, *,
                 with_interior_streams: bool = True) -> "XZZXSchedule":
    """Parse an external Google d3 XZZX schedule: r01 geometry (+ r10 interior streams).

    The two inputs have explicit roles: the r01 instance supplies
    the VERIFIED code geometry (``parse_xzzx_circuit(verify=True)``: 17 qubits /
    8 detectors, two-method stabilizer self-check), and -- when
    ``with_interior_streams=True`` (default) -- the MULTI-ROUND r10 instance supplies
    the per-qutrit within-cycle INTERIOR token streams
    (``sched.with_within_cycle_streams(parse_within_cycle_streams(r10))``; r01's single
    round is first+terminal, not a clean interior round, so r01 alone cannot provide
    them). The active within-cycle carrier
    (``FusedWithinCycleSampler.marshal_within_cycle``) REQUIRES the streams; pass
    ``with_interior_streams=False`` only for geometry-only consumers.

    These Google assets supply geometry and schedule/token streams only. This facade
    does not consume their measurement records or SI1000 noisy circuit and does not
    infer, fit, or validate any preset noise coordinate from them.

    ``dataset_root`` overrides the dataset location (argument > ``ECS_D3_DATA_ROOT``
    env var > the parser default); a missing root/file raises
    :class:`FileNotFoundError` naming it -- never a silent fallback (see
    :func:`_dataset_files`).
    """
    xp = _xzzx_parser()
    files = _dataset_files(dataset_root)
    sched = xp.parse_xzzx_circuit(files["r01_circ"], files["r01_meta"], verify=True)
    if with_interior_streams:
        sched = sched.with_within_cycle_streams(
            xp.parse_within_cycle_streams(files["r10_circ"], files["r10_meta"]))
    return sched


@dataclass(frozen=True, kw_only=True)
class ExperimentPreset:
    """A named, frozen, REGISTERED experiment configuration (GLOSSARY: *preset*).

    Exactly ONE of ``theta_rad`` / ``wg_l1_target`` is set (validated): the two theta
    conventions -- raw-angle vs model-rate-solved -- are DISTINCT presets, never merged
    into one default. All physics knobs are REQUIRED (no silent physics defaults, the
    registered-sweep rule): ``g_seep`` / ``g_heat`` (WG dissipative seep/heat rates),
    ``b_bias`` (leaked-readout bias ``b`` in [0, 1]), ``arm`` (measurement-instrument
    arm, one of ``SV_ARMS``), ``readout_conv`` (terminal-readout convention, one of
    ``SV_READOUT_CONVENTIONS``).

    Units / conventions (N-4): ``theta_rad`` is the WG coherent |1><->|2> exchange
    angle in RADIANS; ``wg_l1_target`` is the per-cycle WG_L1 leak probability the
    angle is numerically solved to hit inside the project channel (dimensionless, in
    (0, 0.5)); this is not device calibration.

    ``provenance_manifest`` is optional for caller-defined presets to preserve the
    existing constructor API, but caller-supplied metadata is never trusted to upgrade
    a run's claim scope. Only the exact module-registered preset objects are bound to
    private canonical manifest snapshots. The field is excluded from equality and
    hashing so auditable metadata does not change preset identity semantics.
    """

    name: str
    theta_rad: "float | None" = None
    wg_l1_target: "float | None" = None
    g_seep: float
    g_heat: float
    b_bias: float
    arm: str
    readout_conv: str
    provenance_manifest: "dict[str, object] | None" = field(
        default=None, compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        if not str(self.name):
            raise ValueError("preset name must be a non-empty string")
        if (self.theta_rad is None) == (self.wg_l1_target is None):
            raise ValueError(
                f"preset {self.name!r}: exactly ONE of theta_rad / wg_l1_target must "
                f"be set (got theta_rad={self.theta_rad}, "
                f"wg_l1_target={self.wg_l1_target}); the two theta conventions are "
                f"distinct presets, never merged")
        if self.theta_rad is not None and float(self.theta_rad) < 0.0:
            raise ValueError(f"preset {self.name!r}: theta_rad must be >= 0 "
                             f"(got {self.theta_rad})")
        if self.wg_l1_target is not None and not 0.0 < float(self.wg_l1_target) < 0.5:
            raise ValueError(f"preset {self.name!r}: wg_l1_target must lie in (0, 0.5) "
                             f"(got {self.wg_l1_target})")
        if float(self.g_seep) < 0.0 or float(self.g_heat) < 0.0:
            raise ValueError(f"preset {self.name!r}: g_seep/g_heat must be >= 0 "
                             f"(got {self.g_seep}, {self.g_heat})")
        if not 0.0 <= float(self.b_bias) <= 1.0:
            raise ValueError(f"preset {self.name!r}: b_bias must be in [0, 1] "
                             f"(got {self.b_bias})")
        if str(self.arm).upper() not in SV_ARMS:
            raise ValueError(f"preset {self.name!r}: arm must be one of {SV_ARMS} "
                             f"(got {self.arm!r})")
        if str(self.readout_conv) not in SV_READOUT_CONVENTIONS:
            raise ValueError(
                f"preset {self.name!r}: readout_conv must be one of "
                f"{SV_READOUT_CONVENTIONS} (got {self.readout_conv!r})")


def _registered_qutrit_preset(*, name: str, theta_rad: "float | None" = None,
                              wg_l1_target: "float | None" = None,
                              g_seep: float, g_heat: float, b_bias: float,
                              arm: str, readout_conv: str) -> ExperimentPreset:
    """Build one registered synthetic preset and its JSON-safe provenance manifest."""
    values: "dict[str, object]" = {
        "name": name,
        "theta_rad": theta_rad,
        "wg_l1_target": wg_l1_target,
        "g_seep": g_seep,
        "g_heat": g_heat,
        "b_bias": b_bias,
        "arm": arm,
        "readout_conv": readout_conv,
    }

    def entry(field_name: str, *, provenance_kind: str, source_kind: str, claim_scope: str,
              literature_references: "list[dict[str, object]] | None" = None,
              **extra: object) -> "dict[str, object]":
        return {
            "value": values[field_name],
            "provenance_kind": provenance_kind,
            "source_kind": source_kind,
            "claim_scope": claim_scope,
            "literature_references": literature_references or [],
            "device_calibrated": False,
            **extra,
        }

    miao_l1 = {
        "source": "Miao et al., Overcoming leakage in quantum error correction",
        "publication": "Nature Physics 19 (2023)",
        "identifier": "arXiv:2211.04728",
        "doi": "10.1038/s41567-023-02226-w",
        "exact_locator": "Fig. 3c",
        "reported_value": "approximately 5e-3 leakage generated per cycle",
        "device_protocol_scope": "reported DQLR surface-code experiment only",
        "transformation_to_field": (
            "no identity transform: approximate cross-observable scale context only"),
        "supports_only": (
            "approximately 5e-3 leakage generated per cycle in the reported "
            "device/protocol"),
    }
    mcewen_seep = {
        "source": (
            "McEwen et al., Removing leakage-induced correlated errors in "
            "superconducting quantum error correction"),
        "publication": "Nature Communications 12 (2021)",
        "identifier": "arXiv:2102.06131",
        "doi": "10.1038/s41467-021-21982-y",
        "exact_locator": "Supplementary Table S1",
        "reported_value": "8.1-9.1 percent per-round no-reset gamma_down scale",
        "device_protocol_scope": "reported bit-flip-code experiment only",
        "transformation_to_field": (
            "cross-device approximate magnitude mapping to project g_seep; not a fit"),
        "supports_only": (
            "approximately 8.1-9.1 percent per-round no-reset seepage scale in "
            "the reported bit-flip-code protocol"),
    }
    fields = {
        "name": entry(
            "name", provenance_kind="project-design", source_kind="project_registration",
            claim_scope="identifier_only"),
        "theta_rad": entry(
            "theta_rad",
            provenance_kind="project-design",
            source_kind=("project_design_point" if theta_rad is not None
                         else "not_applicable_model_rate_coordinate"),
            claim_scope=("synthetic_raw_angle_only" if theta_rad is not None
                         else "not_applicable"),
            magnitude_supported_by_literature=False),
        "wg_l1_target": entry(
            "wg_l1_target",
            provenance_kind="project-design",
            source_kind=("project_target_with_literature_scale_context"
                         if wg_l1_target is not None
                         else "not_applicable_raw_angle_coordinate"),
            claim_scope=("project_channel_target_only"
                         if wg_l1_target is not None else "not_applicable"),
            literature_references=([miao_l1] if wg_l1_target is not None else []),
            whole_project_channel_supported=False,
            direct_observable_match=False,
            transformation_supported=False),
        "g_seep": entry(
            "g_seep", provenance_kind="project-design",
            source_kind="cross_device_scale_anchor",
            claim_scope="project_channel_coordinate_near_reported_seepage_scale_only",
            literature_references=[mcewen_seep],
            direct_parameter_fit=False),
        "g_heat": entry(
            "g_heat", provenance_kind="project-design",
            source_kind="project_ablation_choice",
            claim_scope="synthetic_no_heating_simplification_only"),
        "b_bias": entry(
            "b_bias", provenance_kind="project-design",
            source_kind="registered_synthetic_nuisance_point",
            claim_scope="synthetic_nuisance_sweep_point_only",
            literature_references=[],
            magnitude_supported_by_literature=False,
            required_sweep=list(LEAKED_READOUT_BIAS_SWEEP)),
        "arm": entry(
            "arm", provenance_kind="project-design",
            source_kind="project_instrument_choice",
            claim_scope="synthetic_measurement_instrument_only"),
        "readout_conv": entry(
            "readout_conv", provenance_kind="project-design",
            source_kind="project_readout_convention",
            claim_scope="synthetic_terminal_readout_convention_only"),
    }
    manifest: "dict[str, object]" = {
        "schema": "error_coupling_simulator.frontend.experiment_preset_provenance.v1",
        "preset_name": name,
        "whole_preset": {
            "provenance_kind": "project-design",
            "claim_scope": "registered_synthetic_cross_source_benchmark_only",
            "device_calibrated": False,
            "physical_cell_validated_by_literature": False,
            "direct_whole_cell_literature_support_count": 0,
            "reason": (
                "separate papers anchor separate scales; no source validates "
                "their composition with project-only coordinates"),
        },
        "fields": fields,
        "required_leaked_readout_bias_sweep": list(LEAKED_READOUT_BIAS_SWEEP),
        "dataset_source": {
            "asset": "Google d3_at_q6_7 X patch",
            "provenance_kind": "dataset-measured",
            "claim_scope": "geometry_and_schedule_only",
            "files_used": ["circuit_ideal.stim", "metadata.json"],
            "supplies_physical_noise_parameters": False,
            "uses_measurements_b8": False,
            "uses_circuit_noisy_si1000": False,
        },
    }
    return ExperimentPreset(
        name=name, theta_rad=theta_rad, wg_l1_target=wg_l1_target,
        g_seep=g_seep, g_heat=g_heat, b_bias=b_bias, arm=arm,
        readout_conv=readout_conv, provenance_manifest=manifest)


#: RAW-ANGLE convention: 0.30 rad is a registered synthetic strong-angle point.
#: The remaining coordinates are explicit project/cross-source choices recorded in
#: ``provenance_manifest``; together they are not a paper-validated physical cell.
PRESET_LEAK_THETA_0P30 = _registered_qutrit_preset(
    name="leak_theta_0p30", theta_rad=0.30, g_seep=0.09, g_heat=0.0,
    b_bias=0.9, arm="A", readout_conv="biased_b")

#: MODEL-RATE-SOLVED convention: 5.0e-3 is a Miao magnitude anchor, while 0.09
#: separately uses a McEwen seepage-scale anchor. The other coordinates, including
#: b=0.9, are project choices. This cross-source composition is a synthetic benchmark,
#: not a device-calibrated or literature-validated physical cell.
PRESET_LEAK_WG_L1_5E3 = _registered_qutrit_preset(
    name="leak_wg_l1_5e3", wg_l1_target=5.0e-3, g_seep=0.09, g_heat=0.0,
    b_bias=0.9, arm="A", readout_conv="biased_b")


_REGISTERED_PRESET_MANIFEST_SNAPSHOTS = tuple(
    (preset, json.dumps(preset.provenance_manifest, sort_keys=True))
    for preset in (PRESET_LEAK_THETA_0P30, PRESET_LEAK_WG_L1_5E3)
)


def _canonical_registered_manifest(
        preset: ExperimentPreset) -> "dict[str, object] | None":
    """Return a fresh, validated manifest only for an exact registered object.

    The JSON strings above are immutable snapshots taken at module import. We never
    trust ``preset.provenance_manifest`` here: a frozen dataclass does not make a nested
    dict immutable, and a caller-defined preset may contain arbitrary metadata.
    """
    manifest_json = next(
        (snapshot for registered, snapshot in _REGISTERED_PRESET_MANIFEST_SNAPSHOTS
         if preset is registered),
        None,
    )
    if manifest_json is None:
        return None
    manifest = json.loads(manifest_json)
    if manifest.get("schema") != \
            "error_coupling_simulator.frontend.experiment_preset_provenance.v1":
        raise RuntimeError("registered preset manifest has an invalid schema")
    fields = manifest.get("fields")
    expected_fields = (
        "name", "theta_rad", "wg_l1_target", "g_seep", "g_heat",
        "b_bias", "arm", "readout_conv",
    )
    if not isinstance(fields, dict) or set(fields) != set(expected_fields):
        raise RuntimeError("registered preset manifest field set is corrupt")
    for field_name in expected_fields:
        entry = fields[field_name]
        if not isinstance(entry, dict) or entry.get("value") != getattr(preset, field_name):
            raise RuntimeError(
                f"registered preset manifest value mismatch for {field_name}")
    return manifest


def resolve_theta(preset: ExperimentPreset) -> float:
    """The operative WG exchange angle (radians) for a preset.

    Raw-angle convention: returns the pinned ``theta_rad``. Model-rate-solved
    convention: returns ``solve_theta_for_wg_l1(wg_l1_target, g_seep=...,
    g_heat=...)`` -- the monotone bisection on the EXACT WG channel rate (the same
    import + call shape the L-soft gates use), so the preset's ``g_seep``/``g_heat``
    participate exactly as registered. This solves a project-model coordinate; it
    does not calibrate a device or validate the composed
    preset as a physical cell.
    """
    if preset.theta_rad is not None:
        return float(preset.theta_rad)
    return float(solve_theta_for_wg_l1(
        float(preset.wg_l1_target),
        g_seep=float(preset.g_seep), g_heat=float(preset.g_heat)))


def run_spec_from_preset(preset: ExperimentPreset, *, n_shots: int, n_rounds: int,
                         seed: int, m: int = 0,
                         run_purpose: str = "final",
                         dataset_root: "str | Path | None" = None) -> RunSpec:
    """Build the package-local fused-carrier :class:`RunSpec` for a preset.

    Every run-shape knob is an EXPLICIT keyword (``n_shots``/``n_rounds``/``seed``;
    ``m`` is the prepared logical); every physics knob comes from the preset (theta
    resolved via :func:`resolve_theta` -- the wg_l1 form is model-rate-solved here); the
    circuit/metadata paths are the resolved external r01 instance (the R>1 engine
    reuses the r01 geometry -- attach the r10 interior streams via
    :func:`load_xzzx_d3` when driving a within-cycle carrier). No hidden knobs:
    precision is purpose-derived and cannot be selected independently:
    ``optimization -> c64`` while ``final|certification -> c128``.  Optimization
    artifacts are screening-only; a frozen c128 replay is required before evidence
    use. Everything else is validated by ``RunSpec.__post_init__``. The Google r01
    paths supply geometry and schedule only; no preset noise coordinate is inferred
    from those assets.
    """
    files = _dataset_files(dataset_root)
    theta = resolve_theta(preset)
    dtype, evidence_eligibility = _precision_for_purpose(run_purpose)
    canonical_manifest = _canonical_registered_manifest(preset)
    if canonical_manifest is None:
        numerical_provenance: "dict[str, object]" = {
            "schema": "error_coupling_simulator.frontend.run_numerical_provenance.v1",
            "status": "missing",
            "claim_scope": "implementation_only",
            "reason": (
                "preset is not an exact module-registered object; caller-supplied "
                "provenance metadata is not trusted"),
        }
    else:
        canonical_json = json.dumps(
            canonical_manifest, sort_keys=True, separators=(",", ":"))
        numerical_provenance = {
            "schema": "error_coupling_simulator.frontend.run_numerical_provenance.v1",
            "status": "complete_for_registered_preset",
            "claim_scope": "registered_synthetic_cross_source_benchmark_only",
            "preset_manifest": canonical_manifest,
            "preset_manifest_sha256": hashlib.sha256(
                canonical_json.encode("utf-8")).hexdigest(),
        }
    numerical_provenance["run_binding"] = {
        "resolved_theta_rad": {
            "value": theta,
            "provenance_kind": (
                "project-design"),
            "transformation": (
                "identity_from_registered_theta_rad"
                if preset.theta_rad is not None
                else "project_WG_channel_bisection_to_registered_wg_l1_target"),
            "claims_device_calibration": False,
        },
        "dataset_files": {
            "circuit": str(files["r01_circ"]),
            "metadata": str(files["r01_meta"]),
            "claim_scope": "geometry_and_schedule_only",
            "supplies_physical_noise_parameters": False,
        },
        "run_shape": {
            "n_shots": int(n_shots),
            "n_rounds": int(n_rounds),
            "seed": int(seed),
            "logical_input_m": int(m),
            "provenance_kind": "project-design",
        },
        "precision": {
            "policy": PRECISION_POLICY,
            "run_purpose": str(run_purpose),
            "dtype": dtype,
            "evidence_eligibility": evidence_eligibility,
        },
    }
    run_spec_cls, _sampler_cls, bind_registered_provenance = _sv_runtime()
    spec = run_spec_cls(
        circuit_path=files["r01_circ"],
        metadata_path=files["r01_meta"],
        m=int(m),
        theta=theta,
        g_seep=float(preset.g_seep),
        g_heat=float(preset.g_heat),
        arm=str(preset.arm),
        b=float(preset.b_bias),
        readout_conv=str(preset.readout_conv),
        N=int(n_shots),
        base_seed=int(seed),
        R=int(n_rounds),
        dtype=dtype,
        run_purpose=str(run_purpose),
        numerical_provenance=(
            None if canonical_manifest is not None else numerical_provenance),
    )
    if canonical_manifest is not None:
        return bind_registered_provenance(spec, numerical_provenance)
    return spec


def leak_slice_table(preset_or_params: "ExperimentPreset | RunSpec", *,
                     device: "str | torch.device",
                     as_list: bool = False):
    """The within-cycle per-CZ leak slice ``exp(L/4)`` Kraus table for a preset.

    Routes through :meth:`FusedWithinCycleSampler.build_within_cycle_leak`. Its
    channel-validity preconditions remain inside the builder and cannot be bypassed
    through this facade:

    * CPTP residual ``max|sum_k K_k^dag K_k - I| < 1e-12`` (``CPTP_TOL``) on the slice;
    * the composition identity ``||exp(L) - (exp(L/4))^4|| < 1e-12``
      (``WC_LEAK_COMPOSE_TOL``): four per-CZ slices compose to the registered
      full-cycle channel.

    A violating parameter point RAISES; this function never returns an unasserted
    table. ``preset_or_params`` is an :class:`ExperimentPreset` (theta resolved via
    :func:`resolve_theta`; the table depends only on ``(theta, g_seep, g_heat)``) or
    an explicit :class:`RunSpec` (passed straight to the builder). Returns the stacked
    ``(n_kraus, 3, 3)`` device tensor by default, or the list form ``[K_0, ...]`` when
    ``as_list=True``. GPU-only compute (the fused within-cycle host contract).
    """
    run_spec_cls, sampler_cls, _bind_provenance = _sv_runtime()
    if isinstance(preset_or_params, ExperimentPreset):
        spec = run_spec_cls(
            # circuit_path is NOT consumed here: build_within_cycle_leak reads only
            # (theta, g_seep, g_heat). The sentinel keeps the checked builder's
            # RunSpec signature without requiring the dataset on disk for a pure
            # channel-table build.
            circuit_path="__leak_slice_table_only__",
            theta=resolve_theta(preset_or_params),
            g_seep=float(preset_or_params.g_seep),
            g_heat=float(preset_or_params.g_heat),
            arm=str(preset_or_params.arm),
            b=float(preset_or_params.b_bias),
            readout_conv=str(preset_or_params.readout_conv),
            N=1,
            base_seed=0,
        )
    elif isinstance(preset_or_params, run_spec_cls):
        spec = preset_or_params
    else:
        raise TypeError(
            f"preset_or_params must be an ExperimentPreset or a RunSpec "
            f"(got {type(preset_or_params).__name__})")
    host = sampler_cls(device=device)
    leak, _evidence = host.build_within_cycle_leak(spec)  # CPTP + composition asserted
    if as_list:
        return [leak[k] for k in range(leak.shape[0])]
    return leak
