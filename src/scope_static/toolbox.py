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
            "Stage 2 validated the physical mechanism catalog and the no-leakage "
            "visible recovery protocol. Stage 3 now removes direct mechanism-label "
            "supervision and tests whether SCOPE-Discovery can recover latent "
            "mechanism structure, assignments, and prototypes from the same "
            "learner-visible observation surface."
        ),
        "program_surface": [
            {
                "name": "generate_noisy_data",
                "role": "Generate sampled noisy data from user-enabled physical mechanisms.",
                "primary_layer": "Layer 1: Data Preparation (Prep)",
                "config_template": "configs/scope_static/layer1_user_defined_mechanisms.yaml",
            },
            {
                "name": "learn_and_replay_visible_noise",
                "role": "Learn from learner-visible observations and score similar generated noisy data.",
                "primary_layer": "Layer 3: Learner Classification and Noise Generation (Learner)",
                "metrics": ["channel_distance", "visible_gaussian_nll", "population_ce", "visible_feature_mae"],
            },
            {
                "name": "discover_mechanism_cause",
                "role": "Stage 3 +1 object: distinguish the latent mechanism cause without direct mechanism-label supervision.",
                "roadmap": "docs/STAGE3_ROADMAP.md",
            },
        ],
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
        ],
        "primary_outputs": [
            "Layer 1 mechanism records, probe schedules, sampled observations, and sampling audits",
            "Layer 2 teacher self-distinguishment BA/ARI/NMI/min-recall metrics",
            "Layer 3 visible ceiling, learner classification, channel-distance, NLL, and MAE metrics",
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
