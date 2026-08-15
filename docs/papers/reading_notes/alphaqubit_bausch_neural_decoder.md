# Reading note — AlphaQubit (Bausch et al., Nature 2024) and its open precursor (Varbanov et al., 2023)

## Provenance

- **Source:** arXiv:2310.05900 (full PDF, open access), posted 2023; also Nature 635, 834–840 (2024)
- **Reading method:** FULL-TEXT read (精读) of the arXiv preprint PDF (all 9+ pages, figures, and appendix) — confirmed the arXiv version IS the same paper published in Nature, with full open-access text
- **Status:** complete full-text close-read

> **Source-provenance warning (read first).** AlphaQubit itself — J. Bausch, A. W. Senior,
> F. J. H. Heras, T. Edlich, A. Davies, M. Newman, C. Jones, K. Satzinger, M. Y. Niu,
> S. Blackwell, G. Holland, D. Kafri, J. Atalaya, C. Gidney, D. Hassabis, S. Boixo,
> H. Neven, P. Kohli, *"Learning high-accuracy error decoding for quantum processors"*,
> **Nature 635, 834–840 (2024)** — was originally thought paywalled with no public full text,
> but the arXiv preprint (arXiv:2310.05900, *"Learning to decode the surface code
> with a recurrent, transformer-based neural network"*) **IS fully open access** (the full PDF
> is downloadable from arXiv). So the detailed architectural/algorithmic facts below are drawn
> from **this open-access preprint** combined with the **open precursor** of the same lineage,
> **B. M. Varbanov, M. Serra-Peralta, D. Byfield, B. M. Terhal,
> *"Neural network decoder for near-term surface-code experiments"*, arXiv:2307.03280v2
> (24 Oct 2023)** — QuTech / TU Delft + Riverlane. The PDF in our repo
> (`docs/papers/bausch_nn_decoder_surface_2307.03280.pdf`) is **mislabeled**: arXiv 2307.03280
> is the **Varbanov** paper, not a Bausch paper. The genuine AlphaQubit preprint is 2310.05900.
> Throughout, **[PRECURSOR]** = full-detail facts from Varbanov et al. 2307.03280 (read in
> full, all 9 pages + appendix + Figs. 1–8 + Table I); **[ALPHAQUBIT-PUBLIC]** = high-level
> facts from the DeepMind/Google blog announcement and the arXiv 2310.05900 / Nature abstracts
> only. Do not cite an [ALPHAQUBIT-PUBLIC] number as if it had a method behind it that we could
> read — we could not.

## 1. Header / metadata

| | AlphaQubit | Open precursor (full-detail source) |
|---|---|---|
| **Title** | Learning high-accuracy error decoding for quantum processors | Neural network decoder for near-term surface-code experiments |
| **Authors** | Bausch, Senior, Heras, Edlich, Davies, Newman, Jones, Satzinger, Niu, Blackwell, Holland, Kafri, Atalaya, Gidney, Hassabis, Boixo, Neven, Kohli (Google DeepMind + Google Quantum AI) | Varbanov, Serra-Peralta, Byfield, Terhal (QuTech/TU Delft + Riverlane) |
| **Venue** | Nature 635, 834–840 (2024); preprint arXiv:2310.05900 (2023) | arXiv:2307.03280v2 (Oct 2023); preprint |
| **Public access** | Paywalled; only abstract + blog | Full PDF available (in our repo) |
| **Data** | Google Sycamore `d3`/`d5` (Acharya et al., *Nature* 614, 676 (2023)) + simulation to `d11` | Same Google `d3`/`d5` experiment [Acharya 2023]; + Stim circuit-level simulation `d3/5/7` |
| **Code/weights** | **Not released** | Decoder code released (`qrennd`, `surface-sim` packages); raw data + training scripts "upon request" |
| **Lineage** | Builds on Baireuther et al. (2018/2019) recurrent decoder; adds Transformer + soft/leakage inputs | Same Baireuther LSTM lineage; explicitly cites the AlphaQubit preprint [96] as concurrent work |

