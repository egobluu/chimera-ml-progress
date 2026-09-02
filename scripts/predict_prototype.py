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

UNKNOWN_PRODUCT_FEATURES = {
    "coldfusion_detected",
    "drupal_detected",
    "jboss_detected",
    "jetty_detected",
    "laravel_detected",
    "php_cgi_detected",
    "php_detected",
    "spring_detected",
    "wordpress_detected",
}

SCHEMA_ALIASES = {
    "admin_party": "admin_party_enabled",
    "config_endpoint_accessible": "config_accessible",
    "default_key_detected": "default_key_likely",
    "remember_me_cookie_found": "rememberme_deleteMe_seen",
    "endpoint_missing": "endpoint_missing_count",
    "template_accessible": "velocity_template_accessible",
    "velocity_template_accessible": "velocity_enabled",
}

BLOCKING_NEGATIVE_FEATURES = {
    "version_in_vulnerable_range_false",
    "version_not_affected",
    "version_patched",
    "auth_required",
    "method_put_rejected",
    "upload_blocked",
    "ajp_port_closed",
    "ajp_not_exposed",
    "velocity_disabled",
    "config_api_blocked",
    "invokefunction_not_found",
    "default_key_unlikely",
    "path_traversal_blocked",
    "auth_blocks_exploit",
    "endpoint_not_found",
    "config_blocked",
}

STRONG_POSITIVE_PRECONDITIONS = {
    "method_put_allowed",
    "jsp_upload_candidate",
    "ajp_port_open",
    "velocity_enabled",
    "config_api_accessible",
    "invokefunction_reachable",
    "admin_party_enabled",
    "config_accessible",
    "users_db_accessible",
    "default_key_likely",
    "redis_info_accessible",
    "lua_available",
    "plugin_path_candidate_found",
    "public_plugin_path_accessible",
    "path_traversal_candidate_found",
    "cli_endpoint_reachable",
}

GENERIC_RANKER_FEATURES = {
    "anonymous_access",
    "endpoint_reachable_count",
    "no_auth_required",
    "version_in_vulnerable_range",
}

PRODUCT_DETECTION_FEATURES = {
    "couchdb_auth": {"couchdb_detected"},
    "elasticsearch": {"elasticsearch_detected"},
    "flask": {"flask_detected"},
    "grafana": {"grafana_detected"},
    "jenkins": {"jenkins_detected"},
    "joomla": {"joomla_detected"},
    "nexus": {"nexus_detected"},
    "nginx": {"nginx_detected"},
    "nextjs": {"nextjs_detected"},
    "redis": {"redis_detected"},
    "shiro_key": {"shiro_detected"},
    "solr_velocity": {"solr_detected"},
    "struts2": {"struts2_detected"},
    "thinkphp_rce": {"thinkphp_detected"},
    "tomcat_ajp": {"tomcat_detected"},
    "tomcat_put": {"tomcat_detected"},
}

MIN_READY_RANKER_MARGIN = 0.25
MIN_READY_SPECIFIC_POSITIVE_SIGNALS = 1


