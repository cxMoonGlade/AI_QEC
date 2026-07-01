# Full-text note — Chamberland et al., *Fast and Accurate AI-Based Pre-Decoders for Surface Codes* (NVIDIA)

> Chinese reading companion (non-canonical, for side-by-side reading): [chamberland_ai_predecoder_surface_code_2604.12841.zh.md](chamberland_ai_predecoder_surface_code_2604.12841.zh.md)

> Provenance: full-text read from the PDF `F:\Downloads\2604.12841v1.pdf`
> (owner-password-only encryption stripped with `pikepdf`, empty password),
> converted with `pdftotext -layout` and cached at `docs/papers/2604.12841v1.txt`.
> arXiv:2604.12841v1 [quant-ph], 14 Apr 2026. Code: GitHub · Models: Hugging Face.

---

## 1. Metadata

- **Authors.** Christopher Chamberland, Jan Olle, Muyuan Li, Scott Thornton, Igor Baratta (NVIDIA Corporation, USA). The first three are marked equal main contributors.
- **Venue / status.** arXiv preprint, April 2026. Open source (GitHub repo + Hugging Face model weights).
- **Object.** A **modular AI pre-decoder** for the rotated surface code that performs **local, parallel space–time error correction**, removing most physical errors before a **downstream global decoder** (PyMatching) finishes the job — plus a separate **noise-learning network** that infers matching-graph weights from **syndrome statistics alone**.
- **Headline result.** End-to-end decoding at **O(1 µs)/round** at large code distance on **NVIDIA GB300** GPUs (FP8), **while simultaneously lowering the logical error rate (LER)** relative to the global decoder alone. Claimed first demonstration of *both* LER and full end-to-end speedup vs a state-of-the-art global decoder.
- **Lineage.** Direct successor to Chamberland–Goncalves *et al.* (ref [9], "combining fast local decoders with global decoders", QST 2023) and the Gicev–Hollenberg–Usman fully-convolutional 3D decoder line (refs [22,23]). Parallel-window decoding from Skoric *et al.* (ref [10]) and Tan *et al.* (ref [11]). Learned-global-decoder comparators cited but **not** benchmarked head-to-head: AlphaQubit (Bausch *et al.*, ref [16], Nature 2024) and the real-time neural decoder of Senior–Bausch *et al.* (ref [17], 2512.07737).

**One-sentence takeaway.** This is an *engineering* paper: it keeps the optimal/heuristic global decoder (MWPM) and bolts a fast, local CNN in front of it to shrink the syndrome the global decoder must process; the scientific seasoning is (a) careful label engineering and (b) a distance-independent, differentiable noise-parameter learner — and that second piece is essentially the "learner-as-DEM" idea, executed simulator-only.

---

## 2. Executive summary

The paper has **two architecturally distinct neural networks** that should not be conflated:

**Model A — the pre-decoder** (Section IV). A fully-convolutional **3D CNN** mapping a space–time syndrome volume `(d, d, dm)` to **local Pauli + measurement corrections** of the same shape. It is trained by **supervised binary cross-entropy on simulated error labels** (i.e. you must *know the true error*, hence simulator-only). Its job is not to decode the logical outright but to **reduce the syndrome density `s`** passed to a global decoder. Because the runtime of MWPM scales as `O(s³)` (Union Find `O(s)`), cutting `s` by 1–2 orders of magnitude makes the global decoder dramatically faster; the residual is cleaned up by PyMatching. Most of the genuine novelty is in the **training-label engineering** (Algorithms 1–3: timelike-component isolation, fault deferral, Y-decomposition, and spacelike/timelike homological-equivalence canonicalization) that prevents artificial timelike events and shrinks label complexity so the CNN can learn.

**Model B — the noise-learning network** (Section V). A **2D CNN → global-average-pool → MLP** that ingests the statistics of **two consecutive bulk syndrome rounds** (averaged over many shots) and outputs **25 circuit-level noise parameters**. These feed **closed-form, distance-independent, differentiable probability formulas** for all **18 edge types and 43 hyperedge-type compositions** of the surface-code matching graph, producing a **detector error model (DEM)** for PyMatching (both uncorrelated edges and correlated two-pass hyperedge reweighting). Crucially the loss is a **supervised MSE between predicted and *ground-truth* edge/hyperedge probabilities** computed from the known simulator parameters — so training needs a simulator, but *inference* needs no explicit noise model and generalizes across code distance (because the formulas are distance-independent and the pooling is distance-preserving).

