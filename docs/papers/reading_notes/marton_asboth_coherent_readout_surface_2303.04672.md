# Deep review — Márton & Asbóth, Coherent Errors and Readout Errors in the Surface Code

> Deep reading note (academic-paper-review format; full read Secs. 2–4 incl. both
> error metrics, the 3D-syndrome readout model, the FLO covariance simulation, and
> the threshold results). **Relevance to the twin** centerpiece.

## Metadata
- **Authors.** Áron Márton, János K. Asbóth (Budapest Univ. of Technology; Wigner Research Centre).
- **Venue / status.** Quantum 7, 1116 (2023); arXiv:2303.04672. Peer-reviewed (Quantum, CC-BY).
- **Domain / type.** QEC / fault tolerance; **simulation** (extends Bravyi FLO to coherent + readout).

## Executive summary
The paper extends Bravyi et al.'s exact coherent surface-code simulation to **coherent + readout errors**, on the **rotated** surface code, via the Majorana/fermionic-linear-optics (FLO) covariance-matrix method (`O(d⁴)`, `d` up to 19). Coherent storage noise `Û=∏_j e^{iθẐ_j}` (`p=sin²θ`) yields a **per-syndrome logical rotation** `|Φ_s⟩=e^{iθ_L(s)Ẑ_L}|ψ_L⟩` (Eq. 13). The paper defines **two** logical-error metrics: the **diamond-norm distance** `p_L^d=2Σ_s P(s)|sin θ_L(s)|` (Eq. 14, = Bravyi's `P^L`) and the **maximum infidelity** `p_L^i=Σ_s P(s)sin²θ_L(s)` (Eq. 15) — and they **prefer the maximum infidelity** as "a more natural generalization of the logical error rate for coherent errors." Readout errors are modeled phenomenologically (`P(1→0)=P(0→1)=q`, Eq. 16) giving a **3D syndrome** decoded by 3D MWPM with **distinct spacelike (readout, weight `log((1−q)/q)`) and timelike (physical, `log((1−p)/p)`) edge weights** (Eq. 21); across rounds the logical angle **accumulates**, `θ*(s)=Σ_{j=1}^d θ_L^j(s_1,…,s_j)` (Eq. 31), from **inhomogeneous (per-qubit) coherent errors**. Findings: with `p=q`, the **threshold ≈ 2.6%** (worst-case fidelity); below it, coherence **washes out** at large `d` but logical rates stay **above** the Pauli-twirled channel; **coherent errors are more critical than readout** (easier to tolerate ≥10% readout by lowering coherent than vice versa).

For the twin this paper (i) **clarifies the surface metric ladder** — the *primary* Márton metric is **maximum infidelity** (`p_L^i`, Eq. 15), with diamond-norm (`P^L`) secondary; (ii) supplies the **readout-noise harden axis** (the first richer mechanism beyond pure storage coherence, with the spacelike/timelike 3D structure); and (iii) gives the **scalable exact coherent+readout teacher** with per-round, per-location coherent accumulation — the surface analogue of the twin's multi-round parity-backend forward.

## Contributions (claim → evidence → strength)
- **C1. Exact coherent + readout simulation (FLO covariance, `O(d⁴)`, Sec. 3).** *Evidence:* C4-code Majoranas (Eq. 26–27); covariance `(2d²)⁴` vs `2^{d²}` state; inhomogeneous-coherent decomposition (Eq. 28–31). *Strength: strong (the technical extension).* 
- **C2. Two coherent metrics; max-infidelity preferred (Eq. 14–15, 24–25).** *Evidence:* explicit definitions + stated preference. *Strength: strong (the metric clarification).* 
- **C3. 3D-syndrome readout decoding with `p≠q` weights (Sec. 2.5–2.6).** *Evidence:* Eq. 16–22; spacelike/timelike weights Eq. 21; Fig. 2. *Strength: strong.*
- **C4. Threshold ≈2.6% (p=q); coherence washes out but > twirl; coherent > readout in criticality (Sec. 4).** *Evidence:* Fig. 3 (`d≤19`, finite-size scaling). *Strength: strong.*

## Method (deep)
- **Encoding.** Rotated surface code; logical rotation property needs **even-weight X-stabilizers + odd-weight logical-Z**. Post-correction `|Φ_s⟩=e^{iθ_L(s)Ẑ_L}|ψ_L⟩` (Eq. 13), `θ_L(s)` state-independent.
- **Metrics.** `p_L^d` (diamond, Eq. 14) and `p_L^i` (max infidelity, Eq. 15); with readout, averaged over both the perfect `s` and noisy `s'` (Eq. 24–25).
- **Readout / 3D.** `q` readout error; `d` rounds → 3D syndrome; 3D MWPM (PyMatching) with spacelike (readout) and timelike (physical) edges, weights `w_s,w_t` from `p,q` (Eq. 21); last round assumed perfect (to return to code space).
- **FLO.** Track the `(2d²)⁴` covariance matrix under free-fermionic evolution + Majorana-pair measurement; sample `θ*(s)` in `O(d⁴)`. Multi-round = inhomogeneous single-round coherent errors `Û_j=ÛĈ_{s_{j-1}}`; angles accumulate (Eq. 29–31).

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | Exact FLO; correct per-syndrome rotation structure; metrics rigorously defined; 3D decoding standard. |
| Novelty | **4** | Extends Bravyi (coherent storage) to **coherent + readout** with 3D decoding — a real, useful step, not a paradigm shift. |
| Reproducibility | **5** | Quantum (CC-BY); methods + PyMatching + sampling counts (5000×100) explicit. |
| Experimental design | **4** | Multiple `d` (≤19), finite-size scaling, `p`-vs-`q` plane mapped; single-axis coherent + phenomenological readout. |
| Statistical rigor | **4** | Finite-size-scaling threshold fit; large sample counts; honest that the Pauli ansatz "also fits" coherent numerics. |
| Scalability | **4** | `O(d⁴)` to `d=19`; covariance-matrix method is the enabling efficiency. |

