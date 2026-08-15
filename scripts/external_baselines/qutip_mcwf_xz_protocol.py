#!/usr/bin/env python3
"""Neutral protocol and statistics for the isolated QuTiP MCWF X/Z check.

This module is intentionally standard-library only.  It is shared by the
project-side orchestrator and the isolated baseline worker, and imports no
simulator implementation or external solver.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from pathlib import Path
from typing import Any


FIXTURE_SCHEMA = "error_coupling_simulator.neutral.mcwf_xz_fixture.v2"
REGISTRY_SCHEMA = (
    "error_coupling_simulator.neutral.mcwf_xz_comparison_registry.v1"
)
EXPECTED_FIXTURE_SHA256_BY_ID = {
    "two_qubit_t1_ordered_xz_reset": (
        "72d46d517d2e880327f22148e94611aa3b3c503a4a62d8ee18cf12b2d610257b"
    ),
    "two_qubit_pure_dephasing_ordered_xz_reset": (
        "90604ed353b2334810d6b0af89d82da04e42f4523d47ca846652c21d0c13ca72"
    ),
    "two_qubit_thermal_ordered_xz_reset": (
        "6f1691b833036201fdfcf524e3ddd52d845fc4359fac1cc9d0a0230c74621de1"
    ),
}
EXPECTED_REGISTRY_SHA256 = (
    "3cd654e798a4c45d3bbebf51665ecffbc109f89ccb3a9eb776904236b5525d62"
)
EXPECTED_FIXTURE_IDS = tuple(sorted(EXPECTED_FIXTURE_SHA256_BY_ID))
EXPECTED_MEASUREMENT_KEYS = (
    "mx_before",
    "mz_before",
    "mx_after",
    "mz_after",
)
EXPECTED_MEASUREMENT_TARGETS = (0, 1, 0, 1)
EXPECTED_MEASUREMENT_BASES = ("X", "Z", "X", "Z")
EXPECTED_RESET_AFTER = (True, True, False, False)
EXPECTED_RESET_STATES = {"X": "|+>", "Z": "|0>"}
EXPECTED_DIRECTED_MARGINALS = {
    "two_qubit_t1_ordered_xz_reset": frozenset({"mz_before", "mx_after"}),
    "two_qubit_pure_dephasing_ordered_xz_reset": frozenset(
        {"mx_after", "mz_after"}
    ),
    "two_qubit_thermal_ordered_xz_reset": frozenset(
        {"mz_before", "mz_after"}
    ),
}
FINITE_STEP_MICROSTEP_COUNTS = (10, 20, 40, 80)
FINITE_STEP_EXPECTED_TVS = {
    10: (0.023409825026091874, 0.010275861041313533),
    20: (0.011859662816100847, 0.005088283414417721),
    40: (0.005967971464909766, 0.002531793804892407),
    80: (0.0029934385472444314, 0.0012628170724109378),
}
FINITE_STEP_RATIO_BAND = (1.85, 2.15)
FINITE_STEP_FINAL_JOINT_Z_TV_CAP = 0.0031
FINITE_STEP_FINAL_X_TV_CAP = 0.0013
FINITE_STEP_EXPECTED_JOINT_RADIUS = 0.0640322086265546
FINITE_STEP_EXPECTED_MARGINAL_RADIUS = 0.039518987893233104


def load_fixture(path: Path) -> dict[str, Any]:
    """Load and strictly validate one frozen neutral two-qubit fixture."""

    resolved = Path(path)
    observed_sha256 = fixture_sha256(resolved)
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("neutral MCWF X/Z fixture must be a JSON object")
    fixture = dict(raw)
    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("unsupported neutral MCWF X/Z fixture schema")
    fixture_id = fixture.get("fixture_id")
    if fixture_id not in EXPECTED_FIXTURE_SHA256_BY_ID:
        raise ValueError("unexpected neutral MCWF X/Z fixture id")
    expected_sha256 = EXPECTED_FIXTURE_SHA256_BY_ID[fixture_id]
    if observed_sha256 != expected_sha256:
        raise ValueError(
            "neutral MCWF X/Z fixture SHA-256 mismatch: "
            f"expected {expected_sha256}, observed {observed_sha256}"
        )
    required_keys = {
        "schema",
        "fixture_id",
        "claim_boundary",
        "num_qubits",
        "local_dims",
        "initial_levels",
        "collapse_terms",
        "evolution_segments_ns",
        "project_microstep_count",
        "trajectory_count",
        "seeds",
        "comparison_family_alpha",
        "numerical_zero",
        "measurements",
        "label_to_bit",
    }
    if fixture_id == "two_qubit_thermal_ordered_xz_reset":
        required_keys.add("thermal_metadata")
    if set(fixture) != required_keys:
        raise ValueError("neutral MCWF X/Z fixture fields drifted")
    if not isinstance(fixture.get("claim_boundary"), str) or not fixture[
        "claim_boundary"
    ].strip():
        raise ValueError("neutral MCWF X/Z claim_boundary must be nonempty")
    if fixture.get("num_qubits") != 2:
        raise ValueError("neutral MCWF X/Z fixture must contain two qubits")
    if fixture.get("local_dims") != [2, 2]:
        raise ValueError("neutral MCWF X/Z fixture local_dims must be [2, 2]")
    if fixture.get("initial_levels") != [0, 1]:
        raise ValueError("neutral MCWF X/Z fixture initial_levels must be [0, 1]")

    terms = fixture.get("collapse_terms")
    if not isinstance(terms, list) or not terms:
        raise ValueError("neutral MCWF X/Z collapse_terms must be nonempty")
    normalized_terms: list[dict[str, Any]] = []
    seen_term_ids: set[str] = set()
    for term in terms:
        if not isinstance(term, Mapping) or set(term) != {
            "term_id",
            "family",
            "target",
            "generator_rate_per_ns",
        }:
            raise ValueError("neutral MCWF X/Z collapse term fields drifted")
        term_id = term.get("term_id")
        family = term.get("family")
        target = term.get("target")
        if not isinstance(term_id, str) or not term_id or term_id in seen_term_ids:
            raise ValueError("neutral MCWF X/Z collapse term ids must be unique")
        seen_term_ids.add(term_id)
        if family not in {"number_dephasing", "sigma_minus", "sigma_plus"}:
            raise ValueError("neutral MCWF X/Z collapse family is unsupported")
        if isinstance(target, bool) or not isinstance(target, int) or target not in (0, 1):
            raise ValueError("neutral MCWF X/Z collapse target must be 0 or 1")
        rate = _positive_finite(
            term.get("generator_rate_per_ns"), "generator_rate_per_ns"
        )
        normalized_terms.append(
            {
                "term_id": term_id,
                "family": family,
                "target": target,
                "generator_rate_per_ns": rate,
            }
        )
    if [term["term_id"] for term in normalized_terms] != sorted(seen_term_ids):
        raise ValueError("neutral MCWF X/Z collapse terms must be term-id sorted")
    expected_families = {
        "two_qubit_t1_ordered_xz_reset": [
            (0, "sigma_minus"),
            (1, "sigma_minus"),
        ],
        "two_qubit_pure_dephasing_ordered_xz_reset": [
            (0, "number_dephasing"),
            (1, "number_dephasing"),
        ],
        "two_qubit_thermal_ordered_xz_reset": [
            (0, "sigma_minus"),
            (0, "sigma_plus"),
            (1, "sigma_minus"),
            (1, "sigma_plus"),
        ],
    }
    if [(term["target"], term["family"]) for term in normalized_terms] != (
        expected_families[fixture_id]
    ):
        raise ValueError("neutral MCWF X/Z collapse family/target contract drifted")

    segments = fixture.get("evolution_segments_ns")
    if not isinstance(segments, list) or len(segments) != 2:
        raise ValueError("neutral MCWF X/Z requires two evolution segments")
    durations = [
        _positive_finite(value, "evolution_segments_ns") for value in segments
    ]
    if durations != [10.0, 10.0]:
        raise ValueError("neutral MCWF X/Z evolution segments drifted")

    measurements = fixture.get("measurements")
    if not isinstance(measurements, list) or len(measurements) != 4:
        raise ValueError("neutral MCWF X/Z measurements must contain four entries")
    for measurement in measurements:
        if not isinstance(measurement, Mapping) or set(measurement) != {
            "key",
            "target",
            "basis",
            "reset",
            "reset_state",
        }:
            raise ValueError("neutral MCWF X/Z measurement fields drifted")
    _require_exact_sequence(
        [measurement["key"] for measurement in measurements],
        EXPECTED_MEASUREMENT_KEYS,
        "measurement_keys",
    )
    _require_exact_sequence(
        [measurement["target"] for measurement in measurements],
        EXPECTED_MEASUREMENT_TARGETS,
        "measurement_targets",
    )
    _require_exact_sequence(
        [measurement["basis"] for measurement in measurements],
        EXPECTED_MEASUREMENT_BASES,
        "measurement_bases",
    )
    _require_exact_sequence(
        [measurement["reset"] for measurement in measurements],
        EXPECTED_RESET_AFTER,
        "reset_after",
    )
    reset_states = {
        measurement["basis"]: measurement["reset_state"]
        for measurement in measurements
        if measurement["reset"]
    }
    if reset_states != EXPECTED_RESET_STATES or any(
        measurement["reset_state"] is not None
        for measurement in measurements
        if not measurement["reset"]
    ):
        raise ValueError("neutral MCWF X/Z reset-state contract drifted")

    rates = _rates_by_target({"collapse_terms": normalized_terms})
    expected_lambda = math.log(4.0) / 10.0
    if fixture_id == "two_qubit_t1_ordered_xz_reset":
        if any(
            abs(rates[target]["down"] - expected_lambda) > 1.0e-15
            or rates[target]["up"] != 0.0
            or rates[target]["dephasing"] != 0.0
            for target in (0, 1)
        ):
            raise ValueError("neutral F1 rate contract drifted")
    elif fixture_id == "two_qubit_pure_dephasing_ordered_xz_reset":
        if any(
            rates[target]["down"] != 0.0
            or rates[target]["up"] != 0.0
            or abs(rates[target]["dephasing"] - 2.0 * expected_lambda) > 1.0e-15
            for target in (0, 1)
        ):
            raise ValueError("neutral F2 rate contract drifted")
    else:
        thermal = fixture.get("thermal_metadata")
        if not isinstance(thermal, Mapping) or set(thermal) != {
            "n_bar",
            "gamma_base_per_ns",
            "up_over_down",
        }:
            raise ValueError("neutral F3 thermal metadata fields drifted")
        n_bar = _positive_finite(thermal.get("n_bar"), "n_bar")
        gamma_base = _positive_finite(
            thermal.get("gamma_base_per_ns"), "gamma_base_per_ns"
        )
        ratio = _positive_finite(thermal.get("up_over_down"), "up_over_down")
        if (
            abs(n_bar - 1.0 / 3.0) > 1.0e-15
            or abs(gamma_base - 3.0 * expected_lambda / 5.0) > 1.0e-15
            or ratio != 0.25
        ):
            raise ValueError("neutral F3 thermal metadata drifted")
        for target in (0, 1):
            down = rates[target]["down"]
            up = rates[target]["up"]
            if (
                abs(down - gamma_base * (n_bar + 1.0)) > 1.0e-15
                or abs(up - gamma_base * n_bar) > 1.0e-15
                or abs(up / down - ratio) > 1.0e-15
                or rates[target]["dephasing"] != 0.0
            ):
                raise ValueError("neutral F3 detailed-balance contract drifted")

    _positive_integer(
        fixture.get("project_microstep_count"), "project_microstep_count"
    )
    if _positive_integer(
        fixture.get("trajectory_count"), "trajectory_count"
    ) < 128:
        raise ValueError("trajectory_count must be at least 128")
    seeds = fixture.get("seeds")
    if not isinstance(seeds, Mapping) or set(seeds) != {
        "project",
        "qutip_mcwf",
        "qutip_measurement",
    }:
        raise ValueError("neutral MCWF X/Z seed fields drifted")
    for key, value in seeds.items():
        _positive_integer(value, key)
    alpha = _positive_finite(
        fixture.get("comparison_family_alpha"), "comparison_family_alpha"
    )
    if not alpha < 1.0:
        raise ValueError("comparison_family_alpha must be less than one")
    numerical_zero = _positive_finite(
        fixture.get("numerical_zero"), "numerical_zero"
    )
    if numerical_zero != 1.0e-12:
        raise ValueError("neutral fixture numerical_zero must be exactly 1e-12")
    if fixture.get("label_to_bit") != {"0": 0, "1": 1}:
        raise ValueError("neutral MCWF X/Z label-to-bit contract drifted")

    normalized = dict(fixture)
    normalized["collapse_terms"] = normalized_terms
    normalized["measurement_keys"] = list(EXPECTED_MEASUREMENT_KEYS)
    normalized["measurement_targets"] = list(EXPECTED_MEASUREMENT_TARGETS)
    normalized["measurement_bases"] = list(EXPECTED_MEASUREMENT_BASES)
    normalized["reset_after"] = list(EXPECTED_RESET_AFTER)
    normalized["reset_states"] = dict(EXPECTED_RESET_STATES)
    normalized["evolution_duration_ns"] = durations[0]
    normalized["microstep_count"] = normalized["project_microstep_count"]
    normalized["project_rng_seed"] = seeds["project"]
    normalized["qutip_mcwf_seed"] = seeds["qutip_mcwf"]
    normalized["qutip_measurement_seed"] = seeds["qutip_measurement"]
    normalized["comparison_alpha"] = alpha
    normalized["gamma_1_per_ns"] = rates[0]["down"]
    normalized["gamma_up_per_ns"] = rates[0]["up"]
    normalized["gamma_phi_per_ns"] = rates[0]["dephasing"] / 2.0
    normalized["target_survival_probability"] = math.exp(
        -rates[1]["down"] * durations[0]
    )
    return normalized


def load_comparison_registry(path: Path) -> dict[str, Any]:
    """Load the byte-pinned five-statistics-per-fixture comparison registry."""

    resolved = Path(path)
    observed_sha256 = fixture_sha256(resolved)
    if observed_sha256 != EXPECTED_REGISTRY_SHA256:
        raise ValueError(
            "neutral MCWF X/Z comparison registry SHA-256 mismatch: "
            f"expected {EXPECTED_REGISTRY_SHA256}, observed {observed_sha256}"
        )
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping) or set(raw) != {
        "schema",
        "comparison_family_alpha",
        "entries",
    }:
        raise ValueError("neutral MCWF X/Z comparison registry fields drifted")
    if raw.get("schema") != REGISTRY_SCHEMA:
        raise ValueError("unsupported neutral MCWF X/Z comparison registry schema")
    alpha = _positive_finite(
        raw.get("comparison_family_alpha"), "comparison_family_alpha"
    )
    if alpha != 0.01:
        raise ValueError("neutral MCWF X/Z comparison family alpha drifted")
    entries = raw.get("entries")
    if not isinstance(entries, list) or len(entries) != 15:
        raise ValueError("neutral MCWF X/Z registry must contain 15 entries")
    normalized_entries: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {
            "statistic_id",
            "fixture_id",
            "comparison_kind",
            "view",
            "column_key",
            "alphabet_size",
        }:
            raise ValueError("neutral MCWF X/Z registry entry fields drifted")
        statistic_id = entry.get("statistic_id")
        fixture_id = entry.get("fixture_id")
        kind = entry.get("comparison_kind")
        view = entry.get("view")
        column_key = entry.get("column_key")
        alphabet_size = entry.get("alphabet_size")
        if not isinstance(statistic_id, str) or not statistic_id:
            raise ValueError("neutral MCWF X/Z statistic id must be nonempty")
        if fixture_id not in EXPECTED_FIXTURE_IDS:
            raise ValueError("neutral MCWF X/Z registry fixture id drifted")
        if kind not in {
            "one_sample_project_dense",
            "one_sample_qutip_dense",
            "two_sample_qutip_project",
        }:
            raise ValueError("neutral MCWF X/Z comparison kind drifted")
        if view == "joint":
            if column_key is not None or alphabet_size != 16:
                raise ValueError("neutral MCWF X/Z joint registry entry drifted")
        elif view == "marginal":
            if (
                column_key not in EXPECTED_DIRECTED_MARGINALS[fixture_id]
                or alphabet_size != 2
                or kind != "one_sample_project_dense"
            ):
                raise ValueError("neutral MCWF X/Z marginal registry entry drifted")
        else:
            raise ValueError("neutral MCWF X/Z registry view drifted")
        normalized_entries.append(dict(entry))
    statistic_ids = [entry["statistic_id"] for entry in normalized_entries]
    if statistic_ids != sorted(set(statistic_ids)):
        raise ValueError("neutral MCWF X/Z registry entries must be uniquely sorted")
    for fixture_id in EXPECTED_FIXTURE_IDS:
        fixture_entries = [
            entry
            for entry in normalized_entries
            if entry["fixture_id"] == fixture_id
        ]
        if len(fixture_entries) != 5:
            raise ValueError("neutral MCWF X/Z fixture registry count drifted")
        if sum(entry["view"] == "marginal" for entry in fixture_entries) != 2:
            raise ValueError("neutral MCWF X/Z directed marginal count drifted")
        kinds = [entry["comparison_kind"] for entry in fixture_entries]
        if (
            kinds.count("one_sample_project_dense") != 3
            or kinds.count("one_sample_qutip_dense") != 1
            or kinds.count("two_sample_qutip_project") != 1
        ):
            raise ValueError("neutral MCWF X/Z fixture comparison family drifted")
    return {
        "schema": REGISTRY_SCHEMA,
        "comparison_family_alpha": alpha,
        "entries": normalized_entries,
        "sha256": observed_sha256,
        "entry_count": len(normalized_entries),
        "per_entry_alpha": alpha / len(normalized_entries),
    }


def comparison_entries_for_fixture(
    registry: Mapping[str, Any], fixture_id: str
) -> tuple[dict[str, Any], ...]:
    """Return the five frozen registry entries for one fixture."""

    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise ValueError("comparison registry entries are unavailable")
    selected = tuple(entry for entry in entries if entry.get("fixture_id") == fixture_id)
    if len(selected) != 5:
        raise ValueError("comparison registry fixture entry count drifted")
    return selected


def fixture_sha256(path: Path) -> str:
    """Return the byte-level SHA-256 of one neutral fixture file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rates_by_target(fixture: Mapping[str, Any]) -> dict[int, dict[str, float]]:
    rates = {
        0: {"down": 0.0, "up": 0.0, "dephasing": 0.0},
        1: {"down": 0.0, "up": 0.0, "dephasing": 0.0},
    }
    terms = fixture.get("collapse_terms")
    if not isinstance(terms, Sequence) or isinstance(terms, (str, bytes)):
        raise ValueError("collapse_terms must be a sequence")
    family_key = {
        "sigma_minus": "down",
        "sigma_plus": "up",
        "number_dephasing": "dephasing",
    }
    for term in terms:
        if not isinstance(term, Mapping):
            raise ValueError("collapse term must be a mapping")
        target = term.get("target")
        family = term.get("family")
        if target not in rates or family not in family_key:
            raise ValueError("collapse term family/target is unsupported")
        key = family_key[family]
        rates[target][key] += _positive_finite(
            term.get("generator_rate_per_ns"), "generator_rate_per_ns"
        )
    return rates


