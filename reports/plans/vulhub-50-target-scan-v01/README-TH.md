# Vulhub 50 Target Scan v01

เป้าหมายรอบนี้คือเก็บข้อมูลเพิ่มให้ ML รอดกับโลกจริงมากขึ้น ไม่ใช่เก็บแต่ positive ที่ยิงได้

## จำนวนที่ต้องการ

รวม 50 targets:

- 15 known-positive จาก family ที่ runtime รู้จัก
- 20 negative/weak controls เพื่อสอน Gate ว่าเมื่อไหร่ต้องหยุด
- 15 unknown-family เพื่อกัน Ranker เอา product ใหม่ไปยัดเป็น family เก่า

## หลักคิด

สำหรับ Vulhub ให้ prioritize CVE ที่เป็น RCE หรือใกล้ RCE ก่อน เพราะตรงกับงานของเรา:

- RCE
- auth bypass ที่นำไป RCE
- file upload ที่นำไป RCE
- template injection
- deserialization
- command injection
- path traversal ที่มีผลกับ exploit chain

แต่ทุก family ต้องมี negative/weak คู่กัน ไม่งั้น ML จะจำว่าเห็น product แล้วต้องไปต่อเสมอ

## ไฟล์สำคัญ

- `batch-50-targets.jsonl` คือ target manifest ที่ให้ scanner/OpenCode ใช้เป็นคิว
- `OPENCODE-PROMPT-TH.md` คือ prompt ยาวสำหรับส่งให้เครื่อง Kali/OpenCode
- output ที่ต้องได้กลับมาคือ `features.jsonl`, `targets.jsonl`, `validation-results.jsonl`, `cve-enrichment.jsonl`

## เกณฑ์ผ่าน

งานรอบนี้ถือว่าดีถ้า:

- ได้อย่างน้อย 50 rows
- negative/weak ไม่ต่ำกว่า 20 rows
- unknown-family ไม่ต่ำกว่า 15 rows
- ทุก row มี `target_id`, `category`, `expected_family`, `cve_candidates`, feature หลัก, และ validation note
- positive ที่ evidence ไม่ครบต้องเข้า quarantine ไม่ใช่ฝืน safe_to_merge
