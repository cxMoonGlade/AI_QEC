# Full-text review — SiYing Wang, ZhiXin Xia, Yue Yan, Xiang-Bin Wang, "An exact Error Threshold of Surface Code under Correlated Nearest-Neighbor Errors: A Statistical Mechanical Analysis" (arXiv:2510.24181)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF `outputs/papers/2510.24181.pdf` →
> txt `outputs/papers/2510.24181.txt` (PyMuPDF, 8 pages / 32574 chars, complete through the
> reference list). All §/Eq/Fig/Table refs from that text. Figures not pixel-extracted — figure
> facts (Fig.5 crossings, Fig.6 curves) = captions + numbers stated in text. Paper is a short
> letter; no numbered section headings survived extraction (headers came through as
> "In Sec., we ...") — I refer to sections by name.

## Metadata [paper]
- **Authors / affiliation:** SiYing Wang, ZhiXin Xia, Yue Yan, Xiang-Bin Wang (corresponding,
  xbwang@mail.tsinghua.edu.cn). State Key Lab of Low Dimensional Quantum Physics, Dept. of
  Physics, Tsinghua University, Beijing.
- **Venue / status:** arXiv:2510.24181v1 [quant-ph], dated 28–29 Oct 2025. Preprint (no journal).
- **Type:** Theory (statistical-mechanical mapping) + a small parallel-tempering Monte-Carlo
  numerical example + a PyMatching/Stim decoder comparison.
- **Companion:** ref [33] = Wang, Yan, Xia, Wang, "Symmetry in multi-qubit correlated noise
  errors enhances surface code thresholds," arXiv:2506.15490 (2025) — same group, prior rung.

## Executive summary [paper]
The exact surface-code threshold is known for i.i.d. Pauli noise via the mapping to the 2D
random-bond Ising model (RBIM) on the Nishimori line [paper cites Dennis-Kitaev-Landahl-Preskill,
ref 6]. This paper extends that *exact* mapping to a noise model that adds **correlated ZZ errors
on nearest-neighbor data-qubit pairs** (rate `p2`) on top of i.i.d. single-qubit Z (rate `p1`).
The obstruction is that `P(E)` for correlated chains is a huge sum; they resolve it with an
**"error-edge map" (EEM)** that collapses correlated-pair error configurations onto edges of a
**square-octagonal lattice**, mapping `p_success` to the partition function of a
**square-octagonal RBIM** whose critical (Nishimori) point is the *exact* threshold — decoder-
independent, hence an upper bound that is also achievable. For the symmetric case `p1 = p2 = p`
their parallel-tempering MC gives an exact threshold of **≈3%**. They then run PyMatching 2.0:
correlation-blind i.i.d. decoding thresholds at **1.8%** (Fig.6 label ≈1.9%), and Stim-DEM
correlated-aware matching at **2.4%** — both below the 3% exact value, i.e. **~0.5–0.6% of
decodable headroom is left on the table by current decoders under correlated noise**.

## Method (deep) [paper]

### Noise model (the "CORRELATED ERRORS BETWEEN DATA QUBITS" section)
Z-only (X and Z corrected independently in the surface code; they analyze the Z sector).
- **i.i.d. phase flip**, Eq.(1):  `E(ρ) = (1−p1) ρ + p1 Z ρ Z†`, per data qubit, prob `p1`.
- **Correlated NN ZZ**, Eq.(2):  `E(ρ) = (1−p2) ρ + p2 Zi Zj ρ Zj† Zi†`, applied to each nearest
  data-qubit pair `{qi,j, qi−1,j+1}` and `{qi,j, qi+1,j+1}` with prob `p2`. (Subscripts are 2D
  lattice coordinates; the two orientations are the two diagonal NN pairings — Fig.1b.)
- Both channels act **simultaneously and may overlap** (Fig.1a). This is a *product of two
  independent stochastic channels*, NOT a joint 2-qubit Pauli-Lindblad fit: correlation enters as
  an explicit two-body ZZ jump at rate `p2`, independent of the single-body `p1`.

### The exact-mapping spine (the standard part)
`p_success` as a partition-function ratio, Eq.(3):
```
p_success = Σ_{E'E∈G} P(E') / Σ_{E'E∈C(G)} P(E')
```
`G` = stabilizer group, `C(G)` = centralizer. Correction succeeds iff `E'E ∈ G`; a logical error
occurs iff `E'E ∈ C(G)\G`. Standard Dennis et al. structure.

