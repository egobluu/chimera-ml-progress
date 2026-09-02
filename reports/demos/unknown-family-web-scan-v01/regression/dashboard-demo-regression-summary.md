# Unknown-family Dashboard Demo Regression

| target | product | port | gate | ranker | resolver used | final | overall |
|---|---|---:|---|---|---:|---|---:|
| acme_zerocms_unknown_demo_01 | Acme ZeroCMS | 18080 | likely_exploitable | unknown_family | False | unknown_family_triage | True |
| aurora_notes_unknown_demo_02 | Aurora Notes Portal | 18083 | likely_exploitable | unknown_family | False | unknown_family_triage | True |
| nova_board_unknown_demo_03 | Nova Board Service | 18084 | likely_exploitable | unknown_family | False | unknown_family_triage | True |

## Expected behavior

- Gate should return `likely_exploitable` for these synthetic vulnerable-looking targets.
- Family Ranker is allowed to produce a raw known-family top score.
- Unknown-family guard must block known-family trust and return `unknown_family`.
- CVE/Module Resolver must not run unless final decision is `ready_for_safe_verification`.
- Final decision should be `unknown_family_triage`.
