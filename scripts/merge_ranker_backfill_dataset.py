#!/usr/bin/env python3
"""Merge safe family-ranker backfill records into the target-level CSV dataset.

Backfill files from Kali/OpenCode are JSONL because they are produced per scan
run. The training scripts expect one flat CSV row per target. This script keeps
the original dataset columns, appends any new backfill columns, and writes a
small merge report so we can audit exactly what entered training.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def normalize_value(value: object) -> str:
    if value is True:
        return "1"
    if value is False or value is None:
        return "0"
    return str(value)


def backfill_to_dataset_row(record: dict[str, object], fieldnames: list[str]) -> dict[str, str]:
    target_id = str(record["target_id"])
    row = {name: "0" for name in fieldnames}
    row["target_id"] = target_id
    row["label"] = "1" if record.get("expected_status") == "validated_positive" else "0"

    for key, value in record.items():
        if key in {"expected_family", "expected_status"}:
            continue
        if key in row:
            row[key] = normalize_value(value)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dataset", required=True, type=Path)
    parser.add_argument("--backfill-jsonl", required=True, type=Path)
    parser.add_argument("--audit-jsonl", required=True, type=Path)
    parser.add_argument("--out-csv", required=True, type=Path)
    parser.add_argument("--summary-json", required=True, type=Path)
    args = parser.parse_args()

    with args.base_dataset.open(encoding="utf-8", newline="") as handle:
        base_rows = list(csv.DictReader(handle))
    if not base_rows:
        raise ValueError("base dataset has no rows")

    audit_by_target = {str(row["target_id"]): row for row in read_jsonl(args.audit_jsonl)}
    safe_records = []
    skipped_records = []
    for record in read_jsonl(args.backfill_jsonl):
        target_id = str(record["target_id"])
        audit = audit_by_target.get(target_id, {})
        if audit.get("safe_to_merge") is True:
            safe_records.append(record)
        else:
            skipped_records.append(
                {
                    "target_id": target_id,
                    "reason": audit.get("reason_th") or "safe_to_merge is not true",
                }
            )

    existing_fields = list(base_rows[0].keys())
    new_fields = sorted(
        {
            key
            for record in safe_records
            for key in record
            if key not in existing_fields and key not in {"expected_family", "expected_status"}
        }
    )
    fieldnames = existing_fields + new_fields

    output_by_target = {row["target_id"]: {name: row.get(name, "0") for name in fieldnames} for row in base_rows}
    replaced_targets: list[str] = []
    appended_targets: list[str] = []
    for record in safe_records:
        row = backfill_to_dataset_row(record, fieldnames)
        target_id = row["target_id"]
        if target_id in output_by_target:
            replaced_targets.append(target_id)
        else:
            appended_targets.append(target_id)
        output_by_target[target_id] = row

    output_rows = list(output_by_target.values())
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    summary = {
        "base_dataset": str(args.base_dataset),
        "backfill_jsonl": str(args.backfill_jsonl),
        "base_rows": len(base_rows),
        "output_rows": len(output_rows),
        "safe_records": len(safe_records),
        "skipped_records": skipped_records,
        "appended_targets": sorted(appended_targets),
        "replaced_targets": sorted(replaced_targets),
        "new_columns": new_fields,
        "note_th": (
            "ถ้า target จาก unseen validation ถูกนำเข้า train แล้ว ห้ามใช้ target เดิมนั้น"
            " เป็นหลักฐาน unseen evaluation รอบถัดไป"
        ),
    }
    args.summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
