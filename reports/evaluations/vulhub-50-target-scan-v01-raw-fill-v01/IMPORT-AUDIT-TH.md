# Scan Batch Import Audit

## Summary

| Item | Count |
| --- | ---: |
| Total targets | 51 |
| Feature rows | 51 |
| Validation rows | 51 |
| Enrichment rows | 22 |
| Safe-to-merge ids | 30 |
| Quarantined ids | 21 |

## Runtime Categories

```json
{
  "known_positive": 15,
  "negative_control": 28,
  "unknown_family": 8
}
```

## Issue Counts

```json
{
  "mapped_to_unknown_family": 8
}
```

## First Issues

- `drupal_positive_001`: mapped_to_unknown_family (info)
- `jboss_positive_001`: mapped_to_unknown_family (info)
- `jetty_positive_001`: mapped_to_unknown_family (info)
- `laravel_positive_001`: mapped_to_unknown_family (info)
- `wordpress_positive_001`: mapped_to_unknown_family (info)
- `php_cgi_positive_001`: mapped_to_unknown_family (info)
- `nacos_positive_001`: mapped_to_unknown_family (info)
- `spring_positive_001`: mapped_to_unknown_family (info)

## Next Step

ถ้าไม่มี error ให้ run `scripts/evaluate_runtime_predictions.py` โดยใช้ `features.enriched.jsonl` และ `runtime-targets.jsonl`
