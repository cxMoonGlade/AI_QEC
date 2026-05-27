# S2D.11b M1 Gate-Branch Grouped Calibration Audit

- Source: `outputs/scope_static/S2D.11_typed_SPAM_gate_invariant_learner/phys9_multicircuit_setD_balanced`
- Best variant: `typed_linear_plus_M1_logit_boost`
- Passed: `true`

| variant | status | bal acc | macro F1 | M1 recall | M8 recall | M10 recall | M11 recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_typed_linear | ran | 0.8689 | 0.8614 | 0.3333 | 1.0000 | 1.0000 | 1.0000 |
| typed_linear_plus_M1_logit_boost | ran | 0.8946 | 0.8927 | 0.6667 | 1.0000 | 1.0000 | 1.0000 |
| typed_linear_plus_axial_feature_reweighting | ran | 0.8689 | 0.8614 | 0.3333 | 1.0000 | 1.0000 | 1.0000 |
| compact_plus_selected_RZZ_dense_terms | ran | 0.8689 | 0.8586 | 0.3333 | 1.0000 | 1.0000 | 1.0000 |
| two_stage_gate_classifier | skipped: soft calibration passed or secondary diagnostic disabled | NA | NA | NA | NA | NA | NA |

## Error Type Split

| error type | recall | support |
| --- | ---: | ---: |
| gate | 1.0000 | 33 |
| readout | 0.9630 | 27 |
| prep_reset | 1.0000 | 3 |

## Verdict Checks

- `M1_recall_ge_0_65`: `true`
- `macro_F1_ge_0_80`: `true`
- `balanced_accuracy_ge_0_80`: `true`
- `real_minus_scrambled_ge_0_25`: `true`
- `M5_split_count_le_1`: `true`
- `M8_recall_drop_le_0_15`: `true`
- `M10_recall_drop_le_0_15`: `true`
- `M11_recall_drop_le_0_15`: `true`
- `M11_M4_margin_positive`: `true`
- `M11_M5_margin_positive`: `true`

## Interpretation

S2D.11b converts the S2D.11 strong partial into a pass; the remaining failure was gate-branch M1 calibration.
