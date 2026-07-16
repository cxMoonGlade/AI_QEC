from __future__ import annotations

"""Axis-2 shared-source parameter fan-out for coupled noise processes.

This module implements ``Theta(z_t)``: one explicit source draw conditions many
mechanism parameters in the same cycle/substep. It is deliberately a parameter
layer, not a Stim/DEM noise layer and not a channel assembler. Axis-1 consumes
these parameters later through ``carrier.joint_lindbladian`` and backend-specific
carriers.
"""

from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from fractions import Fraction
import math
import sys
from typing import Iterable, Literal

import numpy as np

from ..numerics import (
    NUMERICAL_ZERO,
    _decimal_to_float64,
    scaled_exp_multiply,
    scaled_product_ratio,
    shifted_probability_from_odds,
)

_TWO_PI = 2.0 * math.pi
SOURCE_COUPLING_CONFIG_SCHEMA = "error_coupling_simulator.source.coupling_config.v2"
COUPLED_PROCESS_PARAMS_SCHEMA = "error_coupling_simulator.source.coupled_process_params.v2"
_SOURCE_KEYS = (
    "zz",
    "gamma_phi",
    "detuning",
    "drive",
    "spillover",
    "readout",
    "reset",
    "cz",
)
_STATIC_ZZ_DIRECT_UPPER_GUARD = sys.float_info.max
for _ in range(16):
    _STATIC_ZZ_DIRECT_UPPER_GUARD = math.nextafter(
        _STATIC_ZZ_DIRECT_UPPER_GUARD,
        0.0,
    )


@dataclass(frozen=True)
class StaticZZParameters:
    """Static-ZZ parameters for the frequency-drift fan-out.

    Units follow the existing qutip-source adaptor convention: frequencies are
    angular rad/ns after conversion, gate time is ns, and ``phi = zeta*t_gate/4``.
    ``base_phi_rad`` is used to infer the fixed exchange ``J`` at the base
    detuning; subsequent source draws shift the detuning and recompute ``zeta``.

    Its built-in values are project-design defaults, not a device calibration,
    and this type stores no
    paper/dataset locator that could establish one. Callers may replace the numbers,
    but must record external calibration provenance in the enclosing run manifest.
    """

    omega_a_ghz: float = 6.0
    omega_b_ghz: float = 6.1
    alpha_mhz: float = -300.0
    t_gate_ns: float = 25.0
    base_phi_rad: float = 1.6e-4

    def __post_init__(self) -> None:
        for name in ("omega_a_ghz", "omega_b_ghz", "alpha_mhz"):
            object.__setattr__(self, name, _require_finite(name, getattr(self, name)))
        object.__setattr__(
            self,
            "t_gate_ns",
            _require_positive("t_gate_ns", self.t_gate_ns),
        )
        base_phi = float(self.base_phi_rad)
        if not math.isfinite(base_phi):
            raise ValueError("base_phi_rad must be finite")
        object.__setattr__(self, "base_phi_rad", base_phi)
        # Every value emitted by to_manifest must already be derivable here.
        # In particular, finite inputs may not defer an infinite exchange J to
        # property access or manifest emission.
        _ = self.exchange_j_radns

    @property
    def base_delta_radns(self) -> float:
        return _TWO_PI * (float(self.omega_a_ghz) - float(self.omega_b_ghz))

    @property
    def alpha_radns(self) -> float:
        return _mhz_to_radns_float64(self.alpha_mhz, name="alpha_radns")

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
    zz: StaticZZParameters = field(default_factory=StaticZZParameters)
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
    schema: str = SOURCE_COUPLING_CONFIG_SCHEMA

    def __post_init__(self) -> None:
        schema = str(self.schema)
        object.__setattr__(self, "schema", schema)
        if schema != SOURCE_COUPLING_CONFIG_SCHEMA:
            raise ValueError(
                f"unsupported source coupling schema {schema!r}; "
                f"expected {SOURCE_COUPLING_CONFIG_SCHEMA!r}"
            )
        if not isinstance(self.zz, StaticZZParameters):
            raise TypeError("zz must be a StaticZZParameters instance")
        object.__setattr__(
            self,
            "z_scale_radns",
            _require_positive("z_scale_radns", self.z_scale_radns),
        )
        object.__setattr__(
            self,
            "gamma_phi_base_per_ns",
            _require_nonnegative(
                "gamma_phi_base_per_ns",
                self.gamma_phi_base_per_ns,
            ),
        )
        for name in (
            "gamma_phi_sensitivity",
            "detuning_base_radns",
            "drive_omega_sensitivity",
        ):
            object.__setattr__(self, name, _require_finite(name, getattr(self, name)))
        object.__setattr__(
            self,
            "drive_omega_base_radns",
            _require_nonnegative(
                "drive_omega_base_radns",
                self.drive_omega_base_radns,
            ),
        )
        for name in (
            "spillover_base_p",
            "readout_flip_base_p",
            "reset_flip_base_p",
            "cz_depol_base_p",
        ):
            object.__setattr__(
                self,
                name,
                _validate_probability(name, getattr(self, name), allow_zero=True),
            )
        for name in (
            "spillover_sensitivity",
            "readout_flip_sensitivity",
            "reset_flip_sensitivity",
            "cz_depol_sensitivity",
        ):
            object.__setattr__(self, name, _require_finite(name, getattr(self, name)))

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
        }


