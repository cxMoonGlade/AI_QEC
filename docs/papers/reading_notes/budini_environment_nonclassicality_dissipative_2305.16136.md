# Full-text review — A. A. Budini, "Quantifying environment non-classicality in dissipative open quantum dynamics" (arXiv:2305.16136)

> **Provenance (2026-07-02): FULL-TEXT read (精读).** PDF fetched from arXiv → txt
> `outputs/papers/2305.16136.txt` (11 pages, PyMuPDF). All §/Eq/Fig refs from that text. Figures not
> pixel-extracted — figure facts = captions + numbers stated in text. Ligatures (ﬂ/ﬁ/ﬀ) and
> hyphen-linebreaks present in the txt; verbatim quotes below are clean ASCII fragments only.

## Metadata [paper]
- **Author / affiliation:** Adrian A. Budini — CONICET, Centro Atomico Bariloche, Argentina; and UTN-FRBA.
  Single author.
- **Venue / status:** arXiv:2305.16136v1 [quant-ph], 25 May 2023. Published as Phys. Rev. A 108, 042203 (2023).
- **Type:** Theory (open-quantum-systems formalism + analytically-solved paradigmatic examples; no experiment,
  no numerical simulation beyond plotting closed-form expressions).

## Executive summary [paper]
Budini proposes a scalar **degree of environment quantumness / non-classicality** for *dissipative* open-system
dynamics. It measures how far a genuine quantum environment's action departs from that of a *classical noise
field*. The physical ground is the non-commutativity `[H, sigma_0] != 0` between the initial reservoir state
`sigma_0` and the total system-environment Hamiltonian `H`. The time-dependent indicator `Q_t` [Eq. (3)]
equals 1 (classicality) exactly when `[H, sigma_0] = 0`, and is written purely in terms of the **dual
propagator** of *system operators* [Eq. (8)], so it is defined identically in Markovian (Lindblad) and
non-Markovian regimes. Maximizing the stationary value over initial system states gives `D_Q` [Eq. (6)],
computable from the largest eigenvalue of the (time-reversed) stationary state [Eq. (13)]. Key structural
result: **`Q_t = 1` for any UNITAL map** [Eq. (22)] — so the indicator is equivalently a measure of departure
from unitality. Worked examples: thermal two-level (`D_Q = tanh(beta*hbar*omega_0/2)`), non-Markovian
zero-T decay, resonance fluorescence (`D_Q -> 1 - 2(Omega/gamma)^4` weak drive), two interacting qubits,
harmonic oscillator.

## Method (deep) [paper]

**Object under study — a DYNAMICAL MAP / expectation value, NOT a measurement record.** The reduced state is
the standard partial-trace dynamical map [PAGE 2, Eq. (1)]:

    rho_t = G_{t,0}[rho_0] = Tr_e[ e^{-iHt} (rho_0 (x) sigma_0) e^{+iHt} ]

Budini splits `rho_t` into a "classical" piece (freezing `sigma_0`) plus a remainder [PAGE 2, Eq. (2)]:

    rho_t = Tr_e[(e^{-iHt} rho_0 e^{+iHt}) sigma_0] + Tr_e[(e^{-iHt} rho_0 e^{+iHt}) Delta_sigma_t]

with `Delta_sigma_t = e^{-iHt} sigma_0 e^{+iHt} - sigma_0`. When `[H, sigma_0] ~ 0` the second term vanishes.

**The quantumness measure (the central object).** [PAGE 2, Eq. (3)]:

    Q_t = Tr_{se}[ (e^{-iHt} rho_0 e^{+iHt}) sigma_0 ]     (dimensionless, scalar, real-valued function of t)

`Q_0 = 1`; `[H,sigma_0]=0 => Q_t = 1`. Its time-derivatives are nested commutators of `H` with `sigma_0`
[PAGE 2, Eqs. (4)-(5)]: `dQ_t/dt = -i Tr_{se}[(e^{-iHt} rho_0 e^{+iHt})[H,sigma_0]]`, etc.