def analytic_binary_distribution(
    fixture: Mapping[str, Any],
) -> dict[tuple[int, int, int, int], float]:
    """Return the hand-derived continuous Lindblad law for one frozen fixture."""

    rates = _rates_by_target(fixture)
    segments = fixture.get("evolution_segments_ns")
    if not isinstance(segments, Sequence) or isinstance(segments, (str, bytes)):
        raise ValueError("evolution_segments_ns must be a sequence")
    if len(segments) != 2:
        raise ValueError("analytic law requires two evolution segments")
    first_duration = _positive_finite(segments[0], "first evolution segment")
    second_duration = _positive_finite(segments[1], "second evolution segment")

    def population_one(target: int, initial_one: float, duration: float) -> float:
        down = rates[target]["down"]
        up = rates[target]["up"]
        total = down + up
        if total == 0.0:
            return initial_one
        equilibrium = up / total
        return equilibrium + (initial_one - equilibrium) * math.exp(-total * duration)

    p_x_before_zero = 0.5
    p_z_before_one = population_one(1, 1.0, first_duration)
    coherence_rate = (
        0.5 * (rates[0]["down"] + rates[0]["up"])
        + 0.5 * rates[0]["dephasing"]
    )
    p_x_after_zero = 0.5 * (1.0 + math.exp(-coherence_rate * second_duration))
    p_z_after_one = population_one(1, 0.0, second_duration)
    law: dict[tuple[int, int, int, int], float] = {}
    for x_before in (0, 1):
        p_x_before = p_x_before_zero if x_before == 0 else 1.0 - p_x_before_zero
        for z_before in (0, 1):
            p_z_before = p_z_before_one if z_before == 1 else 1.0 - p_z_before_one
            for x_after in (0, 1):
                p_x_after = p_x_after_zero if x_after == 0 else 1.0 - p_x_after_zero
                for z_after in (0, 1):
                    p_z_after = (
                        p_z_after_one if z_after == 1 else 1.0 - p_z_after_one
                    )
                    law[(x_before, z_before, x_after, z_after)] = (
                        p_x_before * p_z_before * p_x_after * p_z_after
                    )
    return _normalized_distribution(law, "analytic")


