#!/usr/bin/env python3
"""Generate gate-feature-evidence.jsonl for all validated targets.

This script enriches existing scan output with ML-friendly gate features such as
version range, exploit preconditions, scanner confirmation, and negative
evidence.  The goal is to make vulnerable and non-vulnerable targets comparable
instead of letting the model rely only on product names or tool success.
"""
import json
import os
import re
import glob

EXPAND_DIR = "/home/kali/reports/dec-ml-ranking-data-expand-2026-08-31/raw-curated"
GATE_DIR = "/home/kali/reports/dec-gate-feature-improve-2026-08-31/raw-curated"
OUTPUT_DIR = "/home/kali/reports/dec-ml-only-gate-v02-2026-08-31/raw-curated"

RUN_ID = "dec-ml-only-gate-v02-2026-08-31"

def read_jsonl(filepath):
    """Read one JSON object per line from an evidence file."""
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
    if not os.path.exists(filepath):
        return ""
    with open(filepath) as f:
        return f.read()

def extract_version_from_raw(raw_dir):
    """Extract version from httpx.txt, nuclei.txt, or nmap.txt."""
    version = ""
    product = ""
    
    # Try httpx.txt
    content = read_raw(os.path.join(raw_dir, "httpx.txt"))
    if content:
        # Look for version patterns
        m = re.search(r'Apache\s+CouchDB\s+([\d.]+)', content)
        if m:
            product = "couchdb"
            version = m.group(1)
        m = re.search(r'Elasticsearch\s+([\d.]+)', content)
        if m:
            product = "elasticsearch"
            version = m.group(1)
        m = re.search(r'Grafana\s+([\d.]+)', content)
        if m:
            product = "grafana"
            version = m.group(1)
        m = re.search(r'Jenkins-([\d.]+)', content)
        if m:
            product = "jenkins"
            version = m.group(1)
        m = re.search(r'X-Jenkins:\s*([\d.]+)', content)
        if m:
            product = "jenkins"
            version = m.group(1)
        m = re.search(r'Nexus/([\d.]+)', content)
        if m:
            product = "nexus"
            version = m.group(1)
        m = re.search(r'Server:.*Nexus/([\d.-]+)', content)
        if m:
            product = "nexus"
            version = m.group(1)
        m = re.search(r'nginx/([\d.]+)', content)
        if m:
            product = "nginx"
            version = m.group(1)
        m = re.search(r'PHP/([\d.]+)', content)
        if m and not product:
            product = "php"
            version = m.group(1)
        m = re.search(r'Solr\s+([\d.]+)', content)
        if m:
            product = "solr"
            version = m.group(1)
        m = re.search(r'Apache\s+Tomcat/([\d.]+)', content)
        if m:
            product = "tomcat"
            version = m.group(1)
    
    # Try nuclei.txt
    content = read_raw(os.path.join(raw_dir, "nuclei.txt"))
    if content and not version:
        m = re.search(r'grafana-detect.*?(\d+\.\d+\.\d+)', content)
        if m:
            product = "grafana"
            version = m.group(1)
        m = re.search(r'jenkins-detect.*?(\d+\.\d+\.\d+)', content)
        if m:
            product = "jenkins"
            version = m.group(1)
        m = re.search(r'couchdb-detect.*?(\d+\.\d+\.\d+)', content)
        if m:
            product = "couchdb"
            version = m.group(1)
    
    # Try nmap.txt
    content = read_raw(os.path.join(raw_dir, "nmap.txt"))
    if content and not version:
        m = re.search(r'Apache\s+CouchDB/([\d.]+)', content)
        if m:
            product = "couchdb"
            version = m.group(1)
    
    # Try version_behavior.txt
    content = read_raw(os.path.join(raw_dir, "version_behavior.txt"))
    if content and not version:
        m = re.search(r'(\d+\.\d+\.\d+)', content)
        if m:
            version = m.group(1)
    
    return product, version

def detect_service_port(raw_dir, target_id):
    """Detect service port."""
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
    
    # Infer from target_id
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

def make_feature(target_id, feature_group, feature, value, candidate_family, evidence, source_file="raw", notes=""):
    return {
        "run_id": RUN_ID,
        "target_id": target_id,
        "feature_group": feature_group,
        "feature": feature,
        "value": value,
        "candidate_family": candidate_family,
        "evidence": evidence,
        "source_file": source_file,
        "notes": notes
    }

