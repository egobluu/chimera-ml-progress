#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


TOP_LEVEL_FILES = [
    "UNSEEN-MULTIFAMILY-VALIDATION-TH.md",
    "validation-results.jsonl",
    "safe-to-merge-targets.txt",
    "quarantined-targets.txt",
    "label-consistency-audit.jsonl",
    "unseen-multifamily-targets.jsonl",
]

FAMILY_ALIASES = {
    "redis_lua": "redis",
    "grafana_path_traversal": "grafana",
    "couchdb": "couchdb_auth",
    "couchdb_rce": "couchdb_auth",
}


def read_json_objects(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    rows: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        obj, end = decoder.raw_decode(text, index)
        rows.append(obj)
        index = end
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def prepare(source: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in TOP_LEVEL_FILES:
        path = source / name
        if path.exists() and path.is_file():
            shutil.copy2(path, out_dir / name)
            copied.append(name)

    features = read_json_objects(source / "unseen-multifamily-features.jsonl")
    write_jsonl(out_dir / "unseen-multifamily-features.jsonl", features)

    targets: list[dict[str, Any]] = []
    for row in read_json_objects(source / "unseen-multifamily-targets.jsonl"):
        expected_status = str(row.get("expected_status", ""))
        source_family = str(row.get("expected_family", "none"))
        targets.append(
            {
                "target_id": row["target_id"],
                "category": "known_positive"
                if expected_status == "validated_positive"
                else "negative_control",
                "expected_family": FAMILY_ALIASES.get(source_family, source_family),
                "source_expected_family": source_family,
                "source_image": row.get("source"),
                "validation_status": expected_status,
            }
        )
    write_jsonl(out_dir / "runtime-targets.jsonl", targets)
    return {
        "source": str(source),
        "out_dir": str(out_dir),
        "copied": copied,
        "features": len(features),
        "targets": len(targets),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument(
        "--out-dir",
        default=Path("reports/evaluations/multifamily-unseen-validation-v01"),
        type=Path,
    )
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.out_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
