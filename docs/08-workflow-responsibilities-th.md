# หน้าที่การทำงานของแต่ละส่วน

เอกสารนี้อธิบายว่าในโปรเจกต์นี้แต่ละส่วนทำงานอะไร เพื่อไม่ให้เอาหน้าที่ของ scanner, ML, Metasploit, Codex และ OpenCode ไปปนกัน

## ภาพรวม workflow

```text
Vulhub target
  -> scanner/precheck probes
  -> feature dataset
  -> ML Gate / XGBoost Ranking
  -> Metasploit/manual validation
  -> feedback กลับไปแก้ dataset
```

## OpenCode ฝั่ง Kali

หน้าที่หลักคือ “เก็บหลักฐานจาก target”

ทำ:

- เปิด Vulhub lab ทีละตัว
- รัน scanner/probe ตาม scope
- เก็บ raw evidence
- เขียน JSONL feature
- ใช้ Metasploit/manual validation เมื่อรอบงานต้องการเฉลย
- sync output กลับ shared folder
- ปิด Docker ให้สะอาด

ไม่ทำ:

- ไม่ train ML
- ไม่ claim metric
- ไม่แก้ repo GitHub หลัก
- ไม่เปลี่ยน label เองถ้ายังไม่มี evidence ชัด

## Codex ฝั่งนี้

หน้าที่หลักคือ “ตรวจคุณภาพข้อมูลและทำ ML pipeline”

ทำ:

- ตรวจ schema
- merge dataset
- แยก precheck/postcheck/leak-risk
- train/evaluate XGBoost
- วิเคราะห์ false positive/false negative
- เขียนรายงานภาษาไทย
- อัป repo ความคืบหน้า
- เขียน prompt ให้ OpenCode ทำ scan/probe รอบถัดไป

ไม่ทำ:

- ไม่ควบคุม Kali ถ้า VM ไม่พร้อม
- ไม่เอา output ที่ label/evidence ขัดกันเข้า train
- ไม่ใช้ postcheck feature เป็น input ตอน precheck

## Scanner / Precheck

`precheck` คือข้อมูลที่รู้ได้ก่อนยิง exploit จริง ใช้เป็น input ให้ ML ได้

ตัวอย่าง:

- port เปิดไหม
- software/version คืออะไร
- endpoint สำคัญมีไหม
- auth block ไหม
- method ถูก reject ไหม
- AJP เปิดไหม
- Velocity/Actuator/Invokefunction เปิดไหม

เครื่องมือ:

- `nmap -sT -Pn`
- `naabu`
- `httpx-toolkit`
- `nuclei`
- `whatweb`
- `curl`
- `ffuf`
- probe เฉพาะ family

## ML Gate

ML Gate ตอบคำถาม:

```text
target นี้ควรไปลอง exploit ต่อไหม
```

output ที่ต้องการ:

- `exploit`
- `no_exploit`
- probability/score
- เหตุผลจาก feature สำคัญ

เป้าหมายตอนนี้:

- ลด false positive โดยไม่เพิ่ม false negative มากเกินไป
- ใช้เฉพาะ precheck feature
- ไม่พึ่ง `negative_evidence_count` แบบรวมก้อน

## XGBoost Ranking

XGBoost Ranking ใช้หลัง Gate หรือร่วมกับ Gate เพื่อจัดอันดับ exploit family

ตัวอย่าง:

```text
1. tomcat
2. spring
3. nginx
```

Ranking ต้องมี candidate family เพราะโมเดลต้องเปรียบเทียบว่า family ไหนเหมาะกับ evidence มากที่สุด

## Metasploit / Manual Validation

Metasploit ใช้เป็น “เฉลยหลัง ML ทำนายแล้ว”

ใช้เพื่อ:

- ยืนยันว่า exploit ได้จริง
- ยืนยันว่า exploit ไม่ได้
- เก็บ postcheck evidence
- feedback กลับไปปรับ dataset

ห้ามใช้ผล Metasploit เป็น input precheck เช่น:

- `msf_check_confirmed`
- `msf_check_not_vulnerable`
- `rce_confirmed`
- `manual_poc_failed`

เพราะถ้าใช้ก่อนทำนาย จะกลายเป็นการเอาเฉลยให้ ML ก่อนสอบ

## Quarantine

ถ้า target มี label กับ evidence ขัดกัน ต้องแยกไว้ก่อน

ตัวอย่าง:

- target เป็น `validated_positive` แต่ probe ได้ `velocity_disabled`
- target เป็น `validated_positive` แต่ probe ได้ `invokefunction_not_found`
- positive และ negative ได้ feature เหมือนกันจนแยกไม่ได้

ข้อมูลแบบนี้ต้องเข้า `reports/quarantine/` และยังไม่ควร train จนกว่าจะ recheck

## หลักคิดรอบถัดไป

ไม่ต้องเพิ่ม target เยอะก่อน แต่ต้องเพิ่ม feature ที่เป็นคู่เทียบ:

```text
method_put_allowed   vs method_put_rejected
ajp_port_open        vs ajp_port_closed
velocity_enabled     vs velocity_disabled
invokefunction_found vs invokefunction_not_found
spring_detected      vs spring_not_detected
auth_required        vs no_auth_required
```

ML จะเริ่มเรียนได้จริงเมื่อมีทั้งฝั่งที่ exploit condition ผ่านและฝั่งที่ fail ใน family เดียวกัน
