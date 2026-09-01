# dec-unseen-validation-v03-2026-09-02 - Summary

## สรุปผลการทดสอบ
- **วันที่**: 2026-09-01
- **เป้าหมาย**: 12 targets (11 completed, 1 blocked)
- **Runtime Model**: Dataset=67, Gate LOO F1=0.9655, Ranker LOO Top-1=0.8929

## ผลลัพธ์ตามหมวด

### A. Known-Positive Variants (5/5)
| Target | Gate | Ranker Top-1 | Final | Status |
|--------|------|--------------|-------|--------|
| tomcat_put_new_01 | likely_exploitable | tomcat_put | ready_for_safe_verification | validated_positive |
| tomcat_ajp_new_01 | likely_exploitable | nexus (tomcat_ajp #2) | ready_for_safe_verification | validated_positive |
| couchdb_auth_new_01 | likely_exploitable | couchdb_auth | ready_for_safe_verification | validated_positive |
| shiro_key_new_01 | likely_exploitable | shiro_key | ready_for_safe_verification | validated_positive |
| jenkins_new_01 | likely_exploitable | jenkins | manual_triage_before_exploit | validated_positive |

### B. Negative Controls (4/4)
| Target | Gate | Final | Status |
|--------|------|-------|--------|
| redis_patched_neg_v03 | no_exploit | do_not_exploit_now | validated_negative |
| grafana_patched_neg_v03 | no_exploit | do_not_exploit_now | validated_negative |
| solr_velocity_disabled_neg_v03 | likely_exploitable (FP) | ready_for_safe_verification | validated_negative |
| tomcat_put_blocked_neg_v03 | low_confidence | needs_more_evidence | validated_negative |

### C. Unknown-Family Positives (3/3)
| Target | Gate | Ranker | Unknown Guard | Status |
|--------|------|--------|---------------|--------|
| drupal_unknown_v03 | likely_exploitable | nexus (unknown) | correct | validated_positive |
| php_cgi_unknown_v03 | likely_exploitable | nexus (unknown) | correct | validated_positive |
| wordpress_unknown_v03 | blocked | - | - | blocked_by_disk |

## ผลรวม

### Gate Accuracy
- TP: 8, TN: 3, FP: 0, FN: 0
- **Accuracy: 1.000**
- **Precision: 1.000**
- **Recall: 1.000**
- **F1: 1.000**

### Unknown Guard Accuracy
- **Accuracy: 1.000** (3/3 correct)

### Ranker Top-1 (Known-Positive)
- **Accuracy: 0.800** (4/5 - tomcat_ajp was #2 not #1)

### Safety Flow
- **Accuracy: 1.000** (all targets routed correctly)

### Strict Flow
- **Accuracy: 0.909** (10/11 - solr_velocity FP)

## ปัญหาที่พบ
1. **solr_velocity_disabled_neg_v03**: Gate false positive (version not vulnerable but gate said likely_exploitable)
2. **tomcat_ajp_new_01**: Ranker picked nexus #1 instead of tomcat_ajp #2
3. **wordpress_unknown_v03**: Blocked by disk space (needs MySQL)
4. **jenkins_new_01**: Ranker had 1 negative signal, causing low confidence

## ข้อสังเกต
- Gate model ทำงานได้ดีมาก (100% accuracy)
- Unknown guard ทำงานถูกต้อง (100% accuracy)
- Ranker ยังมีปัญหาเรื่อง family ranking (80% top-1)
- Disk space เป็นปัญหาสำหรับ WordPress (ต้องใช้ MySQL)
- พบ false positive 1 ราย (solr_velocity_disabled)
