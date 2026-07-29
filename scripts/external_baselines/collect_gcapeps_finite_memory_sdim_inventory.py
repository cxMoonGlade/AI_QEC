#!/usr/bin/env python3
"""Collect the frozen SDIM/Stim runtime inventory without importing Quimb.

The returned inventory is read-only provenance.  It attests the installed
environment and editable Quimb checkout used by the qubit-frame corroboration
lane; it is not a package lock, wheel-byte attestation, or scientific result.
Publication envelopes and sealed transport are owned by the supervisor, not
this module.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import unquote, urlparse


INVENTORY_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "sdim_inventory.v1"
)
BOOTSTRAP_YAML_SHA256 = (
    "64236e0cb6dc87a90f116dbebb8ee8a73882dc41d00619af8b7d3ccc35de3431"
)
EXPECTED_PYTHON_VERSION = "3.12.13"
EXPECTED_STIM_VERSION = "1.16.0"
EXPECTED_SDIM_VERSION = "1.3.3"
NORMALIZED_NAME_PATTERN = re.compile(r"[-_.]+")


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Encode one canonical, finite, ASCII JSON object."""

    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def projection_sha256(value: Mapping[str, Any]) -> str:
    projected = dict(value)
    projected.pop("result_projection_sha256", None)
    return canonical_sha256(projected)


def _sha256_file(path: Path) -> str:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"identity path is not a regular file: {resolved}")
    digest = hashlib.sha256()
    with resolved.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_distribution_name(name: str) -> str:
    if not isinstance(name, str) or not name:
        raise ValueError("distribution name must be a nonempty string")
    normalized = NORMALIZED_NAME_PATTERN.sub("-", name).lower()
    if not normalized:
        raise ValueError("distribution name normalizes to an empty string")
    return normalized


def _distribution_info_path(distribution: Any) -> Path:
    raw = getattr(distribution, "_path", None)
    if raw is None:
        raise RuntimeError("distribution-info path is unavailable")
    path = Path(raw).resolve(strict=True)
    if not path.is_dir():
        raise RuntimeError(f"distribution-info is not a directory: {path}")
    return path


def _distribution_record(distribution: Any) -> dict[str, Any]:
    original_name = distribution.metadata.get("Name")
    if not isinstance(original_name, str) or not original_name:
        raise RuntimeError("installed distribution has no valid Name metadata")
    version = distribution.version
    if not isinstance(version, str) or not version:
        raise RuntimeError(f"distribution {original_name!r} has no version")
    info_path = _distribution_info_path(distribution)
    direct_url_path = info_path / "direct_url.json"
    direct_url_sha256 = (
        _sha256_file(direct_url_path) if direct_url_path.is_file() else None
    )
    return {
        "original_name": original_name,
        "normalized_name": normalize_distribution_name(original_name),
        "version": version,
        "distribution_info_realpath": str(info_path),
        "direct_url_json_sha256": direct_url_sha256,
    }


def collect_distribution_records(
    distributions: Iterable[Any] | None = None,
) -> list[dict[str, Any]]:
    """Return normalized, uniquely named installed-distribution records."""

    source = (
        importlib.metadata.distributions()
        if distributions is None
        else distributions
    )
    records = [_distribution_record(distribution) for distribution in source]
    records.sort(key=lambda row: row["normalized_name"])
    names = [row["normalized_name"] for row in records]
    duplicates = sorted(
        {name for index, name in enumerate(names) if name in names[:index]}
    )
    if duplicates:
        raise RuntimeError(
            "duplicate normalized installed-distribution names: "
            + ", ".join(duplicates)
        )
    return records


def _module_origin(module_name: str) -> dict[str, str]:
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None:
        raise RuntimeError(f"{module_name} module origin is unavailable")
    origin = Path(spec.origin).resolve(strict=True)
    return {
        "module": module_name,
        "origin_realpath": str(origin),
        "origin_sha256": _sha256_file(origin),
    }


