#!/usr/bin/env python3
"""Merge light backfill precheck features into the v0.2 gate dataset.

The backfill JSONL contains one row per feature. This script pivots those rows
into target-level numeric columns, adds missing flags for targets without
backfill data, and keeps postcheck/leak-risk features unchanged so the profile
trainer can compare full vs strict precheck behavior.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


BACKFILL_TOOLS = ("whatweb", "curl", "ffuf", "content_discovery")
SKIP_FEATURES = {"detected_product", "detected_version"}


def numeric_value(value: object) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, int | float):
        return float(value)
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return None


def load_base(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def load_backfill(path: Path, require_consistent: bool = False) -> tuple[dict[str, dict[str, float]], list[str], int]:
    by_target: dict[str, dict[str, float]] = {}
    feature_names: set[str] = set()
    skipped_inconsistent = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            if require_consistent and item.get("label_consistency") != "consistent":
                skipped_inconsistent += 1
                continue
            feature = item.get("feature_name")
            if not feature or feature in SKIP_FEATURES:
                continue
            value = numeric_value(item.get("feature_value"))
            if value is None:
                continue
            target_id = item["target_id"]
            by_target.setdefault(target_id, {})[feature] = value
            feature_names.add(feature)
    return by_target, sorted(feature_names), skipped_inconsistent


def add_missing_defaults(row: dict[str, str], feature_names: list[str], has_backfill: bool) -> None:
    for feature in feature_names:
        row.setdefault(feature, "0")

    for tool in BACKFILL_TOOLS:
        missing_name = f"{tool}_missing"
        was_run_name = f"{tool}_was_run"
        if missing_name in feature_names:
            row[missing_name] = "0" if has_backfill else "1"
        if was_run_name in feature_names:
            row[was_run_name] = row.get(was_run_name, "0") if has_backfill else "0"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dataset", required=True, type=Path)
    parser.add_argument("--backfill-jsonl", required=True, type=Path)
    parser.add_argument("--out-csv", required=True, type=Path)
    parser.add_argument("--summary-json", required=True, type=Path)
    parser.add_argument(
        "--require-consistent",
        action="store_true",
        help="Only merge feature records with label_consistency=consistent.",
    )
    args = parser.parse_args()

    rows, base_fields = load_base(args.base_dataset)
    backfill, backfill_fields, skipped_inconsistent = load_backfill(args.backfill_jsonl, require_consistent=args.require_consistent)
    merged_fields = base_fields + [name for name in backfill_fields if name not in base_fields]

    merged_rows: list[dict[str, str]] = []
    targets_with_backfill = 0
    for row in rows:
        target_id = row["target_id"]
        extras = backfill.get(target_id, {})
        has_backfill = bool(extras)
        if has_backfill:
            targets_with_backfill += 1
        merged = dict(row)
        for feature, value in extras.items():
            merged[feature] = str(int(value)) if value.is_integer() else str(value)
        add_missing_defaults(merged, backfill_fields, has_backfill)
        merged_rows.append(merged)

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=merged_fields)
        writer.writeheader()
        writer.writerows(merged_rows)

    summary = {
        "base_targets": len(rows),
        "targets_with_backfill": targets_with_backfill,
        "targets_without_backfill": len(rows) - targets_with_backfill,
        "base_features": len(base_fields) - 2,
        "backfill_numeric_features": len(backfill_fields),
        "skipped_inconsistent_records": skipped_inconsistent,
        "require_consistent": args.require_consistent,
        "merged_features": len(merged_fields) - 2,
        "output_csv": str(args.out_csv),
    }
    args.summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
