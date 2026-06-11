# forward/scalable — scalable forward backend (first content: the C1 composed-carrier arm)

Reserved for the >50-qubit forward model that replaces `forward/exact` beyond the
density-matrix wall. **Status (2026-06-10):** ADR 0008 picked the **C1 composed
architecture** (DEM/HMM bulk + window-exact CPTP coherent corrections) as the
conditionally-admissible shortlist; this module now holds its first real content —
the **seam-test-scale composed-carrier arm** (ADR 0008 C3, seam-test
pre-registration item 3 in `docs/metric_results.md`). The d=5/d=7 bulk engine
(DEM/HMM bulk; dMLE-TN as bulk engine + mandatory baseline) is NOT built yet and
stays gated on the seam-test verdict (K1).

**Contract.** Same `forward` contract `context c → p(s,m|c)`: `composed_strip_law`
returns the exact-Born strip observation law for a strip context, so
`calibration` / `knobs` / `audit` patterns apply unchanged (`fit_composed_carrier`
is the `calibration.nll.calibrate` loop on strip observations; `do_on_*` follows
the `knobs` channel-level discipline). The channel object and the four
capabilities stay backend-agnostic.

## The declared seam composition rule (the ONLY approximation in the arm)

Two repetition-code windows, each with its own checks; **no check straddles the
seam** (declared tiling `two-window-v1`; tiling is family design — a
seam-straddling re-tiling is a second registration). The carrier's strip state is
constrained to the product manifold `rho_L ⊗ rho_R`; in-window slots evolve
EXACTLY (`forward/exact` density-matrix engine per window). The seam slot
(Kraus stack on the seam pair) is applied at the H2 placement
`[ (prod_i E_i) ; E_seam ]^repeats` then extraction — **never commuted past
extraction** — through the pair of synchronous conditional reductions

```
Phi_L[sigma_R](rho_L) = Tr_R[ E_seam( rho_L ⊗ sigma_R ) ]
Phi_R[sigma_L](rho_R) = Tr_L[ E_seam( sigma_L ⊗ rho_R ) ]
```

where `sigma_L, sigma_R` are the two windows' record-averaged reduced seam-qubit
states, snapshotted together before either update. Each reduction is CPTP by
construction (`seam_conditional_reduction`). The strip law is the branch product
of the window laws. Dropped (tier-3 `B_misspec`, functional-indexed `B_carrier`,
never folded into `eps_log`): cross-window record/state correlation + the
record-conditioning of the seam action. With an identity/absent seam slot the
rule is exactly the identity, so the composed law equals the whole-strip
`forward/exact` oracle to float64 round-off — the zero-seam exactness pin.

## Module map

- `composed.py` — `StripSpec`/`StripContext`/`StripObservations` (the thin
  instrument interface), `seam_conditional_reduction`, `composed_strip_law`,
  `StripLaw`, the declared record/code conventions (`split_strip_record`,
  `window_joint_codes`, `strip_observations_from_records`), exact Born-NLL
  scoring (`strip_cross_entropy`/`strip_joint_kl`), `ComposedCarrier` with the
  W2-gated class manifest (`CarrierManifest` — the gate must run BEFORE any fit)
  and channel-level `do_on_seam`/`do_on_location`, and `fit_composed_carrier`
  (label-free; observations only — isolation contract).
- `marginals.py` — fit-free bunching functionals from two-block marginals of the
  stationary carrier law: `r_det_lag` (R_k) and `t3_triple` (T3). Record
  convention DECLARED: data-record-chain (D5↔K2 pin); attribution lags k ≥ 2.
- `pins.py` — structural pin callables (normalization, zero negative mass,
  fixed point ≤ 1e-9, seam-reduction TP, T-A Pauli-ablation R=1, unital-diagonal
  R=1, zero-seam exactness ≤ 1e-10) + `CarrierErrorAccounting` (`eps_log` =
  float64 round-off only; `B_carrier` = measured seam residuals, functional-
  indexed; two books, never merged).

Executable spec: `tests/test_carrier_seam_composition.py`. Production seam-test
fits/runs are reviewer-gated and GPU-only (project rule); the tests there are
toy-scale pins and a clearly-labeled smoke fit.

**Boundaries.** Isolation contract absolute: the carrier consumes only
observations (`StripObservations`); teacher channels/parameters are
evaluator-side and never enter the fit path. Scalability beyond the seam-test
strip (the bulk engine, window fleets, d=5/d=7) is deferred ADR 0008 work — no
claim past the controlled seam-test scale issues from this module.