**Dual-propagator form (why it works out of the Markovian regime).** With the dual propagator `G*_{t,0}`
of *operator* evolution `A_t = G*_{t,0}[A_0] = Tr_e[e^{+iHt} A e^{-iHt} sigma_0]` [PAGE 2, Eq. (7)], the
measure becomes [PAGE 2, Eq. (8)]:

    Q_t = Tr_s[ G*_{-t,0}[rho_0] ]

i.e. `Q_t/dim(H_s)` is the expectation of the "operator" `rho_0` under the maximally-mixed initial state.
Bounds `0 <= Q_t <= dim(H_s)` [Eq. (9)] and `0 <= D_Q <= dim(H_s) - 1` [Eq. (10)].

**Degree of environment quantumness (the scalar invariant).** [PAGE 3, Eq. (6)]:

    D_Q = max_{rho_0} ( lim_{t->inf} Q_t - 1 )

`D_Q = 0` <=> classicality. From the stationary state `~rho_inf` (tilde = time reversal t<->-t) [Eq. (11)-(13)]:

    D_Q = dim(H_s) * max({lambda_i}) - 1 ,   rho_0 = |i_max><i_max|

where `max({lambda_i})` = largest eigenvalue of `~rho_inf`.

**Lindblad realization.** For a GKSL generator [PAGE 4, Eq. (19)] the dual operator evolution [Eq. (20)] is
solved with `A_t|_{t=0} = rho_0`; then `Q_t = Tr_s[~A_t]`.

**Collisional / renewal models** (Appendix, PAGE 9-11): `Q_t` from the dual of a renewal collisional map;
condition `Tr_s[E*[A]] = Tr_s[A]` (dual superoperator trace-preserving) gives `Q_t = 1` [Eq. (18)/(A.3)].

## The MECHANISM (for implementation) [paper -> ours]
Not a mechanism we would implement as a teacher channel — it is a **diagnostic scalar on a given open-system
generator**. To compute Budini's `Q_t`/`D_Q` for one of our teachers we would: (i) take the teacher's Lindblad
generator, (ii) evolve the *dual* operator equation [Eq. (20)] with initial operator `rho_0`, (iii) read
`Q_t = Tr_s[~A_t]`, (iv) maximize the stationary value over `rho_0` via the largest eigenvalue of the
time-reversed stationary state [Eq. (13)]. It requires the **full microscopic / Lindblad generator**, and it
acts on **system operators via the dual map** — there is no repeated-measurement / record ingredient anywhere.
Repo status: not implemented; nothing in `src/qec_twin/` computes this.

## The OBSERVABLE / metric [paper]
- **Metric:** `Q_t` [Eq. (3)] and its maximized-stationary scalar `D_Q` [Eq. (6)]. Units: dimensionless.
  `Q_t = 1` / `D_Q = 0` == classicality (environment reproducible by classical noise). Larger `D_Q`
  (up to `dim(H_s)-1`) == more non-classical / more non-unital.
- **What it measures:** departure of the environment's influence from a *classical stochastic field* — and,
  provably, departure from **unitality** (see next section).
- **Regime where informative:** dissipative dynamics (environment induces energy transitions, not only
  dephasing). Explicitly flagged limitation: for pure-dephasing with `dim(H_s) >= 3` there exist unital
  dynamics not obtainable from classical fields, so `Q_t=1` there is a false-negative for non-classicality
  [PAGE 4, Sec. III.E].

## Findings + numbers [paper]

Answers to the five adjudication questions, each with a verbatim anchor:

**Q1 — object quantified: dynamical map / dual propagator, NOT a measurement record.**
[PAGE 2] "the quantumness measure Qt can be written as Qt = Trs[G ... t,0[rho0]], which only depends on the
operator dual evolution and the initial system state." And the abstract [PAGE 1]: "the measure can be written
in terms of the dual propagator that de nes the evolution of system operators."

