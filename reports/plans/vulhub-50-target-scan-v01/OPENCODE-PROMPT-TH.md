# Prompt สำหรับ OpenCode/Kali: Vulhub 50 Target Scan v01

ทำงานเฉพาะ lab/local/authorized target เท่านั้น ห้ามสแกน public internet แบบสุ่ม และห้ามยิง exploit เพื่อเอา shell จริงนอก lab

เป้าหมายคือเก็บ scanner evidence เพื่อทำให้ Chimera ML Gate + Family Ranker + CVE Resolver แข็งแรงขึ้น โดยเฉพาะเคส negative/weak/unknown ที่กัน model หลอน

## Input

ใช้ manifest นี้เป็นคิวหลัก:

```text
reports/plans/vulhub-50-target-scan-v01/batch-50-targets.jsonl
```

ถ้าไฟล์อยู่บนเครื่อง Codex ให้คัดลอกไปเครื่อง Kali ก่อน หรือสร้างไฟล์เดียวกันใน:

```text
~/chimera-lab-batch/vulhub-50-target-scan-v01/batch-50-targets.jsonl
```

## Output Path

เขียนผลทั้งหมดลง:

```text
/media/sf_kali-share/dataset/vulhub-50-target-scan-v01
```

ต้องมีโครงสร้างนี้:

```text
vulhub-50-target-scan-v01/
  features.jsonl
  targets.jsonl
  validation-results.jsonl
  cve-enrichment.jsonl
  safe-to-merge-targets.txt
  quarantined-targets.txt
  SCAN-REPORT-TH.md
  raw/
    <target_id>/
      docker-compose.yml.copy.txt
      ports.txt
      nmap.txt
      httpx.jsonl
      whatweb.json
      nuclei.jsonl
      curl-root.txt
      probe-notes.json
      enrichment.json
```

## ติดตั้งเครื่องมือ

```bash
sudo apt update
sudo apt install -y git curl wget jq unzip gzip ca-certificates python3 python3-venv python3-pip pipx docker.io docker-compose-plugin nmap whatweb ffuf nikto golang-go
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
docker version
docker compose version
```

ถ้า `docker ps` ติด permission หลัง `usermod` ให้ logout/login ใหม่ หรือใช้ `sudo docker` ชั่วคราว

ติดตั้ง httpx/nuclei:

```bash
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
echo 'export PATH="$PATH:$HOME/go/bin"' >> ~/.bashrc
export PATH="$PATH:$HOME/go/bin"
nuclei -update
nuclei -update-templates
```

Python workspace:

```bash
mkdir -p ~/chimera-lab-batch
cd ~/chimera-lab-batch
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install requests pyyaml tqdm packaging
```

Clone Vulhub:

```bash
cd ~/chimera-lab-batch
git clone https://github.com/vulhub/vulhub.git || true
cd vulhub
git pull --ff-only
```

## วิธีหา lab จาก manifest

สำหรับแต่ละ row ใน `batch-50-targets.jsonl`:

1. อ่าน `source_hint`
2. ถ้าเป็น `vulhub` ให้หา directory ด้วยคำสั่ง:

```bash
find ~/chimera-lab-batch/vulhub -iname '*CVE-2021-43798*' -o -iname '*grafana*'
```

3. ถ้าเจอหลาย directory ให้เลือก directory ที่มี `docker-compose.yml`
4. ถ้าไม่เจอ Vulhub lab ให้สร้าง negative/weak ด้วย docker image official/local เท่านั้น และเขียน note ใน `validation-results.jsonl`
5. ถ้า target รันไม่ได้ ให้ quarantine ไม่ต้องฝืน

## วิธีสแกนต่อ target

ต่อ target หนึ่งตัวให้ทำ:

```bash
docker compose pull || true
docker compose up -d
docker compose ps
docker ps --format '{{.Names}} {{.Ports}}' > raw/<target_id>/ports.txt
```

หา URL/port ที่ map ออก localhost แล้วทำ safe scan:

```bash
echo "http://127.0.0.1:<port>" > raw/<target_id>/urls.txt
nmap -sV -sT -Pn -p <port> 127.0.0.1 -oN raw/<target_id>/nmap.txt || true
httpx -l raw/<target_id>/urls.txt -json -status-code -title -tech-detect -follow-redirects -o raw/<target_id>/httpx.jsonl || true
whatweb --log-json raw/<target_id>/whatweb.json "http://127.0.0.1:<port>" || true
nuclei -l raw/<target_id>/urls.txt -jsonl -severity low,medium,high,critical -o raw/<target_id>/nuclei.jsonl || true
curl -i -L --max-time 10 "http://127.0.0.1:<port>/" > raw/<target_id>/curl-root.txt || true
```

