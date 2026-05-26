# DISC15 Local-Logit-To-Mechanism Discovery

- Result: `evaluator_only_candidate_beats_baseline_no_observable_selection_claim`
- Source: `outputs/scope_static/STAGE2A2_DISC12_multi_env/env_alpha.json`
- Selection rule: `observable_cluster_health_only`
- ARI/NMI used for selection: `false`

| candidate | role | ARI | NMI | active | score | beats baseline |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| local_logit_baseline | measured local-logit baseline | 0.5739 | 0.8618 | 9 | 2.451 | true |
| single_env_local_logit_env0 | observable-selected | 0.3213 | 0.7125 | 9 | 2.801 | false |
| local_logit_probability | evaluator-best | 0.7923 | 0.9245 | 9 | 2.253 | true |

## Top Observable Candidates

| candidate | ARI | NMI | active | score | margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| single_env_local_logit_env0 | 0.3213 | 0.7125 | 9 | 2.801 | 0.341 |
| single_env_local_logit_env1 | 0.1473 | 0.6597 | 9 | 2.795 | 0.293 |
| pca_scores_rank1 | 0.4149 | 0.7702 | 9 | 2.751 | 0.2594 |
| pca_denoised_rank1 | 0.4149 | 0.7702 | 9 | 2.741 | 0.5189 |
| graph_smoothed_pca_scores_rank1 | 0.1651 | 0.6517 | 9 | 2.739 | 0.4212 |
| single_env_local_logit_env2 | 0.2361 | 0.6956 | 9 | 2.735 | 0.3338 |
| nmf_overlap_top2_rank9_seed1 | 0.3574 | 0.7344 | 9 | 2.713 | 1.794 |
| single_env_local_logit_env3 | 0.4884 | 0.8093 | 9 | 2.706 | 0.2535 |
