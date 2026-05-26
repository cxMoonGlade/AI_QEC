# DISC13 Observational Quotient Audit

- Conclusion: `target_mismatch_not_confirmed_learned_not_meaningfully_closer_to_observational_quotient`
- Primary quotient family: `observation_side`
- ARI/NMI used for selection: `false`

## Observational Quotients

| family | dim | active | ARI vs omega | NMI vs omega |
| --- | ---: | ---: | ---: | ---: |
| oracle_logit | 10 | 9 | 1 | 1 |
| oracle_logit_support | 18 | 9 | 0.7404 | 0.938 |
| observation_side | 38 | 9 | 0.2538 | 0.7058 |
| combined | 48 | 9 | 0.3422 | 0.7594 |

## Target Alignment

| learned | quotient | ARI learned/omega | ARI learned/obs | gap | NMI learned/omega | NMI learned/obs |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| known_orbit_oracle_shared_S | observation_side | 1 | 0.2538 | -0.7462 | 1 | 0.7058 |
| multi_env_shared_S_DISC10_init | observation_side | 0.3574 | 0.1432 | -0.2142 | 0.7598 | 0.6363 |
| multi_env_shared_S_random_init | observation_side | 0.2766 | 0.1664 | -0.1103 | 0.6874 | 0.5774 |
| single_env_free_assignment | observation_side | 0.08841 | 0.09475 | 0.006338 | 0.5569 | 0.5388 |
| single_env_local_logit_init | observation_side | 0.2448 | 0.1188 | -0.126 | 0.7025 | 0.6211 |
