# GDISC15 Real Local Mechanism Discovery

- Selection rule: `heldout_excess_then_detector_mae_then_parameter_count`
- Selected model: `GDISC15_pca_scores_rank3`
- True omega available: `false`

| model | params | ex_nll | det_ex | log_ex | det_mae | corr_err | log_cal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GDISC15_pca_scores_rank3 | 99 | 0.006583 | 0.002118 | 0.009266 | 0.00706 | 0.005075 | 0.002853 |
| local_full | 1341 | 0.006611 | 0.002127 | 0.009305 | 0.007211 | 0.005092 | 0.00447 |
| GDISC15_local_logit | 99 | 0.006612 | 0.002127 | 0.009307 | 0.00721 | 0.005092 | 0.004418 |
| GDISC15_local_logit_probability | 99 | 0.006613 | 0.002127 | 0.009308 | 0.007206 | 0.005089 | 0.004462 |
| GDISC15_pca_scores_rank1 | 99 | 0.006638 | 0.002132 | 0.009345 | 0.007293 | 0.005111 | 0.003334 |
| GDISC15_pca_denoised_rank1 | 99 | 0.006638 | 0.002132 | 0.009345 | 0.007293 | 0.005111 | 0.003334 |
| GDISC15_multi_subsample_local_logit | 99 | 0.006652 | 0.002137 | 0.009364 | 0.007293 | 0.005116 | 0.004139 |
| GDISC15_pca_denoised_rank3 | 99 | 0.006652 | 0.002137 | 0.009364 | 0.007293 | 0.005116 | 0.004139 |
| GDISC15_pca_denoised_rank2 | 99 | 0.006662 | 0.002166 | 0.009363 | 0.007323 | 0.005128 | 0.004011 |
| GDISC15_pca_scores_rank2 | 99 | 0.006716 | 0.002161 | 0.009453 | 0.00734 | 0.005137 | 0.00333 |
| GDISC15_structural_plus_graph_smoothed | 99 | 0.006846 | 0.002306 | 0.009574 | 0.007168 | 0.005157 | 0.004005 |
| GDISC15_structural_plus_local_logit | 99 | 0.006877 | 0.002333 | 0.009608 | 0.007202 | 0.005144 | 0.003999 |