def finite_step_binary_distribution(
    fixture: Mapping[str, Any],
    microstep_count: int,
    *,
    no_jump_linear_factor: float = 0.5,
    divide_duration_by_microsteps: bool = True,
) -> dict[tuple[int, int, int, int], float]:
    """Return the normalized finite-step candidate law for the frozen T1 fixture.

    This is an independent scalar recurrence, not a call into the project MCWF
    implementation.  The two keyword controls deliberately expose the
    load-bearing no-jump coefficient and duration subdivision so the evidence
    packet can demonstrate power against those corruptions.
    """

    if fixture.get("fixture_id") != "two_qubit_t1_ordered_xz_reset":
        raise ValueError("finite-step scalar recurrence is registered only for F1")
    count = _positive_integer(microstep_count, "microstep_count")
    factor = _positive_finite(no_jump_linear_factor, "no_jump_linear_factor")
    if type(divide_duration_by_microsteps) is not bool:
        raise TypeError("divide_duration_by_microsteps must be bool")
    gamma = _positive_finite(fixture.get("gamma_1_per_ns"), "gamma_1_per_ns")
    duration = _positive_finite(
        fixture.get("evolution_duration_ns"), "evolution_duration_ns"
    )
    dt_micro = duration / float(count) if divide_duration_by_microsteps else duration
    jump_weight = gamma * dt_micro
    no_jump_excited_amplitude = 1.0 - factor * jump_weight
    if not math.isfinite(no_jump_excited_amplitude):
        raise ValueError("finite-step no-jump amplitude must be finite")
    amplitude_squared = no_jump_excited_amplitude**2
    normalization = amplitude_squared + jump_weight
    if not math.isfinite(normalization) or normalization <= 0.0:
        raise ValueError("finite-step candidate normalization must be positive")

    z_survival = (amplitude_squared / normalization) ** count
    no_jump_path_weight = 1.0
    for step in range(count):
        prior_excited_weight = no_jump_excited_amplitude ** (2 * step)
        numerator = 1.0 + no_jump_excited_amplitude ** (2 * step + 2)
        denominator = 1.0 + normalization * prior_excited_weight
        if not math.isfinite(denominator) or denominator <= 0.0:
            raise ValueError("finite-step path normalization must be positive")
        no_jump_path_weight *= numerator / denominator
    coherence_denominator = 1.0 + no_jump_excited_amplitude ** (2 * count)
    x_coherence = (
        no_jump_path_weight
        * 2.0
        * no_jump_excited_amplitude**count
        / coherence_denominator
    )
    p_x_after_zero = 0.5 * (1.0 + x_coherence)

    law: dict[tuple[int, int, int, int], float] = {}
    for x_before in (0, 1):
        for z_before in (0, 1):
            p_z_before = z_survival if z_before == 1 else 1.0 - z_survival
            for x_after in (0, 1):
                p_x_after = (
                    p_x_after_zero if x_after == 0 else 1.0 - p_x_after_zero
                )
                law[(x_before, z_before, x_after, 0)] = (
                    0.5 * p_z_before * p_x_after
                )
    return _normalized_distribution(law, "finite_step")


