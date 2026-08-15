# Full-text note (精读) — Hantzko, Binkowski & Gupta, "Fast generation of Pauli transfer matrices utilizing tensor product structure" (arXiv:2411.00526)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF `outputs/papers/2411.00526.pdf` → txt
> `outputs/papers/2411.00526.txt` (PyMuPDF, 13 pp). All §/Eq refs from that text. arXiv:2411.00526v1
> [quant-ph], 1 Nov 2024; Leibniz Universität Hannover. Companion to the authors' Phys. Scr. 99, 085128
> (2024) (their ref [13]). **Loaded specifically to supply the CORRECT, citable definition of the
> Pauli Transfer Matrix (PTM) and the Choi-Jamiołkowski complete-positivity criterion** for the
> re-derivation of the M15 / M19 declared-channel docs, REPLACING the docs' fabricated "Nielsen &
> Chuang Sec. 8.4.2 (PTM)" attribution (N&C §8.4.2 is "Quantum process tomography" — the χ-matrix —
> and the textbook does not use the "Pauli transfer matrix" name; verified against the actual N&C PDF
> bookmark TOC, 710 pp). Sibling PTM/coherent-error notes already in-repo:
> `coherent_robust_pauli_2307.08741` (off-diagonal PTM = first-order coherent error, on hardware),
> `correcting_coherent_errors_surface_1710.02270`, `qec_coherent_errors_dem_2510.23797`.

## Why load-bearing [ours]
The M15 (`hard_non_pauli_kraus_gate_error`) and M19 (`weak_type4_ptm_mixing`) docs both invoke the PTM
formalism — M19's entire framing is "off-diagonal PTM mixing". The original docs cited **"Nielsen &
Chuang, Sec. 8.4.2 (PTM representation)"**, which is **wrong**: N&C §8.4.2 is *Quantum process
tomography* (it builds the χ / process matrix, not the PTM), and N&C nowhere defines a "Pauli transfer
matrix". This note is the **honest primary source** for the PTM definition + the CP criterion, so the
re-derived docs can cite a real, close-read reference. It is a *standard-formalism* paper (algorithms
for converting channel representations → PTM), not a physical-mechanism paper — exactly the right
register for a (c)-class stress surrogate's mathematical grounding.

## The definitions we cite [paper] — verbatim

- **Quantum channel = CPTP superoperator** (§II.A, p.2): "a quantum channel … is a completely positive,
  trace-preserving (CPTP) superoperator `E : L(H_A) → L(H_B)`." Complete positivity: for all `d`,
  `id_{Mat(d)} ⊗ E` maps positive elements to positive elements (p.2 + footnote 2).
- **Pauli basis** (§II.A, Eq.2-3, p.3): `σ_{0,1,2,3} = {I,X,Y,Z}` are hermitian, involutory, unitary; a
  length-`n` Pauli string `σ_t = σ_{t1}⊗···⊗σ_{tn}`; the set `P = {σ_t}` is an **ONB of Mat(2ⁿ)**.
- **PTM definition** (§II.A, Eq. for `PTM(E)_{s,t}`, txt line 225-226): for a channel `E`, the
  **Pauli transfer matrix** holds the entries
  ```
  PTM(E)_{s,t} = ⟨σ_s, E(σ_t)⟩     (lexicographic Pauli order in both indices)
  ```
  a `4ⁿ × 4ⁿ` real matrix. The inner product is the Frobenius/Hilbert-Schmidt product
  `⟨A,B⟩ = Tr(A†B)`. **Normalization caveat (txt line 439-440):** "the canonical and Pauli basis are
  not normalized w.r.t. the same inner product" — i.e. `⟨σ_s,σ_t⟩ = Tr(σ_s†σ_t) = 2ⁿ δ_{st}`. So the
  conventional **unit-normalized PTM** (the one used in randomized benchmarking / Qiskit, with the
  identity channel → identity PTM) is `R_{s,t} = (1/2ⁿ) Tr(σ_s E(σ_t))` (single qubit: `R_{ij} =
  ½ Tr(σ_i E(σ_j))`, `i,j∈{I,X,Y,Z}`). This 1/2ⁿ is the normalization the M19 doc's "oracle" got
  WRONG (it kroned `R_{ij}·(σ_j⊗σ_i*)` and divided the Choi by `d`, building a non-PSD matrix from a
  not-actually-a-valid-PTM `R = I + εΔR`).
