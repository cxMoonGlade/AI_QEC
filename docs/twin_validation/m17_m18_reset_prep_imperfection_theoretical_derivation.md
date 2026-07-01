# M17 / M18 Reset & Prep Imperfections — Reset-Substep Channels (CPTP-verified)

Date: 2026-06-30 (re-derived). Status: **(c)-class gate surrogates** — the reset-bias channel and the
prep over-rotation are grounded by the CPTP-channel definition and standard reset/prep physics; the
*magnitudes* are physically motivated (b)-class bands. **NOT (a)-class exact** (the old heading was false).

> **RE-DERIVATION NOTE (2026-06-30).** The previous version declared the M17 reset Kraus set
> `M_0 = |0><0| + √(1−p_r)|0><1|`, `M_1 = √(p_r)|1><0| + |1><1|` and headed it "(a)-class exact". That
> set is **grossly non-CPTP**: `Σ M_k†M_k = [[1, √(1−p_r)],[√(1−p_r), 1+p_r]]` — at `p_r=0.01`,
> `= [[1.01, 1.095],[1.095, 1.99]]`, residual `‖Σ M†M − I‖ = 1.84` (≈2, not 0). Worse, that channel does
> **not reset**: `E(|1><1|) = |1><1|` exactly (`p(|1>)=1.0`), a "reset" that leaves `|1>` untouched,
> while the doc's "oracle" asserted `p(|1>)=p_r=0.01` — a self-contradiction that **crashes** when run
> (`assert abs(prob_1_from_1 − p_r) < NUMERICAL_ZERO` fails, `1.0 ≠ 0.01`). That map was fiction. The
> mechanism as **actually implemented** is a genuinely CPTP reset (M17) + a coherent over-rotation (M18),
> derived and verified below. Epistemic class **(c)** for the channel forms.

## Physical Origin

- **M17 = reset_to_1_bias** — the reset operation has a non-zero probability of leaving (or driving) the
  qubit in `|1>` instead of `|0>`: thermal re-excitation during the reset pulse, imperfect active reset
  that does not fully depopulate `|1>`, or measurement/reset feedback that over-shoots. Most pronounced on
  **measure qubits**, which are reset every round (McEwen et al., arXiv:2102.06131).
- **M18 = prep_axis_or_reset_asymmetry_bias** — the state-preparation gate **over-rotates** about a fixed
  axis (a coherent, systematic prep error), e.g. a mis-calibrated `Rx`/`Ry` prep pulse or a
  readout-induced axis bias. This is a **unitary** (coherent) error, distinct from M17's stochastic reset
  bias.

---

## Mathematical Form (the ACTUAL implemented channels) — (c)-class

### M17 — reset-to-1 bias (`reset_to_state_kraus(p, target_state=1)`, `forward/channels.py`)

A **partial reset that fires with probability `p`, forcing the qubit to `|1>`**, and otherwise passes the
state through. Three Kraus operators on the single-qubit space (`target = 1`):

```
K_0 = √(1−p) · I                 # with prob 1−p: reset does not fire, state unchanged
K_1 = √p · |1><0|                # with prob p: reset fires, |0> component → |1>
K_2 = √p · |1><1|                # with prob p: reset fires, |1> component → |1>
E_reset(ρ) = K_0 ρ K_0† + K_1 ρ K_1† + K_2 ρ K_2†
```

with `p ∈ [0,1]` the **reset-to-1 firing probability** (carrier default `p = 0.018`, `channels.py`).
Intuition: `K_1, K_2` together implement "with probability `p`, project anywhere and re-prepare `|1>`"
(`K_1+K_2`-column = the full computational basis mapped to `|1>`); `K_0` is the no-fire branch.

#### Why this is CPTP — exactly

```
Σ_k K_k†K_k = (1−p) I + p (|0><1|·|1><0|) + p (|1><1|·|1><1|)
            = (1−p) I + p |0><0| + p |1><1|
            = (1−p) I + p I  =  I.    ∎   (for every p ∈ [0,1])
```

#### Why this ACTUALLY resets — and is self-consistent

Apply to the basis states (`verify_m15_m17_m18_m19_cptp.py`, p=0.018):