def finite_step_convergence_evidence(
    fixture: Mapping[str, Any],
) -> dict[str, Any]:
    """Build deterministic convergence and corruption evidence for the fixture."""

    tolerance = _positive_finite(fixture.get("numerical_zero"), "numerical_zero")
    continuous = analytic_binary_distribution(fixture)

    def tvs(
        candidate: Mapping[Sequence[int], float],
        reference: Mapping[Sequence[int], float],
    ) -> dict[str, float]:
        return {
            "joint": total_variation(candidate, reference),
            "z_before": total_variation(
                binary_column_marginal(candidate, column=1),
                binary_column_marginal(reference, column=1),
            ),
            "x_after": total_variation(
                binary_column_marginal(candidate, column=2),
                binary_column_marginal(reference, column=2),
            ),
        }

    grid: list[dict[str, Any]] = []
    observed_by_count: dict[int, dict[str, float]] = {}
    laws_by_count: dict[int, dict[tuple[int, int, int, int], float]] = {}
    for count in FINITE_STEP_MICROSTEP_COUNTS:
        law = finite_step_binary_distribution(fixture, count)
        laws_by_count[count] = law
        observed = tvs(law, continuous)
        observed_by_count[count] = observed
        expected_joint_z, expected_x = FINITE_STEP_EXPECTED_TVS[count]
        expected = {
            "joint": expected_joint_z,
            "z_before": expected_joint_z,
            "x_after": expected_x,
        }
        expected_match = all(
            abs(observed[name] - expected[name]) <= tolerance for name in expected
        )
        grid.append(
            {
                "microstep_count": count,
                "observed_tv": observed,
                "expected_tv": expected,
                "absolute_tolerance": tolerance,
                "expected_match": expected_match,
                "post_z_structural_zero": all(
                    row[3] == 0 or mass == 0.0 for row, mass in law.items()
                ),
            }
        )

    ratio_checks: list[dict[str, Any]] = []
    for coarse, fine in zip(
        FINITE_STEP_MICROSTEP_COUNTS[:-1],
        FINITE_STEP_MICROSTEP_COUNTS[1:],
        strict=True,
    ):
        ratios = {
            name: observed_by_count[coarse][name] / observed_by_count[fine][name]
            for name in ("joint", "z_before", "x_after")
        }
        ratio_checks.append(
            {
                "coarse_microstep_count": coarse,
                "fine_microstep_count": fine,
                "observed_ratios": ratios,
                "required_band": list(FINITE_STEP_RATIO_BAND),
                "strictly_decreasing": all(
                    observed_by_count[fine][name] < observed_by_count[coarse][name]
                    for name in ratios
                ),
                "passed": all(
                    FINITE_STEP_RATIO_BAND[0]
                    <= ratio
                    <= FINITE_STEP_RATIO_BAND[1]
                    for ratio in ratios.values()
                ),
            }
        )

    final_observed = observed_by_count[FINITE_STEP_MICROSTEP_COUNTS[-1]]
    caps = {
        "joint": FINITE_STEP_FINAL_JOINT_Z_TV_CAP,
        "z_before": FINITE_STEP_FINAL_JOINT_Z_TV_CAP,
        "x_after": FINITE_STEP_FINAL_X_TV_CAP,
    }
    final_grid_gate = {
        "microstep_count": FINITE_STEP_MICROSTEP_COUNTS[-1],
        "observed_tv": final_observed,
        "caps": caps,
        "passed": all(final_observed[name] <= caps[name] for name in caps),
    }

    sample_count = _positive_integer(fixture.get("trajectory_count"), "trajectory_count")
    comparison_alpha = _positive_finite(
        fixture.get("comparison_alpha"), "comparison_alpha"
    )
    alpha_each = comparison_alpha / 3.0
    joint_radius = multinomial_tv_radius(
        sample_count=sample_count,
        alphabet_size=16,
        alpha=alpha_each,
    )
    marginal_radius = multinomial_tv_radius(
        sample_count=sample_count,
        alphabet_size=2,
        alpha=alpha_each,
    )
    public_m40_sample_gate_policy = {
        "microstep_count": 40,
        "sample_count": sample_count,
        "bonferroni_comparison_count": 3,
        "per_comparison_alpha": alpha_each,
        "joint_tv_radius": joint_radius,
        "marginal_tv_radius": marginal_radius,
        "expected_joint_tv_radius": FINITE_STEP_EXPECTED_JOINT_RADIUS,
        "expected_marginal_tv_radius": FINITE_STEP_EXPECTED_MARGINAL_RADIUS,
        "passed": bool(
            int(fixture.get("microstep_count")) == 40
            and sample_count == 2048
            and abs(joint_radius - FINITE_STEP_EXPECTED_JOINT_RADIUS) <= tolerance
            and abs(marginal_radius - FINITE_STEP_EXPECTED_MARGINAL_RADIUS)
            <= tolerance
        ),
    }

    correct_40 = laws_by_count[40]
    doubled_no_jump_40 = finite_step_binary_distribution(
        fixture,
        40,
        no_jump_linear_factor=1.0,
    )
    nojump_observed = {
        "joint": total_variation(doubled_no_jump_40, correct_40),
        "x_after": total_variation(
            binary_column_marginal(doubled_no_jump_40, column=2),
            binary_column_marginal(correct_40, column=2),
        ),
    }
    nojump_expected = {
        "joint": 0.08111612211053276,
        "x_after": 0.08111612211053276,
    }
    nojump_80_continuous = total_variation(
        finite_step_binary_distribution(
            fixture,
            80,
            no_jump_linear_factor=1.0,
        ),
        continuous,
    )
    nojump_detected = bool(
        all(
            abs(nojump_observed[name] - nojump_expected[name]) <= tolerance
            for name in nojump_expected
        )
        and abs(nojump_80_continuous - 0.08106347555070871) <= tolerance
        and nojump_observed["joint"] > joint_radius
        and nojump_observed["x_after"] > marginal_radius
    )

    wrong_dt = finite_step_binary_distribution(
        fixture,
        40,
        divide_duration_by_microsteps=False,
    )
    wrong_dt_observed = tvs(wrong_dt, correct_40)
    wrong_dt_expected = {
        "joint": 0.30909405210692065,
        "z_before": 0.24403202853509015,
        "x_after": 0.24746820619510762,
    }
    wrong_dt_detected = bool(
        all(
            abs(wrong_dt_observed[name] - wrong_dt_expected[name]) <= tolerance
            for name in wrong_dt_expected
        )
        and wrong_dt_observed["joint"] > joint_radius
        and wrong_dt_observed["z_before"] > marginal_radius
        and wrong_dt_observed["x_after"] > marginal_radius
    )
    corruption_controls = {
        "nojump_half_to_one": {
            "mutation": "no_jump_linear_factor: 0.5 -> 1.0",
            "observed_tv_vs_correct_m40": nojump_observed,
            "expected_tv_vs_correct_m40": nojump_expected,
            "m80_tv_vs_continuous": nojump_80_continuous,
            "expected_m80_tv_vs_continuous": 0.08106347555070871,
            "joint_detection_threshold": joint_radius,
            "x_after_detection_threshold": marginal_radius,
            "detected": nojump_detected,
            "required_for_overall_pass": True,
        },
        "wrong_dt": {
            "mutation": "dt_micro: duration / microstep_count -> duration",
            "observed_tv_vs_correct_m40": wrong_dt_observed,
            "expected_tv_vs_correct_m40": wrong_dt_expected,
            "joint_detection_threshold": joint_radius,
            "marginal_detection_threshold": marginal_radius,
            "detected": wrong_dt_detected,
            "required_for_overall_pass": True,
        },
    }

    passed = bool(
        all(row["expected_match"] and row["post_z_structural_zero"] for row in grid)
        and all(
            check["strictly_decreasing"] and check["passed"]
            for check in ratio_checks
        )
        and final_grid_gate["passed"]
        and public_m40_sample_gate_policy["passed"]
        and all(control["detected"] for control in corruption_controls.values())
    )
    packet: dict[str, Any] = {
        "schema": "ai_qec.external_baseline.mcwf_xz_finite_step_convergence.v1",
        "claim_boundary": (
            "frozen-fixture normalized finite-step candidate Record law only; "
            "not a linear channel, CPTP, Choi, global-order, or production claim"
        ),
        "microstep_counts": list(FINITE_STEP_MICROSTEP_COUNTS),
        "ratio_band": list(FINITE_STEP_RATIO_BAND),
        "grid": grid,
        "ratio_checks": ratio_checks,
        "final_grid_gate": final_grid_gate,
        "public_m40_sample_gate_policy": public_m40_sample_gate_policy,
        "corruption_controls": corruption_controls,
        "all_checks_passed": passed,
    }
    packet["content_hash"] = canonical_content_hash(packet)
    return packet


