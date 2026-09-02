#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


FAMILY_ALIASES = {
    "redis_lua": "redis",
    "grafana_path_traversal": "grafana",
    "solr_velocity_rce": "solr_velocity",
    "couchdb_rce": "couchdb_auth",
}

UNKNOWN_FAMILIES = {
    "drupal_rce",
    "laravel_rce",
    "jetty_rce",
    "wordpress_rce",
    "php_cgi_rce",
    "jboss_rce",
}


def read_json_stream(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    rows: list[dict[str, object]] = []
    index = 0
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        value, next_index = decoder.raw_decode(text, index)
        if not isinstance(value, dict):
            raise ValueError(f"{path} contains a non-object JSON value")
        rows.append(value)
        index = next_index
    return rows


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def runtime_category(row: dict[str, object]) -> str:
    category = str(row.get("category") or "")
    family = str(row.get("expected_family") or "")
    status = str(row.get("expected_status") or row.get("validation_status") or "")
    if category == "positive" and family in UNKNOWN_FAMILIES:
        return "unknown_family"
    if category == "positive" or status == "validated_positive":
        return "known_positive"
    if category in {"negative", "weak"} or status in {
        "validated_negative",
        "no_exploit",
        "weak_no_exploit",
    }:
        return "negative_control"
    return "unknown_family"


def runtime_family(row: dict[str, object]) -> str:
    family = str(row.get("expected_family") or "unknown")
    if family in UNKNOWN_FAMILIES:
        return "unknown"
    return FAMILY_ALIASES.get(family, family)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", required=True, type=Path)
    args = parser.parse_args()

    stream_files = [
        "features.jsonl",
        "targets.jsonl",
        "validation-results.jsonl",
    ]
    for name in stream_files:
        rows = read_json_stream(args.report_dir / name)
        write_jsonl(args.report_dir / name, rows)
        print(f"normalized {name}: {len(rows)} rows")

    targets = read_json_stream(args.report_dir / "targets.jsonl")
    runtime_targets: list[dict[str, object]] = []
    for row in targets:
        runtime_targets.append(
            {
                "target_id": row["target_id"],
                "category": runtime_category(row),
                "expected_family": runtime_family(row),
                "source_expected_family": row.get("expected_family", "unknown"),
                "source_image": row.get("source_image", "unknown"),
                "validation_status": row.get("expected_status", row.get("validation_status", "unknown")),
            }
        )
    write_jsonl(args.report_dir / "runtime-targets.jsonl", runtime_targets)
    print(f"wrote runtime-targets.jsonl: {len(runtime_targets)} rows")


if __name__ == "__main__":
    main()
