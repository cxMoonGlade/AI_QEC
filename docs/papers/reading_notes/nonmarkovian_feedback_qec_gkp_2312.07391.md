# Full-text review — Puviani, Borah, Zen, Olle & Marquardt, "Non-Markovian feedback for optimized quantum error correction" (arXiv:2312.07391, PRL 134, 020601, 2025)

> **Provenance (2026-07-03): FULL-TEXT read (精读) via arXiv HTML v2 + supplemental
> material descriptions.** arXiv:2312.07391v2 [quant-ph], dated 20 Jan 2025 (v1: 12 Dec
> 2023); published as Phys. Rev. Lett. **134**, 020601 (2025). All section/figure/equation
> refs are from the main text (6 pp body + refs + 4 figures). The supplemental material
> (cited as [9]) was accessed via the PRL page description and ar5iv HTML rendering;
> its detailed Lindblad parameters and RNN architecture specs are summarized from
> the supplemental descriptions — not pixel-extracted from the SM PDF. **Note authored
> by Writer subagent (2026-07-03).** Tags: **[paper]** = stated in the paper; **[ours]** =
> our application/inference for `qec_twin`, NOT the paper's claim.

## Metadata [paper]

- **Authors / affiliation.** Matteo Puviani (corresponding: matteo.puviani@mpl.mpg.de),
  Sangkha Borah, Remmy Zen, Jan Olle, Florian Marquardt (corresponding:
  florian.marquardt@mpl.mpg.de) — all **Max Planck Institute for the Science of Light,
  Erlangen, Germany**; Borah and Marquardt also affiliated with **Friedrich-Alexander
  Universitat Erlangen-Nurnberg**.
- **Venue / status.** Phys. Rev. Lett. **134**, 020601 (2025); arXiv:2312.07391v2,
  20 Jan 2025. 6 pp body + references + 4 figures. Supplemental Material [9] covers
  GKP code background, Lindblad master-equation parameters, gate implementations,
  Feedback-GRAPE algorithm, and extended results.
- **Type.** Methods + numerical simulation. **Feedback-control optimization** for a
  **bosonic code** (GKP), using **model-based gradient descent through a differentiable
  quantum simulation** (Feedback-GRAPE) to train a **recurrent neural network** that
  implements a **non-Markovian QEC feedback policy**. Close companion paper: Porotti,
  Peano & Marquardt, "Gradient Ascent Pulse Engineering with Feedback," PRX Quantum **4**,
  030305 (2023), arXiv:2203.04271 — the Feedback-GRAPE method this paper applies.

## Executive summary [paper]

The paper demonstrates that a **non-Markovian (memory-based) feedback policy for GKP
quantum error correction, implemented by an RNN trained with model-based gradient
descent, more than doubles the logical state lifetime** (from `7.0e2` to `1.5e3`
cycle-times) compared to the standard sBs (small-BIG-small) protocol. The central
finding is that **Markovian (memoryless) feedback performs comparably to the standard
non-feedback protocol** — the performance gain is specifically attributable to the
**memory (non-Markovian) character**, not to feedback per se. The trained RNN learns
an interpretable strategy: its output control parameters evolve with an
"alternating exponential-like behavior" conditioned on past measurement outcomes,
reminiscent of an analytical decision tree. The result holds across multiple noise
levels, initial logical states, and in the presence of imperfect gates.

Structure of the argument:
- **Problem setting:** GKP code using the sBs measurement-based QEC protocol with a
  cavity coupled to an ancilla control qubit. Current protocols respond only to the
  **latest** measurement outcome.
- **Method:** Apply Feedback-GRAPE (Porotti et al., PRX Quantum 2023) — a **model-based**
  gradient-descent method that differentiates through the Lindblad master-equation
  simulation — to train an **RNN** that outputs 15 control parameters per QEC cycle
  conditioned on the **full history** of measurement outcomes.
- **Simulation:** Realistic Lindblad dynamics with experimental parameters from Sivak
  et al. (2023), including gate times, measurement/reset delays, and decoherence
  (T1, Tphi, cavity dissipation).
