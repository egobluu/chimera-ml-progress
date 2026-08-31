# Reports Index

โฟลเดอร์ `reports/` แยกตามชนิดของไฟล์ เพื่อให้อ่านง่ายและไม่เอาความคืบหน้าไปปนกับผลทดลอง

## progress

- `progress/current-status-th.md` - สถานะล่าสุด อ่านไฟล์นี้ก่อนถ้าอยากรู้ว่าตอนนี้ถึงไหน

## audits

- `audits/ml-gate-feature-v02/` - audit feature ของ ML Gate v0.2 ว่าตัวไหนเสี่ยง data leak
- `audits/ml-v02-failure/` - สรุปว่า ML v0.2 ยังพลาดตรงไหน

## evaluations

- `evaluations/profile-v02/` - ผลเทียบ profile ของ v0.2 ก่อนเพิ่ม backfill
- `evaluations/light-backfill-v02/` - ผลหลังเพิ่ม whatweb/curl/ffuf light backfill
- `evaluations/targeted-precondition-v02/` - ผลหลังเพิ่ม targeted precondition รอบแรก
- `evaluations/targeted-pair-fix-v01/` - ผลหลังรวมเฉพาะ targeted pair records ที่ label consistency ผ่าน
- `evaluations/strict-precheck-improve-v01/` - ผลหลังรวม strict precheck safe targets จาก Kali/OpenCode รอบล่าสุด
- `evaluations/label-consistency-fix-v01/` - ผลหลังรวม label consistency fix ที่ safe target เหลือ 1 ตัว และ quarantine อีก 5 ตัว
- `evaluations/clean-control-labs-v01/` - ผลหลังเพิ่ม CouchDB clean control pair เป็น target ใหม่ใน dataset
- `evaluations/clean-control-labs-v02/` - ผลหลังเพิ่ม clean control targets 9 ตัวแบบ precondition focus

## plans

- `plans/targeted-precondition-v01/` - แผน probe รุ่นแรก ยังละเอียด/กว้างเกินไป
- `plans/targeted-precondition-v02/` - แผน probe รุ่นที่เกลาแล้ว อ่านง่ายกว่าและใช้จริงกว่า

## quarantine

- `quarantine/targeted-pair-quality-v01/` - audit ผล targeted pair ที่ยังไม่ควร train เพราะ label/evidence ขัดกัน