## Strengths
- **S1 — the metric distinction made explicit (Eq. 14 vs 15).** Stating *both* the diamond-norm and the maximum-infidelity logical-error measures, and arguing for max-infidelity as the natural coherent generalization, is exactly the clarity a metric-disciplined project needs.
- **S2 — realistic readout via the 3D syndrome (Sec. 2.5).** Adding phenomenological readout with separate spacelike/timelike weights is the first faithful step toward circuit-level coherent QEC, and the `p≠q` weighting is handled correctly.
- **S3 — the `p`-vs-`q` criticality result (Sec. 4).** "Coherent errors are more critical than readout" is a concrete, decoder-relevant finding with a clean tradeoff statement.

## Weaknesses / limitations
- **W1 — single-axis coherent + phenomenological readout.** Still `e^{iθZ}` only (FLO constraint) and idealized readout (perfect last round); no coherent gate errors / hyperedges (that is Takou–Brown 2510.23797).
- **W2 — the Pauli-finite-size-scaling ansatz is borrowed.** The threshold fit uses the *random-Pauli* scaling ansatz, which "also fits" the coherent numerics — convenient but not derived for coherent noise; thresholds are estimates.
- **W3 — `P^L`/`p_L^i` are exact for *pure rotations* only.** Once stochastic noise mixes in, the `sin θ_L` forms are proxies, not exact channel distances — the metric caveat to carry.

## Relevance to the twin
This paper is the **surface-port novelty-adjudication baseline** and the source of its metric and readout-axis decisions:
1. **It pins the surface metric ladder.** The project's hard metric rule has a live trigger: `surface_logical_coherence = Bravyi P_L` (diamond, Eq. 14) is "mislabeled diamond norm," and **"infidelity (Márton primary) not yet computed"** — *that primary infidelity is `p_L^i=Σ_s P(s)sin²θ_L(s)` (Eq. 15) of this paper.* So the twin's surface coherence claims must report **maximum infidelity (Márton primary)**, with diamond-norm `P^L` secondary, and carry W3 (exact only for pure rotations). This paper is the definition both metrics must cite.
2. **The readout-noise harden axis.** Coherent + readout with the **3D syndrome and spacelike/timelike weights** is the first *richer* mechanism beyond pure storage coherence — the surface analogue of the rep-code "ancilla/measurement noise needs the ancilla backend" boundary. When the twin's harden step adds measurement noise, this is the reference for the structure (`p≠q` edge weights) and the expected effect (lower threshold, coherent > readout criticality).
3. **The scalable exact coherent+readout teacher.** The FLO **covariance-matrix** method (`O(d⁴)`, `d≤19`) is the certified large-`d` coherent+readout teacher the twin's surface `recover`/`do()` should be validated against — and its **per-round angle accumulation `θ*=Σ_j θ_L^j`** with **inhomogeneous (per-qubit) coherent errors** is the surface analogue of the twin's **multi-round, per-location** parity-backend forward (where coherent signal accumulates across rounds, the very effect the rep-code teacher exhibits).
4. **"Twirl underestimates `P^L`; coherence washes out but rate > twirl" — surface Pauli-shadowing, confirmed twice.** Reinforces Bravyi's finding (the moment-matched/twirled baseline misses coherent logical error) and locates the coherent signal in the **finite-`d`, sub-threshold** regime — where the twin operates.

## How to use / trust + open questions
- **Trust:** high as the *coherent+readout extension* and the *primary-metric definition*; carry W1 (single-axis/phenomenological) and W2 (borrowed Pauli scaling) as caveats.
- **Open questions for the project:** (i) Compute **maximum infidelity `p_L^i` (Eq. 15) as the surface primary metric** for any twin coherent claim (closing the "Márton primary not yet computed" gap), with `P^L` (diamond, Eq. 14) secondary and the pure-rotation caveat. (ii) Use the **3D spacelike/timelike readout model** as the template when the twin's harden step adds measurement noise. (iii) Validate the twin's multi-round coherent accumulation against the FLO `θ*=Σ_jθ_L^j` (per-round, per-qubit) — a direct cross-check of the parity-backend forward at the surface level. (iv) Reproduce "coherent more critical than readout" as a `do()`-knob prioritization (which mechanism to fix first).
