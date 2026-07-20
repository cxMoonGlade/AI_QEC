"""Standalone specified-noise simulator for QEC error mechanisms.

The package applies declared coupling, leakage, and memoryful noise processes to a QEC circuit and
emits a multi-time syndrome record. It consolidates the simulator implementation behind an
independently releasable package boundary.

There is no physical ground truth implied by a specified noise process. QuTiP, closed-form, and
exact-density-matrix references are formal implementation checks, not evidence of correspondence to
hardware. The emitted record is the product; LER and channel/record metrics are instruments on that
record. Evaluator-only process truth is isolated from emitted artifacts.

The binding object and claim contract is ``docs/SIMULATOR.md``; the current
workflow and public surface are recorded in ``CLAUDE.md``.
"""

import hashlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _package_tree_sha256_at_import() -> str:
    """Seal package files before any submodule can become stale in-process."""

    package_root = Path(__file__).resolve().parent
    included_suffixes = {".py", ".cpp", ".cu", ".md", ".json", ".npz"}
    paths = sorted(
        path
        for path in package_root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix in included_suffixes
    )
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(package_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


_PACKAGE_TREE_SHA256_AT_IMPORT = _package_tree_sha256_at_import()


try:
    __version__ = version("error-coupling-simulator")
except PackageNotFoundError:  # source tree before installation
    __version__ = "0+uninstalled"
