# Finite-RTN exact reduced-map diagnostic — preregistration (2026-07-13)

> **Status:** frozen before implementation or result inspection. **Prerequisite gate: PASS only for
> the two explicitly declared one-qubit free-induction diagnostics below.** Literature packet:
> [`finite_rtn_exact_cpdiv_literature_closure_2026-07-13.md`](finite_rtn_exact_cpdiv_literature_closure_2026-07-13.md).
> The source-to-production-QEC-channel and channel-to-record rows are open, so this preregistration
> does not authorize either inference.

## 1. Question charter

For the defaults of `OneOverFDriftSource`, answer two bounded questions:

1. Under the **continuous symmetric-CTMC free-induction lift**, does the exact product coherence
   have a positive excursion in absolute value and therefore witness BLP backflow/non-divisibility
   of that declared one-qubit reduced map?
2. Under the separately declared **cycle-held free-induction lift**, do the exact cycle-boundary
   characteristic function and a full `2^K` transfer-matrix oracle agree, and does its integer-time
   absolute coherence have a positive excursion in the registered horizon?

Out of scope: CP-divisibility of a stochastic source without a system map; the production
`z -> Theta` fan-out; the quarter-CZ QEC channel; syndrome-record Markov order; process-tensor
quantum memory; PEPS truncation; and LER.

## 2. Frozen production inputs

Read without alteration from `OneOverFDriftSource()`:

```text
A = 1e-4 rad/ns
K = 8
v_k = A/sqrt(K)
gamma_k = geomspace(0.005, 0.5, K) per cycle
tau_cycle = 1000 ns
p_k = (1-exp(-2 gamma_k))/2
```

Use cycle units in the gate:
`a_k = v_k tau_cycle` radians per cycle and `g_k = gamma_k` per cycle. No parameter is
hardware-calibrated; all are project-design values.

## 3. Declared mechanisms

### D1 — continuous CTMC free-induction lift

Each `s_k(t) in {-1,+1}` is a stationary symmetric CTMC with per-direction rate `g_k`. Declare the
diagnostic qubit Hamiltonian

```text
H(t) = (1/2) [sum_k a_k s_k(t)] Z                         (cycle units).
```

For one mode, with `delta_k=sqrt(g_k^2-a_k^2)`, the exact factor is

```text
L_k(t) = exp(-g_k t)
         [cosh(delta_k t) + (g_k/delta_k)sinh(delta_k t)]
```

with analytic continuation `delta_k=i omega_k` for `a_k>g_k`, and limit
`exp(-g_k t)(1+g_k t)` at equality. Independence gives `L(t)=product_k L_k(t)`.

### D2 — cycle-held free-induction lift

At cycle `r`, hold the emitted endpoint state `s_{k,r}` fixed throughout that diagnostic cycle and
apply phase `a_k s_{k,r}`. For one mode, let

```text
T_k = [[1-p_k,p_k],[p_k,1-p_k]],
D_k = diag(exp(-i a_k), exp(+i a_k)),
pi_k = [1/2,1/2].
```

Then for integer `n>=1`,

```text
L_k[n] = pi_k D_k (T_k D_k)^(n-1) 1,
L[n] = product_k L_k[n],   L[0]=1.
```

This is project algebra for the declared held-cycle diagnostic, not a quoted paper result.

## 4. Primary observable and standard metric

For pure dephasing, the trace distance of the optimal equatorial pair is `D(t)=|L(t)|`. The primary
metric is the BLP positive excursion

```text
N_BLP = sum over increasing intervals [D(end)-D(start)].
```

Classification requires only a strict positive excursion. For D1, the load-bearing witness is an
analytic first zero of a strong factor followed by a nonzero recovery; the dense grid estimates
`N_BLP` but cannot create the verdict. For D2, the exact registered observable is
`max_{0<=n<200} (|L[n+1]|-|L[n]|)`.

No logarithmic RHP integral is used as the headline metric because exact coherence zeros make the
time-local generator singular. BLP revival is sufficient to reject divisibility for this pure
dephasing map; it is not asserted to equal every RHP quantifier in general.

## 5. Predictions frozen before the run

1. **D1 positive:** the default has exactly three modes with `a_k>g_k`. The first such factor has a
   finite simple zero
   `t0=(pi-atan(omega/g))/omega`; unless the whole product is identically zero, `|L|` recovers after
   that zero. Predict a positive BLP excursion in `0<=t<=200` cycles.
2. **D2 directional prediction:** strong modes should produce a positive integer-time excursion by
   200 cycles. This may be falsified by cycle-boundary aliasing; a D2 null does not overturn D1.
