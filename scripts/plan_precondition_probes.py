#!/usr/bin/env python3
"""Create a targeted precondition probe plan from gate prediction failures.

Generic crawl/content discovery did not reduce strict_precheck false positives.
This planner turns the remaining risky targets into concrete probe tasks that
can generate stronger precheck features such as method rejected, auth blocks,
patched version, and missing exploit endpoint.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FAMILY_PROBES = {
    "tomcat": [
        ("tomcat_put_allowed", "curl OPTIONS/PUT against a harmless temp path", "method_put_allowed/method_put_rejected"),
        ("tomcat_ajp_open", "nmap -sT -Pn or nc connect to 8009", "ajp_port_open/ajp_port_closed"),
        ("tomcat_version", "curl headers/title/docs and whatweb", "version_patched/version_in_vulnerable_range_true"),
    ],
    "redis": [
        ("redis_auth_required", "redis-cli PING/INFO with short timeout", "auth_required/no_auth_required"),
        ("redis_lua_available", "safe EVAL return probe without writing data", "lua_available/lua_blocked"),
        ("redis_version", "redis-cli INFO server", "version_patched/version_in_vulnerable_range_true"),
    ],
    "shiro": [
        ("shiro_rememberme_cookie", "curl with rememberMe probe and inspect Set-Cookie", "rememberme_cookie_behavior"),
        ("shiro_auth_page", "curl protected/common paths", "auth_required/no_auth_required"),
        ("shiro_version_hint", "whatweb/http headers/title", "version_or_product_hint"),
    ],
    "solr": [
        ("solr_admin_reachable", "curl /solr/admin/info/system", "admin_path_found/admin_access_blocked"),
        ("solr_velocity_enabled", "curl config request for VelocityResponseWriter", "velocity_enabled/velocity_disabled"),
        ("solr_core_discovered", "curl /solr/admin/cores", "solr_core_found/solr_core_missing"),
    ],
    "thinkphp": [
        ("thinkphp_invokefunction", "curl safe invokefunction endpoint reachability", "invokefunction_reachable/invokefunction_not_found"),
        ("thinkphp_error_fingerprint", "curl malformed route and inspect framework error", "thinkphp_detected/wrong_software_type"),
        ("thinkphp_version_hint", "whatweb/http headers/title", "version_or_product_hint"),
    ],
    "grafana": [
        ("grafana_health_version", "curl /api/health", "grafana_version_detected/version_patched"),
        ("grafana_traversal_probe", "safe path traversal read attempt with timeout", "path_traversal_blocked/path_traversal_possible"),
        ("grafana_auth_behavior", "curl /login and /api/user", "auth_required/no_auth_required"),
    ],
    "couchdb": [
        ("couchdb_root_info", "curl / and parse CouchDB version", "version_patched/version_in_vulnerable_range_true"),
        ("couchdb_admin_party", "curl /_users and /_config behavior", "admin_party_enabled/auth_required"),
        ("couchdb_config_access", "curl safe config endpoint", "config_accessible/config_blocked"),
    ],
    "nginx": [
        ("nginx_version", "curl -I and whatweb", "version_patched/version_in_vulnerable_range_true"),
        ("nginx_range_probe", "safe Range header request", "range_behavior_vulnerable/range_behavior_safe"),
        ("nginx_default_paths", "curl default/static paths", "endpoint_reachable_count/endpoint_missing_count"),
    ],
    "spring": [
        ("spring_fingerprint", "curl error pages/headers/actuator candidates", "spring_detected/spring_not_detected"),
        ("spring_actuator", "curl /actuator and /actuator/env", "actuator_path_found/actuator_path_missing"),
        ("spring_classloader_probe", "safe classloader parameter behavior check", "spring_precondition_pass/spring_precondition_fail"),
    ],
    "jenkins": [
        ("jenkins_version", "curl headers and /api/json", "version_patched/version_in_vulnerable_range_true"),
        ("jenkins_cli_or_script", "curl CLI/script endpoints without auth bypass", "endpoint_reachable_count/auth_required"),
        ("jenkins_auth_behavior", "curl /login /whoAmI", "auth_required/no_auth_required"),
    ],
    "nexus": [
        ("nexus_version", "curl service/rest or status endpoints", "version_patched/version_in_vulnerable_range_true"),
        ("nexus_anonymous_access", "curl repository/API endpoints", "anonymous_access/auth_required"),
        ("nexus_endpoint_behavior", "curl vulnerable endpoint candidates", "endpoint_reachable_count/endpoint_missing_count"),
    ],
    "elasticsearch": [
        ("es_version", "curl / and parse version", "version_patched/version_in_vulnerable_range_true"),
        ("es_script_behavior", "safe script/painless capability check", "painless_sandbox_blocks/script_enabled"),
        ("es_auth_behavior", "curl /_cluster/health", "auth_required/no_auth_required"),
    ],
    "phpmyadmin": [
        ("phpmyadmin_version", "curl root/login page and whatweb", "version_patched/version_in_vulnerable_range_true"),
        ("phpmyadmin_auth_behavior", "curl setup/import endpoints", "auth_required/no_auth_required"),
        ("phpmyadmin_endpoint_presence", "curl known route candidates", "endpoint_reachable_count/endpoint_missing_count"),
    ],
}


def infer_family(target_id: str) -> str:
    lowered = target_id.lower()
    for family in FAMILY_PROBES:
        if family in lowered:
            return family
    if "struts" in lowered:
        return "struts"
    if "flask" in lowered:
        return "flask"
    if "nextjs" in lowered:
        return "nextjs"
    if "aria2" in lowered:
        return "aria2"
    return "generic"


def generic_probes(family: str) -> list[tuple[str, str, str]]:
    return [
        (f"{family}_version_probe", "detect product/version from headers/body/tool output", "version_patched/version_in_vulnerable_range_true"),
        (f"{family}_auth_probe", "check whether sensitive endpoint requires auth", "auth_required/no_auth_required"),
        (f"{family}_endpoint_probe", "check expected exploit endpoint exists", "endpoint_reachable_count/endpoint_missing_count"),
    ]


def read_predictions(path: Path, threshold: float) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["planned_predicted_label"] = "1" if float(row["probability"]) >= threshold else "0"
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, object]], threshold: float) -> None:
    false_positives = sorted({row["target_id"] for row in rows if row["failure_type"] == "false_positive"})
    false_negatives = sorted({row["target_id"] for row in rows if row["failure_type"] == "false_negative"})
    families = sorted({row["family"] for row in rows})

    lines = [
        "# Targeted Precondition Probe Plan",
        "",
        f"- threshold used: {threshold}",
        f"- probe tasks: {len(rows)}",
        f"- false positive targets: {len(false_positives)}",
        f"- false negative targets: {len(false_negatives)}",
        f"- families covered: {', '.join(families)}",
        "",
        "## ทำไมต้องทำรอบนี้",
        "",
        "Light backfill รอบก่อนเพิ่มข้อมูลจาก `whatweb`, `curl`, และ `ffuf` แล้ว แต่ `strict_precheck` ยัง false positive 20 ตัวเมื่อเลือก threshold แบบไม่ยอมให้ false negative เกิด แปลว่า generic scan ยังไม่พอ ต้องเก็บ precondition ที่ผูกกับ exploit family โดยตรง",
        "",
        "## Target ที่ควรเริ่มก่อน",
        "",
    ]
    for target_id in false_positives[:12]:
        lines.append(f"- `{target_id}`")

    lines.extend(
        [
            "",
            "## Probe ที่ต้องเก็บ",
            "",
            "| priority | target | family | failure | probe | expected feature |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['priority']} | `{row['target_id']}` | `{row['family']}` | `{row['failure_type']}` | {row['probe_name']} | `{row['expected_feature']}` |"
        )

    lines.extend(
        [
            "",
            "## กฎสำคัญ",
            "",
            "- ใช้เฉพาะ precheck probe ก่อนยิง exploit",
            "- ห้ามใช้ Metasploit/manual PoC result เป็น input",
            "- ห้ามรวมเป็น `negative_evidence_count` ก้อนเดียว",
            "- ทุก probe ต้องมี `was_run`, `worked`, `timeout`, `missing`",
            "- ผลที่ต้องการคือ feature ย่อย เช่น `method_put_rejected`, `auth_required`, `endpoint_missing`, `version_patched`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--threshold", type=float, default=0.10)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    predictions = read_predictions(args.predictions, args.threshold)
    tasks: list[dict[str, object]] = []
    priority = 1
    for row in predictions:
        true_label = row["true_label"]
        predicted = row["planned_predicted_label"]
        if true_label == predicted:
            continue
        failure_type = "false_positive" if true_label == "0" and predicted == "1" else "false_negative"
        target_id = row["target_id"]
        family = infer_family(target_id)
        probes = FAMILY_PROBES.get(family, generic_probes(family))
        for probe_name, instruction, expected_feature in probes:
            tasks.append(
                {
                    "priority": priority,
                    "target_id": target_id,
                    "family": family,
                    "failure_type": failure_type,
                    "probability": row["probability"],
                    "probe_name": probe_name,
                    "probe_instruction": instruction,
                    "expected_feature": expected_feature,
                    "phase": "targeted_precondition_precheck",
                }
            )
            priority += 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if tasks:
        write_csv(args.out_dir / "targeted-precondition-probe-plan.csv", tasks)
        write_markdown(args.out_dir / "TARGETED-PRECONDITION-PROBE-PLAN-TH.md", tasks, args.threshold)
    (args.out_dir / "targeted-precondition-probe-plan.json").write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"probe_tasks": len(tasks), "out_dir": str(args.out_dir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
