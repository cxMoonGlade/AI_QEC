# AI QEC Domain Context

This repository builds a **teacher-learner, quant-finance-structured QEC
error-mechanism digital twin** ("the twin"; spec: `docs/TWIN.md`), with four
capabilities: recover / understand / manipulate / predict.

## Terms

- **The twin**: the teacher-learner, finance-structured QEC error-mechanism digital twin — a per-location CPTP channel field with the four capabilities (recover/understand/manipulate/predict). Spec: `docs/TWIN.md`.
- **DEM parity map**: a binary matrix `A in F_2^{B x M}` mapping Bernoulli DEM fault bits to observed detector/logical bits via `y = A e mod 2`.
- **Fault activation vector**: `e in {0,1}^M`; `e_j ~ Bernoulli(p_j)` records whether effective DEM fault `j` occurred in one shot.
- **Observation bits**: the concatenation of detector bits and logical observable bits. Their count is `B`.
- **Observation vector**: `y in {0,1}^B`; the sampled detector/logical bits for one shot.
- **Fault mechanisms**: DEM error mechanisms. After duplicate-mask canonicalization, their effective count is `M`.
- **Stage-1 fault logit**: `lambda_j = logit(p_j)`. Do not write this as `ell_j`.
- **Observational alias class**: a quotient class for mechanisms that induce indistinguishable or near-indistinguishable visible distributions. If `p(y | m_a) ~= p(y | m_b)` on the declared visible surface, the correct discovery output is `m_a ~_obs m_b`, not an arbitrary forced split.
- **Physicality boundary**: mechanism definitions are implemented as unitary channels, Kraus channels, or classical readout assignment matrices. Enabling a mechanism ID selects that catalog definition. The established learner does not yet learn an arbitrary CPTP/GKSL channel family by construction; as of 2026-06 an exact CPTP physical substrate (the twin's channel substrate — `qec_twin.forward.cptp_channel` channel kernel plus `forward/exact/circuit_sim` and `forward/exact/rep_code` exact circuit-to-observation forward model) is an active small-scale build toward the mechanism-conditioned noise simulator with knobs, not a validated twin.
- **CPTP guardrail audit**: the `cptp_guardrail_audit.json` artifact; it checks complete-positivity representation class, channel dimension, unitary unitarity, Kraus trace preservation, readout stochasticity, and parameter validity for every enabled mechanism record.
- **Born-local**: an exact local Born-rule diagnostic where sampled local observations come from exact local Born probabilities for CPTP/readout mechanisms. It has effective depth one and is not the full-circuit teacher.
- **Four capabilities** (the twin's success axes, ADR 0005): **recover** (label-free calibration), **understand** (mechanism interpretation + honest alias/uncertainty bands), **manipulate** (channel-level `do()` → ΔLER), **predict** (drift / rare-failure / decoder-impact). Emitting CPTP/GKSL objects is necessary structure, not sufficient evidence; the bar is these four over hardware-realistic noise (`docs/TWIN.md`).
- **Mechanism-conditioned noise simulator with knobs**: the ideal downstream use of successful mechanism recovery. If mechanisms, locations, and strengths are recovered accurately enough, the model should become a controllable QEC noise simulator: reduce or amplify a mechanism, move or remove a location, forecast drift, generate rare failure cases, and rank calibration or layout actions by predicted logical impact. This is a target use case, not a claim made by current Google visible-replay artifacts.
- **Intervention unit (knob)**: there is a deliberate gap here. The **end-goal knob** — what an experimentalist would act on — is a specific hardware **location** `E_i` ("fix THIS qubit/gate/location"). With only observational identifiability, whether the per-location channel is resolved (vs only a mechanism **class**) is an identifiability question answered by **probe richness / the alias band** — not by tying parameters. (ADR 0005 retired the earlier orbit-field framing of this gap — `theta = rho(g)·vartheta_omega + U·z`, the "location residual `z`" — as an identifiability lever; orbit-sharing shrinks variance, not the observational alias.) Rule unchanged: do not present a class-level finding as a location-level instruction; report the per-location knob with its alias/uncertainty band (`docs/TWIN.md`, the Tier-0 band).
- **do() / intervention**: a knob is realized as a parameterization-independent, channel-level transformation of the CPTP channel (`E_{i,t}`, the local channel `mathcal E` in `docs/TWIN.md`), not as an edit of a teacher-native parameter (`epsilon`/`gamma`/axis) — those are not functions of the channel alone, so they are ambiguous on a channel recovered only up to the observational alias quotient. Canonical do()s, in increasing alias-sensitivity: **remove** (`E -> I`, unambiguous), **scale strength** (generator `L -> k*L`, `E = exp(k*L)`; requires a declared log branch and a CPTP guardrail — see ADR 0003), **structural** (axis or coherent-vs-stochastic reweight). Counterfactual validity is scored on the observable consequence `Delta p(y)` of the same do() applied to the teacher's true channel and the twin's recovered channel — never by comparing channels directly.
- **Logical error rate (LER)**: the decoded logical-observable flip probability under a declared decoder (e.g. MWPM), not the raw undecoded logical-flip rate. It is the headline observable a knob acts on (`do() -> Delta LER`). In the B feasibility step it is computed exactly on a small repetition code; its decoder-free, finer-grained companion observable is the detector-event distribution `p(y)`.
- **Probe richness (r) / calibration ladder `C_cal(r)`**: the ordered family of calibration contexts B calibrates over, growing from `r=0` (a single repetition-memory circuit) through multiple rounds/bases (`r=1`), active/enhanced local probes (`r=2`), Clifford sandwiches/basis-rotated probes (`r=3`), to `r=4` (coherent/non-Clifford-sensitive, phase-sensitive probes). The same local channel slot is reused across all of them so context diversity breaks the observational alias quotient. B reports counterfactual validity as a function of `r`.
- **Pauli-shadowing**: the loss of coherent/non-Clifford channel information that occurs when calibration fits only low-order moments (detector marginals and pairwise correlations) — which a stochastic Pauli channel already reproduces — instead of the full observation likelihood `p(s, m | c)`. Avoided by calibrating on exact Born-rule observation-NLL; moment matching is therefore a negative-control baseline, not the calibration target.
- **Numerical floor**: floating numerical floors, thresholds, and probability leftovers use `qec_twin.numerics.NUMERICAL_ZERO == 1e-12` instead of exact `0.0`. This value survives square/cube operations in GPU float32. It does not apply to structural zeros such as Pauli matrix entries, bit values, integer indices, counts, labels, or genuinely absent artifacts.
- **Controlled teacher**: a sim-only noise model with KNOWN, evaluator-only ground truth (the CPTP
  channel field + the recorded mechanism parameters / Kraus) that emits records; the object the twin
  is validated against. The d3 XZZX leakage teacher is the current instance (`mechanisms`, the
  `outputs/teacher_prereg` builders).
- **Ground-truth anchor**: an INDEPENDENT, exact-or-declared-reduction reference for a record
  statistic — the d3 density-matrix oracle (`forward/exact/qutrit_dm`), a stim Clifford slice, or a
  closed-form identity (`mechanisms/seam_teachers` T-B chain, `hardware/dem_compose` `markov_flip_cov`,
  WG rates) — against which a teacher / carrier is certified. INDEPENDENT means a route that does NOT
  share the carrier's implementation (anti-circular: a check vs the engine's own oracle is not an
  anchor).
- **Certification (certify)**: scoring a controlled teacher's (or the carrier's) emitted records
  against the ground-truth anchors → an epistemic ledger (per (anchor, statistic): value, band, class
  (a)/(b)/(c), verdict), with first-class negative controls. Evaluator-only (`audit/certify`).

