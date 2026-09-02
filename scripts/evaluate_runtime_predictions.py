#!/usr/bin/env python3
"""Evaluate runtime predictions from flat feature JSONL.

This script reruns the production-style runtime path instead of trusting a
scanner-side summary. It reports safety metrics separately from family ranking
accuracy because a flow can be safe while still ranking the wrong family.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from xgboost import XGBClassifier, XGBRanker

from predict_prototype import (
    DEFAULT_MODEL_DIR,
    active_reason_features,
    add_derived_precondition_features,
    as_float,
    family_decision,
    family_readiness,
    final_decision_from,
    gate_decision,
    load_json,
    normalize_feature_schema,
    rank_families,
    ranker_confidence,
    should_downgrade_for_blocking_evidence,
    should_force_unknown_family,
)


def read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def predict(features: dict[str, object], model_dir: Path, top_k: int) -> dict[str, object]:
    manifest = load_json(model_dir / "prototype_manifest.json")
    features = dict(features)
    target_id = str(features.get("target_id") or "unknown_target")
    schema_warnings = normalize_feature_schema(features)
    add_derived_precondition_features(features)

    gate_model = XGBClassifier()
    gate_model.load_model(model_dir / "gate_precondition_only.json")
    gate_features = manifest["gate"]["features"]
    X_gate = np.array([[as_float(features, name) for name in gate_features]])
    gate_score = float(gate_model.predict_proba(X_gate)[0][1])
    gate_threshold = float(manifest["gate"]["threshold"])
    gate_status = gate_decision(gate_score, gate_threshold)
    if gate_status == "likely_exploitable" and should_downgrade_for_blocking_evidence(features):
        gate_status = "low_confidence"
        schema_warnings.append("blocking negative evidence downgraded likely_exploitable to low_confidence")

    result: dict[str, object] = {
        "target_id": target_id,
        "gate": {
            "model": "gate_precondition_only",
            "score": round(gate_score, 6),
            "threshold": gate_threshold,
            "decision": gate_status,
        },
        "ranker": None,
        "final_decision": final_decision_from(gate_status, None),
        "recommended_next_action": "stop_or_collect_more_evidence",
        "reason_features": active_reason_features(features),
        "schema_warnings": schema_warnings,
    }

    if gate_status != "likely_exploitable":
        return result

    ranker_model = XGBRanker()
    ranker_model.load_model(model_dir / "family_ranker.json")
    families = list(manifest["ranker"]["families"])
    ranked = rank_families(features, families, ranker_model)
    confidence = ranker_confidence(ranked)
    readiness = family_readiness(features, str(ranked[0]["family"]))
    decision = family_decision(
        ranked[0],
        int(manifest["ranker"]["unknown_positive_signal_threshold"]),
        confidence,
        readiness,
    )
    if should_force_unknown_family(features, ranked[0], readiness):
        decision = "unknown_family"
        schema_warnings.append("unknown_product_detected forced unknown_family_triage")

    result["ranker"] = {
        "model": "family_ranker",
        "decision": decision,
        "confidence": confidence,
        "family_readiness": readiness,
        "top_families": ranked[:top_k],
    }
    result["final_decision"] = final_decision_from(gate_status, decision)
    if decision == "known_family_ready":
        result["recommended_next_action"] = "run_safe_metasploit_check_or_manual_probe"
    elif decision == "known_family_but_blocked_or_low_confidence":
        result["recommended_next_action"] = "manual_triage_before_exploit"
    else:
        result["recommended_next_action"] = "unknown_family_scan_more_or_manual_triage"
    return result


def top_family(prediction: dict[str, object]) -> str | None:
    ranker = prediction.get("ranker")
    if not isinstance(ranker, dict):
        return None
    families = ranker.get("top_families")
    if not isinstance(families, list) or not families:
        return None
    top = families[0]
    if not isinstance(top, dict):
        return None
    value = top.get("family")
    return str(value) if value is not None else None


def top_families(prediction: dict[str, object], limit: int) -> list[str]:
    ranker = prediction.get("ranker")
    if not isinstance(ranker, dict):
        return []
    families = ranker.get("top_families")
    if not isinstance(families, list):
        return []
    output: list[str] = []
    for row in families[:limit]:
        if isinstance(row, dict) and row.get("family") is not None:
            output.append(str(row["family"]))
    return output


def evaluate(
    targets: list[dict[str, object]],
    predictions: list[dict[str, object]],
) -> dict[str, object]:
    target_by_id = {str(row["target_id"]): row for row in targets}
    per_target: list[dict[str, object]] = []
    gate_tp = gate_fp = gate_tn = gate_fn = 0
    known_total = known_top1 = known_top3 = 0
    unknown_total = unknown_rejected = 0
    safety_correct = 0
    strict_correct = 0
    low_margin_count = 0
    not_ready_count = 0

    for prediction in predictions:
        target_id = str(prediction["target_id"])
        target = target_by_id[target_id]
        category = str(target["category"])
        expected_family = str(target["expected_family"])
        is_known_positive = category.startswith("known_positive")
        is_unknown_family = category.startswith("unknown_family")
        is_negative_control = category == "negative_control"
        gate_decision_value = str(prediction["gate"]["decision"])  # type: ignore[index]
        final_decision = str(prediction["final_decision"])
        predicted_family = top_family(prediction)
        ranker = prediction.get("ranker")
        confidence = ranker.get("confidence") if isinstance(ranker, dict) else None
        readiness = ranker.get("family_readiness") if isinstance(ranker, dict) else None
        if isinstance(confidence, dict) and confidence.get("level") == "low_margin":
            low_margin_count += 1
        if isinstance(readiness, dict) and not bool(readiness.get("ready")):
            not_ready_count += 1

        expected_exploitable = is_known_positive or is_unknown_family
        predicted_exploitable = gate_decision_value == "likely_exploitable"
        if expected_exploitable and predicted_exploitable:
            gate_tp += 1
        elif expected_exploitable and not predicted_exploitable:
            gate_fn += 1
        elif not expected_exploitable and predicted_exploitable:
            gate_fp += 1
        else:
            gate_tn += 1

        unknown_ok = True
        top1_ok = True
        if is_unknown_family:
            unknown_total += 1
            unknown_ok = final_decision == "unknown_family_triage"
            unknown_rejected += 1 if unknown_ok else 0
            safety_ok = unknown_ok
            strict_ok = unknown_ok
        elif is_negative_control:
            # For real use, a negative target is safe if the runtime refuses
            # automatic verification. "needs_more_evidence" is acceptable here.
            safety_ok = final_decision != "ready_for_safe_verification"
            strict_ok = safety_ok
        elif is_known_positive:
            known_total += 1
            top1_ok = predicted_family == expected_family
            top3_ok = expected_family in top_families(prediction, 3)
            known_top1 += 1 if top1_ok else 0
            known_top3 += 1 if top3_ok else 0
            safety_ok = final_decision in {
                "ready_for_safe_verification",
                "manual_triage_before_exploit",
            }
            strict_ok = safety_ok and top1_ok
        else:
            safety_ok = final_decision != "ready_for_safe_verification"
            strict_ok = safety_ok

        safety_correct += 1 if safety_ok else 0
        strict_correct += 1 if strict_ok else 0
        per_target.append(
            {
                "target_id": target_id,
                "category": category,
                "expected_family": expected_family,
                "gate_decision": gate_decision_value,
                "final_decision": final_decision,
                "predicted_top_family": predicted_family,
                "gate_correct": expected_exploitable == predicted_exploitable,
                "unknown_guard_correct": unknown_ok,
                "ranker_top1_correct": top1_ok,
                "safety_correct": safety_ok,
                "strict_flow_correct": strict_ok,
                "ranker_confidence": confidence,
                "family_readiness": readiness,
                "schema_warnings": prediction.get("schema_warnings", []),
            }
        )

    total = len(predictions)
    gate_accuracy = (gate_tp + gate_tn) / total if total else 0
    gate_precision = gate_tp / (gate_tp + gate_fp) if gate_tp + gate_fp else 0
    gate_recall = gate_tp / (gate_tp + gate_fn) if gate_tp + gate_fn else 0
    gate_f1 = (
        2 * gate_precision * gate_recall / (gate_precision + gate_recall)
        if gate_precision + gate_recall
        else 0
    )
    return {
        "total_targets": total,
        "gate_metrics": {
            "tp": gate_tp,
            "fp": gate_fp,
            "tn": gate_tn,
            "fn": gate_fn,
            "accuracy": round(gate_accuracy, 4),
            "precision": round(gate_precision, 4),
            "recall": round(gate_recall, 4),
            "f1": round(gate_f1, 4),
        },
        "ranker_metrics": {
            "known_positive_top1_correct": known_top1,
            "known_positive_top1_total": known_total,
            "known_positive_top1_accuracy": round(known_top1 / known_total, 4)
            if known_total
            else 0,
            "known_positive_top3_correct": known_top3,
            "known_positive_top3_total": known_total,
            "known_positive_top3_accuracy": round(known_top3 / known_total, 4)
            if known_total
            else 0,
        },
        "unknown_guard_metrics": {
            "unknown_rejected": unknown_rejected,
            "unknown_total": unknown_total,
            "unknown_rejection_rate": round(unknown_rejected / unknown_total, 4)
            if unknown_total
            else 0,
        },
        "ranker_safety_metrics": {
            "low_margin_count": low_margin_count,
            "family_not_ready_count": not_ready_count,
        },
        "final_flow_metrics": {
            "safety_correct": safety_correct,
            "safety_total": total,
            "safety_accuracy": round(safety_correct / total, 4) if total else 0,
            "strict_correct": strict_correct,
            "strict_total": total,
            "strict_accuracy": round(strict_correct / total, 4) if total else 0,
        },
        "per_target_results": per_target,
    }


def write_report(metrics: dict[str, object], output_path: Path) -> None:
    gate = metrics["gate_metrics"]  # type: ignore[index]
    ranker = metrics["ranker_metrics"]  # type: ignore[index]
    unknown = metrics["unknown_guard_metrics"]  # type: ignore[index]
    ranker_safety = metrics["ranker_safety_metrics"]  # type: ignore[index]
    final = metrics["final_flow_metrics"]  # type: ignore[index]
    text = f"""# Corrected Runtime Evaluation

