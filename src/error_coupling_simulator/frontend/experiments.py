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
* :data:`PRESET_LEAK_WG_L1_5E3` -- the RATE-CALIBRATED convention: ``theta_rad`` is
  SOLVED so the exact WG per-cycle leak rate ``WG_L1`` hits the registered target
  (5.0e-3, the Miao-grounded cell) via
  :func:`~error_coupling_simulator.mechanisms.qutrit_teachers.calibrate_theta_for_wg_l1`
  (monotone bisection on the exact channel rate; also re-exported as
  ``qec_twin.mechanisms.qutrit_teachers.calibrate_theta_for_wg_l1``).

Exactly ONE of ``theta_rad`` / ``wg_l1_target`` is set on any preset (validated);
:func:`resolve_theta` maps either convention to the operative angle.

DATASET RESOLUTION (K-vacuity rule). :func:`load_xzzx_d3` / :func:`run_spec_from_preset`
resolve the shipped Google ``d3_at_q6_7`` patch through
``qec_twin.forward.exact.xzzx_parser.default_r01_paths`` / ``default_r10_paths``
(layout: ``<root>/<patch>/<basis>/<r01|r10>/{circuit_ideal.stim, metadata.json}``).
Root precedence: the ``dataset_root`` argument > the ``QEC_TWIN_D3_DATA`` env var
(if the key is SET) > the parser's built-in ``DEFAULT_DATASET_ROOT`` (env key
ABSENT only). A SET-but-empty/whitespace ``QEC_TWIN_D3_DATA`` raises
:class:`ValueError` (fail loud: a broken shell expansion must never be
indistinguishable from unset). A nonexistent override root or a missing file
raises :class:`FileNotFoundError` NAMING the missing path -- NEVER a silent
fallback to the default root (a fallback would make every env-override probe
vacuous: the run would "pass" on the wrong data).

