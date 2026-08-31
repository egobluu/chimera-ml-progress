#!/usr/bin/env python3
"""Train ML-only Exploitability Gate v0.2 with XGBoost.

The Gate is a binary classifier:
    1 = exploit
    0 = no_exploit

Evaluation uses leave-one-target-out because the dataset is still small.  The
threshold sweep intentionally prioritizes recall / low false negatives first:
in this project, skipping a truly vulnerable target is worse than spending time
checking a false positive.
"""
import json
import csv
import os
import sys
import numpy as np

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import LeaveOneOut
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("ERROR: scikit-learn not installed")
    sys.exit(1)

DATASET_CSV = "/home/kali/reports/dec-ml-only-gate-v02-2026-08-31/target-exploitability-dataset.csv"
OUTPUT_DIR = "/home/kali/reports/dec-ml-only-gate-v02-2026-08-31"
MODELS_DIR = os.path.join(OUTPUT_DIR, "models")
DERIVED_DIR = os.path.join(OUTPUT_DIR, "derived")

FEATURES = [
    "service_port",
    "is_http_target",
    "is_non_http_service",
    "raw_file_count",
    "tool_httpx_success",
    "tool_nuclei_success",
    "tool_metasploit_success",
    "metasploit_module_found",
    "version_in_vulnerable_range_true",
    "version_in_vulnerable_range_false",
    "version_not_affected",
    "version_patched",
    "precondition_pass_count",
    "precondition_fail_count",
    "negative_evidence_count",
    "auth_required",
    "no_auth_required",
    "endpoint_reachable_count",
    "endpoint_missing_count",
    "method_put_allowed",
    "method_put_rejected",
    "ajp_port_open",
    "ajp_port_closed",
    "anonymous_access",
    "velocity_enabled",
    "invokefunction_reachable",
    "invokefunction_not_found",
    "admin_party_enabled",
    "spring_detected",
    "spring_not_detected",
    "wrong_software_type",
    "rce_confirmed",
    "msf_check_confirmed",
    "msf_check_not_vulnerable",
    "nuclei_cve_confirmed",
    "nuclei_fingerprint_only",
    "nuclei_no_vuln_found",
    "manual_poc_failed",
    "painless_sandbox_blocks",
    "path_traversal_blocked",
    "auth_blocks_exploit",
    "endpoint_not_found",
    "wrong_version",
    "no_msf_module",
]

def load_dataset():
    targets = []
    labels = []
    feature_matrix = []
    
    with open(DATASET_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets.append(row["target_id"])
            labels.append(int(row["label"]))
            features = [float(row.get(f, 0)) for f in FEATURES]
            feature_matrix.append(features)
    
    return targets, labels, np.array(feature_matrix)

def train_xgboost(X_train, y_train, X_test, y_test):
    if HAS_XGB:
        model = xgb.XGBClassifier(
            objective="binary:logistic",
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            min_child_weight=2,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            eval_metric="logloss",
            random_state=42,
            use_label_encoder=False,
        )
    else:
        model = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            min_samples_leaf=2,
            random_state=42,
        )
    
    model.fit(X_train, y_train)
    y_proba = model.predict_proba(X_test)[:, 1]
    return model, y_proba