**Q2 — driven by UNITALITY specifically; `Q_t = 1` for unital maps.**
[PAGE 4, Sec. III.E, Eq. (22)] "The dynamics is de ned as unital when in addition it is ful lled that
sum_alpha Talpha Talpha^dagger = Is, => Qt = 1." And the Conclusions [PAGE 9]: "the quantumness indicator also
vanishes when the open system dynamics is de ned by a unital map [Eq. (22)]. Hence, the proposed indicator can
also be read as a measure of departure from this dynamical property." Collisional restatement [PAGE 4, Eq.(18)]:
"when the dual superoperator E preserves trace the quantumness indicator vanishes identically ... The condition
(18) ... in general is ful lled by unital maps."

**Q3 — no g^2 / gamma/2 CONSTANT. It is a general commutator/eigenvalue quantifier; any rate appears only in
model-specific closed forms.** The generic object is commutator-based [PAGE 2, Eqs. (4)-(5)] and
eigenvalue-based [PAGE 3, Eq. (13)]. There is NO universal `gamma/2` unitality constant. Rates/coefficients
enter only per example, e.g. thermal TLS `D_Q = tanh(beta*hbar*omega_0/2)` [PAGE 5, Eq. (25)]; harmonic
oscillator `Q_t = exp[(kappa - zeta)t]` [PAGE 8, Eq. (54)]. The one power-law that superficially echoes our
"~g^4 measurement-modulated" is the resonance-fluorescence *weak-drive* expansion [PAGE 7, Eq. (39)]:
`D_Q ~ 1 - 2(Omega/gamma)^4`, `(Omega/gamma) < 1` — but note here the `g^4` term is a departure *toward*
classicality driven by the coherent DRIVE `Omega`, NOT a measurement-modulated addition on top of a floor.

**Q4 — strictly at the map / generator level; never a repeated-measurement record distribution.**
`Q_t` is a single-time trace functional of the dynamical map / dual propagator [Eqs. (3), (8)]. The examples
are all closed-form solutions of `rho_t` / dual operator ODEs. Repeated projective measurement, a stochastic
measurement record, click statistics, or a monitored trajectory NEVER appear. The collisional/renewal models
(Appendix) are *unravellings of the map*, averaged over collision times — still a map, not a conditioned record.

**Q5 — NO additive floor + measurement-modulated decomposition.**
The only decomposition is the classical/quantum split of `rho_t` [PAGE 2, Eq. (2)], and `Q_t` is defined as the
*trace of just the first (classical) term* [PAGE 2, Eq. (3)]. There is no split of `Q_t` (or `D_Q`) into a
measurement-independent floor plus a measurement-modulated part. There is no measurement variable at all, so no
such modulation exists. Confirmed absent.

**Worked-example numbers [paper]:**
| Model | `D_Q` (or `Q_t`) | ref |
|---|---|---|
| Thermal two-level | `D_Q = |<sigma_z>_inf| = tanh(beta*hbar*omega_0/2)`; `->0` high T, `->1` T=0 | Eq. (25) |
| Non-Markovian zero-T decay | `Q_t = 1 - <sigma_z>_0 (1-|c_t|^2)`, `D_Q = 1` | Eqs. (28)-(29) |
| Resonance fluorescence | `D_Q = gamma*sqrt(gamma^2+4Omega^2)/(gamma^2+2Omega^2)`; weak `~1-2(Omega/gamma)^4`; strong `~1/(Omega/gamma)->0` | Eqs. (38)-(40) |
| Two interacting qubits | `D_Q = gamma(gamma+2 sqrt(gamma^2+Omega^2))/(gamma^2+Omega^2)`; entanglement needed near classical limit | Eq. (44) |
| Harmonic oscillator (thermal) | `Q_t = exp[(kappa-zeta)t]` (diverges any finite T); renorm `D_QR = 1 - exp(-beta*hbar*omega_0)` | Eqs. (54), (56) |

