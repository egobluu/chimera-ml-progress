# Lessons Learned

## 1. คะแนน 1.000 ไม่ได้แปลว่าโมเดลเก่งเสมอ

ช่วงแรก XGBoost และ logic baseline ได้ Top-1 = 1.000 ทำให้ดูเหมือนแม่นมาก แต่จริง ๆ dataset เล็กและ feature ชี้คำตอบตรงเกินไป

บทเรียน:

```text
ต้องดู leakage, split method, failure analysis, และ baseline เสมอ
```

## 2. `no_exploit` ไม่ควรอยู่ใน candidate ranking เดียวกับ exploit family

เมื่อเอา `no_exploit` ไปแข่งกับ family เช่น `tomcat`, `redis`, `spring` model จะสับสน เพราะเป็นคนละชนิดของคำถาม

แก้โดยแยกเป็น:

```text
Gate: exploit/no_exploit
Ranker: family ranking
```

## 3. Negative target ต้องมี negative evidence

แค่บอกว่า target เป็น negative ไม่พอ ต้องมีหลักฐานว่าทำไมไม่ vulnerable เช่น:

- version patched
- endpoint missing
- auth required
- precondition fail
- Metasploit check not vulnerable
- scanner เจอแค่ fingerprint

## 4. Product match อย่างเดียวไม่พอ

ถ้า model เห็น `Redis` แล้วทาย exploit ทันที จะพลาดกับ `redis_non_vulnerable`

ต้องมี feature ที่บอกความแตกต่าง:

```text
Redis vulnerable: version/config/precondition ผ่าน
Redis non-vulnerable: auth required/version patched/precondition fail
```

## 5. Rule ยังมีประโยชน์ แต่ไม่ควรเป็นแกนสุดท้าย

Rule Gate ช่วยให้ prototype ปลอดภัยและอธิบายง่าย แต่เป้าหมายสุดท้ายคือ ML-first

แนวทาง:

```text
prototype: rule เป็น guardrail
final: ML เป็นตัวหลัก, rule เป็น sanity check
```

## 6. Feature coverage สำคัญกว่าจำนวน target แบบหลวม ๆ

v0.1 มี feature ครบแค่ 14/40 targets ทำให้ false positive สูง

v0.2 เติม gate feature ครบ 40/40 แล้วผลดีขึ้นทันที

บทเรียน:

```text
เพิ่ม target อย่างเดียวไม่พอ ต้องเพิ่ม feature ที่เทียบกันได้ทุก target
```

## 7. ขั้นต่อไปต้องทดสอบ unseen target

v0.2 ได้คะแนนเต็มบน dataset ปัจจุบัน แต่ยังต้องทดสอบกับ target ใหม่ที่ไม่อยู่ใน train

ถ้า unseen test ยังดี จึงค่อยบอกได้ว่าเริ่มใช้งานจริงระดับหนึ่ง

