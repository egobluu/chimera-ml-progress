# Unknown-family Web Scan Demo v01

demo นี้สร้าง local Docker target ที่ ML ไม่รู้จักชื่อ `Acme ZeroCMS`

เป้าหมาย:

```text
เปิดเว็บ target ใน Docker
scanner อ่านหน้าเว็บและ ground truth
สร้าง feature JSON
เรียก ML runtime
เทียบผลกับเฉลย
สร้าง dashboard HTML
```

## Run

จาก root repo:

```powershell
docker compose -f demos\unknown-family-web-scan-v01\docker-compose.yml up -d --build

$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py demos\unknown-family-web-scan-v01\scripts\scan_unknown_target.py `
  --url http://127.0.0.1:18080 `
  --out-dir reports\demos\unknown-family-web-scan-v01
```

หรือเปิด dashboard แบบกดสแกนจากหน้าเว็บ:

```powershell
$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py demos\unknown-family-web-scan-v01\scripts\demo_dashboard_server.py `
  --host 127.0.0.1 `
  --port 18082 `
  --default-url http://127.0.0.1:18080 `
  --out-dir reports\demos\unknown-family-web-scan-v01\interactive
```

แล้วเปิด:

```text
http://127.0.0.1:18082
```

target local ที่ใช้ลองสแกน:

```text
http://127.0.0.1:18080  Acme ZeroCMS
http://127.0.0.1:18083  Aurora Notes Portal
http://127.0.0.1:18084  Nova Board Service
```

หน้าเว็บจะเริ่มจากช่องใส่ Target URL ก่อน เมื่อกด Scan แล้ว server จะ:

```text
ดึงหน้า target
ดึง ground-truth.json
สร้าง feature JSON
เรียก ML Gate/Ranker
เทียบผลกับเฉลย
แสดง dashboard หลังสแกนเสร็จ
```

เครื่องมือที่ demo นี้ใช้:

```text
python urllib.request              ดึงหน้า target และ /ground-truth.json
local lab ground-truth.json        ใช้เป็นเฉลยของ lab เพื่อวัดว่า ML ถูกไหม
scan_unknown_target.py             แปลงหลักฐานเป็น feature JSON
scripts/predict_prototype.py       เรียก Gate + Family Ranker runtime
demo_dashboard_server.py           รวมผลและแสดง dashboard
```

รัน regression test สำหรับ target demo ทั้ง 3 ตัว:

```powershell
$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py demos\unknown-family-web-scan-v01\scripts\test_dashboard_demo.py
```

ผล report:

```text
reports/demos/unknown-family-web-scan-v01/regression/dashboard-demo-regression-summary.md
reports/demos/unknown-family-web-scan-v01/regression/dashboard-demo-regression-results.json
```

## ปรับ ML ต่อยังไง

จาก demo นี้ Gate ทำงานดีพอสำหรับคำถามแรกว่า target น่าตรวจต่อไหม แต่ Ranker ยังมีอาการ closed-set คือถ้าไม่มีหลักฐานเฉพาะ family มันยังต้องให้คะแนน family ที่รู้จักสักตัว เช่น Redis

สิ่งที่ควรทำต่อ:

```text
1. เก็บ feature เฉพาะ family เพิ่ม เช่น redis_detected, lua_available, solr_detected, velocity_enabled
2. เพิ่ม negative/weak target ที่มี generic signal แต่ไม่มี family-specific signal
3. แยก CVE Resolver เป็น mapping table ไม่เอา CVE เข้า Ranker ตรง ๆ
4. เพิ่ม regression test ให้ unknown-family ต้องไม่กลายเป็น known_family_ready
5. retrain Ranker หลัง dataset มี family-specific positive/negative ครบขึ้น
```

ถ้าต้องการดู dashboard static ที่สร้างไว้แล้ว:

```text
reports/demos/unknown-family-web-scan-v01/dashboard.html
```

## Expected

เพราะ target เป็น family ที่ Ranker ไม่รู้จัก:

```text
Gate ควรทายว่า likely_exploitable
Ranker อาจให้ top family เป็น known family บางตัว แต่ต้องไม่ถูกเชื่อ
final_decision ควรเป็น unknown_family_triage
```

ถ้าผลเป็นแบบนี้ ถือว่า ML ทำงานถูกสำหรับ unknown-family case
