#!/usr/bin/env python3
"""Evaluate how the family ranker behaves on unknown/out-of-scope targets.

The XGBoost ranker is a closed-set model: it always ranks the candidate
families it was given. This script adds a small open-set guard that rejects a
ranking when the target does not match enough family-specific positive
precondition signals.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from train_family_ranker import (
    FAMILY_FEATURES,
    build_group,
    candidate_vector,
    infer_true_family,
    load_positive_rows,
    new_ranker,
)


UNKNOWN_THRESHOLD = 2


def as_float(row: dict[str, str], name: str) -> float:
    try:
        return float(row.get(name) or 0)
    except ValueError:
        return 0.0


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def blank_like(fields: list[str], target_id: str) -> dict[str, str]:
    row = {field: "0" for field in fields}
    row["target_id"] = target_id
    row["label"] = "1"
    row["service_port"] = "80"
    row["is_http_target"] = "1"
    row["is_non_http_service"] = "0"
    return row


def synthetic_unknown_rows(fields: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    wordpress = blank_like(fields, "unknown_wordpress_plugin_rce")
    wordpress["endpoint_reachable_count"] = "1"
    wordpress["login_path_found"] = "1"
    wordpress["whatweb_tech_detected"] = "1"
    rows.append(wordpress)

    laravel = blank_like(fields, "unknown_laravel_debug_rce")
    laravel["endpoint_reachable_count"] = "1"
    laravel["sensitive_path_found"] = "1"
    laravel["whatweb_tech_detected"] = "1"
    rows.append(laravel)

    generic_php = blank_like(fields, "unknown_generic_php_upload")
    generic_php["upload_path_found"] = "1"
    generic_php["endpoint_reachable_count"] = "1"
    generic_php["whatweb_tech_detected"] = "1"
    rows.append(generic_php)

    drupal = blank_like(fields, "unknown_drupal_rce")
    drupal["endpoint_reachable_count"] = "1"
    drupal["admin_path_found"] = "1"
    drupal["whatweb_tech_detected"] = "1"
    rows.append(drupal)

    return rows


def train_full_ranker(dataset: Path, families: list[str]):
    positives = load_positive_rows(dataset)
    X_train, y_train, _, _ = build_group(positives, families)
    group_train = [len(families)] * len(positives)
    model = new_ranker()
    model.fit(X_train, y_train, group=group_train)
    return model


def candidate_signal_counts(row: dict[str, str], candidate: str) -> tuple[int, int]:
    spec = FAMILY_FEATURES[candidate]
    positive = sum(1 for feature in spec["positive"] if as_float(row, feature) > 0)
    negative = sum(1 for feature in spec["negative"] if as_float(row, feature) > 0)
    return positive, negative


def score_row(row: dict[str, str], families: list[str], model) -> dict[str, object]:
    X = np.array([candidate_vector(row, candidate, families) for candidate in families])
    scores = model.predict(X)
    ranked = sorted(zip(families, scores), key=lambda item: item[1], reverse=True)
    top1, top1_score = ranked[0]
    top2, top2_score = ranked[1]
    top1_positive_signals, top1_negative_signals = candidate_signal_counts(row, top1)
    max_positive_signals = max(candidate_signal_counts(row, candidate)[0] for candidate in families)
    max_signal_decision = "known_family" if max_positive_signals >= UNKNOWN_THRESHOLD else "unknown_family"
    top1_signal_decision = "known_family" if top1_positive_signals >= UNKNOWN_THRESHOLD else "unknown_family"
    clean_top1_decision = (
        "known_family"
        if top1_positive_signals >= UNKNOWN_THRESHOLD and top1_negative_signals == 0
        else "unknown_family"
    )
    return {
        "target_id": row["target_id"],
        "label": row.get("label", ""),
        "inferred_known_family": infer_true_family(row["target_id"]) or "",
        "top1_family": top1,
        "top1_score": round(float(top1_score), 6),
        "top2_family": top2,
        "top2_score": round(float(top2_score), 6),
        "score_margin": round(float(top1_score - top2_score), 6),
        "top1_positive_signals": top1_positive_signals,
        "top1_negative_signals": top1_negative_signals,
        "max_positive_signals": max_positive_signals,
        "max_signal_decision": max_signal_decision,
        "top1_signal_decision": top1_signal_decision,
        "clean_top1_decision": clean_top1_decision,
    }


def summarize(rows: list[dict[str, object]], decision_field: str) -> dict[str, object]:
    total = len(rows)
    unknown = sum(1 for row in rows if row[decision_field] == "unknown_family")
    return {
        "targets": total,
        "unknown_rejected": unknown,
        "unknown_reject_rate": round(unknown / total, 4) if total else 0,
        "forced_known_without_guard": total,
        "threshold_max_positive_signals": UNKNOWN_THRESHOLD,
    }


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

    all_rows = load_rows(args.dataset)
    families = sorted({infer_true_family(row["target_id"]) for row in all_rows if infer_true_family(row["target_id"])})
    families = [family for family in families if family in FAMILY_FEATURES]
    model = train_full_ranker(args.dataset, families)

    fields = list(all_rows[0].keys())
    negative_rows = [row for row in all_rows if row.get("label") == "0"]
    synthetic_rows = synthetic_unknown_rows(fields)
    known_positive_rows = [row for row in all_rows if row.get("label") == "1" and infer_true_family(row["target_id"])]
    known_positive_predictions = [score_row(row, families, model) for row in known_positive_rows]
    negative_predictions = [score_row(row, families, model) for row in negative_rows]
    synthetic_predictions = [score_row(row, families, model) for row in synthetic_rows]
    combined_predictions = negative_predictions + synthetic_predictions

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "unknown-family-known-positive-control.csv", known_positive_predictions)
    write_csv(args.out_dir / "unknown-family-negative-predictions.csv", negative_predictions)
    write_csv(args.out_dir / "unknown-family-synthetic-predictions.csv", synthetic_predictions)
    write_csv(args.out_dir / "unknown-family-combined-predictions.csv", combined_predictions)
    summary = {
        "rules": {
            "max_signal_decision": "known if any candidate family has at least 2 positive signals",
            "top1_signal_decision": "known if the winning family has at least 2 positive signals",
            "clean_top1_decision": "known if the winning family has at least 2 positive signals and 0 negative signals",
        },
        "known_positive_control": {
            "max_signal_decision": summarize(known_positive_predictions, "max_signal_decision"),
            "top1_signal_decision": summarize(known_positive_predictions, "top1_signal_decision"),
            "clean_top1_decision": summarize(known_positive_predictions, "clean_top1_decision"),
        },
        "negative_or_no_exploit_rows": {
            "max_signal_decision": summarize(negative_predictions, "max_signal_decision"),
            "top1_signal_decision": summarize(negative_predictions, "top1_signal_decision"),
            "clean_top1_decision": summarize(negative_predictions, "clean_top1_decision"),
        },
        "synthetic_unknown_rows": {
            "max_signal_decision": summarize(synthetic_predictions, "max_signal_decision"),
            "top1_signal_decision": summarize(synthetic_predictions, "top1_signal_decision"),
            "clean_top1_decision": summarize(synthetic_predictions, "clean_top1_decision"),
        },
        "combined_unknown_rows": {
            "max_signal_decision": summarize(combined_predictions, "max_signal_decision"),
            "top1_signal_decision": summarize(combined_predictions, "top1_signal_decision"),
            "clean_top1_decision": summarize(combined_predictions, "clean_top1_decision"),
        },
        "known_candidate_families": families,
        "note": "Without the open-set guard, the closed-set ranker always returns one known family.",
    }
    (args.out_dir / "unknown-family-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()