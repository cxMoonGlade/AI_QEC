# Preregistration — exact-small CAPEPS Clifford catalogue

Date frozen: 2026-07-27
Claim ID: `capeps_exact_small_postlocal_20_v1`
Closure dependency: `CAPEPS_DISENTANGLER_THEORY_FIRST_CLOSURE_2026-07-27.md`
Status: `DRAFT_FROZEN_DESIGN__PREREGISTRATION_GATE_FAIL`
Preregistration gate: `FAIL`
Review state: `CORRECTED_AFTER_INDEPENDENT_REVIEW__FINAL_REREVIEW_PENDING`
Theory-first decision: `CODE_BLOCKED`
Result-blind statement: no implementation or result from the proposed 20-candidate CAPEPS search has been inspected because that search does not yet exist.

This document freezes an experiment design; it does not currently grant code
permission. The minimal exact-small source set is now admitted and
artifact-verified: GCAMPS for the hybrid split, Chang et al. for the phase-free
20-class construction, Liu–Clark for the exact Rényi-2/purity objective, and
the existing Evenbly/Schuch boundary sources. The pinned FOCUS asset remains an
external differential, not evaluator truth.

One repository prerequisite still fails: \(S_2\), \(J_{\max}\), and
\(J_\Sigma\) are frozen proposed metrics here but are not registered in
`docs/METRICS.md` with a current implementation owner and an independent value
test. Until that metric gate closes and receives a new independent review, every
verdict defined below is prospective. Unadmitted qutrit and scalable-PEPS
boundary sources are outside this exact-small qubit claim and remain open for
their separate lanes.

## 1. Question and bounded claim

Frozen question:

> On named finite all-qubit tracers evaluated by exact contraction, do 20 post-local two-qubit Clifford representatives attain exactly the same frozen proposed entanglement score as all 720 phase-free symplectic Clifford actions, while every selected paired refactor preserves the represented physical ray?

Positive claim allowed after every gate passes:

> For the frozen exact-small qubit fixtures and score, the independently reconstructed 20-representative post-local catalogue was score-complete relative to all 720 phase-free candidates, and its paired frame/residual updates preserved the physical ray within the frozen proposed numerical band.

Forbidden extrapolations: generic PEPS optimality, scalable speedup, approximate CTMRG correctness, global convergence of a sweep, qutrit support, QEC Record faithfulness, logical error rate, threshold, or field-wide novelty.

## 2. Mechanism and invariants

The candidate state is

\[
|\Psi\rangle=C|\phi\rangle_{\rm PEPS}.
\]

A candidate \(Q\) acts only as the paired refactor

\[
(C,|\phi\rangle)\mapsto(CQ^\dagger,Q|\phi\rangle).
\tag{P1}
\]

The physical-state invariant is

\[
(CQ^\dagger)(Q|\phi\rangle)=C|\phi\rangle .
\tag{P2}
\]

Let

\[
G=\operatorname{Sp}(4,\mathbb F_2),\qquad |G|=720,
\]

and let the output-local subgroup be

\[
H=\operatorname{Sp}(2,\mathbb F_2)\times
  \operatorname{Sp}(2,\mathbb F_2),\qquad |H|=36.
\]

The mathematical convention is frozen before defining the key. A Pauli vector is

\[
v=(x_0,z_0,x_1,z_1)^T\in\mathbb F_2^4,
\]

and \(S_Q\) is the column-action symplectic matrix defined by
\(Q P(v)Q^\dagger\sim P(S_Qv)\). Its columns, in order, are the images of
\((X_0,Z_0,X_1,Z_1)\), written in the same interleaved coordinate order. Thus
an output-local operation obeys \(S_{LQ}=S_LS_Q\), and the frozen key is

\[
k(S)=\operatorname{lexmin}_{L\in H}
\operatorname{flatten}_{\rm row-major}(LS\bmod2).
\tag{P3}
\]

