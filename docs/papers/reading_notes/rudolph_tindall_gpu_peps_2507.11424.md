# Reading note (精读): Rudolph & Tindall, "Simulating and Sampling from Quantum Circuits with 2D Tensor Networks" (arXiv:2507.11424)

> **Provenance (2026-07-09): FULL-TEXT read (精读).** PDF → txt `outputs/papers/pepo_survey/2507.11424.txt`
> (13 pages + 3 appendix pages, 1396 lines). All §/Eq/Fig refs from that text. Figures not
> pixel-extracted — figure facts = captions + numbers stated in text.
>
> **Focus question:** Does this paper's GPU boundary-MPS contraction + sampling algorithm
> provide a blueprint for sampling from PEPO density matrices on a 2D lattice? Specifically,
> can their generalized tensor network contraction / sampling approach be adapted to our
> PEPO density matrix (mixed-state) sampling for QEC syndrome extraction?
>
> **Second full-text verification pass (2026-07-09, pre-engine-build):** re-read the original
> end-to-end. All load-bearing claims confirmed (ε_i Eq. 1 / f Eq. 2; BP error Eq. 3–4 with
> O(Nχ⁶) full / O(Nχ^{z+1}k) Krylov cost; sampling costs O(Nχ⁵R³)+O(nNχ⁴R³) at z=4; reverse-pass
> norm cache; p/q = unbiased norm estimator Eq. 5; KLD Eq. 6; importance sampling Eq. 9; LUCJ
> f=0.996/0.999 @χ=1000, R=1 exact for 4Fe-4S, R=5/KLD<1e-3 for N2; Willow R~75 @L=15/χ=20;
> >35× GPU). **PRECISION CORRECTION:** this note previously said "All calculations use 32-bit
> floating point precision" globally — the fp32 statement is the **Fig. 5 WALLTIME-BENCHMARK
> caption only** (the >35× GPU timing numbers); the wavefunction memory quotes (96 MB @χ=50
> heavy-hex; 8 GB @χ~300; 13 GB @χ~50 Willow) are explicitly "double precision complex numbers
> in each tensor" (main text). Two implementation details ADDED: (i) gate application = gauge the
> two-site region with the SQUARE ROOT of the incoming BP message tensors, apply the gate, SVD,
> then un-gauge with the inverse square roots (appendix, Fig. 8d); (ii) p(x) is obtained EITHER
> as the square of the final MPS-MPS contraction when R_x is large enough, OR by an independent
> separate contraction of ⟨x|ψ⟩ (main text uses boundary dimension 2χ for this verification) —
> the separate-verification route scales better than raising R_x inside the sampler.