- **Result:** NMF (non-Markovian feedback) achieves 2.14x lifetime vs standard sBs;
  Markovian feedback (MF) does not outperform standard sBs — memory is essential.
  The gain is robust across noise levels and initial states.

## The system and method — EXACT form [paper]

### Physical system (Fig 1, Sec II)
A **bosonic cavity mode** coupled to an **ancilla transmon qubit**, controlled by four
elementary gates (Eickbusch et al., 2022):
1. **Echoed Conditional Displacement (ECD_{qc})** — complex parameter beta, entangles
   qubit and cavity.
2. **Qubit Rotation (R_q)** — real parameters phi, theta.
3. **Cavity Displacement (D_c)** — real parameter alpha.
4. **Cavity Virtual Rotation (VR_c)** — real parameter theta_VR.

The QEC cycle follows the **sBs (small-BIG-small)** protocol, matching the experimental
implementation of Sivak et al. (2023). Each half-cycle consists of: ancilla preparation
in |g>, 4 gate layers (qubit rotation + cavity displacement per layer), projective
measurement of the ancilla along z (outcome g or e), ancilla reset. Full cycle duration:
tau_cycle.

### QEC as a POMDP [paper]
The QEC task is a **quantum observable Markov decision process**: only the binary
measurement outcomes are observed; each observation alone is insufficient to determine
the best parameter set. The RNN integrates information over time, building an internal
belief state that approximates the full system state — this is the non-Markovian element.

### Return function and gradient [paper]
Goal: maximize the fidelity of the final density matrix to the initial logical state:

    R = F(rho_{Z_L}, rho(T))                                              (Eq, Sec II)
    F(sigma, rho) = [Tr{ (sqrt(sigma) rho sqrt(sigma))^{1/2} }]^2         (Eq, Sec II)

Weighted-average cumulative return over measurement trajectories m:

    <R(m)>_m = sum_m P(m) R(m)                                            (Eq, Sec II)

The gradient of the return w.r.t. RNN parameters theta (Eq 1):

    d<R(m)>_m / dtheta = < dR(m)/dtheta + R(m) d ln P_theta(m) / dtheta >_m   (Eq 1)

The first term is the straightforward derivative of the return; the second term captures the
dependence of the trajectory probability on the RNN parameters (the "reinforcement" term
from Porotti et al., PRX Quantum 2023). Automatic differentiation through the multi-step
Lindblad dynamics computes the gradient.

### Simulation [paper]
- **Forward:** Lindblad master equation for the collective cavity+ancilla dynamics with
  fixed time dynamics.
- **Parameters:** Experimental parameters from Sivak et al. (2023); includes qubit
  measurement and reset time, gate delays.
- **Decoherence channels:** Relaxation (T1), dephasing (Tphi), cavity dissipation (Ts)
  — fully specified in the Supplemental Material.
- **Leakage:** neglected (qubit assumed not to reach higher excited states).
- **Training:** 10 full QEC cycles at high noise level; RNN outputs 15 optimized
  parameters per cycle.
- **Evaluation:** 1000 full QEC cycles at multiple noise levels; >500 trajectories
  averaged; tested on different initial logical states without retraining.

### RNN architecture [paper, supplemented by Porotti 2023]
- **Type:** GRU (gated recurrent unit) cells — following Porotti et al. (2023) which
  used `tanh` activation, `sigmoid` recurrent activation, 30 neurons, and 2-4 output
  neurons for control parameters.
- **Input:** Latest binary measurement outcome m_i in {g, e}.
- **Output:** 15 control parameters for the QEC gate layers (ECD beta real/imaginary,
  qubit rotation phi/theta, cavity displacement alpha, virtual rotation theta_VR,
  distributed across 4 layers per half-cycle, with 2 half-cycles per full cycle).
- **Memory mechanism:** The RNN hidden state persists across cycles, carrying information
  about all prior measurement outcomes.

## Findings + numbers [paper]

### Lifetime result (Fig 3a)

| Protocol | Lifetime (T_Z / tau_cycle) | Gain vs standard |
|---|---|---|
| Standard sBs | 7.0e2 | — |
| **NMF (this work)** | **1.5e3** | **~2.14x (114% increase)** |
| MF (Markovian feedback) | ~7.0e2 (comparable to standard) | ~0% |
| Autonomous | shorter than standard | worse |

