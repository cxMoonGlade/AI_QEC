# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_learner_limited`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.3386 | 0.7925 | 11 | 0.6024 | 0.0523 |  |
| physical_local_inverse_probability | 0.4347 | 0.8184 | 11 | 0.5289 | 0.0511 | bootstrap min 0.8261 |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 11 | 0.5352 | 0.0554 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0011 | 0.5739 | 10 | `[1, 1, 2, 3, 2, 2, 2, 1, 4, 1, 4]` |
| structural_only_features | deterministic_kmeans | 0.1486 | 0.6722 | 11 | `[1, 1, 1, 2, 3, 2, 3, 1, 1, 4, 4]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.0598 | 0.6133 | 11 | `[1, 2, 7, 1, 1, 3, 2, 1, 1, 2, 2]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.3386 | 0.7925 | 11 | `[1, 1, 3, 1, 3, 1, 2, 3, 2, 4, 2]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1000 | 0.6433 | 11 | `[2, 2, 6, 2, 1, 1, 2, 2, 1, 2, 2]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.4347 | 0.8184 | 11 | `[2, 1, 1, 5, 1, 1, 1, 1, 2, 3, 5]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 11 | `[1, 5, 9, 1, 1, 1, 1, 1, 1, 1, 1]` |
