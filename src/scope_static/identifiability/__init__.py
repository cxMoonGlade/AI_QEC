"""Passive identifiability helpers for Stage 2A.0.5 DISC10."""

from .clustering import (
    KMeansResult,
    deterministic_kmeans,
    random_partition_baseline,
    standardize_features,
)
from .metrics import (
    active_cluster_stats,
    classify_passive_identifiability,
    contingency_table,
    evaluate_partition,
    group_records,
    mean_by_key,
    random_baseline_summary,
    shuffled_omega_control,
)
from .signatures import (
    combined_signature,
    detector_incidence,
    local_logit_signature,
    moment_spectral_signature,
    observation_moments,
    structural_signature,
)

__all__ = [
    "KMeansResult",
    "active_cluster_stats",
    "classify_passive_identifiability",
    "combined_signature",
    "contingency_table",
    "detector_incidence",
    "deterministic_kmeans",
    "evaluate_partition",
    "group_records",
    "local_logit_signature",
    "mean_by_key",
    "moment_spectral_signature",
    "observation_moments",
    "random_baseline_summary",
    "random_partition_baseline",
    "shuffled_omega_control",
    "standardize_features",
    "structural_signature",
]
