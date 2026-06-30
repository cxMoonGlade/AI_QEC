# M20 coherent_ry_overrotation — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: **PRE-REGISTRATION, 2026-06-29.** Predictions written BEFORE the run; a miss is a finding,
not a re-fit. Third of the four Axis-1 1q coherent over-rotation knobs (M6 rx, M7 rz, **M20 ry**,
M27 h-axis; `axis1_mechanism_completeness_prereg.md` group 1). Direct sibling of the landed M6
(`m6_coherent_rx_overrotation_prereg.md`) and M7 (`m7_coherent_rz_overrotation_prereg.md`) — identical
machinery, **Y axis instead of X / Z**. Does NOT claim Axis-1 completion and adds NO metric to
`docs/METRICS.md` (`1−F_e` already in the ledger).

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)

| sub-axis / mechanism | mechanism paper | observable paper | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| 1q RY coherent over-rotation `U_θ = exp(−iθ_Y Y)` (single-qubit `θ_Y Y` term of `H_θ = Σ_k θ_k P_k`) | Kaufmann, Rojkov & Reiter, arXiv:2307.08741 (Eq. 2: `E_{P,θ}=U_θ∘P∘U_I`, `U_θ=exp(−iH_θ)`, `H_θ=Σ_k θ_k P_k`; the single-qubit set is the 3 rotations `{θ_X X, θ_Y Y, θ_Z Z}` — `θ_Y Y` IS M20; first-order coherent in off-diagonal PTM) | — (mechanism def; observable below) | `docs/papers/reading_notes/coherent_robust_pauli_2307.08741.md` | `simulator/axis1_mcwf_mps_execution.py:_hamiltonian_matrix_for_term` (family `COH_RY` → `_coherent_family_generator` → `H=(coeff/2)Y`, axis map `_ONE_Q_FAMILY_TO_AXIS["COH_RY"]="Y"`, line 1044) |
| process (entanglement) infidelity `1−F_e` of a CPTP map / unitary error | Schumacher, PRA 54, 2614 (1996) (`F_e` def + Kraus form `Σ_k|Tr(ρE_k)|²`) | Nielsen, arXiv:quant-ph/0205035 (Eq. 3 `F_avg=(d F_e+1)/(d+1)`; Eq. 16 operator-basis `F_e`; line 75 def `F_e=⟨φ|(I⊗E)(φ)|φ⟩`) | `docs/papers/reading_notes/schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md` | `forward/joint_lindbladian.py:_choi_state_from_kraus`, `_state_fidelity`, `composed_vs_joint_infidelity`, `assemble_substep_channel` |
| RY over-rotation as the canonical M20 definition | — | — | `docs/error_mechanisms.md` (M20 line 111 = 1q `RY(epsilon)` coherent unitary, "coherent Y-axis control error") | `mechanisms/catalog.py:MECHANISMS["M20"]` |

**Why M20's grounding is at threshold from the same close-reads as M6/M7.** The mechanism paper
(2307.08741) is `H_θ = Σ_k θ_k P_k` over the FULL single-qubit Pauli set `{X,Y,Z}` (Eq. 2 / Sec. II:
"3 single ... rotations per [qubit]"); M6 is the `θ_X X` term, M7 is the `θ_Z Z` term, **M20 is the
`θ_Y Y` term** — the SAME equation, same paper, same close-read. The observable note already states
the `1−F_e` def + Kraus form + the `/d` leading-order ledger that M20 reuses verbatim (the closed
form is axis-agnostic; see §2 B1). No NEW physics is introduced by M20 — only the axis selector
changes (X/Z → Y). The Y axis is in fact the MOST hardware-relevant of the three single-qubit axes
for this paper: the leading two-qubit coherent error reported on `ibm_lagos` is `P_YZ` between CX-pair
qubits, so the Y-axis rotation is an experimentally documented coherent error direction (reading note
C3), not a formal placeholder.

## 1. The mechanism (anchored; REUSE existing carrier code)

**M20 = coherent_ry_overrotation = a 1q `RY(ε)` coherent unitary error** (`docs/error_mechanisms.md`
line 111), the over-rotation knob on the ideal Y-axis control (a coherent Y-axis control error). It is
the single-qubit `θ_Y Y` term of the Kaufmann–Rojkov–Reiter coherent-layer generator
`H_θ = Σ_k θ_k P_k` (2307.08741 Eq. 2), i.e. the coherent Y-axis over-rotation the twin's teacher
composes with stochastic Pauli.

