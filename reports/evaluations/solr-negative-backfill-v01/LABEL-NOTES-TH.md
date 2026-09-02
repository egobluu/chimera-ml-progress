# dec-solr-negative-backfill-2026-09-02

## ผลรวม
- Targets: 2
- Safe to merge: 2
- Quarantined: 0

## Targets

### solr_negative_v04_1
- Source: solr:9.7.0
- Expected: validated_negative
- Features: 27
- Safe to merge: true

### solr_negative_v04_2
- Source: vulhub/solr:8.2.0
- Expected: validated_negative
- Features: 27
- Safe to merge: true

## หมายเหตุ
- Solr 9.7.0: ไม่มี VelocityResponseWriter (ลบออกจาก Solr 9.x)
- Solr 8.2.0: มี VelocityResponseWriter ใน default config แต่ลบออกแล้ว
- ทั้ง 2 targets มี core ที่สร้างสำเร็จ
- Config API สามารถเข้าถึงได้ทั้งคู่
