from __future__ import annotations

from pathlib import Path

import yaml


DEFAULT_OUTPUT_ROOT = Path("outputs/scope_static")


def load_s2d_physical_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D config must be a mapping")
    section = data.get("s2d_physical", data)
    if not isinstance(section, dict):
        raise ValueError("s2d_physical config must be a mapping")
    result = dict(section)
    if "run" in data and isinstance(data["run"], dict):
        result.setdefault("run", dict(data["run"]))
    return result


def output_root_from_config(config: dict[str, object]) -> Path:
    run = config.get("run", {})
    if isinstance(run, dict) and run.get("output_root"):
        return Path(str(run["output_root"]))
    return DEFAULT_OUTPUT_ROOT
