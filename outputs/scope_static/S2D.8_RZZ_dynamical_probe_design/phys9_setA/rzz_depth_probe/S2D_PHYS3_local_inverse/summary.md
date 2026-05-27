# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.7693 | 0.8826 | 6 | 0.3166 | 0.0494 |  |
| physical_local_inverse_probability | 1.0000 | 1.0000 | 6 | 0.3560 | 0.0507 | bootstrap min 1.0000 |
| physical_local_inverse_probability_v2 | 1.0000 | 1.0000 | 6 | 0.3560 | 0.0507 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 6 | 0.3560 | 0.0507 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | 0.0028 | 0.3389 | 6 | `[4, 4, 5, 5, 1, 2]` |
| structural_only_features | deterministic_kmeans | 0.7207 | 0.8181 | 6 | `[1, 2, 1, 3, 6, 8]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.0275 | 0.3600 | 6 | `[2, 13, 2, 2, 1, 1]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.7693 | 0.8826 | 6 | `[1, 1, 8, 2, 6, 3]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.0626 | 0.4407 | 6 | `[3, 7, 2, 6, 1, 2]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 1.0000 | 1.0000 | 6 | `[9, 1, 1, 8, 1, 1]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 1.0000 | 1.0000 | 6 | `[9, 1, 1, 8, 1, 1]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 6 | `[1, 9, 8, 1, 1, 1]` |
