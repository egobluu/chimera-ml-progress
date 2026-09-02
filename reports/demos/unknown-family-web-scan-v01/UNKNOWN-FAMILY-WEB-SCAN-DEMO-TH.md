# Unknown-family Web Scan Demo Result v01

วันที่: 2026-09-03

## สรุป

สร้าง local target ที่ ML ไม่รู้จักชื่อ `Acme ZeroCMS` แล้วให้ demo scanner อ่านหน้าเว็บจริง สร้าง feature ส่งเข้า ML runtime และสร้าง dashboard เทียบกับเฉลย

Docker compose ถูกเตรียมไว้แล้ว แต่ Docker daemon บน Windows ยังไม่เปิด:

```text
failed to connect to dockerDesktopLinuxEngine
```

ดังนั้นรอบนี้รัน target เดียวกันผ่าน local Python HTTP server แทน เพื่อทดสอบ scanner -> feature -> ML -> dashboard ให้ครบก่อน

## Target

| Field | Value |
| --- | --- |
| URL | `http://127.0.0.1:18080` |
| Product | `Acme ZeroCMS` |
| True family | `acme_zerocms` |
| Known to Ranker | `false` |
| Expected Gate | `likely_exploitable` |
| Expected final | `unknown_family_triage` |

## Feature ที่ scanner สร้าง

```json
{
  "target_id": "acme_zerocms_unknown_demo_01",
  "is_http_target": 1,
  "endpoint_reachable_count": 1,
  "no_auth_required": 1,
  "version_in_vulnerable_range": 1,
  "unknown_product_detected": 1,
  "unknown_family_signal_count": 2,
  "known_family_signal_count": 0
}
```

## ML Result

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| Gate exploitability | `likely_exploitable` | `likely_exploitable` | pass |
| Raw top ranked family | `not applicable` | `redis` | expected closed-set behavior |
| Unknown guard | `unknown_family` | `unknown_family` | pass |
| Final decision | `unknown_family_triage` | `unknown_family_triage` | pass |
| Safe known-family verification | `false` | `false` | pass |

## การตีความ

ภาษาคน:

```text
ML Gate มองถูกว่า target นี้มีสัญญาณน่าตรวจต่อ
Ranker ดิบยังฝืนจัดอันดับเป็น redis เพราะ family จริงไม่ได้อยู่ใน candidate list
Unknown guard กันถูก จึงไม่ปล่อยให้ redis ranking ถูกใช้ต่อ
final_decision จบที่ unknown_family_triage ตามที่ควรเป็น
```

ดังนั้นถ้านับเป็น 2 pass:

```text
Pass 1: Gate ทายว่าน่าตรวจ exploit ต่อไหม = ถูก
Pass 2: Ranker/Unknown guard รู้ว่าไม่ควรเชื่อ known-family ranking = ถูก
```

## Output Files

```text
reports/demos/unknown-family-web-scan-v01/feature.json
reports/demos/unknown-family-web-scan-v01/ground-truth.json
reports/demos/unknown-family-web-scan-v01/prediction.json
reports/demos/unknown-family-web-scan-v01/verdict.json
reports/demos/unknown-family-web-scan-v01/dashboard.html
```

## Dashboard

เปิดที่:

```text
http://127.0.0.1:18081/reports/demos/unknown-family-web-scan-v01/dashboard.html
```

## Docker

Docker files อยู่ที่:

```text
demos/unknown-family-web-scan-v01/docker-compose.yml
demos/unknown-family-web-scan-v01/target/Dockerfile
```

เมื่อ Docker Desktop daemon เปิดแล้ว รัน:

```powershell
docker compose -f demos\unknown-family-web-scan-v01\docker-compose.yml up -d --build
```

แล้ว scan ซ้ำ:

```powershell
$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py demos\unknown-family-web-scan-v01\scripts\scan_unknown_target.py `
  --url http://127.0.0.1:18080 `
  --out-dir reports\demos\unknown-family-web-scan-v01
```

