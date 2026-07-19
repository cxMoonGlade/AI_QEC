"""Registry-driven L2 mutation runner.

Runs mutmut via harness.proc so mutmut AND its worker pool live in one process group -> killed
ATOMICALLY (no orphaned workers -- the exact failure the .sh runner had) with a real timeout.
mutmut 3.6 config lives in setup.cfg (no run-CLI), so: back up setup.cfg -> write a per-batch
[mutmut] (newline-joined lists; comma breaks mutmut's parser) -> run -> ALWAYS restore (finally).
Serialized by an flock on the shared setup.cfg. GPU pool acquired if the registry is requires_gpu.
ECS_MUTATION_SKIP_SLOW=1 skips slow physics pins under mutation. Gate: kill_rate>=BAR.
Mutants reported by mutmut as ``no tests`` (worker exit 33) are non-killed and are reported
separately; they must never inflate the kill rate.

Usage:  python tests/harness/mutation.py <registry.json>  [--jobs N] [--timeout SEC]
"""
from __future__ import annotations

import ast
import concurrent.futures
import copy
import fcntl
import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tokenize
from importlib import metadata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tests/ on path (-> `from harness import ...`)
from harness import gpu_pool, proc  # noqa: E402

REPO = Path(__file__).resolve().parents[2]          # portable (works on spark too), not hardcoded
LOGDIR = REPO / "outputs/simulator_validation/logs"
ENVBIN = str(Path(sys.executable).parent)           # the running interpreter's bin (portable: aiqec OR spark venv)
CONFIG_PATH = REPO / "tests" / "harness_config.json"
_MUTMUT_STATUS_TO_KEY = {
    "killed": "killed",
    "survived": "survived",
    "timeout": "timeout",
    "suspicious": "suspicious",
    "no tests": "no_tests",
    "skipped": "skipped",
    "caught by type check": "caught_by_type_check",
    "check was interrupted by user": "check_was_interrupted_by_user",
    "not checked": "not_checked",
    "segfault": "segfault",
}
_MUTMUT_RESULT = re.compile(
    r"^\s*(?P<mutant>.+?):\s*(?P<status>"
    + "|".join(re.escape(status) for status in _MUTMUT_STATUS_TO_KEY)
    + r")\s*$"
)
_SEMANTIC_CATALOG_SCHEMA = (
    "error_coupling_simulator.harness.semantic_mutant_catalog.v2"
)
_SEMANTIC_CLASSIFIER_POLICY = "conservative_exception_prose_ast.v2"
_SEMANTIC_DISPOSITION_SCHEMA = (
    "error_coupling_simulator.harness.mutation_semantic_dispositions.v2"
)
_MUTATION_BATCH_RUN_SCHEMA = (
    "error_coupling_simulator.harness.mutation_batch_run.v3"
)
_MUTATION_SUITE_RUN_SCHEMA = (
    "error_coupling_simulator.harness.mutation_suite_run.v3"
)
_MUTATION_SCORE_FIELDS = frozenset(
    {"total", "killed", "status_counts", "kill_rate", "bar", "modules", "pass"}
)
_SEMANTIC_SCORE_FIELDS = _MUTATION_SCORE_FIELDS | {
    "excluded_counts",
    "excluded_by_status",
    "critical",
}
_EXCEPTION_PROSE_TYPES = {"RuntimeError", "TypeError", "ValueError"}
_MUTMUT_NUMERIC_VARIANT = re.compile(r"^.+__mutmut_[0-9]+$")
_GPU_BOUND_ENVIRONMENT_SCHEMA = (
    "error_coupling_simulator.harness.mutation_gpu_environment.v1"
)
_GPU_DEVICE_IDENTITY_SCHEMA = (
    "error_coupling_simulator.harness.mutation_gpu_device.v1"
)
_GPU_BOUND_ENVIRONMENT_KEYS = (
    "CUDA_VISIBLE_DEVICES",
    "ECS_GPU_SLOT",
    "ECS_DISABLE_NATIVE_KERNELS",
    "ECS_FORCE_UNFACTORIZED_AXIS1",
    "ECS_D3_DATA_ROOT",
    "ECS_D3_MASK",
    "ECS_MUTATION_SKIP_SLOW",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONNOUSERSITE",
    "PYTHONPATH",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
    "PYTEST_XDIST_WORKER",
    "PYTEST_XDIST_WORKER_COUNT",
    "PYTEST_XDIST_TESTRUNUID",
    "PYTORCH_CUDA_ALLOC_CONF",
    "CUDA_LAUNCH_BLOCKING",
    "CUBLAS_WORKSPACE_CONFIG",
    "CUDA_MODULE_LOADING",
    "NVIDIA_VISIBLE_DEVICES",
    "CUDA_HOME",
    "LD_LIBRARY_PATH",
    "PATH",
    "PYTHONHASHSEED",
    "LC_ALL",
    "LANG",
)
_SUITE_LOCK_CONTEXT = threading.local()


def parse_mutmut_results(results_text: str) -> dict[str, str]:
    """Parse the complete ``mutmut results --all True`` output fail closed."""

    rows: dict[str, str] = {}
    for line_number, line in enumerate(results_text.splitlines(), start=1):
        if not line.strip():
            continue
        match = _MUTMUT_RESULT.fullmatch(line)
        if match is None:
            raise ValueError(f"unknown mutmut result row at line {line_number}: {line!r}")
        mutant = match.group("mutant").strip()
        if not mutant or mutant in rows:
            raise ValueError(f"duplicate or empty mutmut result at line {line_number}: {mutant!r}")
        rows[mutant] = _MUTMUT_STATUS_TO_KEY[match.group("status")]
    if not rows:
        raise ValueError("mutmut results contained no mutant rows")
    return rows


def _module_import_name(module: str) -> str:
    path = Path(module)
    if not path.parts or path.parts[0] != "src" or path.suffix != ".py":
        raise ValueError(f"mutation module must be a Python file below src/: {module!r}")
    parts = list(path.with_suffix("").parts[1:])
    if parts and parts[-1] == "__init__":
        parts.pop()
    if not parts:
        raise ValueError(f"mutation module has no import name: {module!r}")
    return ".".join(parts)


def _normalized_function_dump(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    normalized = copy.deepcopy(function)
    normalized.name = "__mutmut_function__"
    return ast.dump(normalized, include_attributes=False)


def _ast_node_paths(
    root: ast.AST,
    target_type: type[ast.AST],
) -> tuple[tuple[tuple[str, int | None], ...], ...]:
    paths: list[tuple[tuple[str, int | None], ...]] = []

    def visit(node: ast.AST, path: tuple[tuple[str, int | None], ...]) -> None:
        if isinstance(node, target_type):
            paths.append(path)
        for field, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                visit(value, (*path, (field, None)))
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item, ast.AST):
                        visit(item, (*path, (field, index)))

    visit(root, ())
    return tuple(paths)


def _ast_node_at(
    root: ast.AST,
    path: tuple[tuple[str, int | None], ...],
) -> ast.AST:
    node: object = root
    for field, index in path:
        node = getattr(node, field)
        if index is not None:
            node = node[index]
    if not isinstance(node, ast.AST):
        raise TypeError("AST path did not resolve to a node")
    return node


def _recognized_exception_text_mutation(
    original: ast.expr,
    mutant: ast.expr,
) -> bool:
    if isinstance(mutant, ast.Constant) and mutant.value is None:
        return isinstance(original, (ast.Constant, ast.JoinedStr)) and (
            not isinstance(original, ast.Constant) or isinstance(original.value, str)
        )
    if isinstance(original, ast.JoinedStr) and isinstance(mutant, ast.JoinedStr):
        if len(original.values) != len(mutant.values):
            return False
        changed_static_segments = 0
        for original_part, mutant_part in zip(
            original.values,
            mutant.values,
            strict=True,
        ):
            if ast.dump(original_part, include_attributes=False) == ast.dump(
                mutant_part,
                include_attributes=False,
            ):
                continue
            if not (
                isinstance(original_part, ast.Constant)
                and isinstance(original_part.value, str)
                and isinstance(mutant_part, ast.Constant)
                and isinstance(mutant_part.value, str)
                and _recognized_exception_text_mutation(
                    original_part,
                    mutant_part,
                )
            ):
                return False
            changed_static_segments += 1
        return changed_static_segments == 1
    if not (
        isinstance(original, ast.Constant)
        and isinstance(original.value, str)
        and isinstance(mutant, ast.Constant)
        and isinstance(mutant.value, str)
    ):
        return False
    candidates = {
        f"XX{original.value}XX",
        original.value.lower(),
        original.value.upper(),
    }
    return mutant.value != original.value and mutant.value in candidates


def _direct_exception_text_payload(raised: ast.Raise) -> ast.expr | None:
    call = raised.exc
    if not (
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id in _EXCEPTION_PROSE_TYPES
        and len(call.args) == 1
        and not call.keywords
    ):
        return None
    return call.args[0]


