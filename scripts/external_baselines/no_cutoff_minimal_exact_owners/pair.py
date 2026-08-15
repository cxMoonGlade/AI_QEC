"""Sparse exact-pair micro-owner for the frozen qualification recurrence."""

from __future__ import annotations

from collections import defaultdict

from .model import (
    MICRO_SCOPE,
    SOLVER_PERMISSION,
    TARGET_LOWERING,
    Codec,
    PairAddProgram,
    PairKey,
    Qsqrt2i,
    ZERO,
    canonical_json_bytes,
    sha256_json,
    validate_frozen_pair_add_program,
)


def _combine(entries: tuple[tuple[PairKey, Qsqrt2i], ...]) -> dict[PairKey, Qsqrt2i]:
    result: dict[PairKey, Qsqrt2i] = {}
    for key, coefficient in entries:
        value = result.get(key, ZERO) + coefficient
        if value.is_zero():
            result.pop(key, None)
        else:
            result[key] = value
    return result


def _snapshot(
    label: str,
    codec: Codec,
    coefficient_map: dict[PairKey, Qsqrt2i],
) -> dict[str, object]:
    entries = [
        {
            "bits": list(codec.encode(key)),
            "coefficient": coefficient.to_data(),
            "key": key.to_data(),
        }
        for key, coefficient in coefficient_map.items()
    ]
    entries.sort(key=canonical_json_bytes)
    truth_entries = [
        {"bits": entry["bits"], "coefficient": entry["coefficient"]}
        for entry in entries
    ]
    return {
        "codec_sha256": codec.sha256,
        "entries": entries,
        "label": label,
        "map_sha256": sha256_json(entries),
        "support": len(entries),
        "truth_entries_sha256": sha256_json(truth_entries),
    }


def run_pair_owner(program: PairAddProgram) -> dict[str, object]:
    """Run the explicit sparse recurrence; this is not a target QEC owner."""

    validate_frozen_pair_add_program(program)
    current = _combine(program.initial)
    checkpoints = [_snapshot("A0", program.codecs[0], current)]
    for index, event in enumerate(program.events):
        rows_by_input: dict[PairKey, list[tuple[PairKey, Qsqrt2i]]] = defaultdict(list)
        for row in event.rows:
            rows_by_input[row.input_key].append((row.output_key, row.weight))
        next_map: dict[PairKey, Qsqrt2i] = {}
        for input_key, input_coefficient in current.items():
            for output_key, weight in rows_by_input.get(input_key, ()):
                value = next_map.get(output_key, ZERO) + input_coefficient * weight
                if value.is_zero():
                    next_map.pop(output_key, None)
                else:
                    next_map[output_key] = value
        current = next_map
        checkpoints.append(_snapshot(event.name, program.codecs[index + 1], current))

    support_history = [int(checkpoint["support"]) for checkpoint in checkpoints]
    peak = max(support_history)
    peak_index = support_history.index(peak)
    peak_event = "INITIAL" if peak_index == 0 else program.events[peak_index - 1].name
    return {
        "checkpoints": checkpoints,
        "history_sha256": sha256_json(support_history),
        "n_pauli_pair_states_peak_micro": peak,
        "peak_event": peak_event,
        "program_sha256": program.sha256,
        "scope": MICRO_SCOPE,
        "solver_permission": SOLVER_PERMISSION,
        "support_history": support_history,
        "target_lowering": TARGET_LOWERING,
    }