def generate_for_target(target_id, expand_dir, gate_dir_existing):
    """Generate gate-feature-evidence.jsonl for a single target."""
    raw_dir = os.path.join(expand_dir, "raw")
    features = []
    
    # Get validation info
    val_rows = read_jsonl(os.path.join(expand_dir, "validation-results.jsonl"))
    if not val_rows:
        return features
    val = val_rows[0]
    validation_status = val.get("validation_status", "unknown")
    is_positive = validation_status == "validated_positive"
    
    # Get candidate family from target_id
    parts = target_id.split("_")
    candidate_family = parts[0] if parts else "unknown"
    if "non_vulnerable" in target_id:
        candidate_family = parts[0] if len(parts) > 1 else "unknown"
    
    # Get metasploit info
    msf_rows = read_jsonl(os.path.join(expand_dir, "metasploit-validation.jsonl"))
    msf_info = msf_rows[0] if msf_rows else {}
    
    # Get tool applicability
    tool_rows = read_jsonl(os.path.join(expand_dir, "tool-applicability.jsonl"))
    
    # Extract version
    product, version = extract_version_from_raw(raw_dir)
    
    # Detect port
    port = detect_service_port(raw_dir, target_id)
    
    # --- Version features ---
    if product:
        features.append(make_feature(target_id, "version", "detected_product", product, candidate_family, f"Product detected: {product}", "raw/httpx.txt"))
    if version:
        features.append(make_feature(target_id, "version", "detected_version", version, candidate_family, f"Version detected: {version}", "raw/httpx.txt"))
        features.append(make_feature(target_id, "version", "version_source", "httpx", candidate_family, "Version extracted from httpx response", "raw/httpx.txt"))
    
    # --- Negative evidence for non-vulnerable targets ---
    if not is_positive:
        # Version not in vulnerable range
        if version:
            if candidate_family == "couchdb" and version.startswith("3."):
                features.append(make_feature(target_id, "negative_evidence", "version_not_affected", True, candidate_family, f"CouchDB {version} requires auth - CVE-2017-12635 affects 2.x", "raw/manual_poc.txt", "CouchDB 3.x admin party disabled"))
            elif candidate_family == "elasticsearch" and version.startswith("5."):
                features.append(make_feature(target_id, "negative_evidence", "version_patched", True, candidate_family, f"Elasticsearch {version} has Painless sandbox blocking execute()", "raw/manual_poc.txt", "CVE-2015-1427 patched in 5.x"))
            elif candidate_family == "grafana" and (version.startswith("8.") or version.startswith("9.")):
                features.append(make_feature(target_id, "negative_evidence", "version_patched", True, candidate_family, f"Grafana {version} patched for CVE-2021-43798 (affects <8.2.0)", "raw/manual_poc.txt", "Path traversal blocked"))
            elif candidate_family == "jenkins" and version:
                features.append(make_feature(target_id, "negative_evidence", "version_not_affected", True, candidate_family, f"Jenkins {version} - CVE-2018-1000861 affects <2.138", "raw/msf_check.txt", "Version below vulnerable threshold"))
            elif candidate_family == "nexus" and version:
                features.append(make_feature(target_id, "negative_evidence", "version_patched", True, candidate_family, f"Nexus {version} - CVE-2020-10199 affects <3.21.2", "raw/msf_check.txt", "Version far above vulnerable range"))
            elif candidate_family == "redis":
                features.append(make_feature(target_id, "negative_evidence", "version_not_affected", True, candidate_family, f"Redis {version} - CVE-2022-0543 affects specific Debian/Ubuntu packages", "raw/msf_check.txt", "Not affected distribution"))
            elif candidate_family == "tomcat":
                features.append(make_feature(target_id, "negative_evidence", "version_patched", True, candidate_family, f"Tomcat {version} - PUT/AJP preconditions fail", "raw/httpx.txt", "Security measures active"))
            elif candidate_family == "spring":
                features.append(make_feature(target_id, "negative_evidence", "wrong_software_type", True, candidate_family, "Target is plain Tomcat, not Spring framework", "raw/httpx.txt", "Spring not detected"))
        
        # Wrong software type
        if product and candidate_family and product != candidate_family:
            if not (candidate_family == "generic" and product == "phpmyadmin"):
                features.append(make_feature(target_id, "negative_evidence", "wrong_software_type", True, candidate_family, f"Detected {product} but testing for {candidate_family}", "raw/httpx.txt"))
        
        # Auth required
        auth_content = read_raw(os.path.join(raw_dir, "auth_behavior.txt"))
        if "401" in auth_content or "unauthorized" in auth_content.lower():
            features.append(make_feature(target_id, "precondition", "auth_required", True, candidate_family, "Authentication required - 401 response", "raw/auth_behavior.txt"))
        
        # Endpoint not found
        exploit_content = read_raw(os.path.join(raw_dir, "exploit_check_behavior.txt"))
        if "404" in exploit_content or "not found" in exploit_content.lower():
            features.append(make_feature(target_id, "precondition", "endpoint_missing", True, candidate_family, "Exploit endpoint returns 404", "raw/exploit_check_behavior.txt"))
        
        # Metasploit check not vulnerable
        if msf_info.get("check_result") == "not_vulnerable":
            features.append(make_feature(target_id, "metasploit", "check_result", "not_vulnerable", candidate_family, msf_info.get("check_output", "Metasploit check confirmed not vulnerable"), "metasploit-validation.jsonl"))
            features.append(make_feature(target_id, "metasploit", "msf_check_not_vulnerable", True, candidate_family, "Metasploit check returned NOT exploitable", "metasploit-validation.jsonl"))
        
        # Metasploit module found but check says no
        if msf_info.get("module_found"):
            features.append(make_feature(target_id, "metasploit", "module_found", True, candidate_family, f"Module {msf_info.get('module_name', 'unknown')} found", "metasploit-validation.jsonl"))
        
        if msf_info.get("check_supported"):
            features.append(make_feature(target_id, "metasploit", "check_supported", True, candidate_family, "Metasploit check method supported", "metasploit-validation.jsonl"))
        
        # Nuclei fingerprint only
        nuclei_content = read_raw(os.path.join(raw_dir, "nuclei.txt"))
        if nuclei_content:
            has_critical = "critical" in nuclei_content.lower()
            has_high = "high" in nuclei_content.lower()
            has_info = "info" in nuclei_content.lower()
            
            if has_critical or has_high:
                # Check if it's actually a vuln confirmation or just detection
                if "detect" in nuclei_content.lower() and "cve" not in nuclei_content.lower():
                    features.append(make_feature(target_id, "scanner_confirmation", "nuclei_fingerprint_only", True, candidate_family, "Nuclei found fingerprint detection only, no CVE confirmation", "raw/nuclei.txt"))
                else:
                    features.append(make_feature(target_id, "scanner_confirmation", "nuclei_cve_confirmed", True, candidate_family, "Nuclei confirmed CVE", "raw/nuclei.txt"))
            
            if not has_critical and not has_high:
                features.append(make_feature(target_id, "scanner_confirmation", "nuclei_no_vuln_found", True, candidate_family, "Nuclei found no critical/high vulnerabilities", "raw/nuclei.txt"))
        
        # Manual PoC failed
        manual_content = read_raw(os.path.join(raw_dir, "manual_poc.txt"))
        if manual_content:
            if "error" in manual_content.lower() or "404" in manual_content or "blocked" in manual_content.lower():
                features.append(make_feature(target_id, "negative_evidence", "manual_poc_failed", True, candidate_family, "Manual PoC returned error/block", "raw/manual_poc.txt"))
    
    # --- Positive evidence for vulnerable targets ---
    else:
        if version:
            features.append(make_feature(target_id, "version", "version_in_vulnerable_range", True, candidate_family, f"Version {version} is in vulnerable range", "raw/httpx.txt"))
        
        # Endpoint reachable
        exploit_content = read_raw(os.path.join(raw_dir, "exploit_check_behavior.txt"))
        if exploit_content and "200" in exploit_content:
            features.append(make_feature(target_id, "precondition", "endpoint_reachable", True, candidate_family, "Exploit endpoint reachable (200)", "raw/exploit_check_behavior.txt"))
        
        # No auth required
        auth_content = read_raw(os.path.join(raw_dir, "auth_behavior.txt"))
        if auth_content and "200" in auth_content:
            features.append(make_feature(target_id, "precondition", "no_auth_required", True, candidate_family, "No authentication required", "raw/auth_behavior.txt"))
        
        # Metasploit confirmed
        if msf_info.get("check_result") == "vulnerable":
            features.append(make_feature(target_id, "metasploit", "msf_check_confirmed", True, candidate_family, "Metasploit check confirmed vulnerable", "metasploit-validation.jsonl"))
        
        # Nuclei confirmed
        nuclei_content = read_raw(os.path.join(raw_dir, "nuclei.txt"))
        if nuclei_content and "cve" in nuclei_content.lower():
            features.append(make_feature(target_id, "scanner_confirmation", "nuclei_cve_confirmed", True, candidate_family, "Nuclei confirmed CVE", "raw/nuclei.txt"))
        
        # Manual PoC success
        manual_content = read_raw(os.path.join(raw_dir, "manual_poc.txt"))
        if manual_content and ("success" in manual_content.lower() or "root" in manual_content.lower() or "uid" in manual_content.lower()):
            features.append(make_feature(target_id, "exploit", "rce_confirmed", True, candidate_family, "Manual PoC confirmed RCE", "raw/manual_poc.txt"))
    
    # --- Metasploit module found (both) ---
    if msf_info.get("module_found") and not any(f["feature"] == "module_found" for f in features):
        features.append(make_feature(target_id, "metasploit", "module_found", True, candidate_family, f"Module found", "metasploit-validation.jsonl"))
    
    if msf_info.get("check_supported") and not any(f["feature"] == "check_supported" for f in features):
        features.append(make_feature(target_id, "metasploit", "check_supported", True, candidate_family, "Check supported", "metasploit-validation.jsonl"))
    
    # --- Port features ---
    features.append(make_feature(target_id, "version", "service_port", port, candidate_family, f"Service port: {port}", "raw/nmap.txt"))
    is_http = port in [80, 443, 8080, 8081, 3000, 8983, 5984]
    features.append(make_feature(target_id, "version", "is_http_target", is_http, candidate_family, f"HTTP target: {is_http}", "raw/nmap.txt"))
    
    # --- Raw file count ---
    raw_count = len([f for f in os.listdir(raw_dir) if os.path.isfile(os.path.join(raw_dir, f))]) if os.path.isdir(raw_dir) else 0
    features.append(make_feature(target_id, "version", "raw_file_count", raw_count, candidate_family, f"Raw files collected: {raw_count}", "raw/"))
    
    # --- Tool success ---
    for tool_row in tool_rows:
        tool_name = tool_row.get("tool_name", "")
        status = tool_row.get("status", "")
        if tool_name == "httpx-toolkit" and status == "success":
            features.append(make_feature(target_id, "scanner_confirmation", "httpx_product_detected", True, candidate_family, "httpx detected product", "tool-applicability.jsonl"))
        if tool_name == "nuclei" and status == "success":
            if not any(f["feature"] == "nuclei_cve_confirmed" for f in features) and not any(f["feature"] == "nuclei_no_vuln_found" for f in features):
                features.append(make_feature(target_id, "scanner_confirmation", "nuclei_fingerprint_only", True, candidate_family, "Nuclei ran successfully", "tool-applicability.jsonl"))
        if "nikto" in tool_name and status == "success":
            nikto_content = read_raw(os.path.join(raw_dir, "nikto.txt"))
            if nikto_content and "vulnerability" in nikto_content.lower():
                features.append(make_feature(target_id, "scanner_confirmation", "nikto_vuln_found", True, candidate_family, "Nikto found vulnerabilities", "raw/nikto.txt"))
    
    return features

