from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scope_static.mechanism_discovery.generator_learning import DEFAULT_MAX_CV_FOLDS
from scope_static.mechanism_discovery.k_stress_audit import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3D4_DIR
from scope_static.mechanism_discovery.observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from scope_static.mechanism_discovery.overcomplete_merge_prune_audit import (
    DEFAULT_MAX_GENERATION_NLL_INCREASE,
    DEFAULT_MAX_MICROCLUSTER_FRACTION,
    DEFAULT_MAX_MICROCLUSTER_SUPPORT,
    DEFAULT_MIN_MICROCLUSTER_FAMILY_COUNT,
    DEFAULT_MIN_POSTMERGE_ARI,
    DEFAULT_MIN_POSTMERGE_BA,
    DEFAULT_MIN_POSTMERGE_MIN_RECALL,
    DEFAULT_MIN_POSTMERGE_NMI,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OVERCOMPLETE_ASSIGNMENT_KEY,
    run_stage3d4b_overcomplete_merge_prune_audit,
)
from scope_static.mechanism_discovery.protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


def run_stage3d4b_overcomplete_merge_prune_audit_from_config(
    *,
    config_path: str | Path | None = None,
    stage3a_dir: str | Path | None = None,
    stage3a5_dir: str | Path | None = None,
    stage3d4_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    assignment_key: str | None = None,
) -> dict[str, object]:
    cfg = _load_config(config_path)
    s3a = Path(stage3a_dir) if stage3a_dir is not None else Path(str(cfg.get("stage3a_dir", DEFAULT_STAGE3A_DIR)))
    s3a5 = Path(stage3a5_dir) if stage3a5_dir is not None else Path(str(cfg.get("stage3a5_dir", DEFAULT_STAGE3A5_DIR)))
    s3d4 = Path(stage3d4_dir) if stage3d4_dir is not None else Path(str(cfg.get("stage3d4_dir", DEFAULT_STAGE3D4_DIR)))
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", DEFAULT_OUTPUT_DIR)))
    result = run_stage3d4b_overcomplete_merge_prune_audit(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3d4_dir=s3d4,
        output_dir=output,
        teacher_dir=None if cfg.get("teacher_dir") is None else Path(str(cfg.get("teacher_dir"))),
        overcomplete_assignment_key=str(assignment_key or cfg.get("overcomplete_assignment_key", DEFAULT_OVERCOMPLETE_ASSIGNMENT_KEY)),
        max_microcluster_support=int(cfg.get("max_microcluster_support", DEFAULT_MAX_MICROCLUSTER_SUPPORT)),
        max_microcluster_fraction=float(cfg.get("max_microcluster_fraction", DEFAULT_MAX_MICROCLUSTER_FRACTION)),
        min_microcluster_family_count=int(cfg.get("min_microcluster_family_count", DEFAULT_MIN_MICROCLUSTER_FAMILY_COUNT)),
        max_cv_folds=None if cfg.get("max_cv_folds") is None else int(cfg.get("max_cv_folds", DEFAULT_MAX_CV_FOLDS)),
        variance_floor=float(cfg.get("variance_floor", 1.0e-6)),
        min_postmerge_nmi=float(cfg.get("min_postmerge_nmi", DEFAULT_MIN_POSTMERGE_NMI)),
        min_postmerge_ari=float(cfg.get("min_postmerge_ari", DEFAULT_MIN_POSTMERGE_ARI)),
        min_postmerge_ba=float(cfg.get("min_postmerge_ba", DEFAULT_MIN_POSTMERGE_BA)),
        min_postmerge_min_recall=float(cfg.get("min_postmerge_min_recall", DEFAULT_MIN_POSTMERGE_MIN_RECALL)),
        max_generation_nll_increase=float(cfg.get("max_generation_nll_increase", DEFAULT_MAX_GENERATION_NLL_INCREASE)),
    )
    metrics = dict(result.get("postmerge_metrics", {}))
    post = dict(metrics.get("postmerge_exact_metrics", {}))
    merge = dict(result.get("merge_map", {}))
    print(
        "Stage 3D.4b overcomplete merge/prune audit complete\n"
        f"  decision={result.get('decision')}\n"
        f"  active_clusters={merge.get('active_cluster_count')}\n"
        f"  postmerge_families={merge.get('postmerge_family_count')}\n"
        f"  microclusters_merged={merge.get('microcluster_count')}\n"
        f"  postmerge_exact_nmi={post.get('normalized_mutual_info')}\n"
        f"  postmerge_exact_min_recall={post.get('min_recall_after_label_matching')}\n"
        f"  output={output}"
    )
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Stage 3D.4b overcomplete merge/prune audit.")
    parser.add_argument("--config", type=Path, default=Path("configs/scope_static/stage3d4b_overcomplete_merge_prune_audit.yaml"))
    parser.add_argument("--stage3a-dir", type=Path)
    parser.add_argument("--stage3a5-dir", type=Path)
    parser.add_argument("--stage3d4-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--assignment-key", type=str)
    parser.add_argument("--overcomplete-assignment-key", type=str)
    args = parser.parse_args(argv)
    run_stage3d4b_overcomplete_merge_prune_audit_from_config(
        config_path=args.config,
        stage3a_dir=args.stage3a_dir,
        stage3a5_dir=args.stage3a5_dir,
        stage3d4_dir=args.stage3d4_dir,
        output_dir=args.output_dir,
        assignment_key=args.assignment_key or args.overcomplete_assignment_key,
    )


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    path = Path(config_path)
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text())
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Stage 3D.4b config must be a mapping")
    section = data.get("stage3d4b_overcomplete_merge_prune_audit", data)
    if not isinstance(section, dict):
        raise ValueError("Stage 3D.4b config section must be a mapping")
    return dict(section)


if __name__ == "__main__":
    main()
