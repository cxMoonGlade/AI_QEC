# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.3838 | 0.7475 | 11 | 0.3478 | 0.0802 |  |
| physical_local_inverse_probability | 0.8845 | 0.8426 | 11 | 0.3869 | 0.0741 | bootstrap min 0.9759 |
| physical_local_inverse_probability_v2 | 0.8876 | 0.8472 | 11 | 0.3909 | 0.0738 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 11 | 0.3718 | 0.0822 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0004 | 0.3623 | 11 | `[3, 4, 2, 9, 4, 2, 2, 5, 9, 8, 9]` |
| structural_only_features | deterministic_kmeans | 0.3622 | 0.6564 | 11 | `[1, 3, 3, 3, 4, 3, 15, 8, 4, 5, 8]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.1109 | 0.4324 | 11 | `[1, 2, 3, 10, 15, 5, 14, 1, 1, 4, 1]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.3838 | 0.7475 | 11 | `[3, 6, 3, 3, 9, 9, 3, 3, 6, 3, 9]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1123 | 0.4467 | 11 | `[1, 2, 14, 2, 4, 15, 1, 6, 2, 6, 4]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.8845 | 0.8426 | 11 | `[27, 3, 3, 12, 1, 1, 2, 4, 1, 1, 2]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 0.8876 | 0.8472 | 11 | `[27, 3, 3, 12, 1, 1, 3, 2, 1, 2, 2]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 11 | `[3, 3, 27, 3, 3, 3, 3, 3, 3, 3, 3]` |
