# Profile Audit v0.2

รอบนี้ทดสอบว่า ML Gate v0.2 ยังแม่นอยู่ไหมเมื่อถอด feature ที่เสี่ยงเป็น data leak ออก โดยใช้ leave-one-out evaluation บน dataset 40 targets เดิม

## ผลเทียบ profile

| profile | features | threshold | accuracy | precision | recall | f1 | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full_v02` | 44 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 |
| `strict_precheck` | 38 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 0 |
| `strict_no_negative_count` | 43 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 0 |
| `scanner_only` | 8 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 0 |
| `no_metasploit` | 40 | 0.20 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 |
| `no_nuclei_confirm` | 43 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 |

## อ่านผลยังไง

`full_v02` ได้ 1.000 เพราะใช้ feature ครบทุกตัว รวมถึง feature หลังตรวจ เช่น `negative_evidence_count`, `msf_check_confirmed`, `manual_poc_failed`

`strict_precheck` ตัด feature เสี่ยงออกแล้วเหลือ accuracy 0.500 และ false positive 20 ตัว แปลว่าโมเดลยังแยก target ที่ไม่ควร exploit ไม่ได้ ถ้าไม่มี negative evidence ที่แข็งมาก

`strict_no_negative_count` ตกเท่า `strict_precheck` แปลว่า `negative_evidence_count` เป็น feature สำคัญที่สุดของ v0.2 และมีโอกาสเป็น shortcut ของ label

`no_metasploit` ยังได้ 1.000 เพราะถึงตัด Metasploit ออก แต่ยังเหลือ `negative_evidence_count` อยู่ จึงยังแยก negative ได้ง่าย

## จุดที่ ML พลาดจริงตอนนี้

1. โมเดลยังมีนิสัย “เห็นหลักฐานไม่พอแล้วเลือก exploit ไว้ก่อน”
2. โมเดลยังไม่มี negative pattern ที่เกิดจาก scanner ธรรมดามากพอ
3. `negative_evidence_count` มีพลังเกินไป เพราะตอนนี้ negative มีค่าทุกตัว แต่ positive ไม่มีเลย
4. ถ้าเจอ target ใหม่ที่ scan ไม่ครบหรือไม่มี custom negative probe โมเดลอาจ false positive สูง

## สิ่งที่ต้องทำให้ใช้จริงระดับพื้นฐาน

1. ทำ `negative_evidence_count` ให้แตกเป็น feature ย่อยที่ตรวจซ้ำได้ เช่น `version_patched`, `auth_required`, `endpoint_missing`, `method_rejected`
2. บังคับให้ทุก target ทั้ง positive และ negative มี probe ชุดเดียวกัน ไม่ใช่เติมเฉพาะตัวที่เคยพลาด
3. train `strict_precheck` ใหม่หลังจากมี negative scanner evidence ที่สมดุล
4. ทำ first-shot validation กับ target ใหม่ 5-10 ตัว โดย model ต้องทำนายก่อน Metasploit/manual PoC

## ข้อสรุป

คะแนน 1.000 ของ v0.2 ใช้เป็นหลักฐานว่า pipeline ทำงานครบได้ แต่ยังไม่ใช่หลักฐานว่า ML ใช้งานจริงแม่นแล้ว เป้าหมายถัดไปคือทำให้ `strict_precheck` ดีขึ้น เพราะ profile นี้ใกล้สถานการณ์ใช้งานจริงที่สุด
