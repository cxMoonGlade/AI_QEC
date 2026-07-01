# Full-text 精读 — Sheldon, Bishop, Magesan, Filipp, Chow, Gambetta, "Characterizing errors on qubit operations via iterative randomized benchmarking" (arXiv:1504.06597)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/1504.06597.txt` (PyMuPDF text extraction, 5 pages). Figures are not
> pixel-extracted; all equation, table, and figure references are from the extracted text.
> Published version: Phys. Rev. A 93, 012301 (PRA 93, 012301), arXiv:1504.06597v1
> [quant-ph], 24 Apr 2015. (The PRA citation is from the task brief, not the extract; the
> extract carries only the arXiv stamp on p. 1.)

Epistemic tags throughout: **[paper]** = stated/derived in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note is the primary literature anchor for the **coherent single-qubit
over-rotation FAMILY** of QEC-Twin Axis-1 mechanisms: **M6 = coherent_rx_overrotation
(`RX(ε)`), M7 = coherent_rz_overrotation (`RZ(ε)`), M20 = coherent_ry_overrotation
(`RY(ε)`)** (`docs/error_mechanisms.md`; pre-regs `m6_*`, `m7_*`, group 1 of
`axis1_mechanism_completeness_prereg.md`). The Twin's COH_R* families are the
single-qubit `θ_k P_k` terms of the Kaufmann–Rojkov–Reiter generator
`H_θ = Σ_k θ_k P_k`; Sheldon et al. is the **measurement-grounding** reference that (a)
writes the small-angle unitary-error form `U = exp(−i (ε/2) r̂·σ)` that the COH_R*
operators instantiate (axis `r̂ ∈ {X̂, Ŷ, Ẑ}` → M6/M20/M7), (b) shows the
**over-/under-rotation fidelity decay is quadratic in the number of repetitions n** (vs
linear for non-unitary), the signature that distinguishes a coherent over-rotation from
a stochastic Pauli, and (c) **intentionally injects** π/64, π/128, π/256 over-rotations
on a real transmon, giving an empirical anchor for the calibration-residual angle scale
the Twin sweeps over. It grounds the operator form and the realistic angle magnitude;
it does not by itself ground any LER claim.

---

## Metadata [paper]

- **Authors:** Sarah Sheldon, Lev S. Bishop, Easwar Magesan, Stefan Filipp, Jerry M.
  Chow, Jay M. Gambetta (IBM T. J. Watson Research Center, Yorktown Heights, NY).
- **arXiv:** 1504.06597v1, quant-ph, 24 Apr 2015. Dated April 27, 2015.
- **Type:** protocol proposal + experimental implementation on a real transmon.
- **Device [paper]:** "two-qubit sample consisting of two transmon qubits coupled by a
  coplanar waveguide resonator." Qubit of interest: "transition frequency of 5.0154 GHz
  and anharmonicity of −323 MHz. T1 and T2 are 45±6 µs and 53±10 µs."

---

## Executive summary [paper]

Iterative randomized benchmarking (IRB) interleaves a target Clifford `C` repeated `n`
times between random Cliffords and tracks the benchmarking decay `α` versus `n`. The
key discriminator: "The benchmarking fidelity decays quadratically with the number of
interleaved gates for unitary errors but linearly for non-unitary, allowing us to
separate systematic coherent errors from decoherent effects." [paper] Using this, the
authors achieve a benchmarked single-qubit fidelity of **99.95%** and conclude the gate
is **not** limited by unitary errors but by "another drive-activated source of
decoherence such as amplitude fluctuations."

---

## The coherent unitary-error form (the load-bearing equation) [paper]

To derive the quadratic-vs-linear signature the paper posits a single-qubit unitary
error. **VERBATIM (Eq. 1, p. 2, lines 176–184 of the extract):**

```
U = exp( −i ε/2  r̂ · ⃗σ ) ,                                    (1)
"where ϵ, r̂, and ⃗σ are the error angle, axis of rotation, and
 vector of Pauli operators respectively."
```

**[twin]** This is exactly the COH_R* carrier operator: `U_M6 = exp(−i (ε/2) X)`,
`U_M20 = exp(−i (ε/2) Y)`, `U_M7 = exp(−i (ε/2) Z)` — i.e. Eq. (1) with `r̂` selecting
the X̂/Ŷ/Ẑ axis. The Twin's pre-regs reuse precisely this `ε ≡ over-rotation angle`
parameterization (`m6_coherent_rx_overrotation_prereg.md` §1).

**Small-angle expansion (Eq. 2, lines 186–191), verbatim:**

```
U^n = 11 − i n ε/2  r̂·⃗σ − ( n(2n−1) ) ε²/4 (r̂·⃗σ)² + O(ε³) .   (2)
```

**Fidelity / benchmarking-parameter decay (Eq. 3, lines 192–205).** The average fidelity
is `F = ( |tr(U^n)|² + 2 ) / 6`, and in terms of `α = 2F − 1`:

```
α = 1 − [ n(2n−1) ε² / 3 ] ,                                    (3)
```

"which shows the quadratic dependence in n. A similar analysis finds that errors due to
a T1 or T2 process do decay linearly in n." [paper] **This quadratic-in-n coherent
accumulation (vs linear for stochastic) is the physical fingerprint the Twin's coherent
over-rotation mechanisms must reproduce** and is the reason M6/M7/M20 are NOT
DEM-reducible to a stochastic Pauli at the same average rate.

---

## Amplitude-calibration fit functions [paper]