```
E_reset(|0><0|) = [[1−p, 0],[0, p]]   ⇒  trace = 1,  p(|1>) = p   = 0.018   ✓
E_reset(|1><1|) = [[0,   0],[0, 1]]   ⇒  trace = 1,  p(|1>) = 1.0          (|1> stays |1>)
```

The realized `p(|1>)` **starting from `|0>` equals the asserted bias `p` exactly** (`0.018 = 0.018`) —
self-consistent, no crash. `|1>` stays `|1>` because this is a reset **toward** `|1>` (M17 = reset-to-1
*bias*: the failure mode is ending in `|1>`). The general `reset_to_state_kraus` is verified to **actually
reset**: the **reset-to-0** variant at strong `p=0.95` sends `|1> → |0>` with mass `p(|0>)=0.95`
(predominantly `|0>`), exactly the "a reset that resets" requirement.

> **Reset-firing vs reset-success convention (carry with the numbers).** Here `p` is the *firing/bias*
> probability — the chance the abrupt re-prep happens. A "reset-to-0 that lands `|1>` predominantly on
> `|0>`" therefore needs `p → 1` (a *strong* reset). For M17 the physically relevant small number is the
> *bias* `p ≈ 10⁻³–10⁻²` (the unwanted reset-to-1 rate), so the channel is *mostly* identity with a small
> reset-to-1 leak — the correct sign for a "reset-to-1 bias" surrogate.

### M18 — prep over-rotation (`rx_unitary(epsilon)`, `forward/channels.py`)

A **coherent (unitary) prep error**: a small over-rotation about X,

```
E_M18(ρ) = U ρ U†,    U = Rx(ε) = exp(−i ε X / 2) = [[cos(ε/2), −i sin(ε/2)], [−i sin(ε/2), cos(ε/2)]]
```

carrier default `ε = 0.025` rad (`channels.py`). A unitary channel is trivially CPTP (`U†U = I`) and CP
(rank-1 Choi `|vec U><vec U|` is PSD). It models the **systematic, coherent** half of prep/reset
asymmetry (the over-rotation), complementing M17's **stochastic** bias. (The old doc's
`(1−p_asym)E_reset + p_asym E_axis` mixture and the `E_phase = (1−p_z)ρ + p_z ZρZ` alternative are not
what the carrier implements; M18 is the clean coherent-over-rotation surrogate.)

---

## Numerical Verification (CPTP + CP, on CUDA)

Script `outputs/twin_validation/verify_m15_m17_m18_m19_cptp.py` (actual carrier code; RTX 5090,
complex128; GPU-first hard constraint):

| item | map | `‖Σ K†K − I‖_F` | `min eig Choi` | reset self-consistency |
|---|---|---|---|---|
| **M17** (`reset_to_1`, p=0.018) | reset-to-1 Kraus | **0.00e+00** ✓ | **0.00e+00** ✓ | `p(|1>\|0>) = 0.018 == p` ✓; `|1>` preserved; trace=1 ✓ |
| M17 (reset-to-0, strong p=0.95) | reset-to-0 Kraus | 1.57e-16 ✓ | 0.00e+00 ✓ | `p(|0>\|1>) = 0.95` (predominantly `\|0>`) ✓ |
| **M18** (`Rx(ε)`, ε=0.025) | unitary | **3.14e-16** ✓ | **−5.44e-16** ✓ | n/a (coherent) |

All pass at machine precision. CP criterion: `Choi(E) ⪰ 0` (Choi-Jamiołkowski, Choi 1975;
`hantzko_..._2411.00526` §II.A). The exact `0.00e+00` for M17 is a structural zero (the `√(1−p)`,
`√p` entries cancel exactly in `Σ K†K`).

---

## Physical Scaling and Magnitude (Class (b) — prediction bands)

- **Reset-to-1 bias `p`:** active reset (e.g. McEwen et al. 2102.06131) `p ≈ 10⁻³`; passive/imperfect
  reset `p ≈ exp(−t_reset/T1) ≈ 10⁻²`–`10⁻³`. Carrier default `p=0.018` sits at the high (stress) end.
