from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import torch

from .fault_graph import FaultGraph, combine_duplicate_probabilities


DEFAULT_UPSTREAM_DMLE_QEC_REPO = Path("/tmp/DMLE-QEC")
UPSTREAM_DMLE_QEC_EXPECTED_COMMIT = "e3b34106a07e65e130fa9cb5f58744ca18ca963f"
UPSTREAM_DMLE_QEC_REQUIRED_MODULES = (
    "ldpc",
    "cotengra",
    "kahypar",
    "pymatching",
    "stim",
    "opt_einsum",
)


@dataclass(frozen=True)
class UpstreamDMLEQECConfig:
    repo_path: Path = DEFAULT_UPSTREAM_DMLE_QEC_REPO
    device: str = "cuda"
    dtype: torch.dtype = torch.float64
    seed: int = 0
    epochs: int = 20
    lr: float = 0.01
    batch_size: int = 10000
    minibatch: int = 1000
    path_file: Path | None = None
    path_search_max_time: int = 0


class UpstreamDMLEQECError(RuntimeError):
    pass


def upstream_dmle_qec_dependency_audit(repo_path: str | Path = DEFAULT_UPSTREAM_DMLE_QEC_REPO) -> dict[str, object]:
    _ensure_matplotlib_config_dir()
    repo = Path(repo_path)
    audit: dict[str, object] = {
        "baseline": "dmle_qec_upstream",
        "repository": str(repo),
        "expected_commit": UPSTREAM_DMLE_QEC_EXPECTED_COMMIT,
        "repository_exists": repo.is_dir(),
        "source_package_exists": (repo / "src" / "__init__.py").is_file(),
        "required_modules": {},
        "missing_modules": [],
        "importable": False,
        "commit": None,
        "commit_matches_expected": None,
    }
    for module_name in UPSTREAM_DMLE_QEC_REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
            audit["required_modules"][module_name] = {"available": True}
        except Exception as exc:
            audit["required_modules"][module_name] = {
                "available": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            audit["missing_modules"].append(module_name)

    audit["commit"] = _git_commit(repo)
    audit["commit_matches_expected"] = audit["commit"] == UPSTREAM_DMLE_QEC_EXPECTED_COMMIT
    if not audit["repository_exists"] or not audit["source_package_exists"] or audit["missing_modules"]:
        return audit

    try:
        upstream = _import_upstream_src(repo)
        for attr in ("TensorNetwork", "PCM", "get_error_rates"):
            if not hasattr(upstream, attr):
                raise AttributeError(f"upstream src missing {attr}")
        audit["importable"] = True
    except Exception as exc:
        audit["import_error_type"] = type(exc).__name__
        audit["import_error"] = str(exc)
    return audit


def fit_upstream_dmle_qec_tensor_network(
    *,
    dem: Any,
    graph: FaultGraph,
    observations: torch.Tensor,
    config: UpstreamDMLEQECConfig,
) -> dict[str, object]:
    if not str(config.device).startswith("cuda"):
        raise UpstreamDMLEQECError("dmle_qec_upstream requires a CUDA device; CPU fallback is not allowed")
    if not torch.cuda.is_available():
        raise UpstreamDMLEQECError("dmle_qec_upstream requested but CUDA is not visible")

    audit = upstream_dmle_qec_dependency_audit(config.repo_path)
    if not bool(audit.get("importable")):
        raise UpstreamDMLEQECError(f"dmle_qec_upstream dependencies are not satisfied: {audit}")
    upstream = _import_upstream_src(Path(config.repo_path))

    raw_probabilities = torch.as_tensor(
        np.asarray(upstream.get_error_rates(dem), dtype=np.float64),
        dtype=config.dtype,
    ).clamp(1e-9, 1.0 - 1e-9)
    if raw_probabilities.numel() != graph.raw_to_effective.numel():
        raise UpstreamDMLEQECError(
            "upstream DEM raw error count does not match the scope_static graph "
            f"({raw_probabilities.numel()} != {graph.raw_to_effective.numel()})"
        )

    pcm, _logical = upstream.PCM(dem)
    detector_rows = _active_detector_rows_from_dem(dem)
    if int(pcm.shape[0]) != len(detector_rows):
        raise UpstreamDMLEQECError(
            "upstream PCM active detector rows do not match the local row audit "
            f"({pcm.shape[0]} != {len(detector_rows)})"
        )

    torch.manual_seed(int(config.seed))
    device = torch.device(config.device)
    priors_logits = torch.logit(raw_probabilities).to(device=device, dtype=config.dtype)
    model = upstream.TensorNetwork(
        pcm=pcm,
        priors_logits=priors_logits,
        dtype=config.dtype,
        dev=str(device),
    )
    path_audit = _maybe_load_or_find_path(model, config)
    detector_data = observations[:, detector_rows].to(device=device, dtype=torch.long)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config.lr))
    history: list[float] = []
    for _epoch in range(int(config.epochs)):
        losses: list[float] = []
        permutation = torch.randperm(detector_data.shape[0], device=device)
        for start in range(0, detector_data.shape[0], int(config.batch_size)):
            batch = detector_data[permutation[start : start + int(config.batch_size)]]
            chunks = torch.split(batch, max(1, int(config.minibatch)), dim=0)
            optimizer.zero_grad()
            loss_value = 0.0
            for chunk in chunks:
                loss = model.forward(chunk) / max(1, len(chunks))
                loss.backward()
                loss_value += float(loss.detach().cpu())
            optimizer.step()
            losses.append(loss_value)
        history.append(float(sum(losses) / len(losses)) if losses else float("nan"))

    raw_final_probabilities = torch.sigmoid(model.priors_logits.detach().to(dtype=torch.float64).cpu())
    effective_probabilities = _raw_to_effective_probabilities(raw_final_probabilities, graph)
    effective_logits = torch.logit(effective_probabilities.clamp(1e-9, 1.0 - 1e-9))
    audit.update(
        {
            "upstream_component": "TensorNetwork",
            "direct_upstream_code_used": True,
            "cpu_fallback_used": False,
            "device": str(device),
            "dtype": str(config.dtype).replace("torch.", ""),
            "epochs": int(config.epochs),
            "lr": float(config.lr),
            "batch_size": int(config.batch_size),
            "minibatch": int(config.minibatch),
            "raw_num_errors": int(raw_probabilities.numel()),
            "effective_num_faults": int(graph.M),
            "active_detector_rows": len(detector_rows),
            "path": path_audit,
        }
    )
    return {
        "logits": effective_logits,
        "raw_logits": torch.logit(raw_final_probabilities.clamp(1e-9, 1.0 - 1e-9)),
        "train_history": history,
        "train_final_nll": history[-1] if history else None,
        "audit": audit,
    }


