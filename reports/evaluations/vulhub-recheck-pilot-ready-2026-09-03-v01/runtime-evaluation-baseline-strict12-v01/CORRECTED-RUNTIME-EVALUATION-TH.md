# Corrected Runtime Evaluation

## สรุป

ไฟล์นี้เป็นผลประเมินที่รันใหม่จาก `scripts/predict_prototype.py` หลัง patch unknown-product guard แล้ว ไม่ใช่การคัดลอกตัวเลขจาก scanner-side summary

## Metrics

| Metric | Result |
| --- | ---: |
| Total targets | 45 |
| Gate accuracy | 0.4222 |
| Gate TP | 11 |
| Gate FP | 3 |
| Gate TN | 8 |
| Gate FN | 23 |
| Gate precision | 0.7857 |
| Gate recall | 0.3235 |
| Gate F1 | 0.4583 |
| Known-positive Ranker Top-1 | 0.5556 |
| Known-positive Ranker Top-3 | 0.5556 |
| Known-positive CVE Resolver coverage | 0.5 |
| Known-positive CVE Resolver Top-1 | 0.5 |
| Known-positive CVE Resolver Top-3 | 0.5 |
| Known-positive CVE Resolver Top-5 | 0.5 |
| Ranker low-margin count | 6 |
| Family not-ready count | 9 |
| Unknown rejection rate | 0.2 |
| Safety flow accuracy | 0.4667 |
| Strict flow accuracy | 0.4667 |

## Standard-label Metrics

ส่วนนี้นับเฉพาะ target ที่มี validation status พร้อมใช้งานจริง เช่น `validated_positive`, `validated_negative`, `no_exploit`, `weak_no_exploit`

| Metric | Result |
| --- | ---: |
| Standard-label targets | 32 |
| Gate accuracy | 0.5312 |
| Gate TP | 9 |
| Gate FP | 2 |
| Gate TN | 8 |
| Gate FN | 13 |
| Gate precision | 0.8182 |
| Gate recall | 0.4091 |
| Gate F1 | 0.5455 |
| Unknown rejection rate | 0.3077 |
| Safety flow accuracy | 0.5938 |
| Strict flow accuracy | 0.5938 |

## Validation Status Counts

```json
{
  "quarantined": 13,
  "validated_negative": 8,
  "validated_positive": 22,
  "weak_no_exploit": 2
}
```

## วิธีอ่าน

`Safety flow accuracy` คือระบบตัดสินทางปลอดภัยถูกไหม เช่น negative ต้องหยุด, unknown ต้อง triage, positive ต้องไม่ถูกหยุดผิด

`Strict flow accuracy` คือเข้มกว่า: known-positive ต้องจัด family ถูกด้วย จึงจะนับว่าถูก

`CVE Resolver Top-3` คือหลัง Ranker เลือก family แล้ว CVE เฉลยอยู่ใน 3 อันดับแรกของ resolver ไหม

`Standard-label Metrics` คือคะแนนที่ตัด target `inconclusive` ออกก่อน เพราะ target กลุ่มนั้นยังไม่มีเฉลยพอสำหรับวัด ML แบบยุติธรรม

ดังนั้นถ้า safety สูงแต่ strict ต่ำ แปลว่า flow ยังปลอดภัย แต่ Ranker ยังต้องปรับ feature/ranking ต่อ
