# Quality Audit: Targeted Precondition Pair Probes

ไฟล์นี้สรุปผลตรวจคุณภาพจาก `dec-targeted-precondition-pairs-2026-08-31` ก่อนนำเข้า train ML

ข้อสรุปสำคัญ: **ยังไม่ควรนำ targeted pair รอบนี้เข้า train ตรง ๆ** เพราะมีหลาย target ที่ label กับ evidence ขัดกัน ถ้าเอาเข้า model จะทำให้ ML เรียนผิด

## ภาพรวม

| รายการ | จำนวน |
| --- | ---: |
| completed | 16 |
| skipped | 1 |
| timeout | 1 |
| feature records | 42 |
| positive features | 20 |
| negative features | 21 |

## แยกสถานะข้อมูล

| สถานะ | target | เหตุผล |
| --- | --- | --- |
| ใช้ได้บางส่วน | `tomcat_CVE-2017-12615` | ได้ `method_put_allowed=1` ตรงกับ CVE-2017-12615 |
| ใช้ได้บางส่วน | `redis_CVE-2022-0543` | ได้ `no_auth_required=1`, `lua_available=1` แต่ต้องมี version/packaging check เพิ่ม |
| ใช้ได้บางส่วน | `tomcat_non_vulnerable` | negative เดิมมี `method_put_rejected`, `ajp_port_closed` แต่รอบ pair ล่าสุด timeout ต้องใช้ evidence รอบ targeted v0.2 เดิมแทนหรือ re-run |
| ต้องตรวจซ้ำ | `thinkphp_5-rce` | positive แต่ได้ `invokefunction_not_found` และ `wrong_software_type` |
| ต้องตรวจซ้ำ | `solr_CVE-2019-17558` | positive แต่ได้ `velocity_disabled` |
| ต้องตรวจซ้ำ | `couchdb_CVE-2017-12635` | positive แต่ได้ `auth_required`, `config_blocked` |
| ต้องตรวจซ้ำ | `shiro_CVE-2016-4437` | positive แต่ได้ `rememberme_not_seen` |
| ต้องตรวจซ้ำ | `nginx_CVE-2017-7529` | positive แต่ได้ `version_patched=1` และเหมือน negative |
| ห้ามใช้ก่อนแก้ | `redis_non_vulnerable` | feature เหมือน `redis_CVE-2022-0543` เกินไป จึงแยก label ไม่ได้ |
| ห้ามใช้ก่อนแก้ | `redis_auth_non_vulnerable` | ได้ `no_auth_required=1` ทั้งที่ชื่อ target สื่อว่าควร auth block |
| ห้ามใช้ก่อนแก้ | `nginx_non_vulnerable` | feature เหมือน `nginx_CVE-2017-7529` เกินไป |

## ทำไมยังไม่ควร train

1. **positive บางตัวออก negative evidence**

   เช่น `thinkphp_5-rce` ควรได้ `invokefunction_reachable` แต่กลับได้ `invokefunction_not_found`

2. **positive/negative บางคู่ได้ feature เหมือนกัน**

   เช่น Redis positive และ Redis negative ได้ `no_auth_required` + `lua_available` เหมือนกัน ทำให้โมเดลไม่มีทางรู้ว่าตัวไหนควรเป็น exploit/no_exploit

3. **บาง feature ยังตีความ version ผิด**

   เช่น `nginx_CVE-2017-7529` และ `nginx_non_vulnerable` ต่างได้ nginx `1.13.2` แต่ตัวหนึ่งเป็น positive อีกตัวเป็น negative ต้องตรวจ mapping/affected range ใหม่

4. **feature บางตัวมีค่า string**

   เช่น `redis_version="5.0.7"` ต้องแปลงเป็น binary feature เช่น `redis_debian_lua_package_affected=1` หรือ `version_in_vulnerable_range_true=1`

## สิ่งที่ใช้ train ได้ทันที

ใช้ได้แบบระวัง:

- `tomcat_CVE-2017-12615`: `method_put_allowed=1`
- `tomcat_non_vulnerable`: `method_put_rejected=1` จาก targeted v0.2 เดิม ถ้า evidence ยังอยู่

คู่นี้เป็นตัวอย่างที่ดี เพราะ feature เป็นคู่ตรงกัน:

```text
method_put_allowed  -> positive
method_put_rejected -> negative
```

## สิ่งที่ต้องแก้ก่อน

### ThinkPHP

ต้องเปิด lab ให้ถูก endpoint แล้ว probe ควรได้:

```text
thinkphp positive: invokefunction_reachable=1
thinkphp negative: invokefunction_not_found=1
```

### Solr

ต้องเปิด Velocity ให้ตรงกับ lab CVE-2019-17558 แล้ว probe ควรได้:

```text
solr positive: velocity_enabled=1
solr negative: velocity_disabled=1
```

### CouchDB

ต้องแยกให้ชัดว่า CVE ที่ใช้ต้องการ admin party/config access แบบไหน แล้ว probe ควรได้:

```text
couchdb positive: admin_party_enabled=1 หรือ config_accessible=1
couchdb negative: auth_required=1 หรือ config_blocked=1
```

### Shiro

ต้องหา endpoint ที่ทำให้ Shiro set/ตอบ cookie behavior จริง แล้ว probe ควรได้:

```text
shiro positive: rememberme_deleteMe_seen=1
shiro negative: rememberme_not_seen=1
```

### Redis

ต้องมี feature ที่แยก Redis positive/negative ได้มากกว่า `lua_available`:

```text
redis_CVE-2022-0543: redis_debian_lua_package_affected=1
redis_non_vulnerable: version_patched=1 หรือ lua_sandbox_escape_not_applicable=1
redis_auth_non_vulnerable: auth_required=1
```

### Nginx

ต้องตรวจ affected range และ mapping ใหม่ก่อน:

```text
nginx positive: range_behavior_vulnerable=1
nginx negative: range_behavior_safe=1 หรือ version_patched=1
```

## ข้อสรุปสำหรับ ML

รอบนี้เป็นประโยชน์มาก เพราะเผยว่าปัญหาไม่ได้อยู่ที่ XGBoost อย่างเดียว แต่อยู่ที่ dataset consistency:

```text
ML จะเรียนได้ก็ต่อเมื่อ positive และ negative มี feature คู่เทียบที่ถูกต้อง
```

งานถัดไปไม่ใช่เพิ่ม target จำนวนมาก แต่คือแก้ 5 family ที่ evidence ขัดกับ label แล้ว re-run pair probes เฉพาะจุด
