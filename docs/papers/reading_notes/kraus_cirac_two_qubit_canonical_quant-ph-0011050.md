# Full-text review — Kraus & Cirac, "Optimal Creation of Entanglement Using a Two–Qubit Gate" (arXiv:quant-ph/0011050)

> **Provenance (2026-06-29): FULL-TEXT read (精读).** PDF `outputs/papers/quant-ph/0011050.pdf` → txt
> `outputs/papers/quant-ph/0011050.txt` (9 pp, PyMuPDF). All §/Eq/App refs from that text. Read in full
> (Sec. I–VI + Appendices A–D). **Support classification: DIRECT** (states the canonical
> `U_d = exp(-i σ_A^T d σ_B)` = Σ_β α_β σ_β⊗σ_β decomposition, and the explicit pure-XX generator).

## Why load-bearing [ours]
The **original "canonical class vector" (KAK) statement** for two-qubit gates: any two-qubit unitary reduces,
up to local operations, to `U_d = exp(-i(α_x σ_x⊗σ_x + α_y σ_y⊗σ_y + α_z σ_z⊗σ_z))` — i.e. the **interaction
content is carried by the three Pauli⊗Pauli generators XX, YY, ZZ** with three real parameters (α_x,α_y,α_z).
Crucially the paper writes the **pure-XX generator explicitly** (Eq. 24: `U_d = e^{-iα S_x} = cos α·1 − i sin α·
σ_x⊗σ_x`) and names `S_β ≡ σ_β⊗σ_β` (Eq. 26). This is the direct, primary-source grounding that **X⊗X is a
canonical, independent two-body interaction generator** — the [α_x,α_y,α_z] precursor to Zhang's [c1,c2,c3].

## Metadata [paper]
- Authors: B. Kraus, J. I. Cirac (Institute for Theoretical Physics, University of Innsbruck).
- Venue: Phys. Rev. A **63**, 062309 (2001); arXiv:quant-ph/0011050v1, 13 Nov 2000.
- Type: theory.

## Executive summary [paper]
Finds which separable two-qubit input states a given two-qubit gate maps to maximally-entangled output, and
which gates can create a maximally entangled state at all. The enabling structural result (Sec. III + App. A):
**every two-qubit gate decomposes as U_AB = (U_A⊗U_B) U_d (V_A⊗V_B)** with U_d depending on only **3 parameters**
(α_x,α_y,α_z), the rest local — so entanglement questions reduce to U_d. Worked in the magic (Bell) basis.

## Method (deep) [paper]
**Canonical decomposition (Sec. III, Eq. 11–12; App. A, Eq. A1).** For any unitary U_AB on two qubits there
exist local unitaries U_A,U_B,V_A,V_B and a non-local U_d with
> **U_AB = (U_A ⊗ U_B) U_d (V_A ⊗ V_B)**   (Eq. 11 / A1)
> **U_d = e^{-i σ_A^T d σ_B}**,  d = diag(α_x, α_y, α_z)   (Eq. 12 / A1)

Here `σ_A = (σ_x,σ_y,σ_z)` and σ_A^T d σ_B is the bilinear form **σ_A^T d σ_B = α_x σ_x⊗σ_x + α_y σ_y⊗σ_y +
α_z σ_z⊗σ_z** (d diagonal ⇒ only the matched XX/YY/ZZ terms survive). So
> **U_d = exp(-i(α_x σ_x⊗σ_x + α_y σ_y⊗σ_y + α_z σ_z⊗σ_z)).**

Only **3 of the 15** parameters of a general two-qubit gate survive after stripping local unitaries (Sec. III).
U_d is diagonal in the magic basis with phases λ1..λ4 (Eq. 14–15) linear in (α_x,α_y,α_z). A canonical chamber
is fixed by π/4 ≥ α_x ≥ α_y ≥ α_z ≥ 0 (Eq. 13), with π/2-periodicity and π/4-symmetry proved in App. B.

**Constructive proof (App. A).** Diagonalize the symmetric operator UᵀU in the magic basis (eigenvalues e^{2iε_k},
maximally-entangled eigenbasis) → choose local unitaries to map both bases to the magic basis → read off the
λ_k hence (α_x,α_y,α_z). (Lemmas 1–2, steps 1–4.)

## The MECHANISM (for implementation) [paper → ours]
The operator form M22 needs is **Eq. 12 + Eq. 24 + Eq. 26**:
- **Eq. 12:** `U_d = e^{-i σ_A^T d σ_B}` with d diagonal — the canonical interaction generator is
  **Σ_β α_β σ_β⊗σ_β over β ∈ {x,y,z}**, i.e. the XX/YY/ZZ Pauli⊗Pauli basis with independent coefficients.
  This is the algebraic license for treating XX as one of the canonical 2-body axes.
