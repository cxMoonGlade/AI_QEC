# GDISC15 Real Local Mechanism Discovery

- Selection rule: `heldout_excess_then_detector_mae_then_parameter_count`
- Selected model: `GDISC15_structural_plus_graph_smoothed`
- True omega available: `false`

| model | params | ex_nll | det_ex | log_ex | det_mae | corr_err | log_cal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GDISC15_structural_plus_graph_smoothed | 98 | 0.005363 | 0.0017 | 0.007572 | 0.007401 | 0.005086 | 0.00626 |
| GDISC15_structural_plus_local_logit | 98 | 0.005457 | 0.001994 | 0.007545 | 0.007638 | 0.005124 | 0.006238 |
| local_full | 1339 | 0.005601 | 0.002508 | 0.007467 | 0.007768 | 0.005126 | 0.00656 |
| GDISC15_local_logit | 98 | 0.005601 | 0.002503 | 0.007469 | 0.007773 | 0.005126 | 0.006585 |
| GDISC15_local_logit_probability | 98 | 0.005604 | 0.002509 | 0.007471 | 0.007771 | 0.005128 | 0.006569 |
| GDISC15_multi_subsample_local_logit | 98 | 0.005604 | 0.002552 | 0.007446 | 0.007791 | 0.005144 | 0.004908 |
| GDISC15_pca_denoised_rank3 | 98 | 0.005604 | 0.002552 | 0.007446 | 0.007791 | 0.005144 | 0.004908 |
| GDISC15_pca_denoised_rank5 | 98 | 0.005604 | 0.002552 | 0.007446 | 0.007791 | 0.005144 | 0.004908 |
| GDISC15_pca_denoised_rank8 | 98 | 0.005604 | 0.002552 | 0.007446 | 0.007791 | 0.005144 | 0.004908 |
| GDISC15_pca_scores_rank1 | 98 | 0.005617 | 0.002613 | 0.007429 | 0.007809 | 0.005141 | 0.003455 |
| GDISC15_pca_denoised_rank1 | 98 | 0.005617 | 0.002613 | 0.007429 | 0.007809 | 0.005141 | 0.003455 |
| GDISC15_pca_scores_rank2 | 98 | 0.005649 | 0.002616 | 0.007479 | 0.007852 | 0.005172 | 0.003814 |
