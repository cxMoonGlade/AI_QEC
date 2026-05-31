from __future__ import annotations

from collections.abc import Iterable, Mapping

import numpy as np

from scope_static.backend.mechanism_catalog import IMPLEMENTED_MECHANISM_IDS, PREP_RESET_MECHANISM_IDS, READOUT_MECHANISM_IDS

PHYC1_STAGE_NAME = "S2D_PHYC1_teacher"
PHYC1_LEGACY_STAGE_NAME = "S2D_PHYS1_teacher"
PHYC1_PREFLIGHT_STAGE_NAME = "S2D_PHYS0_preflight"

FULL_CIRCUIT_TEACHER_MODEL = "full_circuit_cudaq"
LOCAL_OBSERVABLE_TEACHER_MODEL = "local_observable_gpu"

FULL_CIRCUIT_TEACHER_ALIASES = {"full_circuit", "full_circuit_cudaq", "cudaq_full_circuit"}
LOCAL_OBSERVABLE_TEACHER_ALIASES = {"local_observable", "local_observable_gpu", "born_local"}

FULL_CIRCUIT_DEPTH_SEMANTICS = "literal_full_n_qubit_cudaq_schedule"
FULL_CIRCUIT_RZZ_GATE_SEMANTICS = "logical_rzz_unitary_with_post_rzz_mechanism_channel"
FULL_CIRCUIT_CONTRACT_NOTE = "Samples literal n-qubit noisy circuits at configured gate depth."
FULL_CIRCUIT_MECHANISM_APPLICATION_CONVENTION = "post_gate_or_post_reset_channel_at_scheduled_location"
READOUT_APPLICATION_CONVENTION = "post_sample_assignment_postprocess"

MIXED_BASIS_ACTIVE_PROBES = ("alt_xz", "alt_zx", "alt_yz", "alt_zy", "alt_xy", "alt_yx")
RZZ_DEPTH_SWEEP_DEPTHS = (1, 2, 4, 8)
RZZ_DEPTH_SWEEP_PROBES = tuple(f"rzz_depth_{depth}" for depth in RZZ_DEPTH_SWEEP_DEPTHS)
RZZ_ECHO_CONTRAST_PROBES = (
    "rzz_no_echo",
    "rzz_echo_left_even",
    "rzz_echo_right_even",
    "rzz_echo_both_even",
    "rzz_echo_left_odd",
    "rzz_echo_right_odd",
    "rzz_echo_both_odd",
)
RZZ_MINIMAL_INTERVENTION_PROBES = (
    "rzz_int_no_intervention",
    "rzz_int_basis_x",
    "rzz_int_basis_y",
    "rzz_int_basis_xz",
    "rzz_int_basis_yz",
    "rzz_int_twirl_x_left_even",
    "rzz_int_twirl_x_left_odd",
    "rzz_int_twirl_y_left_even",
    "rzz_int_twirl_y_left_odd",
    "rzz_int_twirl_xy_even",
    "rzz_int_twirl_xy_odd",
    "rzz_int_sign_no_flip",
    "rzz_int_sign_flip_left_even",
    "rzz_int_sign_flip_right_even",
    "rzz_int_sign_flip_left_odd",
    "rzz_int_sign_flip_right_odd",
)
RZZ_TOMO_PREP_STATES = ("Zp", "Zm", "Xp", "Yp")
RZZ_TOMO_MEAS_AXES = ("X", "Y", "Z")
RZZ_TOMO_EDGE_PARITIES = ("even", "odd")
RZZ_LOCAL_TOMOGRAPHY_PROBES = tuple(
    f"rzz_tomo_p{prep_left}{prep_right}_m{meas_left}{meas_right}_{parity}"
    for prep_left in RZZ_TOMO_PREP_STATES
    for prep_right in RZZ_TOMO_PREP_STATES
    for meas_left in RZZ_TOMO_MEAS_AXES
    for meas_right in RZZ_TOMO_MEAS_AXES
    for parity in RZZ_TOMO_EDGE_PARITIES
)
EDGE_ORIENTATION_RULE = "lower_qubit_to_higher_qubit"
GATE_MECHANISM_IDS = set(IMPLEMENTED_MECHANISM_IDS).difference(set(READOUT_MECHANISM_IDS) | set(PREP_RESET_MECHANISM_IDS))
OTHER_MECHANISM_IDS = {"M19", "M24"}