## Limitations [paper]
- **Single-time map functional only.** No repeated-measurement / record / monitored-trajectory object anywhere.
- **False negatives from unitality.** Any unital dissipation reads `Q_t = 1` even when genuinely non-classical:
  pure-dephasing with `dim(H_s) >= 3` gives unital-but-not-classical-field dynamics missed by the indicator
  [PAGE 4, Sec. III.E; PAGE 4-5 "the inverse implication is not valid ... there exist unital dynamics that
  cannot be obtained by considering the action of classical stochastic elds"].
- **No universal rate/constant.** Every magnitude/scaling (`gamma/2`, `Omega^4`, `tanh`) is model-specific
  closed form, not a general theorem-grade constant.
- **Open issues stated by the author:** which features cause revivals of `Q_t` is unknown; an *operational
  definition and experimental measurability* are left as open problems [PAGE 9, Conclusions] — i.e. the paper
  itself does NOT give a measurement/record-level operationalization.

## Relevance to AI_QEC / Bone A [ours]
Budini is the **nearest existing quantified non-classicality / non-unitality indicator**, and this note fixes
exactly how far his ownership extends vs our Bone A record-level claim:

- **He OWNS:** a rigorous scalar quantifier of environment non-classicality that (a) is provably driven by
  **non-unitality** — `Q_t = 1` iff (broadly) the dual map is trace-preserving / unital [Eqs. (18),(22)] — and
  (b) is computable from a Lindblad/dual generator across Markovian AND non-Markovian regimes [Eq. (8)]. So the
  *concept* "non-unitality is the fingerprint of a genuinely quantum (non-classical-noise) environment" is
  established prior art. Any AI_QEC claim that "our floor is pinned by unitality" must CITE Budini for that
  concept — it is not novel to us at the map level.
- **He does NOT own (the Bone-A wedge stays open):**
  1. **A RECORD-level object.** Budini's `Q_t` lives on the dynamical map / dual propagator [Eqs. (3),(8)];
     our Bone A is a distance between the **repeated-projective-measurement RECORD** of a monitored quantum
     bath and its best classical imitator. There is no measurement record, click distribution, or monitored
     trajectory anywhere in Budini. He even lists an *operational/experimental* definition as an OPEN problem.
  2. **A `gamma/2`-pinned quantitative FLOOR.** He gives no universal unitality constant. Our `~g^2` non-unital
     floor pinned by a `gamma/2` unitality bound has no counterpart here — his numbers are per-example.
  3. **An ADDITIVE floor + measurement-modulated (`~g^4`) decomposition.** Absent entirely (no measurement
     variable to modulate). His only split is the classical/quantum split of `rho_t` [Eq. (2)], not a
     floor+modulation split of the non-classicality scalar.
- **Correction this forces on us:** do NOT claim novelty for "non-unitality => non-classical environment" at
  the *map* level — Budini owns that (`Q_t=1 <=> unital`, explicitly). Our defensible novelty is narrower and
  must be stated as such: (i) lifting the indicator to a **sequential-measurement RECORD distance**, (ii) the
  `gamma/2`-pinned quantitative floor (`~g^2`), and (iii) the **additive floor + measurement-modulated `~g^4`
  decomposition**. Also note his `~(Omega/gamma)^4` is NOT our `~g^4` (his is a drive-driven approach to
  classicality; ours is a measurement-modulated term over a floor) — do not conflate them.

## How to use / trust + open questions [ours]
- **Trust:** FULL-TEXT read; all equations transcribed from the txt. Figures not pixel-extracted (Fig. 1/2 are
  plots of the closed forms Eqs. (38),(44) already transcribed — no extra load-bearing facts lost).
- **How to use in the adjudication:** cite Budini for the *concept* that non-unitality is the map-level signature
  of a non-classical (non-classical-noise) environment, and to bound our novelty claim to the record level +
  the `gamma/2` floor + the additive `g^2`/`g^4` decomposition. Frame our contribution as the record-level,
  operationally-measurable lift that Budini himself flags as an open problem.
- **Open questions:** (a) Is Budini's map-level `D_Q` recoverable as a *limit* of our record-level distance
  when the measurement is made trivial/absent? If yes, that is a clean way to show our object strictly contains
  his. (b) His unital false-negative (dephasing `dim>=3`) — confirm our record-level object does NOT inherit it
  (a genuine additional-power argument if so).
