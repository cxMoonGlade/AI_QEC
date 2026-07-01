# M21 (leakage-conditional phase) + M34 (leakage seepage/relaxation) — pre-registration

Date: 2026-06-30. Status: **theory-first pre-registration** (Axis-1 rebuild group 7 — the leakage
axis). Both **already run on the Axis-1 MCWF/MPS qutrit carrier** (unlike M12/M17). Governs
`axis1_rebuild_plan.md`. Discipline: `FAITHFULNESS_PROTOCOL.md` + `METRICS.md`. **DOIs verified
against arXiv/journal pages 2026-06-30.**

---

## M21 — leakage-conditional coherent phase (carrier `LEAK_COND_PHASE_LEFT2_RIGHTZ` / `LEFTZ_RIGHT2`)

### 0. What it is + a naming caveat
A two-site **diagonal** Hamiltonian on the qutrit×(qu*) space: when the conditioning site is leaked
to `|2>`, a computational Z-phase is imprinted on the neighbour —
`H[|2,0>]=+ω, H[|2,1>]=−ω` (`_two_site_conditional_phase_hamiltonian`), identity on all blocks where
the conditioner is NOT in `|2>`. `ω_rad_per_ns = φ_rel/(2·dt_gate)`.
**NAMING CAVEAT (flag):** the catalog leaf `M21 = conditional_phase_branch` in
`mechanisms/catalog.py` is a *qubit-level* CPHASE/CZ-angle error `diag(1,1,1,e^{−iθ})` (grouped with
M8 under `RZZ_FAMILY_IDS`) — a DIFFERENT operator. `axis1_mechanism_completeness_prereg.md` maps
catalog-M21 → carrier `LEAK_COND_PHASE`; these are physically distinct. **This prereg grounds the
carrier leakage-conditional-phase form** (the leakage axis), not the qubit-CPHASE leaf.

### 1. Grounding — ≥2 DIRECT-physical (verified DOIs)
- **DIRECT-1 (measured): Miao, McEwen, Atalaya … (Google QAI), "Overcoming leakage in scalable
  quantum error correction," Nat. Phys. 19, 1780–1786 (2023); arXiv:2211.04728; DOI
  10.1038/s41567-023-02226-w.** Fig. 2d–e: interleaved diabatic CZ to a neighbour in `|0>/|1>/|2>`
  measures a **conditional coherent phase ≈ 0.65π when the neighbour is in |2>** (vs 0 for `|0>`,
  π for `|1>`), ECDF over 20 Sycamore qubit pairs. Direct measurement of a leakage-conditioned phase.
- **DIRECT-2 (transmon-Hamiltonian-derived): Varbanov, Battistel … DiCarlo, Terhal, "Leakage
  detection for a transmon-based surface code," npj Quantum Inf. 6, 102 (2020); arXiv:2002.07119;
  DOI 10.1038/s41534-020-00330-w.** §I-A + App. H derive the CZ **conditional leaked phases**
  `φ_L^stat = φ02 − φ12`, `φ_L^flux = φ20 − φ21` from the full multi-level transmon-pair Hamiltonian —
  exactly the carrier operator. (Supporting: McEwen 2102.06131 names the CZ phase residue in the
  leakage-correlation signature.)
