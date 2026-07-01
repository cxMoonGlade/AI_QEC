# Full-text 精读 — Mlynek et al., "Observation of Dicke Superradiance for Two Artificial Atoms in a Cavity with High Decay Rate" (arXiv:1412.2392; Nat. Commun. 5, 5186 (2014))

> **Provenance (2026-06-30): FULL-TEXT 精读.** Plain-text extraction
> `outputs/papers/1412.2392.txt` (6 pages, ~25 k chars; PyMuPDF or equivalent pipeline).
> Figures not pixel-extracted; figure captions and in-text references to figures read verbatim
> from the text. All §/Eq/Fig refs from that text.

---

## Why this note is load-bearing [ours]

**M12 = correlated two-qubit relaxation** in the QEC-Twin models the case where two
superconducting qubits share a common dissipative channel, giving a collective Lindblad
jump operator `L = sqrt(gamma_corr) * (sigma1^- + sigma2^-)`. Before this note the M12
derivation doc cited a magnitude claim "gamma_corr ≈ 0.01–0.1 × gamma_1 (1–10% of the
independent rate)" attributed to "DiVincenzo 1998" — a fabricated citation. This paper
(Mlynek et al. 2014) is the **direct experimental observation** of Dicke superradiance for
exactly two superconducting transmon qubits coupled to a COMMON cavity channel (circuit
QED bad-cavity limit). It provides the **only load-bearing experimental magnitude anchor**
for what ratio gamma_corr/gamma_1 is actually achievable and observed in the
superconducting-qubit setting.

---

## Metadata [paper]

- **Authors:** J. A. Mlynek, A. A. Abdumalikov Jr, C. Eichler, A. Wallraff — ETH Zürich,
  Department of Physics.
- **Preprint:** arXiv:1412.2392v1 [quant-ph], 7 Dec 2014.
- **Published:** Nature Communications **5**, 5186 (2014).
- **Type:** experiment (two transmon qubits in a coplanar waveguide resonator) + master
  equation theory comparison.
- **System:** circuit QED, bad-cavity (fast-decay) limit; two-qubit collective relaxation
  via a shared cavity mode.

---

## Executive summary [paper]

Mlynek et al. demonstrate **close-to-ideal Dicke superradiance** for two superconducting
transmon qubits individually controllable and coupled to a single microwave cavity
resonator with a **large (fast) decay rate κ**. Operating in the bad-cavity limit
(κ ≫ g ≫ Γ_nr, Γ*), the cavity acts as a Markovian common bath: after adiabatic
elimination the cavity mode is a simple decay channel shared by both qubits. The key
results are:

1. **Individual (single-qubit) Purcell decay** measured for each qubit separately:
   Γ_κ(A)/2π ≈ 0.48 MHz, Γ_κ(B)/2π ≈ 0.54 MHz at detuning Δ_r/2π = 25 MHz.
2. **Collective (two-qubit) decay from |ee⟩** shows non-exponential dynamics with an
   initial rate *smaller* than Γ_κ that then *speeds up* to values **larger than** the
   single-qubit rate — the hallmark of superradiance.
3. The bright (symmetric) state |B⟩ = (|ge⟩ + |eg⟩)/√2 decays at **2 × Γ_κ** (twice
   the single-qubit rate); the dark (antisymmetric) state |D⟩ = (|ge⟩ − |eg⟩)/√2 is
   perfectly subradiant (decoupled from the cavity, zero radiative rate).
4. **Density-matrix tomography** of the emitted photon field confirms the quantum-optical
   Dicke picture, with state fidelity F = 0.94 for both bright-state and dark-state
   preparations.

The experiment constitutes **a close to ideal realization of Dicke's original two-spin
Gedankenexperiment** [paper: "close to ideal realization", p. 1].

---

## Setup and collective-decay model [paper]

### Physical setup

Two transmon qubits (A, B) capacitively coupled to an **asymmetric coplanar waveguide
resonator** (one port weakly coupled to input, one overcoupled to output → large κ). Each
qubit has an independent charge gate (green in Fig. 1) and flux bias line (red) for
individual frequency tuning and state preparation. Qubits are positioned at field maxima
of the first harmonic mode.