def as_float(row: dict[str, object], name: str) -> float:
    try:
        return float(row.get(name) or 0)
    except (TypeError, ValueError):
        return 0.0


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_feature_schema(features: dict[str, object]) -> list[str]:
    warnings: list[str] = []
    if "is_non_http_target" in features and "is_non_http_service" not in features:
        features["is_non_http_service"] = features["is_non_http_target"]
        warnings.append("normalized alias: is_non_http_target -> is_non_http_service")

    for old_name, new_name in SCHEMA_ALIASES.items():
        if old_name in features and new_name not in features:
            features[new_name] = features[old_name]
            warnings.append(f"normalized alias: {old_name} -> {new_name}")

    if as_float(features, "solr_detected") > 0 and as_float(features, "velocity_enabled") <= 0:
        if (
            "velocity_endpoint_found" in features
            or "velocity_template_accessible" in features
            or "velocity_rce_candidate" in features
        ):
            features.setdefault("velocity_disabled", 1)
            warnings.append("derived velocity_disabled from Solr velocity probe fields")

    if "version_in_vulnerable_range" in features:
        vulnerable = 1 if as_float(features, "version_in_vulnerable_range") > 0 else 0
        features.setdefault("version_in_vulnerable_range_true", vulnerable)
        features.setdefault("version_in_vulnerable_range_false", 0 if vulnerable else 1)

    if (
        any(as_float(features, name) > 0 for name in UNKNOWN_PRODUCT_FEATURES)
        and as_float(features, "known_family_signal_count") <= 0
    ):
        features["unknown_product_detected"] = 1
        warnings.append("derived unknown_product_detected from unknown product fingerprint")

    if as_float(features, "unknown_product_detected") > 0:
        warnings.append("unknown_product_detected present; known-family ranking requires extra guard")

    if as_float(features, "jenkins_detected") > 0:
        if "script_console_accessible" in features and "cli_endpoint_reachable" not in features:
            features["cli_endpoint_reachable"] = features["script_console_accessible"]
            warnings.append("normalized Jenkins signal: script_console_accessible -> cli_endpoint_reachable")
        if "api_accessible" in features and "endpoint_reachable_count" not in features:
            features["endpoint_reachable_count"] = features["api_accessible"]
            warnings.append("normalized Jenkins signal: api_accessible -> endpoint_reachable_count")

    if as_float(features, "nexus_detected") > 0:
        if "default_credentials" in features and "anonymous_access" not in features:
            features["anonymous_access"] = features["default_credentials"]
            warnings.append("normalized Nexus signal: default_credentials -> anonymous_access")
        if "api_accessible" in features and "endpoint_reachable_count" not in features:
            features["endpoint_reachable_count"] = features["api_accessible"]
            warnings.append("normalized Nexus signal: api_accessible -> endpoint_reachable_count")

    if as_float(features, "struts2_detected") > 0:
        if "rce_endpoint_accessible" in features and "upload_endpoint_reachable" not in features:
            features["upload_endpoint_reachable"] = features["rce_endpoint_accessible"]
            warnings.append("normalized Struts2 signal: rce_endpoint_accessible -> upload_endpoint_reachable")

    if as_float(features, "flask_detected") > 0:
        if "ssti_endpoint_accessible" in features and "rce_endpoint_candidate_found" not in features:
            features["rce_endpoint_candidate_found"] = features["ssti_endpoint_accessible"]
            warnings.append("normalized Flask signal: ssti_endpoint_accessible -> rce_endpoint_candidate_found")

    if as_float(features, "joomla_detected") > 0:
        if "sql_injection_endpoint" in features and "api_path_found" not in features:
            features["api_path_found"] = features["sql_injection_endpoint"]
            warnings.append("normalized Joomla signal: sql_injection_endpoint -> api_path_found")

    if as_float(features, "nextjs_detected") > 0:
        if "ssrf_endpoint_accessible" in features and "endpoint_reachable_count" not in features:
            features["endpoint_reachable_count"] = features["ssrf_endpoint_accessible"]
            warnings.append("normalized Next.js signal: ssrf_endpoint_accessible -> endpoint_reachable_count")

    if as_float(features, "elasticsearch_detected") > 0:
        if "cluster_settings_accessible" in features and "script_engine_enabled" not in features:
            features["script_engine_enabled"] = features["cluster_settings_accessible"]
            warnings.append("normalized Elasticsearch signal: cluster_settings_accessible -> script_engine_enabled")
        if "nodes_accessible" in features and "endpoint_reachable_count" not in features:
            features["endpoint_reachable_count"] = features["nodes_accessible"]
            warnings.append("normalized Elasticsearch signal: nodes_accessible -> endpoint_reachable_count")

    return warnings


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


