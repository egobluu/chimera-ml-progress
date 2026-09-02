# Prompt สำหรับ OpenCode/Kali: Overnight Lab Scan + CVE Enrichment v01

วันที่: 2026-09-02

เป้าหมาย: ใช้เครื่อง Kali/OpenCode เครื่องใหม่ที่รันได้ทั้งคืน เพื่อเก็บ target/lab scan evidence ให้เยอะขึ้นแบบวนต่อเนื่อง และ enrich ด้วย CISA KEV, EPSS, NVD ให้พร้อมใช้กับ Chimera ML runtime เร็วที่สุดภายในคืนนี้

## ข้อกำหนดสำคัญ

ทำเฉพาะ lab/local/authorized target เท่านั้น

ห้ามสแกน public internet target แบบสุ่ม ห้ามยิง exploit ใส่ระบบภายนอก ห้ามใช้ exploit เพื่อเอา shell จริงนอก lab

งานนี้ต้องผลิตข้อมูลในรูปแบบของโปรเจกต์เรา:

```text
target/lab
  -> scanner evidence
  -> feature JSON
  -> ML Gate/Ranker runtime evaluation
  -> safe verification label
  -> CVE enrichment จาก CISA KEV + EPSS + NVD
```

อย่าเอา dataset จากเน็ตมาปน train ตรง ๆ เป็น row เดียวกับ Vulhub scan ถ้ายังไม่ได้ normalize เพราะ dataset นอกส่วนใหญ่เป็น CVE metadata ไม่ใช่ scanner-derived exploitability evidence

## Output Path

เขียนผลทั้งหมดไปที่ shared folder:

```text
/media/sf_kali-share/dataset/dec-overnight-lab-scan-enrichment-2026-09-02
```

ถ้า path นี้ยังไม่มี ให้สร้าง:

```bash
mkdir -p /media/sf_kali-share/dataset/dec-overnight-lab-scan-enrichment-2026-09-02
```

โครงสร้าง output ที่ต้องมี:

```text
dec-overnight-lab-scan-enrichment-2026-09-02/
  features.jsonl
  targets.jsonl
  validation-results.jsonl
  cve-enrichment.jsonl
  safe-to-merge-targets.txt
  quarantined-targets.txt
  OVERNIGHT-LAB-SCAN-ENRICHMENT-TH.md
  raw/
    <target_id>/
      docker-compose.yml.copy.txt
      ports.txt
      httpx.jsonl
      nuclei.jsonl
      nmap.txt
      curl-root.txt
      probe-notes.json
      enrichment.json
```

ไฟล์ raw เก็บไว้ใน shared folder ได้ แต่ตอนส่งกลับ Git/ML repo ให้ copy เฉพาะ top-level files ก่อน จนกว่า Codex จะตรวจอีกที

## สิ่งที่ต้องติดตั้งบน Kali ใหม่

เริ่มจาก update:

```bash
sudo apt update
sudo apt install -y \
  git curl wget jq unzip gzip ca-certificates \
  python3 python3-venv python3-pip pipx \
  docker.io docker-compose-plugin \
  nmap whatweb ffuf nikto \
  metasploit-framework \
  golang-go
```

