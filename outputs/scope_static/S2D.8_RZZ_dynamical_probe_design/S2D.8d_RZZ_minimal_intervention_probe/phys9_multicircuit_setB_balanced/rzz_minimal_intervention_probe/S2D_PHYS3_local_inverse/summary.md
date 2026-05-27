# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.3687 | 0.7110 | 9 | 0.2199 | 0.0533 |  |
| physical_local_inverse_probability | 0.9313 | 0.8770 | 9 | 0.2462 | 0.0516 | bootstrap min 1.0000 |
| physical_local_inverse_probability_v2 | 0.9313 | 0.8770 | 9 | 0.2462 | 0.0516 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 9 | 0.2273 | 0.0537 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0013 | 0.3125 | 9 | `[6, 7, 6, 3, 2, 4, 6, 8, 9]` |
| structural_only_features | deterministic_kmeans | 0.2097 | 0.5525 | 9 | `[1, 3, 6, 6, 6, 1, 12, 9, 7]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.2022 | 0.4757 | 9 | `[1, 12, 1, 3, 21, 1, 1, 2, 9]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.3687 | 0.7110 | 9 | `[6, 3, 3, 5, 8, 11, 4, 8, 3]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1820 | 0.4452 | 9 | `[3, 2, 17, 2, 1, 13, 1, 10, 2]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.9313 | 0.8770 | 9 | `[27, 3, 3, 9, 1, 2, 1, 2, 3]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 0.9313 | 0.8770 | 9 | `[27, 3, 3, 9, 1, 2, 1, 2, 3]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 9 | `[3, 3, 27, 3, 3, 3, 3, 3, 3]` |