The Stim adapter constructs each column from `x_output`/`z_output` and the
interleaved \((x_0,z_0,x_1,z_1)\) coefficients. The pinned FOCUS raw tableau has
rows \((X_0,X_1,Z_0,Z_1)\) and interleaved coefficient columns, so its sole
allowed adapter is

\[
S_{\rm column}=
\left(T_{\rm FOCUS}[[0,2,1,3],:]\right)^T.
\tag{P3a}
\]

Both adapters must round-trip all 16 bits exactly. No later row/column
permutation or multiplication-side choice is permitted under this claim ID.
The semantic implementation name is `PostLocalCosetRepresentative`.

## 3. Frozen proposed score — registration pending

For a normalized state \(|\chi\rangle\) and frozen proposed physical bipartition \(e:A_e|B_e\), define

\[
S_2^{(e)}(\chi)
=-\log\operatorname{Tr}\rho_{A_e}^2,
\qquad
\rho_{A_e}=\operatorname{Tr}_{B_e}|\chi\rangle\langle\chi|.
\tag{P4}
\]

Here and throughout this preregistration, \(\log\) is the natural logarithm.

For candidate \(Q\), the primary score is

\[
J_{\max}(Q)=\max_{e\in\mathcal E}S_2^{(e)}(Q\phi).
\tag{P5}
\]

Tie-breaks, in order, are:

1. smaller
   \[
   J_{\Sigma}(Q)=\sum_{e\in\mathcal E}S_2^{(e)}(Q\phi);
   \tag{P6}
   \]
2. lexicographically smaller post-local key \(k(S_Q)\);
3. lexicographically smaller canonical circuit serialization.

No PEPS tensor norm, virtual-bond singular value, approximate environment value, runtime, or evaluator-only dense target may enter selection.

## 4. Frozen fixtures

All numerical work uses `complex128`. Qubit 0 is the most-significant dense tensor axis, matching the current CAPEPS contract. Every fixture is evaluated in a fresh object without sharing candidate tensors.

Every seeded vector is generated by exactly

```python
rng = np.random.Generator(np.random.PCG64(seed))
v = rng.standard_normal(2**n) + 1j * rng.standard_normal(2**n)
v = np.asarray(v / np.linalg.norm(v), dtype=np.complex128)
payload = np.asarray(v, dtype="<c16").tobytes(order="C")
```

All fixture byte freezes under this claim ID use NumPy 2.4.6. A different
NumPy build is acceptable only if it reproduces the identical payload hash; a
mismatch makes the fixture `UNAVAILABLE` rather than permitting regeneration.

The SHA-256 of `payload` is frozen as follows:

| fixture | seed | canonical byte SHA-256 |
|---|---:|---|
| F1 | 2026072701 | `4e77162da54b87bcf2033f054ee15ac6fb90dbcbd3a86dbbc8c43eef52eb9845` |
| F1 | 2026072702 | `c819540d50c27469b43a5fc35a5ae4e80f0877907e2c3ebb5a1a879038da1ad1` |
| F1 | 2026072703 | `d74064d1ceb57fc2d43d326dfd4fd34bd95d8affce95de0ccfe7ab72569b470a` |
| F1 | 2026072704 | `11efbc932917efc799c51030a590052293663a723dced916f337a154464ece62` |
| F1 | 2026072705 | `390c91d02dc111e91216e53c20e98d244ec695b5037cc9c760c5268cf2259c30` |
| F1 | 2026072706 | `9b4ad9b912ba4b3b528b03ca6e00eeecf65b90345306d89f2aca8b35e09a1d38` |
| F1 | 2026072707 | `ada40ce1202bb6e34980dd61dacc01d760b08f477637634fb7509654f03c0544` |
| F1 | 2026072708 | `57a4d1536b3347aaa34b5d8641811f497777a25dea18106975d7db8dc5348423` |
| F2 | 2026072711 | `2236f77a7cbda563d41a85779c944d085cf0509b1140957dd8361bded96b1f24` |
| F2 | 2026072712 | `0099a3c36008cac967128157edff10b5c73b51b6c22b0d45547c5e55d59f2d7a` |
| F2 | 2026072713 | `c5506ad13834acc89c9265628c0dd0413ec6c99a3e31aad0de53f667322c4a36` |
| F2 | 2026072714 | `beac0e943aa6288e429a7d0e8c9e679367376e450084ee6795484a1fe75d65ae` |
| F3 | 2026072721 | `36aa333d60275266886b5a5eb77c1345c743ada823a236683f2d2a8886b6d98c` |
| F3 | 2026072722 | `16fdab9bc84d8ddd9649d18788a05cf5b261145b558e5f03cdb3bd44ff05c3c3` |