ห้ามใช้ destructive probe:

- ห้าม upload shell
- ห้ามเขียนไฟล์ลง target
- ห้าม reverse shell
- ห้าม brute force
- ห้ามยิง payload ที่เปลี่ยน state ถ้าไม่ใช่ lab ที่ตั้งใจ verify และต้องบันทึกชัด

## Feature ที่ต้องเขียน

เขียน `features.jsonl` เป็น flat JSON 1 บรรทัดต่อ target

field กลาง:

```text
target_id
service_port
is_http_target
is_non_http_service
known_family_signal_count
unknown_family_signal_count
unknown_product_detected
version_in_vulnerable_range
version_patched
auth_required
no_auth_required
endpoint_reachable_count
endpoint_missing_count
precondition_pass_count
precondition_fail_count
```

field ตาม family ให้ดู `required_features` และ `blocking_features` ใน manifest แล้วพยายามเติมเป็น 0/1 ให้ครบ

ถ้า field ไม่มีหลักฐาน ให้ใส่ 0 และเขียนใน `probe-notes.json` ว่าไม่ได้พบจาก probe ไหน

## targets.jsonl

ทุก row ต้องมี:

```json
{"target_id":"grafana_cve_2021_43798_positive_001","category":"positive","expected_family":"grafana_path_traversal","expected_status":"validated_positive","source_image":"vulhub/grafana","cve":"CVE-2021-43798"}
```

category ใช้ได้แค่:

```text
positive
negative
weak
unknown_family
```

## validation-results.jsonl

ทุก target ต้องมี validation row:

```json
{"target_id":"grafana_cve_2021_43798_positive_001","actual_status":"validated_positive","safe_to_merge":true,"validation_method":"lab_ground_truth_plus_safe_precheck","notes":"version and traversal precondition consistent; no shell action"}
```

ถ้าข้อมูลไม่ครบ:

```json
{"target_id":"bad_target_001","actual_status":"inconclusive","safe_to_merge":false,"validation_method":"incomplete","notes":"container started but no mapped service port"}
```

## CISA KEV / EPSS / NVD enrichment

ให้ดึง enrichment สำหรับ CVE ที่พบใน manifest/README/nuclei เท่านั้น

CISA KEV:

```bash
curl -L "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json" -o cisa-kev.json
```

EPSS:

```bash
curl -L "https://api.first.org/data/v1/epss?cve=CVE-2021-43798&pretty=true"
```

NVD:

```bash
curl -L "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2021-43798"
```

ถ้าไม่มี NVD API key ให้ sleep 6 วินาทีต่อ request

เขียน `cve-enrichment.jsonl`:

```json
{"cve":"CVE-2021-43798","in_cisa_kev":true,"epss_score":0.0,"epss_percentile":0.0,"cvss_base_score":7.5,"cvss_base_severity":"HIGH","cwe":["CWE-22"],"affected_product":["grafana"]}
```

ถ้าดึงไม่ได้ให้ใส่ `null` และเขียน error note อย่าเดาค่า

## Quarantine rules

ใส่ `quarantined-targets.txt` ถ้า:

- container start ไม่สำเร็จ
- ไม่มี mapped port
- feature สำคัญหาย
- positive แต่ไม่มี required positive precondition
- negative/weak แต่มี required positive precondition แรงมาก
- label กับ evidence ขัดกัน
- CVE ไม่ชัดจนไม่รู้ว่ากำลัง label อะไร

ใส่ `safe-to-merge-targets.txt` ถ้า:

- feature พอ
- label ชัด
- evidence ไม่ขัด
- raw evidence เก็บครบ
- validation row อธิบายได้

## สรุปที่ต้องเขียน

ท้ายงานเขียน `SCAN-REPORT-TH.md`:

```text
จำนวนทั้งหมด
positive / negative / weak / unknown_family
safe_to_merge / quarantine
family ที่ได้เพิ่ม
CVE ที่เจอ
KEV/EPSS/NVD coverage
target ที่ fail พร้อมเหตุผล
target ที่ควรเอาเข้า validation ก่อน
```

## Success criteria

ขั้นต่ำ:

- ได้ 50 planned rows หรือถ้าบาง lab fail ต้องมี quarantine ชัด
- safe_to_merge อย่างน้อย 35 rows
- negative/weak อย่างน้อย 15 rows
- unknown_family อย่างน้อย 10 rows
- output JSONL valid ทุกไฟล์

ดีมาก:

- safe_to_merge มากกว่า 45 rows
- positive/negative/unknown balance ตาม manifest
- enrichment coverage มากกว่า 80% สำหรับ CVE ที่มี
- ไม่มี row ที่ label กับ evidence ขัดกัน
