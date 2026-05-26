# Stage 2C Failure-Case Audit

- Source: `outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/metrics.json`
- Conclusion: `near_miss_ari_failures_no_cluster_collapse_mostly_low_shot_split_merge`
- Freeze label: `local_inverse_probability_robust_near_strong_with_near_miss_split_merge_failures`
- Conditions: 36/45 strong; 9 failures
- Candidate selection: `disabled_predeclared_representation`
- ARI/NMI used for selection: `false`

## Failure Counts

- By shots: `{'10000': 7, '25000': 1, '50000': 1}`
- By regime: `{'default': 3, 'easy': 3, 'harder': 3}`
- By seed: `{'1': 1, '2': 1, '3': 4, '4': 3}`
- Reasons: `{'ari_below_0.80': 9}`

## Failure Pattern

| group | ARI min mean | ARI min range | NMI min mean | active min | boot NMI mean | purity mean | splits mean |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| failures | 0.7557 | 0.6742-0.7923 | 0.924 | 9 | 0.9125 | 0.945 | 1.148 |
| successes | 0.9374 | 0.8295-1 | 0.9802 | 9 | 0.9775 | 0.9863 | 1.042 |

## Failure Rows

| regime | seed | shots | ARI min | NMI min | active | boot NMI | purity | splits | resolved later |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| easy | 3 | 10000 | 0.6742 | 0.8885 | 9 | 0.8646 | 0.8981 | 1.222 | true |
| easy | 3 | 50000 | 0.7828 | 0.9443 | 9 | 0.9443 | 0.9722 | 1.056 | false |
| easy | 4 | 10000 | 0.7923 | 0.9245 | 9 | 0.9101 | 0.9537 | 1.167 | true |
| default | 2 | 10000 | 0.7426 | 0.9136 | 9 | 0.9217 | 0.95 | 1.167 | true |
| default | 3 | 25000 | 0.7828 | 0.9269 | 9 | 0.9467 | 0.9398 | 1.167 | true |
| default | 4 | 10000 | 0.7613 | 0.9415 | 9 | 0.9023 | 0.963 | 1.111 | true |
| harder | 1 | 10000 | 0.732 | 0.9123 | 9 | 0.942 | 0.9389 | 1.167 | true |
| harder | 3 | 10000 | 0.7828 | 0.9443 | 9 | 0.9201 | 0.9537 | 1.111 | true |
| harder | 4 | 10000 | 0.75 | 0.9201 | 9 | 0.8611 | 0.9352 | 1.167 | true |

## Interpretation

Failures are near-miss recovery errors, not collapse: every failure keeps all 9 clusters active and NMI remains above 0.80. The failed cells miss only the ARI threshold, usually at 10k shots, with split/merge counts slightly above the exact-partition value of 1.0.

This freezes Stage 2C as robust near-strong local-inverse recovery with known hard cases. The next research branch should change observability or broaden the teacher/grid, not add more direct S/alpha hardening.
