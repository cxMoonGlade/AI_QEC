# Full-text review — M. J. Gullans & D. A. Huse, "Scalable probes of measurement-induced criticality" (arXiv:1910.00020v2, Phys. Rev. Lett. 125, 070606, 2020)

> **Provenance:** FULL-TEXT read (精读). Source: `docs/papers/gullans_huse_scalable_probes_mipt_1910.00020.txt`
> (957 lines, arXiv plaintext extraction including Supplemental Material I–II). ID/title verified against
> the header (arXiv:1910.00020v2 [cond-mat.stat-mech], 10 Jun 2020; "Michael J. Gullans and David A. Huse,
> Scalable probes of measurement-induced criticality"; published PRL 125, 070606). All section/equation/
> figure references below are taken directly from this text (main Letter §Introduction through §Conclusions,
> plus Supplemental Material §I "Decoding light cone" and §II "Surface exponent").

## Metadata [paper]

- **Authors / affiliation:** Michael J. Gullans (Princeton Physics), David A. Huse (Princeton Physics +
  Institute for Advanced Study).
- **Venue / status:** arXiv:1910.00020v2, 10 Jun 2020. Published Phys. Rev. Lett. 125, 070606 (2020).
  Letter + Supplemental Material (2 sections).
- **Type:** Theory + numerics. Introduces a local order parameter for measurement-induced criticality
  (MIC) and validates it via exact classical simulation of a 1+1D Clifford stabilizer circuit (polynomial-time
  classically simulable per Gottesman–Knill / Aaronson–Gottesman, refs [24, 25]).
- **Key relationship to our work:** this is a primary source for the "does p≈1 syndrome extraction sit in
  the area-law/bounded phase" question that motivates the crux. It reports the **numerical value of the
  critical measurement rate p_c** and correlation-length exponent ν for one concrete monitored-Clifford-circuit
  universality class, and states explicitly (Introduction, refs [13–15]) the qualitative rule: high measurement
  rate → area-law entangled steady state; low measurement rate → volume-law entangled steady state. It is
  NOT about surface-code syndrome extraction, tensor networks, PEPS, or leakage — the relevance is by
  analogy/universality-class argument only, and the note is explicit below about where that analogy is and
  is not licensed.

## Executive summary [paper]

The paper studies "hybrid" quantum circuits made of layers of local (2-site) unitary gates interspersed with
single-site projective measurements applied with probability p at every site every layer (Eq. 1–2, Fig. 1a).
Such circuits undergo a measurement-induced entanglement transition: area-law steady states at high p, volume-law
at low p, with a critical p_c separating the two (Introduction, citing Li–Chen–Fisher 2018/2019, Skinner–Ruhman–Nahum
2019, Chan–Nandkishore–Pretko–Smith 2019). The authors introduce a genuinely LOCAL, experimentally scalable
order parameter: the average entropy S_Q of a single reference qubit initially maximally entangled with one
system qubit, after tracing out the rest of the system and environment (Eq. 3–5). They validate this order
parameter on a 1+1D random-Clifford-gate + Z-basis-measurement stabilizer circuit (the Li–Chen–Fisher model,
ref [16]), extracting p_c = 0.1598(5) and correlation-length exponent ν = 1.30(5) from finite-size scaling
(Fig. 1b), consistent with prior estimates. They then establish a "decoding light cone" — the classical
measurement record needed to predict/decode the reference qubit's purification is confined to a bounded
space-time region set by the correlation length ξ ~ |p − p_c|^(−ν) (§ "Decoding light cone", Fig. 2) — which
is what makes their probe scalable with only polynomially many experimental runs. Finally they extract
surface (β_s, η_∥) and bulk (η) critical exponents by placing the order parameter at the boundary vs. interior
of the system (Fig. 3), finding rough proximity to 2D percolation exponents in several cases but not others.

## Method (deep) [paper]

**Circuit model (Eq. 1–2, Fig. 1a).** A 1+1D chain; each layer applies spatially local 2-site unitaries
`U_t`, then a round of single-site projective measurements `P_t^{m_t}` (m_t ∈ {0,1}) is applied to EACH site
independently with probability p (i.e. p is a per-site, per-layer Bernoulli measurement rate, not a global
schedule). For the numerical test, each 2-site unitary is an independently-drawn random 2-qubit Clifford
gate and each measurement (when it occurs) is a projective Z-basis measurement (this is the Li–Chen–Fisher
stabilizer-circuit universality class, ref [16], efficiently simulable via the stabilizer/tableau formalism,
refs [24, 25]).

**Reference-qubit order parameter (Eq. 3–6).** The system is purified with a reference qubit R:
`|ψ_RS⟩ = Σ_k √λ_k |k_R⟩|k⟩`. Evolving under the channel (extended to a unitary on system+environment) and
conditioning on the measurement record `m⃗`, the reduced state ρ_{R,m⃗} on the reference qubit (Eq. 4) is
either a fully mixed-like state (poor decodability — volume-law/"ordered" phase) or nearly pure (fully
decodable — area-law/"disordered" phase). Two order parameters are defined from ρ_{R,m⃗}: the **quantum**
order parameter S_Q = coherent quantum information = the record-averaged entropy of the reference qubit
(Eq. 5) — nonzero in the ordered (volume-law) phase, → 0 in the disordered (area-law) phase; and a
**classical** analogue S_C (Eq. 6, off-diagonal elements dropped) measuring the environment's ability to
learn the reference's classical bit.

**Control parameter:** the single-site measurement probability p ∈ [0, 1]. p is tuned continuously; the
transition is located by finite-size scaling of the circuit-averaged ⟨S_Q⟩ across system sizes L (Fig. 1b),
using the scaling ansatz ⟨S_Q⟩ = F[(p − p_c) L^{1/ν}, t/L] (Eq. 7), fixing the dynamical exponent z = 1 by
the model's emergent 1+1D conformal symmetry (cited to refs [16, 22]).

**Decoding light cone (§ main text + Supp. Mat. §I).** They define `⟨ΔS_Q(x,t)⟩`, the average change in S_Q
due to a measurement at spacetime point (x,t) (Fig. 2a). Empirically this is confined to a bounded causal
region around the reference qubit's initial location, with an extent set by ξ ~ |p − p_c|^{−ν} for p ≠ p_c;
truncating the measurement record outside a cutoff |x − x_0| below this bound still reproduces ⟨S_Q⟩ accurately
(Fig. 2b), for both p = 0.08 ≈ p_c/2 (volume-law side) and p = 0.24 ≈ 3p_c/2 (area-law side). At p_c itself the
decoding light cone technically diverges (ξ → ∞), but entanglement growth at criticality in 1+1D is only
LOGARITHMIC in time (cited to Skinner–Ruhman–Nahum, ref [14]), so classical-simulation-based decoders remain
practical even there.

**Surface/bulk exponents (Fig. 3, Supp. Mat. §II).** Surface exponent β_s obtained from ⟨S_Q⟩ at time t = 2L
with the reference entangled at a boundary/surface site, scaling as ⟨S_Q⟩ ~ |p − p_c|^{β_s} away from
criticality (Fig. 3a). Bulk exponent η and surface exponent η_∥ obtained from the two-point mutual information
between TWO reference qubits placed at different sites, at p = p_c, scaling per Eq. 10 (Fig. 3b–c). An
alternative estimate of η_∥ via purification dynamics of 1 or 4 reference qubits maximally entangled with a
contiguous region (Supp. Mat. §II, Eq. S1) gives a drifting estimate depending on the number/extent of
reference qubits used.

## Results + numbers [paper]

| Quantity | Value | Where |
|---|---|---|
| Critical measurement rate p_c (L = 64–256) | 0.1598(5) | Fig. 1b crossing |
| p_c (small-size restricted, L = 4–16) | 0.16(1) | main text, "applicable to small-scale systems" |
| Correlation-length exponent ν | 1.30(5) (L=64–256); 1.3(2) (L=4–16) | Fig. 1b inset (data collapse) |
| Dynamical exponent z | 1 (fixed, not fit) | emergent 1+1D conformal symmetry, refs [16, 22] |
| Surface order-parameter exponent β_s | 0.45(2) | Fig. 3a fit; cf. 2D percolation β_s = 4/9 ≈ 0.444 |
| Bulk exponent η | 0.22(1) | Fig. 3b collapse; cf. 2D percolation η = 5/24 ≈ 0.208 |
| Surface exponent η_∥ (mutual-info method, PBC, 3 estimates) | η_∥1=0.74(1), η_∥2=0.67(2), η_∥3=0.58(2) → combined η_∥ = 0.7(1) | Fig. 3c; cf. 2D percolation η_∥ = 2/3 |
| Surface exponent η_∥ (purification-dynamics method, 1 / 4 ref qubits) | 0.70(2) / 0.76(2) | Supp. Mat. §II, Eq. S1, Fig. S2 |
| Surface exponent η_∥ (independent method, ref [37], Li–Chen–Ludwig–Fisher) | 0.82 | cited comparison, slightly different p_c estimate |
| Correlation length ξ | ξ ~ |p − p_c|^{−ν} | governs decoding-light-cone extent |
| Entanglement growth AT p_c in 1+1D | logarithmic in time (not extensive) | cited, ref [14] (Skinner–Ruhman–Nahum) |
| Entanglement growth in volume-law phase (p < p_c) before decoder saturates | timescale ~ ξ^z | main text, "decoding light cone" paragraph |

All quantities are for the specific 1+1D random-2-qubit-Clifford + single-site-Z-measurement model. No d>1
spatial dimension, no leakage/qutrit physics, and no structured (fixed, translation-invariant, CSS-stabilizer)
circuit is simulated anywhere in this paper.

## The regime boundary [paper → the crux]

**What sets bounded (area-law) vs. growing (volume-law) entanglement here.** The single tunable control
parameter is the per-site measurement probability p. The paper's own framing (Introduction, citing refs
[13–15]): "there is a phase transition between an area-law entangled state in the system at **high**
measurement rate and a volume-law entangled state at **low** measurement rate." In this specific model,
p_c ≈ 0.16 — i.e. only ~16% of sites need to be measured per layer, on average, before the system is already
on the area-law (disordered) side. For p > p_c, the reference qubit purifies (ρ_{R,m⃗} → pure) on a
timescale set by the correlation length ξ ~ |p − p_c|^{−ν}, which shrinks rapidly as p is pushed above p_c;
deep in the area-law phase (p well above p_c, e.g. p → 1) correlations/entanglement should be confined to a
SHORT, p-dependent length/time scale, not growing with system size or number of rounds. This IS the
"bounded/area-law" regime in this paper's own terms — it is directly PROVEN (not conjectured) for this
model via the finite-size-scaling collapse (Fig. 1b) and the explicit decoding-light-cone truncation test
(Fig. 2b, both boundary-condition variants in Supp. Mat. §I, Fig. S1).

