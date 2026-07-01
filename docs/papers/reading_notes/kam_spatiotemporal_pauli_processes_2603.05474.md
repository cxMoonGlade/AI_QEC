# Full-text review - Kam, Southwell, Gicev, Usman & Modi, "Spatiotemporal Pauli processes: Quantum combs for modelling correlated noise in quantum error correction" (arXiv:2603.05474)

> **Provenance (2026-06-28): FULL-TEXT read (Jingdu).** PDF `outputs/papers/2603.05474.pdf` -> txt
> `outputs/papers/2603.05474.txt` (PyMuPDF, 54 pp). All equation / figure references are from that
> extracted text. Figures not pixel-extracted; figure facts below come from captions and numeric values
> stated in the text. Tags: **[paper]** = stated by the paper; **[ours]** = project application/inference.

## Metadata [paper]
- **Authors.** John F. Kam, Angus Southwell, Spiro Gicev, Muhammad Usman, Kavan Modi.
- **Status.** arXiv:2603.05474 [quant-ph], 2026.
- **Type.** Formal process-tensor / Pauli-twirl framework plus Stim/PyMatching surface-code simulations.

## Executive summary [paper]
The paper defines **spatiotemporal Pauli processes** (SPPs): the multi-time Pauli-twirled image of a
general process tensor. The twirl maps arbitrary multi-time dynamics to a process-separable Pauli comb,
equivalently a joint probability distribution over Pauli trajectories across space and time. It then shows
how SPPs can be represented by tensor networks, transfer operators, and, under positivity/normalisation
conditions, hidden Markov models (HMMs). Two QEC-facing examples are implemented: a two-state temporal
"storm" HMM with fixed single-round marginals and tunable correlation length, and a 2D QCA bath that
twirls to a probabilistic cellular automaton (PCA) with pseudo-critical slowing down and surface-code
distance-scaling breakdown.

## Method (deep) [paper]

### Multi-time Pauli twirl
For a `k`-slot process tensor with Choi operator `Upsilon_0:k`, Definition 4.1 defines the multi-time
Pauli twirl as the CPTP projector

```text
T_P^(k)(Upsilon_0:k)
  = 1 / |P(n)|^(k+1) * sum_{P0,...,Pk in P(n)}
      (tensor_j P_j tensor P_j) Upsilon_0:k (tensor_j P_j tensor P_j).
```

The map twirls each time step's input-output pair independently and preserves causal constraints.

Theorem 4.3 gives the core reduction:

```text
Upsilon_TP_0:k = sum_{P in P(n,k)} Pr(P) Upsilon_P,
Upsilon_P = tensor_{j=0}^k Pi_{P_j},
Pr(P) = w(P) / N,
w(P) = Tr[(tensor_j Pi_{P_j}) Upsilon_0:k] >= 0.
```

Thus the twirled process has no quantum temporal correlations, but can retain arbitrary **classical**
temporal correlations through `Pr(P)`. Definition 4.4 names any process tensor of this form an SPP.
The independent Markovian special case factorizes:

```text
Pr_SPP(P0, ..., Pk) = product_j Pr_j(P_j).
```

The paper stresses that this is an **operational** reduction under Pauli-frame randomisation /
randomised compiling. It does not claim the microscopic dynamics literally become an SPP.

### Transfer-operator diagnostics
For a time-homogeneous SPP MPS with matrices `A_x`, Definition 5.1 defines

```text
T   = sum_x A_x,
E_f = sum_x f(x) A_x.
```

With stationary fixed points `<l1|T=<l1|`, `T|r1>=|r1|`, `<l1|r1>=1`, expectations and two-time
correlations are

```text
E[f(x_t)] = <l1|E_f|r1>,
E[f(x_t) g(x_{t+tau})] = <l1|E_f T^(tau-1) E_g|r1>.
```

The centered emission operator is

```text
Etilde_f = E_f - <f> T,
C_f,g(tau) = <l1|Etilde_f T^(tau-1) Etilde_g|r1>.
```

