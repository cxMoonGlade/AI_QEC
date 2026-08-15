# Full-text 精读 — Place, Rodgers, Mundada et al. (de Leon & Houck), "New material platform for superconducting transmon qubits with coherence times exceeding 0.3 milliseconds" (arXiv:2003.00024)

> **Provenance (2026-06-30): FULL-TEXT 精读.** Source:
> `outputs/papers/2003.00024.txt` (PyMuPDF text extraction, 37 pages). The
> extraction contains embedded NUL bytes; quotes below taken after `tr -d '\000'`.
> Figures are not pixel-extracted; figure references read from the extracted text /
> captions. Header: "arXiv:2003.00024v1 [quant-ph] 28 Feb 2020" (later published in
> Science Advances; no journal line in this v1 extract).

Epistemic tags throughout: **[paper]** = stated/measured in the paper;
**[twin]** = our application or inference.

---

## Why load-bearing [twin]

This note anchors the **realistic device-parameter ranges** for two QEC-Twin
mechanisms on 2D transmons (state-of-the-art circa 2020):

- **M4 = T1 longitudinal relaxation.** The paper reports a peak **`T1 = 0.36 ± 0.01
  ms`** (360 µs) tantalum transmon, against the then-record **"longest published T1 is
  114 µs"** for prior 2D transmons. These bracket the M4 relaxation-time scale.
- **M5 = T2 transverse relaxation.** The paper reports **`T2,Echo = 0.20 ± 0.03 ms`**
  (200 µs) and **`T2,CPMG = 0.38 ± 0.11 ms`** (380 µs) in the best device, with the
  explicit Ramsey/echo/CPMG fit forms used.

M4/M5 simulations need their `T1`/`T2` inputs to sit in a measured, citable range
rather than a guessed one; this paper supplies that range and the prior baseline.

---

## Metadata [paper]

- **Authors:** A. P. M. Place, L. V. H. Rodgers, P. Mundada, B. M. Smitham, M.
  Fitzpatrick, Z. Leng, A. Premkumar, J. Bryon, S. Sussman, G. Cheng, T. Madhavan,
  H. K. Babla, B. Jäck, A. Gyenis, N. Yao, R. J. Cava, N. P. de Leon, A. A. Houck
  (Princeton). Place & Rodgers contributed equally.
- **arXiv:** 2003.00024v1, quant-ph, 28 Feb 2020.
- **Type:** experimental materials result — replace niobium with **tantalum** in the
  2D-transmon capacitor + resonators.
- **Device:** α-phase Ta on sapphire (sputtered ~500 °C), Al/AlOx Josephson junctions;
  dispersive readout; measured at "between 9 and 20 mK."

---

## M4 — T1 result and prior baseline [paper]

**Prior state of the art (verbatim):** "the lifetime (T1) of the two-dimensional (2D)
transmon qubit has not reliably improved beyond 100 µs since 2012 (17,18), and **to date
the longest published T1 is 114 µs (19)**, consistent with other recent literature
reports (20–22)." **[twin]** This 114 µs is the pre-tantalum 2D-transmon T1 ceiling — the
lower anchor for M4.

**This work (verbatim):** "To determine T1, we excite the qubit with a π-pulse and
measure its decay over time at a temperature between 9 and 20 mK. In our best device, we
measure a **peak T1 of 0.36 ± 0.01 ms** (Fig. 1C)." Across devices: "time-averaged T1
ranging from 0.15 ms to 0.30 ms, and an **average T1 of 0.23 ms across all devices**."
Fluctuation: "The lifetime of a given qubit fluctuates over time, with a standard
deviation of around 7% of the mean (Fig. 2A)." **[twin]** The ~7% drift is a directly
citable scale for M4 T1 temporal variation.

**T1 fit form [paper]:** "We fit our transmon T1 data to `f(Δt) = e^{−Δt/T1}`, where T1
is a fit parameter and the function represents the population in the excited state." —
i.e. single-exponential population decay, matching the M4 amplitude-damping `e^{−Γ1 t}`.

**Bulk-limited headroom [paper]:** "high-purity bulk sapphire has a loss tangent less
than 10⁻⁹ (26,27), which would enable T1 to exceed 30 ms" — current 2D transmons are
"believed to be limited by microwave dielectric losses" at "uncontrolled defects at
surfaces and interfaces." **[twin]** Context only: the realized T1 is ~10⁻⁴–10⁻⁵ of the
material limit; the loss is interfacial, not intrinsic.

