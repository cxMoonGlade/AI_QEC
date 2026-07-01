# Full-text review — Fux, Kilda, Lovett, Keeling, "Tensor network simulation of chains of non-Markovian open quantum systems" (arXiv:2201.05529)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF (arXiv:2201.05529v3, 10 Jul 2023,
> 1.87 MB, 15 pages) → txt `outputs/papers/2201.05529.txt` (PyMuPDF, 69281 chars). All §/Eq/Fig
> refs from that text. Figures not pixel-extracted — figure facts = captions + numbers stated in text.

## Metadata [paper]
- **Authors / affiliation:** Gerald E. Fux (St Andrews + ICTP Trieste), Dainius Kilda (MPQ Garching),
  Brendon W. Lovett (St Andrews), Jonathan Keeling (St Andrews).
- **Venue / status:** arXiv:2201.05529v3, dated July 11 2023. Published Phys. Rev. Research **5**, 033078.
- **Type:** Numerical method + simulation. Ships as open-source Python package **OQuPy** [ref 47].

## Executive summary [paper]
A general TN method for the **dynamics and multi-time correlations of a 1D CHAIN of open quantum
systems**, where each system may couple STRONGLY to a **structured (non-Markovian) environment**. It
combines the **process-tensor MPO** (PT-MPO — the compressed influence functional of one
system↔environment interaction) with **TEBD** for the 1D chain in Liouville space. The key idea:
compress each site's system↔environment correlations FIRST (into a per-site PT-MPO of bond dim ξ),
THEN fold those into the many-body TEBD problem — "sequentially" rather than "simultaneously"
(§II.B). Cost **O(N K η³ d⁶)** — linear in N sites and K time steps; χ is empirically **independent
of chain length** (App. C). Two demos: (1) FDT-checked thermalization of an N=5/N=9 XYZ chain with
thermal leads; (2) diffusion of an excitation in a **21-site** XY chain with **one bath per site**.

## Method (deep) [paper]