A hash mismatch makes that fixture `UNAVAILABLE`; regeneration with another
RNG, dtype, normalization, byte order, or axis order is forbidden.

### F0 — mandatory analytic disconfirmation fixture

\[
|\phi\rangle=|00\rangle,
\quad Q_0=\operatorname{CNOT},
\quad Q_1=\operatorname{CNOT}(H\otimes I).
\]

Frozen cut: qubit 0 | qubit 1.
Expected scores: \(S_2(Q_0\phi)=0\),
\(S_2(Q_1\phi)=\log2\). This fixture must reject a double-sided quotient.

### F1 — complete two-qubit state battery

Use the following normalized inputs:

- \(|00\rangle\), \(|01\rangle\), \(|10\rangle\), \(|11\rangle\);
- \((|00\rangle+|11\rangle)/\sqrt2\);
- \((|00\rangle+i|01\rangle+2|10\rangle-|11\rangle)/\sqrt7\);
- eight complex Gaussian vectors generated by NumPy `PCG64` seeds
  `2026072701` through `2026072708`, normalized once in `complex128`.

Frozen cut: qubit 0 | qubit 1.

### F2 — genuine-2D four-qubit battery

Geometry: open \(2\times2\) grid with row-major physical order
\((0,1;2,3)\). Candidate edges: \((0,1),(0,2),(1,3),(2,3)\).
Frozen cuts:

- left column \(\{0,2\}\) | right column \(\{1,3\}\);
- top row \(\{0,1\}\) | bottom row \(\{2,3\}\);
- checkerboard \(\{0,3\}\) | \(\{1,2\}\).

For byte-level deterministic construction, items 1–3 use `complex128`, and the
GHZ input is initialized exactly as

```python
v = np.zeros(16, dtype=np.complex128)
v[0] = v[15] = 1 / np.sqrt(np.float64(2))
```

For item 3,
`H = np.asarray([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(np.float64(2))`;
`CX(c,t)` is the 16-by-16 big-endian basis permutation that flips bit `t` iff
bit `c` is one; and the displayed \(R_Y\) entries are evaluated by NumPy
float64 `cos` and `sin`. After each deterministic state is fully constructed,
canonicalize it exactly once before hashing:

```python
v = np.asarray(v / np.linalg.norm(v), dtype=np.complex128)
payload = np.asarray(v, dtype="<c16").tobytes(order="C")
```

This final pass is part of the fixture definition; omitting it gives a different
byte payload despite representing the same mathematical ray.

States:

1. \(|0000\rangle\);
2. the positive-phase 4-qubit GHZ state
   \((|0000\rangle+|1111\rangle)/\sqrt2\), with final canonical byte SHA-256
   `6128661dfc01f177c53c9e8839603db4f2b204d94296109b7696cb3ff2730e44`;
3. the state obtained from \(|0000\rangle\) by the chronological gate list
   `H(0), CX(0,1), CX(0,2), CX(2,3), RY(1,0.13), RY(3,-0.29)`, with final
   canonical byte SHA-256
   `7429ae516dfb1fd5b43742347df1a65de7044fe709cd1f8b462332871140a888`;
