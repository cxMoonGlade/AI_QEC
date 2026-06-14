# The Twin — A Teacher-Learner, Finance-Structured QEC Error-Mechanism Digital Twin

This is the current binding spec for "the twin."
ADR 0003 (B methodology) and ADR 0004 (finance framing) are the methodological core.

"The twin" is the descriptive name. The code package
identifier is `qec_twin`, a neutral, stable handle.

## What it is

A digital twin of a real QEC device's **error mechanisms**, built by a
teacher-learner method, that both **reproduces** observed syndrome/logical data and
answers **counterfactuals** — "if I change this mechanism, how does logical
performance change?" — with **honest uncertainty**.

The organizing principle is **not** symmetry compression. It is the structural
identity (ADR 0004) between QEC mechanism calibration and the
quantitative-finance calibration/risk problem:

> recovering a local noise-channel field `E` from syndrome statistics **is** the
> same ill-posed inverse problem as recovering a volatility surface from option
> prices. Thirty years of quant-finance tooling for its failure modes applies.

## The object

A context `c` (circuit schedule, controls, code descriptor, drift/time) induces a
noisy circuit channel from a **per-location CPTP channel field** `E`, and an
observation `y = (s, m, …)` (detector trajectory `s` + logical outcome `m`):

```
p(y | c) = Tr[ M_y · C_E(c)(ρ0) ],     C_E(c) = ∏_q (E_q ∘ G_q)   (circuit order)
```

- `E_q = PhysDec(θ_q) ∈ CPTP` — each local channel is CPTP **by construction**
  (Stinespring: Hermitian generator → isometry → Kraus; or a GKSL generator
  `E = exp(Δτ·L_θ)`, `H` + PSD Kossakowski, for the non-Clifford/coherent part).
  `θ` is the internal coordinate that *generates* the channel; it is **not** a
  `do()` handle.
- `G_q` is the ideal operation; `M_y` the POVM effect for outcome `y`; `ρ0` the
  initial state.
- The forward is **exact** at small scale (density-matrix, non-Pauli /
  non-Clifford capable) and **differentiable**. Two backends, identical for
  noiseless syndrome extraction (validated to machine precision): an **ancilla**
  register (`2^(2d-1)`) and a data-only **parity** register (`2^d`, each
  stabilizer a direct `Z_jZ_{j+1}` projection) that makes `d ≥ 5` tractable.

No amortized context map `f_ψ(c)` and no scalability carrier are committed now —
the main-line parameterization is chosen later against the four capabilities,
with future scalability as one selection criterion (ADR 0005).

## The four capabilities

The spec is these four capabilities over hardware-realistic noise (with their
finance analogues), **not** a fixed architecture:

| Capability | QEC | Finance analogue |
|---|---|---|
| **recover** | label-free calibration of `E` from `p(s,m\|c)` (exact Born-rule observation-NLL) | volatility-surface calibration |
| **understand** | mechanism interpretation + honest alias/uncertainty bands | model-uncertainty / factor interpretation |
| **manipulate** | channel-level `do()` knobs → ΔLER | Greeks / hedging / scenario stress |
| **predict** | drift / rare-failure / decoder-impact forecasting | state-space / regime / multiscale stochastic-vol |

## Methodology (the finance spine)