- **Bar MET.** Magnitude is **(c) swept/randomized**: Varbanov randomizes φ_L per pair ("not
  characterized in experiment"); Miao's 0.65π is one device realization. Existence/direction is
  device-grounded; magnitude is a swept band, NOT a frozen constant.

### 2. Carrier + cert status
Runs on the carrier (`_TWO_SITE_CONDITIONAL_PHASE_FAMILIES`, summed into the CZ support-group matrix
exp). **Existing cert is GENUINE:** `tests/test_simulator_axis1_schedule.py::
test_axis1_mcwf_mps_conditional_leaked_neighbor_phase_lowers_and_groups` certifies the lowered+grouped
gate against an **independently constructed dense `torch.linalg.matrix_exp`** of the reference 9×9
Hamiltonian (≤5e-12) + a wrong-unit negative control. The diagonal-Hamiltonian channel is closed-form
(`exp(−iωdt·diag)`), so the independent GT (hand-built diagonal H) is non-circular. Independent
*magnitude* GT = Varbanov App. H bare-Hamiltonian rederivation of `φ_L` (channel-independent).
**Epistemic:** (a) operator identity + diagonal-H channel; (c) magnitude swept. **No new cert needed**
(existing one is independent); this prereg adds the literature grounding + the naming caveat.

---

## M34 — leakage relaxation / seepage (carrier `LEAK_SEEP_21`, `LEAK_HEAT_12`, `LEAK_EXCHANGE_12`)

### 0. What it is
The catalog leaf `M34 = leakage_relaxation_surrogate` is a (c)-class computational-subspace surrogate;
the **carrier realizes it with genuine qutrit ladder operators** (stronger):
- `LEAK_SEEP_21`: collapse `√γ↓·|1><2|` — **|2>→|1> seepage** (Wood-Gambetta L2 / McEwen γ↓).
- `LEAK_HEAT_12`: collapse `√γ↑·|2><1|` — **|1>→|2> leakage/heating** (WG L1 incoherent / McEwen γ↑).
- `LEAK_EXCHANGE_12`: 1-site Hamiltonian `coeff·(|1><2|+|2><1|)` — coherent leakage (WG unitary, C_L>0).

### 1. Grounding — ≥2 DIRECT-physical (verified DOIs) — MET decisively
- **DIRECT-1: Wood & Gambetta, "Quantification and Characterization of Leakage Errors," Phys. Rev. A
  97, 032306 (2018); arXiv:1704.03081; DOI 10.1103/PhysRevA.97.032306.** Defines + measures (transmon
  leakage-RB) the **leakage rate L1 and seepage rate L2**; the dissipative model (Eqs. 70–79) is
  `√γ↓|1><2|` (seepage) + `√γ↑|2><1|` (heating) — the carrier operators verbatim.
- **DIRECT-2: McEwen et al., Nat. Commun. 12, 1761 (2021); arXiv:2102.06131; DOI
  10.1038/s41467-021-21982-y.** Table S1: measured per-round **seepage γ↓≈8–9%/round, heating
  γ↑≈0.09–0.11%/round** for `|2>` on Sycamore (rate equation `P|2>(k)`).
- **DIRECT-3 (redundant): Miao et al., Nat. Phys. 19, 1780 (2023); DOI 10.1038/s41567-023-02226-w** —
  injected-`|2>` decay constant ~4.4 cycles; per-cycle leakage ~5×10⁻³.
- Magnitude **(b) swept** (McEwen rates, Sycamore-CZ-specific). (Suchara-Cross-Gambetta 1410.8562 is a
  *model* paper — NOT counted toward the device-direct bar.)

### 2. ANTI-TOY FIX (the load-bearing reason this prereg exists)
The **existing** cert `axis1_qutrit_leakage_oracle_certification_manifest` certifies the carrier
collapse operators against `forward/channels.py::leakage_channel_super` — **the same house
Lindbladian builder (`_lindbladian_super`)**, i.e. a within-engine self-consistency check, NOT
independent ground truth (FAITHFULNESS Rule-I circular-verification). **This prereg replaces it with a
faithful cert** against (i) the Wood-Gambetta **closed-form** L1/L2 and (ii) a **from-scratch** qutrit
Lindbladian (self-tested), importing nothing from `forward/channels.py`/`leakage_channel_super`.

### 3. Closed form (independent GT, hand-derived from Wood-Gambetta)
For jumps `√γ↑|2><1|` (heating, |1>→|2>) + `√γ↓|1><2|` (seepage, |2>→|1>), `|0>` decoupled, `Γ=γ↑+γ↓`:
- **Leakage** `L1 = Tr[|2><2|·E(ρ_X1)]`, `ρ_X1=½(|0><0|+|1><1|)` ⇒ **`L1 = (γ↑/2Γ)(1−e^{−Γt})`**.
- **Seepage** `L2 = Tr[(|0><0|+|1><1|)·E(|2><2|)]` ⇒ **`L2 = (γ↓/Γ)(1−e^{−Γt})`**.
- Seepage-only self-test (γ↑=0): `E(|2><2|)` → `|2>` population `e^{−γ↓t}`, `L2=1−e^{−γ↓t}`, `L1=0`.

### 4. Constraint ledger (faithful, non-circular)
| # | invariant (class) | falsifier |
|---|---|---|
| L1 | op identity `_collapse_operator("LEAK_SEEP_21",√γ↓)==√γ↓\|1><2\|`, `LEAK_HEAT_12==√γ↑\|2><1\|` (a) | wrong matrix element (e.g. [2,1]↔[1,2] swap) ⇒ caught |
| L2 | WG closed form `L1=(γ↑/2Γ)(1−e^{−Γt})`, `L2=(γ↓/Γ)(1−e^{−Γt})` vs from-scratch Lindbladian (a) | swap γ↑↔γ↓ ⇒ L1/L2 swap ⇒ caught |
| L3 | seepage-only self-test `|2> pop = e^{−γ↓t}` (a) | sign error in dissipator ⇒ caught |
| L4 | CPTP (Choi PSD) of the qutrit channel (a) | — structural |
| L5 | anti-circular: GT = WG closed form + from-scratch Lindbladian; `leakage_channel_super`/`_lindbladian_super` NOT imported (structural) | GT = house Lindbladian ⇒ circular ⇒ forbidden |

### 5. Bounded simplifications
- **S1 dissipative-ladder (a-bounded):** seepage/heating as `|1><2|`/`|2><1|` jumps (WG Eqs. 70–79);
  coherent leakage is the separate `LEAK_EXCHANGE_12` arm.
- **S2 magnitudes swept (b):** γ↓∈[~0.05,0.1]/cycle, γ↑∈[~1e-3]/cycle (McEwen) — not frozen.
- **S3 qutrit truncation (c):** `|3>` neglected (ququart available; |2> dominant).

### 6. Verification + status
`outputs/twin_validation/cert_m34_leakage_seepage.py` (the faithful cert; serialized GPU).
- [x] Theory-first grounding (M21: Miao+Varbanov; M34: WG+McEwen+Miao — all DOIs verified).
- [x] M21: existing dense-`matrix_exp` cert is independent/genuine (no new cert); naming caveat flagged.
- [x] M34: faithful cert `outputs/twin_validation/cert_m34_leakage_seepage.py` — serialized GPU, **ALL
  PASS**: op identity exact; from-scratch Lindbladian reproduces WG closed form L1=0.0245 / L2=0.6115
  (independent of `leakage_channel_super` — circular flag FIXED); seepage self-test e^{-γd·t}; CPTP;
  rate-swap + wrong-element falsifiers trip. Run-log captured.
- [ ] Multi-agent review (running).