**Carrier form (the operator under test — REUSE, do not rebuild):** family `COH_RY`, lowered by
`simulator/axis1_mcwf_mps_execution.py:_hamiltonian_matrix_for_term` → `_embed_coherent_generator` →
`_coherent_family_generator` (axis map `_ONE_Q_FAMILY_TO_AXIS["COH_RY"]="Y"`, line 1044, then
`P=_pauli_2level("Y")=[[0,−i],[i,0]]`, line 1002), which returns on the 2-level computational subspace

```
H_M20 = (coeff / 2) · Y ,    Y = [[0,−i],[i,0]]      # rad/ns; embedded with the zero generator on any leaked level
```

so the realized error gate over a substep `dt` is

```
U_M20 = exp(−i · H_M20 · dt) = exp(−i (ε/2) Y) = RY(ε) = [[cos(ε/2), −sin(ε/2)], [sin(ε/2), cos(ε/2)]] ,
        ε ≡ coeff · dt   (the over-rotation angle, rad)
```

**Swept range (NOT a frozen constant):** `ε ∈ {3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3}` rad (≈ the
calibration-residual regime; 2307.08741 reports single-qubit coherent angles ≲ 0.1 rad, systematic +
stable over 19 days). The cert uses `coeff` and `dt_ns` independently so `ε = coeff·dt` is swept by
varying either.

### 1a. RESOLUTION of the COH_* placement ambiguity (ALREADY LANDED with M6 — inherited)

The brief's placement ambiguity was resolved by the M6 work and **M20 inherits the resolution**:
`mechanisms/axis1_primitives.py` lines 19–24 now read *"COH_* / COHERENT_PAULI_FAMILIES are
intentionally NOT declared here ... advertising it here was a declaration-without-lowering
faithfulness trap (M6 pre-registration §1a)"* — the PREFERRED fix-1 (DELETE the COH_* declarations
from the primitives registry, leaving `axis1_mcwf_mps_execution._hamiltonian_matrix_for_term` the
sole, unambiguous COH_* lowering owner) is in the tree (verified 2026-06-29: `grep COH_`
`mechanisms/axis1_primitives.py` shows only the NOTE, no declaration). **The M20 cert imports the
operator under test from `axis1_mcwf_mps_execution._hamiltonian_matrix_for_term` ONLY, never from the
`axis1_primitives` registry** — the same surface the M6/M7 ledgers and the qutrit-leakage
de-circularized cert use. [Epistemic class (c) — a build/placement decision, already executed; no
physics claim.]

## 2. Predicted observable (class (b) bands; ANCHORED — `1−F_e`, the RIGHT one, not invented)

**Observable = process (entanglement) infidelity `1 − F_e`** between the substep channel WITH the M20
error knob and the substep channel WITHOUT it (the ideal/no-error reference) — the standard
`axis1_mechanism_completeness_prereg.md` line-98 cert observable (`assemble_substep_channel` →
Choi-state `F_e`). Schumacher/Nielsen def (reading note); for a pure RY over-rotation vs identity:

- **(B1) EXACT closed form [b-band, derivable to a-exact]:**
  `1 − F_e(RY(ε), I) = 1 − |Tr(RY(ε))/2|² = 1 − |(2cos(ε/2))/2|² = 1 − cos²(ε/2) = sin²(ε/2)`.
  **Axis-agnostic:** for any single-axis SU(2) rotation `R_P(ε)=exp(−i(ε/2)P)`, `P∈{X,Y,Z}`,
  `Tr R_P(ε)=2cos(ε/2)` (traceless `P`, eigenvalues `±1`), so `1−F_e=sin²(ε/2)` is IDENTICAL to M6's
  and M7's — the *scalar* infidelity does not distinguish the axis (it is exactly the "scalar averages
  hide structure" caveat, §B-INSUFFICIENT; the axis is recovered ONLY by the operator gate B4).
  Predicted: the carrier-side `1−F_e` (via `_choi_state_from_kraus`+`_state_fidelity`) equals
  `sin²(ε/2)` to the Uhlmann-estimator floor (~2e-8), monotone increasing in `|ε|`, **even in ε**
  (`1−F_e(ε)=1−F_e(−ε)`: over- and under-rotation of equal magnitude are equally infidel).
