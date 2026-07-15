from __future__ import annotations

"""Axis-2 source processes for cross-cycle coupled noise processes.

This module owns source timelines: explicit latent processes that persist across
QEC cycles and emit payloads consumed by ``source_coupling.Theta``. It is not a
channel assembler, not a Stim/DEM generator, and not an Axis-1 replacement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import numpy as np

from .coupling import (
    CoupledNoiseParameters,
    SourceCouplingConfig,
    independent_baseline_trajectory_to_params,
    trajectory_to_params,
)
from ..numerics import NUMERICAL_ZERO

_TWO_PI = 2.0 * math.pi
_PAULI_ORDER = ("I", "X", "Y", "Z")
SOURCE_TIMELINE_SCHEMA = "error_coupling_simulator.source.timeline.v1"


@dataclass(frozen=True)
class SourceTimeline:
    """Evaluator-side source truth for one shot or one replayable run.

    Arrays in ``payload`` and ``latent`` must have cycle as axis 0. Payload
    fields are the declared values downstream code may consume; latent fields
    remain evaluator-only truth for source audits.
    """

    name: str
    n_cycles: int
    cycle_time_ns: float
    payload: Mapping[str, Any]
    latent: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    seed: int | None = None
    coupling_mode: Literal["shared", "independent"] = "shared"
    schema: str = SOURCE_TIMELINE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SOURCE_TIMELINE_SCHEMA:
            raise ValueError(
                f"unsupported source timeline schema {self.schema!r}; "
                f"expected {SOURCE_TIMELINE_SCHEMA!r}"
            )
        object.__setattr__(self, "n_cycles", _require_positive_int("n_cycles", self.n_cycles))
        object.__setattr__(self, "cycle_time_ns", _require_positive("cycle_time_ns", self.cycle_time_ns))
        object.__setattr__(self, "payload", _coerce_array_map("payload", self.payload, self.n_cycles))
        object.__setattr__(self, "latent", _coerce_array_map("latent", self.latent, self.n_cycles))
        object.__setattr__(self, "metadata", dict(self.metadata))
        if self.coupling_mode not in {"shared", "independent"}:
            raise ValueError(f"coupling_mode must be 'shared' or 'independent', got {self.coupling_mode!r}")

    def payload_series(self, key: str) -> np.ndarray:
        if key not in self.payload:
            raise KeyError(key)
        return np.array(self.payload[key], copy=True)

    def latent_series(self, key: str) -> np.ndarray:
        if key not in self.latent:
            raise KeyError(key)
        return np.array(self.latent[key], copy=True)

    def independent_baseline(
        self,
        *,
        seed: int,
        payload_keys: Sequence[str] | None = None,
    ) -> SourceTimeline:
        """Row-preserving matched-marginal baseline.

        One cycle permutation is shared across the selected payload keys. This
        breaks temporal alignment while preserving same-cycle algebraic
        relations such as ``phase_rad = detuning_radns * window``.
        """

        rng = np.random.default_rng(int(seed))
        keys = tuple(payload_keys) if payload_keys is not None else tuple(self.payload)
        unknown = set(keys) - set(self.payload)
        if unknown:
            raise KeyError(f"unknown payload keys for baseline: {sorted(unknown)!r}")
        perm = rng.permutation(self.n_cycles)
        payload: dict[str, np.ndarray] = {}
        for key, value in self.payload.items():
            arr = np.array(value, copy=True)
            if key in keys:
                arr = arr[perm]
            payload[key] = arr
        metadata = dict(self.metadata)
        metadata.update(
            {
                "baseline_of": self.name,
                "baseline": "matched_marginal_row_preserving_cycle_permutation",
                "baseline_seed": int(seed),
                "permuted_payload_keys": list(keys),
            }
        )
        return SourceTimeline(
            name=f"{self.name}.independent_baseline",
            n_cycles=self.n_cycles,
            cycle_time_ns=self.cycle_time_ns,
            payload=payload,
            latent={},
            metadata=metadata,
            seed=int(seed),
            coupling_mode="independent",
        )

    def per_field_independent_ablation(
        self,
        *,
        seed: int,
        payload_keys: Sequence[str] | None = None,
    ) -> SourceTimeline:
        """Unphysical ablation that independently permutes each payload field.

        Use this only to destroy cross-field alignment deliberately. It is not a
        physically valid matched source when payload fields are derived from the
        same latent event row.
        """

        rng = np.random.default_rng(int(seed))
        keys = tuple(payload_keys) if payload_keys is not None else tuple(self.payload)
        unknown = set(keys) - set(self.payload)
        if unknown:
            raise KeyError(f"unknown payload keys for ablation: {sorted(unknown)!r}")
        payload: dict[str, np.ndarray] = {}
        for key, value in self.payload.items():
            arr = np.array(value, copy=True)
            if key in keys:
                arr = arr[rng.permutation(self.n_cycles)]
            payload[key] = arr
        metadata = dict(self.metadata)
        metadata.update(
            {
                "ablation_of": self.name,
                "ablation": "per_field_independent_cycle_permutation_unphysical",
                "ablation_seed": int(seed),
                "permuted_payload_keys": list(keys),
            }
        )
        return SourceTimeline(
            name=f"{self.name}.per_field_independent_ablation",
            n_cycles=self.n_cycles,
            cycle_time_ns=self.cycle_time_ns,
            payload=payload,
            latent={},
            metadata=metadata,
            seed=int(seed),
            coupling_mode="independent",
        )

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "name": self.name,
            "n_cycles": int(self.n_cycles),
            "cycle_time_ns": float(self.cycle_time_ns),
            "seed": None if self.seed is None else int(self.seed),
            "coupling_mode": self.coupling_mode,
            "payload": {key: _array_summary(value) for key, value in self.payload.items()},
            "latent": {key: _array_summary(value) for key, value in self.latent.items()},
            "metadata": dict(self.metadata),
        }

    def save_npz(self, path: str | Path) -> Path:
        """Persist exact payload/latent arrays plus a hash-bearing manifest."""

        out = Path(path)
        payload_arrays: dict[str, str] = {}
        latent_arrays: dict[str, str] = {}
        arrays: dict[str, np.ndarray] = {}
        for i, (key, value) in enumerate(self.payload.items()):
            array_name = f"payload_{i}"
            payload_arrays[str(key)] = array_name
            arrays[array_name] = np.array(value, copy=True)
        for i, (key, value) in enumerate(self.latent.items()):
            array_name = f"latent_{i}"
            latent_arrays[str(key)] = array_name
            arrays[array_name] = np.array(value, copy=True)
        manifest = self.to_manifest()
        manifest["artifact"] = "exact_source_timeline_npz"
        manifest["payload_arrays"] = payload_arrays
        manifest["latent_arrays"] = latent_arrays
        arrays["__manifest_json__"] = np.asarray(json.dumps(_json_safe(manifest), sort_keys=True))
        np.savez_compressed(out, **arrays)
        return out

    @classmethod
    def load_npz(cls, path: str | Path) -> SourceTimeline:
        """Load a timeline written by :meth:`save_npz`."""

        with np.load(Path(path), allow_pickle=False) as data:
            if "__manifest_json__" not in data:
                raise ValueError("source timeline NPZ missing __manifest_json__")
            manifest = json.loads(str(data["__manifest_json__"].item()))
            if manifest.get("schema") != SOURCE_TIMELINE_SCHEMA:
                raise ValueError(
                    f"unsupported source timeline schema {manifest.get('schema')!r}; "
                    f"expected {SOURCE_TIMELINE_SCHEMA!r}"
                )
            payload = _load_npz_array_map(
                data,
                manifest,
                arrays_key="payload_arrays",
                summary_key="payload",
            )
            latent = _load_npz_array_map(
                data,
                manifest,
                arrays_key="latent_arrays",
                summary_key="latent",
            )
        return cls(
            name=manifest["name"],
            n_cycles=int(manifest["n_cycles"]),
            cycle_time_ns=float(manifest["cycle_time_ns"]),
            payload=payload,
            latent=latent,
            metadata=manifest.get("metadata", {}),
            seed=manifest.get("seed"),
            coupling_mode=manifest.get("coupling_mode", "shared"),
            schema=manifest["schema"],
        )


class SourceProcess(ABC):
    """Base protocol for explicit cross-cycle source processes."""

    @abstractmethod
    def sample(self, *, seed: int, n_cycles: int, layout: Any = None) -> SourceTimeline:
        """Sample one replayable source timeline."""


@dataclass(frozen=True)
class RTNSource(SourceProcess):
    """Single random-telegraph frequency-like source.

    ``gamma_per_cycle`` is the continuous-time switching rate multiplied by the
    QEC-cycle duration. The exact discrete flip probability is
    ``0.5 * (1 - exp(-2 gamma_per_cycle))``, giving latent autocorrelation
    ``exp(-2 gamma_per_cycle * lag)``.
    """

    amplitude_radns: float = 1.0e-4
    gamma_per_cycle: float = 0.05
    cycle_time_ns: float = 1_000.0
    name: str = "rtn"

    def __post_init__(self) -> None:
        _require_nonnegative("amplitude_radns", self.amplitude_radns)
        _require_nonnegative("gamma_per_cycle", self.gamma_per_cycle)
        _require_positive("cycle_time_ns", self.cycle_time_ns)

    @property
    def flip_probability(self) -> float:
        return _rtn_flip_probability(float(self.gamma_per_cycle))

    @property
    def autocorr_base(self) -> float:
        return float(math.exp(-2.0 * float(self.gamma_per_cycle)))

    def sample(self, *, seed: int, n_cycles: int, layout: Any = None) -> SourceTimeline:
        n = _require_positive_int("n_cycles", n_cycles)
        rng = np.random.default_rng(int(seed))
        states = _sample_rtn_states(rng, n, float(self.gamma_per_cycle))
        z = float(self.amplitude_radns) * states.astype(np.float64)
        return SourceTimeline(
            name=self.name,
            n_cycles=n,
            cycle_time_ns=float(self.cycle_time_ns),
            payload={"z_radns": z},
            latent={"rtn_state": states},
            metadata={
                "source": "RTNSource",
                "value_provenance": {
                    "parameter_values": "project-design",
                    "claims_hardware_calibration": False,
                },
                "amplitude_radns": float(self.amplitude_radns),
                "gamma_per_cycle": float(self.gamma_per_cycle),
                "flip_probability": self.flip_probability,
                "autocorr_base": self.autocorr_base,
                "layout_site_count": _layout_site_count(layout, default=1),
            },
            seed=int(seed),
        )


@dataclass(frozen=True)
class OneOverFDriftSource(SourceProcess):
    """Finite log-spaced sum of RTNs with analytic sum-of-Lorentzians PSD."""

    amplitude_radns: float = 1.0e-4
    n_fluctuators: int = 8
    gamma_min_per_cycle: float = 0.005
    gamma_max_per_cycle: float = 0.5
    cycle_time_ns: float = 1_000.0
    name: str = "one_over_f_drift"

    def __post_init__(self) -> None:
        _require_nonnegative("amplitude_radns", self.amplitude_radns)
        _require_positive_int("n_fluctuators", self.n_fluctuators)
        _require_positive("gamma_min_per_cycle", self.gamma_min_per_cycle)
        _require_positive("gamma_max_per_cycle", self.gamma_max_per_cycle)
        if float(self.gamma_max_per_cycle) < float(self.gamma_min_per_cycle):
            raise ValueError("gamma_max_per_cycle must be >= gamma_min_per_cycle")
        _require_positive("cycle_time_ns", self.cycle_time_ns)

    @property
    def gammas_per_cycle(self) -> np.ndarray:
        return np.geomspace(
            float(self.gamma_min_per_cycle),
            float(self.gamma_max_per_cycle),
            int(self.n_fluctuators),
        )

    @property
    def amplitudes_radns(self) -> np.ndarray:
        return np.full(
            int(self.n_fluctuators),
            float(self.amplitude_radns) / math.sqrt(float(self.n_fluctuators)),
            dtype=np.float64,
        )

    def analytic_psd(self, omega_per_cycle: np.ndarray | Sequence[float]) -> np.ndarray:
        """Closed-form finite RTN sum ``sum v_k^2 4g_k / ((2g_k)^2 + omega^2)``."""

        omega = np.asarray(omega_per_cycle, dtype=np.float64)
        if not np.all(np.isfinite(omega)):
            raise ValueError("omega_per_cycle contains non-finite values")
        out = np.zeros_like(omega, dtype=np.float64)
        for gamma, amp in zip(self.gammas_per_cycle, self.amplitudes_radns, strict=True):
            out += amp * amp * (4.0 * gamma) / ((2.0 * gamma) ** 2 + omega * omega)
        return out

    def sample(self, *, seed: int, n_cycles: int, layout: Any = None) -> SourceTimeline:
        n = _require_positive_int("n_cycles", n_cycles)
        rng = np.random.default_rng(int(seed))
        states = np.empty((n, int(self.n_fluctuators)), dtype=np.int8)
        for j, gamma in enumerate(self.gammas_per_cycle):
            states[:, j] = _sample_rtn_states(rng, n, float(gamma))
        z = states.astype(np.float64) @ self.amplitudes_radns
        return SourceTimeline(
            name=self.name,
            n_cycles=n,
            cycle_time_ns=float(self.cycle_time_ns),
            payload={"z_radns": z},
            latent={"rtn_states": states},
            metadata={
                "source": "OneOverFDriftSource",
                "value_provenance": {
                    "parameter_values": "project-design",
                    "claims_hardware_calibration": False,
                },
                "amplitude_radns": float(self.amplitude_radns),
                "n_fluctuators": int(self.n_fluctuators),
                "gamma_min_per_cycle": float(self.gamma_min_per_cycle),
                "gamma_max_per_cycle": float(self.gamma_max_per_cycle),
                "gammas_per_cycle": self.gammas_per_cycle.tolist(),
                "amplitudes_radns": self.amplitudes_radns.tolist(),
                "layout_site_count": _layout_site_count(layout, default=1),
            },
            seed=int(seed),
        )


@dataclass(frozen=True)
class PhaseBurstSource(SourceProcess):
    """Gap-engineered hardware phase-burst source.

    The phase component follows ``delta_f(t)=delta_f(0)/(1+t/t_rec)``. Frequency
    shifts are stored in MHz and converted to angular rad/ns payloads.
    """

    site_count: int = 1
    event_probability_per_cycle: float = 0.0
    event_times: tuple[int, ...] | None = None
    peak_shift_mhz: float = -2.0
    peak_jitter_mhz: float = 0.0
    recovery_time_ns: float = 1.0e6
    t1_duration_ns: float = 10_000.0
    cycle_time_ns: float = 1_000.0
    phase_window_ns: float = 1_000.0
    echo_suppression: float = 0.05
    footprint: Literal["uniform", "cluster"] = "uniform"
    affected_sites: int | None = None
    name: str = "phase_burst"

    def __post_init__(self) -> None:
        _require_positive_int("site_count", self.site_count)
        _validate_probability("event_probability_per_cycle", self.event_probability_per_cycle, allow_zero=True)
        _require_finite("peak_shift_mhz", self.peak_shift_mhz)
        _require_nonnegative("peak_jitter_mhz", self.peak_jitter_mhz)
        _require_positive("recovery_time_ns", self.recovery_time_ns)
        _require_nonnegative("t1_duration_ns", self.t1_duration_ns)
        _require_positive("cycle_time_ns", self.cycle_time_ns)
        _require_nonnegative("phase_window_ns", self.phase_window_ns)
        if not 0.0 <= float(self.echo_suppression) <= 1.0:
            raise ValueError("echo_suppression must be in [0, 1]")
        if self.footprint not in {"uniform", "cluster"}:
            raise ValueError("footprint must be 'uniform' or 'cluster'")
        if self.affected_sites is not None:
            _require_positive_int("affected_sites", self.affected_sites)

    def sample(self, *, seed: int, n_cycles: int, layout: Any = None) -> SourceTimeline:
        n = _require_positive_int("n_cycles", n_cycles)
        site_count = _layout_site_count(layout, default=int(self.site_count))
        rng = np.random.default_rng(int(seed))
        event_times = self._event_times(rng, n)
        delta_mhz = np.zeros((n, site_count), dtype=np.float64)
        event_start = np.zeros(n, dtype=np.int8)
        t1_burst = np.zeros((n, site_count), dtype=np.float64)
        event_site_mask = np.zeros((n, site_count), dtype=np.int8)
        t1_cycles = int(math.ceil(float(self.t1_duration_ns) / float(self.cycle_time_ns)))
        for t0 in event_times:
            if t0 < 0 or t0 >= n:
                raise ValueError(f"event time {t0} outside n_cycles={n}")
            event_start[t0] = 1
            amp = self._footprint_amplitudes(rng, site_count, layout)
            affected = amp != 0.0
            event_site_mask[t0, affected] = 1
            elapsed = (np.arange(t0, n, dtype=np.float64) - float(t0)) * float(self.cycle_time_ns)
            decay = 1.0 / (1.0 + elapsed / float(self.recovery_time_ns))
            delta_mhz[t0:n, :] += decay[:, None] * amp[None, :]
            if t1_cycles > 0 and np.any(affected):
                t1_burst[t0 : min(n, t0 + t1_cycles), affected] = 1.0
        detuning_radns = _mhz_to_radns(delta_mhz)
        phase_rad = detuning_radns * float(self.phase_window_ns)
        return SourceTimeline(
            name=self.name,
            n_cycles=n,
            cycle_time_ns=float(self.cycle_time_ns),
            payload={
                "z_radns": np.mean(detuning_radns, axis=1),
                "delta_fq_mhz": delta_mhz,
                "detuning_radns": detuning_radns,
                "phase_rad": phase_rad,
                "echoed_phase_rad": phase_rad * float(self.echo_suppression),
                "t1_burst": t1_burst,
            },
            latent={"event_start": event_start, "event_site_mask": event_site_mask},
            metadata={
                "source": "PhaseBurstSource",
                "event_times": event_times,
                "peak_shift_mhz": float(self.peak_shift_mhz),
                "peak_jitter_mhz": float(self.peak_jitter_mhz),
                "recovery_time_ns": float(self.recovery_time_ns),
                "t1_duration_ns": float(self.t1_duration_ns),
                "phase_window_ns": float(self.phase_window_ns),
                "echo_suppression": float(self.echo_suppression),
                "footprint": self.footprint,
                "site_count": int(site_count),
            },
            seed=int(seed),
        )

    def _event_times(self, rng: np.random.Generator, n_cycles: int) -> tuple[int, ...]:
        if self.event_times is not None:
            return tuple(
                _require_nonnegative_int(f"event_times[{i}]", t)
                for i, t in enumerate(self.event_times)
            )
        draws = rng.random(n_cycles) < float(self.event_probability_per_cycle)
        return tuple(int(t) for t in np.flatnonzero(draws))

    def _footprint_amplitudes(self, rng: np.random.Generator, site_count: int, layout: Any = None) -> np.ndarray:
        amp = float(self.peak_shift_mhz)
        if float(self.peak_jitter_mhz) > 0.0:
            amp += float(rng.normal(0.0, float(self.peak_jitter_mhz)))
        out = np.zeros(site_count, dtype=np.float64)
        if self.footprint == "uniform":
            out[:] = amp
            return out
        affected = _cluster_affected_count(self.affected_sites, site_count)
        out[_cluster_indices(rng, site_count, affected=affected, layout=layout)] = amp
        return out


@dataclass(frozen=True)
class TemporalStormSPPSource(SourceProcess):
    """Two-state temporal-storm SPP/HMM reduced Pauli comparator."""

    a: float = 0.01
    b: float = 0.10
    q_calm: tuple[float, float, float, float] = (0.999, 1.0 / 3000.0, 1.0 / 3000.0, 1.0 / 3000.0)
    q_storm: tuple[float, float, float, float] = (0.97, 0.01, 0.01, 0.01)
    site_count: int = 1
    scope: Literal["global", "cluster", "per_site"] = "global"
    affected_sites: int | None = None
    cycle_time_ns: float = 1_000.0
    name: str = "temporal_storm_spp"

    def __post_init__(self) -> None:
        _validate_probability("a", self.a, allow_zero=True)
        _validate_probability("b", self.b, allow_zero=True)
        if float(self.a) + float(self.b) >= 1.0:
            raise ValueError("a + b must be < 1 for positive correlation length")
        _validate_distribution("q_calm", self.q_calm)
        _validate_distribution("q_storm", self.q_storm)
        _require_positive_int("site_count", self.site_count)
        if self.scope not in {"global", "cluster", "per_site"}:
            raise ValueError("scope must be 'global', 'cluster', or 'per_site'")
        if self.affected_sites is not None:
            _require_positive_int("affected_sites", self.affected_sites)
        _require_positive("cycle_time_ns", self.cycle_time_ns)

    @classmethod
    def from_fixed_marginal(
        cls,
        *,
        marginal: Sequence[float],
        q_storm: Sequence[float],
        storm_probability: float,
        correlation_length_cycles: float,
        **kwargs: Any,
    ) -> TemporalStormSPPSource:
        """Build a family member with fixed one-cycle Pauli marginal.

        Varying ``correlation_length_cycles`` changes the HMM memory while
        holding the emitted one-cycle marginal fixed.
        """

        p = _validate_distribution("marginal", marginal)
        q1 = _validate_distribution("q_storm", q_storm)
        pi1 = _validate_probability("storm_probability", storm_probability, allow_zero=False)
        xi = _require_positive("correlation_length_cycles", correlation_length_cycles)
        # pi1 in (0, 1) is guaranteed by _validate_probability(allow_zero=False) above, so 1 - pi1 > 0.
        q0 = tuple((p_i - pi1 * q_i) / (1.0 - pi1) for p_i, q_i in zip(p, q1, strict=True))
        _validate_distribution("implied q_calm", q0)
        s = 1.0 - math.exp(-1.0 / xi)
        return cls(a=pi1 * s, b=(1.0 - pi1) * s, q_calm=q0, q_storm=tuple(q1), **kwargs)

    @property
    def transition_matrix(self) -> np.ndarray:
        return np.asarray(
            [[1.0 - float(self.a), float(self.a)], [float(self.b), 1.0 - float(self.b)]],
            dtype=np.float64,
        )

    @property
    def stationary_distribution(self) -> np.ndarray:
        denom = float(self.a) + float(self.b)
        if denom <= NUMERICAL_ZERO:
            return np.asarray([1.0, 0.0], dtype=np.float64)
        return np.asarray([float(self.b) / denom, float(self.a) / denom], dtype=np.float64)

    @property
    def correlation_length_cycles(self) -> float:
        lam2 = 1.0 - float(self.a) - float(self.b)
        if lam2 >= 1.0:
            return math.inf
        return float(-1.0 / math.log(lam2))

    @property
    def marginal_distribution(self) -> np.ndarray:
        pi = self.stationary_distribution
        return pi[0] * np.asarray(self.q_calm, dtype=np.float64) + pi[1] * np.asarray(self.q_storm, dtype=np.float64)

    def sample(self, *, seed: int, n_cycles: int, layout: Any = None) -> SourceTimeline:
        n = _require_positive_int("n_cycles", n_cycles)
        site_count = _layout_site_count(layout, default=int(self.site_count))
        rng = np.random.default_rng(int(seed))
        hidden_shape = (n, site_count) if self.scope == "per_site" else (n, 1)
        hidden = np.empty(hidden_shape, dtype=np.int8)
        hidden[0, :] = rng.choice(2, size=hidden_shape[1], p=self.stationary_distribution)
        for t in range(1, n):
            prev = hidden[t - 1]
            flip_up = (prev == 0) & (rng.random(prev.shape) < float(self.a))
            flip_down = (prev == 1) & (rng.random(prev.shape) < float(self.b))
            cur = np.array(prev, copy=True)
            cur[flip_up] = 1
            cur[flip_down] = 0
            hidden[t] = cur
        if self.scope == "global":
            hidden_sites = np.repeat(hidden, site_count, axis=1)
            cluster_mask = np.ones((n, site_count), dtype=np.int8)
        elif self.scope == "cluster":
            affected = _cluster_affected_count(self.affected_sites, site_count)
            idx = _cluster_indices(rng, site_count, affected=affected, layout=layout)
            hidden_sites = np.zeros((n, site_count), dtype=np.int8)
            hidden_sites[:, idx] = hidden
            cluster_mask = np.zeros((n, site_count), dtype=np.int8)
            cluster_mask[:, idx] = 1
        else:
            hidden_sites = hidden
            cluster_mask = np.ones((n, site_count), dtype=np.int8)
        emissions = np.empty((n, site_count), dtype=np.int8)
        storm_indicator = hidden_sites.astype(np.float64)
        q = np.vstack([np.asarray(self.q_calm, dtype=np.float64), np.asarray(self.q_storm, dtype=np.float64)])
        for t in range(n):
            for i in range(site_count):
                emissions[t, i] = int(rng.choice(4, p=q[int(hidden_sites[t, i])]))
        return SourceTimeline(
            name=self.name,
            n_cycles=n,
            cycle_time_ns=float(self.cycle_time_ns),
            payload={
                "pauli_error": emissions,
                "storm_indicator": storm_indicator,
                "cluster_mask": cluster_mask,
            },
            latent={"storm_state": hidden_sites},
            metadata={
                "source": "TemporalStormSPPSource",
                "a": float(self.a),
                "b": float(self.b),
                "transition_matrix": self.transition_matrix.tolist(),
                "stationary_distribution": self.stationary_distribution.tolist(),
                "correlation_length_cycles": self.correlation_length_cycles,
                "pauli_order": _PAULI_ORDER,
                "marginal_distribution": self.marginal_distribution.tolist(),
                "scope": self.scope,
                "affected_sites": None if self.affected_sites is None else int(self.affected_sites),
                "site_count": int(site_count),
                "boundary": "reduced_pauli_comparator_not_analog_truth",
            },
            seed=int(seed),
        )

    def empirical_transition_matrix(self, timeline: SourceTimeline) -> np.ndarray:
        """Estimate the hidden-state transition matrix from evaluator-side truth."""

        states = timeline.latent_series("storm_state").astype(np.int8)
        if states.shape[0] < 2:
            raise ValueError("need at least two cycles to estimate transitions")
        cluster_mask = np.asarray(timeline.payload.get("cluster_mask", np.ones_like(states)), dtype=bool)
        valid = cluster_mask[:-1] & cluster_mask[1:]
        prev = states[:-1][valid].reshape(-1)
        cur = states[1:][valid].reshape(-1)
        if prev.size == 0:
            raise ValueError("no active storm sites available for transition estimate")
        counts = np.zeros((2, 2), dtype=np.float64)
        for p, c in zip(prev, cur, strict=True):
            counts[int(p), int(c)] += 1.0
        rows = counts.sum(axis=1)
        out = np.zeros((2, 2), dtype=np.float64)
        for i in range(2):
            if rows[i] > 0.0:
                out[i] = counts[i] / rows[i]
        return out

    def empirical_pauli_distribution(self, timeline: SourceTimeline) -> np.ndarray:
        """Return empirical ``(I, X, Y, Z)`` frequencies from emitted payload."""

        emissions = timeline.payload_series("pauli_error").astype(np.int64).reshape(-1)
        if np.any((emissions < 0) | (emissions > 3)):
            raise ValueError("pauli_error payload contains labels outside I=0, X=1, Y=2, Z=3")
        counts = np.bincount(emissions, minlength=4).astype(np.float64)
        total = float(np.sum(counts))
        if total <= 0.0:
            raise ValueError("empty pauli_error payload")
        return counts / total

    def observed_pauli_indicator_autocorrelation(
        self,
        timeline: SourceTimeline,
        *,
        pauli: int = 1,
        lag: int = 1,
    ) -> float:
        """Autocorrelation of an observed Pauli indicator, averaged over sites."""

        if pauli < 0 or pauli > 3:
            raise ValueError("pauli must be ordered as I=0, X=1, Y=2, Z=3")
        indicator = (timeline.payload_series("pauli_error") == int(pauli)).astype(np.float64)
        return lag_autocorrelation(indicator, lag=lag)


def timeline_to_coupled_params(
    timeline: SourceTimeline,
    config: SourceCouplingConfig | None = None,
    *,
    payload_key: str = "z_radns",
    independent_seed: int | None = None,
) -> tuple[CoupledNoiseParameters, ...]:
    """Feed a scalar source payload trajectory into the existing ``Theta`` fan-out."""

    z = timeline.payload_series(payload_key)
    if z.ndim != 1:
        raise ValueError(f"payload {payload_key!r} must be 1-D to feed SourceCouplingConfig")
    if timeline.coupling_mode == "shared":
        return trajectory_to_params(z, config)
    seed = independent_seed
    if seed is None:
        seed = int(timeline.metadata.get("baseline_seed", timeline.seed if timeline.seed is not None else 0))
    return independent_baseline_trajectory_to_params(z, config, seed=int(seed))


def timeline_to_site_coupled_params(
    timeline: SourceTimeline,
    config: SourceCouplingConfig | None = None,
    *,
    payload_key: str = "detuning_radns",
    independent_seed: int | None = None,
) -> tuple[tuple[CoupledNoiseParameters, ...], ...]:
    """Feed a ``(cycle, site)`` payload into per-site ``Theta`` fan-out.

    The return value is cycle-major: ``params[cycle][site]``.
    """

    z = timeline.payload_series(payload_key)
    if z.ndim != 2:
        raise ValueError(f"payload {payload_key!r} must be 2-D with shape (cycle, site)")
    site_series: list[tuple[CoupledNoiseParameters, ...]] = []
    for site in range(z.shape[1]):
        if timeline.coupling_mode == "shared":
            site_series.append(trajectory_to_params(z[:, site], config))
        else:
            seed = independent_seed
            if seed is None:
                seed = int(timeline.metadata.get("baseline_seed", timeline.seed if timeline.seed is not None else 0))
            site_series.append(independent_baseline_trajectory_to_params(z[:, site], config, seed=int(seed) + site))
    return tuple(tuple(site_series[site][cycle] for site in range(z.shape[1])) for cycle in range(z.shape[0]))


def lag_autocorrelation(values: np.ndarray | Sequence[float], lag: int = 1) -> float:
    """Pearson autocorrelation at a positive lag."""

    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 1:
        arr = arr.reshape(arr.shape[0], -1).mean(axis=1)
    lag = _require_positive_int("lag", lag)
    if arr.size <= lag:
        raise ValueError("not enough samples for requested lag")
    a = arr[:-lag]
    b = arr[lag:]
    if float(np.std(a)) <= NUMERICAL_ZERO or float(np.std(b)) <= NUMERICAL_ZERO:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _sample_rtn_states(rng: np.random.Generator, n_cycles: int, gamma_per_cycle: float) -> np.ndarray:
    p_flip = _rtn_flip_probability(gamma_per_cycle)
    states = np.empty(n_cycles, dtype=np.int8)
    states[0] = 1 if rng.random() < 0.5 else -1
    for t in range(1, n_cycles):
        states[t] = -states[t - 1] if rng.random() < p_flip else states[t - 1]
    return states


def _rtn_flip_probability(gamma_per_cycle: float) -> float:
    gamma = _require_nonnegative("gamma_per_cycle", gamma_per_cycle)
    return float(0.5 * (1.0 - math.exp(-2.0 * gamma)))


def _mhz_to_radns(delta_mhz: np.ndarray) -> np.ndarray:
    return _TWO_PI * np.asarray(delta_mhz, dtype=np.float64) * 1.0e-3


def _layout_site_count(layout: Any, *, default: int) -> int:
    if layout is None:
        return _require_positive_int("default", default)
    if isinstance(layout, int):
        return _require_positive_int("layout", layout)
    if isinstance(layout, Mapping):
        for key in ("site_count", "n_qubits", "num_qubits"):
            if key in layout:
                return _require_positive_int(f"layout[{key!r}]", layout[key])
    if hasattr(layout, "num_qubits"):
        return _require_positive_int("layout.num_qubits", getattr(layout, "num_qubits"))
    if hasattr(layout, "n_qubits"):
        return _require_positive_int("layout.n_qubits", getattr(layout, "n_qubits"))
    return _require_positive_int("default", default)


def _cluster_indices(
    rng: np.random.Generator,
    site_count: int,
    *,
    affected: int,
    layout: Any = None,
) -> np.ndarray:
    center = _layout_cluster_center(layout)
    if center is None:
        center = int(rng.integers(0, site_count))
    center = _require_site_index("cluster_center", center, site_count)
    coords = _layout_coordinates(layout, site_count)
    if coords is not None:
        dist = np.sum((coords - coords[center]) ** 2, axis=1)
        return np.argsort(dist, kind="stable")[:affected]
    offsets = np.argsort(np.abs(np.arange(site_count) - center), kind="stable")[:affected]
    return offsets.astype(np.int64)


def _cluster_affected_count(affected_sites: int | None, site_count: int) -> int:
    affected = int(affected_sites) if affected_sites is not None else max(1, round(math.sqrt(site_count)))
    if affected > site_count:
        raise ValueError(f"affected_sites={affected} exceeds site_count={site_count}")
    return affected


def _layout_cluster_center(layout: Any) -> int | None:
    if layout is None:
        return None
    if isinstance(layout, Mapping):
        for key in ("cluster_center", "phase_burst_center"):
            if key in layout:
                return _require_nonnegative_int(f"layout[{key!r}]", layout[key])
    metadata = getattr(layout, "metadata", None)
    if isinstance(metadata, Mapping):
        for key in ("cluster_center", "phase_burst_center"):
            if key in metadata:
                return _require_nonnegative_int(f"layout.metadata[{key!r}]", metadata[key])
    return None


def _layout_coordinates(layout: Any, site_count: int) -> np.ndarray | None:
    raw = None
    if isinstance(layout, Mapping):
        raw = layout.get("qubit_coords", layout.get("coordinates", layout.get("coords")))
    if raw is None:
        metadata = getattr(layout, "metadata", None)
        if isinstance(metadata, Mapping):
            raw = metadata.get("qubit_coords", metadata.get("coordinates", metadata.get("coords")))
    if raw is None:
        return None
    if isinstance(raw, Mapping):
        ordered: list[Sequence[float]] = []
        for i in range(site_count):
            value = raw.get(i, raw.get(str(i)))
            if value is None:
                raise ValueError(f"layout coordinates missing site {i}")
            ordered.append(value)
        coords = np.asarray(ordered, dtype=np.float64)
    else:
        coords = np.asarray(raw, dtype=np.float64)
    if coords.ndim != 2 or coords.shape[0] != site_count or coords.shape[1] == 0:
        raise ValueError(
            "layout coordinates must have shape (site_count, coord_dim), "
            f"got {coords.shape} for site_count={site_count}"
        )
    if not np.all(np.isfinite(coords)):
        raise ValueError("layout coordinates contain non-finite values")
    return coords


def _load_npz_array_map(
    data: np.lib.npyio.NpzFile,
    manifest: Mapping[str, Any],
    *,
    arrays_key: str,
    summary_key: str,
) -> dict[str, np.ndarray]:
    arrays = manifest.get(arrays_key)
    summaries = manifest.get(summary_key)
    if not isinstance(arrays, Mapping) or not isinstance(summaries, Mapping):
        raise ValueError(f"source timeline NPZ manifest missing {arrays_key!r}/{summary_key!r}")
    out: dict[str, np.ndarray] = {}
    for key, array_name in arrays.items():
        if array_name not in data:
            raise ValueError(f"source timeline NPZ missing array {array_name!r} for {summary_key}[{key!r}]")
        arr = np.array(data[array_name], copy=True)
        summary = summaries.get(key)
        if not isinstance(summary, Mapping) or "sha256" not in summary:
            raise ValueError(f"source timeline NPZ manifest missing sha256 for {summary_key}[{key!r}]")
        actual = _array_sha256(arr)
        expected = str(summary["sha256"])
        if actual != expected:
            raise ValueError(
                f"source timeline NPZ hash mismatch for {summary_key}[{key!r}]: "
                f"manifest={expected}, actual={actual}"
            )
        out[str(key)] = arr
    return out


def _require_site_index(name: str, value: int, site_count: int) -> int:
    index = _require_nonnegative_int(name, value)
    if index >= site_count:
        raise ValueError(f"{name}={index} outside site_count={site_count}")
    return index


def _coerce_array_map(name: str, values: Mapping[str, Any], n_cycles: int) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for key, value in dict(values).items():
        arr = np.asarray(value)
        if arr.ndim == 0 or arr.shape[0] != n_cycles:
            raise ValueError(f"{name}[{key!r}] must have cycle axis length {n_cycles}")
        if np.issubdtype(arr.dtype, np.number) and not np.all(np.isfinite(arr.astype(np.float64))):
            raise ValueError(f"{name}[{key!r}] contains non-finite values")
        out[str(key)] = np.array(arr, copy=True)
    return out


def _array_summary(arr: np.ndarray) -> dict[str, Any]:
    value = np.asarray(arr)
    summary: dict[str, Any] = {
        "shape": list(value.shape),
        "dtype": str(value.dtype),
    }
    if np.issubdtype(value.dtype, np.number):
        numeric = value.astype(np.float64)
        summary.update(
            {
                "min": float(np.min(numeric)),
                "max": float(np.max(numeric)),
                "mean": float(np.mean(numeric)),
                "std": float(np.std(numeric)),
                "sha256": _array_sha256(value),
            }
        )
    return summary


def _array_sha256(arr: np.ndarray) -> str:
    value = np.ascontiguousarray(arr)
    h = hashlib.sha256()
    h.update(str(value.dtype).encode("utf-8"))
    h.update(json.dumps(list(value.shape)).encode("utf-8"))
    h.update(value.view(np.uint8))
    return h.hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _validate_distribution(name: str, probs: Sequence[float]) -> tuple[float, ...]:
    if len(probs) != 4:
        raise ValueError(f"{name} must have four probabilities ordered as {_PAULI_ORDER!r}")
    vals = tuple(_require_finite(f"{name}[{i}]", p) for i, p in enumerate(probs))
    for i, value in enumerate(vals):
        if value < 0.0 or value > 1.0:
            raise ValueError(f"{name}[{i}] must be in [0, 1], got {value!r}")
    total = math.fsum(vals)
    if abs(total - 1.0) > 1e-12:
        raise ValueError(f"{name} must sum to 1, got {total}")
    return vals


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


def _require_positive_int(name: str, value: int) -> int:
    v = _require_integral(name, value)
    if v <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    return v


def _require_nonnegative_int(name: str, value: int) -> int:
    v = _require_integral(name, value)
    if v < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}")
    return v


def _require_integral(name: str, value: int) -> int:
    if isinstance(value, bool) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an integer, got {value!r}")
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        fv = float(value)
        if math.isfinite(fv) and fv.is_integer():
            return int(fv)
    raise ValueError(f"{name} must be an integer, got {value!r}")


__all__ = [
    "OneOverFDriftSource",
    "PhaseBurstSource",
    "RTNSource",
    "SourceProcess",
    "SourceTimeline",
    "TemporalStormSPPSource",
    "lag_autocorrelation",
    "timeline_to_coupled_params",
    "timeline_to_site_coupled_params",
]
