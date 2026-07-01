# M6 coherent_rx_overrotation — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: **PRE-REGISTRATION, 2026-06-29.** Predictions written BEFORE the run; a miss is a finding,
not a re-fit. First of the four Axis-1 1q coherent over-rotation knobs (M6 rx, M7 rz, M20 ry,
M27 h-axis; `axis1_mechanism_completeness_prereg.md` group 1). Does NOT claim Axis-1 completion and
adds NO metric to `docs/METRICS.md` (`1−F_e` already in the ledger).

## 0. Grounding ledger (the corresponding papers — all 精读 + noted)

| sub-axis / mechanism | mechanism paper | observable paper | reading note | in-repo code (reuse) |
|---|---|---|---|---|
| 1q RX coherent over-rotation `U_θ = exp(−iθ_X X)` (single-qubit term of `H_θ = Σ_k θ_k P_k`) | Kaufmann, Rojkov & Reiter, arXiv:2307.08741 (Eq. 2: `E_{P,θ}=U_θ∘P∘U_I`, `U_θ=exp(−iH_θ)`, `H_θ=Σ_k θ_k P_k`; first-order coherent in off-diagonal PTM) **+ Sheldon–Bishop–Magesan–Filipp–Chow–Gambetta arXiv:1504.06597** (Eq. 1 over-/under-rotation `U=exp(−i(ε/2)r̂·σ)`; intentional π/64–π/256 over-rotation injected on a transmon) **+ axis-specific Lazăr/Ficheux arXiv:2212.01077** (drive-amplitude mis-calibration → measured over-rotation 0.4°) — ≥2 DIRECT-physical, text-verified 2026-06-30 | observable below | `coherent_robust_pauli_2307.08741.md`, `sheldon_iterative_rb_overrotation_1504.06597.md`, `lazar_drive_nonlinearity_overrotation_2212.01077.md` | `simulator/axis1_mcwf_mps_execution.py:_hamiltonian_matrix_for_term` (family `COH_RX` → `_coherent_family_generator` → `H=(coeff/2)X`) |
| process (entanglement) infidelity `1−F_e` of a CPTP map / unitary error | Schumacher, PRA 54, 2614 (1996) (`F_e` def + Kraus form `Σ_k|Tr(ρE_k)|²`) | Nielsen, arXiv:quant-ph/0205035 (Eq. 3 `F_avg=(d F_e+1)/(d+1)`; Eq. 16 operator-basis `F_e`) | `docs/papers/reading_notes/schumacher_nielsen_entanglement_fidelity_quant-ph-0205035.md` | `forward/joint_lindbladian.py:_choi_state_from_kraus`, `_state_fidelity`, `composed_vs_joint_infidelity`, `assemble_substep_channel` |
| RX over-rotation as the canonical M6 definition | — | — | `docs/error_mechanisms.md` (M6 = 1q `RX(epsilon)` coherent unitary) | `mechanisms/catalog.py:MECHANISMS["M6"]` |

## 1. The mechanism (anchored; REUSE existing carrier code)

**M6 = coherent_rx_overrotation = a 1q `RX(ε)` coherent unitary error** (`docs/error_mechanisms.md`),
the over-rotation knob on the ideal X-axis control (`DR`/`CTRL_*`). It is the single-qubit `θ_X X`
term of the Kaufmann–Rojkov–Reiter coherent-layer generator `H_θ = Σ_k θ_k P_k` (2307.08741 Eq. 2),
i.e. the coherent over-rotation the twin's teacher composes with stochastic Pauli.

**Carrier form (the operator under test — REUSE, do not rebuild):** family `COH_RX`, lowered by
`simulator/axis1_mcwf_mps_execution.py:_hamiltonian_matrix_for_term` → `_embed_coherent_generator` →
`_coherent_family_generator`, which returns on the 2-level computational subspace

```
H_M6 = (coeff / 2) · X ,    X = [[0,1],[1,0]]          # rad/ns; embedded with identity on any leaked level
```

so the realized error gate over a substep `dt` is

```
U_M6 = exp(−i · H_M6 · dt) = exp(−i (ε/2) X) = RX(ε) ,   ε ≡ coeff · dt   (the over-rotation angle, rad)
```

