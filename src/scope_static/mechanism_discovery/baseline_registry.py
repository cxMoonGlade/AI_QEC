from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DOC_BASELINE_KEYS = (
    "dem_physics_prior",
    "rl_optimized_prior",
    "harmony_decoder_ensemble",
    "independent_detector",
    "pairwise_ising",
    "factor_graph_crf",
    "graphical_lasso",
    "bayesian_hierarchical",
    "bernoulli_mixture_em",
    "sparse_coding_dictionary",
    "causal_discovery_structure",
    "vae",
    "gan",
    "ebm_rbm_crbm",
    "autoregressive_generative",
)

PROTOCOL_BASELINE_KEYS = (
    "dmle_qec_tensor_network",
    "dmle_qec_visible_marginal_mle",
    "global_null_visible_replay",
    "mean_only_visible_replay",
    "public_stratified_null",
    "kmeans_visible",
    "gaussian_mixture_diagonal",
    "gaussian_mixture_full",
    "assignment_shuffle_control",
    "feature_scramble_control",
    "context_shuffle_control",
    "random_codebook_transfer",
    "train_on_google_only",
    "mlp_continuous_source",
    "attention_vq_source",
)


@dataclass(frozen=True)
class ExternalRepository:
    name: str
    url: str
    clone_path: str
    role: str
    snapshot_commit: str | None = None
    official_for_baseline: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "url": self.url,
            "clone_path": self.clone_path,
            "role": self.role,
            "snapshot_commit": self.snapshot_commit,
            "official_for_baseline": self.official_for_baseline,
        }


@dataclass(frozen=True)
class BaselineEntry:
    key: str
    display_name: str
    docs_terms: tuple[str, ...]
    category: str
    implementation_status: str
    priority: str
    claim_role: str
    learner_boundary: str
    metric_roles: tuple[str, ...]
    local_references: tuple[str, ...] = ()
    google_dataset_pathways: tuple[str, ...] = ()
    external_repositories: tuple[ExternalRepository, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "docs_terms": list(self.docs_terms),
            "category": self.category,
            "implementation_status": self.implementation_status,
            "priority": self.priority,
            "claim_role": self.claim_role,
            "learner_boundary": self.learner_boundary,
            "metric_roles": list(self.metric_roles),
            "local_references": list(self.local_references),
            "google_dataset_pathways": list(self.google_dataset_pathways),
            "external_repositories": [repo.to_dict() for repo in self.external_repositories],
            "notes": list(self.notes),
        }


