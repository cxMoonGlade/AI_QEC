from __future__ import annotations

"""Simulator-facing adapter for the in-house exact qutrit leakage backend.

This is deliberately not a Stim/DEM path: leakage lives outside the qubit
computational subspace, so the carrier is the project's own QutritDM exact
density-matrix backend and the Wood-Gambetta qutrit Kraus family.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from qec_twin.forward.exact.qutrit_dm import CDTYPE, QutritDM
from qec_twin.mechanisms.qutrit_teachers import (
    G_HEAT_DEFAULT,
    G_SEEP_DEFAULT,
    THETA_DEFAULT,
    coherence_of_leakage,
    leakage_kraus_torch,
    wg_rates,
)

QUTRIT_STRING_CONVENTION = "qutrit_dm_most_significant_q0_left_to_right"
MAX_EXACT_QUTRITS = 9


@dataclass(frozen=True)
class QutritLeakageArtifacts:
    out_dir: Path
    density_matrix: Path | None
    joint_probabilities: Path
    site_populations: Path
    measurement_counts: Path
    theory_prediction: Path
    manifest: Path


@dataclass(frozen=True)
class QutritLeakageResult:
    num_qutrits: int
    initial_levels: tuple[int, ...]
    sites: tuple[int, ...]
    cycles: int
    shots: int
    seed: int
    theta: float
    g_seep: float
    g_heat: float
    joint_probabilities: np.ndarray
    density_matrix: np.ndarray | None
    site_populations: list[dict[str, float]]
    counts: dict[str, int]
    theory_prediction: dict[str, Any]
    manifest: dict[str, Any]
    artifacts: QutritLeakageArtifacts | None = None

    @property
    def total_leaked_population(self) -> float:
        """Expected number of leaked qutrits in the final state."""

        return float(sum(row["p2"] for row in self.site_populations))

    @property
    def initial_state_probability(self) -> float:
        return float(self.joint_probabilities[index_from_qutrit_string(self.initial_levels)])

    def top_outcomes(self, k: int = 8) -> list[tuple[str, float, int]]:
        indices = np.argsort(self.joint_probabilities)[::-1][:int(k)]
        return [
            (
                qutrit_string_from_index(int(index), self.num_qutrits),
                float(self.joint_probabilities[int(index)]),
                int(self.counts.get(qutrit_string_from_index(int(index), self.num_qutrits), 0)),
            )
            for index in indices
        ]


def simulate_qutrit_wg_leakage(
    *,
    num_qutrits: int = 3,
    initial_levels: str | Sequence[int] | None = None,
    sites: Sequence[int] | None = None,
    cycles: int = 1,
    shots: int = 1024,
    seed: int = 0,
    theta: float = THETA_DEFAULT,
    g_seep: float = G_SEEP_DEFAULT,
    g_heat: float = G_HEAT_DEFAULT,
    device: str | torch.device = "cuda",
    out_dir: str | Path | None = None,
    write_density_matrix: bool | None = None,
) -> QutritLeakageResult:
    """Run Wood-Gambetta qutrit leakage on the project's exact density backend.

    The default initial state is ``|111...>`` so coherent ``|1><->|2>`` leakage is
    visible in a one-cycle smoke run. This exact density-matrix backend is meant for
    small qutrit registers and d=3 feasibility runs; it is not the 12-qubit Grover
    statevector carrier.
    """

    n = int(num_qutrits)
    if not 1 <= n <= MAX_EXACT_QUTRITS:
        raise ValueError(f"exact qutrit leakage backend supports 1 <= num_qutrits <= {MAX_EXACT_QUTRITS}")
    if int(cycles) < 0:
        raise ValueError("cycles must be non-negative")
    if int(shots) < 0:
        raise ValueError("shots must be non-negative")
    levels = normalize_initial_levels(initial_levels, n)
    active_sites = tuple(range(n)) if sites is None else tuple(int(s) for s in sites)
    if any(s < 0 or s >= n for s in active_sites):
        raise ValueError(f"sites must lie in [0, {n}), got {active_sites!r}")
    if len(set(active_sites)) != len(active_sites):
        raise ValueError(f"sites must not contain duplicates, got {active_sites!r}")

    dev = torch.device(device)
    eng = QutritDM(n, device=dev)
    rho0 = torch.zeros((eng.dim, eng.dim), dtype=CDTYPE, device=dev)
    rho0[index_from_qutrit_string(levels), index_from_qutrit_string(levels)] = 1.0
    eng.set_state(rho0)

    kraus = leakage_kraus_torch(theta, g_seep, g_heat, device=dev)
    for _ in range(int(cycles)):
        for site in active_sites:
            eng.apply_channel(kraus, site)

    diag = torch.diagonal(eng.rho).real.detach().cpu().numpy()
    diag = np.maximum(diag, 0.0)
    if diag.sum() > 0.0:
        diag = diag / diag.sum()

    site_populations = _site_populations(diag, n)
    counts = _sample_qutrit_counts(diag, n=n, shots=int(shots), seed=int(seed))
    wg_l1, wg_l2 = wg_rates(theta, g_seep, g_heat)
    theory = {
        "available": True,
        "estimator": "exact_density_matrix",
        "carrier": "qutrit",
        "qutrit_string_convention": QUTRIT_STRING_CONVENTION,
        "initial_state": qutrit_string_from_levels(levels),
        "initial_state_probability_ideal": 1.0,
        "initial_state_probability_noisy_expected": float(diag[index_from_qutrit_string(levels)]),
        "total_leaked_population_expected": float(sum(row["p2"] for row in site_populations)),
        "site_populations": site_populations,
    }
    manifest = {
        "schema": "qec_twin.simulator_qutrit_wg_leakage.v1",
        "backend": "qec_twin.forward.exact.qutrit_dm.QutritDM",
        "representability": "exact_qutrit_density_matrix_leakage",
        "mechanism": "wood_gambetta_qutrit_leakage",
        "qutrit_string_convention": QUTRIT_STRING_CONVENTION,
        "num_qutrits": n,
        "initial_levels": qutrit_string_from_levels(levels),
        "active_sites": list(active_sites),
        "cycles": int(cycles),
        "shots": int(shots),
        "seed": int(seed),
        "parameters": {
            "theta": float(theta),
            "g_seep": float(g_seep),
            "g_heat": float(g_heat),
            "WG_L1": float(wg_l1),
            "WG_L2": float(wg_l2),
            "C_L": float(coherence_of_leakage(theta, g_seep, g_heat)),
            "kraus_rank": len(kraus),
        },
        "noise": {
            "type": "qutrit_leakage",
            "source": "qec_twin.mechanisms.qutrit_teachers.leakage_kraus_torch",
        },
        "decoder": None,
        "artifacts": {},
    }

    density_np = None
    if write_density_matrix is None:
        write_density_matrix = eng.dim <= 729
    if bool(write_density_matrix):
        density_np = eng.rho.detach().cpu().numpy()

    result = QutritLeakageResult(
        num_qutrits=n,
        initial_levels=levels,
        sites=active_sites,
        cycles=int(cycles),
        shots=int(shots),
        seed=int(seed),
        theta=float(theta),
        g_seep=float(g_seep),
        g_heat=float(g_heat),
        joint_probabilities=diag,
        density_matrix=density_np,
        site_populations=site_populations,
        counts=counts,
        theory_prediction=theory,
        manifest=manifest,
    )
    if out_dir is None:
        return result

    artifacts = write_qutrit_leakage_artifacts(result, out_dir)
    manifest = dict(manifest)
    manifest["artifacts"] = {
        "joint_probabilities": artifacts.joint_probabilities.name,
        "site_populations": artifacts.site_populations.name,
        "measurement_counts": artifacts.measurement_counts.name,
        "theory_prediction": artifacts.theory_prediction.name,
    }
    if artifacts.density_matrix is not None:
        manifest["artifacts"]["density_matrix"] = artifacts.density_matrix.name
    _write_json(artifacts.manifest, manifest)
    return QutritLeakageResult(
        num_qutrits=n,
        initial_levels=levels,
        sites=active_sites,
        cycles=int(cycles),
        shots=int(shots),
        seed=int(seed),
        theta=float(theta),
        g_seep=float(g_seep),
        g_heat=float(g_heat),
        joint_probabilities=diag,
        density_matrix=density_np,
        site_populations=site_populations,
        counts=counts,
        theory_prediction=theory,
        manifest=manifest,
        artifacts=artifacts,
    )


def write_qutrit_leakage_artifacts(result: QutritLeakageResult, out_dir: str | Path) -> QutritLeakageArtifacts:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    density_path = out / "density_matrix.npy"
    probabilities_path = out / "joint_probabilities.npy"
    populations_path = out / "site_populations.json"
    counts_path = out / "measurement_counts.json"
    theory_path = out / "theory_prediction.json"
    manifest_path = out / "manifest.json"

    np.save(probabilities_path, result.joint_probabilities)
    if result.density_matrix is not None:
        np.save(density_path, result.density_matrix)
        density_out: Path | None = density_path
    else:
        density_out = None
    _write_json(populations_path, result.site_populations)
    _write_json(counts_path, result.counts)
    _write_json(theory_path, result.theory_prediction)
    _write_json(manifest_path, result.manifest)
    return QutritLeakageArtifacts(
        out_dir=out,
        density_matrix=density_out,
        joint_probabilities=probabilities_path,
        site_populations=populations_path,
        measurement_counts=counts_path,
        theory_prediction=theory_path,
        manifest=manifest_path,
    )


def normalize_initial_levels(initial_levels: str | Sequence[int] | None, num_qutrits: int) -> tuple[int, ...]:
    n = int(num_qutrits)
    if initial_levels is None:
        return tuple(1 for _ in range(n))
    if isinstance(initial_levels, str):
        raw = initial_levels.strip()
        if len(raw) != n or any(ch not in "012" for ch in raw):
            raise ValueError(f"initial_levels must be a {n}-trit string over 0/1/2")
        return tuple(int(ch) for ch in raw)
    levels = tuple(int(x) for x in initial_levels)
    if len(levels) != n or any(x not in (0, 1, 2) for x in levels):
        raise ValueError(f"initial_levels must contain {n} values in {{0,1,2}}")
    return levels


def index_from_qutrit_string(levels: str | Sequence[int]) -> int:
    vals = normalize_initial_levels(levels, len(levels) if not isinstance(levels, str) else len(levels.strip()))
    out = 0
    n = len(vals)
    for site, value in enumerate(vals):
        out += int(value) * (3 ** (n - 1 - site))
    return int(out)


def qutrit_string_from_index(index: int, num_qutrits: int) -> str:
    idx = int(index)
    n = int(num_qutrits)
    if idx < 0 or idx >= 3 ** n:
        raise ValueError(f"index outside [0, 3**{n})")
    digits = []
    for site in range(n):
        place = 3 ** (n - 1 - site)
        digit = idx // place
        digits.append(str(int(digit)))
        idx = idx % place
    return "".join(digits)


def qutrit_string_from_levels(levels: Sequence[int]) -> str:
    return "".join(str(int(x)) for x in levels)


def _site_populations(joint: np.ndarray, n: int) -> list[dict[str, float]]:
    out: list[dict[str, float]] = []
    indices = np.arange(joint.shape[0])
    for site in range(int(n)):
        place = 3 ** (int(n) - 1 - site)
        digit = (indices // place) % 3
        out.append(
            {
                "site": int(site),
                "p0": float(joint[digit == 0].sum()),
                "p1": float(joint[digit == 1].sum()),
                "p2": float(joint[digit == 2].sum()),
            }
        )
    return out


def _sample_qutrit_counts(joint: np.ndarray, *, n: int, shots: int, seed: int) -> dict[str, int]:
    if int(shots) == 0:
        return {}
    rng = np.random.default_rng(int(seed))
    draws = rng.choice(np.arange(joint.shape[0]), size=int(shots), p=joint)
    unique, counts = np.unique(draws, return_counts=True)
    return {
        qutrit_string_from_index(int(index), int(n)): int(count)
        for index, count in zip(unique, counts, strict=True)
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