The multi-point correlator, Eq. 61, is

```text
C_{f1,...,fm}
  = <l1| Etilde_f1 T^Delta_t1 Etilde_f2 T^Delta_t2 ... T^Delta_t{m-1} Etilde_fm |r1>.
```

If `T` is diagonalisable, the subleading eigenvalue `lambda_* = |lambda_2|` gives

```text
Delta = 1 - lambda_*,
xi = -1 / ln(lambda_*).
```

This is the cleanest source-level / reduced-record diagnostic for temporal memory in the SPP layer.

### HMM equivalence
Section 5.4 maps positive, row-normalised SPP MPS tensors to an edge-emitting HMM. An HMM has kernels

```text
(K_x)_ij = Pr(S_{t+1}=j, X_t=x | S_t=i),
(K_x)_ij >= 0,
sum_{x,j} (K_x)_ij = 1 for each i.
```

The sequence probability is

```text
Pr(x_0:k) = sum_{s_0,...,s_{k+1}} pi_{s0} product_t (K_{x_t})_{s_t,s_{t+1}}.
```

If an SPP gauge satisfies `(A_x)_ij >= 0` and `sum_{x,j}(A_x)_ij=1`, then `K_x == A_x`, and
`T_HMM == sum_x K_x == sum_x A_x`.

## The MECHANISM (for implementation) [paper -> ours]

### Temporal storm SPP/HMM
The simplest implementable QEC-facing source is the two-state storm model (§6.2). The latent state
`s in {0,1}` represents calm/storm. It evolves with transition probabilities

```text
a = Gamma_{0->1},
b = Gamma_{1->0},
T = [[1-a, a],
     [b, 1-b]].
```

Given the updated state `s'`, the system receives a Pauli channel

```text
E_{s'}[rho] = sum_x q_{s'}^(x) sigma(x) rho sigma(x).
```

The joint Kraus operators are

```text
K^x_{s',s} = sqrt(Gamma_{s->s'} q_{s'}^(x)) |s'><s|_E tensor sigma_x.
```

The SPP matrices are

```text
A(x) = T diag(q_0^(x), q_1^(x)).
```

The spectrum is exact:

```text
lambda_1 = 1,
lambda_2 = 1 - a - b,
Delta = a + b,
xi = -1 / ln(1-a-b),
pi_0 = b/(a+b),
pi_1 = a/(a+b),
pbar(x) = pi_0 q_0^(x) + pi_1 q_1^(x).
```

The key construction is that `xi` can be swept while holding `pbar(x)` fixed. This is the correct
fixed-marginal Axis-2 negative-control geometry.

### QCA/PCA spatiotemporal source
Section 7 builds a microscopic 2D QCA bath:

```text
M_{a,b,theta} = U_SE o Q^E_{B->R}(theta) o Q^E_{R->B}(theta) o S_E(a,b).
```

The environment storm channel flips `0->1` with probability `a` and `1->0` with probability `b`.
The QCA half-steps are controlled-X rotations on a bipartite lattice, and the local system-environment
unitary is controlled by the environment state:

```text
U_SE^(i) = sum_{k=0}^1 |k><k|_{E_i} tensor V_k^{S_i},
V_0 = I,
V_1 = n_x X + n_y Y + n_z Z,
||n||_2 = 1.
```

After system Pauli twirling, the effective PCA HMM has these update steps:

1. storm update each site independently;
2. update black sites with flip probability `sin^2(k(i) theta)` from excited red neighbours;
3. update red sites analogously;
4. emit `I` if `s_{t+1}(i)=0`; emit `X,Y,Z` with probabilities `n_x^2,n_y^2,n_z^2` if `s_{t+1}(i)=1`.

This is a genuine spatiotemporal stress-test source, but it is heavier than the temporal storm HMM and
should be a later build after the basic SourceProcess API is stable.

## The OBSERVABLE / metric [paper]
- **SPP source diagnostics:** transfer spectral gap `Delta`, correlation length `xi`, latent density
  autocorrelation, multi-point correlators Eq. 61.
