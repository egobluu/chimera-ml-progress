# ผล ML หลังรวม Strict Precheck Improve v01

## สรุปสั้น

รอบนี้นำผล `dec-strict-precheck-improve-2026-08-31` จาก Kali/OpenCode มา merge แล้ว train ใหม่ โดยใช้เฉพาะ target ที่ OpenCode ระบุว่า safe to merge เท่านั้น

ผลคือข้อมูลสะอาดขึ้น แต่ `strict_precheck` ยังไม่ถึงระดับใช้งานจริง

## ข้อมูลที่นำเข้า

| รายการ | จำนวน |
| --- | ---: |
| base targets | 40 |
| targets ที่มี strict precheck feature ใช้ได้ | 4 |
| records ที่ skip เพราะ inconsistent | 11 |
| records ที่ skip เพราะ target ไม่อยู่ใน safe list | 45 |
| features หลัง merge | 86 |

safe targets ที่นำเข้า:

- `redis_auth_non_vulnerable`
- `tomcat_non_vulnerable`
- `solr_CVE-2019-17558`
- `shiro_CVE-2016-4437`

quarantined targets ที่ไม่นำเข้า:

- `thinkphp_5-rce`
- `couchdb_CVE-2017-12635`
- `nginx_CVE-2017-7529`
- `tomcat_CVE-2017-12615`
- `tomcat_CVE-2020-1938`
- `solr_non_vulnerable`
- `shiro_non_vulnerable`

## ผลเทรน

| Profile | Features | Threshold | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_v02 | 86 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 20 | 0 | 20 | 0 |
| strict_precheck | 80 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 20 | 0 | 0 |
| strict_no_negative_count | 85 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 20 | 0 | 0 |
| scanner_only | 32 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 20 | 0 | 0 |
| no_metasploit | 82 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 20 | 0 | 20 | 0 |
| no_nuclei_confirm | 85 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 20 | 0 | 20 | 0 |

## Threshold Sweep ของ strict_precheck

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.10 | 20 | 20 | 0 | 0 | 0.500 | 1.000 | 0.667 |
| 0.20 | 16 | 20 | 0 | 4 | 0.444 | 0.800 | 0.571 |
| 0.30 | 13 | 17 | 3 | 7 | 0.433 | 0.650 | 0.520 |
| 0.40 | 13 | 6 | 14 | 7 | 0.684 | 0.650 | 0.667 |
| 0.50 | 13 | 4 | 16 | 7 | 0.765 | 0.650 | 0.703 |
| 0.60 | 13 | 3 | 17 | 7 | 0.812 | 0.650 | 0.722 |
| 0.70 | 10 | 3 | 17 | 10 | 0.769 | 0.500 | 0.606 |
| 0.80 | 3 | 1 | 19 | 17 | 0.750 | 0.150 | 0.250 |
| 0.90 | 0 | 0 | 20 | 20 | 0.000 | 0.000 | 0.000 |

## แปลผล

`strict_precheck` ยังเลือก exploit เยอะเกินไป ถ้าใช้ threshold 0.10 จะไม่พลาด positive เลย แต่ false positive ครบ 20 ตัว

ถ้าขยับ threshold เป็น 0.60 false positive ลดเหลือ 3 ตัว แต่ false negative เพิ่มเป็น 7 ตัว แปลว่าพลาดช่องโหว่จริงมากเกินไป

ดังนั้นสถานะตอนนี้คือ:

```text
pipeline พร้อม
ข้อมูลสะอาดขึ้น
แต่ ML strict_precheck ยังไม่พร้อมใช้งานจริง
```

## ทำไมข้อมูลเพิ่มแล้วยังไม่ดีขึ้น

เพราะรอบนี้ target ที่ safe to merge มีแค่ 4/40 target โมเดลจึงยังเห็น pattern ฝั่ง negative ไม่พอ โดยเฉพาะ family ที่ต้องการคู่เทียบ เช่น Tomcat positive/negative, Solr positive/negative, Shiro positive/negative

อีกปัญหาคือ target หลายตัวที่ควรเป็นคู่เทียบกลับ inconsistent เช่น `tomcat_CVE-2017-12615` positive แต่ probe พบว่า PUT ไม่ผ่าน หรือ `solr_non_vulnerable` negative แต่ probe พบว่า Velocity enabled เหมือน positive

## ควรหยุดไหม

ยังไม่ควรหยุดงาน ML core ถ้าเป้าหมายคือใช้งานจริงแบบ precheck

ควรหยุดเฉพาะงานเพิ่ม feature กว้าง ๆ แล้วเปลี่ยนไปทำงานคุณภาพ label:

1. แก้ target ที่ inconsistent
2. หา lab replacement สำหรับ target ที่ label ไม่ตรง
3. เก็บคู่ positive/negative ที่ consistent ต่อ family
4. ค่อย train `strict_precheck` ใหม่

เกณฑ์ที่ควรถึงก่อนหยุด:

| Metric | เป้าหมายขั้นต่ำ |
| --- | ---: |
| False Positive | <= 5 จาก 20 negative |
| False Negative | <= 2 จาก 20 positive |
| F1 | >= 0.80 |