### The NEW piece — Error-Edge Map (EEM)
Direct `P(E)` is intractable: an illustrative chain has (Eq.4)
```
P(E1) ∝ [2 p2 (1−p2) / (1 − 2 p2 (1−p2))] · (p1/(1−p1))^2  +  (p1/(1−p1))^4
```
i.e. a correlated ZZ contributes the factor `2p2(1−p2)` (the two ways one of a paired set of
NN pairs can carry the error), and it competes/adds with pure-i.i.d. length-4 chains — the sum is
over many equivalent microscopic assignments. EEM removes this by working with **edges** not qubits:
- Connect neighboring ancilla qubits by edges. `l^k_1` = horizontal/vertical edge (i.i.d.
  single-qubit error on the data qubit on that edge). `l^k_2` = diagonal edge, `l^k_3` =
  anti-diagonal edge (the two correlated-pair orientations).
- **The key collapse rule:** a correlated ZZ on *either* pair of a matched set
  (`{qi,j,qi−1,j+1}` OR `{qi+1,j+1,qi+2,j}`) sets `nE'(l^k_2)=1`. If **both** pairs fire
  (prob `p2²`) the four Z's form the stabilizer `Zi+1,j+1 Zi+2,j Zi,j Zi+1,j+1` → **treated as no
  error**. Same for `l^k_3` (anti-diagonal). So a correlated *edge* is "on" with **effective**
  probability `2(1−p2)p2` (one-of-two fires, the both-fire case cancels as a stabilizer).
- Edge occupancy indicator, Eq.(5): `nE(l^k_i) = 1 if l^k_i ∈ Ẽ else 0`, `i∈{1,2,3}`.
- Recovery-chain probability, **Eq.(6)** (the implementable EEM formula):
```
P(Ẽ') ∝ Π_{i∈{1,2,3}} Π_{l^k_i} [ p̄i / (1 − p̄i) ]^{ nE'(l^k_i) }
```
  with the **effective edge probabilities**
```
p̄1 = p1,     p̄2 = 2(1−p2) p2,     p̄3 = 2(1−p3) p3.
```
  (The paper carries `p3` symbolically for the anti-diagonal orientation; in the symmetric example
  it sets everything equal, `p2 = p3`, and `p1 = p2 = p`.)
- They prove the coset sums match, Eqs.(7)–(8): closed cycles `C` ↔ `E'E∈G` (success), spanning
  lines `L` ↔ `E'E∈C(G)\G` (logical failure). `Al` = equivalence class of errors sharing the same
  edge-chain `Ẽ'` differing only by a stabilizer (Eqs.9–11).

### Mapping to the square-octagonal RBIM
Ising-ify the edge probabilities. Define sign variables `ηE(l^k_i)= +1 if l^k_i∉Ẽ else −1`
(Eq.12) and `u(l^k_i)= +1 if l^k_i∉Ẽ'+Ẽ else −1` (Eq.13). Then Eq.(6) becomes (Eq.14):
```
P(Ẽ') ∝ exp[ Σ_i Σ_{l^k_i} ½ Ji ηE'(l^k_i) ],   Ji = ln( (1 − p̄i) / p̄i ).
```
Place Ising spins `σ^k_{i,j} ∈ {±1}` at triangle centers of the dual square-octagonal lattice
(Fig.4). Map `M` (Eq.17):
```
u(l^k_1) ↦ σ4_{i,j} σ1_{i+1,j}   (horizontal)  or  σ3_{i,j} σ2_{i,j+1}  (vertical)
u(l^k_2) ↦ −½(σ1σ2 −1)(σ3σ4 −1) + 1
u(l^k_3) ↦ −½(σ1σ3 −1)(σ2σ4 −1) + 1
```
plus the **gauge/plaquette constraint Eq.(18):  `σ1_{i,j} σ2_{i,j} σ3_{i,j} σ4_{i,j} = 1`** (kills
unwanted partition-function terms). Result — the **square-octagonal RBIM partition function**,
Eq.(19):
```
Z = Σ_{σ} exp[ ½ J1 ηE(l1)(σ3_{i,j}σ1_{i+1,j} + σ4_{i,j}σ2_{i,j+1})
              + ½ J2 ηE(l2)(σ1σ2 + σ3σ4)
              + ½ J3 ηE(l3)(σ1σ4 + σ2σ3) ]
```
Effective Hamiltonian, **Eq.(20)**:
```
H = − Σ_{i,j} [ ηE(l1)(σ3σ1' + σ4σ2')
              + J'2 ηE(l2)(σ1σ2 + σ3σ4)
              + J'3 ηE(l3)(σ1σ4 + σ2σ3) ],
    with  σ1σ2σ3σ4 = 1,   J'2 = J2/J1,  J'3 = J3/J1.
```
- **Correlation enters exactly as the two ANISOTROPIC coupling ratios `J'2 = J2/J1` and
  `J'3 = J3/J1`.** These are the diagonal/anti-diagonal bonds; their strength relative to the
  i.i.d. bond `J1` is set entirely by `p2` vs `p1`. So the "shift" from the i.i.d. RBIM is a
  *lattice + anisotropy* change: NN correlation adds octagonal (diagonal) bonds.
