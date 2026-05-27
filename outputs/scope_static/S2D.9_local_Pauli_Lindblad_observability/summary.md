# S2D.9 Local Pauli-Lindblad Observability

| run | decision | rank | condition | grouped ceiling | signatures | probes |
| --- | --- | ---: | ---: | --- | --- | ---: |
| phys9_setA | regression_pass | 10/10 | 9.582 | SKIP | False | 288 |
| phys9_multicircuit_setB_balanced | partial_identifiable | 10/10 | 9.582 | FAIL | False | 864 |
| phys9_multicircuit_setC_balanced | partial_identifiable | 10/10 | 9.582 | PASS | False | 864 |

## Phase Conclusion

- Label: `local_generator_observability_partial`
- Conclusion: The response Jacobian is identifiable, but recovery/signature evidence is incomplete.
- Next: `debug normalization, nuisance residualization, and generator decision geometry`
