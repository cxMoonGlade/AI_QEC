# Full-text review — Cygorek & Gauger, "ACE: A general-purpose non-Markovian open quantum systems simulation toolkit based on process tensors" (arXiv:2405.19319)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF `outputs/papers/2405.19319.pdf` → txt
> `outputs/papers/2405.19319.txt` (PyMuPDF, 20 pages, 98894 chars). All §/Eq/Fig/Table refs from that
> text. Figures not pixel-extracted — figure facts = captions + numbers stated in text.

## Metadata [paper]
- Authors: Moritz Cygorek (TU Dortmund, Condensed Matter Theory) & Erik M. Gauger (Heriot-Watt, SUPA/IPaQS).
- Venue / status: arXiv:2405.19319v2, 30 Jul 2024. Companion software paper for the ACE code release
  v1.2.1 (Zenodo DOI 10.5281/zenodo.13124376). C++11, config-file driven.
- Type: methods / software toolkit paper (the physics methods are from the authors' prior papers refs
  39/45/48/36; this paper documents the code + usage). NOT a QEC paper.

## Executive summary [paper]
ACE is a general-purpose numerically-exact solver for **zero-dimensional (few-level) open quantum
systems strongly coupled to multiple, general non-Markovian environments**, built on **process-tensor
matrix-product operators (PT-MPOs)**. The core object is a PT-MPO that encapsulates the *entire*
environment influence, is computed **once** and is **independent of the system Hamiltonian**, so it can be
reused across driving protocols, reused to extract multi-time correlators, and — crucially for us —
**stacked** with other PT-MPOs to give a numerically exact solution for a system coupled to several
environments, and combined to propagate **small networks** of open systems. The headline algorithm
(ACE, ref 39) handles **any environment decomposable into `N_E` independent modes** (phonon/photon/
fermion/spin/anharmonic, possibly lossy or driven); Gaussian spin-boson methods (Jørgensen–Pollock,
divide-and-conquer, periodic) are also implemented. Cost is dominated by the PT-MPO inner bond
dimension χ (O(χ³) propagation) and by system dimension D (O(D⁸) for Jørgensen–Pollock; O(D⁴D_M⁶)
per SVD for general off-diagonal ACE coupling to modes of dim D_M), with degeneracy exploitation
(§II.D) the main lever that has let them reach >30 system levels.

## Method (deep) [paper]

### PT-MPO propagation (§II.A)
Total Liouvillian split `L = L_S + L_E` (Eq. 2), where `L_S` is system-only and **`L_E` contains the
system-environment interaction AND acts on both** (Eq. 2 text). Trotter split (Eq. 3, first-order shown;
symmetric second-order is the code default per §II.E), time grid `t_j = t_0 + j∆t`. Tracing out the
environment (assuming an **initially factorized** total state `ρ(0) = ρ̄(0) ⊗ ρ_E(0)`, Eq. 4) gives the
exact-up-to-Trotter reduced propagation

- Eq. 5: `ρ̄_{α_n} = Σ I_{(α_n α'_n)...(α_1 α'_1)} (Π_l M_{α'_l α_{l-1}}) ρ̄_{α_0}`, with `α_j=(ν_j,µ_j)`
  the combined Liouville index, `M = e^{L_S ∆t}` the system propagator, and `I` the **generalized
  Feynman–Vernon influence functional** (footnote 50: "generalized" = allows off-diagonal / non-commuting
  couplings that induce transitions `α_l ≠ α'_l`, beyond the diagonal position-coupling FV case).
- Eq. 6: influence functional written as an MPO, `I = Σ Q^{(α_n α'_n)}_{d_n d_{n-1}} ... Q^{(α_1 α'_1)}_{d_1 d_0}`,
  a chain of matrix products over **inner bonds `d_l`** (edges pinned `d_n=d_0=0`).
- Eq. 7: the propagatable form `ρ̄_{α_n} = Σ_{d_n} q_{d_n} Π_l ( Σ Q^{(α_l α'_l)}_{d_l d_{l-1}} M_{α'_l α_{l-1}} ) ρ̄_{α_0} δ_{d_0,0}` — polynomial (not exponential) in the number of time steps. `q_{d_n}` is the closure.

