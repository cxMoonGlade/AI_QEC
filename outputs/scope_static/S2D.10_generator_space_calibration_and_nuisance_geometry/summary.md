# S2D.10 Generator-Space Calibration And Nuisance Geometry

| run | decision | J rank | J cond | stage1 block acc | primary bal acc | real-scr bal gap | Mahalanobis bal acc |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| phys9_setA | failure | 10 | 9.5824 | 0.1250 | NA | NA | 0.0000 |
| phys9_multicircuit_setB_balanced | failure | 10 | 9.5824 | 0.2222 | 0.7778 | 0.4444 | 0.7778 |
| phys9_multicircuit_setC_balanced | partial_blockwise_or_geometry | 10 | 9.5824 | 0.5000 | 0.9167 | 0.5000 | 1.0000 |

## Phase Conclusion

- Label: `generator_space_calibration_partial`
- Conclusion: Generator coordinates contain useful blockwise or calibrated signal, but flat grouped recovery is incomplete.
- Next: `prefer hierarchical generator-space decisions; inspect residual pair-specific margins`