- **Choi matrix + CP criterion** (§II.A, Eq.9, p.3, txt line ~246-252): `Choi(E) = Σ_{k,ℓ} E_{k,ℓ} ⊗
  E(E_{k,ℓ})` (a basis-dependent form of the Choi-Jamiołkowski isomorphism, "after Choi [14] and
  Jamiołkowski [15]"), and — the load-bearing statement —
  > "the **complete positivity of `E` is equivalent to `Choi(E)` being a positive matrix**."
  i.e. **`E` is CP ⟺ `Choi(E) ⪰ 0` (all eigenvalues ≥ 0).** This is the exact criterion our
  verification script applies (`choi_min_eig ≥ −1e-12`).
- **Kraus form + trace preservation** (§II.A, Eq.12, p.3, txt line ~305-312): the Choi-Jamiołkowski
  proof entails `E(ρ) = Σ_i K_i ρ K_i†` with at most `4ⁿ` Kraus operators and
  > "`Σ_i K_i† K_i = 1`."
  i.e. **trace preservation ⟺ `Σ_k K_k† K_k = I`** — the exact CPTP residual our script measures
  (`‖Σ K†K − I‖_F ≤ 1e-12`).
- **PTM ⊗ structure** (Eq.8): `PTM(E_1 ⊗ E_2) = PTM(E_1) ⊗ PTM(E_2)` (tensorial ONB).
- **Coherent-vs-stochastic in the PTM** (§I, p.1): PTMs are "the standard tool to analyze the effect of
  **Pauli twirling**" — twirling zeroes the off-diagonal PTM, leaving the diagonal (the Pauli
  probabilities). The off-diagonal PTM is therefore the **coherent / non-Pauli** part (this is stated
  more sharply, and on hardware, in `coherent_robust_pauli_2307.08741` Eq.4: first-order coherent
  angles live in the off-diagonal PTM with no Pauli contribution).

## The canonical CP/Choi lineage [paper refs — for citing the theorem itself]
- **Choi, M.-D., Linear Algebra Appl. 10, 285 (1975)** (ref [14]) — the "completely positive ⟺
  Choi-matrix PSD" theorem. THE primary source for the CP criterion.
- **Jamiołkowski, A., Rep. Math. Phys. 3, 275 (1972)** (ref [15]) — the channel-state duality.
- (For the operator-sum/Kraus theorem itself the canonical primary source is **Kraus, K., "General
  State Changes in Quantum Theory," Ann. Phys. 64, 311–335 (1971)**, DOI 10.1016/0003-4916(71)90108-4
  — verified to exist; the **textbook** statement is **Nielsen & Chuang §8.2.3 "Operator-sum
  representation"** + Theorem 8.1; N&C §8.3.5 is "Amplitude damping", §8.3.6 "Phase damping".)

## Relevance to qec_twin [ours]
- **The CORRECT citation for "PTM" in M15/M19.** Use `PTM(E)_{s,t} = ⟨σ_s,E(σ_t)⟩` / normalized
  `R_{ij} = ½Tr(σ_i E(σ_j))` (this note), NOT "N&C §8.4.2". The "off-diagonal PTM = coherent error"
  claim is cited to `coherent_robust_pauli_2307.08741` (hardware) + §I here.
- **The CORRECT CP test.** `Choi(E) ⪰ 0` (Choi 1975) is the complete-positivity criterion both M15 and
  M19's "oracle" must satisfy; the original M19 oracle *manufactured* a non-CP map (`R = I + εΔR` has
  Choi eigenvalues `[−ε, 0, ε, 2]`) and then silently dropped the negative eigenvalue — exactly the
  anti-pattern this criterion forbids. The honest fix is to define the channel by a **valid Kraus set**
  (which the carrier code already does: `weak_type4_mixing_kraus` = Pauli-mix ∘ unitary, CP by
  construction) and *read off* its PTM, never to perturb a PTM and hope it stays CP.
- **What NOT to claim:** there is **no "Type-1…Type-4" classification** of processes/operators in this
  paper, in N&C, or in the PTM literature generally. M19's "Type-4" is a project-local nickname for
  "off-diagonal PTM mixing between two Pauli axes"; it must be presented as such (a (c)-class stress
  label), not attributed to any source.

## How to use / trust + open questions [ours]
- **Trust:** high for the *definitions* (PTM element, Choi-CP equivalence, Kraus trace-preservation) —
  these are the field-standard objects, transcribed verbatim from the text with the normalization caveat
  carried. The paper's *algorithms* (its actual contribution — fast representation conversions) are not
  load-bearing for us; we use only §II.A preliminaries.
- **Classification: DIRECT (for the PTM/Choi definitions)** — the paper writes the PTM element formula,
  the Choi map, the CP⟺PSD equivalence, and the Kraus completeness relation explicitly. It is the clean
  primary source for the formalism the M15/M19 docs lean on.
- **Open question:** none for the formalism. The remaining honesty work is in the docs themselves
  (declare (c)-class; cite this note for PTM, Choi 1975 for CP, Kraus 1971 / N&C §8.2.3 for the
  operator-sum form; delete the N&C §2.1.3 "Type-4" fabrication).