**Results posture (honest reading).**
- Pre-decoder + **uncorrelated** PyMatching: LER improvement up to **4.66×** at d=31 (Model 5, p=0.006) and **3.4–3.5× end-to-end speedup** — but the baseline here is *uncorrelated* matching, the **weak** baseline. At lower p (0.003) the light Model 1 can *hurt* LER (down to 0.70×).
- Pre-decoder + **correlated** PyMatching (the stronger baseline): the small models make LER *worse*; only a much larger 42.6M-param ResNet (Model 6) beats correlated matching, and **only up to d ≤ 13** (at d ≥ 17 it is slightly worse, gap widening as p falls).
- Noise-learning net: **recovers near-optimal weights**. For uncorrelated matching it **slightly under-performs** the true-parameter DEM (a gauge/identifiability fact — see §6.5/§9); for correlated matching it can **slightly beat** the true-parameter DEM (the two-pass heuristic is not optimally fed by true probabilities). Applied to pre-decoder residuals it yields **no gain** (residual errors have a pathological string structure).

The robust, defensible contribution is **speed at scale with no LER regression vs uncorrelated matching**, plus a **clean, reusable, differentiable DEM parameterization**. The "beats the strong baseline" story is narrow (d ≤ 13).

---

## 3. Problem setting and motivation (Sections I, III)

Real-time fault tolerance imposes a hard runtime budget: if the per-round decode time `T_DEC` exceeds the stabilizer-measurement time `T_s`, an **exponential backlog** of unprocessed syndromes accrues (Terhal ref [8]; Chamberland *et al.* ref [9]). Sliding-window decoding needs roughly **O(1 µs)/round**, which is hard for classical MWPM at the syndrome densities seen near threshold. Parallel-window decoding (refs [10,11]) splits the syndrome history into **commit** regions (size `dm`) flanked by **buffer** regions, decoded concurrently; it removes the backlog provided enough parallel resources `N_par ≥ 2 T_DEC / [(T_l + T_s)(n_com + n_W)]` (Eq. 4). But total runtime still scales with `T_DEC`, which for MWPM scales as `O(s³)` in the **syndrome density**

```
s = |Syn| / (dm · S(d)),   S(d) = d² − 1 stabilizers per round.    (Eq. 2)
```

**Key lever:** reduce `s` *before* the global decoder. An AI pre-decoder has **fixed cost independent of `s`** (a CNN forward pass), so the pipeline cost is `T_s + T_l1 + T_DEC^pre(r) + T_l2 + T_DEC^al(r, s')` (Eq. 6) with reduced density `s' ≪ s`. A net speedup occurs whenever the global-decode savings exceed the pre-decoder + communication overhead (Eq. 7). This is the paper's central economic argument: the pre-decoder buys global-decoder speed.

Surface-code primitives used throughout: detector events `d_{i,k} = s_{i,k} ⊕ s_{i,k−1}` (Eq. 9); full syndrome `Syn = (SynX^(1), SynZ^(1), …)` (Eq. 1); threshold ≈ 0.7% for the circuit-level depolarizing model (Eq. just below Eq. 4); rotated patch `[[d², 1, d]]` with a gate schedule (Fig. 2) chosen so a single fault's weight-2 error propagates *perpendicular* to its logical.

---

## 4. Contributions (claim → evidence → strength)

