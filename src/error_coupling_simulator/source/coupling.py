from __future__ import annotations

"""Axis-2 shared-source parameter fan-out for coupled-error teachers.

This module implements ``Theta(z_t)``: one explicit source draw conditions many
mechanism parameters in the same cycle/substep. It is deliberately a parameter
layer, not a Stim/DEM noise layer and not a channel assembler. Axis-1 consumes
these parameters later through ``forward.joint_lindbladian`` and backend-specific
carriers.
"""

from dataclasses import dataclass, field
import math
from typing import Iterable, Literal

import numpy as np

from ..numerics import NUMERICAL_ZERO

_TWO_PI = 2.0 * math.pi
_SOURCE_KEYS = (
    "zz",
    "gamma_phi",
    "detuning",
    "drive",
    "spillover",
    "readout",
    "reset",
    "cz",
    # P2-i (2026-07-06): the Theta->leakage seam. Literature-grounded FORM (a TLS defect's
    # slow 1/f modulation of the affected qubit's error rates — Gao 2605.23385: S(w) ~ 1/f^1.05
    # over ten decades, T1 jumps + low-frequency dephasing; the reading note's "teacher recipe"
    # models the TLS footprint exactly as a slow latent modulating rates). The AMPLITUDES stay
    # class (c) swept brackets — no published TLS->(theta, g_seep) transfer function is claimed.
    "wg_theta",
    "wg_seep",
)


@dataclass(frozen=True)
class StaticZZCalibration:
    """Static-ZZ reference constants for the frequency-drift fan-out.

    Units follow the existing qutip-source adaptor convention: frequencies are
    angular rad/ns after conversion, gate time is ns, and ``phi = zeta*t_gate/4``.
    ``base_phi_rad`` is used to infer the fixed exchange ``J`` at the base
    detuning; subsequent source draws shift the detuning and recompute ``zeta``.

    The class name is retained for API compatibility. Its built-in values are
    project-design defaults, not a device calibration, and this type stores no
    paper/dataset locator that could establish one. Callers may replace the numbers,
    but must record external calibration provenance in the enclosing run manifest.
    """

    omega_a_ghz: float = 6.0
    omega_b_ghz: float = 6.1
    alpha_mhz: float = -300.0
    t_gate_ns: float = 25.0
    base_phi_rad: float = 1.6e-4

    def __post_init__(self) -> None:
        _require_finite("omega_a_ghz", self.omega_a_ghz)
        _require_finite("omega_b_ghz", self.omega_b_ghz)
        _require_finite("alpha_mhz", self.alpha_mhz)
        _require_positive("t_gate_ns", self.t_gate_ns)
        if not math.isfinite(float(self.base_phi_rad)):
            raise ValueError("base_phi_rad must be finite")

    @property
    def base_delta_radns(self) -> float:
        return _TWO_PI * (float(self.omega_a_ghz) - float(self.omega_b_ghz))

    @property
    def alpha_radns(self) -> float:
        return _TWO_PI * float(self.alpha_mhz) * 1e-3

    @property
    def exchange_j_radns(self) -> float:
        return exchange_j_from_phi(
            float(self.base_phi_rad),
            delta_radns=self.base_delta_radns,
            alpha_radns=self.alpha_radns,
            t_gate_ns=float(self.t_gate_ns),
        )

    def to_manifest(self) -> dict:
        return {
            "value_provenance": {
                "built_in_defaults": "project-design",
                "instance_source_locator": None,
                "claims_device_calibration": False,
            },
            "omega_a_ghz": float(self.omega_a_ghz),
            "omega_b_ghz": float(self.omega_b_ghz),
            "alpha_mhz": float(self.alpha_mhz),
            "t_gate_ns": float(self.t_gate_ns),
            "base_phi_rad": float(self.base_phi_rad),
            "base_delta_radns": self.base_delta_radns,
            "alpha_radns": self.alpha_radns,
            "exchange_j_radns": self.exchange_j_radns,
        }


