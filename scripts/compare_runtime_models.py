#!/usr/bin/env python3
"""Compare two runtime regression summaries and write a promotion report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


KEYS = [
    "gate_fp",
    "gate_fn",
    "known_positive_top1_accuracy",
    "unknown_rejection_rate",
    "safety_accuracy",
    "strict_accuracy",
]


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def by_suite(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["suite"]): row for row in summary["results"]}


def gate_train_metrics(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "train_targets": manifest["gate"]["train_targets"],
        "positive_train_targets": manifest["ranker"]["positive_train_targets"],
        "gate_loo_metrics": manifest["gate"]["loo_metrics"],
        "candidate_families": manifest["ranker"]["candidate_families"],
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Candidate Runtime Model Comparison",
        "",
        "## Training Metrics",
        "",
        "| Model | Train targets | Ranker positive targets | Gate precision | Gate recall | Gate F1 | Gate FP/FN |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label in ("baseline", "candidate"):
        metrics = report[f"{label}_training"]
        gate = metrics["gate_loo_metrics"]
        lines.append(
            f"| {label} | {metrics['train_targets']} | {metrics['positive_train_targets']} | "
            f"{gate['precision']} | {gate['recall']} | {gate['f1']} | {gate['fp']}/{gate['fn']} |"
        )

    lines.extend([
        "",
        "## Regression Comparison",
        "",
        "| Suite | Baseline safety | Candidate safety | Baseline strict | Candidate strict | Candidate status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ])
    for row in report["suite_comparison"]:
        lines.append(
            f"| {row['suite']} | {row['baseline'].get('safety_accuracy', '-')} | "
            f"{row['candidate'].get('safety_accuracy', '-')} | {row['baseline'].get('strict_accuracy', '-')} | "
            f"{row['candidate'].get('strict_accuracy', '-')} | {row['candidate_status']} |"
        )

    lines.extend([
        "",
        "## Decision",
        "",
        report["decision_th"],
        "",
        "## Notes",
        "",
        "- Candidate model trained from base 67 rows + 14 strict train-ready rows from Vulhub 50 scan.",
        "- The remaining 37 rows stay validation-only until raw evidence is filled in.",
        "- Do not promote automatically just because the small train-ready subset scores 100%.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-summary", required=True, type=Path)
    parser.add_argument("--candidate-summary", required=True, type=Path)
    parser.add_argument("--baseline-manifest", required=True, type=Path)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    args = parser.parse_args()

    baseline = by_suite(load_summary(args.baseline_summary))
    candidate = by_suite(load_summary(args.candidate_summary))
    suites = sorted(set(baseline) | set(candidate))
    comparison = []
    failures: list[str] = []
    for suite in suites:
        base_metrics = (baseline.get(suite) or {}).get("metrics", {})
        candidate_row = candidate.get(suite) or {}
        candidate_metrics = candidate_row.get("metrics", {})
        row = {
            "suite": suite,
            "baseline": {key: base_metrics.get(key) for key in KEYS},
            "candidate": {key: candidate_metrics.get(key) for key in KEYS},
            "candidate_status": candidate_row.get("status", "missing"),
        }
        comparison.append(row)
        if row["candidate_status"] != "pass":
            failures.append(f"{suite}: candidate status is {row['candidate_status']}")
        if candidate_metrics.get("gate_fn", 1) != 0:
            failures.append(f"{suite}: candidate gate_fn is {candidate_metrics.get('gate_fn')}")
        if float(candidate_metrics.get("safety_accuracy", 0)) < 1.0:
            failures.append(f"{suite}: candidate safety_accuracy is {candidate_metrics.get('safety_accuracy')}")
        if float(candidate_metrics.get("unknown_rejection_rate", 1.0)) < float(base_metrics.get("unknown_rejection_rate", 0)):
            failures.append(f"{suite}: candidate unknown rejection regressed")

    decision = (
        "Candidate ผ่าน gate promotion ขั้นต้น: regression ทุก suite ผ่าน, Gate FN เป็น 0, และ safety ไม่ถอยหลัง "
        "แต่ยังควร promote เป็น candidate/staging ก่อน ไม่ใช่ production ถาวร เพราะข้อมูลเพิ่มมี strict raw evidence เพียง 14 rows"
        if not failures
        else "ยังไม่ควร promote เพราะพบ regression: " + "; ".join(failures)
    )
    report = {
        "baseline_training": gate_train_metrics(args.baseline_manifest),
        "candidate_training": gate_train_metrics(args.candidate_manifest),
        "suite_comparison": comparison,
        "failures": failures,
        "promotion_gate_passed": not failures,
        "decision_th": decision,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(args.out_json.with_suffix(".md"), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
