# GDISC15 Real Local Mechanism Discovery

- Selection rule: `heldout_excess_then_detector_mae_then_parameter_count`
- Selected model: `GDISC15_local_logit`
- True omega available: `false`

| model | params | ex_nll | det_ex | log_ex | det_mae | corr_err | log_cal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| local_full | 1339 | 0.006514 | 0.001992 | 0.009241 | 0.007608 | 0.004995 | 0.01434 |
| GDISC15_local_logit | 98 | 0.006514 | 0.001994 | 0.009241 | 0.007606 | 0.004995 | 0.01433 |
| GDISC15_local_logit_probability | 98 | 0.006516 | 0.001992 | 0.009245 | 0.007611 | 0.004995 | 0.01438 |
| GDISC15_multi_subsample_local_logit | 98 | 0.00655 | 0.002009 | 0.009289 | 0.007647 | 0.005013 | 0.01449 |
| GDISC15_pca_denoised_rank3 | 98 | 0.00655 | 0.002009 | 0.009289 | 0.007647 | 0.005013 | 0.01449 |
| GDISC15_pca_denoised_rank5 | 98 | 0.00655 | 0.002009 | 0.009289 | 0.007647 | 0.005013 | 0.01449 |
| GDISC15_pca_denoised_rank8 | 98 | 0.00655 | 0.002009 | 0.009289 | 0.007647 | 0.005013 | 0.01449 |
| GDISC15_pca_scores_rank3 | 98 | 0.006554 | 0.001973 | 0.009317 | 0.007549 | 0.004969 | 0.01546 |
| GDISC15_pca_scores_rank5 | 98 | 0.006554 | 0.001973 | 0.009317 | 0.007549 | 0.004969 | 0.01546 |
| GDISC15_pca_scores_rank8 | 98 | 0.006554 | 0.001973 | 0.009317 | 0.007549 | 0.004969 | 0.01546 |
| GDISC15_pca_denoised_rank2 | 98 | 0.006564 | 0.002017 | 0.009307 | 0.007651 | 0.005021 | 0.01479 |
| GDISC15_pca_scores_rank1 | 98 | 0.006583 | 0.002031 | 0.009329 | 0.0076 | 0.005014 | 0.01578 |
