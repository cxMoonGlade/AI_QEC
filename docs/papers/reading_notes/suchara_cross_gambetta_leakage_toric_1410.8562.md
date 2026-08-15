# Full-text note — Suchara, Cross & Gambetta, *Leakage Suppression in the Toric Code*

> **2026-07-13 taxonomy correction:** the paper supports a stochastic persistent-leakage model and
> leakage-heralded decoding; it does not prove that its record is non-reducible to every DEM/HMM,
> that a matched finite-order null cannot reproduce it, or that a passive syndrome record contains
> only Pauli/notion-2 structure. Treat the stronger project prose below as superseded by
> `docs/twin_validation/notion123_taxonomy_literature_closure_2026-07-13.md`.

> Provenance: full-text read of the 6-page PDF
> `docs/papers/suchara_cross_gambetta_leakage_toric_1410.8562.pdf`
> (owner-password-only encryption; text via `pdftotext -layout`, equations/tables/figures
> verified against Ghostscript-decrypted page renders at 150–300 DPI). Every page, every
> figure caption, and both tables were read. arXiv:1410.8562v1 [quant-ph], 30 Oct 2014.
> Published in *Quantum Information and Computation* (QIC) Vol. 15, No. 11&12 (2015).

> **[ours] framing corrected 2026-07-13** — leakage persistence can generate notion-2 record memory,
> but this paper does not prove non-reducibility to every Markov/DEM/HMM null. General notion-3
> certification is out of product scope by access choice, not closed by a universal twirl theorem.

---

## 1. Metadata

- **Title.** Leakage Suppression in the Toric Code.
- **Authors.** Martin Suchara (corresponding, `msuchar@us.ibm.com`), Andrew W. Cross, Jay M. Gambetta — all IBM T. J. Watson Research Center, Yorktown Heights, NY.
- **arXiv / venue / year.** arXiv:1410.8562v1, 30 Oct 2014; QIC 15(11&12), 2015. (Cross/Gambetta later co-authors of the IBM superconducting stack — the model is built with hardware leakage in mind.)
- **Object / type.** QEC fault-tolerance; a **stochastic leakage noise model** + **Monte-Carlo simulation** of leakage-aware syndrome extraction in the **toric code** + a **3-outcome ("heralded") syndrome-processing algorithm**. Not an experiment, not a learner — a *simulation + decoder-design* paper.
- **Path.** `docs/papers/suchara_cross_gambetta_leakage_toric_1410.8562.pdf`.

**One-sentence takeaway.** The paper defines a leakage model deliberately engineered to stay *inside the stabilizer formalism* (so leakage is simulable at code scale by propagating one extra classical bit per qubit), surveys four leakage-reduction circuits (No-LRU → Quick → Partial-LRU → Full-LRU) in the toric code, and shows that a decoder which **ingests 3-outcome "L" measurement outcomes and re-weights its matching graph conditionally** roughly *doubles* the leakage threshold versus a leakage-blind decoder.

---

## 2. TL;DR

- **The headline structural trick (Sec. 3).** Leakage is intrinsically a *coherent* qutrit process and hence hard to simulate at code scale. The authors replace it with a **stochastic, "|2⟩-dephased" model** whose defining property is that the code state stays a *mixture of leaked-or-contained qubits* under all model operations. That lets them drop the full stabilizer/density-matrix description and track **one Pauli label `∈ {I,X,Y,Z}` plus one leakage-indicator bit (label `L`) per qubit** — leakage simulation costs the same as ordinary stabilizer/Pauli-frame simulation (lines 343–390 of the extracted text; Eqs. 5–9).
- **Why it stays in the stabilizer formalism.** Two model choices destroy the correlations that would otherwise force a full quantum description: (a) when a contained qubit interacts with a leaked qubit it is **completely depolarized** (independent single-qubit Pauli, not a collective process), and (b) when a leaked qubit relaxes/resets it is replaced by a **completely mixed contained qubit**. So past syndrome history is uncorrelated with the reset state, and a leaked code qubit simply "turns off" the checks it would touch (Sec. 3, p. 6–7).
- **Four circuits (Sec. 4, Fig. 4).** *Full-LRU* (LRU after every gate, 16 extra gates/qubit/cycle), *Partial-LRU* (one LRU per data qubit per cycle, 4 extra gates/data qubit), *Quick* (a SWAP folded into the last CNOT — **one extra CNOT per data qubit, no extra ancillas**), and *No-LRU* (the standard circuit, reference point; data qubits never reset → leakage saturates). The LRU is a **one-bit-teleportation** circuit (Fig. 3), valid as an LRU *because the model's ideal two-qubit gates are "sealed"* (do not propagate leakage).
- **Two decoders.** The **Standard decoder** (leakage-blind; uses pre-computed translation-invariant edge weights, Table 1) and the **Heralded-Leakage (HL) decoder** (Sec. 5), which assumes 3-outcome measurements reporting "L" iff the measured qubit is leaked, and **builds a conditional, non-translation-invariant decoding graph** with low-weight edges placed in the space-time neighborhood of each "L" event.
- **Key numbers.** With **no leakage** (`r=0`) the No-LRU threshold ≈ **0.70 %**, Full-LRU ≈ **0.22 %** (Fig. 11a, Table 2). When leakage rate ≈ depolarizing rate (`r=1`), the Partial-LRU/Quick circuits keep the threshold reduced by **< 4×** with the Standard decoder; the **HL decoder recovers a factor ≈ 2**, i.e. < 2× reduction (Abstract; Sec. 7–8). Below physical error rate **2×10⁻⁴**, the Full-LRU may give the lowest logical error rate of all circuits (Fig. 12b, Table 2 exponents `γ`).
- **Cost.** ~30,000 CPU-hours on an IBM Blue Gene/Q; ≥10⁴ iterations and ≥10³ failures per configuration; Blossom V matching + Boost shortest-paths (Sec. 6).