**Key qualitative finding:** Markovian feedback (feed-forward NN using only the latest
measurement outcome) does NOT outperform the standard non-feedback sBs protocol.
Memory itself is the performance driver — not feedback per se. This is the paper's most
important structural result for the twin.

### Other logical states (Fig 3a inset)
- |-X_L>: comparable lifetime to |+Z_L> (exact value not stated in main text).
- |-Y_L>: T_{-Y}(NMF)/tau_cycle = 7.7e2 — lower than |+Z_L>, described as "an expected
  feature of the square GKP code" (consistent with Campagne-Ibarcq 2020, Sivak 2023).

### Four-way comparison (Fig 3b)

Ordered by performance: **Autonomous < Standard sBs ~ Markovian Feedback (MF) < Non-Markovian Feedback (NMF)**.

The paper states: "Apparently, measurement based protocols are not intrinsically outperforming
the autonomous one under all circumstances, but they become strongly advantageous when
memory is exploited, as in our scheme."

### Error injection (Fig 3c)
- Displacement errors injected to initial |+Z_L> before QEC.
- Measured <Z_L> expectation value over 1032 trajectories.
- "Performance difference of our approach and the standard sBs is always positive."
- NMF reaches higher fidelity in shorter time.

### Learned strategy (Fig 4)
- Post-selected trajectory: 10 g outcomes, then 10 e outcomes, then 10 g.
- 15 RNN-optimized parameters tracked across cycles.
- Initial values "relatively close to the standard one" (dashed lines in Fig 4).
- Parameters "evolve over time with an alternating exponential-like behavior according
  to the previous measurement outcomes."
- Ground-state outcome probability p(g) ~ 0.9, same as standard approach — "experimentally
  desirable" (Sivak et al., 2023).
- Authors note the learned strategy could be converted into an analytical expression
  for simpler experimental implementation.

### Noise-level robustness
- Results verified at multiple noise levels: from low noise (Sivak et al., 2023) to
  higher noise (Campagne-Ibarcq et al., 2020).
- Also holds with imperfect gates.

## Methodology assessment [paper]

| Criterion | 1-5 | Assessment |
|---|---|---|
| Soundness | **4** | Model-based gradient descent through Lindblad dynamics is rigorous; the gradient formula (Eq 1) is derived in Porotti et al. (2023) and is exact for the discrete-measurement setting. Main limitation: the forward simulation is a Lindblad master equation with Markovian decoherence — the "non-Markovian" quality is only in the feedback policy (classical memory), not in the system-bath dynamics. The bath itself is Markovian. |
| Novelty | **4** | First application of non-Markovian (RNN-based) feedback to GKP QEC. The key finding that memory is essential (MF is no better than standard) is a clean, non-obvious result. However, the method (Feedback-GRAPE + RNN) is inherited from Porotti et al. (2023) — this is an application paper, not a new algorithm paper. |
| Reproducibility | **4** | Code available on GitHub (`Matteo-Puviani/GQF`); experimental parameters from published sources (Sivak 2023); methodology described. Minor minus: the hyperparameters of the RNN (layer count, neuron count per layer for THIS specific application) are not stated in the main text and need the Supplemental Material (which was not fully pixel-extracted here). |
| Experimental design | **3** | The comparison set (standard sBs, MF, NMF, autonomous) is well chosen and the lifetime results are clear. Weaknesses: (i) the paper does not systematically explore the RNN architecture space (what if the RNN is deeper/wider? what if memory length is truncated?), (ii) training only on 10 cycles while evaluating on 1000 is a significant extrapolation that needs more analysis (does the policy generalize in-distribution? what about out-of-distribution?), (iii) only one bosonic code (square GKP) is tested — claims of extension to other codes are stated but not demonstrated. |
| Statistical rigor | **3** | >500 trajectories averaged per point; trajectories shown as faded lines in Fig 3a. However: (i) no explicit error bars are plotted on the lifetime numbers in the main text; (ii) the 1032 trajectories for the error-injection test (Fig 3c) are stated but no confidence intervals are reported; (iii) no statistical test (e.g. bootstrap on the lifetime ratio) is presented. |
| Scalability | **2** | The method is demonstrated only for a single GKP mode (one logical qubit in one cavity). Scaling to multi-qubit QEC requires an entirely different simulation approach (the Lindblad master equation for a cavity does not scale to multi-cavity or multi-mode systems). The RNN output dimension (15 params/cycle) is small but the forward simulation cost is the bottleneck, not the RNN. No roadmap for scaling is discussed. |

