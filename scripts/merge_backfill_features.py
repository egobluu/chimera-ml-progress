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
SKIP_FEATURE_SUFFIXES = ("_version_detected",)


def should_skip_feature(feature: str) -> bool:
    return feature in SKIP_FEATURES or feature.endswith(SKIP_FEATURE_SUFFIXES)


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


def iter_jsonl_lines(path: Path | None, directory: Path | None, pattern: str) -> list[str]:
    lines: list[str] = []
    if path is not None:
        lines.extend(path.read_text(encoding="utf-8").splitlines())
    if directory is not None:
        for item in sorted(directory.rglob(pattern)):
            lines.extend(item.read_text(encoding="utf-8").splitlines())
    return lines


def load_backfill(
    lines: list[str],
    require_consistent: bool = False,
    allow_targets: set[str] | None = None,
) -> tuple[dict[str, dict[str, float]], list[str], int, int]:
    by_target: dict[str, dict[str, float]] = {}
    labels_by_target: dict[str, int] = {}
    feature_names: set[str] = set()
    skipped_inconsistent = 0
    skipped_disallowed_target = 0
    for line in lines:
        if not line.strip():
            continue
        item = json.loads(line)
        target_id = item["target_id"]
        expected_family = str(item.get("expected_family", ""))
        labels_by_target.setdefault(target_id, 0 if expected_family == "no_exploit" else 1)
        if allow_targets is not None and target_id not in allow_targets:
            skipped_disallowed_target += 1
            continue
        if require_consistent and item.get("label_consistency") != "consistent":
            skipped_inconsistent += 1
            continue
        feature = item.get("feature_name")
        if not feature or should_skip_feature(feature):
            continue
        value = numeric_value(item.get("feature_value"))
        if value is None:
            continue
        by_target.setdefault(target_id, {})[feature] = value
        feature_names.add(feature)
    by_target["__labels__"] = {target: float(label) for target, label in labels_by_target.items()}
    return by_target, sorted(feature_names), skipped_inconsistent, skipped_disallowed_target


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
    parser.add_argument("--backfill-jsonl", type=Path)
    parser.add_argument("--backfill-dir", type=Path)
    parser.add_argument("--backfill-glob", default="*.jsonl")
    parser.add_argument("--out-csv", required=True, type=Path)
    parser.add_argument("--summary-json", required=True, type=Path)
    parser.add_argument(
        "--require-consistent",
        action="store_true",
        help="Only merge feature records with label_consistency=consistent.",
    )
    parser.add_argument(
        "--allow-targets",
        default="",
        help="Comma-separated target_id allow-list. Use this when a run contains quarantined targets.",
    )
    parser.add_argument(
        "--append-new-targets",
        action="store_true",
        help="Append allowed backfill targets that are not already present in the base dataset.",
    )
    args = parser.parse_args()
    if args.backfill_jsonl is None and args.backfill_dir is None:
        parser.error("one of --backfill-jsonl or --backfill-dir is required")

    rows, base_fields = load_base(args.base_dataset)
    allow_targets = {target.strip() for target in args.allow_targets.split(",") if target.strip()} or None
    backfill_lines = iter_jsonl_lines(args.backfill_jsonl, args.backfill_dir, args.backfill_glob)
    backfill, backfill_fields, skipped_inconsistent, skipped_disallowed_target = load_backfill(
        backfill_lines,
        require_consistent=args.require_consistent,
        allow_targets=allow_targets,
    )
    labels_by_target = {target: int(label) for target, label in backfill.pop("__labels__", {}).items()}
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

    appended_new_targets: list[str] = []
    if args.append_new_targets:
        existing_targets = {row["target_id"] for row in rows}
        for target_id in sorted(backfill):
            if target_id in existing_targets:
                continue
            merged = {field: "0" for field in merged_fields}
            merged["target_id"] = target_id
            merged["label"] = str(labels_by_target.get(target_id, 0))
            for feature, value in backfill[target_id].items():
                merged[feature] = str(int(value)) if value.is_integer() else str(value)
            add_missing_defaults(merged, backfill_fields, has_backfill=True)
            merged_rows.append(merged)
            appended_new_targets.append(target_id)

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=merged_fields)
        writer.writeheader()
        writer.writerows(merged_rows)

    summary = {
        "base_targets": len(rows),
        "targets_with_backfill": targets_with_backfill,
        "targets_without_backfill": len(rows) - targets_with_backfill,
        "appended_new_targets": appended_new_targets,
        "base_features": len(base_fields) - 2,
        "backfill_numeric_features": len(backfill_fields),
        "skipped_inconsistent_records": skipped_inconsistent,
        "skipped_disallowed_target_records": skipped_disallowed_target,
        "require_consistent": args.require_consistent,
        "allow_targets": sorted(allow_targets) if allow_targets else [],
        "merged_features": len(merged_fields) - 2,
        "output_csv": str(args.out_csv),
    }
    args.summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