เปิด Docker:

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
docker version
docker compose version
```

ถ้าเพิ่งเพิ่ม user เข้า group docker แล้ว command `docker ps` ยังติด permission ให้ logout/login ใหม่ หรือใช้ `sudo docker` ชั่วคราว

ติดตั้ง ProjectDiscovery tools:

```bash
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
echo 'export PATH="$PATH:$HOME/go/bin"' >> ~/.bashrc
export PATH="$PATH:$HOME/go/bin"
nuclei -update
nuclei -update-templates
httpx -version
nuclei -version
naabu -version
```

ติดตั้ง Python workspace:

```bash
mkdir -p ~/chimera-nightly
cd ~/chimera-nightly
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install requests pandas pyyaml tqdm python-dateutil
```

clone Vulhub:

```bash
cd ~/chimera-nightly
git clone https://github.com/vulhub/vulhub.git
cd vulhub
git pull --ff-only
```

แหล่ง lab เสริมที่ใช้ได้ถ้ามีเวลา:

```text
Vulhub เป็น core source หลัก
OWASP WebGoat / Juice Shop ใช้เป็น generic negative/noisy/control ได้
local Docker images ที่เราคุมเอง ใช้ได้
public internet ห้ามใช้เป็น target scan ในรอบนี้
```

## แหล่ง enrichment ที่ต้องดึง

ใช้ 3 แหล่งหลักนี้ก่อน:

1. CISA KEV
2. EPSS
3. NVD

### CISA KEV

ดาวน์โหลด JSON:

```bash
mkdir -p ~/chimera-nightly/enrichment
curl -L \
  "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json" \
  -o ~/chimera-nightly/enrichment/cisa-kev.json
```

fallback จาก GitHub mirror:

```bash
curl -L \
  "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json" \
  -o ~/chimera-nightly/enrichment/cisa-kev.json
```

feature ที่ต้องสร้าง:

```text
in_cisa_kev = 1/0
cisa_kev_vendor_project
cisa_kev_product
cisa_kev_vulnerability_name
cisa_kev_date_added
cisa_kev_due_date
cisa_kev_known_ransomware_campaign_use
```

### EPSS

ใช้ API ของ FIRST:

```bash
curl -L "https://api.first.org/data/v1/epss?cve=CVE-2021-41773&pretty=true"
```

feature ที่ต้องสร้าง:

```text
epss_score
epss_percentile
epss_date
```

ถ้ามี CVE หลายตัว ให้ query เป็น batch เท่าที่ API รับไหว หรือวนทีละ CVE แบบ sleep กัน rate limit:

```bash
sleep 1
```

### NVD

ใช้ NVD CVE API 2.0:

```bash
curl -L "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2021-41773"
```

ถ้ามี NVD API key ให้ตั้งค่า:

```bash
export NVD_API_KEY="ใส่ key ถ้ามี"
```

แล้วเรียกแบบมี header:

```bash
curl -H "apiKey: $NVD_API_KEY" \
  "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2021-41773"
```

ถ้าไม่มี key ให้หน่วง request:

```bash
sleep 6
```

feature/metadata ที่ต้องสร้าง:

```text
cvss_base_score
cvss_base_severity
cvss_attack_vector
cvss_attack_complexity
cvss_privileges_required
cvss_user_interaction
cwe
affected_vendor
affected_product
affected_cpe_count
nvd_published
nvd_last_modified
```

## วิธีเลือก Vulhub targets สำหรับคืนนี้

ให้วนหา directory ที่มี `docker-compose.yml` และมีชื่อ CVE หรือ product ที่น่าสนใจ

priority สูง:

```text
มี CVE อยู่ใน CISA KEV
EPSS สูง
มี NVD metadata ครบ
อยู่ใน candidate families ของ runtime
เป็น product ที่เรายังมีข้อมูลน้อย
มี positive/negative/control ทำคู่กันได้
```

candidate families ที่ runtime รู้จัก:

```text
couchdb_auth
elasticsearch
flask
grafana
jenkins
joomla
nextjs
nexus
nginx
redis
shiro_key
solr_velocity
struts2
thinkphp_rce
tomcat_ajp
tomcat_put
```

unknown-family ที่อยากเพิ่ม:

```text
drupal
laravel
jetty
wordpress
php_cgi
jboss
apache_httpd
phpmyadmin
mysql
postgres
oracle_weblogic
apache_struts variants ที่ยังไม่อยู่ใน schema
```

## Naming convention

ตั้งชื่อ target แบบอ่านแล้วรู้ที่มา:

```text
<family>_<cve_or_scenario>_<positive|negative|weak|unknown>_<run_number>
```

ตัวอย่าง:

```text
apache_httpd_cve_2021_41773_positive_001
redis_lua_positive_overnight_001
grafana_path_traversal_negative_overnight_001
drupal_rce_unknown_overnight_001
solr_velocity_weak_overnight_001
```

## Scan loop หลัก

ให้ทำเป็น loop ที่หยุด/เริ่มต่อได้ ไม่พังทั้งคืนถ้า target เดียว fail

pseudocode:

```text
load queue
for each lab in queue:
  create target_id
  docker compose pull
  docker compose up -d
  wait health/ports
  discover mapped ports
  run nmap/httpx/whatweb/nuclei/curl probes
  run family-specific precheck probes
  extract CVE from folder/readme/nuclei result
  enrich CVE with CISA KEV + EPSS + NVD
  write raw evidence
  write flat feature JSON
  write target row
  write validation row
  docker compose down -v
  sleep short cooldown
