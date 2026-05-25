from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import torch
import yaml

from scope_static.stim_dem import build_surface_code_graph


@dataclass(frozen=True)
class TeacherCase:
    mode: str
    epsilon_break: float

    def audit_dict(self) -> dict[str, object]:
        return {"teacher_mode": self.mode, "epsilon_break": float(self.epsilon_break)}


@dataclass(frozen=True)
class ExperimentPlan:
    config_path: Path
    config: dict[str, object]
    output_dir: Path
    output_dir_overridden: bool
    run_cfg: dict[str, object]
    circuit_cfg: dict[str, object]
    graph_cfg: dict[str, object]
    windows_cfg: dict[str, object]
    experiment_cfg: dict[str, object]
    training_cfg: dict[str, object]
    evaluation_cfg: dict[str, object]
    dtype: torch.dtype
    device: torch.device
    residual_ranks: tuple[int, ...]
    teacher_residual_rank: int
    teacher_cases: tuple[TeacherCase, ...]
    likelihood_backend: str
    likelihood_objective: str
    global_exact_max_bits: int | None
    progress_every_records: int

    @classmethod
    def from_path(cls, config_path: str | Path, *, output_dir: str | Path | None = None) -> "ExperimentPlan":
        path = Path(config_path)
        config = yaml.safe_load(path.read_text())
        if not isinstance(config, dict):
            raise ValueError("experiment config must be a mapping")

        run_cfg = dict(config.get("run", {}))
        circuit_cfg = dict(config["circuit"])
        graph_cfg = dict(config["graph"])
        windows_cfg = dict(config.get("windows", {}))
        experiment_cfg = dict(config["experiment"])
        training_cfg = dict(config["training"])
        evaluation_cfg = dict(config.get("evaluation", {}))

        _validate_known_run_identity(path, run_cfg, output_dir_override=output_dir)
        residual_ranks = tuple(_residual_ranks_from_config(graph_cfg))
        teacher_residual_rank = int(experiment_cfg.get("teacher_residual_rank", max(residual_ranks)))
        global_exact_max_bits = evaluation_cfg.get("global_exact_max_bits")
        return cls(
            config_path=path,
            config=config,
            output_dir=Path(output_dir or run_cfg.get("output_dir", "outputs/scope_static/run")),
            output_dir_overridden=output_dir is not None,
            run_cfg=run_cfg,
            circuit_cfg=circuit_cfg,
            graph_cfg=graph_cfg,
            windows_cfg=windows_cfg,
            experiment_cfg=experiment_cfg,
            training_cfg=training_cfg,
            evaluation_cfg=evaluation_cfg,
            dtype=_dtype_from_config(str(run_cfg.get("dtype", "float64"))),
            device=_device_from_config(str(run_cfg.get("device", "cpu"))),
            residual_ranks=residual_ranks,
            teacher_residual_rank=teacher_residual_rank,
            teacher_cases=tuple(_teacher_cases_from_config(experiment_cfg)),
            likelihood_backend=str(training_cfg.get("likelihood_backend", "auto")),
            likelihood_objective=str(training_cfg.get("likelihood_objective", "global_exact")),
            global_exact_max_bits=None if global_exact_max_bits is None else int(global_exact_max_bits),
            progress_every_records=int(run_cfg.get("progress_every_records", 0)),
        )

    @property
    def seeds(self) -> tuple[int, ...]:
        return tuple(int(seed) for seed in self.experiment_cfg.get("seeds", [0]))

    @property
    def shot_budgets(self) -> tuple[int, ...]:
        return tuple(int(shots) for shots in self.experiment_cfg.get("shot_budgets", [128]))

    @property
    def model_names(self) -> tuple[str, ...]:
        default_models = ["local", "hard_orbit", "soft_feature_orbit"]
        return tuple(str(model) for model in self.training_cfg.get("models", default_models))

    @property
    def aggregate_unique(self) -> bool:
        return bool(self.training_cfg.get("aggregate_unique", True))

    @property
    def heldout_shots(self) -> int:
        return int(self.experiment_cfg.get("heldout_shots", 2048))

    @property
    def threshold_epsilon(self) -> float:
        return float(self.experiment_cfg.get("threshold_epsilon", 0.01))

    @property
    def threshold_seed_policy(self) -> str:
        return str(self.experiment_cfg.get("threshold_seed_policy", "mean"))

    def build_graph(self, residual_rank: int):
        return build_surface_code_graph(
            family=self.circuit_cfg.get("family", "surface_code:rotated_memory_x"),
            distance=int(self.circuit_cfg.get("distance", 3)),
            rounds=int(self.circuit_cfg.get("rounds", 1)),
            noise=self.circuit_cfg.get("noise", {}),
            residual_rank=int(residual_rank),
            canonicalize_duplicate_masks=bool(self.graph_cfg.get("canonicalize_duplicate_masks", True)),
        )

    def model_options(self, model_name: str) -> dict[str, object]:
        model_options_by_name = self.training_cfg.get("model_options") or {}
        return dict(model_options_by_name.get(model_name, {}))

    def regularization_weight(self, model_name: str, model_options: dict[str, object]) -> float:
        if model_name != "soft_feature_orbit":
            return 0.0
        return float(model_options.get("beta_l2", self.training_cfg.get("soft_beta_l2", 0.0)))

    def observation_mode(self, model_name: str) -> str:
        return "detectors" if model_name == "dmle_qec" else "full"

    def fit_cache_key(
        self,
        *,
        seed: int,
        teacher_case: TeacherCase,
        shots: int,
        model_name: str,
        observation_mode: str,
    ) -> tuple[object, ...] | None:
        if not is_rank_invariant_model(model_name):
            return None
        return (
            int(seed),
            teacher_case.mode,
            float(teacher_case.epsilon_break),
            int(shots),
            model_name,
            observation_mode,
            self.likelihood_objective,
        )

    def output_audit_dict(self) -> dict[str, object]:
        return {
            "run_name": str(self.run_cfg.get("name", "")),
            "config_path": str(self.config_path),
            "config_stem": self.config_path.stem,
            "output_dir": str(self.output_dir),
            "output_dir_overridden": self.output_dir_overridden,
        }


