# GDISC15 Real Local Mechanism Discovery

- Selection rule: `heldout_excess_then_detector_mae_then_parameter_count`
- Selected model: `GDISC15_local_logit`
- True omega available: `false`

| model | params | ex_nll | det_ex | log_ex | det_mae | corr_err | log_cal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| local_full | 1341 | 0.007702 | 0.001996 | 0.01113 | 0.006762 | 0.005275 | 0.03119 |
| GDISC15_local_logit | 99 | 0.007706 | 0.001993 | 0.01114 | 0.00676 | 0.005277 | 0.03122 |
| GDISC15_local_logit_probability | 99 | 0.007711 | 0.001997 | 0.01114 | 0.006767 | 0.005276 | 0.03123 |
| GDISC15_multi_subsample_local_logit | 99 | 0.007765 | 0.001993 | 0.01123 | 0.006796 | 0.005297 | 0.03136 |
| GDISC15_pca_denoised_rank3 | 99 | 0.007765 | 0.001993 | 0.01123 | 0.006796 | 0.005297 | 0.03136 |
| GDISC15_pca_denoised_rank5 | 99 | 0.007765 | 0.001993 | 0.01123 | 0.006796 | 0.005297 | 0.03136 |
| GDISC15_pca_denoised_rank8 | 99 | 0.007765 | 0.001993 | 0.01123 | 0.006796 | 0.005297 | 0.03136 |
| GDISC15_pca_denoised_rank2 | 99 | 0.007787 | 0.002014 | 0.01126 | 0.006802 | 0.005296 | 0.03158 |
| GDISC15_pca_scores_rank3 | 99 | 0.007791 | 0.002022 | 0.01126 | 0.006793 | 0.005255 | 0.03198 |
| GDISC15_pca_scores_rank5 | 99 | 0.007791 | 0.002022 | 0.01126 | 0.006793 | 0.005255 | 0.03198 |
| GDISC15_pca_scores_rank8 | 99 | 0.007791 | 0.002022 | 0.01126 | 0.006793 | 0.005255 | 0.03198 |
| GDISC15_pca_scores_rank2 | 99 | 0.00788 | 0.002016 | 0.0114 | 0.006855 | 0.005319 | 0.03189 |