REPO_STIM = ExternalRepository(
    name="Stim",
    url="https://github.com/quantumlib/Stim.git",
    clone_path="external/baselines/Stim",
    role="DEM extraction and sampling reference",
    snapshot_commit="01f1aab",
)
REPO_PYMATCHING = ExternalRepository(
    name="PyMatching",
    url="https://github.com/oscarhiggott/PyMatching.git",
    clone_path="external/baselines/PyMatching",
    role="MWPM decoder and DEM graphlike matching reference",
    snapshot_commit="6f63b2b",
)
REPO_FUSION_BLOSSOM = ExternalRepository(
    name="fusion-blossom",
    url="https://github.com/yuewuo/fusion-blossom.git",
    clone_path="external/baselines/fusion-blossom",
    role="Sparse Blossom / fast MWPM reference",
    snapshot_commit="c536a4b",
)
REPO_DMLE_QEC = ExternalRepository(
    name="DMLE-QEC",
    url="https://github.com/cxMoonGlade/DMLE-QEC.git",
    clone_path="external/baselines/DMLE-QEC",
    role="Upstream tensor-network DEM likelihood baseline",
    snapshot_commit="e3b3410",
)
REPO_POMEGRANATE = ExternalRepository(
    name="pomegranate",
    url="https://github.com/jmschrei/pomegranate.git",
    clone_path="external/baselines/pomegranate",
    role="Independent distributions and mixture-model reference",
    snapshot_commit="e916273",
)
REPO_CONIII = ExternalRepository(
    name="coniii",
    url="https://github.com/eltrompetero/coniii.git",
    clone_path="external/baselines/coniii",
    role="Inverse-Ising / pairwise maximum-entropy reference",
    snapshot_commit="00a96a8",
)
REPO_GGLASSO = ExternalRepository(
    name="GGLasso",
    url="https://github.com/fabian-sp/GGLasso.git",
    clone_path="external/baselines/GGLasso",
    role="Sparse inverse covariance / graphical-lasso reference",
    snapshot_commit="7fdb131",
)
REPO_PGMPY = ExternalRepository(
    name="pgmpy",
    url="https://github.com/pgmpy/pgmpy.git",
    clone_path="external/baselines/pgmpy",
    role="Probabilistic graphical model, factor graph, and CPD reference",
    snapshot_commit="f2522f6",
)
REPO_PYRO = ExternalRepository(
    name="pyro",
    url="https://github.com/pyro-ppl/pyro.git",
    clone_path="external/baselines/pyro",
    role="Hierarchical Bayesian and VAE probabilistic-programming reference",
    snapshot_commit="1bbbf38",
)
REPO_CAUSAL_LEARN = ExternalRepository(
    name="causal-learn",
    url="https://github.com/py-why/causal-learn.git",
    clone_path="external/baselines/causal-learn",
    role="Causal discovery and structure-learning reference",
    snapshot_commit="8f479e3",
)
REPO_PROSPER = ExternalRepository(
    name="ProSper",
    url="https://github.com/mlold/prosper.git",
    clone_path="external/baselines/prosper",
    role="Probabilistic sparse coding / binary sparse coding reference",
    snapshot_commit="0865c1d",
)
REPO_PYTORCH_EXAMPLES = ExternalRepository(
    name="pytorch-examples",
    url="https://github.com/pytorch/examples.git",
    clone_path="external/baselines/pytorch-examples",
    role="Generic VAE scaffolding only; not used as qecGPT/autoregressive evidence",
    snapshot_commit="acc295d",
    official_for_baseline=False,
)
REPO_PYTORCH_GAN = ExternalRepository(
    name="PyTorch-GAN",
    url="https://github.com/eriklindernoren/PyTorch-GAN.git",
    clone_path="external/baselines/PyTorch-GAN",
    role="Generic GAN reference implementations",
    snapshot_commit="36d3c77",
    official_for_baseline=False,
)
REPO_RBM = ExternalRepository(
    name="restricted-boltzmann-machines",
    url="https://github.com/echen/restricted-boltzmann-machines.git",
    clone_path="external/baselines/restricted-boltzmann-machines",
    role="Generic RBM reference implementation",
    snapshot_commit="7d69db9",
    official_for_baseline=False,
)
REPO_QECGPT = ExternalRepository(
    name="qecGPT",
    url="https://github.com/CHY-i/qecGPT.git",
    clone_path="external/baselines/qecGPT",
    role="Native qecGPT / GenerativeDecoder upstream implementation",
    snapshot_commit="42d13b3",
)