## สรุป

ไฟล์นี้เป็นผลประเมินที่รันใหม่จาก `scripts/predict_prototype.py` หลัง patch unknown-product guard แล้ว ไม่ใช่การคัดลอกตัวเลขจาก scanner-side summary

## Metrics

| Metric | Result |
| --- | ---: |
| Total targets | {metrics["total_targets"]} |
| Gate accuracy | {gate["accuracy"]} |
| Gate TP | {gate["tp"]} |
| Gate FP | {gate["fp"]} |
| Gate TN | {gate["tn"]} |
| Gate FN | {gate["fn"]} |
| Gate precision | {gate["precision"]} |
| Gate recall | {gate["recall"]} |
| Gate F1 | {gate["f1"]} |
| Known-positive Ranker Top-1 | {ranker["known_positive_top1_accuracy"]} |
| Known-positive Ranker Top-3 | {ranker["known_positive_top3_accuracy"]} |
| Ranker low-margin count | {ranker_safety["low_margin_count"]} |
| Family not-ready count | {ranker_safety["family_not_ready_count"]} |
| Unknown rejection rate | {unknown["unknown_rejection_rate"]} |
| Safety flow accuracy | {final["safety_accuracy"]} |
| Strict flow accuracy | {final["strict_accuracy"]} |

## วิธีอ่าน

`Safety flow accuracy` คือระบบตัดสินทางปลอดภัยถูกไหม เช่น negative ต้องหยุด, unknown ต้อง triage, positive ต้องไม่ถูกหยุดผิด

`Strict flow accuracy` คือเข้มกว่า: known-positive ต้องจัด family ถูกด้วย จึงจะนับว่าถูก

ดังนั้นถ้า safety สูงแต่ strict ต่ำ แปลว่า flow ยังปลอดภัย แต่ Ranker ยังต้องปรับ feature/ranking ต่อ
"""
    output_path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features-jsonl", required=True, type=Path)
    parser.add_argument("--targets-jsonl", required=True, type=Path)
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--top-k", default=5, type=int)
    args = parser.parse_args()

    targets = read_jsonl(args.targets_jsonl)
    features = read_jsonl(args.features_jsonl)
    predictions = [predict(row, args.model_dir, args.top_k) for row in features]
    metrics = evaluate(targets, predictions)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "corrected-runtime-predictions.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in predictions) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "corrected-runtime-evaluation.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(metrics, args.out_dir / "CORRECTED-RUNTIME-EVALUATION-TH.md")
    json.dump(metrics, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
