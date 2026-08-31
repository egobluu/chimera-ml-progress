#!/usr/bin/env python3
"""Audit exploitability gate features for leakage and weak real-world behavior.

This script does not train a model. It reads the gate dataset and reports
which features separate positive/negative labels too perfectly, which features
are likely post-verification signals, and which features are safer for a real
precheck decision.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean


ID_COLUMNS = {"target_id", "label"}

# These features are usually known only after exploit validation or after a
# curated failure note is written. They are useful as feedback, but risky as
# first-pass model inputs.
POSTCHECK_OR_LEAK_RISK = {
    "tool_metasploit_success",
    "msf_check_confirmed",
    "msf_check_not_vulnerable",
    "rce_confirmed",
    "manual_poc_failed",
    "negative_evidence_count",
}

# These features are acceptable only if a repeatable scanner/probe generates
# them before the model makes its exploit/no_exploit decision.
CONDITIONAL_PRECHECK = {
    "nuclei_cve_confirmed",
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
    "method_put_allowed",
    "method_put_rejected",
    "ajp_port_open",
    "ajp_port_closed",
    "anonymous_access",
    "velocity_enabled",
    "invokefunction_reachable",
    "invokefunction_not_found",
    "admin_party_enabled",
    "spring_detected",
    "spring_not_detected",
    "wrong_software_type",
    "nuclei_fingerprint_only",
    "nuclei_no_vuln_found",
    "painless_sandbox_blocks",
    "path_traversal_blocked",
    "auth_blocks_exploit",
    "endpoint_not_found",
    "wrong_version",
    "no_msf_module",
}


def to_float(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def feature_phase(feature: str) -> str:
    if feature in POSTCHECK_OR_LEAK_RISK:
        return "postcheck_or_leak_risk"
    if feature in CONDITIONAL_PRECHECK:
        return "conditional_precheck"
    return "safe_basic_precheck"


def summarize_features(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    features = [name for name in rows[0].keys() if name not in ID_COLUMNS]
    output: list[dict[str, object]] = []

    for feature in features:
        pos = [to_float(row.get(feature)) for row in rows if row["label"] == "1"]
        neg = [to_float(row.get(feature)) for row in rows if row["label"] == "0"]
        pos_nonzero = sum(value != 0 for value in pos)
        neg_nonzero = sum(value != 0 for value in neg)
        separates_positive = pos_nonzero > 0 and neg_nonzero == 0
        separates_negative = neg_nonzero > 0 and pos_nonzero == 0

        output.append(
            {
                "feature": feature,
                "phase": feature_phase(feature),
                "pos_nonzero": pos_nonzero,
                "neg_nonzero": neg_nonzero,
                "pos_avg": round(mean(pos), 4) if pos else 0,
                "neg_avg": round(mean(neg), 4) if neg else 0,
                "perfect_label_separator": separates_positive or separates_negative,
                "separator_direction": (
                    "positive_only"
                    if separates_positive
                    else "negative_only"
                    if separates_negative
                    else "mixed_or_unused"
                ),
            }
        )

    return output


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, dataset_path: Path, rows: list[dict[str, str]], feature_rows: list[dict[str, object]]) -> None:
    positive = sum(row["label"] == "1" for row in rows)
    negative = sum(row["label"] == "0" for row in rows)
    phase_counts: dict[str, int] = {}
    for row in feature_rows:
        phase_counts[row["phase"]] = phase_counts.get(row["phase"], 0) + 1

    suspicious = [
        row
        for row in feature_rows
        if row["perfect_label_separator"] and row["phase"] == "postcheck_or_leak_risk"
    ]
    conditional = [
        row
        for row in feature_rows
        if row["perfect_label_separator"] and row["phase"] == "conditional_precheck"
    ]

    lines = [
        "# ML Gate Feature Audit",
        "",
        f"- dataset: `{dataset_path}`",
        f"- targets: {len(rows)}",
        f"- validated_positive: {positive}",
        f"- validated_negative: {negative}",
        f"- features: {len(feature_rows)}",
        "",
        "## Feature Phase Count",
        "",
    ]
    for phase, count in sorted(phase_counts.items()):
        lines.append(f"- `{phase}`: {count}")

    lines.extend(
        [
            "",
            "## จุดเสี่ยงที่ต้องระวัง",
            "",
            "`postcheck_or_leak_risk` คือ feature ที่มักรู้หลังจากยิง Metasploit/manual PoC หรือหลังเขียนผลยืนยันแล้ว ถ้าเอาไปใช้ก่อนตัดสินใจจริง คะแนนจะสวยเกินจริง",
            "",
        ]
    )
    if suspicious:
        lines.append("| feature | direction | pos_nonzero | neg_nonzero | pos_avg | neg_avg |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
        for row in suspicious:
            lines.append(
                f"| `{row['feature']}` | {row['separator_direction']} | {row['pos_nonzero']} | {row['neg_nonzero']} | {row['pos_avg']} | {row['neg_avg']} |"
            )
    else:
        lines.append("- ไม่พบ postcheck/leak-risk feature ที่แยก label แบบ perfect")

    lines.extend(
        [
            "",
            "## Feature ที่ใช้ได้แบบมีเงื่อนไข",
            "",
            "กลุ่มนี้ใช้ได้ถ้าเกิดจาก scanner/probe ที่รันก่อน model ตัดสินใจ และต้องเก็บด้วยวิธีเดียวกันทุก target",
            "",
        ]
    )
    if conditional:
        lines.append("| feature | direction | pos_nonzero | neg_nonzero | pos_avg | neg_avg |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
        for row in conditional:
            lines.append(
                f"| `{row['feature']}` | {row['separator_direction']} | {row['pos_nonzero']} | {row['neg_nonzero']} | {row['pos_avg']} | {row['neg_avg']} |"
            )
    else:
        lines.append("- ไม่พบ conditional precheck feature ที่แยก label แบบ perfect")

    lines.extend(
        [
            "",
            "## ข้อสรุป",
            "",
            "- ถ้าโมเดลได้ใช้ `negative_evidence_count`, `msf_check_confirmed`, หรือ `manual_poc_failed` ก่อนยิงจริง ผล 1.000 ยังถือว่าไม่พิสูจน์ความแม่น",
            "- baseline ที่ควรวัดต่อคือ `strict_precheck`: ตัด postcheck/leak-risk features ออกก่อน train",
            "- งานถัดไปคือทำ holdout target ใหม่ 5-10 ตัว โดยให้ model ทำนายก่อน แล้วค่อยใช้ Metasploit/manual PoC ตรวจคำตอบ",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    rows = load_rows(args.dataset)
    if not rows:
        raise SystemExit("dataset is empty")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    feature_rows = summarize_features(rows)
    write_csv(args.out_dir / "gate-feature-audit.csv", feature_rows)
    write_markdown(args.out_dir / "ML-GATE-FEATURE-AUDIT-TH.md", args.dataset, rows, feature_rows)
    print(json.dumps({"targets": len(rows), "features": len(feature_rows), "out_dir": str(args.out_dir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
