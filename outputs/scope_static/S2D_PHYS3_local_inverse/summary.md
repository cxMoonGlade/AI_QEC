# S2D PHYS3 Local Inverse Discovery

- Result: `physical_oracle_strong_recovery`
- Predeclared representation: `physical_local_inverse_probability`
- ARI/NMI used for selection: `false`
- Oracle separability gate: `identifying`

| comparison | ARI | NMI | active | heldout NLL | response MAE | boot/notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| direct_S_alpha_assignment | 0.6887 | 0.8865 | 6 | 0.3482 | 0.0457 |  |
| physical_local_inverse_probability | 1.0000 | 1.0000 | 6 | 0.3779 | 0.0452 | bootstrap min 1.0000 |
| oracle_fingerprint_upper_bound | 1.0000 | 1.0000 | 6 | 0.3779 | 0.0452 | evaluator-only |

## All Comparisons

| comparison | method | ARI | NMI | active | cluster masses |
| --- | --- | ---: | ---: | ---: | --- |
| random_partition | uniform_random_partition_trials | 0.0185 | 0.5111 | 5 | `[2, 4, 2, 3, 0, 2]` |
| structural_only_features | deterministic_kmeans | 0.2022 | 0.6886 | 6 | `[1, 2, 2, 2, 3, 3]` |
| raw_observation_probe_summary | deterministic_kmeans | 0.1127 | 0.5984 | 6 | `[1, 5, 2, 2, 2, 1]` |
| direct_S_alpha_assignment | deterministic_kmeans | 0.6887 | 0.8865 | 6 | `[1, 4, 1, 3, 2, 2]` |
| raw_local_inverse_logits | deterministic_kmeans | 0.1127 | 0.5984 | 6 | `[1, 5, 2, 1, 2, 2]` |
| physical_local_inverse_probability | visible_operation_aware_local_inverse_clustering | 1.0000 | 1.0000 | 6 | `[5, 1, 4, 1, 1, 1]` |
| oracle_fingerprint_upper_bound | oracle_ptm_probe_fingerprint_kmeans | 1.0000 | 1.0000 | 6 | `[1, 4, 5, 1, 1, 1]` |