- **i.i.d. limit is recovered exactly:** as `p2 → 0`, `J2, J3 → +∞`, forcing
  `σ1=σ2=σ3=σ4`, and the square-octagonal RBIM **degenerates to the standard 2D RBIM of ref [6]**.
  This is the paper's self-consistency check ([paper], text after Eq.20).
- **Nishimori line:** `β = J1 = −½ ln( p1/(1−p1) )` (Eq.21 text). Domain-wall free-energy cost
  Eq.(21): `Δi(τ) = βF(K,τi) − βF(K,τ) = ln( Z[K,τ] / Z[K,τi] )` — diverges (ordered/below-
  threshold ⇒ correctable) or stays finite (disordered/above-threshold ⇒ failure). `K` = the
  couplings `J'2, J'3`.

### Numerical determination (the "CALCULATING THRESHOLDS" section)
Symmetric case `p2 = p1 = p`. Parallel-tempering MC, finite-size scaling of the correlation
length. Wave-vector susceptibility `χ(k) = (1/L²)⟨|Σ_i s_i e^{i k·r_i}|²⟩`; finite-size
correlation length `ξ = [1/(2 sin(kmin/2))] √( χ(0)/χ(kmin) − 1 )`, `kmin = (2π/L, 0)`.
FSS ansatz Eq.(22): `ξ/L ≈ f[ L^{1/ν} (T − Tc) ]` — curves for different `L` cross at `Tc`
(Fig.5). Params in Table I: `L = {12,15,18,21,24}`, 600–800 disorder samples, `p` swept over
0.025–0.045, `Tmin∈[0.3,0.5]`, `Tmax=1`.

## The MECHANISM (for implementation) [paper → ours]
**Implementable in our teacher as a product of two independent stochastic Z channels:**
1. per data qubit: `Z` with prob `p1` (Eq.1) — already have i.i.d. Pauli.
2. per NN diagonal data-pair `{qi,j, qi−1,j+1}` and `{qi,j, qi+1,j+1}`: `ZiZj` with prob `p2`
   (Eq.2) — a two-body correlated ZZ jump, sampled independently of the single-body channel.

Grounded parameters: `p1, p2 ≥ 0` arbitrary ratio (`p2/p1` unrestricted — paper's headline
generality claim). Symmetric working point `p1=p2=p ∈ [0.025, 0.045]`; exact threshold at
`p1=p2` is **pc ≈ 3%**. Where in the circuit: data-qubit Z after the error step, correlated on the
two diagonal NN orientations only (nearest-neighbor, spatial). Repo: we do not have this exact
square-octagonal EEM mapping; our correlated-2q relaxation / crosstalk teachers
(`docs/twin_validation/m11_*`, `m12_correlated_2q_relaxation_*`) are the nearest existing
mechanisms — those are Lindbladian/relaxation-flavored, NOT the stochastic-ZZ + stat-mech-threshold
object here.

