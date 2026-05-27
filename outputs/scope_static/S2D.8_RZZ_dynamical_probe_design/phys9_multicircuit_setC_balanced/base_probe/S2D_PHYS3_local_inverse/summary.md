# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `hard`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.3880 | 0.7261 | 11 | 0.3245 | 0.0538 |  |
| physical_local_inverse_probability | 0.8892 | 0.8501 | 11 | 0.3432 | 0.0525 | bootstrap min 0.9265 |
| physical_local_inverse_probability_v2 | 0.8894 | 0.8495 | 11 | 0.3290 | 0.0516 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 11 | 0.2668 | 0.0521 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0004 | 0.3623 | 11 | `[3, 4, 2, 9, 4, 2, 2, 5, 9, 8, 9]` |
| structural_only_features | deterministic_kmeans | 0.3622 | 0.6564 | 11 | `[1, 3, 3, 3, 4, 3, 15, 8, 4, 5, 8]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.1651 | 0.4931 | 11 | `[1, 6, 1, 20, 3, 10, 1, 1, 2, 10, 2]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.3880 | 0.7261 | 11 | `[3, 3, 3, 6, 9, 11, 5, 7, 4, 2, 4]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1589 | 0.5102 | 11 | `[1, 6, 18, 3, 3, 3, 1, 1, 3, 11, 7]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.8892 | 0.8501 | 11 | `[27, 3, 3, 12, 2, 2, 2, 1, 2, 1, 2]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 0.8894 | 0.8495 | 11 | `[27, 3, 3, 12, 3, 1, 1, 2, 1, 1, 3]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 11 | `[3, 3, 27, 3, 3, 3, 3, 3, 3, 3, 3]` |