Binding contract: ``docs/twin_validation/api_hardening_ownership_design.md`` row A1,
the NAMING STANDARD (N-1..N-5) and the ratified rename table (``load_xzzx_d3`` /
``ExperimentPreset`` / ``leak_slice_table``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from error_coupling_simulator.mechanisms.qutrit_teachers import calibrate_theta_for_wg_l1
from qec_twin.forward.exact import xzzx_parser as _xp
from qec_twin.forward.scalable.sv_sampler import (
    SV_ARMS,
    SV_READOUT_CONVENTIONS,
    RunSpec,
    SvSampler,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    import torch
    from qec_twin.forward.exact.xzzx_parser import XZZXSchedule

__all__ = [
    "ExperimentPreset",
    "PRESET_LEAK_THETA_0P30",
    "PRESET_LEAK_WG_L1_5E3",
    "leak_slice_table",
    "load_xzzx_d3",
    "resolve_theta",
    "run_spec_from_preset",
]

#: Dataset-root override env var (ratified decision 7 of the ownership contract).
QEC_TWIN_D3_DATA_ENV = "QEC_TWIN_D3_DATA"

#: The four shipped d3_at_q6_7 files, keyed by logical name (the same logical names
#: the tests/conftest.py probe + the AM-2 mask hook use).
_D3_LOGICAL_NAMES = ("r01_circ", "r01_meta", "r10_circ", "r10_meta")


def _dataset_files(dataset_root: "str | Path | None") -> "dict[str, Path]":
    """Resolve the four shipped ``d3_at_q6_7`` files (r01/r10 circuit + metadata).

    Root precedence: ``dataset_root`` argument > ``QEC_TWIN_D3_DATA`` env var (if the
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
    NEVER a silent fallback to the default root (K-vacuity: a fallback would let an
    env-override run silently read the wrong data and still "pass").
    """
    root: "Path | None"
    if dataset_root is not None:
        root, source = Path(dataset_root), "dataset_root argument"
    elif QEC_TWIN_D3_DATA_ENV in os.environ:
        # SET-but-empty/whitespace is a distinct, LOUD error: a broken shell
        # expansion (e.g. QEC_TWIN_D3_DATA="$UNSET_VAR") would otherwise be
        # indistinguishable from unset and silently fall back to the default
        # root -- exactly the silent-fallback class this module forbids.
        env_root = os.environ[QEC_TWIN_D3_DATA_ENV].strip()
        if not env_root:
            raise ValueError(
                f"env var {QEC_TWIN_D3_DATA_ENV} is SET but empty/whitespace; "
                f"empty values are not allowed (a broken shell expansion would "
                f"be indistinguishable from unset). Unset it to use the default "
                f"root {_xp.DEFAULT_DATASET_ROOT}, or set it to a real dataset "
                f"root. Never falling back silently.")
        root, source = Path(env_root), f"env {QEC_TWIN_D3_DATA_ENV}"
    else:
        root, source = None, f"default root {_xp.DEFAULT_DATASET_ROOT}"

    r01_circ, r01_meta = _xp.default_r01_paths()
    r10_circ, r10_meta = _xp.default_r10_paths()
    files: "dict[str, Path]" = {
        "r01_circ": r01_circ, "r01_meta": r01_meta,
        "r10_circ": r10_circ, "r10_meta": r10_meta,
    }
    if root is not None:
        if not root.is_dir():
            raise FileNotFoundError(
                f"d3 dataset root {root} ({source}) does not exist or is not a "
                f"directory. Refusing to fall back to the default root "
                f"{_xp.DEFAULT_DATASET_ROOT} (a silent fallback would make the "
                f"override vacuous).")
        files = {name: root / p.relative_to(_xp.DEFAULT_DATASET_ROOT)
                 for name, p in files.items()}
    missing = [f"{name}: {files[name]}" for name in _D3_LOGICAL_NAMES
               if not files[name].is_file()]
    if missing:
        raise FileNotFoundError(
            f"shipped d3_at_q6_7 file(s) missing (root from {source}): "
            f"{missing}. Never falling back to the default root.")
    return files


def load_xzzx_d3(dataset_root: "str | Path | None" = None, *,
                 with_interior_streams: bool = True) -> "XZZXSchedule":
    """Parse the shipped Google d3 XZZX schedule: r01 geometry (+ r10 interior streams).

    Provenance is the explicit two-source split (model §1): the r01 instance supplies
    the VERIFIED code geometry (``parse_xzzx_circuit(verify=True)``: 17 qubits /
    8 detectors, two-method stabilizer self-check), and -- when
    ``with_interior_streams=True`` (default) -- the MULTI-ROUND r10 instance supplies
    the per-qutrit within-cycle INTERIOR token streams
    (``sched.with_within_cycle_streams(parse_within_cycle_streams(r10))``; r01's single
    round is first+terminal, not a clean interior round, so r01 alone cannot provide
    them). The within-cycle carriers (``SvSampler.marshal_within_cycle``,
    ``MpsLeakageForward.sample``) REQUIRE the streams; pass
    ``with_interior_streams=False`` only for geometry-only consumers.

    ``dataset_root`` overrides the dataset location (argument > ``QEC_TWIN_D3_DATA``
    env var > the parser default); a missing root/file raises
    :class:`FileNotFoundError` naming it -- never a silent fallback (see
    :func:`_dataset_files`).
    """
    files = _dataset_files(dataset_root)
    sched = _xp.parse_xzzx_circuit(files["r01_circ"], files["r01_meta"], verify=True)
    if with_interior_streams:
        sched = sched.with_within_cycle_streams(
            _xp.parse_within_cycle_streams(files["r10_circ"], files["r10_meta"]))
    return sched


@dataclass(frozen=True, kw_only=True)
class ExperimentPreset:
    """A named, frozen, REGISTERED experiment configuration (GLOSSARY: *preset*).

    Exactly ONE of ``theta_rad`` / ``wg_l1_target`` is set (validated): the two theta
    conventions -- raw-angle vs rate-calibrated -- are DISTINCT presets, never merged
    into one default. All physics knobs are REQUIRED (no silent physics defaults, the
    registered-sweep rule): ``g_seep`` / ``g_heat`` (WG dissipative seep/heat rates),
    ``b_bias`` (leaked-readout bias ``b`` in [0, 1]), ``arm`` (measurement-instrument
    arm, one of ``SV_ARMS``), ``readout_conv`` (terminal-readout convention, one of
    ``SV_READOUT_CONVENTIONS``).

    Units / conventions (N-4): ``theta_rad`` is the WG coherent |1><->|2> exchange
    angle in RADIANS; ``wg_l1_target`` is the per-cycle WG_L1 leak probability the
    angle is calibrated to (dimensionless, in (0, 0.5)).
    """

    name: str
    theta_rad: "float | None" = None
    wg_l1_target: "float | None" = None
    g_seep: float
    g_heat: float
    b_bias: float
    arm: str
    readout_conv: str

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


#: RAW-ANGLE convention: theta pinned directly at 0.30 rad (the p2-era registered leak
#: cell: g_seep 0.09 / b 0.9 / arm A / biased-b terminal readout).
PRESET_LEAK_THETA_0P30 = ExperimentPreset(
    name="leak_theta_0p30", theta_rad=0.30, g_seep=0.09, g_heat=0.0,
    b_bias=0.9, arm="A", readout_conv="biased_b")

#: RATE-CALIBRATED convention: theta solved for WG_L1 == 5.0e-3 (the Miao-grounded
#: physical leak cell of test_soft_readout) at the SAME other knobs.
PRESET_LEAK_WG_L1_5E3 = ExperimentPreset(
    name="leak_wg_l1_5e3", wg_l1_target=5.0e-3, g_seep=0.09, g_heat=0.0,
    b_bias=0.9, arm="A", readout_conv="biased_b")


def resolve_theta(preset: ExperimentPreset) -> float:
    """The operative WG exchange angle (radians) for a preset.

    Raw-angle convention: returns the pinned ``theta_rad``. Rate-calibrated
    convention: returns ``calibrate_theta_for_wg_l1(wg_l1_target, g_seep=...,
    g_heat=...)`` -- the monotone bisection on the EXACT WG channel rate (the same
    import + call shape the L-soft gates use), so the preset's ``g_seep``/``g_heat``
    participate in the calibration exactly as registered.
    """
    if preset.theta_rad is not None:
        return float(preset.theta_rad)
    return float(calibrate_theta_for_wg_l1(
        float(preset.wg_l1_target),
        g_seep=float(preset.g_seep), g_heat=float(preset.g_heat)))


def run_spec_from_preset(preset: ExperimentPreset, *, n_shots: int, n_rounds: int,
                         seed: int, m: int = 0,
                         dataset_root: "str | Path | None" = None) -> RunSpec:
    """Build the :class:`~qec_twin.forward.scalable.sv_sampler.RunSpec` for a preset.

    Every run-shape knob is an EXPLICIT keyword (``n_shots``/``n_rounds``/``seed``;
    ``m`` is the prepared logical); every physics knob comes from the preset (theta
    resolved via :func:`resolve_theta` -- the wg_l1 form is calibrated here); the
    circuit/metadata paths are the resolved shipped r01 instance (the R>1 engine
    reuses the r01 geometry -- attach the r10 interior streams via
    :func:`load_xzzx_d3` when driving a within-cycle carrier). No hidden knobs:
    ``dtype`` is pinned to the engine default ``"c128"``; everything else is
    validated by ``RunSpec.__post_init__``.
    """
    files = _dataset_files(dataset_root)
    return RunSpec(
        circuit_path=files["r01_circ"],
        metadata_path=files["r01_meta"],
        m=int(m),
        theta=resolve_theta(preset),
        g_seep=float(preset.g_seep),
        g_heat=float(preset.g_heat),
        arm=str(preset.arm),
        b=float(preset.b_bias),
        readout_conv=str(preset.readout_conv),
        N=int(n_shots),
        base_seed=int(seed),
        R=int(n_rounds),
        dtype="c128",
    )


def leak_slice_table(preset_or_params: "ExperimentPreset | RunSpec", *,
                     device: "str | torch.device",
                     as_list: bool = False):
    """The within-cycle per-CZ leak slice ``exp(L/4)`` Kraus table for a preset.

    Routes through :meth:`SvSampler.build_within_cycle_leak` -- the C1-asserted
    builder. The embedded (a)-class PRECONDITIONS stay inside that builder and are
    therefore embedded in this facade path (contract row A1 -- they are never
    bypassed):

    * CPTP residual ``max|sum_k K_k^dag K_k - I| < 1e-12`` (``CPTP_TOL``) on the slice;
    * the composition identity ``||exp(L) - (exp(L/4))^4|| < 1e-12``
      (``WC_LEAK_COMPOSE_TOL``): four per-CZ slices compose to the registered
      full-cycle channel.

    A violating parameter point RAISES; this function never returns an unasserted
    table. ``preset_or_params`` is an :class:`ExperimentPreset` (theta resolved via
    :func:`resolve_theta`; the table depends only on ``(theta, g_seep, g_heat)``) or
    an explicit :class:`RunSpec` (passed straight to the builder). Returns the stacked
    ``(n_kraus, 3, 3)`` device tensor by default, or the list form ``[K_0, ...]`` when
    ``as_list=True``. GPU-only compute (the SvSampler contract).
    """
    if isinstance(preset_or_params, ExperimentPreset):
        spec = RunSpec(
            # circuit_path is NOT consumed here: build_within_cycle_leak reads only
            # (theta, g_seep, g_heat). The sentinel keeps the C1-asserted builder's
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
    elif isinstance(preset_or_params, RunSpec):
        spec = preset_or_params
    else:
        raise TypeError(
            f"preset_or_params must be an ExperimentPreset or a RunSpec "
            f"(got {type(preset_or_params).__name__})")
    host = SvSampler(device=device)
    leak, _evidence = host.build_within_cycle_leak(spec)  # CPTP + composition asserted
    if as_list:
        return [leak[k] for k in range(leak.shape[0])]
    return leak