**Swept range (NOT a frozen constant):** `ε ∈ {3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3}` rad (≈ the
calibration-residual regime; 2307.08741 reports single-qubit coherent angles ≲ 0.1 rad, stable/
systematic over 19 days). The cert uses `coeff` and `dt_ns` independently so `ε = coeff·dt` is
swept by varying either.

### 1a. RESOLUTION of the COH_* placement ambiguity (decided here, before coding)

`mechanisms/axis1_primitives.py` **DECLARES** `COH_*` in `SUPPORTED_AXIS1_PRIMITIVES` /
`COHERENT_PAULI_FAMILIES` (lines 19–37, 54) but its `lower_two_qubit_axis1_primitives()` for-loop
(lines 280–327) has **NO `COH_*` branch** — `registry.lower([...COH_RX...])` returns an empty
`H_list` silently. **Declaration-without-lowering is a faithfulness trap.** The single canonical
owning module for COH_* lowering is `axis1_mcwf_mps_execution._hamiltonian_matrix_for_term`.

**Decision (PREFERRED fix 1, per the brief):** DELETE the `COH_*` / `COHERENT_PAULI_FAMILIES`
declarations from `mechanisms/axis1_primitives.py` (the `ONE_SITE_COHERENT_FAMILIES`,
`TWO_SITE_COHERENT_FAMILIES`, `CROSSTALK_COHERENT_FAMILIES`, `COHERENT_PAULI_FAMILIES` defs and their
inclusion in `SUPPORTED_AXIS1_PRIMITIVES`), so the registry no longer advertises a lowering it does
not perform, leaving `axis1_mcwf_mps_execution` the sole, unambiguous COH_* lowering owner. (Do NOT
also do fix 2 — pick one.) **Until this lands, every cert and build imports the operator under test
from `axis1_mcwf_mps_execution._hamiltonian_matrix_for_term` ONLY, never from the
`axis1_primitives` registry** — the same surface the qutrit-leakage de-circularized cert uses.
[Epistemic class (c) — a build/placement decision, not a physics claim.]

## 2. Predicted observable (class (b) bands; ANCHORED — `1−F_e`, the RIGHT one, not invented)

**Observable = process (entanglement) infidelity `1 − F_e`** between the substep channel WITH the M6
error knob and the substep channel WITHOUT it (the ideal/no-error reference) — the standard
`axis1_mechanism_completeness_prereg.md` line-98 cert observable (`assemble_substep_channel` →
Choi-state `F_e`). Schumacher/Nielsen def (reading note); for a pure RX over-rotation vs identity:

- **(B1) EXACT closed form [b-band, derivable to a-exact]:**
  `1 − F_e(RX(ε), I) = 1 − |Tr(RX(ε))/2|² = 1 − cos²(ε/2) = sin²(ε/2)`.
  Predicted: the carrier-side `1−F_e` (via `_choi_state_from_kraus`+`_state_fidelity`) equals
  `sin²(ε/2)` to the Uhlmann-estimator floor (~2e-8), monotone increasing in `|ε|`, **even in ε**
  (`1−F_e(ε)=1−F_e(−ε)`: over- and under-rotation of equal magnitude are equally infidel).
- **(B2) LEADING-ORDER scaling [b-band]:** `1 − F_e ≈ ‖G‖²_F/d = ε²/4` with `G=(ε/2)X` (METRICS.md
  `/d`, d=2). Predicted **quadratic** law: `1−F_e ∝ ε²` at small ε; `(1−F_e)/ε² → 1/4` as `ε→0`.
  The exact form deviates from `ε²/4` at `O(ε⁴)` (since `sin²(ε/2)=ε²/4 − ε⁴/48 + …`) — a registered
  higher-order finding, NOT a carrier bug.
- **(B3) AVG-GATE link [b-band]:** `1 − F_avg = (d/(d+1))(1−F_e) = (2/3)sin²(ε/2) ≈ ε²/6` — reported
  as a companion ONLY if an RB-comparable number is wanted; `1−F_e` stays the headline (carry the
  convention with the number).

**Statistic flagged INSUFFICIENT (do NOT headline):** `1−F_e` (or `1−F_avg`) is a *scalar average*
measure — coherent and stochastic channels of equal infidelity are indistinguishable by it
(reading-note Limitations; the surface-code analogue is the Bravyi twirl-underestimate,
`correcting_coherent_errors_surface_1710.02270.md`). The cert therefore ALSO gates the **direct
operator/generator identity** (B4 below), the structural witness `1−F_e` alone cannot provide.

