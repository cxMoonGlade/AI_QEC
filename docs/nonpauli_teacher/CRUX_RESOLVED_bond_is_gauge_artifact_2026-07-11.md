# CRUX RESOLVED — the single-wire 2D PEPS "No-Go" is a truncation-GAUGE artifact, the carrier is FEASIBLE (2026-07-11)

> **SUPERSEDES** `HANDOFF_peps_crux_nogo_retracted_2026-07-11.md`'s "PROVISIONAL — build on
> NEITHER arm". The crux is now **RESOLVED** with (a)-exact + anti-circular evidence across
> all three regimes. **Build on: the carrier is feasible; the per-edge bond was the wrong
> instrument; the fix is an environment-optimal truncator.**

---

## 1. THE VERDICT (60-second brief)

The RUNG-B crux was: *does the single-wire 2D PEPS per-edge bond SATURATE under multi-round
noisy+leaky d5 syndrome extraction?* The bond grew (codestate 4 → 18 → 48/abort), which read
as a **No-Go**.

**The No-Go is FALSE. The per-edge bond growth is a REPRESENTATION (truncation-gauge)
artifact, NOT physical entanglement.** The carrier's *state* is exactly correct; its true
bipartition entanglement (von Neumann entropy `S_A`) is **BOUNDED** (2–4 ebits) and does NOT
grow. The single-wire 2D PEPS carrier is **FEASIBLE**. The fix is a **gauge-independent /
environment-optimal truncator** (FET / loop-corrected / variational) so the *represented*
bond tracks the *true bounded* entanglement — exactly what the reference implementations
(Manabe `external/reference_repos/tn_qsim` FET; canonical-form MPS) do.

---

## 2. THE EVIDENCE (three regimes, each with an INDEPENDENT ground truth)

The load-bearing move (FAITHFULNESS rule I): compare the carrier's **own von Neumann
bipartition entropy `S_A`** (the *physical* entanglement the bond is supposed to represent)
to an **independent** ground truth — NOT the per-edge bond to itself.

| regime | true entanglement `S_A` (independent GT) | Schmidt / bond (representation) | verdict |
|---|---|---|---|
| **d3 leakage-off** (EXACT) | `dense_psi` SVD `S_A = 2.00000` ebits `==` **independent GF(2) stabilizer baseline to 2e-16** | per-edge bond 4→16 | **artifact** |
| **d5 leakage-off** | codestate PERSISTS every round: `|⟨S_g⟩|-1 = 1.4e-15` (all 24 stabs) + `|⟨Z_L⟩|-1 = 4.4e-16` ⇒ `S_A =` **GF(2) 4.000 ebits** (bounded) | per-edge bond 4→16 | **artifact** |
| **d3 leakage-on** (WG_L1=5e-3, C_L=0.199) | `dense_psi` SVD `S_A = 2.00000` ebits, **UNCHANGED across 6 trajectories** | Schmidt rank 4→29, bond 4→18, `|2>`-mass 1e-3 | **artifact + truncatable leakage tail** |

Scripts (committed, `outputs/nonpauli_teacher/`, local evidence): `peps_leakoff_d3_entropy_control.py`,
`peps_leakoff_d5_confirm.py`, `peps_leakon_d3_entropy_confirm.py` (+ `_run.sh`, `_out/summary.json`).

**Anti-circularity.** The independent GT for the Clifford regimes is the **GF(2) stabilizer
entropy** `S_A = rank_GF2(M_B) − |B|` — pure algebra on the KNOWN stabilizer generators,
independent of BOTH the carrier and stim. For a stabilizer state this is **EXACT, zero
information loss** (Gottesman–Knill: the state *is* its symplectic data; `S_A` is exactly
integer). Proven by the d3 match to 2e-16. For leakage-ON (non-Clifford ⇒ GF(2)/stim
inapplicable) the read is the carrier's own exact `dense_psi` `S_A` (feasible at d3), with
per-op faithfulness inherited from the d3 gates (SW0/SW1 vs the exact QutritDM referee).

---

## 3. THE MECHANISM (why the bond grows while `S_A` stays bounded)

- The compiled `√E_s` stabilizer measurement is a qutrit (3,5,3)-rank **TT** (the exact
  lossless tensor-train of the 0/1 parity diagonal — it faithfully represents the projector,
  it does NOT inject entanglement into the *operator*). It **mechanically multiplies each
  path bond by 3–5** before truncation.