continue until stopped
```

## คำสั่ง scan พื้นฐานต่อ target

หลัง `docker compose up -d` ให้ดู port:

```bash
docker compose ps
docker ps --format '{{.Names}} {{.Ports}}'
```

สร้างไฟล์ target URL เช่น:

```bash
echo "http://127.0.0.1:8080" > urls.txt
```

httpx:

```bash
httpx -l urls.txt -json -status-code -title -tech-detect -follow-redirects -o raw/<target_id>/httpx.jsonl
```

nuclei:

```bash
nuclei -l urls.txt -jsonl -severity low,medium,high,critical -o raw/<target_id>/nuclei.jsonl
```

nmap:

```bash
nmap -sV -sT -Pn -p- --min-rate 1000 127.0.0.1 -oN raw/<target_id>/nmap.txt
```

whatweb:

```bash
whatweb --log-json raw/<target_id>/whatweb.json http://127.0.0.1:8080 || true
```

curl:

```bash
curl -i -L --max-time 10 http://127.0.0.1:8080 > raw/<target_id>/curl-root.txt || true
```

## Family-specific probes ที่ต้องพยายามเก็บ

Redis:

```text
redis_detected
redis_info_accessible
lua_available
auth_required
no_auth_required
version_in_vulnerable_range
version_patched
known_family_signal_count
```

Grafana:

```text
grafana_detected
plugin_path_candidate_found
public_plugin_path_accessible
path_traversal_candidate_found
path_traversal_blocked
auth_required
version_in_vulnerable_range
```

Solr Velocity:

```text
solr_detected
solr_core_found
velocity_enabled
velocity_disabled
velocity_template_accessible
config_api_accessible
config_api_blocked
version_in_vulnerable_range
```

Tomcat PUT:

```text
method_put_allowed
method_put_rejected
jsp_upload_candidate
upload_blocked
wrong_context_path
version_in_vulnerable_range
```

Tomcat AJP:

```text
ajp_port_open
ajp_port_closed
ajp_not_exposed
version_in_vulnerable_range
```

CouchDB:

```text
couchdb_detected
admin_party_enabled
config_accessible
config_blocked
users_db_accessible
auth_required
no_auth_required
```

Unknown-family:

```text
unknown_product_detected
unknown_family_signal_count
known_family_signal_count
drupal_detected
laravel_detected
jboss_detected
jetty_detected
wordpress_detected
php_cgi_detected
```

## Feature JSON format

ทุก target ต้องเป็น flat JSON object 1 บรรทัดต่อ 1 target ใน `features.jsonl`

ตัวอย่าง:

```json
{"target_id":"redis_lua_positive_overnight_001","redis_detected":1,"redis_info_accessible":1,"lua_available":1,"auth_required":0,"no_auth_required":1,"version_in_vulnerable_range":1,"known_family_signal_count":3,"unknown_family_signal_count":0,"cve":"CVE-2022-0543","in_cisa_kev":1,"epss_score":0.95,"epss_percentile":0.99,"cvss_base_score":10.0,"cvss_base_severity":"CRITICAL"}
```

ถ้า field ไม่มี ให้ใส่ 0 หรือเว้นไว้ได้ แต่ควรใส่ 0 สำหรับ field สำคัญเพื่อแยกว่า “probe แล้วไม่พบ”

## targets.jsonl format

```json
{"target_id":"redis_lua_positive_overnight_001","category":"positive","expected_family":"redis_lua","expected_status":"validated_positive","source_image":"vulhub/redis:<tag>","cve":"CVE-2022-0543"}
{"target_id":"drupal_rce_unknown_overnight_001","category":"positive","expected_family":"drupal_rce","expected_status":"validated_positive","source_image":"vulhub/drupal:<tag>","cve":"CVE-2018-7600"}
{"target_id":"grafana_path_traversal_weak_overnight_001","category":"weak","expected_family":"none","expected_status":"no_exploit","source_image":"grafana/grafana:latest","cve":"CVE-2021-43798"}
```

หมายเหตุ: ใช้ชื่อ source label ตาม lab ได้ แต่ต้องเก็บ `cve` และ `source_image` ให้ครบ เพื่อให้ Codex normalize ต่อได้

## validation-results.jsonl format

```json
{"target_id":"redis_lua_positive_overnight_001","actual_status":"validated_positive","safe_to_merge":true,"validation_method":"lab_precheck_plus_safe_check","notes":"precheck evidence consistent; no raw shell action required"}
{"target_id":"grafana_path_traversal_weak_overnight_001","actual_status":"weak_no_exploit","safe_to_merge":true,"validation_method":"precheck_blocker","notes":"path traversal blocked; public plugin path inaccessible"}
{"target_id":"bad_case_001","actual_status":"inconclusive","safe_to_merge":false,"validation_method":"incomplete","notes":"container failed before probe completed"}
```

## cve-enrichment.jsonl format

```json
{"cve":"CVE-2021-43798","in_cisa_kev":true,"epss_score":0.944,"epss_percentile":0.997,"cvss_base_score":7.5,"cvss_base_severity":"HIGH","cwe":["CWE-22"],"affected_product":["grafana"]}
```

## Quarantine rules

ใส่ target ลง `quarantined-targets.txt` ถ้าเจอข้อใดข้อหนึ่ง:

```text
container start ไม่สำเร็จ
ไม่มี port หรือ service ให้ probe
feature สำคัญหายจนแปลไม่ได้
label กับ evidence ขัดกัน
positive แต่ไม่มี positive precondition เลย
negative แต่มี exploit-specific positive evidence แรงมาก
CVE enrichment ดึงไม่ได้และ target ต้องพึ่ง CVE นั้นในการ label
```

ใส่ target ลง `safe-to-merge-targets.txt` ถ้า:

```text
feature schema ครบพอ
label กับ evidence ไม่ขัดกัน
raw evidence เก็บครบ
category ชัดว่า positive/negative/weak/unknown
```

## ML runtime evaluation ถ้ามี repo พร้อม

ถ้ามี `chimera-ml-progress-repo` อยู่ในเครื่อง ให้ copy top-level files เข้า reports แล้ว run:

```bash
python scripts/evaluate_runtime_predictions.py \
  --features-jsonl reports/evaluations/overnight-lab-scan-enrichment-v01/features.jsonl \
  --targets-jsonl reports/evaluations/overnight-lab-scan-enrichment-v01/runtime-targets.jsonl \
  --model-dir runtime/models/prototype \
  --out-dir reports/evaluations/overnight-lab-scan-enrichment-v01/runtime-evaluation-current
