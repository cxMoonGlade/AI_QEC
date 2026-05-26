# DISC16b Local-Inverse Recovery Robustness

- Result: `robust_near_strong_some_hard_cases`
- Predeclared representation: `local_logit_probability`
- Candidate selection: `disabled_predeclared_representation`
- ARI/NMI used for selection: `false`
- Regime axis: `synthetic_multi_env_teacher_contrast`

| regime | shots | seeds | ARI mean | ARI min | NMI mean | NMI min | active min | boot NMI | prob var | strong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| default | 10000 | 5 | 0.8443 | 0.7426 | 0.9482 | 0.9136 | 9 | 0.926 | 0.01099 | 3/5 |
| default | 25000 | 5 | 0.936 | 0.7828 | 0.9798 | 0.9269 | 9 | 0.9743 | 0.004533 | 4/5 |
| default | 50000 | 5 | 1 | 1 | 1 | 1 | 9 | 1 | 0.001928 | 5/5 |
| easy | 10000 | 5 | 0.8567 | 0.6742 | 0.9525 | 0.8885 | 9 | 0.9286 | 0.01174 | 3/5 |
| easy | 25000 | 5 | 0.9728 | 0.8611 | 0.9916 | 0.9581 | 9 | 0.9833 | 0.00362 | 5/5 |
| easy | 50000 | 5 | 0.9783 | 0.7828 | 0.9944 | 0.9443 | 9 | 0.9889 | 0.002209 | 4/5 |
| harder | 10000 | 5 | 0.8187 | 0.732 | 0.9458 | 0.9123 | 9 | 0.9191 | 0.01115 | 2/5 |
| harder | 25000 | 5 | 0.9564 | 0.8295 | 0.987 | 0.9515 | 9 | 0.9796 | 0.004292 | 5/5 |
| harder | 50000 | 5 | 0.9626 | 0.8673 | 0.9878 | 0.9581 | 9 | 0.9811 | 0.002197 | 5/5 |

Failure cases: 9

Interpretation labels:

- `confirmed_strong_recovery_robust`: every grid condition clears ARI/NMI and active-cluster thresholds.
- `confirmed_strong_recovery_nearly_all_runs`: at least 90% of grid conditions clear thresholds.
- `robust_near_strong_some_hard_cases`: mean recovery is strong/near-strong, with some below-threshold cases.
- `fragile_recovery_not_robust_across_grid`: strong recovery is not stable across the grid.