def normalize_phyc1_teacher_model(
    config: Mapping[str, object],
    *,
    original_config: Mapping[str, object] | None = None,
) -> str:
    requested = config.get("physical_teacher_model", config.get("teacher_model"))
    source = original_config if original_config is not None else config
    if requested is None and str(source.get("backend", "")).strip() == LOCAL_OBSERVABLE_TEACHER_MODEL:
        requested = LOCAL_OBSERVABLE_TEACHER_MODEL
    model = str(requested or FULL_CIRCUIT_TEACHER_MODEL).strip().lower().replace("-", "_")
    if model in LOCAL_OBSERVABLE_TEACHER_ALIASES:
        return LOCAL_OBSERVABLE_TEACHER_MODEL
    if model in FULL_CIRCUIT_TEACHER_ALIASES:
        return FULL_CIRCUIT_TEACHER_MODEL
    raise ValueError("physical_teacher_model must be 'full_circuit_cudaq' or 'local_observable_gpu'")


def circuit_depth(config: Mapping[str, object]) -> int:
    for key in ("circuit_depth", "depth", "num_layers"):
        if key in config:
            return max(1, int(config.get(key, 1) or 1))
    return 1


def full_circuit_depth_metadata(depth: int) -> dict[str, object]:
    depth = int(depth)
    return {
        "circuit_depth": depth,
        "configured_circuit_depth": depth,
        "effective_circuit_depth": depth,
        "circuit_depth_semantics": FULL_CIRCUIT_DEPTH_SEMANTICS,
    }


def apply_full_circuit_depth_metadata(config: dict[str, object], depth: int) -> None:
    config.update(full_circuit_depth_metadata(depth))


def probe_names(probe_set: str) -> list[str]:
    if probe_set == "base":
        return ["z_basis", "x_measure", "y_measure"]
    if probe_set == "rzz_active_minimal":
        return ["z_basis", "x_measure", "y_measure", *MIXED_BASIS_ACTIVE_PROBES]
    if probe_set == "rzz_depth_sweep":
        return ["z_basis", "x_measure", "y_measure", *RZZ_DEPTH_SWEEP_PROBES]
    if probe_set == "rzz_echo_no_echo":
        return ["z_basis", "x_measure", "y_measure", *RZZ_ECHO_CONTRAST_PROBES]
    if probe_set == "rzz_minimal_intervention":
        return ["z_basis", "x_measure", "y_measure", *RZZ_MINIMAL_INTERVENTION_PROBES]
    if probe_set == "rzz_local_tomography":
        return list(RZZ_LOCAL_TOMOGRAPHY_PROBES)
    if probe_set == "basis":
        return ["z_basis", "x_basis", "y_basis", "x_measure", "y_measure"]
    if probe_set == "full":
        return ["z_basis", "x_basis", "y_basis", "x_measure", "y_measure", "alternating_x", "echo"]
    if probe_set == "echo":
        return ["z_basis", "echo"]
    if probe_set == "base_idle_echo":
        return ["z_basis", "x_measure", "y_measure", "idle", "echo"]
    return [probe_set]


def mechanism_counts(records: Iterable[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        label = str(record["oracle_label"])
        counts[label] = counts.get(label, 0) + 1
    return counts


def counts_to_bit_matrix(counts: Mapping[str, int], *, shots: int, num_bits: int) -> np.ndarray:
    num_bits = int(num_bits)
    keys = []
    repeat_counts = []
    total = 0
    for key, count in sorted(counts.items()):
        c = int(count)
        keys.append(key)
        repeat_counts.append(c)
        total += c
    if total != int(shots):
        raise ValueError(f"counts contain {total} shots, expected {shots}")
    if not keys:
        return np.zeros((0, num_bits), dtype=np.uint8)
    unique_rows = np.zeros((len(keys), num_bits), dtype=np.uint8)
    for idx, key in enumerate(keys):
        unique_rows[idx] = count_key_to_bit_row(key, num_bits=num_bits)
    return np.repeat(unique_rows, np.asarray(repeat_counts, dtype=np.int64), axis=0)


def count_key_to_bit_row(key: object, *, num_bits: int) -> np.ndarray:
    text = str(key).replace(" ", "")
    row = np.zeros(int(num_bits), dtype=np.uint8)
    if text.startswith(("0x", "0X")):
        value = int(text, 16)
        for idx in range(int(num_bits)):
            row[idx] = (value >> idx) & 1
        return row
    for idx, char in enumerate(reversed(text[-int(num_bits) :])):
        row[idx] = 1 if char == "1" else 0
    return row