- **(B2) LEADING-ORDER scaling [b-band]:** `1 − F_e ≈ ‖G‖²_F/d = ε²/4` with `G=(ε/2)Y`,
  `‖G‖²_F=Tr((ε/2 Y)²)=2·(ε/2)²=ε²/2`, `/d=/2 → ε²/4` (METRICS.md `/d`, d=2; `Y²=I`). Predicted
  **quadratic** law: `1−F_e ∝ ε²` at small ε; `(1−F_e)/ε² → 1/4` as `ε→0`. The exact form deviates
  from `ε²/4` at `O(ε⁴)` (since `sin²(ε/2)=ε²/4 − ε⁴/48 + …`) — a registered higher-order finding,
  NOT a carrier bug.
- **(B3) AVG-GATE link [b-band]:** `1 − F_avg = (d/(d+1))(1−F_e) = (2/3)sin²(ε/2) ≈ ε²/6` — reported
  as a companion ONLY if an RB-comparable number is wanted; `1−F_e` stays the headline (carry the
  convention with the number).

**Statistic flagged INSUFFICIENT (do NOT headline):** `1−F_e` (or `1−F_avg`) is a *scalar average*
measure — coherent and stochastic channels of equal infidelity are indistinguishable by it, AND (the
M20-sharp form of the caveat) `1−F_e` is identical for RX/RY/RZ of the same angle (B1) so it cannot
tell which Pauli axis the rotation is about (reading-note Limitations; the surface-code analogue is
the Bravyi twirl-underestimate, `correcting_coherent_errors_surface_1710.02270.md`). The cert
therefore ALSO gates the **direct operator/generator identity** (B4 below), the structural witness
`1−F_e` alone cannot provide — and for M20 the operator gate is the ONLY thing that distinguishes Y
from X/Z.

- **(B4) OPERATOR identity [a-exact, the load-bearing gate]:** the carrier generator equals the
  hand-typed reference: `‖H_carrier − H_ref‖_F ≤ 1e-12` and `‖U_carrier − U_ref‖_F ≤ 1e-10`, with
  `H_carrier` Hermitian (`‖H−H†‖_F ≤ 1e-12`) and traceless (`|Tr H| ≤ 1e-12`), where `H_ref=(coeff/2)Y`.
  A miss is a CARRIER PHYSICS BUG — the finding a `1−F_e`-only or circular cert could never surface.
  **For M20 this gate is load-bearing in a way it is not for M6:** since `1−F_e` is axis-blind (B1),
  B4 is the SOLE witness that the carrier rotates about Y and not X/Z. M20-sharp: the Pauli-Y matrix
  is the only single-qubit Pauli with imaginary off-diagonal entries (`±i`), so a real-valued
  reference (X) or a diagonal reference (Z) is caught by B4 immediately.

## 3. Independent ground truth (non-circular) — the HAND-TYPED reference operator

