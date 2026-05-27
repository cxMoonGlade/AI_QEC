# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.3658 | 0.6946 | 9 | 0.2823 | 0.0541 |  |
| physical_local_inverse_probability | 0.9425 | 0.9172 | 9 | 0.3050 | 0.0514 | bootstrap min 0.9408 |
| physical_local_inverse_probability_v2 | 0.9370 | 0.8969 | 9 | 0.2979 | 0.0514 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 9 | 0.2651 | 0.0520 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0013 | 0.3125 | 9 | `[6, 7, 6, 3, 2, 4, 6, 8, 9]` |
| structural_only_features | deterministic_kmeans | 0.2097 | 0.5525 | 9 | `[1, 3, 6, 6, 6, 1, 12, 9, 7]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.1903 | 0.4596 | 9 | `[1, 6, 19, 1, 3, 1, 9, 9, 2]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.3658 | 0.6946 | 9 | `[5, 3, 3, 5, 9, 11, 4, 7, 4]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1605 | 0.4589 | 9 | `[1, 6, 16, 3, 3, 9, 1, 1, 11]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.9425 | 0.9172 | 9 | `[27, 3, 3, 9, 3, 1, 1, 2, 2]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 0.9370 | 0.8969 | 9 | `[27, 3, 3, 9, 3, 1, 3, 1, 1]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 9 | `[3, 3, 27, 3, 3, 3, 3, 3, 3]` |
