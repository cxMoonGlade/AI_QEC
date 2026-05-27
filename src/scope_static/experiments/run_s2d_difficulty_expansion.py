from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical_oracle import run_physical_oracle_stack


DEFAULT_RUNS: list[dict[str, object]] = [
    {"name": "phys5_setB", "profile": "phys5_chain", "mechanism_set": "set_B", "purpose": "more mechanisms, same circuit"},
    {"name": "phys9_setA", "profile": "phys9_chain", "mechanism_set": "set_A", "purpose": "bigger circuit, same mechanisms"},
    {"name": "phys9_setB", "profile": "phys9_chain", "mechanism_set": "set_B", "purpose": "bigger circuit plus more mechanisms"},
    {"name": "phys9_setC", "profile": "phys9_chain", "mechanism_set": "set_C", "purpose": "harder non-Pauli/SPAM/crosstalk mix"},
    {
        "name": "phys15_setB",
        "profile": "phys15_chain",
        "mechanism_set": "set_B",
        "purpose": "hard profile after phys9_setB is stable",
        "enabled": False,
    },
]


def run_s2d_difficulty_expansion(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_difficulty_config(config_path)
    root = output_root_from_config(physical_cfg)
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", root / "S2D_PHYS4_difficulty_expansion")))
    output.mkdir(parents=True, exist_ok=True)
    runs = _enabled_runs(cfg)
    if max_runs is not None:
        runs = runs[: int(max_runs)]

    records = []
    skipped_runs = []
    phys15_allowed = True
    for run_cfg in runs:
        if str(run_cfg.get("profile")) == "phys15_chain" and not phys15_allowed:
            skipped_runs.append(
                {
                    "name": str(run_cfg.get("name", "phys15_chain")),
                    "reason": "phys15_chain requires stable phys9_setB recovery",
                }
            )
            continue
        record = _run_one(output, physical_cfg, cfg, run_cfg)
        records.append(record)
        if record["decision"] == "probe_limited":
            break
        if record["name"] == "phys9_setB" and record["decision"] not in {"strong_recovery", "near_strong"}:
            phys15_allowed = False

    result = {
        "schema": "scope_static_s2d_phys4_difficulty_expansion_v1",
        "stage": "S2D.4_physical_oracle_difficulty_expansion",
        "output_dir": str(output),
        "run_order": [record["name"] for record in records],
        "skipped_runs": skipped_runs,
        "records": records,
        "summary": _comparison_summary(records),
    }
    (output / "comparison_table.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "comparison_summary.md").write_text(format_difficulty_summary(result))
    return result


def _run_one(output: Path, physical_cfg: dict[str, object], cfg: dict[str, object], run_cfg: dict[str, object]) -> dict[str, object]:
    run_dir = output / str(run_cfg["name"])
    run_dir.mkdir(parents=True, exist_ok=True)
    merged = dict(physical_cfg)
    merged.update({key: value for key, value in run_cfg.items() if key not in {"name", "purpose", "enabled"}})
    merged.update(dict(cfg.get("physical_overrides", {})))
    stack = run_physical_oracle_stack(
        merged,
        output_dir=run_dir,
        bootstrap_replicates=int(cfg.get("bootstrap_replicates", 16)),
        random_baseline_trials=int(cfg.get("random_baseline_trials", 64)),
        run_local_inverse="auto",
    )
    paths = dict(stack["paths"])
    teacher = dict(stack["teacher"])
    separability = dict(stack["metrics"]["teacher_self"])  # type: ignore[index]
    local = stack["metrics"].get("learner") if isinstance(stack.get("metrics"), dict) else None
    decision = str(stack["verdicts"]["overall_diagnosis"])  # type: ignore[index]

    noise_audit_path = Path(str(paths["teacher_dir"])) / "noise_application_audit.json"
    if noise_audit_path.exists():
        (run_dir / "noise_application_audit.json").write_text(noise_audit_path.read_text())

    record = {
        "name": str(run_cfg["name"]),
        "purpose": str(run_cfg.get("purpose", "")),
        "profile": str(merged.get("profile")),
        "mechanism_set": str(merged.get("mechanism_set")),
        "num_qubits": int(teacher.get("num_qubits", merged.get("num_qubits", 0))),
        "shots": int(merged.get("shots", 0)),
        "decision": decision,
        "teacher": {
            "mechanism_counts": teacher.get("mechanism_counts", {}),
            "output_dir": str(paths["teacher_dir"]),
            "noise_application_audit": str(run_dir / "noise_application_audit.json"),
            "aer_simulator": teacher.get("aer_simulator"),
        },
        "PHYS2": separability,
        "PHYS3": local if isinstance(local, dict) else None,
        "physical_oracle_stack": {
            "output_dir": stack.get("output_dir"),
            "verdicts": stack.get("verdicts"),
            "timings_seconds": stack.get("timings_seconds"),
        },
    }
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_run_summary(record))
    return record


def _load_difficulty_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D difficulty config must be a mapping")
    section = data.get("s2d_difficulty_expansion", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d_difficulty_expansion config must be a mapping")
    result = dict(section)
    result.setdefault("runs", DEFAULT_RUNS)
    return result


def _enabled_runs(cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = cfg.get("runs", DEFAULT_RUNS)
    if not isinstance(raw, list):
        raise ValueError("s2d_difficulty_expansion.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _comparison_summary(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "num_runs": len(records),
        "strong_recovery": sum(1 for record in records if record["decision"] == "strong_recovery"),
        "near_strong": sum(1 for record in records if record["decision"] == "near_strong"),
        "probe_limited": sum(1 for record in records if record["decision"] == "probe_limited"),
        "learner_limited": sum(1 for record in records if record["decision"] == "learner_limited"),
    }


def format_difficulty_summary(result: dict[str, object]) -> str:
    lines = [
        "# S2D.4 Physical Oracle Difficulty Expansion",
        "",
        "| run | profile | mechanism set | decision | PHYS2 ARI/NMI | PHYS3 ARI/NMI | NLL class |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for record in result["records"]:  # type: ignore[index]
        phys2 = record["PHYS2"]
        phys3 = record.get("PHYS3")
        if phys3:
            main = phys3["main_result"]
            nll = phys3["nll_difficulty_audit"]["response_task_classification"]
            phys3_score = f"{float(main['ari']):.4f}/{float(main['nmi']):.4f}"
        else:
            nll = ""
            phys3_score = ""
        lines.append(
            f"| {record['name']} | {record['profile']} | {record['mechanism_set']} | {record['decision']} | "
            f"{float(phys2['ari']):.4f}/{float(phys2['nmi']):.4f} | {phys3_score} | {nll} |"
        )
    skipped = result.get("skipped_runs", [])
    if isinstance(skipped, list) and skipped:
        lines.extend(["", "## Skipped Runs", ""])
        for item in skipped:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('name')}`: {item.get('reason')}")
    lines.append("")
    return "\n".join(lines)


def format_run_summary(record: dict[str, object]) -> str:
    phys2 = record["PHYS2"]
    phys3 = record.get("PHYS3")
    lines = [
        f"# {record['name']}",
        "",
        f"- Decision: `{record['decision']}`",
        f"- Profile: `{record['profile']}`",
        f"- Mechanism set: `{record['mechanism_set']}`",
        f"- PHYS2 ARI/NMI: `{float(phys2['ari']):.4f}` / `{float(phys2['nmi']):.4f}`",
    ]
    if phys3:
        main = phys3["main_result"]
        direct = phys3["direct_S_alpha_result"]
        nll = phys3["nll_difficulty_audit"]
        lines.extend(
            [
                f"- PHYS3 local inverse ARI/NMI: `{float(main['ari']):.4f}` / `{float(main['nmi']):.4f}`",
                f"- Direct S/alpha ARI/NMI: `{float(direct['ari']):.4f}` / `{float(direct['nmi']):.4f}`",
                f"- NLL difficulty: `{nll['response_task_classification']}`",
                f"- Local inverse NLL: `{float(nll['local_inverse_NLL']):.4f}`",
                f"- Direct S/alpha NLL: `{float(nll['direct_Salpha_NLL']):.4f}`",
                f"- Oracle fingerprint NLL: `{float(nll['oracle_fingerprint_NLL']):.4f}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.4 physical-oracle difficulty expansion.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d_difficulty_expansion(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.4 difficulty expansion complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}"
    )


if __name__ == "__main__":
    main()
