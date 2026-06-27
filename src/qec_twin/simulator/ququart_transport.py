from __future__ import annotations

"""Simulator-facing adapter for the in-house ququart leakage-transport backend.

This path is for the ``|3>``-faithful small-register transport smoke: a
QuTiP-derived two-transmon CZ leakage channel is applied through the project's
own :class:`QuquartDM` density-matrix carrier. It is intentionally separate from
the qutrit single-site WG leakage adapter.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from qec_twin.forward.exact.qutrit_dm import CDTYPE, QuquartDM

QUQUART_STRING_CONVENTION = "ququart_dm_most_significant_q0_left_to_right"
DEFAULT_TRANSPORT_KRAUS_PATH = Path("outputs/teacher_prereg/qutip_cz_leakage_kraus.npz")


@dataclass(frozen=True)
class QuquartTransportArtifacts:
    out_dir: Path
    density_matrix: Path | None
    joint_probabilities: Path
    site_populations: Path
    measurement_counts: Path
    theory_prediction: Path
    manifest: Path


@dataclass(frozen=True)
class QuquartTransportResult:
    num_ququarts: int
    initial_levels: tuple[int, ...]
    pair: tuple[int, int]
    shots: int
    seed: int
    joint_probabilities: np.ndarray
    density_matrix: np.ndarray | None
    site_populations: list[dict[str, float]]
    counts: dict[str, int]
    theory_prediction: dict[str, Any]
    manifest: dict[str, Any]
    artifacts: QuquartTransportArtifacts | None = None

    @property
    def total_noncomputational_population(self) -> float:
        """Expected count of ququarts in ``|2>`` or ``|3>``."""

        return float(sum(row["p2"] + row["p3"] for row in self.site_populations))

    @property
    def initial_state_probability(self) -> float:
        return float(self.joint_probabilities[index_from_ququart_string(self.initial_levels)])

    def outcome_probability(self, levels: str | Sequence[int]) -> float:
        return float(self.joint_probabilities[index_from_ququart_string(levels)])

    def top_outcomes(self, k: int = 8) -> list[tuple[str, float, int]]:
        indices = np.argsort(self.joint_probabilities)[::-1][:int(k)]
        return [
            (
                ququart_string_from_index(int(index), self.num_ququarts),
                float(self.joint_probabilities[int(index)]),
                int(self.counts.get(ququart_string_from_index(int(index), self.num_ququarts), 0)),
            )
            for index in indices
        ]


def simulate_ququart_transport_smoke(
    *,
    num_ququarts: int = 2,
    initial_levels: str | Sequence[int] | None = None,
    pair: tuple[int, int] = (0, 1),
    shots: int = 1024,
    seed: int = 0,
    kraus_path: str | Path = DEFAULT_TRANSPORT_KRAUS_PATH,
    device: str | torch.device = "cuda",
    out_dir: str | Path | None = None,
    write_density_matrix: bool | None = None,
) -> QuquartTransportResult:
    """Run the ``|3>``-faithful CZ leakage-transport channel on `QuquartDM`.

    The default initial state ``|12>`` exercises the transport-relevant leaked
    manifold. This exact ququart density-matrix path is for small sub-registers
    only; it is not a full 9-data-register production carrier.
    """

    n = int(num_ququarts)
    if not 2 <= n <= QuquartDM.MAX_N:
        raise ValueError(f"ququart transport backend supports 2 <= num_ququarts <= {QuquartDM.MAX_N}")
    if int(shots) < 0:
        raise ValueError("shots must be non-negative")
    levels = normalize_initial_levels4(initial_levels, n)
    i, j = int(pair[0]), int(pair[1])
    if i == j or not (0 <= i < n and 0 <= j < n):
        raise ValueError(f"pair must contain two distinct sites in [0, {n}), got {pair!r}")

    dev = torch.device(device)
    kraus, meta = load_ququart_transport_kraus(kraus_path, device=dev)
    eng = QuquartDM(n, device=dev)
    rho0 = torch.zeros((eng.dim, eng.dim), dtype=CDTYPE, device=dev)
    rho0[index_from_ququart_string(levels), index_from_ququart_string(levels)] = 1.0
    eng.set_state(rho0)
    eng.apply_channel_2site(kraus, i, j)

    diag = torch.diagonal(eng.rho).real.detach().cpu().numpy()
    diag = np.maximum(diag, 0.0)
    if diag.sum() > 0.0:
        diag = diag / diag.sum()

    site_populations = _site_populations4(diag, n)
    counts = _sample_ququart_counts(diag, n=n, shots=int(shots), seed=int(seed))
    theory = {
        "available": True,
        "estimator": "exact_density_matrix",
        "carrier": "ququart",
        "ququart_string_convention": QUQUART_STRING_CONVENTION,
        "initial_state": ququart_string_from_levels(levels),
        "initial_state_probability_ideal": 1.0,
        "initial_state_probability_noisy_expected": float(diag[index_from_ququart_string(levels)]),
        "total_noncomputational_population_expected": float(
            sum(row["p2"] + row["p3"] for row in site_populations)
        ),
        "site_populations": site_populations,
    }
    manifest = {
        "schema": "qec_twin.simulator_ququart_transport.v1",
        "backend": "qec_twin.forward.exact.qutrit_dm.QuquartDM",
        "representability": "exact_ququart_density_matrix_transport",
        "mechanism": "qutip_cz_ququart_leakage_transport",
        "ququart_string_convention": QUQUART_STRING_CONVENTION,
        "num_ququarts": n,
        "initial_levels": ququart_string_from_levels(levels),
        "active_pair": [i, j],
        "shots": int(shots),
        "seed": int(seed),
        "parameters": meta,
        "noise": {
            "type": "ququart_transport",
            "source": str(Path(kraus_path)),
            "kraus_key": "kraus_ququart",
        },
        "decoder": None,
        "artifacts": {},
    }

    density_np = None
    if write_density_matrix is None:
        write_density_matrix = eng.dim <= 1024
    if bool(write_density_matrix):
        density_np = eng.rho.detach().cpu().numpy()

    result = QuquartTransportResult(
        num_ququarts=n,
        initial_levels=levels,
        pair=(i, j),
        shots=int(shots),
        seed=int(seed),
        joint_probabilities=diag,
        density_matrix=density_np,
        site_populations=site_populations,
        counts=counts,
        theory_prediction=theory,
        manifest=manifest,
    )
    if out_dir is None:
        return result

    artifacts = write_ququart_transport_artifacts(result, out_dir)
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
    return QuquartTransportResult(
        num_ququarts=n,
        initial_levels=levels,
        pair=(i, j),
        shots=int(shots),
        seed=int(seed),
        joint_probabilities=diag,
        density_matrix=density_np,
        site_populations=site_populations,
        counts=counts,
        theory_prediction=theory,
        manifest=manifest,
        artifacts=artifacts,
    )


def load_ququart_transport_kraus(
    kraus_path: str | Path = DEFAULT_TRANSPORT_KRAUS_PATH,
    *,
    device: str | torch.device = "cuda",
    dtype: torch.dtype = CDTYPE,
) -> tuple[torch.Tensor, dict[str, Any]]:
    path = Path(kraus_path)
    if not path.is_file():
        raise FileNotFoundError(f"ququart transport Kraus artifact not found: {path}")
    data = np.load(path, allow_pickle=True)
    kraus_np = data["kraus_ququart"]
    if kraus_np.shape[-2:] != (16, 16):
        raise ValueError(f"kraus_ququart must have shape (rank,16,16), got {kraus_np.shape}")
    skk = sum(k.conj().T @ k for k in kraus_np)
    cptp_residual = float(np.max(np.abs(skk - np.eye(16))))
    if cptp_residual >= 1e-9:
        raise ValueError(f"kraus_ququart CPTP residual too large: {cptp_residual:.3e}")
    meta = {
        "kraus_rank": int(kraus_np.shape[0]),
        "cptp_residual": cptp_residual,
    }
    for key in data.files:
        if key.startswith("meta_") or key in (
            "leaked_from_comp_ququart",
            "leaked_from_leaked_max_ququart",
            "pop_ge4_max_ququart",
            "cptp_residual_ququart",
        ):
            meta[key] = _npz_scalar(data[key])
    return torch.as_tensor(kraus_np, dtype=dtype, device=device), meta


def write_ququart_transport_artifacts(
    result: QuquartTransportResult, out_dir: str | Path
) -> QuquartTransportArtifacts:
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
    return QuquartTransportArtifacts(
        out_dir=out,
        density_matrix=density_out,
        joint_probabilities=probabilities_path,
        site_populations=populations_path,
        measurement_counts=counts_path,
        theory_prediction=theory_path,
        manifest=manifest_path,
    )


def normalize_initial_levels4(initial_levels: str | Sequence[int] | None, num_ququarts: int) -> tuple[int, ...]:
    n = int(num_ququarts)
    if initial_levels is None:
        return (1, 2) + tuple(0 for _ in range(n - 2))
    if isinstance(initial_levels, str):
        raw = initial_levels.strip()
        if len(raw) != n or any(ch not in "0123" for ch in raw):
            raise ValueError(f"initial_levels must be a {n}-digit string over 0/1/2/3")
        return tuple(int(ch) for ch in raw)
    levels = tuple(int(x) for x in initial_levels)
    if len(levels) != n or any(x not in (0, 1, 2, 3) for x in levels):
        raise ValueError(f"initial_levels must contain {n} values in {{0,1,2,3}}")
    return levels


def index_from_ququart_string(levels: str | Sequence[int]) -> int:
    vals = normalize_initial_levels4(levels, len(levels) if not isinstance(levels, str) else len(levels.strip()))
    out = 0
    n = len(vals)
    for site, value in enumerate(vals):
        out += int(value) * (4 ** (n - 1 - site))
    return int(out)


def ququart_string_from_index(index: int, num_ququarts: int) -> str:
    idx = int(index)
    n = int(num_ququarts)
    if idx < 0 or idx >= 4 ** n:
        raise ValueError(f"index outside [0, 4**{n})")
    digits = []
    for site in range(n):
        place = 4 ** (n - 1 - site)
        digit = idx // place
        digits.append(str(int(digit)))
        idx = idx % place
    return "".join(digits)


def ququart_string_from_levels(levels: Sequence[int]) -> str:
    return "".join(str(int(x)) for x in levels)


def _site_populations4(joint: np.ndarray, n: int) -> list[dict[str, float]]:
    out: list[dict[str, float]] = []
    indices = np.arange(joint.shape[0])
    for site in range(int(n)):
        place = 4 ** (int(n) - 1 - site)
        digit = (indices // place) % 4
        out.append(
            {
                "site": int(site),
                "p0": float(joint[digit == 0].sum()),
                "p1": float(joint[digit == 1].sum()),
                "p2": float(joint[digit == 2].sum()),
                "p3": float(joint[digit == 3].sum()),
            }
        )
    return out


def _sample_ququart_counts(joint: np.ndarray, *, n: int, shots: int, seed: int) -> dict[str, int]:
    if int(shots) == 0:
        return {}
    rng = np.random.default_rng(int(seed))
    draws = rng.choice(np.arange(joint.shape[0]), size=int(shots), p=joint)
    unique, counts = np.unique(draws, return_counts=True)
    return {
        ququart_string_from_index(int(index), int(n)): int(count)
        for index, count in zip(unique, counts, strict=True)
    }


def _npz_scalar(value: np.ndarray) -> Any:
    if value.shape != ():
        return None
    item = value.item()
    if isinstance(item, np.generic):
        item = item.item()
    return item


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
