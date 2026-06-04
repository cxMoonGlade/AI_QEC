from __future__ import annotations

import tomllib
from pathlib import Path

from scope_static.toolbox import toolbox_manifest


def test_toolbox_manifest_exports_public_layers_and_commands() -> None:
    manifest = toolbox_manifest()

    assert manifest["name"] == "SCOPE-Static Physical Mechanism Toolbox"
    assert [stage["stage_index"] for stage in manifest["catalog_stages"]] == [1, 2, 3]
    assert [stage["stage_name"] for stage in manifest["catalog_stages"]] == [
        "Layer1 preprocessing - teacher generator",
        "Layer 2 teacher self-audit",
        "Layer 3 learner",
    ]
    assert all("legacy_alias" not in stage for stage in manifest["catalog_stages"])
    command_names = {command["name"] for command in manifest["commands"]}
    assert {
        "scope-static-toolbox",
        "scope-data-preparation-teacher",
        "scope-stage3a-freeze",
        "scope-stage3a5-ceiling",
        "scope-stage3b0-baselines",
        "scope-stage3b1-discovery",
        "scope-stage3c-generator",
        "scope-stage3-abc-observability-diagnostic",
        "scope-google-s3-visible-cache-v2",
        "scope-google-s3-visible-aggregate-v2",
        "scope-google-s3-visible-adapter-v2",
    }.issubset(command_names)


def test_pyproject_exposes_toolbox_console_scripts() -> None:
    data = tomllib.loads(Path("pyproject.toml").read_text())
    scripts = data["project"]["scripts"]

    assert scripts["scope-static-toolbox"] == "scope_static.toolbox:main"
    assert scripts["scope-data-preparation-teacher"] == "scope_static.experiments.qec_noise_catalog.data_preparation_teacher:main"
    assert "scope-catalog-teacher" not in scripts
    assert "teacher-distinguishment" not in scripts
    assert "learner-acceptance" not in scripts
    assert scripts["scope-stage3a-freeze"] == "scope_static.experiments.stage3.protocol_freeze:main"
    assert scripts["scope-stage3a5-ceiling"] == "scope_static.experiments.stage3.observability_ceiling:main"
    assert scripts["scope-stage3b0-baselines"] == "scope_static.experiments.stage3.baselines:main"
    assert scripts["scope-stage3b1-discovery"] == "scope_static.experiments.stage3.discovery_model:main"
    assert scripts["scope-stage3c-generator"] == "scope_static.experiments.stage3.generator_learning:main"
    assert scripts["scope-stage3-abc-observability-diagnostic"] == "scope_static.experiments.stage3.observability_abc_diagnostic:main"
    assert scripts["scope-google-s3-visible-cache-v2"] == "scope_static.experiments.willow_data.s3_visible_cache_v2:main"
    assert scripts["scope-google-s3-visible-aggregate-v2"] == "scope_static.experiments.willow_data.s3_visible_aggregate_v2:main"
    assert scripts["scope-google-s3-visible-adapter-v2"] == "scope_static.experiments.willow_data.s3_visible_adapter_v2:main"