The reference is **hand-typed in the cert from the literature equations**, importing NO carrier
symbol (`_coherent_family_generator`, `_embed_coherent_generator`, `ONE_SITE_COHERENT_FAMILIES`,
`_ONE_Q_FAMILY_TO_AXIS`, `_pauli_2level` appear NOWHERE in the cert's executable code). The carrier
side imports ONLY `_hamiltonian_matrix_for_term` (the object under test) — exactly the de-circularized
`axis1_qutrit_leakage_certification` / M6 / M7 ledger pattern (`test_axis1_wc_decircularized.py`,
`test_m6_coherent_rx_constraint_ledger.py`, `test_m7_coherent_rz_constraint_ledger.py`).

**Reference operator spec (PROVENANCE-carried, transcribed not invented):**

```
# M20 reference generator on the 2-level computational subspace (d=2), zero generator on leaked levels.
# H_M20 = (coeff/2) * sigma_y.
#   sigma_y = [[0,-i],[i,0]]                          <- Pauli-Y, standard (Nielsen & Chuang Eq. 2.1).
#   factor 1/2: RY(eps)=exp(-i (eps/2) Y), eps=coeff*dt  <- single-qubit rotation generator convention
#               (Nielsen & Chuang Eq. 4.4-4.7; standard "R_y(theta)=exp(-i theta Y/2)").
#   the over-rotation MECHANISM (coherent gate-axis term theta_Y Y) is grounded in
#               Kaufmann-Rojkov-Reiter arXiv:2307.08741 Eq. 2 (H_theta = sum_k theta_k P_k; the
#               single-qubit Y term theta_Y Y IS M20).
def ref_H_M20(coeff, dim, device):          # dim = local site dim (2, or 3 if qutrit carrier)
    Y = tensor([[0,-1j],[1j,0]], complex128, device)
    H = zeros((dim, dim), complex128, device)
    H[:2,:2] = 0.5 * coeff * Y               # zero generator (identity gate) on level>=2
    return H
# error unitary:  U = matrix_exp(-1j * dt_ns * H)  ==  RY(eps) = [[cos(eps/2),-sin(eps/2)],[sin(eps/2),cos(eps/2)]]
#                 on the 2-block, eps = coeff*dt_ns.
# EXACT 1-F_e reference (unitary vs identity, d=2):  1 - |Tr(U)/2|^2  ==  sin^2(eps/2).
# LEADING 1-F_e reference:  ||(eps/2) Y||_F^2 / 2  ==  eps^2/4.
```

This is a closed-form theorem (the `RY(ε)` matrix + `F_e=|Tr V/d|²`), independent of the
implementation. A from-scratch numerical confirmation on RTX 5090 already ran (scratchpad
`m20_fe_derivation_check.py`, 2026-06-29): the carrier `COH_RY` op equals `(coeff/2)Y` to **opdiff 0**
across ε∈{0.3…1e-3} and dim∈{2,3}; `U=RY(ε)` to **0**; `sin²(ε/2)` vs the carrier Choi `1−F_e` agree
to ~2e-8 (Uhlmann floor); `ε²/4` tracks the exact form with the predicted `O(ε⁴)` deviation
(ε=0.3 → lead_dev 1.7e-4 ≈ ε⁴/48; ε=0.1 → 2.1e-6); `H` Hermitian + traceless residuals exactly 0;
`1−F_e` even in ε to 0.0; wrong-axis X/Z and wrong-unit controls all disagree by ≥ 7e-2 at ε=0.1.
(That script is a derivation-check, NOT the cert.)

**Wrong-axis negative control (the control a `1−F_e`-only / scalar cert structurally CANNOT provide
for M20) — the load-bearing M20 control:** a **WRONG-AXIS** reference `H_wrong = (coeff/2)·X` (or `·Z`)
must DISAGREE with the carrier: `‖U_carrier − U_wrong‖_F ≥ 1e-3` for ε exercised at `ε ≥ 1e-2`
(derivation-check: `|U_RY−U_RX| = |U_RY−U_RZ| ≈ ε` for small ε, so ε=1e-2→~5e-3 ≥ 1e-3; at the very
smallest ε=1e-3 the diff is ~5e-4 < 1e-3, so the wrong-axis gate is registered to fire at ε≥1e-2 —
class (c) gate parameter). RY vs RX, RY vs RZ of the same angle are distinct gates; a wrong Pauli axis
is the M20 analogue of the leakage cert's wrong-level control. Because `1−F_e` is identical for
RX/RY/RZ (B1), **this wrong-axis operator control is the ONLY thing in the cert that detects a
corrupted COH_RY axis map** — making it strictly necessary for M20 (more so than for a scalar-only
cert, which has the angle even if blind to the axis). A weaker `wrong_unit` control (treat `coeff` as
the angle, dropping the ×dt → `coeff·Y`) is retained as a second control. **Show the control trips:**
corrupt the carrier axis map `COH_RY→Y` to `X` (or `Z`) and confirm the hand-typed reference CATCHES
it (diff ≥ 1e-3, cert fails), while a reference derived FROM the corrupted carrier map would mirror it
to diff 0 (false-pass) — the C2-falsifier shape of `test_wc_cert_catches_corrupted_carrier_level_map`
/ `test_m6_...corrupted...` / `test_m7_L3b_broken_wrong_axis_rx_trips`.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)

- **S1 — RY error treated as a STRICT unitary (pure Hamiltonian, no collapse).** Class (a) on the
  certified slice: M20 is by definition a coherent unitary (`docs/error_mechanisms.md` line 111); the
  cert certifies the Hamiltonian generator + the exact `exp(−iHdt)` gate. Error vs faithful: 0 (it IS
  the faithful object). ⇒ **STRICT gate tier** `1−F_e ≤ 1e-6` and operator identities `≤ 1e-12/1e-10`
  (no collapse ⇒ no finite-microstep MCWF error; this is the exact-dense regime, not the GROSS tier).
- **S2 — 2-level computational subspace; zero generator on leaked levels.** Class (a): the M20 RY knob
  acts on the computational `{|0>,|1>}` block; in a qutrit/ququart carrier the generator is the same
  2-block embedded with the zero generator on level ≥ 2 (matches `_embed_coherent_generator`,
  confirmed by the derivation-check dim=3 run: opdiff 0). Error vs faithful: 0 within the stated
  semantics. **M20-specific note:** `RY(ε)` is a real-orthogonal rotation in the `{|0>,|1>}` plane and
  leaves `|2⟩` UNCHANGED (`exp(0)=1` on the leaked level) — i.e. M20 imparts NO population/phase to
  leaked levels; any leaked-level coupling is a DIFFERENT mechanism (leakage transport, M34/LEAK_*),
  not M20. This is the same "identity on leaked levels" simplification as M6 S2 / M7 S2.