- AlphaQubit-public URLs: `https://blog.google/innovation-and-ai/models-and-research/google-deepmind/alphaqubit-quantum-error-correction/`; Nature `https://www.nature.com/articles/s41586-024-08148-8`; preprint `https://arxiv.org/abs/2310.05900`.
- **Path / why we read it.** Our program (memory: *decoder-gate-and-frontier*) has pivoted to a **non-Pauli axis** — a sim-only teacher generating realistic-noise surface-code syndromes (T1/T2, **leakage**, **soft readout**) to train a **TN-affine neural decoder** (GNN / Transformer / ResNet) that captures the non-Pauli/temporal signal **above** what Pauli decoders see. **AlphaQubit is the closest published precedent**: it beats an approximate-maximum-likelihood (tensor-network) decoder on *real* Google data, and the public description attributes that to exactly the two ingredients we want to exploit — **soft (analog) readout** and **leakage** handling. The precursor gives us the only openly-readable, fully-specified recipe in this lineage for (a) the recurrent per-detector decoder, (b) how soft information is **encoded as defect probabilities** rather than raw I/Q, and (c) the **simulate-to-train → evaluate-on-real** transfer that our sim-only constraint forces on us.

## 2. TL;DR

**[ALPHAQUBIT-PUBLIC].** AlphaQubit is a **recurrent, Transformer-based** neural decoder. It is
**pretrained on hundreds of millions of synthetic-noise samples** from a quantum simulator, then
**fine-tuned on a few thousand experimental samples** from a specific Sycamore processor. On
Google's `d3`/`d5` surface codes it makes **~6 % fewer errors than a tensor-network (approximate
MLD) decoder** and **~30 % fewer errors than correlated matching**. It **scales to simulated `d11`
(241 qubits)** and **sustains accuracy out to 100 000 rounds** despite training on only **25**. It
exploits **soft/analog readout and leakage** information as inputs — the headline reason it beats
MLD on real hardware. It is **too slow for real-time** decoding on a superconducting processor.

**[PRECURSOR] (the part we can actually read in full).** A two-layer-LSTM recurrent decoder that
ingests **per-round, per-ancilla syndrome defects** and emits a single logical-flip probability.
On the **same Google `d3`/`d5` data** it reaches **~25 % lower logical error per round than MWPM,
approaching the tensor-network (≈MLD) decoder** — and on `d3` it **equals** the TN decoder.
Crucially for us, it shows the **standard way to feed soft information to an NN decoder**: **not**
raw analog values (which "leads to overall poor logical performance") but a **per-round defect
probability** `P(d_{r,a}=1 | \tilde m_{r,a}, \tilde m_{r-1,a})` computed from a Gaussian readout
model — giving **~10–30 % lower logical error** when the measurement/assignment error is high.

## 3. Main architecture + algorithm (full detail)

### 3.0 Decoding setup common to both papers

A rotated distance-`d` surface code stores one logical qubit in `n = d×d` data qubits; `n−1`
ancillas measure weight-≤4 X- and Z-type stabilizers each round. The raw inputs are stabilizer
measurement outcomes `m_{r,a}` (ancilla `a`, round `r`). The decoder consumes **defects**
`d_{r,a} = m_{r,a} ⊕ m_{r−1,a}` — the *change* between consecutive rounds; an error is signalled
by `d_{r,a}=1`. A final set of defects `d_{r=N,a}` is inferred from the terminal data-qubit
readout. Decoding is framed as **binary classification**: predict whether the logical observable
needs a flip. Logical fidelity `F_L(r) = 1 − 2 p_L(r)` decays as `(1−2ε_L)^{r−r_0}`; the figure of
merit is the **logical error per round `ε_L`** (fit from `r=3` to avoid time-boundary effects).
[PRECURSOR §II]. AlphaQubit uses the identical defect/`ε_L` framing on the same Sycamore data.

