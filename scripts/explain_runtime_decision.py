#!/usr/bin/env python3
"""Create an operator/LLM-facing explanation from a runtime prediction JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_POLICY = Path("runtime/llm-action-policy.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_bool(value: Any) -> str:
    return "yes" if bool(value) else "no"


def top_families(prediction: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    ranker = prediction.get("ranker")
    if not isinstance(ranker, dict):
        return []
    families = ranker.get("top_families")
    if not isinstance(families, list):
        return []
    return [row for row in families[:limit] if isinstance(row, dict)]


def build_summary(prediction: dict[str, Any], policy: dict[str, Any], top_k: int) -> dict[str, Any]:
    final_decision = str(prediction.get("final_decision") or "unknown")
    decision_policy = dict(policy.get("decisions", {}).get(final_decision, {}))
    gate = prediction.get("gate") if isinstance(prediction.get("gate"), dict) else {}
    ranker = prediction.get("ranker") if isinstance(prediction.get("ranker"), dict) else None
    confidence = ranker.get("confidence") if isinstance(ranker, dict) and isinstance(ranker.get("confidence"), dict) else None
    readiness = (
        ranker.get("family_readiness")
        if isinstance(ranker, dict) and isinstance(ranker.get("family_readiness"), dict)
        else None
    )

    return {
        "target_id": prediction.get("target_id", "unknown_target"),
        "final_decision": final_decision,
        "meaning_th": decision_policy.get("meaning_th", "ไม่มี policy สำหรับ decision นี้"),
        "recommended_next_action": prediction.get("recommended_next_action", "unknown"),
        "requires_user_approval": bool(decision_policy.get("requires_user_approval", True)),
        "may_run_safe_verification": bool(decision_policy.get("may_run_safe_verification", False)),
        "may_run_exploit": bool(decision_policy.get("may_run_exploit", False)),
        "gate": {
            "decision": gate.get("decision"),
            "score": gate.get("score"),
            "threshold": gate.get("threshold"),
        },
        "ranker": {
            "decision": ranker.get("decision") if isinstance(ranker, dict) else None,
            "confidence_level": confidence.get("level") if confidence else None,
            "confidence_margin": confidence.get("margin") if confidence else None,
            "family_ready": readiness.get("ready") if readiness else None,
            "readiness_reason": readiness.get("reason") if readiness else None,
            "top_families": top_families(prediction, top_k),
        },
        "reason_features": prediction.get("reason_features", []),
        "schema_warnings": prediction.get("schema_warnings", []),
        "allowed_actions": decision_policy.get("allowed_actions", []),
        "global_rules": policy.get("global_rules", []),
    }


def markdown(summary: dict[str, Any]) -> str:
    top_lines = []
    for row in summary["ranker"]["top_families"]:
        top_lines.append(
            "| {family} | {score} | {pos} | {neg} | {specific} |".format(
                family=row.get("family"),
                score=row.get("score"),
                pos=row.get("positive_signals"),
                neg=row.get("negative_signals"),
                specific=row.get("specific_positive_signals"),
            )
        )
    if not top_lines:
        top_lines.append("| n/a | n/a | n/a | n/a | n/a |")

    reason_features = "\n".join(f"- `{name}`" for name in summary["reason_features"]) or "- ไม่มี active reason feature"
    schema_warnings = "\n".join(f"- {warning}" for warning in summary["schema_warnings"]) or "- ไม่มี schema warning"
    allowed_actions = "\n".join(f"- `{action}`" for action in summary["allowed_actions"]) or "- ไม่มี action policy"

    return f"""# Runtime Decision Explanation

## สรุป

| Field | Value |
| --- | --- |
| target | `{summary['target_id']}` |
| final decision | `{summary['final_decision']}` |
| ความหมาย | {summary['meaning_th']} |
| recommended next action | `{summary['recommended_next_action']}` |
| requires user approval | {format_bool(summary['requires_user_approval'])} |
| may run safe verification | {format_bool(summary['may_run_safe_verification'])} |
| may run exploit | {format_bool(summary['may_run_exploit'])} |

## Gate

| Field | Value |
| --- | --- |
| decision | `{summary['gate']['decision']}` |
| score | `{summary['gate']['score']}` |
| threshold | `{summary['gate']['threshold']}` |

## Ranker

| Field | Value |
| --- | --- |
| decision | `{summary['ranker']['decision']}` |
| confidence | `{summary['ranker']['confidence_level']}` |
| margin | `{summary['ranker']['confidence_margin']}` |
| family ready | `{summary['ranker']['family_ready']}` |
| readiness reason | {summary['ranker']['readiness_reason']} |

## Top Families

| Family | Score | Positive signals | Negative signals | Specific positive |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(top_lines)}

## Reason Features

{reason_features}

## Schema Warnings

{schema_warnings}

## Allowed Actions

{allowed_actions}

## Operator Note

อ่าน `final_decision` ก่อน score เสมอ และอย่าใช้ ML output เพื่อยิง exploit อัตโนมัติ
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction", required=True, type=Path)
    parser.add_argument("--policy", default=DEFAULT_POLICY, type=Path)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--top-k", default=5, type=int)
    args = parser.parse_args()

    prediction = load_json(args.prediction)
    policy = load_json(args.policy)
    summary = build_summary(prediction, policy, args.top_k)
    text = markdown(summary)

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(text, encoding="utf-8")
    if not args.out_json and not args.out_md:
        print(text)


if __name__ == "__main__":
    main()
