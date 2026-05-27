# S2D.7 RZZ Active Probe Design

| run | decision | baseline v3c | active probe-only | active moments+signed | scrambled | RZZ error base/active |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| phys9_setA | regression_pass | 1.0000/1.0000 | 1.0000/1.0000 | 1.0000/1.0000 | 1.0000/1.0000 | 0/0 |
| phys9_multicircuit_setB_balanced | failure | 0.9361/0.8284 | 0.9117/0.7359 | 0.9117/0.7359 | 0.9117/0.7359 | 2/6 |
| phys9_multicircuit_setC_balanced | failure | 0.9177/0.7914 | 0.8878/0.7265 | 0.8878/0.7265 | 0.8878/0.7265 | 3/6 |

## Freeze

- Label: `negative_static_mixed_basis_probe_result`
- Conclusion: Mixed-basis edge moments are learner-visible and leakage-clean, but they do not expose the missing RZZ-family mechanism signal.
- Ruled out: `RZZ-family gap can be solved by static mixed-basis edge moments computed from final shot bits.`
- Next: `S2D.8_RZZ_dynamical_probe_design`