### 3.1 [PRECURSOR] Recurrent (LSTM) decoder — the readable architecture

This is the architecture we can study line-by-line; AlphaQubit replaces the recurrent *body* with
a Transformer but keeps the same input/output contract and two-stage philosophy.

**Body — two stacked LSTMs.** (Figs. 2, follows Baireuther et al. [62,64].)
- Inputs: the time-series of per-round defects `{d_{a,r}}`, `r = 1,…,N−1`, combining **both X- and
  Z-type** stabilizer outcomes, presented **one round at a time** to the recurrent stack.
- **LSTM-1** outputs a hidden state *for every round* → fed to **LSTM-2**, which outputs **only its
  final hidden state** (a fixed-size summary of the whole history). A **ReLU** is applied to LSTM-2's
  output. Internal state size `N_L = 64, 96, 128` for `d = 3, 5, 7` (scaling with distance); a
  `d=5` experimental-data model used `N_L = 253` (Table I). One LSTM layer underperforms at `d=3`;
  **two** is the sweet spot; **four** gives no gain.
- The LSTM body is **round-count-agnostic**: because it is recurrent it decodes experiments with a
  **variable / arbitrary number of rounds** without retraining — the property that lets a model
  trained on ≤37 rounds generalize to 300 rounds (and AlphaQubit-public: 25 → 100 000).

**Two prediction heads (the key training trick).** Each head is a feed-forward net (one hidden layer
of size `N_L`, ReLU, then a sigmoid).
- **Lower / auxiliary head** → `p_aux`: sees *only* the recurrent summary (defects up to round `N−1`).
- **Upper / main head** → `p_main`: **concatenates** the recurrent summary with the **final
  data-qubit defects** `{d_{a,N}}`, so it uses the *complete* error information including the terminal
  readout. **Only `p_main` is used at evaluation.**
- **Loss** = weighted sum of binary cross-entropies against the known truth `p_true ∈ {0,1}`
  (logical state is prepared known and measured at the end):
  `I = H(p_main, p_true) + w_a·H(p_aux, p_true)`, `w_a = 0.5`.
  The auxiliary head **regularizes**: it forces the recurrent body to produce a usable summary at
  every round, which is what makes the decoder **generalize to much longer sequences than trained on**.

**Training details [PRECURSOR §VI B, Table I].** Adam, lr `1e−3` or `5e−4`; batch 256 (or 64);
dropout 20 % (uniform-noise models) or 5 % (experimental-noise models) after the head hidden layer
and sometimes after LSTM-2; early stopping (patience 20 epochs); occasional lr-drop + retrain.
Implemented in TensorFlow; trained on a V100S GPU (DelftBlue cluster). Data volumes: `~1e7` shots
(uniform `d3/5/7`), `2e7` (experimental `d3`), `6e7` (experimental `d5`); rounds sampled on a grid
(e.g. `[1,37,4]` train / `[10,290,...]` eval). **Inference is slow**: ~0.7 s **per QEC round** at
`d3` (batch 50 000, CPU), 0.8 s `d5`, 1.1 s `d7` — i.e. recurrent decoders are **not** real-time.

### 3.2 [PRECURSOR] How soft-readout information is fed in — the crucial encoding lesson

This is the single most transferable section for our program. Transmon readout is **analog**: a
dispersive measurement returns a continuous I/Q signal collapsed to one real variable `\tilde m_{r,q}`,
normally thresholded to a hard bit. The continuous value ("**soft information**") carries strictly
more state information than the bit.

**What does NOT work.** Feeding the **raw soft outcomes `\tilde m_{r,q}` directly** into the NN
"leads to an overall poor logical performance." (Direct-analog input is the naive choice and it
fails.)

