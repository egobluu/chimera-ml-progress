#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


TOP_LEVEL_FILES = [
    "runtime-targets.jsonl",
    "runtime-predictions.jsonl",
    "runtime-metrics.json",
    "family-ranker-errors.csv",
    "unknown-family-guard-report.csv",
    "weak-noisy-report.csv",
    "REPORT-TH.md",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def copy_baseline(src: Path, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in TOP_LEVEL_FILES:
        source = src / name
        if source.exists() and source.is_file():
            shutil.copy2(source, dest / name)
            copied.append(name)
    return copied


def build_current_inputs(baseline_targets: Path, out_dir: Path) -> dict[str, Path]:
    rows = read_jsonl(baseline_targets)
    targets: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []

    for row in rows:
        target_id = row["target_id"]
        feature_row = dict(row.get("features") or {})
        feature_row["target_id"] = target_id
        features.append(feature_row)
        targets.append(
            {
                "target_id": target_id,
                "category": row["category"],
                "expected_family": row["expected_family"],
                "expected_family_raw": row.get("expected_family_raw"),
                "expected_status_raw": row.get("expected_status_raw"),
            }
        )

    inputs_dir = out_dir / "current-runtime-inputs"
    feature_path = inputs_dir / "features.jsonl"
    target_path = inputs_dir / "targets.jsonl"
    write_jsonl(feature_path, features)
    write_jsonl(target_path, targets)
    return {"features": feature_path, "targets": target_path}


def run_current_runtime(repo: Path, inputs: dict[str, Path], out_dir: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "evaluate_runtime_predictions.py"),
            "--features-jsonl",
            str(inputs["features"]),
            "--targets-jsonl",
            str(inputs["targets"]),
            "--model-dir",
            str(repo / "runtime" / "models" / "prototype"),
            "--out-dir",
            str(out_dir / "current-runtime"),
            "--top-k",
            "8",
        ],
        cwd=repo,
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument(
        "--out-dir",
        default=Path("reports/evaluations/shared-validation-runtime-v01"),
        type=Path,
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    out_dir = (repo / args.out_dir).resolve() if not args.out_dir.is_absolute() else args.out_dir
    baseline_dir = out_dir / "baseline-opencode"
    copied = copy_baseline(args.source, baseline_dir)
    inputs = build_current_inputs(baseline_dir / "runtime-targets.jsonl", out_dir)
    run_current_runtime(repo, inputs, out_dir)

    result = {
        "source": str(args.source),
        "out_dir": str(out_dir),
        "baseline_copied": copied,
        "current_inputs": {key: str(path) for key, path in inputs.items()},
        "current_runtime": str(out_dir / "current-runtime"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
