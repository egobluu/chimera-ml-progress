# Chimera ML Pilot Ready Package v01

โฟลเดอร์นี้เตรียมไว้สำหรับ present งาน ML ของ Chimera

## มีอะไรในนี้

- `source_dataset/` ข้อมูลจาก scanner batch ใหม่ เช่น targets, features, validation, CVE enrichment
- `curated/` ผลคัดกรองว่าอะไรเข้า train ได้ อะไรต้อง recheck
- `training/` CSV ที่ใช้ train model จริง
- `train_test_split/` ไฟล์แบ่ง train/test สำหรับ present
- `models/` model files ที่ train แล้ว
- `evaluation/` ผล regression/evaluation
- `PACKAGE-MANIFEST.json` สารบัญไฟล์ทั้งหมด

## ตัวเลขสำคัญ

- Scanner batch: 45 targets
- Scanner safe_to_merge: 32 targets
- Scanner quarantined: 13 targets
- Codex train_ready_strict: 12 targets
- Training dataset: 123 rows
- Train/Test split: 98/25 rows
- Feature columns: 122
- Regression: passed 5/5

## Train/Test Split

ไฟล์อยู่ใน:

`train_test_split/`

- `train.csv`: 98 rows
- `test.csv`: 25 rows
- `train-targets.txt`: รายชื่อ target ที่ใช้ train
- `test-targets.txt`: รายชื่อ target ที่ใช้ test
- `split-summary.json`: สรุปวิธีแบ่งข้อมูล

## Model Files

ไฟล์อยู่ใน:

`models/`

- `gate_precondition_only.json`: Gate model ใช้ทายว่า target ควรลอง exploit ต่อไหม
- `family_ranker.json`: Family Ranker ใช้จัดอันดับ exploit family
- `prototype_manifest.json`: รายละเอียด model, features, threshold, metrics

## คำตัดสินตอนนี้

ใช้ package นี้สำหรับ present/demo ได้

แต่ยังไม่ควรถือว่าเป็น production model เพราะ:

- candidate ใหม่นี้ยังไม่ชนะ baseline strict12 เดิม
- `needs_recheck` ยังเหลือหลาย target
- CVE enrichment ยังไม่ครบ
- family ใหม่ยังต้องเพิ่ม resolver mapping