def finite_step_public_sample_evidence(
    fixture: Mapping[str, Any],
    sampled_distribution: Mapping[Sequence[int], float],
) -> dict[str, Any]:
    """Score one observed public Record law against the frozen m=40 recurrence."""

    tolerance = _positive_finite(fixture.get("numerical_zero"), "numerical_zero")
    microstep_count = _positive_integer(
        fixture.get("microstep_count"), "microstep_count"
    )
    sample_count = _positive_integer(fixture.get("trajectory_count"), "trajectory_count")
    alpha = _positive_finite(fixture.get("comparison_alpha"), "comparison_alpha")
    normalized_sample = _normalized_distribution(sampled_distribution, "sampled")
    reference = finite_step_binary_distribution(fixture, 40)
    observed = {
        "joint": total_variation(normalized_sample, reference),
        "z_before": total_variation(
            binary_column_marginal(normalized_sample, column=1),
            binary_column_marginal(reference, column=1),
        ),
        "x_after": total_variation(
            binary_column_marginal(normalized_sample, column=2),
            binary_column_marginal(reference, column=2),
        ),
    }
    alpha_each = alpha / 3.0
    joint_radius = multinomial_tv_radius(
        sample_count=sample_count,
        alphabet_size=16,
        alpha=alpha_each,
    )
    marginal_radius = multinomial_tv_radius(
        sample_count=sample_count,
        alphabet_size=2,
        alpha=alpha_each,
    )
    post_z_structural_zero = all(
        row[3] == 0 or mass == 0.0 for row, mass in normalized_sample.items()
    )
    radius_binding_passed = bool(
        microstep_count == 40
        and sample_count == 2048
        and abs(joint_radius - FINITE_STEP_EXPECTED_JOINT_RADIUS) <= tolerance
        and abs(marginal_radius - FINITE_STEP_EXPECTED_MARGINAL_RADIUS) <= tolerance
    )
    passed = bool(
        radius_binding_passed
        and post_z_structural_zero
        and observed["joint"] <= joint_radius
        and observed["z_before"] <= marginal_radius
        and observed["x_after"] <= marginal_radius
    )
    evidence: dict[str, Any] = {
        "schema": "ai_qec.external_baseline.mcwf_xz_public_m40_sample_gate.v1",
        "reference_microstep_count": 40,
        "observed_fixture_microstep_count": microstep_count,
        "sample_count": sample_count,
        "bonferroni_comparison_count": 3,
        "per_comparison_alpha": alpha_each,
        "observed_tv": observed,
        "joint_tv_radius": joint_radius,
        "marginal_tv_radius": marginal_radius,
        "expected_joint_tv_radius": FINITE_STEP_EXPECTED_JOINT_RADIUS,
        "expected_marginal_tv_radius": FINITE_STEP_EXPECTED_MARGINAL_RADIUS,
        "radius_and_fixture_binding_passed": radius_binding_passed,
        "post_z_structural_zero": post_z_structural_zero,
        "gate_rule": (
            "joint_tv <= joint_radius and z_before_tv <= marginal_radius and "
            "x_after_tv <= marginal_radius and post_z_structural_zero"
        ),
        "passed": passed,
    }
    evidence["content_hash"] = canonical_content_hash(evidence)
    return evidence


