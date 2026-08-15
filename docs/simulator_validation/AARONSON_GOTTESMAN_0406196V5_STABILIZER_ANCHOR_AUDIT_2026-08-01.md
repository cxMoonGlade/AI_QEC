# Aaronson–Gottesman quant-ph/0406196v5 — stabilizer-simulation and inner-product source audit

Status: source-only audit for the GCAPEPS finite-memory fixture-v2 delta-closure, 2026-08-01.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| exact classical simulation of Clifford dynamics on stabilizer states | Sec. III, tableau and update rules, PDF pp. 3–4; Theorem 1, PDF p. 3 | A 2n×(2n+1)-bit tableau of destabilizer/stabilizer generators is updated exactly in O(n) per CNOT/Hadamard/phase gate and O(n²) per measurement, with `rowsum` tracking phases mod 4. | It does not define trace distance, any distance between stabilizer states, or a collision model. | closed |
| Gottesman–Knill efficient simulability | Abstract and Sec. I, PDF p. 1; Sec. II Theorem 1, PDF p. 3 | Stabilizer circuits (CNOT, Hadamard, phase, measurement) are efficiently classically simulable; Theorem 1 characterizes stabilizer states four ways. | It does not claim simulability of any non-stabilizer gate except by the exponential-in-d extension of Sec. VII C. | closed |
| exact inner product between stabilizer states | End of Sec. III, PDF p. 5 | The inner product of two stabilizer states is 0 if the stabilizers contain the same Pauli with opposite signs, and otherwise equals `2^(−s/2)` with `s` the minimum number of differing generators over all generating sets; an algorithm via the Theorem 8 canonical form plus Gaussian elimination computes it in O(n³). | The printed passage gives a nonnegative value only; it does not discuss the complex phase of ⟨ψ|φ⟩, and it does not connect the inner product to any distance measure. | closed for the magnitude; phase out of printed scope |
| trace-distance formula for pure states | complete source scope, PDF pp. 1–15 | The source computes inner products, canonical forms, and complexity results. | It nowhere states `D = sqrt(1 − |⟨ψ|φ⟩|²)` or any trace-distance identity. | missing source-locally |

## Notation anomaly (preserved, does not affect assigned rows)

PDF p. 4 (Sec. III) prints the bit encoding as "00 means I, 01 means X, 11 means Y,
and 10 means Z", while PDF p. 8 (Sec. V proof) prints "I = 00, X = 10, Y = 11,
Z = 01". Read literally as ordered pairs (x_ij, z_ij) these two enumerations
contradict each other. The operative semantics is fixed unambiguously by the |00⟩
example tableau on PDF p. 4 (stabilizer rows +ZI, +IZ carry x = 0, z-bits set) and by
the Hadamard rule "swap x_ia with z_ia": the x-bit carries the X component and the
z-bit the Z component. Both assigned-row algorithms are stated in terms of the bits
themselves and are unaffected.

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| tableau rows i = 1..2n, gate CNOT(a→b) | r_i ⊕= x_ia z_ib (x_ib ⊕ z_ia ⊕ 1); x_ib ⊕= x_ia; z_ia ⊕= z_ib | bits as defined on PDF p. 4 | updated tableau | Sec. III, PDF p. 4 | complete |
| tableau, Hadamard(a) | r_i ⊕= x_ia z_ia; swap x_ia ↔ z_ia | same | updated tableau | Sec. III, PDF p. 4 | complete |
| tableau, Phase(a) | r_i ⊕= x_ia z_ia; z_ia ⊕= x_ia | same | updated tableau | Sec. III, PDF p. 4 | complete |
| generators h, i | rowsum(h,i): phase from 2r_h + 2r_i + Σ_j g(x_ij, z_ij, x_hj, z_hj) ≡ 0 or 2 (mod 4); bitwise XOR of rows | g as defined; the printed sum is never ≡ 1, 3 (mod 4) | row h := i + h with correct sign | Sec. III, PDF p. 4 | complete |
| measurement of qubit a | Case I (∃ stabilizer row with x_pa = 1): random outcome, rowsum updates, row replacement; Case II: determinate, scratch-row rowsum over destabilizer x_ia = 1 rows returns r_{2n+1} | Prop. 3 invariants (i)–(iv), PDF p. 5 | outcome bit and post-measurement tableau | Sec. III, PDF pp. 4–5 | complete |
| two full tableaus | canonical-form transform (Thm 8) sending |ψ⟩ to |0…0⟩, then Gaussian elimination of the transformed |φ⟩ tableau to count s | unitary invariance of the inner product and of s | |⟨ψ|φ⟩| = 0 or 2^(−s/2) | end of Sec. III, PDF p. 5; Thm 8, PDF pp. 9–10 | complete |

## Project application

The fixture-v2 θ=0 arm is a pure-state Clifford-only evolution of two computational
basis inputs. The source closes: (a) that this arm is exactly classically computable
(tableau algorithm, Theorem 1), and (b) that the overlap magnitude |⟨ψ1(r)|ψ2(r)⟩|
between the two trajectories is exactly computable (inner-product rule). The
remaining step used by the project — `D(|ψ1⟩,|ψ2⟩) = sqrt(1 − |⟨ψ1|ψ2⟩|²)` for pure
states — is **not in this source**; it is closed by the separate complete project
derivation in the fixture-v2 closure packet, with an untimed complex128 matrix
control. The anchor's claim chain is therefore: tableau exactness [this source] +
inner-product magnitude [this source] + pure-state trace-distance identity [project
derivation, controlled]. Only the magnitude |⟨ψ1|ψ2⟩| enters; the phase scope
limitation of the printed passage is immaterial for this use.

## Competing evidence and kill conditions

- The p. 4 vs p. 8 encoding enumerations disagree as printed; any implementation
  must bind to the update-rule semantics and demonstrate the |00⟩ example tableau.
- The inner-product passage is magnitude-only as printed. Any use requiring the
  complex phase of a stabilizer overlap is outside this closure and needs a
  different source or derivation.
- An implementation claiming this source must reproduce ⟨XX,ZZ⟩ vs ⟨ZI,IZ⟩ = 1/√2
  (the printed example) and fail an intentionally sign-corrupted variant.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- assigned-row status: closed for tableau simulation, Gottesman–Knill, and
  inner-product magnitude; the pure-state trace-distance identity is missing
  source-locally by design and closed elsewhere.
