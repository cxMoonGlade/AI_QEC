# M7 coherent_rz_overrotation — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: **PRE-REGISTRATION, 2026-06-29.** Predictions written BEFORE the run; a miss is a finding,
not a re-fit. Second of the four Axis-1 1q coherent over-rotation knobs (M6 rx, **M7 rz**, M20 ry,
M27 h-axis; `axis1_mechanism_completeness_prereg.md` group 1). Direct sibling of the landed M6
(`m6_coherent_rx_overrotation_prereg.md`) — identical machinery, **Z axis instead of X**. Does NOT
claim Axis-1 completion and adds NO metric to `docs/METRICS.md` (`1−F_e` already in the ledger).

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)

| sub-axis / mechanism | mechanism paper | observable paper | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| 1q RZ coherent over-rotation `U_θ = exp(−iθ_Z Z)` (single-qubit `θ_Z Z` term of `H_θ = Σ_k θ_k P_k`) | Kaufmann, Rojkov & Reiter, arXiv:2307.08741 (Eq. 2: `E_{P,θ}=U_θ∘P∘U_I`, `U_θ=exp(−iH_θ)`, `H_θ=Σ_k θ_k P_k`; the single-qubit set is the 3 rotations `{θ_X X, θ_Y Y, θ_Z Z}` — `θ_Z Z` IS M7; first-order coherent in off-diagonal PTM) **+ axis-specific McKay–Wood–Sheldon–Chow–Gambetta arXiv:1612.00858** (Rz = detuning/phase error: off-resonance rotation `U=exp(−it[(Ω/2)X+ΔZ])`, "unwanted Z-gate"; Stark-shift) **+ Sheldon arXiv:1504.06597** (Eq. 1 `U=exp(−i(ε/2)r̂·σ)`, r̂=ẑ) — ≥2 DIRECT-physical, text-verified 2026-06-30 | observable below | `coherent_robust_pauli_2307.08741.md`, `mckay_efficient_z_gates_1612.00858.md`, `sheldon_iterative_rb_overrotation_1504.06597.md` | `simulator/axis1_mcwf_mps_execution.py:_hamiltonian_matrix_for_term` (family `COH_RZ` → `_coherent_family_generator` → `H=(coeff/2)Z`, axis map `COH_RZ→"Z"` line 1045) |
| process (entanglement) infidelity `1−F_e` of a CPTP map / unitary error | Schumacher, PRA 54, 2614 (1996) (`F_e` def + Kraus form `Σ_k|Tr(ρE_k)|²`) | Nielsen, arXiv:quant-ph/0205035 (Eq. 3 `F_avg=(d F_e+1)/(d+1)`; Eq. 16 operator-basis `F_e`; line 75 def `F_e=⟨φ|(I⊗E)(φ)|φ⟩`) | `docs/papers/reading_notes/schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md` | `forward/joint_lindbladian.py:_choi_state_from_kraus`, `_state_fidelity`, `composed_vs_joint_infidelity`, `assemble_substep_channel` |
| RZ over-rotation as the canonical M7 definition | — | — | `docs/error_mechanisms.md` (M7 line 98 = 1q `RZ(epsilon)` coherent unitary, "coherent phase/control error") | `mechanisms/catalog.py:MECHANISMS["M7"]` |

**Why M7 meets the ≥2-DIRECT-physical bar (shared close-reads as M6 + the axis-specific McKay 1612.00858 detuning/phase ref).** The mechanism paper
(2307.08741) is `H_θ = Σ_k θ_k P_k` over the FULL single-qubit Pauli set `{X,Y,Z}` (Eq. 2 / Sec. II:
"3 single ... rotations per [qubit]"); M6 is the `θ_X X` term, M7 is the `θ_Z Z` term — the SAME
equation, same paper, same close-read. The observable note already states the `1−F_e` def + Kraus
form + the `/d` leading-order ledger that M7 reuses verbatim (the closed form is axis-agnostic; see §2
B1). No NEW physics is introduced by M7 — only the axis selector changes.

## 1. The mechanism (anchored; REUSE existing carrier code)