def _git_bytes(checkout: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _git_scalar(checkout: Path, *arguments: str) -> str:
    raw = _git_bytes(checkout, *arguments)
    try:
        value = raw.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise RuntimeError("Git identity is not ASCII") from exc
    if not value or "\n" in value or "\r" in value:
        raise RuntimeError("Git identity is not one scalar")
    return value


def _quimb_direct_url(
    records: Sequence[Mapping[str, Any]],
) -> tuple[Path, bool, str]:
    matches = [
        row for row in records if row["normalized_name"] == "quimb"
    ]
    if len(matches) != 1:
        raise RuntimeError("inventory must contain exactly one Quimb distribution")
    info = Path(matches[0]["distribution_info_realpath"])
    direct_url_path = (info / "direct_url.json").resolve(strict=True)
    raw = direct_url_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != matches[0][
        "direct_url_json_sha256"
    ]:
        raise RuntimeError("Quimb direct_url.json changed during collection")
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Quimb direct_url.json is invalid") from exc
    if not isinstance(value, Mapping):
        raise RuntimeError("Quimb direct_url.json must contain an object")
    parsed = urlparse(value.get("url", ""))
    if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
        raise RuntimeError("Quimb direct URL is not a local file checkout")
    checkout = Path(unquote(parsed.path)).resolve(strict=True)
    directory_info = value.get("dir_info")
    editable = bool(
        isinstance(directory_info, Mapping)
        and directory_info.get("editable") is True
    )
    return checkout, editable, hashlib.sha256(raw).hexdigest()


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def collect_inventory_state(
    *,
    environment_yaml: Path | None = None,
    quimb_checkout: Path | None = None,
    distributions: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Collect the complete preregistered installed state.

    This function never imports Quimb, GCAPEPS, Stim, or SDIM.  Module origins
    are found through import metadata only.
    """

    repo_root = Path(__file__).resolve(strict=True).parents[2]
    yaml_path = (
        repo_root
        / "external"
        / "forks"
        / "quimb-gcapeps"
        / "environment-gcapeps-sdim.yml"
        if environment_yaml is None
        else Path(environment_yaml)
    ).resolve(strict=True)
    yaml_sha256 = _sha256_file(yaml_path)
    if yaml_sha256 != BOOTSTRAP_YAML_SHA256:
        raise RuntimeError("SDIM bootstrap YAML hash drifted")

    records = collect_distribution_records(distributions)
    versions = {
        row["normalized_name"]: row["version"] for row in records
    }
    for name, expected in (
        ("stim", EXPECTED_STIM_VERSION),
        ("sdim", EXPECTED_SDIM_VERSION),
    ):
        if versions.get(name) != expected:
            raise RuntimeError(
                f"{name} version drifted: expected {expected}, "
                f"got {versions.get(name)!r}"
            )

    direct_checkout, editable, direct_url_sha256 = _quimb_direct_url(records)
    checkout = (
        direct_checkout
        if quimb_checkout is None
        else Path(quimb_checkout).resolve(strict=True)
    )
    if checkout != direct_checkout or not editable:
        raise RuntimeError("installed Quimb is not editable from the bound checkout")
    if not checkout.is_dir():
        raise RuntimeError("editable Quimb checkout is not a directory")

    origins = {
        name: _module_origin(name) for name in ("stim", "sdim", "quimb")
    }
    quimb_origin = Path(origins["quimb"]["origin_realpath"])
    if not _is_within(quimb_origin, checkout):
        raise RuntimeError("Quimb import origin is outside its editable checkout")

    status_bytes = _git_bytes(
        checkout,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    python_executable = Path(sys.executable).resolve(strict=True)
    state = {
        "bootstrap_environment": {
            "yaml_realpath": str(yaml_path),
            "yaml_sha256": yaml_sha256,
            "bootstrap_only": True,
            "transitive_lock_attested": False,
            "wheel_bytes_attested": False,
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable_realpath": str(python_executable),
            "executable_sha256": _sha256_file(python_executable),
        },
        "installed_distributions": {
            "record_count": len(records),
            "records": records,
        },
        "module_origins": origins,
        "editable_quimb": {
            "checkout_realpath": str(checkout),
            "direct_url_json_sha256": direct_url_sha256,
            "direct_url_editable": editable,
            "origin_within_checkout": True,
            "commit": _git_scalar(
                checkout, "rev-parse", "--verify", "HEAD^{commit}"
            ),
            "tree": _git_scalar(
                checkout, "rev-parse", "--verify", "HEAD^{tree}"
            ),
            "clean": status_bytes == b"",
            "status_porcelain_v1_z_sha256": hashlib.sha256(
                status_bytes
            ).hexdigest(),
        },
    }
    if state["python"]["version"] != EXPECTED_PYTHON_VERSION:
        raise RuntimeError(
            "Python version drifted: expected "
            f"{EXPECTED_PYTHON_VERSION}, got {state['python']['version']}"
        )
    return state


def validate_inventory_state(state: Mapping[str, Any]) -> None:
    if not isinstance(state, Mapping):
        raise TypeError("inventory_state must be a mapping")
    expected = {
        "bootstrap_environment",
        "python",
        "installed_distributions",
        "module_origins",
        "editable_quimb",
    }
    if set(state) != expected:
        raise ValueError("inventory_state top-level key set drifted")
    records_block = state["installed_distributions"]
    if not isinstance(records_block, Mapping) or set(records_block) != {
        "record_count",
        "records",
    }:
        raise ValueError("installed_distributions key set drifted")
    records = records_block["records"]
    if not isinstance(records, list) or records_block["record_count"] != len(
        records
    ):
        raise ValueError("installed distribution count drifted")
    names: list[str] = []
    for row in records:
        if not isinstance(row, Mapping) or set(row) != {
            "original_name",
            "normalized_name",
            "version",
            "distribution_info_realpath",
            "direct_url_json_sha256",
        }:
            raise ValueError("installed distribution row key set drifted")
        if row["normalized_name"] != normalize_distribution_name(
            row["original_name"]
        ) or not isinstance(row["version"], str) or not row["version"]:
            raise ValueError("installed distribution name or version drifted")
        info_path = row["distribution_info_realpath"]
        if (
            not isinstance(info_path, str)
            or not Path(info_path).is_absolute()
            or (
                row["direct_url_json_sha256"] is not None
                and not _is_lower_hex(row["direct_url_json_sha256"], 64)
            )
        ):
            raise ValueError("installed distribution provenance drifted")
        names.append(row["normalized_name"])
    if names != sorted(names) or len(names) != len(set(names)):
        raise ValueError("installed distributions are unsorted or duplicated")
    versions = {row["normalized_name"]: row["version"] for row in records}
    if (
        versions.get("stim") != EXPECTED_STIM_VERSION
        or versions.get("sdim") != EXPECTED_SDIM_VERSION
        or "quimb" not in versions
    ):
        raise ValueError("required installed distribution version drifted")
    origins = state["module_origins"]
    if not isinstance(origins, Mapping) or set(origins) != {
        "stim",
        "sdim",
        "quimb",
    }:
        raise ValueError("module origin key set drifted")
    for module_name in ("stim", "sdim", "quimb"):
        origin = origins[module_name]
        if (
            not isinstance(origin, Mapping)
            or set(origin) != {"module", "origin_realpath", "origin_sha256"}
            or origin["module"] != module_name
            or not isinstance(origin["origin_realpath"], str)
            or not Path(origin["origin_realpath"]).is_absolute()
            or not _is_lower_hex(origin["origin_sha256"], 64)
        ):
            raise ValueError(f"{module_name} origin row drifted")
    bootstrap = state["bootstrap_environment"]
    if not isinstance(bootstrap, Mapping) or set(bootstrap) != {
        "yaml_realpath",
        "yaml_sha256",
        "bootstrap_only",
        "transitive_lock_attested",
        "wheel_bytes_attested",
    }:
        raise ValueError("bootstrap environment key set drifted")
    if (
        bootstrap["yaml_sha256"] != BOOTSTRAP_YAML_SHA256
        or not isinstance(bootstrap["yaml_realpath"], str)
        or not Path(bootstrap["yaml_realpath"]).is_absolute()
        or bootstrap["bootstrap_only"] is not True
        or bootstrap["transitive_lock_attested"] is not False
        or bootstrap["wheel_bytes_attested"] is not False
    ):
        raise ValueError("bootstrap YAML identity drifted")
    python = state["python"]
    if not isinstance(python, Mapping) or set(python) != {
        "implementation",
        "version",
        "executable_realpath",
        "executable_sha256",
    }:
        raise ValueError("Python identity key set drifted")
    if (
        python["version"] != EXPECTED_PYTHON_VERSION
        or not isinstance(python["implementation"], str)
        or not isinstance(python["executable_realpath"], str)
        or not Path(python["executable_realpath"]).is_absolute()
        or not _is_lower_hex(python["executable_sha256"], 64)
    ):
        raise ValueError("Python version identity drifted")
    editable = state["editable_quimb"]
    if not isinstance(editable, Mapping) or set(editable) != {
        "checkout_realpath",
        "direct_url_json_sha256",
        "direct_url_editable",
        "origin_within_checkout",
        "commit",
        "tree",
        "clean",
        "status_porcelain_v1_z_sha256",
    }:
        raise ValueError("editable Quimb key set drifted")
    if (
        not isinstance(editable["checkout_realpath"], str)
        or not Path(editable["checkout_realpath"]).is_absolute()
        or not _is_lower_hex(editable["direct_url_json_sha256"], 64)
        or editable["direct_url_editable"] is not True
        or editable["origin_within_checkout"] is not True
        or not _is_lower_hex(editable["commit"], 40)
        or not _is_lower_hex(editable["tree"], 40)
        or not isinstance(editable["clean"], bool)
        or not _is_lower_hex(editable["status_porcelain_v1_z_sha256"], 64)
    ):
        raise ValueError("editable Quimb value drifted")


def build_inventory_core(
    inventory_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the role-specific core without any envelope/self-file binding."""

    validate_inventory_state(inventory_state)
    core: dict[str, Any] = {
        "schema": INVENTORY_SCHEMA,
        "role": "sdim_runtime_inventory",
        "scope": {
            "bootstrap_only": True,
            "scientific_result": False,
            "timing_ratio_member": False,
            "imports_quimb": False,
            "imports_gcapeps": False,
        },
        "inventory_state": dict(inventory_state),
        "inventory_state_sha256": canonical_sha256(inventory_state),
        "result_projection_sha256": "",
    }
    core["result_projection_sha256"] = projection_sha256(core)
    validate_inventory_core(core)
    return core


def validate_inventory_core(core: Mapping[str, Any]) -> None:
    if not isinstance(core, Mapping) or set(core) != {
        "schema",
        "role",
        "scope",
        "inventory_state",
        "inventory_state_sha256",
        "result_projection_sha256",
    }:
        raise ValueError("inventory core key set drifted")
    if core["schema"] != INVENTORY_SCHEMA or core["role"] != "sdim_runtime_inventory":
        raise ValueError("inventory core identity drifted")
    validate_inventory_state(core["inventory_state"])
    if core["inventory_state_sha256"] != canonical_sha256(
        core["inventory_state"]
    ):
        raise ValueError("inventory_state_sha256 mismatch")
    if core["result_projection_sha256"] != projection_sha256(core):
        raise ValueError("inventory result_projection_sha256 mismatch")
    if core["scope"] != {
        "bootstrap_only": True,
        "scientific_result": False,
        "timing_ratio_member": False,
        "imports_quimb": False,
        "imports_gcapeps": False,
    }:
        raise ValueError("inventory scope drifted")


def _load_timing_module() -> Any:
    path = Path(__file__).resolve(strict=True).with_name(
        "gcapeps_finite_memory_timing.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_gcapeps_fm_sdim_inventory_timing", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("finite-memory timing helper is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_inventory_worker() -> dict[str, Any]:
    """Collect, encode, and frame one ordinary inventory worker result."""

    timing = _load_timing_module()
    timer = timing.LayeredTimer()
    with timer.span(
        "sdim_inventory.root",
        scope="sdim_inventory_worker_total",
        kind="worker",
    ):
        with timer.span(
            "sdim_inventory.collect",
            scope="sdim_inventory_collection",
            kind="installed_state",
        ):
            state = collect_inventory_state()
        with timer.span(
            "sdim_inventory.serialize",
            scope="serialization",
            kind="canonical_core_encoding",
        ):
            core = build_inventory_core(state)
            core_bytes = timing.canonical_json_bytes(core)
    timing_payload = timer.finish()
    trailer_bytes = timing.build_late_telemetry_trailer(
        core_bytes, timing_payload
    )
    return {
        "core": core,
        "core_bytes": core_bytes,
        "timing": timing_payload,
        "trailer_bytes": trailer_bytes,
        "framed_bytes": timing.encode_two_frames(core_bytes, trailer_bytes),
    }


def _is_lower_hex(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Emit exactly the standard two frames; the supervisor owns publication."""

    if argv not in (None, []) and len(argv) != 0:
        raise ValueError("the inventory collector accepts no arguments")
    result = run_inventory_worker()
    sys.stdout.buffer.write(result["framed_bytes"])
    sys.stdout.buffer.flush()
    os.fsync(sys.stdout.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
