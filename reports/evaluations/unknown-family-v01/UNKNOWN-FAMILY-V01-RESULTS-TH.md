# ผลทดสอบ Unknown Family v01

## สรุปสั้น

ทดสอบแล้วว่า XGBoost Family Ranker ถ้าเจอ target นอก family ที่รู้จักจะเป็นอย่างไร

ผลสำคัญคือ:

```text
ถ้าไม่มี unknown guard ตัว Ranker จะฝืนตอบ family เดิมเสมอ
ถ้ามี unknown guard แบบดู family-specific signal จะเริ่มแยก unknown/no-exploit ได้
```

ดังนั้นระบบใช้งานจริงต้องมี `unknown_family` หรือ `needs_manual_triage` ไม่อย่างนั้นโมเดลจะมั่วตอบหนึ่งใน candidate family ที่มีอยู่เสมอ

## ขอบเขตการทดสอบ

Dataset ที่ใช้:

```text
reports/evaluations/family-ranking-backfill-v01/target-exploitability-family-ranking-backfill.csv
```

สคริปต์ที่ใช้:

```text
scripts/evaluate_unknown_family.py
```

คำสั่ง:

```bash
python scripts/evaluate_unknown_family.py \
  --dataset reports/evaluations/family-ranking-backfill-v01/target-exploitability-family-ranking-backfill.csv \
  --out-dir reports/evaluations/unknown-family-v01
```

## Known candidate families ตอนนี้

Ranker รู้จัก family เหล่านี้เท่านั้น:

```text
couchdb_auth
elasticsearch
flask
grafana
jenkins
joomla
nextjs
nexus
nginx
phpmyadmin
redis
shiro_key
solr_velocity
spring
struts2
thinkphp_rce
tomcat_ajp
tomcat_put
```

ถ้า target เป็น family อื่น เช่น WordPress, Laravel, Drupal, Apache อื่น ๆ ตัว Ranker จะตอบชื่อจริงไม่ได้ถ้ายังไม่เพิ่ม candidate family นั้นเข้าไป

## วิธีทดสอบ

ทดสอบ 2 กลุ่ม:

1. `negative/no_exploit rows` จาก dataset จริง 39 targets
2. synthetic unknown 4 targets:
   - `unknown_wordpress_plugin_rce`
   - `unknown_laravel_debug_rce`
   - `unknown_generic_php_upload`
   - `unknown_drupal_rce`

หมายเหตุ: synthetic unknown ไม่ใช่ผลสแกนจริง แต่ใช้เป็น smoke test เพื่อดูพฤติกรรมว่า model จะฝืนตอบ family เดิมไหมเมื่อไม่มี feature ที่ตรงกับ family ที่รู้จัก

## Open-set rules ที่ลอง

| Rule | ความหมาย |
| --- | --- |
| `max_signal_decision` | ยอมเป็น known ถ้ามี candidate family ใด ๆ match positive signal อย่างน้อย 2 ตัว |
| `top1_signal_decision` | ยอมเป็น known ถ้า family ที่ชนะอันดับ 1 match positive signal อย่างน้อย 2 ตัว |
| `clean_top1_decision` | ยอมเป็น known ถ้า family ที่ชนะอันดับ 1 match positive signal อย่างน้อย 2 ตัว และไม่มี negative signal |

## ผลกับ unknown/no-exploit

| กลุ่ม | Rule | Reject เป็น unknown |
| --- | --- | ---: |
| negative/no_exploit 39 targets | `max_signal_decision` | 36/39 |
| negative/no_exploit 39 targets | `top1_signal_decision` | 38/39 |
| negative/no_exploit 39 targets | `clean_top1_decision` | 39/39 |
| synthetic unknown 4 targets | ทุก rule | 4/4 |

แปลว่า unknown guard จับ synthetic unknown ได้ครบ และจับ no-exploit ได้เกือบครบ

## จุดที่ยังพลาด

เมื่อใช้ rule กลาง `top1_signal_decision` ยังมี no-exploit ที่หลุด 1 ตัว:

| Target | Top-1 ที่ Ranker ตอบ | เหตุผลที่หลุด |
| --- | --- | --- |
| `redis_auth_non_vulnerable` | `redis` | มี Redis signal จริง เช่น `redis_info_accessible`, `lua_available` แต่มี `auth_required` เป็น negative signal |