def is_rank_invariant_model(model_name: str) -> bool:
    return model_name in {"local", "dmle_qec", "hard_orbit"}


def _dtype_from_config(name: str) -> torch.dtype:
    if name == "float32":
        return torch.float32
    if name == "float64":
        return torch.float64
    raise ValueError(f"unsupported dtype {name!r}")


def _device_from_config(name: str) -> torch.device:
    device = torch.device(name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "run.device requests CUDA, but torch.cuda.is_available() is false in this environment. "
            "Fix the PyTorch/CUDA driver visibility before running GPU-native MVP05."
        )
    return device


def _residual_ranks_from_config(graph_cfg: dict[str, object]) -> list[int]:
    if "residual_ranks" in graph_cfg:
        ranks = [int(rank) for rank in graph_cfg["residual_ranks"]]
    else:
        ranks = [int(graph_cfg.get("residual_rank", 0))]
    if not ranks:
        raise ValueError("graph.residual_ranks must not be empty")
    if any(rank < 0 for rank in ranks):
        raise ValueError("residual ranks must be non-negative")
    return ranks


def _teacher_cases_from_config(experiment_cfg: dict[str, object]) -> list[TeacherCase]:
    if "teacher_cases" in experiment_cfg:
        cases = [
            TeacherCase(
                mode=str(case["mode"]),
                epsilon_break=float(case.get("epsilon_break", case.get("epsilon", 0.0))),
            )
            for case in experiment_cfg["teacher_cases"]
        ]
        if not cases:
            raise ValueError("experiment.teacher_cases must not be empty")
        return cases
    return [
        TeacherCase(mode=str(teacher_mode), epsilon_break=float(epsilon_break))
        for teacher_mode in experiment_cfg.get("teacher_modes", ["exact_orbit"])
        for epsilon_break in experiment_cfg.get("epsilon_breaks", [0.0])
    ]


def _validate_known_run_identity(
    config_path: Path,
    run_cfg: dict[str, object],
    *,
    output_dir_override: str | Path | None,
) -> None:
    if output_dir_override is not None:
        return
    config_label = _mvp_label(str(config_path))
    if config_label is None:
        return
    output_dir = run_cfg.get("output_dir")
    if output_dir is None:
        return
    output_label = _mvp_label(str(output_dir))
    if output_label is None or output_label == config_label:
        return
    raise ValueError(
        f"config {config_path} looks like {config_label}, but run.output_dir points to {output_label}; "
        "use --output-dir for an intentional override"
    )


_MVP_LABEL_RE = re.compile(r"MVP\d+", re.IGNORECASE)


def _mvp_label(text: str) -> str | None:
    match = _MVP_LABEL_RE.search(text)
    return None if match is None else match.group(0).upper()
