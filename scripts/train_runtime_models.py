#!/usr/bin/env python3
"""Train the prototype runtime models used by the LLM/agentic layer.

This script creates the small set of artifacts that should be treated as the
"current usable prototype":

- an XGBoost Gate trained with the precondition-only feature profile
- an XGBoost Family Ranker trained on known positive families
- metadata that tells inference which features, families, and thresholds to use
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from train_family_ranker import build_group, infer_true_family, load_positive_rows, new_ranker
from train_gate_profiles import build_matrix, choose_threshold, load_dataset, loo_predict, new_model, profile_features


def train_gate(dataset: Path, out_dir: Path) -> dict[str, object]:
    targets, labels, data = load_dataset(dataset)
    all_features = list(data.keys())
    features = profile_features("precondition_only", all_features)
    X = build_matrix(data, features)
    probabilities = loo_predict(X, labels)
    metrics = choose_threshold(labels, probabilities)

    model = new_model()
    model.fit(X, labels)
    model_path = out_dir / "gate_precondition_only.json"
    model.save_model(model_path)

    return {
        "model_path": str(model_path),
        "profile": "precondition_only",
        "features": features,
        "threshold": metrics["threshold"],
        "loo_metrics": metrics,
        "train_targets": len(targets),
    }


def train_ranker(dataset: Path, out_dir: Path) -> dict[str, object]:
    rows = load_positive_rows(dataset)
    families = sorted({infer_true_family(row["target_id"]) for row in rows if infer_true_family(row["target_id"])})
    X_train, y_train, _, _ = build_group(rows, families)
    group_train = [len(families)] * len(rows)

    model = new_ranker()
    model.fit(X_train, y_train, group=group_train)
    model_path = out_dir / "family_ranker.json"
    model.save_model(model_path)

    return {
        "model_path": str(model_path),
        "families": families,
        "positive_train_targets": len(rows),
        "candidate_families": len(families),
        "unknown_positive_signal_threshold": 2,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    gate = train_gate(args.dataset, args.out_dir)
    ranker = train_ranker(args.dataset, args.out_dir)
    manifest = {
        "name": "chimera-ml-prototype-runtime",
        "dataset": str(args.dataset),
        "gate": gate,
        "ranker": ranker,
        "runtime_entrypoint": "scripts/predict_prototype.py",
        "intended_use_th": (
            "ใช้กับ feature ที่รู้ได้ก่อนยิง exploit เพื่อแนะนำว่า target น่าลองต่อไหม "
            "และถ้าน่าลองควรเริ่มจาก exploit family ใด"
        ),
        "not_for_th": (
            "ไม่ใช่ตัวพิสูจน์ exploit สำเร็จ ต้องใช้ Metasploit check/manual PoC ยืนยันหลังจากนี้"
        ),
    }
    (args.out_dir / "prototype_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()