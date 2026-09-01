# Codex Review: Unseen Validation v03

## สรุปสั้น

รอบ `dec-unseen-validation-v03-2026-09-02` เป็นรอบที่มีคุณค่ามากกว่าตัวเลข 100% ก่อนหน้า เพราะใช้ target ใหม่หลัง retrain runtime แล้ว และเปิดให้เห็น failure จริงของระบบ

source report จาก OpenCode มีตัวเลขบางจุดขัดกัน จึงไม่ควรใช้สรุปดิบโดยตรง ต้องใช้ corrected evaluation จาก `scripts/evaluate_runtime_predictions.py`

## Source Result จาก OpenCode

| Metric | Source Result |
| --- | ---: |
| Completed targets | 11/12 |
| Gate Accuracy | 1.000 |
| Unknown Guard | 1.000 |
| Ranker Top-1 | 0.800 |
| Safety Flow | 1.000 |
| Strict Flow | 0.909 |

ปัญหาที่ source report ระบุ:

- `solr_velocity_disabled_neg_v03` เป็น Gate false positive
- `tomcat_ajp_new_01` Ranker เลือก `nexus` เป็นอันดับ 1 แต่ `tomcat_ajp` อยู่ #2
- `wordpress_unknown_v03` ถูก block เพราะ disk เหลือน้อย

## สิ่งที่ Codex ตรวจเจอ

เมื่อ reconstruct JSONL จาก per-target files แล้ว rerun ด้วย runtime ปัจจุบันก่อนแก้ guard เพิ่ม ได้ผล:

| Metric | Corrected Before Guard Fix |
| --- | ---: |
| Total targets | 11 |
| Gate accuracy | 0.9091 |
| Gate FP | 1 |
| Gate FN | 0 |
| Known-positive Ranker Top-1 | 0.6000 |
| Unknown rejection rate | 0.0000 |
| Safety flow accuracy | 0.7273 |
| Strict flow accuracy | 0.5455 |

นี่แปลว่า source report ดิบยังไม่น่าเชื่อพอ เพราะ:

- unknown targets อย่าง `drupal_unknown_v03` และ `php_cgi_unknown_v03` มี fingerprint ของ unknown product แต่ตั้ง `unknown_product_detected=0`
- `solr_velocity_disabled_neg_v03` ไม่มี canonical `velocity_disabled=1`
- `couchdb_auth_new_01` ใช้ alias `admin_party` และ `config_endpoint_accessible` แทน canonical runtime fields
- `tomcat_ajp_new_01` แพ้ `nexus` เพราะ generic features เช่น `anonymous_access` และ `endpoint_reachable_count`

## Runtime Guard Fix ที่ทำหลังเห็น failure

แก้ `scripts/predict_prototype.py` เพิ่ม:

1. schema aliases

```text
admin_party -> admin_party_enabled
config_endpoint_accessible -> config_accessible
velocity_template_accessible -> velocity_enabled
```

2. unknown product derivation

ถ้ามี fingerprint เช่น:

```text
drupal_detected
php_detected
laravel_detected
jboss_detected
wordpress_detected
```

และไม่มี known-family signal ให้ derive:

```text
unknown_product_detected=1
```

3. blocking evidence downgrade

ถ้าโมเดลบอก `likely_exploitable` แต่มี negative evidence หนัก เช่น `version_not_affected` หรือ `velocity_disabled` และไม่มี strong positive precondition ให้ downgrade เป็น:

```text
low_confidence
```

4. family-specific rerank

ถ้า family หนึ่งมีหลักฐานเฉพาะจริง เช่น `ajp_port_open`, `couchdb_detected`, `shiro rememberMe`, `jenkins cli` ให้ priority สูงกว่า family ที่มีแต่ generic signal

## Corrected After Runtime Guard Fix

หลังแก้ runtime แล้ว rerun corrected evaluation:

| Metric | Corrected After Guard Fix |
| --- | ---: |
| Total targets | 11 |
| Gate accuracy | 1.0000 |
| Gate TP | 7 |
| Gate FP | 0 |
| Gate TN | 4 |
| Gate FN | 0 |
| Known-positive Ranker Top-1 | 1.0000 |
| Unknown rejection rate | 1.0000 |
| Safety flow accuracy | 1.0000 |
| Strict flow accuracy | 1.0000 |

## การตีความที่ถูกต้อง

ผลหลังแก้ runtime ไม่ใช่ proof ว่าโมเดลแม่น 100% กับโลกจริง เพราะเป็นการแก้หลังเห็น failure ของ v03 แล้ว

ควรพูดว่า:

```text
Unseen v03 ทำให้เจอ failure จริง 3 จุด ได้แก่ unknown-product flag, Solr negative evidence, และ generic-signal ranking bias หลังแก้ runtime guard แล้ว flow ผ่านในชุด v03 แต่ต้องทดสอบ v04 ด้วย target ใหม่เพื่อยืนยัน
```

ไม่ควรพูดว่า:

```text
โมเดลแม่น 100% แล้ว
```

## สิ่งที่ควรนำเข้า training dataset

ควรนำเข้าได้หลัง review:

- known-positive ที่ consistent: Tomcat PUT, Tomcat AJP, CouchDB, Shiro, Jenkins
- negative controls ที่ consistent: Redis patched, Grafana patched, Solr velocity disabled, Tomcat PUT blocked

ยังต้องระวัง:

- unknown-family positives ไม่ควรนำเข้า Ranker known-family training โดยตรง เพราะจะทำให้ closed-set family list เพี้ยน
- `wordpress_unknown_v03` ยังไม่ควรใช้ เพราะ blocked by disk

## งานถัดไป

1. ให้ OpenCode ทำ v04 ด้วย target ใหม่และส่ง canonical features ให้ตรง schema ตั้งแต่แรก
2. เพิ่ม disk cleanup ก่อนรัน WordPress/MySQL target
3. เพิ่ม feature extractor rule ว่า unknown product fingerprint ต้องตั้ง `unknown_product_detected=1`
4. เพิ่ม canonical Solr negative features เช่น `velocity_disabled=1`, `config_api_blocked=1`
5. ค่อย retrain หลัง merge เฉพาะ records ที่ consistent
