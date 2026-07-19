# Project-fit audit — Schieffer et al. 2501.15939v1

Date: 2026-07-17
Source artifact: `outputs/papers/2501.15939.pdf`
Source SHA-256: `37e6238b971a87f3cdc06c098076f911131f9ae3829f7bd6e7f3f6f3858f8316`
Question: what implementation and performance evidence does the CUDA-Q MPS study establish, and
does its QAOA top-outcome check establish state, distribution, adaptive Record, or project-carrier
accuracy?

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Evaluated implementation | Secs. II–III and Table I, PDF pp. 2–3 | CUDA-Q's `tensornet-mps` and `tensornet` backends use cuTensorNet; the state-vector backend uses cuStateVec. The MPS runs use default `MAX_BOND=64`, absolute and relative cutoffs `10^-5`, and the default QR SVD algorithm. | These settings do not characterize Quimb, complex128 trajectory execution, or a custom fused MPS kernel. | closed for the named CUDA-Q stack |
| Measurement protocol | Sec. III-D, PDF p. 5 | Runtime experiments use `cudaq.sample` with 1,024 shots, one warm-up, and ten measured repetitions that recreate the circuit each time on one Grace Hopper Superchip. | This is not a kernel-only benchmark and does not isolate compilation, circuit construction, sampling, or state update costs. | closed with protocol boundary |
| Empirical scaling | Sec. IV-B and Fig. 5, PDF pp. 5–6 | For the measured high-qubit range, QAOA and Quantum Volume are fit by power laws while QFT and GHZ are fit linearly; MPS reaches 60 qubits for all four circuits and 90 for GHZ on the tested machine. | The fitted curves are not asymptotic complexity theorems or performance guarantees on other circuits, precisions, software versions, or GPUs. | closed as benchmark only |
| Small-circuit crossover | Sec. IV-A and Fig. 4, PDF pp. 5–6 | Where state-vector simulation fits, it is consistently faster than both TN methods; exact TN is faster than MPS below 12 qubits, and MPS is faster than exact TN after the observed 12-to-13-qubit transition. | The source does not show an MPS-versus-state-vector crossover at 12 qubits. | closed; prior stronger reading rejected |
| Profiling decomposition | Sec. IV-C and Fig. 6, PDF pp. 6–7 | On one 20-qubit QFT, 10-shot profile, exact TN is divided into 80% CPU-only and 20% CPU+GPU contraction time; MPS is divided into 22% CPU-only, 70% GPU SVD, and 8% CPU+GPU contraction time, with 33% average activity during the SVD phase. | These fractions are not shown to generalize beyond that single profiling workload. | closed as one profile |
| Transfer and Tensor Core observations | Sec. IV-C.2 and Fig. 7, PDF p. 7 | The MPS contraction interval is 45 ms versus 225 ms for exact TN; during 60% of the MPS contraction interval no kernels run while roughly 128-byte H2D transfers occur, and whole-execution Tensor Core utilization is below 1%. | The profile does not prove that transfers alone cause the idle interval, that operator fusion removes it, or that Tensor Cores are intrinsically unsuitable. | closed with causal boundary |
| Accuracy test definition | Sec. V and Fig. 8, PDF pp. 7–8 | The source compares 100,000-shot histograms for one 10-qubit QAOA circuit with random parameters and defines correctness through preservation of the four most-sampled state identities relative to state-vector sampling. | It reports no state norm, fidelity, trace distance, full-distribution TV/Hellinger/KL distance, confidence interval, or multi-seed stability analysis. | closed with narrow observable |
| Bond-cap result | Sec. V-B and Table III, PDF p. 8 | In the evaluated sweep, the top-four state set is retained at `chi_max=64,32,16`; at `chi_max<=15`, at most two reference top-four identities remain. | `chi_max=16` is not a universal accuracy threshold, and even in this experiment it certifies only the chosen top-four-set rule. | closed for one instance only |
| Conditional-circuit observation | Sec. IV-A, PDF p. 5 | The 12-qubit counterfeit-coin circuit takes 2.8 s with state vector, 4 min with exact TN, and 19 min with MPS; the authors suggest its intermediate measurements and conditional gates cause the slowdown. | This is one circuit and an attributed explanation, not an isolated measurement/reset cost model or a theorem about adaptive circuits. | closed as observation only |
| Detector Record bridge | Full-text scope, PDF pp. 1–10 | The source benchmarks standalone circuit sampling and one conditional circuit. | It defines no temporal detector fold, logical-observable bit, repeated-round Record law, independent Record oracle, or Record-distance certificate. | missing |

## Notation ledger

