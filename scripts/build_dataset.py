#!/usr/bin/env python3
"""Build target-level exploitability dataset v0.2 with enhanced features.

Input:
    - expanded scan JSONL/raw evidence
    - completed gate-feature-evidence.jsonl from v0.2

Output:
    - target-exploitability-dataset.csv

The script converts per-target evidence into one row per target.  It keeps the
model decision problem focused on exploitability: label 1 means the target is a
validated positive, label 0 means it is a validated negative.  Inconclusive
targets are intentionally skipped so uncertain evidence does not pollute train
labels.
"""
import json
import os
import glob
import csv
import re

EXPAND_DIR = "/home/kali/reports/dec-ml-ranking-data-expand-2026-08-31/raw-curated"
GATE_V02_DIR = "/home/kali/reports/dec-ml-only-gate-v02-2026-08-31/raw-curated"
OUTPUT_CSV = "/home/kali/reports/dec-ml-only-gate-v02-2026-08-31/target-exploitability-dataset.csv"

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

def read_jsonl(filepath):
    """Read JSONL evidence and ignore malformed lines instead of failing a run."""
    if not os.path.exists(filepath):
        return []
    rows = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except:
                    pass
    return rows

def read_raw(filepath):
    """Read a raw scanner/probe file; missing files simply become empty text."""
    if not os.path.exists(filepath):
        return ""
    with open(filepath) as f:
        return f.read()

def count_raw_files(target_dir):
    raw_dir = os.path.join(target_dir, "raw")
    if not os.path.isdir(raw_dir):
        return 0
    return len([f for f in os.listdir(raw_dir) if os.path.isfile(os.path.join(raw_dir, f))])

def detect_service_port(target_id, raw_dir):
    content = read_raw(os.path.join(raw_dir, "nmap.txt"))
    content += read_raw(os.path.join(raw_dir, "naabu.txt"))
    
    if "5984" in content: return 5984
    if "6379" in content: return 6379
    if "8081" in content: return 8081
    if "8080" in content: return 8080
    if "3000" in content: return 3000
    if "9200" in content: return 9200
    if "6800" in content: return 6800
    if "8009" in content: return 8009
    
    if "redis" in target_id: return 6379
    if "couchdb" in target_id: return 5984
    if "nexus" in target_id: return 8081
    if "jenkins" in target_id: return 8080
    if "grafana" in target_id: return 3000
    if "tomcat" in target_id: return 8080
    if "elasticsearch" in target_id: return 9200
    if "solr" in target_id: return 8983
    if "aria2" in target_id: return 6800
    if "nginx" in target_id: return 80
    if "shiro" in target_id: return 8080
    if "thinkphp" in target_id: return 80
    if "struts2" in target_id: return 8080
    if "flask" in target_id: return 5000
    if "phpmyadmin" in target_id: return 8080
    
    return 0

