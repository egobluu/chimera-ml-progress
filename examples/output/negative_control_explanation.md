# Runtime Decision Explanation

## สรุป

| Field | Value |
| --- | --- |
| target | `example_negative_control` |
| final decision | `do_not_exploit_now` |
| ความหมาย | หลักฐานตอนนี้ยังไม่ควรตรวจ exploit ต่อ |
| recommended next action | `stop_or_collect_more_evidence` |
| requires user approval | no |
| may run safe verification | no |
| may run exploit | no |

## Gate

| Field | Value |
| --- | --- |
| decision | `no_exploit` |
| score | `0.059168` |
| threshold | `0.15` |

## Ranker

| Field | Value |
| --- | --- |
| decision | `None` |
| confidence | `None` |
| margin | `None` |
| family ready | `None` |
| readiness reason | None |

## Top Families

| Family | Score | Positive signals | Negative signals | Specific positive |
| --- | ---: | ---: | ---: | ---: |
| n/a | n/a | n/a | n/a | n/a |

## Reason Features

- `auth_required`
- `endpoint_reachable_count`
- `has_negative_precondition_signal`
- `has_positive_precondition_signal`
- `is_http_target`
- `service_port`
- `version_in_vulnerable_range_false`
- `version_patched`

## Schema Warnings

- ไม่มี schema warning

## Allowed Actions

- `summarize_evidence`
- `recommend_non_intrusive_scan`
- `stop_current_exploit_path`

## Operator Note

อ่าน `final_decision` ก่อน score เสมอ และอย่าใช้ ML output เพื่อยิง exploit อัตโนมัติ