@dataclass(frozen=True)
class SourceCouplingConfig:
    """Design constants for ``Theta(z_t)``.

    ``z_scale_radns`` converts the source draw to a dimensionless normalized
    coordinate for the class-(c) log-rate/logit maps. The static-ZZ map uses the
    raw rad/ns draw directly as a detuning shift.
    """

    z_scale_radns: float = 1.0e-4
    zz: StaticZZCalibration = field(default_factory=StaticZZCalibration)
    gamma_phi_base_per_ns: float = 1.0 / 75_000.0
    gamma_phi_sensitivity: float = 0.35
    detuning_base_radns: float = 0.0
    drive_omega_base_radns: float = math.pi / 25.0
    drive_omega_sensitivity: float = 0.05
    spillover_base_p: float = 1.0e-3
    spillover_sensitivity: float = 0.15
    readout_flip_base_p: float = 1.0e-2
    readout_flip_sensitivity: float = 0.40
    reset_flip_base_p: float = 5.0e-3
    reset_flip_sensitivity: float = 0.35
    cz_depol_base_p: float = 2.0e-3
    cz_depol_sensitivity: float = 0.30
    # P2-i Theta->leakage fields (Wood-Gambetta coherent |1><->|2| angle + seep jump rate).
    # DEFAULTS ARE FULLY INERT (base 0 AND sensitivity 0 => the fan-out emits 0 and no
    # existing consumer's behavior changes); the P2-iv teacher passes its physical cell
    # (e.g. theta = calibrate_theta_for_wg_l1(5e-3), g_seep = 0.09 per McEwen 2102.06131)
    # explicitly. Both use the positive-rate exp map (theta > 0 is an angle magnitude; the
    # WG L1 ~ sin^2(theta)/2 rate then inherits ~2x the relative modulation). Class (c).
    wg_theta_base_rad: float = 0.0
    wg_theta_sensitivity: float = 0.0
    wg_g_seep_base: float = 0.0
    wg_g_seep_sensitivity: float = 0.0
    schema: str = "qec_twin.mechanisms.SourceCouplingConfig.v1"

    def __post_init__(self) -> None:
        _require_positive("z_scale_radns", self.z_scale_radns)
        _require_nonnegative("gamma_phi_base_per_ns", self.gamma_phi_base_per_ns)
        _require_finite("gamma_phi_sensitivity", self.gamma_phi_sensitivity)
        _require_finite("detuning_base_radns", self.detuning_base_radns)
        _require_nonnegative("drive_omega_base_radns", self.drive_omega_base_radns)
        _require_finite("drive_omega_sensitivity", self.drive_omega_sensitivity)
        for name in (
            "spillover_base_p",
            "readout_flip_base_p",
            "reset_flip_base_p",
            "cz_depol_base_p",
        ):
            _validate_probability(name, getattr(self, name), allow_zero=True)
        for name in (
            "spillover_sensitivity",
            "readout_flip_sensitivity",
            "reset_flip_sensitivity",
            "cz_depol_sensitivity",
            "wg_theta_sensitivity",
            "wg_g_seep_sensitivity",
        ):
            _require_finite(name, getattr(self, name))
        _require_nonnegative("wg_theta_base_rad", self.wg_theta_base_rad)
        _require_nonnegative("wg_g_seep_base", self.wg_g_seep_base)

    def to_manifest(self) -> dict:
        return {
            "schema": self.schema,
            "epistemic_class": {
                "static_zz_formula": "a",
                "constants_and_sensitivities": "c",
                "log_rate_and_logit_maps": "c",
            },
            "z_scale_radns": float(self.z_scale_radns),
            "zz": self.zz.to_manifest(),
            "gamma_phi_base_per_ns": float(self.gamma_phi_base_per_ns),
            "gamma_phi_sensitivity": float(self.gamma_phi_sensitivity),
            "detuning_base_radns": float(self.detuning_base_radns),
            "drive_omega_base_radns": float(self.drive_omega_base_radns),
            "drive_omega_sensitivity": float(self.drive_omega_sensitivity),
            "spillover_base_p": float(self.spillover_base_p),
            "spillover_sensitivity": float(self.spillover_sensitivity),
            "readout_flip_base_p": float(self.readout_flip_base_p),
            "readout_flip_sensitivity": float(self.readout_flip_sensitivity),
            "reset_flip_base_p": float(self.reset_flip_base_p),
            "reset_flip_sensitivity": float(self.reset_flip_sensitivity),
            "cz_depol_base_p": float(self.cz_depol_base_p),
            "cz_depol_sensitivity": float(self.cz_depol_sensitivity),
            "wg_theta_base_rad": float(self.wg_theta_base_rad),
            "wg_theta_sensitivity": float(self.wg_theta_sensitivity),
            "wg_g_seep_base": float(self.wg_g_seep_base),
            "wg_g_seep_sensitivity": float(self.wg_g_seep_sensitivity),
        }


