from __future__ import annotations


def feature_block_indices(feature_names: list[str]) -> dict[str, list[int]]:
    blocks: dict[str, list[int]] = {}
    for idx, name in enumerate(feature_names):
        block = feature_block_name(str(name))
        blocks.setdefault(block, []).append(int(idx))
    return dict(sorted(blocks.items()))


def feature_block_name(name: str) -> str:
    parts = name.split("__")
    if len(parts) >= 2 and parts[0] in {"raw", "meta"}:
        return f"{parts[0]}__{parts[1]}"
    if parts and parts[0] == "visible_metadata":
        return "visible_metadata"
    return "other"
