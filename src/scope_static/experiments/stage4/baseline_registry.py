from __future__ import annotations

import argparse
from pathlib import Path

from scope_static.mechanism_discovery.baseline_registry import write_baseline_registry_audit


DEFAULT_OUTPUT_DIR = Path("outputs/scope_static/baseline_registry")


def run_baseline_registry_audit_from_args(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    repo_root: str | Path | None = None,
    strict_clones: bool = False,
) -> dict[str, object]:
    audit = write_baseline_registry_audit(output_dir, repo_root=repo_root)
    missing = [repo for repo in audit["external_repositories"] if not bool(dict(repo).get("present"))]
    print("Baseline registry audit complete")
    print(f"entries={len(audit['entries'])}")
    print(f"external_repositories={len(audit['external_repositories'])}")
    print(f"missing_external_repositories={len(missing)}")
    print(f"output={Path(output_dir)}")
    if strict_clones and missing:
        names = ", ".join(str(dict(repo).get("name")) for repo in missing)
        raise SystemExit(f"Missing external baseline clones: {names}")
    return audit


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit SCOPE baseline registry and external baseline clone cache.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--strict-clones", action="store_true")
    args = parser.parse_args(argv)
    run_baseline_registry_audit_from_args(
        output_dir=args.output_dir,
        repo_root=args.repo_root,
        strict_clones=bool(args.strict_clones),
    )


if __name__ == "__main__":
    main()
