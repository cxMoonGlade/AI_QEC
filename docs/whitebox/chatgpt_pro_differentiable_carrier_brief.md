# ChatGPT Pro research brief: can the d5/d7 white-box carrier be made differentiable?

> Purpose: this document is meant to be pasted into ChatGPT Pro, together with the Harper paper/note if
> possible. The goal is an adversarial research assessment of whether the deferred d5/d7 white-box
> carrier can supply useful gradients, or whether the grey-box architecture must settle for
> provenance-tagged response estimates instead of end-to-end differentiability.

## Request to ChatGPT Pro

You are being asked to act as a research collaborator, not as a cheerleader. Please assess whether the
white-box carrier described below can be made differentiable enough for inference and for a downstream
black-box GNN fusion layer. Give a technically grounded answer with explicit failure modes, not just a
high-level yes/no.

Please use the following epistemic tags in your answer:

- **exact**: theorem/identity/standard derivation that can be used as a premise.
- **prediction**: plausible but must be measured by a spike/experiment.
- **heuristic**: engineering decision or approximation; useful only with validation.

## Project context

The project is an AI-QEC digital twin for surface-code noise. The current architecture is grey-box:

1. A **white-box local recover model**: physically parameterized CPTP mechanisms inside a 3x3 data
   window. It should recover as much local mechanism structure as the data identifies, with honest
   Fisher/Godambe alias bands.
2. A **black-box GNN fusion layer**: composes local windows across seams / long-range residuals. The
   GNN should not be treated as a physics oracle; it should consume calibrated white-box outputs,
   uncertainty bands, overlap states, residual budgets, and possibly local response/gradient objects.

Build order:

1. **d3 white-box**: use nine standalone d=3 patches. Each patch is one complete 3x3 window, with 9
   data qubits and 8 full stabilizers, no seam. This validates local white-box recover performance.
2. **d7 seam/GNN**: use the real d=7 patch with 49 windows and real seams. This validates whether the
   local outputs help the black-box fusion layer.
3. **d5 validation**: post-d7 intermediate-scale sanity / interpolation rung.

The immediate theoretical problem is not d3. At d3, the current planned forward is a dense
surface-block Born likelihood on <=13q blocks, fit by a block-marginal composite likelihood. The
hard question is the later **d5/d7 carrier**, where dense density matrices are infeasible.

## d3 baseline: what is already separated from this question

At d3, the full faithful patch would be 9 data + 8 ancilla = 17q, too large as a dense density matrix.
The current plan avoids that by using <=13q blocks:

- state entering a round is the stationary state `rho_ss(theta)`;
- each block has 9 data + <=4 ancilla;
- compute exact block syndrome probabilities `P_theta(sigma_Tj | rho_ss(theta))`;
- fit the composite log-likelihood

```text
ell(theta) = sum_j log P_theta(sigma_Tj | rho_ss(theta)).
```

If built as planned, this d3 block likelihood can give exact/autograd gradients within the <=13q
dense oracle. That only certifies local white-box recover. It does **not** solve d5/d7 carrier
scaling, seam composition, or the GNN interface.

## Literature reference: Harper et al. 2605.29514

Please read/consider:

- Ben Harper, Azar C. Nakhl, Martin Sevior, Muhammad Usman, "Non-Clifford Crosstalk Noise in Surface
  Codes Using Hybrid Stabilizer-Tensor Network Methods", arXiv:2605.29514v1.
- Local reading note summary:
  `docs/papers/reading_notes/harper_nonclifford_crosstalk_surface_2605.29514.md`

Key facts from the paper/note:

- It is a **forward simulation** paper, not an inference/calibration paper.
- It represents a state as

```text
|psi> = C |MPS>,
```

where `C` is a Clifford operator/tableau and `|MPS>` carries the non-Clifford coherent perturbation.

