"""Layer 3 learner recovery and visible-generation quality interface."""

from .acceptance import (
    audit_phyc2_teacher_self,
    audit_phyc3a_baseline,
    audit_phyc3b_visible_repair,
    audit_phyc3c_accepted_learner,
    format_layer3_acceptance_summary,
    run_layer3_acceptance,
)
from .gaussian_likelihood import (
    HEADS,
    GaussianFoldModel,
    build_batch_protocol,
    fit_gaussian_fold_model,
    format_phyc3c_summary,
    gaussian_parameter_schema,
    leakage_guardrail_audit_phyc3c,
    run_phyc3c_distributional_gaussian_likelihood_head,
)
from .learner_recovery import (
    format_phyc3_no_leakage_learner_recovery_summary,
    run_phyc3_no_leakage_learner_recovery,
)
from .quality import (
    ChannelVector,
    channel_vector,
    format_sampled_quantum_error_quality_summary,
    run_sampled_quantum_error_quality_audit,
)
from .validation import (
    format_phyc3c_validation_summary,
    non_leakage_audit,
    protocol_validity_audit,
    run_phyc3c_validation_audit,
)
from .zx_visible_probe_suite import (
    ALIAS_PAIRS,
    FORBIDDEN_FEATURE_TOKENS,
    FORBIDDEN_LEARNER_INPUTS,
    VISIBLE_OPERATION_CONTEXTS,
    ZXVisibleFeatureTable,
    audit_m34_implementation,
    build_zx_visible_feature_table,
    build_zx_visible_probe_schedule,
    deterministic_visible_ceiling_audit,
    format_phyc3b_summary,
    leakage_guardrail_audit_zx_visible,
    run_phyc3b_zx_visible_alias_breaking_probe_suite,
)

__all__ = [
    "ALIAS_PAIRS",
    "ChannelVector",
    "FORBIDDEN_FEATURE_TOKENS",
    "FORBIDDEN_LEARNER_INPUTS",
    "VISIBLE_OPERATION_CONTEXTS",
    "GaussianFoldModel",
    "HEADS",
    "ZXVisibleFeatureTable",
    "audit_m34_implementation",
    "audit_phyc2_teacher_self",
    "audit_phyc3a_baseline",
    "audit_phyc3b_visible_repair",
    "audit_phyc3c_accepted_learner",
    "build_batch_protocol",
    "build_zx_visible_feature_table",
    "build_zx_visible_probe_schedule",
    "channel_vector",
    "deterministic_visible_ceiling_audit",
    "fit_gaussian_fold_model",
    "format_layer3_acceptance_summary",
    "format_phyc3_no_leakage_learner_recovery_summary",
    "format_phyc3b_summary",
    "format_phyc3c_summary",
    "format_phyc3c_validation_summary",
    "format_sampled_quantum_error_quality_summary",
    "gaussian_parameter_schema",
    "leakage_guardrail_audit_phyc3c",
    "leakage_guardrail_audit_zx_visible",
    "non_leakage_audit",
    "protocol_validity_audit",
    "run_layer3_acceptance",
    "run_phyc3_no_leakage_learner_recovery",
    "run_phyc3b_zx_visible_alias_breaking_probe_suite",
    "run_phyc3c_distributional_gaussian_likelihood_head",
    "run_phyc3c_validation_audit",
    "run_sampled_quantum_error_quality_audit",
]
