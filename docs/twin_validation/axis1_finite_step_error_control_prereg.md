# Axis-1 Finite-Step Error CONTROL Prereg — Register the Bound (do not just gate it)

Date: 2026-06-29

Status: theory-first PRE-REGISTRATION (finish-plan Step 5). This document
**registers a falsifiable finite-step error bound as a prediction band** (epistemic
class **b**) for the Axis-1 MCWF carrier, fitting the band constants from the
already-witnessed Step-3 convergence data. It does **not** claim Axis-1 completion,
does **not** introduce a new metric (process infidelity `1-F_e` and Choi trace
distance are the existing standard metrics, `docs/METRICS.md`), and does **not**
promote the bound to a production error bound. A prediction-band miss is a FINDING,
never a silent refit.

> **Headline epistemic guard:** the registered bound is a **prediction band (b)**,
> NOT a theorem (a). Therefore `accepted_as_error_bound = False` stays hard-coded in
> the carrier acceptance policy. No production error-bound claim, no definition, no
> derivation, and no further design may take this band as a premise until it is
> proven a-class. (CLAUDE.md epistemic-status discipline; `docs/METRICS.md`
> "epistemic-status declaration".)

## Why Step 5 exists (relative to Steps 1–4)

| step | object | what it gave |
|---|---|---|
| W-A (Step 1) | connected-cluster Hamiltonian join | overlapping-support H summed before `expm`, killing the S1 split |
| W-B (Step 2) | dense-oracle acceptance gate | the carrier refuses to claim dense-channel evidence it did not earn |
| Step 3 | convergence regression `tests/test_axis1_convergence.py` | WITNESSED `1-F_e ∝ 1/m²` (first-order) and `∝ 1/m⁴` (Strang) vs the independent oracle |
| W-C (Step 4) | de-circularized leakage cert | independent ground truth for the two-site leakage operators |

Step 3 proved the carrier **converges with the right power law and direction**. It
checked the *ratio* per microstep doubling (a shape gate). It did **not** register a
*magnitude ceiling* — i.e. an actual error bound `1-F_e ≤ (something computable from
the substep)`. Step 5 closes that gap: it registers the magnitude bound as a
prediction band and pins, in a test, that the measured infidelity sits **below** the
registered band at a grid of `m`, while the acceptance policy continues to surface
`accepted_as_error_bound = False`.

## Current Evidence (carried from the policy preregs)

- Dense Axis-1 evidence remains the small-window oracle
  `forward.joint_lindbladian.assemble_substep_channel(...)`: one summed same-substep
  generator and one `exp(L dt)`. (a)
- Step-3 `tests/test_axis1_convergence.py` WITNESSED, GPU (RTX 5090), DR+T1 substep,
  `dt=30 ns`: first-order `1-F_e` doubling ratio → 4.00 asymptotically; Strang → ~16;
  the commuting ZZ+T2 positive control `1-F_e = 0` at all `m` (class a). (a/b)
- cert1 (`outputs/axis1_review/agentic_v2/opus/r2_mcwf_channel_vs_jointL_beyondT1.py`)
  and cert4 (`r2_nojump_product_bias_S2.py`) supply the reconstruction harness and the
  S2 no-jump-product mass-residual data (production readout `1-F_e(m=1)=1.2e-2`
  @ `dt=500 ns`, device rates). (a/b)
- The restricted carrier already emits a `restricted_acceptance_policy` keeping
  `claims_exact_joint_lindblad_generator=false`,
  `claims_production_scalable_backend=false`,
  `accepted_as_production_error_bound=false`. Step 5 adds the explicit
  `accepted_as_error_bound=false` flag tied to THIS band's epistemic class. (a/c)

## Grounding Ledger (theory-first; sources READ, not cited-from-memory)