**Where p ≈ 1 (near-maximal measurement rate) sits.** Since p_c ≈ 0.16 ≪ 1, any circuit measuring at rate
p ≈ 1 sits FAR on the area-law side of the transition (deep disordered phase), not merely past p_c. The
paper does not compute exponents or bond-dimension-type quantities exactly at p = 1, but the physics of the
transition (ξ ~ |p−p_c|^{−ν} shrinking monotonically away from p_c) implies short correlation length and
strongly suppressed entanglement generation at p ≈ 1, i.e. this is the paper's clearest quantitative support
for "high measurement rate ⇒ short-range/bounded entanglement," which is the qualitative statement our crux
needs, extracted from the same reference this paper cites for the general rule (refs [13–15], and the
authors' own companion work [19]).

**Geometry / lattice / structure dependence — the caveats that matter most for our crux.**
1. **Dimensionality.** Everything numerically demonstrated here is **1+1D** (a 1D chain, 2-site nearest-
   neighbor gates). The Conclusions section states explicitly: "Many open questions remain about the
   appropriate classification of these phase transitions, especially **outside 1+1 dimensions** or in the
   presence of quenched disorder." p_c, ν, and even z=1 (fixed by an emergent 1+1D conformal symmetry that
   need not exist in 2D) are 1D-specific numbers. Our target is a genuinely 2D (d=5 rotated-XZZX) lattice;
   this paper gives NO 2D p_c or exponents, and does not claim the 1D values transfer.
