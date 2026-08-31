#!/usr/bin/env python3
"""Train/evaluate multiple exploitability gate feature profiles.

The goal is to compare a strong but leak-prone profile against stricter
precheck profiles. This makes the model failure mode visible before we claim
the gate is ready for real use.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import LeaveOneOut
from xgboost import XGBClassifier


ID_COLUMNS = {"target_id", "label"}

POSTCHECK_OR_LEAK_RISK = {
    "tool_metasploit_success",
    "msf_check_confirmed",
    "msf_check_not_vulnerable",
    "rce_confirmed",
    "manual_poc_failed",
    "negative_evidence_count",
}

METASPLOIT_FEATURES = {
    "tool_metasploit_success",
    "metasploit_module_found",
    "msf_check_confirmed",
    "msf_check_not_vulnerable",
}

NUCLEI_CONFIRMATION_FEATURES = {
    "nuclei_cve_confirmed",
}

BASIC_SCANNER_FEATURES = {
    "service_port",
    "is_http_target",
    "is_non_http_service",
    "raw_file_count",
    "tool_httpx_success",
    "tool_nuclei_success",
    "nuclei_fingerprint_only",
    "nuclei_no_vuln_found",
}


def load_dataset(path: Path) -> tuple[list[str], np.ndarray, dict[str, np.ndarray]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    targets = [row["target_id"] for row in rows]
    labels = np.array([int(row["label"]) for row in rows])
    columns = [name for name in rows[0] if name not in ID_COLUMNS]
    data = {
        name: np.array([float(row.get(name) or 0) for row in rows])
        for name in columns
    }
    return targets, labels, data


def profile_features(profile: str, all_features: list[str]) -> list[str]:
    if profile == "full_v02":
        return all_features
    if profile == "strict_precheck":
        return [name for name in all_features if name not in POSTCHECK_OR_LEAK_RISK]
    if profile == "strict_no_negative_count":
        return [name for name in all_features if name != "negative_evidence_count"]
    if profile == "scanner_only":
        return [name for name in all_features if name in BASIC_SCANNER_FEATURES]
    if profile == "no_metasploit":
        return [name for name in all_features if name not in METASPLOIT_FEATURES]
    if profile == "no_nuclei_confirm":
        return [name for name in all_features if name not in NUCLEI_CONFIRMATION_FEATURES]
    raise ValueError(f"unknown profile: {profile}")


def build_matrix(data: dict[str, np.ndarray], features: list[str]) -> np.ndarray:
    return np.column_stack([data[name] for name in features])


def new_model() -> XGBClassifier:
    return XGBClassifier(
        objective="binary:logistic",
        n_estimators=120,
        max_depth=3,
        learning_rate=0.08,
        min_child_weight=2,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.2,
        reg_lambda=1.2,
        eval_metric="logloss",
        random_state=42,
    )


def evaluate(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, object]:
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    return {
        "threshold": threshold,
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "precision": round(float(precision_score(y_true, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def choose_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> dict[str, object]:
    candidates = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    results = [evaluate(y_true, probabilities, threshold) for threshold in candidates]

    # Prefer low false negatives first, then fewer false positives, then F1.
    return sorted(results, key=lambda row: (row["fn"], row["fp"], -row["f1"], row["threshold"]))[0]


def loo_predict(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    probabilities = np.zeros(len(y))
    for train_idx, test_idx in LeaveOneOut().split(X):
        model = new_model()
        model.fit(X[train_idx], y[train_idx])
        probabilities[test_idx] = model.predict_proba(X[test_idx])[:, 1]
    return probabilities


def write_predictions(path: Path, targets: list[str], y: np.ndarray, probabilities: np.ndarray, threshold: float) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["target_id", "true_label", "predicted_label", "probability", "threshold"])
        for target, true_label, probability in zip(targets, y, probabilities):
            writer.writerow([target, int(true_label), int(probability >= threshold), round(float(probability), 4), threshold])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    targets, y, data = load_dataset(args.dataset)
    all_features = list(data.keys())
    profiles = [
        "full_v02",
        "strict_precheck",
        "strict_no_negative_count",
        "scanner_only",
        "no_metasploit",
        "no_nuclei_confirm",
    ]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    summary: list[dict[str, object]] = []
    for profile in profiles:
        features = profile_features(profile, all_features)
        X = build_matrix(data, features)
        probabilities = loo_predict(X, y)
        metrics = choose_threshold(y, probabilities)
        write_predictions(args.out_dir / f"{profile}-predictions.csv", targets, y, probabilities, float(metrics["threshold"]))
        summary.append(
            {
                "profile": profile,
                "features": len(features),
                **metrics,
            }
        )

    with (args.out_dir / "gate-profile-comparison.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    with (args.out_dir / "gate-profile-comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
