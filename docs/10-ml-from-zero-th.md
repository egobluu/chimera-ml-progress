# เข้าใจ Chimera ML จากศูนย์

เอกสารนี้เขียนไว้สำหรับคนที่เริ่มจากศูนย์จริง ๆ อ่านแล้วควรเข้าใจว่า ML ในโปรเจกต์นี้คืออะไร ใช้ข้อมูลอะไร train model ทำงานยังไง ไฟล์แต่ละไฟล์มีไว้ทำอะไร metric แปลว่าอะไร และงานนี้จะถูกส่งต่อให้ LLM/agentic ยังไง

หลักการเขียนของเอกสารนี้คือใช้ภาษาคนก่อน แล้วค่อยใส่ชื่อในระบบไว้ในวงเล็บหรือ code block

## ภาพใหญ่ของงานนี้

โปรเจกต์นี้ไม่ได้สร้าง ML เพื่อ “แฮกแทนคน” แต่สร้าง ML เพื่อช่วยตัดสินใจก่อนว่า target ไหนควรตรวจต่อ และถ้าควรตรวจต่อควรเริ่มจาก exploit family ไหน

พูดง่าย ๆ:

```text
scanner เก็บหลักฐาน
ML ช่วยตัดสินว่า evidence พอไหม
LLM/agent อธิบายและวางแผนต่อ
คนหรือ policy layer เป็นคนอนุมัติก่อน verification จริง
```

flow ล่าสุด:

```text
Scanner / Feature Extractor
        ↓
Feature JSON
        ↓
Exploitability Gate
        ↓
Family Ranker
        ↓
Runtime Guard
        ↓
final_decision
        ↓
LLM / Operator
        ↓
Safe Verification / More Evidence / Stop
```

คำสำคัญ:

| ภาษาคน | ชื่อในระบบ |
| --- | --- |
| หลักฐานที่ scanner เก็บได้ | `features` |
| ตัวคัดกรองว่าน่าตรวจ exploit ต่อไหม | `Exploitability Gate` |
| ตัวจัดอันดับว่า exploit family ไหนน่าจะตรง | `Family Ranker` |
| กฎกันโมเดลมั่นใจเกินไป | `Runtime Guard` |
| คำตอบสุดท้ายให้ LLM อ่าน | `final_decision` |

## ทำไมต้องมี ML

scanner ปกติมักให้ข้อมูลเยอะ แต่ข้อมูลไม่ได้แปลว่า “ยิง exploit ได้จริง” เสมอไป

ตัวอย่าง:

```text
เจอ Redis service
เจอ version ที่ดูน่าสงสัย
แต่ต้อง auth หรือ Lua ใช้ไม่ได้
```

ถ้าใช้ rule ง่าย ๆ อาจเผลอบอกว่า Redis นี้น่ายิง exploit ทั้งที่หลักฐานยังไม่พอ

ML ในงานนี้จึงช่วยตอบ 2 คำถาม:

1. target นี้ “น่าตรวจ exploit ต่อไหม”
2. ถ้าน่าตรวจ ควรเริ่มจาก exploit family ไหน

แต่มันยังไม่ใช่ตัวพิสูจน์ว่ายิงสำเร็จจริง ต้องมี verification หลังจากนั้น

## ข้อมูลมาจากไหน

ข้อมูลเริ่มจาก lab target และผล scan ของแต่ละ target

ตัวอย่าง target:

```text
redis_positive_guard_01
grafana_negative_guard_01
solr_positive_guard_01
drupal_guard_01
redis_weak_guard_01
```

แต่ละ target จะมีหลักฐาน เช่น:

```text
service เป็นอะไร
version อยู่ในช่วงเสี่ยงไหม
endpoint เปิดไหม
ต้อง auth ไหม
มี blocker ไหม
มี feature เฉพาะ family ไหม
```

หลักฐานพวกนี้ถูกแปลงเป็นตัวเลขในไฟล์ feature

ตัวอย่างภาษาคน:

```text
Redis ถูกตรวจพบ
INFO endpoint เปิด
Lua ใช้ได้
ไม่ต้อง auth
version อยู่ในช่วง vulnerable
```

กลายเป็น:

```json
{
  "redis_detected": 1,
  "redis_info_accessible": 1,
  "lua_available": 1,
  "auth_required": 0,
  "no_auth_required": 1,
  "version_in_vulnerable_range": 1
}
```

ตัวเลข `1` แปลว่า “มี/จริง/พบ” และ `0` แปลว่า “ไม่มี/ไม่จริง/ไม่พบ”

