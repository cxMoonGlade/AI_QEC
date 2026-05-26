# DISC10 Passive Identifiability Audit

- Result: `weak`
- Best visible signature: `local_logit`
- K mode: `known_K_synthetic_audit`

ARI/NMI are evaluator-only diagnostics and are not used for signature selection.

| family | score | ARI | NMI | active | result |
| --- | ---: | ---: | ---: | ---: | --- |
| structural | 1.631 | 0.6833 | 0.9294 | 9 | weak |
| local_logit | 2.734 | 0.2748 | 0.7097 | 9 | weak |
| moment_spectral | 1.546 | 0.03387 | 0.5772 | 9 | failed |
| combined | 0.5529 | 0.4104 | 0.7898 | 9 | weak |

## Claim Boundary

A positive DISC10 means passive visible signatures contain enough information to separate the synthetic hidden quotient; it is not a physical-mechanism claim and does not prove the likelihood learner can recover omega(j).