4. four complex Gaussian states generated by the frozen recipe and seeds
   `2026072711` through `2026072714`.

Here

\[
R_Y(\theta)=
\begin{bmatrix}
\cos(\theta/2)&-\sin(\theta/2)\\
\sin(\theta/2)& \cos(\theta/2)
\end{bmatrix},
\]

and each listed gate left-multiplies the column state in chronological order.
The circuit state must be constructed independently as a dense matrix product
and through the residual carrier. Random dense states are score fixtures only
and need not be representable at a small PEPS bond dimension.

### F3 — optional six-qubit geometry stress fixture

Geometry: open \(2\times3\) grid with row-major physical order
\((0,1,2;3,4,5)\). Candidate edges are
\((0,1),(1,2),(3,4),(4,5),(0,3),(1,4),(2,5)\). Frozen cuts are

- left column \(\{0,3\}\) | \(\{1,2,4,5\}\);
- first two columns \(\{0,1,3,4\}\) | right column \(\{2,5\}\);
- top row \(\{0,1,2\}\) | bottom row \(\{3,4,5\}\);
- checkerboard \(\{0,2,4\}\) | \(\{1,3,5\}\).

The two states are normalized complex Gaussian vectors generated independently
by NumPy `PCG64` seeds `2026072721` and `2026072722` in `complex128`. F3 runs
in one fresh process with a 900-second wall timeout and an 8-GiB peak host-RSS
cap. Exceeding either cap is reported `UNAVAILABLE`, never silently omitted.
F3 is secondary and cannot rescue a failure on F0–F2.

## 5. Independent ground truth

The candidate implementation may use a project GF(2) group enumerator and canonical key. Acceptance uses three independent references:

1. **Dense physics authority:** hand-written NumPy `complex128` matrices for
   \(H,S=\operatorname{diag}(1,i),X,Z,\operatorname{CX}\), tensor products,
   partial traces, and Eq. (P4). It must not call CAPEPS frame, residual,
   scorer, catalogue, Stim, or FOCUS helpers.
2. **Full-candidate authority:** an isolated breadth-first enumeration generated
   from the ordered gate alphabet
   `H(0), H(1), S(0), S(1), CX(0,1), CX(1,0)`, deduplicated by its independently
   computed mathematical symplectic matrix until all 720 elements are present.
   State evolution multiplies only the hand-written `complex128` matrices from
   item 1. Stim is a secondary tableau/circuit differential and cannot override
   this authority or choose the expected result.
3. **External differential only:** FOCUS file
   `pyfocus/camps/file/clifford_2qubit_big.npz`, pinned to commit
   `05b5b3a37a6dfcdfad1d809155f387565ed17734` and SHA-256
   `466b03f9d2c59dcee5c67c9a97c348e5415b21c34b4a94b04b4fdb8aee996a8e`.
   It may confirm post-local orbit coverage up to convention, but it is not the source of the expected answer and cannot override gates 1 or 2. The similarly named indexed asset `clifford-2bits-unique-entropy-big.npz` is a mandatory non-source: it covers the pre-local direction and must not be imported. The bundled `clifford_ops` matrices are `complex64` and are forbidden from scoring, lifting, or ground truth. Only tableau entries verified to be exact 0/1 values may be read, after which the project independently reconstructs a `complex128` lift.

Any phase-free representative used for exact state evolution must be lifted to an explicit Clifford circuit. Pauli/global-phase freedom is harmless for the score, but the exact lift and its inverse must be retained in the frame accumulator.

## 6. Primary acceptance gates

All gates are conjunctive.

### G1 — group and orbit structure

- exactly 720 distinct elements in \(G\);
- exactly 36 distinct elements in \(H\);
- exactly 20 canonical keys;
- every orbit has exactly 36 elements;
- the 20 orbits are disjoint and cover all 720 elements.

