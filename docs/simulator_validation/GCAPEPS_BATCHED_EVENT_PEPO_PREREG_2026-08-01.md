# GCAPEPS batched-event PEPO — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-08-01. Predictions written BEFORE any A/B run; a miss is
a finding, not a re-fit. Delta-closure: `.scratch/gcapeps-batched-pepo/theory/CLOSURE_PACKET.md`
(closed, per-event scope). Design screens (nonclaim): `.scratch/gcapeps-batched-pepo/screening/`.

## -1. Question charter

- **Decision + consequence:** whether the GCAPEPS residual update applies each realized
  collision event as ONE exact four-term tree PEPO — replacing three sequential
  two-term bond-2 trees and their two inter-axis truncations — as an opt-in carrier
  lane. Consequence: 3× fewer truncation events per event, removal of the v1-closure
  caveat that truncating between axes de-describes the exact partial-SWAP, and the
  literal McCloskey unitary applied with closed coefficients (no phase composition).
- **Plausible attack + anchor:** dense oracle at n=14; the construction is an instance
  of the already-PASS-reviewed project theorem (no new mathematics is at risk); GF(2)
  screens cross-validated against the review's split-cost model (1069 = J exactly).
- **Alternative formulations + invariants:** status quo (three bond-2 trees) is the
  A/B control; sub-round rank-budget grouping is the registered extension (blocked on
  its 2^rank derivation + control); invariant: the lowering is exact before
  compression, and the emitted record is unchanged.
- **Kill condition:** the core bet inverted — batched measurably worse than sequential
  at equal cap (P2 below) — kills per-event batching as an accuracy lever (it may
  survive as a wall-clock lever only if fidelity is within noise); an exact-lowering
  validator failure kills the implementation, not the theorem.
- Selection warning acknowledged.

## 0. Grounding ledger

| sub-axis | mechanism source | observable source | reading note / artifact | in-repo reuse |
|---|---|---|---|---|
| collision primitive is one unitary | McCloskey–Paternostro 1402.4639v3 Eq. (1); SWAP = (I+XX+YY+ZZ)/2 printed in the v1 closure §2 | — | `mccloskey_paternostro_collision_1402.4639v3_source_review.md`; `GCAPEPS_FINITE_MEMORY_BOND32_LITERATURE_CLOSURE_2026-07-29.md` | fixture gate definitions |
| r-term tree PEPO, exact closure, whole-gate theorem | project theorem packet (PASS-reviewed): Lemma 3 Eqs. (8)–(9), Lemma 4 Eqs. (10)–(11), Theorem 1 Eqs. (11a)–(13) | — | `GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md` (SHA 7f5ec9c7…) + independent review report | fork `pepo.py` two-term construction generalizes |
| whole-gate-through-frame precedent | Liu–Clark 2412.17209 Sec. II Eqs. (1)–(2); Masot-Llima STN Main results item (2) + SM III Eqs. (40)–(42); Fröhlich 2607.01323 Sec. IV.C (aI+bP bond-2 MPO); GCAMPS direct application | — | admitted notes | — |
| workload structure | project screens: rank exactly 2 for 57/57 (P0) and 29/29 (X8) events; splits 1069→838; trunc events 171→57 | — | `.scratch/gcapeps-batched-pepo/screening/` (verifier-lineage instruments) | screening machinery |

## 1. The mechanism

For each realized event at rung (i, w+i) with angle γ and Clifford prefix C:

```
U_event = C† (cos γ·I + i sin γ·SWAP_{i,w+i}) C
        = (cos γ + i·sin γ/2)·I + (i·sin γ/2)·(Q_XX + Q_YY + Q_ZZ),
  Q_a = C† P_a C (signed pullbacks; conjugation permutes Pauli words ⇒ exactly r = 4
  nonzero coefficients, class (a))
```

Lowered per Theorem 1 on any connected tree containing
W_U = supp(Q_XX) ∪ supp(Q_YY) ∪ supp(Q_ZZ): copy tensors enforcing one global 4-valued
label at EVERY tree vertex including the root; common local factors B_v retained at
routing vertices (the reviewed Lemma-3 repair); coefficients at the root only; bond 4
on tree edges, 1 elsewhere. Compression then proceeds through the existing per-edge
machinery unchanged (one pass instead of three). Opt-in carrier lane following the
`degenerate_boundary` plumbing pattern; default off = current behavior bit-identical.

## 2. Metric binding

- Existing ledgered instruments only: complete-state fidelity vs the dense oracle,
  BLP objects, split/doubling ledgers, pullback weight beside every fidelity number
  (anti-degeneracy, spec §0b.6). No new metric.
- Forbidden proxies: discarded-weight totals as a fidelity claim (v1-closed
  limitation); plan-level split counts as an accuracy claim (they are class (a)
  combinatorics, reported separately).

## 2a. Predicted observables (frozen)

On the r4 calibration cell (`calibration-g2-s2-w7-r4-a3-p3of4`, inputs 1 and 2, cap
32, shipped wholesale policy, thread count 1, with the degenerate-boundary trim ON in
both arms for determinism):