3. **Independent-oracle agreement:** product and full `2^8` formulations agree to absolute error
   `<=1e-10` at all registered comparison times.
4. **Gaussian negative control:** the second-cumulant surrogate formed from the same positive
   exponential covariance is monotone and has no positive excursion above roundoff.
5. **All-weak negative control:** replacing every `g_k` by `2 a_k` makes every exact CTMC factor
   positive and monotone; the product has no positive excursion above roundoff.
6. **Corruption falsifiers:** interpreting `g_k` as half the coded rate (using `2g_k` in the closed
   form), or omitting one product factor, must disagree with the unchanged full-state oracle by more
   than `100 x 1e-10` at at least one registered point.

## 6. Independent ground truth

The main formula factors into eight analytic `2x2` problems. Ground truth deliberately uses a
different representation:

- D1: enumerate all `2^8=256` joint sign states; construct the CTMC row generator `Q`; evaluate the
  Feynman–Kac characteristic function
  `pi exp[(Q+i diag(sum_k a_k s_k))t] 1` with `scipy.linalg.expm`.
- D2: construct the full joint transition matrix `T=kronecker_k T_k`; evolve a 256-state weighted
  row vector by full-state phase and transition operations, without multiplying single-mode
  characteristic functions.

The two oracles share physical assumptions and parameters but not the factorized implementation,
so omission, ordering, and rate-convention errors are exposed.

## 7. Registered comparison points and numerical gates

- D1 horizon: `0..200` cycles; display grid spacing `0.01` cycle only for a reported BLP estimate.
- D1 oracle times: `0, 1, 10, 25, 50, 75, 100, 150, 200` cycles.
- D1 exact witness: earliest strong-factor zero and `t0+1` cycle, evaluated at 80 decimal digits.
- D2 integer horizon: `n=0..200`; oracle comparisons at `n=0,1,2,5,25,50,75,100,150,200`.
- Product/oracle tolerance: absolute `1e-10`, epistemic class (c), chosen to be far above double
  roundoff and far below the predicted physical-scale excursions.
- Monotonic-control tolerance: maximum positive step `<=1e-12` on the registered grid/sequence.
- High-precision zero: `|L(t0)|<=1e-60`; recovery is positive if `|L(t0+1)|>1e-12`.

Tolerance values are numerical-only and support implementation acceptance, not a physical threshold.

## 8. Constraint falsifiers and negative controls

| check | deliberate break | required outcome |
|---|---|---|
| rate convention | use `2g_k` in factors but unchanged generator | oracle gate fails loudly |
| product completeness | omit the slowest mode | oracle gate fails loudly |
| non-Gaussian necessity | use Gaussian second cumulant | monotone/null |
| strong-coupling necessity | set every `g_k=2a_k` | monotone/null |
| formulation invariance | factorized versus 256-state implementation | agree within tolerance |
| cycle semantics | continuous CTMC versus held-cycle | reported separately even if verdicts agree |

## 9. Bounded simplifications and error accounting

- D1 fills in an intra-cycle CTMC path consistent with, but not executed by, the endpoint sampler.
- D2 fills in a held phase that the source sampler also does not apply in the production fan-out.
- Both omit the actual multi-parameter fan-out, gates, leakage, ancilla, measurement/reset, and
  decoder. Their error relative to the production record is **unbounded** because the missing bridge
  is the object of interest. Therefore neither is a bounded approximation to the full QEC claim.
- Finite horizon can miss later revivals; a positive finding is valid within the horizon, while a
  null is only a horizon-bounded null.
- Dense-grid BLP is descriptive. D1's verdict uses an analytic zero/recovery witness so grid
  resolution cannot generate it.

## 10. Epistemic classes and decision rule

- **(a) exact literature-grounded:** D1 single-factor formula, independent product algebra, BLP
  revival implication under the declared pure-dephasing map.
- **(a) exact project-defined:** D2 transfer formula once the held-cycle lift is declared.
- **(b) predicted:** D1 positive; D2 positive within 200 cycles.
- **(c) numerical:** oracle tolerances, grids, output serialization, corruption margins.

Decision labels:

- `CONFIRMED_DIAGNOSTIC_ONLY`: all exact-oracle and falsifier gates pass and the registered revival
  exists for that named lift.
- `NULL_WITHIN_HORIZON`: exact-oracle gates pass but no registered revival exists.
- `IMPLEMENTATION_GATE_FAILED`: any independent-oracle or corruption-falsifier gate fails.

Under every label, the production QEC/channel/record claim remains `OPEN_BRIDGE`; no downstream
claim propagation is authorized.

