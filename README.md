# Chimera Scanner ML Progress

repo นี้ใช้เก็บสรุปความคืบหน้าฝั่ง Machine Learning ของโครงงาน `chimera-scanner-dataset` ตั้งแต่ช่วงที่เริ่มเปลี่ยนแนวทางมาใช้ **XGBoost Ranking / XGBoost Gate** เพื่อช่วยจัดลำดับการทดสอบช่องโหว่จากผล vulnerability scanner

เนื้อหาเน้นตอบคำถามหลัก:

- เราทำอะไรไปแล้ว
- ใช้ข้อมูลอะไร train
- ทดสอบอย่างไร
- คะแนนมาจากไหน
- เจอปัญหาอะไร
- แก้อย่างไร
- ตอนนี้โมเดลอยู่ระดับไหน
- ต้องทำอะไรต่อเพื่อให้ใช้งานจริงได้มากขึ้น

## แนวคิดระบบล่าสุด

ระบบถูกออกแบบเป็น 2-stage ML workflow:

```text
Scanner Evidence
      ↓
ML-only Exploitability Gate
      ↓
XGBoost Family Ranker
      ↓
Metasploit / Manual Verification
      ↓
Feedback กลับเข้า Dataset
```

ความหมาย:

- `Exploitability Gate`: โมเดลตัดสินว่า target นี้ควรถูกทดสอบ exploit ต่อหรือควรเป็น `no_exploit`
- `Family Ranker`: ถ้า Gate บอกว่าควร exploit จึงจัดอันดับ exploit family เช่น `tomcat`, `redis`, `spring`, `nexus`
- `Verification`: ใช้ Metasploit/manual PoC ตรวจว่าผลที่เลือกใช้ได้จริงหรือไม่
- `Feedback Loop`: เอาผลยิงได้/ยิงไม่ได้กลับมาเพิ่ม dataset และ feature

## สถานะล่าสุด

สถานะล่าสุดคือ **ML-only Exploitability Gate v0.2 รันได้ครบ pipeline แล้ว** แต่ผลที่เหมาะกับการใช้งานจริงต้องดู profile `strict_precheck` เป็นหลัก

ผลจาก full profile:

| Metric | v0.1 | v0.2 |
| --- | ---: | ---: |
| Recall | 1.000 | 1.000 |
| False Negative | 0 | 0 |
| False Positive | 12 | 0 |
| F1 | 0.769 | 1.000 |
| gate-feature-evidence | 14/40 | 40/40 |
| Features | 33 | 44 |

ข้อควรระวัง: คะแนน full profile ยังดีเกินจริง เพราะมี feature ที่ใกล้คำเฉลยหรือเกิดหลังตรวจ exploit แล้ว ส่วน `strict_precheck` หลังรวม targeted pair fix ยังมี FP=20 ที่ threshold 0.10 จึงยังไม่ควรพูดว่าโมเดลแม่นแล้ว

## เอกสารสำคัญ

