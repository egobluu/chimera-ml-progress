#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


SAFE_PROBES = {
    "redis": [
        "Confirm service fingerprint and version from existing scanner evidence.",
        "Run Redis INFO/read-only capability check only if authorized.",
        "Check whether Lua/EVAL is available without executing payload logic.",
        "Confirm package/distribution context before associating CVE-2022-0543.",
    ],
    "grafana": [
        "Confirm Grafana fingerprint and version from headers/body/tool output.",
        "Check whether public plugin paths are reachable.",
        "Use harmless file-read/path traversal probe only in lab or authorized scope.",
        "Stop if auth_required or path_traversal_blocked is observed.",
    ],
    "tomcat_put": [
        "Confirm Tomcat fingerprint and version.",
        "Check OPTIONS/Allow headers for PUT support.",
        "Do not upload/write files without explicit approval.",
        "Stop if method_put_rejected or upload_blocked is observed.",
    ],
    "tomcat_ajp": [
        "Confirm Tomcat fingerprint and AJP exposure.",
        "Check whether AJP port is open and reachable.",
        "Use read-only Ghostcat-style check only in lab or authorized scope.",
        "Stop if ajp_port_closed or ajp_not_exposed is observed.",
    ],
    "couchdb_auth": [
        "Confirm CouchDB fingerprint and version.",
        "Check /_config and /_users access in read-only mode.",
        "Confirm admin-party/auth behavior before any deeper verification.",
        "Stop if auth_required or config_blocked is observed.",
    ],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0].keys()) if rows else ["target_id"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_plan_rows(rows: list[dict[str, str]], limit: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows[:limit], start=1):
        family = row["top_family"]
        output.append(
            {
                "priority": index,
                "target_id": row["target_id"],
                "family": family,
                "final_decision": row["final_decision"],
                "gate_score": row["gate_score"],
                "ranker_confidence_level": row["ranker_confidence_level"],
                "specific_positive_signals": row["specific_positive_signals"].split(";")
                if row["specific_positive_signals"]
                else [],
                "cve_candidates": row["cve_candidates"].split(";") if row["cve_candidates"] else [],
                "metasploit_modules": row["metasploit_modules"].split(";") if row["metasploit_modules"] else [],
                "manual_safe_probe_th": row["manual_safe_probe_th"],
                "safe_probe_steps": SAFE_PROBES.get(family, [row["manual_safe_probe_th"]]),
                "allowed_actions": [
                    "read_only_fingerprint_check",
                    "read_only_endpoint_check",
                    "safe_metasploit_check_if_supported",
                    "write_verification_result_jsonl",
                ],
                "forbidden_actions": [
                    "run_exploit",
                    "obtain_shell",
                    "write_file_to_target",
                    "bruteforce_credentials",
                    "destructive_fuzzing",
                    "bypass_authentication",
                ],
                "requires_human_approval_before_safe_verification": True,
                "verification_status": "planned",
            }
        )
    return output


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Safe Verification Plan v01",
        "",
        "แผนนี้สร้างจากคิว `ready_for_safe_verification` บนเครื่อง 2 ฝั่ง Host Codex",
        "",
        "กติกาหลัก:",
        "",
        "```text",
        "read-only/safe check เท่านั้น",
        "ห้าม run exploit",
        "ห้ามเอา shell",
        "ห้ามเขียนไฟล์ลง target",
        "ห้าม brute force",
        "ต้องมี human approval ก่อน safe verification",
        "```",
        "",
        "## Top 5 Targets",
        "",
        "| priority | target | family | CVE candidates | safe probe |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['priority']} | `{row['target_id']}` | `{row['family']}` | `{'; '.join(row['cve_candidates'])}` | {row['manual_safe_probe_th']} |"
        )
    lines.extend(
        [
            "",
            "## Prompt สำหรับ Kali VM OpenCode",
            "",
            "```text",
            "คุณอยู่ใน Kali VM บนเครื่อง 2 และรับงานจาก Host Codex ผ่าน shared folder",
            "",
            "ทำเฉพาะ safe verification plan นี้เท่านั้น",
            "",
            "Rules:",
            "- ตรวจเฉพาะ target ที่อยู่ใน verification-plan.jsonl",
            "- read-only/safe check เท่านั้น",
            "- ห้าม run exploit",
            "- ห้ามเอา shell",
            "- ห้ามเขียนไฟล์ลง target",
            "- ห้าม brute force",
            "- ห้าม destructive fuzzing",
            "- ถ้า tool ใดจะ execute payload หรือเปลี่ยน state ให้หยุดและรายงานก่อน",
            "",
            "Output ที่ต้องเขียนกลับ:",
            "verification-results.jsonl",
            "verification-tool-log.jsonl",
            "VERIFICATION-RESULT-TH.md",
            "",
            "สำหรับแต่ละ target ให้รายงาน:",
            "target_id",
            "family",
            "safe_probe_status",
            "observed_evidence",
            "blocked_by",
            "recommended_feedback_features",
            "should_feed_back_to_dataset",
            "notes_th",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ready-csv", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--limit", default=5, type=int)
    args = parser.parse_args()

    rows = build_plan_rows(read_csv(args.ready_csv), args.limit)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "verification-plan.jsonl", rows)
    write_csv(args.out_dir / "verification-plan.csv", rows)
    write_report(args.out_dir / "SAFE-VERIFICATION-PLAN-TH.md", rows)

    print(
        json.dumps(
            {
                "planned_targets": len(rows),
                "out_dir": str(args.out_dir),
                "targets": [row["target_id"] for row in rows],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
