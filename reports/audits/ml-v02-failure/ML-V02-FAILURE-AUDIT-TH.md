# วิเคราะห์ว่า ML Gate v0.2 ยังพลาดตรงไหน

สรุปสั้น: คะแนน v0.2 ที่ได้ 1.000 ยังไม่ควรตีความว่าโมเดลแม่นจริงในงานใช้งานจริง เพราะ feature หลักที่โมเดลใช้มีลักษณะใกล้ผลตรวจหลังบ้านมากเกินไป โดยเฉพาะ `negative_evidence_count`, `msf_check_confirmed`, และ `nuclei_cve_confirmed`

## สิ่งที่โมเดลทำได้แล้ว

- แยก target ที่มี evidence ครบ 40 ตัวได้ดีมาก
- ลด false positive จาก v0.1 ได้จริงในชุดข้อมูลเดิม
- เริ่มมี schema ที่บอกเหตุผลได้ เช่น version, precondition, auth, endpoint, Metasploit check, nuclei match

## จุดที่ยังเสี่ยงพลาด

1. **Feature รู้ผลหลังตรวจแล้ว**

   `msf_check_confirmed`, `msf_check_not_vulnerable`, `rce_confirmed`, และ `manual_poc_failed` เป็นข้อมูลหลังจากตรวจ exploit แล้ว ถ้าเอาไปใช้เป็น input ก่อนตัดสินใจจริง จะกลายเป็น data leak

2. **`negative_evidence_count` แรงเกินไป**

   ใน v0.2 ค่า `negative_evidence_count` เป็น 0 ทุกตัวที่เป็น positive และมากกว่า 0 ทุกตัวที่เป็น negative ทำให้โมเดลแยก label ได้ง่ายมาก แต่ใน target ใหม่จริง ๆ เราอาจยังไม่มี negative evidence ครบแบบนี้

3. **จำนวน target ยังเล็ก**

   ตอนนี้ train/evaluate จาก 40 target ที่ validate แล้ว แม้จะสมดุล 20 positive / 20 negative แต่ยังน้อยสำหรับพิสูจน์ว่า generalize ข้าม software family ได้

4. **ยังไม่ได้วัดแบบ first-shot**

   วิธีวัดที่ควรใช้จริงคือให้ model ทำนายจาก scanner evidence ก่อน แล้วค่อยยิง Metasploit/manual PoC เพื่อเช็คว่าถูกไหม ถ้าใช้ evidence หลังยิงมาย้อน train/evaluate จะประเมินสูงเกินจริง

5. **feature บางตัวเป็น shortcut เฉพาะ lab**

   เช่น port, product, version หรือ nuclei template อาจทำให้ถูกใน Vulhub แต่ไม่พอสำหรับ target จริงที่ config ต่างออกไป

## นิยามระดับใช้งานพื้นฐาน

ระดับพื้นฐานที่ควรทำให้ถึงก่อนคือ:

- ใช้เฉพาะ precheck/scanner evidence แล้ว recall positive ได้อย่างน้อย 0.80
- false negative ต้องต่ำ เพราะไม่ควรพลาด target ที่น่าลอง exploit
- false positive ยอมมีได้บ้าง แต่ต้องอธิบายได้ว่าพลาดเพราะ evidence ไหนไม่พอ
- ทดสอบกับ holdout target ที่ไม่ได้ใช้ตอนสร้าง feature หรือจูน threshold

## แผนแก้

1. สร้าง profile `strict_precheck`
   - ตัด `tool_metasploit_success`
   - ตัด `msf_check_confirmed`
   - ตัด `msf_check_not_vulnerable`
   - ตัด `rce_confirmed`
   - ตัด `manual_poc_failed`
   - ตัดหรือแยก `negative_evidence_count` จนกว่าจะยืนยันว่าเกิดจาก probe อัตโนมัติจริง

2. เทรนและวัด 3 profile
   - `scanner_only`: naabu/nmap/httpx/nuclei/nikto/wapiti/curl fingerprint
   - `strict_precheck`: scanner + version/precondition ที่ probe ก่อนตัดสินใจ
   - `postcheck_feedback`: ใช้ Metasploit/manual result เพื่อเรียนรู้หลังตรวจ ไม่ใช้เป็น precheck score

3. ทำ first-shot validation
   - เลือก target ใหม่ 5-10 ตัว
   - ให้ model ทำนายก่อน
   - บันทึก top decision และ probability
   - ใช้ Metasploit/manual PoC ตรวจคำตอบ
   - เอาผลผิดกลับมาเพิ่ม dataset

4. เพิ่ม failure labels
   - `wrong_version`
   - `endpoint_missing`
   - `auth_required`
   - `module_not_applicable`
   - `scanner_timeout`
   - `manual_poc_failed`

## ข้อสรุปตอนนี้

ML ไม่ได้พัง แต่คะแนนปัจจุบันยังตอบไม่ได้ว่าใช้จริงแล้วแม่นแค่ไหน สิ่งที่ต้องทำต่อคือแยก feature ตามเวลาที่รู้ข้อมูล: ก่อนยิง, ระหว่าง probe, หลังยิง แล้ววัดใหม่ด้วย `strict_precheck` และ first-shot holdout
