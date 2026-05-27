# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.3744 | 0.7436 | 9 | 0.2040 | 0.0479 |  |
| physical_local_inverse_probability | 0.9425 | 0.9172 | 9 | 0.2362 | 0.0472 | bootstrap min 0.9443 |
| physical_local_inverse_probability_v2 | 0.9425 | 0.9172 | 9 | 0.2362 | 0.0472 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 9 | 0.2158 | 0.0478 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0013 | 0.3125 | 9 | `[6, 7, 6, 3, 2, 4, 6, 8, 9]` |
| structural_only_features | deterministic_kmeans | 0.2097 | 0.5525 | 9 | `[1, 3, 6, 6, 6, 1, 12, 9, 7]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.1848 | 0.4813 | 9 | `[1, 19, 10, 1, 1, 3, 2, 5, 9]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.3744 | 0.7436 | 9 | `[7, 3, 3, 10, 4, 8, 5, 2, 9]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1943 | 0.4845 | 9 | `[1, 17, 10, 1, 2, 1, 15, 2, 2]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.9425 | 0.9172 | 9 | `[27, 3, 3, 9, 3, 2, 1, 2, 1]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 0.9425 | 0.9172 | 9 | `[27, 3, 3, 9, 3, 2, 1, 2, 1]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 9 | `[3, 3, 27, 3, 3, 3, 3, 3, 3]` |