def _is_exception_prose_only(
    original: ast.FunctionDef | ast.AsyncFunctionDef,
    mutant: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Prove that the sole mutation is an outer noncontractual error-text edit."""

    original_paths = _ast_node_paths(original, ast.Raise)
    if original_paths != _ast_node_paths(mutant, ast.Raise):
        return False
    matching_paths = 0
    for path in original_paths:
        original_raise = _ast_node_at(original, path)
        mutant_raise = _ast_node_at(mutant, path)
        if not isinstance(original_raise, ast.Raise) or not isinstance(
            mutant_raise, ast.Raise
        ):
            return False
        original_payload = _direct_exception_text_payload(original_raise)
        mutant_payload = _direct_exception_text_payload(mutant_raise)
        if original_payload is None or mutant_payload is None:
            continue
        if not _recognized_exception_text_mutation(original_payload, mutant_payload):
            continue

        original_copy = copy.deepcopy(original)
        mutant_copy = copy.deepcopy(mutant)
        original_copy.name = "__mutmut_function__"
        mutant_copy.name = "__mutmut_function__"
        original_copy_raise = _ast_node_at(original_copy, path)
        mutant_copy_raise = _ast_node_at(mutant_copy, path)
        if not isinstance(original_copy_raise, ast.Raise) or not isinstance(
            mutant_copy_raise, ast.Raise
        ):
            return False
        original_call = original_copy_raise.exc
        mutant_call = mutant_copy_raise.exc
        if not isinstance(original_call, ast.Call) or not isinstance(
            mutant_call, ast.Call
        ):
            return False
        sentinel = ast.Constant(value="__NONCONTRACTUAL_EXCEPTION_PROSE__")
        original_call.args[0] = copy.deepcopy(sentinel)
        mutant_call.args[0] = copy.deepcopy(sentinel)
        if ast.dump(original_copy, include_attributes=False) == ast.dump(
            mutant_copy,
            include_attributes=False,
        ):
            matching_paths += 1
    return matching_paths == 1


def _top_level_function_spans(text: str) -> dict[str, tuple[int, int]]:
    """Index top-level generated functions without parsing a potentially huge module."""

    line_offsets = [0]
    for line in text.splitlines(keepends=True):
        line_offsets.append(line_offsets[-1] + len(line))

    spans: dict[str, tuple[int, int]] = {}
    current: dict[str, object] | None = None
    pending_async_line: int | None = None
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    for token in tokens:
        if current is None:
            if token.type == tokenize.NAME and token.string == "async" and token.start[1] == 0:
                pending_async_line = token.start[0]
                continue
            if token.type == tokenize.NAME and token.string == "def" and (
                token.start[1] == 0
                or (
                    pending_async_line == token.start[0]
                    and token.start[1] > 0
                )
            ):
                current = {
                    "start_line": pending_async_line or token.start[0],
                    "name": None,
                    "depth": 0,
                    "seen_indent": False,
                }
                pending_async_line = None
                continue
            if token.type not in {tokenize.NL, tokenize.NEWLINE, tokenize.ENCODING}:
                pending_async_line = None
            continue

        if current["name"] is None and token.type == tokenize.NAME:
            current["name"] = token.string
            continue
        if token.type == tokenize.INDENT:
            current["depth"] = int(current["depth"]) + 1
            current["seen_indent"] = True
            continue
        if token.type == tokenize.DEDENT and bool(current["seen_indent"]):
            current["depth"] = int(current["depth"]) - 1
            if int(current["depth"]) == 0:
                name = current["name"]
                if not isinstance(name, str) or name in spans:
                    raise ValueError(f"duplicate or unnamed trampoline function: {name!r}")
                start_line = int(current["start_line"])
                start = line_offsets[start_line - 1]
                end = line_offsets[token.start[0] - 1] + token.start[1]
                spans[name] = (start, end)
                current = None
    if current is not None:
        raise ValueError("unterminated top-level trampoline function")
    return spans


def _parse_trampoline_function(
    text: str,
    *,
    symbol: str,
    spans: dict[str, tuple[int, int]],
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    if symbol not in spans:
        raise ValueError(f"missing trampoline function: {symbol}")
    start, end = spans[symbol]
    parsed = ast.parse(text[start:end])
    if len(parsed.body) != 1 or not isinstance(
        parsed.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        raise ValueError(f"invalid trampoline function body: {symbol}")
    function = parsed.body[0]
    if function.name != symbol:
        raise ValueError(f"trampoline function identity mismatch: {symbol}")
    return function


def build_semantic_mutant_catalog(
    rows: dict[str, str],
    *,
    modules: tuple[str, ...],
    repo: Path = REPO,
) -> dict:
    """Authenticate generated mutmut functions and classify only proven prose edits."""

    if not rows:
        raise ValueError("semantic mutant catalog requires rows")
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    try:
        mutmut_version = metadata.version("mutmut")
    except metadata.PackageNotFoundError as exc:
        raise RuntimeError("semantic mutant catalog requires installed mutmut") from exc
    module_names = {module: _module_import_name(module) for module in modules}
    classifications: dict[str, dict] = {}
    module_catalogs: dict[str, dict] = {}
    for module, import_name in module_names.items():
        module_rows = {
            mutant: status
            for mutant, status in rows.items()
            if mutant.startswith(import_name + ".")
        }
        if not module_rows:
            raise ValueError(f"semantic catalog module has no mutants: {module}")
        source_path = repo / module
        trampoline_path = repo / "mutants" / module
        if not source_path.is_file() or not trampoline_path.is_file():
            raise FileNotFoundError(
                f"missing source or trampoline for semantic catalog: {module}"
            )
        text = trampoline_path.read_text(encoding="utf-8", errors="strict")
        spans = _top_level_function_spans(text)
        expected_symbols = {mutant.rsplit(".", 1)[1] for mutant in module_rows}
        generated_symbols = {
            symbol for symbol in spans if _MUTMUT_NUMERIC_VARIANT.fullmatch(symbol)
        }
        if generated_symbols != expected_symbols:
            raise ValueError(
                "trampoline mutant inventory mismatch for "
                f"{module}: missing={sorted(expected_symbols - generated_symbols)}, "
                f"extra={sorted(generated_symbols - expected_symbols)}"
            )

        source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
        parsed_functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}

        def parsed(symbol: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
            if symbol not in parsed_functions:
                parsed_functions[symbol] = _parse_trampoline_function(
                    text,
                    symbol=symbol,
                    spans=spans,
                )
            return parsed_functions[symbol]

        digest_rows: list[tuple[str, str, str, str]] = []
        prose_mutants: list[str] = []
        for mutant in sorted(module_rows):
            symbol = mutant.rsplit(".", 1)[1]
            family, separator, ordinal = symbol.rpartition("__mutmut_")
            if not separator or not ordinal.isdigit():
                raise ValueError(f"invalid mutmut numeric symbol: {symbol}")
            original_symbol = family + "__mutmut_orig"
            original = parsed(original_symbol)
            variant = parsed(symbol)
            original_dump = _normalized_function_dump(original)
            mutant_dump = _normalized_function_dump(variant)
            original_ast_sha256 = hashlib.sha256(
                original_dump.encode("utf-8")
            ).hexdigest()
            mutant_ast_sha256 = hashlib.sha256(
                mutant_dump.encode("utf-8")
            ).hexdigest()
            diff_payload = json.dumps(
                {
                    "policy": _SEMANTIC_CLASSIFIER_POLICY,
                    "python_version": python_version,
                    "mutmut_version": mutmut_version,
                    "module": module,
                    "source_sha256": source_sha256,
                    "mutant": mutant,
                    "original_ast_sha256": original_ast_sha256,
                    "mutant_ast_sha256": mutant_ast_sha256,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            mutation_diff_sha256 = hashlib.sha256(diff_payload).hexdigest()
            prose_only = _is_exception_prose_only(original, variant)
            if prose_only:
                prose_mutants.append(mutant)
            classifications[mutant] = {
                "kind": (
                    "exception_prose_noncontractual" if prose_only else "semantic"
                ),
                "criticality": "not_applicable" if prose_only else "critical",
                "module": module,
                "source_sha256": source_sha256,
                "original_ast_sha256": original_ast_sha256,
                "mutant_ast_sha256": mutant_ast_sha256,
                "mutation_diff_sha256": mutation_diff_sha256,
            }
            digest_rows.append(
                (mutant, original_ast_sha256, mutant_ast_sha256, mutation_diff_sha256)
            )
        catalog_sha256 = hashlib.sha256(
            json.dumps(
                digest_rows,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        prose_set_sha256 = hashlib.sha256(
            json.dumps(sorted(prose_mutants), separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        module_catalogs[module] = {
            "source_sha256": source_sha256,
            "mutant_count": len(module_rows),
            "catalog_sha256": catalog_sha256,
            "exception_prose_count": len(prose_mutants),
            "exception_prose_set_sha256": prose_set_sha256,
        }

    if set(classifications) != set(rows):
        raise ValueError(
            "semantic catalog identities mismatch: "
            f"missing={sorted(set(rows) - set(classifications))}, "
            f"extra={sorted(set(classifications) - set(rows))}"
        )
    return {
        "schema": _SEMANTIC_CATALOG_SCHEMA,
        "classifier_policy": _SEMANTIC_CLASSIFIER_POLICY,
        "generator": {"name": "mutmut", "version": mutmut_version},
        "python_version": python_version,
        "modules": module_catalogs,
        "classifications": classifications,
    }


def _semantic_catalog_sha256(catalog: dict) -> str:
    """Hash the complete generated semantic catalog with canonical JSON."""

    if not isinstance(catalog, dict):
        raise TypeError("semantic mutant catalog must be an object")
    raw = json.dumps(
        catalog,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _gpu_bound_environment(env: dict[str, str]) -> dict:
    """Bind every ambient switch allowed to affect a GPU mutation child."""

    if not isinstance(env, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in env.items()
    ):
        raise TypeError("GPU mutation child environment must be a string mapping")
    values = {name: env.get(name) for name in _GPU_BOUND_ENVIRONMENT_KEYS}
    payload = {
        "schema": _GPU_BOUND_ENVIRONMENT_SCHEMA,
        "values": values,
    }
    return {
        **payload,
        "sha256": hashlib.sha256(_canonical_json_bytes(payload)).hexdigest(),
    }


def _validate_gpu_bound_environment(document: object) -> None:
    if not isinstance(document, dict) or set(document) != {
        "schema",
        "values",
        "sha256",
    }:
        raise TypeError("GPU execution policy bound environment is incomplete")
    if document["schema"] != _GPU_BOUND_ENVIRONMENT_SCHEMA:
        raise ValueError("GPU execution policy bound environment schema mismatch")
    values = document["values"]
    if not isinstance(values, dict) or set(values) != set(
        _GPU_BOUND_ENVIRONMENT_KEYS
    ):
        raise ValueError("GPU execution policy bound environment keys mismatch")
    if any(value is not None and not isinstance(value, str) for value in values.values()):
        raise TypeError("GPU execution policy bound environment values are invalid")
    payload = {"schema": document["schema"], "values": values}
    expected = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
    if document["sha256"] != expected:
        raise ValueError("GPU execution policy bound environment digest mismatch")


def _gpu_device_identity_document(
    *,
    slot: int,
    uuid: str,
    driver_version: str,
) -> dict:
    if type(slot) is not int or slot < 0:
        raise ValueError("GPU device identity slot is invalid")
    if not isinstance(uuid, str) or not uuid.strip():
        raise ValueError("GPU device identity UUID is invalid")
    if not isinstance(driver_version, str) or not driver_version.strip():
        raise ValueError("GPU device identity driver version is invalid")
    payload = {
        "schema": _GPU_DEVICE_IDENTITY_SCHEMA,
        "slot": slot,
        "uuid": uuid.strip(),
        "driver_version": driver_version.strip(),
    }
    return {
        **payload,
        "sha256": hashlib.sha256(_canonical_json_bytes(payload)).hexdigest(),
    }


def _validate_gpu_device_identity(document: object) -> None:
    if not isinstance(document, dict) or set(document) != {
        "schema",
        "slot",
        "uuid",
        "driver_version",
        "sha256",
    }:
        raise TypeError("GPU execution policy device identity is incomplete")
    expected = _gpu_device_identity_document(
        slot=document["slot"],
        uuid=document["uuid"],
        driver_version=document["driver_version"],
    )
    if document != expected:
        raise ValueError("GPU execution policy device identity digest mismatch")


def _gpu_device_identity(env: dict[str, str]) -> dict:
    slot_text = env.get("ECS_GPU_SLOT")
    visible = env.get("CUDA_VISIBLE_DEVICES")
    try:
        slot = int(slot_text) if slot_text is not None else -1
    except ValueError as exc:
        raise ValueError("GPU device identity requires an integer ECS_GPU_SLOT") from exc
    if slot < 0 or visible != str(slot):
        raise ValueError("GPU device identity lease/visibility mismatch")
    command = [
        "nvidia-smi",
        "--query-gpu=index,uuid,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15.0,
            check=False,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("GPU device identity probe failed") from exc
    if completed.returncode != 0:
        raise RuntimeError(
            "GPU device identity probe failed: " + completed.stderr.strip()
        )
    matches: list[tuple[str, str]] = []
    for raw_line in completed.stdout.splitlines():
        fields = [field.strip() for field in raw_line.split(",")]
        if len(fields) != 3:
            raise ValueError("GPU device identity probe row is malformed")
        try:
            index = int(fields[0])
        except ValueError as exc:
            raise ValueError("GPU device identity probe index is malformed") from exc
        if index == slot:
            matches.append((fields[1], fields[2]))
    if len(matches) != 1:
        raise RuntimeError(f"GPU device identity slot {slot} was not unique")
    uuid, driver_version = matches[0]
    return _gpu_device_identity_document(
        slot=slot,
        uuid=uuid,
        driver_version=driver_version,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    file_descriptor = os.open(str(directory), flags)
    try:
        os.fsync(file_descriptor)
    finally:
        os.close(file_descriptor)


def _durable_file_sha256(path: Path) -> str:
    """Flush a completed evidence file and its directory before authenticating it."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        os.fsync(handle.fileno())
        handle.seek(0)
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    _fsync_directory(path.parent)
    return digest.hexdigest()


def _mutation_runtime_fingerprint() -> dict:
    """Bind the exact Python executable and Conda/import metadata in use."""

    from harness import service_acceptance

    python = Path(sys.executable).resolve(strict=True)
    payload = {
        "schema": "error_coupling_simulator.harness.mutation_runtime.v1",
        "python_executable": {
            "path": str(python),
            "sha256": _sha256_file(python),
        },
        "environment": service_acceptance._environment_metadata_identity(
            Path(sys.prefix)
        ),
    }
    return {
        **payload,
        "sha256": hashlib.sha256(_canonical_json_bytes(payload)).hexdigest(),
    }


def _gpu_worker_log_name(tag: str, sequence_index: int, mutant: str) -> str:
    if not tag or Path(tag).name != tag or sequence_index <= 0 or not mutant:
        raise ValueError("GPU mutation worker log identity is invalid")
    mutant_digest = hashlib.sha256(mutant.encode("utf-8")).hexdigest()[:16]
    return f"{tag}_worker_{sequence_index:06d}_{mutant_digest}.log"


def score_mutation_rows(
    rows: dict[str, str],
    *,
    modules: tuple[str, ...],
    bar: float,
    classifications: dict[str, dict] | None = None,
) -> dict:
    """Score one complete batch and each declared source module."""

    _validate_mutation_gate_knobs(
        bar=bar,
        timeout_multiplier=1.0,
        timeout_constant=0.0,
    )
    if not rows:
        raise ValueError("mutmut results contained no mutant rows")
    unknown = sorted(set(rows.values()) - set(_MUTMUT_STATUS_TO_KEY.values()))
    if unknown:
        raise ValueError(f"unknown normalized mutmut statuses: {unknown}")
    incomplete = {
        status: sum(value == status for value in rows.values())
        for status in ("not_checked", "check_was_interrupted_by_user")
    }
    if any(incomplete.values()):
        raise ValueError(f"incomplete mutmut execution: {incomplete}")

    module_names = {module: _module_import_name(module) for module in modules}
    by_module: dict[str, dict[str, str]] = {module: {} for module in modules}
    for mutant, status in rows.items():
        matches = [
            module
            for module, import_name in module_names.items()
            if mutant == import_name or mutant.startswith(import_name + ".")
        ]
        if len(matches) != 1:
            raise ValueError(
                f"mutant must map to exactly one declared module: {mutant!r} -> {matches}"
            )
        by_module[matches[0]][mutant] = status

    status_counts = {
        status: sum(value == status for value in rows.values())
        for status in _MUTMUT_STATUS_TO_KEY.values()
    }
    total = len(rows)
    killed = status_counts["killed"]
    module_scores: dict[str, dict] = {}
    for module, module_rows in by_module.items():
        module_total = len(module_rows)
        module_killed = sum(value == "killed" for value in module_rows.values())
        rate = module_killed / module_total if module_total else 0.0
        module_scores[module] = {
            "total": module_total,
            "killed": module_killed,
            "kill_rate": round(rate, 4),
            "bar": bar,
            "pass": module_total > 0 and rate >= bar,
        }
    rate = killed / total
    raw = {
        "total": total,
        "killed": killed,
        "status_counts": status_counts,
        "kill_rate": round(rate, 4),
        "bar": bar,
        "modules": module_scores,
        "pass": rate >= bar and all(score["pass"] for score in module_scores.values()),
    }
    if classifications is None:
        return raw
    if set(classifications) != set(rows):
        raise ValueError(
            "semantic classification identities mismatch: "
            f"missing={sorted(set(rows) - set(classifications))}, "
            f"extra={sorted(set(classifications) - set(rows))}"
        )

    allowed = {
        ("exception_prose_noncontractual", "not_applicable"),
        ("semantic", "critical"),
    }
    excluded_kinds = {"exception_prose_noncontractual"}
    semantic_rows: dict[str, str] = {}
    excluded_counts = {kind: 0 for kind in sorted(excluded_kinds)}
    excluded_by_status = {
        status: 0 for status in _MUTMUT_STATUS_TO_KEY.values()
    }
    critical_not_killed: list[dict[str, str]] = []
    critical_declared = 0
    critical_killed = 0
    for mutant, status in rows.items():
        classification = classifications[mutant]
        if not isinstance(classification, dict):
            raise TypeError(f"semantic classification must be an object: {mutant}")
        kind = classification.get("kind")
        criticality = classification.get("criticality")
        if (kind, criticality) not in allowed:
            raise ValueError(
                f"invalid semantic classification for {mutant}: "
                f"kind={kind!r}, criticality={criticality!r}"
            )
        if kind in excluded_kinds:
            excluded_counts[str(kind)] += 1
            excluded_by_status[status] += 1
            continue
        semantic_rows[mutant] = status
        if criticality == "critical":
            critical_declared += 1
            if status == "killed":
                critical_killed += 1
            else:
                critical_not_killed.append({"mutant": mutant, "status": status})

    if not semantic_rows:
        raise ValueError("semantic mutation denominator is empty")
    semantic_by_module = {
        module: {
            mutant: status
            for mutant, status in by_module[module].items()
            if mutant in semantic_rows
        }
        for module in modules
    }
    semantic_modules: dict[str, dict] = {}
    for module, module_rows in semantic_by_module.items():
        module_total = len(module_rows)
        module_killed = sum(status == "killed" for status in module_rows.values())
        module_rate = module_killed / module_total if module_total else 0.0
        semantic_modules[module] = {
            "total": module_total,
            "killed": module_killed,
            "kill_rate": round(module_rate, 4),
            "bar": bar,
            "pass": module_total > 0 and module_rate >= bar,
        }
    semantic_total = len(semantic_rows)
    semantic_killed = sum(status == "killed" for status in semantic_rows.values())
    semantic_rate = semantic_killed / semantic_total
    semantic_status_counts = {
        status: sum(value == status for value in semantic_rows.values())
        for status in _MUTMUT_STATUS_TO_KEY.values()
    }
    machine_excluded_total = sum(excluded_counts.values())
    if total != semantic_total + machine_excluded_total:
        raise ValueError("raw/semantic/machine-excluded totals are not conserved")
    for status, raw_count in status_counts.items():
        if raw_count != semantic_status_counts[status] + excluded_by_status[status]:
            raise ValueError(
                "raw/semantic/machine-excluded status counts are not conserved"
            )
    critical_not_killed.sort(key=lambda item: item["mutant"])
    semantic_pass = (
        semantic_rate >= bar
        and all(score["pass"] for score in semantic_modules.values())
        and not critical_not_killed
    )
    semantic = {
        "total": semantic_total,
        "killed": semantic_killed,
        "status_counts": semantic_status_counts,
        "kill_rate": round(semantic_rate, 4),
        "bar": bar,
        "excluded_counts": excluded_counts,
        "excluded_by_status": excluded_by_status,
        "critical": {
            "declared": critical_declared,
            "killed": critical_killed,
            "not_killed": critical_not_killed,
        },
        "modules": semantic_modules,
        "pass": semantic_pass,
    }
    machine_excluded = {
        "total": machine_excluded_total,
        "status_counts": excluded_by_status,
        "kind_counts": excluded_counts,
    }
    return {
        **raw,
        "raw": raw,
        "semantic": semantic,
        "machine_excluded": machine_excluded,
        "pass": semantic_pass,
    }


def _knob(reg: dict, section: str, key: str, envname: str, default, cast):
    """Resolve a harness knob. Precedence: env > registry 'harness' block > tests/harness_config.json
    default. Keeps the important tunables (timeout, bar, jobs) in ONE visible config, not buried."""
    if envname and os.environ.get(envname) not in (None, ""):
        return cast(os.environ[envname])
    rh = (reg.get("harness") or {}).get(section, {})
    if key in rh:
        return cast(rh[key])
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8")).get(section, {})
        if key in cfg and not str(key).startswith("_"):
            return cast(cfg[key])
    except Exception:
        pass
    return default


def _configured_knob(reg: dict, section: str, key: str, default, cast):
    """Resolve the non-environment floor for a scientific gate knob."""

    registry_section = (reg.get("harness") or {}).get(section, {})
    if key in registry_section:
        return cast(registry_section[key])
    try:
        configured = json.loads(CONFIG_PATH.read_text(encoding="utf-8")).get(
            section,
            {},
        )
        if key in configured and not str(key).startswith("_"):
            return cast(configured[key])
    except (OSError, TypeError, ValueError):
        pass
    return default


def _validate_mutation_gate_knobs(
    *,
    bar: float,
    timeout_multiplier: float,
    timeout_constant: float,
) -> None:
    """Reject non-finite or gate-weakening numerical controls."""

    if not math.isfinite(bar) or not 0.0 <= bar <= 1.0:
        raise ValueError("kill_rate_bar must be finite and within [0, 1]")
    if not math.isfinite(timeout_multiplier) or timeout_multiplier <= 0.0:
        raise ValueError("timeout_multiplier must be finite and positive")
    if not math.isfinite(timeout_constant) or timeout_constant < 0.0:
        raise ValueError("timeout_constant must be finite and nonnegative")


def _resolve_mutation_bar(reg: dict) -> float:
    """Resolve the kill-rate bar without allowing an environment downgrade."""

    configured = _configured_knob(
        reg,
        "mutation_gate",
        "kill_rate_bar",
        0.90,
        float,
    )
    selected = _knob(
        reg,
        "mutation_gate",
        "kill_rate_bar",
        "ECS_MUT_BAR",
        0.90,
        float,
    )
    _validate_mutation_gate_knobs(
        bar=configured,
        timeout_multiplier=1.0,
        timeout_constant=0.0,
    )
    _validate_mutation_gate_knobs(
        bar=selected,
        timeout_multiplier=1.0,
        timeout_constant=0.0,
    )
    if selected < configured:
        raise ValueError(
            "ECS_MUT_BAR cannot weaken the configured kill_rate_bar: "
            f"{selected} < {configured}"
        )
    return selected


def _env() -> dict:
    e = dict(os.environ)
    e["PATH"] = ENVBIN + ":" + e.get("PATH", "")
    e["ECS_MUTATION_SKIP_SLOW"] = "1"
    return e


def lane_environment(base: dict[str, str], *, lane: str) -> dict[str, str]:
    """Return an isolated child environment for one mutation execution lane."""

    if lane not in {"cpu_parallel", "gpu_serial"}:
        raise ValueError(f"unknown mutation lane: {lane!r}")
    child = dict(base)
    child.pop("PYTHONPATH", None)
    child["PYTHONNOUSERSITE"] = "1"
    if lane == "cpu_parallel":
        child["CUDA_VISIBLE_DEVICES"] = ""
        child.pop("ECS_GPU_SLOT", None)
        for name in (
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        ):
            child[name] = "1"
    else:
        child["PYTHONDONTWRITEBYTECODE"] = "1"
        child["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        for name in (
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "PYTEST_XDIST_WORKER",
            "PYTEST_XDIST_WORKER_COUNT",
            "PYTEST_XDIST_TESTRUNUID",
        ):
            child.pop(name, None)
        for name in (
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        ):
            child[name] = "1"
    return child


def resolve_jobs(reg: dict, *, lane: str, requested: int | None) -> int:
    """Resolve worker count and bound one leased GPU batch to four fresh workers."""

    if lane not in {"cpu_parallel", "gpu_serial"}:
        raise ValueError(f"unknown mutation lane: {lane!r}")
    raw: object = requested
    if raw is None and os.environ.get("MUTMUT_JOBS") not in (None, ""):
        try:
            raw = int(os.environ["MUTMUT_JOBS"])
        except ValueError as exc:
            raise ValueError("MUTMUT_JOBS must be a positive integer") from exc
    if raw is None:
        raw = ((reg.get("harness") or {}).get("mutation_gate") or {}).get("jobs")
    if raw is None:
        try:
            configured = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            raw = (configured.get("mutation_gate") or {}).get("jobs")
        except (OSError, ValueError, TypeError):
            raw = None
    if raw is None:
        raw = 4 if lane == "cpu_parallel" else 1
    if isinstance(raw, bool) or not isinstance(raw, int) or raw <= 0:
        raise ValueError("mutation jobs must be a positive integer")
    if lane == "gpu_serial" and raw > 4:
        raise ValueError("gpu_serial mutation allows at most 4 fresh workers")
    return raw


def execution_policy(*, lane: str, jobs: int) -> dict:
    """Materialize the enforced CPU/GPU concurrency contract as result evidence."""

    if lane == "gpu_serial":
        if type(jobs) is not int or jobs <= 0:
            raise ValueError("gpu_serial mutation requires positive jobs")
        if jobs > 4:
            raise ValueError("gpu_serial mutation allows at most 4 fresh workers")
        return {
            "lane": lane,
            "jobs": jobs,
            "cuda_hidden": False,
            "stock_mutmut_worker_pool": False,
            "fresh_exec_per_tested_mutant": True,
            "max_concurrent_mutant_workers": jobs,
        }
    if lane == "cpu_parallel":
        if type(jobs) is not int or jobs <= 0:
            raise ValueError("cpu_parallel mutation requires positive jobs")
        return {
            "lane": lane,
            "jobs": jobs,
            "cuda_hidden": True,
            "stock_mutmut_worker_pool": True,
            "fresh_exec_per_tested_mutant": False,
            "max_concurrent_mutant_workers": jobs,
        }
    raise ValueError(f"unknown mutation lane: {lane!r}")


def _validate_gpu_execution_policy(policy: object) -> int:
    """Require the full fail-closed policy used for checkpointed GPU work."""

    if not isinstance(policy, dict):
        raise TypeError("GPU execution policy must be an object")
    jobs = policy.get("jobs")
    if type(jobs) is not int or not (1 <= jobs <= 4):
        raise ValueError("GPU execution policy jobs must be in [1, 4]")
    expected = {
        "lane": "gpu_serial",
        "cuda_hidden": False,
        "stock_mutmut_worker_pool": False,
        "fresh_exec_per_tested_mutant": True,
        "max_concurrent_mutant_workers": jobs,
    }
    for key, value in expected.items():
        if key not in policy or policy[key] != value:
            raise ValueError(f"GPU execution policy {key} mismatch")
    for key in ("timeout_multiplier", "timeout_constant"):
        value = policy.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"GPU execution policy {key} is invalid")
        if not math.isfinite(float(value)) or float(value) <= 0.0:
            raise ValueError(f"GPU execution policy {key} is invalid")
    explicit_timeout = policy.get("explicit_timeout")
    if explicit_timeout is not None:
        if isinstance(explicit_timeout, bool) or not isinstance(
            explicit_timeout, (int, float)
        ):
            raise TypeError("GPU execution policy explicit_timeout is invalid")
        if not math.isfinite(float(explicit_timeout)) or float(explicit_timeout) <= 0.0:
            raise ValueError("GPU execution policy explicit_timeout is invalid")
    if "bound_environment" not in policy:
        raise ValueError("GPU execution policy bound_environment is missing")
    _validate_gpu_bound_environment(policy["bound_environment"])
    if "device_identity" not in policy:
        raise ValueError("GPU execution policy device_identity is missing")
    _validate_gpu_device_identity(policy["device_identity"])
    bound_slot = policy["bound_environment"]["values"]["ECS_GPU_SLOT"]
    bound_visible = policy["bound_environment"]["values"]["CUDA_VISIBLE_DEVICES"]
    if (
        bound_slot != str(policy["device_identity"]["slot"])
        or bound_visible != bound_slot
    ):
        raise ValueError("GPU execution policy device/environment identity mismatch")
    return jobs