```

ถ้ายังไม่มี normalizer อย่าฝืน evaluate ด้วย raw expected_family เพราะชื่อ family บางตัวไม่ตรง runtime

mapping ที่ Codex ต้องใช้ภายหลัง:

```text
redis_lua -> redis
grafana_path_traversal -> grafana
couchdb -> couchdb_auth
couchdb_rce -> couchdb_auth
solr_velocity_rce -> solr_velocity
shiro_deserialize -> shiro_key
shiro_rce -> shiro_key
thinkphp -> thinkphp_rce
thinkphp_rce -> thinkphp_rce
jenkins_rce -> jenkins
elasticsearch_rce -> elasticsearch
tomcat_put -> tomcat_put
tomcat_ajp -> tomcat_ajp
```

ถ้า normalized family ไม่อยู่ใน candidate families ให้ category เป็น `unknown_family`

## Loop รอบกลางคืน

ให้ทำงานเป็น batch ละ 10-20 targets แล้วสรุป progress ทุก batch

ตัวอย่าง loop:

```bash
while true; do
  date
  echo "[chimera] starting next batch"
  python ~/chimera-nightly/scripts/run_vulhub_batch.py \
    --vulhub-root ~/chimera-nightly/vulhub \
    --out /media/sf_kali-share/dataset/dec-overnight-lab-scan-enrichment-2026-09-02 \
    --max-targets 20 \
    --prefer-kev \
    --prefer-high-epss \
    --timeout-per-target 900
  echo "[chimera] batch done, sleeping"
  sleep 60