- **Eq. 24 (Example 1) — PURE XX, written out:**
  > **U_d = e^{-iα S_x} = cos(α)·1 − i sin(α)·σ_x ⊗ σ_x**,  with S_x = σ_x⊗σ_x.
  An explicit standalone single-generator gate exp(-iα XX) — exactly our M22 `rxx_unitary` exp(-iθ XX/2)
  (θ = 2α). This is the most direct possible grounding that **pure X⊗X is a legitimate independent generator**.
- **Eq. 26 (Example 2):** defines `S_β ≡ σ_β ⊗ σ_β (β = x,y,z)` and uses `[S_x,S_y]=[S_x,S_z]=[S_y,S_z]=0`
  — naming XX, YY, ZZ as the three **mutually-commuting** canonical generators (the Cartan subalgebra, in
  Zhang's later language). Their commuting-ness is the algebraic fact that lets [α_x,α_y,α_z] be simultaneous
  coordinates.

Repo: `forward/channels.py::rxx_unitary` (M22), `forward/mechanisms_torch.py:319` (exp(-i θ XX/2)),
catalog `M22 = coherent_cxx_parasitic_coupling` (`mechanisms/catalog.py:28`).

## The OBSERVABLE / metric [paper]
**Concurrence** C(|Ψ⟩) = |⟨Ψ|σ_y⊗σ_y|Ψ*⟩| (Eq. 3); in the magic basis C = |Σ_k μ_k²| (Eq. 4). Max attainable
concurrence from a product state under U_d: **C = max_{k,l}|sin(λ_k − λ_l)|** (Eq. 21), and U_d makes a
maximally-entangled state from a product state **iff α_x+α_y ≥ π/4 and α_y+α_z ≤ π/4** (App. C). For small
angle (α_x ≤ π/8), C = sin(α_x+α_y) — the entangling power of the σ_A^T d σ_B Hamiltonian. [Not our primary
metric — we lift the *generator form*, not the entanglement measure — but it ties C directly to the canonical
(α_x,α_y,α_z), so the class coordinates are the physically-measured object.]

## Findings + numbers [paper]
- Any two-qubit gate → 3-parameter canonical core U_d (Eq. 11–12). Max concurrence Eq. 21; maximal-entangler
  condition α_x+α_y ≥ π/4, α_y+α_z ≤ π/4 (App. C).
- Ancilla example (Eq. 26–28): for U_d = e^{-iα(S_x+S_y+S_z)} (isotropic), the best input switches from local
  product to local maximally-entangled at α0 = arccos(1/5)/4 ≈ 0.109π.

## Limitations [paper]
- Closed two-qubit unitaries (+ ancillas) only; no open-system / leakage / dissipation. Goal is entanglement
  creation, not noise modeling — we borrow only the canonical generator algebra (Eq. 12/24/26), which is exact.
- The decomposition labels a *local-equivalence core*; single-qubit dressing is stripped. Same quotient caveat
  as Zhang (see verdict): canonical-generator status is independent of that dressing.

## Relevance to qec_twin [ours]
- **Primary-source DIRECT grounding for the M22 form**, complementary to Zhang (which adds the full su(4)
  Cartan/Weyl machinery): Kraus–Cirac give (i) the σ_A^T d σ_B = Σ_β α_β σ_β⊗σ_β decomposition (Eq. 12) and
  (ii) **the pure-XX generator written out** (Eq. 24). Eq. 24 is the cleanest one-line citation for "exp(-iα
  X⊗X) is a canonical standalone two-qubit gate" — i.e. M22 is well-posed as a single independent 2-body axis.
- Together with Zhang Eq. 7/10/11 this fixes the **8 independent 2-body Pauli generators** (M22=XX, M23=YY,
  M28–M33 cross-terms) as the non-local su(4) basis. ZZ (the M8/M9/M10/M21 phase family) is the third Cartan
  axis.
- No correction to the form. Reinforces that "pure XX" (Eq. 24) and the exchange "XX+YY" combination
  (achievable as the S_x+S_y partial sum) are both legitimate — pure XX = basis element; XX+YY = physical
  swap/exchange. (See verdict.)

## How to use / trust + open questions [ours]
- **Trust: full-text 精读, theorem-grade.** Eq. 11–12 (decomposition) is proved constructively in App. A;
  Eq. 24/26 are explicit identities. Epistemic class (a) exact for the operator form.
- GT-feasibility: exact / no compute (explicit 4×4 generators). This paper sets the *algebra*, NOT the
  device magnitude of J_xx — magnitudes come from device-physics notes (foxen 2001.08343, pettersson
  2408.15402), not here.
- Historical note: this is the paper Zhang et al. cite ([8] in 0209120) as the Cirac-group origin of the
  canonical decomposition; reading both confirms the [α_x,α_y,α_z] (Kraus–Cirac) ≡ [c1,c2,c3] (Zhang)
  identification (up to the ½ and sign conventions).
