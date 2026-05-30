from __future__ import annotations

import tomllib
from pathlib import Path

from scope_static.toolbox import toolbox_manifest


def test_toolbox_manifest_exports_public_layers_and_commands() -> None:
    manifest = toolbox_manifest()

    assert manifest["name"] == "SCOPE-Static Physical Mechanism Toolbox"
    assert [layer["layer_index"] for layer in manifest["layers"]] == [1, 2, 3]
    assert [layer["legacy_alias"] for layer in manifest["layers"]] == ["PHYC1", "PHYC2", "PHYC3"]
    command_names = {command["name"] for command in manifest["commands"]}
    assert {
        "scope-static-toolbox",
        "scope-layer1-prep",
        "scope-layer2-teacher",
        "scope-layer3-canonical",
        "scope-stage3a-freeze",
        "scope-stage3a5-ceiling",
        "scope-stage3b0-baselines",
        "scope-stage3b1-discovery",
    }.issubset(command_names)


def test_pyproject_exposes_toolbox_console_scripts() -> None:
    data = tomllib.loads(Path("pyproject.toml").read_text())
    scripts = data["project"]["scripts"]

    assert scripts["scope-static-toolbox"] == "scope_static.toolbox:main"
    assert scripts["scope-layer1-prep"] == "scope_static.experiments.run_s2d_physical_teacher:main"
    assert scripts["scope-layer2-teacher"] == "scope_static.experiments.run_phyc2_sampled_observation_separability:main"
    assert scripts["scope-layer3-canonical"] == "scope_static.experiments.run_layer3_canonical_acceptance:main"
    assert scripts["scope-stage3a-freeze"] == "scope_static.experiments.run_stage3a_protocol_freeze:main"
    assert scripts["scope-stage3a5-ceiling"] == "scope_static.experiments.run_stage3a5_observability_ceiling:main"
    assert scripts["scope-stage3b0-baselines"] == "scope_static.experiments.run_stage3b0_baselines:main"
    assert scripts["scope-stage3b1-discovery"] == "scope_static.experiments.run_stage3b1_discovery_model:main"
