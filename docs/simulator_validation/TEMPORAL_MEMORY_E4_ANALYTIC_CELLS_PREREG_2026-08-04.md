# E4 analytic record-law cells (RTN + Gaussian dephasing) — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-08-04. Registered BEFORE any derivation writing or numerical run.
Closure: `outputs/temporal_memory_survey_2026-08-04/E4_CLOSURE_REPORTS.md` (C-1..C-3; C-1 gold
anchor PDF-opened; C-2 source-verified-direct; C-3 pixel-verified) + the in-turn check that PRX
Quantum 7, 020351 (SSCS, arXiv:2509.22073) is correlator-level spectroscopy, not a record-law
scoop. Deliverables: two ASSEMBLY notes (honest priority framing per closure), verified
oracle-grade reference scripts, result doc. No `src/**`.

## -1. Question charter

- **Decision + consequence.** Produce the two closed-form analytic record-law cells the survey
  identified (04F-L4) with correct attribution, machine-verified against independent oracles and
  published anchor identities. Yields: (i) an independent ANALYTIC oracle family for the E1/E2
  falsifier ecosystem (structure- and code-path-independent of O1/O2); (ii) two production cells
  where `EVALUATE_FUNCTIONAL` is closed-form for any N; (iii) survey-record errata discharged.
- **Priority landscape (frozen from closure — the honest claims):**
  - RTN cell: endpoint-resolved kernel is PUBLISHED (Cheng–Wang–Joynt PRA 78, 022313 (2008),
    transfer-matrix solution, Eqs. (3)–(8); BGA NJP 11, 025002 Eqs. (30)–(32) state-resolved
    equations; Ramon PRB 92, 155422 Eq. (4)). Claimable increment [new]: the exact joint
    N-outcome record law as an O(N·2²) endpoint-kernel matrix product with QEC Record framing —
    not found within declared scope as of 2026-04 (pressure citations: Wudarski et al. PRApplied
    19, 064066 = same protocol, 1/2/3-point only; Jin–Ye–Ma 2601.18290 two-point transfer
    matrix).
  - Gaussian cell: Sakuldee–Cywiński PRA 101, 012314 contains ALL ingredients (Eq. (6)
    conditional independence given trajectory; Eqs. (7)–(11) n-point correlators = Walsh
    coefficients; Eq. (19) the 2^{−n} sign-vector sum; Eqs. (22)–(28) single-Gaussian-functional
    closed forms, recovering Fink–Bluhm at n=2). Claimable increment [assembly lemma only]: the
    Walsh inversion writing the normalized joint law P(m) = 2^{−n}Σ_S(Π_{k∈S}m_k)·C_S — stated
    as OUR lemma citing their equations, never attributed to them.
- **Kill conditions.** (K1) any anchor-reduction identity fails symbolically (N=1 RTN law must
  equal BGA Eq. (35) exactly; echo variant Eq. (41); n=2 Gaussian must equal Fink–Bluhm
  Eqs. (2)/(4)) — halts the note, wrong derivation or wrong convention. (K2) numerical oracle
  disagreement beyond declared gates. (K3) discovery of a published joint-law statement
  (converts increments to citations; work continues as verification).

## 0. Grounding ledger (conventions pinned by C-3, binding)