Idle transition frequencies: ω_A,0/2π ≈ 8.20 GHz, ω_B,0/2π ≈ 7.40 GHz [Methods,
p. 5]. Resonator center frequency: ω_r/2π ≈ 7.064 GHz [p. 2].

### Extracted experimental parameters [paper, p. 2]

```
Γ_nr/2π (A, B)  ≈ (0.040, 0.042) MHz     — non-radiative (intrinsic) decay rate
Γ*/2π   (A, B)  ≈ (0.25,  0.27)  MHz     — pure dephasing rate
g/2π    (A, B)  ≈ (3.5,   3.7)   MHz     — qubit–cavity coupling rate
κ/2π            ≈ 43              MHz     — cavity photon decay rate (large = bad-cavity)
```

Parameter hierarchy confirming bad-cavity limit: **κ ≫ g ≫ Γ_nr, Γ***
(43 MHz ≫ 3.5–3.7 MHz ≫ 0.04–0.042 MHz).

### Single-qubit Purcell decay [paper, p. 2]

At small detuning Δ_r/2π = (ω_A/B − ω_r)/2π = 25 MHz from resonance:

```
Γ_κ = κ g² / |κ/2 + i Δ_r|²          # Purcell rate formula, bad-cavity limit
```

Numerically extracted from master-equation fits:

```
Γ_nr(Δ = 25 MHz)/2π  =  (0.04,  0.042) MHz    [non-radiative, both qubits]
Γ_κ  (Δ = 25 MHz)/2π  =  (0.48,  0.54) MHz    [Purcell / radiative, qubit A/B]
```

Non-radiative is small compared to radiative: Γ_nr ≈ 0.08 × Γ_κ — the decay is
**dominated by the Purcell (cavity-mediated) channel**. Average single-qubit radiative
rate: **Γ̄_κ/2π ≈ 0.51 MHz**.

Corresponding approximate T₁ (radiative Purcell channel only, single qubit):
T₁ ≈ 1/Γ̄_κ ≈ 1/(2π × 0.51 MHz) ≈ **312 ns** (at Δ = 25 MHz operating point).

### Collective decay: Dicke states and transition rates [paper, pp. 3–4]

The paper presents the collective level scheme explicitly (Fig. 4a, 4b). Verbatim from
the text, describing the two-qubit decay channels:

**Coupled-basis (Fig. 4a):**

```
|ee⟩
  ↓  [only channel: via bright state |B⟩]
|B⟩ = (1/√2)(|eg⟩ + |ge⟩)    — bright (symmetric) state
  ↓  rate: 2 × Γ_κ
|gg⟩

|D⟩ = (1/√2)(|eg⟩ − |ge⟩)    — dark (antisymmetric) state
  ↓  rate: 0  (does not couple to cavity field mode)
[trapped]
```

**Uncoupled-basis (Fig. 4b):**

```
|ee⟩     →    |ge⟩ or |eg⟩    rate:  1 × Γ_κ   [each qubit decays independently]
|ge⟩     →    |gg⟩             rate:  1 × Γ_κ
|eg⟩     →    |gg⟩             rate:  1 × Γ_κ

Collective |B⟩ → |gg⟩          rate:  2 × Γ_κ   [the superradiant enhancement]
```

Direct quote: "the transition rate from |B⟩ to |gg⟩ is **two times larger than the
single decay rate** out of the states |ge⟩ or |eg⟩ respectively" [p. 3].

The analytical approximation for the emitted power deviation starting from |ee⟩ [p. 3]:
```
ΔP(t) = 2P₀ e^{−2 Γ̄_κ t} (1 + 2 Γ̄_κ t) − 2 P̄(t)
```
This is the **non-exponential two-qubit superradiant decay** (Gross & Haroche 1982, Ref.
[7]), with characteristic timescale 1/(2 Γ̄_κ) — half the single-qubit T₁.

From superposition initial state (|g⟩+|e⟩)(|g⟩+|e⟩)/2 [p. 4]:
```
ΔP(t) = P₀ e^{−2 Γ̄_κ t} (3/2 + Γ̄_κ t) − P̄(t)
```