def should_downgrade_for_blocking_evidence(features: dict[str, object]) -> bool:
    if (
        as_float(features, "redis_detected") > 0
        and as_float(features, "lua_available") <= 0
        and as_float(features, "known_family_signal_count") <= 0
    ):
        return True

    if (
        as_float(features, "grafana_detected") > 0
        and as_float(features, "path_traversal_blocked") > 0
        and as_float(features, "public_plugin_path_accessible") <= 0
    ):
        return True

    if (
        as_float(features, "solr_detected") > 0
        and as_float(features, "velocity_disabled") > 0
        and as_float(features, "velocity_enabled") <= 0
    ):
        return True

    if (
        as_float(features, "nexus_detected") > 0
        and as_float(features, "anonymous_access") > 0
        and as_float(features, "endpoint_reachable_count") > 0
    ):
        return False

    negative = sum(1 for name in BLOCKING_NEGATIVE_FEATURES if as_float(features, name) > 0)
    strong_positive = sum(1 for name in STRONG_POSITIVE_PRECONDITIONS if as_float(features, name) > 0)
    if (
        as_float(features, "known_family_signal_count") <= 0
        and as_float(features, "unknown_product_detected") <= 0
        and strong_positive == 0
        and (
            as_float(features, "version_in_vulnerable_range") > 0
            or as_float(features, "anonymous_access") > 0
            or as_float(features, "no_auth_required") > 0
        )
    ):
        return True
    return negative > 0 and strong_positive <= negative


def signal_counts(features: dict[str, object], family: str) -> tuple[int, int]:
    spec = FAMILY_FEATURES[family]
    positive = sum(1 for name in spec["positive"] if as_float(features, name) > 0)
    negative = sum(1 for name in spec["negative"] if as_float(features, name) > 0)
    return positive, negative


def specific_positive_signal_count(features: dict[str, object], family: str) -> int:
    spec = FAMILY_FEATURES[family]
    return sum(
        1
        for name in spec["positive"]
        if name not in GENERIC_RANKER_FEATURES and as_float(features, name) > 0
    )


def product_hint_signal_count(features: dict[str, object], family: str) -> int:
    return sum(1 for name in PRODUCT_DETECTION_FEATURES.get(family, set()) if as_float(features, name) > 0)


def rank_families(features: dict[str, object], families: list[str], model: XGBRanker) -> list[dict[str, object]]:
    row = {name: str(value) for name, value in features.items()}
    X = np.array([candidate_vector(row, family, families) for family in families])
    scores = model.predict(X)
    ranked = sorted(zip(families, scores), key=lambda item: item[1], reverse=True)
    output = []
    for family, score in ranked:
        positive, negative = signal_counts(features, family)
        specific_positive = specific_positive_signal_count(features, family)
        product_hint = product_hint_signal_count(features, family)
        output.append(
            {
                "family": family,
                "score": round(float(score), 6),
                "positive_signals": positive,
                "negative_signals": negative,
                "specific_positive_signals": specific_positive,
                "product_hint_signals": product_hint,
            }
        )
    if any(int(row["product_hint_signals"]) > 0 for row in output):
        output = sorted(
            output,
            key=lambda row: (
                int(row["product_hint_signals"]),
                int(row["specific_positive_signals"]),
                float(row["score"]),
            ),
            reverse=True,
        )
    elif any(int(row["specific_positive_signals"]) > 0 for row in output):
        output = sorted(
            output,
            key=lambda row: (
                int(row["specific_positive_signals"]) > 0,
                int(row["specific_positive_signals"]),
                float(row["score"]),
            ),
            reverse=True,
        )
    return output


def ranker_confidence(ranked: list[dict[str, object]]) -> dict[str, object]:
    if not ranked:
        return {
            "level": "no_rank",
            "top_score": None,
            "runner_up_score": None,
            "margin": None,
            "reason": "ไม่มีผลจัดอันดับ family",
        }
    top_score = float(ranked[0]["score"])
    runner_up_score = float(ranked[1]["score"]) if len(ranked) > 1 else None
    margin = None if runner_up_score is None else round(top_score - runner_up_score, 6)
    if margin is None:
        level = "single_candidate"
        reason = "มี candidate family เดียว จึงไม่มีอันดับสองให้เทียบ"
    elif margin >= MIN_READY_RANKER_MARGIN:
        level = "clear_margin"
        reason = "อันดับหนึ่งชนะอันดับสองชัดเจน"
    else:
        level = "low_margin"
        reason = "อันดับหนึ่งกับอันดับสองคะแนนใกล้กัน ควรให้คนตรวจหรือเก็บ evidence เพิ่มก่อน"
    return {
        "level": level,
        "top_score": round(top_score, 6),
        "runner_up_score": round(runner_up_score, 6) if runner_up_score is not None else None,
        "margin": margin,
        "min_ready_margin": MIN_READY_RANKER_MARGIN,
        "reason": reason,
    }