BGA: γ = per-direction switching rate; telegraph correlator decays as e^{−2γ|t|}; v = full
angular-frequency modulation (phase velocity ±v); stationary unbiased fluctuator init (½,½);
Eq. (35)/Eq. (41) verbatim as pixel-verified. Fink–Bluhm: χ± both live in Eq. (4); Eq. (5) is
the GaAs spectral model (survey record corrected); protocol = re-prepared single-shot σx Ramsey;
Gaussian zero-mean, stationarity implicit. Registered errata to `04F` L4: (e1) Fink–Bluhm
"Eqs. (4)–(5)" → Eq. (4); (e2) Layden–Chen–Cappellaro correction order O(t^q), q = 2^{n−1}−1
(survey's 2^n−1 wrong), and the fluctuator there is quantum multi-level with incoherent jumps;
(e3) BGA conventions as above. Citation-hygiene debts: SC 1907.01784 equation numbers vs
published PRA PDF (2-min check before external writeup); Fink–Bluhm PRL supplement unopened;
Kubo/Anderson 1954 paywalled (SECONDARY only).

## 1. Registered targets

- **A1 (RTN record law, [new assembly])**: For the declared cell — one qubit, pure dephasing by
  one symmetric classical telegraph (γ, v), N Ramsey blocks (prepare |+x⟩, evolve τ_k, projective
  σx measurement, outcome-independent re-preparation; block gaps δ_k declared) — the joint law is
  `P(m_1..m_N) = 1ᵀ [ Π_{k=N..1} B_{m_k}(τ_k) · D(δ_k) ] π` with 2×2 fluctuator-space blocks
  `B_±(τ) = ½[T(τ) ± Re K(τ)]`, where T = plain telegraph propagator, K = the endpoint-resolved
  phase kernel (matrix exponential of the published generator, pure-dephasing block of
  Cheng–Wang–Joynt Eq. (6)), D = gap propagator. Derivation note must: state the kernel with
  full attribution; prove the block structure (conditional independence given the telegraph
  path + endpoint sufficiency — the Markov property); reduce symbolically to BGA Eq. (35) at
  N=1 and Eq. (41) for the echo variant; extend to the declared multi-qubit common-fluctuator
  variant (Layden-model classical two-level instance) with parity-check records; map to ECS
  semantics (timing-declared process; time_discretization ledger = EXACT_ZERO; declared trivial
  layout + optional XOR fold).
- **A2 (Gaussian record law, [assembly lemma])**: For declared stationary zero-mean Gaussian
  dephasing with PSD S(ω), N re-prepared Ramsey blocks: the Walsh coefficients of the record law
  are single Gaussian characteristic functionals (SC Eqs. (22)–(25) form; block-filter
  covariance Σ_{kk'}), and the joint law is their exact 2^{−N} Walsh inversion; parity
  functionals closed-form for ANY N (poly per coefficient); full law for small N. Note must:
  attribute per the closure; state OUR inversion lemma with proof (elementary, via SC Eq. (6));
  reduce to Fink–Bluhm Eq. (2) at n=2 symbolically; connect the two-stage sampling route
  (exact circulant-embedding trajectory draw + conditional independent outcomes — the E2
  discipline) as the SAMPLE side; ECS mapping as in A1.

## 2. Metric binding & verification battery

Class (a) rows: anchor reductions (K1 identities, symbolic — sympy allowed as tool, hand-checked
constants); normalization Σ_m P = 1 exact-symbolic; kernel unitarity/stochasticity limits
(v→0 ⇒ product of plain telegraph/coin laws; γ→0 ⇒ quasistatic mixture of deterministic-phase
laws — both derived and checked); positivity of every computed law entry. Class (c) gates:
numerics — matrix-exponential kernel vs high-precision ODE integration (mpmath, tolerance
1e-20) and vs trajectory Monte Carlo (exact telegraph path sampler / circulant-embedding
Gaussian sampler; universal-mixture e-process at α=1e-3, N=10⁵ per cell instance; LR e-process
for corruption runs per the E2 lesson — budgets from exact KLs computed at freeze of the
numeric stage). Corruption falsifiers (each must trip): wrong-γ-convention kernel (γ↔2γ swap —
must break the BGA reduction row); dropped cross-block covariance in Σ (must break Fink–Bluhm
reduction and the e-process); sign-filter corruption in the Walsh inversion (parity relabel —
must break normalization or a declared marginal); layout-identity corruption per E1 C3 pattern.
Forbidden proxy: correlator-level agreement (any fixed order) may not stand in for the joint-law
claims — the whole point of the cells is the N-outcome object.

## 3. Independent ground truth

Published anchor identities (pixel-verified, conventions pinned); high-precision ODE oracle;
exact trajectory MC (telegraph paths piecewise-exact; Gaussian via circulant embedding with PSD
check); for tiny N additionally an independent dense instrument-chain evaluation with the
fluctuator as declared memory (O2-pattern, discrete-jump-free via the exact kernel — authorship
disjoint from the note-writers' scripts).

## 4. Bounded simplifications

None in the analytic laws (continuous-time exact; no truncation). MC uncertainty = sampling
ledger; mpmath tolerance declared; symbolic steps carry no floating error.

## 5. Epistemic status

(a): anchor reductions, normalization/limit identities, the two laws once derived+verified
(enumerated small-N objects). (b): none registered (no magnitude bets needed — everything is
exact or gated). (c): e-process/ODE-agreement gates. Headline: "two analytic record-law cells
VERIFIED and available as oracle family + production EVALUATE_FUNCTIONAL cells" — PROVISIONAL
until un-led review; increments claimed exactly as frozen in §-1 priority framing, no more.

## 6. Build org

Note-writers: two independent agents (A1, A2). Flaw-planter + two adversarial checkers (E3
calibration pattern, variants decoupled from originals per E3's design-weakness finding — the
planter rewrites the surrounding prose so the flaw is not diff-recoverable). Numerics builder
(independent; implements laws from the NOTES' final formulas, oracles from the DECLARATIONS).
Un-led reviewer. Artifacts under `outputs/temporal_memory_survey_2026-08-04/e4/`.

---

Gate: `premises closed? yes (C-1..C-3 + SSCS check; priority frozen with honest increments) |
standard metric bound? yes | predictions frozen? yes (class-a identity rows; K1-K3) |
independent GT? yes (anchors + ODE + exact MC + dense small-N, disjoint authorship) |
constraint falsifiers registered? yes (four corruption rows, each must trip) | simplifications
bounded? yes (none in the laws) | controls registered? yes (v→0, γ→0 limits; normalization) |
preregistration gate: pass`
