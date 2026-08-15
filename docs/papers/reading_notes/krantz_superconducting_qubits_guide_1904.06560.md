# Full-text 精读 — Krantz, Kjaergaard, Yan, Orlando, Gustavsson & Oliver, "A Quantum Engineer's Guide to Superconducting Qubits" (arXiv:1904.06560)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/1904.06560.txt` (PyMuPDF text extraction, 67 pages). The
> extraction contains embedded NUL bytes; all quotes below were taken after
> `tr -d '\000'`. Figures are not pixel-extracted; all equation/figure references
> are read from the extracted text. Header: "(Dated: 9 July 2021)"; published as a
> review (Applied Physics Reviews); no journal citation line appears in this
> extract.

Epistemic tags throughout: **[paper]** = stated/derived in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note is the primary literature anchor for two QEC-Twin mechanisms:

- **M4 = T1 longitudinal relaxation.** The paper gives the exponential decay law
  `exp(-Γ1 t)` with `Γ1 = 1/T1` (Eq. 41), and the Fermi-golden-rule relation
  `Γ1 ∝ Sλ(ωq)` (Eq. 54) — relaxation rate proportional to the bath noise PSD at the
  qubit frequency — which grounds the M4 amplitude-damping rate.
- **M5 = T2 transverse relaxation / pure dephasing.** The paper gives
  `Γ2 = Γ1/2 + Γφ` (Eq. 42, Fig. 4(d) caption) and the Bloch-Redfield density matrix
  with `exp(-Γ2 t)` on the off-diagonals (Eq. 44), and identifies pure dephasing `Γφ`
  as caused by **longitudinal (z-axis) noise that fluctuates the qubit frequency** —
  the M5 dephasing channel.

This is the textbook-grade derivation chain `(noise PSD) → (golden-rule rate) →
(Bloch-Redfield decay)` that M4/M5 implement.

---

## Metadata [paper]

- **Authors:** P. Krantz, M. Kjaergaard, F. Yan, T. P. Orlando, S. Gustavsson, W. D.
  Oliver (MIT RLE; Chalmers/WACQT; MIT Lincoln Laboratory).
- **arXiv:** 1904.06560; extract dated "9 July 2021".
- **Type:** review / tutorial ("introductory guide"), not original measurement; the
  T1/T2 traces shown (Fig. 5) are illustrative transmon data (Ref. 117).
- **Scope used here:** Sec. on noise (Bloch-Redfield picture, T1/T2 rates, noise PSD).

---

## M4 — longitudinal relaxation (T1) [paper]

**Rate definition (Eq. 41):**

```
longitudinal relaxation rate:  Γ1 ≡ 1/T1
```

**[paper]** "T1 is the 1/e decay time in the exponential decay function in Eq. (44),
and it is the characteristic time scale over which qubit population will relax to its
steady-state value."

**Up/down split (Eq. 45):**

```
Γ1 ≡ 1/T1 = Γ1↓ + Γ1↑
```

**[paper]** Detailed balance: "Γ1↑ = exp(−ℏωq/kBT) Γ1↓", with equilibrium polarization
"p = tanh(ℏωq/2kBT)". For "ωq/2π ≈ 5 GHz" at "T ≈ 20 mK" the up-rate is exponentially
suppressed, so "only the down-rate Γ1↓ contributes significantly, relaxing the
population to the ground state." **[twin]** This is exactly the M24 caveat: at finite
T the up-rate is not strictly zero — see Jin/Wenner notes.

**Golden-rule connection to the noise PSD (Eq. 54) — the load-bearing M4 relation:**

```
Γ1 = (1/ℏ²) |⟨0| ∂Ĥq/∂λ |1⟩|² Sλ(ωq)                                    (54)
```

**[paper]** "Its inverse, Γ1 = 1/T1 is called the relaxation rate and depends on the
power spectral density of the noise S(ω) at the transition frequency of the qubit
ω = ωq". "Eq. (54) is equivalent to Fermi's Golden Rule, in which the qubit's
transverse susceptibility to noise is driven by the noise power spectral density."
**[paper]** Only *transverse* noise (coupling operator of type σx or (a+a†)) "can cause
transitions between the qubit eigenstates" — i.e. T1 is a resonant process, sensitive
to noise at ±ωq. Noise at +ωq → emission (Γ1↓); at −ωq → absorption (Γ1↑).

---

## M5 — transverse relaxation (T2) and pure dephasing [paper]

**Rate definition (Eq. 42) — the load-bearing M5 relation:**

```
transverse relaxation rate:  Γ2 ≡ 1/T2 = Γ1/2 + Γφ                      (42)
```

**[paper]** "which contains the pure dephasing rate Γϕ." The paper flags the
assumption: "the definition of Γ2 as a sum of rates presumes that the individual decay
functions are exponential, which occurs for Lorentzian noise spectra (centered at
ω = 0) such as white noise (short correlation times) with a high-frequency cutoff."
**[twin]** For 1/f noise this additive form fails (see Eq. 46 below) — a bound M5 must
respect.

