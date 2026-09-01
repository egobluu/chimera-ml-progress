# Codex Review: Unseen Validation v02

## สรุปสั้น

รอบ `dec-unseen-validation-v02-2026-09-01` เป็นรอบทดสอบที่มีประโยชน์มาก เพราะเริ่มใกล้การใช้งานจริงกว่าเดิม: ให้โมเดลทำนายจาก target ที่ไม่ได้อยู่ในชุด train เดิม แล้วค่อยตรวจผลกับ evidence/verification ทีหลัง

แต่ผลรอบนี้ **ยังไม่ควรสรุปว่า final flow ผ่าน 100% แบบไม่มีเงื่อนไข** เพราะไฟล์ evaluation กับไฟล์ prediction มีข้อมูลขัดกันในส่วน unknown-family guard

สิ่งที่ถือว่าโอเค:

- Gate แยก `likely_exploitable` กับ `no_exploit` ได้ดีมากในชุดนี้
- negative controls 4 ตัวถูกหยุดได้ถูกต้อง
- unknown-family targets มี feature บอกว่าเป็น unknown แล้ว

สิ่งที่ยังต้องแก้:

- Ranker ยังทาย family ผิดใน Redis/Grafana variants
- prediction เดิมปล่อย unknown-family บางตัวไปเป็น `ready_for_safe_verification`
- feature schema จาก OpenCode ยังไม่ตรงกับ runtime schema ทุกจุด

## ผลที่รายงานจาก OpenCode

| Metric | Result |
| --- | ---: |
| Completed/Total | 12/12 |
| Gate accuracy | 100% |
| Gate TP | 8 |
| Gate FP | 0 |
| Gate TN | 4 |
| Gate FN | 0 |
| Ranker top-1 | 33.3% |
| Unknown guard | 100% |
| Final flow | 100% |

## สิ่งที่ Codex ตรวจเจอ

ไฟล์ `unseen-v02-evaluation.json` รายงานว่า unknown guard ถูก 5/5 แต่ใน `per_target_results` ของไฟล์เดียวกันมี unknown-family targets ที่มีค่า:

```text
unknown_guard_correct: false
```

และใน `unseen-v02-predictions.jsonl` unknown-family targets เช่น:

- `unseen_drupal_01`
- `unseen_laravel_01`
- `unseen_jetty_01`
- `unseen_php_cgi_01`
- `unseen_jboss_01`

ถูกทำนายเป็น:

```text
gate.decision = likely_exploitable
ranker.decision = known_family_ready
final_decision = ready_for_safe_verification
```

ดังนั้นถ้าดูจาก prediction จริงก่อนแก้ runtime คำว่า `final flow 100%` ยังไม่ปลอดภัยพอสำหรับใช้งานจริง เพราะ unknown-family ไม่ควรถูกส่งไปเป็น known-family verification โดยอัตโนมัติ

## สาเหตุหลัก

### 1. Feature schema ไม่ตรงกันบางจุด

OpenCode ส่ง feature:

```text
is_non_http_target
```

แต่ runtime prototype ใช้:

```text
is_non_http_service
```

ทำให้บาง signal ไม่ถูกอ่านในรูปแบบที่โมเดลคาดไว้

### 2. Known-positive variants มี family-specific evidence ไม่พอ

ตัวอย่าง Redis variant ไม่มี signal สำคัญที่ ranker ใช้ เช่น:

```text
redis_detected
redis_info_accessible
lua_available
```

ตัวอย่าง Grafana variant ไม่มี signal สำคัญ เช่น:

```text
grafana_detected
plugin_path_candidate_found
public_plugin_path_accessible
path_traversal_candidate_found
```

เมื่อไม่มี signal เฉพาะ family พอ Ranker จึงไปเลือก family อื่นที่มี generic signal คล้ายกัน เช่น `redis`, `couchdb_auth`, `joomla`

### 3. Unknown-product feature ถูกเก็บแล้ว แต่ runtime เดิมยังไม่ใช้กันพลาด

ใน unseen v02 มี feature กลุ่มนี้:

```text
unknown_product_detected
unknown_family_signal_count
known_family_signal_count
drupal_detected
laravel_detected
jetty_detected
php_cgi_detected
jboss_detected
```

แต่ runtime เดิมยังปล่อยให้ Ranker ตอบ known family ได้ แม้ `unknown_product_detected=1`

## สิ่งที่ Codex แก้แล้ว

แก้ `scripts/predict_prototype.py`

เพิ่ม schema normalization:

```text
is_non_http_target -> is_non_http_service
```

เพิ่ม unknown-product guard:

```text
ถ้า unknown_product_detected=1
และ unknown_family_signal_count >= known_family_signal_count
ให้บังคับ ranker decision เป็น unknown_family
```

ผลหลังแก้ เมื่อทดสอบกับ `unseen_drupal_01`:

```text
gate.decision = likely_exploitable
ranker.decision = unknown_family
final_decision = unknown_family_triage
recommended_next_action = unknown_family_scan_more_or_manual_triage
```

นี่คือ behavior ที่ถูกต้องกว่า เพราะ Drupal ไม่ได้อยู่ใน family ที่ runtime ranker รุ่นนี้รู้จัก

## การตีความผลล่าสุดแบบถูกต้อง

ควรพูดว่า:

```text
Unseen v02 ยืนยันว่า Gate เริ่มดีมากกับ negative/positive split ในชุดนี้ แต่ Ranker ยังต้องแก้ feature schema และเพิ่ม family-specific features ส่วน unknown-family ต้องใช้ guard ใน runtime เพื่อไม่ให้โมเดลเดา family ที่ไม่รู้จัก
```

ไม่ควรพูดว่า:

```text
ระบบทั้งหมดแม่น 100% แล้ว
```

## สถานะใช้งานจริงระดับ prototype

ตอนนี้ใช้ได้แบบระวัง:

| ส่วน | สถานะ |
| --- | --- |
| Gate | ใช้เป็นตัวคัดว่า `likely_exploitable/no_exploit/low_confidence` ได้ระดับ prototype |
| Family Ranker | ใช้ได้เฉพาะ family ที่มี evidence เฉพาะครบ |
| Unknown Guard | ต้องใช้ runtime ที่ patch แล้วเท่านั้น |
| Auto exploit | ยังไม่ควรยิงอัตโนมัติ ต้องเป็น Metasploit check/manual PoC หลัง user ยืนยัน |

## งานถัดไป

งานถัดไปไม่ควรเป็น “สแกนเพิ่มแบบกว้าง” ทันที แต่ควรเป็น:

1. ทำ feature schema alignment ให้ OpenCode ส่ง field ตรงกับ runtime
2. backfill family-specific features ให้ Redis/Grafana/Joomla/Tomcat/NextJS
3. rerun prediction ด้วย runtime ที่ patch แล้ว
4. ค่อย retrain ranker หลังข้อมูล schema ตรงกัน

เป้าหมายรอบถัดไป:

```text
Gate ต้องยังไม่มี FN
Unknown-family ต้องไม่หลุดเป็น ready_for_safe_verification
Ranker known-positive variants ต้อง Top-1 ดีขึ้นจาก 33.3%
```