## Metadata [paper]
- **Authors:** Manuel S. Rudolph (EPFL; Flatiron pre-doc; 2024 Google PhD Fellow) and Joseph Tindall (Flatiron Institute, Center for Computational Quantum Physics)
- **Venue / status:** arXiv:2507.11424v2 [quant-ph], 14 Sep 2025 (v1 posted Jul 2025). Preprint, not yet journal-published.
- **Type:** Algorithm + numerical simulation (2D tensor network circuit simulation and sampling; GPU-accelerated boundary MPS contraction).
- **Code:** Open source Julia code: [TensorNetworkQuantumSimulator.jl](https://github.com/JoeyT1994/TensorNetworkQuantumSimulator) (built on ITensors.jl / ITensorNetworks.jl).

## Executive summary [paper]
The paper demonstrates **controllable, systematically improvable simulation and sampling** from quantum circuits using **2D tensor network ansatze** that match processor geometry. Two core algorithmic innovations:

1. **Generalized boundary MPS contraction** (§II-B): extends the standard boundary-MPS method from open-boundary square lattices to **any planar tensor network** (heavy-hex, rotated square, etc.) by partitioning tensors into columns (or rows) and passing MPS of bond dimension R through sequential MPS-MPO fittings. The fitting uses a **one-site variational procedure** that scales more favorably with bond dimension than density-matrix or SVD-based alternatives [28, 29].

2. **Generalized TNS sampling** (§II-C, Appendix): extends the Vieijra et al. [31] PEPS sampling procedure to **arbitrary planar topologies**. The norm network `<psi|psi>` is pre-contracted (once) via reverse-order MPS-MPO fitting, then each sample is drawn by sequentially sampling partitions left-to-right, fitting MPS of dimension Rx between each partition.

GPU speedups of **>35x** (RTX A6000 vs Intel Xeon Gold CPU) are demonstrated for both direct contraction and per-sample generation (Fig. 5). Applications:

- **LUCJ circuits** (IBM heavy-hex, 52/72 qubits): simulated to **numerical precision**; the 72-qubit 4Fe-4S circuit showed zero loop correlations — R=1 (i.e., belief propagation) sufficed for exact-quality samples.
- **Heisenberg domain-wall quench** (164-qubit heavy-hex vs 105-qubit Willow/rotated-square): **dramatic geometric effect** — heavy-hex loop correlations negligible even at L=20 layers (R=1 suffices for local observables), while Willow requires R~75 at L=15 because loop correlations build up rapidly.
- **BP error metric** (Eq. 3-4): a first-order loop-correlation diagnostic from the eigenvalue spectrum of transfer matrices around primitive loops, quantifying when BP alone is insufficient and larger R is needed.

**Central finding for the field:** processor geometry is decisive for classical simulability. Heavy-hex (IBM) has tree-like topology with large (12-site) primitive loops → loop correlations grow extremely slowly → BP/R=1 is nearly exact. Rotated square (Willow/Google) has small 4-site plaquettes → loop correlations grow rapidly → large boundary MPS bond dimensions are required.

## Method (deep) [paper]

### Tensor network ansatz (geometry-matched PEPS)

A PEPS (projected entangled pair state) with one tensor per qubit whose virtual bond network mirrors the device topology. Memory: `O(N_qubits * chi^z)` where `z` = coordination number (`z=3` heavy-hex, `z=4` Willow/square).

**Gate application (§II-A, Fig. 8):** Two-qubit gates are applied via the **belief propagation (BP) simple update** in the Vidal gauge [22]. The environment of the two sites being gated is approximated by a factorizable outer product of BP message tensors. SVD truncates back to bond dim `chi`. The approximate gate error `epsilon_i = sum_{j=chi+1}^{chi'} sigma_j^2` (the discarded singular value weight) is a reliable accuracy metric even in the presence of loops.

**Message update strategy:** BP is re-run between **layers of non-overlapping gates** (Trotter layers). For structured dynamics (Heisenberg evolution by edge coloring), this naturally aligns with the Trotter decomposition. Number of BP updates is independent of system size → overall time complexity `O(N_qubits * chi^{z+1} * L)` for `L` Trotter steps.

### Generalized boundary MPS contraction (§II-B, Fig. 7)

**Core idea:** Partition the planar tensor network into `Nb` column partitions (or any linear ordering). Contract the network by passing an MPS of bond dim `R` through sequential MPS-MPO fittings:

1. **Reverse pass (pre-computation, once per R):** For each partition b = Nb, Nb-1, ..., 2, fit the contraction of MPS_{b+1->b} with partition T_b to a new MPS M_{b->b-1} of bond dim Rn. This yields a set of MPS {M_{Nb->Nb-1}, ..., M_{3->2}, M_{2->1}} representing partial contractions of the norm network `<psi|psi>`.

2. **Forward pass (sampling, per sample):** Starting from partition b=1:
   - Sample all qubits within partition 1 conditioned on incident MPS M_{2->1} (forming 1-site reduced density matrices sequentially)
   - Fit the resulting X_1 = x_1 * psi_1 to an MPS m_{1->2} of bond dim Rx
   - Continue through partitions b=2, ..., Nb
   - Yields a full bitstring x drawn from distribution `q(x)` defined by (Rn, Rx)

**Cost scaling for z=4 (Willow/square):**
- Pre-computation: `O(N_qubits * chi^5 * R^3)` (partitioning by columns/rows)
- Per sample: `O(N_qubits * chi^4 * R^3)`

**Cost scaling for z=3 (heavy-hex):**
- Pre-computation: `O(N_qubits * chi^4 * R^3)` (partitioning by columns/rows)
- Per sample: `O(N_qubits * chi^3 * R^3)`

The one-site fitting procedure (replacing a single MPS tensor per step via derivative of the MPS-MPO-MPS overlap) is the key to favorable scaling.

### Sampling quality metrics (§II-C)

Three metrics:

1. **Fidelity per gate** `f_i = 1 - epsilon_i` → overall state fidelity `f = prod_i f_i ≈ |<psi_m| prod_i G_i |psi_0>|^2` (Eq. 2). This is an approximation but empirically reliable [2, 14].

2. **p(x)/q(x) ratio** (Eq. 5): For each sample, compute the ratio of the true probability `p(x) = |<x|psi>|^2` to the sampled probability `q(x)`. The mean ratio is an unbiased estimator of the norm `<psi|psi>`. Ratios near 1 indicate high-quality samples.

3. **Sample Kullback-Leibler divergence** `KLD(q,p) = E_{x~q}[log(q(x)/p(x))]` (Eq. 6): The average log-ratio over all samples. KLD=0 means identical distributions; values significantly below 1 typically indicate high-quality samples.

**Importance sampling correction (Eq. 9):** When sample quality is imperfect, observables can be corrected via:
`<psi|O|psi> ≈ (1/N) sum_i (p(x_i)/q(x_i)) <x_i|O|x_i>`
with `N = (1/n) sum_i p(x_i)/q(x_i)`.

### BP error metric (§II-B, Figs. 6, 9)

Per-loop BP error: `epsilon_l = 1 - |lambda^l_1| / sum_i |lambda^l_i|` where `lambda^l_i` are eigenvalues of the transfer matrix formed by inserting BP messages on the boundary of primitive loop `l` and cutting one edge. Values `0 <= epsilon <= 1-1/chi^2`. The average `epsilon` quantifies "loop correlations" — when `epsilon` is large, BP (R=1) is insufficient and larger boundary MPS dimensions R are needed.

This metric is computable in `O(N_qubits * chi^6)` (full spectrum) or `O(N_qubits * chi^{z+1} * k)` (Krylov for top-k eigenvalues).

### GPU implementation (§III, Fig. 5)

The boundary MPS approach is dominated by **tensor contractions and QR decompositions** — operations that benefit maximally from GPU hardware. The paper reports **>35x speedup** on Nvidia RTX A6000 vs Intel Xeon Gold (6244) CPU for both norm-network contraction and per-sample generation. **Precision (corrected 2026-07-09): the Fig. 5 walltime benchmarks are in 32-bit floating point (its caption); the wavefunction storage figures quoted in the main text are double-precision complex.** The fp32 GPU timing numbers therefore do NOT transfer as-is to a complex128 engine.

The GPU speedup enables:
- Contracting a 105-qubit Willow PEPS (chi=20) with R=75 in tractable walltime (Fig. 5)
- Generating samples in under one second per sample for heavy-hex LUCJ circuits (Fig. 2)
- Scaling to chi=300 (8GB RAM) for heavy-hex and chi=50 (13GB RAM) for Willow (quoted memory costs for double-precision complex)

## Results [paper]

### LUCJ circuits (Fig. 1, 2)

| System | Qubits | chi | State fidelity f | Sampling quality |
|--------|--------|-----|-----------------|-----------------|
| N2 molecule (IBM heavy-hex) | 52 | 600 | 0.95 | KLD < 1e-3 at R=5 |
| 4Fe-4S molecule (IBM heavy-hex) | 72 | 600 | 1.00 | KLD < 1e-8 even at R=1 |

- Mean CNOT gate fidelities of **99.9998%** and **99.99999%** (vs 99.8% reported in Ref. [12]) — effectively simulating the circuit without transpilation overhead
- The 4Fe-4S circuit exhibited **zero loop correlations** despite high depth: the inter-sub-register CP gates are few, effectively making the system two weakly coupled MPS
- Sampling time: **far below one second per sample on a single GPU** (Fig. 2 annotations)

### Heisenberg domain-wall quench (Fig. 3, 4, 6)

| Geometry | Qubits | L (layers) | chi | Memory | Loop correlations |
|----------|--------|------------|-----|--------|-----------------|
| Heavy-hex (IBM) | 164 | 20 | 50 (f>99%) | 96 MB (cp128) | Negligible — R=1 converges local obs |
| Heavy-hex max | 164 | 20 | 300 | 8 GB | — |
| Willow (Google) | 105 | 15 | 20 (f>86%) | 247 MB (cp128) | Strong — needs R~75 for convergence |
| Willow max | 105 | 15 | 50 | 13 GB | — |

Key results:
- **Heavy-hex**: Local Z expectation values converged at R=1 (immediate). Sample KLD < 1 at modest R. >96% correct magnetization even at R=3 (Fig. 3 inset). Loop correlations negligible even at L=20 (Fig. 6: epsilon < 1e-10).
- **Willow**: Local Z at L=15 requires R~75 for convergence. At L=7, R ~ chi = 20 sufficed. BP error epsilon jumps 8+ orders of magnitude above heavy-hex by L=6 (Fig. 6). At R=1, sample probabilities can be off by dozens of orders of magnitude (Fig. 3 bottom). At R=20, probability ratios within ~1 order of magnitude.
- **GPU speedup** >35x for both contraction and sampling at large R (Fig. 5).

### Loop correlations — geometric effect (Fig. 6)

The BP error metric shows a **drastic difference** between heavy-hex and Willow:
- Heavy-hex: epsilon remains < 10^{-9} even at L=20 (after accounting for Trotter artifacts)
- Willow: epsilon > 10^{-1} at L=10, indicating strong loop correlations
- This exceeds the naive expectation epsilon(heavy-hex) ~ epsilon(Willow)^3 based on loop size ratio (12 vs 4 sites)
- The authors hypothesize "loop interference" in large lattices compounding with increased loop sizes

## Relevance to twin [ours]
**Dimension: Can their GPU boundary-MPS sampling be adapted for PEPO density matrix sampling?**

This paper is directly relevant because it demonstrates a **generalized boundary MPS contraction that works on any planar tensor network** — and a PEPO (projected entangled pair operator) representing a mixed state `rho` on a 2D lattice IS a planar tensor network (with an extra physical index contraction). The key question is how the method maps to density-matrix vs state-vector sampling.

### What maps directly (the yes column)

1. **Generalized planar boundary MPS (§II-B) works for PEPO.** The method contracts any planar tensor network by partitioning columns and passing MPS through MPS-MPO fitting. A PEPO is just another planar tensor network — the physical bra and ket indices are contracted (or left open for operators). The same MPS-MPO fitting procedure applies. **No structural change needed** to contract a PEPO norm network `Tr(rho^† rho)` or `Tr(rho * O)`.

2. **GPU acceleration transfers (§III, Fig. 5).** The method's dominance by tensor contractions and QR decompositions means GPU speedups of >35x for our PEPO contractions too. The paper uses RTX A6000 (our RTX 5090 is faster). The 32-bit precision used throughout is sufficient and faster than complex128.

3. **Sampling with fidelity metrics (§II-C) maps to our Born-rule sampling.** The p(x)/q(x) ratio and sample KLD are representation-independent metrics. For a PEPO density matrix `rho`, `p(x) = <x|rho|x>` (the Born-rule probability) — the same as their `|<x|psi>|^2` but with `rho` replacing `|psi><psi|`. The sequential partition sampling (Fig. 7d) generalizes: each partition's reduced density matrix is formed by contracting the PEPO projection onto sampled outcomes, then sampled. The same MPS-MPO fitting handles the MPO-to-MPS contraction.

4. **BP error metric (Eq. 3-4) is a loop-correlation diagnostic for our PEPO.** Before investing in high-R contraction, we can compute epsilon_l per primitive loop of our PEPO to determine whether BP (R=1) is sufficient. For heavy-hex-derived QEC lattices, large loops likely mean weak loop correlations.

5. **Heavy-hex = our geometry.** Our surface code on rotated/square lattice has z=4 (Willow-like), not z=3 (heavy-hex). But many QEC devices (IBM, some Google generations) use heavy-hex or near-heavy-hex connectivity where the method works extremely well.

6. **Importance sampling correction (Eq. 9)** is directly applicable: use lower-cost boundary MPS for sampling, then correct observables with p(x)/q(x) weights computed from a higher-cost accurate contraction.

### What needs adaptation (the non-trivial part)

1. **PEPO has a doubled local space.** For a density matrix `rho` on `N` qubits with local dimension `d=2`, the PEPO has local tensors of shape `(d, d, D, D, D, D)` (bra, ket, + 4 bond indices) or fused `(d^2, D, D, D, D)` = `(4, D, D, D, D)`. The "physical index" is `d^2=4` — this is manageable but doubles the tensor ranks vs PEPS (`(d, D, D, D, D)` = `(2, D, D, D, D)`). The MPS-MPO fitting and per-partition sampling would need to handle the fused bra+ket dimension.

2. **Sampling from a PEPO is NOT the same as sampling from a PEPS.** The paper samples from `p(x) = |<x|psi>|^2` for a pure state. For a PEPO density matrix, `p(x) = <x|rho|x>` — this requires contracting the PEPO with the projection operator `|x><x|` not just `|x>`. In the partitioned sampling of Fig. 7d:
   - Step: "form 1-site reduced density matrix conditioned on incident MPS" generalizes to: form `rho_{1-site} = Tr_{env}(rho)` where `Tr_env` is the partial contraction of the PEPO environment at that site. This IS a boundary MPS contraction of a single-layer (PEPO, not doubled) network.
   - The "wavefunction" partition `psi_b` becomes the "density matrix partition" `rho_b` (or its vectorized form).
   - The two-layer norm network `<psi|psi>` becomes `rho_bra * rho_ket` (a 4-layer contraction) OR, more efficiently, the vectorized norm network `|rho>>` — this doubles the effective depth of the network to contract.

3. **Mid-circuit measurements (syndrome extraction) are not in this paper.** The paper assumes terminal measurements at circuit end. For QEC syndrome extraction, each round involves mid-circuit measurements that collapse the state. The boundary MPS sampling procedure would need to handle partial collapse and re-preparation of ancilla qubits between rounds.

4. **Non-unitary (noise) channels are not discussed.** The paper applies the circuit as a sequence of unitary gates. A PEPO representing noisy evolution includes non-unitary (Kraus) operators. The gate application step (§II-A, Fig. 8) uses SVD truncation conditioned on BP messages — this extends naturally to Kraus operators (just another tensor contraction followed by truncation), but the paper doesn't address this.

5. **The PEPO bond dimension for noise is the challenge.** For a noisy surface code with `d=5` (49 qubits), the PEPO bond dimension required for accurate noise representation could be large — especially for non-Pauli / coherent noise. The paper's chi=20-50 for noiseless Heisenberg dynamics is optimistic for noisy QEC states where entanglement structures are different.

### Concrete mapping for our use case

If we build a PEPO density matrix `rho` representing the noisy surface code state after `t` rounds of syndrome extraction on a 2D lattice:

```
rho — planar PEPO on N_qubits × (d^2, D, D, D, D) tensors
    → Partition by columns (or rows matching syndrome extraction order)
    → Pre-compute norm network Tr(rho^† rho) via boundary MPS (reverse pass, dim Rn)
    → For each sample:
        1. Sequential partition sampling: for partition b=1..Nb:
             - Contract PEPO projection onto site outcomes within partition
             - Fit to MPS m_{b->b+1} of dim Rx
        2. Compute true probability p(x) = <x|rho|x> via separate, higher-accuracy
           boundary MPS contraction
        3. Compute q(x) from sampling procedure MPS (product of conditional 1-site probs)
        4. p(x)/q(x) ratio → sample quality metric
```

The GPU speedups shown in Fig. 5 directly apply to steps 1-3 (all are tensor contractions + QR). The main new cost vs PEPS: each partition's reduced density matrix involves a 4-index tensor (bra, ket, left-MPS-bond, right-MPS-bond) rather than the 3-index PEPS case — about 2x the contraction cost per step.

### Specific numbers from the paper relevant to our problem

| Paper parameter | Value | Our analog | Implications |
|---|---|---|---|
| Willow chi=20, R=75, L=15 | ~35x GPU speedup, tractable on RTX A6000 | Surface code d=5 (49q), comparable N_qubits | Feasible on our RTX 5090 |
| Heavy-hex chi=300, 8 GB cp128 | Simulation to high fidelity | Larger chi may be needed for non-Pauli noise | Memory OK within 65 GB ceiling |
| Sample time per sample (heavy-hex LUCJ) | <1 sec on GPU | Per syndrome round sampling | Single-GPU serial not a bottleneck for O(10^4) samples |
| KLD at R=1 vs R=20, Willow L=15 | R=1: ratios off by 10+ orders; R=20: within 1 order | Importance sampling (Eq. 9) needed for low-R | Use p(x)/q(x) weighting to reduce required R |
| BP error epsilon, heavy-hex L=20 | <1e-9 | For heavy-hex QEC chips, BP may suffice | For square/rotated lattice, expect Willow-like behavior |

### What the paper does NOT tell us (key gaps for our adaptation)

1. **No density-matrix sampling demonstrated.** The paper samples pure-state PSI — not mixed-state RHO. The generalization is structurally straightforward (replace |psi> with the PEPO rho, adjust dimension labels) but the paper doesn't validate it. We need to implement and test the PEPO variant.

2. **No mid-circuit measurements.** The sampling algorithm assumes terminal measurement. QEC syndrome extraction requires mid-circuit measurement + ancilla reset. Extending the boundary MPS sampling to handle mid-circuit collapse requires conditioning subsequent partitions on measurement outcomes from earlier rounds — the existing left-to-right partition scan handles one direction; multiple rounds add a 2nd (temporal) dimension.

3. **No noisy circuit results.** All demonstrations are on noiseless unitary circuits. The PEPO for a noisy surface code is intrinsically mixed-state. The bond dimension growth during circuit simulation for noisy dynamics may differ from the unitary case both qualitatively and quantitatively.

4. **No error mitigation for the EP convergence.** The fidelity metric `f = prod f_i` (Eq. 2) is an approximation whose quality degrades in the presence of loops. For our PEPO, we would need an independent certification — e.g., comparing small-system (d=3) PEPO sampling against exact DM simulation.

5. **Julia-only code.** The implementation is in Julia (ITensors.jl / ITensorNetworks.jl). We would need to either (a) port the generalized boundary MPS to Python/quimb/torch, (b) write a Julia bridge, or (c) use the code as a reference implementation and build our own Python version.

## Limitations [paper]
- **Pure-state only.** All methods and demonstrations are for pure-state PEPS. Mixed-state PEPO generalization is not discussed.
- **Terminal measurements only.** The sampling algorithm assumes measurement at circuit end — no mid-circuit measurements on subsets of qubits.
- **Noiseless circuits only.** All demonstrations are on unitary quantum circuits. Noisy (open-system) evolution is not shown or discussed.
- **First-order BP gate approximation.** Gate application uses BP message tensors which are exact only for loop-free networks. In the presence of loops (Willow), the gate fidelity metric `f_i` is an approximation.
- **Fidelity metric approximation.** Eq. (2)'s `f = prod f_i` as an estimate of overall state fidelity is "empirically reliable" but is NOT a certified error bound — it degrades with loop strength.
- **Julia/ITensor-specific code.** No Python, PyTorch, or JAX implementation for direct integration with machine learning frameworks.
- **No pathological-state analysis.** The paper notes (Ref. [36]) that some PEPS require exponential R for perfect sampling, but claims local Hamiltonian dynamics avoid this regime.
- **32-bit precision.** All GPU calculations are in float32 (complex64). The resulting truncation noise at 32-bit may limit ultimate precision for some applications.
- **System sizes moderate.** The largest demonstration is 164 qubits (heavy-hex) — well below QEC-relevant scales (d=7 surface code = 97 qubits, d=11 = 241 qubits). Scaling analysis of the boundary MPS method to 200+ qubits with moderate chi is not characterized.
- **R <= chi assumption in cost analysis.** The complexity scaling expressions assume R <= chi, which may not hold when strong loop correlations demand R >> chi.

## Tags
- `[paper]` Generalized boundary MPS contraction: works on ANY planar tensor network (heavy-hex, rotated square, arbitrary)
- `[paper]` BP simple-update gate application: O(N_qubits * chi^{z+1} * L) with Trotter-layer message updates
- `[paper]` GPU speedup >35x on RTX A6000 vs Intel Xeon Gold CPU (tensor contractions + QR dominated)
- `[paper]` Sampling via partitioned boundary MPS: pre-compute norm (reverse pass), then sequential partition sampling (forward pass, per sample)
- `[paper]` Heavy-hex (IBM): loop correlations negligible even at L=20, R=1 suffices for local observables
- `[paper]` Willow/rotated-square (Google): strong loop correlations at L=15, needs R~75 for convergence
- `[paper]` p(x)/q(x) ratio + sample KLD + BP error metric = three quality diagnostics
- `[paper]` Importance sampling correction (Eq. 9): correct observables with p(x)/q(x) weights
- `[paper]` BP error metric epsilon_l (Eq. 3-4): per-loop loop-correlation diagnostic from transfer-matrix eigenvalues
- `[paper]` "Loop interference" hypothesis: heavy-hex epsilon < Willow^3 beyond naive loop-size scaling
- `[paper]` Cost: z=4: O(N_qubits*chi^5*R^3) pre + O(n*N*chi^4*R^3) sample; z=3: O(N*chi^4*R^3) pre + O(n*N*chi^3*R^3) sample
- `[paper]` Open-source Julia code: TensorNetworkQuantumSimulator.jl (ITensors.jl backend)
- `[paper]` 32-bit float GPU precision sufficient for all benchmarks
- `[ours]` **YES — the generalized boundary MPS contraction maps directly to PEPO density matrix contraction** on any planar 2D lattice
- `[ours]` Sampling from `p(x) = <x|rho|x>` for a PEPO generalizes their `|<x|psi>|^2` sampling: same partition structure, same MPS-MPO fitting, same quality metrics
- `[ours]` **BUT three gaps**: (1) no mixed-state / PEPO demonstration in the paper, (2) no mid-circuit measurement handling (needed for QEC syndrome extraction), (3) no noisy circuit benchmarks
- `[ours]` Their heavy-hex vs Willow geometric finding has direct QEC implications: heavy-hex surface codes are classically simulatable to much larger depths than square-lattice codes
- `[ours]` GPU speedup >35x means our RTX 5090 can likely contract PEPO norm networks for d=5 (49q) in seconds, not hours
- `[ours]` BP error metric (Eq. 3-4) is a pre-investment diagnostic: compute epsilon on our PEPO before deciding to build full boundary MPS infrastructure
- `[ours]` The 4Fe-4S result (R=1 exact sampling) is a cautionary data point: "low loop correlations" can mean a problem is trivially simulable — not yet QEC-relevant. We must benchmark our PEPO on QEC-relevant noise to know if it's in the heavy-hex regime or the Willow regime.