- **QEC-facing metrics:** logical failure / logical error rate from surface-code memory or stability
  experiments under Stim sampling and PyMatching decoding with a marginalised independent DEM.
- **Important insufficiency boundary:** single-round marginals are intentionally fixed; any simulator
  validation that only checks marginals cannot see the contribution.

## Findings + numbers [paper]
- Temporal storm simulations use rotated surface-code memory (`N_r=3d`, distances up to `d=19`) and a
  stability primitive (diameter-4 patch). The correlated SPP is applied at the start of each QEC cycle,
  with marginal error rate fixed at `p=0.1%`. Increasing `xi` at fixed marginals degrades logical
  performance and stability.
- QCA/PCA simulations fix `a=1e-4`, `b=0.5`, sweep `theta`, use lattices for distances `d=9,11,13,15`
  for bath statistics, and surface-code memory up to `d=17` with `N_r=3d`.
- The PCA density crossover begins near `theta ~= 0.35*pi`; the pseudo-critical threshold is about
  `theta_th ~= 0.39*pi`; fitted density correlation time reaches about `xi_eta ~= 140` cycles for `d=9`.
- In the pseudo-critical window `theta ~= 0.36*pi - 0.40*pi`, distance scaling breaks down; above
  `theta_th ~= 0.39*pi`, larger codes can perform worse than smaller codes.

## Limitations [paper]
- SPP is a Pauli-twirled / reduced process object. It is appropriate for stabilizer QEC records under
  Pauli-frame randomisation, not a full analog/leakage/coherent joint-L teacher.
- Temporal storm is one latent state per system qubit in the paper's example, not a full shared analog
  source over dephasing, detuning, leakage, readout, and gates.
- MWPM uses a marginalised detector error model; correlation-aware decoders may recover some performance.
- QCA/PCA is a stress-test model, not a fitted hardware model.

## Relevance to AI_QEC [ours]
1. **SPP is the right reduced Axis-2 comparator, not the analog truth.** It should live beside the analog
   source fan-out as a Pauli/record-level comparator, much like the corrqec-scope caveat in the build
   contract: useful for temporal masks and matched-marginal Pauli generation, not a validator of coherent
   joint-L/leakage dynamics.
2. **The `SourceProcess` API should support fixed-marginal controls.** The temporal storm equations give
   an exact source where `xi` changes while `pbar(x)` is held fixed. This is the clean negative-control
   test that a mere time-indexed rate model cannot pass.
3. **The minimal Axis-2 build should not start with QCA.** Build `TemporalStormSPPSource` after a generic
   `SourceProcess` / `SourceTimeline` exists. Build `QCAPCASource` later as a stress-test source because it
   carries a spatial lattice, burn-in, density statistics, and pseudo-critical tuning.
4. **G4/G6 faithfulness should use multi-time observables.** Candidate observables: source spectral gap
   / correlation length; same-marginal independent baseline; timelike-string or multi-point record
   statistic; decoder-facing LER under marginal DEM when a Stim/Pauli slice is used.
5. **Do not launder Axis-2 into Markovian Lindblad rates.** The HMM hidden state is the source. Independent
   positive rates per time step are only the matched-marginal control.

## How to use / trust + open questions [ours]
- **Trust:** high for the SPP definitions, HMM equations, and qualitative QEC result; full text read. The
  paper is recent/preprint, but the formal object is directly implementable.
- **First implementation:** `TemporalStormSPPSource` as a reduced Pauli comparator with exact `xi`, `pbar`,
  and independent matched-marginal baseline.
- **Do not use it for:** validating full analog Axis-1 joint-L channel fidelity, qutrit leakage, or coherent
  drive/ZZ couplings.
- **Open:** decide whether the first SPP source is global-shared across a register, per-site independent,
  or clustered. The paper's temporal storm uses per-qubit environments; our coupling simulator likely needs
  both per-site and shared/clustered modes.
