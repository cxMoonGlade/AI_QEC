# Deep review — Bravyi, Englbrecht, König & Peard, Correcting Coherent Errors with Surface Codes

> Deep reading note (academic-paper-review format; full read Secs. I–III + the
> storage/prep results and thresholds; the Majorana/FLO encoding (C4-code, link
> operators, Lemmas 1–3) and Algorithms A/B read in detail). **Relevance to the
> twin** centerpiece.

## Metadata
- **Authors.** Sergey Bravyi, Matthias Englbrecht, Robert König, Nolan Peard (IBM T.J. Watson; TU Munich; MIT).
- **Venue / status.** npj Quantum Information 4, 55 (2018); arXiv:1710.02270.
- **Domain / type.** QEC / fault tolerance; **theoretical + simulation** (exact classical simulation algorithms).

## Executive summary
The paper gives **`O(n²)` exact classical algorithms** to simulate the distance-`d` surface code under **coherent** noise, by encoding each qubit into **4 Majorana modes** (a "C4-code") so the protocol becomes a **fermionic-linear-optics (FLO)** circuit — exactly simulable for **single-axis `Z`-rotation coherent + Pauli** noise to `n=2401` qubits (`d=49`) in seconds. Under translation-invariant storage noise `(e^{iθZ})^{⊗n}`, the syndrome distribution `p(s)` is **independent of the logical state**, and the post-correction logical channel is a **per-syndrome coherent rotation** `ρ↦e^{iθ_s Z_L}ρe^{-iθ_s Z_L}`. The logical error rate is
> **`P^L = 2Σ_s p(s)|sin θ_s|`** — the **average diamond-norm distance** between the conditional logical channel and the identity (Eq. 4).

Main findings: a **threshold `θ_0∈[0.08π,0.1π]`** (storage; `P^L` decays exponentially in `d` below it); the threshold **agrees** with the Pauli-twirl (dephasing `ε=sin²θ`, `ε_0≈0.11`), **but the Pauli twirl significantly *underestimates* `P^L` sub-threshold**; and at large `d` the per-syndrome angles **concentrate at `{0, π/2}`** (logical `{I, Z_L}`) — coherent physical noise is **converted to incoherent logical noise**, but with rate *exceeding* the twirl.

For the twin this is the **computational substrate and the field-standard metric for the surface-code port**: the FLO simulator is the **certified, scalable, exact coherent teacher** (beyond the ~15-qubit density-matrix ceiling); `P^L` (avg diamond-norm) is the **standard logical-coherence metric** the project's metric rule names ("Bravyi `P_L`"); and "twirl underestimates `P^L`" is the **surface-code statement of Pauli-shadowing** the twin must reproduce.

## Contributions (claim → evidence → strength)
- **C1. `O(n²)` exact coherent surface-code simulation via Majorana/FLO (Secs. II–V).** *Evidence:* C4-code encoding (Eq. 7–8), `B_f=∏_{e∈∂f}L_e` (Lemma 1), FLO gate set + complexity; Table I (`d=49`, seconds). *Strength: strong — the enabling technical result.*
- **C2. `P^L`= average diamond-norm distance, exact for pure rotations (Eq. 3–4).** Per-syndrome logical rotation `θ_s`; `P^L=2Σ_s p(s)|sin θ_s|`. *Strength: strong (the right, computable metric).* 
- **C3. Thresholds + twirl-underestimate (Eq. 5–6).** Storage `θ_0∈[0.08π,0.1π]`; prep `θ_0(φ)∈[0.1π,0.15π]`; twirl matches the *threshold* but underestimates sub-threshold `P^L`. *Strength: strong.*
- **C4. Coherence-to-incoherence conversion at large `d`.** `θ_s` concentrates at `{0,π/2}` → effective logical Pauli noise as `d→∞`, rate > twirl. *Strength: strong (the washout, with the right caveat).* 

## Method (deep)
- **C4-code.** 4 Majorana modes `c_1..c_4` per qubit, stabilizer `S=−c_1c_2c_3c_4`; logical `X̄=ic_1c_2`, `Z̄=ic_2c_3` (Eq. 7–8). Surface code on a planar graph `G=(V,E,F)`, `4n` modes; **link operators** `L_e=ic_p c_q` (Eq. 9) Hermitian, pairwise commuting.
- **Syndrome = product of links.** `B̄_f=∏_{e∈∂f}L_e` (Lemma 1, Fig. 4); measuring the syndrome reduces to measuring commuting link operators — a **Gaussian/FLO** operation. Logical ops `X̄_L,Z̄_L` are link products on the boundary (Eq. 12, Lemma 2).
- **FLO simulability.** Gates: init pairs, rotation `exp(γc_pc_q)`, projector `(I+ic_pc_q)/2`. Runtimes `O(n)` (init/rot), `O(n²)` (projector); exploiting locality → `O(n^{1/2})` active modes → total `O(n²)`. The link state `φ_link` is a fermionic Gaussian state; coherent `Z`-error preserves Gaussianity → simulable.
- **Algorithms.** A (storage): sample `p(s)`, compute `θ_s`, `P^L`. B (logical prep): syndrome projector `Π_s=∏_f ½(I+s_f B_f)` (Eq. 15), `p(s)=⟨ψ|Π_s|ψ⟩`, final `|φ_s⟩=C_sΠ_s|ψ⟩/√p(s)` (Eq. 18); Pauli correction `C_s` via constant-weight MWPM.

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | Exact FLO simulation with proven lemmas; `P^L` rigorously a diamond-norm distance for pure rotations. |
| Novelty | **5** | First large-scale exact coherent surface-code simulation; the Majorana/FLO algorithm is the enabling, widely-reused tool. |
| Reproducibility | **5** | Algorithms + complexity + runtime table; self-contained encoding. |
| Experimental design | **4** | Storage + prep, multiple distances, twirl comparison; single-axis coherent only (the FLO constraint). |
| Statistical rigor | **4** | Threshold estimates with ranges; exponential-decay diagnostics; finite-`d` extrapolation. |
| Scalability | **5** | `O(n²)` to `d=49` on a laptop — the headline. |