def evaluate_at_threshold(y_true, y_proba, threshold):
    y_pred = (y_proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    return {
        "threshold": threshold,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "false_negatives": int(fn),
        "false_positives": int(fp),
    }

def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(DERIVED_DIR, exist_ok=True)
    
    # Load dataset
    targets, labels, X = load_dataset()
    y = np.array(labels)
    
    print(f"Loaded {len(targets)} targets")
    print(f"Positive: {sum(y == 1)}, Negative: {sum(y == 0)}")
    print(f"Features: {X.shape[1]}")
    
    # Leave-One-Target-Out evaluation
    loo = LeaveOneOut()
    all_probas = np.zeros(len(targets))
    all_true = np.zeros(len(targets))
    all_target_names = []
    
    print("\n=== Leave-One-Target-Out Evaluation ===")
    fold = 0
    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model, y_proba = train_xgboost(X_train, y_train, X_test, y_test)
        
        all_probas[test_idx] = y_proba
        all_true[test_idx] = y_test
        all_target_names.append(targets[test_idx[0]])
        
        fold += 1
        if fold % 10 == 0:
            print(f"  Fold {fold}/{len(targets)} done")
    
    print(f"  All {fold} folds completed")
    
    # Threshold sweep
    thresholds = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    sweep_results = []
    
    print("\n=== Threshold Sweep ===")
    print(f"{'Threshold':>10} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'FN':>5} {'FP':>5}")
    
    best_score = -1
    best_threshold = 0.5
    best_result = None
    
    for t in thresholds:
        result = evaluate_at_threshold(all_true, all_probas, t)
        sweep_results.append(result)
        
        fn = result["false_negatives"]
        fp = result["false_positives"]
        recall = result["recall"]
        f1 = result["f1"]
        
        print(f"{t:>10.2f} {result['accuracy']:>10.4f} {result['precision']:>10.4f} {result['recall']:>10.4f} {result['f1']:>10.4f} {fn:>5} {fp:>5}")
        
        # Selection criteria:
        # 1. FN <= 2
        # 2. Recall >= 0.90
        # 3. Lowest FP
        # 4. Highest F1
        if fn <= 2 and recall >= 0.90:
            # Score = F1 weighted by FP reduction
            score = f1 * (1 - fp / 40)  # penalize FP
            if score > best_score:
                best_score = score
                best_threshold = t
                best_result = result
    
    # If no threshold meets criteria, find best FN <= 2
    if best_result is None:
        print("\n  No threshold meets Recall>=0.90 & FN<=2, finding best FN<=2...")
        for t in thresholds:
            result = evaluate_at_threshold(all_true, all_probas, t)
            fn = result["false_negatives"]
            fp = result["false_positives"]
            if fn <= 2:
                score = result["f1"] * (1 - fp / 40)
                if score > best_score:
                    best_score = score
                    best_threshold = t
                    best_result = result
    
    # Last resort: lowest FN
    if best_result is None:
        print("\n  Finding lowest FN...")
        min_fn = float('inf')
        for t in thresholds:
            result = evaluate_at_threshold(all_true, all_probas, t)
            if result["false_negatives"] < min_fn:
                min_fn = result["false_negatives"]
                best_threshold = t
                best_result = result
    
    print(f"\nBest threshold: {best_threshold}")
    print(f"  FN: {best_result['false_negatives']}, FP: {best_result['false_positives']}")
    print(f"  Recall: {best_result['recall']}, F1: {best_result['f1']}")
    
    # Failure analysis
    print("\n=== Failure Analysis ===")
    y_pred_best = (all_probas >= best_threshold).astype(int)
    
    fn_targets = []
    fp_targets = []
    for i, t in enumerate(targets):
        if all_true[i] == 1 and y_pred_best[i] == 0:
            fn_targets.append((t, all_probas[i]))
            print(f"  FALSE NEGATIVE: {t} (score={all_probas[i]:.4f})")
        elif all_true[i] == 0 and y_pred_best[i] == 1:
            fp_targets.append((t, all_probas[i]))
            print(f"  FALSE POSITIVE: {t} (score={all_probas[i]:.4f})")
    
    # Train final model on all data
    print("\n=== Training Final Model ===")
    if HAS_XGB:
        final_model = xgb.XGBClassifier(
            objective="binary:logistic",
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            min_child_weight=2,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            eval_metric="logloss",
            random_state=42,
            use_label_encoder=False,
        )
    else:
        final_model = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            min_samples_leaf=2,
            random_state=42,
        )
    
    final_model.fit(X, y)
    
    # Save model
    model_path = os.path.join(MODELS_DIR, "gate_xgb_v02.json")
    if HAS_XGB:
        final_model.save_model(model_path)
    else:
        import pickle
        with open(model_path, "wb") as f:
            pickle.dump(final_model, f)
    print(f"Model saved to {model_path}")
    
    # Feature importance
    importances = final_model.feature_importances_
    importance_data = sorted(zip(FEATURES, importances), key=lambda x: -x[1])
    
    print("\n=== Feature Importance (Top 15) ===")
    for feat, imp in importance_data[:15]:
        print(f"  {feat}: {imp:.4f}")
    
    # Save feature importance
    importance_path = os.path.join(DERIVED_DIR, "gate-feature-importance.csv")
    with open(importance_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["feature", "importance"])
        for feat, imp in importance_data:
            writer.writerow([feat, round(imp, 4)])
    
    # Save threshold sweep
    sweep_path = os.path.join(DERIVED_DIR, "gate-threshold-sweep.csv")
    with open(sweep_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sweep_results[0].keys())
        writer.writeheader()
        writer.writerows(sweep_results)
    
    # Save failure analysis
    failure_path = os.path.join(DERIVED_DIR, "gate-failure-analysis.csv")
    with open(failure_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["target_id", "true_label", "predicted_label", "probability", "failure_type"])
        for i, t in enumerate(targets):
            pred = y_pred_best[i]
            prob = all_probas[i]
            true = int(all_true[i])
            if true == 1 and pred == 0:
                writer.writerow([t, true, pred, round(prob, 4), "false_negative"])
            elif true == 0 and pred == 1:
                writer.writerow([t, true, pred, round(prob, 4), "false_positive"])
            else:
                writer.writerow([t, true, pred, round(prob, 4), "correct"])
    
    # Save predictions
    predictions_path = os.path.join(DERIVED_DIR, "gate-predictions.csv")
    with open(predictions_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["target_id", "true_label", "predicted_label", "probability", "threshold"])
        for i, t in enumerate(targets):
            writer.writerow([t, int(all_true[i]), int(y_pred_best[i]), round(all_probas[i], 4), best_threshold])
    
    # Save gate metrics
    gate_metrics = {
        "model_version": "v0.2",
        "best_threshold": best_threshold,
        "metrics_at_best": best_result,
        "recall_target": 0.90,
        "recall_achieved": best_result["recall"],
        "recall_pass": best_result["recall"] >= 0.90,
        "fn_target": 2,
        "fn_achieved": best_result["false_negatives"],
        "fn_pass": best_result["false_negatives"] <= 2,
        "fp_target": 6,
        "fp_achieved": best_result["false_positives"],
        "fp_pass": best_result["false_positives"] <= 6,
        "f1_target": 0.769,
        "f1_achieved": best_result["f1"],
        "f1_pass": best_result["f1"] > 0.769,
        "total_targets": len(targets),
        "positive_targets": int(sum(y == 1)),
        "negative_targets": int(sum(y == 0)),
        "features_used": FEATURES,
        "feature_count": len(FEATURES),
        "false_negative_targets": [t for t, _ in fn_targets],
        "false_positive_targets": [t for t, _ in fp_targets],
        "threshold_sweep": sweep_results,
    }
    
    metrics_path = os.path.join(OUTPUT_DIR, "gate-metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(gate_metrics, f, indent=2)
    
    print(f"\n=== Results ===")
    print(f"Metrics saved to {metrics_path}")
    print(f"Failure analysis saved to {failure_path}")
    print(f"Threshold sweep saved to {sweep_path}")
    print(f"Feature importance saved to {importance_path}")
    print(f"Predictions saved to {predictions_path}")
    
    # Check success criteria
    print(f"\n=== Success Criteria ===")
    print(f"Recall >= 0.90: {'PASS' if best_result['recall'] >= 0.90 else 'FAIL'} ({best_result['recall']:.4f})")
    print(f"FN <= 2: {'PASS' if best_result['false_negatives'] <= 2 else 'FAIL'} ({best_result['false_negatives']})")
    print(f"FP <= 6: {'PASS' if best_result['false_positives'] <= 6 else 'FAIL'} ({best_result['false_positives']})")
    print(f"F1 > 0.769: {'PASS' if best_result['f1'] > 0.769 else 'FAIL'} ({best_result['f1']:.4f})")
    print(f"Model saved: PASS")
    print(f"Inference script: PENDING")

if __name__ == "__main__":
    main()