@dataclass(frozen=True)
class CoupledNoiseParameters:
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
    coupling_mode: Literal["shared", "independent"] = "shared"
    schema: str = field(default=COUPLED_PROCESS_PARAMS_SCHEMA, init=False)

    def __post_init__(self) -> None:
        coupling_mode = str(self.coupling_mode)
        object.__setattr__(self, "coupling_mode", coupling_mode)
        if coupling_mode not in ("shared", "independent"):
            raise ValueError(
                "coupling_mode must be 'shared' or 'independent', "
                f"got {coupling_mode!r}"
            )
        source_draws = _snapshot_named_draws(self.source_draws_radns)
        normalized_draws = _snapshot_named_draws(self.normalized_draws)
        object.__setattr__(self, "source_draws_radns", source_draws)
        object.__setattr__(self, "normalized_draws", normalized_draws)
        if tuple(key for key, _ in source_draws) != _SOURCE_KEYS:
            raise ValueError(
                "source_draws_radns must contain each source key exactly once "
                "in canonical order"
            )
        if tuple(key for key, _ in normalized_draws) != _SOURCE_KEYS:
            raise ValueError(
                "normalized_draws must contain each source key exactly once "
                "in canonical order"
            )
        scalar_fields = (
            "zz_phi_rad",
            "zz_zeta_radns",
            "zz_exchange_j_radns",
            "gamma_phi_per_ns",
            "tphi_ns",
            "detuning_radns",
            "drive_omega_radns",
            "spillover_cx",
            "readout_flip_p",
            "reset_flip_p",
            "cz_depol_p",
        )
        for field_name in scalar_fields:
            object.__setattr__(self, field_name, float(getattr(self, field_name)))
        values = {
            **dict(source_draws),
            **{f"normalized_{key}": value for key, value in normalized_draws},
            "zz_phi_rad": self.zz_phi_rad,
            "zz_zeta_radns": self.zz_zeta_radns,
            "zz_exchange_j_radns": self.zz_exchange_j_radns,
            "gamma_phi_per_ns": self.gamma_phi_per_ns,
            "detuning_radns": self.detuning_radns,
            "drive_omega_radns": self.drive_omega_radns,
            "spillover_cx": self.spillover_cx,
            "readout_flip_p": self.readout_flip_p,
            "reset_flip_p": self.reset_flip_p,
            "cz_depol_p": self.cz_depol_p,
        }
        for field_name, value in values.items():
            if not math.isfinite(float(value)):
                raise ValueError(
                    f"{field_name} must be finite at the coupling emission boundary, got {value!r}"
                )
        if self.gamma_phi_per_ns < 0.0:
            raise ValueError("gamma_phi_per_ns must be >= 0 at the coupling emission boundary")
        for field_name in ("zz_exchange_j_radns", "drive_omega_radns"):
            value = float(getattr(self, field_name))
            if value < 0.0:
                raise ValueError(
                    f"{field_name} must be >= 0 at the coupling emission boundary, "
                    f"got {value!r}"
                )
        for field_name in (
            "spillover_cx",
            "readout_flip_p",
            "reset_flip_p",
            "cz_depol_p",
        ):
            value = float(getattr(self, field_name))
            if not 0.0 <= value < 1.0:
                raise ValueError(
                    f"{field_name} must be in [0, 1) at the coupling emission boundary, "
                    f"got {value!r}"
                )
        if self.gamma_phi_per_ns == 0.0:
            if self.tphi_ns != math.inf:
                raise ValueError("tphi_ns must be +inf when gamma_phi_per_ns is structural zero")
        elif not math.isfinite(self.tphi_ns) or self.tphi_ns <= 0.0:
            raise ValueError(
                "tphi_ns must be finite and > 0 when gamma_phi_per_ns is positive"
            )
        elif self.tphi_ns != 1.0 / self.gamma_phi_per_ns:
            raise ValueError(
                "tphi_ns must equal 1 / gamma_phi_per_ns at the coupling emission boundary"
            )

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
        }


