from __future__ import annotations

import argparse
import json

from .physical.layers import layer_stack_metadata


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
            "separability, and train Layer 3 learners that recover and replay "
            "learner-visible noisy observation distributions without oracle "
            "leakage. Stage 3 is the next claim boundary: remove direct "
            "mechanism-label supervision and test whether latent mechanism "
            "structure can be inferred from visible observations alone."
        ),
        "program_surface": [
            {
                "name": "generate_teacher_declared_observations",
                "role": "Generate teacher-declared noisy QEC observations from a controlled catalog.",
                "primary_layer": "Layer 1: Data Preparation (Prep)",
                "config_template": "configs/scope_static/layer1_user_defined_mechanisms.yaml",
            },
            {
                "name": "learn_and_replay_visible_noise",
                "role": "Learn from learner-visible observations and score recovery/replay of visible noisy observation distributions.",
                "primary_layer": "Layer 3: Learner Classification and Noise Generation (Learner)",
                "metrics": ["channel_distance", "visible_gaussian_nll", "population_ce", "visible_feature_mae"],
            },
            {
                "name": "discover_latent_mechanism_quotient",
                "role": "Stage 3 +1 object: infer the latent mechanism quotient without direct mechanism-label supervision.",
                "roadmap": "docs/STAGE3_ROADMAP.md",
            },
        ],
        "physicality_boundary": (
            "Layer 1 physicality comes from implemented catalog mechanisms: "
            "unitary channels, Kraus channels, and classical readout assignment "
            "matrices. Layer 3 does not yet learn arbitrary CPTP/GKSL channels "
            "by construction. Layer 1 emits cptp_guardrail_audit.json for "
            "per-run artifact-level physicality audits."
        ),
        "layers": layer_stack_metadata(),
        "commands": [
            {
                "name": "scope-static-toolbox",
                "role": "Print the toolbox manifest and public layer map.",
                "module": "scope_static.toolbox",
            },
            {
                "name": "scope-layer1-prep",
                "role": "Generate Layer 1 physical-mechanism data artifacts.",
                "module": "scope_static.experiments.run_s2d_physical_teacher",
            },
            {
                "name": "scope-layer2-teacher",
                "role": "Run Layer 2 teacher self-distinguishment.",
                "module": "scope_static.experiments.run_phyc2_sampled_observation_separability",
            },
            {
                "name": "scope-layer3-canonical",
                "role": "Run Layer 3 canonical learner/noise-generation acceptance.",
                "module": "scope_static.experiments.run_layer3_canonical_acceptance",
            },
            {
                "name": "scope-stage3a-freeze",
                "role": "Freeze the Stage 3A learner-visible dataset and protocol artifacts.",
                "module": "scope_static.experiments.run_stage3a_protocol_freeze",
            },
            {
                "name": "scope-stage3a5-ceiling",
                "role": "Compute the Stage 3A.5 visible observability and alias ceiling.",
                "module": "scope_static.experiments.run_stage3a5_observability_ceiling",
            },
            {
                "name": "scope-stage3b0-baselines",
                "role": "Run Stage 3B.0 visible-only non-learned clustering baselines.",
                "module": "scope_static.experiments.run_stage3b0_baselines",
            },
            {
                "name": "scope-stage3b1-discovery",
                "role": "Train the Stage 3B.1 visible-only prototype-mixture discovery model.",
                "module": "scope_static.experiments.run_stage3b1_discovery_model",
            },
        ],
        "primary_outputs": [
            "Layer 1 mechanism records, probe schedules, sampled observations, and sampling audits",
            "Layer 2 teacher self-distinguishment BA/ARI/NMI/min-recall metrics",
            "Layer 3 visible ceiling, learner classification, channel-distance, NLL, and MAE metrics",
            "Stage 3A visible schema, split manifest, batch/context schema, assignment unit, and forbidden-feature audit",
            "Stage 3A.5 pairwise visible distances, oracle alias classes, exact-label ceiling, and quotient-label ceiling",
            "Stage 3B.0 non-learned visible-only baseline assignments, controls, evaluator-only metrics, and model-selection audit",
            "Stage 3B.1 learned assignment matrix, visible prototypes, covariance parameters, heldout visible-generation metrics, and label-leakage audit",
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
        lines.append(f"  {layer['layer_name']} [legacy {layer['legacy_alias']}]")
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
