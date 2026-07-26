#!/usr/bin/env python3
"""Generate a complete first-hop map of every Git clone under ``external/``.

The map is intentionally structural.  It records exact upstream identities and
routes a reader to documentation, manifests, source roots, likely entry files,
tests, and examples without pretending that automatically selected anchors are
scientific evidence or a semantic close-read.  The curated tensor-network map
remains the deeper guide for MPS/PEPS work.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "external"
OUTPUT = ROOT / "docs" / "external_baselines" / "EXTERNAL_CODE_MAP.md"
MARKER = "<!-- external-code-map-inputs-sha256:"

CATEGORY_ORDER = ("direct", "baselines", "reference_repos")

LANGUAGES = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cxx": "C++",
    ".cu": "CUDA",
    ".cuh": "CUDA",
    ".f": "Fortran",
    ".f90": "Fortran",
    ".go": "Go",
    ".h": "C/C++ header",
    ".hh": "C/C++ header",
    ".hpp": "C/C++ header",
    ".ipynb": "Jupyter",
    ".java": "Java",
    ".jl": "Julia",
    ".js": "JavaScript",
    ".kt": "Kotlin",
    ".m": "MATLAB/Objective-C",
    ".py": "Python",
    ".pyi": "Python",
    ".pyx": "Cython",
    ".r": "R",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sh": "Shell",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
}

MANIFEST_NAMES = {
    "Cargo.toml",
    "CMakeLists.txt",
    "Manifest.toml",
    "Makefile",
    "Project.toml",
    "environment.yml",
    "environment.yaml",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
    "tox.ini",
}

ENTRY_BASENAME_PRIORITY = {
    "__init__.py": 0,
    "lib.rs": 1,
    "main.rs": 2,
    "main.py": 3,
    "api.py": 4,
    "cli.py": 5,
    "simulator.py": 6,
    "decoder.py": 7,
    "circuit.py": 8,
    "core.py": 9,
}

NON_SOURCE_ROOTS = {
    ".github",
    "asset",
    "assets",
    "benchmark",
    "benchmarks",
    "build",
    "demo",
    "demos",
    "doc",
    "docs",
    "documentation",
    "example",
    "examples",
    "external",
    "notebook",
    "notebooks",
    "script",
    "scripts",
    "test",
    "tests",
    "third_party",
    "tutorial",
    "tutorials",
    "vendor",
}


@dataclass(frozen=True)
class RepoInfo:
    category: str
    relative_path: str
    name: str
    origin: str
    branch: str
    head: str
    tree: str
    shallow: bool
    partial: bool
    sparse: bool
    tracked_file_count: int
    languages: tuple[tuple[str, int], ...]
    readmes: tuple[str, ...]
    manifests: tuple[str, ...]
    source_roots: tuple[tuple[str, int], ...]
    entry_anchors: tuple[str, ...]
    test_anchors: tuple[str, ...]
    example_anchors: tuple[str, ...]
    documentation_roots: tuple[str, ...]


def git_text(repo: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *arguments],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def git_optional(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def tracked_files(repo: Path) -> tuple[str, ...]:
    raw = subprocess.check_output(
        [
            "git",
            "-C",
            str(repo),
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            "HEAD",
        ],
        stderr=subprocess.DEVNULL,
    )
    return tuple(
        item.decode("utf-8", errors="surrogateescape")
        for item in raw.split(b"\0")
        if item
    )


def category_for(repo: Path) -> str:
    parts = repo.relative_to(EXTERNAL).parts
    if len(parts) == 1:
        return "direct"
    if parts[0] in {"baselines", "reference_repos"}:
        return parts[0]
    return "nested"


def clone_roots() -> tuple[tuple[str, Path], ...]:
    found: list[tuple[str, Path]] = []
    for current, directories, files in os.walk(EXTERNAL):
        candidate = Path(current)
        if ".git" in directories or ".git" in files:
            found.append((category_for(candidate), candidate))
            directories[:] = []
    if not found:
        raise RuntimeError(f"no Git clones found under {EXTERNAL}")
    order = {category: index for index, category in enumerate(CATEGORY_ORDER)}
    return tuple(
        sorted(
            found,
            key=lambda item: (
                order.get(item[0], len(order)),
                str(item[1].relative_to(ROOT)).lower(),
            ),
        )
    )


def sanitized_origin(origin: str) -> str:
    parsed = urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        return origin
    hostname = parsed.hostname
    if ":" in hostname:
        hostname = f"[{hostname}]"
    netloc = hostname
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


def root_names(
    files: tuple[str, ...],
    *,
    names: frozenset[str],
) -> tuple[str, ...]:
    roots = {
        Path(item).parts[0]
        for item in files
        if len(Path(item).parts) > 1
        and Path(item).parts[0].lower() in names
    }
    return tuple(sorted(roots, key=str.lower))


def category_anchors(
    files: tuple[str, ...],
    *,
    root_names_to_match: frozenset[str],
    basename_markers: tuple[str, ...],
    excluded_parent_names: frozenset[str] = frozenset(),
) -> tuple[str, ...]:
    roots = root_names(files, names=root_names_to_match)
    if roots:
        return roots
    candidates = []
    for item in files:
        path = Path(item)
        stem = path.stem.lower()
        if any(
            part.lower() in excluded_parent_names
            for part in path.parts[:-1]
        ):
            continue
        if (
            any(part.lower() in root_names_to_match for part in path.parts[:-1])
            or any(
                stem.startswith(marker) or stem.endswith(marker)
                for marker in basename_markers
            )
        ):
            candidates.append(item)
    return tuple(
        sorted(
            candidates,
            key=lambda item: (len(Path(item).parts), len(item), item.lower()),
        )[:4]
    )


def choose_source_roots(
    files: tuple[str, ...],
) -> tuple[tuple[str, int], ...]:
    counts: Counter[str] = Counter()
    for item in files:
        path = Path(item)
        if path.suffix.lower() not in LANGUAGES:
            continue
        root = path.parts[0] if len(path.parts) > 1 else "."
        if root.lower() in NON_SOURCE_ROOTS:
            continue
        counts[root] += 1
    return tuple(
        sorted(counts.items(), key=lambda pair: (-pair[1], pair[0].lower()))[:4]
    )


def choose_entry_anchors(
    files: tuple[str, ...],
    source_roots: tuple[tuple[str, int], ...],
) -> tuple[str, ...]:
    code_files = [
        item
        for item in files
        if Path(item).suffix.lower() in LANGUAGES
        and Path(item).suffix.lower() != ".ipynb"
        and not any(
            part.lower().startswith(("test", "example", "tutorial", "benchmark"))
            for part in Path(item).parts[:-1]
        )
    ]
    chosen: list[str] = []
    for root, _ in source_roots:
        candidates = [
            item
            for item in code_files
            if root == "." or Path(item).parts[0] == root
        ]
        if not candidates:
            continue
        candidates.sort(
            key=lambda item: (
                ENTRY_BASENAME_PRIORITY.get(Path(item).name.lower(), 100),
                len(Path(item).parts),
                len(item),
                item.lower(),
            )
        )
        if candidates[0] not in chosen:
            chosen.append(candidates[0])
    ranked = sorted(
        code_files,
        key=lambda item: (
            ENTRY_BASENAME_PRIORITY.get(Path(item).name.lower(), 100),
            len(Path(item).parts),
            len(item),
            item.lower(),
        ),
    )
    for item in ranked:
        if item not in chosen:
            chosen.append(item)
        if len(chosen) >= 6:
            break
    return tuple(chosen[:6])


def inspect_repo(category: str, repo: Path) -> RepoInfo:
    files = tracked_files(repo)
    language_counts = Counter(
        LANGUAGES[Path(item).suffix.lower()]
        for item in files
        if Path(item).suffix.lower() in LANGUAGES
    )
    languages = tuple(
        sorted(
            language_counts.items(),
            key=lambda pair: (-pair[1], pair[0].lower()),
        )[:6]
    )
    readmes = tuple(
        sorted(
            (
                item
                for item in files
                if Path(item).name.lower().startswith("readme")
                and len(Path(item).parts) <= 2
            ),
            key=lambda item: (len(Path(item).parts), len(item), item.lower()),
        )[:3]
    )
    manifests = tuple(
        sorted(
            (
                item
                for item in files
                if Path(item).name in MANIFEST_NAMES
                and len(Path(item).parts) <= 2
            ),
            key=lambda item: (len(Path(item).parts), item.lower()),
        )[:8]
    )
    source_roots = choose_source_roots(files)
    branch = git_text(repo, "branch", "--show-current") or "(detached)"
    try:
        origin = sanitized_origin(git_text(repo, "remote", "get-url", "origin"))
    except subprocess.CalledProcessError:
        origin = "(no origin remote)"
    head = git_text(repo, "rev-parse", "HEAD")
    tree = git_text(repo, "rev-parse", "HEAD^{tree}")
    if re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise RuntimeError(f"invalid HEAD identity for {repo}: {head!r}")
    if re.fullmatch(r"[0-9a-f]{40}", tree) is None:
        raise RuntimeError(f"invalid tree identity for {repo}: {tree!r}")
    return RepoInfo(
        category=category,
        relative_path=str(repo.relative_to(ROOT)),
        name=repo.name,
        origin=origin,
        branch=branch,
        head=head,
        tree=tree,
        shallow=git_text(repo, "rev-parse", "--is-shallow-repository") == "true",
        partial=(
            git_optional(
                repo,
                "config",
                "--bool",
                "--get",
                "remote.origin.promisor",
            )
            == "true"
        ),
        sparse=(
            git_optional(
                repo,
                "config",
                "--bool",
                "--get",
                "core.sparseCheckout",
            )
            == "true"
        ),
        tracked_file_count=len(files),
        languages=languages,
        readmes=readmes,
        manifests=manifests,
        source_roots=source_roots,
        entry_anchors=choose_entry_anchors(files, source_roots),
        test_anchors=category_anchors(
            files,
            root_names_to_match=frozenset({"test", "tests", "testing"}),
            basename_markers=("test_", "_test"),
        ),
        example_anchors=category_anchors(
            files,
            root_names_to_match=frozenset(
                {
                    "demo",
                    "demos",
                    "example",
                    "examples",
                    "notebook",
                    "notebooks",
                    "tutorial",
                    "tutorials",
                }
            ),
            basename_markers=("example_", "demo_", "tutorial_"),
            excluded_parent_names=frozenset({"test", "tests", "testing"}),
        ),
        documentation_roots=root_names(
            files,
            names=frozenset({"doc", "docs", "documentation"}),
        ),
    )


def inspect_all() -> tuple[RepoInfo, ...]:
    return tuple(inspect_repo(category, repo) for category, repo in clone_roots())


def inputs_hash(repositories: tuple[RepoInfo, ...]) -> str:
    digest = hashlib.sha256(Path(__file__).read_bytes())
    digest.update(
        json.dumps(
            [asdict(repository) for repository in repositories],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return digest.hexdigest()


def joined_code(items: tuple[str, ...], *, empty: str = "none detected") -> str:
    if not items:
        return empty
    return ", ".join(f"`{item}`" for item in items)


def render(repositories: tuple[RepoInfo, ...], digest: str) -> str:
    category_counts = Counter(repository.category for repository in repositories)
    lines = [
        "# Complete external repository code map",
        "",
        f"{MARKER} {digest} -->",
        "",
        "Generated by `python tools/gen_external_code_map.py`. It discovers every outermost Git",
        "worktree anywhere below `external/` and stops descent at each repository boundary.",
        "The map is a structural first hop, not scientific evidence or a claim that an automatically",
        "selected file is the semantic center of a repository. For curated MPS/PEPS routes, continue",
        "to [`TENSOR_NETWORK_CODE_MAP.md`](TENSOR_NETWORK_CODE_MAP.md).",
        "",
        f"Inventory: **{len(repositories)} clones** — "
        + ", ".join(
            f"{category_counts[category]} {category}"
            for category in (
                *CATEGORY_ORDER,
                *sorted(set(category_counts) - set(CATEGORY_ORDER)),
            )
            if category_counts[category]
        )
        + ".",
        "",
        "The recorded commit and tree bind tracked content. History depth and partial/sparse clone",
        "modes are reported explicitly.",
        "This map does not certify worktree cleanliness, installed-package identity, runtime",
        "compatibility, or fidelity; claim-bearing adapters must verify those independently.",
        "",
        "## Repository index",
        "",
        "| Group | Repository | Commit | Clone | Recognized suffix profile (file counts) | Code-bearing roots |",
        "|---|---|---|---|---|---|",
    ]
    for repository in repositories:
        languages = ", ".join(
            f"{language} ({count})" for language, count in repository.languages
        ) or "none detected"
        roots = ", ".join(
            f"`{root}` ({count})" for root, count in repository.source_roots
        ) or "none detected"
        clone_modes = [
            "shallow" if repository.shallow else "non-shallow",
        ]
        if repository.partial:
            clone_modes.append("partial")
        if repository.sparse:
            clone_modes.append("sparse")
        clone_kind = ", ".join(clone_modes)
        lines.append(
            f"| {repository.category} | `{repository.relative_path}` | "
            f"`{repository.head[:12]}` | {clone_kind} | {languages} | {roots} |"
        )

    for repository in repositories:
        clone_modes = [
            "shallow" if repository.shallow else "non-shallow",
        ]
        if repository.partial:
            clone_modes.append("partial")
        if repository.sparse:
            clone_modes.append("sparse")
        clone_kind = ", ".join(clone_modes)
        languages = ", ".join(
            f"{language} ({count})" for language, count in repository.languages
        ) or "none detected"
        source_roots = ", ".join(
            f"`{root}` ({count} code files)"
            for root, count in repository.source_roots
        ) or "none detected"
        lines += [
            "",
            f"## {repository.relative_path}",
            "",
            f"- Upstream: `{repository.origin}`",
            f"- Checkout: `{repository.branch}` at `{repository.head}`; tree `{repository.tree}`; {clone_kind}",
            f"- Tracked inventory: {repository.tracked_file_count} files; recognized suffix profile: {languages}",
            f"- Read first: {joined_code(repository.readmes)}",
            f"- Build/package manifests: {joined_code(repository.manifests)}",
            f"- Code-bearing roots: {source_roots}",
            f"- Lexical entry-name candidates: {joined_code(repository.entry_anchors)}",
            f"- Test anchors: {joined_code(repository.test_anchors)}",
            f"- Example/tutorial anchors: {joined_code(repository.example_anchors)}",
            f"- Documentation roots: {joined_code(repository.documentation_roots)}",
        ]

    lines += [
        "",
        "## Safe use",
        "",
        "1. Treat every clone as read-only; adapters, patches, locks, and outputs belong in this repository.",
        "2. Use the full commit and tree above when citing code. A branch name or directory name alone is not a durable source locator.",
        "3. Check clone cleanliness, ignored files, submodules/LFS, and installed-source identity before a claim-bearing run.",
        "4. Open the README and manifest before following an automatically selected entry anchor.",
        "5. Promote load-bearing code to a curated map or audit note with exact file/line locators and an explicit claim boundary.",
        "",
        "## Regeneration",
        "",
        "```bash",
        "python tools/gen_external_code_map.py",
        "python tools/gen_external_code_map.py --check",
        "```",
        "",
        "Regenerate after adding, removing, or deliberately updating an external clone.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    repositories = inspect_all()
    digest = inputs_hash(repositories)
    expected = render(repositories, digest)
    if arguments.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
            print(f"STALE: {OUTPUT.relative_to(ROOT)}")
            return 1
        print(
            f"CURRENT: {OUTPUT.relative_to(ROOT)} "
            f"({len(repositories)} clones, {digest})"
        )
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8")
    print(
        f"WROTE: {OUTPUT.relative_to(ROOT)} "
        f"({len(repositories)} clones, {digest})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