- **Calibration = exact multi-context Born-rule observation-NLL**, not moment
  matching. Low-order moments (detector marginals + pairwise) are exactly what a
  stochastic Pauli channel reproduces, so moment matching **Pauli-shadows** the
  coherent/non-Clifford structure (the finance "vanillas pin marginals, not
  dynamics"). Moment matching is a negative control only. (ADR 0003.)
- **Probe richness breaks the alias, not parameter-tying.** An observational fit
  pins `E` only up to the **observational alias quotient**; what shrinks it is
  *data* (a probe-richness ladder `C_cal(r)`: memory → multi-round/bases → active
  → basis-rotated → coherent-sensitive). Physical priors (CPTP, locality, known
  circuit) act as a Tikhonov *regularizer* — they shrink the parameter/variance
  space but do **not** break a genuine observational alias; parameter/orbit
  sharing is retired as an identifiability claim (ADR 0005).
- **`do()` is a channel-level, parameterization-independent transform** (Tier 0:
  `E_i → I` remove; Tier 1: CPTP-safe weakening `(1-a)I + aE`), scored by ΔLER
  under a **predeclared, frozen decoder** `D`.
- **Honest uncertainty bands.** Report a band, not a point: the range of ΔLER over
  the calibration-consistent model set `{E : NLL ≤ NLL_min + slack}` (finance
  model-uncertainty / UVM). Tier-0 closed form: `band = (z/√N)·√(gᵀ H⁺ g)` with
  `g = ∇ΔLER`, `H = ∇²NLL`; the finite-shot scale enters as `1/√N`, and `g`'s
  weight in `H`'s near-null space is the epistemic alias (the learnable-DOF
  deficiency surfaced on the knob).
- **Counterfactuals are never validated by calibration fit alone** — they are
  validated against a **controlled teacher** whose true mechanisms are known
  (finance: P&L backtest of a hedge). This is the only counterfactual ground truth
  and bounds what real-data (C) can claim.

## Path and status

> The gated roadmap — phase acceptance gates, strict invariants, and what stays
> open — is [`docs/PLAN.md`](PLAN.md); this section stays the object-contract summary.

**B (validate the loop on a controlled toy) → HARDEN (richer/correlated
mechanisms, larger `d`, drift) → C (real Google 72Q/105Q).** Success axes =
recover/understand/manipulate/predict.

- **B — done on an exact repetition-code toy.** Label-free calibration recovers a
  coherent over-rotation teacher (`calib_kl ≈ 0`); the `do()` knob matches the
  controlled teacher's true ΔLER; the negative controls fail as predicted
  (moment-matched ≈ 900× worse = Pauli-shadowing, shuffled-channel ≈ 1400× worse
  = mechanism misassignment); calibrate-on-`r≤k` / predict-the-held-out-exotic
  shows the out-of-basis counterfactual stays Pauli-shadowed until phase-sensitive
  probes enter calibration; Tier-0 alias bands cover the truth and shrink with
  probe richness.
- **Harden — in progress.** Code-scaling d3→d5 does **not** break the loop
  (bijection, alias-DOF, calibration, knob, band coverage all robust; the band
  even tightens) — so the falsification boundary is the **richer/correlated
  mechanism** axis (next), then drift.
- **C — deferred** until the loop is validated under realistic complexity. Real
  data has no realized counterfactual, so calibration fit can never validate a
  knob there; the available validation is cross-config transfer (d3→d5/d7, X↔Z,
  set1→set2, 72→105Q), carrying the controlled-system alias band forward as a
  prior on every Google knob.

## Notation (reserved)

| Symbol | Meaning |
|---|---|
| `A` | DEM parity map `F_2^{B×M}` (fault→observation) — never for assignment |
| `S` / `Π` | learned soft assignment matrix |
| `ω(j)` | **known** teacher orbit/symmetry-class assignment of fault `j` — used as known structure for compute/correctness, never an identifiability lever |
| `λ_j` | Stage-1 fault logit `logit(p_j)` — never `ℓ_j` |
| `m` | logical observable bit — never `o` |
| `e` | latent DEM fault vector |
| `y = (s,m,…)` | observation: detector trajectory `s` + logical `m` |
| `K` | prototype count |
| `B` | observation bits | `M` | effective DEM faults |
| `c` | circuit/control context | `E` / `θ` | per-location CPTP channel / its internal coordinate |

## Claim boundary

Controlled, small-scale, exact. No Google physical-mechanism, public-label,
legacy-catalog-ID, Born-rule-generation, or CPTP/GKSL-learning claim beyond the
validated controlled loop until C is reached and earned. The `raw_target_only`
block-normalized score plus controls remains the Google V2 headline, not
`full_target` alone.