- **(B4) OPERATOR identity [a-exact, the load-bearing gate]:** the carrier generator equals the
  hand-typed reference: `‖H_carrier − H_ref‖_F ≤ 1e-12` and `‖U_carrier − U_ref‖_F ≤ 1e-10`, with
  `H_carrier` Hermitian (`‖H−H†‖_F ≤ 1e-12`) and traceless (`|Tr H| ≤ 1e-12`). A miss is a CARRIER
  PHYSICS BUG — the finding a `1−F_e`-only or circular cert could never surface.

## 3. Independent ground truth (non-circular) — the HAND-TYPED reference operator

The reference is **hand-typed in the cert from the literature equations**, importing NO carrier
symbol (`_coherent_family_generator`, `_embed_coherent_generator`, `ONE_SITE_COHERENT_FAMILIES`
appear NOWHERE in the cert's executable code). The carrier side imports ONLY
`_hamiltonian_matrix_for_term` (the object under test) — exactly the de-circularized
`axis1_qutrit_leakage_certification` pattern (`test_axis1_wc_decircularized.py`).

**Reference operator spec (PROVENANCE-carried, transcribed not invented):**

```
# M6 reference generator on the 2-level computational subspace (d=2), identity on leaked levels.
# H_M6 = (coeff/2) * sigma_x.
#   sigma_x = [[0,1],[1,0]]                         <- Pauli-X, standard (Nielsen & Chuang Eq. 2.1).
#   factor 1/2: RX(eps)=exp(-i (eps/2) X), eps=coeff*dt  <- single-qubit rotation generator convention
#               (Nielsen & Chuang Eq. 4.4-4.7; standard "R_x(theta)=exp(-i theta X/2)").
#   the over-rotation MECHANISM (coherent gate-axis term theta_X X) is grounded in
#               Kaufmann-Rojkov-Reiter arXiv:2307.08741 Eq. 2 (H_theta = sum_k theta_k P_k).
def ref_H_M6(coeff, dim, device):           # dim = local site dim (2, or 3 if qutrit carrier)
    X = tensor([[0,1],[1,0]], complex128, device)
    H = zeros((dim, dim), complex128, device)
    H[:2,:2] = 0.5 * coeff * X               # identity (zero generator) on level>=2
    return H
# error unitary:  U = matrix_exp(-1j * dt_ns * H)  ==  RX(eps) on the 2-block, eps = coeff*dt_ns.
# EXACT 1-F_e reference (unitary vs identity, d=2):  1 - |Tr(U)/2|^2  ==  sin^2(eps/2).
# LEADING 1-F_e reference:  ||(eps/2) X||_F^2 / 2  ==  eps^2/4.
```

This is a closed-form theorem (the RX(ε) matrix + `F_e=|Tr V/d|²`), independent of the implementation.
A from-scratch numerical confirmation on RTX 5090 already ran (scratchpad
`m6_fe_derivation_check.py`): `sin²(ε/2)` vs the carrier Choi machinery agree to ~2e-8 across
ε∈{0.3…1e-3}; `ε²/4` tracks the exact form with the predicted `O(ε⁴)` deviation; `H` Hermitian +
traceless residuals exactly 0. (That script is a derivation-check, NOT the cert.)

**Level-discriminating negative control (the control a `1−F_e`-only / wrong-axis cert lacks):** a
**WRONG-AXIS** reference `H_wrong = (coeff/2)·Z` (or `·Y`) must DISAGREE with the carrier:
`‖U_carrier − U_wrong‖_F ≥ 1e-3` for ε not a multiple of 2π. (RX, RY, RZ of the same angle are
distinct gates; a wrong Pauli axis is the M6 analogue of the leakage cert's wrong-level control.) A
weaker `wrong_unit` control (treat `coeff` as the angle, dropping the ×dt) is retained as a second
control. **Show the control trips:** corrupt the carrier axis map `COH_RX→X` to `Z` and confirm the
hand-typed reference CATCHES it (diff ≥ 1e-3, cert fails), while a reference derived FROM the
corrupted carrier map would mirror it to diff 0 (false-pass) — the C2-falsifier shape of
`test_wc_cert_catches_corrupted_carrier_level_map`.

## 4. Bounded simplifications (declared; unbounded ⇒ STOP)

- **S1 — RX error treated as a STRICT unitary (pure Hamiltonian, no collapse).** Class (a) on the
  certified slice: M6 is by definition a coherent unitary (`docs/error_mechanisms.md`); the cert
  certifies the Hamiltonian generator + the exact `exp(−iHdt)` gate. Error vs faithful: 0 (it IS the
  faithful object). ⇒ **STRICT gate tier** `1−F_e ≤ 1e-6` and operator identities `≤ 1e-12/1e-10`
  (no collapse ⇒ no finite-microstep MCWF error; this is the exact-dense regime, not the GROSS tier).
- **S2 — 2-level computational subspace; identity on leaked levels.** Class (a): the M6 RX knob acts
  on the computational `{|0>,|1>}` block; in a qutrit/ququart carrier the generator is the same
  2-block embedded with the zero generator on level ≥ 2 (matches `_embed_coherent_generator`). Error
  vs faithful: 0 within the stated semantics (M6 does not drive leakage — that is M34/LEAK_*).
- **S3 — `ε = coeff·dt` constant across the substep (no intra-substep drift).** Class (b): drift of
  the over-rotation angle ACROSS cycles is M13 = Axis-2 (frozen), not M6. Error bound: `O(Δε/ε)`;
  within one substep with a declared instantaneous `coeff`, exact. Cross-cycle drift is explicitly
  out of this slice.
- **S4 — `1−F_e` reported via the Uhlmann sqrt/eigh Choi estimator (≈2e-8 floor).** Class (c): the
  estimator floors at ~2e-8 (documented in `composed_vs_joint_infidelity`), so `1−F_e` is reported as
  the standard-metric companion at that resolution; the LOAD-BEARING zero-tolerance gate is the
  direct operator identity (B4) at 1e-12, not the `1−F_e` value.

## 5. Epistemic status (METRICS-ladder)

- **(a) exact:** the operator identity B4 (`H_carrier = (coeff/2)X` = hand-typed ref, Hermitian,
  traceless; `U=RX(ε)`); the closed forms `1−F_e=sin²(ε/2)` and `‖G‖²_F/d=ε²/4`; the wrong-axis
  control disagreement. These are theorems/identities — the only class anything is built on.
- **(b) bands:** B1 (carrier `1−F_e` = `sin²(ε/2)` to estimator floor), B2 (quadratic `∝ε²`, ratio
  →1/4), B3 (`1−F_avg=(2/3)·`), and the `O(ε⁴)` exact-vs-leading deviation. A miss is a finding.
- **(c) gates:** STRICT numeric tiers (`1−F_e ≤ 1e-6`, operator `≤ 1e-12/1e-10`, control `≥ 1e-3`);
  the placement-fix decision (§1a); the swept ε grid.
- **Headline verdict stays PROVISIONAL** until the GPU cert runs green AND the corruption-falsifier
  trips. Reportable + go/no-go; nothing is built on it. No Axis-1-completion claim, no METRICS change.

## 6. Build org + gate plan

- **Gate tier:** **STRICT** (`1−F_e ≤ 1e-6`; operator-identity `≤ 1e-12`/unitary `≤ 1e-10`) — M6 is
  a pure-Hamiltonian / exact-dense error (no collapse, no finite-step MCWF). NOT the GROSS+convergence
  tier (that is only for collapse-bearing first-order MCWF). Support size: **1 site, d=2** (and a
  d=3 embed check that the qutrit-carrier op is the 2-block + identity).
- **Independent-operator plan:** hand-typed `ref_H_M6` (§3) in the cert module, importing only
  `_hamiltonian_matrix_for_term` from the carrier; `1−F_e` via `_choi_state_from_kraus`+
  `_state_fidelity` (the channels these helpers build from the per-term op are independent of the
  carrier's grouping/lowering path). Wrong-axis (X→Z/Y) + wrong-unit negative controls; a corruption
  falsifier (carrier axis map corrupted → hand-typed ref catches it; circular ref would false-pass).
- **GPU-only, serialized:** assert `torch.cuda.is_available()`; CUDA-missing fails the collection
  (memory rule). Scripted-execution; the placement fix (§1a) + cert land commit-gated.
- **If built heavy:** ≥3 disjoint-ownership builders (carrier-placement-fix / reference-operator /
  cert-wiring) + an un-led reviewer given only this prereg + the artifacts.
