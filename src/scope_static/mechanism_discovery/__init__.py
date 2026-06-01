"""Public Stage 3 mechanism-discovery interface.

Implementation modules live under this package so the top-level physical
package is not a flat pile of similarly named Stage 3 files.
"""

from .artifacts import (
    Stage3EvaluatorLabels,
    Stage3VisibleFeatures,
    feature_schema_matches_stage3a,
    load_json_object,
    load_mechanism_records,
    load_stage3_evaluator_labels,
    load_stage3a_frozen_visible_features,
    load_stage3a_visible_features,
    resolve_teacher_dir,
)
from .observability_ceiling import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_OUTPUT_DIR,
    run_stage3a5_observability_alias_ceiling,
)
from .protocol_freeze import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_OUTPUT_DIR,
    run_stage3a_dataset_protocol_freeze,
)
from .baselines import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B0_OUTPUT_DIR,
    run_stage3b0_nonlearned_clustering_baselines,
)
from .discovery_model import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_OUTPUT_DIR,
    run_stage3b1_first_discovery_model,
)
from .generator_learning import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3C_OUTPUT_DIR,
    PRIMARY_GENERATION_LIKELIHOOD_METRIC,
    SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
    run_stage3c_prototype_generator_learning,
)
from .assignment_shuffle_audit import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3D1_OUTPUT_DIR,
    run_stage3d1_assignment_shuffle_audit,
)
from .feature_scramble_audit import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3D2_OUTPUT_DIR,
    run_stage3d2_feature_scramble_audit,
)
from .context_shuffle_audit import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3D3_OUTPUT_DIR,
    run_stage3d3_context_shuffle_audit,
)
from .k_stress_audit import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3D4_OUTPUT_DIR,
    run_stage3d4_k_stress_audit,
)
from .overcomplete_merge_prune_audit import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3D4B_OUTPUT_DIR,
    run_stage3d4b_overcomplete_merge_prune_audit,
)
from .stage4_artifacts import (
    Stage4SourceLabels,
    load_stage4_source_evaluator_labels,
    load_stage4_visible_matrix,
    validate_stage4_source_label_separation,
)
from .source_ceiling import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE4_SOURCE_CEILING_OUTPUT_DIR,
    run_stage4_source_surface_survival_audit,
)
from .source_pretrain import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE4_SOURCE_PRETRAIN_OUTPUT_DIR,
    run_stage4_source_pretrain,
)
from .google_transfer import (
    DEFAULT_OUTPUT_DIR as DEFAULT_STAGE4_GOOGLE_TRANSFER_OUTPUT_DIR,
    DEFAULT_DIAGNOSTIC_OUTPUT_DIR as DEFAULT_STAGE4_TRANSFER_DIAGNOSTICS_OUTPUT_DIR,
    run_stage4_google_transfer,
    run_stage4_transfer_diagnostics,
)

__all__ = [
    "DEFAULT_STAGE3A_OUTPUT_DIR",
    "DEFAULT_STAGE3A5_OUTPUT_DIR",
    "DEFAULT_STAGE3B0_OUTPUT_DIR",
    "DEFAULT_STAGE3B1_OUTPUT_DIR",
    "DEFAULT_STAGE3C_OUTPUT_DIR",
    "DEFAULT_STAGE3D1_OUTPUT_DIR",
    "DEFAULT_STAGE3D2_OUTPUT_DIR",
    "DEFAULT_STAGE3D3_OUTPUT_DIR",
    "DEFAULT_STAGE3D4_OUTPUT_DIR",
    "DEFAULT_STAGE3D4B_OUTPUT_DIR",
    "DEFAULT_STAGE4_GOOGLE_TRANSFER_OUTPUT_DIR",
    "DEFAULT_STAGE4_SOURCE_CEILING_OUTPUT_DIR",
    "DEFAULT_STAGE4_SOURCE_PRETRAIN_OUTPUT_DIR",
    "DEFAULT_STAGE4_TRANSFER_DIAGNOSTICS_OUTPUT_DIR",
    "PRIMARY_GENERATION_LIKELIHOOD_METRIC",
    "SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC",
    "Stage3EvaluatorLabels",
    "Stage3VisibleFeatures",
    "Stage4SourceLabels",
    "feature_schema_matches_stage3a",
    "load_json_object",
    "load_mechanism_records",
    "load_stage3_evaluator_labels",
    "load_stage3a_frozen_visible_features",
    "load_stage3a_visible_features",
    "load_stage4_source_evaluator_labels",
    "load_stage4_visible_matrix",
    "resolve_teacher_dir",
    "run_stage3a_dataset_protocol_freeze",
    "run_stage3a5_observability_alias_ceiling",
    "run_stage3b0_nonlearned_clustering_baselines",
    "run_stage3b1_first_discovery_model",
    "run_stage3c_prototype_generator_learning",
    "run_stage3d1_assignment_shuffle_audit",
    "run_stage3d2_feature_scramble_audit",
    "run_stage3d3_context_shuffle_audit",
    "run_stage3d4_k_stress_audit",
    "run_stage3d4b_overcomplete_merge_prune_audit",
    "run_stage4_google_transfer",
    "run_stage4_source_pretrain",
    "run_stage4_source_surface_survival_audit",
    "run_stage4_transfer_diagnostics",
    "validate_stage4_source_label_separation",
]