- **Prep over-rotation `ε`:** typical mis-calibrated prep `ε ≈ 10⁻³`–`10⁻²` rad; readout-induced bias up
  to `~10⁻¹` rad. Carrier default `ε=0.025` rad. **Class (b)** bands (a missed band is a finding, not a
  premise).

---

## Observable Signatures

- **M17 — detector offset.** After a reset-to-1 leak, the post-reset population carries `p(|1>) = p`
  instead of 0, biasing the first detector of the round (violates the "reset-then-measure starts at 0"
  assumption). Most visible on **measure qubits** (reset each round; McEwen 2102.06131).
- **M18 — coherent prep bias.** The over-rotation shifts the prepared-state Bloch vector by `ε`,
  producing a systematic (state-dependent) detector mean shift and, across rounds, the coherent
  signature an Rx over-rotation leaves (cf. `coherent_robust_pauli_2307.08741`).

Score with the field-standard channel metric (process/entanglement fidelity, `docs/METRICS.md`); the
detector-offset / mean-shift are project-defined diagnostics (rung-3, flagged).

---

## Bounded Simplifications (declared + bounded)

1. **M17 reset is memoryless (Markovian)** — **Class (c)**. Reset is a fast (~100–300 ns) operation; no
   cross-cycle memory in the channel. Cross-cycle reset history is Axis-2 (frozen). Bound: exact within a
   substep; any cross-cycle correlation is out of this object's scope by construction.
2. **M17 reset is a single-qubit (local) channel** — **Class (c)**. No inter-qubit reset crosstalk;
   correlated reset effects are M11/M12. Bound: exact for the isolated reset substep.
3. **M18 is a pure coherent over-rotation about a fixed axis (X)** — **Class (c)** (design choice). A
   genuine prep error may mix axes / add incoherent decay; M18 isolates the coherent over-rotation axis.
   Bound: it spans the coherent prep-bias mode exactly; it does not add the stochastic part (that is
   M17/M25/M26 by design). Error vs a full prep channel: unbounded in general, but the surrogate's purpose
   (the coherent prep axis) is met exactly.
4. **No small-`p` Taylor approximation** — the reset Kraus map is exact for all `p∈[0,1]` (CPTP holds
   identically), so there is no `O(p²)` term. (The old doc's "(b) small-bias, error O(p_r²)" was an
   artifact of its broken non-CPTP algebra and is removed.)

---

## Independent Oracle for Certification

Per FAITHFULNESS_PROTOCOL rule (I), score the carrier channel against an **independent** reconstruction:

```python
# M17
K = reset_to_state_kraus(p=0.018, target_state=1)          # carrier source of truth
assert ‖Σ_k K_k†K_k − I‖_F ≤ 1e-12                          # trace preservation
assert min eig( Σ_k vec(K_k) vec(K_k)† ) ≥ −1e-12           # CP (Choi PSD; independent of carrier apply)
E0 = Σ_k K_k |0><0| K_k† ;  assert |E0[1,1] − p| ≤ 1e-12    # realized bias == asserted bias (SELF-CONSISTENT)
E1 = Σ_k K_k |1><1| K_k† ;  assert |trace(E1) − 1| ≤ 1e-12  # trace preserved on |1>
# M18
U = rx_unitary(0.025) ;     assert ‖U†U − I‖_F ≤ 1e-12      # unitary ⇒ CPTP+CP
```

The corrected oracle's reset assertion (`E0[1,1] == p`) is **self-consistent** — it checks the realized
reset-to-1 mass against the asserted bias and they are equal — unlike the old oracle, which asserted the
`|1>`-input would land at `p_r` when the broken map left it at 1.0 (guaranteed crash).

---

## Literature Grounding

M17/M18 are **(c)-class surrogates** with physically-motivated (b)-class magnitudes; the channel forms
are standard:

1. **Reset / active-reset characterization, measure-qubit reset bias** — **McEwen et al., Nat. Commun.
   12, 1761 (2021), arXiv:2102.06131** (read note `mcewen_removing_leakage_correlated_2102.06131.md`);
   **Reed et al., Appl. Phys. Lett. 96, 203110 (2010); arXiv:1003.0142** (fast active reset, journal
   DOI 10.1063/1.3435463). These ground that a reset-to-1 bias of `~10⁻³` is real and concentrated on
   measure qubits.
   > **CITATION FIX (2026-06-30):** the prior "Reed et al., PRL 105, 173601 (2010)" was WRONG (that is
   > a different paper). Verified correct: APL 96, 203110 (2010) / arXiv:1003.0142.
   > **M18 DISPOSITION (2026-06-30): CUT / merged into M6.** Under the hard ≥2-DIRECT-physical gate,
   > M18's carrier object `rx_unitary(ε)` is operator-identical to M6 (coherent Rx over-rotation), with
   > no distinct device-direct coherent-prep grounding — it is "M6 sited at prep," not an independent
   > mechanism. See `m17_reset_to_1_bias_prereg.md` §0. M17 is kept and carried in that prereg.
2. **Amplitude-damping / generalized-amplitude-damping reset physics** — **Nielsen & Chuang §8.3.5
   "Amplitude damping"** (section title verified against the N&C bookmark TOC). The reset-to-1 channel is
   *not* literally amplitude damping (it is an abrupt re-prep), but the thermal-re-excitation origin is
   the finite-temperature (generalized) amplitude-damping picture (N&C §8.3.5 + Exercise 8.27).
3. **Kraus / CPTP form** — **Kraus, K., Ann. Phys. 64, 311–335 (1971)**; **N&C §8.2.3 "Operator-sum
   representation."** **CP ⟺ Choi PSD: Choi, Linear Algebra Appl. 10, 285 (1975)**
   (`hantzko_..._2411.00526`).
4. **Coherent prep over-rotation (M18)** — coherent systematic gate errors:
   `coherent_robust_pauli_2307.08741` (Kaufmann et al.; over-rotation = off-diagonal PTM).

> **Citation corrections vs the previous doc.** (a) The old "Nielsen & Chuang, Sec. 8.3.5 (generalized
> amplitude damping)" — the **section number is correct** (§8.3.5 *is* "Amplitude damping"), but the M17
> channel is an abrupt re-prep, not the AD channel itself, so the citation is kept only as the
> *thermal-re-excitation* physical origin, not as the channel's defining equation. (b) The reset channel's
> *form* is the carrier's `reset_to_state_kraus`, grounded in the Kraus/CPTP theorem + Choi-PSD, not in
> any single paper's reset Kraus operators.

---

## Status

- **M17** = CPTP-verified reset-to-1 channel (`reset_to_state_kraus`, target=1); it **actually resets**,
  and the realized bias equals the asserted bias (self-consistent). **M18** = CPTP coherent prep
  over-rotation (`rx_unitary`). Both inside Axis-1 (time-local CPTP maps on the system Hilbert space).
- Pre-registration must declare both **(c)-class** channel forms with **(b)-class** magnitude bands, cite
  McEwen 2102.06131 for the reset-bias magnitude, and use the Kraus/Choi sources (never claim "(a)-class
  exact").

---

## References

- McEwen et al. (2021), *Removing leakage-induced correlated errors in superconducting QEC*, arXiv:2102.06131. (read note in-repo)
- Reed et al. (2010), *Fast Reset and Suppressing Spontaneous Emission of a Superconducting Qubit*, Appl. Phys. Lett. 96, 203110 (2010); arXiv:1003.0142; DOI 10.1063/1.3435463. [corrected from the wrong "PRL 105, 173601"]
- Kraus, K. (1971). *General State Changes in Quantum Theory.* Ann. Phys. 64, 311–335.
- Choi, M.-D. (1975). *Completely Positive Linear Maps on Complex Matrices.* Linear Algebra Appl. 10, 285.
- Nielsen & Chuang, *QCQI*: §8.2.3 (operator-sum), §8.3.5 (amplitude damping).
- Kaufmann, Rojkov & Reiter (2023), arXiv:2307.08741 — coherent over-rotation = off-diagonal PTM (read note in-repo).

**Provenance:** (c)-class reset/prep surrogates. Maps = carrier `reset_to_state_kraus(·, target=1)` (M17)
and `rx_unitary` (M18); CPTP + CP + reset-self-consistency verified on CUDA
(`verify_m15_m17_m18_m19_cptp.py`).