def default_source_coupling_config() -> SourceCouplingConfig:
    """Return the default source-coupling config.

    The returned constants are class-(c) design defaults; callers may override
    them for device-specific calibration.
    """

    return SourceCouplingConfig()


def source_to_params(
    z_t_radns: float,
    config: SourceCouplingConfig | None = None,
) -> CoupledNoiseParameters:
    """Map one shared source draw to all coupled mechanism parameters."""

    cfg = config or default_source_coupling_config()
    z = _require_finite("z_t_radns", z_t_radns)
    draws = {key: z for key in _SOURCE_KEYS}
    return _params_from_draws(draws, cfg, coupling_mode="shared")


def trajectory_to_params(
    z_trajectory_radns: Iterable[float],
    config: SourceCouplingConfig | None = None,
) -> tuple[CoupledNoiseParameters, ...]:
    """Apply the shared-source fan-out to every draw in a trajectory."""

    cfg = config or default_source_coupling_config()
    z_arr = _as_1d_finite("z_trajectory_radns", z_trajectory_radns)
    return tuple(source_to_params(float(z), cfg) for z in z_arr)


def independent_baseline_trajectory_to_params(
    z_trajectory_radns: Iterable[float],
    config: SourceCouplingConfig | None = None,
    *,
    seed: int,
) -> tuple[CoupledNoiseParameters, ...]:
    """Break same-cycle shared-source coupling while preserving one-field marginals.

    Each mechanism field receives an independent permutation of the same source
    trajectory. This leaves each field's marginal distribution unchanged while
    destroying common-latent same-cycle alignment between fields.
    """

    cfg = config or default_source_coupling_config()
    z_arr = _as_1d_finite("z_trajectory_radns", z_trajectory_radns)
    rng = np.random.default_rng(int(seed))
    permuted = {key: np.array(z_arr, copy=True) for key in _SOURCE_KEYS}
    for key in _SOURCE_KEYS:
        rng.shuffle(permuted[key])
    out: list[CoupledNoiseParameters] = []
    for i in range(z_arr.size):
        draws = {key: float(permuted[key][i]) for key in _SOURCE_KEYS}
        out.append(_params_from_draws(draws, cfg, coupling_mode="independent"))
    return tuple(out)


def parameter_series(params: Iterable[CoupledNoiseParameters], field: str) -> np.ndarray:
    """Extract one parameter field as a float64 trajectory."""

    values = []
    for p in params:
        if not hasattr(p, field):
            raise AttributeError(f"CoupledNoiseParameters has no field {field!r}")
        values.append(float(getattr(p, field)))
    return np.asarray(values)


