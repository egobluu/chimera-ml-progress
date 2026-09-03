# Corrected Runtime Evaluation

## สรุป

ไฟล์นี้เป็นผลประเมินที่รันใหม่จาก `scripts/predict_prototype.py` หลัง patch unknown-product guard แล้ว ไม่ใช่การคัดลอกตัวเลขจาก scanner-side summary

## Metrics

| Metric | Result |
| --- | ---: |
| Total targets | 51 |
| Gate accuracy | 0.9608 |
| Gate TP | 23 |
| Gate FP | 2 |
| Gate TN | 26 |
| Gate FN | 0 |
| Gate precision | 0.92 |
| Gate recall | 1.0 |
| Gate F1 | 0.9583 |
| Known-positive Ranker Top-1 | 1.0 |
| Known-positive Ranker Top-3 | 1.0 |
| Known-positive CVE Resolver coverage | 1.0 |
| Known-positive CVE Resolver Top-1 | 1.0 |
| Known-positive CVE Resolver Top-3 | 1.0 |
| Known-positive CVE Resolver Top-5 | 1.0 |
| Ranker low-margin count | 1 |
| Family not-ready count | 11 |
| Unknown rejection rate | 1.0 |
| Safety flow accuracy | 1.0 |
| Strict flow accuracy | 1.0 |

## วิธีอ่าน

`Safety flow accuracy` คือระบบตัดสินทางปลอดภัยถูกไหม เช่น negative ต้องหยุด, unknown ต้อง triage, positive ต้องไม่ถูกหยุดผิด

`Strict flow accuracy` คือเข้มกว่า: known-positive ต้องจัด family ถูกด้วย จึงจะนับว่าถูก

`CVE Resolver Top-3` คือหลัง Ranker เลือก family แล้ว CVE เฉลยอยู่ใน 3 อันดับแรกของ resolver ไหม

ดังนั้นถ้า safety สูงแต่ strict ต่ำ แปลว่า flow ยังปลอดภัย แต่ Ranker ยังต้องปรับ feature/ranking ต่อ