- **P1 (class (a), combinatorial):** batched truncation events = number of realized
  events (r4 cell: 57 → per-round ledger counts match the screen exactly); sequential
  arm = 3× that. Doubling events: batched ≈ 838-scale vs sequential 1069-scale on the
  r10 cell family (exact per-cell numbers from the plan ledger before any state run).
- **P2 (class (b), THE core bet):** complete-state infidelity of the batched arm is
  no worse than the sequential arm at every checkpoint:
  `1-F_batched ≤ 1-F_sequential` (pass condition), with predicted direction a strict
  improvement driven by fewer, better-conditioned truncations. A miss (batched worse
  by more than the thread-invariance floor 1.2e-15 at K ≤ 6 scale, or by > 5% relative
  at the shipped policy) is a finding that kills the accuracy claim.
- **P3 (class (c) gate):** wall-clock of the batched arm ≤ 1.5× sequential (bigger
  single SVDs, three-fold fewer events); report both algorithm-only and
  evidence-inclusive timings per v1 discipline.
- Statistic the literature proves insufficient: local discarded weight (not a global
  error bound; v1-closed).

## 2b. Disconfirmation surface

Strongest competitor: the three sequential truncations may act as beneficial
regularization at the shipped wholesale policy (the review measured that *some*
intuitive "fixes" hurt: coefficient-weighted gauges −2%..−81%). The A/B at equal cap
and equal policy separates the readings directly; P2's band is two-sided by design.
Sequential-arm superiority on ANY cell is reported as-is.

## 3. Independent ground truth

- Dense oracle (numpy+stdlib, import-firewalled) for every fidelity number.
- **Exact-lowering validator** for the 4-term PEPO: contract the constructed PEPO
  against dense `C† U_MP C` on the carrier graph at the working sizes before any
  compression; tolerance 1e-12 (complex128).
- GF(2) plan ledger (event count, union supports, per-edge labels) cross-checked
  against the review-validated cost model.

## 3a. Constraint ledger + corruption falsifiers

| constraint | exact assertion | falsifying test | deliberately broken input | evidence test trips |
|---|---|---|---|---|
| exact lowering (I1) | `max\|PEPO_contracted − dense\| ≤ 1e-12` per event | validator above | sign flip on one Q term; wrong root coefficient | to demonstrate pre-run |
| Lemma-3 routing-vertex factor (the reviewed counterexample) | routing vertices carry the common factor B_v, not identity | validator on an event whose routing vertex sits inside a nonidentity common factor | force identity at a routing vertex | must reproduce the review's counterexample failure |
| single-axis degeneration | family-1 cells (one axis per event, r=2) reduce the batched construction to the existing two-term path | bitwise equality of ledgers and states on a family-1 cell | — (structural) | equality is the test |
| γ=0 no-op | batched event at γ=0 is the identity | bitwise state invariance | γ=0 with corrupted coefficient must NOT be identity | to demonstrate pre-run |
| record invariance (B-5) | emitted record semantics unchanged; fixture, masks, inputs untouched | record-level diff batched vs sequential arm | — (structural) | equality is the test |
| exactness at unlimited cap | `max_bond=None` gives F = 1 to machine precision in the batched arm | v1 control pattern | — | inherited control |
| determinism | both arms run with trim_cluster ON; same-thread bit-reproducibility | rep-pair check | — | inherited from the thread-fix validation |

## 4. Bounded simplifications

- A/B on the frozen calibration cell(s) at thread 1 is an engineering comparison; no
  claim transfers to other policies, fixtures, or to the v1/v2 registered experiments
  until their preregs adopt the lane by amendment.
- Sub-round grouping is OUT of this prereg (blocked on its 2^rank derivation +
  control, registered debt in the closure packet).

## 5. Epistemic status

- (a) exact: the r=4 coefficient identity; Theorem-1 instance; P1 combinatorics;
  validator equalities.
- (b) band: P2 (the core bet).
- (c) gates: P3 wall-clock; go/no-go controls.
- Headline verdict PROVISIONAL until an independent rereview of this prereg passes
  (v1 pattern) and the A/B runs on the registered cells.

## 6. Build org

- Fork implementation behind an opt-in gate key (pattern: `degenerate_boundary`),
  generalizing the two-term `pepo.py` construction to r-term with a ledger schema
  bump; the sequential path stays byte-identical when the option is absent.
- A/B harness in `.scratch` first; landing gated on owner diff review; no committed
  main-repo surface adopts the lane in this prereg's scope.

## Gate

premises closed? **yes** (closure packet, per-event scope; the construction is a
PASS-reviewed project theorem) | standard metric bound? **yes** (v1-ledgered
instruments, no new metric) | predictions frozen? **yes** (P1–P3) | independent GT?
**yes** (dense oracle + exact-lowering validator + plan ledger) | constraint
falsifiers registered? **yes** (7 rows; 3 to demonstrate pre-run incl. the reviewed
Lemma-3 counterexample) | simplifications bounded? **yes** | controls registered?
**yes** | **preregistration gate: pass** — execution blockers: the pre-run corruption
trips, and an independent prereg rereview before the first registered A/B.
