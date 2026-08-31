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

สถานะล่าสุดคือ **ML-only Exploitability Gate v0.2 สำเร็จตามเกณฑ์ prototype**

ผลหลัก:

| Metric | v0.1 | v0.2 |
| --- | ---: | ---: |
| Recall | 1.000 | 1.000 |
| False Negative | 0 | 0 |
| False Positive | 12 | 0 |
| F1 | 0.769 | 1.000 |
| gate-feature-evidence | 14/40 | 40/40 |
| Features | 33 | 44 |

ข้อควรระวัง: คะแนน v0.2 ยังมาจาก dataset ขนาดเล็ก 40 targets จึงยังไม่ใช่หลักฐานว่า generalize กับ target ใหม่ได้ดี ต้องทำ unseen target test ต่อ

## เอกสารสำคัญ

- [docs/01-project-scope-th.md](docs/01-project-scope-th.md) - ขอบเขตงาน ML หลังเริ่มใช้ XGBoost Ranking
- [docs/02-timeline-th.md](docs/02-timeline-th.md) - timeline ว่าทำอะไรไปแล้วตามลำดับ
- [docs/03-training-and-evaluation-th.md](docs/03-training-and-evaluation-th.md) - วิธี train/test และ metric ที่ใช้
- [docs/04-feature-schema-th.md](docs/04-feature-schema-th.md) - feature ที่ใช้และเหตุผล
- [docs/05-lessons-learned-th.md](docs/05-lessons-learned-th.md) - ปัญหาและสิ่งที่แก้
- [docs/06-scanning-tools-th.md](docs/06-scanning-tools-th.md) - เครื่องมือที่ใช้ในงานจริงและงานเก็บ dataset
- [docs/07-feature-catalog-th.md](docs/07-feature-catalog-th.md) - รายการ feature ทั้งหมดและ phase ที่ใช้ได้/ห้ามใช้
- [scripts/README.md](scripts/README.md) - script ที่ใช้ build dataset, train model และ inference
- [reports/current-status-th.md](reports/current-status-th.md) - สรุปสถานะล่าสุด

## ระดับความพร้อม

ถ้าให้คะแนนภาพรวมเป้าหมายสุดท้ายเป็น 10/10:

```text
ตอนนี้อยู่ประมาณ 2/10
```

เพราะ:

- มี ML-only Gate ที่ train/evaluate/infer ได้แล้ว
- มี dataset 20 positive / 20 negative ที่ balance
- มี feature evidence ครบทุก target ที่ใช้ train
- แต่ยังต้องพิสูจน์กับ target ใหม่ที่ไม่เคยอยู่ใน train