def _maybe_load_or_find_path(model: object, config: UpstreamDMLEQECConfig) -> dict[str, object]:
    audit: dict[str, object] = {
        "path_file": None if config.path_file is None else str(config.path_file),
        "path_loaded": False,
        "tree_loaded": False,
        "path_found": False,
        "path_search_max_time": int(config.path_search_max_time),
    }
    if config.path_file is not None:
        path_file = Path(config.path_file)
        if path_file.suffix == ".json":
            model.load_tree(str(path_file))
            audit["tree_loaded"] = True
        else:
            model.load_path(str(path_file))
            audit["path_loaded"] = True
        return audit
    if int(config.path_search_max_time) > 0:
        path = model.find_contraction_path(
            batch_size=max(1, int(config.minibatch)),
            max_time=int(config.path_search_max_time),
        )
        if path is None:
            raise UpstreamDMLEQECError("upstream TensorNetwork path search did not find an acceptable path")
        model.path = path
        audit["path_found"] = True
    return audit


def _raw_to_effective_probabilities(raw_probabilities: torch.Tensor, graph: FaultGraph) -> torch.Tensor:
    values = []
    for raw_indices in graph.effective_to_raw:
        values.append(combine_duplicate_probabilities(raw_probabilities[list(raw_indices)]))
    if not values:
        return raw_probabilities.new_empty((0,))
    return torch.stack(values).to(dtype=torch.float64)


def _active_detector_rows_from_dem(dem: Any) -> list[int]:
    used = np.zeros(int(dem.num_detectors), dtype=np.bool_)
    for instruction in dem.flattened():
        if instruction.type != "error":
            continue
        for target in instruction.targets_copy():
            if target.is_relative_detector_id():
                used[int(target.val)] = True
    return [int(idx) for idx in np.nonzero(used)[0].tolist()]


def _import_upstream_src(repo: Path):
    _ensure_matplotlib_config_dir()
    repo = Path(repo)
    if not (repo / "src" / "__init__.py").is_file():
        raise UpstreamDMLEQECError(f"DMLE-QEC repository does not contain src/__init__.py: {repo}")
    current_src = sys.modules.get("src")
    if current_src is not None and not str(getattr(current_src, "__file__", "")).startswith(str(repo)):
        for name in [name for name in sys.modules if name == "src" or name.startswith("src.")]:
            del sys.modules[name]
    sys.path.insert(0, str(repo))
    try:
        return importlib.import_module("src")
    finally:
        try:
            sys.path.remove(str(repo))
        except ValueError:
            pass


def _git_commit(repo: Path) -> str | None:
    if not repo.is_dir():
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return completed.stdout.strip() or None


def _ensure_matplotlib_config_dir() -> None:
    path = Path("/tmp/scope_static_matplotlib")
    path.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(path))