def cross_mechanism_correlation(
    params: Iterable[CoupledNoiseParameters],
    field_a: str,
    field_b: str,
) -> float:
    """Pearson correlation of two emitted mechanism-parameter trajectories."""

    a = parameter_series(params, field_a)
    b = parameter_series(params, field_b)
    if a.size != b.size or a.size < 2:
        raise ValueError("need at least two paired samples")
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{field_a} must contain only finite emitted values for correlation")
    if not np.all(np.isfinite(b)):
        raise ValueError(f"{field_b} must contain only finite emitted values for correlation")
    if np.all(a == a[0]) or np.all(b == b[0]):
        return 0.0
    a_scaled = a / float(np.max(np.abs(a)))
    b_scaled = b / float(np.max(np.abs(b)))
    a_centered = a_scaled - float(np.mean(a_scaled))
    b_centered = b_scaled - float(np.mean(b_scaled))
    numerator = float(np.dot(a_centered, b_centered))
    denominator = math.sqrt(
        float(np.dot(a_centered, a_centered))
        * float(np.dot(b_centered, b_centered))
    )
    if not math.isfinite(numerator) or not math.isfinite(denominator) or denominator == 0.0:
        raise ValueError("Pearson correlation is not representable as a finite float64")
    result = numerator / denominator
    if not math.isfinite(result):
        raise ValueError("Pearson correlation is not representable as a finite float64")
    return float(min(1.0, max(-1.0, result)))


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
    if J == 0.0 or alpha == 0.0:
        return 0.0

    j_squared = J * J
    scaled_j_squared = 4.0 * j_squared
    numerator = scaled_j_squared * alpha
    denominator = denom1 * denom2
    if all(
        math.isfinite(value) and abs(value) >= sys.float_info.min
        for value in (
            J,
            alpha,
            denom1,
            denom2,
            j_squared,
            scaled_j_squared,
            numerator,
            denominator,
        )
    ):
        result = float(numerator / denominator)
        if (
            math.isfinite(result)
            and abs(result) >= sys.float_info.min
            and abs(result) < _STATIC_ZZ_DIRECT_UPPER_GUARD
        ):
            return result

    delta_exact = Fraction.from_float(delta)
    alpha_exact = Fraction.from_float(alpha)
    exchange_exact = Fraction.from_float(J)
    exact = (
        4
        * exchange_exact
        * exchange_exact
        * alpha_exact
        / ((delta_exact - alpha_exact) * (delta_exact + alpha_exact))
    )
    try:
        recovered = float(exact)
    except OverflowError:
        recovered = math.copysign(math.inf, -1.0 if exact < 0 else 1.0)
    if not math.isfinite(recovered) or recovered == 0.0:
        raise ValueError(
            "static_zz_zeta nonzero result is not representable as a finite float64"
        )
    return recovered


def _mhz_to_radns_float64(value_mhz: float, *, name: str) -> float:
    """Convert a finite MHz scalar to rad/ns without an overflowing product."""

    value = _require_finite(f"{name}.value_mhz", value_mhz)
    if value == 0.0:
        return value
    product = _TWO_PI * value
    direct = product * 1.0e-3
    if (
        math.isfinite(product)
        and abs(product) >= sys.float_info.min
        and math.isfinite(direct)
        and abs(direct) >= sys.float_info.min
    ):
        return float(direct)
    return scaled_product_ratio(
        value,
        _TWO_PI,
        1_000.0,
        name=name,
    )