def input_snapshot(
    paths: tuple[str | Path, ...],
    *,
    repo: Path = REPO,
) -> str:
    """Hash an immutable, path-bound view of all declared mutation inputs."""

    root = repo.resolve()
    files: set[Path] = set()
    for raw in paths:
        candidate = Path(raw)
        candidate = candidate if candidate.is_absolute() else root / candidate
        resolved = candidate.resolve(strict=True)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"snapshot input escapes repository: {raw!r}") from exc
        candidates = resolved.rglob("*") if resolved.is_dir() else (resolved,)
        for path in candidates:
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            canonical = path.resolve(strict=True)
            try:
                canonical.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"snapshot input escapes repository: {path}") from exc
            files.add(canonical)
    if not files:
        raise ValueError("mutation snapshot has no files")

    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _validate_mutation_score_summary(
    score: object,
    *,
    bar: float,
    context: str,
    validate_pass: bool = True,
    exact_fields: frozenset[str] | set[str] | None = None,
) -> None:
    if not isinstance(score, dict):
        raise TypeError(f"{context} score must be an object")
    required_fields = _MUTATION_SCORE_FIELDS
    missing_fields = required_fields - set(score)
    if missing_fields:
        raise ValueError(
            f"{context} required score fields are missing: {sorted(missing_fields)}"
        )
    if exact_fields is not None and set(score) != set(exact_fields):
        raise ValueError(f"{context} score fields do not match the v3 schema")
    total = score.get("total")
    killed = score.get("killed")
    if (
        type(total) is not int
        or type(killed) is not int
        or total <= 0
        or killed < 0
        or killed > total
    ):
        raise ValueError(f"{context} score has invalid counts")
    status_counts = score.get("status_counts")
    if not isinstance(status_counts, dict) or any(
        type(value) is not int or value < 0 for value in status_counts.values()
    ):
        raise TypeError(f"{context} status counts are invalid")
    expected_status_keys = set(_MUTMUT_STATUS_TO_KEY.values())
    if set(status_counts) != expected_status_keys:
        raise ValueError(f"{context} status keys do not match the normalized domain")
    if sum(status_counts.values()) != total:
        raise ValueError(f"{context} status counts do not equal total")
    if int(status_counts.get("killed", 0)) != killed:
        raise ValueError(f"{context} killed count disagrees with status counts")
    if score["bar"] != bar:
        raise ValueError(f"{context} kill-rate bar mismatch")
    expected_rate = round(killed / total, 4)
    if score["kill_rate"] != expected_rate:
        raise ValueError(f"{context} kill rate disagrees with counts")

    modules = score.get("modules")
    expected_modules_pass = True
    if not isinstance(modules, dict) or not modules:
        raise ValueError(f"{context} modules must be a nonempty object")
    module_total = 0
    module_killed = 0
    for module, module_score in modules.items():
        if not isinstance(module, str) or not isinstance(module_score, dict):
            raise TypeError(f"{context} module score is malformed")
        current_total = module_score.get("total")
        current_killed = module_score.get("killed")
        if (
            type(current_total) is not int
            or type(current_killed) is not int
            or current_total <= 0
            or current_killed < 0
            or current_killed > current_total
        ):
            raise ValueError(f"{context} module score has invalid counts")
        current_rate = round(current_killed / current_total, 4)
        current_pass = current_killed / current_total >= bar
        if (
            module_score.get("bar") != bar
            or module_score.get("kill_rate") != current_rate
            or module_score.get("pass") is not current_pass
        ):
            raise ValueError(f"{context} module score disagrees with counts")
        module_total += current_total
        module_killed += current_killed
        expected_modules_pass = expected_modules_pass and current_pass
    if module_total != total or module_killed != killed:
        raise ValueError(f"{context} module counts do not equal batch counts")
    expected_pass = killed / total >= bar and expected_modules_pass
    if type(score["pass"]) is not bool:
        raise TypeError(f"{context} pass must be boolean")
    if validate_pass and score["pass"] is not expected_pass:
        raise ValueError(f"{context} pass disagrees with counts")


def merge_mutation_batches(batches: tuple[dict, ...], *, bar: float) -> dict:
    """Merge batch scores with mutant-count weighting and no masking of a failed batch."""

    _validate_mutation_gate_knobs(
        bar=bar,
        timeout_multiplier=1.0,
        timeout_constant=0.0,
    )
    if not batches:
        raise ValueError("mutation suite requires at least one batch")
    for index, batch in enumerate(batches):
        if batch.get("schema") != _MUTATION_BATCH_RUN_SCHEMA:
            raise ValueError("unsupported mutation batch result schema")
        raw_score = batch.get("raw") if "semantic" in batch else batch
        _validate_mutation_score_summary(
            raw_score,
            bar=bar,
            context=f"mutation batch {index} raw",
            exact_fields=_MUTATION_SCORE_FIELDS if "semantic" in batch else None,
        )
        if "semantic" in batch:
            semantic_score = batch.get("semantic")
            _validate_mutation_score_summary(
                semantic_score,
                bar=bar,
                context=f"mutation batch {index} semantic",
                validate_pass=False,
                exact_fields=_SEMANTIC_SCORE_FIELDS,
            )
            machine_excluded = batch.get("machine_excluded")
            if not isinstance(machine_excluded, dict) or set(machine_excluded) != {
                "total",
                "status_counts",
                "kind_counts",
            }:
                raise ValueError("mutation batch machine exclusion is malformed")
            excluded_total = machine_excluded["total"]
            excluded_status_counts = machine_excluded["status_counts"]
            excluded_kind_counts = machine_excluded["kind_counts"]
            if (
                type(excluded_total) is not int
                or excluded_total < 0
                or not isinstance(excluded_status_counts, dict)
                or not isinstance(excluded_kind_counts, dict)
                or set(excluded_status_counts)
                != set(_MUTMUT_STATUS_TO_KEY.values())
                or set(excluded_kind_counts)
                != {"exception_prose_noncontractual"}
                or any(
                    type(value) is not int or value < 0
                    for value in (
                        *excluded_status_counts.values(),
                        *excluded_kind_counts.values(),
                    )
                )
                or sum(excluded_status_counts.values()) != excluded_total
                or sum(excluded_kind_counts.values()) != excluded_total
                or raw_score["total"] != semantic_score["total"] + excluded_total
            ):
                raise ValueError("mutation batch machine exclusion is not conserved")
            all_statuses = set(raw_score["status_counts"]) | set(
                semantic_score["status_counts"]
            ) | set(excluded_status_counts)
            if any(
                int(raw_score["status_counts"].get(status, 0))
                != int(semantic_score["status_counts"].get(status, 0))
                + int(excluded_status_counts.get(status, 0))
                for status in all_statuses
            ):
                raise ValueError("mutation batch machine exclusion is not conserved")
    total = sum(int(batch["total"]) for batch in batches)
    killed = sum(int(batch["killed"]) for batch in batches)
    if total <= 0 or killed < 0 or killed > total:
        raise ValueError("mutation suite has invalid aggregate counts")
    statuses = sorted(
        {
            status
            for batch in batches
            for status in batch.get("status_counts", {})
        }
    )
    status_counts = {
        status: sum(int(batch.get("status_counts", {}).get(status, 0)) for batch in batches)
        for status in statuses
    }
    if sum(status_counts.values()) != total:
        raise ValueError("mutation suite status counts do not equal total")
    rate = killed / total
    raw_merged = {
        "total": total,
        "killed": killed,
        "status_counts": status_counts,
        "kill_rate": round(rate, 4),
        "bar": bar,
        "batches": list(batches),
        "pass": rate >= bar and all(batch.get("pass") is True for batch in batches),
    }
    semantic_presence = ["semantic" in batch for batch in batches]
    if any(semantic_presence) and not all(semantic_presence):
        raise ValueError("mutation suite cannot merge a raw/semantic mixture")
    if not any(semantic_presence):
        return raw_merged

    semantic_total = 0
    semantic_killed = 0
    semantic_statuses: set[str] = set()
    semantic_modules: dict[str, dict] = {}
    excluded_kinds: set[str] = set()
    excluded_statuses: set[str] = set()
    critical_declared = 0
    critical_killed = 0
    critical_not_killed: list[dict] = []
    for batch in batches:
        raw = batch.get("raw")
        semantic = batch.get("semantic")
        if not isinstance(raw, dict) or not isinstance(semantic, dict):
            raise TypeError("semantic mutation batch requires raw and semantic objects")
        if any(
            type(raw.get(field)) is not type(batch.get(field))
            or raw.get(field) != batch.get(field)
            for field in (
                "total",
                "killed",
                "status_counts",
                "kill_rate",
                "bar",
                "modules",
            )
        ):
            raise ValueError("semantic batch raw aliases disagree")
        if (
            type(batch.get("pass")) is not bool
            or batch["pass"] is not semantic.get("pass")
        ):
            raise ValueError("semantic batch pass alias disagrees")
        batch_semantic_total = int(semantic.get("total", -1))
        batch_semantic_killed = int(semantic.get("killed", -1))
        if (
            batch_semantic_total <= 0
            or batch_semantic_killed < 0
            or batch_semantic_killed > batch_semantic_total
        ):
            raise ValueError("semantic mutation batch has invalid counts")
        batch_status_counts = semantic.get("status_counts")
        if not isinstance(batch_status_counts, dict) or sum(
            int(value) for value in batch_status_counts.values()
        ) != batch_semantic_total:
            raise ValueError("semantic mutation status counts do not equal total")
        semantic_total += batch_semantic_total
        semantic_killed += batch_semantic_killed
        semantic_statuses.update(batch_status_counts)
        batch_modules = semantic.get("modules")
        if not isinstance(batch_modules, dict) or not batch_modules:
            raise ValueError("semantic mutation batch requires module scores")
        overlap = set(semantic_modules) & set(batch_modules)
        if overlap:
            raise ValueError(f"semantic mutation modules overlap: {sorted(overlap)}")
        semantic_modules.update(batch_modules)
        machine_excluded = batch["machine_excluded"]
        excluded = machine_excluded["kind_counts"]
        excluded_by_status = machine_excluded["status_counts"]
        if not isinstance(excluded, dict) or not isinstance(excluded_by_status, dict):
            raise TypeError("semantic mutation exclusions must be objects")
        if (
            semantic.get("excluded_counts") != excluded
            or semantic.get("excluded_by_status") != excluded_by_status
        ):
            raise ValueError("semantic exclusion aliases disagree with machine evidence")
        excluded_kinds.update(excluded)
        excluded_statuses.update(excluded_by_status)
        critical = semantic.get("critical")
        if (
            not isinstance(critical, dict)
            or set(critical) != {"declared", "killed", "not_killed"}
            or type(critical.get("declared")) is not int
            or type(critical.get("killed")) is not int
            or not isinstance(critical.get("not_killed"), list)
        ):
            raise TypeError("semantic mutation critical evidence is malformed")
        batch_not_killed = critical["not_killed"]
        if (
            critical["declared"] != batch_semantic_total
            or critical["killed"] != batch_semantic_killed
            or len(batch_not_killed)
            != batch_semantic_total - batch_semantic_killed
            or any(
                not isinstance(item, dict)
                or set(item) != {"mutant", "status"}
                or not isinstance(item["mutant"], str)
                or not item["mutant"]
                or item["status"] not in _MUTMUT_STATUS_TO_KEY.values()
                or item["status"] == "killed"
                for item in batch_not_killed
            )
            or len({item["mutant"] for item in batch_not_killed})
            != len(batch_not_killed)
            or any(
                sum(item["status"] == status for item in batch_not_killed)
                != int(batch_status_counts[status])
                for status in _MUTMUT_STATUS_TO_KEY.values()
                if status != "killed"
            )
        ):
            raise ValueError(
                "semantic mutation critical evidence disagrees with counts"
            )
        expected_semantic_pass = (
            batch_semantic_killed / batch_semantic_total >= bar
            and all(
                module_score.get("pass") is True
                for module_score in batch_modules.values()
            )
            and not batch_not_killed
        )
        if semantic.get("pass") is not expected_semantic_pass:
            raise ValueError(
                "semantic mutation pass disagrees with critical evidence"
            )
        critical_declared += critical["declared"]
        critical_killed += critical["killed"]
        critical_not_killed.extend(batch_not_killed)

    semantic_status_counts = {
        status: sum(
            int(batch["semantic"]["status_counts"].get(status, 0))
            for batch in batches
        )
        for status in sorted(semantic_statuses)
    }
    excluded_counts = {
        kind: sum(
            int(batch["semantic"]["excluded_counts"].get(kind, 0))
            for batch in batches
        )
        for kind in sorted(excluded_kinds)
    }
    excluded_by_status = {
        status: sum(
            int(batch["semantic"]["excluded_by_status"].get(status, 0))
            for batch in batches
        )
        for status in sorted(excluded_statuses)
    }
    critical_identities = [
        item.get("mutant") for item in critical_not_killed if isinstance(item, dict)
    ]
    if len(critical_identities) != len(set(critical_identities)):
        raise ValueError("duplicate critical mutant across semantic batches")
    critical_not_killed.sort(key=lambda item: item["mutant"])
    semantic_rate = semantic_killed / semantic_total
    semantic_pass = (
        semantic_rate >= bar
        and all(score.get("pass") is True for score in semantic_modules.values())
        and not critical_not_killed
        and all(batch["semantic"].get("pass") is True for batch in batches)
    )
    semantic_merged = {
        "total": semantic_total,
        "killed": semantic_killed,
        "status_counts": semantic_status_counts,
        "kill_rate": round(semantic_rate, 4),
        "bar": bar,
        "excluded_counts": excluded_counts,
        "excluded_by_status": excluded_by_status,
        "critical": {
            "declared": critical_declared,
            "killed": critical_killed,
            "not_killed": critical_not_killed,
        },
        "modules": semantic_modules,
        "pass": semantic_pass,
    }
    machine_excluded_total = sum(excluded_counts.values())
    machine_excluded = {
        "total": machine_excluded_total,
        "status_counts": excluded_by_status,
        "kind_counts": excluded_counts,
    }
    if total != semantic_total + machine_excluded_total or any(
        int(status_counts.get(status, 0))
        != int(semantic_status_counts.get(status, 0))
        + int(excluded_by_status.get(status, 0))
        for status in set(status_counts)
        | set(semantic_status_counts)
        | set(excluded_by_status)
    ):
        raise ValueError("merged machine exclusion is not conserved")
    raw_summary = {
        key: value for key, value in raw_merged.items() if key != "batches"
    }
    raw_summary["pass"] = rate >= bar and all(
        batch["raw"].get("pass") is True for batch in batches
    )
    return {
        **raw_merged,
        "raw": raw_summary,
        "semantic": semantic_merged,
        "machine_excluded": machine_excluded,
        "pass": semantic_pass,
    }