**Bloch-Redfield density matrix (Eq. 44):**

```
ρ_BR = [ 1 + (|α|²−1) e^{−Γ1 t}     αβ* e^{iδωt} e^{−Γ2 t} ]
       [ α*β e^{−iδωt} e^{−Γ2 t}     |β|² e^{−Γ1 t}        ]            (44)
```

**[paper]** "First, we have introduced the longitudinal decay function exp(−Γ1t)…
Second, we introduced the transverse decay function exp(−Γ2t), which accounts for
transverse decay of the qubit." This is the channel M4 (population term `e^{−Γ1 t}`) +
M5 (coherence term `e^{−Γ2 t}`) act on.

**Pure dephasing is longitudinal-noise driven [paper]:** "the pure dephasing rate Γφ
describes depolarization in the x−y plane… pure dephasing is caused by longitudinal
noise that couples to the qubit via the z-axis. Such longitudinal noise causes the
qubit frequency ωq to fluctuate." "in contrast to energy relaxation, pure dephasing is
not a resonant phenomenon; noise at any frequency can modify the qubit frequency…
qubit dephasing is subject to broadband noise." **[paper]** And it is in principle
reversible ("the dephasing can be 'undone'… through… dynamical decoupling pulses") —
unlike T1 relaxation, which is "irreversible."

**Fig. 4 caption (verbatim, the M4/M5 Bloch-sphere picture):** "Transverse and
longitudinal noise represented on the Bloch sphere. … (b) Longitudinal relaxation
results from energy exchange between the qubit and its environment… the up-rate is
suppressed, leading to the overall decay rate Γ1 ≈ Γ1↓. (c) Pure dephasing in the
transverse plane arises from longitudinal noise along the z axis that fluctuates the
qubit frequency. A Bloch vector along the x-axis will diffuse clockwise or […] Γφ.
(d) Transverse relaxation results in a loss of coherence at a rate Γ2 = Γ1/2 + Γφ, due
to a combination of energy relaxation and pure dephasing."

**1/f modification (Eq. 46) [paper] — the bound on Eq. 42:** for Gaussian 1/f noise the
phase decay is Gaussian `exp(−(t/Tϕ,G)²)`, separable from the T1 exponential, so the
density matrix off-diagonal becomes `e^{−(Γ1/2) t} e^{−χN(t)}` with
`χN = (t/Tϕ,G)²`. **[paper]** "for such cases, the simple expression in Eq. (42) is not
applicable."

**Fig. 5 caption (illustrative T1/T2 values) [paper]:** T1 measurement (Xπ then wait τ)
gives "characteristic time T1 = 85 µs"; Ramsey gives "T2* = 95 µs" (text later also
quotes "T2* = 98 µs"); Hahn echo gives "T2E = 120 µs"; the echo not reaching the
"2T1 limit" indicates residual low-frequency dephasing. **[paper]** "of pure dephasing,
the maximum T2 = 2T1 is reached" (the no-dephasing limit). **[twin]** These are review
illustration numbers, not a single device's headline — do not cite as a record.

---

## Limitations / bounds for M4–M5 [paper] / [twin]

1. **[paper]** Eq. 42 (`Γ2 = Γ1/2 + Γφ`) is valid only for exponential decay
   (Lorentzian/white noise); 1/f noise → Gaussian decay (Eq. 46), additive-rate form
   breaks. **[twin]** A Markovian Lindblad M5 reproduces Eq. 42, not Eq. 46.
2. **[paper]** Eq. 44 assumes low temperature ("thermal excitations… rarely occur"), so
   population fully relaxes to ground; finite-T up-rate is dropped here (carried by
   M24).
3. **[paper]** Eq. 54 is lowest-order Fermi golden rule (weak coupling, Born-Markov);
   "non-Gaussian noise"/higher-order spectra are flagged as open.
4. **[twin]** This is a review; the closed-form Kraus operators for the
   amplitude-/phase-damping *channels* (the actual operator set M4/M5 apply) are not
   written here — those are sourced from Arsenijevic (1606.01145).

---

## Trust [twin]

- **`Γ1 = 1/T1`, `exp(−Γ1 t)`, `Γ1 ∝ Sλ(ωq)` (Eqs. 41, 44, 54):** certificate-grade
  textbook relations for the M4 rate.
- **`Γ2 = Γ1/2 + Γφ`, pure-dephasing = longitudinal-Z noise (Eqs. 42, 44; Fig. 4d):**
  certificate-grade for the M5 channel in the Bloch-Redfield (exponential) regime;
  bounded by Eq. 46 outside it.
- **Numerical T1/T2 (85/95/120 µs):** illustrative only (review figure, Ref. 117) — not
  a device record.