def total_variation(
    left: Mapping[Sequence[int], float],
    right: Mapping[Sequence[int], float],
) -> float:
    """Compute TV after normalizing two finite nonnegative laws."""

    normalized_left = _normalized_distribution(left, "left")
    normalized_right = _normalized_distribution(right, "right")
    support = set(normalized_left) | set(normalized_right)
    return 0.5 * math.fsum(
        abs(normalized_left.get(row, 0.0) - normalized_right.get(row, 0.0))
        for row in support
    )


def binary_column_marginal(
    distribution: Mapping[Sequence[int], float], *, column: int
) -> dict[tuple[int], float]:
    """Return one binary-column marginal of a finite Record law."""

    if isinstance(column, bool) or not isinstance(column, int) or column < 0:
        raise ValueError("column must be a nonnegative integer")
    normalized = _normalized_distribution(distribution, "record")
    marginal = {(0,): 0.0, (1,): 0.0}
    for row, mass in normalized.items():
        if column >= len(row):
            raise ValueError("marginal column is outside the Record width")
        value = row[column]
        if value not in (0, 1):
            raise ValueError("binary marginal requires a binary Record column")
        marginal[(value,)] += mass
    return marginal


def population_rate_x_coherence_mutation(
    fixture: Mapping[str, Any],
) -> dict[tuple[int], float]:
    """Return the X-after law for the load-bearing ``sqrt(s) -> s`` mutation."""

    gamma = _positive_finite(fixture.get("gamma_1_per_ns"), "gamma_1_per_ns")
    duration = _positive_finite(
        fixture.get("evolution_duration_ns"), "evolution_duration_ns"
    )
    survival = math.exp(-gamma * duration)
    return {
        (0,): 0.5 * (1.0 + survival),
        (1,): 0.5 * (1.0 - survival),
    }


