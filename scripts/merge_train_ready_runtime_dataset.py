#!/usr/bin/env python3
"""Merge strict train-ready runtime JSONL rows into the CSV training dataset."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


POSITIVE_CATEGORIES = {"known_positive", "unknown_family"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: row must be an object")
        rows.append(row)
    return rows


def as_number(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "0"
    text = str(value).strip()
    if not text:
        return "0"
    try:
        float(text)
    except ValueError:
        return "0"
    return text


def label_for(target: dict[str, Any]) -> str:
    return "1" if str(target.get("category") or "") in POSITIVE_CATEGORIES else "0"


def build_added_rows(
    features: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    fieldnames: list[str],
) -> list[dict[str, str]]:
    target_by_id = {str(row["target_id"]): row for row in targets}
    output: list[dict[str, str]] = []
    for feature in features:
        target_id = str(feature["target_id"])
        target = target_by_id.get(target_id)
        if target is None:
            raise ValueError(f"missing runtime target for {target_id}")
        row = {name: "0" for name in fieldnames}
        row["target_id"] = target_id
        row["label"] = label_for(target)
        for name in fieldnames:
            if name in {"target_id", "label"}:
                continue
            if name in feature:
                row[name] = as_number(feature[name])
        output.append(row)
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# Candidate Runtime Dataset Merge

## Summary

| Item | Count |
| --- | ---: |
| Base rows | {summary['base_rows']} |
| Added train-ready rows | {summary['added_rows']} |
| Output rows | {summary['output_rows']} |
| Output columns | {summary['columns']} |

## Label Counts

```json
{json.dumps(summary['label_counts'], ensure_ascii=False, indent=2)}
```

## Input

- Base dataset: `{summary['base_dataset']}`
- Added features: `{summary['added_features']}`
- Added targets: `{summary['added_targets']}`

## Decision

นี่คือ candidate training dataset สำหรับ experiment เท่านั้น ยังไม่ใช่ production promote
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-csv", required=True, type=Path)
    parser.add_argument("--features-jsonl", required=True, type=Path)
    parser.add_argument("--targets-jsonl", required=True, type=Path)
    parser.add_argument("--out-csv", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    with args.base_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("base CSV has no header")
        fieldnames = list(reader.fieldnames)
        base_rows = list(reader)

    features = read_jsonl(args.features_jsonl)
    targets = read_jsonl(args.targets_jsonl)
    added_rows = build_added_rows(features, targets, fieldnames)
    output_rows = base_rows + added_rows

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    label_counts: dict[str, int] = {}
    for row in output_rows:
        label_counts[row["label"]] = label_counts.get(row["label"], 0) + 1
    summary = {
        "base_dataset": str(args.base_csv),
        "added_features": str(args.features_jsonl),
        "added_targets": str(args.targets_jsonl),
        "base_rows": len(base_rows),
        "added_rows": len(added_rows),
        "output_rows": len(output_rows),
        "columns": len(fieldnames),
        "label_counts": dict(sorted(label_counts.items())),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(args.report.with_suffix(".md"), summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
