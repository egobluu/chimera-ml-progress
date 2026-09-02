# Runtime Decision Explanation

## สรุป

| Field | Value |
| --- | --- |
| target | `example_redis_weak` |
| final decision | `needs_more_evidence` |
| ความหมาย | หลักฐานยังไม่พอ ต้องให้ scanner/probe เก็บข้อมูลเพิ่ม |
| recommended next action | `stop_or_collect_more_evidence` |
| requires user approval | no |
| may run safe verification | no |
| may run exploit | no |

## Gate

| Field | Value |
| --- | --- |
| decision | `low_confidence` |
| score | `0.933099` |
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

- `has_positive_precondition_signal`
- `is_non_http_service`
- `no_auth_required`
- `redis_detected`
- `redis_info_accessible`
- `service_port`
- `version_in_vulnerable_range`
- `version_in_vulnerable_range_true`

## Schema Warnings

- blocking negative evidence downgraded likely_exploitable to low_confidence

## Allowed Actions

- `summarize_missing_evidence`
- `recommend_precheck_probe`
- `run_authorized_non_destructive_probe`

## Operator Note

อ่าน `final_decision` ก่อน score เสมอ และอย่าใช้ ML output เพื่อยิง exploit อัตโนมัติ