1. **Pre-decoder with joint spacelike + timelike corrections** (claim: a fully-conv 3D CNN can jointly predict data-qubit Pauli and measurement corrections across the whole space–time volume, backend-agnostic to the global decoder). *Evidence:* architecture in §IV B + Fig. 4; new label-processing Algorithms 1–3. *Strength:* **strong** — the architecture is standard, but the label engineering is the real, well-justified novelty.
2. **Simultaneous LER improvement *and* end-to-end runtime reduction** (claim: first to do both vs a SOTA global decoder). *Evidence:* Tables IV–VIII; Fig. 13, 19. *Strength:* **moderate-to-strong but baseline-qualified** — clearly true vs *uncorrelated* matching at d ≥ 21; vs *correlated* matching only d ≤ 13 and needs the 42.6M-param Model 6.
3. **GPU deployment / benchmarking** (5 architectures, FP8, GB300, TensorRT; up to **3.42×** total speedup uncorrelated, **3.5×** correlated at d=31, p=0.006). *Evidence:* §VI C, Tables VII–X. *Strength:* **strong** (the paper's most solid contribution).
4. **Noise-learning architecture from syndrome statistics** (claim: infer near-optimal edge + hyperedge weights from syndrome stats with no explicit noise model, generalizing across distance via 18 edge + 43 hyperedge distance-independent formulas). *Evidence:* §V, §VI E, Fig. 20, Appendix A. *Strength:* **conceptually strong, empirically modest** — recovers ≈ true weights (slightly under for uncorrelated, slightly over for correlated).
5. **Resource reduction via batching** (up to **12.5×** fewer `N_par`). *Evidence:* §VII, Table XIII. *Strength:* **moderate** (an engineering throughput knob; the 12.5× costs 80% slower `T_DEC`).

---

## 5. Model A — the pre-decoder (Section IV)

### 5.1 Architecture (§IV B)
- **Fully convolutional 3D CNN** — only 3D conv layers, no dense/projection layers, so the output keeps the input's space–time shape and corrections are *local everywhere in the volume*. Trained on `(d, d, dm)` and applied at inference to *different* `(d', d', d'm)` (the scalability claim).
- **Receptive field** `R_l = 1 + Σ_i (k_i − 1)` (Eq. 8) sets the **maximum effective decoding distance** — error chains longer than `R_l` cannot be corrected locally. Depth and kernel size both grow `R_l`; the paper shows **increasing kernel size costs runtime much more than depth** (§VI C), motivating deep/small-kernel designs.
- **Model zoo (Table II):** Model 1 `[128,128,128,4]` k=3 (RF 9, 0.91M params, fastest); Model 2 widens to 256 (3.6M); Model 3 k=5 (RF 17, 4.2M, slow); Model 4 six layers k=3 (RF 13, 1.8M); Model 5 six layers ×256 (RF 13, 7.1M, highest capacity of the five); **Model 6** (Fig. 15) is a separate 8-layer 3D **ResNet** with skip connections, 4 residual blocks 4→512→…→4, RF 17, **42.6M params**, used only for the correlated-matching regime.

### 5.2 Input encoding — 4 channels (§IV B 1)
For a `D × D` grid per round (`D` = max data qubits per row/col):
- **Channel 1–2:** X-type and Z-type **detector events** mapped to the grid (weight-4 stabilizers → top-left/top-right data qubit; weight-2 boundary → top/right). Value 1 if the stabilizer outcome changed between consecutive rounds, else 0 (Eqs. 15–16, Fig. 5).
- **Channel 3–4:** `x_present`, `z_present` — **normalized stabilizer-weight geometry** (Eqs. 17–18), encoding boundary-vs-bulk structure and, importantly, zeroed appropriately during logical init (round 1) and final measurement (round `dm`) depending on basis (Eqs. 19–20). This hands the network explicit geometric priors so it need not relearn the lattice.

### 5.3 Output targets — 4 channels (§IV B 2)
- **Channel 1–2:** spacelike **Z̃, X̃** data-qubit Pauli corrections, defined as the *error difference between consecutive rounds* `X̃_{i,k} = E(X)_{i,k} ⊕ E(X)_{i,k−1}` (Eqs. 12–14, 21–22).
- **Channel 3–4:** **timelike** stabilizer-flip corrections for X- and Z-type stabilizers, defined only for `k = 1 … dm − 1`.

### 5.4 The real novelty — label engineering (§IV B 2–4)
This is where the paper earns its keep; naive labels poison the CNN.
- **Algorithm 1 (timelike-component isolation).** Propagate the round-`k` faults to get syndrome `s1`; propagate the *resulting data-qubit errors* through one more round to get `s2`; the timelike label is `s1 ⊕ s2`. Two-stage propagation cancels the persistent spacelike effect and isolates the *pure* timelike contribution (Fig. 6).
- **Algorithm 2 (fault deferral).** Only update `trainY` when a fault produces a **non-trivial syndrome in the same round**; otherwise **defer** its data-qubit error into round `k+1`'s input. Prevents "spurious vertical pairs" — an error created in round `k` but only *visible* in `k+1` would otherwise create an artificial timelike event and teach the network to correct in the wrong round.
- **Y-decomposition (Table I).** All Y-containing two-qubit faults (always data⊗ancilla after a CNOT) are rewritten into X/Z-only equivalents (e.g. `YZ → ZZ ⊕ XI`) so detection events localize correctly in time.
- **Spacelike homological equivalence (Fig. 8).** `weightReduction` + `fixEquivalence`: pick a canonical representative per homology class (reduce a weight-3 error on a stabilizer to weight-1 via the stabilizer; remove weight-4; canonicalize vertical/horizontal/diagonal chains and boundary cases). Iterated to convergence (Eq. 25).
- **Algorithm 3 + timelike homological equivalence (Figs. 9–11).** Adding an X/Z error to the same data qubit in *two consecutive rounds* together with the anticommuting measurement errors in the first round can be a **trivial operation** (no net syndrome change). Exploiting this gauge freedom simplifies `trainY` into structure CNNs learn more easily. The full protocol interleaves spacelike → timelike → spacelike-cleanup passes (Fig. 11). During training they restrict to **weight-one** timelike corrections (found best).

### 5.5 Loss and inference (§IV B 5–6)
- **Loss:** per-voxel per-channel **binary cross-entropy** with sigmoid heads, `4 D² dm` terms (Eq. 43). The network outputs independent per-voxel correction probabilities.
- **Inference:** apply the predicted spacelike + timelike corrections to the measured syndrome history → **residual syndromes** `R^(j,k)` (Eqs. 50–53) → global decoder. The pre-decoder already fixes some logicals (sign `S_L^(1)`); the global decoder fixes the rest (`S_L^(2)`); final logical sign `S_L = S_L^(1) ⊕ S_L^(2)` (Fig. 3). A logical error is declared if accumulated `L(X)`/`L(Z)` (Eqs. 56–57) anticommutes with the logical operator.

---

## 6. Model B — noise-learning from syndrome statistics (Section V)

### 6.1 Motivation (§V intro)
Real devices may have **unknown or drifting** noise, and—even with a known model—**applying a pre-decoder changes the syndrome statistics**, so PyMatching's noise-model-derived weights become **suboptimal**. Hence: infer effective decoding weights **directly from syndrome data**.

### 6.2 Architecture (§V A, Fig. 12, Table XII)
- Input tensor `(B, 4, 2, D, D)` — the 4 channels from §5.2 over **two consecutive bulk rounds** (middle of the experiment, avoiding init/final boundary effects).
- **2D CNN** (4 layers `[128,256,256,128]`, 3×3, GroupNorm-32, GeLU, dropout on last layer) → **global average pooling** `g_c = (1/D²) Σ_{x,y} H_{c,x,y}` (Eq. 58) — *distance-preserving*: pooled features have fixed dim regardless of `d`.
- **3-layer MLP** `[256,128,25]` per sample → logits `z_k ∈ R²⁵` (Eq. 59), **averaged across the batch/shots** `z̄ = (1/B) Σ z_k` (Eq. 60), then a **bounded log-space transform** (Eq. 61) maps to 25 probabilities spanning `[p_min/100, 3 p_max]` (with `p_min=10⁻³`, `p_max=10⁻²`). Post-MLP logit averaging means every shot contributes its own estimate before aggregation; the same aggregation is used at train and test (no train–test mismatch). ~1.26M params total.

### 6.3 The 25-parameter circuit noise model (Appendix A.1)
2 state-prep (`PSX`, `PSZ`) · 2 measurement (`PmX`, `PmZ`) · 3 idle-during-CNOT single-qubit Pauli · 3 idle-during-SPAM single-qubit Pauli · **15 CNOT two-qubit Pauli** `P_CX^(P_i P_j)` for each non-identity `P_i⊗P_j`. PyMatching edge weight `w = −log P`.

### 6.4 Distance-independent edge/hyperedge formulas (§V B, Appendix A)
The crux that enables single-distance training → arbitrary-distance inference: edge probabilities depend only on **local stabilizer geometry, not global code size**, so the *functional form* is identical for all `d ≥ 5`; only the **count** of each type scales with `d`.
- **18 edge types** per basis: **3 spacelike (S1–S3), 4 timelike (T1–T4), 5 diagonal (D1–D5), 6 boundary (B1–B6)** (Appendix A.2). Each is an **XOR combination** `P1 ⊕ P2 = P1 + P2 − 2 P1 P2` (Eq. A1) of the Pauli probabilities that flip the same detector pair (some boundary formulas have 50–68 XOR components over dozens of detector patterns — A.3.d). The Z-graph formulas follow from the X-graph by X↔Z symmetry (A.4).
- **43 hyperedge type compositions** for **correlated** two-pass matching, where conditional probabilities `P(E2 | E1) = P_joint / P(E1)` reweight edges after a first matching pass. All 86 types derived at d=5 cover those observed at d = 5,7,9,11,21,31, **verified against Stim's DEM** (A.5).
- All formulas are **fully differentiable** (only `+`/`×`), enabling gradient training to the matching weights.

### 6.5 Loss — supervised regression to *known* probabilities (§V C)
`L = L_edge + L_hyper`, both **count-weighted MSE between predicted and ground-truth edge/hyperedge probabilities** derived from the *known* simulator parameters (Eqs. 64–65). A **variance-stabilizing weight** `w(p) = (p0/p)²` with `p0 = √(p_min p_max)` corrects the log-uniform sampling bias (Eqs. 66–68; "unbiased" loss). Hyperedge terms **break the parameter degeneracy** of edge-only fitting (a built-in identifiability regularizer). **Important:** the net regresses to the *identifiable* observable (edge/hyperedge probabilities), **not** the raw 25 parameters — implicitly handling the gauge that the project would call the alias quotient.

### 6.6 Training / inference (§V D–E)
- **Training:** on-the-fly GPU **Pauli-frame** simulator; per step sample a base rate log-uniform on `[10⁻³,10⁻²]`, derive 25 params with location-specific random multipliers + random Pauli-type splits, generate `B` syndrome samples, predict `p̂`, minimize MSE through the differentiable formulas. AdamW + EMA; 250 random `p`-vectors × 4096 shots/epoch; trained at d = 21, 31 on 32 GPUs (Table XII).
- **Inference:** trained net → 25 params → build a **Stim** circuit → **DEM** (`decompose_errors=True`, `approximate_disjoint_errors=True`) → PyMatching (uncorrelated edges and/or correlated hyperedge conditionals).

---

## 7. Results (Section VI–VII)

### 7.1 Syndrome-density reduction + uncorrelated PyMatching (§VI A)
- **Density reduction (Fig. 14):** up to ~100× (Model 1) / ~140–180× (Model 5); largest at low p (chains of length k scale as `c pᵏ`).
- **LER improvement factor, p=0.006, X-basis (Table IV):** Model 1 1.29×(d5)→1.44×(d31); Model 4 1.44→3.21×; Model 5 1.50→**4.66×**. Improvement **grows with distance**.
- **At p=0.003 (Table V):** Model 1 *degrades* LER at mid distances (0.91×@d13, 0.84×@d17, **0.70×@d21**); only the big models stay >1. Reason: training loss dominated by high-p samples → under-trained on rare low-p chains. **All vs uncorrelated matching (weak baseline).**

### 7.2 Correlated PyMatching + Model 6 (§VI B)
- The five small models make LER **worse** than correlated matching alone: residual logical-failure errors form **strings of length > (d−1)/2 parallel to a logical**, so *any* minimum-weight global decoder fails on them.
- The **42.6M-param Model 6** (Fig. 15, RF 17, trained at d=17) **beats correlated matching at d = 5, 9, 13**; at **d ≥ 17 it is slightly worse**, gap widening as p decreases (Fig. 16). So the "beats the strong baseline" claim is bounded to **d ≤ 13**.

### 7.3 Runtimes (§VI C, Tables VII–X)
- Pre-decoder on **GB300, FP8, TensorRT** (CUDA-graph capture, no host transfers); PyMatching on **Grace Neoverse-V2 CPU**.
- **Total speedup vs uncorrelated (Table VIII, p=0.006):** up to **3.42×** (Model 4, d=31). Vs **correlated (Table X):** up to **3.54×** (d=31). Speedup **grows with d and p**; at small d the pre-decoder cost dominates and raw PyMatching is faster (Fig. 19).
- Pre-decoder runtime is **independent of p**; PyMatching depends strongly on p via density. **ReLU** is faster than **GeLU** at a slight LER cost (Table VI vs IV). Large kernels (Model 3) are the worst speed tradeoff.

### 7.4 Parallel-window + batching (§VI D, VII; Table XI, XIII)
- Deployed in the temporal **parallel-window** scheme (refs [10,11]) over blocks `d×d×3d`: per-round time **well below 1 µs** (Table XI: 0.11–0.55 µs/round over 1000 rounds, with the GPU count per block listed).
- Batching trades `N_par` for `T_DEC`: batch 2 → 3.2× fewer resources at 1.99× faster `T_DEC`; **batch 64 → 12.5× fewer resources but 80% slower** `T_DEC` (Table XIII) — relevant for lattice-surgery patches needing 100k+ GPUs.
- Distance-selection identity `p_L(p,d) ≈ c1 · d · (c2 p)^((d+1)/2)` with `c1=0.01938, c2=116.95` (Eq. 69), used to argue the ReLU LER hit rarely forces a larger d.

### 7.5 Noise-learning results (§VI E, Fig. 20)
- **Recovers near-optimal weights.** **Uncorrelated:** edge weights from the learned model **approach but slightly under-perform** the true-DEM baseline — because uncorrelated edge weights depend only on **sums** of probabilities (a gauge), so the **true DEM is a lower bound** on uncorrelated-matching LER (you cannot beat knowing the truth). **Correlated:** the learned model can **slightly beat** the true-DEM baseline, because the correlated two-pass is a *heuristic* and true probabilities aren't its optimal inputs.
- **On pre-decoder residuals: no improvement** — the residual errors are the pathological `>(d−1)/2` strings; no reweighting helps. Best configs: d=31 unbiased loss generalizes best to d=21/31; d=21 models better at d=9/13 (boundary effects).

---

## 8. Conclusions and future work (Section VIII)

Claimed first simultaneous LER + full end-to-end speedup vs a SOTA global decoder, via better label processing and GB300/FP8 deployment. Future directions: (1) **close the correlated-matching gap** at low p / large d — failures are dominated by **rare patterns underrepresented in training** → curate rare-event-enriched data; (2) **model distillation** — train an over-parameterized "teacher" that learns rare events, distill into a fast "student" (decouple capacity from runtime); (3) **extreme quantization** — push FP8 → **NVFP4 (4-bit)** with **quantization-aware training**; (4) **color codes** (forthcoming manuscript) and **lattice surgery** with spatial-temporal parallel block-wise decoding.

---

## 9. Methodology scorecard (1–5)

| Criterion | Score | Justification |
|---|---|---|
| **Soundness** | 5 | Circuit-level derivations traced per fault location and **verified against Stim**'s DEM (A.5); honest about failure regimes (low-p degradation, d≥17 correlated gap, residual-string pathology). |
| **Novelty** | 3.5 | Pre-decoder concept is prior art (Gicev [22,23]; Chamberland–Goncalves [9]). Genuine novelty = the **label-engineering Algorithms 1–3** + the **distance-independent differentiable 18-edge/43-hyperedge parameterization** + simultaneous LER/runtime demonstration. |
| **Reproducibility** | 5 | **Open source** (GitHub + HF weights); full hyperparameters (Tables III, XII); explicit 25-param noise model + appendix formulas + Stim verification. |
| **Experimental design** | 4 | Broad sweeps (d=5…31, two p, 5+1 models, two activations, batching, two bases). **But** baselines are PyMatching variants only — **no head-to-head vs AlphaQubit-class learned global decoders** ([16,17] cited, not run), and the global decoder runs on CPU while the pre-decoder runs on a top-tier GPU (a fair *system* comparison, but not a like-for-like hardware one). |
| **Statistical rigor** | 2.5 | LER curves are Monte Carlo but **no confidence intervals / per-point shot counts** are reported; several headline d=31 points are **extrapolated** (Fig. 19 `(*)`, Table V `(*)`). The improvement *factors* are point estimates. |
| **Scalability** | 5 | The entire thesis: demonstrated to **d=31**, distance-independent noise formulas, **<1 µs/round** in parallel windows, GPU-deployed FP8. |

**Strengths.**
- **S1 (the engineering win).** Fixed-cost local CNN + density reduction genuinely converts MWPM's `O(s³)` near-threshold blowup into a 3–3.5× end-to-end speedup at d=31 (§VI C, Tables VIII/X) — a real systems result on real hardware (GB300).
- **S2 (label discipline).** Algorithms 1–3 are a principled fix to a subtle, under-appreciated data-generation bug (artificial timelike events / mislocalized Y faults). This is the kind of detail that separates a working decoder from a plausible one (§IV B 2–4).
- **S3 (a reusable parameterization).** The 18-edge/43-hyperedge **closed-form, distance-independent, differentiable** map from 25 circuit parameters to matching weights (Appendix A) is independently useful — it is a clean, Stim-verified DEM parameterization that any differentiable-DEM program can adopt.

**Weaknesses / limitations.**
- **W1 (weak headline baseline).** The big LER multipliers (up to 4.66×) are vs **uncorrelated** matching; against **correlated** matching the gain is bounded to **d ≤ 13** and requires a 42.6M-param model. The "simultaneous improvement" claim is real but should be read as "vs uncorrelated matching, with no regression."
- **W2 (supervised, simulator-bound training).** Both nets are trained on **simulated labels** — Model A on true errors, Model B on true noise parameters. Nothing here is, or claims to be, validated on real hardware syndromes; the "no explicit noise model needed" applies only to *inference*. The rare-event/low-p degradation (W in §VI A) and the residual-string pathology (§VI E) are direct symptoms of the training distribution.
- **W3 (no learned-decoder comparison + thin statistics).** No head-to-head against AlphaQubit/BP-OSD; no error bars; extrapolated d=31 points. The noise-learning net's net effect on LER is within roughly ±5–10% of the true-DEM baseline (Fig. 20) — i.e. it **matches**, it does not unlock a new regime.

---

## 10. Relevance to the twin (centerpiece)

This paper is unusually on-point for the current `qec_twin` fork, because **Model B is, structurally, the "learner-as-DEM" architecture the project has been weighing** — built, trained, and reported **simulator-only**. Mapping it onto our spine:

**10.1 Model B ≙ our differentiable-DEM learner — but with the opposite supervision principle.**
- NVIDIA: **supervised regression**, `syndrome statistics → 25 circuit parameters`, loss = **MSE to the *known* simulator probabilities**. Needs ground-truth parameters at train time (hence simulator-only); fast amortized **point estimate** at inference; no uncertainty.
- Ours (`src/qec_twin/forward/scalable/hypergraph_dem.py`): **label-free NLL** — the model *is* a DEM likelihood `P_θ(y)`, fit by maximizing the likelihood of *observed* syndromes; **no parameter labels needed**, and the audit stack yields **alias/uncertainty bands** (Fisher/Godambe, the alias quotient). These are **complementary**: NVIDIA's is the amortized-inverse / fast-inference end (ADR 0009 Layer 3 territory), ours is the posterior-spine end (ADR 0009 Layer 1).
- The **"labels = hardware info, not error"** instinct from our discussion is exactly NVIDIA's choice: their supervision target is the **25 circuit-level noise parameters** (gate/SPAM/idle rates — hardware properties), not error labels. Model A is the one trained on error labels; Model B is not.

**10.2 The honest ceiling — and it matches our `exact-inverse-artifact` finding.**
NVIDIA states plainly (§VI E) that for uncorrelated matching the **true-parameter DEM is a lower bound** on achievable LER, so a learner can only **approach**, never beat it. That is precisely the project's recorded insight that on a well-specified simulator with an identifiable DEM class, *recovery ≠ capability* — the best a syndrome→parameter learner can do is invert to the truth. Any "we beat the true model on simulator" claim should trigger the same red flag we apply to "perfect/machine-exact" results. (Their **correlated** slight-beat is not a counterexample: it exploits sub-optimality of a *heuristic* two-pass decoder, not a better noise estimate.)

**10.3 Where the twin can be genuinely distinct (not a reproduction).**
1. **Bands, not point estimates.** NVIDIA hits the gauge degeneracy (edge weights = sums of probabilities) and side-steps it by regressing to the *identifiable* edge/hyperedge combination — i.e. they implicitly handle the alias but **never quantify a band**. Our entire `audit/` machinery exists to *quantify* that alias quotient. A twin contribution = the same DEM learning **with explicit alias/uncertainty bands** and held-out syndrome NLL, per ADR 0009 scoring.
2. **Exact decoder, hyperedge-native.** NVIDIA feeds **PyMatching** (matching, with hyperedges decomposed into edge-pairs for a heuristic two-pass). We can feed a learned DEM into the **exact TN-MLD** (the cuda-qx decoder from the decoder-gate work) and keep **hyperedges native** in `hypergraph_dem`, avoiding the decomposition approximation.
3. **Attack their stated open regimes.** Their future-work list *is* a gap map: rare-event / low-p / large-d (training-distribution starvation), and the correlated-matching gap at d ≥ 17. A label-free likelihood fit that does not depend on a training distribution over `p` is structurally better positioned on the low-p tail.
4. **Reusable gift to adopt.** The **distance-independent 18-edge/43-hyperedge differentiable parameterization** (Appendix A) is a clean DEM parameterization we can borrow/cite directly. Under baseline discipline it should be vendored at its **own** settings (it is open source on GitHub/HF) and run as a comparator — *never edited in-tree*.

**10.4 The sim-only reframe — what it changes for us.**
- This paper is the published **precedent** that a **simulator-only** AI-decoder study is a legitimate, high-impact venue (NVIDIA reports exclusively on circuit-level depolarizing noise). It removes the objection that "simulator-only = toy": NVIDIA's Model A is trained on *true error labels*, which **only a simulator can provide**, and that is accepted practice.
- It also **reframes our own prior pre-decoder "dead end."** Our recorded XZZX pre-decoder failure was a **sim2real** failure (b2-sim training → +692% on real d7, a density mismatch). NVIDIA trains *and* evaluates in-sim, so there is **no sim2real gap** — and the route works. **If the project commits to sim-only, the pre-decoder is not a dead end in-sim.** What it is *not*, in that frame, is a contribution on our stated **industry-adoption / unowned-seam** axis (it would land next to NVIDIA's framework). That is the real strategic tension to resolve before building: sim-only is a *defensible methods venue* but **not** the real-hardware twin claim the project's goal memory describes.

**10.5 Net recommendation for the twin.** Treat this paper as (a) the **comparator/baseline** to beat or match for any DEM-learning-on-simulator line, (b) a **parameterization to adopt**, and (c) a **discipline check** (its lower-bound statement = our exact-inverse rule). If we go DEM-learning on simulator, the *only* non-reproductive framing is **label-free NLL + explicit bands + exact/hyperedge-native decoding**, ideally aimed at the **rare-event / low-p** regime NVIDIA flags as open. A bare syndrome→parameters regressor would re-derive Section V.

---

## 11. Key equations cheat-sheet

| # | Equation | Meaning |
|---|---|---|
| Eq. 2 | `s = \|Syn\|/(dm·(d²−1))` | syndrome density; governs `T_DEC` (`O(s³)` MWPM, `O(s)` UF). |
| Eq. 4 | `N_par ≥ 2 T_DEC/[(T_l+T_s)(n_com+n_W)]` | parallel resources to avoid backlog. |
| Eq. 8 | `R_l = 1 + Σ(k_i−1)` | CNN receptive field = max local decoding distance. |
| Eq. 9 | `d_{i,k} = s_{i,k} ⊕ s_{i,k−1}` | detector event. |
| Eq. 43 | `L_BCE = Σ_{c,α,β,k} [−Y log Ŷ − (1−Y) log(1−Ŷ)]` | pre-decoder per-voxel BCE loss. |
| Eq. 61 | `p̂_i = exp(log p'_min + (log p'_max − log p'_min)·σ(z̄_i))` | bounded log-space noise-parameter head. |
| Eq. A1 | `P1 ⊕ P2 = P1 + P2 − 2 P1 P2` | independent-mechanism probability combination (XOR). |
| Eqs. 64–68 | `L = L_edge + L_hyper` (count-weighted MSE, biased/unbiased) | noise-learning loss to *known* probabilities. |
| Eq. 69 | `p_L(p,d) ≈ c1·d·(c2 p)^((d+1)/2)` | sub-threshold LER fit (`c1=0.01938, c2=116.95`). |

---

## 12. Glossary

- **Pre-decoder.** A fast local decoder that corrects most errors and reduces syndrome density before a global decoder; here a 3D CNN.
- **Global decoder.** The downstream algorithmic decoder (uncorrelated/correlated PyMatching) that finishes the correction.
- **Syndrome density `s`.** Fraction of non-trivial detection events; the cost driver for matching.
- **Spacelike / timelike / diagonal / boundary edges.** Matching-graph edge categories from data-qubit errors / measurement errors / combined / boundary measurement errors (Appendix A.2).
- **Uncorrelated vs correlated PyMatching.** Edge-only matching vs two-pass matching that uses hyperedge conditional probabilities to reweight after a first pass.
- **Homological equivalence.** Two errors differing by a stabilizer are equivalent; used to canonicalize labels.
- **Distance-independent formula.** Edge/hyperedge probability whose functional form is the same for all `d ≥ 5`; only the instance count scales with `d`.
- **Parallel-window decoding.** Commit/buffer partition of the syndrome history decoded concurrently to remove backlog (refs [10,11]).

---

## 13. Selected references (for follow-up)

- **[9]** Chamberland, Goncalves, *et al.*, *Techniques for combining fast local decoders with global decoders under circuit-level noise*, QST 8, 045011 (2023) — the direct predecessor.
- **[10]** Skoric *et al.*, *Parallel window decoding…*, Nat. Commun. 14, 7040 (2023); **[11]** Tan *et al.*, *Scalable Surface-Code Decoders with Parallelization in Time*, PRX Quantum 4, 040344 (2023).
- **[16]** Bausch *et al.* (**AlphaQubit**), *Learning high-accuracy error decoding for quantum processors*, Nature 635, 834 (2024); **[17]** Senior, Bausch *et al.*, *A scalable and real-time neural decoder…*, arXiv:2512.07737 (2025) — the learned-global-decoder comparators (cited, not benchmarked).
- **[22,23]** Gicev, Hollenberg, Usman — scalable ANN / fully-convolutional 3D surface-code decoders (the architectural lineage).
- **[29]** Higgott, *PyMatching*; **[33]** Higgott & Gidney, *Sparse Blossom* (the global decoders used).
- **[34]** Hinton, Vinyals, Dean, *Distilling the knowledge in a neural network* (2015) — the distillation route future work points to.

---

### How to use / trust
- **Cite for:** the pre-decoder + density-reduction systems argument; the distance-independent differentiable DEM parameterization; a published precedent for simulator-only AI-decoder studies.
- **Do not cite for:** "AI decoder beats correlated matching" (true only d ≤ 13); any real-hardware claim (all simulator); statistically-bounded LER claims (no CIs, some extrapolated points).
- **Open questions for us:** (i) does a label-free NLL DEM fit beat NVIDIA's supervised regressor on the low-p tail it flags as open? (ii) what does an *explicit alias band* over the 25 parameters look like given the sum-gauge they note? (iii) learned DEM → exact TN-MLD vs → correlated PyMatching: how much of the correlated-matching gap is the *decoder* heuristic vs the *weights*?
