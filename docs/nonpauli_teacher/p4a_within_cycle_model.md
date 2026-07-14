# P4a within-cycle leakage model — circuit-faithful per-cycle spec (build spec)

> **Object.** The circuit-faithful WITHIN-CYCLE leakage model for the P4a d3 XZZX leakage engine,
> derived theory-first from the raw `circuit_ideal.stim` and confirmed numerically. It replaces the
> current LUMPED per-round model `[all single-qubit gates] → [ONE full-cycle WG leakage] → [measure]`
> (H's folded into `stab_supp_isx`), which OVER-STATES the leaked `|2⟩` population by a large factor
> (the deliverable's "~4×" is the low-R/matched-Y figure; the actual figure is 15× at R=3 with matched
> Y, and grows to ~150× at R=10 for the no-Y engine — see §6). The fix interleaves the leakage with the
> H/X/Y gates at their real circuit positions, so the mid-cycle X echo (and the per-qubit H pattern,
> via `H·X·H = Z`) REFOCUSES the coherent `|1⟩↔|2⟩` exchange.
>
> **Scope.** This is a DERIVATION + SPEC. It does NOT edit mainline (`.cu`, `sv_sampler.py`,
> `qutrit_dm.py`, `xzzx_parser.py`) or `external/`. Build agents (K/H/V per `p4a_build_contract.md`)
> implement it in the kernel + host + DM oracle, commit-gated.
>
> **Precision boundary (2026-07-13).** The within-cycle WG generator, `exp(L/4)` slice,
> four-slice composition check, CPTP checks, gate tables, and codestate are constructed and
> checked in c128. Only `FusedWithinCycleSampler` / `sv_traj_d3_wc` may cast the already-checked
> complex execution tables and codestate to c64, and only for an optimization run marked
> `screening_only`. Final/certification is c128/`c128_candidate`; PEPS/MPS remain c128-only.
> This boundary does not change a scientific tolerance or FET setting.
>
> **Provenance (all from committed scripts, printed evidence):**
> `outputs/teacher_prereg/p4a_within_cycle_derive_parser.py` (per-qubit gate stream + round-invariance),
> `…_czmap.py` (per-qubit CZ-layer participation), `…_calib.py` (split-convention calibration),
> `…_hstudy.py` (H effect on `|2⟩(R)`), `…_hrecon.py` (H/measurement reconciliation),
> `…_confirm.py` (deliverable `|2⟩(R)` + V-reconciliation), `…_audit.py` (anomaly audit + positive
> control + qutip oracle). Anchored to V's `…_p4a_verify_circuit_faithful_leakage.py` `dist+Y` reference.

---

## 0. Epistemic-status declaration (METRICS.md §"epistemic-status declaration")

| Item | Class | Justification |
|---|---|---|
| Per-qubit ordered gate+CZ stream (§1, §2) | **(a) exact** | verbatim from the raw circuit; interior rounds 1..8 byte-identical |
| 4 CZ layers/round; mid-X between CZ2–CZ3; post-M Y; terminal drops Y; first folds init-H | **(a) exact** | stim parse, asserted |
| Per-coordinate CZ-leak geometry is reuse-stable r01↔r10 (same patch) | **(a) exact** | coordinate-keyed comparison, 9/9 nCZ identical |
| `exp(L/4)` slice algebra; siting one slice at every touched CZ layer | **(a) algebra / (c) siting convention** | `(exp(L/4))^4=exp(L)` for the same time-independent project generator; current code compares the full output matrix for one `rho=ket(1)bra(1)` input with shared channel machinery, not an independent full-superoperator oracle; no paper derives this as a physical quarter-CZ channel |
| `H·X·H = Z` refocusing; H's net to identity per round (even count) | **(a) exact** | operator identity, `‖H·X·H − Z‖ = 2e-16`, `‖H²−I‖ = 2e-16` |
| H/measurement reconciliation: **KEEP `stab_supp_isx`** (in-stream H's net to a detector-invariant `Z`; they do NOT rotate the measurement basis) | **(a) exact** | verified on the d3 codestate: drop → X-type stabilizers read 0; keep → `⟨S⟩=+1` all 8 |
| The leakage channel `(θ, g_seep, g_heat)` and WG_L1/WG_L2 regime | **(c) design constant** | registered SWEEP (`qutrit_teachers.py`); evaluator-only; go/no-go siting |
| The `ket(2;R)` target numbers (§5) | **(a) exact GIVEN (θ, g_seep)** | exact 3×3 channel algebra at the registered siting; two independent representations agree `1e-15` |
| "Over-statement factor ~N×" (§6) | **(c) heuristic / reportable** | provisional characterization of the lumped-model error; not a premise |

The model itself is **(a) exact** machinery at a **(c) swept** operating point: given the registered
`(θ, g_seep, g_heat)`, the within-cycle `|2⟩(R)` is an exact channel computation.

---

## 1. The faithful within-cycle structure (per interior round)

Per INTERIOR round the real circuit applies, on each DATA qutrit, the single-qutrit gates at their
positions relative to the **4 CZ layers** (the CZ's themselves are dropped as transport = P4b, but
their leakage point is KEPT — leakage accrues at each CZ, where `DEPOLARIZE2` sits in the noisy
circuit). The global per-round skeleton (TICK layers of one interior round, from the parser):

```
 reset(R, ancilla) → H-layer → CZ-layer1 → H-layer → CZ-layer2 → X(mid-cycle echo)
   → CZ-layer3 → H-layer → CZ-layer4 → H-layer → M(ancilla) → Y(post-M echo)
```

Key global facts (all **(a)**-exact, asserted in `…_parser.py` / `…_czmap.py`):

- **Exactly 4 CZ layers per round** (the 4 leak sub-step layers).
- **The mid-cycle X echo is between CZ-layer 2 and CZ-layer 3** — transversal on all 9 data.
- **The post-M Y is transversal on all 9 data** (an UNCONDITIONAL physical pulse — V proved it is a
  bare `Y q…`, not a `CY rec[…] q` frame correction — so it is IN the leakage path).
- **Interior rounds 1..8 are byte-identical** in per-qubit gate+CZ structure (round-invariant
  interior).
- **The terminal round (last) drops the post-M Y** (it ends in the terminal data readout).
- **The FIRST round folds an extra data-init H layer** (circuit line 24/315: a wider `H` over data
  + ancilla, the logical-state prep), so it is NOT a clean interior round either.

> **r01-vs-r10 caveat (important for "reuse r01 geometry, override R").** r01 and r10 are the SAME
> physical patch (all 9 data coordinates shared), with the SAME per-coordinate CZ-LEAK geometry
> (which/how-many CZ layers each data qubit touches — IDENTICAL r01↔r10, the leakage authority). BUT
> r01's single round is BOTH first (folds the data-init H layer) AND terminal (no post-M Y), so its
> per-qubit **H-slot distribution differs** from a clean interior round (`…_parser.py` §4: CZ-leak
> 9/9 identical, H-slots 4/9 identical). **SPEC RULE: source the per-qubit INTERIOR gate stream from a
> MULTI-ROUND circuit's interior rounds (e.g. r10 round 1..8), NOT from r01's single round.** Handle
> the first round (data-init H) and the terminal round (no post-M Y) explicitly. The §2 table is the
> interior round (from r10).

**Per-qubit refinement (the load-bearing subtlety the prompt flagged).** Each data qubit does NOT
participate in all 4 CZ layers — only **2, 3, or 4** of them (boundary qubits couple in fewer CZ gates
than the bulk). And the **H pattern is per-qubit** (the XZZX structure). The per-qubit gate stream is
the authority (§2), not a uniform template.

---

## 2. Per-qubit gate-sequence table (the parser output — authority)

Verbatim ordered within-round stream per data qubit (from `…_parser.py` / `…_hrecon.py`, interior
round; `CZ` = a leak sub-step, `M` = the stabilizer-measurement boundary). Engine register position =
index into `data_indices` (the metadata data-coord order). **Each qubit has exactly 2 H's per round**,
with the X echo between them → net single-qubit = `H·X·H = Z` (diagonal, detector-invariant; data stays
in the computational basis at M, so `stab_supp_isx` is KEPT — see §4).

| qid | engine pos | ordered interior stream | nCZ | CZ layers it touches | CZ before X | CZ after X |
|---:|---:|---|---:|---|---|---|
| 1  | 0 | `CZ H CZ X H M Y`     | 2 | {1,2}     | {1,2} | {}    |
| 4  | 1 | `CZ H X CZ H CZ M Y` | 3 | {1,3,4}   | {1}   | {3,4} |
| 6  | 2 | `H CZ X CZ H CZ M Y` | 3 | {2,3,4}   | {2}   | {3,4} |
| 8  | 3 | `CZ H X CZ H M Y`    | 2 | {1,3}     | {1}   | {3}   |
| 10 | 4 | `CZ H CZ X CZ H CZ M Y` | 4 | {1,2,3,4} | {1,2} | {3,4} |
| 12 | 5 | `H CZ X H CZ M Y`    | 2 | {2,4}     | {2}   | {4}   |
| 13 | 6 | `CZ H CZ X CZ H M Y` | 3 | {1,2,3}   | {1,2} | {3}   |
| 15 | 7 | `CZ H CZ X H CZ M Y` | 3 | {1,2,4}   | {1,2} | {4}   |
| 18 | 8 | `H X CZ H CZ M Y`    | 2 | {3,4}     | {}    | {3,4} |

The per-qubit H-presence at the three pre-M H-layer slots (pre-CZ1, between CZ1–CZ2, between CZ3–CZ4),
4 distinct patterns across the 9 qubits:

| pattern (H@preCZ1, H@CZ1–2, H@CZ3–4) | qubits (qid) |
|---|---|
| (0,1,0) | 1, 4, 8, 15 |
| (0,1,1) | 10, 13 |
| (1,0,0) | 6 |
| (1,1,0) | 12, 18 |

> **Build note.** The kernel/host/oracle must marshal, per data qutrit, its OWN ordered stream from the
> parsed circuit (not a uniform template). The CZ leak sub-step is applied ONLY at the CZ layers the
> qubit participates in; the X echo is applied to all data at its global slot; the H's at the qubit's
> own slots; the post-M Y on all data (dropped in the terminal round).

---

## 3. Leakage project normalization (TASK 3 — pinned simulation convention)

> **Literature correction (2026-07-13).** `exp(L/4)` is a project normalization/siting
> convention, not a measured physical quarter-CZ channel. See
> [`production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md`](../twin_validation/production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md).

**The project places the normalized slice `exp(L · 1/4)` at every touched CZ layer
(`global_per_cz`).**

- `L` is the WG Lindbladian generator: `H = θ(|1⟩⟨2| + |2⟩⟨1|)`, jump `J_seep = √g_seep |1⟩⟨2|`
  (and optional `J_heat = √g_heat |2⟩⟨1|`), as in `forward.channels.leakage_channel_super`.
- The full-cycle WG channel is `E = exp(L)` (the registered per-round leakage,
  `forward.channels.leakage_kraus(θ, g_seep, g_heat)`). The per-CZ slice is the Kraus of `exp(L/4)`
  (Choi-factorized; `…_calib.py` `leak_frac_kraus(…, 0.25)`).
- **Composition algebra (a-exact inside the declared model):** four exponentials of the same
  time-independent generator satisfy `(exp(L/4))^4=exp(L)`. A qutrit touched in `n_cz_q` layers is
  assigned `exp(L · n_cz_q/4)` by this convention. This does not prove that a boundary qutrit
  physically accumulates exactly that fraction. The current implementation comparison uses one
  `|1><1|` input and compares its full output matrix; both arms share the same channel machinery, so
  an independent full-superoperator corruption check is still missing.
- **Why the project uses `global_per_cz`, not `per_qubit_uniform`.** The real circuit supplies a
  distinct number of CZ-layer touches, so per-touch siting is the sharper hypothesis to test than
  forcing identical per-round totals. The circuit's `DEPOLARIZE2` placement does not establish that
  the same leakage generator or rate applies at each CZ; that physical bridge is open.
- **Calibration anchor (a-exact, gap 0.0).** For the 4-CZ qubit (q10) with the H's turned OFF, this
  model reproduces V's `dist+Y` reference EXACTLY (`…_confirm.py` panel A: `max gap = 0.0e+00`). V's
  `dist+Y` is the special case `n_cz=4, no H`; the H's are the sole remaining difference (§4).
- **Registered siting (c-class, swept).** First-pass central point `θ = 0.07, g_seep = 0.09,
  g_heat = 0.0` → WG_L1 = `2.339e-3`, WG_L2 = `9.047e-2` (in the Miao/McEwen bands). These are SWEPT
  (`THETA_SWEEP × G_SEEP_SWEEP`), not pinned; use `calibrate_theta_for_wg_l1` for an exact target WG_L1.
- **External-library, same-model probe.** The `exp(L/4)` implementation matches a qutip
  `mesolve(L, 0.25)` propagation on `|1⟩⟨1|` to `2.6e-9` (`…_audit.py` panel S4). This catches
  errors on that input; it is neither a full-superoperator certificate nor external physical
  validation of the siting convention.

---

## 4. H / measurement reconciliation (TASK 4 — definitive)

**The H's are LOAD-BEARING for `|2⟩(R)` (they refocus the coherent leak) — but they do NOT replace
`stab_supp_isx`; the measurement basis rotation is SEPARATE and KEPT.**

> ⚠️ **CORRECTION (Agent H, 2026-06-20, verified on the d3 codestate).** The original "REPLACE
> `stab_supp_isx` → pure-Z" below was a derivation slip. The per-round in-stream single-qubit gates compose
> to `H·X·H = Z` — a DIAGONAL phase, detector-invariant on the even-weight stabilizers — so the data is in
> the COMPUTATIONAL basis at M (NOT Z-rotated). A pure-Z read then gives the 4 X-type stabilizers as
> **0 (wrong syndrome)**; keeping `stab_supp_isx` gives `⟨S⟩=+1` for all 8. The in-stream H's affect ONLY
> the `|2⟩` trajectory (net-`Z` is detector-invariant), so applying them AND `stab_supp_isx` is NOT a
> double-count. **Net: the measurement is UNCHANGED (keep `stab_supp_isx`); only the per-round op-schedule
> (interleaved gates+leak) and the `exp(L/4)` leak change.** (R1/R3 below, §8, and the §0 row are corrected to match.)

1. **Each qubit has 2 H's with the X echo between them → the net single-qubit Clifford is `H·X·H = Z`**
   (a DIAGONAL phase; `|2⟩` is H/Z-inert). `Z` is detector-invariant on the even-weight stabilizers (so
   the syndrome is unchanged), and being diagonal it leaves the data in the COMPUTATIONAL basis at M — so
   the measurement still needs its OWN X-support rotation (`stab_supp_isx`). (`…_hrecon.py` R1.)

2. **But the 2 H's are INTERLEAVED with the leak sub-steps** (e.g. q10 = `CZ H CZ X CZ H CZ`), so they
   change the mid-round `|1⟩↔|2⟩` leak exposure and therefore CHANGE `|2⟩(R)` — even though they net to
   identity. The mechanism is `H·X·H = Z` (`‖H·X·H − Z‖ = 2e-16`): when the X echo sits between two
   H's, the effective echo is a **Z-like phase echo**, which REFOCUSES the coherent `|1⟩↔|2⟩` exchange.
   This is exactly the prompt's "the H's change whether the echo is X-like or Z-like for leakage."
   Quantified effect: H-in vs H-out shifts `|2⟩(R)` by up to `8.3e-3` (`…_hstudy.py`).

3. **Measurement reconciliation (corrected — see the box above).** The in-stream H's compose to a net
   detector-invariant `Z`, NOT a basis rotation — so the data is in the computational basis at M and the
   measurement STILL needs its own X-support rotation. **KEEP `stab_supp_isx` unchanged; apply the
   in-stream H's SEPARATELY in the gate stream (for the `|2⟩` refocusing).** No double-count: the net-`Z`
   is detector-invariant, so the syndrome is identical with/without the in-stream H's — only the `|2⟩`
   trajectory changes. Verified on the d3 codestate: keep → `⟨S⟩=+1` all 8; drop → X-type stabilizers
   read 0 (wrong syndrome).

4. **The measured observable AND the measurement are unchanged.** `stab_supp_isx` is KEPT; the XZZX
   stabilizer structure (4 X-type + 4 Z-type, weights 2/4) and the logical Z (engine positions {0,2,5} =
   circuit ids {0,5,10}) read out exactly as before (`…_hrecon.py` R4). The in-stream H's are ADDED to
   the gate stream for the `|2⟩` refocusing (NOT relocated from the measurement); being a detector-
   invariant net `Z`, they leave the syndrome and logical outcome identical for the Clifford part — only
   the non-Pauli `|2⟩` trajectory changes (the whole point).

> **Engine/oracle implementation.** (a) Build each qutrit's per-round gate stream with the explicit H's
> at their slots. (b) Apply the leak slice `exp(L/4)` at each CZ-layer the qubit touches, the X echo at
> the global mid slot, the post-M Y on all data (terminal round drops Y). (c) KEEP `project_stabilizer`'s
> X-support Hadamard (`stab_supp_isx`) UNCHANGED (the leaked-readout `b`-POVM and the arms A/C/B1/B2 of
> `p4a_build_contract.md` §4 are also unchanged); the in-stream H's are ADDED to the gate stream for the
> `|2⟩` refocusing, SEPARATE from the measurement (net detector-invariant `Z` → no double-count).
> The DM oracle (`qutrit_dm.py`) and the SV-MC kernel must implement the IDENTICAL per-round stream so
> Gate 4 stays valid.

---

## 5. The `|2⟩(R)` target (TASK 5 — the deliverable numbers)

Single-isolated-data-qutrit `|2⟩` population after R rounds, faithful within-cycle model (H-in,
per-CZ `exp(L/4)`, mid-X, post-M Y), at `θ=0.07, g_seep=0.09`. Two independent representations
(Kraus-sum + column-stacking superoperator) agree to `1.5e-15`.

**From `|1⟩` (the leakage-active input):**

| qid | nCZ | R=1 | R=2 | R=3 | R=5 | R=10 |
|---:|---:|---:|---:|---:|---:|---:|
| 1  | 2 | 0.000024 | 0.000174 | 0.000145 | 0.000022 | 0.000147 |
| 4  | 3 | 0.000139 | 0.000278 | 0.000139 | 0.000123 | 0.000218 |
| 6  | 3 | 0.000298 | 0.000863 | 0.000547 | 0.000266 | 0.000678 |
| 8  | 2 | 0.000871 | 0.000983 | 0.000146 | 0.000801 | 0.000829 |
| 10 | 4 | 0.000000 | 0.000586 | 0.000535 | 0.000004 | 0.000429 |
| 12 | 2 | 0.000874 | 0.000983 | 0.000142 | 0.000804 | 0.000829 |
| 13 | 3 | 0.000294 | 0.000873 | 0.000559 | 0.000263 | 0.000685 |
| 15 | 3 | 0.000158 | 0.000295 | 0.000139 | 0.000140 | 0.000232 |
| 18 | 2 | 0.000027 | 0.000174 | 0.000142 | 0.000025 | 0.000147 |

**From `|0⟩`:** same order, `|2⟩(R=10)` in `0.000143..0.000860` (full table in `…_confirm.py`).

- **Order + flatness:** `max |2⟩(R)` over all qubits/levels/R = `0.001015` — O(1e-3), FLAT in R (no
  runaway). Lands in the same **~0.001–0.0016 band as V's `dist+Y`** (the deliverable target). The H's
  shift `|2⟩` WITHIN the band (downward, by refocusing); they do not leave it.
- **Reconciliation with V's `dist+Y`.** V's reference (`dist+Y`, no H's) gives `|2⟩(R=10,|1⟩)=0.0016`
  for the 4-CZ qutrit. The faithful per-qubit model gives `0.00015..0.00083` (lower, because the per-
  qubit H's refocus the coherent leak via `H·X·H = Z`). **V's `dist+Y` is the ORDER-ANCHOR + the exact
  4-CZ no-H sanity point (reproduced to gap 0.0); the faithful target is the H-in per-qubit number.**
  This is the correct reading of "must reproduce V's `dist+Y`": same band, exact in V's special case.
- **Coherent refocusing is REAL, not a bug** (audited, `…_audit.py`): the q10 step-by-step trace shows
  `|2⟩` building mid-round then refocusing to ~2e-7 by round end; a `theta=0` (purely incoherent)
  positive control gives MONOTONE-rising `|2⟩(R)` (0.0149→0.139), proving the machinery is not
  trivially zeroing; the qutip oracle confirms the leak slice.

---

## 6. Over-statement vs the current lumped engine (the fix's headline)

The current engine applies `L_full ; X` per round with NO Y (the post-M Y was dropped). Comparison
(from `|1⟩`, `…_confirm.py` panel C):

| R | lumped `L;X` (engine, no Y) | lumped `L;X;Y` | faithful (mean over 9 q) | ratio engine/faithful |
|---:|---:|---:|---:|---:|
| 1  | 0.004678 | 0.004678 | 0.000298 | 15.7× |
| 2  | 0.004254 | 0.008910 | 0.000579 | 7.4× |
| 3  | 0.017013 | 0.004231 | 0.000277 | 61.4× |
| 5  | 0.034638 | 0.004082 | 0.000272 | 127.3× |
| 10 | 0.069274 | 0.006522 | 0.000466 | 148.6× |

- **The deliverable's "~4×" is the LOW-R / MATCHED-Y figure** (e.g. lumped+Y vs `dist+Y`-style at R≈2;
  V's original review comparison). The HONEST, fully-characterized figures are larger: **15× at R=3
  with matched Y** (lumped+Y / faithful-mean), and the **no-Y engine RUNS AWAY** (61× at R=3, ~149× at
  R=10) because its `|2⟩` is never refocused. The runaway IS the headline reason the fix matters:
  lumping + dropping the Y converts a flat ~1e-3 leakage into an accumulating ~1e-1.
- **Two error sources, both fixed by this spec:** (i) LUMPING (one full-cycle channel vs 4 distributed
  per-CZ slices around the X echo) and (ii) DROPPING THE POST-M Y (no refocusing). The within-cycle
  model fixes both.
- **The post-M Y refocuses** (`…_confirm.py` panel D, `…_audit.py`): faithful with-Y keeps `|2⟩` flat;
  the per-qubit H-X-H structure already refocuses much of it even before the Y for some qubits (q10),
  but the Y is required in general (and is a genuine physical pulse, per V).

> **Claim discipline.** The "~N× over-statement" is a **(c)-class reportable characterization** of the
> lumped model's error, not a premise. The factor is R-dependent and Y-convention-dependent; the spec
> states the full table, not a single number.

---

## 7. Build checklist (for K / H / V — `p4a_build_contract.md` ownership)

1. **Parser/host (H):** surface the per-qubit ordered INTERIOR stream (§2) from a MULTI-ROUND
   circuit's interior rounds (NOT r01's first+terminal single round) — H's at their slots, the
   CZ-layer participation set per qubit, the global mid-X slot, the post-M Y. Handle the FIRST round
   (folds the data-init H layer) and the TERMINAL round (drops the post-M Y) explicitly. Marshal
   per-qutrit gate+leak CSR honoring the per-qubit CZ-layer set (apply `exp(L/4)` only at the touched
   CZ layers).
2. **Calibration (H):** per-CZ slice = `leakage_kraus`-style Kraus of `exp(L/4)` (Choi-factorized);
   assert `‖exp(L) − (exp(L/4))⁴‖ < 1e-12` before marshalling. `(θ, g_seep, g_heat)` from the
   registered sweep.
3. **Measurement (CORRECTED — UNCHANGED):** apply the explicit circuit H's in the gate stream (for the
   `|2⟩` refocusing); the stabilizer measurement is **UNCHANGED — KEEP `stab_supp_isx`** (the in-stream
   H's net to a detector-invariant `Z`, so the data is in the computational basis at M and the X-support
   rotation is still needed — verified: dropping it reads X-type stabilizers as 0). The `b`-POVM + arms
   A/C/B1/B2 are unchanged. **K's `measure_stab_block` needs NO change; only the op-schedule + leak.**
4. **DM oracle (H):** `qutrit_dm.py` implements the IDENTICAL per-round stream (per-qubit H's +
   per-CZ leak slices + mid-X + post-M Y + the STANDARD measurement, `stab_supp_isx` kept) so Gate 4
   (`TV(SV-MC, DM) ~ C/√N`) stays valid against the within-cycle model.
5. **V:** re-point the Gate-4 oracle + the `|2⟩(R)` physics control to the §5 targets; assert the
   faithful `|2⟩(R)` reproduces §5 (per qubit), the calibration anchor (q10 H-out == V `dist+Y`, gap
   0), and the over-statement table (§6).

---

## 8. Subtleties (read before implementing)

- **Per-qubit CZ count varies (2/3/4), NOT a uniform 4.** The prompt's "4 leak sub-steps" is the GLOBAL
  per-round CZ-layer count; each qubit touches only its own subset. Marshal per qubit. (`…_czmap.py`.)
- **The H pattern is per-qubit (4 distinct patterns).** Do not hard-code a single template; read each
  qubit's stream from the circuit. (`…_parser.py`.)
- **The H's net to identity per round but are NOT free for `|2⟩`** — they refocus the coherent leak via
  `H·X·H = Z` because the X sits between them. Dropping the H's (V's `dist+Y` simplification) OVER-states
  `|2⟩` ~2–10× relative to the faithful model. Keep the H's. (`…_hstudy.py`, `…_audit.py`.)
- **`stab_supp_isx` and the in-stream H's are DIFFERENT roles — keep BOTH.** The in-stream H's compose to
  a detector-invariant net `Z` (they refocus `|2⟩`, do NOT rotate the measurement basis); `stab_supp_isx`
  is the measurement's X-support rotation (still needed). Verified (drop → X-type stabilizers read 0).
- **The leaked-readout `b`-POVM + arms A/C/B1/B2 are untouched.** They act diagonally in the Z basis;
  after the explicit H's, the state is already in the Z basis, so the existing diagonal machinery
  applies verbatim.
- **The terminal round drops the post-M Y** — for the FINAL `|2⟩` read this is captured by the
  `terminal-no-Y` convention; for q10 it makes zero difference (already refocused), but a general qubit
  needs the terminal-no-Y handling. (`…_audit.py` S3.)
- **r01's single round is NOT a clean interior round** (it is first+terminal: folds the data-init H
  layer AND drops the post-M Y). Source the per-qubit INTERIOR stream from a multi-round circuit's
  interior rounds; handle first (data-init H) + terminal (no-Y) rounds explicitly. The CZ-leak
  geometry is reuse-stable across r01/r10 (same patch), so the LEAKAGE placement is faithful to reuse;
  only the round-boundary gate set (init-H / Y) needs per-round-position handling. (`…_parser.py` §4.)
