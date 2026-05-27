# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_learner_limited`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.4048 | 0.7828 | 9 | 0.4803 | 0.0518 |  |
| physical_local_inverse_probability | 0.6142 | 0.8408 | 9 | 0.4744 | 0.0505 | bootstrap min 0.8216 |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 9 | 0.4454 | 0.0538 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0013 | 0.4954 | 8 | `[4, 3, 4, 2, 0, 1, 3, 2, 3]` |
| structural_only_features | deterministic_kmeans | 0.4815 | 0.7197 | 9 | `[1, 1, 1, 4, 3, 7, 3, 1, 1]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.0702 | 0.5550 | 9 | `[1, 2, 6, 1, 3, 5, 2, 1, 1]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.4048 | 0.7828 | 9 | `[1, 1, 6, 1, 3, 2, 3, 2, 3]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1542 | 0.6324 | 9 | `[2, 2, 5, 2, 1, 3, 2, 1, 4]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.6142 | 0.8408 | 9 | `[2, 1, 1, 4, 1, 1, 1, 7, 4]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 9 | `[1, 6, 9, 1, 1, 1, 1, 1, 1]` |
