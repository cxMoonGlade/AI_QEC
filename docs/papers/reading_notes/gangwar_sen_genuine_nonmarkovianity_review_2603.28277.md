# Reading note (精读): Gangwar & Sen, "Genuine and Non-Genuine Quantum Non-Markovianity: A Unified Information-Theoretic Review" (arXiv:2603.28277)

> **Provenance (2026-07-05): FULL-TEXT read (精读), §§1-6 read in full.** PDF → txt
> `outputs/papers/2603.28277.txt` (21 pages, PyMuPDF). All §/Eq refs from that text.
> Adjudication target: does this review ground the claim that **process-tensor methods
> provide a multi-time framework for distinguishing classical vs quantum memory** in a way
> that applies to our joint-parity measurement records? **Verdict: YES — it maps the
> landscape comprehensively and confirms the vacuum our proposition fills.**

## Metadata [paper]
- **Authors:** Rajeev Gangwar (Technion) & Ujjwal Sen (HRI, India)
- **Venue / status:** arXiv:2603.28277v3 [quant-ph], 8 Apr 2026. Review article (preprint).
- **Type:** comprehensive review (21 pp, ∼150 refs)

## Executive summary [paper]
This review organizes the landscape of genuine vs non-genuine quantum non-Markovianity
across ALL major frameworks: CP-divisibility (RHP), distinguishability (BLP), correlation-based
(LFS), conditional-correlation, general-contractivity, and **process-tensor** methods. The central
taxonomy: non-Markovianity splits into **(a) classical** (convex mixture of Markovian maps,
classical-memory simulation possible), **(b) non-genuine quantum** (mixing-induced, squashed),
and **(c) genuine quantum** (temporally-entangled process tensor, no classical decomposition).
The review confirms that the process-tensor framework is the only one that fully captures the
multi-time structure needed to distinguish these categories, and that the operational definition
in terms of Kolmogorov-consistent multi-time statistics (Milz et al.) is the gold standard.

## Key frameworks mapped (verbatim from review) [paper]

### Process-tensor Markovianity — Definition 7 [paper]
```
T^{Markov}_{n:0} = C_{t_n:t_{n-1}} ⊗ C_{t_{n-1}:t_{n-2}} ⊗ ... ⊗ C_{t_1:t_0}   (21)
```
Factorization into independent one-step Choi matrices ⇔ Markovian. Any temporal
correlation beyond this ⇒ non-Markovian. This is the multi-time generalization:
CP-divisibility ≠ process-tensor Markovianity (Appendix B 2 gives a counterexample).

### Classical vs Quantum memory (Giarmatzi & Costa) [paper]
A non-Markovian process has **classical memory** iff its process tensor admits:
```
T^{cl}_{n:0} = Σ_λ p_λ ⊗_{k=0}^{n-1} T^{(λ)}_{k+1:k}   (52)
```
where p_λ ≥ 0, each T^{(λ)} is a positive operator for a CP map. This = all temporal
correlations are mediated by a classical hidden variable λ. If no such decomposition
exists, T_{n:0} is **temporally entangled** ⇒ **quantum memory**. Temporal entanglement
IS the structural signature of genuine quantum non-Markovianity.

### Operational classicality (Milz et al.) [paper]
Joint probabilities from sequential projective measurements are classical (Kolmogorov-consistent)
iff the process tensor is diagonal in the tensor-product measurement basis [Eq. (51)]:
```
T_{n:0} = Σ_{x⃗,x⃗'} p(x⃗,x⃗') ⊗_{k=0}^{n-1} |x_k⟩⟨x_k| ⊗ |x'_k⟩⟨x'_k|
```
Otherwise ⇒ **quantum information backflow**. The minimal quantum resource = basis-dependent
**quantum discord** between system and environment.

### Single-time quantum memory witness [paper]
If E(C_1) < E(C_2) where C_k are Choi states of dynamical maps E_1 (t_0→t_1) and E_2
(t_0→t_2), with E the entanglement of assistance [Eq. (46)], then the dynamics REQUIRE
quantum memory — no classical-memory realization possible [Eq. (43)]. This connects
directly to our K observable: K > 0 is the multi-time operational signature; the
single-time witness is a simpler (but weaker) test.

### Key negative result: classical mixing can fake non-Markovianity [paper]
Section 5.2: convex mixtures of Markovian maps Φ_t = Σ_i q_i Λ^{(i)}_t can show
distinguishability revivals (BLP-non-Markovian) from purely classical uncertainty
about which map was applied. This means BLP/RHP non-Markovianity alone does NOT
certify quantum memory — the process-tensor structure is needed.

## Relevance to project [ours]
**Dimensions 1 & 5 — FRAMEWORK MAP CONFIRMED.** This review provides the comprehensive
taxonomy within which our K-survival proposition sits:

1. **The hierarchy is clear:** BLP/RHP non-Markovianity → process-tensor non-Markovianity
   → temporal entanglement → K > 0. Our K observable probes the strongest condition.

2. **The vacuum is confirmed:** the review covers single-qubit operational classicality
   (Milz), process-tensor quantum memory (Giarmatzi-Costa), and classical-memory witnesses
   (Banacki, single-time Choi-entanglement criteria). **None of these are instantiated
   on multi-qubit stabilizer-parity measurement records.** The extension to
   "coarse-grained, ancilla-mediated, joint-parity measurements on a coded register"
   is the vacuum our proposition fills.

3. **The geometric sensitivity we predict maps cleanly:** Eq. (51) — classicality =
   process tensor diagonal in measurement basis. When the measurement basis aligns with
   the coupling eigenbasis (r=1, common-mode), the process tensor is approximately
   diagonal → K ∼ 0. When misaligned (r≠1), off-diagonal temporal correlations survive
   → K > 0. This is the structural mechanism of the K-survival proposition.

4. **The discord connection:** Milz et al. identify basis-dependent quantum discord as
   the minimal quantum resource for K > 0. Our quantum bath (pseudomode with σ_z
   coupling) generates system-environment discord. The joint-parity measurement
   either "sees" this discord (r≠1) or is blind to it (r=1), depending on geometric
   alignment. This is the concrete physical mechanism.

## Limitations [paper]
- Review article — no new results, but comprehensive mapping of existing work
- All frameworks discussed are single-qubit or few-qubit; no QEC/stabilizer instantiations
- The process-tensor approach to classical vs quantum memory [Eq. (52)] requires process
  tensor tomography, which scales exponentially — not yet demonstrated for coded registers
- The single-time quantum memory witnesses [Eq. (46)] are easier to compute but weaker
  (sufficient but not necessary)

## Tags
- `[paper]` comprehensive taxonomy: CP-divisibility → BLP → process-tensor → temporal entanglement
- `[paper]` classical vs quantum memory: process-tensor separability [Eq. (52)] is the structural criterion
- `[paper]` operational classicality = diagonal process tensor in measurement basis [Eq. (51)]
- `[ours]` K-survival proposition = first instantiation of this framework on stabilizer-parity records
- `[ours]` r=1 collapse = process tensor approximately diagonal (measurement aligned with coupling)
- `[ours]` r≠1 survival = temporal off-diagonals survive (misalignment)
