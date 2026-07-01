# M17 reset_to_1_bias — pre-registration (theory-first)

Date: 2026-06-30. Status: **theory-first pre-registration** (Axis-1 rebuild group 6). Companion
`m17_m18_reset_prep_imperfection_theoretical_derivation.md` (M17 kept here; **M18 CUT/merged into
M6** — see §0). Governs `axis1_rebuild_plan.md`. Discipline: `FAITHFULNESS_PROTOCOL.md` + `METRICS.md`.
**DOIs verified against arXiv/journal pages 2026-06-30.**

## 0. Scope (and the M18 cut)
- **M17 = reset_to_1_bias** — a reset-substep channel imperfection: the reset leaves residual
  population in `|1>` (thermal re-excitation / imperfect active reset / feedback overshoot), most
  pronounced on **measure qubits** (reset every round). Carrier object:
  `forward/channels.py::reset_to_state_kraus(p, target_state=1)`.
- **M18 = prep_axis_or_reset_asymmetry_bias — CUT (merged into M6).** Under the hard ≥2-DIRECT-physical
  gate: M18's carrier object is `rx_unitary(ε)` — **operator-identical to M6** (coherent Rx
  over-rotation, same `1−F_e=sin²(ε/2)`), with no distinct ≥2-DIRECT-physical grounding for a
  prep-specific coherent-unitary (only one imperfect-match ref, Lienhard PRR 4, 013199 (2022), whose
  error is a coherent-phase admixture, not `rx_unitary`; the other SPAM candidate is classical-
  stochastic). M18 is "M6 sited at prep" — a circuit-placement label, not a distinct mechanism →
  **fails the gate independently → cut/merged into M6.** (If a genuinely distinct coherent-prep
  mechanism is wanted later, re-spec it as the Lienhard coherent-phase reset admixture — a different
  operator than `rx_unitary` — and it still needs a 2nd device-direct coherent-prep ref.)

## 1. Grounding — ≥2 DIRECT-physical (verified DOIs)
- **DIRECT-1 (experiment): McEwen et al., "Removing leakage-induced correlated errors in
  superconducting quantum error correction," Nat. Commun. 12, 1761 (2021); arXiv:2102.06131; DOI
  10.1038/s41467-021-21982-y.** Sycamore transmons; multi-level reset returning `|1,2,3>→|0>`; reset
  error ≈10⁻³ = "probability of producing any state other than |0>", with **residual computational
  P(|1>) the dominant reset error** (Fig. S3); reset applied to measure qubits each round. Device-real
  reset-to-residual-|1> imperfection.
- **DIRECT-2 (experiment): Reed, Johnson, Houck, DiCarlo, Chow, Schuster, Frunzio, Schoelkopf, "Fast
  Reset and Suppressing Spontaneous Emission of a Superconducting Qubit," Appl. Phys. Lett. 96, 203110
  (2010); arXiv:1003.0142** (journal DOI 10.1063/1.3435463; arXiv DataCite 10.48550/arXiv.1003.0142).
  Active reset to ground (99.9% in 120 ns; in-situ T1 control); directly quantifies reset infidelity
  = residual excited-state population.
  - **CITATION FIX:** the earlier derivation doc cited Reed as "PRL 105, 173601 (2010)" — **WRONG**
    (that is a different paper). Corrected here to APL 96, 203110 (2010) / arXiv:1003.0142.

Bar **MET** (2 real SC-qubit reset-imperfection experiments). Magnitude `p` is **(b) prediction band**:
active reset `p≈10⁻³` (McEwen), imperfect/passive up to `~10⁻²` — swept.

## 2. Carrier status (deferred, like M12 Phase-B / M11 emission)
`reset_to_state_kraus` is a `forward/` channel (consumed by `forward/ptm.py`, `cptp_guardrail.py`,
`exact/born_local.py`); the Axis-1 MCWF/MPS carrier reset (`_reset_operator` /
`_sample_reset_for_operations_multilevel`) is a **clean projective reset** to `|0>/|+>/|+i>` — it has
**no p-biased reset path**, and `SUPPORTED_AXIS1_PRIMITIVES` has no reset-bias primitive. So M17 is
certified at the **channel level** here; wiring a p-biased reset operator into the carrier reset
substep is a deferred carrier-execution step (gated, like M12 Phase-B).

