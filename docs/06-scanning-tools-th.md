# เครื่องมือสแกน: แยกงานจริงกับงานเก็บ Dataset

เอกสารนี้แยกเครื่องมือออกเป็น 2 กลุ่ม เพราะ “เครื่องมือที่ใช้ในโปรแกรมจริง” กับ “เครื่องมือที่ใช้เก็บ dataset เพื่อ train ML” ไม่จำเป็นต้องเหมือนกันทั้งหมด

## หลักคิด

งานจริงต้องเร็ว คุมง่าย และไม่สร้างภาระเครื่องมากเกินไป ส่วนงานเก็บ dataset ต้องละเอียดกว่า เพราะต้องเก็บ evidence ให้ ML เรียนรู้ว่าอะไรทำให้ target vulnerable หรือไม่ vulnerable

```text
งานจริง = ใช้เท่าที่จำเป็นเพื่อช่วยตัดสินและจัดอันดับ
งาน dataset = ใช้มากขึ้นเพื่อเก็บ feature, label, evidence และ failure case
```

## เครื่องมือที่ใช้ในตัวโปรแกรมจริง

กลุ่มนี้คือ core runtime scanner ที่ควรใช้เมื่อระบบถูกนำไปใช้งานจริงหรือ demo workflow

| เครื่องมือ | หน้าที่ | เหตุผลที่ใช้จริง |
| --- | --- | --- |
| `naabu` | หา port เปิด | เร็ว เหมาะเป็นด่านแรก |
| `nmap -sT -Pn` | TCP connect scan/service hint | ใช้ได้แม้ raw socket จำกัด |
| `httpx-toolkit` | HTTP probe, status, title, header, tech | สร้าง feature พื้นฐานให้ Gate/Ranker |
| `nuclei` | CVE/fingerprint/misconfig scan | ให้ scanner signal ที่เข้มกว่า HTTP probe |
| `curl` / manual probe | endpoint/precondition probe | ใช้ทดสอบเงื่อนไขเฉพาะแบบควบคุมได้ |
| `msfconsole` | Metasploit search/check/run เฉพาะ lab ที่ได้รับอนุญาต | เป็น verification feedback สำคัญของโปรเจกต์ |
| `redis-cli` | Redis-specific probe | Redis ไม่ใช่ HTTP target ต้องใช้ protocol tool |
| `jq` | ตรวจ JSONL/สรุป count | ทำให้ output ตรวจซ้ำได้และลด schema พัง |

## เครื่องมือที่ใช้เสริมในงานจริงเฉพาะบาง target

| เครื่องมือ | ใช้เมื่อไหร่ | เหตุผล |
| --- | --- | --- |
| `nikto` | web server target | เพิ่ม web server vulnerability evidence |
| `wapiti` | web app target ที่ต้องดู behavior | เพิ่ม web application behavior signal |
| `sqlmap` | target มี parameter น่าสงสัย | ใช้เฉพาะ SQLi candidate เพื่อลด noise |
| `katana` | ต้อง crawl หา endpoint/API | ช่วยหา route ที่ scanner ปกติไม่เห็น |
| `ffuf` หรือ `feroxbuster` | ต้อง fuzz path/endpoint | ช่วยหา admin/API/upload/hidden path |
| `WhatWeb` หรือ `Wappalyzer` | fingerprint ยังไม่ชัด | ช่วยยืนยัน product/framework/version |
| `testssl.sh` หรือ `tlsx` | HTTPS/TLS target | เก็บ TLS/protocol/certificate feature |

## เครื่องมือที่ใช้เก็บ Dataset

กลุ่มนี้ใช้ตอน build dataset และ train ML เพราะต้องการ evidence ลึกกว่า runtime จริง

### Network Scanning

| เครื่องมือ | ใช้ทำอะไร | ไฟล์ผลลัพธ์ |
| --- | --- | --- |
| `naabu` | สแกน port เปิด | `raw/naabu.txt` |
| `nmap -sT -Pn` | สแกน port + service detection แบบไม่ใช้ raw socket | `raw/nmap.txt` |

### HTTP Analysis