**The compression that makes it exact-yet-tractable:** identifying `Q = e^{L_E ∆t}` naively gives inner
bonds the size of the full environment Liouville space (intractable). Instead the influence is laid out as a
2D tensor network and contracted row-by-row with **SVD sweeps keeping σ_k ≥ ε σ_0** (ε = `threshold`),
auto-selecting the most relevant environment-excitation subspace. Ref 36 view: `Q = T e^{L_E ∆t} T^{-1}`
with lossy compression `T` — the PT-MPO matrices ARE the compressed environment propagator projected
onto the relevant excitation subspace. **This is the "compress system-environment correlations before
folding" idea**: environment influence is compressed into the PT-MPO (once), then folded against the
system propagator `M` step-by-step (Eq. 7 / Fig. 1a). The PT-MPO knows nothing about `M`.

### ACE algorithm — the independent-modes requirement (§II.B, Eq. 8) — THE SCOPE STATEMENT
> "It can be applied to general environments that consist of `N_E` independent modes. Consequently, the
> environment Liouvillian can be decomposed as `L_E = Σ_{k=1}^{N_E} L_E^{(k)}` (Eq. 8), where `L_E^{(k)}`
> **only affect the system and the k-th environment mode**. Similarly, the initial states of the modes are
> uncorrelated `ρ_E(t_0) = Π_k ρ_{E,(k)}(t_0)`."

PT-MPOs are built per mode (`Q ← e^{L_E^{(k)} ∆t}`, multiply by `ρ_{E,(k)}(t_0)` first step, trace last),
then combined pairwise/sequentially with SVD compression after each combine. Tree-like variant (ref 48)
combines neighbours pairwise (binary tree) → 1–2 orders of magnitude faster; the last few large-bond
combines use a preselection SVD step (ref 45).

### Multi-environment stacking (§II.A last ¶, §II.E, Fig. 1b) — numerically EXACT
A system coupled to two or more environments is simulated with **two (or more) PT-MPOs computed
independently and stacked** — the result stays numerically exact (refs 36/39). The compressed-propagator
view explains why: each PT-MPO is `T e^{L_E^{(i)} ∆t} T^{-1}` and stacking reconstructs the joint
influence. For non-commuting interaction Hamiltonians they recommend `propagate_alternate true`
(Eqs. 16–18): a symmetric Trotter over the *joint* environment `e^{(L_E^{(1)}+L_E^{(2)})(2∆t)} =
e^{L_E^{(1)}∆t} e^{L_E^{(2)}(2∆t)} e^{L_E^{(1)}∆t} + O(∆t³)` alternating the outer-index multiplication
order.

### Outer-bond / degeneracy reduction (§II.D) — the D-scaling lever
Outer bonds `β_l=(α_l,α'_l)` span D⁴. They store only ONE representative when `Q^{β}=0` for all
(d_l,d_{l-1}) or when `Q^{β}=Q^{β'}` for β≠β' — i.e. they exploit **degeneracies of the eigenvalues of
the system coupling operator `Â`**. Diagonal `Â` ⇒ `Q ∝ δ_{α_l,α'_l}` ⇒ D² not D⁴. **When the
environment couples to only one subsystem of a composite system, the coupling operator is highly
degenerate on the composite space** and the PT-MPO cost collapses to that of the bare subsystem
(the QD-cavity example §IV.F: 6-dim composite, but PT-MPO cost = that of an isolated 2-level system,
"automatically identified by the code"). `add_PT ... [n_left] [n_right]` temporarily expands the outer
bonds of a subsystem PT-MPO to act on `H_left ⊗ H_S^{(0)} ⊗ H_right` (§IV.G).

## The MECHANISM (for implementation) [paper → ours]

**Spin-boson environment** (Eq. 9): `H_E = Σ_k ħω_k b_k†b_k + Σ_k ħ(g_k* b_k† + g_k b_k) Â + ∆H_PS`,
`Â` Hermitian on the **system Hilbert space** (can be composite/multi-site), `∆H_PS = Σ_k(|g_k|²/ω_k)Â²`
the polaron-shift counter-term. Bath fully specified by `Â` + spectral density `J(ω)=Σ_k|g_k|²δ(ω-ω_k)`
+ temperature T; Gaussian, so all correlators reduce to the two-time `C(t)` (Eq. 10).