| decision surface | source | project note / code | use here | class |
|---|---|---|---|---|
| Same-substep GKSL target; `L=A+B` cross-term warning | Jaschke, Montangero & Carr, arXiv:1804.09796 (FULL-TEXT read) | `docs/papers/reading_notes/jaschke_open_quantum_tensor_networks_1804.09796.md` | the summed-generator target the bound is measured against; the appendix-A warning that a same-substep coupling must not be split | (a) |
| Second-order Trotter `O(dt²)` global / `O(dt³)` local scaling; non-Hermitian `H_eff = H − (i/2) Σ Lᵥ†Lᵥ` | Jaschke et al. arXiv:1804.09796, Method | reading note above | the order language that fixes the bound's *powers* (first-order ∝1/m², Strang ∝1/m⁴); the joint no-jump propagator the S2 product approximates | (a) |
| Product-formula error-bound language | Werner et al., arXiv:1412.5746 | `docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md` | LPTN gives a *stronger* trace-norm certificate path — explicitly the DEFERRED a-class route; this prereg does NOT cite it as already implemented | (a/c) |
| QEC MPS-trajectory truncation/discarded-weight ledger precedent | Manabe, Suzuki & Darmawan, arXiv:2308.08186 | `docs/papers/reading_notes/leakage_tensor_network_simulation_2308.08186.md` | per-shot trajectory + discarded-weight monitoring shape; not a magnitude bound | (a/c) |
| Process infidelity + Choi trace distance conventions | `docs/METRICS.md` | metric ledger | the two standard metrics the band is expressed in; no new metric introduced | (a) |

**Theory-first confirmation.** The Jaschke note carries a `FULL-TEXT read` provenance
header (PDF → txt, 1649 lines, 2026-06-28). The Trotter order law (`O(dt²)` global at
fixed total time for the second-order split; the `H_eff` no-jump propagator) is read
directly from its Method section. The *powers* in the registered bound are therefore
literature-anchored (a-class grounding for the FORM); the *constants* are fitted from
project data and are themselves b-class (a band, not a theorem).

## Derivation of the bound FORM (the powers are a-grounded; the bound itself is b)

Per microstep of duration `dt_micro = dt/m`:

1. **First-order split (H then collapse).** The leading Lie–Trotter defect generator is
   `G_micro ~ [H, Σ_k c_k†c_k] · dt_micro²` (the commutator of the Hamiltonian step with
   the dissipator's no-jump drift). Accumulated over `m` microsteps,
   `G_tot ~ m · [H, Σc†c] · (dt/m)² = [H, Σc†c] · dt²/m`. Process infidelity is second
   order in the error generator: `1-F_e ~ ‖G_tot‖²/D ~ ‖[H,Σc†c]‖²·dt⁴/(D·m²) ∝ 1/m²`.
   Writing the per-microstep dimensionless small parameter
   `gdt := (Ω·γ)^{1/2}·dt` (the geometric mean of the two competing generator rates —
   the Hamiltonian strength `Ω` and the dissipator rate `γ` that source `[H,Σc†c]`),
   the bound is
   ```
   1-F_e_first_order(m)  ≤  c · (gdt / m)².            [b]
   ```

2. **Strang split (H half, collapse, H half).** The symmetric split cancels the leading
   `dt_micro²` defect, leaving `O(dt_micro³)` per microstep → `1-F_e ∝ 1/m⁴`
   (Jaschke `O(dt²)` global vs `O(dt³)` local maps to one extra order in `m`):
   ```
   1-F_e_strang(m)  ≤  c' · (gdt / m)⁴.               [b, asymptotic m]
   ```
   Strang is pre-asymptotic at small `m` (the `1/m⁴` law only governs once `dt_micro`
   is small); the band is registered for `m ≥ 4`, mirroring how the first-order *ratio*
   gate in Step-3 already excludes `m < 2`.

3. **S2 no-jump-product mass-residual.** The carrier's no-jump branch is the per-term
   sequential product `Π_k (I − ½ dt_micro c_k†c_k)`, which differs from the JOINT
   first-order no-jump `I − ½ dt_micro Σ_k c_k†c_k` by `+¼ dt_micro² Σ_{i<j} c_i†c_i c_j†c_j`
   (cert4 algebra; non-zero only for stacked same-support collapses, e.g. production
   readout T2+RD both `|1⟩⟨1|`). This is an `O(dt_micro²)` per-microstep bias →
   `∝ 1/m²` accumulated:
   ```
   residual_S2(m)  ≤  c'' · (gdt_RD / m)²,            [b]
   ```
   with `gdt_RD := (2 γ_readout_φ)·dt` the readout-dissipator per-substep small parameter.

The FORM (powers 2, 4, 2 and the `gdt` normalization) is anchored in Jaschke. The
CONSTANTS `c, c', c''` are fitted below and are **b-class** — a registered falsifiable
bet, not a theorem.

## Fitted constants (from the WITNESSED Step-3 / cert4 data — CPU arithmetic, no new run)

DR+T1 substep, `dt=30 ns`: `Ω = Ω_π/2` with `Ω_π = π/dt = 0.10472 rad/ns`,
`γ₁ = 1/30000 /ns`. Geometric-mean small parameter
`gdt = (Ω_π·γ₁)^{1/2}·dt = 5.6050e-02`.
(Source of the witnessed `1-F_e`: `outputs/axis1_review/fixes/step3/step3_b/NOTES.md`,
matched-`m` table + first-order `m`-sweep; the test re-derives them live so the fit is
never stale.)

| order | `m`-grid `c_fit = (1-F_e)/(gdt/m)^p` | worst `c_fit` (in-band `m`) | margin | **REGISTERED constant** |
|---|---|---|---|---|
| first-order (`p=2`, all `m≥1`) | 0.123 (m1), 0.106, 0.076, 0.073, 0.073 (m16) | 0.123 | ×1.5 | **`c = 0.19`** |
| Strang (`p=4`, `m≥4`) | 7.17 (m4), 6.34, 6.20 (m16) | 7.17 | ×1.5 | **`c' = 10.76`** |
| S2 residual (`p=2`, production readout) | 0.012 @ `dt=500 ns`, `m=1` | 0.012 | ×1.5 | **`c'' = 0.02`** |

Verification that the registered ceilings hold at every in-band `m` (CPU re-check):
- first-order `c=0.19`: measured ≤ bound at `m = 1,2,4,8,16` (e.g. m=1 `3.86e-4 ≤ 5.97e-4`; m=16 `8.95e-7 ≤ 2.33e-6`).
- Strang `c'=10.76`, `m≥4`: measured ≤ bound (m=4 `2.76e-7 ≤ 4.15e-7`; m=16 `9.34e-10 ≤ 1.62e-9`).
- S2 residual `c''=0.02`, production readout: measured `1.2e-2 ≤ 2.0e-2`.

The Strang band is **deliberately not** evaluated at `m = 1,2`: there the `1/m⁴` law is
pre-asymptotic (`c_fit` = 16.9, 26.3), so a small-`m` ceiling would be physics-blind.
Excluding `m < 4` from the Strang band is the asymptotic-regime declaration, identical
in spirit to the Step-3 first-order ratio gate's `m ≥ 2` asymptotic restriction.

## Registered prediction bands (epistemic class b unless marked)

- **B1 [b] first-order magnitude bound.** For the DR+T1 substep at `dt=30 ns`, the
  carrier's measured first-order `1-F_e(m)` lies **at or below** `c·(gdt/m)²` with
  `c = 0.19`, for every `m ∈ {1,2,4,8,16,32,64}`. A measured value ABOVE the band at any
  in-band `m` is a FINDING (the carrier is worse than the registered first-order law),
  reported, never silently refit.
- **B2 [b] Strang magnitude bound.** For the same substep, measured Strang `1-F_e(m)`
  lies at or below `c'·(gdt/m)⁴` with `c' = 10.76`, for every `m ∈ {4,8,16,32,64}`
  (asymptotic regime). `m < 4` is excluded by declaration (pre-asymptotic).
- **B3 [b] S2 mass-residual bound.** For the production readout substep (T2+RD, both
  `|1⟩⟨1|`) the measured per-microstep no-jump mass-residual `1-F_e(m)` lies at or
  below `c''·(gdt_RD/m)²` with `c'' = 0.02`, for the registered `m`-grid.
- **B4 [a] commuting positive control.** ZZ+T2 (all diagonal) `1-F_e ≤ 1e-6` at all `m`
  (no Trotter defect, no S2 residual). Exact statement (carried from Step-3); if it
  fails, the reconstruction or oracle wiring is broken — stop.
- **B5 [a, claim-discipline] acceptance flag.** The carrier acceptance policy surfaces
  `accepted_as_error_bound = False` for THIS band, because the band is class b, not a.
  This is an exact assertion about the policy ledger: the band is registered and used
  for go/no-go gating ONLY; it is never a production error bound, a premise, or a
  derivation basis. (CLAUDE.md provisional-conclusion corollary.)

## Anti-toy / no-laundering predictions

- **No theorem-laundering:** the band must keep `accepted_as_error_bound=false` and
  `comparison_outcome_is_metric=false`. Promoting the band to an a-class error bound
  requires either a from-scratch operator-norm Trotter theorem with an explicit
  remainder, or the Werner LPTN trace-norm certificate — NEITHER is claimed here. (a)
- **No silent refit:** a band miss (measured > registered ceiling at an in-band `m`)
  must surface as a FINDING in the test failure, not trigger a constant bump. The
  registered constants are frozen by this document; changing them is a new prereg. (b)
- **No metric invention:** `1-F_e` and Choi trace distance are the existing standard
  metrics; the bound is a ceiling on them, not a new scored quantity. (a)
- **No Axis-2 leakage:** this prereg adds no source timelines, memoryful noise, `.dem`,
  or decoder semantics. (a)
- **Anti-circular oracle:** the band is checked against the term-based
  `assemble_substep_channel`, never the carrier's `_hamiltonian_group_gates` grouping
  — a wrong carrier grouping is caught, not mirrored (Step-3 / cert1 idiom). (a)

## Acceptance policy (what the carrier ledger must report for this band)

```
finite_step_error_control = {
  "registered_band": {
    "first_order":  {"power": 2, "constant_c":  0.19,
                     "small_parameter": "gdt = sqrt(Omega*gamma)*dt",
                     "fixture": "DR+T1 dt=30ns", "epistemic_class": "b"},
    "strang":       {"power": 4, "constant_c": 10.76, "asymptotic_m_min": 4,
                     "small_parameter": "gdt = sqrt(Omega*gamma)*dt",
                     "fixture": "DR+T1 dt=30ns", "epistemic_class": "b"},
    "s2_residual":  {"power": 2, "constant_c":  0.02,
                     "small_parameter": "gdt_RD = (2*gamma_rd)*dt",
                     "fixture": "readout T2+RD dt=500ns", "epistemic_class": "b"},
  },
  "accepted_as_error_bound": false,             # class b => NOT a production error bound
  "comparison_outcome_is_metric": false,
  "source_data": "outputs/axis1_review/fixes/step3 + agentic_v2/opus/cert4",
  "bound_form_grounding": "Jaschke 1804.09796 (FULL-TEXT)",
}
```

`accepted_as_error_bound=false` is **load-bearing and non-optional**: it is the explicit
record that a registered band is not a theorem. Promotion to `true` is gated on an
a-class proof and a new prereg.

## Open Risks / Decisions

- The fitted constants are calibrated on ONE substep family (DR+T1) and ONE readout
  family (T2+RD). They are registered bands for THOSE fixtures; a different substep
  (e.g. multi-jump qutrit leakage exchange, cert1 case D/E) may need its own `gdt`
  normalization and its own band. Generalizing the constant to arbitrary substeps is a
  future a-class question, not claimed here. (b/c)
- Production-grade error CONTROL (an a-class bound usable to PICK `m` from a target
  tolerance) still needs the LPTN/MPDO trace-norm certificate or a from-scratch
  operator-norm Trotter remainder. The registered band is a falsifiable *check*, not the
  *control law*. (c)
- The Strang asymptotic-regime exclusion (`m ≥ 4`) is a declared band domain. If a future
  application needs the Strang bound at `m = 1,2`, the pre-asymptotic regime must be
  modeled separately (it is not `1/m⁴` there). (b)
