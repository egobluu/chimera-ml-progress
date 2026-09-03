# Scan Batch Import Audit

## Summary

| Item | Count |
| --- | ---: |
| Total targets | 45 |
| Feature rows | 45 |
| Validation rows | 45 |
| Enrichment rows | 6 |
| Safe-to-merge ids | 32 |
| Quarantined ids | 13 |

## Runtime Categories

```json
{
  "known_positive": 9,
  "negative_control": 11,
  "unknown_family": 25
}
```

## Issue Counts

```json
{
  "mapped_to_unknown_family": 28,
  "missing_cve_enrichment": 21,
  "non_standard_status": 13
}
```

## First Issues

- `adminer_pos_001`: non_standard_status (warning)
- `adminer_pos_001`: mapped_to_unknown_family (info)
- `adminer_pos_001`: missing_cve_enrichment (warning)
- `confluence_pos_001`: mapped_to_unknown_family (info)
- `confluence_pos_001`: missing_cve_enrichment (warning)
- `couchdb_positive_001`: missing_cve_enrichment (warning)
- `dataease_pos_001`: non_standard_status (warning)
- `dataease_pos_001`: mapped_to_unknown_family (info)
- `dataease_pos_001`: missing_cve_enrichment (warning)
- `drupal_pos_002`: non_standard_status (warning)
- `drupal_pos_002`: mapped_to_unknown_family (info)
- `drupal_pos_002`: missing_cve_enrichment (warning)
- `fastjson_positive_001`: non_standard_status (warning)
- `fastjson_positive_001`: mapped_to_unknown_family (info)
- `gitea_pos_001`: mapped_to_unknown_family (info)
- `gitlab_pos_001`: mapped_to_unknown_family (info)
- `gitlab_pos_001`: missing_cve_enrichment (warning)
- `gogs_pos_001`: non_standard_status (warning)
- `gogs_pos_001`: mapped_to_unknown_family (info)
- `gogs_pos_001`: missing_cve_enrichment (warning)
- `hadoop_pos_001`: non_standard_status (warning)
- `hadoop_pos_001`: mapped_to_unknown_family (info)
- `hugegraph_pos_001`: mapped_to_unknown_family (info)
- `hugegraph_pos_001`: missing_cve_enrichment (warning)
- `jupyter_pos_001`: mapped_to_unknown_family (info)
- `kibana_pos_001`: mapped_to_unknown_family (info)
- `kibana_pos_001`: missing_cve_enrichment (warning)
- `metabase_pos_001`: mapped_to_unknown_family (info)
- `metabase_pos_001`: missing_cve_enrichment (warning)
- `minio_pos_001`: mapped_to_unknown_family (info)
- `minio_pos_001`: missing_cve_enrichment (warning)
- `mongo_express_pos_001`: mapped_to_unknown_family (info)
- `mongo_express_pos_001`: missing_cve_enrichment (warning)
- `n8n_pos_001`: mapped_to_unknown_family (info)
- `n8n_pos_001`: missing_cve_enrichment (warning)
- `openfire_pos_001`: non_standard_status (warning)
- `openfire_pos_001`: mapped_to_unknown_family (info)
- `openfire_pos_001`: missing_cve_enrichment (warning)
- `rocketchat_pos_001`: non_standard_status (warning)
- `rocketchat_pos_001`: mapped_to_unknown_family (info)
- `rocketchat_pos_001`: missing_cve_enrichment (warning)
- `saltstack_pos_001`: non_standard_status (warning)
- `saltstack_pos_001`: mapped_to_unknown_family (info)
- `saltstack_pos_001`: missing_cve_enrichment (warning)
- `spring_pos_001`: non_standard_status (warning)
- `spring_pos_001`: mapped_to_unknown_family (info)
- `spring_pos_001`: missing_cve_enrichment (warning)
- `superset_pos_001`: mapped_to_unknown_family (info)
- `superset_pos_001`: missing_cve_enrichment (warning)
- `supervisor_pos_001`: mapped_to_unknown_family (info)

## Next Step

ถ้าไม่มี error ให้ run `scripts/evaluate_runtime_predictions.py` โดยใช้ `features.enriched.jsonl` และ `runtime-targets.jsonl`