**What works — soft defects.** Model each soft outcome given true state `i∈{0,1}` as Gaussian
`N_i(\tilde m)` with means `µ_0=−1, µ_1=+1` and shared `σ` set by the target assignment-error
`p_m = ½ erfc(SNR/√2)`, `SNR = |µ_0−µ_1|/2σ`. Then:
1. Posterior state probability (uniform prior `P(i)=½`):
   `P(i | \tilde m_{r,q}) = N_i(\tilde m_{r,q}) / Σ_j N_j(\tilde m_{r,q})`.
2. **Soft defect probability** (a defect = the two adjacent rounds disagree):
   `P(d_{r,a}=1 | \tilde m_{r,a}, \tilde m_{r−1,a}) = 1 − Σ_{i∈{0,1}} P(i|\tilde m_{r,a})·P(i|\tilde m_{r−1,a})`.
   The terminal data-qubit soft defect is derived analogously.
3. **Feed this real-valued probability in place of the hard binary defect** `d_{r,a}` — the network
   architecture is otherwise unchanged. So "soft" enters as a **[0,1] continuous defect channel**,
   not as raw I/Q and not as a second input stream.

**Result.** With ancilla assignment error `p^a_m = 1 %` (data `p^d_m = 0.1 %`), the **soft NN** gets
**~30 % lower `ε_L`** vs hard MWPM (the **hard NN** alone gets ~20 %), i.e. soft adds ~10 % on top
of the NN gain (Fig. 7). The benefit **grows with `p^a_m`** and is negligible when readout is already
clean (`p^a_m ≲ 0.1 %`). Honest caveats the authors flag: this defect-probability representation is
**sub-optimal** (the soft-MWPM weighting of [Pattison et al. 2107.13589] uses the soft info better
at high `p_m`), and at very high `p^a_m ≳ 20 %` the defect probability saturates near 0.5 and *hurts*.
**Open**: a better soft representation (e.g. feeding the assignment-error **likelihood** `L_{r,a}`
alongside hard defects), and crucially **asymmetric / non-Gaussian** readout distributions (relaxation
during readout biases `|1⟩`) — and **the continuous outcome also contains leakage information**.

### 3.3 [PRECURSOR] Leakage — stated as a gap, not solved

The precursor does **not** model leakage. It repeatedly identifies leakage (and crosstalk/stray
interactions) as the **dominant un-modeled error** that makes its Pauli-trained simulation
*under-predict* the real `ε_L`, and notes `d5` is *more* leakage-sensitive than `d3`, plausibly
explaining why its `d5` model underperforms `d3`. It explicitly points (citing the concurrent
AlphaQubit preprint [96]) to **"considering leakage in addition to the soft information"** as the way
to *exceed* the TN decoder. So: **leakage is the named headroom; the precursor leaves it on the table;
AlphaQubit is the paper that picks it up.**

### 3.4 [ALPHAQUBIT-PUBLIC] What AlphaQubit changes (high-level only)

From the blog + abstracts (no readable method):
- **Recurrent + Transformer.** Same recurrent, variable-round philosophy as §3.1, but the per-round
  processing/aggregation is a **Transformer** ("the architecture that underpins large language
  models"), with a **per-stabilizer/per-detector representation** updated across rounds (consistent
  with the abstract's "recurrent, transformer-based"). Exact block structure is not in the public
  text.
- **Two-stage training.** (i) **Pretrain** on **hundreds of millions** of synthetic samples spanning
  many noise settings/levels; (ii) **fine-tune** on **thousands** of real Sycamore samples per task.
  This is the precursor's simulate-to-train recipe scaled up and given an explicit real-data
  fine-tune step.
- **Soft + leakage inputs.** The public description credits beating MLD to using **analog/soft readout
  and leakage** information — i.e. AlphaQubit operationalizes exactly the two extensions the precursor
  flagged as open (§3.2–3.3). The public sources do **not** disclose the input encoding; we should
  assume it is *richer* than the precursor's scalar soft-defect (likely raw or multi-feature analog +
  a leakage indicator) but we **cannot verify** this.
- **Trained on 25 rounds, holds to 100 000** — the recurrent generalization property of §3.1 at scale.

