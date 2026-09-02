# Corrected Runtime Evaluation

## สรุป

ไฟล์นี้เป็นผลประเมินที่รันใหม่จาก `scripts/predict_prototype.py` หลัง patch unknown-product guard แล้ว ไม่ใช่การคัดลอกตัวเลขจาก scanner-side summary

## Metrics

| Metric | Result |
| --- | ---: |
| Total targets | 10 |
| Gate accuracy | 1.0 |
| Gate TP | 5 |
| Gate FP | 0 |
| Gate TN | 5 |
| Gate FN | 0 |
| Gate precision | 1.0 |
| Gate recall | 1.0 |
| Gate F1 | 1.0 |
| Known-positive Ranker Top-1 | 1.0 |
| Known-positive Ranker Top-3 | 1.0 |
| Ranker low-margin count | 0 |
| Family not-ready count | 0 |
| Unknown rejection rate | 0 |
| Safety flow accuracy | 1.0 |
| Strict flow accuracy | 1.0 |

## วิธีอ่าน

`Safety flow accuracy` คือระบบตัดสินทางปลอดภัยถูกไหม เช่น negative ต้องหยุด, unknown ต้อง triage, positive ต้องไม่ถูกหยุดผิด

`Strict flow accuracy` คือเข้มกว่า: known-positive ต้องจัด family ถูกด้วย จึงจะนับว่าถูก

ดังนั้นถ้า safety สูงแต่ strict ต่ำ แปลว่า flow ยังปลอดภัย แต่ Ranker ยังต้องปรับ feature/ranking ต่อ
