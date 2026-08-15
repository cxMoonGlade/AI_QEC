# Full-text review — Papaefstathiou, Malz, Cirac, Bañuls, "Efficient tensor network simulation of multi-emitter non-Markovian systems" (arXiv:2407.10140)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF `outputs/papers/2407.10140.pdf` → txt
> `outputs/papers/2407.10140.txt` (PyMuPDF, 14 pages, 67072 chars, HEAD+TAIL confirmed). All §/Eq/Fig refs
> from that text. Figures not pixel-extracted — figure facts = captions + numbers stated in text.

## Metadata [paper]
- Authors: Irene Papaefstathiou (MPQ Garching + MCQST), Daniel Malz (Univ. Copenhagen, Math), J. Ignacio
  Cirac (MPQ + MCQST), Mari Carmen Bañuls (MPQ + MCQST).
- Venue/status: arXiv:2407.10140v2 [quant-ph], dated 8 Jul 2025 (v2). Published PRA 112, 013721 (per prompt).
- Type: numerical method + simulation (tensor-network / MPS real-time evolution).

## Executive summary [paper]
Core question: how to simulate — quasi-exactly, in ANY coupling regime (weak↔strong, Markovian↔strongly
non-Markovian) — the real-time dynamics of MULTIPLE quantum emitters coupled to ONE SHARED non-interacting
bosonic bath, keeping the full bath-mediated inter-emitter correlations. Method: a **Block Lanczos (BL)**
basis transformation of the (non-interacting) bath, seeded by the modes the emitters actually couple to,
which maps the whole system-plus-bath onto a **quasi-1D ladder (strip)** whose WIDTH = number of
system–bath coupling operators N_O (≈ #emitters), then evolved with t-MPS. Two efficiency levers:
(i) exploit the bath's spatial point-group symmetry (D4) to cut the strip width by a constant factor;
(ii) truncate the bath in ENERGY space to a window [ω0−Δ, ω0+Δ] around the emitter transition so the chain
hoppings are bounded by Δ (longer Trotter steps, shorter chains). Demonstrated up to **6 emitters with up to
6 excitations** on a 2D square-lattice boson bath (up to 701×701 sites), studying non-Markovian suppression
of collective (super)radiance and dynamical bound-state formation. Benchmarked exactly in the
single/two-excitation subspaces.

## Method (deep) [paper]

**Setting (Eq. 1–2).** `H = H_S + H_B + H_int`. The bath is NON-INTERACTING (quadratic):
`H_B = Σ_{m,n} a†_n [H_B]_{nm} a_m = Σ_q ε_q ã†_q ã_q`. The interaction is LINEAR in bath modes:
`H_int = Σ_{i=1}^{N_O} Σ_n ( g^(i)_n O^(i) a†_n + h.c. )`, with `O^(i)` arbitrary operators on the system.
`L_B` = #bath modes, `N_O` = #system coupling operators. **No assumption on the form of `O^(i)`** and no
restriction on bath geometry/dimension (the only structural requirements: bath quadratic/non-interacting,
coupling linear).

**Block Lanczos (§II B, Eq. 3–9).** Standard Lanczos tridiagonalizes `H_B` from one seed vector; BL
generalizes to a BLOCK of `N_O` seeds `{q^(i)}`, chosen as the (orthonormalized) coupling vectors
`q^(i)_n ∝ g^(i)_n` — i.e. the bath modes the emitters directly couple to. Collect them into
`Q_1 = [q^(1),…,q^(N_O)]` (an `L_B × N_O` matrix). Recursion (Eq. 3):
`R_i = H_B Q_i − Q_i E_i − Q_{i−1} T_{i−1}`, with `E_i = Q_i† H_B Q_i`, `Q_0=T_0=0`; next block from the
QR factorization `R_i = Q_{i+1} T_i†` (so `T_i ∈ C^{N_O×N_O}` are lower-triangular). After L iterations
`Q = [Q_1,…,Q_L]` with `Q†Q = I`; if `L = L_B/N_O` then `Q` is unitary (BL is then EXACT). In this basis
the bath becomes **block-tridiagonal** (Eq. 6):
```
H_B^BL = Q† H_B Q =  [ E_1  T_1   0   …
                       T_1† E_2  T_2  …
                        0   T_2† E_3  … ]
```
Because `T_i` are triangular, Hamiltonian terms connect only modes in the SAME rung or a NEIGHBOURING rung.
Transformed operators: `b_n = Σ_m Q†_{nm} a_m` (Eq. 7); `H_B = Σ b†_m [H_B^BL]_{mn} b_n` (Eq. 8);
`H_int = Σ_i Σ_{n,m} ( g^(i)_n O^(i) [Q*]_{nm} b†_m + h.c. )` (Eq. 9).

**Geometry.** Result is a **ladder/strip of WIDTH = N_O (#coupling operators ≈ #emitters), LENGTH = L
(#BL iterations)**; the emitter sites sit on the edge/first block (Fig. 1). The bath's structure/dimension
is completely erased by the mapping — *"the structure of the resulting system only depends on the number of
system operators and does NOT depend on the structure or dimensions of the bath"* (Fig. 1 caption).

**Mapping to 1D + long-range terms (Fig. 2, §II E).** To use a 1D MPS the ladder is snaked into a chain;
this converts the width-N_O ladder into a 1D chain with **long-range interactions of maximum range = N_O**
(the ladder width), for a chosen site ordering. So: **more emitters ⇒ wider ladder ⇒ longer-range 1D terms
⇒ more expensive.** This is the dominant width/cost coupling.

**Length truncation via light cone (§II B).** Exact needs `L = L_B/N_O`, but along-chain coupling is
nearest-neighbour, so transport has a finite propagation speed (Lieb-Robinson; the paper notes bounds
hold via bounded total particle number [69] or bounded-energy-density hopping [70]). For a target time
`t_trunc` one stops at `L_trunc < L_B/N_O` once the light cone is covered; `H_B^BL` is truncated to
`(N_O L_trunc) × (N_O L_trunc)`. **This is the key that makes "effectively infinite bath" tractable.**

**Symmetry enhancement (§II C).** For a discrete bath symmetry `U_α` with `[H_B, U_α]=0`, `H_B` is
block-diagonal over symmetry sectors and BL runs independently per sector — giving several ladders coupled
only THROUGH the emitters, in a star geometry. Concretely for a 2D square lattice (odd `L`, PBC, center at
origin) the symmetry group is dihedral D4 (5 irreps). They use two orthogonal reflection axes D1,D2 →
4 sectors labeled `(s1,s2)`, `s=±`. A generic point `(x,y)` has an orbit of 4 modes `a_{±x,±y}`; symmetric
combinations give modes of definite `(s1,s2)`. Each definite-symmetry bath mode couples only to a linear
combination of the emitters in the same orbit — group those emitters into an **effective (larger-local-dim)
system**, seed BL per sector. Net effect: **ladder width reduced from N_O to #multiplets** (roughly a
constant factor, e.g. ×2 or ×4), at the price of larger local dimension — a favorable trade because MPS
handles large local dim well. *"the reduction in the width by a constant factor allows us to multiply the
number of emitters that we can treat by the same number."*

**Energy-window truncation (§II D, Eq. 10).** If `H_S` has transitions near `ω0` and the bath spectral
range `‖H_B‖_2` ≫ coupling, the chain hoppings are large ⇒ tiny Trotter steps ⇒ inefficient. Split
`H_B = H_B^keep ⊕ H_B^discard`, keeping only modes in `[ω0−Δ, ω0+Δ]` so `‖H_B^keep − ω0 1‖_2 ≤ Δ` ⇒ BL of
the truncated bath has hoppings bounded by Δ ⇒ shorter chains, larger Trotter steps. If `Δ ≫ |g_{αn}|` the
discarded modes contribute only a Lamb shift `δω_α = Σ_{ε_n∉window} |g_{n,α}|²/(ω0−ε_n)` (Eq. 10), with
`δω_α < g0/Δ`. Best Δ found NUMERICALLY: solve the single-particle problem exactly for increasing Δ until
convergence (in practice they parametrize the window as `[Ω−αg, Ω+αg]` and converge in α; α=4 typical).

**t-MPS evolution (§II E).** MPS ansatz on the snaked chain; real-time via t-MPS (Trotter,
`e^{−iHt} ≈ (Π_p e^{−iH_p δ})^{t/δ}`), each `e^{−iH_p δ}` an MPO applied variationally. Because terms are
long-range (range up to ladder width `Ñ`), the Trotter grouping matters: they split into two-body terms
(bath-bath or system-bath), group NON-CROSSING sets into a single MPO, giving `O(Ñ²)` MPOs per time step
(instead of `O(ÑL)` gates one-by-one). **Bosonic truncation is exact-ish:** total excitation number is
CONSERVED and bounded by #emitters (bath starts in vacuum), so each bosonic mode occupation can be capped at
`n_max` = #excitations with NO error; in practice a smaller `n_max` (checked by convergence) suffices.
Entanglement stays bounded because the excitation count is low ⇒ long-time evolution with moderate bond
dimension D (demonstrated D = 10–20).

**Model studied (§III A, Eq. 11–12).** `N_e` two-level emitters on a 2D square boson lattice `L_B = N×N`:
`H = −J Σ_{⟨n,m⟩}(a†_n a_m + h.c.) + Ω Σ_i σ+_i σ−_i + g Σ_i (a_{n_i} σ+_i + h.c.)`. Each emitter couples to a
SINGLE spatial bath site `n_i` (but arbitrary disorder allowed). RWA (no counter-rotating terms) — justified
for the nanophotonic optical regime, but the method itself allows counter-rotating terms. Dispersion
`ω_k = −2J[cos k_x + cos k_y]`, band `[−4J, 4J]`.

## The MECHANISM (for implementation) [paper → ours]
The implementable object is: **(non-interacting bath + linear coupling of ≥2 system operators to the SAME
bath) → Block-Lanczos → width-N_O block-tridiagonal ladder → t-MPS.** For OUR twin the target mechanism —
a shared 1/f/TLS bath causing CORRELATED dephasing + COLLECTIVE relaxation across code qubits — maps as:
system operators `O^(i)` = the per-qubit coupling operators to the shared bath. **Dephasing/`σ_z`-type
coupling and relaxation/`σ−`-type coupling are BOTH admissible** because Eq. (2) puts NO restriction on
`O^(i)` (only linear in bath modes). The bath-mediated cross-qubit correlation is carried EXACTLY by the
off-diagonal blocks `T_i` of Eq. (6) plus the shared seed structure — it is NOT factorized per qubit.
Grounded parameters in the demo: `g/J` ∈ {0.05, 0.1, 1}, `Ω/J = −3.95` (band edge) or `0` (band center),
`L_trunc` 75–1000, δ 0.05–0.7, D 10–20, `n_max` 2–3, α=4. Repo status: **not yet implemented.** The
existing scalable carrier (`src/qec_twin/forward/scalable/mps_forward.py`, qutrit MCWF on a quimb MPS,
ADR 0010) is a per-site MCWF with NO shared-bath / bath-mediated-correlation representation — this BL
mapping is a DIFFERENT, complementary object (explicit bath in the tensor network, not a Lindblad/jump per
site).

## The OBSERVABLE / metric [paper]
- Total emitter excitation `C(t) = Σ_i ⟨σ+_i σ−_i⟩ = Σ_ℓ ⟨Π_ℓ⟩` (Eq. 19), pair projector
  `Π_ℓ = (2|2⟩⟨2| + |1+⟩⟨1+| + |1−⟩⟨1−|)_ℓ` (Eq. 20). Measures collective (super/sub)radiant decay.
- Central-pair occupation `C_1(t) = ½⟨Ψ|Π_1|Ψ⟩` (Eq. 22) — the many-excitation observable that
  distinguishes decay vs bound-state trapping.
- Bound-state fidelity `F(ρ,ϕ_em) = ⟨ϕ_em|ρ(t)|ϕ_em⟩` (Eq. 27), `ρ(t)` = reduced emitter DM; convergence to
  a non-zero plateau (~0.7) = dynamical bound-state preparation.
- **The informative signature of non-Markovianity here is DEVIATION of `C(t)`/`C_1(t)` from the Markovian
  (Lindblad/Dicke) prediction** — collective radiance is SUPPRESSED (not enhanced) by non-Markovian memory,
  growing with both `g/J` and `N_e`. [ours: this is a dynamics/occupation observable, NOT a coherence-revival
  |L(t)| probe — see our note `project-nonmarkovian-wedge-must-be-coherence.md`; the two are related but this
  paper's observable is emitter-population, benchmarked against Markov, not CP-divisibility.]

## Findings + numbers [paper]
- Single-excitation, `g/J=0.05`, band edge Ω/J=−3.95, `L_B=501²`: MPS **exactly matches** direct
  single-excitation diagonalization of the ORIGINAL Eq. (11) Hamiltonian (independent benchmark); Markovian
  prediction already fails for 4 and 6 emitters (Fig. 7a).
- Fully-excited, `g/J=0.1`: substantial deviation from Markov, collective radiation suppressed, worse for
  larger `N_e` (Fig. 7b).
- Strong coupling `g/J=1`, `L_B=301²`: collective radiance ABSENT; `C_1(t)` does not decay to zero ⇒ a
  many-excitation BOUND STATE; oscillation frequency DECREASES with more emitters (opposite to radiance).
  No energy truncation possible here (Fig. 7c).
- Diamond config, band center Ω=0, `g/J=0.05`, `L_B=701²`, 3-excitation initial state: bound-state fidelity
  rises and saturates to **~0.7** (Fig. 8); symmetry-matched initial state prepares the bound state better.
- Max demonstrated size: **6 emitters, up to 6 excitations**; bath effectively infinite (501²/701²).
- Ladder width after symmetry: `N_e/2` per sector (diagonal config); D=10–20, `n_max`=2–3.

## Limitations [paper]
- **Bath MUST be non-interacting (quadratic) and coupling MUST be linear in bath modes** (Eq. 2). Interacting
  baths are out of scope.
- **Cost grows FAST with #emitters**: ladder width = N_O ⇒ 1D long-range terms of range N_O ⇒ `O(Ñ²)` MPOs
  per step; "the presence of long N_O-range terms limits the practical application to problems with a reduced
  number of system operators." Symmetry only buys a constant factor. 6 emitters is the demonstrated ceiling.
- Efficiency RELIES on LOW excitation number (bounded by #emitters) to keep entanglement/bond dimension
  moderate; the bosonic-truncation-is-exact argument depends on excitation conservation (empty-bath start).
  A regime with many excitations / non-excitation-conserving coupling would be harder.
- Strong coupling is the hard regime: NO energy truncation, larger `n_max`, faster entanglement growth,
  smaller Trotter steps ⇒ shorter reachable times.
- Demonstrated only for VACUUM bath initial state and RWA (though the discussion claims thermal/
  counter-rotating are straightforward extensions, NOT shown).
- Only real-time dynamics + occupation/fidelity observables shown; no LER, no measurement/decoding, no
  multi-round circuit structure.

## Relevance to qec_twin (the shared-bath correlated-noise teacher) [ours]
Our target: a controlled-teacher noise source = a SHARED 1/f/TLS bath producing CORRELATED dephasing +
COLLECTIVE relaxation across the qubits of a full-2D surface code, multi-round — needing an INDEPENDENT exact
oracle to certify an approximate coupled simulator (per `project-coupling-nonmarkovian-is-the-contribution.md`,
`project-nonmarkovian-wedge-must-be-coherence.md`).

- **Does it KEEP the shared-bath coupling? YES.** The bath-mediated inter-emitter correlation is carried
  exactly (in the `L=L_B/N_O` limit) by the block-tridiagonal `T_i` couplings + shared seeds. It is genuinely
  NON-factorized and genuinely non-Markovian. This is exactly the physics our teacher's "contribution" wedge
  needs (unowned + non-removable correlated non-Markovian bath).
- **Non-Markovian memory: YES**, in any regime (the whole point). Includes the strongly-non-Markovian
  band-center regime where Lindblad/Green-function methods fail.
- **CORRECTION it forces / what it does NOT give us for QEC:**
  (1) It is a *spin-boson* / emitter-photon-bath object (bosonic bath, `σ±`/`σz` linear coupling), matching a
      Gaussian bosonic (1/f-as-oscillator-bath / spin-boson) model of TLS/1/f — but a *discrete TLS* bath
      (finite two-level fluctuators) is NOT a non-interacting bosonic bath and would need a different mapping.
  (2) It carries NO measurement / mid-circuit reset / decoding / multi-round-syndrome machinery. It is a
      continuous-time Hamiltonian evolution of populations, not a QEC circuit. To be a QEC oracle it would
      need Trotterized gates + projective syndrome measurement interleaved — a substantial extension the
      paper does not do.
  (3) The efficiency hinges on LOW excitation number bounded by #emitters. A full-2D surface code has many
      qubits (≫6) and, under relaxation, potentially many excitations — the width=#operators cost and the
      excitation-count entanglement growth are BOTH adverse. The demonstrated 6-emitter ceiling is far below
      d=3 (17 qubits) let alone d=5/d=7.

- **RELEVANCE VERDICT: (a) a SMALL-SCALE EXACT ORACLE — conditionally.** For a FEW qubits (≤ ~6) coupled to a
  shared Gaussian/bosonic dephasing+relaxation bath, in the RWA/excitation-bounded regime, this is a
  quasi-exact (convergence-controlled) reference that KEEPS the correlated non-Markovian coupling — precisely
  the independent oracle our anti-toy protocol demands (independent of a per-site MCWF carrier's blind spot).
  It is NOT (b) a scalable carrier for full-2D multi-round QEC (width + excitation cost + no circuit/readout).
  It is NOT (c) a memory closure in our sense. The specific faithfulness trade-off: it is exact for the
  *continuous Hamiltonian* shared-bath dynamics but says nothing about the *QEC circuit* wrapper, and it
  demands a bosonic (not discrete-TLS) bath and low excitation count.

## Error control [paper → ours]
- **A-PRIORI where it counts, convergence-only elsewhere.** (i) Length truncation `L_trunc` is bounded by a
  LIGHT-CONE / Lieb-Robinson argument — a-priori guarantee that truncating the chain past the light cone is
  harmless for time ≤ t_trunc [69,70]. (ii) Bosonic occupation cap `n_max` = #excitations is EXACT (excitation
  conservation) — a-priori zero error, though a smaller `n_max` is convergence-checked. (iii) BL itself is
  EXACT at `L=L_B/N_O` (unitary Q) — the whole scheme is quasi-exact by construction. (iv) Energy-window Δ and
  MPS bond dimension D are CONVERGENCE-only (Δ found numerically till convergence; the discarded-mode Lamb
  shift is bounded `δω_α < g0/Δ`, Eq. 10, which IS an a-priori error bound on the energy truncation). (v)
  Trotter step δ is convergence-checked. Overall: stronger error control than a phenomenological carrier —
  the load-bearing truncations (length, occupation) have a-priori bounds; D and δ are the usual TN/Trotter
  convergence knobs. Cited convergence-guarantee lineage: Woods-Cramer-Plenio [34], de Vega-Schollwöck-Wolf
  [35], Trivedi-Malz-Cirac [36].

## INDEPENDENT-ORACLE-ability [ours]
YES for the constrained regime above. Crucially it is INDEPENDENT of our implementation family: it is an
*explicit-bath* tensor-network evolution (bath in the TN), whereas our scalable carrier is a *reduced-system*
qutrit MCWF (bath integrated out into jumps). A shared blind spot is therefore unlikely — this satisfies
anti-toy Rule I (independent ground truth, not a parallel copy of our own engine). The paper itself
demonstrates the oracle pattern: it benchmarks the MPS against EXACT single/two-excitation diagonalization of
the ORIGINAL Hamiltonian (Fig. 7a) — the same anti-circular discipline we require. GT-feasibility for us: we
would (1) build the shared bosonic bath + linear multi-qubit coupling, (2) run BL + t-MPS for ≤~6 qubits,
(3) compare correlated-dephasing/relaxation observables against our approximate coupled simulator. The
extension cost is the QEC-circuit wrapper (interleaved gates + projective measurement), which the paper does
not provide.

## How to use / trust + open questions [ours]
- Trust: FULL-TEXT 精读; equations verbatim from the txt; figure NUMBERS taken from captions/text (figures
  not pixel-extracted).
- Open questions for implementation: (1) Can a discrete-TLS / 1/f bath be recast as an effective
  non-interacting bosonic bath faithfully enough to use this mapping, or does it need a genuinely interacting
  bath (out of scope)? (2) Can projective syndrome measurement + reset be interleaved into the t-MPS evolution
  without breaking the excitation-conservation argument that keeps `n_max`/bond dimension small? (measurement
  injects/removes excitations → the exactness-of-`n_max` premise may fail.) (3) What is the largest qubit
  count reachable for a QEC-relevant shared dephasing bath after symmetry reduction — is d=3 (17 qubits) even
  in range, or is this strictly a ≤6-qubit oracle? (4) Reuse target: our carrier lives in
  `src/qec_twin/forward/scalable/`; a BL oracle would be a NEW independent module (evaluator-only, per the
  isolation contract), used by `audit/certify` as an independent anchor — NOT fed to the learner.

---
Tags: **[paper]** = stated in 2407.10140 (with §/Eq/Fig ref). **[ours]** = our inference for qec_twin, not
the paper's claim.