## Strengths [paper]

- **S1 (Sec II, Eq 1, Fig 3a-b): clean isolation of memory as the performance driver.**
  The comparison MF vs NMF is controlled: same architecture except memory. The result
  that MF is no better than standard sBs, while NMF doubles the lifetime, proves that
  **the gain is from the non-Markovian character**, not from feedback optimization per se.
  This is the paper's strongest contribution — it sets a benchmark for what memory can
  buy in QEC.

- **S2 (Fig 4): the learned strategy is interpretable and potentially analytically
  distillable.** The RNN's output parameters evolve with "alternating exponential-like
  behavior" conditioned on past measurement outcomes. The authors explicitly note that
  this could be converted into an analytical decision policy — bridging the gap between
  black-box ML optimization and deployable experimental control. This is a rare and
  valuable quality for ML-in-QEC work.

- **S3 (Fig 3c): positive advantage under injected errors.** The error-injection test
  shows the NMF strategy provides benefit even for displacement errors (a different
  error type from the training distribution), suggesting some degree of robustness /
  generalization.

## Weaknesses / limitations [paper]

- **W1: The "non-Markovian" label applies to the feedback policy, not to the physics.**
  The system-bath dynamics are simulated as a **Lindblad master equation with Markovian
  decoherence channels** (T1, Tphi, Ts). There is no non-Markovian system-bath interaction,
  no memory kernel, no colored noise. The "non-Markovian" quality is purely in the
  **classical measurement-feedback loop** (the RNN hidden state). This is a fundamentally
  different kind of non-Markovianity from what the twin studies (environmental memory /
  time-correlated noise / coherent drift). The paper's title is technically correct
  (the feedback is non-Markovian) but potentially misleading for readers looking for
  non-Markovian *noise* physics.

- **W2: Training-evaluation extrapolation gap (10-cycle train, 1000-cycle eval).**
  The RNN is trained on trajectories of only 10 QEC cycles but evaluated on 1000 cycles.
  This is a 100x extrapolation in trajectory length. While the results hold, the paper
  does not analyze how the policy behaves in the extrapolation regime: does the RNN hidden
  state saturate or drift? Is there a maximum effective memory length? What happens at
  cycle 100 if all prior outcomes were g vs a mixed history? Without a memory-length
  ablation (e.g., truncating the RNN to the last N outcomes), the effective range of the
  learned memory is unknown.

- **W3: Single code, single system, no error model variation.**
  Only the square GKP code (one logical qubit, one cavity, one ancilla) is tested. The
  decoherence model is fixed to standard Markovian T1/Tphi/Ts. No study of how the NMF
  policy degrades under (a) non-Markovian noise, (b) parameter drift, (c) correlated
  errors, (d) qubit-coupling crosstalk — all of which are relevant to the twin's
  application domain. The claim of extension to other bosonic codes is plausible but
  undemonstrated.

