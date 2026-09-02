#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DECISION_PRIORITY = {
    "ready_for_safe_verification": 100,
    "manual_triage_before_exploit": 70,
    "unknown_family_triage": 50,
    "needs_more_evidence": 30,
    "do_not_exploit_now": 0,
}


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


def load_targets(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    return {str(row["target_id"]): row for row in read_jsonl(path)}


def top_family(prediction: dict[str, Any]) -> dict[str, Any]:
    ranker = prediction.get("ranker")
    if not isinstance(ranker, dict):
        return {}
    families = ranker.get("top_families")
    if not isinstance(families, list) or not families or not isinstance(families[0], dict):
        return {}
    return families[0]


def ranker_field(prediction: dict[str, Any], name: str, default: Any = "") -> Any:
    ranker = prediction.get("ranker")
    if not isinstance(ranker, dict):
        return default
    return ranker.get(name, default)


def resolver_for(resolver: dict[str, Any], final_decision: str, family: str) -> dict[str, Any]:
    families = resolver.get("families", {})
    if final_decision != "ready_for_safe_verification":
        return {
            "resolver_used": False,
            "family_used": "",
            "cve_candidates": [],
            "metasploit_modules": [],
            "manual_safe_probe_th": "",
            "resolver_note_th": "ยังไม่ใช้ resolver เพราะ final_decision ยังไม่ใช่ ready_for_safe_verification",
        }
    mapped = families.get(family, {})
    return {
        "resolver_used": True,
        "family_used": family,
        "cve_candidates": mapped.get("cve_candidates", []),
        "metasploit_modules": mapped.get("metasploit_modules", []),
        "manual_safe_probe_th": mapped.get("manual_safe_probe_th", ""),
        "resolver_note_th": mapped.get("notes_th", "family ยังไม่มี mapping"),
    }


def normalize_prediction_row(row: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    prediction = row.get("prediction") if isinstance(row.get("prediction"), dict) else row
    target_id = str(row.get("target_id") or prediction.get("target_id") or "unknown_target")
    return target_id, prediction, row


def build_rows(
    predictions: list[dict[str, Any]],
    targets: dict[str, dict[str, Any]],
    resolver: dict[str, Any],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in predictions:
        target_id, prediction, original = normalize_prediction_row(row)
        target = targets.get(target_id, {})
        gate = prediction.get("gate") if isinstance(prediction.get("gate"), dict) else {}
        final_decision = str(prediction.get("final_decision", ""))
        top = top_family(prediction)
        family = str(top.get("family", "") or "")
        readiness = ranker_field(prediction, "family_readiness", {})
        confidence = ranker_field(prediction, "confidence", {})
        mapped = resolver_for(resolver, final_decision, family)
        priority_score = DECISION_PRIORITY.get(final_decision, 0) + float(gate.get("score", 0) or 0)

        output.append(
            {
                "target_id": target_id,
                "category": target.get("category", original.get("category", "")),
                "expected_family": target.get("expected_family", original.get("expected_family", "")),
                "final_decision": final_decision,
                "recommended_next_action": prediction.get("recommended_next_action", ""),
                "priority_score": round(priority_score, 6),
                "gate_decision": gate.get("decision", ""),
                "gate_score": gate.get("score", ""),
                "top_family": family,
                "top_family_score": top.get("score", ""),
                "ranker_decision": ranker_field(prediction, "decision", ""),
                "ranker_confidence_level": confidence.get("level", "") if isinstance(confidence, dict) else "",
                "family_ready": readiness.get("ready", "") if isinstance(readiness, dict) else "",
                "specific_positive_signals": ";".join(readiness.get("specific_positive_signals", []))
                if isinstance(readiness, dict)
                else "",
                "blocking_negative_signals": ";".join(readiness.get("blocking_negative_signals", []))
                if isinstance(readiness, dict)
                else "",
                "schema_warnings": ";".join(prediction.get("schema_warnings", [])),
                "resolver_used": mapped["resolver_used"],
                "resolver_family": mapped["family_used"],
                "cve_candidates": ";".join(mapped["cve_candidates"]),
                "metasploit_modules": ";".join(mapped["metasploit_modules"]),
                "manual_safe_probe_th": mapped["manual_safe_probe_th"],
                "resolver_note_th": mapped["resolver_note_th"],
            }
        )
    return sorted(output, key=lambda item: float(item["priority_score"]), reverse=True)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["target_id"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    ready = [row for row in rows if row["final_decision"] == "ready_for_safe_verification"]
    manual = [row for row in rows if row["final_decision"] == "manual_triage_before_exploit"]
    unknown = [row for row in rows if row["final_decision"] == "unknown_family_triage"]
    more = [row for row in rows if row["final_decision"] == "needs_more_evidence"]
    stop = [row for row in rows if row["final_decision"] == "do_not_exploit_now"]

    def table(sample: list[dict[str, Any]]) -> list[str]:
        lines = ["| target | decision | top family | CVE candidates | next action |", "| --- | --- | --- | --- | --- |"]
        for row in sample:
            lines.append(
                f"| `{row['target_id']}` | `{row['final_decision']}` | `{row['top_family'] or 'none'}` | `{row['cve_candidates'] or 'none'}` | `{row['recommended_next_action']}` |"
            )
        return lines

    text = [
        "# Priority Report",
        "",
        "รายงานนี้สร้างจาก runtime prediction ที่มีอยู่แล้วบนเครื่อง 2 ไม่ได้สแกน target ใหม่",
        "",
        "## Summary",
        "",
        "| กลุ่ม | จำนวน | ความหมาย |",
        "| --- | ---: | --- |",
        f"| ready_for_safe_verification | {len(ready)} | มีหลักฐานพอสำหรับ safe verification หลังคนอนุมัติ |",
        f"| manual_triage_before_exploit | {len(manual)} | มีสัญญาณบวกแต่ยังต้องให้คนตรวจ |",
        f"| unknown_family_triage | {len(unknown)} | น่าตรวจต่อแต่ family ไม่อยู่ใน model หรือ guard ไม่ให้เชื่อ Ranker |",
        f"| needs_more_evidence | {len(more)} | ยังต้องเก็บ precheck เพิ่ม |",
        f"| do_not_exploit_now | {len(stop)} | ตอนนี้ไม่ควรตรวจ exploit path นี้ |",
        "",
        "## Top Ready Targets",
        "",
        *table(ready[:20]),
        "",
        "## Unknown-family Queue",
        "",
        *table(unknown[:20]),
        "",
        "## Manual/More Evidence Queue",
        "",
        *table((manual + more)[:20]),
        "",
        "## Safety Note",
        "",
        "`ready_for_safe_verification` ไม่ได้แปลว่ายิง exploit ได้ทันที ต้องใช้เฉพาะ safe check/manual non-destructive probe และต้องมี human approval",
    ]
    path.write_text("\n".join(text) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--resolver", default=Path("runtime/resolver/family-cve-module-map.json"), type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    resolver = json.loads(args.resolver.read_text(encoding="utf-8"))
    targets = load_targets(args.targets)
    predictions = read_jsonl(args.predictions)
    rows = build_rows(predictions, targets, resolver)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "priority-review.csv", rows)
    write_jsonl(args.out_dir / "priority-review.jsonl", rows)
    write_csv(args.out_dir / "ready-for-safe-verification.csv", [row for row in rows if row["final_decision"] == "ready_for_safe_verification"])
    write_csv(args.out_dir / "unknown-family-triage.csv", [row for row in rows if row["final_decision"] == "unknown_family_triage"])
    write_csv(args.out_dir / "manual-or-more-evidence.csv", [row for row in rows if row["final_decision"] in {"manual_triage_before_exploit", "needs_more_evidence"}])
    write_report(args.out_dir / "PRIORITY-REPORT-TH.md", rows)

    print(
        json.dumps(
            {
                "total": len(rows),
                "ready_for_safe_verification": sum(1 for row in rows if row["final_decision"] == "ready_for_safe_verification"),
                "manual_triage_before_exploit": sum(1 for row in rows if row["final_decision"] == "manual_triage_before_exploit"),
                "unknown_family_triage": sum(1 for row in rows if row["final_decision"] == "unknown_family_triage"),
                "needs_more_evidence": sum(1 for row in rows if row["final_decision"] == "needs_more_evidence"),
                "do_not_exploit_now": sum(1 for row in rows if row["final_decision"] == "do_not_exploit_now"),
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
