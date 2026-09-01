# ผล ML หลังรวม Negative Control Variations v01

## สรุปสั้น

รอบนี้นำผล `dec-negative-control-variations-2026-09-01` มา merge ต่อจาก dataset ล่าสุด โดยเพิ่ม negative control variations 13 targets

หลังเพิ่ม derived precondition features แล้ว `precondition_only` ผ่านเกณฑ์ prototype ที่ตั้งไว้

## ข้อมูลที่นำเข้า

| รายการ | จำนวน |
| --- | ---: |
| base targets | 52 |
| appended new targets | 13 |
| total targets หลัง merge | 65 |
| features หลัง merge | 95 |
| skipped disallowed target records | 5 |

targets ใหม่ที่เพิ่ม:

- `tomcat_put_negative_v01`
- `tomcat_put_negative_v02`
- `tomcat_put_negative_v03`
- `tomcat_ajp_negative_v01`
- `tomcat_ajp_negative_v02`
- `tomcat_ajp_negative_v03`
- `shiro_key_negative_v01`
- `shiro_key_negative_v02`
- `shiro_key_negative_v03`
- `couchdb_auth_negative_v01`
- `couchdb_auth_negative_v02`
- `thinkphp_rce_negative_v01`
- `thinkphp_rce_negative_v02`

## การแก้ที่ทำในรอบนี้

เพิ่ม derived features ที่สร้างจาก precheck/precondition เท่านั้น:

- `precondition_positive_signal_count`
- `precondition_negative_signal_count`
- `precondition_signal_balance`
- `has_positive_precondition_signal`
- `has_negative_precondition_signal`

feature กลุ่มนี้ไม่ใช่คำเฉลยหลังยิง exploit แต่เป็นการสรุปสัญญาณจาก precondition ที่ scanner/probe เห็นก่อนยิงจริง

## ผลเทรนล่าสุด

| Profile | Features | Threshold | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_v02 | 100 | 0.15 | 0.954 | 0.926 | 0.962 | 0.943 | 25 | 2 | 37 | 1 |
| strict_precheck | 94 | 0.15 | 0.954 | 0.926 | 0.962 | 0.943 | 25 | 2 | 37 | 1 |
| strict_no_negative_count | 99 | 0.15 | 0.954 | 0.926 | 0.962 | 0.943 | 25 | 2 | 37 | 1 |
| precondition_only | 44 | 0.15 | 0.954 | 0.926 | 0.962 | 0.943 | 25 | 2 | 37 | 1 |
| scanner_only | 32 | 0.10 | 0.400 | 0.400 | 1.000 | 0.571 | 26 | 39 | 0 | 0 |
| no_metasploit | 96 | 0.15 | 0.954 | 0.926 | 0.962 | 0.943 | 25 | 2 | 37 | 1 |
| no_nuclei_confirm | 99 | 0.15 | 0.954 | 0.926 | 0.962 | 0.943 | 25 | 2 | 37 | 1 |

## เทียบกับเกณฑ์หยุด

| Metric | ผลล่าสุด | เกณฑ์หยุด | สถานะ |
| --- | ---: | ---: | --- |
| FP | 2 | <= 5 | ผ่าน |
| FN | 1 | <= 2 | ผ่าน |
| F1 | 0.943 | >= 0.80 | ผ่าน |

สรุป: ผ่านเกณฑ์ prototype แล้ว

## Threshold Sweep ของ precondition_only

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.05 | 26 | 21 | 18 | 0 | 0.553 | 1.000 | 0.712 |
| 0.10 | 25 | 4 | 35 | 1 | 0.862 | 0.962 | 0.909 |
| 0.15 | 25 | 2 | 37 | 1 | 0.926 | 0.962 | 0.943 |
| 0.20 | 25 | 2 | 37 | 1 | 0.926 | 0.962 | 0.943 |
| 0.30 | 25 | 2 | 37 | 1 | 0.926 | 0.962 | 0.943 |
| 0.40 | 25 | 2 | 37 | 1 | 0.926 | 0.962 | 0.943 |
| 0.50 | 25 | 2 | 37 | 1 | 0.926 | 0.962 | 0.943 |

threshold ที่แนะนำสำหรับ prototype ตอนนี้คือ `0.15`

## จุดที่ยังพลาด

| Target | Label จริง | Prediction | ความหมาย |
| --- | ---: | ---: | --- |
| `solr_non_vulnerable` | negative | positive | false positive |
| `solr_velocity_negative` | negative | positive | false positive |
| `thinkphp_5-rce` | positive | negative | false negative |

หมายเหตุ: `solr_non_vulnerable` และ `thinkphp_5-rce` เคยถูก flag ว่า label/problematic มาก่อน จึงควรถูก quarantine ใน clean dataset รุ่นถัดไป

## ข้อสรุป

ตอนนี้หยุดสแกนวนเพื่อเพิ่ม ML core ได้แล้วในระดับ prototype

สิ่งที่สำเร็จ:

- dataset มี 65 targets
- มี clean negative variations หลาย family
- มี profile `precondition_only` ที่ไม่พึ่ง Metasploit/postcheck
- FP/FN/F1 ผ่านเกณฑ์ขั้นต่ำ

งานถัดไปควรเปลี่ยนจาก “สแกนเพิ่มเพื่อให้คะแนนดีขึ้น” เป็น “ทำให้ใช้งานจริง”:

1. freeze dataset รุ่นนี้เป็น baseline
2. ทำ clean dataset ที่ตัด target quarantined ออก
3. สร้าง inference script/API ที่ใช้ `precondition_only`
4. ให้ Metasploit เป็น postcheck หลัง ML ทำนาย ไม่ใช่ feature precheck

