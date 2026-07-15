# carrier/peps — single-wire 2D PEPS trajectory carrier

**Status: research carrier; full-record faithfulness remains open.** This package is the
**single-wire (pure-state trajectory)** answer to the crux the compiled-geometry
**doubled-wire** DM-PEPO (`carrier/pepo`, retained research carrier) could not close:
does the per-edge bond of a 2D PEPS
stay bounded under multi-round noisy+leaky syndrome extraction (WP1)?

The primary axis is **single-wire vs doubled-wire**, not ancilla. The same compiled
`√E_s` POVM used by the density-matrix carrier is applied
here, but on a **pure-state** carrier — so the ket⊗bra squaring that concentrated
rank onto fresh path bonds (F-SEL-1/F-REC-1) never forms: the TT rank bound drops
from `(2·min+1)²` to `2·min+1` (SF3).

## Scope fences (contract §1.3)
- **S10 compiled/data-register** semantics — NO ancilla qutrits; every artifact
  carries the compiled-semantics label (SW-S1).
- **Arm A only** (the p1c cell); arm C (leak-flag dephase) raises (SW-S2).
- **GPU-only**, torch-cuda-complex128 ALWAYS (SW-S8). `PepsSampler` rejects c64 run metadata
  before execution; the optimization-c64 policy belongs only to the active fused within-cycle
  SV-MC carrier and does not amend the PEPS/FET contract or its tolerances.
- d3 is fully certifiable (state-level vs the exact QutritDM referee; record-level
  vs the per-record DMPathEvaluator route). d5 has **no exact referee** — d5 claims
  are bond/cost only (SW-S4).

## Module map
| File | Bounds |
|---|---|
| `state.py` | `PepsState` (dim-3 phys legs `k{pos}`, bonds `B{p}_{q}`, cuda-c128, ledger); `build_codestate_peps` (pepo steps 1-3 ket layer + unit-NORM finalize, no step-4 fuse — SF1); `dense_psi` (d3 referee bridge, n≤9); local referee-independent gate table (D4) |
| `stab_tt.py` | `SingleWireStabTT` + `stab_tt_singlewire` (the UNSQUARED `√e` diagonal TT, rank bound `(3,5,3)`/`(3,)` — SF3); `apply_stab_branch` |
| `contraction.py` | double-layer `⟨ψ\|Π\|ψ⟩` boundary-MPS reads (SF9 — the pepo column-sweep skeleton reused, only the caps become ket+conj double layer); two-term Born read; §6.2 accuracy instruments (`cross_route_q1`, `chib_doubling_delta`); terminal POVM + exact-P(obs) seam |
| `trajectory.py` | per-shot loop (D7 — the `mps_forward` value contracts on 2D); §6.1 dynamic-ε policy (`TruncationPolicy`, `truncate_*`, `W_max=160`, `D_abort=40`, window-binding invariant); `PepsSampler` packed-record driver |
| `sampling_maps.py` | the three pinned uniform→outcome maps (single source; `sbit_from_uniform`, `terminal_bit_from_uniform`, `leak_branch_from_uniform`); rejected alternative directions are exercised by corruption falsifiers (RT1-B1/B2) |
| `diagnostics.py` | `bond_profile` (SW8 instrument); `eps_l` (§6.3 Rudolph-Tindall loop-correlation BP error — hand-rolled on explicit tensors, no shared code with the known-answer reference); `loop_rank_probe` (WP1 adjudication path A') |

## Reuse / independence
- **Reused from the retained `carrier/pepo` research carrier:** the
  d-generic `PepoLayout` (SF2), the ket-layer chain machinery, the boundary-MPS
  skeleton (`_max_row_bond` / `_row_tag` / fit pattern), the truncators
  (`svd_precut_bond` / `ntu_truncate`).
- **Reused from `carrier.record_fold`:** the carrier-neutral `s_to_det` / `det_to_s`
  temporal detector-record convention.
- **Schedule-host seam:** `PepsSampler` accepts an injected schedule/marshalling host and defaults
  to package-local `carrier.within_cycle.WithinCycleScheduleHost`. Schedule marshalling, WG
  leak-slice construction, headers, and `RunSpec` ownership are package-local. Packed records use
  package-local `carrier.records.PackedShotBatch`; its public record accessor applies the required
  temporal detector fold.
- **Referee-independent (contract §3):** the engine shares NO code path with
  `carrier/exact/qutrit_dm` — all gates/Hadamard are local formulas mirroring the
  `mps_forward` value contract; the referee is imported only in the gate
  scripts/tests, never here. `eps_l` is hand-rolled so the §6.3 known-answer
  reference (an independent dense eigendecomposition) shares no code with it.

## Tests / gates
Registered d3 pytest gates: [`tests/test_peps_spike.py`](../../../../tests/test_peps_spike.py)
(SW0-SW6 + §6.3 `eps_l` known-answers). GPU evidence runs for the chain probe,
record law, cross-carrier byte identity, and d5 resource probes remain separate
scripted executions.