The over-/under-rotation angle is extracted by error-amplification sequences
`Xπ/2 − (X{π,π/2})²ⁿ`. **Verbatim fit functions (Eqs. 4–5, lines 229–243):**

```
P(|0⟩) = a + ½(−1)^n cos(π/2 + 2nε)      (Xπ/2 pulse)          (4)
P(|0⟩) = a + ½    cos(π/2 + 2nε)         (Xπ pulse)            (5)
```

"The angle error, ϵ, found by this fit corresponds to a gate error r ≈ ϵ²/6." [paper]
**[twin]** The `r ≈ ε²/6` relation (and `2ε²/3` for the X–Y axis-error sequence, line
521) is the same quadratic-in-ε infidelity scaling the Twin's `1−F_e` ledger predicts
for a pure over-rotation; it cross-checks the closed-form `1−F_e ∝ ε²` band in the M6/M7
pre-regs.

---

## Intentional over-rotation injection (the empirical angle anchor) [paper]

**VERBATIM (p. 3, lines 325–329):** "We then intentionally add overrotation errors to
the Xπ gate to determine a bound on the sensitivity of this procedure to amplitude
errors. We repeat the iterative benchmarking procedure with the Xπ/2 pulse replaced with
Xπ/2+ϵ, where ϵ = {π/64, π/128, π/256}."

- Numerically: `π/64 ≈ 0.049 rad ≈ 2.81°`, `π/128 ≈ 0.0245 rad ≈ 1.41°`,
  `π/256 ≈ 0.0123 rad ≈ 0.70°` **[twin]** (degree/rad conversions are ours, not in the
  extract).
- **[paper]** "The π/64 and π/128 overrotations lead to fidelities that fall off
  quadratically and are clearly distinguishable from gates approaching the coherence
  limit. The π/256 appears to have similar errors to the calibrated gates, giving a
  bound on the sensitivity to overrotation errors."
- **[paper]** "From this analysis it follows that a π/128 overrotation is detectable
  with this method and that consequently coherent rotation errors must be smaller than
  this value." Equivalently the residual coherent over-rotation on the calibrated gate
  is `< π/128 ≈ 0.0245 rad`.
- Model selection (Table I, AIC, Eqs. 6–7): the calibrated gate is best fit linear (no
  unitary error); the π/128 gate is best fit by the quadratic model. [paper]

**[twin] Anchor for the sweep range.** The Twin's M6 pre-reg sweeps
`ε ∈ {3e-1 … 1e-3} rad`; this paper pins the **real-hardware injected scale at
π/256–π/64 ≈ 0.012–0.049 rad** and the **detectability floor at ≈ π/128 ≈ 0.0245 rad**,
i.e. the lower-middle of the Twin's swept band is exactly the experimentally
demonstrated calibration-residual regime. This is a magnitude anchor, not a magnitude
that must be frozen.

---

## What the paper does NOT provide [twin]

- **No QEC / LER number.** This is a single-qubit gate-characterization paper; it makes
  no surface-code or logical-error statement.
- **No Z-axis (M7) injection.** The intentional over-rotations are on `Xπ/2`
  (i.e. RX-type, M6). An **X–Y axis error** is separately characterized (Ramsey
  sequence `Xπ/2 − (Xπ − Yπ)^n − Y−π/2`, gate error `2ε²/3`, lines 516–521), which
  touches the Y axis (M20). A pure **virtual-Z over-rotation (M7) is not injected here**
  — for the Z-axis mechanism the load-bearing companion is McKay et al. 1612.00858
  (`mckay_efficient_z_gates_1612.00858.md`). The Eq. (1) form is axis-agnostic, so it
  still grounds M7's operator; only the injection demonstration is X/Y here.
- **No per-axis fidelity decomposition** beyond noting "the error of a Yπ/2 gate is
  larger than the Xπ/2 gate error" attributed to a calibration assumption (lines
  492–497), and an extra error on the un-calibrated `Xπ/2Yπ/2` indicating "a phase
  error" (lines 508–512).

---

## Limitations [paper]

1. **Coherence-limited sensitivity.** "with infinite T1 we could increase the
   sensitivity of this scheme by repeating a larger number of interleaved gates" (line
   354): finite T1/T2 caps the smallest detectable over-rotation (here ≈ π/256).
2. **Small-angle (ε ≪ 1) expansion.** Eqs. (2)–(3) are second-order in ε; large
   over-rotations are outside the quadratic-decay derivation.
3. **Pulse-history / buffer effects.** The X–Y axis error decreases with buffer time and
   "is likely due to distortions that cause successive pulses to overlap" (lines
   535–537) — "not typically considered in RB, in which it is assumed a pulse knows no
   history of previous pulses" (lines 538–539). Coherent-error attribution is
   buffer-dependent.

---

## Trust [twin]

- **Coherent over-rotation operator form `U = exp(−i (ε/2) r̂·σ)` (Eq. 1):**
  certificate-grade for grounding the COH_R* mechanism operator (M6/M7/M20) — it is the
  explicit small-angle unitary-error definition.
- **Quadratic-in-n coherent vs linear non-unitary signature (Eqs. 2–3):**
  certificate-grade (derived + experimentally confirmed).
- **Injected angle scale π/64, π/128, π/256 and the ≈ π/128 detectability floor:**
  measurement-grade on this specific transmon — a realistic anchor for the Twin's swept
  ε, NOT a universal constant to freeze.
- **Any QEC/LER implication:** ABSENT — out of scope for this paper.