Any count failure is terminal.

### G2 — post-local score invariance

For every frozen state, candidate edge, \(S\in G\), and \(L\in H\),

\[
|J_{\max}(LS)-J_{\max}(S)|\le10^{-12},
\]

and likewise for \(J_\Sigma\). A score that fails this gate is not allowed to use the 20-class quotient.

### G3 — catalogue score completeness

For every frozen state and candidate edge,

\[
\left|
\min_{S\in G}J_{\max}(S)
-
\min_{R\in\mathcal R_{20}}J_{\max}(R)
\right|
\le10^{-12}.
\tag{P7}
\]

After applying the frozen proposed tie-breaks, the selected post-local keys must also agree. Matching only the minimum number while selecting a different frozen key is a failure.

### G4 — paired physical-ray invariant

For every selected representative and frozen CAPEPS-compatible fixture, define

\[
F_{\rm ray}=
\frac{|\langle\Psi_{\rm before}|\Psi_{\rm after}\rangle|^2}
{\langle\Psi_{\rm before}|\Psi_{\rm before}\rangle
 \langle\Psi_{\rm after}|\Psi_{\rm after}\rangle}.
\]

Both norms and \(F_{\rm ray}\) must be finite, both norms must be strictly
positive, and

\[
\left|1-F_{\rm ray}\right|
\le10^{-12}.
\tag{P8}
\]

The implementation may not clamp \(F_{\rm ray}\) into \([0,1]\) before this
check. The test must compare complete dense vectors. Updating only the frame or
only the residual must fail by more than the band on at least one nontrivial
fixture.

### G5 — convention and phase controls

- the exact Stim and FOCUS adapters in Eqs. (P3)–(P3a) round-trip every generator and all 16 tableau bits;
- each selected lift reproduces its symplectic action on all two-qubit Pauli generators;
- adding any two-qubit Pauli on the output side leaves Eqs. (P5)–(P6) invariant;
- the full signed tableau action and inverse accumulator remain exact;
- the pinned FOCUS representatives are covered by the same 20 post-local orbits, up to the documented convention.

## 7. Mandatory negative controls

1. **Double-quotient invariance falsifier:** the deliberately wrong
   double-sided key must place
   \(Q_0=\operatorname{CNOT}\) and
   \(Q_1=\operatorname{CNOT}(H\otimes I)\) in the same class, while the direct
   dense calculation on F0 must satisfy
   \[
   |S_2(Q_1|00\rangle)-S_2(Q_0|00\rangle)|
   \ge \log 2-10^{-12}.
   \]
   This rejects the equivalence relation directly. A four-representative
   catalogue is not required to fail a minimum-score test, because a
   representative such as identity can accidentally retain the same minimum.
2. **Wrong action side:** replacing the post-local quotient by an input-local
   quotient without a separate proof must identify at least one unequal-score
   pair in F0 and therefore fail its claimed within-class invariance.
3. **Half refactor:** frame-only and residual-only mutations must fail Eq. (P8).
4. **Dropped phase:** a noncommuting Clifford sequence with a signed \(Y\) pullback must fail if tableau signs are removed.
5. **Candidate leakage:** altering any candidate tensor while scoring the next candidate must be detected by parent hashes or exact state comparison.
6. **Identity control:** identity must remain selectable when no nontrivial representative improves the frozen proposed score.
7. **Nondegenerate Bell control:** on the Bell input in F1, identity must have score \(\log 2\), while the all-720 and 20-candidate minima must both be zero within \(10^{-12}\). This prevents a constant-score or always-identity implementation from passing.

If a negative control does not fire, the run is invalid even when primary values look favorable.

## 8. Secondary proposed exact finite-network certificate — registration pending

This phase is descriptive and cannot rescue G1–G5. If a finite \(2\times2\) or
\(2\times3\) PEPS compression is added later, every compression event must
exactly contract the complete pre- and post-compression states and report

