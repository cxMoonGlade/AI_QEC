# 精读 — White, Jurcevic, Hill, Modi, "Unifying non-Markovian characterisation with an efficient and self-consistent framework" (arXiv:2312.08454)

> **Provenance (2026-07-03): FULL-TEXT 精读 of the conceptual core.** PDF → txt `outputs/papers/2312.08454.txt`
> (PyMuPDF, 45 pages, arXiv v2 30 May 2025). Read in depth: abstract, §I (intro), §II (background + summary
> of results: the GST/PTT/self-consistent-PTT comparison Fig. 1, the process-tensor formalism Eqs. 1–4).
> The applied results (§III, IBM + synthetic) and the full technical framework (§IV: the NM categorization,
> the self-consistent estimator, the tensor-network compression) are in the txt for deeper reads — summarized
> here at the level the reconstruction needs. Tags: **[paper]** stated; **[ours]** our inference.

## Metadata [paper]
- **Authors.** G. A. L. White (FU Berlin / Monash / Melbourne), P. Jurcevic (IBM Quantum), C. D. Hill (SQC / Melbourne),
  K. Modi (SUTD / Monash). Same White/Modi lineage as PTT (2106.11722).
- **Venue.** arXiv:2312.08454v2 (30 May 2025). Theory + method + IBM-hardware demonstration.

## Executive summary [paper]
Establishes a **single self-consistent framework that uniformly incorporates and classifies ALL
non-Markovian phenomena**, written entirely in experimentally-accessible circuit-level quantities,
assuming no parameter values. It closes the gap between two prior tools (Fig. 1): **GST** is
self-consistent (estimates gates + a time-local background together) but assumes Markovian, time-independent
noise; **standard PTT** (2106.11722) handles non-Markovian background but assumes gates are KNOWN/perfect.
**Self-consistent PTT (this work)** estimates ALL objects simultaneously — the correlated background process
AND the control instruments — allowing temporal correlations in BOTH. Made **efficient + modular via tensor
network learning** (scalable NM characterization, and scalable self-consistent Markovian estimation as a
byproduct). Demonstrated on synthetic models (exchange with nuclear spins; coherent + 1/f gate noise;
control "spillage" into environment dynamics) and IBM devices; applied to noise-aware SU(4) gate
decomposition + optimized dynamical decoupling (significant diamond-norm / avg-gate-fidelity gains).

## Method (deep) — the core objects + the advance [paper]
- **Process tensor recap (Eqs. 1–4, = quantum comb / process matrix).** A k-step process driven by a sequence
  of CP control ops `A_{k-1:0}` gives `ρ_k(A_{k-1:0}) = tr_E[U_{k:k-1} A_{k-1} ⋯ U_{1:0} A_0(ρ^{SE}_0)]`; the
  process tensor `T_{k:0}[A_{k-1:0}] = ρ_k`; Choi `Υ_{k:0} ∈ B(H_{ok}⊗H_{ik}⊗⋯⊗H_{o0})` (alternating i/o legs).
  Action by projection (Eq. 3, the spatiotemporal Born rule): sequences of ops ARE observables of `Υ`. NM ⟺
  temporal correlations distributed as SPATIAL correlations between legs → probed with many-body tools.
- **The three models (Fig. 1).** (a) GST: time-local gates + time-local background, self-consistent, Markovian.
  (b) PTT: correlated background, gates assumed known. (c) **Self-consistent PTT (this work): estimate
  everything simultaneously**, temporal correlations allowed in BOTH background and control instruments.
- **Broadened NM (the conceptual advance).** Includes correlated parameters at the CONTROL level,
  process-control INTERPLAY (a probe affecting the bath itself), and the instrument set forming an unknown
  environment in its own right. A CATEGORIZATION (§IV A) sub-divides "non-Markovian" into
  experimentally-relevant components (background vs control noise; quantum vs classical temporal correlations)
  — not a strict hierarchy, but a structure the estimator exploits.
- **Efficiency (§IV C–D).** Derive the self-consistent estimator in full generality, then COMPRESS with
  tensor networks → palatable model size without sacrificing generality/interpretability; modular
  (rearrange components per hardware idiosyncrasies / native gates / expected physics).

## Findings [paper]
- Characterizes a wide variety of NM models with "no operational equivalent in the literature," at scale +
  expressivity beyond prior PTT; maps spatiotemporal correlations on IBM devices emergent purely from noise.
- Applied: noise-aware compilation + optimized DD → significant diamond-norm & avg-gate-fidelity improvements
  on arbitrary SU(4), beating off-the-shelf DD.

## Limitations [paper]
- Still built on the PTT machinery (exponential in k in full generality; tempered by TN compression +
  low-memory / modular assumptions). High-fidelity control still needed (though gate error is now
  self-consistently estimated, not assumed). Demonstrations few-qubit / few-step.

## Relevance to the reconstruction [ours]
- **Grounds the "active ⇏ no gauge" honesty rigorously.** The reconstruction's active probes ARE gates that
  may themselves be noisy/correlated; self-consistent PTT is exactly the tool that estimates the control
  instruments AND the background together (GST-style self-consistency lifted to NM) — so the active-probe
  characterization does not silently trust its own probes. This is the process-tensor answer to the
  identifiability/gauge caveat.
- **The scalable-characterization path:** tensor-network learning of the (self-consistent) process tensor is
  the efficiency lever the reconstruction's Phase-1 prereg cites for scaling the active-observation
  characterization beyond the toy — complements Keeling PT-MPO [[keeling_process_tensor_2509.07661]] and the
  pseudomode carrier.
- **The NM categorization (§IV A)** is a ready taxonomy for the prereg's observable partition (background vs
  control; quantum vs classical temporal correlation) — sharper than the retracted single matched-marginal
  discriminator, and it explicitly includes process-control interplay (a probe affecting the bath), which the
  passive framing could not represent.
- Same spatiotemporal-Born-rule observable + necessary/sufficient NM measure as
  [[white_pollock_process_tensor_tomography_2106.11722]]; this paper is the efficient + self-consistent upgrade.

## Related notes
[[white_pollock_process_tensor_tomography_2106.11722]] (the PTT foundation), [[keeling_process_tensor_2509.07661]]
(PT-MPO efficiency), [[tn_decoders_process_tensor_nonmarkovian_2412.13739]], [[qec_insitu_benchmarking_clifford_2601.21472]]
(GST/self-consistent lineage), [[ziyad_emergent_nonmarkovianity_logical_2512.08893]] (button-theoretic Markovianity = the GST-side def).
