# ขอบเขตงาน ML หลังเริ่มใช้ XGBoost Ranking

## เป้าหมายหลัก

เป้าหมายของงานฝั่ง ML คือสร้างระบบช่วยจัดลำดับการทดสอบช่องโหว่จากผล scanner โดยไม่ให้ระบบต้องลอง exploit แบบสุ่มหรือพึ่ง reasoning ของ agent อย่างเดียว

ระบบควรตอบได้ 2 คำถาม:

1. target นี้ควรถูกทดสอบ exploit ต่อหรือควรหยุดที่ `no_exploit`
2. ถ้าควร exploit ควรลอง exploit family ไหนก่อน

## เหตุผลที่เลือก XGBoost

เราเลือก XGBoost เพราะข้อมูลของโปรเจกต์เป็น tabular feature จาก scanner เช่น port, product, version, endpoint, precondition, nuclei result, Metasploit result

XGBoost เหมาะกับงานนี้เพราะ:

- ใช้กับข้อมูลตารางได้ดี
- train เร็ว
- ไม่ต้องใช้ dataset ใหญ่มากเท่า deep learning
- ดู feature importance ได้
- ทำ binary classification และ ranking ได้
- เหมาะกับ prototype ที่ต้องอธิบายผลให้อาจารย์เข้าใจ

## ทำไมไม่ใช้ LLM เป็นตัวตัดสินหลัก

LLM เหมาะกับการอธิบายผล, ช่วยอ่าน evidence, และช่วยวางแผน แต่ไม่เหมาะเป็นตัววัดเชิงสถิติหลักว่า exploit ไหนควรลองก่อน เพราะ:

- ผลอาจไม่คงที่ทุกครั้ง
- ยากต่อการวัด metric แบบ reproducible
- ยากต่อการเทียบ baseline
- อาจให้เหตุผลดูดีแต่ไม่ตรงกับ evidence จริง

ดังนั้น LLM ควรอยู่ในบทบาท assistant/explainer ส่วน ML ใช้เป็น ranking engine

## Architecture ที่เลือก

จากการทดลองพบว่าไม่ควรเอา `no_exploit` ไปแข่งกับ exploit family ใน candidate ranking โดยตรง เพราะ model จะสับสนระหว่าง “ไม่ควรยิง” กับ “ควรยิง family ไหน”

จึงเปลี่ยนเป็น 2-stage:

```text
Stage 1: Exploitability Gate
label 1 = validated_positive
label 0 = validated_negative

Stage 2: Family Ranker
ใช้เฉพาะ validated_positive
rank exploit family ที่ควรลองก่อน
```

## ขอบเขตที่ยังไม่ทำ

- ยังไม่ใช้กับ real-world target นอก lab
- ยังไม่ทำ online learning
- ยังไม่ทำ UI
- ยังไม่ผูกกับ LLM agent/co-op workspace เต็มระบบ
- ยังไม่สรุปว่าโมเดล generalize ได้จริงจนกว่าจะทดสอบ unseen target

