# Full-text 精读 — Wenner, Yin, Lucero et al. (Cleland & Martinis), "Excitation of superconducting qubits from hot non-equilibrium quasiparticles" (arXiv:1209.1674)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/1209.1674.txt` (PyMuPDF text extraction, 6 pages). The extraction
> contains embedded NUL bytes; quotes below taken after `tr -d '\000'`. Figures are
> not pixel-extracted; figure references read from the extracted text / captions.
> Header: "arXiv:1209.1674v2 [cond-mat.supr-con] 13 Apr 2013" (Phys. Rev. Lett. 110,
> 150502 (2013); no journal line in this extract).

Epistemic tags throughout: **[paper]** = stated/derived/measured in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note is the **mechanism reference** for QEC-Twin **M24 = residual / thermal
excited-state population**. Where Jin (1412.2772) *measures* the residual `P|e⟩` floor and
attributes it (conditionally) to hot quasiparticles, this paper supplies the **physical
mechanism and the excitation-rate equation**: "hot" non-equilibrium quasiparticles with
energy above the superconducting gap can tunnel through the Josephson junction and drive
the `|g⟩ → |e⟩` transition, producing an excited-state population **in excess of any
thermal value**. This is the microscopic origin M24 is modeling — and the demonstration
that M24's population is **not** describable by a single effective temperature.

---

## Metadata [paper]

- **Authors:** J. Wenner, Yi Yin, E. Lucero, R. Barends, Yu Chen, B. Chiaro, J. Kelly,
  M. Lenander, M. Mariantoni, A. Megrant, C. Neill, P. J. J. O'Malley, D. Sank,
  A. Vainsencher, H. Wang, T. C. White, A. N. Cleland, J. M. Martinis (UCSB; CNSI;
  Zhejiang Univ.).
- **arXiv:** 1209.1674v2, cond-mat.supr-con, 13 Apr 2013 (PRL 110, 150502).
- **Type:** theory (rate model) + experiment (inject hot quasiparticles, measure ΔPe).
- **Device:** superconducting phase qubit; quasiparticles injected by a voltage pulse
  "above the gap voltage."

---

## M24 mechanism — abstract claim [paper]

**Abstract (verbatim, the load-bearing claim):** "Superconducting qubits probe
environmental defects such as non-equilibrium quasiparticles, an important source of
decoherence. We show that **"hot" non-equilibrium quasiparticles, with energies above the
superconducting gap, affect qubits differently from quasiparticles at the gap**, implying
qubits can probe the dynamic quasiparticle energy distribution. **For hot quasiparticles,
we predict a non-neligable [sic] increase in the qubit excited state probability Pe.** By
injecting hot quasiparticles into a qubit, we **experimentally measure an increase of Pe
in semi-quantitative agreement with the model and rule out the typically assumed thermal
distribution.**"

**[twin]** The last clause is the key M24 caveat: the excited-state population is
**non-thermal** — "rule out the typically assumed thermal distribution" — so M24 cannot
in general be captured by a Boltzmann `P|e⟩(T)` at a single Teff (consistent with Jin's
sub-35 mK deviation from thermal).

---

## The excitation mechanism and rate [paper]

**Energy-threshold picture (verbatim) [paper]:** "Any quasiparticle in the junction area
can absorb this energy, so the qubit |e⟩ → |g⟩ decay rate Γ↓ due to this channel is
proportional to the quasiparticle density nqp. For a qubit initially in its ground state,
a **"hot" quasiparticle sufficiently above the gap energy can excite the qubit, but only
if the quasiparticle has energy greater than Δ + Ege** (red arrows in Fig. 1(a,c)). The
qubit |g⟩ → |e⟩ excitation rate Γ↑ thus depends on the energy distribution of the
quasiparticle population."

**[paper]** "If the quasiparticle population were well-described by a temperature T ≃ 20
mK ≪ Ege/kB, then a negligible qubit excitation rate Γ↑ would be expected." It is the
**non-equilibrium hot tail** — "energies well above kBT" — that produces a measurable
Γ↑. **[twin]** This is exactly why M24's residual `P|e⟩` does not vanish at base
temperature: a cold thermal model predicts ~0 excitation, but the hot-QP tail keeps
P|e⟩ finite.

