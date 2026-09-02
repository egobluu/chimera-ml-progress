# Chimera Overnight Lab Scan Skill

ใช้ skill นี้เมื่อมีเครื่อง Kali/OpenCode ใหม่ที่ต้องเก็บ lab scan dataset จำนวนมากสำหรับ Chimera ML

## Goal

สร้างข้อมูลแบบนี้ให้ได้ต่อเนื่อง:

```text
lab target -> scanner evidence -> feature JSON -> validation label -> CVE enrichment
```

โดยใช้เฉพาะ lab/local/authorized targets และ enrich ด้วย:

```text
CISA KEV
EPSS
NVD
```

## Safety Scope

ทำได้:

```text
Vulhub
local Docker lab
authorized internal lab
negative/control containers ที่เราคุมเอง
```

ห้าม:

```text
public internet random scan
unauthorized exploit
post-exploit shell collection นอก lab
เอา postcheck result เป็น precheck feature
```

## Setup

```bash
sudo apt update
sudo apt install -y \
  git curl wget jq unzip gzip ca-certificates \
  python3 python3-venv python3-pip pipx \
  docker.io docker-compose-plugin \
  nmap whatweb ffuf nikto metasploit-framework golang-go

sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
export PATH="$PATH:$HOME/go/bin"
nuclei -update
nuclei -update-templates
```

Python:

```bash
mkdir -p ~/chimera-nightly
cd ~/chimera-nightly
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install requests pandas pyyaml tqdm python-dateutil
```

Vulhub:

```bash
cd ~/chimera-nightly
git clone https://github.com/vulhub/vulhub.git
```

## Output Contract

เขียนไปที่:

```text
/media/sf_kali-share/dataset/dec-overnight-lab-scan-enrichment-YYYY-MM-DD
```

ต้องมี:

```text
features.jsonl
targets.jsonl
validation-results.jsonl
cve-enrichment.jsonl
safe-to-merge-targets.txt
quarantined-targets.txt
OVERNIGHT-LAB-SCAN-ENRICHMENT-TH.md
raw/<target_id>/*
```

## Per-target Routine

```text
1. เลือก Vulhub/local lab target
2. start ด้วย docker compose
3. รอ service พร้อม
4. เก็บ port/http/fingerprint evidence
5. run nuclei/httpx/nmap/whatweb/curl
6. run family-specific precheck probes
7. extract CVE
8. enrich CVE จาก CISA KEV + EPSS + NVD
9. เขียน features.jsonl
10. เขียน targets.jsonl
11. เขียน validation-results.jsonl
12. เขียน raw evidence
13. docker compose down -v
14. ไป target ถัดไป
```

## Enrichment Sources

CISA KEV:

```bash
curl -L "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json" -o enrichment/cisa-kev.json
```

EPSS:

```bash
curl -L "https://api.first.org/data/v1/epss?cve=CVE-2021-41773&pretty=true"
```

NVD:

```bash
curl -L "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2021-41773"
```

## Feature Rules

ใช้ precheck feature เท่านั้น:

```text
version_in_vulnerable_range
auth_required
no_auth_required
endpoint_reachable_count
method_put_allowed
ajp_port_open
velocity_enabled
admin_party_enabled
lua_available
known_family_signal_count
unknown_family_signal_count
```

ห้ามใช้เป็น feature:

```text
tool_metasploit_success
msf_check_confirmed
msf_check_not_vulnerable
rce_confirmed
manual_poc_failed
shell_obtained
flag_found
```

## Target Categories

```text
positive = lab ยืนยันว่า vulnerable
negative = lab/control ยืนยันว่าไม่ vulnerable
weak = มี signal บาง แต่ evidence ยังไม่พอ
unknown_family = vulnerable หรือ suspicious แต่ไม่อยู่ใน runtime candidate families
```

## Quarantine

quarantine ถ้า:

```text
container fail
port หาย
label/evidence ขัดกัน
feature สำคัญขาด
CVE metadata จำเป็นแต่ดึงไม่ได้
positive ไม่มี positive precondition เลย
negative มี exploit-specific positive signal แรงมาก
```

## Report

ท้าย batch ต้องสรุป:

```text
targets ทั้งหมด
safe_to_merge
quarantined
positive/negative/weak/unknown
families ที่ได้
CVE ที่เจอ
จำนวน in_cisa_kev
EPSS range
CVSS range
failure ราย target
```

