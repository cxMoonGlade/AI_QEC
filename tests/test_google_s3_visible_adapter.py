from __future__ import annotations

import yaml

from scope_static.experiments.willow_data.s3_visible_adapter import main
from scope_static.mechanism_discovery.artifacts import load_stage3a_visible_features

from google_s3_fixture import write_tiny_google_s3_dataset


def test_google_s3_visible_adapter_cli_uses_config_and_writes_artifacts(tmp_path) -> None:
    root = write_tiny_google_s3_dataset(tmp_path, contexts=3)
    output = tmp_path / "adapter_out"
    config = tmp_path / "adapter.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "google_s3_visible_adapter": {
                    "dataset_root": str(root),
                    "output_dir": str(output),
                    "max_contexts": 3,
                    "windows_per_context": 1,
                    "shotblocks_per_context": 2,
                    "shotblock_size": 2,
                    "min_shotblock_size": 2,
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = main(["--config", str(config)])
    visible = load_stage3a_visible_features(output)

    assert result["decision"] == "google_s3_visible_surface_passed"
    assert visible.matrix.shape[0] == 6
    assert (output / "forbidden_feature_audit.json").exists()
    assert (output / "split_manifest.json").exists()

