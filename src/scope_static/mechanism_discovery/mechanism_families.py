from __future__ import annotations

from typing import Mapping


FAMILY_BUCKETS = (
    "readout_spam",
    "prep_reset",
    "spatial_two_qubit_crosstalk",
    "temporal_stability_drift",
    "logical_tail_high_impact",
)


def mechanism_family_bucket(record: Mapping[str, object]) -> str:
    label = str(record.get("oracle_label", record.get("mechanism_id", "")))
    text = " ".join(str(record.get(key, "")) for key in ("name", "mechanism_id", "mechanism_set", "instruction")).lower()
    if label in {"M1", "M2", "M3", "M16"} or any(token in text for token in ("readout", "measure", "spam")):
        return "readout_spam"
    if label in {"M17", "M18"} or any(token in text for token in ("prep", "reset")):
        return "prep_reset"
    if label in {"M8", "M9", "M10", "M11", "M12"} or any(token in text for token in ("rzz", "crosstalk", "correlated", "two")):
        return "spatial_two_qubit_crosstalk"
    if label in {"M13", "M14", "M20"} or any(token in text for token in ("drift", "idle", "dephasing", "relaxation", "overrotation")):
        return "temporal_stability_drift"
    if any(token in text for token in ("logical", "boundary", "leakage", "thermal", "tail")):
        return "logical_tail_high_impact"
    if label.startswith("M") and label[1:].isdigit():
        return FAMILY_BUCKETS[int(label[1:]) % len(FAMILY_BUCKETS)]
    return "readout_spam"


def records_by_family_bucket(records: list[dict[str, object]]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {bucket: [] for bucket in FAMILY_BUCKETS}
    for idx, record in enumerate(records):
        out[mechanism_family_bucket(record)].append(idx)
    all_indices = list(range(len(records)))
    for bucket in FAMILY_BUCKETS:
        if not out[bucket]:
            out[bucket] = list(all_indices)
    return out