def canonical_content_hash(payload: Mapping[str, Any]) -> str:
    """Hash one JSON payload while excluding its top-level content hash."""

    normalized = dict(payload)
    normalized.pop("content_hash", None)
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def multinomial_tv_radius(
    *, sample_count: int, alphabet_size: int, alpha: float
) -> float:
    """Weissman-style finite-sample TV radius for one multinomial law.

    The bound used is ``P(TV(phat, p) >= r) <=
    (2**k - 2) exp(-2 n r**2)`` for alphabet size ``k``.
    """

    n = _positive_integer(sample_count, "sample_count")
    k = _positive_integer(alphabet_size, "alphabet_size")
    risk = _positive_finite(alpha, "alpha")
    if risk >= 1.0:
        raise ValueError("alpha must be less than one")
    prefactor = math.pow(2.0, k) - 2.0
    if prefactor <= 0.0:
        return 0.0
    radius = math.sqrt(math.log(prefactor / risk) / (2.0 * n))
    return min(1.0, radius)


def two_sample_tv_comparison(
    left: Mapping[Sequence[int], float],
    right: Mapping[Sequence[int], float],
    *,
    left_sample_count: int,
    right_sample_count: int,
    alphabet_size: int,
    alpha: float,
) -> dict[str, Any]:
    """Apply a Bonferroni two-sample multinomial TV gate."""

    risk = _positive_finite(alpha, "alpha")
    if risk >= 1.0:
        raise ValueError("alpha must be less than one")
    left_radius = multinomial_tv_radius(
        sample_count=left_sample_count,
        alphabet_size=alphabet_size,
        alpha=risk / 2.0,
    )
    right_radius = multinomial_tv_radius(
        sample_count=right_sample_count,
        alphabet_size=alphabet_size,
        alpha=risk / 2.0,
    )
    simultaneous_radius = min(1.0, left_radius + right_radius)
    observed = total_variation(left, right)
    return {
        "schema": (
            "error_coupling_simulator.external_baseline."
            "two_sample_multinomial_tv.v1"
        ),
        "total_variation": observed,
        "left_sample_count": int(left_sample_count),
        "right_sample_count": int(right_sample_count),
        "alphabet_size": int(alphabet_size),
        "alpha": risk,
        "left_tv_radius": left_radius,
        "right_tv_radius": right_radius,
        "simultaneous_tv_radius": simultaneous_radius,
        "gate_rule": "observed_total_variation <= left_radius + right_radius",
        "passed": bool(observed <= simultaneous_radius),
    }