### Total Hamiltonian (Eq. 1 / A1 — THE structural assumption)
```
Ĥ = Σ_{n=1}^{N} ( Ĥ^S_n + Ĥ^E_n )  +  Σ_{n=1}^{N-1} K̂_{n,n+1}                    (Eq. 1)
```
- `Ĥ^S_n ∈ B(H^S_n)` — on-site system Hamiltonian.
- `Ĥ^E_n ∈ B(H^S_n ⊗ H^E_n)` — on-site **system↔environment** interaction (site n's system couples
  to site n's OWN environment `H^E_n`).
- `K̂_{n,n+1} ∈ B(H^S_n ⊗ H^S_{n+1})` — **nearest-neighbour coherent SYSTEM–SYSTEM coupling** along
  the chain.

### The load-bearing decomposition
Total Liouvillian split (Eq. A3): `L = L_chain + Σ_n L^E_n`, with
`L_chain = Σ_n L^S_n + Σ_{n=1}^{N-1} L^K_{n,n+1}` (Eq. A4). L^S_n may additionally carry **local GKSL
dissipation** (Eq. A5), `L^S_n· = -i[Ĥ^S_n,·] + Σ_k (L̂_{n,k}·L̂†_{n,k} - ½{L̂†_{n,k}L̂_{n,k},·})`,
with `L̂_{n,k} ∈ B(H^S_n)` — i.e. any extra dissipation is also STRICTLY on-site.

**Second-order Suzuki-Trotter between chain and environments** (Eqs. A6–A8):
```
e^{Lt} = (e^{Lδt})^M ≃ [ e^{L_chain δt/2} ( Π_{n=1}^{N} e^{L^E_n δt} ) e^{L_chain δt/2} ]^M   (A8)
```
"...the last equality follows from the fact that the L^E_n **act on disjoint spaces**" (line ~1412).
This is the mathematical crux: the environment propagators commute because **no two share a Hilbert
space** → each `e^{L^E_n δt}` (with its env initial state ρ̃^E_n and final trace Tr_{H^E_n}) is EXACTLY
the process tensor of site n, encodable as a **separate per-site PT-MPO** (Fig. 11b, §A.1).

**Chain propagator → TEBD** (§A.1, Eqs. A9–A12): on-site Ĥ^S_n absorbed into neighbour terms
K̂'_{n,n+1} (Eq. A9), then Suzuki-Trotter split odd/even bonds into two-body gates
`G = e^{L^{K'}_{n,n+1} δt/4}` (Eq. A12) → standard TEBD in Liouville space.

**Augmented MPS** (§A.1 end): the chain state is an MPS in Vidal form where **each Γ tensor carries
one EXTRA leg** connecting that site to its own PT-MPO (its environment memory). Uncorrelated
initial state ⇒ dummy legs of dim 1 (grow as memory builds); initially correlated chain↔env ⇒ leg
dim > 1. Contraction (§A.2, Fig. 12c–l) absorbs the network "line by line" (time step by time step):
alternate (i) two-site TEBD gate application with truncated SVDs and (ii) contracting each augmented
Γ_n with one PT-MPO tensor P_n (the PT bond legs become the new augmented legs). **Cap tensors**
C^{(m)}_n (Fig. 12a–b, §A.3) temporarily trace out the environment memory to read the reduced chain
density matrix at any intermediate step (process-tensor "containment property").

### Multi-time correlations (§A.4, Eqs. A13–A15)
`C = ⟨Π_{p=1}^{P} Ĉ_p(m_p δt)⟩` computed by inserting left-acting super-operators `C^L_p := Ĉ_p·`
between propagation segments in the SAME network (Fig. 11d). Out-of-time-order ⇒ right-acting `·Ĉ_p`.
FDT observables (Eq. 4): fluctuation spectrum S_A(ω) = FT of ½⟨{Â(τ),Â(0)}⟩, dissipation χ''_A(ω) =
Im FT of iΘ(τ)⟨[Â(τ),Â(0)]⟩; effective temperature `T(ω) = ω / (2·artanh[χ''(ω)/S(ω)])` (Eq. 5).

## Scaling [paper] (§II.B, App. B/C)
- **Cost: O(N · K · η³ · d⁶)** — N sites, K time steps, d = single-site Hilbert dim, η the SVD
  working bond with `χ ≲ η ≤ χ ξ` (χ = spatial MPS bond, ξ = PT-MPO bond). Worst-case matrices
  (χ ξ d²)×(χ ξ d²) reduced to (η d²)×(η d²) by the App. A contraction/SVD order.
- **Linear in N and in K.** "well suited for parallel computing, since each pair of neighboring sites
  can be evolved separately."
- **χ independent of chain length** (App. C, verbatim): "even for the anisotropic case the bond
  dimension χ is, however, independent of the chain length, which means that the computation scales
  approximately linearly with system size." → the chain-length cost is genuinely O(N), not hidden
  exponential.
- **PT-MPO bond ξ = degree of non-Markovianity** [ref 53]: measured ξ = 26 (α=0.16), 37 (α=0.32) for
  the 21-site demo; 37/44 for T_hot/T_cold leads. Memory ∆K_max = 40 steps at δt = 0.2 (corr. time 8.0).
- **Spatial χ** in the demos: 204 (isotropic η=0) up to 382 (anisotropic η=0.04); grows ~linearly in
  time for anisotropic (excitation number not conserved).
- **1D-ONLY:** yes — the spatial contraction is TEBD (nearest-neighbour two-body gates on a 1D MPS).
  Higher-order Trotter and long-range couplings mentioned as possible extensions [refs 70,72] but the
  demonstrated geometry is a 1D chain. No 2D/PEPS.
- **Bottleneck:** the SVDs compressing the spatial (augmented) MPS after each gate — dominated by the
  η³d⁶ factor; anisotropy (excitation creation) inflates χ over time.
- **Demonstrated max:** **21 sites** (XY chain, one bath each). Largest run 46 h on 32 Xeon cores
  (α=0.32, η=0.04). N=9 leads run: ~8 h to steady state on 4 cores.

## THE LOAD-BEARING SCOPE STATEMENT [paper] — verbatim
From §II.A (lines 218–223), directly under Eq. 1:

> "with N system-environment pairs and nearest neighbor couplings K̂_{n,n+1} among the systems. Note
> that we assume that each environment is coupled only to one system site. **Models in which
> environments simultaneously couple to multiple sites or directly among each other are outside the
> scope of this work.** For each system site, the effects of interactions with its environment can
> thus be encoded in separate PT-MPOs..."

And the mathematical reason it works (§A, line ~1412):

> "...where the last equality follows from the fact that the L^E_n act on disjoint spaces."

**Verdict on the scope:** each environment couples to **EXACTLY ONE** system site. Baths are **NOT
shared** across sites and are **NOT coupled to each other**. Both of those are **explicitly declared
OUT OF SCOPE.** The whole per-site-PT-MPO factorization (Eq. A8) is only valid *because* the L^E_n
act on disjoint Hilbert spaces — a shared/correlated bath would couple them and break the disjoint-
space product that makes the method tractable.

## Coupling it CAN vs CANNOT keep [paper]
- **CAN keep (kept exactly, not factorized):**
  - **Inter-SYSTEM coherent coupling along the chain** — K̂_{n,n+1} nearest-neighbour system–system
    terms (Eq. 1). This is entangling and is carried by the spatial TEBD MPS; NOT factorized.
  - **Strong, structured, non-Markovian system↔OWN-bath coupling** — full memory (∆K_max steps) per
    site, no Born/Markov/weak-coupling approximation, no quantum-regression assumption.
  - On-site local GKSL dissipation (Eq. A5) as an add-on.
- **CANNOT represent (declared out of scope):**
  - **A bath SHARED by ≥2 system sites** (one environment coupling to multiple sites).
  - **Baths COUPLED to each other** (environment–environment coupling).
  - ⇒ Any **environment-mediated / correlated dissipation across sites** — the exact object a shared
    bath produces — is not representable. Correlations between sites are only ever the coherent
    K̂_{n,n+1} channel plus whatever the local baths independently do.

## Findings + numbers [paper]
- **Single-lead N=5 XYZ:** two-time correlations of every spin obey the FDT (Eq. 4) at the bath
  temperature T=1.6 (flat T(ω), Fig. 3d) → full thermalization confirmed at strong coupling α=0.32.
  The competing **2-spin GKSL-driving** protocol [refs 63–65] gives two-time correlations that
  "strongly deviate from the FDT and are thus incorrect" (Fig. 3, §III.A.3) — a headline negative
  control: getting the reduced state right is NOT enough for correct multi-time correlations.
- **Two-lead N=9 (T_hot=1.6, T_cold=0.8):** frequency-dependent effective temperature; inner spins
  share a common mid-frequency T (bulk states), position-dependent high-frequency T (surface states);
  on-site disorder destroys the common mid-frequency plateau (Figs. 4–7).
- **21-site XY, bath per site:** initial mid-chain excitation spreads **diffusively** (MSD ~ linear in
  t at late times, Fig. 10); larger diffusion constant for larger anisotropy η and WEAKER bath
  coupling; anisotropy breaks total-excitation conservation (≈linear growth). ξ=26/37, χ up to 382.
- **Weak-coupling check (Fig. 2):** steady-state ↔ Gibbs trace distance vanishes linearly in α
  (quadratic in bath amplitude) — matches mean-force-Gibbs perturbation theory [ref 59].

## Limitations [paper]
- **1D chain only** (TEBD); nearest-neighbour system coupling in the demos.
- **One bath per site; no shared / mutually-coupled baths** (the scope statement above) — the single
  hardest structural restriction.
- Second-order Suzuki-Trotter error O(δt²) in BOTH the chain–env and inter-site splittings; δt must be
  small enough for both.
- Error control is **convergence-only** (see below) — no a-priori/certified error bound.
- Requires the per-site PT-MPO to be efficiently constructible (bosonic/fermionic/spin baths via
  PT-TEMPO [36,37,39], ACE [40], etc.) AND the spatial state to be a low-χ MPS.
- Cost blows up if either ξ (non-Markovianity) or χ (inter-site entanglement, anisotropy) is large.

## ERROR CONTROL [paper]
**Convergence-only, no certified bound.** Three PT convergence knobs (δt, ∆K_max memory depth,
ϵ_TEMPO SVD threshold) and three TEBD knobs (ϵ_TEBD, t_ss steady-state time, τ_max). The reported
"numerical error" (line-thickness bands in Figs. 4/6/7) is a **finite-difference estimate**: rerun with
tightened parameters (δt 0.2→0.15, ∆K 40→30, ϵ_TEMPO 1e-6→1e-5, ϵ_TEBD 1e-6→1e-5, t_ss 192→160,
τ_max 128→160) and take the spread; dominated by ϵ_TEBD (App. B). No theorem-grade error bar.

## Independent-oracle-ability [ours]
- **Positive:** it IS an independent, from-scratch, published channel-level oracle for a **1D chain of
  transmon-like systems each with its OWN non-Markovian bath + coherent nearest-neighbour coupling**,
  shipped as runnable OQuPy code. For that geometry it certifies against nothing circular — a genuine
  independent GT (rule I) for correlated-error questions that arise from the *coherent* chain coupling
  or from *per-qubit* structured baths (e.g. per-qubit 1/f dephasing, per-qubit TLS with memory).
- **Negative for OUR core question:** the SHARED-bath / correlated-dissipation mechanism we care about
  is precisely what this method **cannot represent**. So it CANNOT serve as the oracle for a shared-bath
  correlated-error teacher — it would silently answer a *different* (factorized-bath) model.

## Relevance to qec_twin [ours]

### Verdict: it FACTORIZES the bath per-site — the WRONG direction for a shared-bath teacher.
This paper is the "does it secretly re-factorize?" case, and the answer is **it factorizes OPENLY, by
explicit assumption** — not secretly. Its entire tractability (Eq. A8, "L^E_n act on disjoint spaces";
per-site PT-MPOs) rests on **one independent bath per site**. Shared baths and bath–bath coupling are
declared **out of scope** (verbatim quote above). For our teacher, whose whole point is a **SHARED
bath → correlated errors across qubits that we must KEEP (not factorize)**, this method's structural
assumption is exactly the thing we are trying to violate. It **cannot be the carrier** for the
shared-bath correlated-error mechanism, and it **cannot be the independent oracle** for it either
(rule I): scoring a shared-bath teacher against this factorized-bath engine is circular in the worst
way — the reference shares the blind spot (no cross-site dissipative correlation) by construction.

### What it CAN do for us (the coherent-coupling arm)
- It **keeps inter-system coherent coupling** K̂_{n,n+1} exactly. That maps onto our
  `CoupledCycleTeacher` **Axis-1 coherent** correlated-error channel (coherent inter-qubit ZZ / spillover
  along a 1D qubit line). PT-MPO+TEBD is a legitimate **independent oracle for the coherent-coupling +
  per-qubit-non-Markovian-bath** slice — i.e. the Axis-1 (joint-Lindbladian, per-site bath) part, NOT
  the Axis-2 shared-latent-source part.
- Cross-check vs prior notes: our shared-bath source line
  (`project-coupling-nonmarkovian-is-the-contribution`, `project-nonmarkovian-wedge-must-be-coherence`)
  says the **contribution** is exactly the shared/correlated bath (TLS/1/f/shared-bath), and the
  removable/owned baseline is coherent-concurrent-Markovian. This paper covers the coherent-coupling
  baseline geometry with structured *per-site* baths, and by its scope statement **excludes** the
  shared-bath contribution — so it corroborates the framing: the shared-bath axis is genuinely NOT
  handled by this class of factorized-bath TN method, reinforcing that it is the unowned wedge.

### The CORRECTION it forces
If we ever reach for "PT-MPO / OQuPy as our correlated-error carrier or oracle," this note is the STOP:
it factorizes the dissipation per site. To keep a **shared** bath we would need either (a) an
influence-functional / process-tensor that couples multiple system legs to ONE bath (out of scope
here — a genuinely different construction), or (b) an explicit chain-mapping of the shared bath into
auxiliary modes carried inside the spatial MPS (TEDOPA-style, ref 21/22) so the "environment" becomes
part of the *system* chain — at which point it is no longer a per-site PT-MPO. Do NOT approximate a
shared bath by N independent per-site PT-MPOs; that is the factorization we are trying to avoid.

## How to use / trust + open questions [ours]
- **Trust:** FULL-TEXT read incl. all appendices (method Eqs. A1–A15, scope statement, scaling). Figure
  numbers taken from captions/text (not pixel-extracted) — no load-bearing claim rests on pixels.
- **Relevance verdict:** **oracle for the COHERENT-coupling + per-site-bath arm only; N/A (in fact a
  cautionary counter-model) for the SHARED-bath correlated-error arm.** Not a carrier for our target.
- **Trade-off if used as coherent-arm oracle:** get exact non-Markovian per-site memory + exact
  coherent K̂_{n,n+1}, but 1D-only, convergence-only error control, and CPU-scale demos (21 sites, tens
  of hours) — feasibility check needed for our d=3/d=5 qubit-line window sizes and our d (transmon
  d=2 or qutrit d=3 ⇒ d⁶ = 64 or 729 per SVD block).
- **Open questions:** (1) Can the shared-bath teacher's cross-qubit correlation be *bounded* by
  bracketing between (i) N independent per-site PT-MPOs [this method, no correlation] and (ii) a
  chain-mapped shared bath — using the gap as a sensitivity band? (2) Is OQuPy's PT-TEMPO usable at our
  qutrit d=3 with realistic transmon 1/f spectral densities to serve as the coherent-arm independent
  oracle? Both require a separate feasibility pass; neither is settled by this paper.
