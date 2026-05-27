# S2D.11 Typed Gate/Readout/Prep Invariant Learner

SPAM is implemented as two explicit typed branches: `readout_branch` and `prep_reset_branch`.

| run | role | decision | bal acc | macro F1 | min recall | M5 split | M11 preflight | real-within gap | maha bal acc |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| phys9_multicircuit_setD_balanced | primary | failure_typed_branch_or_prep_design | 0.8689 | 0.8614 | 0.3333 | 1 | True | 0.6638 | 0.8462 |

## Phase Conclusion

- Label: `typed_gate_readout_prep_invariant_learner_negative`
- Conclusion: Typed branch structure did not beat required grouped controls or class-level criteria on set_D.
- Next: `inspect branch feature observability before adding probes`
