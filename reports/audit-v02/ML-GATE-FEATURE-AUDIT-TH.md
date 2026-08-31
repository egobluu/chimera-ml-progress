# ML Gate Feature Audit

- dataset: `C:\Users\rapii\Desktop\kali-share\dataset\dec-ml-only-gate-v02-2026-08-31\target-exploitability-dataset.csv`
- targets: 40
- validated_positive: 20
- validated_negative: 20
- features: 44

## Feature Phase Count

- `conditional_precheck`: 31
- `postcheck_or_leak_risk`: 6
- `safe_basic_precheck`: 7

## จุดเสี่ยงที่ต้องระวัง

`postcheck_or_leak_risk` คือ feature ที่มักรู้หลังจากยิง Metasploit/manual PoC หรือหลังเขียนผลยืนยันแล้ว ถ้าเอาไปใช้ก่อนตัดสินใจจริง คะแนนจะสวยเกินจริง

| feature | direction | pos_nonzero | neg_nonzero | pos_avg | neg_avg |
| --- | --- | ---: | ---: | ---: | ---: |
| `negative_evidence_count` | negative_only | 0 | 20 | 0.0 | 3.25 |
| `rce_confirmed` | positive_only | 4 | 0 | 0.2 | 0.0 |
| `msf_check_confirmed` | positive_only | 10 | 0 | 0.5 | 0.0 |
| `msf_check_not_vulnerable` | negative_only | 0 | 6 | 0.0 | 0.3 |
| `manual_poc_failed` | negative_only | 0 | 5 | 0.0 | 0.25 |

## Feature ที่ใช้ได้แบบมีเงื่อนไข

กลุ่มนี้ใช้ได้ถ้าเกิดจาก scanner/probe ที่รันก่อน model ตัดสินใจ และต้องเก็บด้วยวิธีเดียวกันทุก target

| feature | direction | pos_nonzero | neg_nonzero | pos_avg | neg_avg |
| --- | --- | ---: | ---: | ---: | ---: |
| `version_in_vulnerable_range_true` | positive_only | 4 | 0 | 0.2 | 0.0 |
| `version_not_affected` | negative_only | 0 | 8 | 0.0 | 0.4 |
| `version_patched` | negative_only | 0 | 8 | 0.0 | 0.4 |
| `precondition_pass_count` | positive_only | 7 | 0 | 1.15 | 0.0 |
| `auth_required` | negative_only | 0 | 4 | 0.0 | 0.2 |
| `no_auth_required` | positive_only | 1 | 0 | 0.05 | 0.0 |
| `ajp_port_open` | positive_only | 1 | 0 | 0.05 | 0.0 |
| `ajp_port_closed` | negative_only | 0 | 1 | 0.0 | 0.05 |
| `anonymous_access` | positive_only | 2 | 0 | 0.1 | 0.0 |
| `velocity_enabled` | positive_only | 1 | 0 | 0.05 | 0.0 |
| `invokefunction_reachable` | positive_only | 1 | 0 | 0.05 | 0.0 |
| `invokefunction_not_found` | negative_only | 0 | 1 | 0.0 | 0.05 |
| `admin_party_enabled` | positive_only | 1 | 0 | 0.05 | 0.0 |
| `spring_not_detected` | negative_only | 0 | 1 | 0.0 | 0.05 |
| `wrong_software_type` | negative_only | 0 | 1 | 0.0 | 0.05 |
| `nuclei_no_vuln_found` | negative_only | 0 | 6 | 0.0 | 0.3 |
| `painless_sandbox_blocks` | negative_only | 0 | 1 | 0.0 | 0.05 |
| `path_traversal_blocked` | negative_only | 0 | 3 | 0.0 | 0.15 |

## ข้อสรุป

- ถ้าโมเดลได้ใช้ `negative_evidence_count`, `msf_check_confirmed`, หรือ `manual_poc_failed` ก่อนยิงจริง ผล 1.000 ยังถือว่าไม่พิสูจน์ความแม่น
- baseline ที่ควรวัดต่อคือ `strict_precheck`: ตัด postcheck/leak-risk features ออกก่อน train
- งานถัดไปคือทำ holdout target ใหม่ 5-10 ตัว โดยให้ model ทำนายก่อน แล้วค่อยใช้ Metasploit/manual PoC ตรวจคำตอบ