def write_json_atomic(destination: Path, payload: dict) -> None:
    """Durably publish one complete result with a same-directory atomic replace."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    serialized = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    try:
        with temporary.open("wb") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _also_copy_paths(reg: dict) -> tuple[str, ...]:
    """Return the isolated mutmut support files declared by a registry."""

    configured = reg.get("mutation_also_copy", [])
    if not isinstance(configured, list):
        raise TypeError("mutation_also_copy must be a list")
    paths = ["src"]
    for value in configured:
        if not isinstance(value, str) or not value.strip():
            raise TypeError("mutation_also_copy entries must be nonempty paths")
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("mutation_also_copy entries must stay inside the repository")
        normalized = path.as_posix()
        if normalized not in paths:
            paths.append(normalized)
    return tuple(paths)


def _semantic_dispositions_path(
    reg: dict,
    *,
    repo: Path = REPO,
) -> Path | None:
    configured = reg.get("semantic_dispositions")
    if configured is None:
        return None
    if not isinstance(configured, str) or not configured.strip():
        raise TypeError("semantic_dispositions must be a nonempty repository path")
    relative = Path(configured)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("semantic_dispositions must stay inside the repository")
    root = repo.resolve(strict=True)
    resolved = (root / relative).resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("semantic_dispositions must stay inside the repository") from exc
    if not resolved.is_file():
        raise FileNotFoundError(f"semantic dispositions are not a file: {resolved}")
    return resolved


def _validate_evidence_locator(locator: object, *, repo: Path) -> str:
    if not isinstance(locator, str) or not locator.strip():
        raise ValueError("semantic disposition evidence locator must be nonempty")
    path_text = locator.split("::", 1)[0].split("#", 1)[0]
    relative = Path(path_text)
    if relative.is_absolute() or ".." in relative.parts or not path_text:
        raise ValueError("semantic disposition evidence locator escapes repository")
    root = repo.resolve(strict=True)
    evidence = (root / relative).resolve(strict=True)
    try:
        evidence.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            "semantic disposition evidence locator escapes repository"
        ) from exc
    if not evidence.is_file():
        raise FileNotFoundError(
            f"semantic disposition evidence locator is not a file: {locator}"
        )
    return locator


def _preflight_semantic_disposition_document(
    path: Path,
    *,
    repo: Path = REPO,
) -> dict:
    """Reject stale or malformed annotation authority before mutation setup."""

    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or set(document) != {
        "schema",
        "classifier_policy",
        "reviewed",
    }:
        raise ValueError("semantic disposition document fields mismatch")
    if document["schema"] != _SEMANTIC_DISPOSITION_SCHEMA:
        raise ValueError("unsupported semantic disposition schema")
    if document["classifier_policy"] != _SEMANTIC_CLASSIFIER_POLICY:
        raise ValueError("semantic disposition classifier policy mismatch")
    reviewed = document["reviewed"]
    if not isinstance(reviewed, list):
        raise TypeError("semantic disposition reviewed field must be a list")
    expected_row_fields = {
        "mutant",
        "mutation_diff_sha256",
        "disposition",
        "reviewer",
        "rationale",
        "evidence_locator",
    }
    seen: set[str] = set()
    for review in reviewed:
        if not isinstance(review, dict) or set(review) != expected_row_fields:
            raise ValueError("semantic disposition review fields mismatch")
        mutant = review["mutant"]
        if not isinstance(mutant, str) or not mutant or mutant in seen:
            raise ValueError(f"duplicate or invalid semantic disposition: {mutant!r}")
        seen.add(mutant)
        if not isinstance(review["mutation_diff_sha256"], str) or re.fullmatch(
            r"[0-9a-f]{64}", review["mutation_diff_sha256"]
        ) is None:
            raise ValueError(
                f"semantic disposition fingerprint must be lowercase sha256: {mutant}"
            )
        if review["disposition"] not in {
            "reviewed_equivalent",
            "reviewed_noncontractual",
            "reviewed_noncritical",
        }:
            raise ValueError(
                f"unknown semantic disposition: {review['disposition']!r}"
            )
        for field in ("reviewer", "rationale"):
            if not isinstance(review[field], str) or not review[field].strip():
                raise ValueError(f"semantic disposition {field} must be nonempty")
        _validate_evidence_locator(review["evidence_locator"], repo=repo)
    return document


def authenticate_semantic_dispositions(
    path: Path,
    *,
    rows: dict[str, str],
    catalog: dict,
    repo: Path = REPO,
) -> tuple[dict[str, dict], dict]:
    """Authenticate manual annotations without granting scoring authority."""

    raw = path.read_bytes()
    document = json.loads(raw.decode("utf-8"))
    expected_document_fields = {"schema", "classifier_policy", "reviewed"}
    if not isinstance(document, dict) or set(document) != expected_document_fields:
        raise ValueError("semantic disposition document fields mismatch")
    if document["schema"] != _SEMANTIC_DISPOSITION_SCHEMA:
        raise ValueError("unsupported semantic disposition schema")
    if document["classifier_policy"] != catalog.get("classifier_policy"):
        raise ValueError("semantic disposition classifier policy mismatch")
    reviewed = document["reviewed"]
    if not isinstance(reviewed, list):
        raise TypeError("semantic disposition reviewed field must be a list")
    catalog_classifications = catalog.get("classifications")
    if not isinstance(catalog_classifications, dict) or set(
        catalog_classifications
    ) != set(rows):
        raise ValueError("semantic disposition catalog identities mismatch")
    classifications = copy.deepcopy(catalog_classifications)
    expected_row_fields = {
        "mutant",
        "mutation_diff_sha256",
        "disposition",
        "reviewer",
        "rationale",
        "evidence_locator",
    }
    seen: set[str] = set()
    applied_mutants: list[str] = []
    out_of_scope_mutants: list[str] = []
    owned_module_prefixes = tuple(
        _module_import_name(module) + "." for module in catalog["modules"]
    )
    for review in reviewed:
        if not isinstance(review, dict) or set(review) != expected_row_fields:
            raise ValueError("semantic disposition review fields mismatch")
        mutant = review["mutant"]
        if not isinstance(mutant, str) or not mutant or mutant in seen:
            raise ValueError(f"duplicate or invalid semantic disposition: {mutant!r}")
        seen.add(mutant)
        fingerprint = review["mutation_diff_sha256"]
        if not isinstance(fingerprint, str) or re.fullmatch(
            r"[0-9a-f]{64}", fingerprint
        ) is None:
            raise ValueError(
                f"semantic disposition fingerprint must be lowercase sha256: {mutant}"
            )
        disposition = review["disposition"]
        if disposition not in {
            "reviewed_equivalent",
            "reviewed_noncontractual",
            "reviewed_noncritical",
        }:
            raise ValueError(f"unknown semantic disposition: {disposition!r}")
        for field in ("reviewer", "rationale"):
            if not isinstance(review[field], str) or not review[field].strip():
                raise ValueError(f"semantic disposition {field} must be nonempty")
        _validate_evidence_locator(review["evidence_locator"], repo=repo)
        if mutant not in classifications:
            if mutant.startswith(owned_module_prefixes):
                raise ValueError(
                    "semantic disposition references unknown mutant in owned scope: "
                    f"{mutant}"
                )
            out_of_scope_mutants.append(mutant)
            continue
        current = classifications[mutant]
        if current.get("kind") != "semantic" or current.get("criticality") != "critical":
            raise ValueError(
                f"semantic disposition cannot override automatic exclusion: {mutant}"
            )
        if rows[mutant] != "survived":
            raise ValueError(
                f"reviewed semantic disposition requires survived status: {mutant}"
            )
        if fingerprint != current.get("mutation_diff_sha256"):
            raise ValueError(f"semantic disposition fingerprint mismatch: {mutant}")
        current["review"] = copy.deepcopy(review)
        applied_mutants.append(mutant)

    root = repo.resolve(strict=True)
    resolved_path = path.resolve(strict=True)
    try:
        relative_path = resolved_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("semantic disposition file escapes repository") from exc
    authentication = {
        "schema": document["schema"],
        "path": relative_path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "classifier_policy": document["classifier_policy"],
        "reviewed_count": len(reviewed),
        "applied_reviewed_count": len(applied_mutants),
        "out_of_scope_reviewed_count": len(out_of_scope_mutants),
        "applied_mutants": sorted(applied_mutants),
        "out_of_scope_mutants": sorted(out_of_scope_mutants),
        "scope_modules": sorted(catalog["modules"]),
        "scope_complete": not out_of_scope_mutants,
        "module_catalogs": copy.deepcopy(catalog.get("modules")),
    }
    return classifications, authentication


def _authenticate_suite_disposition_partition(
    batch_results: list[dict],
    *,
    disposition_path: Path,
    repo: Path = REPO,
    require_classifications: bool = False,
) -> dict:
    """Prove that every shared-manifest review is applied by exactly one batch."""

    raw = disposition_path.read_bytes()
    document = json.loads(raw.decode("utf-8"))
    expected_document_fields = {"schema", "classifier_policy", "reviewed"}
    if not isinstance(document, dict) or set(document) != expected_document_fields:
        raise ValueError("semantic disposition document fields mismatch")
    if document["schema"] != _SEMANTIC_DISPOSITION_SCHEMA:
        raise ValueError("unsupported semantic disposition schema")
    if document["classifier_policy"] != _SEMANTIC_CLASSIFIER_POLICY:
        raise ValueError("semantic disposition classifier policy mismatch")
    if not isinstance(document["reviewed"], list):
        raise TypeError("semantic disposition reviewed field must be a list")
    reviewed_rows = document["reviewed"]
    reviewed_by_mutant: dict[str, dict] = {}
    for review in reviewed_rows:
        if not isinstance(review, dict):
            raise ValueError("semantic disposition review must be an object")
        mutant = review.get("mutant")
        if not isinstance(mutant, str) or not mutant or mutant in reviewed_by_mutant:
            raise ValueError(f"duplicate or invalid semantic disposition: {mutant!r}")
        reviewed_by_mutant[mutant] = review

    root = repo.resolve(strict=True)
    resolved_path = disposition_path.resolve(strict=True)
    try:
        relative_path = resolved_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("semantic disposition file escapes repository") from exc
    manifest_sha256 = hashlib.sha256(raw).hexdigest()
    expected_mutants = set(reviewed_by_mutant)
    application_counts = {mutant: 0 for mutant in expected_mutants}
    application_by_mutant: dict[str, str] = {}
    batch_application_counts: dict[str, int] = {}
    seen_tags: set[str] = set()

    for batch in batch_results:
        if not isinstance(batch, dict):
            raise TypeError("mutation batch result must be an object")
        tag = batch.get("tag")
        if not isinstance(tag, str) or not tag or tag in seen_tags:
            raise ValueError(f"invalid or duplicate mutation batch result tag: {tag!r}")
        seen_tags.add(tag)
        authentication = batch.get("disposition_authentication")
        if not isinstance(authentication, dict):
            raise ValueError(f"mutation batch lacks disposition authentication: {tag}")
        if authentication.get("path") != relative_path:
            raise ValueError(f"mutation batch disposition path mismatch: {tag}")
        if authentication.get("sha256") != manifest_sha256:
            raise ValueError(f"mutation batch disposition sha256 mismatch: {tag}")
        if authentication.get("schema") != document["schema"]:
            raise ValueError(f"mutation batch disposition schema mismatch: {tag}")
        if authentication.get("classifier_policy") != document["classifier_policy"]:
            raise ValueError(
                f"mutation batch disposition classifier policy mismatch: {tag}"
            )
        if authentication.get("reviewed_count") != len(expected_mutants):
            raise ValueError(f"mutation batch disposition count mismatch: {tag}")

        applied_raw = authentication.get("applied_mutants")
        out_of_scope_raw = authentication.get("out_of_scope_mutants")
        if not isinstance(applied_raw, list) or not isinstance(out_of_scope_raw, list):
            raise TypeError(f"mutation batch disposition partition is malformed: {tag}")
        if any(not isinstance(mutant, str) or not mutant for mutant in applied_raw):
            raise ValueError(f"mutation batch applied mutant is invalid: {tag}")
        if any(
            not isinstance(mutant, str) or not mutant
            for mutant in out_of_scope_raw
        ):
            raise ValueError(f"mutation batch out-of-scope mutant is invalid: {tag}")
        applied = set(applied_raw)
        out_of_scope = set(out_of_scope_raw)
        if len(applied) != len(applied_raw) or len(out_of_scope) != len(
            out_of_scope_raw
        ):
            raise ValueError(f"mutation batch disposition partition has duplicates: {tag}")
        if applied & out_of_scope:
            raise ValueError(f"mutation batch disposition partition overlaps: {tag}")
        if applied | out_of_scope != expected_mutants:
            raise ValueError(f"mutation batch disposition partition is incomplete: {tag}")
        if authentication.get("applied_reviewed_count") != len(applied):
            raise ValueError(f"mutation batch applied disposition count mismatch: {tag}")
        if authentication.get("out_of_scope_reviewed_count") != len(out_of_scope):
            raise ValueError(
                f"mutation batch out-of-scope disposition count mismatch: {tag}"
            )

        if require_classifications:
            semantic_classification = batch.get("semantic_classification")
            if not isinstance(semantic_classification, dict):
                raise ValueError(f"mutation batch lacks semantic classifications: {tag}")
            catalog = semantic_classification.get("catalog")
            if not isinstance(catalog, dict):
                raise ValueError(f"mutation batch semantic catalog is malformed: {tag}")
            catalog_modules = catalog.get("modules")
            if not isinstance(catalog_modules, dict) or not catalog_modules:
                raise ValueError(
                    f"mutation batch semantic catalog modules are malformed: {tag}"
                )
            if authentication.get("module_catalogs") != catalog_modules:
                raise ValueError(f"mutation batch module catalogs mismatch: {tag}")
            scope_modules = authentication.get("scope_modules")
            if (
                not isinstance(scope_modules, list)
                or any(not isinstance(module, str) for module in scope_modules)
                or scope_modules != sorted(catalog_modules)
            ):
                raise ValueError(f"mutation batch scope modules mismatch: {tag}")
            if authentication.get("scope_complete") is not (not out_of_scope):
                raise ValueError(f"mutation batch scope completeness mismatch: {tag}")
            classifications = semantic_classification.get("classifications")
            if not isinstance(classifications, dict):
                raise ValueError(f"mutation batch classifications are malformed: {tag}")
            classification_mutants = set(classifications)
            expected_applied = expected_mutants & classification_mutants
            expected_out_of_scope = expected_mutants - classification_mutants
            if applied != expected_applied or out_of_scope != expected_out_of_scope:
                raise ValueError(
                    f"mutation batch disposition scope partition mismatch: {tag}"
                )
            for mutant, classification in classifications.items():
                if not isinstance(classification, dict) or classification.get(
                    "module"
                ) not in catalog_modules:
                    raise ValueError(
                        f"mutation batch classification module mismatch: {tag}:{mutant}"
                    )
            actually_reviewed = {
                mutant
                for mutant, classification in classifications.items()
                if isinstance(classification, dict) and "review" in classification
            }
            if actually_reviewed != applied:
                raise ValueError(
                    f"mutation batch claimed applications disagree with classifications: {tag}"
                )
            for mutant in applied:
                if classifications[mutant].get("review") != reviewed_by_mutant[mutant]:
                    raise ValueError(
                        "mutation batch applied review disagrees with manifest: "
                        f"{tag}:{mutant}"
                    )

        batch_application_counts[tag] = len(applied)
        for mutant in applied:
            application_counts[mutant] += 1
            if mutant not in application_by_mutant:
                application_by_mutant[mutant] = tag

    invalid_counts = {
        mutant: count for mutant, count in application_counts.items() if count != 1
    }
    if invalid_counts:
        raise ValueError(
            "every semantic disposition must be applied by exactly one batch: "
            f"{invalid_counts}"
        )
    return {
        "schema": document.get("schema"),
        "path": relative_path,
        "sha256": manifest_sha256,
        "classifier_policy": document.get("classifier_policy"),
        "reviewed_count": len(expected_mutants),
        "applied_exactly_once_count": len(application_by_mutant),
        "application_by_mutant": {
            mutant: application_by_mutant[mutant]
            for mutant in sorted(application_by_mutant)
        },
        "batch_application_counts": {
            tag: batch_application_counts[tag] for tag in sorted(batch_application_counts)
        },
        "pass": True,
    }


def _prepare_also_copy_destinations(
    paths: tuple[str, ...],
    *,
    repo: Path = REPO,
) -> None:
    """Create parents that mutmut 3.6 does not create for file copies."""

    mutants = repo / "mutants"
    mutants.mkdir(parents=True, exist_ok=True)
    for value in paths:
        if (repo / value).is_file():
            (mutants / value).parent.mkdir(parents=True, exist_ok=True)


def _process_evidence(ran) -> dict:
    return {
        "returncode": int(ran.returncode),
        "timed_out": bool(ran.timed_out),
        "group_cleanup_verified": bool(ran.group_cleanup_verified),
        "ok": bool(ran.ok),
    }


def _require_process_ok(label: str, ran) -> dict:
    evidence = _process_evidence(ran)
    if (
        not evidence["ok"]
        or evidence["returncode"] != 0
        or evidence["timed_out"]
        or not evidence["group_cleanup_verified"]
    ):
        raise RuntimeError(f"{label} failed: {evidence}")
    return evidence


def _batch_snapshot_paths(registry_path: Path, reg: dict) -> tuple[str | Path, ...]:
    paths: list[str | Path] = [registry_path]
    harness_path = REPO / "tests" / "harness" / "mutation.py"
    if harness_path.is_file():
        paths.append(harness_path)
    if CONFIG_PATH.is_file():
        paths.append(CONFIG_PATH)
    for tests_path in (REPO / "tests", REPO / "test"):
        if tests_path.is_dir():
            paths.append(tests_path)
    paths.extend(sorted(path for path in REPO.glob("test*.py") if path.is_file()))
    for automatic_input in (REPO / "setup.cfg", REPO / "pyproject.toml"):
        if automatic_input.is_file():
            paths.append(automatic_input)
    paths.extend(reg["reconcile_modules"])
    paths.extend(reg["covered_by_test_files"])
    paths.extend(_also_copy_paths(reg))
    semantic_dispositions = _semantic_dispositions_path(reg, repo=REPO)
    if semantic_dispositions is not None:
        paths.append(semantic_dispositions)
    return tuple(paths)


def _clear_mutants_tree(*, repo: Path = REPO) -> None:
    """Remove all mutmut state, including a tree frozen by an abrupt exit."""

    mutants = repo / "mutants"
    if mutants.is_symlink():
        raise RuntimeError(f"mutants tree may not be a symlink: {mutants}")
    if mutants.exists():
        paths = [mutants, *sorted(mutants.rglob("*"), key=lambda path: path.as_posix())]
        if any(path.is_symlink() for path in paths):
            raise RuntimeError("mutants tree may not contain symlinks during cleanup")
        for path in paths:
            if path.is_dir():
                mode = path.stat().st_mode & 0o7777
                path.chmod(mode | 0o300)
        shutil.rmtree(mutants)
    if mutants.exists() or mutants.is_symlink():
        raise RuntimeError(f"mutants tree survived cleanup: {mutants}")


def _make_generated_tree_read_only(root: Path) -> list[tuple[Path, int]]:
    """Remove every write bit from an immutable generated worker tree."""

    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"generated mutant tree is not a real directory: {root}")
    paths = [root, *sorted(root.rglob("*"), key=lambda path: path.as_posix())]
    if any(path.is_symlink() for path in paths):
        raise ValueError("generated mutant tree may not contain symlinks")
    frozen: list[tuple[Path, int]] = []
    try:
        for path in paths:
            mode = path.stat().st_mode & 0o7777
            frozen.append((path, mode))
            path.chmod(mode & ~0o222)
            if path.stat().st_mode & 0o222:
                raise RuntimeError(f"generated mutant path remained writable: {path}")
    except BaseException:
        for path, mode in reversed(frozen):
            if path.exists() and not path.is_symlink():
                path.chmod(mode)
        raise
    return frozen


def _restore_generated_tree_modes(frozen: list[tuple[Path, int]]) -> None:
    violations: list[str] = []
    for path, _mode in frozen:
        if path.is_symlink() or not path.exists():
            violations.append(f"missing-or-symlink:{path}")
        elif path.stat().st_mode & 0o222:
            violations.append(f"became-writable:{path}")
    restore_errors: list[str] = []
    for path, mode in reversed(frozen):
        try:
            if path.exists() and not path.is_symlink():
                path.chmod(mode)
        except OSError as exc:
            restore_errors.append(f"{path}:{type(exc).__name__}")
    if violations or restore_errors:
        raise RuntimeError(
            "generated mutant tree read-only contract failed: "
            f"violations={violations}, restore_errors={restore_errors}"
        )


def _write_mutmut_config(
    setup: Path,
    *,
    modules: tuple[str, ...],
    tests: tuple[str, ...],
    also_copy: tuple[str, ...],
    timeout_multiplier: float,
    timeout_constant: float,
) -> None:
    setup.write_text(
        "[mutmut]\n"
        "source_paths=" + "\n\t".join(modules) + "\n"
        "pytest_add_cli_args_test_selection=-m\n"
        "\tnot mutation_trampoline_incompatible\n\t"
        + "\n\t".join(tests)
        + "\n"
        "also_copy=" + "\n\t".join(also_copy) + "\n"
        f"timeout_multiplier={timeout_multiplier}\n"
        f"timeout_constant={timeout_constant}\n",
        encoding="utf-8",
    )


_EXIT_STATUS = {
    None: "not_checked",
    0: "survived",
    1: "killed",
    2: "check_was_interrupted_by_user",
    3: "suspicious",
    4: "suspicious",
    5: "no_tests",
    33: "no_tests",
    34: "skipped",
    35: "suspicious",
    36: "timeout",
    37: "caught_by_type_check",
    -24: "timeout",
    24: "timeout",
    152: "timeout",
    255: "timeout",
    -11: "segfault",
    -9: "segfault",
}


def _load_mutmut_meta_rows(
    modules: tuple[str, ...],
    *,
    repo: Path = REPO,
) -> tuple[dict[str, str], dict[str, int | None]]:
    """Load canonical mutation statuses from mutmut's raw per-source exit codes."""

    rows: dict[str, str] = {}
    raw_codes: dict[str, int | None] = {}
    for module in modules:
        _module_import_name(module)
        meta_path = repo / "mutants" / Path(module).with_suffix(".py.meta")
        if not meta_path.is_file():
            raise FileNotFoundError(f"missing mutmut metadata for {module}: {meta_path}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        exit_codes = meta.get("exit_code_by_key")
        if not isinstance(exit_codes, dict) or not exit_codes:
            raise ValueError(f"mutmut metadata has no exit_code_by_key rows: {meta_path}")
        for mutant, raw_code in exit_codes.items():
            if not isinstance(mutant, str) or not mutant or mutant in rows:
                raise ValueError(f"invalid or duplicate raw mutmut key: {mutant!r}")
            if raw_code is not None and type(raw_code) is not int:
                raise TypeError(
                    f"raw mutmut exit code must be an integer or null: {mutant}"
                )
            rows[mutant] = _EXIT_STATUS.get(raw_code, "suspicious")
            raw_codes[mutant] = raw_code
    if not rows:
        raise ValueError("raw mutmut metadata contained no mutant rows")
    return rows, raw_codes


def _cross_check_mutmut_display(
    canonical_rows: dict[str, str],
    display_rows: dict[str, str],
    *,
    raw_codes: dict[str, int | None],
) -> list[dict]:
    """Cross-check human-readable rows without trusting their rc=3 mislabel."""

    if set(display_rows) != set(canonical_rows):
        raise ValueError(
            "mutmut display/raw mutant identity mismatch: "
            f"missing={sorted(set(canonical_rows) - set(display_rows))}, "
            f"extra={sorted(set(display_rows) - set(canonical_rows))}"
        )
    if set(raw_codes) != set(canonical_rows):
        raise ValueError("raw mutmut exit-code identities do not match canonical rows")
    mismatches: list[dict] = []
    for mutant in sorted(canonical_rows):
        canonical = canonical_rows[mutant]
        displayed = display_rows[mutant]
        if canonical == displayed:
            continue
        raw_code = raw_codes[mutant]
        if raw_code != 3 or canonical != "suspicious" or displayed != "killed":
            raise ValueError(
                "unexpected mutmut display/raw status mismatch: "
                f"{mutant}: rc={raw_code!r}, canonical={canonical}, "
                f"display={displayed}"
            )
        mismatches.append(
            {
                "mutant": mutant,
                "raw_exit_code": raw_code,
                "canonical_status": canonical,
                "display_status": displayed,
            }
        )
    return mismatches


def _fresh_worker_status(ran) -> str:
    if not ran.group_cleanup_verified:
        raise RuntimeError("fresh mutant worker process-group cleanup was not verified")
    if ran.timed_out:
        return "timeout"
    return _EXIT_STATUS.get(int(ran.returncode), "suspicious")


_PYTEST_SENTINEL_SCHEMA = (
    "error_coupling_simulator.harness.mutation_pytest_completion.v2"
)


def _direct_resource_exhaustion_kind(exc: BaseException) -> str | None:
    if isinstance(exc, MemoryError):
        return "host_out_of_memory"
    exc_type = type(exc)
    module = exc_type.__module__.casefold()
    name = exc_type.__name__.casefold()
    if name == "outofmemoryerror" and any(
        token in module for token in ("torch", "cupy", "cuda")
    ):
        return "cuda_out_of_memory"
    message = str(exc).casefold()
    cuda_oom_markers = (
        "cuda out of memory",
        "cuda error: out of memory",
        "cudaerrormemoryallocation",
        "cublas_status_alloc_failed",
    )
    if isinstance(exc, RuntimeError) and any(
        marker in message for marker in cuda_oom_markers
    ):
        return "cuda_out_of_memory"
    return None


def _resource_exhaustion_kinds(exc: BaseException) -> set[str]:
    """Collect resource failures through groups and chained exceptions."""

    pending = [exc]
    seen: set[int] = set()
    kinds: set[str] = set()
    while pending:
        current = pending.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        kind = _direct_resource_exhaustion_kind(current)
        if kind is not None:
            kinds.add(kind)
        nested = getattr(current, "exceptions", ())
        if isinstance(nested, tuple):
            pending.extend(item for item in nested if isinstance(item, BaseException))
        for linked in (current.__cause__, current.__context__):
            if isinstance(linked, BaseException):
                pending.append(linked)
    return kinds


def _resource_exhaustion_kind(exc: BaseException) -> str | None:
    kinds = sorted(_resource_exhaustion_kinds(exc))
    return kinds[0] if kinds else None


class _ResourceExhaustionPlugin:
    def __init__(self) -> None:
        self.kinds: set[str] = set()

    def pytest_runtest_makereport(self, item, call) -> None:
        del item
        if call.excinfo is None:
            return
        self.kinds.update(_resource_exhaustion_kinds(call.excinfo.value))


def _read_pytest_completion_sentinel(
    sentinel_path: Path,
    *,
    ran,
    required: bool,
) -> dict | None:
    """Authenticate proof that pytest itself returned an exit code."""

    if not sentinel_path.is_file():
        if required:
            raise RuntimeError("fresh pytest completion sentinel is missing")
        return None
    try:
        raw = sentinel_path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        expected_fields = {
            "schema",
            "completed",
            "pytest_exit_code",
            "sentinel_name",
            "resource_exhaustion_detected",
            "resource_exhaustion_kinds",
        }
        if not isinstance(payload, dict) or set(payload) != expected_fields:
            raise ValueError("fresh pytest completion sentinel fields mismatch")
        if payload["schema"] != _PYTEST_SENTINEL_SCHEMA:
            raise ValueError("fresh pytest completion sentinel schema mismatch")
        if payload["completed"] is not True:
            raise ValueError("fresh pytest completion sentinel must be completed")
        if payload["sentinel_name"] != sentinel_path.name:
            raise ValueError("fresh pytest completion sentinel identity mismatch")
        exit_code = payload["pytest_exit_code"]
        if type(exit_code) is not int:
            raise TypeError("fresh pytest sentinel exit code is invalid")
        timeout_kill_exit = bool(ran.timed_out and exit_code == 1)
        if exit_code != int(ran.returncode) and not timeout_kill_exit:
            raise ValueError("fresh pytest sentinel/process exit-code mismatch")
        resource_detected = payload["resource_exhaustion_detected"]
        resource_kinds = payload["resource_exhaustion_kinds"]
        if type(resource_detected) is not bool:
            raise TypeError("fresh pytest resource exhaustion flag must be exact bool")
        if not isinstance(resource_kinds, list) or any(
            not isinstance(kind, str) or not kind for kind in resource_kinds
        ):
            raise TypeError("fresh pytest resource exhaustion kinds are invalid")
        if resource_kinds != sorted(set(resource_kinds)):
            raise ValueError("fresh pytest resource exhaustion kinds are not canonical")
        if resource_detected != bool(resource_kinds):
            raise ValueError("fresh pytest resource exhaustion evidence is inconsistent")
        return {
            "schema": _PYTEST_SENTINEL_SCHEMA,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "pytest_exit_code": exit_code,
            "sentinel_name": payload["sentinel_name"],
            "resource_exhaustion_detected": resource_detected,
            "resource_exhaustion_kinds": resource_kinds,
        }
    finally:
        sentinel_path.unlink(missing_ok=True)


def _authenticated_fresh_worker_status(ran, *, sentinel_path: Path) -> tuple[str, dict | None]:
    """Classify one worker without crediting an unauthenticated rc=1."""

    if not ran.group_cleanup_verified:
        raise RuntimeError("fresh mutant worker process-group cleanup was not verified")
    sentinel = _read_pytest_completion_sentinel(
        sentinel_path,
        ran=ran,
        required=False,
    )
    if ran.timed_out:
        if (
            sentinel is not None
            and sentinel["pytest_exit_code"] == 1
            and sentinel["resource_exhaustion_detected"] is False
        ):
            return "killed", sentinel
        return "timeout", sentinel
    if sentinel is None:
        return "suspicious", None
    if sentinel["resource_exhaustion_detected"]:
        return "suspicious", sentinel
    return _EXIT_STATUS.get(int(ran.returncode), "suspicious"), sentinel


_FRESH_EXEC_PLAN_SCHEMA = (
    "error_coupling_simulator.harness.mutation_fresh_exec_plan.v3"
)


def _validated_plan_tests(
    value: object,
    *,
    context: str,
    allow_empty: bool,
) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(test, str) or not test for test in value
    ):
        raise TypeError(f"{context} tests must be nonempty strings")
    if not allow_empty and not value:
        raise ValueError(f"{context} tests must be nonempty")
    if value != sorted(set(value)):
        raise ValueError(f"{context} tests must be sorted and unique")
    return list(value)