\[
F_t=
\frac{|\langle\psi_t^-|\psi_t^+\rangle|^2}
{\langle\psi_t^-|\psi_t^-\rangle
 \langle\psi_t^+|\psi_t^+\rangle}.
\]

Before any square root is evaluated, both norms and the overlap must be finite,
both norms must be strictly positive, and the computed fidelity must satisfy
\(0\le F_t\le1\). Any violation returns `UNAVAILABLE`; clipping or clamping is
forbidden. An approximate contraction may substitute only an independently
certified conservative lower bound \(F_{t,\rm lo}\), never a raw environment
estimate.

For deterministic evolution, the frozen proposed bound is

\[
B_T=\min\left(1,\sum_t\sqrt{1-F_t}\right).
\tag{P9}
\]

The independently measured final trace distance and every frozen proposed
measurement TV distance must not exceed \(B_T+10^{-12}\). For a nonzero
observable \(O\), the normalized error
\(|\langle O\rangle-\langle O\rangle_{\rm ref}|/(2\|O\|_\infty)\) must obey the
same gate. A zero operator is checked as an exact structural zero and is never
used as a denominator.

For a complete enumerated classical–quantum frontier, every weight must be
finite and nonnegative, the before/after histories must be identical, the
weights must be unchanged by the truncation transaction, and the complete
weights must sum to one within \(10^{-12}\) without post-hoc renormalization.
The frozen proposed increment and cumulative bound are

\[
\Delta_t=\sum_h w_{t,h}\sqrt{1-F_{t,h}},
\qquad
B_{\rm cq}=\min\left(1,\sum_t\Delta_t\right).
\tag{P10}
\]

Independent complete-law calculations must satisfy

\[
\operatorname{TV}(P_{\rm raw},\widetilde P_{\rm raw})\le B_{\rm cq}+10^{-12},
\qquad
\operatorname{TV}(P_{\rm fold},\widetilde P_{\rm fold})\le B_{\rm cq}+10^{-12}.
\tag{P11}
\]

Equation (P10) does not certify a rare normalized conditional branch; any such
claim requires its own direct state fidelity. Ordinary approximate-environment
values are forbidden from being called certificates.

## 9. Prospective result interpretation — inactive while the gate is `FAIL`

- `PASS`: G1–G5 and all mandatory negative controls pass on F0–F2.
- `PASS_WITH_F3_UNAVAILABLE`: same as `PASS`, with F3 explicitly unavailable under the frozen envelope.
- `FAIL`: any conjunctive gate or negative control fails.
- `UNAVAILABLE`: the independent 720-candidate or dense reference cannot complete; this is not evidence for or against the claim.

No tolerance, fixture, seed, cut family, objective, tie-break, or verdict rule may be changed after the first proposed-optimizer result is inspected. Any change creates a new claim ID and preregistration.

## 10. Epistemic classes and code permission

- Source facts: group counts, paper objectives, the paired GCAMPS refactor direction, and the cited no-go/heuristic limitations.
- Project derivations: Eqs. (P3), (P7), (P9), and (P10) as applied to this project.
- Proposed experiment: F0–F3 and G1–G5.
- Existing observation: the repository already has 18 untruncated mechanics tests, but they do not test this catalogue claim and are not preregistration results.

Independent review corrected the quotient falsifier, convention freeze, fixture
specification, and fidelity guards, but the formal preregistration gate remains
`FAIL`. While source admission or metric registration is open, the only valid
decision is `CODE_BLOCKED`; the prospective result labels in Section 9 are
inactive. A later gate transition requires a new independent review and hash
freeze. Even after such a transition, permission would cover only the
exact-small qubit implementation needed to execute this preregistration, not a
scalable approximate-environment optimizer, qutrit CAPEPS, composite
dimensions, or efficiency claims. Any `src/**` implementation also requires
explicit user confirmation and a reviewed phase diff under repository policy.
