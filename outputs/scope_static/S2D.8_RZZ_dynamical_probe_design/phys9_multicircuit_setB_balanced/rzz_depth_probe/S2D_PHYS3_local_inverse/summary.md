# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.3949 | 0.7340 | 9 | 0.2309 | 0.0483 |  |
| physical_local_inverse_probability | 0.9388 | 0.9003 | 9 | 0.2467 | 0.0482 | bootstrap min 0.9408 |
| physical_local_inverse_probability_v2 | 0.9351 | 0.8947 | 9 | 0.2367 | 0.0474 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 9 | 0.2151 | 0.0477 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0013 | 0.3125 | 9 | `[6, 7, 6, 3, 2, 4, 6, 8, 9]` |
| structural_only_features | deterministic_kmeans | 0.2097 | 0.5525 | 9 | `[1, 3, 6, 6, 6, 1, 12, 9, 7]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.2991 | 0.4987 | 9 | `[1, 12, 2, 2, 30, 1, 1, 1, 1]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.3949 | 0.7340 | 9 | `[8, 3, 3, 3, 5, 12, 6, 1, 10]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1944 | 0.5000 | 9 | `[1, 12, 17, 2, 1, 2, 1, 2, 13]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.9388 | 0.9003 | 9 | `[27, 3, 3, 9, 3, 2, 1, 2, 1]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 0.9351 | 0.8947 | 9 | `[27, 3, 3, 9, 1, 4, 1, 1, 2]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 9 | `[3, 3, 27, 3, 3, 3, 3, 3, 3]` |
