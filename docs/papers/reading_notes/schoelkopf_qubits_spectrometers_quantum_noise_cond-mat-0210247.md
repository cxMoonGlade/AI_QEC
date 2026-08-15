# Reading note: Schoelkopf, Clerk, Girvin, Lehnert, Devoret — "Qubits as Spectrometers of Quantum Noise" (arXiv:cond-mat/0210247)

Provenance: FULL-TEXT close-read (精读). Source read in full (31 pages) from
`\\wsl.localhost\ubuntu-f\home\cx\Document\AI_QEC\AI_QEC\outputs\papers\cond-mat\0210247.txt`.
All quotes below are short ASCII fragments transcribed verbatim from that txt (ligatures /
hyphen-line-breaks cleaned in the quote text only; page anchors are the `===== PAGE N/31 =====`
markers in the file).

---

## Metadata [paper]

- Title: "QUBITS AS SPECTROMETERS OF QUANTUM NOISE" (PAGE 1).
- Authors: R.J. Schoelkopf, A.A. Clerk, S.M. Girvin, K.W. Lehnert, M.H. Devoret, Yale
  University, Departments of Applied Physics and Physics (PAGE 1).
- arXiv: cond-mat/0210247v1 [cond-mat.mes-hall], 10 Oct 2002 (PAGE 1). A book-chapter / lecture-note
  style review (draft filename `rjsdraft12.tex`).
- Type: pedagogical review + original SET-noise calculation. Establishes the canonical
  "two-level system as a quantum spectrum analyzer" framework and the sign convention for
  two-sided quantum noise spectral densities.
- Companion / foundational refs cited: Caldeira-Leggett [1], Callen-Welton FDT [2], Devoret
  circuit-quantization [3], Johansson-Kack-Wendin SET noise [14], Clerk-Girvin-Nguyen-Stone [17].

## Executive summary [paper]

A weakly-coupled two-level system (qubit) is a *frequency-resolved* quantum spectrum analyzer.
Prepared in its ground state, its excitation rate `Gamma_up` measures the noise spectral density at
**negative** frequency `S(-omega_01)`; prepared in its excited state, its relaxation/emission rate
`Gamma_down` measures the density at **positive** frequency `S(+omega_01)` (PAGE 4-5, Eqs. 13-14).
Because the noise variable `f` is a bath operator with `[f(tau),f(0)] != 0`, the spectrum is
**asymmetric**: `S(+omega) != S(-omega)` (PAGE 5). In equilibrium the asymmetry is fixed by
detailed balance, `S(+omega_01) = exp(beta hbar omega_01) S(-omega_01)` (PAGE 5, Eq. 15). Positive
frequency = energy delivered *to* the bath (bath absorbs); negative frequency = energy *from* the
bath (bath emits / spontaneous emission); at `T=0` the negative-frequency (absorption-by-qubit) side
vanishes (PAGE 5, PAGE 8). The steady-state qubit polarization reads out the asymmetry directly:
`Pss = [S(+w)-S(-w)]/[S(+w)+S(-w)]`, equal to `tanh(hbar omega_01 / 2 kB T)` in equilibrium
(PAGE 14 Eq. 40, PAGE 16). The paper then applies the "run it in reverse" idea — attach an
auxiliary qubit to a device and compute its up/down rates to get the device's full two-sided quantum
noise — to a single-electron transistor (SET), reproducing the Johansson et al. spectrum.

**This note adjudicates a spectral-asymmetry attribution.** What this paper OWNS (canonical
statement): the qubit-spectrometer identification `Gamma_up ~ S(-omega_01)` (excitation <- negative
freq), `Gamma_down ~ S(+omega_01)` (emission <- positive freq), the operator-noncommutation origin
of `S(+omega) != S(-omega)`, and the detailed-balance ratio `S(+w)/S(-w) = exp(beta hbar w)` with
the emission/absorption reading and the `T=0` one-sidedness.

## Method (deep) [paper] — exact equations verbatim

### Setup: TLS + weak transverse noise coupling

Two-level Hamiltonian, spin-1/2 mapping (spin up = ground state) (PAGE 2):

```
H0 = -(hbar omega_01 / 2) sigma_z            (Eq. 1)
```

Perturbation by a (initially classical, later operator) noise source `f(t)` transverse to the
qubit axis (PAGE 3):

```
V = A f(t) sigma_x                            (Eq. 2)
```

with `A` the coupling constant. Footnote 1 notes the general case would also couple `sigma_y`, and
that `sigma_z`-coupled noise causes dephasing (explicitly *not* treated here) — quote:
"Noise coupled to sigma_z commutes with the Hamiltonian" (PAGE 3).