- [docs/00-navigation-th.md](docs/00-navigation-th.md) - สารบัญหลักว่าอ่าน repo นี้ยังไง
- [docs/01-project-scope-th.md](docs/01-project-scope-th.md) - ขอบเขตงาน ML หลังเริ่มใช้ XGBoost Ranking
- [docs/02-timeline-th.md](docs/02-timeline-th.md) - timeline ว่าทำอะไรไปแล้วตามลำดับ
- [docs/03-training-and-evaluation-th.md](docs/03-training-and-evaluation-th.md) - วิธี train/test และ metric ที่ใช้
- [docs/04-feature-schema-th.md](docs/04-feature-schema-th.md) - feature ที่ใช้และเหตุผล
- [docs/05-lessons-learned-th.md](docs/05-lessons-learned-th.md) - ปัญหาและสิ่งที่แก้
- [docs/06-scanning-tools-th.md](docs/06-scanning-tools-th.md) - เครื่องมือที่ใช้ในงานจริงและงานเก็บ dataset
- [docs/07-feature-catalog-th.md](docs/07-feature-catalog-th.md) - รายการ feature ทั้งหมดและ phase ที่ใช้ได้/ห้ามใช้
- [docs/08-workflow-responsibilities-th.md](docs/08-workflow-responsibilities-th.md) - หน้าที่ของ Codex, OpenCode, ML, scanner และ Metasploit
- [scripts/README.md](scripts/README.md) - script ที่ใช้ build dataset, train model และ inference
- [reports/README.md](reports/README.md) - สารบัญ reports แยก progress/audit/evaluation/plan/quarantine
- [reports/progress/current-status-th.md](reports/progress/current-status-th.md) - สรุปสถานะล่าสุด
- [reports/plans/targeted-precondition-v02/TARGETED-PRECONDITION-PROBE-PLAN-TH.md](reports/plans/targeted-precondition-v02/TARGETED-PRECONDITION-PROBE-PLAN-TH.md) - แผน probe เจาะจงที่เกลาใหม่สำหรับลด false positive
- [reports/evaluations/targeted-precondition-v02/TARGETED-PRECONDITION-ML-RESULTS-TH.md](reports/evaluations/targeted-precondition-v02/TARGETED-PRECONDITION-ML-RESULTS-TH.md) - ผล ML หลังรวม targeted precondition และข้อผิดพลาดที่ยังเหลือ
- [reports/quarantine/targeted-pair-quality-v01/TARGETED-PAIR-QUALITY-AUDIT-TH.md](reports/quarantine/targeted-pair-quality-v01/TARGETED-PAIR-QUALITY-AUDIT-TH.md) - ตรวจคุณภาพ targeted pair ก่อนนำเข้า train
- [reports/evaluations/targeted-pair-fix-v01/TARGETED-PAIR-FIX-ML-RESULTS-TH.md](reports/evaluations/targeted-pair-fix-v01/TARGETED-PAIR-FIX-ML-RESULTS-TH.md) - ผลหลังรวมเฉพาะ targeted pair records ที่ consistent
- [reports/evaluations/strict-precheck-improve-v01/STRICT-PRECHECK-IMPROVE-ML-RESULTS-TH.md](reports/evaluations/strict-precheck-improve-v01/STRICT-PRECHECK-IMPROVE-ML-RESULTS-TH.md) - ผลหลังรวม strict precheck safe targets รอบล่าสุด
- [reports/evaluations/label-consistency-fix-v01/LABEL-CONSISTENCY-FIX-ML-RESULTS-TH.md](reports/evaluations/label-consistency-fix-v01/LABEL-CONSISTENCY-FIX-ML-RESULTS-TH.md) - ผลหลังคัด label consistency fix รอบล่าสุด
- [reports/evaluations/clean-control-labs-v01/CLEAN-CONTROL-LABS-ML-RESULTS-TH.md](reports/evaluations/clean-control-labs-v01/CLEAN-CONTROL-LABS-ML-RESULTS-TH.md) - ผลหลังเพิ่ม CouchDB clean control pair เป็น target ใหม่
- [reports/evaluations/clean-control-labs-v02/CLEAN-CONTROL-LABS-V02-ML-RESULTS-TH.md](reports/evaluations/clean-control-labs-v02/CLEAN-CONTROL-LABS-V02-ML-RESULTS-TH.md) - ผลหลังเพิ่ม clean control targets 9 ตัวแบบ precondition focus
- [reports/evaluations/missing-positive-controls-v01/MISSING-POSITIVE-CONTROLS-ML-RESULTS-TH.md](reports/evaluations/missing-positive-controls-v01/MISSING-POSITIVE-CONTROLS-ML-RESULTS-TH.md) - ผลหลังเพิ่ม positive controls ที่ขาด และทดสอบ `precondition_only`
- [reports/evaluations/negative-control-variations-v01/NEGATIVE-CONTROL-VARIATIONS-ML-RESULTS-TH.md](reports/evaluations/negative-control-variations-v01/NEGATIVE-CONTROL-VARIATIONS-ML-RESULTS-TH.md) - ผลหลังเพิ่ม negative controls จน `precondition_only` ผ่านเกณฑ์ prototype
- [reports/evaluations/family-ranking-v01/FAMILY-RANKING-V01-RESULTS-TH.md](reports/evaluations/family-ranking-v01/FAMILY-RANKING-V01-RESULTS-TH.md) - ผลทดสอบ XGBoost Family Ranker รอบแรก

## ระดับความพร้อม

ถ้าให้คะแนนภาพรวมเป้าหมายสุดท้ายเป็น 10/10:

```text
ตอนนี้อยู่ประมาณ 3/10 สำหรับ pipeline รวม และ `precondition_only` ผ่านระดับ prototype แล้ว
```

เพราะ:

- มี ML-only Gate ที่ train/evaluate/infer ได้แล้ว
- มี dataset 20 positive / 20 negative ที่ balance
- มี feature evidence ครบทุก target ที่ใช้ train
- แต่ยังต้องพิสูจน์กับ target ใหม่ที่ไม่เคยอยู่ใน train
- strict precheck ยัง false positive สูง ต้องเพิ่ม positive/negative pair ที่ label ไม่ขัดกัน