- **S3 — `ε = coeff·dt` constant across the substep (no intra-substep drift).** Class (b): drift of
  the over-rotation angle ACROSS cycles is M13 = Axis-2 (frozen), not M20. Error bound: `O(Δε/ε)`;
  within one substep with a declared instantaneous `coeff`, exact. Cross-cycle drift is explicitly out
  of this slice.
- **S4 — `1−F_e` reported via the Uhlmann sqrt/eigh Choi estimator (≈2e-8 floor).** Class (c): the
  estimator floors at ~2e-8 (documented in `composed_vs_joint_infidelity`; confirmed by the
  derivation-check |d|~2e-8), so `1−F_e` is reported as the standard-metric companion at that
  resolution; the LOAD-BEARING zero-tolerance gate is the direct operator identity (B4) at 1e-12, not
  the `1−F_e` value.

## 5. Epistemic status (METRICS-ladder)

- **(a) exact:** the operator identity B4 (`H_carrier = (coeff/2)Y` = hand-typed ref, Hermitian,
  traceless; `U=RY(ε)`); the closed forms `1−F_e=sin²(ε/2)` and `‖G‖²_F/d=ε²/4`; the wrong-axis
  control disagreement (at ε≥1e-2); the even-in-ε symmetry. These are theorems/identities — the only
  class anything is built on.
- **(b) bands:** B1 (carrier `1−F_e` = `sin²(ε/2)` to estimator floor; axis-agnostic scalar), B2
  (quadratic `∝ε²`, ratio →1/4), B3 (`1−F_avg=(2/3)·`), and the `O(ε⁴)` exact-vs-leading deviation. A
  miss is a finding.
- **(c) gates:** STRICT numeric tiers (`1−F_e ≤ 1e-6`, operator `≤ 1e-12/1e-10`, wrong-axis `≥ 1e-3`
  at ε≥1e-2); the placement-fix decision (§1a, inherited); the swept ε grid.
- **Headline verdict stays PROVISIONAL** until the GPU cert runs green AND the corruption-falsifier
  trips. Reportable + go/no-go; nothing is built on it. No Axis-1-completion claim, no METRICS change.

## 6. Build org + gate plan

- **Gate tier:** **STRICT** (`1−F_e ≤ 1e-6`; operator-identity `≤ 1e-12`/unitary `≤ 1e-10`) — M20 is a
  pure-Hamiltonian / exact-dense error (no collapse, no finite-step MCWF). NOT the GROSS+convergence
  tier (that is only for collapse-bearing first-order MCWF). Support size: **1 site, d=2** (and a d=3
  embed check that the qutrit-carrier op is the 2-block + zero generator on level 2).
- **Independent-operator plan:** hand-typed `ref_H_M20` (§3) in the cert module, importing only
  `_hamiltonian_matrix_for_term` from the carrier; `1−F_e` via `_choi_state_from_kraus`+
  `_state_fidelity` (the channels these helpers build from the per-term op are independent of the
  carrier's grouping/lowering path). Wrong-axis (Y→X / Y→Z) + wrong-unit negative controls; a
  corruption falsifier (carrier axis map `COH_RY→Y` corrupted to `X` → hand-typed ref catches it;
  circular ref would false-pass). The cert mirrors `tests/test_m7_coherent_rz_constraint_ledger.py`
  with the axis swapped Z→Y (the L1–L10 invariant set carries over verbatim; only the reference Pauli
  matrix, the family string `COH_RZ→COH_RY`, and the wrong-axis controls `X/Y → X/Z` change).
- **GPU-only, serialized:** assert `torch.cuda.is_available()`; CUDA-missing fails the collection
  (memory rule). Scripted-execution; the cert lands commit-gated.
- **If built heavy:** ≥3 disjoint-ownership builders (reference-operator / cert-wiring /
  control+falsifier) + an un-led reviewer given only this prereg + the artifacts. (M20 is a thin
  sibling of the landed M6/M7, so a single-builder + reviewer pass is also acceptable per the
  light-weight-path rule — the heavy split is reserved for novel physics, which M20 is not.)