@dataclass(frozen=True)
class CoupledMechanismParams:
    """Parameter bundle emitted by ``Theta(z_t)`` for one cycle/substep."""

    source_draws_radns: tuple[tuple[str, float], ...]
    normalized_draws: tuple[tuple[str, float], ...]
    zz_phi_rad: float
    zz_zeta_radns: float
    zz_exchange_j_radns: float
    gamma_phi_per_ns: float
    tphi_ns: float
    detuning_radns: float
    drive_omega_radns: float
    spillover_cx: float
    readout_flip_p: float
    reset_flip_p: float
    cz_depol_p: float
    # P2-i Theta->leakage outputs (0.0 = the inert default; defaults keep every
    # pre-P2 direct constructor valid).
    wg_theta_rad: float = 0.0
    wg_g_seep: float = 0.0
    coupling_mode: Literal["shared", "independent"] = "shared"
    schema: str = "qec_twin.mechanisms.CoupledMechanismParams.v1"

    def source_draw_for(self, key: str) -> float:
        draws = dict(self.source_draws_radns)
        if key not in draws:
            raise KeyError(key)
        return float(draws[key])

    def to_manifest(self) -> dict:
        return {
            "schema": self.schema,
            "coupling_mode": self.coupling_mode,
            "source_draws_radns": dict(self.source_draws_radns),
            "normalized_draws": dict(self.normalized_draws),
            "zz_phi_rad": float(self.zz_phi_rad),
            "zz_zeta_radns": float(self.zz_zeta_radns),
            "zz_exchange_j_radns": float(self.zz_exchange_j_radns),
            "gamma_phi_per_ns": float(self.gamma_phi_per_ns),
            "tphi_ns": float(self.tphi_ns),
            "detuning_radns": float(self.detuning_radns),
            "drive_omega_radns": float(self.drive_omega_radns),
            "spillover_cx": float(self.spillover_cx),
            "readout_flip_p": float(self.readout_flip_p),
            "reset_flip_p": float(self.reset_flip_p),
            "cz_depol_p": float(self.cz_depol_p),
            "wg_theta_rad": float(self.wg_theta_rad),
            "wg_g_seep": float(self.wg_g_seep),
        }


def default_source_coupling_config() -> SourceCouplingConfig:
    """Return the documented slice-1 reference config.

    The returned constants are class-(c) design defaults; callers may override
    them for device-specific calibration.
    """

    return SourceCouplingConfig()


def source_to_params(
    z_t_radns: float,
    config: SourceCouplingConfig | None = None,
) -> CoupledMechanismParams:
    """Map one shared source draw to all coupled mechanism parameters."""

    cfg = config or default_source_coupling_config()
    z = _require_finite("z_t_radns", z_t_radns)
    draws = {key: z for key in _SOURCE_KEYS}
    return _params_from_draws(draws, cfg, coupling_mode="shared")


def trajectory_to_params(
    z_trajectory_radns: Iterable[float],
    config: SourceCouplingConfig | None = None,
) -> tuple[CoupledMechanismParams, ...]:
    """Apply the shared-source fan-out to every draw in a trajectory."""

    cfg = config or default_source_coupling_config()
    z_arr = _as_1d_finite("z_trajectory_radns", z_trajectory_radns)
    return tuple(source_to_params(float(z), cfg) for z in z_arr)