**Fig. 1 caption (verbatim, the two regimes) [paper]:** "(b) **Cold** non-equilibrium
quasiparticles, which have energies near the superconducting gap Δ, **can only absorb
Ege, resulting in qubit Γ↓ decay.** … (c) **Hot** non-equilibrium quasiparticles with
energy above Δ + Ege … **not only can cause qubit Γ↓ transitions but can also relax by
causing qubit |g⟩ → |e⟩ transitions.**"

**Rate equation (Eq. 1) — the load-bearing rate [paper]:** for a tunnel junction with
resistance R_T, capacitance C, and normalized quasiparticle density of states
`ρ(E) = E/√(E²−Δ²)`,

```
Γ↓(↑) = (1 + cos φ)/(R_T C) ∫_{Δ(+Ege)}^{∞} dE (Ege/(E·Ef) + Δ²/(E·Ef)) ρ(E) ρ(Ef) f(E)   (1)
```

**[paper]** The lower integration limit differs for decay vs excitation: `Δ` for Γ↓ vs
`Δ + Ege` for Γ↑ — encoding the threshold that **only quasiparticles above `Δ + Ege` can
excite the qubit**. `f(E)` is "the non-equilibrium quasiparticle occupation probability."
**[twin]** Eq. 1 is the microscopic generator of the up-rate `Γ1↑` that, balanced against
`Γ1↓`, sets M24's steady-state `P|e⟩` (cf. Krantz Eq. 45 detailed balance — but here the
distribution is non-thermal, so detailed balance with a single T does **not** apply).

**Steady-state distribution [paper]:** quasiparticles "injected in the junction at a
constant rate at an energy Einj well above Δ + Ege, with the resulting quasiparticle
density nqp scaling as the square root of the injection rate"; "the qubit excited state
probability Pe is independent of the injection energy." The steady-state `f(E)` "has a
similar dependence on quasiparticle energy as a 70 mK thermal distribution for
Δ < E < 1.4Δ", but "**no effective temperature can fully describe f(E) for all energies,
implying a non-thermal distribution.**"

---

## Experimental confirmation [paper]

**[paper]** "By injecting a non-equilibrium [quasiparticle population]…" the measured
increases in Pe "directly demonstrate a non-equilibrium" distribution, "demonstrating the
presence of hot quasiparticles and directly showing that **hot quasiparticles can
significantly excite**" the qubit. Agreement with the model is "semi-quantitative"
(abstract).

---

## Limitations / bounds for M24 [paper] / [twin]

1. **[paper]** Agreement is explicitly "**semi-quantitative**" — the rate model (Eq. 1)
   reproduces the *trend and order* of the Pe increase, not an exact value.
2. **[paper]** Self-flagged assumption: "the calculation of Pe assumes non-equilibrium
   [distribution]… altering the prediction for the excitation rate" — the predicted Γ↑
   depends on the assumed `f(E)`, which is itself modeled (injection + phonon-scattering
   balance), not directly measured.
3. **[paper]** Device is a **phase qubit** with deliberately *injected* quasiparticles —
   a controlled excess, not the ambient residual of a quiescent transmon. **[twin]** It
   establishes the mechanism and the non-thermal character; the *ambient* M24 magnitude on
   a transmon comes from Jin (≈0.1%, Teff = 35 mK).
4. **[twin]** Because `f(E)` is non-thermal, an M24 that uses a single Boltzmann factor at
   one Teff is a simplification — faithful M24 either imposes a measured residual floor
   (Jin) or carries a non-equilibrium up-rate.

---

## Trust [twin]

- **Hot-QP-above-gap excitation mechanism; threshold `E > Δ + Ege`; non-thermal `f(E)`
  (abstract; Fig. 1; Eq. 1):** certificate-grade as the *mechanism* and qualitative law
  for M24's finite residual `P|e⟩` and its non-thermal character.
- **Rate equation Eq. 1 (Γ↑ from the hot tail):** the microscopic up-rate generator —
  numerics-grade ("semi-quantitative" agreement), model-dependent `f(E)`.
- **Quantitative ambient `P|e⟩` magnitude:** NOT set here (injected, not ambient) — that
  anchor is Jin 1412.2772 (≈0.1%, Teff = 35 mK).