def extract_features(target_id, target_dir):
    features = {f: 0 for f in FEATURES}
    
    raw_dir = os.path.join(target_dir, "raw")
    
    # raw_file_count
    features["raw_file_count"] = count_raw_files(target_dir)
    
    # Service port
    port = detect_service_port(target_id, raw_dir)
    features["service_port"] = port
    features["is_http_target"] = 1 if port in [80, 443, 8080, 8081, 3000, 8983, 5984] else 0
    features["is_non_http_service"] = 1 if port in [6379, 3306, 5432, 6800] else 0
    
    # Tool applicability
    tool_file = os.path.join(target_dir, "tool-applicability.jsonl")
    if not os.path.exists(tool_file):
        tool_file = os.path.join(os.path.dirname(target_dir), target_id, "tool-applicability.jsonl")
    for row in read_jsonl(tool_file):
        tool = row.get("tool_name", "")
        if tool == "httpx-toolkit" and row.get("status") == "success":
            features["tool_httpx_success"] = 1
        if tool == "nuclei" and row.get("status") == "success":
            features["tool_nuclei_success"] = 1
        if "metasploit" in tool and row.get("status") == "success":
            features["tool_metasploit_success"] = 1
    
    # Metasploit validation
    msf_file = os.path.join(target_dir, "metasploit-validation.jsonl")
    if not os.path.exists(msf_file):
        msf_file = os.path.join(os.path.dirname(target_dir), target_id, "metasploit-validation.jsonl")
    for row in read_jsonl(msf_file):
        if row.get("module_found"):
            features["metasploit_module_found"] = 1
        if row.get("check_result") == "vulnerable":
            features["msf_check_confirmed"] = 1
        if row.get("check_result") == "not_vulnerable":
            features["msf_check_not_vulnerable"] = 1
        if not row.get("module_found"):
            features["no_msf_module"] = 1
    
    # Gate feature evidence
    gate_file = os.path.join(target_dir, "gate-feature-evidence.jsonl")
    for row in read_jsonl(gate_file):
        fg = row.get("feature_group", "")
        feat = row.get("feature", "")
        val = row.get("value", False)
        
        # Version features
        if feat == "version_in_vulnerable_range" and val:
            features["version_in_vulnerable_range_true"] = 1
        elif feat == "version_in_vulnerable_range" and not val:
            features["version_in_vulnerable_range_false"] = 1
        if feat == "version_not_affected" and val:
            features["version_not_affected"] = 1
        if feat == "version_patched" and val:
            features["version_patched"] = 1
        
        # Precondition features
        if fg == "precondition":
            if val:
                features["precondition_pass_count"] += 1
            else:
                features["precondition_fail_count"] += 1
        
        # Negative evidence count
        if fg == "negative_evidence":
            features["negative_evidence_count"] += 1
        
        # Auth
        if feat == "no_auth_required" and val: features["no_auth_required"] = 1
        if feat == "auth_required" and val: features["auth_required"] = 1
        if feat == "auth_blocks_exploit" and val: features["auth_blocks_exploit"] = 1
        
        # Endpoint
        if feat == "anonymous_access" and val: features["anonymous_access"] = 1
        if feat == "endpoint_reachable" and val: features["endpoint_reachable_count"] += 1
        if feat == "endpoint_missing" and val: features["endpoint_missing_count"] += 1
        if feat == "endpoint_not_found" and val: features["endpoint_not_found"] = 1
        
        # Specific negative evidence
        if feat == "velocity_enabled" and val: features["velocity_enabled"] = 1
        if feat == "invokefunction_reachable" and val: features["invokefunction_reachable"] = 1
        if feat == "invokefunction_not_found" and val: features["invokefunction_not_found"] = 1
        if feat == "admin_party_enabled" and val: features["admin_party_enabled"] = 1
        if feat == "ajp_port_open" and val: features["ajp_port_open"] = 1
        if feat == "ajp_port_closed" and val: features["ajp_port_closed"] = 1
        if feat == "spring_detected" and val: features["spring_detected"] = 1
        if feat == "spring_not_detected" and val: features["spring_not_detected"] = 1
        if feat == "wrong_software_type" and val: features["wrong_software_type"] = 1
        if feat == "wrong_version" and val: features["wrong_version"] = 1
        if feat == "method_put_rejected" and val: features["method_put_rejected"] = 1
        if feat == "method_put_allowed" and val: features["method_put_allowed"] = 1
        
        # Exploit confirmation
        if feat == "rce_confirmed" and val: features["rce_confirmed"] = 1
        
        # Scanner features
        if feat == "nuclei_cve_confirmed" and val: features["nuclei_cve_confirmed"] = 1
        if feat == "nuclei_fingerprint_only" and val: features["nuclei_fingerprint_only"] = 1
        if feat == "nuclei_no_vuln_found" and val: features["nuclei_no_vuln_found"] = 1
        if feat == "manual_poc_failed" and val: features["manual_poc_failed"] = 1
        
        # Metasploit
        if feat == "msf_check_confirmed" and val: features["msf_check_confirmed"] = 1
        if feat == "msf_check_not_vulnerable" and val: features["msf_check_not_vulnerable"] = 1
        
        # Specific vuln mechanisms
        if feat == "painless_sandbox_blocks" and val: features["painless_sandbox_blocks"] = 1
        if feat == "path_traversal_blocked" and val: features["path_traversal_blocked"] = 1
    
    # Check raw files for additional signals
    if os.path.isdir(raw_dir):
        # Check for PUT method
        for fname in os.listdir(raw_dir):
            fpath = os.path.join(raw_dir, fname)
            if os.path.isfile(fpath):
                content = read_raw(fpath)
                if "http_method" in fname or "exploit_check" in fname:
                    if "PUT" in content and "405" in content:
                        features["method_put_rejected"] = 1
                    if "PUT" in content and "200" in content:
                        features["method_put_allowed"] = 1
        
        # Check nuclei output
        nuclei_content = read_raw(os.path.join(raw_dir, "nuclei.txt"))
        if nuclei_content:
            if "critical" in nuclei_content.lower() or "high" in nuclei_content.lower():
                if "cve" in nuclei_content.lower():
                    features["nuclei_cve_confirmed"] = 1
                else:
                    features["nuclei_fingerprint_only"] = 1
            elif not nuclei_content.strip():
                features["nuclei_no_vuln_found"] = 1
    
    return features

def get_label(validation_status):
    if validation_status == "validated_positive":
        return 1
    elif validation_status == "validated_negative":
        return 0
    return None

def main():
    rows = []
    
    # Process all targets from expand run
    for target_dir in sorted(glob.glob(os.path.join(EXPAND_DIR, "*"))):
        target_id = os.path.basename(target_dir)
        
        # Get label
        val_file = os.path.join(target_dir, "validation-results.jsonl")
        val_rows = read_jsonl(val_file)
        if not val_rows:
            continue
        
        validation_status = val_rows[0].get("validation_status", "unknown")
        label = get_label(validation_status)
        if label is None:
            continue
        
        # Use v02 gate dir features
        gate_dir = os.path.join(GATE_V02_DIR, target_id)
        if os.path.isdir(gate_dir):
            features = extract_features(target_id, gate_dir)
        else:
            features = extract_features(target_id, target_dir)
        
        row = {"target_id": target_id, "label": label}
        row.update(features)
        rows.append(row)
    
    # Write CSV
    fieldnames = ["target_id", "label"] + FEATURES
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(rows, key=lambda x: x["target_id"]):
            writer.writerow(row)
    
    print(f"Dataset written to {OUTPUT_CSV}")
    print(f"Total targets: {len(rows)}")
    print(f"Positive (exploit): {sum(1 for r in rows if r['label'] == 1)}")
    print(f"Negative (no_exploit): {sum(1 for r in rows if r['label'] == 0)}")
    print(f"Features: {len(FEATURES)}")
    
    # Show feature summary
    print("\n=== Feature Summary ===")
    for feat in FEATURES:
        vals = [r[feat] for r in rows]
        non_zero = sum(1 for v in vals if v > 0)
        if non_zero > 0:
            print(f"  {feat}: {non_zero}/{len(rows)} targets have non-zero")

if __name__ == "__main__":
    main()