def _validated_estimated_time(value: object, *, context: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < 0.0
    ):
        raise ValueError(f"invalid estimated test time for {context}")
    return float(value)


def _load_fresh_exec_plan(plan_path: Path) -> tuple[dict, str]:
    """Read and authenticate a fresh-exec plan before any mutant is credited."""

    raw = plan_path.read_bytes()
    plan = json.loads(raw.decode("utf-8"))
    expected_top = {
        "schema",
        "generated_catalog_sha256",
        "clean_control",
        "mutants",
    }
    if not isinstance(plan, dict) or set(plan) != expected_top:
        raise ValueError(
            "fresh-exec mutation plan fields mismatch: "
            f"missing={sorted(expected_top - set(plan)) if isinstance(plan, dict) else sorted(expected_top)}, "
            f"extra={sorted(set(plan) - expected_top) if isinstance(plan, dict) else []}"
        )
    if plan["schema"] != _FRESH_EXEC_PLAN_SCHEMA:
        raise ValueError("unsupported fresh-exec mutation plan schema")
    generated_catalog_sha256 = plan["generated_catalog_sha256"]
    if not isinstance(generated_catalog_sha256, str) or re.fullmatch(
        r"[0-9a-f]{64}", generated_catalog_sha256
    ) is None:
        raise ValueError("fresh-exec generated catalog sha256 is invalid")
    clean = plan["clean_control"]
    if not isinstance(clean, dict) or set(clean) != {
        "tests",
        "estimated_test_time",
    }:
        raise ValueError("fresh-exec clean-control fields mismatch")
    clean_tests = _validated_plan_tests(
        clean["tests"],
        context="fresh-exec clean-control",
        allow_empty=False,
    )
    clean_estimated = _validated_estimated_time(
        clean["estimated_test_time"],
        context="fresh-exec clean-control",
    )
    raw_mutants = plan["mutants"]
    if not isinstance(raw_mutants, list) or not raw_mutants:
        raise ValueError("fresh-exec mutation plan must contain mutants")

    normalized_rows: list[dict] = []
    names: set[str] = set()
    union_tests: set[str] = set()
    for raw_row in raw_mutants:
        if not isinstance(raw_row, dict) or set(raw_row) != {
            "name",
            "tests",
            "estimated_test_time",
        }:
            raise ValueError("fresh-exec mutant row fields mismatch")
        mutant = raw_row["name"]
        if not isinstance(mutant, str) or not mutant or mutant in names:
            raise ValueError(f"invalid or duplicate fresh-exec mutant: {mutant!r}")
        tests = _validated_plan_tests(
            raw_row["tests"],
            context=f"fresh-exec mutant {mutant}",
            allow_empty=True,
        )
        estimated = _validated_estimated_time(
            raw_row["estimated_test_time"],
            context=mutant,
        )
        names.add(mutant)
        union_tests.update(tests)
        normalized_rows.append(
            {"name": mutant, "tests": tests, "estimated_test_time": estimated}
        )
    if clean_tests != sorted(union_tests):
        raise ValueError("fresh-exec clean-control tests must equal mutant test union")
    return (
        {
            "schema": _FRESH_EXEC_PLAN_SCHEMA,
            "generated_catalog_sha256": generated_catalog_sha256,
            "clean_control": {
                "tests": clean_tests,
                "estimated_test_time": clean_estimated,
            },
            "mutants": normalized_rows,
        },
        hashlib.sha256(raw).hexdigest(),
    )


_GPU_CHECKPOINT_SCHEMA = (
    "error_coupling_simulator.harness.mutation_gpu_checkpoint.v4"
)


def _fresh_exec_plan_identity(plan: dict) -> str:
    """Hash only stable test/mutant identity, never measured durations."""

    payload = {
        "schema": plan["schema"],
        "generated_catalog_sha256": plan["generated_catalog_sha256"],
        "clean_control_tests": list(plan["clean_control"]["tests"]),
        "mutants": [
            {"name": row["name"], "tests": list(row["tests"])}
            for row in plan["mutants"]
        ],
    }
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _completion_sentinel_sha256(
    exit_code: int,
    *,
    sentinel_name: str,
    resource_exhaustion_kinds: tuple[str, ...] = (),
) -> str:
    kinds = sorted(set(resource_exhaustion_kinds))
    payload = {
        "schema": _PYTEST_SENTINEL_SCHEMA,
        "completed": True,
        "pytest_exit_code": exit_code,
        "sentinel_name": sentinel_name,
        "resource_exhaustion_detected": bool(kinds),
        "resource_exhaustion_kinds": kinds,
    }
    raw = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _gpu_worker_sentinel_name(tag: str, sequence_index: int) -> str:
    return f".{tag}_fresh_worker_{sequence_index}_completion.json"


def _validated_gpu_checkpoint_row(
    raw: object,
    *,
    sequence_index: int,
    plan_row: dict,
    tag: str,
    log_root: Path,
) -> dict:
    fields = {
        "sequence_index",
        "mutant",
        "tests",
        "estimated_test_time",
        "effective_timeout",
        "status",
        "process_executed",
        "completion_sentinel_authenticated",
        "completion_sentinel",
        "returncode",
        "timed_out",
        "group_cleanup_verified",
        "ok",
        "log",
        "log_sha256",
    }
    if not isinstance(raw, dict) or set(raw) != fields:
        raise ValueError("GPU mutation checkpoint worker fields mismatch")
    if raw["sequence_index"] != sequence_index:
        raise ValueError("GPU mutation checkpoint prefix is not contiguous")
    if raw["mutant"] != plan_row["name"] or raw["tests"] != plan_row["tests"]:
        raise ValueError("GPU mutation checkpoint mutant identity mismatch")
    _validated_estimated_time(
        raw["estimated_test_time"],
        context=f"GPU checkpoint {raw['mutant']}",
    )
    expected_log = _gpu_worker_log_name(tag, sequence_index, plan_row["name"])
    if raw["log"] != expected_log:
        raise ValueError("GPU mutation checkpoint worker log identity mismatch")
    log_hash = raw["log_sha256"]
    if not isinstance(log_hash, str) or re.fullmatch(r"[0-9a-f]{64}", log_hash) is None:
        raise ValueError("GPU mutation checkpoint worker log digest is invalid")
    root = log_root.resolve(strict=True)
    log_path = (root / expected_log).resolve(strict=True)
    if log_path.parent != root or not log_path.is_file():
        raise ValueError("GPU mutation checkpoint worker log escaped log root")
    if _sha256_file(log_path) != log_hash:
        raise ValueError("GPU mutation checkpoint worker log digest mismatch")
    if type(raw["process_executed"]) is not bool:
        raise TypeError("GPU mutation checkpoint process_executed must be exact bool")
    if type(raw["completion_sentinel_authenticated"]) is not bool:
        raise TypeError(
            "GPU mutation checkpoint sentinel authentication must be exact bool"
        )

    if not raw["process_executed"]:
        expected_none = (
            "effective_timeout",
            "completion_sentinel",
            "returncode",
            "timed_out",
            "group_cleanup_verified",
            "ok",
        )
        if plan_row["tests"] or raw["status"] != "no_tests":
            raise ValueError("GPU mutation checkpoint no-tests row is inconsistent")
        if raw["completion_sentinel_authenticated"] or any(
            raw[field] is not None for field in expected_none
        ):
            raise ValueError("GPU mutation checkpoint no-tests process evidence exists")
        return dict(raw)

    effective_timeout = raw["effective_timeout"]
    if (
        isinstance(effective_timeout, bool)
        or not isinstance(effective_timeout, (int, float))
        or not math.isfinite(float(effective_timeout))
        or float(effective_timeout) <= 0.0
    ):
        raise ValueError("GPU mutation checkpoint effective timeout is invalid")
    returncode = raw["returncode"]
    if type(returncode) is not int:
        raise TypeError("GPU mutation checkpoint returncode must be exact int")
    if type(raw["timed_out"]) is not bool or type(raw["ok"]) is not bool:
        raise TypeError("GPU mutation checkpoint process flags must be exact bool")
    if raw["group_cleanup_verified"] is not True:
        raise ValueError("GPU mutation checkpoint process cleanup was not verified")
    if raw["ok"] != (returncode == 0 and not raw["timed_out"]):
        raise ValueError("GPU mutation checkpoint process ok flag is inconsistent")

    sentinel = raw["completion_sentinel"]
    if sentinel is None or not raw["completion_sentinel_authenticated"]:
        raise ValueError(
            "GPU mutation checkpoint worker requires authenticated completion sentinel"
        )
    if not isinstance(sentinel, dict) or set(sentinel) != {
        "schema",
        "sha256",
        "pytest_exit_code",
        "sentinel_name",
        "resource_exhaustion_detected",
        "resource_exhaustion_kinds",
    }:
        raise ValueError("GPU mutation checkpoint sentinel fields mismatch")
    if sentinel["schema"] != _PYTEST_SENTINEL_SCHEMA:
        raise ValueError("GPU mutation checkpoint sentinel schema mismatch")
    sentinel_exit_code = sentinel["pytest_exit_code"]
    if type(sentinel_exit_code) is not int:
        raise TypeError("GPU mutation checkpoint sentinel exit code is invalid")
    authenticated_timeout_kill = bool(
        raw["timed_out"]
        and sentinel_exit_code == 1
        and raw["status"] == "killed"
    )
    if sentinel_exit_code != returncode and not authenticated_timeout_kill:
        raise ValueError("GPU mutation checkpoint sentinel/process rc mismatch")
    expected_sentinel_name = _gpu_worker_sentinel_name(tag, sequence_index)
    if sentinel["sentinel_name"] != expected_sentinel_name:
        raise ValueError("GPU mutation checkpoint sentinel identity mismatch")
    if sentinel["resource_exhaustion_detected"] is not False or sentinel[
        "resource_exhaustion_kinds"
    ] != []:
        raise ValueError("GPU mutation checkpoint cannot resume resource exhaustion")
    if raw["timed_out"] and not authenticated_timeout_kill:
        raise ValueError(
            "GPU mutation checkpoint timed-out worker is not an authenticated kill"
        )
    if sentinel["sha256"] != _completion_sentinel_sha256(
        sentinel_exit_code,
        sentinel_name=expected_sentinel_name,
    ):
        raise ValueError("GPU mutation checkpoint sentinel digest mismatch")

    status_exit_code = sentinel_exit_code if raw["timed_out"] else returncode
    derived_status = _EXIT_STATUS.get(status_exit_code, "suspicious")
    if raw["status"] != derived_status:
        raise ValueError("GPU mutation checkpoint worker status is inconsistent")
    return dict(raw)


