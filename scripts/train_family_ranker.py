#!/usr/bin/env python3
"""Train/evaluate an XGBoost exploit-family ranker.

The gate answers "should we try exploitation?". This ranker answers the next
question: "which exploit family should be tried first?". Negative/no-exploit
targets are excluded from ranking training because they belong to the gate
problem, not the family-ranking problem.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from xgboost import XGBRanker


FAMILY_FEATURES: dict[str, dict[str, set[str]]] = {
    "tomcat_put": {
        "positive": {"method_put_allowed", "jsp_upload_candidate", "version_in_vulnerable_range"},
        "negative": {"method_put_rejected", "upload_blocked", "wrong_context_path", "version_patched"},
    },
    "tomcat_ajp": {
        "positive": {"ajp_port_open", "version_in_vulnerable_range"},
        "negative": {"ajp_port_closed", "ajp_not_exposed", "version_patched"},
    },
    "shiro_key": {
        "positive": {"default_key_likely", "rememberme_deleteMe_seen"},
        "negative": {"default_key_unlikely", "version_patched"},
    },
    "solr_velocity": {
        "positive": {"solr_core_found", "velocity_enabled", "config_api_accessible", "version_in_vulnerable_range"},
        "negative": {"velocity_disabled", "config_api_blocked", "version_patched"},
    },
    "thinkphp_rce": {
        "positive": {"invokefunction_reachable", "rce_endpoint_candidate_found", "version_in_vulnerable_range"},
        "negative": {"invokefunction_not_found", "endpoint_not_found", "version_patched"},
    },
    "couchdb_auth": {
        "positive": {"admin_party_enabled", "no_auth_required", "config_accessible", "users_db_accessible"},
        "negative": {"auth_required", "config_blocked", "version_patched"},
    },
    "redis": {
        "positive": {"lua_available", "no_auth_required", "version_in_vulnerable_range"},
        "negative": {"auth_required", "version_patched", "version_not_affected"},
    },
    "grafana": {
        "positive": {"path_traversal_blocked", "version_in_vulnerable_range"},
        "negative": {"version_patched", "auth_required"},
    },
    "nexus": {
        "positive": {"anonymous_access", "endpoint_reachable_count", "version_in_vulnerable_range"},
        "negative": {"auth_required", "endpoint_missing_count", "version_patched"},
    },
    "jenkins": {
        "positive": {"endpoint_reachable_count", "version_in_vulnerable_range"},
        "negative": {"auth_required", "endpoint_missing_count", "version_patched"},
    },
    "nginx": {
        "positive": {"version_in_vulnerable_range"},
        "negative": {"version_patched", "wrong_version"},
    },
    "spring": {
        "positive": {"actuator_path_found", "version_in_vulnerable_range"},
        "negative": {"spring_not_detected", "actuator_path_missing", "wrong_software_type"},
    },
    "struts2": {
        "positive": {"endpoint_reachable_count", "version_in_vulnerable_range"},
        "negative": {"endpoint_missing_count", "version_patched"},
    },
    "phpmyadmin": {
        "positive": {"endpoint_reachable_count", "version_in_vulnerable_range"},
        "negative": {"endpoint_missing_count", "version_patched"},
    },
    "elasticsearch": {
        "positive": {"version_in_vulnerable_range"},
        "negative": {"painless_sandbox_blocks", "version_patched"},
    },
    "flask": {
        "positive": {"rce_endpoint_candidate_found", "endpoint_reachable_count"},
        "negative": {"endpoint_missing_count", "version_patched"},
    },
    "joomla": {
        "positive": {"api_path_found", "no_auth_required", "version_in_vulnerable_range"},
        "negative": {"auth_required", "version_patched"},
    },
    "nextjs": {
        "positive": {"endpoint_reachable_count", "version_in_vulnerable_range"},
        "negative": {"endpoint_missing_count", "version_patched"},
    },
}

ALL_CANDIDATE_FEATURES = sorted(
    {
        feature
        for spec in FAMILY_FEATURES.values()
        for group in ("positive", "negative")
        for feature in spec[group]
    }
)


def infer_true_family(target_id: str) -> str | None:
    lowered = target_id.lower()
    if "tomcat_put" in lowered or "cve-2017-12615" in lowered:
        return "tomcat_put"
    if "tomcat_ajp" in lowered or "cve-2020-1938" in lowered:
        return "tomcat_ajp"
    if "shiro" in lowered:
        return "shiro_key"
    if "solr" in lowered:
        return "solr_velocity"
    if "thinkphp" in lowered:
        return "thinkphp_rce"
    if "couchdb" in lowered:
        return "couchdb_auth"
    for family in FAMILY_FEATURES:
        if family in lowered:
            return family
    if "redis" in lowered:
        return "redis"
    if "grafana" in lowered:
        return "grafana"
    if "nexus" in lowered:
        return "nexus"
    if "jenkins" in lowered:
        return "jenkins"
    if "nginx" in lowered:
        return "nginx"
    if "spring" in lowered:
        return "spring"
    if "struts" in lowered:
        return "struts2"
    if "phpmyadmin" in lowered:
        return "phpmyadmin"
    if "elastic" in lowered:
        return "elasticsearch"
    if "flask" in lowered:
        return "flask"
    if "joomla" in lowered:
        return "joomla"
    if "nextjs" in lowered:
        return "nextjs"
    return None


def as_float(row: dict[str, str], name: str) -> float:
    try:
        return float(row.get(name) or 0)
    except ValueError:
        return 0.0


def feature_value(row: dict[str, str], name: str) -> float:
    return 1.0 if as_float(row, name) > 0 else 0.0


def candidate_vector(row: dict[str, str], candidate: str, families: list[str]) -> list[float]:
    spec = FAMILY_FEATURES[candidate]
    positive_values = [feature_value(row, name) for name in sorted(spec["positive"])]
    negative_values = [feature_value(row, name) for name in sorted(spec["negative"])]
    pos_count = sum(positive_values)
    neg_count = sum(negative_values)

    vector = [
        pos_count,
        neg_count,
        pos_count - neg_count,
        1.0 if pos_count > 0 else 0.0,
        1.0 if neg_count > 0 else 0.0,
        as_float(row, "service_port"),
        as_float(row, "is_http_target"),
        as_float(row, "is_non_http_service"),
    ]
    for feature in ALL_CANDIDATE_FEATURES:
        if feature in spec["positive"] or feature in spec["negative"]:
            vector.append(feature_value(row, feature))
        else:
            vector.append(0.0)
    vector.extend(1.0 if family == candidate else 0.0 for family in families)
    return vector


def load_positive_rows(path: Path) -> list[dict[str, str]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    positives = [row for row in rows if int(row["label"]) == 1 and infer_true_family(row["target_id"])]
    return positives


def build_group(rows: list[dict[str, str]], families: list[str]) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    X: list[list[float]] = []
    y: list[int] = []
    target_ids: list[str] = []
    candidates: list[str] = []
    for row in rows:
        true_family = infer_true_family(row["target_id"])
        for candidate in families:
            X.append(candidate_vector(row, candidate, families))
            y.append(1 if candidate == true_family else 0)
            target_ids.append(row["target_id"])
            candidates.append(candidate)
    return np.array(X), np.array(y), target_ids, candidates


def new_ranker() -> XGBRanker:
    return XGBRanker(
        objective="rank:pairwise",
        n_estimators=120,
        max_depth=3,
        learning_rate=0.08,
        min_child_weight=1,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
    )


def evaluate_ranking(rows: list[dict[str, str]], families: list[str]) -> tuple[list[dict[str, object]], dict[str, object]]:
    predictions: list[dict[str, object]] = []
    reciprocal_ranks: list[float] = []
    top1 = top3 = top5 = 0

    for index, test_row in enumerate(rows):
        train_rows = [row for i, row in enumerate(rows) if i != index]
        X_train, y_train, _, _ = build_group(train_rows, families)
        group_train = [len(families)] * len(train_rows)
        model = new_ranker()
        model.fit(X_train, y_train, group=group_train)

        X_test, _, _, candidates = build_group([test_row], families)
        scores = model.predict(X_test)
        ranked = sorted(zip(candidates, scores), key=lambda item: item[1], reverse=True)
        true_family = infer_true_family(test_row["target_id"])
        rank = [candidate for candidate, _ in ranked].index(true_family) + 1
        top1 += int(rank <= 1)
        top3 += int(rank <= 3)
        top5 += int(rank <= 5)
        reciprocal_ranks.append(1.0 / rank)
        predictions.append(
            {
                "target_id": test_row["target_id"],
                "true_family": true_family,
                "rank": rank,
                "top1_family": ranked[0][0],
                "top1_score": round(float(ranked[0][1]), 6),
                "top3": "|".join(candidate for candidate, _ in ranked[:3]),
                "top5": "|".join(candidate for candidate, _ in ranked[:5]),
            }
        )

    total = len(rows)
    summary = {
        "positive_targets": total,
        "candidate_families": len(families),
        "top1": round(top1 / total, 4),
        "top3": round(top3 / total, 4),
        "top5": round(top5 / total, 4),
        "mrr": round(float(np.mean(reciprocal_ranks)), 4),
    }
    return predictions, summary


def summarize_predictions(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    return {
        "targets": total,
        "top1": round(sum(int(row["rank"]) <= 1 for row in rows) / total, 4),
        "top3": round(sum(int(row["rank"]) <= 3 for row in rows) / total, 4),
        "top5": round(sum(int(row["rank"]) <= 5 for row in rows) / total, 4),
        "mrr": round(sum(1 / int(row["rank"]) for row in rows) / total, 4),
    }


def segment_name(target_id: str) -> str:
    clean_markers = (
        "_positive",
        "tomcat_put_",
        "tomcat_ajp_",
        "shiro_default_key_",
        "solr_velocity_",
        "thinkphp_invokefunction_",
        "couchdb_admin_party_",
    )
    return "clean_control_positive" if any(marker in target_id for marker in clean_markers) else "original_positive"


def segment_summary(predictions: list[dict[str, object]]) -> list[dict[str, object]]:
    segments: dict[str, list[dict[str, object]]] = {}
    for row in predictions:
        segments.setdefault(segment_name(str(row["target_id"])), []).append(row)
    return [{"segment": name, **summarize_predictions(rows)} for name, rows in sorted(segments.items())]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    rows = load_positive_rows(args.dataset)
    families = sorted({infer_true_family(row["target_id"]) for row in rows if infer_true_family(row["target_id"])})
    families = [family for family in families if family in FAMILY_FEATURES]
    predictions, summary = evaluate_ranking(rows, families)
    segments = segment_summary(predictions)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "family-ranker-predictions.csv", predictions)
    write_csv(args.out_dir / "family-ranker-segment-summary.csv", segments)
    (args.out_dir / "family-ranker-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.out_dir / "family-ranker-segment-summary.json").write_text(
        json.dumps(segments, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
