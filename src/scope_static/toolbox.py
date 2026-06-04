from __future__ import annotations

import argparse
import json

from .protocols import catalog_validation_stage_metadata


TOOLBOX_NAME = "SCOPE-Static Physical Mechanism Toolbox"


def toolbox_manifest() -> dict[str, object]:
    return {
        "schema": "scope_static_toolbox_manifest_v1",
        "name": TOOLBOX_NAME,
        "package": "scope-static",
        "status": "pre-release",
        "claim_boundary": (
            "Stage 2 is closed as a no-leakage physical-mechanism catalog "
            "validation stage: the system can generate controlled noisy QEC "
            "observations from declared mechanisms, verify teacher/catalog "
            "separability, and train learner models that recover and replay "
            "learner-visible noisy observation distributions without oracle "
            "leakage. Stage 3 is the next claim boundary: remove direct "
            "mechanism-label supervision and test whether latent mechanism "
            "structure can be inferred from visible observations alone."
        ),
        "program_surface": [
            {
                "name": "generate_teacher_declared_observations",
                "role": "Generate teacher-declared noisy QEC observations from a controlled catalog.",
                "primary_stage": "Layer1 preprocessing - teacher generator",
                "config_template": "configs/scope_static/layer1_user_defined_mechanisms.yaml",
            },
            {
                "name": "learn_and_replay_visible_noise",
                "role": "Learn from learner-visible observations and score recovery/replay of visible noisy observation distributions.",
                "primary_stage": "Layer 3 learner",
                "metrics": ["channel_distance", "visible_gaussian_nll", "population_ce", "visible_feature_mae"],
            },
            {
                "name": "discover_latent_mechanism_quotient",
                "role": "Stage 3 +1 object: infer the latent mechanism quotient without direct mechanism-label supervision.",
                "roadmap": "docs/STAGE3_ROADMAP.md",
            },
        ],
        "physicality_boundary": (
            "Layer1 preprocessing - teacher generator is the first-class physical-process generator. It validates "
            "implemented catalog mechanisms as unitary channels, Kraus channels, "
            "or stochastic readout maps before sampling, then runs a blocking "
            "post-sampling physicality audit. The learner does not yet learn "
            "arbitrary CPTP/GKSL channels by construction."
        ),
        "catalog_stages": catalog_validation_stage_metadata(),
        "layers": catalog_validation_stage_metadata(),
        "commands": [
            {
                "name": "scope-static-toolbox",
                "role": "Print the toolbox manifest and public catalog stage map.",
                "module": "scope_static.toolbox",
            },
            {
                "name": "scope-data-preparation-teacher",
                "role": "Generate the first-class data-preparation physical-process teacher artifact.",
                "module": "scope_static.experiments.qec_noise_catalog.data_preparation_teacher",
            },
            {
                "name": "scope-teacher-physicality-audit",
                "role": "Run the Layer1 preprocessing teacher-generator physicality audit.",
                "module": "scope_static.experiments.qec_noise_catalog.teacher_physicality_audit",
            },
            {
                "name": "scope-stage3a-freeze",
                "role": "Freeze the Stage 3A learner-visible dataset and protocol artifacts.",
                "module": "scope_static.experiments.stage3.protocol_freeze",
            },
            {
                "name": "scope-stage3a5-ceiling",
                "role": "Compute the Stage 3A.5 visible observability and alias ceiling.",
                "module": "scope_static.experiments.stage3.observability_ceiling",
            },
            {
                "name": "scope-stage3b0-baselines",
                "role": "Run Stage 3B.0 visible-only non-learned clustering baselines.",
                "module": "scope_static.experiments.stage3.baselines",
            },
            {
                "name": "scope-stage3b1-discovery",
                "role": "Train the Stage 3B.1 visible-only prototype-mixture discovery model.",
                "module": "scope_static.experiments.stage3.discovery_model",
            },
            {
                "name": "scope-stage3c-generator",
                "role": "Fit and score the Stage 3C heldout visible generator.",
                "module": "scope_static.experiments.stage3.generator_learning",
            },
            {
                "name": "scope-stage3d1-assignment-shuffle",
                "role": "Run the Stage 3D.1 assignment-shuffle generator audit.",
                "module": "scope_static.experiments.stage3.assignment_shuffle_audit",
            },
            {
                "name": "scope-stage3d2-feature-scramble",
                "role": "Run the Stage 3D.2 feature-scramble generator audit.",
                "module": "scope_static.experiments.stage3.feature_scramble_audit",
            },
            {
                "name": "scope-stage3d3-context-shuffle",
                "role": "Run the Stage 3D.3 context-shuffle protocol audit.",
                "module": "scope_static.experiments.stage3.context_shuffle_audit",
            },
            {
                "name": "scope-stage3d4-k-stress",
                "role": "Run the Stage 3D.4 K undercomplete/exact/overcomplete stress audit.",
                "module": "scope_static.experiments.stage3.k_stress_audit",
            },
            {
                "name": "scope-stage3d4b-overcomplete-merge-prune",
                "role": "Run the Stage 3D.4b visible-only overcomplete merge/prune audit.",
                "module": "scope_static.experiments.stage3.overcomplete_merge_prune_audit",
            },
            {
                "name": "scope-stage3-abc-observability-diagnostic",
                "role": "Run diagnostic-only A/B/C observability upper-bound checks for targeted Stage 3 mechanisms.",
                "module": "scope_static.experiments.stage3.observability_abc_diagnostic",
            },
            {
                "name": "scope-stage4-synthetic-freeze",
                "role": "Build a synthetic Google-shaped Stage 3A-compatible source freeze.",
                "module": "scope_static.experiments.stage4.synthetic_freeze",
            },
            {
                "name": "scope-stage4-source-ceiling",
                "role": "Audit source-surface mechanism and quotient survival.",
                "module": "scope_static.experiments.stage4.source_ceiling",
            },
            {
                "name": "scope-stage4-source-pretrain",
                "role": "Train source replay models from visible features.",
                "module": "scope_static.experiments.stage4.source_pretrain",
            },
            {
                "name": "scope-stage4-support-audit",
                "role": "Audit source and Google support overlap before transfer claims.",
                "module": "scope_static.experiments.stage4.support_audit",
            },
            {
                "name": "scope-stage4-assignment-geometry",
                "role": "Audit source and Google assignment support geometry.",
                "module": "scope_static.experiments.stage4.assignment_geometry",
            },
            {
                "name": "scope-stage4-google-unit-source-expansion",
                "role": "Build Google-unit controlled source artifacts.",
                "module": "scope_static.experiments.stage4.google_unit_source_expansion",
            },
            {
                "name": "scope-stage4-google-transfer",
                "role": "Run frozen source-to-Google transfer.",
                "module": "scope_static.experiments.stage4.google_transfer",
            },
            {
                "name": "scope-stage4-transfer-diagnostics",
                "role": "Run transfer diagnostics and controls.",
                "module": "scope_static.experiments.stage4.transfer_diagnostics",
            },
            {
                "name": "scope-stage5b1-property-recovery",
                "role": "Run S5B1 context-relative property recovery.",
                "module": "scope_static.experiments.stage5.property_recovery",
            },
            {
                "name": "scope-stage5b1b-conditional-property-recovery",
                "role": "Run S5B1b conditional property recovery.",
                "module": "scope_static.experiments.stage5.conditional_property_recovery",
            },
            {
                "name": "scope-google-s3-visible-cache-v2",
                "role": "Precompute the read-only public cache for Google S3A V2 syndrome-response signatures.",
                "module": "scope_static.experiments.willow_data.s3_visible_cache_v2",
            },
            {
                "name": "scope-google-s3-visible-aggregate-v2",
                "role": "Precompute accelerated per-context aggregate rows for Google S3A V2 syndrome-response signatures.",
                "module": "scope_static.experiments.willow_data.s3_visible_aggregate_v2",
            },
            {
                "name": "scope-google-s3-visible-adapter-v2",
                "role": "Build Google real-data public syndrome-response signatures as a Stage 3A-compatible visible surface.",
                "module": "scope_static.experiments.willow_data.s3_visible_adapter_v2",
            },
        ],
        "primary_outputs": [
            "Layer1 preprocessing mechanism records, probe schedules, sampled observations, and sampling audits",
            "Layer 2 teacher self-audit BA/ARI/NMI/min-recall metrics",
            "Layer 3 visible ceiling, learner classification, channel-distance, NLL, and MAE metrics",
            "Stage 3A visible schema, split manifest, batch/context schema, assignment unit, and forbidden-feature audit",
            "Stage 3A.5 pairwise visible distances, oracle alias classes, exact-label ceiling, and quotient-label ceiling",
            "Stage 3B.0 non-learned visible-only baseline assignments, controls, evaluator-only metrics, and model-selection audit",
            "Stage 3B.1 learned assignment matrix, visible prototypes, covariance parameters, heldout visible-generation metrics, and label-leakage audit",
            "Stage 3C heldout visible-generation metrics against predicted assignments, oracle comparators, global-null, and mean-only baselines",
            "Stage 3D assignment-shuffle, feature-scramble, context-shuffle, K-stress, and overcomplete merge/prune robustness audits",
        ],
    }


def format_toolbox_manifest(manifest: dict[str, object]) -> str:
    lines = [f"{manifest['name']} ({manifest['status']})", ""]
    lines.append("Program surface:")
    for item in manifest.get("program_surface", []):  # type: ignore[assignment]
        if not isinstance(item, dict):
            continue
        lines.append(f"  {item['name']}: {item['role']}")
    lines.append("")
    lines.append("Physicality boundary:")
    lines.append(f"  {manifest['physicality_boundary']}")
    lines.append("")
    lines.append("Layers:")
    for layer in manifest["layers"]:  # type: ignore[index]
        if not isinstance(layer, dict):
            continue
        lines.append(f"  {layer['layer_name']}")
        lines.append(f"    {layer['role']}")
    lines.append("")
    lines.append("Commands:")
    for command in manifest["commands"]:  # type: ignore[index]
        if not isinstance(command, dict):
            continue
        lines.append(f"  {command['name']}: {command['role']}")
    lines.append("")
    lines.append(str(manifest["claim_boundary"]))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Print the SCOPE-Static pre-release toolbox manifest.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)
    manifest = toolbox_manifest()
    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(format_toolbox_manifest(manifest))


if __name__ == "__main__":
    main()