## 3. Epistemic classes
- **(a) exact:** the reset Kraus `{√(1−p)I, √p|1><0|, √p|1><1|}`; `ΣK†K=I`; the reset-bias closed forms
  (residual P(|1>)=p; |1> preserved).
- **(b) prediction band:** the bias magnitude `p∈[10⁻³,10⁻²]` (McEwen/Reed) — swept.
- **(c) gate/convention:** reset-firing-vs-success convention (`p` = the abrupt re-prep firing prob).

## 4. Closed form (independent GT, hand-derived)
`reset_to_state_kraus(p, target=1)`: `K0=√(1−p)·I`, `K1=√p·|1><0|`, `K2=√p·|1><1|`.
- CPTP: `ΣK†K = (1−p)I + p|0><0| + p|1><1| = (1−p)I + pI = I` (structural, exact).
- `E(|0><0|) = diag(1−p, p)` ⇒ **residual P(|1>) = p** (realized bias == asserted bias).
- `E(|1><1|) = diag(0, 1)` ⇒ `|1>` preserved (reset TOWARD `|1>`; M17 = the reset-to-1 failure mode).
- General reset-to-0 variant at strong `p`: `E(|1><1|)→` mostly `|0>` (a reset that resets).

## 5. Constraint ledger (physical theorem + FALSIFYING test each)
Independent GT = hand-typed reset Kraus (raw `|0>,|1>` outer products) + closed form. Cert imports
ONLY `reset_to_state_kraus` (object under test); MUST NOT import the carrier reset helpers
(`_reset_operator`/`_sample_reset_*` — a CLEAN projective reset, which lacks the bias → a vacuous/
wrong oracle), nor `mechanism_channel` (wraps the same channels.py source-of-truth).

| # | invariant (class) | falsifier (must trip) |
|---|---|---|
| L1 | op identity: carrier `reset_to_state_kraus(p,1)` == hand-typed `{√(1−p)I, √p\|1><0\|, √p\|1><1\|}` (a) | swap a Kraus entry ⇒ caught |
| L2 | CPTP `ΣK†K=I` ≤1e-12 + CP (Choi PSD) (a) | scale K1→1.3K1 ⇒ not TP ⇒ caught |
| L3 | reset-bias self-consistency `E(\|0><0\|)[1,1]==p` (a) | target 1→0 ⇒ `E(\|0><0\|)[1,1]=0≠p` ⇒ caught |
| L4 | `\|1>` preserved `E(\|1><1\|)=diag(0,1)` (reset toward 1) (a) | — structural |
| L5 | reset-to-0 variant actually resets: `E(\|1><1\|)[0,0]=p` at strong p (a) | a no-op (identity) ⇒ no reset ⇒ caught |
| L6 | anti-circular: GT hand-typed; carrier reset helpers / mechanism_channel NOT imported (structural) | GT from carrier projective-reset would lack the bias ⇒ false-fail ⇒ forbidden |

## 6. Bounded simplifications
- **S1 abrupt re-prep (c):** reset modeled as a fast (~100–300 ns) channel; cross-cycle reset history
  is Axis-2. Exact within the reset substep.
- **S2 local (c):** single-qubit reset; inter-qubit reset crosstalk is M11.
- **S3 magnitude swept (b):** `p∈[10⁻³,10⁻²]`.

## 7. Verification plan + status
`outputs/twin_validation/cert_m17_reset_bias.py` (scripted; asserts + printed evidence + flushed +
`__main__`): assert L1–L6 vs hand-typed GT; falsifiers trip; run-log captured.
- [x] Theory-first grounding (≥2 DIRECT-physical, verified DOIs; Reed citation corrected).
- [ ] Cert `cert_m17_reset_bias.py` (channel-level, serialized GPU).
- [ ] Multi-agent review.
- M18: **cut/merged into M6** (documented above + in `axis1_rebuild_plan.md`).