**Generic mode via Boson generator** (Eq. 15): `H_E^{(k)} = Σ_k ħω_k b_k†b_k + Σ_k ħg_k(Â b_k† + Â† b_k)`,
where `Â = Boson_SysOp` is a **matrix-valued expression on the full (possibly composite) system space**.
Config knobs: `Boson_N_modes`, `Boson_M` (dim/mode), `Boson_omega_min/max`, `Boson_temperature` (K),
`Boson_J_from_file` or `Boson_J_type`, `Boson_g`/`Boson_rate`, `Boson_subtract_polaron_shift`.
Method select: `use_Gaussian[_divide_and_conquer|_periodic] true`, `use_combine_tree true`.
Fully explicit modes via `add_single_mode {H_E on H_S⊗H_mode} {ρ_mode(0)}`.

**How collective/multi-qubit coupling is expressed:** the coupling operator `Â` (`Boson_SysOp`, or the
system operator inside `add_single_mode`'s `H_E`) is written on the composite system space, so it CAN be
a collective operator like `σ_1^± + σ_2^±`. In the superradiance demo (§IV.G) the *collective radiative*
coupling is a Markovian Lindblad `2κ D[σ_S^-]`, `σ_S^± = (1/√2)(σ_1^±+σ_2^±)` (Eqs. 20), added with a
multi-site collapse operator `{|0><1|_2 otimes Id_2 + Id_2 otimes |0><1|_2}`. The **phonon baths there are
LOCAL / per-QD** (two separate PT-MPOs via `add_PT QDPhonon.pt 0 2` and `add_PT QDPhonon.pt 2 0`).

## The SHARED-BATH question — SETTLED FROM THE TEXT [paper → ours]

**Verdict: ACE CAN represent a single (non-Markovian, PT-MPO) bath coupling to a COLLECTIVE / multi-site
system operator. The independent-modes requirement (Eq. 8) is a constraint on the BATH decomposition,
NOT on how many system sites a mode may touch.**

Settling evidence, verbatim from the text:
1. Eq. 8 requires `L_E = Σ_k L_E^{(k)}` with `L_E^{(k)}` acting on "**the system** and the k-th
   environment mode" — "the system" is the *whole* (composite) system, and the modes (not the sites)
   must be independent with uncorrelated initial states.
2. In the spin-boson/Boson-generator interaction (Eqs. 9, 15) the coupling operator `Â` is "a general
   Hermitian operator [that] acts only on the **system Hilbert space**" — with no restriction that `Â` be
   single-site. Setting `Â = σ_1 + σ_2` (or any collective coordinate) gives ONE bath / one spectral
   density coupling to MULTIPLE qubits through a common coordinate = a **shared / collective bath** with a
   single PT-MPO. This is exactly a **correlated-dephasing shared bath** if `Â = Z_1 + Z_2 + ...` (diagonal
   collective coupling) — and diagonal `Â` even triggers the cheap D²-outer-bond path (§II.D).
3. §II.D explicitly discusses **decoherence-free subspaces** arising "when [system states] couple
   identically to the local phonon bath" — i.e. the code already handles multiple system states sharing
   one bath coordinate (the biexciton-exciton diamond example, refs 55/56).

**Where the verifier's "CONTESTED" flag resolves:** the confusion is bath-modes vs system-sites. ACE
does NOT allow the *bath modes* to be mutually correlated (must factorize, Eq. 8) — but it fully allows a
mode (or a whole spectral density) to couple to a *collective system operator spanning many qubits*. A
genuinely SHARED bath (one J(ω), one Â=Σ_i O_i) → single PT-MPO. Independent per-site baths → one
PT-MPO per site, stacked. **Collective DISSIPATION** (`D[Σ_i σ_i^-]`, superradiance) is likewise
expressible; in the demo it is Markovian-Lindblad (flat J), but a non-Markovian collective bath is the
`Â=Σ_i σ_i` PT-MPO. What ACE canNOT do is have two *separate* PT-MPOs share correlated bath modes — a
shared bath must be one PT-MPO with a collective `Â`.

## SCALING / cost [paper]
- **System dimension D:** Jørgensen–Pollock Gaussian PT-MPO nominally **O(D⁸)** (footnote 70: SVD of a
  row is O(NM²) with M=D², N=MD²). General ACE off-diagonal coupling to modes of Hilbert dim D_M:
  single-SVD **O(D⁴ D_M⁶)**. *(The prompt's "2603.06840 d⁸→d⁴ improvement" is NOT cited/present in this
  paper — the D⁸ is stated but no d⁸→d⁴ reduction ref appears here; the Chebyshev low-rank idea of ref 72
  arXiv:2407.11327 is floated for larger systems, not a d⁸→d⁴ theorem.)*
- **Degeneracy collapse (§II.D):** the O(D⁴) outer bond drops to D² (diagonal Â) or to the bare-subsystem
  cost (environment on one subsystem). This is what let them reach **>30 system levels** (4-level QD + two
  bosonic modes dim-3 each, ref 71; superradiance from **5 closely-spaced emitters**, ref 45).
- **Inner bond χ:** dominates — O(χ³) for propagation; χ "strongly depends on the concrete environment
  and is difficult to estimate a priori." Strongly-structured spectral densities (narrow peaks, long
  memory) blow χ up: the FMO 62-mode demo (§IV.H) hit χ ~ 1000 at ε=3×10⁻⁴, hours of compute.