def exchange_j_from_phi(
    phi_rad: float,
    *,
    delta_radns: float,
    alpha_radns: float,
    t_gate_ns: float,
) -> float:
    """Invert ``phi = zeta(J)*t_gate/4`` for ``|J|`` at the base detuning."""

    phi = _require_finite("phi_rad", phi_rad)
    delta = _require_finite("delta_radns", delta_radns)
    alpha = _require_finite("alpha_radns", alpha_radns)
    t_gate = _require_positive("t_gate_ns", t_gate_ns)
    denom1 = delta - alpha
    denom2 = delta + alpha
    if abs(denom1) <= NUMERICAL_ZERO or abs(denom2) <= NUMERICAL_ZERO:
        raise ValueError(
            "static_zz_zeta singular: Delta too close to +/- alpha "
            f"(Delta={delta}, alpha={alpha})"
        )
    if alpha == 0.0:
        raise ValueError("cannot infer exchange J because zeta coefficient is zero")
    if phi == 0.0:
        return 0.0
    coeff_is_negative = (alpha < 0.0) != ((denom1 < 0.0) != (denom2 < 0.0))
    if (phi < 0.0) != coeff_is_negative:
        try:
            coefficient_description: float | str = static_zz_zeta(delta, alpha, 1.0)
        except ValueError:
            coefficient_description = "negative" if coeff_is_negative else "positive"
        raise ValueError(
            "phi sign is inconsistent with the static-ZZ coefficient; "
            f"phi={phi}, coeff={coefficient_description}, t_gate={t_gate}"
        )

    numerator = phi * denom1
    scaled_numerator = numerator * denom2
    denominator = alpha * t_gate
    j_squared = scaled_numerator / denominator if denominator != 0.0 else math.nan
    if all(
        math.isfinite(value) and abs(value) >= sys.float_info.min
        for value in (
            phi,
            alpha,
            t_gate,
            denom1,
            denom2,
            numerator,
            scaled_numerator,
            denominator,
            j_squared,
        )
    ) and j_squared < sys.float_info.max:
        return float(math.sqrt(j_squared))

    delta_exact = Fraction.from_float(delta)
    alpha_exact = Fraction.from_float(alpha)
    exact_j_squared = (
        Fraction.from_float(abs(phi))
        * abs(delta_exact - alpha_exact)
        * abs(delta_exact + alpha_exact)
        / (abs(alpha_exact) * Fraction.from_float(t_gate))
    )
    with localcontext() as context:
        context.prec = 300
        exact_j_squared_decimal = (
            Decimal(exact_j_squared.numerator)
            / Decimal(exact_j_squared.denominator)
        )
        recovered = _decimal_to_float64(exact_j_squared_decimal.sqrt())
    if not math.isfinite(recovered) or recovered <= 0.0:
        raise ValueError(
            "exchange_j_radns is not representable as a finite positive float64"
        )
    return recovered


def zz_phi_from_frequency_drift(z_t_radns: float, config: SourceCouplingConfig) -> tuple[float, float]:
    """Return ``(phi_rad, zeta_radns)`` after applying the detuning drift."""

    z = _require_finite("z_t_radns", z_t_radns)
    zz = config.zz
    delta = zz.base_delta_radns + z
    zeta = static_zz_zeta(delta, zz.alpha_radns, zz.exchange_j_radns)
    phi = scaled_product_ratio(
        zeta,
        zz.t_gate_ns,
        4.0,
        name="zz_phi_rad",
    )
    return phi, float(zeta)


def drift_to_t2(
    z_t_radns: float,
    config: SourceCouplingConfig | None = None,
) -> tuple[float, float]:
    """Map a source drift draw to ``(gamma_phi_per_ns, Tphi_ns)``.

    The map is class-(c): a positive log-rate modulation around the configured
    pure-dephasing base rate.
    """

    cfg = config or default_source_coupling_config()
    z = _require_finite("z_t_radns", z_t_radns)
    gamma_phi = _modulate_positive_rate(
        cfg.gamma_phi_base_per_ns,
        z,
        cfg.gamma_phi_sensitivity,
        name="gamma_phi_per_ns",
        x_scale=cfg.z_scale_radns,
    )
    if gamma_phi == 0.0:
        tphi_ns = math.inf
    else:
        tphi_ns = float(1.0 / gamma_phi)
        if not math.isfinite(tphi_ns):
            raise ValueError(
                "gamma_phi_per_ns is positive but its reciprocal is not "
                "representable as a finite float64 Tphi"
            )
    return gamma_phi, tphi_ns


