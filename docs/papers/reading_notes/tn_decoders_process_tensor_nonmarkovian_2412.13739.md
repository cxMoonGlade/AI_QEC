# Full-text review — Kobayashi, Manabe, White, Farrelly, Modi, Stace, "Tensor-network decoders for process tensor descriptions of non-Markovian noise" (arXiv:2412.13739)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF `outputs/papers/2412.13739.pdf` → txt
> `outputs/papers/2412.13739.txt` (PyMuPDF, 27 pages / 67040 chars). All §/Eq/Fig/Table refs from that
> text (pages 1–23 body + references). Figures NOT pixel-extracted — figure facts = captions + numbers
> stated in text (Fig. 9 / Fig. 12 / Table 2 numbers are read from the extracted numeric columns).

## Metadata [paper]
- **Authors / affiliation.** F. Kobayashi & H. Manabe (Osaka U.), G. A. L. White (FU Berlin), T. Farrelly &
  T. M. Stace (U. Queensland / EQUS), K. Modi (Monash). Modi = corresponding.
- **Venue / status.** arXiv:2412.13739v1 [quant-ph], 18 Dec 2024. Preprint.
- **Type.** Theory + small-scale numerical simulation (no hardware, no hardware-tomographed process
  tensor — the process tensor is *synthetically constructed* from a declared microscopic noise model).

## Executive summary [paper]
Question: how do you build an **optimal (ML) decoder** for a stabiliser QEC code when the noise is genuinely
non-Markovian / spatiotemporally correlated, described exactly by a **process tensor** (quantum comb) rather
than an iid Pauli channel? Method: represent the whole QEC episode — encoder, the process tensor Υ (which
carries the bath memory), the syndrome-measurement instruments, and the recovery — as **one tensor network of
Choi states contracted with the link product ⋆**; the ML logical operator per syndrome is the `argmax`/`argmin`
of a closeness-to-identity objective (Hilbert–Schmidt overlap χ_HS, Eq. 43/44, or channel-distance χ_CD,
Eq. 47/48), and the logical failure rate is a single TN contraction (Eq. 45/49), NOT a Monte-Carlo sample
average. Demonstrated on the **[[5,1,3]] perfect code** and **[[7,1,3]] Steane code**, one round of syndrome
measurement, with a noise model mixing iid depolarising + Heisenberg system–bath coupling (non-Markovian, NM)
+ ZZ crosstalk (CT). Headline: **both NM and CT raise the logical failure rate** (Fig. 9, Table 2); the effect
"suddenly appears" once J_NM / J_CT reach **~10× the stochastic per-error rate p_err** (Fig. 9c). Second
contribution: an **MPS approximation** of Υ + tester that reproduces the exact LER "in low-noise regimes" at
much lower cost (Steane, Table 2). No baseline Markov/Pauli decoder is run head-to-head — the comparison is
NM/CT-aware ML decoder vs. *itself at J=0*, not vs. a mismatched decoder.

## Method (deep) [paper]

**Representation (all in Choi / double-ket form).** Vectorisation `vec(|ψ⟩⟨ϕ|)=|ψ⟩⊗|ϕ*⟩` (Eq. 4); a channel Ě
acts as a matrix on `|ρ⟩⟩` (Eq. 7–8); Choi state `Υ_E = (E⊗I)[|Φ+⟩⟨Φ+|] = Σ_ij E[|i⟩⟨j|]⊗|i⟩⟨j|` (Eq. 9);
channel action via Choi is `Ě|ρ⟩⟩ = vec(tr_i[(1_o⊗ρ^T)Υ_E]) = _i⟨⟨ρ*|Υ_E⟩⟩_o` (Eq. 10). A quantum instrument is a
set of CP maps `J={A_j}` summing to CPTP with `ρ'_j = A_j[ρ] = Σ_α K_{α,j} ρ K†_{α,j}`, `P(j|J)=tr(A_j[ρ])`
(Eq. 12); Choi form `P(j|J) = ⟨⟨A*_j|1⟩⟩_o ⊗ |ρ⟩⟩_i` (Eq. 14).