done
```

ถ้ายังไม่มี script ให้ทำ manual loop ได้ แต่ต้องรักษา output schema ข้างบนให้ครบ

## Report ที่ต้องเขียนท้ายรอบ

ไฟล์:

```text
OVERNIGHT-LAB-SCAN-ENRICHMENT-TH.md
```

ต้องมี:

```text
วันที่เริ่ม/จบ
เครื่องมือที่ติดตั้งและ version
จำนวน targets ทั้งหมด
จำนวน positive/negative/weak/unknown
จำนวน safe_to_merge
จำนวน quarantine
Top CVE ที่เจอ
จำนวน CVE ที่อยู่ใน CISA KEV
EPSS สูงสุด/กลาง/ต่ำสุด
NVD/CVSS summary
family ที่ได้ข้อมูลเพิ่ม
failure ราย target
ข้อเสนอว่าควรเอา target ไหนเข้า validation ก่อน
```

## Success criteria ภายในคืนนี้

ขั้นต่ำ:

```text
ติดตั้ง toolchain สำเร็จ
Vulhub run ได้
เก็บได้อย่างน้อย 30 targets
features.jsonl/targets.jsonl/validation-results.jsonl เขียนได้
ดึง CISA KEV ได้
ดึง EPSS ได้อย่างน้อยกับ CVE ที่เจอ
ดึง NVD ได้อย่างน้อยกับ CVE ที่เจอ
มี quarantine แยกชัด
```

ดีมาก:

```text
เก็บได้ 80-150 targets
มี known family + unknown family + weak/noisy ครบ
มี CVE enrichment ครบมากกว่า 80%
มี negative/control cases เพียงพอ
มี report อ่านแล้ว Codex นำเข้า ML repo ต่อได้ทันที
```

## ห้ามทำ

```text
ห้าม scan public IP/domain ที่ไม่ได้รับอนุญาต
ห้ามเอา post-exploit success เป็น precheck feature
ห้ามเอา CISA/EPSS/NVD metadata มาแทน scanner evidence
ห้าม train ทับทันทีโดยไม่แยก validation set
ห้ามลบ raw evidence ก่อน Codex ตรวจ
ห้ามปิด container ทิ้งโดยไม่เขียน failure note
```

## แหล่งอ้างอิง official

ใช้แหล่งเหล่านี้เป็นหลัก:

- CISA KEV: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- CISA KEV JSON feed: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
- CISA KEV GitHub mirror: https://github.com/cisagov/kev-data
- EPSS API: https://api.first.org/data/v1/epss
- EPSS overview/data: https://www.first.org/epss/
- NVD CVE API 2.0: https://nvd.nist.gov/developers/vulnerabilities
- NVD data feeds: https://nvd.nist.gov/vuln/data-feeds
- Vulhub: https://github.com/vulhub/vulhub
- Vulhub getting started: https://vulhub.org/getting-started
- Nuclei install: https://docs.projectdiscovery.io/opensource/nuclei/install
- Naabu install: https://docs.projectdiscovery.io/opensource/naabu/install

