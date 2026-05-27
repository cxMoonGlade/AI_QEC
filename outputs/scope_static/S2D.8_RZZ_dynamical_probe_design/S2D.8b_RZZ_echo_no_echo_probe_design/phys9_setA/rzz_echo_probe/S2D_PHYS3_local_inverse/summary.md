# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.8465 | 0.9001 | 6 | 0.2710 | 0.0455 |  |
| physical_local_inverse_probability | 1.0000 | 1.0000 | 6 | 0.2996 | 0.0458 | bootstrap min 1.0000 |
| physical_local_inverse_probability_v2 | 1.0000 | 1.0000 | 6 | 0.2996 | 0.0458 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 6 | 0.2996 | 0.0458 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | 0.0028 | 0.3389 | 6 | `[4, 4, 5, 5, 1, 2]` |
| structural_only_features | deterministic_kmeans | 0.7207 | 0.8181 | 6 | `[1, 2, 1, 3, 6, 8]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.0549 | 0.4133 | 6 | `[2, 11, 2, 2, 1, 3]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.8465 | 0.9001 | 6 | `[1, 1, 6, 2, 9, 2]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.3440 | 0.6070 | 6 | `[2, 5, 2, 3, 8, 1]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 1.0000 | 1.0000 | 6 | `[9, 1, 1, 8, 1, 1]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 1.0000 | 1.0000 | 6 | `[9, 1, 1, 8, 1, 1]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 6 | `[1, 9, 8, 1, 1, 1]` |