## Label คืออะไร

ML ต้องเรียนจากตัวอย่างที่มีคำเฉลย คำเฉลยนี้เรียกว่า label

ในงานนี้ label หลักคือ:

| Label | ความหมาย |
| --- | --- |
| `validated_positive` | target นี้มีช่องโหว่จริงตาม family/scenario นั้น |
| `validated_negative` | target นี้ไม่ vulnerable ต่อ scenario นั้น |
| `no_exploit` | ไม่ควร exploit จากหลักฐานที่มี |
| `weak_no_exploit` | มีสัญญาณบาง ๆ แต่ยังไม่พอให้ exploit |
| `unknown_family` | target อาจมีช่องโหว่ แต่ไม่อยู่ใน family ที่ Ranker รู้จัก |

คำว่า `exploitable` ในงานนี้หมายถึง “มีเหตุผลพอให้เข้าสู่ขั้น safe verification” ไม่ได้แปลว่า “ยิงจริงสำเร็จแล้ว”

คำว่า `validated_positive` หมายถึง “ผ่านการยืนยันใน lab/report ว่าเป็น positive จริง” ไม่ใช่แค่ model ทำนายว่า positive

## Feature คืออะไร

Feature คือข้อมูลที่แปลงให้ model อ่านได้

มนุษย์อ่านแบบนี้:

```text
Tomcat เปิด PUT และมี path ที่น่าจะ upload JSP ได้
```

model อ่านแบบนี้:

```json
{
  "method_put_allowed": 1,
  "jsp_upload_candidate": 1,
  "version_in_vulnerable_range": 1
}
```

ในโปรเจกต์นี้ feature แบ่งได้คร่าว ๆ เป็น 4 กลุ่ม

| กลุ่ม | ความหมาย | ตัวอย่าง |
| --- | --- | --- |
| Basic scanner | สิ่งที่ scanner เห็นทั่วไป | `is_http_target`, `service_port` |
| Precondition | เงื่อนไขก่อน exploit | `auth_required`, `method_put_allowed` |
| Family-specific | หลักฐานเฉพาะ family | `lua_available`, `velocity_enabled` |
| Postcheck/leak-risk | หลักฐานหลังยิงหรือใกล้คำเฉลย | `msf_check_confirmed`, `rce_confirmed` |

สิ่งสำคัญ: model runtime ต้องใช้ feature ที่รู้ได้ก่อนยิง exploit เป็นหลัก เพราะถ้าใช้ผลหลังยิงมา train จะเหมือนแอบดูคำตอบ

## Precheck กับ Postcheck ต่างกันยังไง

Precheck คือหลักฐานที่เก็บได้ก่อนยิง exploit

ตัวอย่าง:

```text
version อยู่ในช่วง vulnerable
endpoint เปิด
ไม่ต้อง auth
PUT method เปิด
Lua ใช้ได้
Velocity enabled
```

Postcheck คือหลักฐานหลังจากลอง exploit/check แล้ว

ตัวอย่าง:

```text
Metasploit check confirmed
RCE confirmed
manual PoC success
```

ถ้าเอา postcheck ไป train model สำหรับ runtime จะทำให้คะแนนสวยเกินจริง เพราะตอนใช้งานจริงเรายังไม่มีคำตอบพวกนี้

ดังนั้น runtime รุ่นปัจจุบันใช้ profile ที่เน้น precheck:

```text
profile = precondition_only
```

## Dataset ที่ใช้ train คืออะไร

Dataset คือ table ที่รวม target หลายตัวไว้ด้วยกัน แต่ละแถวคือหนึ่ง target

หน้าตาประมาณนี้:

```text
target_id,label,auth_required,no_auth_required,lua_available,version_patched,...
redis_positive_01,1,0,1,1,0,...
redis_negative_01,0,1,0,0,0,...
```

สำหรับ Gate:

```text
label = 1 คือ positive/exploitable
label = 0 คือ negative/no_exploit
```

สำหรับ Ranker:

```text
ใช้เฉพาะ positive target
แล้วสร้าง candidate family หลายแถวต่อหนึ่ง target
family ที่ถูกต้องได้ label 1
family อื่นได้ label 0
```

## ทำไมต้องมี 2-stage model

ถ้ามี model ตัวเดียวที่ตอบทั้ง “ควรยิงไหม” และ “ยิงอะไร” จะสับสนง่าย เพราะ negative target ไม่มี exploit family จริง

เราเลยแยกเป็น 2 ขั้น:

1. Gate ตอบก่อนว่า target นี้ควรไปต่อไหม
2. Ranker ทำงานเฉพาะเมื่อ Gate บอกว่าน่าตรวจต่อ

ภาษาคน:

```text
อย่าให้ตัวจัดอันดับ exploit family ไปฝืนเลือก family ให้ target ที่จริง ๆ ไม่ควร exploit
```

## Model 1: Exploitability Gate

Gate คือ binary classifier แปลว่า model ที่ตอบได้สองฝั่ง

คำถามที่ Gate ตอบ:

```text
target นี้น่าตรวจ exploit ต่อไหม
```

ชื่อไฟล์ model:

```text
runtime/models/prototype/gate_precondition_only.json
```

ชนิด model:

```text
XGBClassifier
objective = binary:logistic
```

`binary:logistic` แปลว่า model คืนค่าเป็น score ระหว่าง 0 ถึง 1 คล้ายความน่าจะเป็นของฝั่ง positive

ตัวอย่าง:

```text
score = 0.93 แปลว่า model มองว่าน่าจะ exploitable สูง
score = 0.04 แปลว่า model มองว่ายังไม่น่า exploit
```

แต่ score ยังไม่ใช่คำตอบสุดท้าย ต้องเทียบกับ threshold

## Gate threshold คืออะไร

Threshold คือเส้นแบ่งว่า score เท่าไหร่ถึงจะถือว่า positive

ใน runtime ปัจจุบัน:

```text
threshold = 0.15
```

แปลว่า:

```text
score >= 0.15 → likely_exploitable
score ต่ำกว่านั้นมาก → no_exploit
score ใกล้ ๆ threshold → low_confidence
```

ทำไมไม่ใช้ 0.50 เหมือนที่คุ้น ๆ กัน

เพราะในงาน security เราไม่อยากพลาด positive จริงง่ายเกินไป จึงเลือก threshold จากผล evaluation โดยเรียงความสำคัญแบบนี้:

```text
False Negative น้อยก่อน
False Positive น้อยตามมา
F1 ดีตามมา
```

ใน code อยู่ที่:

```text
scripts/train_gate_profiles.py
choose_threshold()
```

## Model 2: Family Ranker

Ranker ไม่ได้ตอบว่า exploit ได้ไหม แต่ตอบว่า “ถ้าจะตรวจต่อ family ไหนควรมาก่อน”

ชื่อไฟล์ model:

```text
runtime/models/prototype/family_ranker.json
```

ชนิด model:

```text
XGBRanker
objective = rank:pairwise
```

`rank:pairwise` แปลว่า model เรียนรู้จากการเปรียบเทียบเป็นคู่ เช่น สำหรับ target Redis:

```text
redis ควรอยู่เหนือ grafana
redis ควรอยู่เหนือ tomcat_put
redis ควรอยู่เหนือ couchdb_auth
```

แล้วตอนใช้งานจริง model จะให้คะแนนทุก candidate family และเรียงอันดับ

ตัวอย่าง:

```json
[
  {"family": "redis", "score": 2.91},
  {"family": "joomla", "score": 0.43},
  {"family": "couchdb_auth", "score": -0.42}
]
```

อันดับหนึ่งคือ family ที่ควรตรวจต่อก่อน

## Candidate families คืออะไร

Candidate families คือรายชื่อ family ที่ Ranker รู้จักและเลือกได้