| source symbol or name | source meaning | domain or scope | fixed/variable |
|---|---|---|---|
| `chi` | MPS bond dimension | CUDA-Q pure-state circuit simulation | dynamically bounded |
| `chi_max` | maximum allowed bond dimension | approximation sweep in Sec. V | user-controlled |
| `CUDAQ_MPS_ABS_CUTOFF` | singular-value cutoff | CUDA-Q MPS configuration | default `10^-5` in experiments |
| `CUDAQ_MPS_RELATIVE_CUTOFF` | relative singular-value cutoff | CUDA-Q MPS configuration | default `10^-5` in experiments |
| entanglement ratio | `N_2q/N_total` gate-count ratio | five benchmark circuits | circuit-dependent proxy |
| GPU activity | fraction of GPU cycles with a nonempty compute pipeline | Nsight profile in Fig. 6 | measured profile statistic |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| five CUDA-Q circuits | sample with state-vector, exact-TN, and MPS backends | one Grace Hopper system; 1,024 shots; one warm-up and ten timed repetitions | runtime curves and executable-size observations | Sec. III-D; Sec. IV-A–B; Figs. 4–5, PDF pp. 5–6 | reproduced at protocol level |
| measured high-qubit runtimes | fit `t=alpha n^beta` or `t=an+b` by circuit family | fit only the plotted ranges | empirical scaling coefficients and `R^2` | Fig. 5, PDF p. 6 | reproduced |
| one 20-qubit QFT, 10-shot execution | profile CUDA/CPU activity with Nsight Systems and NVTX annotations | one warm-up and one profiled iteration | phase shares, kernel/transfer timeline, and Tensor Core observation | Sec. IV-C and Figs. 6–7, PDF pp. 6–7 | reproduced as one profile |
| one 10-qubit random-parameter QAOA | sample 100,000 shots with state vector and MPS | top-four state identities are selected as the correctness target | reference top-four set | Sec. V-A and Fig. 8, PDF pp. 7–8 | reproduced |
| same QAOA circuit | sweep `chi_max` and compare each top-four set to the reference set | other MPS controls retain their experiment settings | Table III match/failure pattern | Sec. V-B and Table III, PDF p. 8 | reproduced |
| profile with 128-byte H2D transfers | infer that a fused project operator will remove the measured idle time | no fusion experiment or project workload appears in the source | no source-supported speedup | Sec. IV-C.2, PDF p. 7 | blocked |
| top-four QAOA agreement | reinterpret as state, full-distribution, or adaptive-Record faithfulness | those metrics and objects are absent | no source-supported certificate | Sec. V; full-text boundary, PDF pp. 7–10 | blocked |

## Project application

The paper is useful as a performance-characterization precedent for the isolated CUDA-Q/cuTensorNet
surface, not as a direct benchmark of the restricted MPS implementation. The current restricted QT/MPS
and MCWF/MPS routes use different evolution laws, MPS mechanics, precision requirements, schedule parsing,
measurement/reset semantics, and acceptance rules. The paper supports only these narrow uses:

1. Reproduce phase-separated profiling on the actual project workload before optimizing: state update/SVD,
   contraction, host orchestration, transfer, circuit parsing, and Record materialization must remain separate.
2. Treat small-tensor GPU under-utilization and small H2D transfers as hypotheses to measure on the project
   route. The source does not establish operator fusion, launch-count reduction, or a performance gain.
3. Include conditional measurement/control workloads in performance characterization because the paper's
   single adaptive benchmark is dramatically slower, while preserving that this is not a causal decomposition.

The accuracy evidence does not meet the project contract. Preserving a top-four set on one QAOA histogram
cannot replace a declared standard distribution distance against an independent oracle, cannot validate the
complete temporal detector/observable Record, and cannot choose a production bond cap. The observed
12-to-13-qubit crossover is MPS versus exact TN, not MPS versus state vector, and must not be used to select the
project carrier for a similarly sized register.

The paper also does not specify an evidence-bearing complex128 comparison, state-error ledger, discarded-weight
accumulation rule, or complete adaptive multi-round Record. Its performance findings therefore remain
characterization inputs and do not affect scientific acceptance.

## Competing evidence and kill conditions

- Shao et al. 2606.00474v1 proves Hilbert–Schmidt/OEE statements for unconditional density-operator
  trajectories under restricted noise assumptions; that theorem-grade object is not Schieffer's empirical
  top-four pure-state sampling check.
- Werner et al. 1412.5746v2 derives a final-state trace-norm bound for a one-dimensional locally purified
  density carrier under canonical compression; Schieffer reports no analogous error certificate.
- Kill any claim that 33% SVD activity or 128-byte transfers are project measurements; both come from one
  20-qubit QFT CUDA-Q profile.
- Kill any fusion-speedup claim until the actual project route has a controlled before/after profile with identical
  precision, operator order, RNG semantics, and output law.
- Kill any universal `chi=16` rule: the source evaluates only the top-four set of one 10-qubit QAOA instance.
- Kill any state- or Record-faithfulness claim based on top-four agreement, histogram normalization, completed
  execution, or high qubit count.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- CUDA-Q implementation/profile row: closed for the named hardware and workload
- MPS scaling row: closed as empirical fit only
- accuracy row: closed only for the source-defined top-four-set observable
- state/full-distribution certificate row: missing
- adaptive detector Record row: missing
- project disposition: `implementation_profile_only_no_accuracy_certificate`
- current gate effect: no bond-cap choice and no restricted-MPS or Record-faithfulness upgrade
