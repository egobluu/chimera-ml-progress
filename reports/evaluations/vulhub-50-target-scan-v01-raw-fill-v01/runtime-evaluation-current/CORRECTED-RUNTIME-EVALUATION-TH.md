# Corrected Runtime Evaluation

## สรุป

ไฟล์นี้เป็นผลประเมินที่รันใหม่จาก `scripts/predict_prototype.py` หลัง patch unknown-product guard แล้ว ไม่ใช่การคัดลอกตัวเลขจาก scanner-side summary

## Metrics

| Metric | Result |
| --- | ---: |
| Total targets | 51 |
| Gate accuracy | 0.8235 |
| Gate TP | 23 |
| Gate FP | 9 |
| Gate TN | 19 |
| Gate FN | 0 |
| Gate precision | 0.7188 |
| Gate recall | 1.0 |
| Gate F1 | 0.8364 |
| Known-positive Ranker Top-1 | 0.5333 |
| Known-positive Ranker Top-3 | 0.6 |
| Known-positive CVE Resolver coverage | 0.5 |
| Known-positive CVE Resolver Top-1 | 0.5 |
| Known-positive CVE Resolver Top-3 | 0.5 |
| Known-positive CVE Resolver Top-5 | 0.5 |
| Ranker low-margin count | 18 |
| Family not-ready count | 25 |
| Unknown rejection rate | 1.0 |
| Safety flow accuracy | 0.8627 |
| Strict flow accuracy | 0.8627 |

## วิธีอ่าน

`Safety flow accuracy` คือระบบตัดสินทางปลอดภัยถูกไหม เช่น negative ต้องหยุด, unknown ต้อง triage, positive ต้องไม่ถูกหยุดผิด

`Strict flow accuracy` คือเข้มกว่า: known-positive ต้องจัด family ถูกด้วย จึงจะนับว่าถูก

`CVE Resolver Top-3` คือหลัง Ranker เลือก family แล้ว CVE เฉลยอยู่ใน 3 อันดับแรกของ resolver ไหม

ดังนั้นถ้า safety สูงแต่ strict ต่ำ แปลว่า flow ยังปลอดภัย แต่ Ranker ยังต้องปรับ feature/ranking ต่อ
