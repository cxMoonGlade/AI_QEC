from __future__ import annotations

import tomllib
from pathlib import Path

from scope_static.toolbox import toolbox_manifest


def test_toolbox_manifest_exports_public_layers_and_commands() -> None:
    manifest = toolbox_manifest()

    assert manifest["name"] == "SCOPE-Static Physical Mechanism Toolbox"
    assert [stage["stage_index"] for stage in manifest["catalog_stages"]] == [1, 2, 3]
    assert [stage["legacy_alias"] for stage in manifest["catalog_stages"]] == ["PHYC1", "PHYC2", "PHYC3"]
    command_names = {command["name"] for command in manifest["commands"]}
    assert {
        "scope-static-toolbox",
        "scope-catalog-teacher",
        "scope-data-preparation-teacher",
        "teacher-distinguishment",
        "learner-acceptance",
        "scope-stage3a-freeze",
        "scope-stage3a5-ceiling",
        "scope-stage3b0-baselines",
        "scope-stage3b1-discovery",
    }.issubset(command_names)


def test_pyproject_exposes_toolbox_console_scripts() -> None:
    data = tomllib.loads(Path("pyproject.toml").read_text())
    scripts = data["project"]["scripts"]

    assert scripts["scope-static-toolbox"] == "scope_static.toolbox:main"
    assert scripts["scope-catalog-teacher"] == "scope_static.experiments.qec_noise_catalog.controlled_catalog_teacher:main"
    assert scripts["scope-data-preparation-teacher"] == "scope_static.experiments.qec_noise_catalog.data_preparation_teacher:main"
    assert scripts["teacher-distinguishment"] == "scope_static.experiments.qec_noise_catalog.teacher_distinguishment:main"
    assert scripts["learner-acceptance"] == "scope_static.experiments.qec_noise_catalog.learner_acceptance:main"
    assert scripts["scope-stage3a-freeze"] == "scope_static.experiments.stage3.protocol_freeze:main"
    assert scripts["scope-stage3a5-ceiling"] == "scope_static.experiments.stage3.observability_ceiling:main"
    assert scripts["scope-stage3b0-baselines"] == "scope_static.experiments.stage3.baselines:main"
    assert scripts["scope-stage3b1-discovery"] == "scope_static.experiments.stage3.discovery_model:main"
