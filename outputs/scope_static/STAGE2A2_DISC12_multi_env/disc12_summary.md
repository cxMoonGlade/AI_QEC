# DISC12 Multi-Environment Shared Assignment

- Metrics: `outputs/scope_static/STAGE2A2_DISC12_multi_env/metrics.json`
- Train envs: `[0, 1, 2, 3]`
- Heldout envs: `[4]`
- Stage label: `multi_env_predictive_only_weak_recovery_gain_observable_contrast_likely_insufficient`
- ARI/NMI used for selection: `false`

| model | ARI | NMI | active | dNLL known | env holdout dNLL | result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| local_full_per_fault_per_env | - | - | - | 0.004092 | - | predictive_only |
| single_env_free_assignment | 0.08841 | 0.5569 | 9 | 0.004815 | 0.01554 | predictive_only |
| single_env_local_logit_init | 0.2448 | 0.7025 | 9 | 0.005611 | 0.01321 | predictive_only |
| multi_env_independent_S_per_env | 0.1234 | 0.5431 | 9 | 0.004224 | - | predictive_only |
| multi_env_shared_S_random_init | 0.2766 | 0.6874 | 9 | 0.003421 | 0.003536 | predictive_only |
| multi_env_shared_S_DISC10_init | 0.3574 | 0.7598 | 9 | 0.003462 | 0.003062 | predictive_only |
| known_orbit_oracle_shared_S | 1 | 1 | 9 | 0 | 0.002417 | strong_recovery |

## Environment Contrast Audit

```json
{
  "alpha_variation_norm": 2.496114054507956,
  "between_env_rate_contrast": 0.0025294751639825014,
  "per_prototype_alpha_separation": [
    0.6228009648156052,
    0.3103845949997421,
    0.24615930910276707,
    0.5548102009758936,
    0.19094398693738923,
    0.1977174916195906,
    0.3798208713652633,
    0.26054357980551435,
    0.32525375866657447
  ],
  "mean_per_prototype_alpha_separation": 0.34315941758759333
}
```


## DISC12b Contrast Sweep

- Decision: `high_observable_contrast_but_recovery_still_low`
- Calibration warning: `high_contrast_rows_degrade_heldout_environment_transfer`

| strength | rate contrast | alpha sep | ARI | NMI | dNLL known | env dNLL | result |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 0.00522 | 0.5556 | 0.3036 | 0.7377 | 0.009174 | 0.007998 | predictive_only |
| 2 | 0.01295 | 1.111 | 0.0844 | 0.565 | 0.004705 | 0.009573 | predictive_only |
| 4 | 0.05487 | 2.222 | 0.1565 | 0.5737 | 0.001516 | 0.105 | predictive_only |
| 8 | 0.2489 | 4.444 | 0.04396 | 0.4444 | -0.0354 | 0.1399 | predictive_only |
| 16 | 0.3129 | 8.889 | 0.2197 | 0.692 | -2.001 | 0.4694 | predictive_only |