- **W4: Feedback-GRAPE requires a differentiable forward model — it is NOT model-free.**
  The method requires full knowledge of the system Hamiltonian, Lindblad operators, and
  measurement process to compute gradients. This is feasible for a well-characterized
  single-cavity system but becomes prohibitive for multi-qubit surface-code setups where
  the noise mechanisms are themselves the unknown (this is exactly the twin's problem).
  So the approach does not transfer to the twin's setting as a method — it transfers only
  as a **result** (the prize of memory-enhanced QEC).

## What they do NOT do — for the twin novelty defense [paper / verbatim-absence]

1. **(i) NO non-Markovian system-bath physics.** The bath is Lindblad-Markovian (T1, Tphi,
   Ts with constant rates). There is no memory kernel, no 1/f noise, no colored spectrum,
   no quasi-static drift, no time-correlated coherent errors. The "non-Markovian" label
   is classical feedback memory, not quantum environmental memory. **The paper does not
   study, simulate, or claim results for non-Markovian noise environments.**

2. **(ii) NO syndrome / detection-event analysis; NO DEM; NO detector statistics.**
   The only measurement outcomes are the ancilla readouts used for feedback. There is no
   syndrome extraction layer, no detector-error model, no detection-event density analysis,
   no DEM estimation. The metric is **state fidelity** — not a logical error rate computed
   from a syndrome-decoding pipeline. The paper operates entirely at the level of
   physical qubit control, not at the level of QEC decoding.

3. **(iii) NO decoder, no frozen-decoder discipline, no do() intervention scoring.**
   Because the feedback policy directly controls the physical gates, there is no separation
   between "noise recovery" and "decoding." The twin's central framework (recover noise
   parameters, then score do()-DELER under a frozen decoder) does not appear and is not
   anticipated in this work.

4. **(iv) NO alias / identifiability analysis, NO uncertainty bands.**
   The RNN outputs a single deterministic policy. There is no characterization of how
   different policies could produce the same measurement statistics, no gauge / alias /
   model-uncertainty analysis. The twin's central methodological concern (observational
   vs interventional equivalence) is entirely absent.

5. **(v) NO surface-code / multi-qubit generalization.**
   The method is demonstrated on a single GKP logical qubit in one cavity. Scaling to
   multi-qubit surface codes would require a fundamentally different forward simulation
   and likely a different control architecture. No scaling roadmap is provided.

6. **(vi) NO code-capacity / circuit-level separation, NO distance dependence.**
   There is no study of how the NMF gain scales with code distance — because the GKP code
   does not have a "distance" parameter in the surface-code sense. The paper studies
   lifetime extension, not error suppression as a function of code size.

## Relevance to the twin [ours]

This paper serves three functions for the twin project:

### 1. The prize: non-Markovian QEC is a validated performance frontier.

The paper provides direct quantitative evidence that **memory-based feedback can more than
double logical state lifetime** in a bosonic QEC system. This motivates the twin's entire
program: if environmental memory (non-Markovian noise) causes performance degradation,
then characterizing and exploiting that memory structure (recover -> understand ->
manipulate -> predict) should yield proportionally large gains. The twin's goal is to
understand the *noise* structure that creates the non-Markovian dynamics; Puviani et al.
show the payoff for exploiting *measurement-record* memory. These are complementary
(non-Markovian noise -> need to understand it; non-Markovian feedback -> can exploit it),
and the twin's `predict` capability would be the natural bridge: predict the structured
noise evolution, feed it into a memory-aware decoder/controller.

### 2. Orthogonal axis: classical feedback memory vs environmental memory.

This paper is **not** about non-Markovian noise — it is about non-Markovian *control*
under Markovian noise. The twin studies the opposite: non-Markovian *noise* under
Markovian control (or fixed decoder). The two axes are orthogonal and complementary:
- Puviani: bath = Markovian Lindblad, controller = non-Markovian (RNN).
- Twin: bath = non-Markovian (colored/correlated/drift), decoder = Markovian (frozen MWPM).
Both can be true simultaneously in real hardware, and the frontier is when you have
both non-Markovian noise AND non-Markovian control. The twin currently occupies the
"non-Markovian noise, Markovian decoder" cell; this paper occupies "Markovian noise,
non-Markovian controller."

This orthogonality is important for positioning: **no collision, no pre-emption.**
The paper does not study what the twin studies, and vice versa. Citations should be
along the lines of "Complementary work by Puviani et al. [arXiv:2312.07391] shows the
performance gains available from non-Markovian feedback in bosonic codes, motivating
the twin's effort to characterize the noise structure that memory-aware controllers
could exploit."

### 3. Methodological distance: Feedback-GRAPE does not transfer to the twin's setting.

