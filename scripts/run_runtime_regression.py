#!/usr/bin/env python3
"""Run the current runtime against saved validation/regression suites."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SUITES: dict[str, dict[str, Any]] = {
    "ranker_guard_unknown_v01": {
        "features": "reports/evaluations/ranker-guard-unknown-validation-v01/features.jsonl",
        "targets": "reports/evaluations/ranker-guard-unknown-validation-v01/runtime-targets.jsonl",
        "checks": {
            "total_targets": 24,
            "gate_fp": 0,
            "gate_fn": 0,
            "known_positive_top1_accuracy": 1.0,
            "unknown_rejection_rate": 1.0,
            "safety_accuracy": 1.0,
            "strict_accuracy": 1.0,
        },
    },
    "multifamily_unseen_v01": {
        "features": "reports/evaluations/multifamily-unseen-validation-v01/unseen-multifamily-features.jsonl",
        "targets": "reports/evaluations/multifamily-unseen-validation-v01/runtime-targets.jsonl",
        "checks": {
            "total_targets": 10,
            "gate_fp": 0,
            "gate_fn": 0,
            "known_positive_top1_accuracy": 1.0,
            "safety_accuracy": 1.0,
            "strict_accuracy": 1.0,
        },
    },
    "unseen_solr_schema_v01": {
        "features": "reports/evaluations/unseen-solr-schema-validation-v01/unseen-solr-features.jsonl",
        "targets": "reports/evaluations/unseen-solr-schema-validation-v01/unseen-solr-runtime-targets.jsonl",
        "checks": {
            "total_targets": 4,
            "gate_fp": 0,
            "gate_fn": 0,
            "known_positive_top1_accuracy": 1.0,
            "safety_accuracy": 1.0,
            "strict_accuracy": 1.0,
        },
    },
}


def metric_view(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "total_targets": metrics["total_targets"],
        "gate_fp": metrics["gate_metrics"]["fp"],
        "gate_fn": metrics["gate_metrics"]["fn"],
        "known_positive_top1_accuracy": metrics["ranker_metrics"]["known_positive_top1_accuracy"],
        "unknown_rejection_rate": metrics["unknown_guard_metrics"]["unknown_rejection_rate"],
        "safety_accuracy": metrics["final_flow_metrics"]["safety_accuracy"],
        "strict_accuracy": metrics["final_flow_metrics"]["strict_accuracy"],
    }


def compare(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if isinstance(expected_value, float):
            if round(float(actual_value), 4) < expected_value:
                failures.append(f"{key}: expected >= {expected_value}, got {actual_value}")
        elif actual_value != expected_value:
            failures.append(f"{key}: expected {expected_value}, got {actual_value}")
    return failures


def run_suite(repo: Path, name: str, suite: dict[str, Any], model_dir: Path, out_root: Path) -> dict[str, Any]:
    features = repo / suite["features"]
    targets = repo / suite["targets"]
    out_dir = out_root / name
    if not features.exists() or not targets.exists():
        return {
            "suite": name,
            "status": "missing_inputs",
            "features": str(features),
            "targets": str(targets),
        }

    command = [
        sys.executable,
        str(repo / "scripts/evaluate_runtime_predictions.py"),
        "--features-jsonl",
        str(features),
        "--targets-jsonl",
        str(targets),
        "--model-dir",
        str(model_dir),
        "--out-dir",
        str(out_dir),
    ]
    subprocess.run(command, cwd=repo, check=True, text=True, capture_output=True)
    metrics_path = out_dir / "corrected-runtime-evaluation.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    actual = metric_view(metrics)
    failures = compare(actual, suite["checks"])
    return {
        "suite": name,
        "status": "pass" if not failures else "fail",
        "metrics": actual,
        "checks": suite["checks"],
        "failures": failures,
        "metrics_path": str(metrics_path),
    }


def write_markdown(path: Path, results: list[dict[str, Any]]) -> None:
    lines = [
        "# Runtime Regression Result",
        "",
        "| Suite | Status | Gate FP/FN | Ranker Top-1 | Unknown Reject | Safety | Strict |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        metrics = result.get("metrics") or {}
        lines.append(
            "| {suite} | {status} | {fp}/{fn} | {top1} | {unknown} | {safety} | {strict} |".format(
                suite=result["suite"],
                status=result["status"],
                fp=metrics.get("gate_fp", "-"),
                fn=metrics.get("gate_fn", "-"),
                top1=metrics.get("known_positive_top1_accuracy", "-"),
                unknown=metrics.get("unknown_rejection_rate", "-"),
                safety=metrics.get("safety_accuracy", "-"),
                strict=metrics.get("strict_accuracy", "-"),
            )
        )
    failures = [result for result in results if result["status"] != "pass"]
    lines.extend(["", "## Failures", ""])
    if failures:
        for result in failures:
            lines.append(f"### {result['suite']}")
            for failure in result.get("failures", [result["status"]]):
                lines.append(f"- {failure}")
    else:
        lines.append("- All regression suites passed.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default=Path("runtime/models/prototype"), type=Path)
    parser.add_argument("--out-dir", default=Path("reports/regression/runtime-current"), type=Path)
    parser.add_argument("--suite", choices=["all", *SUITES.keys()], default="all")
    args = parser.parse_args()

    repo = Path.cwd()
    model_dir = args.model_dir if args.model_dir.is_absolute() else repo / args.model_dir
    suites = SUITES if args.suite == "all" else {args.suite: SUITES[args.suite]}
    args.out_dir.mkdir(parents=True, exist_ok=True)

    results = [
        run_suite(repo, name, suite, model_dir, args.out_dir)
        for name, suite in suites.items()
    ]
    summary = {
        "total_suites": len(results),
        "passed": sum(1 for result in results if result["status"] == "pass"),
        "failed": sum(1 for result in results if result["status"] != "pass"),
        "results": results,
    }
    (args.out_dir / "runtime-regression-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_markdown(args.out_dir / "RUNTIME-REGRESSION-RESULT-TH.md", results)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
