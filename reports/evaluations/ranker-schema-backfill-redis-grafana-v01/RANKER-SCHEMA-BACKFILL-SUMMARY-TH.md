# RANKER-SCHEMA-BACKFILL-SUMMARY-TH.md

## สรุปผลการเก็บรวบรวมข้อมูล Schema-Aligned Backfill

### วัตถุประสงค์
แก้ไขจุดอ่อนของ Family Ranker โดยการเก็บรวบรวมข้อมูล Features ที่สอดคล้องกับ Runtime Schema สำหรับ Redis และ Grafana เท่านั้น

### เป้าหมายที่ตรวจสอบ

#### 1. Redis CVE-2022-0543
- **Target ID**: unseen_redis_variant_01
- **Expected Family**: redis
- **Expected Status**: validated_positive
- **Lab**: vulhub/redis:5.0.7

**หลักฐานที่พบ:**
- Redis service detected บนพอร์ต 6379
- INFO command ทำงานได้ (redis_version:5.0.7)
- Lua available (EVAL command ทำงาน)
- No auth required (PING ได้ PONG)
- Version in vulnerable range (5.0.7 ได้รับผลกระทบจาก CVE-2022-0543)

**Features ที่เก็บรวบรวม:**
- redis_detected=1
- redis_info_accessible=1
- lua_available=1
- no_auth_required=1
- auth_required=0
- version_in_vulnerable_range=1
- version_in_vulnerable_range_true=1
- version_in_vulnerable_range_false=0
- version_patched=0
- is_non_http_service=1
- open_port_count=1
- service_count=1

**ผลการตรวจสอบ:**
- Label Consistency: consistent
- Safe to Merge: true

#### 2. Grafana CVE-2021-43798
- **Target ID**: unseen_grafana_variant_01
- **Expected Family**: grafana
- **Expected Status**: validated_positive
- **Lab**: vulhub/grafana:8.2.6

**หลักฐานที่พบ:**
- Grafana detected บนพอร์ต 3000
- Version 8.2.6 (จาก /api/health)
- API health accessible (200 OK)
- Plugin path candidate found (/public/plugins/alertlist/)
- Public plugin path accessible (302 redirect)
- Path traversal candidate found และยืนยันแล้ว
- Path traversal works - อ่าน /etc/passwd ได้สำเร็จ
- No auth required สำหรับ vulnerable path

**Features ที่เก็บรวบรวม:**
- grafana_detected=1
- plugin_path_candidate_found=1
- public_plugin_path_accessible=1
- path_traversal_candidate_found=1
- path_traversal_blocked=0
- version_in_vulnerable_range=1
- version_in_vulnerable_range_true=1
- version_in_vulnerable_range_false=0
- version_patched=0
- auth_required=0
- no_auth_required=1
- is_http_target=1
- open_port_count=1
- http_port_count=1
- service_count=1
- endpoint_reachable_count=1

**ผลการตรวจสอบ:**
- Label Consistency: consistent
- Safe to Merge: true

### ผลรวม

| รายการ | จำนวน |
|--------|--------|
| เป้าหมายที่ตรวจสอบเสร็จ | 2/2 |
| Safe to Merge | 2 |
| Inconsistent/Quarantined | 0 |
| Feature records | 2 |
| Docker containers running | 0 |
| Disk usage | 96% (3.0G free) |

### ปัญหาที่พบ
- ไม่พบปัญหาในการเก็บรวบรวมข้อมูล
- ทั้ง Redis และ Grafana ทำงานได้ตามคาดหมาย
- Features ที่เก็บรวบรวมสอดคล้องกับ Runtime Schema

### หมายเหตุ
- การสำรวจนี้ใช้เวลาประมาณ 5 นาที
- ไม่ได้รัน ZAP หรือ full scans
- ใช้ timeout สำหรับทุก tool command
- ไม่มี container ค้างอยู่
