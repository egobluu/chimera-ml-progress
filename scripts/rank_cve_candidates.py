#!/usr/bin/env python3
"""Rank CVE/module candidates inside a predicted exploit family."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_RULES = Path("runtime/resolver/cve-ranking-rules.json")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        if isinstance(value, dict):
            rows.append(value)
    return rows


def as_float(row: dict[str, Any], name: str) -> float:
    try:
        return float(row.get(name) or 0)
    except (TypeError, ValueError):
        return 0.0


def active(features: dict[str, Any], name: str) -> bool:
    return as_float(features, name) > 0


def cve_id(row: dict[str, Any]) -> str:
    return str(row.get("cve") or row.get("cve_id") or "").upper()


def enrichment_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {cve_id(row): row for row in rows if cve_id(row)}


def feature_or_enrichment_number(features: dict[str, Any], enrichment: dict[str, Any], *names: str) -> float:
    for name in names:
        if name in features:
            return as_float(features, name)
        if name in enrichment:
            return as_float(enrichment, name)
    return 0.0


def feature_or_enrichment_bool(features: dict[str, Any], enrichment: dict[str, Any], *names: str) -> bool:
    for name in names:
        if name in features:
            return bool(features[name])
        if name in enrichment:
            return bool(enrichment[name])
    return False


def score_candidate(
    candidate: dict[str, Any],
    features: dict[str, Any],
    enrichment: dict[str, Any],
    weights: dict[str, float],
) -> dict[str, Any]:
    required = [str(name) for name in candidate.get("required_features", [])]
    blocking = [str(name) for name in candidate.get("blocking_features", [])]
    matched_required = [name for name in required if active(features, name)]
    matched_blocking = [name for name in blocking if active(features, name)]
    required_ratio = len(matched_required) / len(required) if required else 0.0
    blocking_ratio = len(matched_blocking) / len(blocking) if blocking else 0.0
    explicit_match = str(features.get("cve") or "").upper() == str(candidate["cve"]).upper()
    kev = feature_or_enrichment_bool(features, enrichment, "in_cisa_kev", "kev")
    epss = feature_or_enrichment_number(features, enrichment, "epss_score", "epss")
    cvss = feature_or_enrichment_number(features, enrichment, "cvss_base_score", "cvss")
    modules = list(candidate.get("modules") or [])
    safe_check = bool(candidate.get("safe_check_th"))

    raw_score = (
        weights["required_feature_ratio"] * required_ratio
        + weights["no_blocking_feature"] * (1.0 - blocking_ratio)
        + weights["explicit_cve_match"] * (1.0 if explicit_match else 0.0)
        + weights["kev"] * (1.0 if kev else 0.0)
        + weights["epss"] * max(0.0, min(epss, 1.0))
        + weights["cvss"] * max(0.0, min(cvss / 10.0, 1.0))
        + weights["module_available"] * (1.0 if modules else 0.0)
        + weights["safe_check_available"] * (1.0 if safe_check else 0.0)
        - 0.4 * blocking_ratio
    )
    score = max(0.0, min(raw_score, 1.0))
    reasons: list[str] = []
    if matched_required:
        reasons.append("required features matched: " + ", ".join(matched_required))
    if matched_blocking:
        reasons.append("blocking features present: " + ", ".join(matched_blocking))
    if explicit_match:
        reasons.append("target CVE matches candidate")
    if kev:
        reasons.append("CVE is marked in KEV/enrichment")
    if epss:
        reasons.append(f"EPSS signal: {epss:.4f}")
    if cvss:
        reasons.append(f"CVSS signal: {cvss:.1f}")
    if modules:
        reasons.append("module mapping available")
    if safe_check:
        reasons.append("safe check guidance available")

    if score >= 0.75 and not matched_blocking:
        recommendation = "safe_check_candidate"
    elif score >= 0.45:
        recommendation = "manual_triage_candidate"
    else:
        recommendation = "low_priority_or_more_evidence"

    return {
        "cve": candidate["cve"],
        "title": candidate.get("title", ""),
        "score": round(score, 4),
        "required_feature_ratio": round(required_ratio, 4),
        "matched_required_features": matched_required,
        "missing_required_features": [name for name in required if name not in matched_required],
        "matched_blocking_features": matched_blocking,
        "in_cisa_kev": kev,
        "epss_score": round(epss, 4) if epss else 0,
        "cvss_base_score": round(cvss, 1) if cvss else 0,
        "modules": modules,
        "safe_check_th": candidate.get("safe_check_th", ""),
        "risk": candidate.get("risk", "unknown"),
        "recommendation": recommendation,
        "reasons": reasons,
    }


def rank_cves_for_family(
    family: str,
    features: dict[str, Any],
    rules: dict[str, Any],
    enrichment_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    families = rules.get("families", {})
    candidates = list(families.get(family, []))
    enrichments = enrichment_index(enrichment_rows or [])
    weights = {key: float(value) for key, value in rules["score_weights"].items()}
    ranked = [
        score_candidate(candidate, features, enrichments.get(str(candidate["cve"]).upper(), {}), weights)
        for candidate in candidates
    ]
    ranked.sort(key=lambda row: (float(row["score"]), row["cve"]), reverse=True)
    return {
        "model": "rule_cve_ranker_v01",
        "family": family,
        "candidate_count": len(ranked),
        "top_cves": ranked,
        "safety_note_th": "Resolver แนะนำ candidate เท่านั้น ห้าม execute exploit อัตโนมัติ ต้องเริ่มจาก safe check/manual triage",
    }


def infer_family_from_prediction(prediction: dict[str, Any]) -> str | None:
    ranker = prediction.get("ranker")
    if not isinstance(ranker, dict):
        return None
    if ranker.get("decision") == "unknown_family":
        return None
    families = ranker.get("top_families")
    if not isinstance(families, list) or not families:
        return None
    top = families[0]
    if not isinstance(top, dict) or top.get("family") is None:
        return None
    return str(top["family"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True, type=Path)
    parser.add_argument("--prediction", type=Path)
    parser.add_argument("--family")
    parser.add_argument("--rules", default=DEFAULT_RULES, type=Path)
    parser.add_argument("--enrichment-jsonl", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    features = read_json(args.features)
    prediction = read_json(args.prediction) if args.prediction else {}
    family = args.family or infer_family_from_prediction(prediction)
    if not family:
        result = {
            "model": "rule_cve_ranker_v01",
            "family": None,
            "candidate_count": 0,
            "top_cves": [],
            "safety_note_th": "ไม่มี known family ที่พร้อม resolver จึงไม่จัดอันดับ CVE",
        }
    else:
        result = rank_cves_for_family(
            family,
            features,
            read_json(args.rules),
            read_jsonl(args.enrichment_jsonl),
        )
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