## 4. Key results

### 4.1 [PRECURSOR] (numbers we can trust — read off the figures/text)
- **Y-error correlation gain (Fig. 3).** On uniform depolarizing circuit-level noise (`p=0.1 %`),
  the NN gives **~20 % lower `ε_L`** than MWPM at `d3`, **constant across 10→300 rounds**
  (`ε_L`: 0.245 % MWPM → 0.199 % NN). The gain comes from learning **Y-error correlations** (correlated
  X+Z defects MWPM ignores): under a Y-bias `η`, the NN wins for `η ≥ 0.5` and the margin grows with
  bias; at `η=0` (pure X/Z) MWPM is optimal and the NN does not beat it.
- **Real Google `d3`/`d5` data (Figs. 4–5).** Trained on the experimental Pauli model, evaluated on
  real data: the NN **beats MWPM and the correlated (Corr.) MWPM**, and **matches the tensor-network
  (≈MLD) decoder at `d3`**. The abstract states **"≈25 % lower than MWPM, approaching the
  maximum-likelihood (TN) decoder."** At `d5` the NN **trails** the TN and belief-matching decoders —
  attributed to harder optimization of the larger model **and** leakage that the Pauli training model
  omits. Comparison order (Fig. 5): MWPM < Corr.-matching < (NN ≈ BM) ≲ TN.
- **Sim-vs-real gap.** Evaluated on real data, `ε_L` is **~15 % (`d3`) / ~40 % (`d5`) higher** than on
  the matched simulation — quantifying how much the Pauli training model **under-predicts** reality
  (leakage/crosstalk). Contrary to Acharya 2023's TN result, the precursor's `d5` real `ε_L` is *above*
  the `d3` average — its honest admission of the leakage/optimization gap.
- **Error suppression Λ (Fig. 6).** `d=3,5,7`, depolarizing `p`: a better (NN) decoder buys a higher
  suppression factor. At `p=0.1 %`, NN gives **~10 % higher Λ** than MWPM; at `p=0.05 %`, **~60 %
  higher** (`Λ`: MWPM 7.38 / NN 11.58 at the cleaner rate; MWPM 3.71 / NN 4.04 at `p=0.1 %`). Practical
  payoff: reaching `ε_L ≈ 1e−10` needs `d=19` (MWPM) vs `d=15` (NN) at `p=0.05 %` — **~40 % fewer
  physical qubits**. Whether the NN holds this at larger `d` is left open.
- **Soft information (Fig. 7).** As §3.2: soft NN **~30 %** vs hard MWPM (hard NN ~20 %) at
  `p^a_m=1 %`; benefit rises with assignment error, vanishes when readout is clean.