def _params_from_draws(
    draws_radns: dict[str, float],
    cfg: SourceCouplingConfig,
    *,
    coupling_mode: Literal["shared", "independent"],
) -> CoupledNoiseParameters:
    draws = {key: _require_finite(f"draws_radns[{key}]", draws_radns[key]) for key in _SOURCE_KEYS}
    x = {
        key: scaled_product_ratio(
            1.0,
            draws[key],
            cfg.z_scale_radns,
            name=f"normalized_draws[{key}]",
        )
        if draws[key] != 0.0
        else draws[key]
        for key in _SOURCE_KEYS
    }
    zz_phi, zz_zeta = zz_phi_from_frequency_drift(draws["zz"], cfg)
    gamma_phi, tphi_ns = drift_to_t2(draws["gamma_phi"], cfg)
    drive_omega = _modulate_positive_rate(
        cfg.drive_omega_base_radns,
        draws["drive"],
        cfg.drive_omega_sensitivity,
        name="drive_omega_radns",
        x_scale=cfg.z_scale_radns,
    )
    return CoupledNoiseParameters(
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
            draws["spillover"],
            cfg.spillover_sensitivity,
            name="spillover_cx",
            x_scale=cfg.z_scale_radns,
        ),
        readout_flip_p=_modulate_probability_logit(
            cfg.readout_flip_base_p,
            draws["readout"],
            cfg.readout_flip_sensitivity,
            name="readout_flip_p",
            x_scale=cfg.z_scale_radns,
        ),
        reset_flip_p=_modulate_probability_logit(
            cfg.reset_flip_base_p,
            draws["reset"],
            cfg.reset_flip_sensitivity,
            name="reset_flip_p",
            x_scale=cfg.z_scale_radns,
        ),
        cz_depol_p=_modulate_probability_logit(
            cfg.cz_depol_base_p,
            draws["cz"],
            cfg.cz_depol_sensitivity,
            name="cz_depol_p",
            x_scale=cfg.z_scale_radns,
        ),
        coupling_mode=coupling_mode,
    )


def _modulate_positive_rate(
    base: float,
    x: float,
    sensitivity: float,
    *,
    name: str,
    x_scale: float = 1.0,
) -> float:
    base = _require_nonnegative(name + ".base", base)
    sens = _require_finite(name + ".sensitivity", sensitivity)
    xv = _require_finite(name + ".x", x)
    scale = _require_positive(name + ".x_scale", x_scale)
    try:
        shift = scaled_product_ratio(
            sens,
            xv,
            scale,
            name=f"{name}: sensitivity*x/x_scale",
        )
    except ValueError as exc:
        raise ValueError(
            f"{name}: sensitivity*x is not representable as a finite float64"
        ) from exc
    if shift == 0.0:
        return base
    if base == 0.0:
        raise ValueError(f"{name}: nonzero sensitivity cannot modulate a zero base rate")

    try:
        return scaled_exp_multiply(
            base,
            shift,
            name=f"{name}: modulated positive rate",
        )
    except ValueError as exc:
        raise ValueError(f"{name}: modulated positive rate is not representable") from exc


def _modulate_probability_logit(
    base_p: float,
    x: float,
    sensitivity: float,
    *,
    name: str,
    x_scale: float = 1.0,
) -> float:
    p = _validate_probability(name + ".base_p", base_p, allow_zero=True)
    sens = _require_finite(name + ".sensitivity", sensitivity)
    xv = _require_finite(name + ".x", x)
    scale = _require_positive(name + ".x_scale", x_scale)
    try:
        shift = scaled_product_ratio(
            sens,
            xv,
            scale,
            name=f"{name}: sensitivity*x/x_scale",
        )
    except ValueError as exc:
        raise ValueError(
            f"{name}: sensitivity*x is not representable as a finite float64"
        ) from exc
    if shift == 0.0:
        return p
    if p == 0.0:
        raise ValueError(f"{name}: nonzero sensitivity cannot logit-modulate p=0")

    return shifted_probability_from_odds(
        p,
        shift,
        name=f"{name}: modulated",
    )


def _as_1d_finite(name: str, values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(tuple(values), dtype=np.float64)
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError(f"{name} must be a non-empty 1-D trajectory")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def _snapshot_named_draws(values: Iterable[tuple[str, float]]) -> tuple[tuple[str, float], ...]:
    try:
        return tuple((str(key), float(value)) for key, value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError("draw entries must be (name, numeric value) pairs") from exc


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
    "CoupledNoiseParameters",
    "SourceCouplingConfig",
    "StaticZZParameters",
    "cross_mechanism_correlation",
    "default_source_coupling_config",
    "drift_to_t2",
    "exchange_j_from_phi",
    "independent_baseline_trajectory_to_params",
    "parameter_series",
    "source_to_params",
    "static_zz_zeta",
    "trajectory_to_params",
    "zz_phi_from_frequency_drift",
]
