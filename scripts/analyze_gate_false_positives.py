#!/usr/bin/env python3
"""Analyze false positives from a gate prediction CSV.

The gate training scripts already write one prediction row per target. This
helper joins those predictions back to the flat dataset so we can see which
active features pushed negative targets above the decision threshold.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FOCUS_FEATURES = [
    "version_in_vulnerable_range",
    "version_in_vulnerable_range_true",
    "version_in_vulnerable_range_false",
    "version_not_affected",
    "version_patched",
    "precondition_pass_count",
    "precondition_fail_count",
    "auth_required",
    "no_auth_required",
    "endpoint_reachable_count",
    "endpoint_missing_count",
    "anonymous_access",
    "velocity_enabled",
    "velocity_disabled",
    "velocity_endpoint_found",
    "velocity_template_accessible",
    "velocity_rce_candidate",
    "config_api_accessible",
    "config_api_blocked",
    "solr_detected",
    "solr_core_found",
    "known_family_signal_count",
    "precondition_positive_signal_count",
    "precondition_negative_signal_count",
    "precondition_signal_balance",
    "has_positive_precondition_signal",
    "has_negative_precondition_signal",
]


def truthy(value: str | None) -> bool:
    if value is None:
        return False
    try:
        return float(value) > 0
    except ValueError:
        return bool(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def analyze(dataset: Path, predictions: Path) -> dict[str, object]:
    rows_by_target = {row["target_id"]: row for row in read_csv(dataset)}
    prediction_rows = read_csv(predictions)
    false_positives = [
        row
        for row in prediction_rows
        if row["true_label"] == "0" and row["predicted_label"] == "1"
    ]

    details = []
    for prediction in false_positives:
        target_id = prediction["target_id"]
        row = rows_by_target[target_id]
        active_focus = {
            name: row.get(name, "0")
            for name in FOCUS_FEATURES
            if truthy(row.get(name))
        }
        likely_reason = "generic positive signals outweighed blocker"
        if truthy(row.get("velocity_disabled")) and not truthy(row.get("velocity_enabled")):
            likely_reason = "Solr Velocity is disabled but generic Solr/access signals pushed the score up"
        details.append(
            {
                "target_id": target_id,
                "probability": float(prediction["probability"]),
                "threshold": float(prediction["threshold"]),
                "active_focus_features": active_focus,
                "likely_reason_th": likely_reason,
            }
        )

    return {
        "dataset": str(dataset),
        "predictions": str(predictions),
        "false_positive_count": len(details),
        "false_positives": details,
        "recommendation_th": (
            "แก้ runtime/feature policy ให้ Solr ที่ velocity_disabled=1 และ velocity_enabled=0 "
            "ถูกลดเป็น low_confidence/no_exploit ก่อนส่งเข้า exploit verification"
        ),
    }


def write_report(result: dict[str, object], path: Path) -> None:
    rows = result["false_positives"]  # type: ignore[index]
    lines = [
        "# Gate False Positive Investigation",
        "",
        "## สรุป",
        "",
        f"พบ false positive {result['false_positive_count']} targets จาก prediction CSV",
        "",
        "| Target | Probability | เหตุผลหลัก |",
        "| --- | ---: | --- |",
    ]
    for row in rows:  # type: ignore[assignment]
        lines.append(
            f"| `{row['target_id']}` | {row['probability']:.4f} | {row['likely_reason_th']} |"
        )
    lines.extend(
        [
            "",
            "## วิธีอ่าน",
            "",
            "False positive คือ target ที่ label เป็น negative แต่ Gate ทายว่า likely exploitable",
            "",
            "ในรอบนี้ FP ทั้งหมดเกี่ยวกับ Solr และมี blocker สำคัญคือ `velocity_disabled=1`",
            "",
            "## Recommendation",
            "",
            str(result["recommendation_th"]),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args()

    result = analyze(args.dataset, args.predictions)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(result, args.out_md)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