**Process tensor (the non-Markovian object).** For a k-step process, the state after a chosen control sequence
`A_{xT_{k-1}}` is `ρ[A_{xT_{k-1}}] = tr_E[ ⃝_{j=0}^{k-1} U_j ∘ A_{x_j}(ρ_SE(0)) ] =: Υ_{T_k}[A_{xT_{k-1}}]`
(Eq. 17). Key structure: **the CP maps A_j act only on the system S, but the interleaving unitaries U_j act on
BOTH S and E** — tracing out E leaves temporal correlations, i.e. Υ is the multi-time comb that carries the
bath memory forward across steps. Contracting Υ with a control/instrument sequence gives outcome probabilities
`P(xT_k|JT_k) = tr[Υ_{T_k}[A_{xT_k}]] = ⟨⟨1_{o_k}|Υ_{T_k}[A_{xT_k}]⟩⟩` (Eq. 20). A **tester** (Eq. 23) is a
correlated instrument with "common memory" (ancilla) — this is exactly what feed-forward syndrome→recovery is.

**QEC as a tester contracted into Υ ("strategic code" / "interleave QEC").** Syndrome measurement of stabiliser
generator G_j is the projective instrument `J_j = {π_{x_j} = (1+(-1)^{x_j}G_j)/2}` (Eq. 25), CP map
`Π_{x_j}(•)=π_{x_j}•π_{x_j}` (Eq. 26). The post-syndrome (un-normalised) state with the process tensor is
`|ρ(t_{n-k+1}|x, J_C)⟩⟩ = (⟨⟨Π*_x| ⊗ ⟨⟨ρ*_{L,i}|)|Υ_{T_{n-k+1}}⟩⟩` (Eq. 27). Recovery `R(ρ|x)=R(x)ρR†(x)`
(Eq. 28). The (syndrome-measurement + recovery) pair is a single **large tester** with the classical syndrome
correlation enforced by a Kronecker delta `δ_{x,x'}` between the measured and the fed-forward outcome
(Eq. 30 / Eq. 37). **This δ is where the syndrome likelihood enters** — the process tensor's temporal
correlations flow through Υ, and the tester's δ ties the recovery choice to what Υ actually produced.

**ML decoder.** Pure errors (destabilisers) `P(s⃗)=Π_i P_i^{s_i}` fix a representative error for syndrome s⃗
(Eq. 31). Degeneracy: `P(s⃗)SL` all share s⃗; only the logical class L matters (Eq. 32 for the iid-Pauli
objective `χ(L,s⃗)=Σ_{S∈S_C} P(P(s⃗)SL)`). Recovery `R(s⃗)=L̄ P(s⃗)`, `L̄=argmax_L χ(L,s⃗)` (Eq. 33). Choi form
`R(L,x)=L ⋆ P(x)` via the **link product ⋆** (Eq. 36) which composes maps at the Choi level.

**The two process-tensor objectives (the actual decoder objective functions):**
- **Hilbert–Schmidt overlap** `χ_HS(L,s⃗) = ⟨⟨ Π_dec ⋆ I ⋆ [C_{Lpdc,spdc}] ⋆ Υ_{T_{n-k+1}}[C_{L,s⃗}] ⋆ Π_enc | Υ_1 ⟩⟩`
  (Eq. 43) — overlap of the full strategic-code process (encode → noisy Υ → syndrome → recover → *perfect*
  syndrome+decode round via the identity comb I) with the logical identity channel. `L̄(s⃗)=argmax_L χ_HS`
  (Eq. 44). Note: a **perfect (noiseless) second round of syndrome measurement + decode is appended** so that
  errors that slipped past the (noisy) first round are counted as failures. **χ_HS ignores off-diagonal /
  coherent terms of the logical channel** (paper flags this as a limitation of the HS metric).
