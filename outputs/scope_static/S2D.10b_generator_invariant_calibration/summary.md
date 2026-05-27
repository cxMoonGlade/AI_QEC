# S2D.10b Generator Invariant Calibration

| run | decision | primary bal acc | macro F1 | min recall | real-scr bal gap | M1/M7 acc | Mahalanobis bal acc |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| phys9_setA | failure | NA | NA | NA | NA | NA | 0.0000 |
| phys9_multicircuit_setB_balanced | success | 0.8889 | 0.8857 | 0.6667 | 0.5556 | 0.8333 | 1.0000 |
| phys9_multicircuit_setC_balanced | success | 1.0000 | 1.0000 | 1.0000 | 0.5000 | 1.0000 | 1.0000 |

## Phase Conclusion

- Label: `generator_invariant_calibration_positive`
- Conclusion: Learner-visible scalar invariants resolve balanced setB/setC generator-space recovery.
- Next: `promote scalar invariants into the physical generator learner representation`
