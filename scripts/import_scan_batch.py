#!/usr/bin/env python3
"""Import a scanner batch into a runtime-evaluation-ready report folder.

The scanner box can produce slightly different top-level names per batch. This
script copies only safe top-level files, normalizes JSON streams to JSONL, maps
source family labels to runtime families, joins CVE enrichment as metadata, and
writes a small audit summary before runtime evaluation.
"""
from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_FILE_CANDIDATES = (
    "targets.jsonl",
    "unseen-multifamily-targets.jsonl",
    "unknown-multifamily-targets.jsonl",
)
FEATURE_FILE_CANDIDATES = (
    "features.jsonl",
    "unseen-multifamily-features.jsonl",
    "unknown-multifamily-features.jsonl",
)
VALIDATION_FILE_CANDIDATES = ("validation-results.jsonl",)
ENRICHMENT_FILE_CANDIDATES = ("cve-enrichment.jsonl",)

TOP_LEVEL_COPY_NAMES = set(
    TARGET_FILE_CANDIDATES
    + FEATURE_FILE_CANDIDATES
    + VALIDATION_FILE_CANDIDATES
    + ENRICHMENT_FILE_CANDIDATES
    + (
        "safe-to-merge-targets.txt",
        "quarantined-targets.txt",
    )
)

FAMILY_ALIASES = {
    "redis_lua": "redis",
    "grafana_path_traversal": "grafana",
    "couchdb": "couchdb_auth",
    "couchdb_rce": "couchdb_auth",
    "solr_velocity_rce": "solr_velocity",
    "shiro_deserialize": "shiro_key",
    "shiro_rce": "shiro_key",
    "thinkphp": "thinkphp_rce",
    "thinkphp_rce": "thinkphp_rce",
    "jenkins_rce": "jenkins",
    "elasticsearch_rce": "elasticsearch",
    "tomcat_put": "tomcat_put",
    "tomcat_ajp": "tomcat_ajp",
}

SAFE_STATUS = {
    "validated_positive",
    "validated_negative",
    "no_exploit",
    "weak_no_exploit",
}

NEGATIVE_STATUS = {
    "validated_negative",
    "no_exploit",
    "weak_no_exploit",
}

POSTCHECK_OR_LABEL_ONLY_FIELDS = {
    "tool_metasploit_success",
    "msf_check_confirmed",
    "msf_check_not_vulnerable",
    "rce_confirmed",
    "manual_poc_failed",
    "shell_obtained",
    "flag_found",
}

CVSS_SEVERITIES = {
    "LOW": "cvss_base_severity_low",
    "MEDIUM": "cvss_base_severity_medium",
    "HIGH": "cvss_base_severity_high",
    "CRITICAL": "cvss_base_severity_critical",
}