- **Channel distance** `χ_CD(L,s⃗) = ‖ Π_dec ⋆ I ⋆[C_{Lpdc,spdc}] ⋆ Υ[C_{L,s⃗}] ⋆ Π_enc − Υ_1 ‖_2` (Eq. 47),
  `L̄=argmin_L χ_CD` (Eq. 48); the 2-norm (Frobenius) distance to the identity Choi — DOES see coherence, but
  "cannot satisfy the strict axioms of probability" (paper's caveat).

**Logical failure rate (single TN contraction, not MC):**
- HS: `p_fail = 1 − Σ_{s⃗} χ_HS(L̄(s⃗), s⃗)` (Eq. 45).
- CD: `p_fail = Σ_{s⃗} p(s⃗) χ_CD(L̄(s⃗), s⃗)`, with `p(s⃗)=tr[ρ_L Π_enc^T Π_{s⃗}^T Υ]`, ρ_L the completely mixed
  logical state (Eq. 46, Eq. 49). Sum over ALL syndromes s⃗ ∈ {0,1}^{n-k} — the TN contraction yields the whole
  per-syndrome success matrix at once (Fig. 8b).

**MPS approximation (Steane, §4.3).** State-vector cost of Υ+tester is `4^{2n+1}·2^k` (Steane n=7,k=6 → 2^36,
needs HPC). Instead represent Υ and tester as **MPS** with index ordering [auxiliary | data₁ bath₁ data₂ bath₂
… | classical bits] (Fig. 10b); noise + stabiliser measurements are MPOs applied by MPO-MPS evolution;
truncate to max bond dimension D=χ and drop singular values below 10^-8; trace out bath qubits at the end. The
decoder-side tensor `Q(L,s⃗)=Π_dec ⋆ I ⋆[C_{Lpdc,spdc}] ⋆ R(L,s⃗)` (Eq. 53) is noise-independent, built once,
cheap. Estimation and TN-decoder-performance LERs are Eq. 54 (`p_est`, uses approx Υ̃, p̃ both for building AND
scoring) and Eq. 55/56 (`p_perf`, decoder L̃ chosen from approx Υ̃ but scored against the EXACT Υ — the honest
"how good is the approximate decoder" number). Diagnostic: **bipartite entanglement entropy (BEE)** between
classical and quantum subsystems (Fig. 11) is small at low noise → biased syndrome distribution → aggressive
truncation is safe.

## The MECHANISM (for implementation) [paper → ours]
The synthetic noise model (§4.1, Fig. 7) — three tunable ingredients per step, per data qubit i:
1. **Stochastic (iid Markovian) depolarising:** `E_dep(ρ,p_err) = (1−p_err)ρ + p_err Σ_{σ∈{X,Y,Z}} σρσ†`
   (Eq. 50). [NB this is the *3p* convention: weight p_err on EACH of X,Y,Z, total error prob 3·p_err.]
2. **Non-Markovian (NM) system–bath Heisenberg coupling:** `U_NM = exp{−i J_NM (X_i X_{B_i} + Y_i Y_{B_i} +
   Z_i Z_{B_i})}` (Eq. 51). Each data qubit i has its OWN local bath qubit B_i; U_NM entangles them, and
   because the bath is carried across steps (not reset), this injects TEMPORAL (non-Markovian) correlation on
   that qubit. This is the load-bearing "memory" ingredient.
3. **Crosstalk (CT) ZZ coupling:** `U_CT = exp{−i J_CT Z_i Z_{i+1}}` (Eq. 52). Coherent ZZ between neighbouring
   *data* qubits — SPATIAL correlation, coherent (unitary), no bath.
Grounded magnitudes swept: `p_err ∈ [10^-6, 10^-1]`; `J_NM, J_CT ∈ {0, 10^-4, 10^-3, 10^-2, 10^-1}` (Fig. 9);
Table 2 uses matched `p_err=J_CT=J_NM ∈ {10^-4, 10^-3, 10^-2}`. Baths are one qubit per data qubit, traced out
per step. **This is close in spirit to our coupled teacher's Axis-2 (shared-latent / bath source coupling) +
Axis-1 (ZZ crosstalk), but the NM here is per-qubit private baths (not a shared latent source), so it produces
temporal but NOT genuinely correlated-across-qubits non-Markovianity.**

## The OBSERVABLE / metric [paper]
- **Headline observable = logical failure rate p_fail**, computed as a deterministic TN contraction over all
  syndromes (Eq. 45 HS-metric / Eq. 49 CD-metric), NOT a MC LER. This is our ΔLER-family observable but note
  it is *decoder-optimal by construction* (ML), so it measures the intrinsic decode-relevant impact of the
  noise under the BEST decoder — there is no suboptimal-decoder baseline in the same plot.
- **Two metrics, and the paper explicitly flags one as insufficient:** χ_HS (inner-product, Eq. 43) is
  **blind to coherent/off-diagonal logical error** — the paper says so directly and introduces χ_CD (2-norm,
  Eq. 47) to capture coherence, at the cost of χ_CD not being a strict probability. (For our purposes: if the
  non-Markovian/coherent wedge is coherence-carrying, the HS metric will UNDER-count it — a direct warning that
  a diagonal/Pauli-only likelihood misses exactly the coherent part we care about.)
- **MPS-quality observables:** infidelity `1−F` of the approximate final state vs exact; `p_est` (Eq. 54)
  vs `p_perf` (Eq. 55) to separate "approximation error in estimating LER" from "performance loss of the
  approximate decoder"; BEE (Fig. 11) as the truncation-safety diagnostic.

## Findings + numbers [paper]
**Five-qubit code (Fig. 9), one round:**
- Even at **J_NM = J_CT = 0**, p_fail is NOT suppressed to zero — because with a single noisy syndrome round an
  error occurring *after* the measurement it would trigger goes undetected; the decoder cannot pick the right
  recovery. (This is a single-round artifact, not a non-Markovian effect — see Limitations.)
- Both **stronger NM and stronger CT raise p_fail** (Fig. 9a/b). NM adds real noise (info leaks to bath) so its
  curve sits *above* CT for equal coupling; CT is unitary and "only scrambles information" but still degrades
  the LER. The paper insists a *fair* comparison must account for the extra bath noise J_NM>0 introduces.
- **Threshold-of-appearance (Fig. 9c, p_err=10^-3 fixed):** the NM and CT effects "suddenly appear at ~10×
  greater strengths of J_CT and J_NM than the stochastic error probability." → the correlated-noise penalty
  turns on when coupling ≳ 10·p_err.
- The paper is blunt that the 5-qubit code "is not designed to handle complex noise" and its performance "was
  not distinguished" — the point is the *framework*, not a code that beats correlated noise.

**Steane code + MPS (Table 2), one round:** exact-TN LER reproduced by MPS. Representative (matched noise):
| noise (p_err=J_CT=J_NM) | exact p_fail | MPS χ=128 | MPS χ=1024 | 1−F @χ=1024 | time χ=1024 vs exact |
|---|---|---|---|---|---|
| 10^-4 (low)  | 8.083e-4 | p_est 6.27e-4 / p_perf 9.03e-4 | 8.08e-4 | 4.1e-13 | 199s vs 532s (MPS faster) |
| 10^-3 (med)  | 8.691e-3 | 6.74e-3 / 9.63e-3 | 8.691e-3 | 1.1e-12 | 1320s vs 532s (MPS slower) |
| 10^-2 (high) | 1.355e-1 | 1.15e-1 / 1.43e-1 | 1.355e-1 | 5.6e-7 | 6378s vs 532s (MPS much slower) |
- **Low noise:** even χ=128 lands close and is FASTER than exact (63s vs 532s at 10^-4); MPS is a genuine win.
- **High noise:** MPS needs large χ, and at χ=1024 it is ~12× SLOWER than exact — the approximation stops
  paying off. Trade-off is explicit.
- **NM is the hardest for the approximation:** "in regions where non-Markovian noise is strong, a clear
  performance decrease is evident," whereas strong depolarising/CT do not degrade the TN-decoder performance.
  → non-Markovianity is precisely the ingredient that inflates entanglement / bond dimension.

## Limitations [paper]
- **Single round of syndrome measurement only.** Explicitly stated in the Conclusion: "Our construction of the
  ML decoder treats just single round syndrome measurement." No repeated-measurement / space-time decoding; the
  irreducible J=0 failure floor is a direct consequence. Multi-round is named as future work (and would blow up
  the TN size).
- **Small codes only:** [[5,1,3]] and [[7,1,3]] — distance 3, k=1. State-vector cost 4^{2n+1}·2^k; even Steane
  needed MPS or HPC. No surface code, no d>3, no scaling study of the LER-vs-distance kind.
- **Synthetic process tensor, not tomographed.** Υ is built from the declared Eq. 50–52 model with 1 bath
  qubit per data qubit; not a device-measured process tensor. NM is per-qubit PRIVATE baths → temporal
  correlation but no shared-bath cross-qubit non-Markovian correlation.
- **No head-to-head vs a Markov/Pauli decoder.** The decoder is always the process-tensor-aware ML decoder;
  the "gap" is measured as p_fail(J>0) − p_fail(J=0) under the *same optimal* decoder, i.e. the intrinsic noise
  penalty, NOT "PT-aware decoder beats a mismatched Markov decoder by X%." That specific number is absent.
- **HS metric coherence-blind** (Eq. 43); CD metric not a proper probability (Eq. 49). No diamond-distance run.
- MPS accuracy has "no guarantee" for more qubits / multiple measurements / strong noise; relies on biased
  syndrome distributions (low BEE) which fails at high noise.

## Relevance to qec_twin [ours]
**This is the closest published match to the DECODER side of our coupled-teacher program.** It supplies, in one
paper: (1) a formally optimal (ML) decoder whose likelihood is built *directly from a process-tensor
description of non-Markovian noise* — exactly the object our coupled teacher emits; (2) the decode-relevant
observable (p_fail / LER via TN contraction); (3) a quimb+cotengra MPS carrier that is architecturally the
same class as our `forward/scalable` MPS carrier (ADR 0008/0010). Concrete reuse / correction points:

- **Observable + decoder mapping.** Their χ_HS/χ_CD ML objective (Eq. 43/47) → argmax/argmin L per syndrome →
  p_fail (Eq. 45/49) is a ready template for a *process-tensor-aware ML decoder* to sit alongside our frozen
  MWPM DEM decoder. It gives the ceiling (ML-optimal) against which a Pauli/DEM decoder's suboptimality on
  correlated noise can be scored — but WE would have to add the mismatched-decoder baseline they omit to get
  our headline "ΔLER of PT-aware vs Markov decoder."
- **Validates that non-Markovian coupling is decode-RELEVANT (partial).** Fig. 9/Table 2 show NM (and CT)
  raise the optimal LER, and that the effect switches on at coupling ≳ 10·p_err. This is evidence that
  correlated noise is NOT decode-benign — but it is the *intrinsic* penalty under an optimal decoder, NOT proof
  that a Markov decoder is fooled (the Kam-benign "syndrome-correlation is captured by Markov-k" strawman we
  worried about is NOT directly refuted here, because they never run a Markov decoder). **Correction it forces:
  our "non-Markovian wedge must be coherence" note is REINFORCED — the HS metric is explicitly coherence-blind,
  so a diagonal/Pauli likelihood under-counts exactly the coherent wedge; and their NM is private-bath
  (removable-ish, adds incoherent noise) not shared-latent, matching our "OWNED/removable vs the real
  contribution" filter.**
- **Reusable engineering.** MPS ordering trick (data/bath interleaved + classical bits last), 10^-8 SV
  threshold, BEE(classical:quantum) as truncation-safety diagnostic, p_est vs p_perf split (approx-estimation
  error vs approx-decoder-performance loss) — all directly portable to our MPS carrier and to how we should
  report approximate-decoder numbers honestly.
- **Cost signal for us.** They confirm NM is the ingredient that inflates bond dimension / kills the MPS
  advantage at strong coupling; and their exact cost is 4^{2n+1}·2^k — i.e. their exact method is d=3-only,
  same wall we hit. Multi-round + surface-code + larger d is exactly the open gap we would need to push into
  (they name minimum-weight matching over pooled multi-round syndromes as the way forward — our frozen-MWPM
  substrate is on that path).

## How to use / trust + open questions [ours]
- **Trust:** FULL-TEXT read; equations verbatim from the extracted txt. Fig. 9 curves read from stated coupling
  values; Table 2 numbers read from the extracted numeric columns (high confidence — they are plain text, not
  raster). Figures not pixel-extracted, but the load-bearing numbers are in Table 2 text.
- **BLUNT verdict answering the three asks:**
  1. **Does a PT-aware decoder beat a Pauli/Markov decoder, by how much, at what scale?** — *Not measured as a
     head-to-head.* The paper builds the optimal PT-aware ML decoder and shows correlated noise (NM/CT) raises
     the optimal LER (5-qubit Fig. 9; Steane Table 2, e.g. exact p_fail 8.08e-4 → 8.69e-3 → 1.35e-1 as
     p_err=J=10^-4→10^-3→10^-2), with the correlated penalty switching on at coupling ≳ 10·p_err. But there is
     **no "PT-aware minus Markov-decoder ΔLER" number** — that comparison is the piece WE must add. Scale = d=3
     only ([[5,1,3]], [[7,1,3]]), single round.
  2. **Which non-Markovian noise?** — Per-data-qubit PRIVATE bath via Heisenberg XX+YY+ZZ system–bath coupling
     U_NM (Eq. 51, temporal correlation on each qubit), plus coherent ZZ nearest-neighbour crosstalk U_CT
     (Eq. 52, spatial, coherent), on top of iid depolarising. NOT a shared-latent / shared-bath cross-qubit
     source; NOT tomographed from hardware.
  3. **Reusability as our decoder/observable?** — HIGH for the *decoder construction* (χ_HS/χ_CD ML objective +
     link-product Choi TN + p_fail-by-contraction) and the *MPS engineering* (quimb/cotengra, ordering,
     BEE diagnostic, p_est/p_perf split); it is the right decoder-family + LER observable for our coupled
     teacher. MEDIUM as a *validation of decode-relevance*: it confirms correlated noise inflates the OPTIMAL
     LER but does not close the Kam-benign strawman (no mismatched-decoder baseline), and its HS metric being
     coherence-blind reinforces our "the wedge must be coherence, scored with a coherence-sensitive metric"
     stance. Missing pieces WE own: multi-round space-time decoding, surface code / d>3, shared-latent NM,
     and the explicit PT-aware-vs-Markov ΔLER.