runtime ปัจจุบันรู้จัก 16 family:

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
redis
shiro_key
solr_velocity
struts2
thinkphp_rce
tomcat_ajp
tomcat_put
```

ถ้า target เป็น Drupal, Laravel, Jetty, WordPress, PHP-CGI หรือ JBoss รุ่นนี้ยังไม่ควรให้ Ranker ฝืนตอบว่าเป็น Redis/Grafana/Tomcat

จึงต้องมี unknown-family guard

## Unknown-family guard คืออะไร

ปัญหาของ Ranker แบบ closed-set คือมันต้องเลือกจาก family ที่รู้จักเสมอ

ถ้าเอา Drupal เข้าไป ทั้งที่ไม่มี Drupal ใน candidate families มันอาจฝืนตอบเป็น `nextjs` หรือ `joomla` เพราะต้องเลือกอะไรสักอย่าง

ดังนั้น runtime ต้องดูเพิ่มว่า:

```text
มี unknown product signal ไหม
known-family signal มีพอไหม
```

ถ้า unknown signal เด่นกว่า จะไม่เชื่อ family ที่ Ranker เลือก และส่งไป:

```text
final_decision = unknown_family_triage
```

ภาษาคน:

```text
ระบบบอกว่า target นี้อาจมีประเด็น แต่ไม่อยู่ใน family ที่ model รู้จัก อย่าฝืนยิง exploit family ผิด
```

## Runtime Guard คืออะไร

Runtime Guard คือกฎความปลอดภัยที่อยู่หลัง model

เหตุผลที่ต้องมี guard:

```text
model อาจเห็น signal บางส่วนแล้วมั่นใจเกินไป
score อาจสูงแต่มี blocker สำคัญ
Ranker อาจเลือก family ถูกแต่หลักฐานยังไม่ครบ
```

ตัวอย่าง guard ล่าสุด:

Redis weak/noisy:

```text
redis_detected = 1
lua_available = 0
known_family_signal_count = 0
```

ภาษาคน:

```text
เห็น Redis ก็จริง แต่ Lua ใช้ไม่ได้และ scanner บอกว่าสัญญาณ family ยังไม่พอ จึงไม่ควรบอกว่าพร้อมตรวจ exploit ต่อ
```

Grafana weak/noisy:

```text
grafana_detected = 1
path_traversal_blocked = 1
public_plugin_path_accessible = 0
```

ภาษาคน:

```text
เห็น Grafana ก็จริง แต่ path traversal ถูก block และเข้า plugin path ไม่ได้ จึงไม่ควรปล่อยเป็นพร้อมตรวจต่อ
```

## ไฟล์ model แต่ละตัวทำอะไร

`gate_precondition_only.json`

คือ model ของ Gate ใช้ตอบว่า target นี้น่าตรวจ exploit ต่อไหม

input:

```text
precheck features
```

output:

```text
score + decision
```

`family_ranker.json`

คือ model ของ Ranker ใช้จัดอันดับ exploit family

input:

```text
target features + candidate family features
```

output:

```text
ranked family list
```

`prototype_manifest.json`

คือไฟล์กำกับ runtime บอกว่า:

```text
ต้องโหลด model path ไหน
Gate ใช้ feature list อะไร
threshold เท่าไหร่
Ranker รู้จัก family อะไร
train targets กี่ตัว
metric ตอน train/evaluate ได้เท่าไหร่
entrypoint คือ script ไหน
```

ถ้าไม่มี manifest runtime จะไม่รู้ว่าต้องใช้ feature order แบบไหน

## ทำไม feature order สำคัญ

ML model ไม่ได้อ่านชื่อ feature แบบมนุษย์ตอน predict มันรับ array ตัวเลขตามลำดับ

ตัวอย่าง:

```text
[version_patched, auth_required, lua_available]
```

ถ้าตอน train ลำดับคือ:

```text
[version_patched, auth_required, lua_available]
```

แต่ตอน predict ส่งผิดเป็น:

```text
[lua_available, version_patched, auth_required]
```

model จะตีความผิดหมด

ดังนั้น `prototype_manifest.json` จึงเก็บ feature list ที่ถูกต้องไว้ให้ runtime ใช้

## scripts สำคัญ

`scripts/train_runtime_models.py`

ใช้ train runtime artifacts ชุดที่เอาไปใช้จริงระดับ prototype ได้แก่ Gate, Ranker และ manifest

`scripts/train_gate_profiles.py`

ใช้เทียบหลาย feature profile เพื่อดูว่า profile ไหนใช้จริงได้ และ profile ไหนเสี่ยง data leak

`scripts/train_family_ranker.py`

ใช้ train/evaluate Family Ranker โดยสร้าง candidate family rows และใช้ XGBoost ranking

`scripts/predict_prototype.py`

คือ entrypoint ตอนใช้งานจริง รับ feature JSON หนึ่ง target แล้วคืน JSON result ให้ LLM/operator อ่าน

`scripts/evaluate_runtime_predictions.py`

ใช้ทดสอบ runtime กับ validation set หลาย target แล้วสรุป metric เช่น Gate accuracy, Ranker Top-1, unknown rejection, safety flow

## วิธี train แบบภาพรวม

คำสั่ง train runtime prototype:

```bash
python scripts/train_runtime_models.py \
  --dataset reports/evaluations/ranker-schema-backfill-redis-grafana-v01/target-exploitability-family-ranking-backfill-plus-redis-grafana.csv \
  --out-dir runtime/models/prototype