def one_sample_tv_comparison(
    observed: Mapping[Sequence[int], float],
    reference: Mapping[Sequence[int], float],
    *,
    sample_count: int,
    alphabet_size: int,
    alpha: float,
) -> dict[str, Any]:
    """Apply one registered empirical-to-exact multinomial TV gate."""

    risk = _positive_finite(alpha, "alpha")
    if risk >= 1.0:
        raise ValueError("alpha must be less than one")
    radius = multinomial_tv_radius(
        sample_count=sample_count,
        alphabet_size=alphabet_size,
        alpha=risk,
    )
    total = total_variation(observed, reference)
    return {
        "schema": (
            "error_coupling_simulator.external_baseline."
            "one_sample_multinomial_tv.v1"
        ),
        "total_variation": total,
        "sample_count": int(sample_count),
        "alphabet_size": int(alphabet_size),
        "alpha": risk,
        "tv_radius": radius,
        "gate_rule": "observed_total_variation <= tv_radius",
        "passed": bool(total <= radius),
    }


def flip_binary_column(
    distribution: Mapping[Sequence[int], float], *, column: int
) -> dict[tuple[int, ...], float]:
    """Deterministically corrupt one binary Record column."""

    if isinstance(column, bool) or not isinstance(column, int) or column < 0:
        raise ValueError("column must be a nonnegative integer")
    flipped: dict[tuple[int, ...], float] = {}
    for raw_row, raw_mass in distribution.items():
        row = tuple(int(value) for value in raw_row)
        if column >= len(row):
            raise ValueError("corruption column is outside the Record width")
        if any(value not in (0, 1) for value in row):
            raise ValueError("binary corruption requires binary Record rows")
        corrupted = list(row)
        corrupted[column] ^= 1
        key = tuple(corrupted)
        flipped[key] = flipped.get(key, 0.0) + float(raw_mass)
    return flipped


def _normalized_distribution(
    distribution: Mapping[Sequence[int], float], name: str
) -> dict[tuple[int, ...], float]:
    if not isinstance(distribution, Mapping) or not distribution:
        raise ValueError(f"{name} distribution must be a nonempty mapping")
    normalized: dict[tuple[int, ...], float] = {}
    width: int | None = None
    for raw_row, raw_mass in distribution.items():
        row = tuple(int(value) for value in raw_row)
        if width is None:
            width = len(row)
        if not row or len(row) != width:
            raise ValueError(f"{name} distribution has inconsistent row width")
        if isinstance(raw_mass, bool):
            raise TypeError(f"{name} distribution mass must be real, not bool")
        mass = float(raw_mass)
        if not math.isfinite(mass) or mass < 0.0:
            raise ValueError(f"{name} distribution mass must be finite and nonnegative")
        normalized[row] = normalized.get(row, 0.0) + mass
    total = math.fsum(normalized.values())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError(f"{name} distribution must have positive finite mass")
    return {row: mass / total for row, mass in normalized.items()}


def _require_exact_sequence(value: object, expected: Sequence[object], name: str) -> None:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{name} must be a JSON array")
    if tuple(value) != tuple(expected):
        raise ValueError(f"neutral MCWF X/Z {name} drifted")


def _positive_finite(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be real, not bool")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return normalized


def _zero(value: object, name: str) -> None:
    if isinstance(value, bool) or float(value) != 0.0:
        raise ValueError(f"{name} must be exactly zero")


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value