From |ge⟩ initial state (single-atom superradiance) [p. 4]:
```
ΔP(t) = P₀ e^{−2 Γ̄_κ t} − P̄(t)
```
Half the excitation is trapped in |D⟩, half decays from |B⟩ at rate 2Γ̄_κ. Measured
trapped energy: **0.707 photons** (expected from master equation: 0.709 photons) —
close to the ideal 50% trapping limit; deviation attributed to finite Γ* [p. 4].

---

## The collective-vs-single rate magnitude — exhaustive number extraction [paper]

This is the load-bearing section. All numbers from the paper text.

### Fundamental Dicke relation: Γ_bright vs Γ_single

In the ideal two-emitter Dicke limit with cavity-mediated common bath, the radiative
decay rates of the collective states are:

```
Γ_bright (bright/superradiant state |B⟩) = 2 × Γ_κ      [= 2 × single-qubit rate]
Γ_dark   (dark/subradiant state |D⟩)     = 0              [perfectly subradiant]
```

This corresponds to a cross (correlated) decay rate:
```
Γ_12 = Γ_κ    [equals the single-qubit rate]
```

so that Γ_bright = Γ_κ + Γ_12 = 2Γ_κ and Γ_dark = Γ_κ − Γ_12 = 0.

**In the language of the twin's Lindblad model** with collective jump operator
`L = sqrt(gamma_corr) * (sigma1^- + sigma2^-)`:
The jump operator (σ₁⁻ + σ₂⁻) has norm² = 2 on |B⟩ and 0 on |D⟩. So
`gamma_corr = Γ_κ` (the single-qubit Purcell rate) in the **ideal engineered case** where
the common channel dominates. The independent decay part is also `Γ_κ` per qubit.

Equivalently, in a Lindblad decomposition with separate and correlated jump operators:
```
L_1 = sqrt(Γ_κ) sigma1^-   [independent]
L_2 = sqrt(Γ_κ) sigma2^-   [independent]
L_12 = sqrt(Γ_12) (sigma1^- + sigma2^-)  with Γ_12 = Γ_κ
```
the bright state decays at Γ_κ + Γ_12 = 2Γ_κ and dark at Γ_κ − Γ_12 = 0, fully
consistent with the observation.

**Enhancement factor for this experiment:**
```
Γ_bright / Γ_single  =  2 × Γ_κ / Γ_κ  =  2.0   [ideal theoretical limit]
Measured:  "approximately twice as large" [p. 2–3], quantitatively matched by
           master equation + analytic approximation ("in quantitative agreement") [p. 3]
```

The experiment achieves **≈ 2× enhancement** (quantitatively matched to theory), meaning
this is essentially a **fully cooperative** common-bath system.

### Absolute rates at the operating point (Δ = 25 MHz)

```
Quantity                          Qubit A       Qubit B       Units
─────────────────────────────────────────────────────────────────────
Γ_nr/2π  (non-radiative)          0.040         0.042         MHz
Γ_κ/2π   (Purcell / radiative)   0.48          0.54          MHz
T₁ (Purcell only, approx.)        332           295           ns
Γ̄_κ/2π  (mean)                   0.51                        MHz
─────────────────────────────────────────────────────────────────────
Γ_bright/2π  = 2Γ̄_κ/2π          ≈ 1.02                      MHz
Γ_dark/2π    = 0                  0                           MHz
Γ_12/2π      = Γ̄_κ/2π           ≈ 0.51                      MHz
─────────────────────────────────────────────────────────────────────
```

### Ratio Γ_12 / Γ_single (the cooperative / cross-rate fraction)

```
Γ_12 / Γ̄_κ  =  1.0   (i.e. 100% — fully cooperative in this engineered setup)
```

The paper does not quote a finite "coupling efficiency" η < 1 for the cross rate; the
model used and the theory fits are all at Γ_12 = Γ̄_κ (fully cooperative limit). The
small deviation from perfectly trapped dark state (0.707 vs ideal 0.500 photons emitted
from |ge⟩) is attributed to **dephasing Γ*** lifting the dark state, not to a reduced
Γ_12.

### Supporting cavity-level parameters

