# Runtime Stress Validation v01

ชุดนี้เอาไว้ทดสอบว่า runtime ML จะไม่มั่นใจเกินไปเมื่อเจอ target ที่ข้อมูลยังบางหรือขัดแย้งกัน

เป้าหมายไม่ใช่ทำ accuracy ให้สวย แต่คือกันเคสอันตรายก่อนเอาไปใช้กับโลกจริง:

- unknown product ที่มีแค่ generic web signal ต้องไป `unknown_family_triage`
- Redis ที่เห็นแค่ banner/version แต่ไม่มี Lua/info evidence ต้องไม่พร้อม verify
- Grafana ที่เห็นแค่ version แต่ไม่มี plugin/path traversal evidence ต้องไม่พร้อม verify
- Tomcat PUT ที่มี signal บวกแต่ upload ถูก block ต้องไม่พร้อม verify
- Solr ที่เจอ core แต่ Velocity/config ถูก block ต้องไม่พร้อม verify
- known-positive ที่ evidence ครบต้องยังผ่านได้

Regression suite นี้ควรผ่านก่อนเริ่มเอา target จริงเข้ามาเพิ่ม
