# Stage 2A.0 Summary

- Result: `likelihood_match_without_partition_recovery`
- Outcome hint: `B_candidate_2A0_needs_recovery_biased_optimization`
- Source metrics: `outputs/scope_static/STAGE2A_full/metrics.json`

Success requires both high partition recovery and heldout NLL close to the matched known-orbit oracle.

## Main Matched-K `disc_hard`

| scenario | teacher | shots | K | mean ARI | mean NMI | mean dNLL known | collapses | result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| matched_k_exact | exact_orbit_separated | 2048 | 9 | 0.181 | 0.6386 | 0.004337 | 0 | likelihood_match_without_partition_recovery |

## Claim Boundary

This summarizes synthetic Stage 2A.0 free-assignment recovery only; it is not a physical mechanism discovery claim.
