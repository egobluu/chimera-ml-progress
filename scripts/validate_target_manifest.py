#!/usr/bin/env python3
"""Validate a planned scanner target manifest before handing it to OpenCode."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "target_id",
    "category",
    "expected_family",
    "runtime_family",
    "cve_candidates",
    "source",
    "source_hint",
    "required_features",
    "blocking_features",
}

ALLOWED_CATEGORIES = {"positive", "negative", "weak", "unknown_family"}


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


def validate(rows: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    ids = [str(row.get("target_id") or "") for row in rows]
    duplicate_ids = sorted(target_id for target_id, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate target_id: {', '.join(duplicate_ids)}")

    for index, row in enumerate(rows, start=1):
        missing = sorted(field for field in REQUIRED_FIELDS if field not in row)
        if missing:
            errors.append(f"row {index} missing fields: {', '.join(missing)}")
        category = str(row.get("category") or "")
        if category not in ALLOWED_CATEGORIES:
            errors.append(f"row {index} invalid category: {category}")
        for list_field in ("cve_candidates", "required_features", "blocking_features"):
            if list_field in row and not isinstance(row[list_field], list):
                errors.append(f"row {index} {list_field} must be a list")

    categories = Counter(str(row.get("category") or "") for row in rows)
    families = Counter(str(row.get("runtime_family") or "") for row in rows)
    summary = {
        "total": len(rows),
        "categories": dict(sorted(categories.items())),
        "runtime_families": dict(sorted(families.items())),
        "duplicate_ids": duplicate_ids,
    }
    return errors, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    rows = read_jsonl(args.manifest)
    errors, summary = validate(rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