### 4.2 [ALPHAQUBIT-PUBLIC] (headline numbers, method unreadable)
- **~6 % fewer errors than tensor-network (approx-MLD)** decoding on real Google `d3`/`d5`.
- **~30 % fewer errors than correlated matching** on the same data.
- **Outperforms leading algorithmic decoders at all scales up to simulated `d11` (241 qubits)**.
- **Maintains accuracy to 100 000 rounds**, trained on **25**.
- **Too slow for real-time** superconducting decoding (latency, not accuracy, is the open problem —
  consistent with the precursor's ~1 s/round recurrent cost).

> **Reconciling the two "vs TN" numbers.** The precursor *matches* TN at `d3` and *trails* at `d5`,
> using only hard defects + a Pauli training model. AlphaQubit *beats* TN by ~6 % — the delta is
> exactly the soft+leakage inputs and the Transformer + real-data fine-tune. That delta **is the
> non-Pauli headroom our program is chasing**, and it is **modest (~6 %) even for DeepMind**, which
> is a calibration on how large our own target can realistically be.

## 5. Useful for our project (concrete)

Our target: a **sim-only teacher** (T1/T2 + **leakage** + **soft readout**) → **TN-affine neural
decoder** capturing non-Pauli/temporal signal above Pauli decoders. Concrete take-aways:

**A. Adopt the input/output contract verbatim.**
- Input = **per-detector defect time-series** `{d_{r,a}}` over rounds + a **terminal data-qubit defect
  set** `{d_{N,a}}`; output = **one logical-flip probability**; train as **binary cross-entropy vs
  the known prepared logical** (sim gives us `p_true` for free — a clean supervision signal we *have*).
- Keep the **two-head trick** (`p_main` with terminal defects + auxiliary `p_aux`, `w_a=0.5`). It is
  cheap and is *the* mechanism that buys **variable-round generalization** — directly relevant since
  our teacher can emit any round count and we want one model to cover all.
- A **recurrent / variable-round** core is non-negotiable for the "trained-on-few-rounds, holds-to-many"
  property. For a **TN-affine** decoder this argues for a recurrent-over-rounds wrapper around a
  per-round TN/GNN block (matches our planned GNN-stitching + differentiable-TN skeleton in the
  decoding-floor program).

**B. Soft-readout encoding — start from the precursor, then go richer.**
- **Baseline (known-good):** the **soft-defect probability** of §3.2
  (`P(d_{r,a}=1 | \tilde m_{r,a}, \tilde m_{r−1,a})` from a Gaussian readout model) as a **[0,1]
  continuous defect channel** replacing the hard bit. This is *proven* to help and is trivial to
  generate from our teacher (we control `µ_i, σ`, hence `SNR`/`p_m`). **Do this first** — it is the
  validated rung.
- **Known failure to avoid:** do **not** feed raw I/Q scalars straight in (precursor: "overall poor
  logical performance").
- **Where AlphaQubit goes beyond (our headroom to test):** (i) **asymmetric / non-Gaussian** readout
  (relaxation-biased `|1⟩`) — our teacher should emit realistic asymmetric I/Q so the decoder *must*
  learn it; (ii) richer soft features than a single defect probability (e.g. per-round posterior
  `P(i|\tilde m)` for *both* rounds, or the assignment-likelihood `L_{r,a}` alongside hard defects, an
  open idea the precursor names); (iii) since AlphaQubit's edge over TN is *soft+leakage*, our
  **differentiator metric** is the **gap between a soft-feature neural decoder and a hard Pauli MLD/TN
  on the same rich-noise sim** — this is the "**Bayes-floor-vs-Pauli gap on rich-noise sim**" de-risk
  in our memory, made concrete.

**C. Leakage — the named, unclaimed headroom; this is where we differentiate.**
- The precursor **leaves leakage unmodeled** and flags it as the dominant sim-vs-real gap; AlphaQubit
  is closed-source on *how* it uses leakage. **Neither gives us a readable leakage recipe** → this is
  genuinely open space. Our teacher can **inject leakage explicitly** (population leaving the
  computational subspace, leakage-induced multi-round correlated defects, leakage signatures in the
  analog readout) and we can feed a **leakage indicator/feature per detector** — a feature class Pauli
  decoders structurally cannot use. Since `d5` is *more* leakage-sensitive than `d3` (precursor), the
  leakage advantage should **grow with distance** — a falsifiable prediction to pre-register.

**D. Synthetic→real training recipe — what transfers to sim-only.**
- The full lineage trains on **simulation** and (AlphaQubit) **fine-tunes on real**. We are **sim-only**,
  so the **transferable half is the pretraining half**: large synthetic corpus (precursor `~1e7`,
  AlphaQubit hundreds of millions) over a **grid of noise levels and round counts**, Adam, dropout,
  early stopping, distance-scaled hidden size. **We cannot do the real fine-tune** — so we must **not**
  claim real-hardware accuracy; our claims are bounded by *"on rich-noise simulation"*.
- **Critical honest lesson, doubly so for us.** The precursor's own numbers show a Pauli training model
  **under-predicts real `ε_L` by 15–40 %**. Our teacher is explicitly **non-Pauli (T1/T2/leakage/soft)**,
  which is the *right* direction to shrink that gap **in simulation** — but a model that only ever sees
  *our* simulator will be **as wrong as our simulator is**. The validated contribution is therefore the
  **headroom a soft+leakage neural decoder shows over a Pauli decoder *on the same teacher*** (a
  controlled, in-sim, apples-to-apples ΔLER), **never** an implied real-hardware SOTA.
- **Baseline discipline.** When we run this, AlphaQubit's public numbers are **not** a baseline we can
  reproduce (no code/weights). The reproducible baselines are: the **precursor's released `qrennd`
  recurrent decoder** + `surface-sim` (open), **MWPM/Corr-MWPM/belief-matching/TN** as in the precursor,
  and a **hard-defect version of our own net** (the soft/leakage gain must be measured *against itself
  with the feature ablated*, the precursor's exact hard-vs-soft NN design).

**E. Cheap wins to copy immediately:** distance-scaled hidden width (`N_L ∝ d`), the auxiliary-head
regularizer, round-count curriculum on the training grid, and the **defect (not raw-outcome)**
input convention — all low-risk and all validated in the open precursor.

## 6. Limitations / what we cannot reproduce

- **No AlphaQubit source, weights, or full method.** Architecture block-diagram, the *exact* soft/leakage
  input encoding, hyper-parameters, and the precise pretraining distribution are **not public**. Every
  AlphaQubit-specific claim here is **headline-level** and **must not** be used as a derivation premise
  (epistemic class (c) at best). The `~6 %` / `~30 %` figures are reported results we **cannot** re-derive.
- **Mislabeled repo PDF.** `bausch_nn_decoder_surface_2307.03280.pdf` **is Varbanov et al.**, not Bausch.
  The genuine AlphaQubit preprint is **arXiv:2310.05900** (abstract-only) → Nature 635, 834 (2024). Fix
  the filename/metadata if this note is cited.
- **Precursor scope limits (the readable parts).** (i) **Recurrent, not real-time** (~1 s/round at `d3`)
  — the same latency wall AlphaQubit hits; if we want real-time we inherit the Mamba/scalable-decoder
  trade-off (see `scalable_neural_decoder_realtime_2510.22724.md`, `sparse_mamba_decoder_2605.17156.md`),
  not this design. (ii) **Soft handled only as a scalar Gaussian defect probability** — sub-optimal vs
  soft-MWPM at high `p_m`; saturates/hurts at `p^a_m ≳ 20 %`; **symmetric-Gaussian** readout only (real
  readout is asymmetric). (iii) **No leakage/crosstalk modeled at all** — precisely the signal we want,
  so the precursor gives us the *gap statement* but **no recipe**. (iv) `d ≤ 7` only, and `d5` already
  shows training-optimization fragility — scaling the *recurrent* design is unproven (AlphaQubit's `d11`
  is *simulation*, also unverifiable by us).
- **Transfer caveat for our program.** The whole lineage's accuracy on *real* hardware comes from a
  **real-data fine-tune we cannot perform**. We can replicate the **pretraining methodology and the
  soft/leakage *feature design*** in simulation; we **cannot** claim its real-hardware results, and our
  honest deliverable is an **in-simulation ΔLER (soft+leakage neural vs Pauli decoder) on our own
  rich-noise teacher**, reported as such.

### Trust / how to use
- **Trust:** precursor numbers **high** (read in full from text + figures + Table I); AlphaQubit numbers
  **medium** (single-source headline, no method) — cite as *reported*, never as reproducible or as a premise.
- **Use as:** the **input/output contract + soft-defect encoding + two-head recurrent recipe** are our
  starting blueprint; AlphaQubit is the **existence proof** that soft+leakage neural decoding beats
  approx-MLD on real hardware (the ~6 % delta = our headroom envelope) and the **named precedent** for
  the non-Pauli axis. The reproducible baseline is the precursor's open `qrennd`/`surface-sim`, not AlphaQubit.