def independent_baseline_trajectory_to_params(
    z_trajectory_radns: Iterable[float],
    config: SourceCouplingConfig | None = None,
    *,
    seed: int,
) -> tuple[CoupledMechanismParams, ...]:
    """Break same-cycle shared-source coupling while preserving one-field marginals.

    Each mechanism field receives an independent permutation of the same source
    trajectory. This is the Axis-2 negative control for G6-style ablations: the
    marginal distribution of each field is unchanged, but cross-mechanism
    same-cycle correlations from the common latent are destroyed.
    """

    cfg = config or default_source_coupling_config()
    z_arr = _as_1d_finite("z_trajectory_radns", z_trajectory_radns)
    rng = np.random.default_rng(int(seed))
    permuted = {key: np.array(z_arr, copy=True) for key in _SOURCE_KEYS}
    for key in _SOURCE_KEYS:
        rng.shuffle(permuted[key])
    out: list[CoupledMechanismParams] = []
    for i in range(z_arr.size):
        draws = {key: float(permuted[key][i]) for key in _SOURCE_KEYS}
        out.append(_params_from_draws(draws, cfg, coupling_mode="independent"))
    return tuple(out)


def parameter_series(params: Iterable[CoupledMechanismParams], field: str) -> np.ndarray:
    """Extract one parameter field as a float64 trajectory."""

    values = []
    for p in params:
        if not hasattr(p, field):
            raise AttributeError(f"CoupledMechanismParams has no field {field!r}")
        values.append(float(getattr(p, field)))
    return np.asarray(values)


def cross_mechanism_correlation(
    params: Iterable[CoupledMechanismParams],
    field_a: str,
    field_b: str,
) -> float:
    """Pearson correlation of two emitted mechanism-parameter trajectories."""

    a = parameter_series(params, field_a)
    b = parameter_series(params, field_b)
    if a.size != b.size or a.size < 2:
        raise ValueError("need at least two paired samples")
    if float(np.std(a)) <= NUMERICAL_ZERO or float(np.std(b)) <= NUMERICAL_ZERO:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def static_zz_zeta(delta_radns: float, alpha_radns: float, exchange_j_radns: float) -> float:
    """Static-ZZ dispersive cross-Kerr coefficient.

    ``zeta = 2 J^2 [1/(Delta-alpha) - 1/(Delta+alpha)]``.
    """

    delta = _require_finite("delta_radns", delta_radns)
    alpha = _require_finite("alpha_radns", alpha_radns)
    J = _require_nonnegative("exchange_j_radns", exchange_j_radns)
    denom1 = delta - alpha
    denom2 = delta + alpha
    if abs(denom1) <= NUMERICAL_ZERO or abs(denom2) <= NUMERICAL_ZERO:
        raise ValueError(
            "static_zz_zeta singular: Delta too close to +/- alpha "
            f"(Delta={delta}, alpha={alpha})"
        )
    return float(2.0 * J * J * (1.0 / denom1 - 1.0 / denom2))


def exchange_j_from_phi(
    phi_rad: float,
    *,
    delta_radns: float,
    alpha_radns: float,
    t_gate_ns: float,
) -> float:
    """Invert ``phi = zeta(J)*t_gate/4`` for ``|J|`` at the base detuning."""

    phi = _require_finite("phi_rad", phi_rad)
    t_gate = _require_positive("t_gate_ns", t_gate_ns)
    coeff = static_zz_zeta(delta_radns, alpha_radns, 1.0)
    if abs(coeff) <= NUMERICAL_ZERO:
        raise ValueError("cannot infer exchange J because zeta coefficient is zero")
    J2 = 4.0 * phi / (coeff * t_gate)
    if J2 < -NUMERICAL_ZERO:
        raise ValueError(
            "phi sign is inconsistent with the static-ZZ coefficient; "
            f"phi={phi}, coeff={coeff}, t_gate={t_gate}"
        )
    return float(math.sqrt(max(0.0, J2)))


def zz_phi_from_frequency_drift(z_t_radns: float, config: SourceCouplingConfig) -> tuple[float, float]:
    """Return ``(phi_rad, zeta_radns)`` after applying the detuning drift."""

    z = _require_finite("z_t_radns", z_t_radns)
    zz = config.zz
    delta = zz.base_delta_radns + z
    zeta = static_zz_zeta(delta, zz.alpha_radns, zz.exchange_j_radns)
    return float(zeta * float(zz.t_gate_ns) / 4.0), float(zeta)