2. **Circuit structure: random vs. structured/deterministic.** The unitaries here are drawn i.i.d. from the
   Haar-random-over-Clifford ensemble each layer, and the measurement pattern is i.i.d. Bernoulli(p) per
   site per layer — a fully RANDOM, disorder-averaged circuit. A real syndrome-extraction circuit is a FIXED,
   deterministic, translation-invariant sequence of CNOTs measuring specific weight-4 stabilizer generators
   via ancillas — not a random circuit and not a random measurement pattern. The paper is silent on whether
   structured/deterministic stabilizer circuits share the same transition or the same qualitative "high-rate
   ⇒ area-law" rule; it only asserts the rule holds "[f]or rather generic choices of unitaries" (main text,
   Order-parameter-measurement section), which is a genericity claim about the unitary ensemble, not a proof
   that a fixed stabilizer-code circuit is equivalent.
3. **What is measured.** The model projects INDIVIDUAL system qubits directly in the Z basis with
   probability p. Real syndrome extraction never directly measures data qubits — it entangles ancillas
   with several data qubits (a weight-4 stabilizer) via CNOTs, then measures only the ancilla. This is
   structurally a different (weaker, multi-qubit, non-destructive-of-the-code-word) measurement than the
   projective single-site measurements analyzed here. The paper does not model ancilla-mediated stabilizer
   measurement at all.