## Claim Boundary

The long-horizon target is a twin that is simultaneously faithful, interpretable,
useful to decoders, cross-context generalizing, drift-predictive, and identifiable
— the four capabilities recover / understand / manipulate / predict (ADR 0005).
CPTP/GKSL parameterization is one constraint mechanism, not the claim by itself.

Operationally, the desired endpoint is not just a generator that reproduces
syndrome samples. The desired endpoint is a mechanism-conditioned noise simulator
with actionable knobs: change a recovered mechanism strength, remove a noisy
location, perturb a drift component, or generate rare failure cases, then predict
the effect on visible statistics, logical error, decoder priors, or calibration
priorities. Current replay metrics such as NLL, moment MAE, and covariance
Frobenius distance are evidence for distributional fidelity; they become
engineering value only when tied to counterfactual mechanism interventions and
decoder-facing utility.

The current implemented evidence package studies sample efficiency, compression,
quotient-aware recovery, and controlled-catalog physical-mechanism observations.
Mechanisms are implemented as unitary/Kraus/readout
definitions, but the established learner does not yet learn an arbitrary
CPTP/GKSL channel family by construction. As of 2026-06 an exact CPTP physical
substrate (the twin's channel substrate, `qec_twin.forward.cptp_channel`,
`forward/exact/circuit_sim`, and `forward/exact/rep_code`) is an active small-scale build toward the
interventional twin; it is a capability substrate, not a validated twin, so the
claims below still stand. The package does not claim unsupervised latent
mechanism discovery, real-hardware ground-truth mechanism recovery, Born-rule
likelihood, context-conditioned amortization, OOD transfer, temporal drift
tracking, decoder utility, or a complete validated twin across the four
capabilities (recover / understand / manipulate / predict).