def read_json_stream(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    rows: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        value, next_index = decoder.raw_decode(text, index)
        if not isinstance(value, dict):
            raise ValueError(f"{path} contains a non-object JSON value")
        rows.append(value)
        index = next_index
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def find_first(folder: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = folder / name
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def load_candidate_families(model_dir: Path) -> set[str]:
    manifest = json.loads((model_dir / "prototype_manifest.json").read_text(encoding="utf-8"))
    return set(str(family) for family in manifest["ranker"]["families"])


def normalize_family(source_family: str) -> str:
    return FAMILY_ALIASES.get(source_family, source_family)


def runtime_category(row: dict[str, Any], candidate_families: set[str]) -> str:
    category = str(row.get("category") or "")
    source_family = str(row.get("expected_family") or "unknown")
    status = str(row.get("expected_status") or row.get("validation_status") or "")
    normalized = normalize_family(source_family)

    if category in {"negative", "weak"} or status in NEGATIVE_STATUS or source_family == "none":
        return "negative_control"
    if category == "unknown_family":
        return "unknown_family"
    if category == "positive" or status == "validated_positive":
        return "known_positive" if normalized in candidate_families else "unknown_family"
    return "unknown_family"


def runtime_family(row: dict[str, Any], candidate_families: set[str]) -> str:
    source_family = str(row.get("expected_family") or "unknown")
    normalized = normalize_family(source_family)
    if normalized in candidate_families:
        return normalized
    return "unknown"


def enrichment_by_cve(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        cve = str(row.get("cve") or row.get("cve_id") or "").upper()
        if cve:
            output[cve] = row
    return output


def normalize_enrichment_features(enrichment: dict[str, Any]) -> dict[str, Any]:
    features: dict[str, Any] = {}
    if not enrichment:
        return features

    if "in_cisa_kev" in enrichment:
        features["in_cisa_kev"] = 1 if bool(enrichment["in_cisa_kev"]) else 0
    if "epss_score" in enrichment:
        features["epss_score"] = enrichment["epss_score"]
    if "epss_percentile" in enrichment:
        features["epss_percentile"] = enrichment["epss_percentile"]
    if "cvss_base_score" in enrichment:
        features["cvss_base_score"] = enrichment["cvss_base_score"]

    severity = str(enrichment.get("cvss_base_severity") or "").upper()
    for name in CVSS_SEVERITIES.values():
        features[name] = 0
    if severity in CVSS_SEVERITIES:
        features[CVSS_SEVERITIES[severity]] = 1

    cwe_values = enrichment.get("cwe") or []
    if isinstance(cwe_values, str):
        cwe_values = [cwe_values]
    features["nvd_cwe_count"] = len(cwe_values) if isinstance(cwe_values, list) else 0
    return features


def import_top_level_files(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for file in src.iterdir():
        if not file.is_file():
            continue
        if file.name in TOP_LEVEL_COPY_NAMES or file.suffix.lower() in {".md", ".txt"}:
            shutil.copy2(file, dst / file.name)


def build_runtime_targets(
    targets: list[dict[str, Any]],
    candidate_families: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in targets:
        rows.append(
            {
                "target_id": row["target_id"],
                "category": runtime_category(row, candidate_families),
                "expected_family": runtime_family(row, candidate_families),
                "source_expected_family": row.get("expected_family", "unknown"),
                "source_image": row.get("source_image", row.get("source", "unknown")),
                "cve": row.get("cve", ""),
                "validation_status": row.get("expected_status", row.get("validation_status", "unknown")),
            }
        )
    return rows


def join_enrichment(
    features: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    enrichment_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target_cve = {
        str(row["target_id"]): str(row.get("cve") or "").upper()
        for row in targets
    }
    enrichment = enrichment_by_cve(enrichment_rows)
    output: list[dict[str, Any]] = []
    for row in features:
        merged = dict(row)
        cve = str(merged.get("cve") or target_cve.get(str(merged.get("target_id")), "") or "").upper()
        if cve:
            merged["cve"] = cve
            merged.update(normalize_enrichment_features(enrichment.get(cve, {})))
        output.append(merged)
    return output


def audit(
    features: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    runtime_targets: list[dict[str, Any]],
    validations: list[dict[str, Any]],
    enrichment_rows: list[dict[str, Any]],
    safe_ids: set[str],
    quarantined_ids: set[str],
    candidate_families: set[str],
) -> dict[str, Any]:
    feature_by_id = {str(row.get("target_id")): row for row in features}
    validation_by_id = {str(row.get("target_id")): row for row in validations}
    target_ids = [str(row.get("target_id")) for row in targets]
    cve_enriched = {str(row.get("cve") or row.get("cve_id") or "").upper() for row in enrichment_rows}

    issues: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target.get("target_id"))
        source_family = str(target.get("expected_family") or "unknown")
        status = str(target.get("expected_status") or target.get("validation_status") or "")
        feature = feature_by_id.get(target_id)
        validation = validation_by_id.get(target_id)
        normalized_family = normalize_family(source_family)

        if feature is None:
            issues.append({"target_id": target_id, "severity": "error", "issue": "missing_feature_row"})
            continue
        if validation is None:
            issues.append({"target_id": target_id, "severity": "warning", "issue": "missing_validation_row"})
        leaked = sorted(name for name in POSTCHECK_OR_LABEL_ONLY_FIELDS if name in feature)
        if leaked:
            issues.append(
                {
                    "target_id": target_id,
                    "severity": "error",
                    "issue": "postcheck_field_used_as_feature",
                    "fields": leaked,
                }
            )
        if status not in SAFE_STATUS:
            issues.append({"target_id": target_id, "severity": "warning", "issue": "non_standard_status", "status": status})
        if source_family != "none" and normalized_family not in candidate_families:
            issues.append(
                {
                    "target_id": target_id,
                    "severity": "info",
                    "issue": "mapped_to_unknown_family",
                    "source_expected_family": source_family,
                }
            )
        cve = str(target.get("cve") or feature.get("cve") or "").upper()
        if cve and cve not in cve_enriched:
            issues.append({"target_id": target_id, "severity": "warning", "issue": "missing_cve_enrichment", "cve": cve})

    runtime_categories = Counter(str(row["category"]) for row in runtime_targets)
    source_families = Counter(str(row.get("expected_family") or "unknown") for row in targets)
    return {
        "total_targets": len(targets),
        "feature_rows": len(features),
        "validation_rows": len(validations),
        "enrichment_rows": len(enrichment_rows),
        "safe_to_merge_count": len(safe_ids),
        "quarantined_count": len(quarantined_ids),
        "runtime_categories": dict(sorted(runtime_categories.items())),
        "source_families": dict(sorted(source_families.items())),
        "candidate_families": sorted(candidate_families),
        "issues": issues,
        "issue_counts": dict(sorted(Counter(str(issue["issue"]) for issue in issues).items())),
    }


def read_id_file(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            ids.add(stripped)
    return ids


def write_report(path: Path, summary: dict[str, Any]) -> None:
    issue_lines = "\n".join(
        f"- `{item['target_id']}`: {item['issue']} ({item['severity']})"
        for item in summary["issues"][:50]
    )
    if not issue_lines:
        issue_lines = "- ไม่พบ issue จาก import audit"
    text = f"""# Scan Batch Import Audit

## Summary

| Item | Count |
| --- | ---: |
| Total targets | {summary['total_targets']} |
| Feature rows | {summary['feature_rows']} |
| Validation rows | {summary['validation_rows']} |
| Enrichment rows | {summary['enrichment_rows']} |
| Safe-to-merge ids | {summary['safe_to_merge_count']} |
| Quarantined ids | {summary['quarantined_count']} |

## Runtime Categories

```json
{json.dumps(summary['runtime_categories'], ensure_ascii=False, indent=2)}
```

## Issue Counts

```json
{json.dumps(summary['issue_counts'], ensure_ascii=False, indent=2)}
```

## First Issues

{issue_lines}

## Next Step

ถ้าไม่มี error ให้ run `scripts/evaluate_runtime_predictions.py` โดยใช้ `features.enriched.jsonl` และ `runtime-targets.jsonl`
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--model-dir", default=Path("runtime/models/prototype"), type=Path)
    args = parser.parse_args()

    import_top_level_files(args.source_dir, args.out_dir)

    feature_path = find_first(args.out_dir, FEATURE_FILE_CANDIDATES)
    target_path = find_first(args.out_dir, TARGET_FILE_CANDIDATES)
    validation_path = find_first(args.out_dir, VALIDATION_FILE_CANDIDATES)
    enrichment_path = find_first(args.out_dir, ENRICHMENT_FILE_CANDIDATES)
    if feature_path is None or target_path is None:
        raise SystemExit("missing required feature/target files")

    features = read_json_stream(feature_path)
    targets = read_json_stream(target_path)
    validations = read_json_stream(validation_path) if validation_path else []
    enrichment_rows = read_json_stream(enrichment_path) if enrichment_path else []

    candidate_families = load_candidate_families(args.model_dir)
    enriched_features = join_enrichment(features, targets, enrichment_rows)
    runtime_targets = build_runtime_targets(targets, candidate_families)

    write_jsonl(args.out_dir / "features.jsonl", enriched_features)
    write_jsonl(args.out_dir / "features.enriched.jsonl", enriched_features)
    write_jsonl(args.out_dir / "targets.jsonl", targets)
    write_jsonl(args.out_dir / "runtime-targets.jsonl", runtime_targets)
    if validations:
        write_jsonl(args.out_dir / "validation-results.jsonl", validations)
    if enrichment_rows:
        write_jsonl(args.out_dir / "cve-enrichment.jsonl", enrichment_rows)

    summary = audit(
        enriched_features,
        targets,
        runtime_targets,
        validations,
        enrichment_rows,
        read_id_file(args.out_dir / "safe-to-merge-targets.txt"),
        read_id_file(args.out_dir / "quarantined-targets.txt"),
        candidate_families,
    )
    (args.out_dir / "import-audit.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(args.out_dir / "IMPORT-AUDIT-TH.md", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
