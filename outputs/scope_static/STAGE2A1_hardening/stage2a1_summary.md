# Stage 2A.1 Hardening Summary

- Metrics: `outputs/scope_static/STAGE2A1_hardening/metrics.json`
- Conclusion: `likelihood_good_recovery_low_hardening_non_rescuing`
- Movement interpretation: `local_logit_initialized_assignments_remain_at_disc10_ceiling`
- Selection rule: `validation_nll_plus_observable_health`
- ARI/NMI used for selection: `false`

| id | condition | ARI | NMI | dNLL known | active | result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| A | free_random_init | 0.1747 | 0.5972 | 0.002575 | 9 | failure_likelihood_good_recovery_low |
| B | free_local_logit_init | 0.2748 | 0.7097 | 0.00281 | 9 | failure_likelihood_good_recovery_low |
| C | hard_st_random_init | 0.148 | 0.6509 | 0.006166 | 8.667 | failure_likelihood_good_recovery_low |
| D | hard_st_local_logit_init | 0.1961 | 0.6812 | 0.01065 | 9 | failure |
| E | hard_st_local_logit_init_entropy_anneal | 0.2748 | 0.7097 | 0.003647 | 9 | failure_likelihood_good_recovery_low |
| F | hard_st_local_logit_init_entropy_balance | 0.2493 | 0.7004 | 0.005425 | 9 | failure_likelihood_good_recovery_low |
| G | hard_st_local_logit_init_entropy_balance_separation | 0.2748 | 0.7097 | 0.003727 | 9 | failure_likelihood_good_recovery_low |

## Assignment Movement Audit

| id | init-final NMI | rows changed | entropy start | entropy end | grad norm | alpha delta | selected by ARI/NMI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A | 0.4055 | 0.7971 | 2.197 | 1.65 | 0.000287 | 4.221 | false |
| B | 1 | 0 | 0.000639 | 0.1422 | 1.864e-05 | 0.155 | false |
| C | 0.6744 | 0.4203 | 0.000639 | 0.6394 | 0.00126 | 3.188 | false |
| D | 0.8614 | 0.1884 | 0.000639 | 0.5365 | 0.00122 | 0.9353 | false |
| E | 1 | 0 | 0.000639 | 0.01124 | 0.0003437 | 0.2005 | false |
| F | 0.9869 | 0.01449 | 0.000639 | 0.01135 | 0.0003423 | 0.2143 | false |
| G | 1 | 0 | 0.000639 | 0.01136 | 0.0003204 | 0.2746 | false |

DISC10 is used only as a controlled visible-signature initializer context; ARI/NMI remain evaluator-only.