---

## 3. Main contribution + core method (full technical detail)

The abstract states three contributions: (1) a leakage **model** that "differs in critical details from earlier models", (2) a **Monte-Carlo survey** of several syndrome-extraction circuits, and (3) — given 3-outcome measurements — a "**dramatically improved syndrome processing algorithm**". Below, each in the detail our program needs.

### 3.1 The toric-code substrate and the decoding graph (Sec. 2)

Standard toric-code setup on a `d×d` torus: `n = 2d²` data qubits on edges, vertex (star) `A_v = ∏_{ℓ∈N(v)} X_ℓ` (Eq. 2) and face (plaquette) `B_f = ∏_{ℓ∈N(f)} Z_ℓ` (Eq. 3) checks, each weight-4, measured with an ancilla prepared in `|0⟩` (plaquette) or `|+⟩` (star) and four CNOTs in the fixed order U, L, R, D (the gate order of Wang–Fowler–Hollenberg [9] / Stephens [8]). One cycle = 6 steps → one noisy `2d²`-bit syndrome. **`O(d)` cycles** are needed for fault tolerance; the simulation uses **`d` rounds + one final perfect round** (Sec. 6).

Decoding is **classic Dennis–Kitaev–Landahl–Preskill MWPM** on a 3D decoding graph `G=(V,E)`, **separately for X and Z** (Edmonds' algorithm; here Blossom V). The unit cell (Fig. 2) has **six distinctly-weighted edge types**: `a` (vertical = measurement error), `b`,`d` (horizontal = qubit errors), `c`,`e` (diagonal = correlated qubit–measurement errors), `f` (correlated qubit–qubit–measurement). A defect sits on a vertex whose two incident "a" edges carry different syndrome labels; edge weight = `−log p(ε)` so MWPM returns a most-likely error. The `b–d` and `c–e` weight symmetry is **broken** by the non-atomic, ordered CNOT schedule (Sec. 4, Table 1 caption).

### 3.2 The leakage model (Sec. 3) — *the centerpiece for us*

Each physical subsystem is a **qutrit**: `H_S[j] = H_C[j] ⊕ H_L[j]`, computational `H_C` = span{|0⟩,|1⟩}, leakage `H_L` = span{|2⟩}. A qubit is **leaked** if its state lives entirely in `H_L`, **contained** if in `H_C`. A gate is **sealed** if it block-diagonalises over the containment pattern — a sealed two-qubit gate is

```
U = U_{HC[i]⊗HC[j]}  ⊕  U_{HC[i]⊗HL[j]}  ⊕  U_{HL[i]⊗HC[j]}  ⊕  U_{HL[i]⊗HL[j]}        (Eq. 4)
```

so it **does not propagate leakage** between the leakage and computational sectors. The paper argues real microwave/resonance-driven superconducting gates are *approximately sealed* (all blocks except `HC⊗HC` are ~diagonal in the undriven-Hamiltonian eigenbasis; refs [24,25]).

The **stochastic faulty-gate model** adds three elements on top of sealed ideal gates:

1. **Discrete leakage (excitation), prob. `p↑`.** Independently on each output qutrit of an ideal gate,
   ```
   E↑(ρ_j) = (1 − p↑) ρ_j + p↑ |2⟩⟨2|.                                              (Eq. 5)
   ```
2. **Relaxation (amplitude-damping analogue), prob. `p↓`.** Independently on each output qutrit,
   ```
   E↓(ρ_j) = (1 − p↓) ρ_j + p↓ E_decay(ρ_j),                                        (Eq. 6)
   E_decay(ρ) = A ρ A† + Σ_{k=0,1} A_k ρ A_k†,                                       (Eq. 7)
   A = |0⟩⟨0| + |1⟩⟨1|,   A_k = (1/√2) |k⟩⟨2|.                                       (Eq. 8)
   ```
   These Kraus elements are chosen so that **a decaying leaked qubit is replaced by a *maximally mixed contained* qubit** (½(|0⟩⟨0|+|1⟩⟨1|)).
3. **Two-qubit-gate handling.** A sealed two-qubit gate applies the intended op on the `HC⊗HC` block; the `HL⊗HL` block is a harmless global phase; the **mixed `HC⊗HL` / `HL⊗HC` blocks each apply a Haar-random single-qubit unitary to the *contained* partner → the contained qubit is *completely depolarized***. Noisy two-qubit gates are then followed by independent `E↑`,`E↓` on each output.

The **fixed-point / "|2⟩-dephased" property (Eq. 9).** With `Z(2) = |0⟩⟨0|+|1⟩⟨1|−|2⟩⟨2|` and the dephasing channel `Φ(ρ) = ½(ρ + Z(2)ρZ(2))`, any initial fixed point `ρ_0` of `Φ` stays a fixed point under all `E↑, E↓`, sealed single-qubit gates, and the two-qubit model — i.e. the system stays a **classical mixture over leaked/contained patterns** at all times. This is the lemma that licenses the simulation simplification.

**Why earlier models differ (explicit in the paper).**
- vs. **loss/erasure models** ([15,16], 50 % loss threshold): those convert leakage to a *detected loss at a known space-time location* and measure high-weight "super"-stabilizers — natural for measurement-based QC but awkward on a fixed planar array. Here leakage is **not** an erasure: a 3-outcome "L" detection only localizes the leak to *somewhere between a qubit's init and its measurement*, and **leakage induces ordinary Pauli errors whose pattern depends on where it happened** (Sec. 5, opening). "A 3-outcome measurement is **not** equivalent to a simple erasure model."
- vs. **Aliferis–Terhal [1]** (concatenated-code LRU threshold, fully coherent worst-case): this paper trades the coherent worst case for a *stochastic proxy* amenable to stabilizer simulation in a *topological* code.
- vs. **Fowler's repetition-code leakage model [19]:** explicitly contrasted (line 422). Suchara et al. **start each simulation from the steady-state leakage population** (more faithful to a long computation), whereas [19] does not.
- **Deliberately not worst-case.** The Haar-random depolarisation in the mixed blocks **destroys correlations** that a fixed-unknown-unitary model would keep; so when several contained qubits touch one leaked qubit they suffer *independent* depolarising noise, not a collective channel (lines 327–341). The authors flag this as an optimistic ("not worst-case stochastic") choice, justified because in topological codes a leaked qubit touches few neighbours and is reset within a few cycles.

**Steady-state leakage population (Sec. 3, end).** Data qubits in the No-LRU circuit are never re-initialised, so leakage accumulates to the transition-matrix equilibrium

```
p_eq ≈ 4 p↑ / (4 p↑ + 6 p↓)                                                        (Sec. 3)
```

(numerator 4 = four CNOTs; denominator 6 = four CNOTs + two idle steps). The second eigenvalue `(1−p↑)^6 (1−p↓)^4` gives a relaxation rate `μ = −6 ln[(1−p↑)(1−p↓)]`, so the non-equilibrium part decays like `exp(−μn)`. Under `p↓ ≳ p↑` the leaked-data fraction reaches **≈ 40 %**, far past threshold — i.e. **without leakage reduction the toric code is unusable**. This is the quantitative motivation for the LRU circuits.

**Model parameters (the simulator's dials, Sec. 3 summary).** `p` (depolarizing gate/init/idle error), `q` (measurement error, set `q=p`), `p↑` (excitation), `p↓` (relaxation), with **relative excitation `r = p↑/p`** and **relative relaxation `s = p↓/p`**. Elementary-gate behaviour:
- *Idle:* depolarize w.p. `p` (uniform X/Y/Z); no leakage; a leaked idle qubit may relax w.p. `p↓`.
- *Prep `|0⟩`/`|+⟩`:* succeeds w.p. `1−p` (else orthogonal state), then leaks w.p. `p↑`.
- *Measure:* contained qubit reports wrong outcome w.p. `p`. **Leaked qubit → two scenarios:** either the meter cannot tell |2⟩ from |1⟩ and **reports "1"** (Standard model), or it has a **third outcome "L"** (Heralded model).
- *CNOT:* joint depolarize w.p. `p` (uniform over the 15 non-identity two-qubit Paulis); **if any input is leaked, every non-leaked input is completely depolarized** (uniform single-qubit Pauli); each output then leaks w.p. `p↑`, relaxes w.p. `p↓`.

### 3.3 Leakage-reduction circuits (Sec. 4)

LRUs satisfy (a) identity on a contained input, (b) map a leaked input back into the computational space [1]. Here the LRU is **one-bit teleportation** (Fig. 3, ref [26]) rather than full quantum teleportation [27] — *cheaper*, and a valid LRU *only because* the model's ideal two-qubit gates are sealed (can't output a pair of leaked qubits). The four error-correction circuits, most→least aggressive:

| Circuit | Leakage reduction | Extra cost vs standard | Notes |
|---|---|---|---|
| **Full-LRU** | LRU on every output of every gate (à la [1]) | **16 extra gates / qubit / cycle** (4 LRUs) | best suppression; no LRU on ancillas pre-measurement |
| **Partial-LRU** | one LRU per data qubit per cycle (while ancillas are measured) | **4 extra gates / data qubit** | ancillas reset anyway; can detect leakage on **both** ancillas (measured) and data (via LRU) |
| **Quick** | SWAP data↔ancilla folded into the last CNOT (3 CNOTs = SWAP, gate cancellation) | **1 extra CNOT / data qubit, no extra ancillas** | data/ancilla trade roles; each physical qubit reset every *other* cycle; ≈ [21]'s superconducting scheme |
| **No-LRU** | none (standard Fig. 1 circuit) | 0 | reference; data never reset → leakage saturates to `p_eq` |

For the surface code (open boundaries) the Quick SWAP can alternate U/D qubits on odd/even cycles, needing only `O(d)` boundary ancillas.

**Standard-decoder edge weights (Table 1).** For each circuit the prior of edge `ε ∈ {a,b,c,d,e,f}` is `p(ε) = Σ_j p_j(ε)` summed over single-fault locations `j` that produce the defect pair `{∂ε}`; weight `= −log p(ε)`. The leakage-reducing circuits add **no new edge types** to `G` (only re-weight) for the *Standard* decoder, which **does not account for leakage events and is therefore expected to be suboptimal**.

**Table 1 — Standard-decoder edge weights** (entries are `−w_ε`, i.e. the exponent; `q` set `=p`):

| Circuit | `exp(−w_a)` | `exp(−w_b)` | `exp(−w_c)` | `exp(−w_d)` | `exp(−w_e)` | `exp(−w_f)` |
|---|---|---|---|---|---|---|
| No LRU | `31/15 p + q` | `28/15 p` | `16/15 p` | `52/15 p` | `8/15 p` | `8/15 p` |
| Quick | `7/3 p + q` | `32/15 p` | `4/3 p` | `4 p` | `8/15 p` | `8/15 p` |
| Full-LRU | `103/15 p + q` | `52/15 p` | `88/15 p` | `172/15 p` | `32/15 p` | `32/15 p` |
| Partial-LRU | `31/15 p + q` | `52/15 p` | `16/15 p` | `76/15 p` | `8/15 p` | `8/15 p` |

(Full-LRU's `e`,`f` weights are 4× the others — the 4 LRU locations. No-LRU's `a` weight exceeds [9] because these circuits include ancilla initialisation.)

### 3.4 The Heralded-Leakage (HL) decoder (Sec. 5) — *the "3-outcome syndrome processing" contribution*

**Assumption:** measurements have a third outcome **"L"**, reported **iff** the input qubit is leaked (optimistic, perfect heralding). No change to the quantum circuit — only the classical decoder changes. The HL decoder is applied to the **Partial-LRU and Quick** circuits.

**Why it helps and why it is not erasure.** In this model a leaked qubit produces ordinary errors on **specific known locations** (its neighbours), so on an "L" event the decoder can lower the matching cost of *exactly those* space-time edges. But "L" is only seen *when a qubit is measured* (in an LRU or a syndrome readout), so it localizes the leak only to the interval **[init, measurement]** — hence the need for a *conditional probability* over fault positions, not a point erasure.

**Algorithm (conditional decoding graph `G_L`):**

1. Start from the Standard graph `G` (weights = Table 1).
2. Each "L" event is treated **independently** (model's leakage events are independent). For an "L" on qubit `q`, enumerate the `n` fault locations between (and including) `q`'s init and its measurement. Since each gate leaks independently and equally, **`P(q leaked when it interacts at the i-th location) ≈ i/n`**, and an X (or Z) error lands on the qubit that interacts with `q` at location `i` with probability
   ```
   p_i = i / (2n).                                                                 (Sec. 5)
   ```
3. For each such error, find the defect pair it creates, and **update that edge's probability** (it may be a *new* low-weight edge not in `G`). Combining the prior `p_0` already on the edge with `p_i`:
   ```
   p_new = p_0 + p_i − 2 p_0 p_i        (XOR/serial composition of two error mechanisms). (Sec. 5)
   ```
   New weight = `−log p_new`. Because `p_i` can be large (close to ½), these are **very-low-weight edges** in the space-time neighbourhood of the "L".
4. **Missing-syndrome handling.** If "L" occurs *while measuring a syndrome*, that syndrome bit is **absent** from the history. For a run of "L" at contiguous times `t+1,…,t+m` on one check, set the corresponding `a`-edges `e_{t+1},…,e_{t+m}` to **weight 0**; if the check's bit at `t` differs from `t+m+1`, place a **defect on the earliest vertex** in that run. (This is the leakage analogue of erasure-edge handling.)
5. `G_L` is **generally not translation-invariant** and has *extra* edges → the decoder cannot use coordinate-distance shortcuts and must run a **shortest-path algorithm** (Boost) on the whole graph before matching (Blossom V).

Worked examples are given for the **Quick circuit** (11 leakage locations on the leaked qubit between init and measurement → e.g. the long edge `p_1` connecting `α` and `γ` qubits arises with prob ≈ `1/22`; Figs. 5,6) and the **Partial-LRU circuit** (5 ancilla leakage locations, 9 data leakage locations; Figs. 7–10). Example: in Partial-LRU an ancilla is leaked after its 2nd CNOT with prob `3/5`, spreading a Z to qubit R with `p_3 = 3/10`, which modifies a specific diagonal edge (Figs. 7, 8c). For the data-qubit case the conditional probabilities use `p_i = i/18` (9 locations × 2) and `i/10` (5 locations × 2) respectively (Figs. 8, 10 axis labels).

### 3.5 Simulation method (Sec. 6)

- Propagate a label `∈ {I,X,Y,Z,L}` per data **and** ancilla qubit through the chosen circuit under the Sec. 3 model. `E↑` traces out the qubit and sets `L`; `E↓` resets `L` and replaces the qubit with a completely mixed state; sealed 1q gates act as intended on contained, identity on leaked; sealed 2q gates act as intended on (contained,contained), **depolarize the contained partner** on (contained,leaked), identity on (leaked,leaked).
- Simulate **`d` rounds + 1 perfect final round** (leaked qubits replaced by depolarized ones, syndromes read noiselessly); decode **all `d+1` syndromes together**; register a **failure** iff the post-correction code state **anticommutes with a logical operator**.
- **Steady-state initialisation:** each qubit starts with label `L` with the circuit-appropriate probability — persistent (never re-initialised) data qubits start at the `p_eq` of Sec. 3.
- Tools: **Boost** shortest paths (for the non-translation-invariant HL graph), **Blossom V** [29] matching. ≥10⁴ iterations, ≥10³ failures per point; ~30,000 CPU-hours on Blue Gene/Q.

---

## 4. Key results (with figures & tables)

### 4.1 Thresholds vs leakage (Fig. 11a, Table 2)

Thresholds estimated from the `d=7`/`d=9` failure-rate crossover, scanning `r` in steps of 0.1, `p` in steps of 0.01 %, at `s=1`.

- **No leakage (`r=0`):** simpler circuits win — **No-LRU ≈ 0.70 %**, Quick/Partial-LRU intermediate, **Full-LRU ≈ 0.22 %** (more locations → lower threshold, as expected).
- **Quick ≈ Partial-LRU** thresholds (differ visibly only for `r<0.3`): the Quick circuit's fewer gates roughly offset the Partial-LRU's more frequent re-initialisation.
- **HL beats Standard once `r ≳ 0.3`** and the gap grows with `r`. The threshold decays **monotonically** with `r` for every circuit/decoder.
- **Idealized-decoder bound.** Treating each leakage as a depolarizing error of strength `λ=3/4` and effective rate `p̃=(1+r)p`, a leading-order argument gives logical error `p = A p̃^m + O(p̃^{m+1}) = A(1+r)^m p^m + …` (Eq. 10), threshold `p_thr ≈ [A(1+r)^m]^{−1/(m−1)}` (Eq. 11), and the **threshold-ratio law**
  ```
  p_thr(r) / p_thr(0) = (1+r)^{−m/(m−1)}  ≈  1/(1+r),                               (Eq. 12)
  ```
  i.e. **threshold ≈ α/(1+βr)**. A Standard decoder cannot exceed this idealized bound; a 3-outcome decoder *can* in principle — and the HL decoder's measured threshold tracks the idealized curve (Fig. 11a).

### 4.2 Threshold independent of relaxation rate `s` (Fig. 11b)

For the Quick+HL circuit, sweeping `s ∈ {0.1, 1, 10}` leaves the threshold essentially unchanged — relaxation is slow compared with the circuit's own leakage-reduction rate.

### 4.3 Sub-threshold logical error rates (Fig. 12, Table 2)

At `r=s=1`, failure rate vs `p` for `d=7,9,11`. Crossings give thresholds; the **slope on a log scale gives the suppression exponent `γ`** in `LER ∼ A p^{γ d}`. The **Full-LRU LER falls faster** below threshold and crosses below the others — *"for low enough physical error rates the Full-LRU circuit will be better"* — explicitly, **when `p < 2×10⁻⁴`** (Abstract).

**Table 2 — fitted `threshold ≈ α/(1+βr)` and sub-threshold `LER ∼ A p^{γ d}`:**

| Circuit / decoder | `α` (≈ threshold %, r=0) | `β` | `γ` (LER exponent) |
|---|---|---|---|
| idealized | 0.65 | 3/4 | n.a. |
| Full-LRU | 0.22 | 1.72 | 0.67 |
| Quick | 0.65 | 3.59 | 0.45 |
| Partial-LRU | 0.55 | 2.55 | 0.46 |
| **Quick (HL)** | 0.62 | **1.23** | {0.45, 0.52, 0.64} for d=7,9,11 |
| **Partial-LRU (HL)** | 0.55 | **0.92** | {0.48, 0.53, 0.65} for d=7,9,11 |

Reading: the HL decoder roughly **halves `β`** (Quick 3.59→1.23; Partial-LRU 2.55→0.92) — i.e. the threshold degrades with leakage about **2× more slowly** than under the Standard decoder. The HL `γ` is given per-distance because the simulations are still seeing higher-order LER terms at accessible `p` (the lowest-order exponent not yet reached). Full-LRU has the steepest single-rate exponent `γ=0.67`, consistent with it winning at very low `p`.

### 4.4 Headline claims (Abstract / Conclusion)

1. Simple circuits with **one extra CNOT/qubit and no extra ancillas** (Quick) reduce the threshold by **< 4×** when leakage ≈ depolarizing.
2. With **3-outcome (HL) decoding** that becomes **< 2×** (a factor-2 improvement over the Standard decoder).
3. Below `p = 2×10⁻⁴`, the **Full-LRU** (LRU after every gate) may give the **lowest LER** of all circuits considered.
4. The closely related **planar and rotated** codes are expected to show the same thresholds; ideas should generalize to other topological codes.

---

## 5. **Useful for our project**

Our program uses this paper for a declared stochastic leakage/seepage model and scalable record-generation ideas. Persistent leakage can create notion-2 record memory, but whether a declared Markov-`k`/DEM/HMM family reproduces it is an empirical model-class question, not a theorem from this paper. Notion-3 is a separate process-level access class; the passive record is not thereby proved to contain only Pauli/notion-2 structure. Faithfulness still requires comparison to an independent oracle on the full declared record ladder.

**(a) Canonical leakage+seepage SOURCE model + the "faithfulness vs an independent oracle" question.**
- This is a **canonical stochastic leakage model** with two physically-motivated channels the simulator can generate directly: **excitation** `E↑(ρ)=(1−p↑)ρ + p↑|2⟩⟨2|` (Eq. 5) and **seepage/relaxation** `E↓` with Kraus `A=|0⟩⟨0|+|1⟩⟨1|`, `A_k=(1/√2)|k⟩⟨2|` mapping a leaked qubit to the **maximally mixed contained** state (Eqs. 6–8). These are exactly the "leakage + seepage" source primitives, in closed Kraus form — the rates and channels are **targets the generated record must reproduce**. Our canonical T1/T2 Kraus channels compose with these on the `{|0⟩,|1⟩,|2⟩}` qutrit.
- **The model is a stochastic proxy for coherent qutrit leakage.** The paper deliberately replaces
  mixed two-qubit blocks by Haar-random single-qubit depolarisation of the contained partner, discarding
  some leakage-induced correlations. The resulting discrepancy must be bounded against an independent
  coherent-qutrit reference on the joint detector law and downstream LER. The paper leaves quantifying a
  worst-case stochastic model to future work; it does not establish that any particular matched null is
  incapable of reproducing those correlations.
- **`α/(1+βr)` (Eq. 12) is a ready sanity-law.** Any leakage record the simulator generates should reproduce a monotone threshold-vs-`r` decay close to `1/(1+r)` when scored downstream, and the leakage-blind idealized `λ=3/4` depolarizing bound (Eqs. 10–12) is the leading-order behaviour it must respect. This is a cheap *predict-before-measure* plausibility gate on the generated source (theory-first discipline) — a downstream cross-check, not a validity leg.

**(b) How to generate the leakage record at scale — the decisive idea for us.**
- The **"|2⟩-dephased" fixed-point lemma (Eq. 9)** is the trick that makes leakage **stabilizer-simulable at code scale**: track **one Pauli label + one leakage bit (`L`) per qubit**, no density matrix (Sec. 3, lines 343–390). This is *exactly* the generation regime the simulator wants — it scales to surface-code `d` like ordinary Pauli-frame/Stim simulation. Concretely, the propagation rules to implement: `E↑` sets `L` (trace out the qubit); `E↓` clears `L` and injects a completely-mixed (→ uniform Pauli-frame) qubit; a sealed 2q gate on (contained, leaked) **completely depolarizes the contained input** (uniform single-qubit Pauli) and acts as identity on (leaked, leaked). A leaked **data** qubit silently drops itself from the checks it would join; a leaked **ancilla** "turns off" its check. This is the cheapest faithful way to generate the leakage source, and it produces **honest binary detectors** `{det}` (plus an optional per-readout "L" flag) — the correct record shape. Its faithfulness is the leg to certify: bound the stabilizer proxy against the exact qutrit-DM oracle (`src/error_coupling_simulator/carrier/exact/qutrit_dm.py`) / the qutrit-MPS reference (`leakage_tensor_network_simulation_2308.08186`).
- **Steady-state seeding (`p_eq ≈ 4p↑/(4p↑+6p↓)`, Sec. 3)** is a detail the generator must copy: never-reset data qubits must start at their equilibrium leakage population, else the generated record under-states leakage in long runs. The 40%-leaked No-LRU saturation is the *positive control* that the simulator's leakage accumulation is wired correctly — a faithfulness check on the source.
- **The correlated multi-round record is the relevant notion-2 object.** Because a leaked qubit can persist across rounds until it relaxes, its "L" interval imprints correlations on neighboring detector events (Sec. 5). This motivates explicit record-memory tests. It does not prove non-reducibility to every DEM/HMM/finite-order family; that depends on the allowed model class and tested history depth.

**(c) The "L" herald / soft-info as an additional faithful OUTPUT channel of the record.**
- The paper specifies *exactly what leakage information the record carries and how it correlates with the syndrome*, which is the OUTPUT-channel spec for the simulator. The **3-outcome "L" herald** is a per-qubit, per-measurement classical flag, available **only at LRU/syndrome-measurement times**, that localizes a leak to an *interval* and implies **high-probability Pauli errors on the leaked qubit's space-time neighbours** with the explicit weights `p_i=i/(2n)` and composition `p_new=p_0+p_i−2p_0p_i` (Sec. 5). For the simulator this maps cleanly to an **additional faithful output channel** alongside `{det, obs}`: the binary detector tensor plus a parallel **leakage-herald tensor**, and — when readout is analog — a **soft-info/IQ tensor** (`soft_readout.py`). The Sec. 5 conditional structure (`p_i`, `p_new`) is the *ground-truth correlation the generated herald channel must reproduce* against the qutrit oracle; it is a richer OUTPUT, not a validity leg. The **missing-syndrome rule** (absent bit on an "L", zero-weight `a`-edges, defect on the earliest vertex of a contiguous "L" run) is the principled way the record represents leaked readouts — reproduce it as the record's masking convention.
- **The Standard-vs-HL gap measures the value of the declared leakage herald to those decoders.** The Standard decoder is leakage-blind (re-weights edges but ignores "L"); the HL decoder uses the herald and **roughly doubles the leakage threshold** (`β`: 3.59→1.23 Quick, 2.55→0.92 Partial-LRU; Table 2). This is downstream evidence that the herald is useful under the paper's model and perfect-heralding assumption; it is not a proof that every matched Pauli/latent model is incapable of representing the record.

**Cross-references in our tree.** Same leakage axis as the program memory note *decoder-gate-and-frontier* (the non-Pauli leakage/soft-readout/T1T2 source line). Complements `marton_asboth_coherent_readout_surface_2303.04672.md` (the *coherent*+readout axis, exact FLO) — Suchara is the *leakage* axis with the opposite tradeoff (stabilizer-cheap but correlation-lossy, vs FLO exact-but-coherent-only). The exact-qutrit faithfulness reference is `src/error_coupling_simulator/carrier/exact/qutrit_dm.py` (+ the qutrit-MPS of `leakage_tensor_network_simulation_2308.08186` for scale); the herald/soft-info is an output channel of the generated record (`soft_readout.py`). Master handoff: `docs/twin_validation/HANDOFF_static_simulator_notion2_2026-07-06.md`.

---

## 6. Limitations / what does **not** apply to us

- **W1 — optimistic perfect heralding.** The HL decoder assumes the meter reports "L" **iff** the qubit is leaked (Sec. 5). Real readout has **leakage-detection error** (false/missed "L") and, on superconducting hardware, "L" is entangled with the *analog IQ* distribution rather than a clean classifier output. The ≈2× HL benefit is therefore an **upper bound**; the simulator's soft-readout output channel (`soft_readout.py`) must generate imperfect heralding (the IQ tail of |2⟩ overlapping |1⟩), which is *more* realistic and the actually-interesting regime. **What carries over:** the herald as a faithful output channel of the record; **what does not:** the perfect-heralding factor-2 number.
- **W2 — not worst-case; correlations deliberately simplified.** The Haar-random depolarisation in
  mixed two-qubit blocks makes neighboring errors independent under the proxy, whereas coherent leakage
  can create collective correlations. The direction and magnitude of the record error are not fixed by
  this paper. Treat the proxy as a baseline and bound its full-record gap against an independent
  coherent-qutrit reference; do not label the missing structure unforgeable by every Markov/DEM model.
- **W3 — toric, translation-invariant, phenomenological-ish.** Results are on the **toric** code (periodic boundaries); planar/rotated are only *conjectured* equal (Abstract). The Standard decoding graph is translation-invariant; edge weights are single-fault counts (Sec. 4), not a full circuit DEM. The simulator's target is the **rotated surface code on real Google layouts**, so the *numbers* (0.70 %, 0.22 %, Table 1 weights) are not directly portable — the *source model* is.
- **W4 — no continuous/coherent leakage dynamics, no T1/T2 inside the leak.** Leakage is a discrete per-gate Bernoulli (`p↑`) with stochastic relaxation (`p↓`); there is **no Markovian/coherent qutrit evolution**, no T1/T2 during the leaked interval, no seepage-rate physics beyond the `E_decay` Kraus. The simulator intends *canonical T1/T2 Kraus* on the qutrit; those must be **composed** onto this source ourselves — this paper supplies the leakage/seepage half of the generated source, not the relaxation-during-leakage half.
- **W5 — Standard decoder edge weights are model-specific.** Table 1 weights are derived **for this exact stochastic model and gate order**; they are not a general leakage DEM (and a matched Pauli-DEM null is exactly the null the leakage record must beat). Useful as a *worked example* of how leakage imprints correlated structure on the syndrome, not as numbers to reuse.
- **W6 — decoder is MWPM, classical, offline.** No learning, no real-time constraint, no scalability study of the HL shortest-path matching. All of §5's decoder machinery is downstream *use* of the record (`docs/METRICS.md`), outside the simulator's validity chain; the *source model* — leakage+seepage channels, the |2⟩-dephased generation rule, steady-state seeding — is what transfers.

---

### Appendix — equation/figure index (for citation)

- **Eq. 4** sealed two-qubit gate (block-diagonal, no leakage propagation).
- **Eq. 5** excitation `E↑`; **Eqs. 6–8** relaxation `E↓` / `E_decay` / Kraus `A, A_k`.
- **Eq. 9** the dephasing fixed-point ("|2⟩-dephased") lemma.
- **`p_eq ≈ 4p↑/(4p↑+6p↓)`** steady-state leakage population (Sec. 3, unnumbered).
- **`p_i = i/(2n)`**, **`p_new = p_0 + p_i − 2 p_0 p_i`** HL conditional-edge construction (Sec. 5, unnumbered).
- **Eqs. 10–12** idealized-decoder threshold law `≈ α/(1+βr)`.
- **Table 1** Standard-decoder edge weights (4 circuits × 6 edge types).
- **Table 2** fitted `α, β, γ` (6 circuit/decoder rows).
- **Fig. 1** toric code + syndrome-extraction circuits; **Fig. 2** decoding-graph unit cell (edges a–f).
- **Fig. 3** one-bit-teleportation LRU; **Fig. 4** Full-/Partial-/Quick circuits.
- **Figs. 5–6** Quick-circuit "L" event → conditional X/Z edges (11 locations).
- **Figs. 7–8** Partial-LRU ancilla "L" (5 locations); **Figs. 9–10** Partial-LRU data "L" (9 locations).
- **Fig. 11** (a) threshold vs `r`, all circuits/decoders + idealized bound; (b) threshold vs `s` (≈ flat).
- **Fig. 12** failure rate vs `p` at `r=s=1`, `d=7,9,11` (linear / log) — Full-LRU steepest sub-threshold slope.