---

## M5 — T2 result and fit forms [paper]

**This work (verbatim):** "The time-averaged coherence time, **T2,Echo, in our best
device is 0.20 ± 0.03 ms** (a trace is shown in Fig. 2C). We can extend the coherence
time using a Carr-Purcell-Meiboom-Gill (CPMG) pulse sequence (38) (Fig. 2D)… and we
achieve a **time-averaged T2,CPMG of 0.38 ± 0.11 ms** in our best device (Fig. 2A)."

**A specific-device echo value (Fig. 2C caption) [paper]:** "A T2,Echo measurement of
Device 18a, fit with a stretched exponential. The fit gives **T2,Echo = 249 ± 4 µs**."
**[twin]** Note: the 0.20 ms quoted in the body is the *time-averaged* best-device echo;
the 249 µs is a single representative trace (Device 18a). Carry the distinction.

**T2 fit forms [paper]:**
- Ramsey (with fringes): "`f(Δt) = 0.5 e^{−Δt/T2R} cos(2π Δt δ + φ0) + 0.5` where T2R,
  δ, and φ0 are fit parameters."
- Echo / CPMG: "we fit our T2 data with a stretched exponential, `f(Δt) = 0.5
  e^{−(Δt/T2)^n} + 0.5`, where T2 and n are fit parameters. If n < 1, the data is refit
  to a pure exponential." **[twin]** The stretched exponent `n` signals non-Markovian
  (e.g. 1/f) dephasing — consistent with Krantz Eq. 46; an M5 with a single Lindblad Γ2
  gives n = 1.

**Noise spectrum [paper]:** "The spectral noise density extracted from dynamical
decoupling measurements is consistent with 1/f noise (Fig. S12)" / supplement: "a noise
power spectral density that is well fit by `A/f^α + B` with **α = 0.7**." **[twin]** This
is the M5 dephasing-noise color anchor (≈1/f) for tantalum transmons.

**T2,Echo < T1 caveat [paper]:** "T2,Echo is shorter" than the T1 — i.e. echo coherence
is still dephasing-limited, not at the `T2 = 2T1` relaxation floor.

---

## Robustness [paper]

**[paper]** "We observe reproducible, robust enhancement of T1 across all devices…
Results for eight devices are presented in Fig. 2B… We have observed increased lifetimes
for seventeen devices, indicating that these material improvements are robust." Plus "a
total of 23 transmon qubits" with varied geometries in the supplement (Table S1).

---

## Limitations / bounds for M4–M5 [paper] / [twin]

1. **[paper]** Single-material study (Ta vs Nb); the loss model ("complicated
   stoichiometry of oxides at the niobium surface… insulating oxide of tantalum reduces
   microwave loss") is a stated **hypothesis**, not proven microscopically here.
2. **[paper]** All numbers are single-qubit. "it has been well-established that
   multi-qubit devices suffer from sig[nificant]…" degradation — these T1/T2 are
   isolated-qubit best cases, an **upper** anchor for M4/M5 in a multi-qubit QEC patch.
3. **[twin]** Stretched-exponential `n < 1` and 1/f PSD mean M5's single-Γ2 Lindblad is
   an approximation here; the realized dephasing is partly non-Markovian.
4. **[twin]** Best-device vs averaged numbers differ (peak T1 0.36 ms vs avg 0.23 ms;
   echo 0.20 ms avg vs 249 µs single trace) — carry which is which when used as an M4/M5
   input.

---

## Trust [twin]

- **`T1 = 0.36 ± 0.01 ms` (peak), avg `0.23 ms`, ~7% drift; prior record `114 µs`:**
  certificate-grade measured values for the M4 T1 range (best-case isolated transmon).
- **`T2,Echo = 0.20 ± 0.03 ms` (avg), `T2,CPMG = 0.38 ± 0.11 ms`; `T2,Echo = 249 ± 4 µs`
  (Device 18a):** certificate-grade for the M5 T2 range; carry the averaged-vs-trace
  distinction.
- **1/f PSD (α = 0.7), stretched-exponential fits:** measured M5 dephasing-noise
  character; bounds the Markovian-Lindblad approximation.