แปลว่า rule นี้ยังไม่พอ ต้องดู negative signal ร่วมด้วย เช่นถ้า `auth_required=1` สำหรับ Redis exploit ควรไม่ปล่อยเป็น known-ready

## ผลกับ known positive

ถ้าใช้ rule `top1_signal_decision` จะ reject known positive 7/26 targets:

| Target | Family จริง | สาเหตุ |
| --- | --- | --- |
| `couchdb_CVE-2017-12636` | `couchdb_auth` | มี positive signal แค่ 1 ตัว |
| `joomla_CVE-2023-23752` | `joomla` | ยังไม่มี backfill evidence ที่ merge ได้ |
| `nextjs_CVE-2025-29927` | `nextjs` | ยังไม่มี Vulhub lab/evidence ที่ merge ได้ |
| `nexus_CVE-2020-10199` | `nexus` | มี positive signal แค่ 1 ตัว |
| `nexus_CVE-2024-4956` | `nexus` | มี positive signal แค่ 1 ตัว |
| `thinkphp_5023_rce` | `thinkphp_rce` | มี positive signal แค่ 1 ตัว |
| `tomcat_CVE-2017-12615` | `tomcat_put` | ยังไม่มี evidence ที่เสถียร |

นี่ไม่ได้แปลว่า target เหล่านี้ไม่ vulnerable แต่แปลว่า evidence สำหรับ family ranking ยังไม่พอให้ตอบอย่างมั่นใจ

## คำตอบว่าเจอของนอกชุดแล้วทำได้ดีไหม

คำตอบคือ:

```text
ถ้าไม่มี unknown guard: ยังไม่ดี เพราะ Ranker จะฝืนตอบ family ที่รู้จักเสมอ
ถ้ามี unknown guard: เริ่มดีขึ้น จับ unknown smoke test ได้ครบ แต่ยังต้องจูนกับ target จริงมากกว่านี้
```

ตอนนี้เหมาะพูดว่า:

```text
ระบบเริ่มรองรับ unknown-family ได้ระดับ prototype โดยใช้ open-set guard จาก family-specific signal
```

ยังไม่ควรพูดว่า:

```text
ระบบรู้จักช่องโหว่ทุกชนิดแล้ว
```

## วิธีทำให้ครอบคลุมขึ้น

1. เพิ่ม `unknown_family` เป็น output จริงของโปรแกรม
2. แยกการตัดสินเป็น 3 ค่า:
   - `known_family_ready`
   - `known_family_but_low_confidence`
   - `unknown_family`
3. ใช้ Gate ก่อน Ranker เสมอ ถ้า Gate บอก `no_exploit` ไม่ต้องเชื่อ Ranker
4. เพิ่ม negative signal ใน unknown guard เช่น `auth_required`, `version_patched`, `endpoint_missing`
5. เพิ่ม candidate family ทีละกลุ่มจาก target ใหม่ที่เจอบ่อย เช่น WordPress, Drupal, Laravel, Apache HTTPD, PHP-CGI
6. สำหรับ family ใหม่ ต้องเก็บอย่างน้อย:
   - positive controls 3-5 targets
   - negative controls 3-5 targets
   - precondition features ที่บอกว่ายิงได้/ยิงไม่ได้
   - Metasploit/manual PoC result เป็นเฉลย
7. ทำ unseen validation โดยให้ model ทายก่อน แล้วค่อยยิง Metasploit/manual PoC เพื่อเฉลย

## ข้อเสนอสำหรับระบบจริง

ตอนใช้งานจริงควรให้ output เป็นแบบนี้:

```text
Gate:
  exploitability = likely_exploitable / no_exploit / unknown

Family Ranker:
  top1_family = redis
  confidence = low / medium / high
  decision = known_family_ready / known_family_but_low_confidence / unknown_family
  reason = lua_available=1, auth_required=1 ทำให้ไม่ควรยิงทันที
```

ถ้าเป็น `unknown_family` ให้ระบบตอบว่า:

```text
ยังไม่อยู่ใน family ที่โมเดลรู้จัก หรือ evidence ยังไม่พอ
ควรสแกนเพิ่มและทำ manual triage ก่อน
```