```
κ/2π    = 43   MHz   — cavity decay rate (sets the bad-cavity / Markovian limit)
g/2π    = 3.5–3.7 MHz — qubit–cavity coupling
g²/κ/2π = Γ_κ(res)/2π ≈ g²/κ  [at resonance]
          ≈ (3.6)²/43 ≈ 0.30  MHz  [rough estimate at resonance; actual Γ_κ at Δ=25 MHz quoted above]
```

The bad-cavity limit (κ ≫ g) is critical: it ensures the cavity can be adiabatically
eliminated, making it a **pure Markovian common bath** with cross rate Γ_12 = Γ_κ (fully
cooperative). If κ were small (strong coupling), the cross rate would depend on the
inter-qubit phase relationship and could be much smaller.

---

## Conditions for strong cooperativity [paper]

The paper identifies the following conditions for the **full (ideal) superradiant enhancement**:

1. **Frequency matching of the two qubits.** Both qubits must be tuned to the same
   transition frequency — here achieved by flux tuning both into resonance with the cavity
   at ω_r simultaneously ("tuned synchronously into resonance with the resonator", p. 3).
   When one qubit is off-resonant (ω_B,0 ≈ 7.41 GHz vs cavity at 7.064 GHz), the
   collective behavior vanishes.

2. **Shared cavity coupling (common mode) with κ ≫ g.** The bad-cavity (fast-decay)
   limit is essential: "κ ≫ g ≫ Γ_nr, Γ*" [p. 2]. When κ is large the cavity can be
   adiabatically eliminated and acts as a simple Markovian decay channel seen by *both*
   qubits simultaneously. This is what generates the collective Lindbladian.

3. **Equal (or near-equal) coupling rates g.** Both qubits coupled at g/2π ≈ 3.5, 3.7
   MHz (within ~6%). The theoretical picture assumes equal g; the small difference
   accounts for the small spread in individual decay rates.

4. **Low non-radiative decay Γ_nr relative to Γ_κ.** Here Γ_nr ≈ 0.08 × Γ_κ, so
   the cavity-mediated channel dominates. If Γ_nr were comparable to Γ_κ, the dark state
   would be lifted and the cross rate would be fractional.

5. **Low dephasing Γ* (for dark-state integrity).** Finite Γ* lifts the dark state,
   which is observed as the 0.707 vs ideal 0.50 trapped-photon measurement. Γ*/2π ≈
   0.25–0.27 MHz is larger than Γ_nr but still smaller than Γ_κ.

---

## Relevance to qec_twin M12 [ours]

### What regime does this experiment represent?

This experiment is an **engineered common-bath experiment**: both qubits are deliberately
frequency-matched and both coupled with equal rate g to the SAME cavity mode which has
large κ. The cavity is the designed common dissipation channel. This is NOT incidental
or parasitic — it is maximally cooperative by construction.

The result is **Γ_12 = Γ_κ = Γ_single_radiative**, i.e., the cross-rate equals the
single-qubit rate → enhancement factor 2×.

### Does this support or contradict "gamma_corr ≈ 0.01–0.1 × gamma_1"?

**Contradicts** the specific claim, but the comparison requires care:

| Scenario | Γ_12 / Γ_single | Source |
|---|---|---|
| Ideal engineered common bath (Mlynek, this paper) | **1.0 (100%)** | experiment |
| Current M12 claim in twin doc | 0.01–0.1 (1–10%) | fabricated citation |

The M12 claim of 1–10% is **not supported by this paper**. In the engineered common-bath
regime Dicke superradiance achieves the maximum: Γ_12 = Γ_single. **The 1–10% figure
could plausibly describe an incidental / parasitic correlated decay** (e.g., from
accidental partial shared environment, substrate phonons, stray field modes), where the
two qubits are NOT intentionally sharing a common channel at equal coupling — but no
paper supporting that specific number has been cited and the "DiVincenzo 1998" reference
is fabricated.

### Mechanism difference: engineered vs incidental common bath

**[twin]** The twin's M12 models an *incidental* correlated decay from a shared substrate
or parasitic mode, not an engineered common resonator. The distinction matters:

- **Engineered common bath (this paper):** g_A ≈ g_B, κ ≫ g, qubits frequency-matched
  → Γ_12 ≈ Γ_κ → cross rate is 100% of the radiative rate. This is the *maximum*
  physically achievable.