Feedback-GRAPE requires a **differentiable forward model** of the system — which is
exactly what the twin **does not have** in the real-hardware setting (the whole point of
recover is to discover the noise model from observations). The twin's forward model is
the learned parameterization itself; Puviani's forward model is a known Lindblad master
equation with known parameters. So Feedback-GRAPE is not applicable to the twin's
recover/manipulate capabilities as a method. It is relevant as a result / motivation /
validation target.

However, the **RNN-as-non-Markovian-policy** architecture could be relevant to the twin's
`predict` capability: if the twin recovers a non-Markovian noise model, the next step
is predicting the noise trajectory and adapting the decoder/controller accordingly.
The RNN structure that Puviani et al. use (GRU cells processing measurement outcomes)
could serve as the prediction head for the twin's drift model (Stage C, `predict`).

### 4. Specific citation use cases for the twin

| What to cite | How to use | Not to conflate |
|---|---|---|
| Lifetime doubling (1.5e3 vs 7.0e2 tau_cycle, Fig 3a) | The prize: quantitative evidence that memory-aware QEC has large headroom | The gain is from classical feedback memory under Markovian noise, NOT from environmental memory characterization |
| MF vs NMF comparison (Fig 3b) | Memory is the driver, not feedback per se — strong evidence for non-Markovian advantage | Does not imply anything about non-Markovian NOISE being the source of performance gain |
| Interpretable learned strategy (Fig 4, exponential-like parameters) | ML-discovered strategies can be distilled to analytical form | The specific strategy is GKP-specific and does not transfer to surface codes |
| Error-injection robustness (Fig 3c) | Some degree of out-of-distribution generalization | The test is still within the same single-cavity system; does not test cross-code or cross-error-type transfer |

## How to use / trust + open questions [ours]

- **Trust:** **High** for the qualitative result (memory-based feedback > Markovian feedback)
  and the lifetime numbers as stated. **Medium-high** for the quantitative lifetime ratio
  (2.14x) — the simulation is standard (Lindblad master equation, well-characterized
  parameters), but the 10-cycle training / 1000-cycle evaluation gap and the lack of
  explicit error bars on the lifetime numbers are mild concerns. The paper is from a
  respected group (Marquardt group at MPI Erlangen, known for quantum control and ML for
  quantum physics; Feedback-GRAPE is their own method).

- **Open questions (for discussion / further investigation):**
  1. What is the effective memory length of the learned RNN policy? Does the performance
     degrade if the RNN is truncated to the last N < ~10 outcomes? An ablation study
     (control = RNN, vary the recurrence depth or truncate backpropagation) would reveal
     how much history is actually useful. (Not done in the paper.)
  2. How does the NMF strategy change under non-Markovian noise (colored dephasing,
     1/f flux noise, quasi-static coherent rotation)? This is the intersection cell
     the twin targets — does RNN-based feedback still help when the noise itself has
     memory, or does the complexity compound?
  3. Can the learned strategy actually be converted into an analytical form, as the
     authors suggest? The exponential-like parameter trajectories in Fig 4 suggest a
     simple dynamical system (e.g., first-order IIR filter on past outcomes). If so,
     the paper would have a powerful secondary result: the optimal non-Markovian policy
     is a simple linear filter, not a complex RNN.
  4. Does the Feedback-GRAPE / RNN method scale to multi-qubit bosonic codes (e.g.,
     two-cavity GKP codes)? The Lindblad simulation cost grows with the cavity Hilbert
     space truncation, but more importantly the measurement space grows exponentially
     (2^N outcomes per round for N ancillary qubits). The RNN input would need a
     fundamentally different encoding.

- **Reading caveat (my review):** I read the main text (PRL 6 pp + 4 figures) in full
  from the arXiv HTML v2 and ar5iv rendering. The Supplemental Material [9] was
  described (not pixel-extracted) — its Lindblad parameters, RNN hyperparameters, and
  extended results are taken from the text descriptions. If the SM contains additional
  quantitative results (e.g., explicit RNN layer counts, convergence curves, hyperparameter
  scans), those would supplement this note. The companion paper Porotti et al. (PRX
  Quantum 2023) was used for the RNN architecture details (GRU cells, 30 neurons,
  tanh/sigmoid activations) from its public description.