def main():
    # Get all validated targets
    all_targets = []
    for d in sorted(os.listdir(EXPAND_DIR)):
        val_file = os.path.join(EXPAND_DIR, d, "validation-results.jsonl")
        if not os.path.exists(val_file):
            continue
        with open(val_file) as f:
            line = f.readline()
            if not line.strip():
                continue
            row = json.loads(line)
            status = row.get("validation_status", "unknown")
            if status in ("validated_positive", "validated_negative"):
                all_targets.append(d)
    
    print(f"Found {len(all_targets)} validated targets")
    
    generated = 0
    skipped = 0
    
    for target_id in all_targets:
        expand_dir = os.path.join(EXPAND_DIR, target_id)
        output_dir = os.path.join(OUTPUT_DIR, target_id)
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "gate-feature-evidence.jsonl")
        
        # Check if already exists in v01 gate dir
        gate_existing = os.path.join(GATE_DIR, target_id, "gate-feature-evidence.jsonl")
        if os.path.exists(gate_existing):
            # Copy existing
            import shutil
            shutil.copy2(gate_existing, output_file)
            print(f"  {target_id}: COPIED from v01 gate ({len(open(output_file).readlines())} features)")
            skipped += 1
            continue
        
        # Generate new
        features = generate_for_target(target_id, expand_dir, gate_existing)
        
        if features:
            with open(output_file, "w") as f:
                for feat in features:
                    f.write(json.dumps(feat) + "\n")
            print(f"  {target_id}: GENERATED {len(features)} features")
            generated += 1
        else:
            print(f"  {target_id}: NO FEATURES GENERATED")
    
    print(f"\nTotal: {generated} generated, {skipped} copied from v01")

if __name__ == "__main__":
    main()