- Clifford gates update `C` cheaply.
- A non-Clifford operator is expanded into Paulis, commuted through `C`, and applied to the MPS.
- A physically local Pauli string can become high-weight/non-local on the MPS after conjugation by `C`.
- Mid-circuit measurement collapses the non-Clifford error into a Pauli error in the Clifford tableau.
- The method uses bond truncation by SVD; Harper reports `chi_max = 32` for their forward simulations,
  with truncation giving lower-bound LER if too aggressive.
- The paper studies coherent ZZ crosstalk and compares to Pauli twirling. It shows coherence and
  coherent distribution matter, but it assumes known noise parameters and uses a Pauli decoder.

The useful part for us is the carrier idea: keep the ideal surface-code Clifford circuit in `C`, and
carry the coherent/non-Clifford error in an MPS/TN. The missing part is differentiable inverse
calibration.

## Candidate d5/d7 carrier designs

### Option A: pure-state trajectory carrier

This is the currently open candidate because it is the closest to Harper and is expected to scale.

Per shot / trajectory:

1. Keep a pure stabilizer-TN state `C_k |MPS_k>`.
2. Sample Kraus or stochastic branches where needed.
3. Absorb Pauli/Clifford noise branches into the tableau when possible.
4. Apply coherent/non-Clifford insertions to the MPS.
5. Truncate the MPS bond by SVD or another compression rule.
6. Sample or compute syndrome probabilities.

Advantages:

- avoids dense density matrices at d5/d7;
- per-shot MPS may carry only weak coherent perturbations;
- close to Harper's successful forward carrier.

Core problem:

- the fit objective `P_theta(syndrome)` is sampled / trajectory-averaged;
- gradients are not obviously low-variance or unbiased;
- coherent parameters may admit pathwise differentiation, but stochastic and non-unital CPTP
  mechanisms involve discrete branch choices with theta-dependent probabilities;
- SVD truncation and measurement branches may introduce bias or non-smooth gradients.

### Option B: deterministic Clifford-frame MPDO/MPO

This was attractive because it would carry the mixed state directly:

```text
rho_tilde = U_C^\dagger rho U_C
```

The ideal Clifford circuit is absorbed into the frame. Noise acts in the Clifford-conjugated basis.
The likelihood would be an exact differentiable contraction at full bond.

But an internal Spike A measured the framed MPDO bond at a real 13q d3 subsystem as about `chi = 162`,
only about 3x below the unframed 512, dominated by noise mixedness and expected to grow with distance.
So deterministic MPDO currently looks non-viable for d5/d7 under the hardware budget.

Hardware budget:

- one GPU around 32 GB;
- RAM around 60 GB;
- pilot tests should run in hours, not weeks;
- dense oracle is available only for <=13q validation.

## What the downstream GNN needs

The GNN does not necessarily need to backpropagate through the whole white-box solver. It needs useful
calibrated information. A good interface could include:

- `theta_hat`: recovered per-window mechanism parameters;
- `Sigma` / Godambe band: uncertainty and alias bands;
- identified/null-space masks from Fisher rank;
- `rho_BC`: overlap/seam reduced states;
- coherence budget: Pauli-twirl distance + unitarity;
- residual budget: what the white-box cannot close, e.g. long-range bunching / >4-stabilizer
  correlations;
- **local response object**: scores, Jacobians, finite-difference Greeks, or tangent-linear
  approximations, each with provenance and variance/bias bands.

Important distinction:

- Training the GNN's own weights can use stop-gradient white-box features.
- Counterfactual / physical gradients with respect to `theta` require a white-box response object, but
  that object does not have to be exact end-to-end autograd if a validated estimator is available.

## Research questions

Please answer these questions as concretely as possible.

### 1. Is Option A differentiable enough for inference?

Can a pure-state trajectory stabilizer-TN carrier provide an unbiased or controlled-bias estimator of

```text
grad_theta log P_theta(syndrome)
```

or of a composite/mini-batch NLL gradient?

Please consider:

- likelihood-ratio / score-function estimators for discrete Kraus/measurement branches;
- pathwise differentiation for coherent rotations where amplitudes depend smoothly on theta;
- reparameterization, Gumbel/relaxations, common random numbers, Rao-Blackwellization, or conditional
  expectation tricks;
- forward-mode/tangent propagation of `d|MPS>/dtheta` along a fixed trajectory;
- adjoint/backprop through MPS contractions;
- whether differentiating the sampled trajectory gives the gradient of the desired likelihood or only
  a surrogate objective;
- whether estimating `P_theta(s)` and `grad P_theta(s)` separately, then forming
  `grad log P = grad P / P`, is statistically feasible for rare syndromes.

### 2. How should SVD/bond truncation be handled?

Please analyze:

- fixed-rank truncated SVD differentiation and non-smoothness at singular value crossings;
- whether truncation bias contaminates gradients even if forward probabilities look converged;
- soft truncation / smooth cutoff / randomized SVD / canonical MPS gauge choices;
- whether one should use straight-through, stop-gradient on truncation, tangent-space projection, or
  TDVP-like methods;
- what validation would detect gradient bias from truncation.

### 3. Are there better alternatives than Option A?

Please compare with at least:

- locally purified tensor networks / purification MPS;
- MPDO/MPO with aggressive compression or noise-tail decomposition;
- perturbative expansion in small coherent angle `theta ~ 1e-3`;
- Pauli baseline plus coherent correction / influence functions;
- differentiable surrogate trained against the dense <=13q oracle;
- simulation-based inference or neural ratio/score estimation;
- SPSA / finite differences / random-direction derivatives as the response object;
- implicit differentiation through the optimizer only at d3, with stop-gradient features at d7;
- hybrid: exact d3 gradients + approximate d7 response bands.

For each, state expected exactness, bias, variance, scaling, implementation burden, and fit with the
GNN interface.

### 4. What is the minimal viable gradient object for the GNN?

If end-to-end differentiability is unrealistic, define the weakest useful object the white-box should
export to the GNN. For example:

```text
Response_w = {
  theta_hat_w,
  Sigma_w,
  identified_mask_w,
  null_space_basis_w,
  rho_BC_w,
  score_estimates_w(obs),
  Jacobian_or_Greeks_w with variance/bias bands,
  unavailable_direction_mask_w
}
```

Please say which parts must be exact, which can be estimated, and which must be explicitly marked
unavailable.

### 5. What spikes should be run before committing?

Design a small experimental sequence using the <=13q dense oracle:

- gradient correctness checks: autograd vs finite difference vs trajectory estimator;
- variance scaling with number of trajectories;
- bias from truncation at different `chi`;
- common-random-number finite differences or SPSA;
- Fisher rank / identified directions stability;
- controlled-teacher recovery coverage under Godambe bands;
- runtime/memory gates for a d5/d7 pilot.

Please give concrete pass/fail gates where possible.

## Desired output format

Please structure your answer as:

1. **Executive verdict**: likely feasible, conditionally feasible, or unlikely, with one paragraph of
   reasoning.
2. **Main technical obstacle**: the single hardest issue.
3. **Ranked candidate methods**: table with exactness, bias, variance, scaling, implementation cost,
   and recommendation.
4. **Best candidate derivation**: formulas for the gradient estimator or tangent propagation.
5. **Validation/spike plan**: minimal experiments and pass/fail criteria.
6. **Recommended interface to the GNN**: what white-box response object should be exported.
7. **Red flags**: signs that the direction should be abandoned or downgraded.
8. **References to check**: papers/keywords for differentiable quantum trajectories, tensor-network
   gradients, truncated SVD differentiation, likelihood-ratio estimators, and stabilizer-TN methods.

Please be explicit when something is unknown or likely hard. The desired outcome is not optimism; it
is a reliable decision about whether a differentiable white-box carrier is a credible research path.

