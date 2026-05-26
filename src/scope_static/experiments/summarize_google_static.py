"""Summarize Google SCOPE-Static result JSON with model-comparison effect sizes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from scope_static.metrics import augment_model_comparison_metrics, augment_transfer_comparison_metrics


def main(argv: list[str] | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    metrics_path = Path(args.metrics_path)
    with metrics_path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)

    records = list(result.get("records", []))
    transfers = list(result.get("cross_sample_transfer_records", []))
    augment_model_comparison_metrics(records, baseline_model=args.baseline_model)
    augment_transfer_comparison_metrics(transfers, baseline_model=args.baseline_model)

    filtered_records = [
        record
        for record in records
        if args.preprocessing_mode == "all" or record.get("preprocessing_mode") == args.preprocessing_mode
    ]
    filtered_transfers = [
        record
        for record in transfers
        if args.preprocessing_mode == "all" or record.get("preprocessing_mode") == args.preprocessing_mode
    ]

    if args.json:
        payload = {"records": filtered_records, "cross_sample_transfer_records": filtered_transfers}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload

    _print_report(
        metrics_path=metrics_path,
        records=filtered_records,
        transfers=filtered_transfers,
        baseline_model=args.baseline_model,
        preprocessing_mode=args.preprocessing_mode,
    )
    return {"records": filtered_records, "cross_sample_transfer_records": filtered_transfers}


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics_path")
    parser.add_argument("--baseline-model", default="local")
    parser.add_argument("--preprocessing-mode", default="fault_graph_heuristic")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _print_report(
    *,
    metrics_path: Path,
    records: list[dict[str, object]],
    transfers: list[dict[str, object]],
    baseline_model: str,
    preprocessing_mode: str,
) -> None:
    print("Google static model comparison")
    print(f"metrics: {metrics_path}")
    print(f"preprocessing: {preprocessing_mode}")
    print(f"baseline: {baseline_model}")
    print("")
    print("Heldout")
    _print_table(
        [
            "model",
            "params",
            "comp",
            "ex_mn",
            "d_mn",
            "d_bit/shot",
            "log_d_mn",
            "log_cal",
            "det_mae",
            "pareto",
        ],
        [
            [
                record.get("model"),
                record.get("parameter_count"),
                _fmt_float(record.get("compression_ratio"), precision=2),
                _fmt_float(record.get("excess_mnats_per_window")),
                _fmt_signed_float(record.get("excess_delta_mnats_vs_baseline")),
                _fmt_signed_float(record.get("pseudo_delta_bits_per_shot_vs_baseline")),
                _fmt_signed_float(record.get("logical_excess_delta_mnats_vs_baseline")),
                _fmt_float(record.get("logical_flip_rate_calibration")),
                _fmt_float(record.get("detector_rate_mae")),
                record.get("combined_excess_parameter_pareto_status"),
            ]
            for record in _sort_records(records)
        ],
    )
    print(
        "  ex_mn is milli-nats/window above empirical entropy. "
        "d_* columns are paired deltas vs the baseline; d_bit/shot multiplies by the number of windows."
    )

    if transfers:
        print("")
        print("Cross-Sample Transfer Means")
        rows = []
        for model, model_rows in _group_by_model(transfers):
            rows.append(
                [
                    model,
                    len(model_rows),
                    _fmt_float(_mean_metric(model_rows, "cross_sample_excess_mnats_per_window")),
                    _fmt_signed_float(_mean_metric(model_rows, "cross_sample_excess_delta_mnats_vs_baseline")),
                    _fmt_signed_float(_mean_metric(model_rows, "cross_sample_pseudo_delta_bits_per_shot_vs_baseline")),
                    _fmt_signed_float(_mean_metric(model_rows, "cross_sample_logical_excess_delta_mnats_vs_baseline")),
                    _fmt_float(_mean_metric(model_rows, "cross_sample_logical_flip_calibration")),
                    _fmt_float(_mean_metric(model_rows, "cross_sample_detector_rate_MAE")),
                ]
            )
        _print_table(
            ["model", "n", "ex_mn", "d_mn", "d_bit/shot", "log_d_mn", "log_cal", "det_mae"],
            rows,
        )


def _sort_records(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    order = {"local": 0, "dmle_qec": 1, "hard_orbit": 2, "soft_feature_orbit": 3}
    return sorted(records, key=lambda record: order.get(str(record.get("model")), 99))


def _group_by_model(records: list[dict[str, object]]) -> list[tuple[str, list[dict[str, object]]]]:
    groups: dict[str, list[dict[str, object]]] = {}
    for record in records:
        if not bool(record.get("transfer_evaluated", True)):
            continue
        groups.setdefault(str(record.get("model")), []).append(record)
    return [(model, groups[model]) for model in sorted(groups)]


def _mean_metric(records: list[dict[str, object]], key: str) -> float | None:
    values = [float(record[key]) for record in records if record.get(key) is not None]
    return sum(values) / len(values) if values else None


def _print_table(headers: list[str], rows: list[list[object]]) -> None:
    if not rows:
        print("  (none)")
        return
    string_rows = [[_cell(value) for value in row] for row in rows]
    widths = [
        max(len(headers[col]), *(len(row[col]) for row in string_rows))
        for col in range(len(headers))
    ]
    print("  " + "  ".join(headers[col].ljust(widths[col]) for col in range(len(headers))))
    print("  " + "  ".join("-" * width for width in widths))
    for row in string_rows:
        print("  " + "  ".join(row[col].ljust(widths[col]) for col in range(len(headers))))


def _fmt_float(value: object, *, precision: int = 4) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) >= 100:
        return f"{number:.2f}"
    if abs(number) >= 10:
        return f"{number:.3f}"
    return f"{number:.{precision}g}"


def _fmt_signed_float(value: object, *, precision: int = 4) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) < 10 ** (-(precision + 1)):
        return "0"
    return f"{number:+.{precision}g}"


def _cell(value: object) -> str:
    if value is None:
        return "-"
    return str(value)


if __name__ == "__main__":
    main()
