#!/usr/bin/env python3
"""Explicit logical-memory accounting for the finite-memory benchmark.

This module measures only the ownership categories frozen by the
preregistration.  Callers must enumerate every live NumPy array and every
canonical frame/ledger payload at an ownership transition.  Python object
overhead, allocator caches, and transient library workspaces are deliberately
outside this logical count and remain visible only to process/cgroup telemetry.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable

import numpy as np


SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "logical_memory.v1"
)
_ARRAY_CATEGORIES = (
    "carrier_tensor_bytes",
    "gauge_spectrum_bytes",
    "evidence_auxiliary_array_bytes",
)


def canonical_json_bytes(value: Any) -> bytes:
    """Encode a logical payload with the experiment's canonical JSON rules."""

    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def root_array(array: np.ndarray) -> np.ndarray:
    """Return the unique owning NumPy root, rejecting impossible base cycles."""

    if not isinstance(array, np.ndarray):
        raise TypeError("logical-memory arrays must be NumPy arrays")
    root = array
    seen: set[int] = set()
    while isinstance(root.base, np.ndarray):
        if id(root) in seen:
            raise ValueError("NumPy base cycle")
        seen.add(id(root))
        root = root.base
    return root


def _payload_bytes(payloads: Iterable[Any]) -> int:
    return sum(len(canonical_json_bytes(payload)) for payload in payloads)


@dataclass(frozen=True)
class LogicalMemorySample:
    """One synchronous logical-ownership sample."""

    label: str
    tensor_role: str
    carrier_tensor_bytes: int
    gauge_spectrum_bytes: int
    frame_bytes: int
    ledger_bytes: int
    evidence_auxiliary_array_bytes: int
    evidence_auxiliary_ledger_bytes: int

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("logical-memory sample label must be nonempty")
        if self.tensor_role not in {"plain_physical", "gc_residual", "none"}:
            raise ValueError("unknown logical-memory tensor role")
        for field in (
            "carrier_tensor_bytes",
            "gauge_spectrum_bytes",
            "frame_bytes",
            "ledger_bytes",
            "evidence_auxiliary_array_bytes",
            "evidence_auxiliary_ledger_bytes",
        ):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field} must be an integer")
            if value < 0:
                raise ValueError(f"{field} must be nonnegative")
        if self.tensor_role == "none" and (
            self.carrier_tensor_bytes
            or self.gauge_spectrum_bytes
            or self.frame_bytes
            or self.ledger_bytes
        ):
            raise ValueError("tensor_role=none requires zero base categories")
        if self.tensor_role == "plain_physical" and self.frame_bytes != 0:
            raise ValueError("plain logical memory must have frame_bytes=0")

    @property
    def total_owned_logical_bytes(self) -> int:
        return (
            self.carrier_tensor_bytes
            + self.gauge_spectrum_bytes
            + self.frame_bytes
            + self.ledger_bytes
        )

    @property
    def evidence_owned_logical_bytes(self) -> int:
        return (
            self.total_owned_logical_bytes
            + self.evidence_auxiliary_array_bytes
            + self.evidence_auxiliary_ledger_bytes
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "tensor_role": self.tensor_role,
            "carrier_tensor_bytes": self.carrier_tensor_bytes,
            "gauge_spectrum_bytes": self.gauge_spectrum_bytes,
            "frame_bytes": self.frame_bytes,
            "ledger_bytes": self.ledger_bytes,
            "total_owned_logical_bytes": self.total_owned_logical_bytes,
            "evidence_auxiliary_array_bytes": (
                self.evidence_auxiliary_array_bytes
            ),
            "evidence_auxiliary_ledger_bytes": (
                self.evidence_auxiliary_ledger_bytes
            ),
            "evidence_owned_logical_bytes": (
                self.evidence_owned_logical_bytes
            ),
        }


def measure_logical_memory(
    *,
    label: str,
    tensor_role: str,
    carrier_arrays: Iterable[np.ndarray] = (),
    gauge_arrays: Iterable[np.ndarray] = (),
    frame_payloads: Iterable[Any] = (),
    ledger_payloads: Iterable[Any] = (),
    evidence_auxiliary_arrays: Iterable[np.ndarray] = (),
    evidence_auxiliary_ledger_payloads: Iterable[Any] = (),
) -> LogicalMemorySample:
    """Measure explicitly enumerated live ownership categories.

    NumPy roots are deduplicated inside a category.  A root present in more
    than one category is rejected rather than silently attributed twice.
    """

    arrays_by_category = {
        "carrier_tensor_bytes": tuple(carrier_arrays),
        "gauge_spectrum_bytes": tuple(gauge_arrays),
        "evidence_auxiliary_array_bytes": tuple(
            evidence_auxiliary_arrays
        ),
    }
    root_category: dict[int, str] = {}
    root_sizes: dict[int, int] = {}
    totals = {category: 0 for category in _ARRAY_CATEGORIES}
    for category in _ARRAY_CATEGORIES:
        for array in arrays_by_category[category]:
            root = root_array(array)
            key = id(root)
            previous = root_category.get(key)
            if previous is not None and previous != category:
                raise ValueError(
                    "logical-memory NumPy root aliases categories "
                    f"{previous!r} and {category!r}"
                )
            root_category[key] = category
            root_sizes[key] = int(root.nbytes)
        totals[category] = sum(
            root_sizes[key]
            for key, owner in root_category.items()
            if owner == category
        )
    return LogicalMemorySample(
        label=label,
        tensor_role=tensor_role,
        carrier_tensor_bytes=totals["carrier_tensor_bytes"],
        gauge_spectrum_bytes=totals["gauge_spectrum_bytes"],
        frame_bytes=_payload_bytes(frame_payloads),
        ledger_bytes=_payload_bytes(ledger_payloads),
        evidence_auxiliary_array_bytes=totals[
            "evidence_auxiliary_array_bytes"
        ],
        evidence_auxiliary_ledger_bytes=_payload_bytes(
            evidence_auxiliary_ledger_payloads
        ),
    )


