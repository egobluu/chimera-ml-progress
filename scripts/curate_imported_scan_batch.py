#!/usr/bin/env python3
"""Curate an imported scanner batch into train/validation/recheck splits."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


STANDARD_SAFE_STATUSES = {
    "validated_positive",
    "validated_negative",
    "no_exploit",
    "weak_no_exploit",
}

IMAGE_MISSING_MARKERS = (
    "image missing",
    "images missing",
    "some images missing",
)


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def read_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def runtime_results(path: Path) -> dict[str, dict[str, Any]]:
    metrics = json.loads(path.read_text(encoding="utf-8"))
    return {str(row["target_id"]): row for row in metrics["per_target_results"]}


def raw_target_ids(raw_dir: Path | None) -> set[str]:
    if raw_dir is None or not raw_dir.exists():
        return set()
    return {item.name for item in raw_dir.iterdir() if item.is_dir()}


def report_mentions_missing_images(report_path: Path) -> bool:
    if not report_path.exists():
        return False
    text = report_path.read_text(encoding="utf-8", errors="ignore").lower()
    return any(marker in text for marker in IMAGE_MISSING_MARKERS)


def target_curation_reason(
    target: dict[str, Any],
    feature: dict[str, Any] | None,
    validation: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    safe_ids: set[str],
    raw_ids: set[str],
    report_has_missing_images: bool,
) -> tuple[str, list[str]]:
    target_id = str(target["target_id"])
    reasons: list[str] = []

    if feature is None:
        reasons.append("missing feature row")
    if validation is None:
        reasons.append("missing validation row")
    if runtime is None:
        reasons.append("missing runtime evaluation row")
    if target_id not in safe_ids:
        reasons.append("not listed in safe-to-merge-targets.txt")

    status = str((validation or {}).get("status") or target.get("validation_status") or "")
    if status and status not in STANDARD_SAFE_STATUSES:
        reasons.append(f"non-standard validation status: {status}")

    if runtime is not None and not bool(runtime.get("strict_flow_correct")):
        reasons.append("runtime strict flow failed")

    has_raw = target_id in raw_ids
    if not has_raw:
        reasons.append("missing raw evidence folder")

    if report_has_missing_images and not has_raw:
        reasons.append("scanner report mentioned missing images; raw evidence required before train")

    if any(reason.startswith("missing feature") or reason.startswith("missing validation") for reason in reasons):
        return "needs_recheck", reasons
    if runtime is not None and not bool(runtime.get("strict_flow_correct")):
        return "needs_recheck", reasons
    if not has_raw:
        return "validation_only", reasons
    return "train_ready_strict", reasons or ["raw evidence present and runtime strict flow passed"]


def write_markdown(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    split_counts = summary["split_counts"]
    lines = [
        "# Imported Scan Batch Curation",
        "",
        "เอกสารนี้แยกข้อมูลหลัง import ว่า target ไหนพร้อมเข้า train จริง และ target ไหนควรใช้เป็น validation/recheck ก่อน",
        "",
        "## Summary",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| Total rows | {summary['total_rows']} |",
        f"| train_ready_strict | {split_counts.get('train_ready_strict', 0)} |",
        f"| validation_only | {split_counts.get('validation_only', 0)} |",
        f"| needs_recheck | {split_counts.get('needs_recheck', 0)} |",
        f"| raw evidence folders | {summary['raw_evidence_count']} |",
        "",
        "## Runtime Categories",
        "",
        "```json",
        json.dumps(summary["category_counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## แปลแบบง่าย",
        "",
        "- `train_ready_strict`: มี raw evidence จริง, label ไม่พัง, runtime strict ผ่าน ใช้ train/validation ได้หลังคนตรวจ raw",
        "- `validation_only`: runtime ผ่าน แต่ raw evidence ยังไม่ครบ ใช้ทดสอบ regression ได้ก่อน อย่าเพิ่ง train",
        "- `needs_recheck`: ข้อมูลหายหรือ runtime ไม่ผ่าน ต้องกลับไปสแกน/แก้ label",
        "",
        "## Targets",
        "",
        "| Target | Split | Category | Runtime family | Reasons |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        reasons = "; ".join(str(reason) for reason in row["curation_reasons"])
        lines.append(
            f"| `{row['target_id']}` | `{row['curation_split']}` | `{row['runtime_category']}` | `{row['runtime_family']}` | {reasons} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-dir", required=True, type=Path)
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()

    batch_dir = args.batch_dir
    out_dir = args.out_dir or batch_dir / "curation-v01"
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = read_jsonl(batch_dir / "runtime-targets.jsonl")
    source_targets = {str(row["target_id"]): row for row in read_jsonl(batch_dir / "targets.jsonl")}
    features = {str(row["target_id"]): row for row in read_jsonl(batch_dir / "features.enriched.jsonl")}
    validations = {str(row["target_id"]): row for row in read_jsonl(batch_dir / "validation-results.jsonl")}
    runtime = runtime_results(batch_dir / "runtime-evaluation-current" / "corrected-runtime-evaluation.json")
    safe_ids = read_ids(batch_dir / "safe-to-merge-targets.txt")
    raw_ids = raw_target_ids(args.raw_dir)
    report_has_missing_images = report_mentions_missing_images(batch_dir / "SCAN-REPORT-TH.md")

    curated: list[dict[str, Any]] = []
    split_rows: dict[str, list[dict[str, Any]]] = {
        "train_ready_strict": [],
        "validation_only": [],
        "needs_recheck": [],
    }
    for target in targets:
        target_id = str(target["target_id"])
        split, reasons = target_curation_reason(
            target,
            features.get(target_id),
            validations.get(target_id),
            runtime.get(target_id),
            safe_ids,
            raw_ids,
            report_has_missing_images,
        )
        row = {
            "target_id": target_id,
            "curation_split": split,
            "curation_reasons": reasons,
            "runtime_category": target["category"],
            "runtime_family": target["expected_family"],
            "source_expected_family": target.get("source_expected_family"),
            "source_image": target.get("source_image"),
            "cve": target.get("cve"),
            "validation_status": target.get("validation_status"),
            "has_raw_evidence": target_id in raw_ids,
            "runtime_strict_flow_correct": bool((runtime.get(target_id) or {}).get("strict_flow_correct")),
            "source_target": source_targets.get(target_id, {}),
        }
        curated.append(row)
        split_rows[split].append(row)

    for split, rows in split_rows.items():
        write_jsonl(out_dir / f"{split}.jsonl", rows)
        (out_dir / f"{split}-targets.txt").write_text(
            "\n".join(str(row["target_id"]) for row in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )
        split_ids = {str(row["target_id"]) for row in rows}
        write_jsonl(
            out_dir / f"{split}-features.jsonl",
            [features[target_id] for target_id in split_ids if target_id in features],
        )
        write_jsonl(
            out_dir / f"{split}-runtime-targets.jsonl",
            [target for target in targets if str(target["target_id"]) in split_ids],
        )

    summary = {
        "total_rows": len(curated),
        "split_counts": dict(sorted(Counter(row["curation_split"] for row in curated).items())),
        "category_counts": dict(sorted(Counter(str(row["runtime_category"]) for row in curated).items())),
        "raw_evidence_count": len(raw_ids),
        "raw_evidence_ids": sorted(raw_ids),
        "report_has_missing_images_note": report_has_missing_images,
    }
    (out_dir / "curation-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_jsonl(out_dir / "curated-targets.jsonl", curated)
    write_markdown(out_dir / "CURATION-REPORT-TH.md", summary, curated)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
