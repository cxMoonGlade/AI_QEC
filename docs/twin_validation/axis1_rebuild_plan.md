# Axis-1 from-scratch rebuild — physical-correctness-first plan

Date: 2026-06-30. Status: **operative plan (controls the Axis-1 rebuild).**
Owner discipline: `docs/FAITHFULNESS_PROTOCOL.md` + `docs/METRICS.md` epistemic-status ladder.

## 1. Problem statement

Deliverable: **the simulator's Axis-1 — a correct, complete error-mechanism coupling**, where
"Axis-1" = the same-substep *instantaneous joint Lindbladian* / same-substep generator coupling
carrier (`src/qec_twin/simulator/axis1_*`). Every mechanism admitted to Axis-1 must be a
time-local GKSL generator (a Hamiltonian or a collapse operator) acting WITHIN one substep on the
system Hilbert space (`axis1_mechanism_completeness_prereg.md` test (a)).

**The binding bar for this rebuild: every scientific-correctness claim is supported by ≥2 DIRECT
real references.** A reference is **DIRECT** only if the cited paper exhibits *this* physical
mechanism / *this* operator as a real effect (not "is local-unitary-equivalent to", not "the
general framework permits"). Mathematical-basis membership (e.g. "X⊗Z is an su(4) basis element")
is **not** a DIRECT physical reference; it is at most operator-algebra grounding and is logged
separately.

**HARD CUT-GATE — UNIFORM ACROSS EVERY MECHANISM AND GROUP (2026-06-30, user-binding).** ≥2
DIRECT-physical is not a per-group bar; it is a hard gate every kept Axis-1 mechanism must clear,
with NO exceptions and NO soft "framing" pass. Step 2 of the per-mechanism pipeline (theory-first)
is a GO/NO-GO: a mechanism that cannot be shown ≥2 DIRECT-physical (real, text-verified, exhibiting
THIS coupling device-physically — in isolation OR as an identified, measured component of a real
device Hamiltonian) is **CUT** from the carrier exactly like the deleted off-Cartan terms — it is
not retained with a weaker label. This applies retroactively to every already-built group and
prospectively to all remaining ones (M12, M17, M18, M21, M34). Mechanisms most at risk: **M18**
(prep over-rotation — must earn a 2nd DIRECT-physical ref or be cut) and **M21/M34** (leakage —
grounding unaudited). The one borderline already-kept case is **M23** (pure YY): it clears ONLY via
"YY is a measured component of ≥2 device Hamiltonians (Sung + Foxen exchange)"; it has NO isolated
pure-YY device ref (Geller's coupler has no YY). Kept per the user's "Cartan-component" decision and
flagged as the weakest; if the hard gate is read as requiring isolated exhibition, M23 is CUT.

## 2. Gap analysis — why the deleted set fails, what is kept

The prior Axis-1 mechanism set was audited against the ≥2-DIRECT-physical bar (multi-agent review,
2026-06-29/30, recorded in the review thread). The audit found two failure modes:

**(F1) Off-Cartan directional 2q couplings are not independently device-grounded.** The five terms
XY, YX, XZ, YZ, ZY are all local-unitary (KAK) equivalent to the Cartan set {XX, YY, ZZ} dressed by
single-qubit rotations — they are not 5 independent physical mechanisms. No read paper exhibits a
standalone parasitic XY/YX/XZ/YZ/ZY term; the cross-resonance literature produces **ZX** (Magesan
1804.04073), and its role-swap/quadrature partners are reached only by relabeling. Their preregs
self-classified the device grounding as **INDIRECT** and cleared "(a)-class" only via su(4)-basis
membership (a math, not physical, DIRECT). → **fails the ≥2-DIRECT-physical bar.**

**(F2) Non-physical stress surrogates.** M15 (`hard_non_pauli_kraus`) and M19 (`weak_type4_ptm_
mixing`) are CPTP capability probes with **no physical-mechanism paper by design**. Their math
(CPTP/CP) is grounded (Kraus 1971, Choi 1975), but as physical error mechanisms they have zero
DIRECT references. → out of scope for "correct physical error mechanisms."

**(F3) Arbitrary axis choice.** M27 (coherent over-rotation about the `(X+Z)/√2` Hadamard axis):
the *family* (coherent single-axis over-rotation) is grounded, but the specific 45° axis is a
declared (c) catalog choice with no DIRECT physical reference. → fails the bar (Rx/Ry/Rz survive).

### Deleted (2026-06-30, backed up to session scratchpad `axis1_deleted_backup/`)
M15, M19, M27, M28 (XY), M30 (ZY), M31 (XZ), M32 (YZ), M33 (YX).
- docs/twin_validation: their prereg / derivation `.md` (8 files).
- outputs: their `*_cert.py` (6 files).
- tests: their `*_constraint_ledger.py` (6 files).
- carrier families removed from `axis1_mcwf_mps_execution.py` + `axis1_qt_mps_execution.py`:
  `COH_H`, `COH_XY`, `COH_ZY`, `COH_XZ`, `COH_YZ`, `COH_YX`.
- **Left untouched:** `forward/channels.py` `custom_non_pauli_kraus` (M15) / `weak_type4_mixing_kraus`
  (M19) belong to the *forward/PTM* subsystem (consumed by `forward/*`, `mechanisms_torch.py`,
  not the Axis-1 carrier); deleting them is a separate, out-of-scope (B-path) surgery.
- Post-surgery check: kept coherent ledgers + `test_window_channel` → **191 passed, 6 skipped.**

### Kept — the physical Axis-1 mechanism inventory to rebuild
Each must earn ≥2 DIRECT physical references before its prereg is (a)/(b)-admissible.

| group | mechanisms | carrier form | prior status |
|---|---|---|---|
| Incoherent collapse | M4 amplitude_damping (T1), M5 idle_dephasing (T2), M24 thermal_excitation (T1↑) | collapse | ✅ implemented, grounding UNAUDITED |
| 1q coherent over-rotation | M6 Rx, M7 Rz, M20 Ry | 1q Hamiltonian | prereg+cert, reviewed SOUND |
| 2q coherent (device-real) | M8 ZZ, M22 XX, M23 YY, M10 XX+YY, M29 ZX | 2q Hamiltonian | prereg+cert (M8 ✅) |
| Crosstalk | M11 spectator ZZ/RZ | extended-support Hamiltonian | derivation-only; **circular oracle + buggy code** |
| Correlated relaxation | M12 Dicke collective | 2-site joint collapse | prereg+derivation; **circular oracle**; magnitude (c) |
| Reset / prep | M17 reset-to-1 bias, M18 prep over-rotation | reset-substep channel | derivation-only; M18 grounding **TBD (cut if <2 DIRECT)** |
| Leakage / conditional | M21 conditional_phase, M34 leakage_relaxation | qutrit/ququart | ✅ implemented, grounding UNAUDITED |

## 3. Per-mechanism pipeline (run one mechanism at a time)

1. **Define problem + gap** — what the mechanism is, what the carrier currently does, what is
   missing / unproven for THIS mechanism.
2. **Theory-first** (`theory-first` skill) — find the CORRESPONDING published papers for the
   *mechanism* AND the *observable*; download → convert → close-read (精读) into committed reading
   notes under `docs/papers/reading_notes/`; require **≥2 DIRECT physical** refs (else the
   mechanism is cut or demoted to (c)); write a literature-anchored prereg with epistemic classes
   (a/b/c) and a constraint ledger (physical theorems + a falsifying test each).
3. **Multi-agent doc review** — ≥2 independent read-only reviewers (no leading): physics
   correctness, ≥2-DIRECT check, genuine-vs-vacuous falsifiers, independent-GT non-circularity,
   bounded simplifications.
4. **Implementation** — carrier code for the mechanism (or verify existing code matches the freshly
   grounded theory). Scripted-execution discipline.
5. **Verify + test (multi-agent)** — independent ground-truth check (closed-form / hand-typed /
   from-scratch, NEVER the engine's own oracle); CPTP/CP; constraint-ledger falsifiers all trip;
   serialized GPU cert. Reviewers analyse results read-only.
6. **Analyse result** — metric audit (field-standard or rung-3 flagged); rigor audit (theorem-backed
   vs provisional).
7. **Fix issue / go next** — iterate until green, then advance.

## 4. Hard discipline (non-negotiable)

- **GPU serialization** — model compute on GPU; **NO concurrent GPU jobs** (workstation = live
  desktop). Multi-agent fan-out is **READ-ONLY analysis only**; the actual GPU cert/test runs are
  executed serially by the orchestrator, one at a time.
- **Independent ground truth (Rule-I)** — certification is against a reference INDEPENDENT of the
  implementation (closed-form theorem / raw artifact / hand-typed from literature). `assemble_
  substep_channel` is the carrier-under-test, **never** the independent oracle. (Fix the residual
  circular-oracle wording in M11 / M12 / the completeness doc during their rebuilds.)
- **Constraint ledger + bounded simplifications** — written BEFORE code; every simplification
  declared with epistemic class + error bound (unbounded = STOP).
- **Epistemic classes** — (a) exact / (b) prediction band / (c) heuristic gate; undeclared ⇒ (c);
  provisional unless theorem-backed.
- **Scripted execution** — every run is a committed script (asserts + printed evidence + flushed +
  `__main__` guard for multiprocessing). No inline one-liners running project logic.
- **Commit gate** — Axis-1 carrier (`src/`) + test edits are surfaced for review; commits land on
  the `Dev-F` branch per coherent milestone (cleanup; then per mechanism group).

## 5. Status
- [x] Cleanup: sub-bar set deleted; carrier surgical removal; survivors green (191 passed).
- [x] This plan / gap analysis.
- [x] Collapse set (M4/M5/M24) — DONE: ≥2-DIRECT (Krantz/Place; Jin/Wenner), cert ALL PASS, 2 reviewers SOUND.
- [x] 1q coherent (M6/M7/M20) — DONE: ≥2-DIRECT (Sheldon/Lazăr/McKay added), ledgers green, reviewer SOUND.
- [x] 2q coherent (M8/M22/M23/M10/M29) — DONE (M8 prereg+cert ALL PASS; M29 +Sheldon; M22/M23 kept
  as honest Cartan components; 2 reviewers cleared: M8 SOUND, M22/M23/M29 grounding HONEST).
  **Decision (2026-06-30, user):** under the
  ≥2-DIRECT-physical audit, the device-real objects are {M8 ZZ cross-Kerr, M10 XX+YY exchange, M29 ZX
  cross-resonance}; **pure XX (M22) / pure YY (M23) kept as honest Cartan-axis COMPONENTS of the
  device-real exchange** (they appear as measured components in ≥2 device Hamiltonians — Sung+Foxen;
  M22 also Geller pure-XX), pure-isolation declared as a bounded (c)-class idealization. Distinct from
  the cut off-Cartan terms, which have NO device home. M8 prereg+cert ADDED (was missing); M29 gains
  Sheldon 1603.04821 (CR measurement) as 2nd device-direct ref. M10/M22/M23/M29 certs already green +
  audited genuine.
- [x] Crosstalk M11 — DONE (prereg + cert ALL PASS incl. the novel 3q cluster-join; reviewer SOUND;
  ≥2 DIRECT-physical for ZZ [Sarovar+Mundada] and RZ [Sarovar+Song]; circular oracle + buggy code
  already fixed on-disk). Deferred: schedule-level spectator emission (cert at term-dict level).
- [x] Correlated relaxation M12 — DONE (Phase-A): circular oracle confirmed-fixed; ≥2-DIRECT (Mlynek+Cattaneo); channel cert ALL PASS; reviewer SOUND. Phase-B trajectory seam = task #11 (deferred).
- [x] Reset/prep — M17 reset_to_1_bias **KEPT** (≥2 DIRECT-physical: McEwen Nat.Commun.12,1761 DOI
  10.1038/s41467-021-21982-y + Reed APL 96,203110/arXiv:1003.0142 — Reed citation corrected from the
  wrong "PRL 105,173601"; channel cert ALL PASS). **M18 prep over-rotation CUT/merged into M6** —
  operator-identical (`rx_unitary`), no distinct device-direct coherent-prep grounding → fails the
  hard gate as an independent mechanism. Both forward/-only (carrier reset is clean projective; no
  prep substep) — biased-reset carrier wiring deferred like M12 Phase-B.
- [x] Leakage/conditional M21 / M34 — DONE: both KEEP (M21 Miao+Varbanov; M34 WG+McEwen), run on the carrier; M34 circular cert replaced with faithful WG-closed-form cert ALL PASS; reviewer SOUND.
- [x] Final integration + grounding + metric + rigor audit — DONE: `axis1_rebuild_completion_audit.md`; 392 local / 424 panel regression; 5-model review (4 SOUND-WITH-FIXES + 1 NOT-YET), all fixes applied (§9).