| เครื่องมือ | ใช้ทำอะไร | ไฟล์ผลลัพธ์ |
| --- | --- | --- |
| `httpx-toolkit` | HTTP response, header, title, status, tech | `raw/httpx.txt` |
| `nuclei` | CVE, fingerprint, misconfiguration | `raw/nuclei.txt` หรือ `raw/nuclei.jsonl` |
| `nikto` | web server vulnerability scan | `raw/nikto.txt` |
| `wapiti` | web application vulnerability scan | `raw/wapiti.txt` |
| `curl` | manual PoC / endpoint / precondition | `raw/manual_poc.txt`, `raw/curl_root.txt` |
| `katana` | crawl endpoint, JS route, forms | `raw/katana.jsonl` |
| `ffuf` / `feroxbuster` | directory/path fuzzing | `raw/ffuf.json`, `raw/feroxbuster.json` |
| `WhatWeb` / `Wappalyzer` | technology fingerprint | `raw/whatweb.json`, `raw/wappalyzer.json` |

### Exploitation / Validation

| เครื่องมือ | ใช้ทำอะไร | ไฟล์ผลลัพธ์ |
| --- | --- | --- |
| `msfconsole` | Metasploit module search/check/run | `raw/msf_search.txt`, `raw/msf_check.txt`, `raw/metasploit_behavior.txt` |
| `sqlmap` | SQL injection testing | `raw/sqlmap.txt` |
| `redis-cli` | Redis-specific testing | `raw/redis_info.txt`, `raw/redis_lua_probe.txt` |

### Custom Probes

| ไฟล์ | ใช้ทำอะไร |
| --- | --- |
| `raw/version_behavior.txt` | software/version fingerprint |
| `raw/precondition_probe.txt` | exploit precondition เช่น auth, endpoint, method |
| `raw/rce_test.txt` | safe RCE confirmation ใน local lab |
| `raw/ajp_probe.txt` | AJP/Ghostcat check |
| `raw/auth_behavior.txt` | auth required/no auth required |
| `raw/api_behavior.txt` | API endpoint behavior |
| `raw/error_behavior.txt` | error signature |
| `raw/http_methods.txt` | HTTP method เช่น PUT/DELETE/OPTIONS |
| `raw/exploit_check_behavior.txt` | exploit endpoint reachability |

## เครื่องมือที่ไม่ควรใช้เป็น default runtime

| เครื่องมือ | เหตุผล |
| --- | --- |
| OpenVAS/GVM | หนัก ช้า กิน disk เหมาะ deep scan/report มากกว่า loop ML |
| ZAP full scan | ดีแต่หนัก ควรใช้เฉพาะ selected target |
| Amass/Subfinder | เหมาะ real domain recon แต่ Vulhub local ไม่ค่อยจำเป็น |
| Trivy | ดีสำหรับ container/image CVE แต่ sudo ถูกบล็อก และไม่ใช่แกนหลักตอนนี้ |

## Pipeline ที่แนะนำ

### Runtime จริง

```text
target input
  -> naabu/nmap
  -> httpx-toolkit
  -> nuclei
  -> curl/custom precondition probes
  -> ML-only Gate
  -> XGBoost Family Ranker
  -> Metasploit/manual verification
```

### Dataset collection

```text
Vulhub Docker Lab
  -> naabu/nmap
  -> httpx-toolkit + WhatWeb/Wappalyzer
  -> katana + ffuf/feroxbuster
  -> nuclei + nikto + wapiti
  -> custom version/precondition probes
  -> msfconsole/sqlmap/redis-cli/manual PoC
  -> JSONL evidence
  -> XGBoost training
```

## สรุป

เครื่องมือที่ควรเพิ่มก่อนเพื่อให้ ML แม่นขึ้นคือ:

```text
katana
ffuf หรือ feroxbuster
WhatWeb หรือ Wappalyzer
jq
```

เพราะช่วยเพิ่ม feature ที่ model ต้องการจริง:

- endpoint reachable/missing
- auth required/no auth
- product/version confidence
- scanner fingerprint vs confirmed CVE
- precondition pass/fail
- negative evidence