### First-order perturbation theory -> transition probability

Interaction-picture first-order amplitude to reach the excited state from the ground state
(PAGE 3, Eq. 6): the excited-state amplitude carries `e^{i omega_01 tau} f(tau)`. Averaging the
probability over the noise gives (PAGE 3, Eq. 8):

```
pbar_e(t) = (A^2 / hbar^2) INT INT dtau1 dtau2 e^{-i omega_01 (tau1 - tau2)} <f(tau1) f(tau2)>
```

### Spectral density definition (the load-bearing definition)

For stationary noise with finite autocorrelation time, define (PAGE 4, Eq. 11):

```
S_f(omega) = INT_{-inf}^{+inf} dtau e^{i omega tau} <f(tau) f(0)>            (Eq. 11)
```

verbatim: "Sf (omega) = INT ... dtau e^{i omega tau} <f(tau)f(0)>" (PAGE 4). The excited-state
probability then grows linearly in time (PAGE 4, Eq. 12):

```
pbar_e(t) = t (A^2 / hbar^2) S_f(-omega_01)                                  (Eq. 12)
```

### The core result: up-rate and down-rate (the OWNED statement)

Excitation (up, 0->1) rate — proportional to the **negative**-frequency density (PAGE 4, Eq. 13):

```
Gamma_up = (A^2 / hbar^2) S_f(-omega_01)                                     (Eq. 13)
```

verbatim: "Note that we are taking in this last expression the spectral density on the negative
frequency side." (PAGE 4).

Relaxation (down, 1->0, emission) rate — proportional to the **positive**-frequency density; "the
sign of the frequency is reversed" (PAGE 5, Eq. 14):

```
Gamma_down = (A^2 / hbar^2) S_f(+omega_01)                                   (Eq. 14)
```

verbatim: "Another possible experiment is to prepare the two-level system in its excited state and
look at the rate of decay" ... "the sign of the frequency is reversed" (PAGE 5).

### Operator (quantum) spectral density -> Fermi Golden Rule

Reinterpreting `f` as a bath operator, the spectral density becomes the standard quantum expression
(PAGE 5, Eqs. 16-18):

```
S_f(omega) = INT dtau e^{i omega tau} SUM_{alpha,gamma} rho_aa <a|f(tau)|g><g|f(0)|a>   (Eq. 16)
S_f(omega) = 2 pi hbar SUM_{alpha,gamma} rho_aa |<a|f|g>|^2 delta(eps_g - eps_a - hbar omega)  (Eq. 18)
```

Substituting into Eqs. 13-14 yields "the familiar Fermi Golden Rule expressions for the two
transition rates" (PAGE 6). The paper frames Fermi's Golden Rule itself as "resulting from the
continuum acting as a quantum noise source" (PAGE 6).

### Master equation, polarization, T1

Rate equations for `p_e`, `p_g` with `Gamma_up`, `Gamma_down` (PAGE 13, Eqs. 38-39); polarization
`P = p_g - p_e`. Steady-state polarization reads out the asymmetry directly (PAGE 14, Eq. 40):

```
Pss = (Gamma_down - Gamma_up)/(Gamma_down + Gamma_up)
    = [S(+omega_01) - S(-omega_01)] / [S(+omega_01) + S(-omega_01)]          (Eq. 40)
```

Relaxation to steady state at the *sum* rate (PAGE 14, Eq. 41 and following):

```
Gamma_1 = Gamma_up + Gamma_down = (A/hbar)^2 [S(-omega_01) + S(+omega_01)]
```

verbatim: "the time 1/Gamma1 is referred to as T1" (PAGE 14).

### Table I "translation" between disciplines (PAGE 15)

`Gamma_up = (A^2/hbar^2) SV(+|omega|)`, `Gamma_down = (A^2/hbar^2) SV(-|omega|)`;
`P = (Gamma_down - Gamma_up)/(Gamma_down + Gamma_up)`; Quantum-optics Einstein B-coefficient
`= Gamma_up`, A-coefficient `= Gamma_down - Gamma_up`.

> Convention warning [paper->ours]: Table I on PAGE 15 writes `Gamma_up ~ SV(+|omega|)` and
> `Gamma_down ~ SV(-|omega|)`, which is the OPPOSITE sign pairing from the main-text Eqs. 13-14
> (`Gamma_up ~ S(-omega_01)`, `Gamma_down ~ S(+omega_01)`). The Table uses `SV` with a `|omega|`
> argument and a flipped sign convention; it appears to be a transcription slip / an alternate
> convention. **Trust the main-text Eqs. 13-14** (derived line-by-line, PAGE 4-5) as the canonical
> statement, not the Table. This is the exact kind of sign ambiguity our note is here to pin down.