4. **No leakage / no CPTP noise / no non-Pauli physics.** The circuit is exactly unitary-Clifford +
   projective-measurement (pure-state stabilizer formalism); there is no qutrit leakage, no thermal/Kraus
   noise, no mixed-state (density-matrix) evolution anywhere in this paper. Our carrier's entanglement
   growth is driven in part by exactly this kind of non-Pauli/leakage physics, which is entirely outside
   this paper's scope.
5. **Caveat toward growth, explicitly flagged by the authors:** long-range interactions. The Conclusions
   note "In cases with long-range interactions, entanglement within the system may no longer be a useful
   diagnostic of the phase transition" — i.e. the clean area-law/volume-law dichotomy tied to a single
   measurement-rate knob is itself known to break down or require reinterpretation once interactions/
   correlations are not strictly local, which is a live concern for any noise model with correlated
   (non-local) errors.

## Relevance to the d5 PEPS crux [ours]

This paper is the strongest *quantitative* anchor in our reading list for the qualitative direction "high
measurement rate → bounded/area-law entanglement," and it is directly on-point for the general MIPT rule our
pilot-artifact hypothesis leans on: p_c ≈ 0.16 is small, so a syndrome-extraction circuit with effective
measurement rate p ≈ 1 (every ancilla measured every round) sits deep in the area-law/disordered phase of
THIS universality class, not near a critical point where entanglement would be expected to grow with system
size or number of rounds. To the extent the "measurement rate → regime" rule generalizes at all (which is
the paper's own claimed genericity, "for rather generic choices of unitaries"), this SUPPORTS the working
hypothesis that our pilot's fast bond growth (4→18→>40 in 2 rounds) is an instrument artifact — a real
p≈1 stabilizer-measurement process, if it behaved anything like this universality class, should produce
SHORT correlation length / bounded entanglement, not runaway growth.

However, this support is a **universality-class analogy, not a proof for our system**: (1) the paper is
strictly 1+1D and says nothing about 2D p_c or whether the transition even exists in the same form on a
d=5 surface-code lattice; (2) it studies fully random Clifford circuits with i.i.d. single-site Z
measurements, not the fixed, translation-invariant, weight-4-stabilizer/ancilla-mediated circuit our
syndrome extraction actually runs — the mapping from "p" in this paper to "our circuit's effective
measurement rate" is qualitative, not a like-for-like parameter identification; (3) it has zero leakage/
non-Pauli/qutrit content, and our suspected instrument artifact (compiled weight-4 √E_s POVM injecting
spurious entanglement) is exactly the kind of "structured/engineered operator, not a generic single-site
projector" object this paper does not model. So: this paper is consistent with, and lends generic-rule
support to, "bond should saturate at p≈1" — but it does NOT itself certify that our specific single-wire 2D
PEPS carrier for a structured d=5 stabilizer circuit will saturate; it is silent on geometry (2D), circuit
structure (deterministic stabilizer vs. random Clifford), and the leakage/POVM specifics that are the
prime suspects for our pilot's growth.

## How to use / trust + open questions [ours]

- **Trust level:** FULL-TEXT 精读 (957-line plaintext extraction incl. Supplemental Material). Peer-reviewed
  (PRL). Numbers (p_c, ν, exponents) are load-bearing results of the paper's own finite-size-scaling fits,
  not review claims — cite with the (·) uncertainty as given.
- **Epistemic status for our use:** the "high measurement rate ⇒ area law" direction is the paper's own
  PROVEN result for its specific 1+1D random-Clifford model (Fig. 1b + Fig. 2 are direct numerical evidence);
  its application to our d=5 2D structured syndrome-extraction PEPS is an ANALOGY by universality-class
  genericity, not a transferred theorem — flag any downstream claim built on this note as provisional per
  the repo's epistemic-status discipline.
- **What would need to be true for the analogy to actually hold:** either (a) find a paper that studies the
  transition for STRUCTURED/deterministic (non-random) local-check circuits (e.g. the "self-organized error
  correction" line, ref [41] in this paper: R. Fan, S. Vijay, A. Vishwanath, Y.-Z. You, arXiv:2002.12385) or
  for genuine stabilizer-code syndrome-extraction circuits specifically, or (b) for a 2D lattice geometry
  (this paper is 1D only), or (c) directly measure OUR carrier's bond growth after removing the suspected
  compiled-POVM/truncation artifact and check it against the qualitative "should shrink toward p≈1" prediction
  empirically rather than relying further on analogy.
- **Immediately actionable numbers:** none of p_c/ν/η here are directly usable as thresholds for our system
  (different geometry/model class) — use this paper ONLY for the qualitative "high p ⇒ short ξ ⇒ bounded
  entanglement" direction, and for its own honest limitation list (1D-only; generic-unitary caveat;
  long-range-interaction caveat) when writing the crux's risk register.
- **Companion papers worth chasing next** (cited inside this one, not yet read): [19] Gullans & Huse,
  "Dynamical purification phase transition induced by quantum measurements" (arXiv:1905.05195) — a
  MEASUREMENT-ONLY variant, structurally closer to ancilla-mediated stabilizer measurement than the
  unitary+measurement model here; [41] Fan, Vijay, Vishwanath, You, "Self-Organized Error Correction in
  Random Unitary Circuits with Measurement" (arXiv:2002.12385) — explicitly frames the ordered phase as a
  QEC code, which is the right frame to check whether "ordered/volume-law" (protected logical info) vs.
  "disordered/area-law" (info leaked to measurement record) maps onto "good code" vs. "bad code" the way our
  intuition about syndrome extraction wants it to; and [33] Ippoliti, Gullans, Gopalakrishnan, Huse, Khemani,
  "Entanglement phase transitions in measurement-only dynamics" (arXiv:2004.09560).
