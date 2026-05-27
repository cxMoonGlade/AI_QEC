# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `usable`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.3194 | 0.7218 | 11 | 0.2439 | 0.0492 |  |
| physical_local_inverse_probability | 0.8927 | 0.8630 | 11 | 0.2482 | 0.0474 | bootstrap min 0.9350 |
| physical_local_inverse_probability_v2 | 0.8898 | 0.8689 | 11 | 0.2405 | 0.0476 |  |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 11 | 0.2229 | 0.0478 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | -0.0004 | 0.3623 | 11 | `[3, 4, 2, 9, 4, 2, 2, 5, 9, 8, 9]` |
| structural_only_features | deterministic_kmeans | 0.3622 | 0.6564 | 11 | `[1, 3, 3, 3, 4, 3, 15, 8, 4, 5, 8]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.2150 | 0.5498 | 11 | `[1, 8, 21, 2, 3, 1, 1, 2, 1, 16, 1]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.3194 | 0.7218 | 11 | `[1, 3, 3, 7, 6, 2, 4, 5, 11, 9, 6]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1913 | 0.5368 | 11 | `[1, 10, 19, 3, 1, 3, 1, 1, 8, 2, 8]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.8927 | 0.8630 | 11 | `[27, 3, 3, 12, 3, 3, 1, 2, 1, 1, 1]` |
| physical_local_inverse_probability_v2 | visible_operation_aware_local_inverse_clustering_v2 | 0.8898 | 0.8689 | 11 | `[27, 3, 3, 12, 1, 5, 1, 1, 2, 1, 1]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 11 | `[3, 3, 27, 3, 3, 3, 3, 3, 3, 3, 3]` |