def drift_to_t2(
    z_t_radns: float,
    config: SourceCouplingConfig | None = None,
) -> tuple[float, float]:
    """Map a source drift draw to ``(gamma_phi_per_ns, Tphi_ns)``.

    This is the public spelling of the build-contract helper named
    ``_drift_to_T2``. The map is class-(c): a positive log-rate modulation around
    the configured pure-dephasing base rate.
    """

    cfg = config or default_source_coupling_config()
    z = _require_finite("z_t_radns", z_t_radns)
    x = z / float(cfg.z_scale_radns)
    gamma_phi = _modulate_positive_rate(
        cfg.gamma_phi_base_per_ns,
        x,
        cfg.gamma_phi_sensitivity,
        name="gamma_phi_per_ns",
    )
    tphi_ns = math.inf if gamma_phi <= NUMERICAL_ZERO else float(1.0 / gamma_phi)
    return gamma_phi, tphi_ns


def _drift_to_T2(
    z_t_radns: float,
    config: SourceCouplingConfig | None = None,
) -> tuple[float, float]:
    """Contract-compatible alias for :func:`drift_to_t2`."""

    return drift_to_t2(z_t_radns, config)


def leakage_from_drift(
    theta_z_radns: float,
    seep_z_radns: float,
    config: SourceCouplingConfig | None = None,
) -> tuple[float, float]:
    """Map source drift draws to the per-cycle WG leakage cell ``(theta_rad, g_seep)``.

    P2-i (prereg ``p2_conjunction_wiring_prereg.md``). FORM grounded in the TLS
    literature (Gao 2605.23385: a defect's 1/f^1.05 spectrum slowly modulates the
    affected qubit's error rates — the reading note's teacher recipe), spelled as
    the same positive-rate exp map the gamma_phi fan-out uses; AMPLITUDES are
    class-(c) swept brackets (no published TLS->(theta, g_seep) transfer function
    is claimed). Inert at the default config (base 0, sensitivity 0 -> (0, 0));
    ``Theta(0)`` returns the configured bases exactly (the off-source identity).
    """

    cfg = config or default_source_coupling_config()
    x_theta = _require_finite("theta_z_radns", theta_z_radns) / float(cfg.z_scale_radns)
    x_seep = _require_finite("seep_z_radns", seep_z_radns) / float(cfg.z_scale_radns)
    theta = _modulate_positive_rate(
        cfg.wg_theta_base_rad, x_theta, cfg.wg_theta_sensitivity, name="wg_theta_rad"
    )
    g_seep = _modulate_positive_rate(
        cfg.wg_g_seep_base, x_seep, cfg.wg_g_seep_sensitivity, name="wg_g_seep"
    )
    return theta, g_seep


def _params_from_draws(
    draws_radns: dict[str, float],
    cfg: SourceCouplingConfig,
    *,
    coupling_mode: Literal["shared", "independent"],
) -> CoupledMechanismParams:
    draws = {key: _require_finite(f"draws_radns[{key}]", draws_radns[key]) for key in _SOURCE_KEYS}
    x = {key: draws[key] / float(cfg.z_scale_radns) for key in _SOURCE_KEYS}
    zz_phi, zz_zeta = zz_phi_from_frequency_drift(draws["zz"], cfg)
    gamma_phi, tphi_ns = drift_to_t2(draws["gamma_phi"], cfg)
    wg_theta, wg_g_seep = leakage_from_drift(draws["wg_theta"], draws["wg_seep"], cfg)
    drive_omega = _modulate_positive_rate(
        cfg.drive_omega_base_radns,
        x["drive"],
        cfg.drive_omega_sensitivity,
        name="drive_omega_radns",
    )
    return CoupledMechanismParams(
        source_draws_radns=tuple((key, draws[key]) for key in _SOURCE_KEYS),
        normalized_draws=tuple((key, float(x[key])) for key in _SOURCE_KEYS),
        zz_phi_rad=zz_phi,
        zz_zeta_radns=zz_zeta,
        zz_exchange_j_radns=cfg.zz.exchange_j_radns,
        gamma_phi_per_ns=gamma_phi,
        tphi_ns=tphi_ns,
        detuning_radns=float(cfg.detuning_base_radns + draws["detuning"]),
        drive_omega_radns=drive_omega,
        spillover_cx=_modulate_probability_logit(
            cfg.spillover_base_p,
            x["spillover"],
            cfg.spillover_sensitivity,
            name="spillover_cx",
        ),
        readout_flip_p=_modulate_probability_logit(
            cfg.readout_flip_base_p,
            x["readout"],
            cfg.readout_flip_sensitivity,
            name="readout_flip_p",
        ),
        reset_flip_p=_modulate_probability_logit(
            cfg.reset_flip_base_p,
            x["reset"],
            cfg.reset_flip_sensitivity,
            name="reset_flip_p",
        ),
        cz_depol_p=_modulate_probability_logit(
            cfg.cz_depol_base_p,
            x["cz"],
            cfg.cz_depol_sensitivity,
            name="cz_depol_p",
        ),
        wg_theta_rad=wg_theta,
        wg_g_seep=wg_g_seep,
        coupling_mode=coupling_mode,
    )