## Strengths
- **S1 — exact + scalable coherent simulation (the FLO trick).** Encoding into Majorana modes to make coherent surface-code QEC a Gaussian-fermionic (hence classically exact) computation is the decisive contribution — it is *the* way to have a certified large-`d` coherent teacher.
- **S2 — the right metric (`P^L`= avg diamond-norm, Eq. 4).** Defining the logical error rate as a *diamond-norm distance* (worst-case channel distinguishability) — not a fidelity that hides coherence — is exactly correct for coherent errors and is the field standard.
- **S3 — the twirl-underestimate finding (sub-threshold).** Showing the threshold matches the twirl but the sub-threshold `P^L` does **not** is the precise, honest statement of why coherence matters where it counts (the operating regime).

## Weaknesses / limitations
- **W1 — single-axis (`Z`-rotation) + Pauli only.** FLO/Gaussianity requires Clifford + single-axis coherent; general coherent (multi-axis, coherent gates) breaks it. The teacher is exact only on this slice.
- **W2 — `P^L`'s diamond-norm identity is exact only for *pure rotations*.** Once stochastic/non-unitary noise mixes in, `P^L=2Σp|sinθ|` is a proxy, not exactly the diamond norm — a caveat the twin's metric rule must carry.
- **W3 — translation-invariant, idealized.** Storage noise is uniform `(e^{iθZ})^{⊗n}`; no circuit-level/measurement noise (added by Márton–Asbóth 2303.04672).

## Relevance to the twin
This is the **substrate, the metric, and the Pauli-shadowing confirmation for the twin's surface-code port (HARDEN)**:
1. **The certified scalable coherent teacher.** The twin's exact density-matrix / parity backend dies past ~15 qubits; the **Majorana/FLO simulator is how the twin gets a *certified, exact, large-`d`* coherent surface-code teacher** to validate `recover`/`do()` against — the surface analogue of the rep-code controlled teacher. The memory's "Bravyi gate / Bravyi `P_L`" lineage is this. Constraint (W1): only single-axis `Z`-rotation + Pauli — so the surface coherent teacher must be that slice (consistent with staying exact-but-structured).
2. **`P^L`= avg diamond-norm IS the twin's surface coherence metric (the standard-metric rule).** The project's hard metric rule flags `surface_logical_coherence = Bravyi P_L` (avg per-syndrome diamond distance, *exact only for pure rotations*) — *this paper is its definition*. Any twin surface claim must be filed against `P^L` (Eq. 4), with the W2 caveat carried (it is exact only for pure rotations; infidelity/diamond-norm distinctions matter once stochastic noise enters).
3. **"Twirl underestimates `P^L` sub-threshold" = surface Pauli-shadowing.** The surface-code version of the rep-code "moment-matched twin underestimates the coherent knob." The twin must reproduce this: its coherent surface `recover` should expose the `P^L` the Pauli-twirled (moment-matched) baseline misses — the surface-code falsification of moment-matching.
4. **The washout sets where the coherent signal lives.** `θ_s→{0,π/2}` at large `d` means the *single-shot logical channel looks Pauli* asymptotically; the coherent advantage is in the **finite-`d`, per-syndrome, sub-threshold** regime — exactly where a *small-distance exact twin* should operate, and a caution against claiming coherent recovery from large-`d` logical statistics alone.
5. **Per-syndrome `θ_s` ↔ a do()-relevant logical quantity.** The conditional logical rotation `θ_s` is the surface analogue of the twin's per-context coherent signature; `P^L` averaging `|sin θ_s|` over syndromes is the decoder-relevant aggregate the twin's `manipulate`/`predict` axes target.

## How to use / trust + open questions
- **Trust:** very high as the *exact coherent surface-code teacher* and the *definition of the surface coherence metric*; carry W1 (single-axis) and W2 (pure-rotation-only diamond-norm) as hard caveats.
- **Open questions for the project:** (i) Stand up the **FLO simulator as the surface coherent teacher** and validate the twin's `recover`/`do()` against its exact `P^L` (the surface analogue of the rep-code teacher validation). (ii) Reproduce the **twirl-underestimate of `P^L`** with the twin's moment-matched control on the surface — the surface Pauli-shadowing falsifier. (iii) Pin the **metric convention**: `P^L` is exact-diamond only for pure rotations; once readout/stochastic noise enters (Márton–Asbóth), state whether the twin reports `P^L`, true diamond norm, or infidelity (the standard-metric ladder). (iv) Operate the coherent surface claims in the **finite-`d` sub-threshold** regime where the washout has not erased the coherence.