def _load_gpu_checkpoint(
    checkpoint_path: Path,
    *,
    tag: str,
    input_snapshot_sha256: str,
    plan: dict,
    plan_identity_sha256: str,
    raw_plan_sha256: str,
    execution_policy: dict,
    runtime_fingerprint: dict,
) -> tuple[dict[str, str], list[dict], list[str]]:
    _validate_gpu_execution_policy(execution_policy)
    if not checkpoint_path.is_file():
        return {}, [], [raw_plan_sha256]
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    fields = {
        "schema",
        "tag",
        "lane",
        "input_snapshot_sha256",
        "plan_schema",
        "plan_identity_sha256",
        "generated_catalog_sha256",
        "plan_mutant_count",
        "execution_policy",
        "runtime_fingerprint",
        "raw_plan_sha256_history",
        "completed_prefix",
    }
    if not isinstance(checkpoint, dict) or set(checkpoint) != fields:
        raise ValueError("GPU mutation checkpoint fields mismatch")
    if checkpoint["schema"] != _GPU_CHECKPOINT_SCHEMA:
        raise ValueError("unsupported GPU mutation checkpoint schema")
    if checkpoint["tag"] != tag or checkpoint["lane"] != "gpu_serial":
        raise ValueError("GPU mutation checkpoint batch identity mismatch")
    if checkpoint["input_snapshot_sha256"] != input_snapshot_sha256:
        raise RuntimeError("GPU mutation checkpoint input snapshot mismatch")
    if _canonical_json_bytes(checkpoint["execution_policy"]) != _canonical_json_bytes(
        execution_policy
    ):
        raise RuntimeError("GPU mutation checkpoint execution policy mismatch")
    if _canonical_json_bytes(checkpoint["runtime_fingerprint"]) != _canonical_json_bytes(
        runtime_fingerprint
    ):
        raise RuntimeError("GPU mutation checkpoint runtime fingerprint mismatch")
    if (
        checkpoint["plan_schema"] != plan["schema"]
        or checkpoint["plan_identity_sha256"] != plan_identity_sha256
        or checkpoint["generated_catalog_sha256"]
        != plan["generated_catalog_sha256"]
        or checkpoint["plan_mutant_count"] != len(plan["mutants"])
    ):
        raise RuntimeError("GPU mutation checkpoint semantic plan mismatch")
    if not isinstance(checkpoint["generated_catalog_sha256"], str) or re.fullmatch(
        r"[0-9a-f]{64}", checkpoint["generated_catalog_sha256"]
    ) is None:
        raise ValueError("GPU mutation checkpoint generated catalog digest is invalid")
    history = checkpoint["raw_plan_sha256_history"]
    if (
        not isinstance(history, list)
        or any(
            not isinstance(value, str)
            or re.fullmatch(r"[0-9a-f]{64}", value) is None
            for value in history
        )
        or history != sorted(set(history))
    ):
        raise ValueError("GPU mutation checkpoint raw plan history is invalid")
    history = sorted(set(history) | {raw_plan_sha256})
    prefix = checkpoint["completed_prefix"]
    if not isinstance(prefix, list) or len(prefix) > len(plan["mutants"]):
        raise ValueError("GPU mutation checkpoint completed prefix is invalid")
    rows: dict[str, str] = {}
    normalized: list[dict] = []
    for index, raw_row in enumerate(prefix, start=1):
        row = _validated_gpu_checkpoint_row(
            raw_row,
            sequence_index=index,
            plan_row=plan["mutants"][index - 1],
            tag=tag,
            log_root=checkpoint_path.parent,
        )
        rows[row["mutant"]] = row["status"]
        normalized.append(row)
    return rows, normalized, history


def _write_gpu_checkpoint(
    checkpoint_path: Path,
    *,
    tag: str,
    input_snapshot_sha256: str,
    plan: dict,
    plan_identity_sha256: str,
    execution_policy: dict,
    runtime_fingerprint: dict,
    raw_plan_sha256_history: list[str],
    completed_prefix: list[dict],
) -> None:
    _validate_gpu_execution_policy(execution_policy)
    write_json_atomic(
        checkpoint_path,
        {
            "schema": _GPU_CHECKPOINT_SCHEMA,
            "tag": tag,
            "lane": "gpu_serial",
            "input_snapshot_sha256": input_snapshot_sha256,
            "plan_schema": plan["schema"],
            "plan_identity_sha256": plan_identity_sha256,
            "generated_catalog_sha256": plan["generated_catalog_sha256"],
            "plan_mutant_count": len(plan["mutants"]),
            "execution_policy": execution_policy,
            "runtime_fingerprint": runtime_fingerprint,
            "raw_plan_sha256_history": sorted(set(raw_plan_sha256_history)),
            "completed_prefix": completed_prefix,
        },
    )


def _effective_worker_timeout(
    *,
    explicit_timeout: float | None,
    estimated_test_time: float,
    timeout_multiplier: float,
    timeout_constant: float,
    contention_factor: int = 1,
) -> float:
    if type(contention_factor) is not int or contention_factor <= 0:
        raise ValueError("mutation timeout contention factor must be a positive integer")
    if explicit_timeout is not None:
        value = float(explicit_timeout)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError("explicit mutation timeout must be finite and positive")
        return value
    value = (
        (estimated_test_time + timeout_constant)
        * timeout_multiplier
        * contention_factor
    )
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("effective mutation timeout must be finite and positive")
    return value


def _fresh_pytest_basetemp(sentinel_path: Path) -> Path:
    return sentinel_path.with_name(f"{sentinel_path.name}.pytest_tmp")


def _fresh_pytest_command(tests: list[str], *, sentinel_path: Path) -> list[str]:
    if not tests:
        raise ValueError("fresh pytest execution requires selected tests")
    return [
        sys.executable,
        "tests/harness/mutation.py",
        "--run-fresh-pytest",
        str(sentinel_path),
        "--rootdir=.",
        "--tb=native",
        "-x",
        "-q",
        "-o",
        "addopts=",
        "-p",
        "no:randomly",
        "-p",
        "no:random-order",
        "-p",
        "no:cacheprovider",
        f"--basetemp={_fresh_pytest_basetemp(sentinel_path)}",
        *tests,
    ]


def run_fresh_pytest_worker(sentinel_path: Path, pytest_args: list[str]) -> int:
    """Run pytest in the mutant tree and attest only a normal pytest return."""

    import pytest

    sentinel_path.unlink(missing_ok=True)
    resource_plugin = _ResourceExhaustionPlugin()
    exit_code = int(pytest.main(pytest_args, plugins=[resource_plugin]))
    resource_kinds = sorted(resource_plugin.kinds)
    write_json_atomic(
        sentinel_path,
        {
            "schema": _PYTEST_SENTINEL_SCHEMA,
            "completed": True,
            "pytest_exit_code": exit_code,
            "sentinel_name": sentinel_path.name,
            "resource_exhaustion_detected": bool(resource_kinds),
            "resource_exhaustion_kinds": resource_kinds,
        },
    )
    return exit_code


def _prepare_gpu_fresh_exec(
    *,
    tag: str,
    env: dict[str, str],
    timeout: float | None,
    log: Path,
    plan_path: Path,
    checkpoint_path: Path,
    input_snapshot_sha256: str,
    execution_policy: dict,
    runtime_fingerprint: dict,
    modules: tuple[str, ...] = (),
) -> dict[str, object]:
    """Prepare the plan and validate resume state in the leased GPU environment."""

    env = lane_environment(env, lane="gpu_serial")
    _validate_gpu_execution_policy(execution_policy)
    if _canonical_json_bytes(execution_policy["bound_environment"]) != (
        _canonical_json_bytes(_gpu_bound_environment(env))
    ):
        raise ValueError("GPU execution policy does not bind the preparation environment")
    plan_path.unlink(missing_ok=True)
    prepare = proc.run(
        [
            sys.executable,
            str(REPO / "tests" / "harness" / "mutation.py"),
            "--prepare-fresh-exec",
            str(plan_path),
            *modules,
        ],
        cwd=str(REPO),
        env=env,
        timeout=timeout,
        log_path=str(log),
        append=True,
    )
    prepare_evidence = _require_process_ok("fresh-exec mutation preparation", prepare)
    if not plan_path.is_file():
        raise RuntimeError("fresh-exec mutation preparation produced no plan")
    try:
        plan, plan_sha256 = _load_fresh_exec_plan(plan_path)
    finally:
        plan_path.unlink(missing_ok=True)
    plan_identity_sha256 = _fresh_exec_plan_identity(plan)
    rows, resumed_workers, raw_plan_sha256_history = _load_gpu_checkpoint(
        checkpoint_path,
        tag=tag,
        input_snapshot_sha256=input_snapshot_sha256,
        plan=plan,
        plan_identity_sha256=plan_identity_sha256,
        raw_plan_sha256=plan_sha256,
        execution_policy=execution_policy,
        runtime_fingerprint=runtime_fingerprint,
    )
    return {
        "tag": tag,
        "input_snapshot_sha256": input_snapshot_sha256,
        "prepare": prepare_evidence,
        "plan": plan,
        "plan_sha256": plan_sha256,
        "plan_identity_sha256": plan_identity_sha256,
        "execution_policy": copy.deepcopy(execution_policy),
        "runtime_fingerprint": copy.deepcopy(runtime_fingerprint),
        "rows": rows,
        "resumed_workers": resumed_workers,
        "raw_plan_sha256_history": raw_plan_sha256_history,
    }


def _remove_fresh_basetemp(sentinel_path: Path) -> None:
    basetemp = _fresh_pytest_basetemp(sentinel_path)
    if basetemp.is_symlink():
        basetemp.unlink()
    elif basetemp.exists():
        shutil.rmtree(basetemp)
    if basetemp.exists() or basetemp.is_symlink():
        raise RuntimeError(f"fresh pytest basetemp survived cleanup: {basetemp}")


def _gpu_clean_log_name(tag: str, replica_index: int) -> str:
    return f"{tag}_clean_{replica_index:02d}.log"


def _run_gpu_clean_replica(
    *,
    tag: str,
    replica_index: int,
    tests: list[str],
    estimated_test_time: float,
    effective_timeout: float,
    env: dict[str, str],
    plan_path: Path,
    log_root: Path,
    start_barrier: threading.Barrier,
    cancellation_event: threading.Event,
) -> dict:
    clean_env = dict(env)
    clean_env["MUTANT_UNDER_TEST"] = ""
    sentinel_path = plan_path.with_name(
        f".{tag}_fresh_clean_{replica_index}_completion.json"
    )
    log_path = log_root / _gpu_clean_log_name(tag, replica_index)
    sentinel_path.unlink(missing_ok=True)
    log_path.unlink(missing_ok=True)
    _remove_fresh_basetemp(sentinel_path)
    try:
        start_barrier.wait(timeout=min(max(effective_timeout, 1.0), 60.0))
        process_started_ns = time.monotonic_ns()
        ran = proc.run(
            _fresh_pytest_command(tests, sentinel_path=sentinel_path),
            cwd=str(REPO / "mutants"),
            env=clean_env,
            timeout=effective_timeout,
            log_path=str(log_path),
            cancellation_event=cancellation_event,
        )
        process_finished_ns = time.monotonic_ns()
        sentinel = _read_pytest_completion_sentinel(
            sentinel_path,
            ran=ran,
            required=True,
        )
        assert sentinel is not None
        if sentinel["resource_exhaustion_detected"]:
            raise RuntimeError(
                "fresh-exec clean admission detected resource exhaustion: "
                + ",".join(sentinel["resource_exhaustion_kinds"])
            )
        process = _require_process_ok(
            f"fresh-exec clean control failed for replica {replica_index}",
            ran,
        )
        return {
            "replica_index": replica_index,
            "tests": tests,
            "estimated_test_time": estimated_test_time,
            "effective_timeout": effective_timeout,
            "process_started_monotonic_ns": process_started_ns,
            "process_finished_monotonic_ns": process_finished_ns,
            "completion_sentinel": sentinel,
            **process,
            "log": log_path.name,
            "log_sha256": _durable_file_sha256(log_path),
        }
    except BaseException:
        cancellation_event.set()
        raise
    finally:
        _remove_fresh_basetemp(sentinel_path)


def _run_gpu_mutant_worker(
    *,
    tag: str,
    sequence_index: int,
    plan_row: dict,
    env: dict[str, str],
    timeout: float | None,
    timeout_multiplier: float,
    timeout_constant: float,
    contention_factor: int,
    plan_path: Path,
    log_root: Path,
    cancellation_event: threading.Event,
) -> dict:
    mutant = plan_row["name"]
    tests = plan_row["tests"]
    estimated = plan_row["estimated_test_time"]
    worker_log_path = log_root / _gpu_worker_log_name(
        tag,
        sequence_index,
        mutant,
    )
    worker_log_path.unlink(missing_ok=True)
    if not tests:
        write_json_atomic(
            worker_log_path,
            {
                "schema": (
                    "error_coupling_simulator.harness."
                    "mutation_no_tests_evidence.v1"
                ),
                "mutant": mutant,
                "status": "no_tests",
                "tests": [],
            },
        )
        return {
            "sequence_index": sequence_index,
            "mutant": mutant,
            "tests": [],
            "estimated_test_time": estimated,
            "effective_timeout": None,
            "status": "no_tests",
            "process_executed": False,
            "completion_sentinel_authenticated": False,
            "completion_sentinel": None,
            "returncode": None,
            "timed_out": None,
            "group_cleanup_verified": None,
            "ok": None,
            "log": worker_log_path.name,
            "log_sha256": _durable_file_sha256(worker_log_path),
        }

    worker_env = dict(env)
    worker_env["MUTANT_UNDER_TEST"] = mutant
    worker_sentinel_path = plan_path.with_name(
        _gpu_worker_sentinel_name(tag, sequence_index)
    )
    worker_sentinel_path.unlink(missing_ok=True)
    _remove_fresh_basetemp(worker_sentinel_path)
    per_mutant_timeout = _effective_worker_timeout(
        explicit_timeout=timeout,
        estimated_test_time=estimated,
        timeout_multiplier=timeout_multiplier,
        timeout_constant=timeout_constant,
        contention_factor=contention_factor,
    )
    try:
        ran = proc.run(
            _fresh_pytest_command(tests, sentinel_path=worker_sentinel_path),
            cwd=str(REPO / "mutants"),
            env=worker_env,
            timeout=per_mutant_timeout,
            log_path=str(worker_log_path),
            cancellation_event=cancellation_event,
        )
        status, worker_sentinel = _authenticated_fresh_worker_status(
            ran,
            sentinel_path=worker_sentinel_path,
        )
        row = {
            "sequence_index": sequence_index,
            "mutant": mutant,
            "tests": tests,
            "estimated_test_time": estimated,
            "effective_timeout": per_mutant_timeout,
            "status": status,
            "process_executed": True,
            "completion_sentinel_authenticated": worker_sentinel is not None,
            "completion_sentinel": worker_sentinel,
            **_process_evidence(ran),
            "log": worker_log_path.name,
            "log_sha256": _durable_file_sha256(worker_log_path),
        }
        return row
    finally:
        _remove_fresh_basetemp(worker_sentinel_path)


def _gpu_worker_row_is_resumable(row: dict) -> bool:
    if not row["process_executed"]:
        return row["status"] == "no_tests"
    sentinel = row["completion_sentinel"]
    authenticated_timeout_kill = bool(
        row["status"] == "killed"
        and row["timed_out"] is True
        and isinstance(sentinel, dict)
        and sentinel.get("pytest_exit_code") == 1
    )
    return bool(
        row["group_cleanup_verified"] is True
        and (row["timed_out"] is False or authenticated_timeout_kill)
        and row["completion_sentinel_authenticated"] is True
        and isinstance(sentinel, dict)
        and sentinel["resource_exhaustion_detected"] is False
    )


