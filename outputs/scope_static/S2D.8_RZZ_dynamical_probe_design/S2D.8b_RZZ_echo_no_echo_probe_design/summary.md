# S2D.8b RZZ Echo / No-Echo

| run | decision | baseline v3c | S2D.7 static | S2D.8a depth | echo contrast | scrambled echo | RZZ error ref/echo | boot NMI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| phys9_setA | regression_pass | 1.0000/1.0000 | 1.0000/1.0000 | 1.0000/1.0000 | 1.0000/1.0000 | 1.0000/1.0000 | 0/0 | 1.0000 |
| phys9_multicircuit_setB_balanced | failure | 0.9361/0.8284 | 0.9117/0.7359 | 0.9379/0.8199 | 0.9247/0.7770 | 0.9266/0.7917 | 3/5 | 0.7728 |
| phys9_multicircuit_setC_balanced | partial_m1_m7_m10_improved | 0.9177/0.7914 | 0.8878/0.7265 | 0.9300/0.8444 | 0.9247/0.8189 | 0.9247/0.8189 | 3/2 | 0.7942 |

## Phase Conclusion

- Label: `echo_no_echo_mixed_control_limited`
- Conclusion: RZZ echo/no-echo paired contrasts give a partial RZZ-family improvement on one balanced run, but fail on the other and do not beat the scrambled-echo control.
- Ruled out: `current paired echo/no-echo final-shot contrasts as a sufficient RZZ-family fix.`
- Next: `S2D.8c_minimal_twirl_style_probes`
