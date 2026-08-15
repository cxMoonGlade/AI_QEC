# Full-text review — Schumacher (PRA 54, 2614, 1996) + Nielsen, "A simple formula for the average gate fidelity of a quantum dynamical operation" (arXiv:quant-ph/0205035)

> **Provenance (2026-06-29): FULL-TEXT read (精读) of Nielsen 2002.** PDF
> `outputs/papers/quant-ph/0205035.pdf` → txt `outputs/papers/quant-ph/0205035.txt`
> (PyMuPDF, 3 pages). All §/Eq refs from that text. Schumacher 1996 (PRA 54, 2614) is
> the pre-arXiv origin of the entanglement-fidelity DEFINITION; it is cited as Nielsen
> ref [2] (the `F_e ≡ ⟨φ|(I⊗E)(φ)|φ⟩` definition, Nielsen line 75) and its Kraus form is
> the field-standard `F_e = Σ_k |Tr(ρ E_k)|²` carried in `docs/METRICS.md`. This note is
> the observable grounding for the Axis-1 mechanism-completeness `1−F_e` cert (M6 and the
> other same-substep generator mechanisms).

## Metadata [paper]
- **Authors / affiliation.** Michael A. Nielsen (Centre for Quantum Computer Technology & Dept. of Physics, University of Queensland). Origin of the definition: Benjamin Schumacher (Phys. Rev. A 54, 2614, 1996). Horodecki relation: M., P. & R. Horodecki (Phys. Rev. A 60, 1888, 1999).
- **Venue / status.** Nielsen: arXiv:quant-ph/0205035 v2 (12 May 2002); published Phys. Lett. A 303, 249 (2002). Schumacher: Phys. Rev. A 54, 2614 (1996).
- **Type.** Theory (closed-form identities for channel/gate fidelity).

## Executive summary [paper]
Defines and connects the two field-standard scalar quality measures of a CPTP map `E` on a `d`-dim qudit: the **entanglement (process) fidelity** `F_e(E)` and the **average gate fidelity** `F(E)`. `F_e(E) ≡ ⟨φ|(I⊗E)(φ)|φ⟩` is the overlap of a maximally entangled state `φ` of `RQ` before/after `E` acts on `Q` (Nielsen line 75; Schumacher 1996) — independent of which maximally entangled `φ` is chosen. The note gives a simplified proof of the **Horodecki relation** `F(E) = (d·F_e(E) + 1)/(d+1)` (Eq. 3) by twirling `E` to a depolarizing channel, and an explicit operator-basis formula `F_e(E) = Σ_j Tr(U_j† E(U_j))/d³` (Eq. 16). For a gate target `U`, `F(E,U) = F(U†∘E)` (Eq. 2).

## Method (deep) [paper]
- **Average gate fidelity** (Eq. 1–2): `F(E) ≡ ∫dψ ⟨ψ|E(ψ)|ψ⟩`; vs a target gate, `F(E,U) ≡ ∫dψ ⟨ψ|U†E(ψ)U|ψ⟩ = F(U†∘E)`, Haar-averaged over pure input states.
- **Entanglement fidelity** (line 69–83): `φ = Σ_j |j⟩|j⟩/√d` maximally entangled on `RQ`; `F_e(E) ≡ ⟨φ|(I⊗E)(φ)|φ⟩`. Value is `φ`-independent (any two maximally entangled states differ by a unitary on `R` alone).
- **Horodecki relation** (Eq. 3): `F(E) = (d·F_e(E) + 1)/(d+1)`. Proof (Nielsen, simplified): twirl `E_T(ρ) ≡ ∫dU U†E(UρU†)U`; twirling preserves both `F` and `F_e` (Eq. 4–8); `E_T` is depolarizing `E_T(ρ)=pI/d+(1−p)ρ` (Eq. 9–10 covariance argument); Eq. 3 holds by direct check for depolarizing channels, hence for all `E`.
- **Operator-basis formula** (Eq. 11–16): with `{U_j}` an orthogonal unitary basis (`Tr(U_j†U_k)=δ_{jk}d`, e.g. `X^k Z^l`), `F_e(E) = Σ_j Tr(U_j† E(U_j))/d³` (Eq. 16). Gate form: `F(E,U) = [Σ_j Tr(U U_j† U† E(U_j)) + d²] / [d²(d+1)]` (Eq. 17). For `d=2` with `{I,X,Y,Z}`: `F(E,U) = 1/2 + (1/12)Σ_{j=1,2,3} Tr(Uσ_j U† E(σ_j))` (Eq. 18).

## The MECHANISM (for implementation) — N/A
This is an OBSERVABLE/metric paper, not a noise mechanism. (The mechanism, M6 RX over-rotation, is grounded in `docs/error_mechanisms.md` and the Axis-1 carrier `_hamiltonian_matrix_for_term`.)

## The OBSERVABLE / metric [paper → ours]
**`F_e` (entanglement/process fidelity), reported as `1 − F_e` (process infidelity).** Three equivalent forms used in the project:

1. **Definition (Schumacher / Nielsen line 75):** `F_e(E) = ⟨φ|(I⊗E)(φ)|φ⟩`, `φ` maximally entangled. Equivalently `F_e(E_1, E_2) = F_Uhlmann(J_1/d, J_2/d)` is the Uhlmann state fidelity of the trace-normalised **Choi states** — the convention the repo computes via `forward/joint_lindbladian._choi_state_from_kraus` + `_state_fidelity` (used inside `composed_vs_joint_infidelity`). [ours: the comparison form `F_e(E_1,E_2)` between two channels is the natural generalisation; for `E_2 = I` it reduces to Schumacher's single-channel `F_e(E_1)`.]

2. **Kraus form (Schumacher 1996; standard):** `F_e(ρ, E) = Σ_k |Tr(ρ E_k)|²` for the reference input `ρ = I/d`. For a **unitary error** channel `E(·)=V·V†` vs identity, the single Kraus operator gives **`F_e(V, I) = |Tr(V)/d|²`** — the closed form the M6 reference uses.

3. **Avg-gate-fidelity link (Horodecki/Nielsen Eq. 3):** `F_avg = (d·F_e + 1)/(d+1)`, i.e. `1 − F_avg = d/(d+1)·(1 − F_e)`. So the RB-standard average-gate infidelity and the process infidelity differ only by the constant `d/(d+1)`.

**Leading-order coherent closed form [ours, from METRICS.md ledger]:** for a coherent error `V = exp(−iG)`, `G` Hermitian traceless, `1 − F_e ≈ Tr(G²)/d = ‖G‖²_F / d` (the **/d, NOT /d²** — a v1 doc error was caught + corrected; METRICS.md "Composed-vs-joint channel infidelity" row). Then `1 − F_avg ≈ ‖G‖²_F/(d+1)`.

## Findings + numbers [paper]
- `F(E) = (d·F_e(E)+1)/(d+1)` (Eq. 3) — exact, all `d`, all CPTP `E`.
- `F_e(E) = Σ_j Tr(U_j† E(U_j))/d³` (Eq. 16) — exact operator-basis formula.
- No experimental numbers (a theory note); the formulas are exact identities.

## Limitations [paper]
- `F` and `F_e` are **average / state-averaged** measures, NOT worst-case. The worst-case (fault-tolerance-relevant) quantity is the **diamond norm** (Kitaev) — distinct, reported only when FT distinguishability is the question. [ours: M6 is a gate-locality faithfulness cert, so process infidelity is the right field-standard scalar; diamond norm is not required here.]
- `F_e` is `φ`-independent only for **maximally** entangled `φ` (Schumacher's general definition allows non-maximal `φ`; Nielsen uses maximal).
- These are scalar summaries: two channels can share `F_e` yet differ (e.g. coherent vs stochastic of equal infidelity). The cert therefore ALSO compares the operator/generator directly (a stronger, structural witness), not `1−F_e` alone.

## Relevance to qec_twin [ours]
1. **The Axis-1 mechanism-completeness cert observable.** `docs/twin_validation/axis1_mechanism_completeness_prereg.md` line 98 specifies every admitted Axis-1 mechanism is "certified one-/two-site vs the independent oracle `assemble_substep_channel` (process infidelity `1−F_e` / Choi trace distance)". THIS paper is the definition of that `1−F_e`. M6 is the first of the four 1q over-rotation knobs (M6/M7/M20/M27).
2. **REUSE the existing Choi machinery.** `forward/joint_lindbladian._choi_state_from_kraus` + `_state_fidelity` already implement `F_e` in exactly the Schumacher/Nielsen Choi-state convention (cross-checked against the `qutip_*_channels` gtchecks). The M6 cert reuses these — it does NOT reinvent a fidelity.
3. **The closed-form reference for M6.** For the RX over-rotation error `V = RX(ε) = exp(−i(ε/2)X)`, this paper's Kraus form gives the EXACT reference `1−F_e(RX(ε), I) = 1 − |Tr(RX(ε))/2|² = 1 − cos²(ε/2) = sin²(ε/2)`, and METRICS.md's leading-order ledger gives `1−F_e ≈ ‖(ε/2)X‖²_F/2 = ε²/4`. Both are independent of any carrier symbol (the cert's anti-circularity requirement).
4. **Correction this enforces.** The `/d` (not `/d²`) factor for the leading-order process infidelity — a prior `/d²` doc slip — and the `d/(d+1)` `F_avg`↔`F_e` constant (so an RB-style average-gate-infidelity number is NOT the same as `1−F_e`; carry the convention with the number, per the metric-discipline rule).

## How to use / trust + open questions [ours]
- **Trust:** very high. Nielsen 2002 full-text read; the identities (Eq. 3, 16, 18) are exact and are the field standard; Schumacher 1996 is THE definitional origin (cited as Nielsen ref [2]) and its Kraus form is standard textbook (Nielsen & Chuang §). Figures: none (theory note) — nothing pixel-extracted needed.
- **Open questions:** none for M6. The only convention choices to carry: (i) report `1−F_e` (process infidelity) as the headline, NOT `1−F_avg`, and state which; (ii) `d` is the window Hilbert dim (`d=2` for a 1q M6 cert on the computational subspace; if embedded in a qutrit `d=3` carrier the cert computes `1−F_e` on the operative support with the actual local dim — but the M6 reference operator is the 2-level RX block, with identity on any leaked level).
- **GT-feasibility:** the closed-form `sin²(ε/2)` reference is exact and trivially computable; the carrier-side `1−F_e` via the Choi machinery agrees to ~2e-8 (the Uhlmann sqrt/eigh estimator floor), so the cert gates the exact-operator identities at ~1e-12 and reports `1−F_e` as the standard-metric companion.