def _run_gpu_fresh_exec(
    *,
    tag: str,
    env: dict[str, str],
    timeout: float | None,
    log: Path,
    plan_path: Path,
    checkpoint_path: Path,
    input_snapshot_sha256: str,
    execution_policy: dict,
    runtime_fingerprint: dict,
    timeout_multiplier: float,
    timeout_constant: float,
    modules: tuple[str, ...] = (),
    prepared: dict[str, object] | None = None,
) -> tuple[dict[str, str], dict[str, dict | list]]:
    """Run concurrent clean admission, then fixed CUDA mutant waves."""

    env = lane_environment(env, lane="gpu_serial")
    if prepared is None:
        prepared = _prepare_gpu_fresh_exec(
            tag=tag,
            env=env,
            timeout=timeout,
            log=log,
            plan_path=plan_path,
            checkpoint_path=checkpoint_path,
            input_snapshot_sha256=input_snapshot_sha256,
            execution_policy=execution_policy,
            runtime_fingerprint=runtime_fingerprint,
            modules=modules,
        )
    if (
        prepared.get("tag") != tag
        or prepared.get("input_snapshot_sha256") != input_snapshot_sha256
        or _canonical_json_bytes(prepared.get("execution_policy"))
        != _canonical_json_bytes(execution_policy)
        or _canonical_json_bytes(prepared.get("runtime_fingerprint"))
        != _canonical_json_bytes(runtime_fingerprint)
    ):
        raise ValueError("prepared GPU mutation plan identity mismatch")
    plan = prepared.get("plan")
    rows = prepared.get("rows")
    resumed_workers = prepared.get("resumed_workers")
    raw_plan_sha256_history = prepared.get("raw_plan_sha256_history")
    if not isinstance(plan, dict) or not isinstance(rows, dict):
        raise TypeError("prepared GPU mutation plan payload is invalid")
    if not isinstance(resumed_workers, list) or not isinstance(
        raw_plan_sha256_history, list
    ):
        raise TypeError("prepared GPU mutation checkpoint payload is invalid")
    plan_sha256 = prepared.get("plan_sha256")
    plan_identity_sha256 = prepared.get("plan_identity_sha256")
    if not isinstance(plan_sha256, str) or not isinstance(
        plan_identity_sha256, str
    ):
        raise TypeError("prepared GPU mutation plan digests are invalid")
    jobs = _validate_gpu_execution_policy(execution_policy)
    if _canonical_json_bytes(execution_policy["bound_environment"]) != (
        _canonical_json_bytes(_gpu_bound_environment(env))
    ):
        raise ValueError("GPU execution policy does not bind the worker environment")
    if float(execution_policy["timeout_multiplier"]) != float(timeout_multiplier):
        raise ValueError("GPU execution policy timeout multiplier mismatch")
    if float(execution_policy["timeout_constant"]) != float(timeout_constant):
        raise ValueError("GPU execution policy timeout constant mismatch")
    bound_timeout = execution_policy["explicit_timeout"]
    if (bound_timeout is None) != (timeout is None) or (
        bound_timeout is not None and float(bound_timeout) != float(timeout)
    ):
        raise ValueError("GPU execution policy explicit timeout mismatch")
    evidence: dict[str, dict | list] = {
        "prepare": prepared["prepare"],
        "workers": [],
    }
    clean = plan["clean_control"]
    clean_timeout = _effective_worker_timeout(
        explicit_timeout=timeout,
        estimated_test_time=clean["estimated_test_time"],
        timeout_multiplier=timeout_multiplier,
        timeout_constant=timeout_constant,
        contention_factor=jobs,
    )
    evidence["plan"] = {
        "schema": plan["schema"],
        "sha256": plan_sha256,
        "identity_sha256": plan_identity_sha256,
        "generated_catalog_sha256": plan["generated_catalog_sha256"],
        "mutant_count": len(plan["mutants"]),
        "clean_control_tests": clean["tests"],
        "execution_policy": copy.deepcopy(execution_policy),
        "runtime_fingerprint": copy.deepcopy(runtime_fingerprint),
    }
    clean_start_barrier = threading.Barrier(jobs)
    clean_cancellation = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=jobs,
        thread_name_prefix=f"{tag}-clean",
    ) as executor:
        clean_futures = [
            executor.submit(
                _run_gpu_clean_replica,
                tag=tag,
                replica_index=replica_index,
                tests=clean["tests"],
                estimated_test_time=clean["estimated_test_time"],
                effective_timeout=clean_timeout,
                env=env,
                plan_path=plan_path,
                log_root=checkpoint_path.parent,
                start_barrier=clean_start_barrier,
                cancellation_event=clean_cancellation,
            )
            for replica_index in range(1, jobs + 1)
        ]
        clean_replicas = [future.result() for future in clean_futures]
    latest_clean_start = max(
        replica["process_started_monotonic_ns"] for replica in clean_replicas
    )
    earliest_clean_finish = min(
        replica["process_finished_monotonic_ns"] for replica in clean_replicas
    )
    clean_overlap_ns = earliest_clean_finish - latest_clean_start
    if jobs > 1 and clean_overlap_ns <= 0:
        raise RuntimeError("fresh-exec clean controls did not overlap in process time")
    primary_clean = clean_replicas[0]
    evidence["clean_control"] = {
        "tests": clean["tests"],
        "estimated_test_time": clean["estimated_test_time"],
        "effective_timeout": clean_timeout,
        "replica_count": jobs,
        "configured_max_concurrent_replicas": jobs,
        "concurrency_admission_verified": True,
        "all_replica_overlap_ns": max(0, clean_overlap_ns),
        "replicas": clean_replicas,
        "completion_sentinel": primary_clean["completion_sentinel"],
        "returncode": primary_clean["returncode"],
        "timed_out": primary_clean["timed_out"],
        "group_cleanup_verified": primary_clean["group_cleanup_verified"],
        "ok": primary_clean["ok"],
    }

    evidence["workers"] = list(resumed_workers)
    evidence["checkpoint"] = {
        "path": str(checkpoint_path),
        "resumed_prefix_count": len(resumed_workers),
        "completed_prefix_count": len(resumed_workers),
        "raw_plan_sha256_history": raw_plan_sha256_history,
    }
    workers = evidence["workers"]
    assert isinstance(workers, list)
    remaining = list(enumerate(plan["mutants"], start=1))[len(resumed_workers) :]
    for wave_start in range(0, len(remaining), jobs):
        wave = remaining[wave_start : wave_start + jobs]
        wave_cancellation = threading.Event()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=jobs,
            thread_name_prefix=f"{tag}-mutant",
        ) as executor:
            futures = [
                executor.submit(
                    _run_gpu_mutant_worker,
                    tag=tag,
                    sequence_index=index,
                    plan_row=raw,
                    env=env,
                    timeout=timeout,
                    timeout_multiplier=timeout_multiplier,
                    timeout_constant=timeout_constant,
                    contention_factor=jobs,
                    plan_path=plan_path,
                    log_root=checkpoint_path.parent,
                    cancellation_event=wave_cancellation,
                )
                for index, raw in wave
            ]
            outcomes: list[dict | BaseException | None] = [None] * len(futures)
            positions = {future: position for position, future in enumerate(futures)}
            failure_trigger: tuple[int, dict | BaseException] | None = None
            for future in concurrent.futures.as_completed(futures):
                position = positions[future]
                sequence_index = wave[position][0]
                try:
                    outcome = future.result()
                    outcomes[position] = outcome
                    if not _gpu_worker_row_is_resumable(outcome):
                        if failure_trigger is None:
                            failure_trigger = (sequence_index, outcome)
                        wave_cancellation.set()
                except BaseException as exc:
                    if failure_trigger is None:
                        failure_trigger = (sequence_index, exc)
                    wave_cancellation.set()
                    outcomes[position] = exc

        failure_index: int | None = None
        committed = False
        for (index, raw), outcome in zip(wave, outcomes, strict=True):
            if outcome is None:
                raise RuntimeError("GPU mutant worker produced no outcome")
            if isinstance(outcome, BaseException):
                failure_index = index
                break
            if not _gpu_worker_row_is_resumable(outcome):
                failure_index = index
                break
            rows[raw["name"]] = outcome["status"]
            workers.append(outcome)
            committed = True

        if committed:
            _write_gpu_checkpoint(
                checkpoint_path,
                tag=tag,
                input_snapshot_sha256=input_snapshot_sha256,
                plan=plan,
                plan_identity_sha256=plan_identity_sha256,
                execution_policy=execution_policy,
                runtime_fingerprint=runtime_fingerprint,
                raw_plan_sha256_history=raw_plan_sha256_history,
                completed_prefix=workers,
            )
            evidence["checkpoint"]["completed_prefix_count"] = len(workers)
        if failure_trigger is not None:
            trigger_index, trigger = failure_trigger
            evidence["checkpoint"]["resume_blocked_at_sequence_index"] = failure_index
            evidence["failure_trigger_sequence_index"] = trigger_index
            if isinstance(trigger, BaseException):
                raise trigger
            evidence["failed_worker"] = trigger
            sentinel = trigger.get("completion_sentinel")
            resource_kinds = (
                sentinel.get("resource_exhaustion_kinds")
                if isinstance(sentinel, dict)
                else None
            )
            raise RuntimeError(
                f"GPU mutant worker {trigger_index} produced non-resumable evidence: "
                f"status={trigger.get('status')!r}, "
                f"returncode={trigger.get('returncode')!r}, "
                f"timed_out={trigger.get('timed_out')!r}, "
                f"resource_exhaustion_kinds={resource_kinds!r}; "
                f"contiguous resume blocked at worker {failure_index}"
            )
    return rows, evidence


def prepare_fresh_exec_plan(
    plan_path: Path,
    *,
    modules: tuple[str, ...],
) -> None:
    """Build mutmut trampolines and test associations, but execute no mutant in this process."""

    if not modules or any(not isinstance(module, str) or not module for module in modules):
        raise ValueError("fresh-exec preparation requires source modules")

    import mutmut as mutmut_state
    import mutmut.__main__ as mutmut_main

    os.environ["MUTANT_UNDER_TEST"] = "mutant_generation"
    mutmut_main.Config.ensure_loaded()
    (REPO / "mutants").mkdir(parents=True, exist_ok=True)
    mutmut_main.copy_src_dir()
    mutmut_main.copy_also_copy_files()
    mutmut_main.setup_source_paths()
    mutmut_main.store_lines_covered_by_tests()
    mutmut_main.create_mutants(1)

    runner = mutmut_main.PytestRunner()
    runner.prepare_main_test_run()
    mutmut_main.collect_or_load_stats(runner)
    mutants, mutation_data = mutmut_main.collect_source_file_mutation_data(
        mutant_names=[]
    )
    mutmut_main._check_test_to_mutant_associations(mutation_data)

    os.environ["MUTANT_UNDER_TEST"] = ""
    if runner.run_tests(mutant_name=None, tests=set()) != 0:
        raise RuntimeError("fresh-exec preparation clean tests failed")
    mutmut_main.run_forced_fail_test(runner)

    plan_rows = []
    clean_tests: set[str] = set()
    for _data, mutant, _result in mutants:
        tests = sorted(mutmut_main.tests_for_mutant_names([mutant]))
        estimated = sum(mutmut_state.duration_by_test[test] for test in tests)
        clean_tests.update(tests)
        plan_rows.append(
            {
                "name": mutant,
                "tests": tests,
                "estimated_test_time": estimated,
            }
        )
    if not plan_rows:
        raise RuntimeError("fresh-exec preparation generated no mutants")
    ordered_clean_tests = sorted(clean_tests)
    if not ordered_clean_tests:
        raise RuntimeError("fresh-exec preparation associated no tests with mutants")
    clean_estimated = sum(
        mutmut_state.duration_by_test[test] for test in ordered_clean_tests
    )
    placeholder_rows = {row["name"]: "not_checked" for row in plan_rows}
    generated_catalog = build_semantic_mutant_catalog(
        placeholder_rows,
        modules=modules,
        repo=REPO,
    )
    write_json_atomic(
        plan_path,
        {
            "schema": _FRESH_EXEC_PLAN_SCHEMA,
            "generated_catalog_sha256": _semantic_catalog_sha256(
                generated_catalog
            ),
            "clean_control": {
                "tests": ordered_clean_tests,
                "estimated_test_time": clean_estimated,
            },
            "mutants": plan_rows,
        },
    )


def _resolve_registry_reference(owner: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise TypeError("mutation registry reference must be a nonempty path")
    raw = Path(value)
    candidates = (raw,) if raw.is_absolute() else (owner.parent / raw, REPO / raw)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"mutation registry reference not found: {value!r}")


def load_mutation_suite(suite_path: Path) -> dict:
    """Load and validate an immutable suite plan with an exact module partition."""

    path = suite_path.resolve()
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema") != "error_coupling_simulator.harness.mutation_suite.v1":
        raise ValueError("unsupported mutation suite schema")
    suite_bar = _configured_knob(
        suite,
        "mutation_gate",
        "kill_rate_bar",
        0.90,
        float,
    )
    _validate_mutation_gate_knobs(
        bar=suite_bar,
        timeout_multiplier=1.0,
        timeout_constant=0.0,
    )
    raw_batches = suite.get("batches")
    if not isinstance(raw_batches, list) or not raw_batches:
        raise ValueError("mutation suite requires nonempty batches")
    coverage_path = _resolve_registry_reference(path, suite.get("coverage_registry"))
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    coverage_modules = coverage.get("reconcile_modules")
    if not isinstance(coverage_modules, list) or not coverage_modules:
        raise ValueError("coverage registry requires reconcile_modules")
    if len(set(coverage_modules)) != len(coverage_modules):
        raise ValueError("coverage registry contains duplicate modules")
    suite_semantic_value = suite.get("semantic_dispositions")
    suite_semantic_path = (
        None
        if suite_semantic_value is None
        else _resolve_registry_reference(path, suite_semantic_value)
    )
    if suite_semantic_path is not None:
        _preflight_semantic_disposition_document(suite_semantic_path, repo=REPO)

    names: set[str] = set()
    registry_paths: set[Path] = set()
    owned_modules: set[str] = set()
    batches: list[dict] = []
    for raw in raw_batches:
        if not isinstance(raw, dict):
            raise TypeError("mutation suite batches must be objects")
        name = raw.get("name")
        lane = raw.get("lane")
        jobs = raw.get("jobs")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError(f"invalid or duplicate mutation batch name: {name!r}")
        if lane not in {"cpu_parallel", "gpu_serial"}:
            raise ValueError(f"unknown mutation lane: {lane!r}")
        if isinstance(jobs, bool) or not isinstance(jobs, int) or jobs <= 0:
            raise ValueError(f"mutation batch jobs must be positive: {name}")
        if lane == "gpu_serial" and jobs > 4:
            raise ValueError("gpu_serial mutation permits at most 4 jobs")
        registry_path = _resolve_registry_reference(path, raw.get("registry"))
        if registry_path in registry_paths:
            raise ValueError(f"duplicate mutation batch registry: {registry_path}")
        registry_doc = json.loads(registry_path.read_text(encoding="utf-8"))
        if registry_doc.get("schema") != "error_coupling_simulator.harness.mutation_batch.v1":
            raise ValueError(f"unsupported mutation batch schema: {registry_path}")
        if registry_doc.get("lane") != lane:
            raise ValueError(f"suite/child lane mismatch: {name}")
        if bool(registry_doc.get("requires_gpu")) != (lane == "gpu_serial"):
            raise ValueError(f"suite/child requires_gpu mismatch: {name}")
        child_bar = _configured_knob(
            registry_doc,
            "mutation_gate",
            "kill_rate_bar",
            0.90,
            float,
        )
        _validate_mutation_gate_knobs(
            bar=child_bar,
            timeout_multiplier=1.0,
            timeout_constant=0.0,
        )
        if child_bar != suite_bar:
            raise ValueError(f"suite/child kill-rate bar mismatch: {name}")
        child_semantic_path = _semantic_dispositions_path(
            registry_doc,
            repo=REPO,
        )
        if child_semantic_path != suite_semantic_path:
            raise ValueError(f"suite/child semantic dispositions mismatch: {name}")
        configured_jobs = (
            ((registry_doc.get("harness") or {}).get("mutation_gate") or {}).get("jobs")
        )
        if configured_jobs is not None and configured_jobs != jobs:
            raise ValueError(f"suite/child jobs mismatch: {name}")
        modules = registry_doc.get("reconcile_modules")
        if not isinstance(modules, list) or not modules or len(set(modules)) != len(modules):
            raise ValueError(f"batch requires unique reconcile_modules: {name}")
        overlap = owned_modules & set(modules)
        if overlap:
            raise ValueError(f"mutation batch modules overlap: {sorted(overlap)}")
        owned_modules.update(modules)
        names.add(name)
        registry_paths.add(registry_path)
        batches.append(
            {
                "name": name,
                "lane": lane,
                "jobs": jobs,
                "registry_path": registry_path,
                "registry_doc": registry_doc,
            }
        )
    expected_modules = set(coverage_modules)
    if owned_modules != expected_modules:
        raise ValueError(
            "mutation suite module union mismatch: "
            f"missing={sorted(expected_modules - owned_modules)}, "
            f"extra={sorted(owned_modules - expected_modules)}"
        )
    return {
        "path": path,
        "suite_doc": suite,
        "coverage_path": coverage_path,
        "coverage_doc": coverage,
        "semantic_dispositions_path": suite_semantic_path,
        "batches": batches,
    }


def _suite_snapshot_paths(plan: dict) -> tuple[str | Path, ...]:
    paths: list[str | Path] = [plan["path"], plan["coverage_path"]]
    if plan.get("semantic_dispositions_path") is not None:
        paths.append(plan["semantic_dispositions_path"])
    for batch in plan["batches"]:
        paths.extend(
            _batch_snapshot_paths(batch["registry_path"], batch["registry_doc"])
        )
    return tuple(paths)


def _atomic_verified_copy(source: Path, destination: Path) -> None:
    """Publish an exact file copy via same-directory atomic replacement."""

    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.unlink(missing_ok=True)
    try:
        shutil.copy2(source, temporary)
        if temporary.read_bytes() != source.read_bytes():
            raise RuntimeError(
                f"atomic backup copy verification failed: {source} -> {destination}"
            )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _recover_stale_setup_state(
    *,
    setup: Path,
    backup: Path,
    absent_marker: Path,
) -> None:
    """Restore setup.cfg state left by a previously hard-killed run."""

    backup.with_name(f".{backup.name}.tmp").unlink(missing_ok=True)
    setup.with_name(f".{setup.name}.tmp").unlink(missing_ok=True)
    if backup.exists() and absent_marker.exists():
        raise RuntimeError("conflicting stale setup.cfg recovery markers")
    if backup.exists():
        if not backup.is_file():
            raise RuntimeError(f"invalid stale setup.cfg backup: {backup}")
        _atomic_verified_copy(backup, setup)
        backup.unlink()
    elif absent_marker.exists():
        setup.unlink(missing_ok=True)
        absent_marker.unlink()


def _begin_setup_override(
    *,
    setup: Path,
    backup: Path,
    absent_marker: Path,
) -> bool:
    _recover_stale_setup_state(
        setup=setup,
        backup=backup,
        absent_marker=absent_marker,
    )
    had_config = setup.is_file()
    if had_config:
        _atomic_verified_copy(setup, backup)
    else:
        absent_marker.write_text("setup.cfg absent before mutation\n", encoding="utf-8")
    return had_config