**M7 = coherent_rz_overrotation = a 1q `RZ(ε)` coherent unitary error** (`docs/error_mechanisms.md`
line 98), the over-rotation knob on the ideal Z-axis control (a coherent phase/control error). It is
the single-qubit `θ_Z Z` term of the Kaufmann–Rojkov–Reiter coherent-layer generator
`H_θ = Σ_k θ_k P_k` (2307.08741 Eq. 2), i.e. the coherent Z-axis over-rotation the twin's teacher
composes with stochastic Pauli.

**Carrier form (the operator under test — REUSE, do not rebuild):** family `COH_RZ`, lowered by
`simulator/axis1_mcwf_mps_execution.py:_hamiltonian_matrix_for_term` → `_embed_coherent_generator` →
`_coherent_family_generator` (axis map `_ONE_Q_FAMILY_TO_AXIS["COH_RZ"]="Z"`, line 1045), which
returns on the 2-level computational subspace

```
H_M7 = (coeff / 2) · Z ,    Z = [[1,0],[0,-1]]        # rad/ns; embedded with the zero generator on any leaked level
```

so the realized error gate over a substep `dt` is

```
U_M7 = exp(−i · H_M7 · dt) = exp(−i (ε/2) Z) = RZ(ε) = diag(e^{−iε/2}, e^{+iε/2}) ,
       ε ≡ coeff · dt   (the over-rotation angle, rad)
```

**Swept range (NOT a frozen constant):** `ε ∈ {3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3}` rad (≈ the
calibration-residual regime; 2307.08741 reports single-qubit coherent angles ≲ 0.1 rad, systematic
+ stable over 19 days). The cert uses `coeff` and `dt_ns` independently so `ε = coeff·dt` is swept by
varying either.

### 1a. RESOLUTION of the COH_* placement ambiguity (ALREADY LANDED with M6 — inherited)

The brief's placement ambiguity was resolved by the M6 work and **M7 inherits the resolution**:
`mechanisms/axis1_primitives.py` lines 19–23 now read *"COH_* / COHERENT_PAULI_FAMILIES are
intentionally NOT declared here ... advertising it here was a [faithfulness trap]"* — the PREFERRED
fix-1 (DELETE the COH_* declarations from the primitives registry, leaving
`axis1_mcwf_mps_execution._hamiltonian_matrix_for_term` the sole, unambiguous COH_* lowering owner) is
in the tree. **The M7 cert imports the operator under test from
`axis1_mcwf_mps_execution._hamiltonian_matrix_for_term` ONLY, never from the `axis1_primitives`
registry** — the same surface the M6 ledger and the qutrit-leakage de-circularized cert use.
[Epistemic class (c) — a build/placement decision, already executed; no physics claim.]

## 2. Predicted observable (class (b) bands; ANCHORED — `1−F_e`, the RIGHT one, not invented)

**Observable = process (entanglement) infidelity `1 − F_e`** between the substep channel WITH the M7
error knob and the substep channel WITHOUT it (the ideal/no-error reference) — the standard
`axis1_mechanism_completeness_prereg.md` line-98 cert observable (`assemble_substep_channel` →
Choi-state `F_e`). Schumacher/Nielsen def (reading note); for a pure RZ over-rotation vs identity:

- **(B1) EXACT closed form [b-band, derivable to a-exact]:**
  `1 − F_e(RZ(ε), I) = 1 − |Tr(RZ(ε))/2|² = 1 − |(e^{−iε/2}+e^{+iε/2})/2|² = 1 − cos²(ε/2) = sin²(ε/2)`.
  **Axis-agnostic:** for any single-axis SU(2) rotation `R_P(ε)=exp(−i(ε/2)P)`, `P∈{X,Y,Z}`,
  `Tr R_P(ε)=2cos(ε/2)` (traceless `P`, eigenvalues `±1`), so `1−F_e=sin²(ε/2)` is IDENTICAL to M6's
  — the *scalar* infidelity does not distinguish the axis (it is exactly the "scalar averages hide
  structure" caveat, §B-INSUFFICIENT; the axis is recovered ONLY by the operator gate B4). Predicted:
  the carrier-side `1−F_e` (via `_choi_state_from_kraus`+`_state_fidelity`) equals `sin²(ε/2)` to the
  Uhlmann-estimator floor (~2e-8), monotone increasing in `|ε|`, **even in ε**
  (`1−F_e(ε)=1−F_e(−ε)`: over- and under-rotation of equal magnitude are equally infidel).
- **(B2) LEADING-ORDER scaling [b-band]:** `1 − F_e ≈ ‖G‖²_F/d = ε²/4` with `G=(ε/2)Z`,
  `‖G‖²_F=Tr((ε/2 Z)²)=2·(ε/2)²=ε²/2`, `/d=/2 → ε²/4` (METRICS.md `/d`, d=2). Predicted **quadratic**
  law: `1−F_e ∝ ε²` at small ε; `(1−F_e)/ε² → 1/4` as `ε→0`. The exact form deviates from `ε²/4` at
  `O(ε⁴)` (since `sin²(ε/2)=ε²/4 − ε⁴/48 + …`) — a registered higher-order finding, NOT a carrier bug.
- **(B3) AVG-GATE link [b-band]:** `1 − F_avg = (d/(d+1))(1−F_e) = (2/3)sin²(ε/2) ≈ ε²/6` — reported
  as a companion ONLY if an RB-comparable number is wanted; `1−F_e` stays the headline (carry the
  convention with the number).

**Statistic flagged INSUFFICIENT (do NOT headline):** `1−F_e` (or `1−F_avg`) is a *scalar average*
measure — coherent and stochastic channels of equal infidelity are indistinguishable by it, AND (the
M7-sharp form of the caveat) `1−F_e` is identical for RX/RY/RZ of the same angle (B1) so it cannot
tell which Pauli axis the rotation is about (reading-note Limitations; the surface-code analogue is
the Bravyi twirl-underestimate, `correcting_coherent_errors_surface_1710.02270.md`). The cert
therefore ALSO gates the **direct operator/generator identity** (B4 below), the structural witness
`1−F_e` alone cannot provide — and for M7 the operator gate is the ONLY thing that distinguishes Z
from X/Y.

- **(B4) OPERATOR identity [a-exact, the load-bearing gate]:** the carrier generator equals the
  hand-typed reference: `‖H_carrier − H_ref‖_F ≤ 1e-12` and `‖U_carrier − U_ref‖_F ≤ 1e-10`, with
  `H_carrier` Hermitian (`‖H−H†‖_F ≤ 1e-12`) and traceless (`|Tr H| ≤ 1e-12`), where `H_ref=(coeff/2)Z`.
  A miss is a CARRIER PHYSICS BUG — the finding a `1−F_e`-only or circular cert could never surface.
  **For M7 this gate is load-bearing in a way it is not for M6:** since `1−F_e` is axis-blind (B1),
  B4 is the SOLE witness that the carrier rotates about Z and not X/Y.

## 3. Independent ground truth (non-circular) — the HAND-TYPED reference operator

The reference is **hand-typed in the cert from the literature equations**, importing NO carrier
symbol (`_coherent_family_generator`, `_embed_coherent_generator`, `ONE_SITE_COHERENT_FAMILIES`,
`_ONE_Q_FAMILY_TO_AXIS` appear NOWHERE in the cert's executable code). The carrier side imports ONLY
`_hamiltonian_matrix_for_term` (the object under test) — exactly the de-circularized
`axis1_qutrit_leakage_certification` / M6-ledger pattern (`test_axis1_wc_decircularized.py`,
`test_m6_coherent_rx_constraint_ledger.py`).

**Reference operator spec (PROVENANCE-carried, transcribed not invented):**

```
# M7 reference generator on the 2-level computational subspace (d=2), zero generator on leaked levels.
# H_M7 = (coeff/2) * sigma_z.
#   sigma_z = [[1,0],[0,-1]]                         <- Pauli-Z, standard (Nielsen & Chuang Eq. 2.1).
#   factor 1/2: RZ(eps)=exp(-i (eps/2) Z), eps=coeff*dt  <- single-qubit rotation generator convention
#               (Nielsen & Chuang Eq. 4.4-4.7; standard "R_z(theta)=exp(-i theta Z/2)").
#   the over-rotation MECHANISM (coherent gate-axis term theta_Z Z) is grounded in
#               Kaufmann-Rojkov-Reiter arXiv:2307.08741 Eq. 2 (H_theta = sum_k theta_k P_k; the
#               single-qubit Z term theta_Z Z IS M7).
def ref_H_M7(coeff, dim, device):           # dim = local site dim (2, or 3 if qutrit carrier)
    Z = tensor([[1,0],[0,-1]], complex128, device)
    H = zeros((dim, dim), complex128, device)
    H[:2,:2] = 0.5 * coeff * Z               # zero generator (identity gate) on level>=2
    return H
# error unitary:  U = matrix_exp(-1j * dt_ns * H)  ==  RZ(eps)=diag(e^{-i eps/2}, e^{+i eps/2}) on the 2-block, eps = coeff*dt_ns.
# EXACT 1-F_e reference (unitary vs identity, d=2):  1 - |Tr(U)/2|^2  ==  sin^2(eps/2).
# LEADING 1-F_e reference:  ||(eps/2) Z||_F^2 / 2  ==  eps^2/4.
```

This is a closed-form theorem (the `RZ(ε)` matrix + `F_e=|Tr V/d|²`), independent of the
implementation. A from-scratch numerical confirmation on RTX 5090 already ran (scratchpad
`m7_fe_derivation_check.py`): the carrier `COH_RZ` op equals `(coeff/2)Z` to **opdiff 0**; `sin²(ε/2)`
vs the carrier `|Tr U/2|²` agree to ~1e-16 across ε∈{0.3…1e-3}; `ε²/4` tracks the exact form with the
predicted `O(ε⁴)` deviation (ε=0.3 → 1.68e-4 ≈ ε⁴/48); `H` Hermitian + traceless residuals exactly 0;
`1−F_e` even in ε to <1e-12. (That script is a derivation-check, NOT the cert.)

**Wrong-axis negative control (the control a `1−F_e`-only / scalar cert structurally CANNOT provide
for M7) — the load-bearing M7 control:** a **WRONG-AXIS** reference `H_wrong = (coeff/2)·X` (or `·Y`)
must DISAGREE with the carrier: `‖U_carrier − U_wrong‖_F ≥ 1e-3` for ε exercised at `ε ≥ 1e-2`
(derivation-check: `|U_RZ−U_RX| = |U_RZ−U_RY| ≈ ε` for small ε, so ε=1e-2→5e-3 ≥ 1e-3; at the very
smallest ε=1e-3 the diff is ~5e-4 < 1e-3, so the wrong-axis gate is registered to fire at ε≥1e-2 —
class (c) gate parameter). RZ vs RX, RZ vs RY of the same angle are distinct gates; a wrong Pauli
axis is the M7 analogue of the leakage cert's wrong-level control. Because `1−F_e` is identical for
RX/RY/RZ (B1), **this wrong-axis operator control is the ONLY thing in the cert that detects a
corrupted COH_RZ axis map** — making it strictly necessary for M7 (more so than for M6, where the
scalar still has the angle even if blind to the axis). A weaker `wrong_unit` control (treat `coeff` as
the angle, dropping the ×dt) is retained as a second control. **Show the control trips:** corrupt the
carrier axis map `COH_RZ→Z` to `X` (or `Y`) and confirm the hand-typed reference CATCHES it (diff ≥
1e-3, cert fails), while a reference derived FROM the corrupted carrier map would mirror it to diff 0
(false-pass) — the C2-falsifier shape of `test_wc_cert_catches_corrupted_carrier_level_map` /
`test_m6_...corrupted...`.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)

- **S1 — RZ error treated as a STRICT unitary (pure Hamiltonian, no collapse).** Class (a) on the
  certified slice: M7 is by definition a coherent unitary (`docs/error_mechanisms.md` line 98); the
  cert certifies the Hamiltonian generator + the exact `exp(−iHdt)` gate. Error vs faithful: 0 (it IS
  the faithful object). ⇒ **STRICT gate tier** `1−F_e ≤ 1e-6` and operator identities `≤ 1e-12/1e-10`
  (no collapse ⇒ no finite-microstep MCWF error; this is the exact-dense regime, not the GROSS tier).
- **S2 — 2-level computational subspace; zero generator on leaked levels.** Class (a): the M7 RZ knob
  acts on the computational `{|0>,|1>}` block; in a qutrit/ququart carrier the generator is the same
  2-block embedded with the zero generator on level ≥ 2 (matches `_embed_coherent_generator`). Error
  vs faithful: 0 within the stated semantics. **M7-specific note:** `RZ(ε)` leaves `|2⟩` phase
  UNCHANGED (`exp(0)=1` on the leaked level) — i.e. M7 imparts NO phase to leaked population; any
  leaked-level phase is a DIFFERENT mechanism (qutrit-frame phase / leakage transport, M34/LEAK_*),
  not M7. This is the same "identity on leaked levels" simplification as M6 S2.
- **S3 — `ε = coeff·dt` constant across the substep (no intra-substep drift).** Class (b): drift of
  the over-rotation angle ACROSS cycles is M13 = Axis-2 (frozen), not M7. Error bound: `O(Δε/ε)`;
  within one substep with a declared instantaneous `coeff`, exact. Cross-cycle drift is explicitly out
  of this slice.
- **S4 — `1−F_e` reported via the Uhlmann sqrt/eigh Choi estimator (≈2e-8 floor).** Class (c): the
  estimator floors at ~2e-8 (documented in `composed_vs_joint_infidelity`), so `1−F_e` is reported as
  the standard-metric companion at that resolution; the LOAD-BEARING zero-tolerance gate is the direct
  operator identity (B4) at 1e-12, not the `1−F_e` value.

## 5. Epistemic status (METRICS-ladder)

- **(a) exact:** the operator identity B4 (`H_carrier = (coeff/2)Z` = hand-typed ref, Hermitian,
  traceless; `U=RZ(ε)=diag(e^{∓iε/2})`); the closed forms `1−F_e=sin²(ε/2)` and `‖G‖²_F/d=ε²/4`; the
  wrong-axis control disagreement (at ε≥1e-2). These are theorems/identities — the only class anything
  is built on.
- **(b) bands:** B1 (carrier `1−F_e` = `sin²(ε/2)` to estimator floor; axis-agnostic scalar), B2
  (quadratic `∝ε²`, ratio →1/4), B3 (`1−F_avg=(2/3)·`), and the `O(ε⁴)` exact-vs-leading deviation. A
  miss is a finding.
- **(c) gates:** STRICT numeric tiers (`1−F_e ≤ 1e-6`, operator `≤ 1e-12/1e-10`, wrong-axis `≥ 1e-3`
  at ε≥1e-2); the placement-fix decision (§1a, inherited); the swept ε grid.
- **Headline verdict stays PROVISIONAL** until the GPU cert runs green AND the corruption-falsifier
  trips. Reportable + go/no-go; nothing is built on it. No Axis-1-completion claim, no METRICS change.

## 6. Build org + gate plan

- **Gate tier:** **STRICT** (`1−F_e ≤ 1e-6`; operator-identity `≤ 1e-12`/unitary `≤ 1e-10`) — M7 is a
  pure-Hamiltonian / exact-dense error (no collapse, no finite-step MCWF). NOT the GROSS+convergence
  tier (that is only for collapse-bearing first-order MCWF). Support size: **1 site, d=2** (and a d=3
  embed check that the qutrit-carrier op is the 2-block + zero generator on level 2).
- **Independent-operator plan:** hand-typed `ref_H_M7` (§3) in the cert module, importing only
  `_hamiltonian_matrix_for_term` from the carrier; `1−F_e` via `_choi_state_from_kraus`+
  `_state_fidelity` (the channels these helpers build from the per-term op are independent of the
  carrier's grouping/lowering path). Wrong-axis (Z→X/Z→Y) + wrong-unit negative controls; a corruption
  falsifier (carrier axis map `COH_RZ→Z` corrupted to `X` → hand-typed ref catches it; circular ref
  would false-pass). The cert mirrors `tests/test_m6_coherent_rx_constraint_ledger.py` with the axis
  swapped X→Z.
- **GPU-only, serialized:** assert `torch.cuda.is_available()`; CUDA-missing fails the collection
  (memory rule). Scripted-execution; the cert lands commit-gated.
- **If built heavy:** ≥3 disjoint-ownership builders (reference-operator / cert-wiring /
  control+falsifier) + an un-led reviewer given only this prereg + the artifacts. (M7 is a thin
  sibling of the landed M6, so a single-builder + reviewer pass is also acceptable per the
  light-weight-path rule — the heavy split is reserved for novel physics, which M7 is not.)
```
