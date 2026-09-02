# Runtime Hardening Next

เอกสารนี้บันทึกงานที่ต้องผ่านก่อนเอา ML ไปใช้กับ target จริง

## เกณฑ์ที่ต้องผ่าน

1. runtime ต้องรันได้จากเครื่องใหม่ด้วย `requirements.txt`
2. regression ชุดเดิมต้องผ่านทั้งหมด
3. stress validation ต้องผ่าน เพื่อกันเคส feature บาง, feature ขัดแย้ง, และ unknown product
4. target ที่เป็น negative/weak/unknown ต้องไม่ถูกปล่อยเป็น `ready_for_safe_verification`
5. target ที่เป็น known-positive และมี evidence เฉพาะ family ครบ ต้องยังถูก rank family ถูก

## ความหมายแบบใช้งานจริง

ถ้า stress validation ผ่าน แปลว่า runtime ยังไม่พร้อมยิง exploit จริงอัตโนมัติ แต่พร้อมใช้เป็นตัวกรองก่อนตรวจแบบปลอดภัย:

- อะไรหลักฐานไม่พอ ให้หยุดหรือเก็บ evidence เพิ่ม
- อะไรไม่รู้จัก family ให้เข้า unknown-family triage
- อะไร known family และ precondition ชัด ให้ค่อยส่งต่อ safe verification

## คำสั่งหลัก

```bash
python -m pip install -r requirements.txt
python scripts/run_runtime_regression.py
```