def _restore_setup_override(
    *,
    setup: Path,
    backup: Path,
    absent_marker: Path,
    had_config: bool,
) -> None:
    if had_config:
        if not backup.is_file() or absent_marker.exists():
            raise RuntimeError("setup.cfg backup state is incomplete")
        _atomic_verified_copy(backup, setup)
        backup.unlink()
    else:
        if not absent_marker.is_file() or backup.exists():
            raise RuntimeError("setup.cfg absence marker state is incomplete")
        setup.unlink(missing_ok=True)
        absent_marker.unlink()


def _acquire_direct_suite_lock() -> int | None:
    """Serialize direct batches with suite publish/checkpoint retirement."""

    if getattr(_SUITE_LOCK_CONTEXT, "held", False):
        return None
    LOGDIR.mkdir(parents=True, exist_ok=True)
    fd = os.open(
        str(LOGDIR / ".ecs_mutation_suite.lock"),
        os.O_CREAT | os.O_WRONLY,
        0o644,
    )
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
    except BaseException:
        os.close(fd)
        raise
    return fd


def run_mutation_suite(
    suite: str,
    *,
    timeout: float | None = None,
) -> dict:
    """Run an exact CPU/GPU registry partition without allowing input drift."""

    if getattr(_SUITE_LOCK_CONTEXT, "held", False):
        raise RuntimeError("nested mutation suite orchestration is not allowed")
    suite_path = Path(suite).resolve()
    LOGDIR.mkdir(parents=True, exist_ok=True)
    result_path = LOGDIR / f"{suite_path.stem}_mutation_survivors.json"
    lock_fd = os.open(
        str(LOGDIR / ".ecs_mutation_suite.lock"),
        os.O_CREAT | os.O_WRONLY,
        0o644,
    )
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    _SUITE_LOCK_CONTEXT.held = True
    try:
        result_path.unlink(missing_ok=True)
        recovery_lock_fd = os.open(
            str(LOGDIR / ".ecs_mutation.lock"),
            os.O_CREAT | os.O_WRONLY,
            0o644,
        )
        fcntl.flock(recovery_lock_fd, fcntl.LOCK_EX)
        try:
            _recover_stale_setup_state(
                setup=REPO / "setup.cfg",
                backup=LOGDIR / ".setup.cfg.bak",
                absent_marker=LOGDIR / ".setup.cfg.absent",
            )
        finally:
            os.close(recovery_lock_fd)
        return _run_mutation_suite_locked(
            suite_path,
            timeout=timeout,
            result_path=result_path,
        )
    finally:
        _SUITE_LOCK_CONTEXT.held = False
        os.close(lock_fd)


def _run_mutation_suite_locked(
    suite_path: Path,
    *,
    timeout: float | None,
    result_path: Path,
) -> dict:
    """Run one suite while the dedicated suite-orchestration lock is held."""

    result_path.unlink(missing_ok=True)
    plan = load_mutation_suite(suite_path)
    suite_doc = plan["suite_doc"]
    bar = _resolve_mutation_bar(suite_doc)
    snapshot_paths = _suite_snapshot_paths(plan)
    snapshot_before = input_snapshot(snapshot_paths, repo=REPO)
    batch_results: list[dict] = []
    for batch in plan["batches"]:
        current_snapshot = input_snapshot(snapshot_paths, repo=REPO)
        if current_snapshot != snapshot_before:
            raise RuntimeError(
                "mutation input snapshot drifted before batch "
                f"{batch['name']}: {snapshot_before} -> {current_snapshot}"
            )
        result = run_mutation(
            str(batch["registry_path"]),
            jobs=batch["jobs"],
            timeout=timeout,
            lane=batch["lane"],
        )
        if result.get("tag") != batch["registry_path"].stem:
            raise ValueError(f"mutation batch result identity mismatch: {batch['name']}")
        current_snapshot = input_snapshot(snapshot_paths, repo=REPO)
        if current_snapshot != snapshot_before:
            raise RuntimeError(
                "mutation input snapshot drifted after batch "
                f"{batch['name']}: {snapshot_before} -> {current_snapshot}"
            )
        batch_results.append(result)

    snapshot_after = input_snapshot(snapshot_paths, repo=REPO)
    if snapshot_after != snapshot_before:
        raise RuntimeError(
            "mutation input snapshot drifted before suite publish: "
            f"{snapshot_before} -> {snapshot_after}"
        )
    suite_disposition_authentication = None
    if plan["semantic_dispositions_path"] is not None:
        suite_disposition_authentication = _authenticate_suite_disposition_partition(
            batch_results,
            disposition_path=plan["semantic_dispositions_path"],
            repo=REPO,
            require_classifications=True,
        )
    merged = merge_mutation_batches(tuple(batch_results), bar=bar)
    status_counts = merged["status_counts"]
    doc = {
        "schema": _MUTATION_SUITE_RUN_SCHEMA,
        "tag": plan["path"].stem,
        "input_snapshot_sha256": snapshot_before,
        "verified_snapshot_sha256": snapshot_after,
        **merged,
        **(
            {
                "suite_disposition_authentication": (
                    suite_disposition_authentication
                )
            }
            if suite_disposition_authentication is not None
            else {}
        ),
        "survived": status_counts.get("survived", 0),
        "no_tests": status_counts.get("no_tests", 0),
    }
    publish_snapshot = input_snapshot(snapshot_paths, repo=REPO)
    if publish_snapshot != snapshot_before:
        raise RuntimeError(
            "mutation input snapshot drifted before suite publish: "
            f"{snapshot_before} -> {publish_snapshot}"
        )
    doc["verified_snapshot_sha256"] = publish_snapshot
    write_json_atomic(result_path, doc)
    for batch in plan["batches"]:
        if batch["lane"] != "gpu_serial":
            continue
        checkpoint = (
            LOGDIR
            / f"{batch['registry_path'].stem}_mutation_checkpoint.json"
        )
        checkpoint.unlink(missing_ok=True)
        checkpoint.with_name(f".{checkpoint.name}.tmp").unlink(missing_ok=True)
    return doc


def run_mutation(
    registry: str,
    *,
    jobs: int | None = None,
    timeout: float | None = None,
    lane: str | None = None,
) -> dict:
    registry_path = Path(registry).resolve()
    reg = json.loads(registry_path.read_text(encoding="utf-8"))
    if "batches" in reg:
        return run_mutation_suite(str(registry_path), timeout=timeout)
    if reg.get("schema") != "error_coupling_simulator.harness.mutation_batch.v1":
        raise ValueError("direct mutation registry must use mutation_batch.v1 schema")
    semantic_dispositions = _semantic_dispositions_path(reg, repo=REPO)
    if semantic_dispositions is not None:
        _preflight_semantic_disposition_document(semantic_dispositions, repo=REPO)

    tag = registry_path.stem
    modules = tuple(reg["reconcile_modules"])
    tests = tuple(reg["covered_by_test_files"])
    also_copy = _also_copy_paths(reg)
    selected_lane = lane or reg.get("lane") or (
        "gpu_serial" if reg.get("requires_gpu") else "cpu_parallel"
    )
    requires_gpu = bool(reg.get("requires_gpu"))
    if requires_gpu != (selected_lane == "gpu_serial"):
        raise ValueError("mutation lane and requires_gpu disagree")
    worker_count = resolve_jobs(reg, lane=selected_lane, requested=jobs)
    policy = execution_policy(lane=selected_lane, jobs=worker_count)
    bar = _resolve_mutation_bar(reg)
    tmult = _knob(
        reg, "mutation_gate", "timeout_multiplier", "ECS_MUT_TIMEOUT_MULT", 15.0, float
    )
    tconst = _knob(
        reg, "mutation_gate", "timeout_constant", "ECS_MUT_TIMEOUT_CONST", 1.0, float
    )
    _validate_mutation_gate_knobs(
        bar=bar,
        timeout_multiplier=tmult,
        timeout_constant=tconst,
    )
    if timeout is not None:
        _effective_worker_timeout(
            explicit_timeout=timeout,
            estimated_test_time=0.0,
            timeout_multiplier=tmult,
            timeout_constant=tconst,
        )

    LOGDIR.mkdir(parents=True, exist_ok=True)
    log = LOGDIR / f"{tag}_mutation.log"
    result_text = LOGDIR / f"{tag}_mutation_results.txt"
    result_json = LOGDIR / f"{tag}_mutation_survivors.json"
    setup = REPO / "setup.cfg"
    backup = LOGDIR / ".setup.cfg.bak"
    absent_marker = LOGDIR / ".setup.cfg.absent"
    process_evidence: dict[str, dict | list] = {}
    status_authentication: dict = {}

    suite_lock_fd = _acquire_direct_suite_lock()
    try:
        lock_fd = os.open(
            str(LOGDIR / ".ecs_mutation.lock"),
            os.O_CREAT | os.O_WRONLY,
            0o644,
        )
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
    except BaseException:
        if suite_lock_fd is not None:
            os.close(suite_lock_fd)
        raise
    gpu = None
    expected_generated_catalog_sha256: str | None = None
    setup_override_started = False
    try:
        result_json.unlink(missing_ok=True)
        had_config = _begin_setup_override(
            setup=setup,
            backup=backup,
            absent_marker=absent_marker,
        )
        setup_override_started = True
        snapshot_paths = _batch_snapshot_paths(registry_path, reg)
        snapshot_before = input_snapshot(snapshot_paths, repo=REPO)
        try:
            _write_mutmut_config(
                setup,
                modules=modules,
                tests=tests,
                also_copy=also_copy,
                timeout_multiplier=tmult,
                timeout_constant=tconst,
            )
            _clear_mutants_tree(repo=REPO)
            _prepare_also_copy_destinations(also_copy, repo=REPO)
            base_env = _env()
            log.write_text(
                f"tag={tag}\nsource_paths={modules}\ntest_selection={tests}\n"
                f"lane={selected_lane}\nmax_children={worker_count}\n",
                encoding="utf-8",
            )
            result_text.unlink(missing_ok=True)
            if selected_lane == "gpu_serial":
                plan_path = LOGDIR / f".{tag}_fresh_exec_plan.json"
                checkpoint_path = LOGDIR / f"{tag}_mutation_checkpoint.json"
                gpu = gpu_pool.acquire_gpu_slot()
                child_env = lane_environment(
                    gpu.child_env(base_env),
                    lane=selected_lane,
                )
                checkpoint_execution_policy = {
                    **policy,
                    "timeout_multiplier": tmult,
                    "timeout_constant": tconst,
                    "explicit_timeout": timeout,
                    "bound_environment": _gpu_bound_environment(child_env),
                    "device_identity": _gpu_device_identity(child_env),
                }
                runtime_fingerprint = _mutation_runtime_fingerprint()
                prepared = _prepare_gpu_fresh_exec(
                    tag=tag,
                    env=child_env,
                    timeout=timeout,
                    log=log,
                    plan_path=plan_path,
                    checkpoint_path=checkpoint_path,
                    input_snapshot_sha256=snapshot_before,
                    execution_policy=checkpoint_execution_policy,
                    runtime_fingerprint=runtime_fingerprint,
                    modules=modules,
                )
                prepared_plan = prepared.get("plan")
                if not isinstance(prepared_plan, dict) or not isinstance(
                    prepared_plan.get("generated_catalog_sha256"), str
                ):
                    raise TypeError("prepared GPU generated catalog digest is invalid")
                expected_generated_catalog_sha256 = prepared_plan[
                    "generated_catalog_sha256"
                ]
                frozen_tree = _make_generated_tree_read_only(REPO / "mutants")
                try:
                    rows, process_evidence = _run_gpu_fresh_exec(
                        tag=tag,
                        env=child_env,
                        timeout=timeout,
                        log=log,
                        plan_path=plan_path,
                        checkpoint_path=checkpoint_path,
                        input_snapshot_sha256=snapshot_before,
                        execution_policy=checkpoint_execution_policy,
                        runtime_fingerprint=runtime_fingerprint,
                        timeout_multiplier=tmult,
                        timeout_constant=tconst,
                        modules=modules,
                        prepared=prepared,
                    )
                finally:
                    _restore_generated_tree_modes(frozen_tree)
                process_evidence["generated_tree_access"] = {
                    "read_only_enforced": True,
                    "restored_entry_count": len(frozen_tree),
                }
                status_authentication = {
                    "canonical_status_source": "fresh_pytest_process_exit_code",
                    "fresh_clean_control_required": True,
                    "pytest_internal_or_usage_error_credited_as_killed": False,
                }
            else:
                child_env = lane_environment(base_env, lane=selected_lane)
                ran = proc.run(
                    ["mutmut", "run", "--max-children", str(worker_count)],
                    cwd=str(REPO),
                    env=child_env,
                    timeout=timeout,
                    log_path=str(log),
                    append=True,
                )
                process_evidence["run"] = _require_process_ok("mutmut run", ran)
                results_ran = proc.run(
                    ["mutmut", "results", "--all", "True"],
                    cwd=str(REPO),
                    env=child_env,
                    timeout=timeout,
                    log_path=str(result_text),
                )
                process_evidence["results"] = _require_process_ok(
                    "mutmut results --all", results_ran
                )
                display_rows = parse_mutmut_results(
                    result_text.read_text(encoding="utf-8", errors="strict")
                )
                rows, raw_codes = _load_mutmut_meta_rows(modules, repo=REPO)
                display_mismatches = _cross_check_mutmut_display(
                    rows,
                    display_rows,
                    raw_codes=raw_codes,
                )
                status_authentication = {
                    "canonical_status_source": (
                        "mutants/<source>.py.meta:exit_code_by_key"
                    ),
                    "display_cross_check_source": "mutmut results --all True",
                    "display_status_mismatches": display_mismatches,
                    "pytest_internal_or_usage_error_credited_as_killed": False,
                }
        finally:
            try:
                if setup_override_started:
                    _restore_setup_override(
                        setup=setup,
                        backup=backup,
                        absent_marker=absent_marker,
                        had_config=had_config,
                    )
                    setup_override_started = False
            finally:
                if gpu is not None:
                    gpu.release()
                    gpu = None

        snapshot_after = input_snapshot(snapshot_paths, repo=REPO)
        if snapshot_after != snapshot_before:
            raise RuntimeError(
                f"mutation input snapshot drifted: {snapshot_before} -> {snapshot_after}"
            )
        semantic_dispositions = _semantic_dispositions_path(reg, repo=REPO)
        semantic_catalog: dict | None = None
        semantic_catalog_sha256: str | None = None
        disposition_authentication: dict | None = None
        semantic_classifications: dict[str, dict] | None = None
        if semantic_dispositions is not None:
            semantic_catalog = build_semantic_mutant_catalog(
                rows,
                modules=modules,
                repo=REPO,
            )
            semantic_catalog_sha256 = _semantic_catalog_sha256(semantic_catalog)
            if (
                expected_generated_catalog_sha256 is not None
                and semantic_catalog_sha256
                != expected_generated_catalog_sha256
            ):
                raise RuntimeError(
                    "GPU mutation generated semantic catalog drifted after execution"
                )
            (
                semantic_classifications,
                disposition_authentication,
            ) = authenticate_semantic_dispositions(
                semantic_dispositions,
                rows=rows,
                catalog=semantic_catalog,
                repo=REPO,
            )
        score = score_mutation_rows(
            rows,
            modules=modules,
            bar=bar,
            classifications=semantic_classifications,
        )
        status_counts = score["status_counts"]
        doc = {
            "schema": _MUTATION_BATCH_RUN_SCHEMA,
            "tag": tag,
            "lane": selected_lane,
            "jobs": worker_count,
            "execution_policy": policy,
            "input_snapshot_sha256": snapshot_before,
            "verified_snapshot_sha256": snapshot_after,
            "processes": process_evidence,
            "status_authentication": status_authentication,
            **(
                {
                    "semantic_classification": {
                        "catalog": {
                            "sha256": semantic_catalog_sha256,
                            **{
                                key: value
                                for key, value in semantic_catalog.items()
                                if key != "classifications"
                            },
                        },
                        "classifications": semantic_classifications,
                    },
                    "disposition_authentication": disposition_authentication,
                }
                if semantic_catalog is not None
                else {}
            ),
            **score,
            "survived": status_counts["survived"],
            "no_tests": status_counts["no_tests"],
            "timeout_multiplier": tmult,
            "timeout_constant": tconst,
            "survivors": sorted(
                mutant for mutant, status in rows.items() if status == "survived"
            ),
            "no_test_mutants": sorted(
                mutant for mutant, status in rows.items() if status == "no_tests"
            ),
        }
        publish_snapshot = input_snapshot(snapshot_paths, repo=REPO)
        if publish_snapshot != snapshot_before:
            raise RuntimeError(
                "mutation input snapshot drifted before batch publish: "
                f"{snapshot_before} -> {publish_snapshot}"
            )
        doc["verified_snapshot_sha256"] = publish_snapshot
        write_json_atomic(result_json, doc)
        return doc
    finally:
        try:
            try:
                if setup_override_started:
                    _restore_setup_override(
                        setup=setup,
                        backup=backup,
                        absent_marker=absent_marker,
                        had_config=had_config,
                    )
            finally:
                if gpu is not None:
                    gpu.release()
        finally:
            try:
                os.close(lock_fd)
            finally:
                if suite_lock_fd is not None:
                    os.close(suite_lock_fd)


def main(argv: list) -> int:
    args = list(argv)
    if len(args) >= 3 and args[0] == "--run-fresh-pytest":
        return run_fresh_pytest_worker(Path(args[1]), args[2:])
    if len(args) >= 3 and args[0] == "--prepare-fresh-exec":
        prepare_fresh_exec_plan(
            Path(args[1]),
            modules=tuple(args[2:]),
        )
        return 0
    jobs = timeout = None
    if "--jobs" in args:
        i = args.index("--jobs")
        jobs = int(args[i + 1]); del args[i:i + 2]
    if "--timeout" in args:
        i = args.index("--timeout")
        timeout = float(args[i + 1]); del args[i:i + 2]
    assert args, "usage: mutation.py <registry.json> [--jobs N] [--timeout SEC]"
    doc = run_mutation(args[0], jobs=jobs, timeout=timeout)
    timeout_label = (
        f" timeout_x{doc['timeout_multiplier']}"
        if "timeout_multiplier" in doc
        else ""
    )
    print(
        f"MUTATION tag={doc['tag']} total={doc['total']} killed={doc['killed']} "
        f"survived={doc['survived']} no_tests={doc['no_tests']} "
        f"raw_kill_rate={doc['kill_rate']:.4f} "
        + (
            f"semantic_kill_rate={doc['semantic']['kill_rate']:.4f} "
            if "semantic" in doc
            else ""
        )
        + f"bar={doc['bar']}"
        f"{timeout_label} {'PASS' if doc['pass'] else 'FAIL'}"
    )
    return 0 if doc["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