```

ข้างใน script ทำงานแบบนี้:

```text
โหลด dataset
เลือก precondition_only features
ทำ leave-one-target-out evaluation ให้ Gate
เลือก threshold ที่เหมาะ
train Gate ด้วย dataset ทั้งหมด
save gate_precondition_only.json
โหลดเฉพาะ positive rows
สร้าง candidate family list
train Family Ranker
save family_ranker.json
เขียน prototype_manifest.json
```

พูดง่าย ๆ:

```text
ประเมินก่อนว่าการตั้งค่าโอเคไหม แล้วค่อย train model เต็มจากข้อมูลทั้งหมดเพื่อเอาไว้ใช้งาน
```

## Leave-one-target-out คืออะไร

เพราะ dataset ยังเล็ก ถ้าแบ่ง train/test แบบสุ่ม อาจได้ test set น้อยเกินไป

Leave-one-target-out ทำแบบนี้:

```text
รอบที่ 1: เอา target A ออกเป็น test, train ด้วยที่เหลือ
รอบที่ 2: เอา target B ออกเป็น test, train ด้วยที่เหลือ
รอบที่ 3: เอา target C ออกเป็น test, train ด้วยที่เหลือ
ทำจนทุก target เคยเป็น test
```

ข้อดี:

```text
ทุก target ได้ถูกทดสอบ
เหมาะกับ dataset เล็ก
เห็น failure ราย target
```

ข้อจำกัด:

```text
ถ้า target ใน dataset คล้ายกันมาก คะแนนยังอาจดูดีเกินจริง
ยังไม่แทน unseen validation จาก lab ใหม่
```

ใน code เรียก:

```text
LeaveOneOut
loo_predict()
```

## Metrics คืออะไร

สมมติ Gate ต้องทายว่า target เป็น positive หรือ negative

มีคำสำคัญ 4 ตัว:

| ชื่อ | ภาษาคน |
| --- | --- |
| TP | ของจริงเป็น positive และ model ทาย positive |
| FP | ของจริงเป็น negative แต่ model ทาย positive |
| TN | ของจริงเป็น negative และ model ทาย negative |
| FN | ของจริงเป็น positive แต่ model ทาย negative |

ตัวอย่างจาก runtime prototype:

```text
TP = 28
FP = 2
TN = 37
FN = 0
```

แปลว่า:

```text
จับ positive ได้ถูก 28 ตัว
เผลอมอง negative เป็น positive 2 ตัว
กัน negative ได้ถูก 37 ตัว
ไม่มี positive ตัวไหนหลุดเป็น negative
```

## Accuracy คำนวณยังไง

Accuracy คือทายถูกทั้งหมดหารด้วยจำนวนทั้งหมด

สูตร:

```text
accuracy = (TP + TN) / (TP + FP + TN + FN)
```

แทนค่า:

```text
(28 + 37) / (28 + 2 + 37 + 0)
= 65 / 67
= 0.9701
```

แปลว่า model ทายถูกประมาณ 97.01% ใน evaluation ชุดนั้น

## Precision คำนวณยังไง

Precision คือ “ที่ model บอกว่า positive นั้นถูกจริงกี่ส่วน”

สูตร:

```text
precision = TP / (TP + FP)
```

แทนค่า:

```text
28 / (28 + 2)
= 28 / 30
= 0.9333
```

แปลว่า ทุก 30 ครั้งที่ model บอกว่าน่าตรวจต่อ มี 28 ครั้งที่ถูก และ 2 ครั้งที่เป็น false positive

## Recall คำนวณยังไง

Recall คือ “positive จริงทั้งหมด model จับได้กี่ส่วน”

สูตร:

```text
recall = TP / (TP + FN)
```

แทนค่า:

```text
28 / (28 + 0)
= 1.0000
```

แปลว่าใน evaluation รอบนั้น positive จริงไม่หลุดเลย

สำหรับงาน security ค่า Recall สำคัญมาก เพราะ false negative คือช่องโหว่จริงที่ระบบมองข้าม

## F1 คำนวณยังไง

F1 คือค่าเฉลี่ยแบบ harmonic ระหว่าง Precision และ Recall

สูตร:

```text
F1 = 2 * precision * recall / (precision + recall)
```

แทนค่า:

```text
2 * 0.9333 * 1.0000 / (0.9333 + 1.0000)
= 0.9655
```

F1 ใช้ดูภาพรวมระหว่าง “ยิงเกินไหม” กับ “พลาดของจริงไหม”

## Ranker Top-1 คืออะไร

Top-1 คือ family อันดับแรกตรงกับคำตอบจริงไหม

ตัวอย่าง:

```text
target = redis_positive_01
true family = redis
ranker อันดับ 1 = redis
```

แบบนี้ Top-1 ถูก

ถ้าอันดับเป็น:

```text
อันดับ 1 = joomla
อันดับ 2 = redis
```

แบบนี้ Top-1 ผิด แต่ Top-3 อาจยังถูกถ้า Redis อยู่ใน 3 อันดับแรก

ใน runtime validation ล่าสุด:

```text
Known-positive Ranker Top-1 = 6/6
```

แปลว่า positive ที่อยู่ใน known family ทั้ง 6 ตัว Ranker เลือก family อันดับหนึ่งถูกหมดในชุด validation นั้น

## Ranker confidence คืออะไร

Ranker confidence ไม่ใช่ความน่าจะเป็นแท้ ๆ แต่เป็นการดูว่าอันดับหนึ่งชนะอันดับสองห่างพอไหม

ตัวอย่าง:

```text
อันดับ 1 redis score = 2.917933
อันดับ 2 joomla score = 0.433710
margin = 2.484223
```

ถ้า margin มากกว่าเกณฑ์:

```text
MIN_READY_RANKER_MARGIN = 0.25
```

จะถือว่าอันดับหนึ่งชนะชัด:

```text
ranker.confidence.level = clear_margin
```

ถ้า margin ต่ำกว่า 0.25:

```text
ranker.confidence.level = low_margin
```

ภาษาคน:

```text
model ลังเลระหว่าง family มากกว่าหนึ่งตัว อย่าเพิ่งเชื่ออันดับหนึ่งเต็มที่
```

## Family readiness คืออะไร

Family readiness คือการตรวจว่า family ที่ Ranker เลือกมีหลักฐานเฉพาะ family จริงไหม

ตัวอย่าง Redis พร้อม:

```text
redis_detected = 1
redis_info_accessible = 1
lua_available = 1
```

แบบนี้มีหลักฐานเฉพาะ Redis

ตัวอย่างที่ยังไม่พร้อม:

```text
version_in_vulnerable_range = 1
no_auth_required = 1
```

สองตัวนี้เป็น signal กว้าง ๆ เจอได้หลาย family จึงไม่พอให้มั่นใจว่าเป็น Redis/Grafana/Tomcat family ใด family หนึ่ง

ชื่อ field:

```text
ranker.family_readiness.ready
ranker.family_readiness.specific_positive_signals
ranker.family_readiness.blocking_negative_signals
```

ถ้า `ready=false` runtime จะไม่ปล่อยเป็น `ready_for_safe_verification`

## final_decision คืออะไร

`final_decision` คือคำตอบรวมที่ LLM ควรอ่านเป็นหลัก เพราะมันรวม Gate + Ranker + Guard แล้ว

| final_decision | ภาษาคน |
| --- | --- |
| `do_not_exploit_now` | ยังไม่ควร exploit ตอนนี้ |
| `needs_more_evidence` | หลักฐานยังไม่พอ ควร scan/probe เพิ่ม |
| `ready_for_safe_verification` | พร้อมเข้าสู่ safe verification แต่ยังต้องมี approval |
| `manual_triage_before_exploit` | มีสัญญาณบวกแต่ยังมี blocker/ความไม่มั่นใจ ต้องตรวจมือ |
| `unknown_family_triage` | target อาจมีประเด็นแต่ไม่อยู่ใน family ที่ model รู้จัก |

LLM ไม่ควรดูแค่ score เดี่ยว ๆ แล้วตัดสินเอง ควรดู `final_decision` ก่อน

## ตัวอย่าง runtime output

Input Redis positive:

```json
{
  "target_id": "redis_positive_example",
  "redis_detected": 1,
  "redis_info_accessible": 1,
  "lua_available": 1,
  "auth_required": 0,
  "no_auth_required": 1,
  "version_in_vulnerable_range": 1,
  "known_family_signal_count": 2,
  "unknown_family_signal_count": 0
}
```

Output สำคัญ:

```json
{
  "gate": {
    "score": 0.933099,
    "threshold": 0.15,
    "decision": "likely_exploitable"
  },
  "ranker": {
    "decision": "known_family_ready",
    "confidence": {
      "level": "clear_margin",
      "margin": 2.484223
    },
    "family_readiness": {
      "ready": true,
      "specific_positive_signals": [
        "lua_available",
        "redis_detected",
        "redis_info_accessible"
      ]
    }
  },
  "final_decision": "ready_for_safe_verification"
}
```

แปลภาษาคน:

```text
Gate บอกว่าน่าตรวจต่อ
Ranker เลือก Redis ชนะ family อื่นชัด
มีหลักฐานเฉพาะ Redis พอ
ดังนั้นพร้อมเข้าสู่ safe verification แต่ยังไม่ใช่ยิงอัตโนมัติ
```

## ตัวอย่าง weak/noisy

Input Redis weak:

```json
{
  "target_id": "redis_weak_guard_01",
  "redis_detected": 1,
  "redis_info_accessible": 1,
  "lua_available": 0,
  "known_family_signal_count": 0
}
```

ผลที่ต้องการ:

```text
final_decision = needs_more_evidence
หรือ manual_triage_before_exploit
```

ไม่ควรได้:

```text
final_decision = ready_for_safe_verification
```

เหตุผล:

```text
Redis service มีจริง แต่ evidence สำหรับ exploit path ยังไม่พอ โดยเฉพาะ Lua
```

นี่คือ failure ที่เจอจาก validation ล่าสุด และแก้ด้วย runtime guard แล้ว

## การ validation ล่าสุดบอกอะไร

ชุด `ranker-guard-unknown-validation-v01` มี 24 targets:

| กลุ่ม | จำนวน | ความหมาย |
| --- | ---: | --- |
| Known family | 12 | family ที่ model รู้จัก มีทั้ง positive/negative |
| Unknown family | 6 | exploit จริงแต่ family ไม่อยู่ใน candidate list |
| Weak/noisy | 6 | มี signal บางส่วนแต่ไม่ควร exploit |

ผลหลังแก้ guard:

```text
Gate TP / FP / TN / FN = 12 / 0 / 12 / 0
Known-positive Ranker Top-1 = 6/6
Unknown-family rejected = 6/6
Safety flow = 24/24
Strict flow = 24/24
```

แปลว่าในชุดนี้:

```text
positive ที่ควรเห็น เห็นครบ
negative/weak ไม่ถูกปล่อยไป exploit
unknown-family ไม่ถูกฝืนจัดเป็น known family
```

แต่ยังไม่ควรพูดว่า production-ready 100% เพราะยังเป็น validation set ขนาด 24 targets ที่ควบคุมเอง

## ทำไมไม่ควรเอา validation set ไป train ทับทันที

Validation set มีหน้าที่เป็นข้อสอบ

ถ้าเราเอาข้อสอบไปให้ model เรียนทันที แล้วค่อยสอบข้อเดิม คะแนนจะดูดีแต่ไม่บอกว่า model เข้าใจจริง

ดังนั้นชุดล่าสุดควรเก็บเป็น regression/validation set ก่อน:

```text
ใช้ตรวจว่าการแก้รอบต่อไปไม่ทำให้ behavior ถอย
ยังไม่เอาเข้า train ทับทันที
```

เมื่อมี validation ชุดใหม่เพิ่มพอ ค่อยตัดสินใจว่า target ไหนควรย้ายเข้า training dataset

## ML พร้อมต่อกับ LLM แค่ไหน

พร้อมต่อแบบ prototype decision-support แล้ว

แปลว่า LLM สามารถเรียก:

```text
scripts/predict_prototype.py
```

แล้วอ่าน output เพื่อ:

```text
อธิบายเหตุผล
แนะนำ scan เพิ่ม
แนะนำ safe verification
กัน unknown-family
กัน weak/noisy target
เขียน report
```

แต่ยังไม่พร้อมเป็น autonomous exploit runner

สิ่งที่ LLM ต้องเคารพ:

```text
ห้ามยิง exploit จริงอัตโนมัติ
อ่าน final_decision เป็นหลัก
ถ้า low confidence ให้เก็บ evidence เพิ่ม
ถ้า unknown-family ให้ triage ก่อน
ถ้า ready ต้องมี approval/policy ก่อน verification
```

## ไฟล์ที่ LLM/agent ควรใช้จริง

| ไฟล์ | หน้าที่ |
| --- | --- |
| `scripts/predict_prototype.py` | entrypoint inference |
| `runtime/models/prototype/gate_precondition_only.json` | Gate model |
| `runtime/models/prototype/family_ranker.json` | Ranker model |
| `runtime/models/prototype/prototype_manifest.json` | feature list, threshold, families |
| `runtime/README-TH.md` | คู่มือ runtime |
| `docs/09-llm-handoff-runtime-th.md` | วิธีส่งต่อให้ LLM |

ไฟล์ training/evaluation ไม่จำเป็นต้องเรียกทุกครั้งตอนใช้งานจริง

## สิ่งที่ scanner ต้องทำให้ดี

ML ดีได้เท่ากับ feature ที่ scanner ส่งมา

scanner ต้องพยายามส่ง field สำคัญเหล่านี้ให้ครบ:

```text
known_family_signal_count
unknown_family_signal_count
unknown_product_detected
auth_required
no_auth_required
version_in_vulnerable_range
version_patched
family-specific positive signals
family-specific blockers
```

ตัวอย่าง family-specific signals:

| Family | Signal สำคัญ |
| --- | --- |
| Redis | `redis_detected`, `redis_info_accessible`, `lua_available` |
| Grafana | `grafana_detected`, `public_plugin_path_accessible`, `path_traversal_candidate_found` |
| Solr | `solr_detected`, `solr_core_found`, `velocity_enabled`, `config_api_accessible` |
| Tomcat PUT | `method_put_allowed`, `jsp_upload_candidate` |
| Tomcat AJP | `ajp_port_open` |
| CouchDB | `admin_party_enabled`, `config_accessible`, `users_db_accessible` |

ถ้า scanner ส่งแต่ generic signal เช่น version หรือ endpoint อย่างเดียว Ranker อาจยังไม่พร้อม

## สิ่งที่ต้องระวังเรื่องชื่อ feature

บางรอบ OpenCode/scanner ใช้ชื่อไม่ตรงกับ runtime

ตัวอย่าง alias:

```text
admin_party -> admin_party_enabled
config_endpoint_accessible -> config_accessible
template_accessible -> velocity_template_accessible
velocity_template_accessible -> velocity_enabled
```

runtime normalize ให้บางส่วน แต่ระยะยาวควรทำให้ scanner ส่งชื่อ canonical ตั้งแต่แรก

## งานนี้เดินมายังไงแบบย่อ

ช่วงแรก:

```text
สร้าง Gate เพื่อแยก exploit/no_exploit
เจอปัญหา feature leak และ false positive
```

ช่วงกลาง:

```text
แยก strict/precondition profile
เพิ่ม negative controls
เพิ่ม positive controls
เริ่ม Family Ranker
```

ช่วงหลัง:

```text
พบว่า Ranker พลาด Redis/Grafana เพราะ feature เฉพาะ family ไม่ครบ
ทำ schema backfill
เพิ่ม unknown-family guard
เพิ่ม Solr schema fix
เพิ่ม Ranker safety guard
ทดสอบ multi-family unseen และ unknown/weak validation
```

ตอนนี้:

```text
runtime prototype ใช้งานเป็น decision-support ได้
มี guard กัน unknown-family และ weak/noisy ดีขึ้น
ยังต้องต่อ feature extractor จริงและทำ validation เพิ่มก่อน production
```

## งานถัดไปที่ควรทำ

ลำดับที่แนะนำ:

1. ต่อ scanner feature extractor ให้ส่ง JSON ตาม `runtime/README-TH.md`
2. ทำ integration test แบบ end-to-end จาก target จริงถึง `final_decision`
3. เก็บ unknown-family และ weak/noisy เพิ่มจากหลาย product
4. แยก validation set กับ training set ให้ชัด
5. เพิ่ม report อัตโนมัติให้ LLM อธิบาย `reason_features`, `schema_warnings`, `family_readiness`
6. ค่อย retrain เมื่อมีข้อมูลใหม่มากพอและยังเก็บ validation set ไว้ทดสอบหลัง train

## สรุปแบบจำง่าย

โปรเจกต์นี้มี ML เพื่อช่วยตัดสินใจ ไม่ใช่เพื่อกด exploit แทนคน

Gate ตอบ:

```text
ควรตรวจต่อไหม
```

Ranker ตอบ:

```text
ถ้าตรวจต่อ ควรเริ่มจาก family ไหน
```

Guard ตอบ:

```text
โมเดลมั่นใจเกินไปหรือเปล่า หลักฐานพอจริงไหม target เป็น unknown-family ไหม
```

LLM ควรใช้:

```text
final_decision
ranker.confidence
ranker.family_readiness
reason_features
schema_warnings
```

และต้องจำไว้เสมอ:

```text
ready_for_safe_verification ไม่เท่ากับ exploit สำเร็จ
มันแปลว่า evidence พอสำหรับขั้นตรวจยืนยันแบบปลอดภัยภายใต้ approval เท่านั้น
```

