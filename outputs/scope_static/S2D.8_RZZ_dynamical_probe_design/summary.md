# S2D.8a RZZ Depth Sweep

| run | decision | baseline v3c | S2D.7 static | depth features | scrambled depth | RZZ error ref/depth | boot NMI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| phys9_setA | regression_pass | 1.0000/1.0000 | 1.0000/1.0000 | 1.0000/1.0000 | 1.0000/1.0000 | 0/0 | 1.0000 |
| phys9_multicircuit_setB_balanced | failure | 0.9361/0.8284 | 0.9117/0.7359 | 0.9379/0.8199 | 0.9379/0.8199 | 3/4 | 0.8153 |
| phys9_multicircuit_setC_balanced | failure | 0.9177/0.7914 | 0.8878/0.7265 | 0.9300/0.8444 | 0.9300/0.8444 | 3/4 | 0.8052 |

## Phase Conclusion

- Label: `depth_sweep_control_matched_negative`
- Conclusion: RZZ depth sweep features are learner-visible and improve some global scores, but they match the scrambled-depth control and do not close the RZZ-family gap.
- Ruled out: `RZZ-family gap can be solved by depth-sweep final-shot response features alone.`
- Next: `S2D.8b_RZZ_echo_no_echo_probe_design`
