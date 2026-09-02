# Runtime Decision Explanation

## สรุป

| Field | Value |
| --- | --- |
| target | `example_unknown_wordpress_plugin` |
| final decision | `unknown_family_triage` |
| ความหมาย | target อาจมีประเด็น แต่ไม่อยู่ใน family ที่ Ranker รู้จัก |
| recommended next action | `unknown_family_scan_more_or_manual_triage` |
| requires user approval | yes |
| may run safe verification | no |
| may run exploit | no |

## Gate

| Field | Value |
| --- | --- |
| decision | `likely_exploitable` |
| score | `0.884658` |
| threshold | `0.15` |

## Ranker

| Field | Value |
| --- | --- |
| decision | `unknown_family` |
| confidence | `clear_margin` |
| margin | `0.53496` |
| family ready | `False` |
| readiness reason | scanner ระบุว่า known-family signal ยังไม่พอ จึงไม่ควรถือว่าพร้อมตรวจต่ออัตโนมัติ |

## Top Families

| Family | Score | Positive signals | Negative signals | Specific positive |
| --- | ---: | ---: | ---: | ---: |
| nextjs | -0.084027 | 1 | 0 | 0 |
| flask | -0.618987 | 1 | 0 | 0 |
| jenkins | -0.618987 | 1 | 0 | 0 |
| nexus | -0.618987 | 1 | 0 | 0 |
| struts2 | -0.618987 | 1 | 0 | 0 |

## Reason Features

- `endpoint_reachable_count`
- `has_positive_precondition_signal`
- `is_http_target`
- `login_path_found`
- `service_port`
- `unknown_family_signal_count`
- `unknown_product_detected`
- `upload_path_found`
- `whatweb_tech_detected`
- `wordpress_detected`

## Schema Warnings

- derived unknown_product_detected from unknown product fingerprint
- unknown_product_detected present; known-family ranking requires extra guard
- unknown_product_detected forced unknown_family_triage

## Allowed Actions

- `summarize_unknown_family_signals`
- `recommend_fingerprint_enrichment`
- `recommend_new_family_research`
- `quarantine_from_known_family_autorun`

## Operator Note

อ่าน `final_decision` ก่อน score เสมอ และอย่าใช้ ML output เพื่อยิง exploit อัตโนมัติ