### SET as noise source (Secs. 7-8, the original calculation)

Auxiliary qubit coupled to an SET, `H = H_SET - (1/2) Omega sigma_x + A sigma_z n` (PAGE 21,
Eq. 56); weak-coupling rates `Gamma_down/up = (A^2/hbar) S_Q(+/- Omega)` (PAGE 21, Eq. 57), i.e.
knowing the qubit up/down rates at tunable splitting `Omega` gives the SET's two-sided charge noise
`S_Q(Omega)` at all frequencies. Density-matrix / degenerate-2nd-order-perturbation machinery
(PAGE 22-27) reproduces the Johansson et al. spectrum (PAGE 28, Eq. 81) with "direct" and
"interference" contributions.

## The MECHANISM [paper -> ours]

Mechanism = **spectral asymmetry of a quantum bath as read out by a two-level probe**.

- A quantum bath coupled to a qubit has an intrinsically two-sided, asymmetric noise spectrum
  `S(omega)` because the coupling operator does not commute with itself at different times.
- The two sides drive physically distinct processes: `S(-omega_01)` -> qubit *excitation* (bath
  gives up energy `hbar omega_01`); `S(+omega_01)` -> qubit *relaxation/emission* (bath absorbs
  `hbar omega_01`).
- In equilibrium the ratio is Boltzmann-fixed (detailed balance). Out of equilibrium (biased
  amplifier/detector) "no general relation holds" (PAGE 6) — the two sides become independent.

For ours (AI_QEC twin / CGF-probe / coupled-bath teacher line): this is the **prior-art anchor** for
the emission-vs-absorption asymmetry of a bath spectrum and for the T=0 one-sidedness. It is the
canonical citation for "up-rate <- S(-w), down-rate <- S(+w)" and for the detailed-balance /
`tanh(beta hbar w / 2)` polarization statement. It is the physics our qubit-spectrometer / rate-gate
objects presuppose; it does NOT own our specific correlated/non-Markovian coupling wedge (Markovian,
single-qubit, transverse-only here).

## The OBSERVABLE / metric [paper]

Two independent observables fully characterize a quantum reservoir at a frequency (PAGE 14):
"a quantum noise source is always characterized by two numbers (at any frequency)".

1. **Up / down transition rates** `Gamma_up`, `Gamma_down` — measured by preparing the qubit in
   ground vs excited state and timing the transition (Eqs. 13-14). Directly give `S(-w)` and `S(+w)`.
2. **Steady-state polarization** `Pss` (Eq. 40) — reads the *asymmetry* `[S(+w)-S(-w)]`.
3. **Relaxation time** `T1 = (Gamma_up + Gamma_down)^{-1}` — reads the *sum* / symmetric part.

"a measurement of both the polarization and T1 of a two-level system is needed to fully characterize
the quantum noise" (PAGE 14).

Frequency-resolution requirement (spectrometer linewidth must beat the thermal smearing), quote:
"omega01/Delta_omega >= max[kBT/hbar omega01, 1]" (PAGE 5).

## Findings + numbers [paper]

Extracted precisely for the spectral-asymmetry adjudication:

### 1. Core qubit-spectrometer result (up <- S(-w), down <- S(+w))

- Spectral density definition (Eq. 11, PAGE 4):
  "Sf (omega) = INT ... dtau e^{i omega tau} <f(tau)f(0)>".
- Up rate (Eq. 13, PAGE 4): "Gamma_up = (A^2 / hbar^2) Sf(-omega01)", with the explicit note
  "we are taking ... the spectral density on the negative frequency side" (PAGE 4).
- Down rate (Eq. 14, PAGE 5): "Gamma_down = (A^2 / hbar^2) Sf(+omega01)"; the excited-state-decay
  experiment gives "the sign of the frequency is reversed" (PAGE 5).
- Physical role of the sides (PAGE 5): "Negative frequency noise transfers energy from the noise
  source to the spectrometer" and "Positive frequency noise transfers energy from the spectrometer
  to the noise source."

### 2. Asymmetry of quantum noise + detailed balance

- Operator noncommutation is the origin (PAGE 5): "because as we discuss below f is actually an
  operator" ... "[f(tau), f(0)] != 0 and Sf(-omega01) != Sf(+omega01)". If `f` were classical,
  "Sf(-omega01) = Sf(+omega01)" (PAGE 4-5).
