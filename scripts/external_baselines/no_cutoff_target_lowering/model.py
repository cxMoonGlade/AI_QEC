"""Canonical data envelope shared by static target-lowering artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


STATIC_SCOPE = "STATIC_TARGET_LOWERING_ONLY"
NEUTRAL_SCHEMA = (
    "error_coupling_simulator.external.declared_error_record_program.v1"
)
PAIR_SCHEMA = (
    "error_coupling_simulator.external.exact_pair_transition_program.v1"
)
ADD_SCHEMA = (
    "error_coupling_simulator.external.dynamic_add_relation_program.v1"
)
TN_SCHEMA = (
    "error_coupling_simulator.external.retained_boundary_factor_network.v1"
)


def canonical_json_bytes(value: object) -> bytes:
    """Return the preregistered finite canonical JSON encoding."""

    return json.dumps(
        value,
        sort_keys=True,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def reject_floats(value: object, *, path: str = "artifact") -> None:
    if isinstance(value, float):
        raise TypeError(f"floating value is forbidden at {path}")
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise TypeError(f"non-string JSON key at {path}")
            reject_floats(nested, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            reject_floats(nested, path=f"{path}[{index}]")


def validate_static_envelope(
    data: object,
    *,
    schema: str,
    semantic_keys: set[str],
) -> dict[str, Any]:
    """Validate the common strict static-lowering envelope."""

    if not isinstance(data, dict):
        raise TypeError("static artifact must be a JSON object")
    reject_floats(data)
    if set(data) != {"_schema", "scope", "semantic", "semantic_sha256"}:
        raise ValueError("static artifact envelope has missing or unknown fields")
    if data["_schema"] != schema or data["scope"] != STATIC_SCOPE:
        raise ValueError("static artifact schema or scope mismatch")
    semantic = data["semantic"]
    if not isinstance(semantic, dict) or set(semantic) != semantic_keys:
        raise ValueError("static artifact semantic schema mismatch")
    if data["semantic_sha256"] != sha256_json(semantic):
        raise ValueError("static artifact semantic hash mismatch")
    return semantic


@dataclass(frozen=True, slots=True)
class StaticArtifact:
    """A small public interface around a deeply validated semantic object."""

    schema: str
    semantic: Mapping[str, Any]

    def to_data(self) -> dict[str, Any]:
        reject_floats(self.semantic, path="semantic")
        semantic = dict(self.semantic)
        return {
            "_schema": self.schema,
            "scope": STATIC_SCOPE,
            "semantic": semantic,
            "semantic_sha256": sha256_json(semantic),
        }

    @property
    def semantic_sha256(self) -> str:
        return sha256_json(dict(self.semantic))

    @property
    def sha256(self) -> str:
        return sha256_json(self.to_data())