class LogicalMemoryTracker:
    """Track the frozen committed, algorithm, and evidence logical peaks."""

    def __init__(self, *, tensor_role: str, evidence: bool) -> None:
        if tensor_role not in {"plain_physical", "gc_residual"}:
            raise ValueError("tracker requires a candidate tensor role")
        if not isinstance(evidence, bool):
            raise TypeError("evidence must be a bool")
        self.tensor_role = tensor_role
        self.evidence = evidence
        self._final_committed: LogicalMemorySample | None = None
        self._max_committed: LogicalMemorySample | None = None
        self._max_algorithm: LogicalMemorySample | None = None
        self._max_evidence: LogicalMemorySample | None = None
        self._sample_count = 0

    @staticmethod
    def _larger(
        current: LogicalMemorySample | None,
        candidate: LogicalMemorySample,
        *,
        evidence_total: bool,
    ) -> LogicalMemorySample:
        if current is None:
            return candidate
        key = (
            "evidence_owned_logical_bytes"
            if evidence_total
            else "total_owned_logical_bytes"
        )
        if getattr(candidate, key) > getattr(current, key):
            return candidate
        return current

    def sample_committed(
        self,
        sample: LogicalMemorySample,
        *,
        final: bool = False,
    ) -> None:
        self._require_base_sample(sample)
        if sample.evidence_auxiliary_array_bytes or (
            sample.evidence_auxiliary_ledger_bytes
        ):
            raise ValueError("committed sample contains evidence auxiliaries")
        self._sample_count += 1
        self._max_committed = self._larger(
            self._max_committed,
            sample,
            evidence_total=False,
        )
        self._max_algorithm = self._larger(
            self._max_algorithm,
            sample,
            evidence_total=False,
        )
        if final:
            self._final_committed = sample

    def sample_algorithm(self, sample: LogicalMemorySample) -> None:
        self._require_base_sample(sample)
        if sample.evidence_auxiliary_array_bytes or (
            sample.evidence_auxiliary_ledger_bytes
        ):
            raise ValueError("algorithm sample contains evidence auxiliaries")
        self._sample_count += 1
        self._max_algorithm = self._larger(
            self._max_algorithm,
            sample,
            evidence_total=False,
        )

    def sample_evidence(self, sample: LogicalMemorySample) -> None:
        if not self.evidence:
            raise ValueError("performance tracker cannot sample evidence")
        if sample.tensor_role != "none":
            raise ValueError(
                "instrumented evidence samples require zero base ownership"
            )
        self._sample_count += 1
        self._max_evidence = self._larger(
            self._max_evidence,
            sample,
            evidence_total=True,
        )

    def _require_base_sample(self, sample: LogicalMemorySample) -> None:
        if sample.tensor_role != self.tensor_role:
            raise ValueError("logical-memory sample tensor role drifted")

    def base_report(self) -> dict[str, Any]:
        if self._final_committed is None:
            raise ValueError("final committed logical-memory sample is absent")
        if self._max_committed is None or self._max_algorithm is None:
            raise ValueError("base logical-memory peaks are absent")
        return {
            "schema": SCHEMA,
            "tensor_role": self.tensor_role,
            "sample_count": self._sample_count,
            "final_committed_owned_logical_bytes": (
                self._final_committed.total_owned_logical_bytes
            ),
            "max_committed_owned_logical_bytes": (
                self._max_committed.total_owned_logical_bytes
            ),
            "max_sampled_algorithm_owned_logical_bytes": (
                self._max_algorithm.total_owned_logical_bytes
            ),
            "final_committed_sample": self._final_committed.as_dict(),
            "max_committed_sample": self._max_committed.as_dict(),
            "max_sampled_algorithm_sample": self._max_algorithm.as_dict(),
        }
    def report(self) -> dict[str, Any]:
        output = self.base_report()
        if self.evidence:
            if self._max_evidence is None:
                raise ValueError("evidence logical-memory peak is absent")
            output.update(
                {
                    "max_sampled_evidence_owned_logical_bytes": (
                        self._max_evidence.evidence_owned_logical_bytes
                    ),
                    "max_sampled_evidence_sample": (
                        self._max_evidence.as_dict()
                    ),
                }
            )
        return output