- Detailed balance on the RATES (PAGE 5): "the transition rates must obey detailed balance
  Gamma_down/Gamma_up = e^{beta hbar omega01}".
- Detailed balance on the SPECTRAL DENSITIES (Eq. 15, PAGE 5):
  "Sf(+omega01) = e^{beta hbar omega01} Sf(-omega01)".
- Symmetric part = quantum FDT (Eq. 31, PAGE 9): "SV(omega) + SV(-omega) = 2 R0 hbar omega
  coth(hbar omega / 2 kB T)". Antisymmetric part (Eq. 32, PAGE 9):
  "SV(omega) - SV(-omega) = 2 R0 hbar omega".
- Compact resistor form (Eq. 28, PAGE 8): "SV(omega) = 2 R0 hbar omega / (1 - e^{-hbar omega/kBT})".

### 3. Emission vs absorption; T=0 one-sidedness

- Reading (PAGE 5): negative-freq noise "represents energy emitted by the noise source"; positive-freq
  "transfers energy from the spectrometer to the noise source".
- Resistor two-sided density (Eq. 27, PAGE 8) with the T=0 statement, quote: "at zero temperature
  there is no noise at negative frequencies because energy can not be extracted from zero-point
  motion" and "the vacuum is capable of absorbing energy from the qubit" (PAGE 8).
- Quantum-limit form (Eq. 30, PAGE 9): "SV(omega) = 2 R0 hbar omega Theta(omega)", with "the
  resistor can only absorb energy, not emit it, at zero temperature" (PAGE 9).
- Master-equation restatement (PAGE 14): "In the zero-temperature limit, there is no possibility of
  the qubit absorbing energy" ... "Gamma_up = 0, and we find full polarization P = 1".

### 4. Polarization / temperature readout (tanh statement)

- Steady-state polarization = asymmetry ratio (Eq. 40, PAGE 14):
  "Pss = ... [S(+omega01) - S(-omega01)] / [S(+omega01) + S(-omega01)]", with
  "An measurement of the steady-state polarization allows one to observe the amount of asymmetry".
- Equilibrium value (PAGE 16): "P = tanh(hbar omega01 / 2 kB T), as one expects for any two-level
  system at temperature T." (this is the tanh(beta hbar omega / 2) statement the note was asked to
  pin down; here `beta = 1/kBT`).
- Classical -> zero polarization (PAGE 13): "if the spectral density is symmetric (classical!), then
  the rates ... are equal ... the polarization ... is identically zero. It is the quantum, or
  antisymmetric, part of the noise which gives the finite polarization".

### SET application numbers (secondary)

- Weak-coupling SET-qubit rates (Eq. 57, PAGE 21): "Gamma_down/up = (A^2/hbar) SQ(+/- Omega)".
- Full SET quantum charge-noise spectrum (Eq. 81, PAGE 28) reproducing Johansson et al. [14], built
  from "direct" (Eq. 72) + negative "interference" (Eq. 73) contributions.
- `T=0` high-freq cutoff of the negative side at `|Omega| ~ VDS/2` (PAGE 27): "SQ(-Omega) will
  vanish identically at zero temperature" beyond the largest energy the SET can give up per event.

## Limitations [paper]