def family_readiness(features: dict[str, object], family: str) -> dict[str, object]:
    spec = FAMILY_FEATURES[family]
    specific_positive = sorted(
        name
        for name in spec["positive"]
        if name not in GENERIC_RANKER_FEATURES and as_float(features, name) > 0
    )
    blocking_negative = sorted(name for name in spec["negative"] if as_float(features, name) > 0)
    missing_specific_positive = sorted(
        name
        for name in spec["positive"]
        if name not in GENERIC_RANKER_FEATURES and name not in features
    )
    known_signal_missing = (
        "known_family_signal_count" in features
        and as_float(features, "known_family_signal_count") <= 0
    )
    ready = (
        len(specific_positive) >= MIN_READY_SPECIFIC_POSITIVE_SIGNALS
        and not blocking_negative
        and not known_signal_missing
    )
    if ready:
        reason = "มีหลักฐานเฉพาะ family เพียงพอ และไม่พบตัวบล็อกของ family นี้"
    elif blocking_negative:
        reason = "พบตัวบล็อกของ family นี้ จึงไม่ควรถือว่าพร้อมตรวจต่ออัตโนมัติ"
    elif known_signal_missing:
        reason = "scanner ระบุว่า known-family signal ยังไม่พอ จึงไม่ควรถือว่าพร้อมตรวจต่ออัตโนมัติ"
    else:
        reason = "หลักฐานเฉพาะ family ยังบางเกินไป ควรเก็บ evidence เพิ่มก่อน"
    return {
        "ready": ready,
        "specific_positive_signals": specific_positive,
        "blocking_negative_signals": blocking_negative,
        "missing_specific_positive_features": missing_specific_positive,
        "min_ready_specific_positive_signals": MIN_READY_SPECIFIC_POSITIVE_SIGNALS,
        "reason": reason,
    }


def family_decision(
    top_family: dict[str, object],
    threshold: int,
    confidence: dict[str, object] | None = None,
    readiness: dict[str, object] | None = None,
) -> str:
    positive = int(top_family["positive_signals"])
    negative = int(top_family["negative_signals"])
    if positive < threshold:
        if readiness is not None and readiness.get("specific_positive_signals"):
            return "known_family_but_blocked_or_low_confidence"
        if int(top_family.get("product_hint_signals", 0)) > 0:
            return "known_family_but_blocked_or_low_confidence"
        return "unknown_family"
    if readiness is not None and not bool(readiness["ready"]):
        return "known_family_but_blocked_or_low_confidence"
    if confidence is not None and confidence.get("level") == "low_margin":
        return "known_family_but_blocked_or_low_confidence"
    if negative == 0:
        return "known_family_ready"
    return "known_family_but_blocked_or_low_confidence"


def should_force_unknown_family(
    features: dict[str, object],
    top_family: dict[str, object] | None = None,
    readiness: dict[str, object] | None = None,
) -> bool:
    if as_float(features, "unknown_product_detected") <= 0:
        return False
    if (
        readiness is not None
        and readiness.get("specific_positive_signals")
        and top_family is not None
        and int(top_family.get("product_hint_signals", 0)) > 0
    ):
        return False
    unknown_count = as_float(features, "unknown_family_signal_count")
    known_count = as_float(features, "known_family_signal_count")
    return known_count <= unknown_count or known_count <= 0


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
    schema_warnings = normalize_feature_schema(features)
    add_derived_precondition_features(features)

    gate_model = XGBClassifier()
    gate_model.load_model(args.model_dir / "gate_precondition_only.json")
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
    confidence = ranker_confidence(ranked)
    readiness = family_readiness(features, str(top["family"]))
    decision = family_decision(
        top,
        int(manifest["ranker"]["unknown_positive_signal_threshold"]),
        confidence,
        readiness,
    )
    if should_force_unknown_family(features, top, readiness):
        decision = "unknown_family"
        schema_warnings.append("unknown_product_detected forced unknown_family_triage")
    result["ranker"] = {
        "model": "family_ranker",
        "decision": decision,
        "confidence": confidence,
        "family_readiness": readiness,
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
