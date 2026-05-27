# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_learner_limited`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`
- NLL difficulty: `hard`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.4212 | 0.8685 | 9 | 0.5268 | 0.0465 |  |
| physical_local_inverse_probability | 0.3868 | 0.8578 | 9 | 0.6662 | 0.0485 | bootstrap min 0.9437 |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 9 | 0.5430 | 0.0468 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | 0.0264 | 0.6845 | 7 | `[2, 2, 2, 1, 0, 0, 3, 2, 2]` |
| structural_only_features | deterministic_kmeans | 0.0353 | 0.7528 | 9 | `[1, 1, 1, 2, 1, 3, 2, 1, 2]` |
| raw_observation_probe_summary | deterministic_kmeans | -0.0817 | 0.7162 | 9 | `[1, 2, 2, 1, 2, 1, 2, 2, 1]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.4212 | 0.8685 | 9 | `[1, 2, 1, 2, 2, 1, 1, 3, 1]` |
| raw_local_inverse_logits | deterministic_kmeans | -0.0817 | 0.7162 | 9 | `[1, 2, 2, 1, 1, 2, 2, 1, 2]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 0.3868 | 0.8578 | 9 | `[2, 1, 1, 1, 1, 1, 1, 3, 3]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 9 | `[1, 2, 5, 1, 1, 1, 1, 1, 1]` |