## The OBSERVABLE / metric [paper]
- **Primary (exact):** the surface-code **error threshold `pc`** = Nishimori critical point of the
  square-octagonal RBIM (Eq.20). Decoder-independent, so it is the *maximum achievable*
  threshold. Symmetric-case value **pc ≈ 3%** (MC, text after Fig.5; the text says "The
  calculated threshold is 3%").
- **Decode-relevant (the ΔLER analogue):** **logical error rate LER(p)** curves and the
  **decoder threshold gap** (Fig.6): i.i.d.-blind matching 1.8% (Fig.6 caption says ≈1.9%),
  Stim-DEM correlated-aware matching 2.4%, vs exact 3%. The **gap = pc(exact) − pc(decoder)** is
  the isolable "correlation is not being fully exploited" quantity ≈ **0.5–0.6%** (paper: "This
  remains 0.5% lower than our calculated threshold 3%"). This is *headroom left by the decoder*,
  the direct analogue of a decode-relevant ΔLER.
- **Susceptibility / correlation-length FSS** (`χ(k)`, `ξ/L`, Eq.22) — the estimator, not a QEC
  observable per se; crossing of `ξ/L` locates `Tc` ⇒ `pc`.

## Findings + numbers [paper]

| Quantity | Value | Source |
|---|---|---|
| Exact threshold, symmetric `p1=p2=p` | **≈ 3.0%** | MC + FSS, text after Fig.5 |
| PyMatching, correlation-**blind** (i.i.d. decode) | **1.8%** (Fig.6 label ≈1.9%) | decoder comparison |
| PyMatching + Stim-DEM, **correlated-aware** matching | **2.4%** | decoder comparison |
| Decoder gap to exact | **~0.5–0.6%** | "0.5% lower than 3%" |
| i.i.d. limit (`p2→0`) | reduces to standard 2D RBIM threshold of ref [6] | after Eq.20 |
| Effective edge prob (correlated) | `p̄2 = 2(1−p2)p2` | Eq.6 |
| Coupling | `Ji = ln((1−p̄i)/p̄i)`, anisotropy `J'2=J2/J1` | Eq.14, Eq.20 |
| Nishimori line | `β = J1 = −½ ln(p1/(1−p1))` | Eq.21 |

**Direction / magnitude of the correlation shift:** Correlated NN errors turn the plain 2D RBIM
into an **anisotropic square-octagonal RBIM** with extra diagonal bonds `J'2, J'3`. At the
symmetric point the *exact* threshold (≈3%) sits **above** what correlation-blind matching achieves
(1.8–1.9%) and even above correlated-aware Stim-DEM matching (2.4%). So (a) properly handled, the
NN-correlated code is *more* correctable than a naive-decoder estimate suggests, and (b) the exact
threshold quantifies decodable headroom (~0.5–0.6% at the symmetric point). The paper does NOT
tabulate `pc` vs `p2/p1` as a curve — it proves the mapping works for any ratio but only reports the
one symmetric number.

## Limitations [paper]
- **Nearest-neighbor, spatial-only, two-body ZZ.** Only diagonal/anti-diagonal NN data-qubit pairs
  (Eq.2). No next-NN, no >2-body correlations.
- **NO temporal correlation, NO non-Markovianity.** Purely a static spatial 2-body stochastic
  channel; time / measurement rounds do not enter the mapping. (The intro *motivates* with
  temporal & non-Markovian noise, ref [30,31], but the model and mapping cover neither.)
- **Z-sector only** (X/Z decoupled assumption); depolarizing/correlated-XZ not treated.
- **`p_success` factorization implicit** in EEM: the both-pairs-fire → stabilizer cancellation
  and the coset argument assume the specific NN pairing geometry; generality to arbitrary
  correlation graphs is not shown.
- **Exact threshold value is MC-derived**, not closed-form: the *mapping* is exact/analytic, but
  the reported `pc ≈ 3%` comes from parallel-tempering + FSS on `L≤24`, so it carries FSS
  uncertainty (paper gives no error bar; "3%" is stated to 1 sig-fig). The i.i.d. baseline in the
  paper's own text is internally loose (1.8% in the decoder-comparison prose vs "approximately
  1.9%" in Fig.6 caption).
- **Companion caveat:** the "symmetry enhances thresholds" story is in ref [33] (arXiv:2506.15490);
  this paper is the exact-mapping half.

## Relevance to qec_twin [ours]
**Verdict: a genuine but SCOPED independent analytic anchor for a *spatial-NN-correlated stochastic-
Z* teacher — NOT for our live non-Markovian / temporal-correlation wedge.**

- **Rule-I independent anchor (partial):** The square-octagonal RBIM Nishimori mapping (Eqs.6,
  14, 17–20) is an *implementation-independent* ground truth. Any correlated-error teacher/decoder
  we build that matches this exact noise model (i.i.d. `p1` ⊗ NN-ZZ `p2`, Z-sector) MUST reproduce:
  (i) the exact edge-probability rule `p̄2 = 2(1−p2)p2` (a closed-form check on how a two-body ZZ
  channel folds into an effective single-edge rate — this is a cheap, exact, non-circular unit
  test); (ii) the i.i.d.-limit degeneracy (`p2→0` ⇒ standard RBIM threshold ~10.9% for the
  Nishimori point of the plain code, or whatever ref-6 value applies); (iii) the symmetric-point
  exact threshold `pc ≈ 3%` (MC-grade, so a *bracket* not a zero-tolerance anchor). Item (i) is the
  strongest anchor — it is exact and closed-form.
- **Confirms correlation is decode-relevant, not benign:** YES — the ~0.5–0.6% gap between exact
  (3%) and even a correlated-aware Stim-DEM decoder (2.4%) is *positive and above the i.i.d.-blind
  baseline* (1.8–1.9%). This is direct external evidence that NN spatial correlation is a
  decode-relevant lever with real headroom, the analogue of a positive ΔLER — and independently
  supports our "correlation matters" framing.
- **Does NOT rescue our non-Markovian wedge.** Per MEMORY
  (`project-nonmarkovian-wedge-must-be-coherence`, `project-coupling-nonmarkovian-is-the-
  contribution`): our contribution must be *temporal / CP-divisibility-breaking* correlation that
  Markov-k and DD cannot capture. This paper's correlation is **static, spatial, Markovian,
  stochastic Pauli** — exactly the *removable/owned* class our red-team flagged as a strawman
  contribution. It is thus a **baseline/anchor**, not a novelty. Concretely: a Stim-DEM /
  Markov-k decoder already partially captures it (2.4% here), consistent with our finding that
  classical spatial-round-correlation is Markov-k-capturable.
- **Reuse:** the exact `p̄2 = 2(1−p2)p2` folding rule and the i.i.d.-limit degeneracy are worth
  adding as unit-test anchors if/when a spatial-NN-correlated Z teacher is built; the
  square-octagonal RBIM `pc≈3%` is a coarse cross-check bracket. Our `certify` seam (independent
  exact/declared anchors, ADR 0008) is the natural home. Existing nearest mechanisms:
  `docs/twin_validation/m12_correlated_2q_relaxation_*`, `m11_spectator_crosstalk_*` — but those
  are Lindblad-relaxation, not this stochastic-ZZ object, so the anchor does not transfer to them
  without re-deriving the effective edge rate for the relaxation channel.

## How to use / trust + open questions [ours]
- **Trust:** FULL text read; the mapping (Eqs.1–20) is stated verbatim and self-consistent (the
  `p2→0` degeneracy is a real internal check). The threshold *value* 3% is MC/FSS at `L≤24` with
  no quoted error bar (1 sig-fig) — treat as a **bracket**, not an exact number. The exact,
  citable pieces are the closed-form edge rule `p̄2=2(1−p2)p2`, the coupling `Ji=ln((1−p̄i)/p̄i)`,
  and the i.i.d.-limit degeneracy — those are theorem-grade within the paper's model.
- **Open questions for implementation:** (1) `pc` vs `p2/p1` curve is not given — if we want an
  anchor away from the symmetric point we must run the MC ourselves (their Table I is enough to
  reproduce). (2) The both-pairs-fire → stabilizer cancellation depends on the exact rotated-lattice
  pairing; verify the geometry matches whatever surface-code convention our teacher uses before
  reusing the edge rule. (3) Fig.6 caption (`d=9,15,21`) vs its legend text (`d=9,11,15`) disagree —
  minor, ignore. (4) The "3% exact" and "2.4% Stim-DEM" are the two numbers to cross-check against
  any spatial-NN-correlated decoder we run.
- **GT-feasibility:** HIGH for the closed-form edge rule (exact unit test, no simulation).
  MEDIUM for the threshold (needs our own parallel-tempering MC to get an error bar). The paper's
  own PyMatching/Stim comparison is reproducible with our vendored PyMatching + Stim baselines.
