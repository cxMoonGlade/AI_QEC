# Full-text review — Burgelman, Wonglakhon, Bernal-Garcia, Paz-Silva & Viola, "Limitations to Dynamical Error Suppression and Gate-Error Virtualization from Temporally Correlated Nonclassical Noise" (arXiv:2407.04766v2; PRX Quantum 6, 010323, 2025)

> **Provenance (2026-07-03): FULL-TEXT read (精读).** arXiv HTML fetch
> (`WebFetch arxiv.org/html/2407.04766v2`) + abstract page, 31 pp, read end-to-end
> incl. 3 appendices. All section/equation/figure references are from the extracted text.
> Tags: **[paper]** = stated in the paper; **[twin]** = our application/inference for
> `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** Michiel Burgelman, Nattaphong Wonglakhon, Diego N. Bernal-Garcia,
  Gerardo A. Paz-Silva, Lorenza Viola. All at Dartmouth (Dept. Physics & Astronomy)
  except Wonglakhon (Khon Kaen Univ., Thailand). Viola group = long-standing leaders in
  dynamical decoupling, open quantum systems, and non-Markovian noise theory.
- **Venue / status.** arXiv:2407.04766v2 [quant-ph], 10 Apr 2025; published PRX Quantum 6,
  010323 (2025). 31 pp incl. 9 figures + 3 appendices (A-C). Typeset in PRX Quantum format.
- **Type.** Analytic theory (exact single-qubit Gaussian dephasing model) + numerical
  evaluation (spectral density integrals). Rigorous theorem + corollaries, no full-scale QEC
  simulation.

## Executive summary [paper]
The paper studies whether **dynamical error suppression (DES)** and the associated notion of a
**constant gate-error-per-gate (EPG)** — which underlies gate-error virtualization in layered
fault-tolerant architectures — can be maintained when noise is both **temporally correlated**
and **nonclassical** (i.e., has non-vanishing commutator `[B(t2), B(t1)]`). It uses a minimal
exactly solvable single-qubit model under Gaussian quantum dephasing noise. Core results:

1. **Gate fidelity depends on control history.** The fidelity of a DES-protected gate is
   determined not only by classical (symmetrized) noise correlations but also by a
   **bath-induced quantum phase** `theta_q` that encodes the entire prior control history.
   For purely classical noise (`C^-(tau) = 0`), this phase vanishes and fidelity is
   history-independent.

2. **Asymptotic fidelity saturation.** Under periodic control with many repetitions
   (`M -> infty`), the gate fidelity saturates at a value strictly lower than the initial
   (history-free) value, even when the classical decay `chi_c` is fully suppressed by DES.
   The saturation is proven under mild conditions on the low-frequency behavior of the
   nonclassical noise spectrum `S^-(omega) ~ sgn(omega) |omega|^s` with `s > 0`.

3. **Multi-reset phase accumulation.** After each perfect qubit reset, the quantum phase
   contributions `theta_{q,[k]}` from each inter-reset block accumulate: the total fidelity
   is `F_G(t_K) = 1/2 (1 + e^{-chi_c} cos(sum_k theta_{q,[k]}))`. Even with perfect system
   resets, the bath memory persists — the bath state cannot be reset without also resetting
   the bath.

4. **Control-induced resonances.** When periodic DES repetition frequency aligns with
   high-frequency noise spectral features (e.g., a Gaussian peak at `omega_1`), resonances
   can dramatically degrade gate performance.

5. **Bath re-equilibration rescue.** Prolonged high-fidelity idling (higher-order DD, scenario
   c3) can approximately restore the original bath statistics if applied over timescales
   exceeding the bath correlation time — but this exposes the qubit to white noise and
   creates tension with QEC cycle times.

6. **Challenge to FT architectures.** The results imply that standard fault-tolerant threshold
   theorems assuming refreshed bath states at each circuit location may need revision for
   nonclassical noise. Gate-error virtualization — the idea that QEC can treat all gates
   as having a fixed, location-independent EPG — may require active bath management
   beyond system-side QEC.

## Model — single-qubit Gaussian quantum dephasing (Sections II, III) [paper]
**Setup:** Single qubit with quantization axis `sigma_z`, internal Hamiltonian
`H_S = (omega_q/2) sigma_z` (hbar=1). The bath `H_B` is arbitrary; the interaction is pure
dephasing: `H_int = sigma_z otimes B`, where `B` is a bath operator. Under control via
instantaneous `pi_x` pulses (switching function `y(t) in {+1, -1}`), the total Hamiltonian
becomes `H(t) = y(t) sigma_z otimes B(t)`.

**Noise assumptions:**
- **Gaussian** with zero mean: all cumulants beyond second order vanish.
- **Stationary:** correlation functions depend only on `tau = t2 - t1`.
- **Nonclassical:** the anti-symmetrized correlation `C^-(tau) = <[B(t2), B(t1)]>` is nonzero.
  Classical noise would have `C^-(tau) = 0`.

**Correlation functions:**
- Classical (symmetrized): `C^+(tau) = <{B(t2), B(t1)}>` — real, even.
- Quantum (anti-symmetrized): `C^-(tau) = <[B(t2), B(t1)]>` — purely imaginary, odd.
- Fourier transforms: `S^+(omega)` and `S^-(omega)`.

**Spin-boson realization (explicit):** `H_B = sum_k Omega_k b_k^dagger b_k`,
`B = sum_k (g_k b_k^dagger + g_k^* b_k)`. Spectral density
`J(omega) = (1/2pi) sum_k |g_k|^2 (delta(omega - Omega_k) + delta(omega + Omega_k))`.
Then `S^+(omega) = coth(beta|omega|/2) J(omega)` and `S^-(omega) = sgn(omega) J(omega)`.
Paper uses zero temperature (`beta = infty`) for numerics.

**Spectral density model (used in numerics):**
- LF Ohmic part: `J_LF(omega) = (1/Gamma((1+s)/2)) (Delta_0/gamma_0) (|omega|/gamma_0)^s e^{-omega^2/gamma_0^2}`
- HF Gaussian peak: `J_HF(omega) = (Delta_1/(sqrt(pi) gamma_1)) [e^{-(omega - omega_1)^2/gamma_1^2} + e^{-(omega + omega_1)^2/gamma_1^2}]`
- Total coupling rate: `pi(Delta_0 + 2 Delta_1) = sum_k |g_k|^2`.

## Exact fidelity and the classical/quantum split (Section III) [paper]
The exact gate fidelity (Eq. 2 of the paper) for a DES-protected gate of duration `tau_G`,
applied at time `t_s` after the start of control, is:

`F_G(t_s) = 1/2 (1 + e^{-chi_c} cos(theta_q))`

**`chi_c` (classical decay factor):**
`chi_c = int_0^{tau_G} d tau_2 int_0^{tau_G} d tau_1 y_G(tau_1) y_G(tau_2) C^+(tau_2 - tau_1)`
where `y_G` is the gate's own switching function. This is purely classical — it depends
only on `C^+`. DES (DD) suppresses `chi_c` by engineering `y_G` such that its filter
function has high-order zeros near zero frequency.

**`theta_q` (quantum phase):**
A bath-induced phase that depends on the *full* control history before `t_s` via `C^-`.
Crucially, DES does NOT suppress `theta_q` in the same way as `chi_c` — the filter
order for the quantum phase is generically different (lower), leading to asymptotic
saturation.

**Key distinction:** For classical noise, `C^-(tau) = 0` => `theta_q = 0` =>
`F_G = 1/2 (1 + e^{-chi_c})`. No history dependence, no saturation below the
`chi_c -> 0` limit. The quantum phase is the sole source of history dependence
and the fidelity ceiling.

## Asymptotic saturation theorem (Section IV) [paper]
**Theorem (informal, Section IV.A):** For periodic control with DES, under mild conditions
on the low-frequency behavior of `S^-(omega)` (specifically, Ohmicity `s > 0`), the gate
fidelity converges in the limit `M -> infty` to:

`F_G(infty) = 1/2 (1 + e^{-chi_c} cos(theta_q^infty))`

with `theta_q^infty` finite. This saturation value is **strictly lower** than the
history-free fidelity `F_G(0)`. The physical origin: the quantum phase `theta_q`
accumulates with each repetition and converges to a finite asymptotic value, causing
`cos(theta_q)` to settle.

**Control-induced resonances (Section IV.B):** When the repetition frequency of periodic
control matches the center frequency `omega_1` of the HF noise peak, `theta_q` can
diverge (resonance), causing catastrophic fidelity loss. The resonance condition is
identified and analyzed via the filter-function formalism.

**DEPENDENCE on DES order:** Higher-order DD (e.g., concatenated DD) can suppress `chi_c`
to higher order but the quantum phase `theta_q` involves a different effective filtering
order. The mismatch is fundamental: classical and quantum parts of the noise couple to
control through different filter functions.

## Multi-reset scenario (Section IV.C) [paper]
For layered FT architectures with `K` reset operations (QEC rounds), the fidelity after
the K-th reset is:

`F_G(t_K) = 1/2 (1 + e^{-chi_c} cos(theta_{q,[1]} + theta_{q,[2]} + ... + theta_{q,[K]}))`

where each `theta_{q,[k]}` is the quantum phase accumulated between resets `k-1` and `k`.

**Key finding:** The quantum phases accumulate across QEC rounds. Even perfect qubit
resets do NOT reset the phase to zero because the bath retains memory of prior control.
The authors explicitly show that the bath state after a reset is
`rho_B(t_k^+) = Tr_S[rho_SB(t_k^-)]` — it carries forward all prior history.

**Asymptotic behavior:** As `K -> infty`, the same saturation behavior emerges but with
additional complexity from the interplay between the number of inter-reset repetitions
`M` and the number of resets `K`. The fidelity can oscillate if the phases do not
converge to a fixed value.

## Bath dynamics interpretation (Section V) [paper]
The paper provides the physical mechanism via the **exact bath-statistics update**:
- After each control+reset cycle, the joint unitary `U(t1,t2) = T_+ exp(-i sigma_z otimes int_{t1}^{t2} y(s) B(s) ds)` entangles system and bath.
- When the qubit is reset, the entanglement is broken, but the bath retains a modified state
  reflecting the accumulated phase.
- This produces **non-stationary noise** — the noise the qubit experiences changes from
  cycle to cycle because the bath evolves in response to prior control.

**Approximate re-equilibration (Section V.C):** If the qubit is kept highly pure for long
enough (via high-order DD or long idling periods), the bath has time to "forget" the
control history and approximately return to its initial thermal state. Condition:
idling time >> bath correlation time. However, this exposes the qubit to temporally
uncorrelated (white) noise — a tradeoff.

## Gate-error virtualization (Section VI Discussion) [paper]
"Gate-error virtualization" is the idea at the foundation of layered FT architectures
(including QEC): each gate can be characterized by a constant EPG, independent of
its location in the circuit. DES is supposed to reduce this EPG uniformly, and the
resulting virtual qubits/gates with a stable effective noise level can then be handled
by QEC.

**Why it fails:**
1. Fidelity saturation means DES effectiveness degrades over time — the EPG is not
   constant but explicitly history-dependent.
2. Cross-cycle bath memory produces non-stationary noise — the same gate at different
   circuit locations experiences different effective noise.
3. Control-induced resonances mean periodic DES can be actively harmful when spectral
   features align.

The paper concludes that for nonclassical noise, "the full bath evolution between circuit
locations must be accounted for" and that active bath management strategies (not just
system-side QEC) may be required.

## Numerical parameters and figure data [paper]
- **Minimum acceptable fidelity:** `F_G^{min} = 0.98` throughout.
- **Temperature:** Zero temperature (`beta = infty`).
- **Spectral density parameters (nominal):** LF Ohmic: `s = 1` (Ohmic), `gamma_0`, `Delta_0`;
  HF Gaussian: `omega_1`, `gamma_1`, `Delta_1`.
- Figures 1-9 explore fidelity vs M, vs tau_p (pulse spacing), for various spectral
  compositions, demonstrating saturation (Fig. 3-4), resonances (Fig. 5-6), and
  re-equilibration (Fig. 7-8).
- Specific parameter sweeps (from figures): saturation at `F_G ~ 0.96-0.985` for various
  Ohmicity values; resonance dips to `F_G ~ 0.5-0.9` when control repetition matches
  `omega_1`.

## Limitations [paper]
- **L1 — Single-qubit model.** Pure dephasing, no relaxation, no multi-qubit effects.
  The generalization to multi-qubit noise (crosstalk, correlated bath) is non-trivial
  and explicitly deferred.
- **L2 — Gaussian noise only.** Higher-order cumulants vanish; the theorem depends on
  Gaussianity for exact solvability. Non-Gaussian noise (e.g., two-level fluctuators)
  could introduce additional effects.
- **L3 — No full QEC simulation.** The paper analyzes gate fidelity, not logical error
  rates under a full QEC circuit. The implications for fault-tolerance thresholds are
  qualitative (discussion Section VI), not numerically quantified.
- **L4 — Instantaneous pulses and resets.** `pi_x` pulses are instantaneous (zero-width).
  Finite-duration pulses would introduce additional filter-function complexity.
- **L5 — Ideal projective resets.** Perfect qubit reset assumes no reset errors or
  measurement back-action on the bath.
- **L6 — Zero-temperature numerics.** Finite temperature would change the ratio of
  `S^+/S^-` (via the `coth` factor) and may modify the saturation values.

## Relevance to the twin — noise simulator, gauge, coupling simulator [twin]
1. **The fundamental mechanism for the twin's coupling simulator.** The paper proves
   that **bath-mediated error propagation persists even with perfect system resets**
   — the bath state is a dynamical variable that evolves under control. This is the
   foundational theoretical basis for why the twin's coupling simulator (continuous
   `Sigma`, passive detector records, MPS carrier) needs to track the bath state,
   not just the system. A Markovian approximation (reset bath each cycle) is
   provably too optimistic when noise is nonclassical. **[twin: noise simulator
   architecture]**

2. **Gauge/identifiability implications.** The quantum phase `theta_q` is invisible
   to any measurement that only tracks the classical (symmetrized) noise correlations.
   This creates a **gauge freedom**: two different bath states (differing by a pure
   quantum phase) produce identical `C^+(tau)` but different gate fidelities. The
   twin's identifiability analysis must account for this: the classical noise spectrum
   does NOT fix the quantum noise spectrum. For the twin's detector-level observables,
   this means the `C^+`-derived quantities (marginal detection rates) are insufficient
   to identify the full noise — consistent with the twin's existing finding that
   syndrome-only data is blind to coherence (`project-coherence-not-identifiable-syndrome-only`).
   **[twin: gauge/identifiability]**

3. **Continuous `Sigma` and passive detector records.** The paper's multi-reset analysis
   (Section IV.C) directly applies to the twin's QEC setting: each QEC round is a
   "reset" of the system qubits (via measurement and re-initialization), and the bath
   state `rho_B(t_k^+)` carries forward all prior history. The quantum phase
   `theta_{q,[k]}` from each round accumulates. This means the twin's passive detector
   records (detection events) encode information about the **accumulated** quantum
   phase, not just the per-round marginal noise — the detector correlations across
   rounds carry a signature of nonclassical noise that is not reducible to a classical
   noise spectrum. **[twin: continuous Sigma, passive detector records]**

4. **MPS carrier implications.** The MPS carrier (quimb MPS) represents the system+bath
   state. If we track the joint state, the bath's von Neumann entropy after each
   system reset is a witness for the accumulated quantum phase. The paper's result
   that `rho_B(t_k^+)` is a nontrivial function of prior control implies that the
   MPS's bath bond dimension may need to grow with `k` — limiting the number of
   QEC rounds that can be faithfully simulated with fixed bond dimension. This is a
   concrete resource bound for the twin's scalable carrier. **[twin: MPS carrier]**

5. **Gauge theorem connection.** The paper's classical (chi_c) vs quantum (theta_q)
   split maps onto the twin's gauge theorem's decomposition of observable noise into
   "gauge-fixed" and "gauge-dependent" parts. `chi_c` is gauge-fixed (determined
   by `C^+` alone); `theta_q` is gauge-dependent (requires knowing `C^-`). The
   twin's claim that the learner only identifies quantities in the gauge-fixed
   sector is physically grounded here: the quantum phase is exactly what the learner
   (which only sees `C^+`-equivalent marginals) cannot recover. **[twin: gauge theorem]**

6. **Control-induced resonances as a twin design constraint.** If the twin's coupling
   simulator uses periodic DES or periodic QEC cycles, the repetition frequency must
   be checked against spectral features of the bath. A control-induced resonance
   would manifest as a sudden degradation in logical error rate at specific cycle
   counts — a phenomenon the twin could potentially observe and that would validate
   the nonclassical nature of the noise. **[twin: coupling simulator validation]**

7. **Bath re-equilibration as a control knob.** The paper's finding that prolonged
   high-fidelity idling can approximately restore bath statistics suggests a possible
   **control strategy** for the twin's manipulation capability (the "MANIPULATE"
   axis). Inserting DD idling blocks between QEC rounds could serve as a knob to
   tune the effective bath memory — a `do()` intervention on the bath state, not
   just the system. **[twin: MANIPULATE capability]**

## How to use / trust + open questions [twin]
- **Trust:** high (PRX Quantum published; exact analytic results in the Gaussian
  dephasing model; rigorous theorem with mild conditions). The single-qubit restriction
  is the main caveat — generalization to multi-qubit noise is an open problem.
- **How to use:** (i) As the theoretical foundation for the twin's coupling simulator
  architecture — the bath memory mechanism is PROVED, not assumed. (ii) As the missing
  reference for the gauge theorem — the `chi_c`/`theta_q` split is the physical basis
  for the gauge-fixed/gauge-dependent decomposition. (iii) As a citation for why
  per-round marginal matching is insufficient for nonclassical noise.
- **Open for the twin:** (i) Generalize the single-qubit model to multi-qubit correlated
  noise — does the theta_q accumulation produce correlated logical errors? (ii) Compute
  the quantum phase accumulation explicitly for the twin's specific MPS carrier with
  finite-duration gates and non-instantaneous resets. (iii) Does the `s > 0` Ohmic
  condition hold for the Google Sycamore/Willow noise spectrum? If `s = 0` (sub-Ohmic),
  the saturation theorem's condition fails and the behavior may differ. (iv) The
  control-induced resonance effect at high-symmetry QEC cycle frequencies — can the
  twin's simulator reproduce this as a logical error rate spike at specific d and
  cycle count?