BASELINE_ENTRIES: tuple[BaselineEntry, ...] = (
    BaselineEntry(
        key="dem_physics_prior",
        display_name="DEM-based physics prior",
        docs_terms=("DEM-based physics prior", "SI1000 DEM prior", "correlated matching"),
        category="qec_specific_reference",
        implementation_status="native_reader_and_external_references",
        priority="required",
        claim_role="Mechanism-coordinate reference for DEM support, weights, synthetic syndrome sampling, and decoder priors.",
        learner_boundary="Uses circuit/DEM artifacts, not hidden Google mechanism labels.",
        metric_roles=("logical_delta_p_l", "cross_decoding_delta_p_l", "decay_curve_distance", "dem_f1", "strength_spearman"),
        local_references=(
            "scope_static.google.set1:load_google_dem_data",
            "scope_static.dem.stim_dem:extract_dem_data",
            "scope_static.google.s3_visible_common:load_google_dem_data",
        ),
        google_dataset_pathways=(
            "correlated_matching_decoder_with_si1000_prior",
            "harmony_decoder_with_si1000_prior",
            "error_model.dem",
        ),
        external_repositories=(REPO_STIM, REPO_PYMATCHING, REPO_FUSION_BLOSSOM),
        notes=("Primary DEM support is present in the Google dataset and local readers.",),
    ),
    BaselineEntry(
        key="rl_optimized_prior",
        display_name="RL/optimizer optimized prior",
        docs_terms=("RL/optimizer optimized prior", "RL-optimized prior"),
        category="qec_specific_reference",
        implementation_status="google_dataset_pathway_only",
        priority="required",
        claim_role="Strong logical-performance reference for decoder-prior calibration.",
        learner_boundary="Uses syndromes and observable flips for prior calibration; does not provide Google mechanism labels.",
        metric_roles=("logical_delta_p_l", "cross_decoding_delta_p_l", "decay_curve_distance"),
        local_references=(
            "scope_static.google.set1:DECODER_ALIASES",
            "scope_static.google.set1:load_google_predicted_observables",
        ),
        google_dataset_pathways=(
            "correlated_matching_decoder_with_rl_optimized_prior",
            "harmony_decoder_with_rl_optimized_prior",
        ),
        notes=("No official public GitHub repository was found; the Google dataset pathway outputs are the reproducible artifact.",),
    ),
    BaselineEntry(
        key="harmony_decoder_ensemble",
        display_name="Harmony / decoder ensemble",
        docs_terms=("Harmony", "decoder ensemble"),
        category="qec_specific_reference",
        implementation_status="google_dataset_pathway_only",
        priority="required",
        claim_role="Logical-performance and confidence/risk reference, not a mechanism learner.",
        learner_boundary="Consumes decoder outputs and public syndromes; no hidden mechanism labels.",
        metric_roles=("logical_delta_p_l", "cross_decoding_delta_p_l", "decay_curve_distance"),
        local_references=(
            "scope_static.google.set1:DECODER_ALIASES",
            "scope_static.google.set1:load_google_predicted_observables",
        ),
        google_dataset_pathways=(
            "harmony_decoder_with_si1000_prior",
            "harmony_decoder_with_rl_optimized_prior",
        ),
        notes=("No official public GitHub repository was found; use the dataset-provided Harmony pathways.",),
    ),
    BaselineEntry(
        key="independent_detector",
        display_name="Independent detector",
        docs_terms=("Independent detector", "factorized Bernoulli"),
        category="statistical_weak_baseline",
        implementation_status="external_adapter_pending_no_native_proxy",
        priority="required",
        claim_role="Weak lower-bound model for first moments and independent detector rates.",
        learner_boundary="Fits only learner-visible syndromes or visible surfaces.",
        metric_roles=("syndrome_first_moment", "syndrome_nll"),
        local_references=(
            "scope_static.dem.baselines:DMLEQECIndependentField",
            "scope_static.mechanism_discovery.generator_learning:evaluate_mean_only_generation",
            "scope_static.mechanism_discovery.google_unit_source:_dmle_qec_visible_marginal_mle_baseline",
        ),
        external_repositories=(REPO_POMEGRANATE,),
    ),
    BaselineEntry(
        key="pairwise_ising",
        display_name="Pairwise Ising / sparse graph model",
        docs_terms=("Pairwise Ising", "sparse Ising", "pairwise maximum entropy"),
        category="statistical_structure_baseline",
        implementation_status="external_cloned_not_integrated",
        priority="required",
        claim_role="Binary pair-correlation baseline for asking whether mechanism recovery beats pairwise correlations.",
        learner_boundary="Fits only learner-visible syndrome bits and optional public context.",
        metric_roles=("syndrome_first_moment", "syndrome_second_moment", "syndrome_nll", "cross_decoding_delta_p_l"),
        external_repositories=(REPO_CONIII,),
        notes=("A SCOPE-native runner still needs to wrap the inverse-Ising fit and binary sampler.",),
    ),
    BaselineEntry(
        key="factor_graph_crf",
        display_name="Graph model / CRF / factor graph",
        docs_terms=("Graph model", "CRF", "factor graph", "MRF"),
        category="statistical_structure_baseline",
        implementation_status="external_cloned_not_integrated",
        priority="recommended",
        claim_role="Conditional or unconditional graphical-model comparator for public context and local cliques.",
        learner_boundary="Uses public metadata/context plus learner-visible syndromes; no evaluator labels for fit.",
        metric_roles=("syndrome_second_moment", "syndrome_nll", "cross_decoding_delta_p_l"),
        external_repositories=(REPO_PGMPY,),
    ),
    BaselineEntry(
        key="graphical_lasso",
        display_name="Graphical lasso / sparse inverse covariance",
        docs_terms=("Graphical lasso", "sparse inverse covariance"),
        category="statistical_structure_baseline",
        implementation_status="external_cloned_not_integrated",
        priority="recommended",
        claim_role="Sparse conditional-dependence graph baseline for detector moments.",
        learner_boundary="Fits centered learner-visible moments; binary likelihood is an approximate projection.",
        metric_roles=("syndrome_second_moment", "location_graph"),
        external_repositories=(REPO_GGLASSO,),
    ),
    BaselineEntry(
        key="bayesian_hierarchical",
        display_name="Bayesian hierarchical model",
        docs_terms=("Bayesian hierarchical model", "context-conditioned random effects"),
        category="statistical_strength_baseline",
        implementation_status="external_cloned_not_integrated",
        priority="required",
        claim_role="Context-relative strength and drift baseline with uncertainty estimates.",
        learner_boundary="Uses public sample/patch/basis/cycles context and learner-visible syndromes.",
        metric_roles=("strength_spearman", "syndrome_nll", "uncertainty_calibration", "cross_context_generalization"),
        external_repositories=(REPO_PYRO,),
    ),
    BaselineEntry(
        key="bernoulli_mixture_em",
        display_name="EM / mixture of Bernoullis",
        docs_terms=("EM", "mixture of Bernoullis", "noise working points"),
        category="statistical_density_baseline",
        implementation_status="external_adapter_pending_no_native_proxy",
        priority="recommended",
        claim_role="Shot-level latent working-point density/generation baseline.",
        learner_boundary="Fits learner-visible syndrome or visible feature rows only.",
        metric_roles=("syndrome_nll", "syndrome_first_moment", "syndrome_second_moment"),
        local_references=(
            "scope_static.mechanism_discovery.baselines:run_stage3b0_nonlearned_clustering_baselines",
            "scope_static.mechanism_discovery.baselines:_gmm_diagonal",
            "scope_static.mechanism_discovery.baselines:_gmm_full",
        ),
        external_repositories=(REPO_POMEGRANATE,),
        notes=("Do not report SCOPE-native mixture proxies as this external baseline; run through the cloned pomegranate/upstream adapter once integrated.",),
    ),
    BaselineEntry(
        key="sparse_coding_dictionary",
        display_name="Sparse coding / dictionary learning",
        docs_terms=("Sparse coding", "dictionary learning", "probabilistic sparse coding"),
        category="statistical_mechanism_baseline",
        implementation_status="external_cloned_not_integrated",
        priority="required",
        claim_role="Closest non-neural baseline for mechanism-like atoms, activations, locations, and strengths.",
        learner_boundary="Fits only learner-visible syndromes or visible response features.",
        metric_roles=("dem_f1", "strength_spearman", "syndrome_nll", "syndrome_second_moment"),
        external_repositories=(REPO_PROSPER,),
    ),
    BaselineEntry(
        key="causal_discovery_structure",
        display_name="Causal discovery / structure learning",
        docs_terms=("Causal discovery", "structure learning", "DAG", "PAG", "CPD"),
        category="statistical_structure_baseline",
        implementation_status="external_cloned_not_integrated",
        priority="optional",
        claim_role="Exploratory dependency-direction baseline; useful but weakly identifiable on observational syndromes.",
        learner_boundary="Uses observational learner-visible syndromes and public context only.",
        metric_roles=("location_graph", "syndrome_nll"),
        external_repositories=(REPO_CAUSAL_LEARN, REPO_PGMPY),
    ),
    BaselineEntry(
        key="vae",
        display_name="VAE",
        docs_terms=("VAE", "beta-VAE", "Bernoulli decoder"),
        category="deep_generative_baseline",
        implementation_status="external_reference_cloned_not_qec_specific",
        priority="recommended",
        claim_role="Latent-regime density/generation baseline with approximate likelihood.",
        learner_boundary="Fits learner-visible syndromes or visible surfaces without evaluator labels.",
        metric_roles=("syndrome_nll", "syndrome_first_moment", "syndrome_second_moment", "cross_decoding_delta_p_l"),
        external_repositories=(REPO_PYRO, REPO_PYTORCH_EXAMPLES),
        notes=("No surface-code-specific official VAE baseline was found.",),
    ),
    BaselineEntry(
        key="gan",
        display_name="GAN",
        docs_terms=("GAN", "WGAN", "implicit generator"),
        category="deep_generative_baseline",
        implementation_status="external_reference_cloned_not_qec_specific",
        priority="optional",
        claim_role="Implicit sample-realism baseline; no native tractable syndrome likelihood.",
        learner_boundary="Fits learner-visible syndromes or visible surfaces without evaluator labels.",
        metric_roles=("sample_realism", "syndrome_first_moment", "syndrome_second_moment", "cross_decoding_delta_p_l"),
        external_repositories=(REPO_PYTORCH_GAN,),
        notes=("Generic GAN reference only; a binary-syndrome runner still needs Gumbel/straight-through or policy-gradient sampling.",),
    ),
    BaselineEntry(
        key="ebm_rbm_crbm",
        display_name="EBM / RBM / CRBM",
        docs_terms=("EBM", "RBM", "CRBM", "energy-based model"),
        category="deep_generative_baseline",
        implementation_status="external_reference_cloned_not_qec_specific",
        priority="recommended",
        claim_role="Binary high-order correlation density/generation baseline.",
        learner_boundary="Fits learner-visible syndrome bits and optional public context.",
        metric_roles=("syndrome_second_moment", "syndrome_nll", "cross_decoding_delta_p_l"),
        external_repositories=(REPO_RBM,),
        notes=("Generic RBM reference only; AIS/pseudolikelihood audit is needed for fair NLL reporting.",),
    ),
    BaselineEntry(
        key="autoregressive_generative",
        display_name="Autoregressive generative / qecGPT-style",
        docs_terms=("Autoregressive generative", "qecGPT", "Generative Decoding", "Transformer"),
        category="deep_generative_baseline",
        implementation_status="external_reference_cloned_native_entrypoint_pending",
        priority="required",
        claim_role="Published decoder-agnostic generative reference with exact autoregressive likelihood.",
        learner_boundary="Fits learner-visible syndrome streams, optionally logical responses for decoder evaluation; no Google mechanism labels.",
        metric_roles=("syndrome_nll", "cross_decoding_delta_p_l", "syndrome_first_moment", "syndrome_second_moment"),
        external_repositories=(REPO_QECGPT,),
        notes=(
            "Use only qecGPT native scripts/classes as upstream evidence; do not report SCOPE-written autoregressive helpers as this baseline.",
            "The cloned repo includes qec/decoding/training.py and qec/decoding/cir.py; current D3/D5 runner records not-run until a native upstream entrypoint can consume the dataset layout.",
        ),
    ),
    BaselineEntry(
        key="dmle_qec_tensor_network",
        display_name="Upstream DMLE-QEC tensor-network adapter",
        docs_terms=("dmle_qec_upstream", "DMLE-QEC TensorNetwork"),
        category="repo_protocol_baseline",
        implementation_status="native_upstream_adapter_available",
        priority="historical_reference",
        claim_role="Stage 1 DEM tensor-network likelihood comparator.",
        learner_boundary="Uses DEM structure; not a Google hidden-label mechanism learner.",
        metric_roles=("syndrome_nll", "dem_fault_logit_likelihood"),
        local_references=(
            "scope_static.dem.dmle_upstream:upstream_dmle_qec_dependency_audit",
            "scope_static.dem.dmle_upstream:fit_upstream_dmle_qec_tensor_network",
            "scope_static.dem.baselines:baseline_metadata",
        ),
        external_repositories=(REPO_DMLE_QEC,),
    ),
    BaselineEntry(
        key="dmle_qec_visible_marginal_mle",
        display_name="dMLE-style visible marginal MLE",
        docs_terms=("dmle_qec_visible_marginal_mle", "visible-surface dMLE-style marginal MLE"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Independent marginal MLE comparator for Stage 4 Google visible-surface transfer.",
        learner_boundary="Uses learner-visible Google calibration rows only; no evaluator labels.",
        metric_roles=("syndrome_first_moment", "visible_surface_mae", "visible_surface_nll"),
        local_references=("scope_static.mechanism_discovery.google_unit_source:_dmle_qec_visible_marginal_mle_baseline",),
    ),
    BaselineEntry(
        key="global_null_visible_replay",
        display_name="Global-null visible replay",
        docs_terms=("global-null", "global_null"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="No-structure lower bound for visible replay and transfer.",
        learner_boundary="Uses only learner-visible global means.",
        metric_roles=("visible_surface_mae", "visible_surface_nll", "generation_lift"),
        local_references=(
            "scope_static.mechanism_discovery.generator_learning:evaluate_global_null_generation",
            "scope_static.mechanism_discovery.google_unit_source:_global_null_on_calibration",
        ),
    ),
    BaselineEntry(
        key="mean_only_visible_replay",
        display_name="Mean-only visible replay",
        docs_terms=("mean-only", "mean_only"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Context/assignment-free visible mean comparator.",
        learner_boundary="Uses learner-visible means only.",
        metric_roles=("visible_surface_mae", "visible_surface_nll", "generation_lift"),
        local_references=("scope_static.mechanism_discovery.generator_learning:evaluate_mean_only_generation",),
    ),
    BaselineEntry(
        key="public_stratified_null",
        display_name="Public-field stratified null",
        docs_terms=("public stratified null", "public-field-only stratified null"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Honest Google-shaped control that uses public fields but no oracle labels.",
        learner_boundary="Uses public context fields only; no mechanism labels.",
        metric_roles=("visible_surface_mae", "visible_surface_nll", "google_raw_target_only"),
        local_references=("scope_static.mechanism_discovery.generator_learning:evaluate_public_stratified_null_generation",),
    ),
    BaselineEntry(
        key="kmeans_visible",
        display_name="Visible k-means",
        docs_terms=("k-means", "visible k-means", "prototype baseline"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Nonlearned clustering comparator on frozen visible features.",
        learner_boundary="Fits Stage 3A frozen visible features; evaluator labels are report-only.",
        metric_roles=("ari", "nmi", "balanced_accuracy"),
        local_references=(
            "scope_static.mechanism_discovery.baselines:run_stage3b0_nonlearned_clustering_baselines",
            "scope_static.mechanism_discovery.baselines:_kmeans",
        ),
    ),
    BaselineEntry(
        key="gaussian_mixture_diagonal",
        display_name="Diagonal GMM visible baseline",
        docs_terms=("diagonal GMM", "gaussian_mixture_diagonal"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Nonlearned visible-feature mixture comparator with diagonal covariance.",
        learner_boundary="Fits Stage 3A frozen visible features; evaluator labels are report-only.",
        metric_roles=("ari", "nmi", "balanced_accuracy"),
        local_references=("scope_static.mechanism_discovery.baselines:_gmm_diagonal",),
    ),
    BaselineEntry(
        key="gaussian_mixture_full",
        display_name="Full-covariance GMM visible baseline",
        docs_terms=("full-covariance GMM", "gaussian_mixture_full"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Nonlearned visible-feature mixture comparator with full covariance.",
        learner_boundary="Fits Stage 3A frozen visible features; evaluator labels are report-only.",
        metric_roles=("ari", "nmi", "balanced_accuracy"),
        local_references=("scope_static.mechanism_discovery.baselines:_gmm_full",),
    ),
    BaselineEntry(
        key="assignment_shuffle_control",
        display_name="Assignment-shuffle control",
        docs_terms=("assignment-shuffle", "assignment_shuffle"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Tests whether recovered assignments matter beyond row-level visible statistics.",
        learner_boundary="Shuffles learner-produced assignments; does not use evaluator labels.",
        metric_roles=("generation_lift", "collapse_audit"),
        local_references=(
            "scope_static.mechanism_discovery.generator_learning:assignment_shuffle_audit",
            "scope_static.mechanism_discovery.assignment_shuffle_audit:run_stage3d1_assignment_shuffle_audit",
            "scope_static.mechanism_discovery.source_pretrain:_shuffle_control_metrics",
        ),
    ),
    BaselineEntry(
        key="feature_scramble_control",
        display_name="Feature-scramble control",
        docs_terms=("feature-scramble", "feature_scramble"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Tests whether visible feature semantics matter beyond marginal distributions.",
        learner_boundary="Scrambles learner-visible feature columns; no evaluator labels.",
        metric_roles=("generation_lift", "collapse_audit"),
        local_references=(
            "scope_static.mechanism_discovery.generator_learning:feature_scramble_audit",
            "scope_static.mechanism_discovery.feature_scramble_audit:run_stage3d2_feature_scramble_audit",
            "scope_static.mechanism_discovery.source_pretrain:_feature_scramble_metrics",
        ),
    ),
    BaselineEntry(
        key="context_shuffle_control",
        display_name="Context-shuffle control",
        docs_terms=("context-shuffle", "context_shuffle"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Tests whether grouped public context is carrying the claimed transfer signal.",
        learner_boundary="Refits under shuffled public context groups; no evaluator labels.",
        metric_roles=("generation_lift", "context_robustness"),
        local_references=("scope_static.mechanism_discovery.context_shuffle_audit:run_stage3d3_context_shuffle_audit",),
    ),
    BaselineEntry(
        key="random_codebook_transfer",
        display_name="Random-codebook transfer",
        docs_terms=("random-codebook", "random_codebook"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Stage 4 control for frozen codebook transfer.",
        learner_boundary="Uses random codebook assignments; no evaluator labels.",
        metric_roles=("visible_surface_mae", "transfer_lift"),
        local_references=(
            "scope_static.mechanism_discovery.google_unit_source:_random_codebook_transfer",
            "scope_static.mechanism_discovery.google_transfer:_random_codebook_transfer",
        ),
    ),
    BaselineEntry(
        key="train_on_google_only",
        display_name="Train-on-Google-only transfer",
        docs_terms=("train-on-Google-only", "train_on_google_only"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="required_control",
        claim_role="Checks whether synthetic-source transfer beats fitting only the Google calibration split.",
        learner_boundary="Uses only held-in Google calibration rows.",
        metric_roles=("visible_surface_mae", "transfer_lift"),
        local_references=("scope_static.mechanism_discovery.google_unit_source:_train_on_google_only_transfer",),
    ),
    BaselineEntry(
        key="mlp_continuous_source",
        display_name="MLP continuous source pretrain",
        docs_terms=("mlp_continuous", "MLP continuous"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="mainline_reference",
        claim_role="Minimal Stage 4 source-surface replay learner.",
        learner_boundary="Fits frozen visible source matrix; evaluator labels are not fit inputs.",
        metric_roles=("visible_surface_mae", "source_replay"),
        local_references=("scope_static.mechanism_discovery.source_pretrain:_fit_mlp_continuous",),
    ),
    BaselineEntry(
        key="attention_vq_source",
        display_name="Attention-VQ source pretrain",
        docs_terms=("attention_vq", "Attention-VQ"),
        category="repo_protocol_baseline",
        implementation_status="native_implemented",
        priority="mainline_reference",
        claim_role="Minimal codebook/prototype source learner for frozen transfer.",
        learner_boundary="Fits frozen visible source matrix; evaluator labels are not fit inputs.",
        metric_roles=("visible_surface_mae", "source_replay", "transfer_lift"),
        local_references=("scope_static.mechanism_discovery.source_pretrain:_fit_attention_vq",),
    ),
)

BASELINE_REGISTRY: dict[str, BaselineEntry] = {entry.key: entry for entry in BASELINE_ENTRIES}


def list_baseline_entries(*, include_protocol: bool = True) -> list[BaselineEntry]:
    if include_protocol:
        return list(BASELINE_ENTRIES)
    return [BASELINE_REGISTRY[key] for key in DOC_BASELINE_KEYS]


def baseline_entry(key: str) -> BaselineEntry:
    try:
        return BASELINE_REGISTRY[key]
    except KeyError as exc:
        known = ", ".join(sorted(BASELINE_REGISTRY))
        raise KeyError(f"Unknown baseline key {key!r}. Known keys: {known}") from exc


def mentioned_baseline_keys(*, include_protocol: bool = True) -> tuple[str, ...]:
    if include_protocol:
        return DOC_BASELINE_KEYS + PROTOCOL_BASELINE_KEYS
    return DOC_BASELINE_KEYS


def baseline_registry_audit(*, repo_root: str | Path | None = None, include_protocol: bool = True) -> dict[str, object]:
    root = Path(repo_root) if repo_root is not None else _default_repo_root()
    entries = list_baseline_entries(include_protocol=include_protocol)
    missing_doc_keys = sorted(set(DOC_BASELINE_KEYS) - {entry.key for entry in entries})
    missing_protocol_keys = sorted(set(PROTOCOL_BASELINE_KEYS) - set(BASELINE_REGISTRY))
    external_audit = _external_repository_audit(root, entries)
    status_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for entry in entries:
        status_counts[entry.implementation_status] = status_counts.get(entry.implementation_status, 0) + 1
        category_counts[entry.category] = category_counts.get(entry.category, 0) + 1
    return {
        "schema": "scope_static_baseline_registry_audit_v1",
        "repo_root": str(root),
        "coverage": {
            "docs_baseline_keys": list(DOC_BASELINE_KEYS),
            "protocol_baseline_keys": list(PROTOCOL_BASELINE_KEYS),
            "missing_doc_baseline_keys": missing_doc_keys,
            "missing_protocol_baseline_keys": missing_protocol_keys,
            "docs_coverage_passed": not missing_doc_keys,
            "protocol_coverage_passed": not missing_protocol_keys,
        },
        "status_counts": status_counts,
        "category_counts": category_counts,
        "external_repositories": external_audit,
        "entries": [entry.to_dict() for entry in entries],
    }


def write_baseline_registry_audit(
    output_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    include_protocol: bool = True,
) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    audit = baseline_registry_audit(repo_root=repo_root, include_protocol=include_protocol)
    (output / "baseline_registry_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "baseline_registry_summary.md").write_text(_summary_markdown(audit), encoding="utf-8")
    return audit


def _external_repository_audit(root: Path, entries: Iterable[BaselineEntry]) -> list[dict[str, object]]:
    repos: dict[str, ExternalRepository] = {}
    for entry in entries:
        for repo in entry.external_repositories:
            repos.setdefault(repo.clone_path, repo)
    rows: list[dict[str, object]] = []
    for clone_path, repo in sorted(repos.items()):
        path = root / clone_path
        rows.append(
            {
                **repo.to_dict(),
                "present": path.exists(),
                "actual_short_commit": _git_short_hash(path) if path.exists() else None,
                "snapshot_commit_matches": _snapshot_matches(repo.snapshot_commit, _git_short_hash(path) if path.exists() else None),
            }
        )
    return rows


def _snapshot_matches(snapshot: str | None, actual: str | None) -> bool | None:
    if snapshot is None or actual is None:
        return None
    return actual.startswith(snapshot) or snapshot.startswith(actual)


def _git_short_hash(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _summary_markdown(audit: dict[str, object]) -> str:
    coverage = dict(audit["coverage"])
    lines = [
        "# Baseline Registry Audit",
        "",
        f"- Docs coverage passed: `{coverage['docs_coverage_passed']}`",
        f"- Protocol coverage passed: `{coverage['protocol_coverage_passed']}`",
        f"- Entry count: `{len(audit['entries'])}`",
        "",
        "| baseline | status | priority | category |",
        "|---|---|---|---|",
    ]
    for entry in audit["entries"]:
        row = dict(entry)
        lines.append(f"| `{row['key']}` | `{row['implementation_status']}` | `{row['priority']}` | `{row['category']}` |")
    lines.extend(["", "## External Repositories", "", "| repo | present | commit | path |", "|---|---:|---|---|"])
    for repo in audit["external_repositories"]:
        row = dict(repo)
        lines.append(
            f"| `{row['name']}` | `{row['present']}` | `{row['actual_short_commit']}` | `{row['clone_path']}` |"
        )
    return "\n".join(lines) + "\n"


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