- **Dephasing excluded.** Only transverse (`sigma_x`) noise / relaxation + polarization treated;
  `sigma_z` (pure-dephasing) noise explicitly set aside (PAGE 3 footnote 1; PAGE 12-13: "we deal ...
  with only these first two features ... and ignore the dephasing").
- **Weak coupling / lowest-order PT.** Rates are first-order (Eqs. 5-14) or second-order (SET,
  A->0); validity window `tau_f << t << 1/Gamma` (PAGE 4 footnote 3). Strong coupling not covered.
- **Markov / stationarity assumed.** Correlation function assumed stationary with finite `tau_f`
  (PAGE 3-4); SET calc makes an explicit Markov approximation (PAGE 22). No non-Markovian /
  memory / correlated-bath structure — this is a single-qubit Markovian spectrometer.
- **Detailed balance holds only in equilibrium.** Out of equilibrium (biased amplifier/detector)
  "no general relation holds" (PAGE 6); Eq. 15 and the tanh polarization are equilibrium-only.
- **Sequential-tunneling regime** for the SET (`g/2pi << 1`, near degeneracy); higher-order
  co-tunneling neglected (PAGE 19-20, PAGE 27).
- **Table-I sign inconsistency** vs main-text Eqs. 13-14 (see Method note) — a convention/transcription
  hazard for anyone citing the Table rather than the derivation.

## Relevance [ours]

- **Direct prior-art anchor for spectral asymmetry.** Any AI_QEC claim of the form "excitation rate
  tracks S(-w), emission/relaxation rate tracks S(+w), and the asymmetry is detailed balance
  `S(+w)/S(-w)=exp(beta hbar w)`" is OWNED by this paper (Eqs. 13-15, 40). Cite it as the canonical
  source; do not re-derive it as novel.
- **CGF-probe / rate-gate line** (MEMORY: quantum-bath M1+M2, "rate-gate object clarified
  ... directional ratio (N+1)/(N+1/2)"): the directional (up vs down) rate distinction and its
  Bose/detailed-balance ratio are exactly this paper's up/down-rate asymmetry. Our directional-ratio
  physics is a *special case / re-expression* of Schoelkopf et al.'s `Gamma_down/Gamma_up =
  exp(beta hbar w)` (equivalently `(n+1)/n` for a thermal mode). This paper is the attribution owner
  for that gate; our contribution must be positioned *beyond* it (e.g., non-Markovian / correlated
  structure it explicitly does not treat).
- **Coupled-bath / pseudomode teacher line:** the emission-vs-absorption reading and the T=0
  one-sidedness (`Theta(omega)`) are the baseline the coupling wedge must exceed. The paper's bath is
  Markovian, single-qubit, equilibrium (or simple nonequilibrium SET) — our non-Markovian / correlated
  contribution is what it does NOT own (consistent with MEMORY project-coupling-nonmarkovian-is-the-
  contribution).
- **"Qubit as spectrometer" method** (attach an auxiliary qubit, read up/down rates -> device's
  two-sided noise, Secs. 7-8) is the conceptual template for using a probe qubit to certify a noise
  source — relevant to any twin/teacher certification-by-probe design.

## How to use / trust [ours]

- **Trust: high, canonical.** This is the standard reference for the qubit-spectrometer relation and
  the two-sided sign convention. Derivations are explicit and pedagogical.
- **Cite Eqs. 11, 13, 14, 15, 40 from the MAIN TEXT** for: `S(omega)` definition, up-rate `~S(-w)`,
  down-rate `~S(+w)`, detailed-balance spectral ratio, and polarization = asymmetry.
- **Do NOT cite Table I (PAGE 15) for the sign pairing** — it disagrees with Eqs. 13-14 (Table:
  `Gamma_up~SV(+|w|)`; main text: `Gamma_up~S(-w)`). If a downstream doc took the sign from the
  Table, flag it as an error and re-anchor on the derivation.
- **Scope guard for our claims:** anything we build on this must stay inside Markovian, weak-coupling,
  transverse-noise assumptions, OR be explicitly declared as extending past them. Detailed balance +
  tanh polarization are equilibrium-only; do not apply them to a driven/nonequilibrium source without
  the SET-style full two-sided calculation.
- **Epistemic class (per METRICS.md):** the up/down-rate and detailed-balance relations are (a) exact
  results within stated assumptions (Fermi Golden Rule / KMS), usable as a derivation premise for the
  spectral-asymmetry direction. The tanh polarization and `exp(beta hbar w)` ratio are exact-in-
  equilibrium; treat as (a) only under the equilibrium premise, else (c).

---

### 3-line owner summary (for the adjudication)

Schoelkopf-Clerk-Girvin-Lehnert-Devoret (cond-mat/0210247) OWNS the canonical qubit-spectrometer
statement: the UP (0->1, excitation) rate `Gamma_up = (A^2/hbar^2) S(-omega_01)` reads the noise at
NEGATIVE frequency, and the DOWN (1->0, relaxation/emission) rate `Gamma_down = (A^2/hbar^2)
S(+omega_01)` reads POSITIVE frequency (Eqs. 13-14, PAGE 4-5), with `S(omega)=INT dtau e^{i omega
tau}<f(tau)f(0)>` (Eq. 11). The ASYMMETRY `S(+w)!=S(-w)` comes from operator noncommutation and, in
equilibrium, is DETAILED BALANCE `S(+omega_01)=exp(beta hbar omega_01) S(-omega_01)` (Eq. 15,
PAGE 5); positive freq = emission INTO the bath, negative freq = absorption FROM the bath, T=0
kills the negative side (PAGE 8), and `Pss=[S(+w)-S(-w)]/[S(+w)+S(-w)]=tanh(hbar omega_01/2kBT)`
(Eq. 40 / PAGE 16) reads the asymmetry/temperature.
