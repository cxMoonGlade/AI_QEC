# Axis-1 inter-error coupling (联动) — status

Date: 2026-06-30. Answers "how strong / how correct is the coupling between the rebuilt error
mechanisms?" Two levels: **(A) within-substep (Markovian joint Lindbladian)** — now comprehensively
certified; **(B) cross-mechanism correlated / non-Markovian** — partially built (Axis-2), the open
contribution.

## A. Within-substep coupling — CERTIFIED (exact + quantified)
The engine: `liouvillian_superop` sums ALL `H_i` into one `H` *before* the commutator (cross-terms
`[H_i,H_j]` retained) + all `D[c_k]` → one generator → one `expm` (`assemble_substep_channel`). The
connected-cluster join extends this to overlapping supports.

**Cert `outputs/twin_validation/cert_axis1_full_coupling.py` — ALL PASS** (serialized GPU). Six
heterogeneous rebuilt mechanisms coupled in one 2q substep: drive `H_DR=(Ω/2)X₀`, cross-Kerr
`H_ZZ=ζ|11⟩⟨11|`, parasitic `H_XX=(c/4)X⊗X`, `T1 √γ₁σ⁻₀`, `T2 √(2γφ)n₁`, collective
`M12 √γ_c(σ⁻⊗I+I⊗σ⁻)`.
- **L1 (exactness):** the carrier joint channel == a **from-scratch independent scipy Liouvillian**
  (sum-H, all `D[c]`) to **2.42e-15** — the coupling is assembled exactly, anti-circular GT.
- **L2 (coupling is real):** `1−F_e(joint, composed) = 0.0256` for the full set (≫1e-4): the
  within-substep cross-terms genuinely matter (joint ≠ independent-composition).
- **L3/L5 (controls):** disjoint `T1(q0)+T2(q1)` → `−1.8e-8`; single mechanism → `−5.9e-8` (no
  coupling, as required).
- **L4:** joint channel CPTP.

**Pairwise coupling effect-size `1−F_e(joint, composed)` — physically correct commutation structure:**

| pair | effect | pair | effect | pair | effect |
|---|---|---|---|---|---|
| DR×ZZ | 2.8e-3 ✦ | ZZ×XX | 3.1e-4 ✦ | XX×CORR | 3.0e-3 ✦ |
| DR×XX | ~0 (commute) | ZZ×T1 | 6.6e-5 ✦ | T1×T2 | ~0 (disjoint) |
| DR×T1 | 6.8e-3 ✦ | ZZ×T2 | ~0 (diag) | T1×CORR | 1.3e-5 ✦ |
| DR×T2 | ~0 (disjoint) | ZZ×CORR | 2.1e-4 ✦ | T2×CORR | 7.9e-4 ✦ |
| DR×CORR | 1.4e-2 ✦ | XX×T1 | 8.1e-4 ✦ | XX×T2 | 2.4e-3 ✦ |

✦ = genuine coupling. Zeros are exactly where physics requires: disjoint-qubit pairs (DR/T2, T1/T2)
and both-diagonal pairs (ZZ/T2) commute → no coupling; DR×XX commute (`[X₀,X⊗X]=0`). Largest coupling
DR×CORR (drive on q0 ⊗ collective relaxation involving q0) is physically sensible.

**Verdict (A):** the within-substep 联动 is **well-engineered, exact, and quantified** — the rebuilt
mechanisms couple correctly through the joint Lindbladian, certified against an independent GT, with
the coupling effect-size measured per pair and the commutation structure physically correct.

## B. Cross-mechanism correlated / non-Markovian coupling — the open contribution
- **Correlated COHERENT** (shared latent source → correlated detuning/drive/ZZ): runs today via the
  cluster-join + `mechanisms/source_coupling.py` (`cross_mechanism_correlation > 0.95` shared vs
  `< 0.15` independent, marginals preserved). Axis-2.
- **Correlated DISSIPATIVE** (shared bath → collective/correlated relaxation): the **operator** is
  M12 (Dicke), now executable on the scalable carrier via **Phase-B** (the 2-site joint-collapse
  trajectory seam). Multi-qubit correlated collapse is unblocked.
- **Non-Markovian** (shared bath / TLS / 1/f → CP-divisibility-breaking, echo-irremovable): the
  unforgeable signature (per the project plan, the actual contribution) — **NOT built**. Needs an
  explicit source/bath-memory carrier (Axis-2/Axis-3).

**Next (#3):** theory-first scope the correlated-coupling teacher (shared source fanning into both
coherent params AND the M12-type collective collapse) and the non-Markovian wedge, on top of
`source_coupling` + the Phase-B seam.

## Status
- [x] A — within-substep coupling cert (exact + effect-size table + controls). ALL PASS.
- [x] M12 Phase-B (multi-site joint-collapse seam — the dissipative-coupling foundation).
- [ ] B — correlated/non-Markovian coupling (the contribution): scope + build (#3).