- **Incidental / parasitic shared bath:** partial overlap with a common mode, possibly
  different effective couplings, possibly off-resonant → Γ_12 < Γ_κ, potentially much
  less. A natural parametrization is Γ_12 = η × Γ_single where 0 ≤ η ≤ 1 (η = 1 =
  this paper). For incidental sources η could be small (few %).

**[ours]** The honest statement for M12 is therefore:

- **Upper bound from physics:** Γ_12 ≤ Γ_single (equality achieved in the fully
  cooperative engineered case of this paper — 2× enhancement).
- **Plausible incidental range:** η = Γ_12/Γ_single is an open parameter; 1–10% is a
  plausible *order-of-magnitude* choice for incidental coupling but is NOT derived from a
  cited source. It should be declared as a [heuristic gate] not a [prediction band] or
  [exact] result.
- **"DiVincenzo 1998" must be removed.** No such citation supports this.

### Appropriate update to M12 doc [ours]

The M12 derivation should:
1. Remove the fabricated "DiVincenzo 1998" attribution.
2. Cite Mlynek et al. (this paper) for the **Γ_bright = 2Γ_single / Γ_12 = Γ_single**
   relation in the fully cooperative (engineered) common-bath limit.
3. Declare the "0.01–0.1 × gamma_1" range explicitly as a **[heuristic gate]** for the
   *incidental/parasitic* case, with the physical upper bound η ≤ 1 from this paper.
4. Flag that the Mlynek experiment is the engineered maximum — the parasitic M12 regime
   (if intended to model accidental correlated decay) sits at η ≪ 1, but no experimental
   paper directly measuring that incidental fraction in a superconducting multi-qubit
   processor has been read.

---

## Limitations [paper]

- **Engineered system, not a real QEC processor.** This is a dedicated two-qubit
  experiment with intentional common-bath coupling. In a real QEC chip the correlated
  relaxation from incidental shared modes would be weaker (η < 1, magnitude unknown).
- **Two qubits only.** Scaling to larger N is not addressed in this experiment.
- **Measurement at a specific detuning** (Δ = 25 MHz) to slow decay within acquisition
  bandwidth; the rates quoted (Γ_κ/2π ≈ 0.48–0.54 MHz) are not at zero detuning. At
  resonance Γ_κ(res) = 4g²/κ/2π ≈ 0.30 MHz (rough), smaller than the detuned value.
- **Figures not pixel-extracted:** the time-domain decay curves (Fig. 3) contain
  quantitative information (e.g., where the two-qubit power curve crosses the single-
  qubit curve) that is reported qualitatively here; the exact crossover time and peak
  power enhancement number are read from the text descriptions, not from the figure data.
- **No direct cross-rate Γ_12 number quoted.** The paper quotes Γ_κ (single-qubit) and
  describes Γ_bright = 2Γ_κ; the cross rate Γ_12 = Γ_κ is inferred from the Dicke
  relation, not quoted as an independent measurement. The experiment is consistent with
  the fully cooperative limit Γ_12 = Γ_κ but does not independently measure Γ_12.

---

## Trust [ours]

- **Full-text 精读.** All rate equations and Dicke state definitions transcribed verbatim
  from the paper text.
- **Γ_κ, Γ_nr, Γ*, g, κ numbers:** [paper] directly quoted from p. 2 — certificate-grade.
- **Γ_bright = 2Γ_κ relation:** [paper] stated explicitly in text and Fig. 4 caption —
  certificate-grade (from paper).
- **Γ_dark = 0:** [paper] "The dark state does not couple to the cavity field mode"
  (Fig. 4 caption) — certificate-grade.
- **Enhancement factor ≈ 2×:** [paper] "approximately twice as large" (p. 2–3),
  "quantitative agreement with master equation simulation" (p. 3) — numerics-grade
  (matched to within detection efficiency s ≈ 0.9, scaled accordingly).
- **Cross rate Γ_12 = Γ_κ (η = 1):** inferred from Dicke relation + perfect match to
  fully cooperative theory — numerics-grade inference, not a directly quoted number.
- **0.01–0.1 × gamma_1 claim:** [ours / fabricated prior] NOT supported by this paper,
  declared [heuristic gate], requires independent grounding.
