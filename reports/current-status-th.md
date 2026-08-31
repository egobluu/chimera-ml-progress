# สถานะล่าสุดของงาน ML

## สรุปสถานะ

ตอนนี้งาน ML เดินมาถึง **ML-only Exploitability Gate v0.2**

ถือว่าผ่านเป้าหมาย prototype ระดับต้น เพราะ:

- ไม่พึ่ง Rule Gate เป็นตัวตัดสินหลัก
- train/evaluate/infer ได้
- มี model artifact
- มี threshold tuning
- มี feature schema
- มี dataset target-level
- มี evidence ครบ 40/40 validated targets

## Dataset ล่าสุด

| รายการ | จำนวน |
| --- | ---: |
| validated_positive | 20 |
| validated_negative | 20 |
| inconclusive | 15 |
| train/evaluate targets | 40 |
| gate features | 44 |

## ผล v0.2

| Metric | Result |
| --- | ---: |
| Accuracy | 1.000 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| False Positive | 0 |
| False Negative | 0 |

## การตีความ

ผลนี้แปลว่า v0.2 ทำงานดีมากบน dataset ปัจจุบัน แต่ยังไม่ควรสรุปว่าใช้งานจริงได้กับ target ใหม่ทั้งหมด เพราะ dataset ยังเล็กและ feature บางตัวอาจมีความใกล้กับ label

คำพูดที่เหมาะสม:

```text
โมเดล ML-only Gate v0.2 สามารถทำงานได้คงที่บน controlled dataset และพร้อมเข้าสู่ขั้นตอน unseen target validation
```

ไม่ควรพูดว่า:

```text
โมเดลแม่น 100% แล้ว
```

## งานถัดไป

1. ทำ leak audit ของ 44 features
2. แยก feature เป็น `precheck`, `postcheck`, `forbidden`
3. เพิ่ม unseen target 5-10 ตัว
4. ให้ model infer ก่อนเฉลย
5. ค่อยใช้ Metasploit/manual PoC ตรวจจริง
6. วัดว่า false positive/false negative ยังต่ำไหม

## Audit ล่าสุด

เพิ่มสคริปต์ `scripts/audit_gate_features.py` เพื่อเช็คว่า feature ไหนอาจทำให้คะแนนสูงเกินจริง โดยเฉพาะ feature ที่รู้หลังยิง exploit หรือหลังเขียนผล validation แล้ว งานถัดไปควรวัด `strict_precheck` ที่ตัด feature กลุ่มนี้ออกก่อน

## Light Backfill ล่าสุด

นำผล `dec-precheck-light-backfill-2026-08-31` มา merge แล้วได้ dataset 40 targets / 68 features โดยมี target ที่ backfill จริง 15 ตัว ผลยังชี้ว่า `strict_precheck` และ `scanner_only` มี FP=20 เมื่อเลือก threshold แบบไม่ยอมให้ FN เกิด แปลว่า feature ใหม่ช่วยเรื่องความสะอาดของข้อมูล แต่ยังไม่พอให้โมเดลแยก `no_exploit` ได้ ต้องเพิ่ม targeted precondition probes ต่อ

## Targeted Probe Plan

เพิ่มแผน `reports/targeted-precondition-plan-v01/` จาก false positive ของ `strict_precheck` ได้ 60 probe tasks ครอบคลุม 20 false positive targets เป้าหมายคือเก็บ feature ที่ผูกกับ exploit condition จริง เช่น `method_put_rejected`, `ajp_port_closed`, `auth_required`, `endpoint_missing`, `version_patched` เพื่อให้โมเดลลด FP โดยไม่ต้องพึ่ง `negative_evidence_count`

ปรับเพิ่มเป็น `reports/targeted-precondition-plan-v02/` เพื่อให้อ่านง่ายและทำงานจริงง่ายขึ้น โดยตัด probe กว้าง ๆ ที่ไม่จำเป็นออก เช่น `generic_*`, default path discovery ทั่วไป, target ที่ไม่มี lab ตรง และเน้นเฉพาะ precondition ที่ตอบว่า exploit family นั้นผ่านหรือไม่ผ่านจริง
