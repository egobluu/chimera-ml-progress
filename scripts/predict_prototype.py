#!/usr/bin/env python3
"""Runtime prediction entrypoint for the Chimera ML prototype.

Input is a flat JSON feature object. The scanner/feature-extractor layer should
produce this object before calling the ML layer. The output is JSON designed to
be easy for an LLM/agentic controller to consume.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from xgboost import XGBClassifier, XGBRanker

from train_family_ranker import FAMILY_FEATURES, candidate_vector
from train_gate_profiles import NEGATIVE_PRECONDITION_FEATURES, POSITIVE_PRECONDITION_FEATURES


DEFAULT_MODEL_DIR = Path("runtime/models/prototype")


def as_float(row: dict[str, object], name: str) -> float:
    try:
        return float(row.get(name) or 0)
    except (TypeError, ValueError):
        return 0.0


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_derived_precondition_features(features: dict[str, object]) -> None:
    positive = sum(1 for name in POSITIVE_PRECONDITION_FEATURES if as_float(features, name) > 0)
    negative = sum(1 for name in NEGATIVE_PRECONDITION_FEATURES if as_float(features, name) > 0)
    features["precondition_positive_signal_count"] = positive
    features["precondition_negative_signal_count"] = negative
    features["precondition_signal_balance"] = positive - negative
    features["has_positive_precondition_signal"] = 1 if positive > 0 else 0
    features["has_negative_precondition_signal"] = 1 if negative > 0 else 0


def gate_decision(score: float, threshold: float) -> str:
    if score >= threshold:
        return "likely_exploitable"
    if score >= threshold * 0.65:
        return "low_confidence"
    return "no_exploit"


def signal_counts(features: dict[str, object], family: str) -> tuple[int, int]:
    spec = FAMILY_FEATURES[family]
    positive = sum(1 for name in spec["positive"] if as_float(features, name) > 0)
    negative = sum(1 for name in spec["negative"] if as_float(features, name) > 0)
    return positive, negative


def rank_families(features: dict[str, object], families: list[str], model: XGBRanker) -> list[dict[str, object]]:
    row = {name: str(value) for name, value in features.items()}
    X = np.array([candidate_vector(row, family, families) for family in families])
    scores = model.predict(X)
    ranked = sorted(zip(families, scores), key=lambda item: item[1], reverse=True)
    output = []
    for family, score in ranked:
        positive, negative = signal_counts(features, family)
        output.append(
            {
                "family": family,
                "score": round(float(score), 6),
                "positive_signals": positive,
                "negative_signals": negative,
            }
        )
    return output


def family_decision(top_family: dict[str, object], threshold: int) -> str:
    positive = int(top_family["positive_signals"])
    negative = int(top_family["negative_signals"])
    if positive >= threshold and negative == 0:
        return "known_family_ready"
    if positive >= threshold:
        return "known_family_but_blocked_or_low_confidence"
    return "unknown_family"


def final_decision_from(gate_status: str, ranker_decision: str | None) -> str:
    if gate_status == "no_exploit":
        return "do_not_exploit_now"
    if gate_status == "low_confidence":
        return "needs_more_evidence"
    if ranker_decision == "known_family_ready":
        return "ready_for_safe_verification"
    if ranker_decision == "known_family_but_blocked_or_low_confidence":
        return "manual_triage_before_exploit"
    if ranker_decision == "unknown_family":
        return "unknown_family_triage"
    return "needs_more_evidence"


def active_reason_features(features: dict[str, object], limit: int = 12) -> list[str]:
    active = [
        name
        for name, value in features.items()
        if as_float(features, name) > 0 and not name.startswith("precondition_")
    ]
    return sorted(active)[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True, type=Path, help="Flat JSON feature object.")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, type=Path)
    parser.add_argument("--top-k", default=5, type=int)
    parser.add_argument("--out", type=Path, help="Optional path to write the JSON result.")
    args = parser.parse_args()

    manifest_path = args.model_dir / "prototype_manifest.json"
    if not manifest_path.exists():
        print(f"missing manifest: {manifest_path}", file=sys.stderr)
        sys.exit(2)

    manifest = load_json(manifest_path)
    features = load_json(args.features)
    target_id = str(features.get("target_id") or args.features.stem)
    add_derived_precondition_features(features)

    gate_model = XGBClassifier()
    gate_model.load_model(args.model_dir / "gate_precondition_only.json")
    gate_features = manifest["gate"]["features"]
    X_gate = np.array([[as_float(features, name) for name in gate_features]])
    gate_score = float(gate_model.predict_proba(X_gate)[0][1])
    gate_threshold = float(manifest["gate"]["threshold"])
    gate_status = gate_decision(gate_score, gate_threshold)

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
        "safety_note_th": "ยังไม่ยิง exploit อัตโนมัติ ต้องใช้ Metasploit check/manual PoC หลังผู้ใช้ยืนยัน",
    }

    if gate_status != "likely_exploitable":
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(output + "\n", encoding="utf-8")
        print(output)
        return

    ranker_model = XGBRanker()
    ranker_model.load_model(args.model_dir / "family_ranker.json")
    families = list(manifest["ranker"]["families"])
    ranked = rank_families(features, families, ranker_model)
    top = ranked[0]
    decision = family_decision(top, int(manifest["ranker"]["unknown_positive_signal_threshold"]))
    result["ranker"] = {
        "model": "family_ranker",
        "decision": decision,
        "top_families": ranked[: args.top_k],
    }
    result["final_decision"] = final_decision_from(gate_status, decision)
    if decision == "known_family_ready":
        result["recommended_next_action"] = "run_safe_metasploit_check_or_manual_probe"
    elif decision == "known_family_but_blocked_or_low_confidence":
        result["recommended_next_action"] = "manual_triage_before_exploit"
    else:
        result["recommended_next_action"] = "unknown_family_scan_more_or_manual_triage"

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()