- **Time steps:** polynomial in n; Gaussian divide-and-conquer O(n log n), periodic PT-MPO
  O(n_mem log n_mem) independent of total n → **million-time-step** simulations (ref 45).
- **"Small networks" limit (§V):** multi-partite propagation multiplies matrices of size
  (Π_i D_i)·(Π_i χ_i) — **exponential in the number of network parts**. This is the stated bottleneck;
  future work = TEBD-style many-body techniques on the network (ref 43). Convergence heuristic:
  `N_E = 0.4(ω_max-ω_min)(t_e-t_a)`.

## What ACE CANNOT do at multi-qubit-code scale [paper → ours]
- **The system Hilbert space is dense.** ACE treats the composite system as one D-dim object (D⁴ outer
  bonds before degeneracy). A d=3 surface-code patch (≥17 qubits → D≥2¹⁷, DM Liouville 2³⁴) is FAR
  beyond the >30-level ceiling. ACE is a **small-system / small-network** exact solver, not a code-scale
  carrier. It has no MPS/PEPS factorization of the *system* register (only the *environment* influence is
  MPO-compressed). Multi-round × full-2D surface code is out of scope by orders of magnitude.
- **Bath modes must factorize** (Eq. 8) — genuinely correlated *bath modes* across sites cannot live in
  separate stacked PT-MPOs; they must be folded into one collective-`Â` PT-MPO (fine physically, but the
  single PT-MPO's χ then carries all the cross-site environment excitations → χ grows).
- **Network scaling is exponential in # parts** (§V) — even the "small networks of open systems" story
  is bounded to a handful of sites.

## ERROR CONTROL [paper]
**Convergence-controlled, numerically exact — NOT a fixed-order approximation.** Two knobs:
(1) **Trotter error** O(∆t²) first-order / O(∆t³) symmetric — controlled by `dt`, checked by ∆t→0
extrapolation (Fig. 4 inset shows the O(∆t²) trend; odd/even zigzag under `propagate_alternate` is itself
a Trotter-error indicator); (2) **MPO compression error** — controlled by `threshold` ε, with
`threshold_range_factor`, forward/backward/select ratios, `final_sweep_n`. Guidance (§IV.D): compression
error at fixed ε depends on ∆t (don't compare across ∆t); the **maximal inner bond dimension** is the more
stable absolute-error indicator (extract via `PTB_analyze`). Caveat (§IV.H): at high T, **trace
preservation drifts to several % even at the smallest threshold** — so an independent reference is advised
even for "converged" runs. Preselection-based methods can fail to converge with decreasing threshold at
small ∆t (needs fine-tuning). **No a-priori error bound — it is convergence-study-based.**

## INDEPENDENT-ORACLE-ability [paper → ours]
**Yes — ACE ships with, and validates against, genuinely independent exact references**, which is exactly
what our anti-circular faithfulness protocol demands:
- **Polaron-transform closed form** for free coherence decay `⟨σ_x(t)⟩` at H_S=0 (Eq. 23, §IV.H) — an
  analytic exact expression the PT-MPO is checked against.
- **Analytic photon-coincidence / g²** for the phonon-free superradiance case (§IV.G, refs 4/41).
- **Independent-boson model** analytic solution (super-Ohmic coherence plateau, §IV.G).
- **TEMPO** binary (same config file) and **QUAPI** — methodologically distinct path-integral solvers —
  serve as cross-checks (TEMPO matches Eq. 23 "perfectly"; recommended as a reference in the high-T regime
  where PT-MPO trace drifts).
Thus a small-network ACE run is itself an **independent exact oracle** for a shared/collective-bath model
in the regime where it converges (few qubits, controlled χ).

## Relevance to the QEC digital-twin (oracle / carrier / closure / N/A) [ours]

**Verdict: ORACLE (independent, small-N, exact) — NOT a carrier; NOT a closure at code scale.**

- **As an ORACLE — strong fit.** ACE is precisely the independent, implementation-disjoint,
  convergence-controlled exact reference our faithfulness protocol (rule I) requires for a **SHARED bath →
  correlated dephasing + collective dissipation across a FEW qubits**. It can encode: correlated dephasing
  via one PT-MPO with diagonal collective `Â = Σ_i Z_i` (+ a J(ω) with the target memory kernel);
  collective/superradiant dissipation via `D[Σ_i σ_i^-]` (Markovian) or a collective-`Â` bath
  (non-Markovian); per-site independent baths via stacked PT-MPOs. It is **non-Markovian-native** (the
  whole point) — so it can certify the CP-divisibility-breaking / coherence-revival signatures our
  non-Markovian wedge rests on (see `project-nonmarkovian-wedge-must-be-coherence`,
  `project-coupling-nonmarkovian-is-the-contribution`). Because it is config-file-driven C++ with distinct
  math (PT-MPO path integral, not MCWF-on-MPS), it is genuinely INDEPENDENT of our qutrit-MCWF-on-quimb
  carrier — a real second-method cross-check, not "our own qutip."
- **NOT a carrier.** The system register is dense (D⁴/D⁸ scaling, >30-level ceiling, exponential in
  network parts). It cannot represent a full-2D multi-round surface-code register — that stays our
  MPS/PEPS carrier (ADR 0010, `project-fulld-1dmps-wall-and-2dpeps`). ACE compresses the *environment*,
  we must compress the *system*.
- **Closure:** N/A at code scale; only a small-window closure oracle.

**Trade-off / how to use:** run ACE on a **2–5-qubit window** (matching our small-window-twin identity,
`docs/plan3.md`) with a shared/collective bath to get an EXACT reduced density matrix / observable, then
certify our carrier's window against it (the carrier↔DM↔closed-form seam, `audit/certify`). Its own
polaron/TEMPO cross-checks give a second independent layer. This directly answers the "needs an
independent oracle" clause of our shared-bath teacher: ACE is that oracle for the collective-bath few-qubit
window; it is NOT the scalable engine.

## How to trust + open questions [ours]
- **Trust:** FULL-text read; all equations/scalings transcribed from the text. Figures not pixel-extracted
  (fig facts = captions + in-text numbers) — does not affect the method/scope conclusions, which are all
  in prose/equations.
- **Open (for a decision, not settled by this paper):**
  1. Effect-size / χ feasibility: how large does the PT-MPO inner bond χ get for a *diagonal collective*
     `Â=Σ_i Z_i` correlated-dephasing bath across k qubits with a realistic QEC-relevant J(ω)? Diagonal Â
     gives the cheap D²-outer-bond path, but χ (the real cost) is env-dependent and un-estimable a priori —
     must be measured on a pilot run.
  2. Units/regime: ACE defaults are ps/meV/K (solid-state emitter units). A QEC bath (µs gates, MHz
     couplings) is just a dimensionless remap (multiply energies by ħ, temperatures by ħ/k_B, per §III.B) —
     mechanical, but must be done carefully so J(ω) and the memory time are in-band.
  3. The "d⁸→d⁴" improvement of arXiv:2603.06840 referenced in the task is **NOT in this paper** — verify
     that separately if that speedup is load-bearing (this paper states O(D⁸) Jørgensen–Pollock and floats
     ref 72 Chebyshev low-rank for larger systems, no d⁸→d⁴ claim).
  4. Collective *dissipation* non-Markovian: the superradiance demo uses a Markovian collective Lindblad;
     confirm on a pilot that a fully non-Markovian *collective-emission* bath (collective `Â` into a
     structured J(ω)) converges at acceptable χ before relying on it as the collective-dissipation oracle.