def _modulate_positive_rate(base: float, x: float, sensitivity: float, *, name: str) -> float:
    base = _require_nonnegative(name + ".base", base)
    sens = _require_finite(name + ".sensitivity", sensitivity)
    xv = _require_finite(name + ".x", x)
    if base <= NUMERICAL_ZERO:
        if abs(sens) > NUMERICAL_ZERO:
            raise ValueError(f"{name}: nonzero sensitivity cannot modulate a zero base rate")
        return 0.0
    expo = max(-60.0, min(60.0, sens * xv))
    return float(base * math.exp(expo))


def _modulate_probability_logit(base_p: float, x: float, sensitivity: float, *, name: str) -> float:
    p = _validate_probability(name + ".base_p", base_p, allow_zero=True)
    sens = _require_finite(name + ".sensitivity", sensitivity)
    xv = _require_finite(name + ".x", x)
    if p <= NUMERICAL_ZERO:
        if abs(sens) > NUMERICAL_ZERO:
            raise ValueError(f"{name}: nonzero sensitivity cannot logit-modulate p=0")
        return 0.0
    p = min(max(p, NUMERICAL_ZERO), 1.0 - NUMERICAL_ZERO)
    logit = math.log(p / (1.0 - p))
    y = max(-60.0, min(60.0, logit + sens * xv))
    return float(1.0 / (1.0 + math.exp(-y)))


def _as_1d_finite(name: str, values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(tuple(values), dtype=np.float64)
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError(f"{name} must be a non-empty 1-D trajectory")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def _validate_probability(name: str, value: float, *, allow_zero: bool) -> float:
    v = _require_finite(name, value)
    lo_ok = v >= 0.0 if allow_zero else v > 0.0
    if not lo_ok or v >= 1.0:
        bound = "[0, 1)" if allow_zero else "(0, 1)"
        raise ValueError(f"{name} must be in {bound}, got {v!r}")
    return v


def _require_finite(name: str, value: float) -> float:
    v = float(value)
    if not math.isfinite(v):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return v


def _require_positive(name: str, value: float) -> float:
    v = _require_finite(name, value)
    if v <= 0.0:
        raise ValueError(f"{name} must be > 0, got {v!r}")
    return v


def _require_nonnegative(name: str, value: float) -> float:
    v = _require_finite(name, value)
    if v < 0.0:
        raise ValueError(f"{name} must be >= 0, got {v!r}")
    return v


__all__ = [
    "CoupledMechanismParams",
    "SourceCouplingConfig",
    "StaticZZCalibration",
    "cross_mechanism_correlation",
    "default_source_coupling_config",
    "drift_to_t2",
    "exchange_j_from_phi",
    "independent_baseline_trajectory_to_params",
    "leakage_from_drift",
    "parameter_series",
    "source_to_params",
    "static_zz_zeta",
    "trajectory_to_params",
    "zz_phi_from_frequency_drift",
]
