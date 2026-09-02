# LLM Decision Explainer

เอกสารนี้คือชั้นต่อจาก ML runtime

ภาษาคน:

```text
ML คืน JSON ที่มี score/decision เยอะ
LLM ต้องเอา JSON นั้นไปอธิบายให้คนเข้าใจและเลือก next action อย่างปลอดภัย
```

สคริปต์:

```text
scripts/explain_runtime_decision.py
```

input:

```text
examples/output/*_prediction.json
```

policy:

```text
runtime/llm-action-policy.json
```

output:

```text
Markdown report สำหรับ operator
JSON summary สำหรับ LLM/agent
```

## วิธีใช้

```powershell
$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py scripts\explain_runtime_decision.py `
  --prediction examples\output\redis_likely_exploitable_prediction.json `
  --policy runtime\llm-action-policy.json `
  --out-md examples\output\redis_likely_exploitable_explanation.md `
  --out-json examples\output\redis_likely_exploitable_explanation.json
```

## Output ที่ต้องดู

สคริปต์จะสรุป:

- target id
- `final_decision`
- ความหมายภาษาไทย
- ต้องขอ approval ไหม
- run safe verification ได้ไหม
- run exploit ได้ไหม
- Gate score/threshold/decision
- Ranker confidence/readiness
- top families
- reason features
- schema warnings
- allowed actions จาก policy

## ทำไมต้องมี

เพราะ LLM ไม่ควรอ่าน score แล้วตัดสินเอง

สิ่งที่ถูกคือ:

```text
ML runtime ตัดสินเชิง model
LLM decision explainer แปลผลตาม policy
operator/user เป็นคน approve ขั้น verification
```

## กฎสำคัญ

```text
final_decision เป็น field หลัก
score เป็นข้อมูลประกอบ
schema_warnings ต้องพูดถึงเสมอถ้ามี
family_readiness.ready=false ห้าม claim ว่า family พร้อม
may_run_exploit=false ทุก decision ใน prototype ตอนนี้
```