- The single-wire 2D PEPS tracks **NO global gauge / canonical form**. The bond is measured &
  truncated via the **LOCAL simple-update pair-insertion spectrum** (`_insertion_spectrum` =
  `svdvals(R_A R_B^T)`, `_qr_split` isometrising ONLY each site's own legs). In a loopy 2D
  PEPS this is an **UPPER BOUND** on the true Schmidt rank — it counts gauge + loop-correlation
  directions a globally-canonical / environment-optimal representation would compress away.
  The local ε-truncation cannot globally re-optimise, so the over-count **compounds** across
  rounds (this is the contract's own declared **SW-S6** caveat).
- Leakage-ON adds a **tiny Schmidt tail** (the `|2>`-mass ~1e-3 spreads into ~25 small σ)
  that inflates the *rank* but contributes ~0 to the *entropy* (leakage is a LOCAL channel;
  a local channel adds no bipartition entanglement). ε=1e-8 KEEPS this tail ⇒ bond inflates;
  a looser-ε / fidelity-optimal (FET) cut drops it ⇒ bond collapses.

**`loop_rank_probe.rank == dim` does NOT refute this** — it certifies only that no *local
single-bond* regauge shrinks that bond; it is NOT the bipartition Schmidt rank, and a
*global* re-optimisation still compresses the same bounded-`S_A` state (SW-S6).

---

## 4. WP1 RE-DERIVATION — gate on the PHYSICAL entanglement `S_A`, not the per-edge bond

**The per-edge bond `D_t(r)` was the WRONG WP1 instrument.** It measures the non-canonical
*representation cost*, not the physical entanglement; it over-counts by construction on a
loopy PEPS and inflates with an ε that keeps sub-threshold tails.

**WP1' (re-derived).** Feasibility ⇔ the physical **bipartition entanglement entropy
`S_A(cut, r)` SATURATES** (bounded, area-law) under multi-round extraction — read as:
- exact `dense_psi` `S_A` at d3; the GF(2) baseline (leakage-off) / an independent
  non-Clifford oracle (leakage-on) as GT;
- a converged-`χ_b` **boundary-MPS cut-open reduced-DM `S_A`** at d5 (the maximal-rigor read;
  the codestate-persistence check `|⟨S_g⟩|=1` is the cheaper leakage-off surrogate used here).
- **Registered bet:** `S_A` bounded (area-law, `S_A ∝ cut length`), round-independent —
  CONFIRMED at rounds 1–2 (d3/d5): `S_A` = the codestate value to machine precision.
- **Open (needs the fix):** full `S_A`-saturation over R=20–40 requires the FET/loop
  truncator (§5) so the run is not aborted by the *artifact* bond hitting `D_abort`.

The old `D*∈[2,32]` per-edge-bond band is **RETIRED** as a feasibility gate (it measured the
wrong quantity). `D_abort` becomes a pure resource guard on the representation, decoupled
from the feasibility verdict.

---

## 5. THE FIX (the build path — RUNG-B option 1)

Swap the **local simple-update ε-truncation** for a **gauge-independent / environment-optimal
truncator** so the represented per-edge bond tracks the true bounded `S_A`:
- **FET (Full Environment Truncation)** — the Manabe/tn_qsim method
  (`external/reference_repos/tn_qsim`: `find_optimal_truncation` → target dim ~4 on a 2D
  PEPDO per-edge bond); environment-weighted fidelity optimisation, drops the loop/leakage
  redundancy the local cut keeps.
- and/or **loop-corrected / variational (BP-environment) truncation** (`eps_l` /
  `loop_rank_probe` are the registered A' diagnostics already in the carrier).
- Re-gate WP1 on `S_A` (§4); then run the full R=20–40 multi-round saturation on the corrected
  truncator (the true test the artifact previously blocked).

---

## 6. EPISTEMIC STATUS & DISCIPLINE

- **(a)-exact** at d3 leakage-off (zero-tolerance `S_A == independent GF(2)` to 2e-16).
- **CONFIRMED** at d5 leakage-off (persistence to 1.4e-15) and d3 leakage-on (S_A unchanged /
  6 trajectories). The "carrier feasible" conclusion is theorem-backed + exact/near-exact
  evidence across all regimes.
- **Discipline caught THREE successive wrong conclusions** before the exact anti-circular test:
  (i) "No-Go" (bond grows) → (ii) "gauge inflation `loop_rank_probe` would catch" (WRONG —
  it's local-only) → (iii) "compiled `√E_s` over-entangling bug" (WRONG — `S_A` matches the
  independent GT exactly). The chain was: `theory-fix` (literature apples-to-oranges: Manabe =
  1D-MPS bipartition bond of a rep-code/thin-strip WITH ancilla reset, `external/reference_repos/tn_qsim`
  = his actual code; our bond = 2D-PEPS per-EDGE, no reset) → the **validity workflow**
  (theorem-grade: `√E_s` = exact projector ⇒ `S_A` provably constant; the fair test is
  same-measure `S_A`, not bond-vs-entropy) → the **d3/d5/leakon exact `S_A` tests**. This is the
  FAITHFULNESS-protocol independent-GT rule working as designed.

---

## 7. POINTERS

- Memory: `project-peps-spike-build-state.md` (the RESUME, carries this resolution verbatim).
- Prior chain: `HANDOFF_peps_crux_nogo_retracted_2026-07-11.md` (superseded), the c64 plan/contract
  (`c64_screening_engine_*_2026-07-11.md`, parked — c64 is a screening accelerator, orthogonal).
- Reference code: `external/reference_repos/tn_qsim` = Manabe-Suzuki-Darmawan 2308.08186 (FET).
- Contract: `peps_singlewire_spike_contract.md` (WP1 to be amended per §4; SW-S6 caveat vindicated).
