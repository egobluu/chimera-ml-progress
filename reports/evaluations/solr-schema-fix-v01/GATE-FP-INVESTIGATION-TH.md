# Gate False Positive Investigation

## สรุป

พบ false positive 4 targets จาก prediction CSV

| Target | Probability | เหตุผลหลัก |
| --- | ---: | --- |
| `solr_non_vulnerable` | 0.5879 | Solr Velocity is disabled but generic Solr/access signals pushed the score up |
| `solr_velocity_negative` | 0.6230 | Solr Velocity is disabled but generic Solr/access signals pushed the score up |
| `solr_negative_v04_1` | 0.8085 | Solr Velocity is disabled but generic Solr/access signals pushed the score up |
| `solr_negative_v04_2` | 0.8389 | Solr Velocity is disabled but generic Solr/access signals pushed the score up |

## วิธีอ่าน

False positive คือ target ที่ label เป็น negative แต่ Gate ทายว่า likely exploitable

ในรอบนี้ FP ทั้งหมดเกี่ยวกับ Solr และมี blocker สำคัญคือ `velocity_disabled=1`

## Recommendation

แก้ runtime/feature policy ให้ Solr ที่ velocity_disabled=1 และ velocity_enabled=0 ถูกลดเป็น low_confidence/no_exploit ก่อนส่งเข้า exploit verification
