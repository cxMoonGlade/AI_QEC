# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.4037 | 0.7732 | 11 | 0.2113 | 0.0472 |  |
| physical_local_inverse_probability | 0.9009 | 0.8927 | 11 | 0.2508 | 0.0466 | bootstrap min 0.9378 |
| physical_local_inverse_probability_v2 | 0.9009 | 0.8927 | 11 | 0.2508 | 0.0466 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 11 | 0.2190 | 0.0476 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0004 | 0.3623 | 11 | `[3, 4, 2, 9, 4, 2, 2, 5, 9, 8, 9]` |
| structural_only_features | deterministic_kmeans | 0.3622 | 0.6564 | 11 | `[1, 3, 3, 3, 4, 3, 15, 8, 4, 5, 8]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.2104 | 0.5412 | 11 | `[1, 21, 8, 1, 1, 3, 16, 3, 1, 1, 1]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.4037 | 0.7732 | 11 | `[3, 1, 3, 5, 8, 11, 4, 7, 3, 8, 4]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1566 | 0.5463 | 11 | `[1, 13, 10, 3, 2, 4, 1, 6, 6, 1, 10]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.9009 | 0.8927 | 11 | `[27, 3, 3, 12, 3, 2, 1, 1, 2, 1, 2]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 0.9009 | 0.8927 | 11 | `[27, 3, 3, 12, 3, 2, 1, 1, 2, 2, 1]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 11 | `[3, 3, 27, 3, 3, 3, 3, 3, 3, 3, 3]` |
