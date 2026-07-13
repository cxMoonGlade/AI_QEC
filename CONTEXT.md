# AI QEC Domain Context

This repository builds toward a **faithful, GPU-first simulator of QEC error mechanisms**
(`error_coupling_simulator`): it applies a **specified noise process** to a QEC circuit
(rotated surface code / XZZX) and produces the **multi-time syndrome record**. Binding
spec: `docs/SIMULATOR.md`.

## Terms

- **Noise process**: a noise model we SPECIFY (not a fit to hardware). It applies declared
  error mechanisms to the circuit and emits records, carrying its own **evaluator-only**
  ground truth (the channel field + source trajectory + mechanism params). It is the true
  generative process — richer than, and **not** identified with, a DEM. The current
  source-conditioned dense-qubit process (`noise_processes/`) and static data-qutrit XZZX process
  (`mechanisms/` + legacy scalable carriers) are **separate objects**, not one production instance.
  Their complete bridges are `open / CODE_BLOCKED`; see
  `docs/twin_validation/production_rtn_and_leakage_bridge_split_literature_closure_2026-07-13.md`.
- **Record**: the product — per-round `{detector bits, observable flips}`, emitted as `.b8` shot
  data or represented by its joint law. A `.dem` is an optional decoder-facing reduction, not the
  record. Feasibility and faithfulness gate on the record, never on a carrier bond / state fidelity
  (ADR 0011). A known legacy qutrit accessor currently labels raw syndrome bits as `det`; it must
  receive the declared temporal XOR fold before detector-level scoring.
- **Two noise axes**: **Axis-1** = within-substep joint-Lindbladian coupling (ZZ crosstalk,
  T1/T2, thermal, fSim residual, readout dephasing, leakage Hamiltonians, assembled into one
  joint generator per substep); **Axis-2** = **notion-2** classical multi-time record memory
  (a shared classical source `z_t` / `ξ(t)` — 1/f bath or RTN — modulating per-round rates,
  designed to leave a beyond-Markov record signature; current evidence is limited to the declared
  frozen record policy, not a generic causal process family).
- **Non-Pauli mechanisms**: span both axes — **leakage** (qutrit `|2⟩` / ququart `|3⟩`;
  WG leakage; LRU/DQLR reset), **drift** (slow coherent over/under-rotation, axis drift),
  **crosstalk** (coherent ZZ coupling, correlated errors), **burst** (correlated-in-time
  bursts). They can carry coherence/structure a fixed nonnegative Pauli-rate vector cannot;
  they are **not in general exactly/losslessly representable by a fixed nonnegative Pauli DEM**.
  Special channel-, schedule-, or instrument-specific reductions may still exist.
- **notion-1 / -2 / -3** (three non-exclusive object labels, not a strength ladder):
  **notion-1** = reduced-map divisibility/backflow diagnostics (RHP and BLP are distinct; neither
  is by itself evidence of a quantum bath); **notion-2** =
  observed-record memory/order in the fixed passive record law `P(m_1:R)`, without identifying a
  classical or quantum origin (the current Axis-2 implementation uses a classical latent source;
  its Gaussian positive-covariance surrogate is CP-divisible; two declared free-induction lifts
  of the finite-RTN defaults have exact BLP backflow, but the production `z -> Theta` QEC map and
  record still lack the channel/instrument bridge needed for any notion-1 verdict);
  **notion-3** = quantum
  memory/backaction at the environment/process-tensor level. Certifying notion-3 generally needs
  an instrument family/active access and is out of scope. These labels do not imply that coherent
  or non-unital mechanisms are absent from a fixed record. Evidence/status:
  `docs/twin_validation/notion123_taxonomy_literature_closure_2026-07-13.md` and
  `docs/twin_validation/finite_rtn_exact_cpdiv_result_2026-07-13.md`.
- **Carrier**: the forward engine. Ladder: exact density matrix (`carrier/exact`; roughly 15
  **qubits** by memory, but the current qutrit d3 oracle is 9 sites at about 5.77 GiB) → MPS MCWF
  thin-strip (`quimb`; bounded χ is conditional on fixed strip width/depth/noise/accuracy) → **2D
  PEPS full `d×d`** (`carrier/peps`, the active frontier; a 1D MPS can require `χ=2^{Θ(d)}` across
  a full-square cut in the worst/project-estimate regime).
- **Record-faithful truncation** (ADR 0011, reopened): an acceptance criterion requiring the
  truncated carrier to preserve the declared joint record law within its registered band. It is
  **not yet established** for coherent leakage or long-range/loopy PEPS truncation; zero added
  entropy, WTG/FET/ZMT objectives, and notion-2 memory diagnostics cannot substitute for the full
  d3 record comparison. Feasibility gates on the record, never on `bond=χ` alone.
- **DEM parity map** (`A`): a binary matrix `A ∈ F_2^{B×M}` mapping Bernoulli DEM fault bits
  to observed detector/logical bits via `y = A·e (mod 2)`. The DEM is the decoder-facing
  reduction of a noise process, never the object itself.
- **Stage-1 fault logit**: `lambda_j = logit(p_j)`. Do not write this as `ell_j`.
- **do() / intervention**: a knob is realized as a parameterization-independent, channel-level
  transformation of the CPTP channel (`E_{i,t}`) — never an edit of a mechanism-native
  parameter. Its effect is scored on the observable consequence `Δp(y)` / ΔLER on the record,
  never by comparing channels directly.
- **Logical error rate (LER)**: the decoded logical-observable flip probability under a
  declared frozen decoder (e.g. MWPM/PyMatching), not the raw undecoded flip rate.
- **Ground-truth anchor**: an INDEPENDENT, exact-or-declared-reduction reference for a record
  statistic — the d3 density-matrix oracle (`carrier/exact/qutrit_dm`), a Stim Clifford slice,
  the GF(2) stabilizer entropy, or a closed-form identity — against which a carrier is
  certified. INDEPENDENT = a route that does NOT share the carrier's implementation
  (anti-circular: a check vs the engine's own oracle is not an anchor).
- **Certification (certify)**: scoring a noise process's (or the carrier's) emitted records
  against the ground-truth anchors → an epistemic ledger (per (anchor, statistic): value,
  band, class (a)/(b)/(c), verdict), with first-class, non-optional negative controls.
  Evaluator-only (`certify/`).
- **Memory-axis instrument (notion-2)**: the record's absolute multi-time Markov-order
  structure vs a genuinely-Markov-order-k generative null — a full-history/order ladder,
  with lag-local CMI `I(mᵣ;mᵣ₋₂|mᵣ₋₁)`, Anderson–Goodman `G²`, and `E(k)` as diagnostics.
  A **memory-specific discriminability instrument, not a parameter-recovery learner**, and never
  a generic full-record-faithfulness certificate. Fitting `θ` from the same fixed passive record is
  passive parameter recovery; it becomes notion-3-style active tester access only when the
  instrument/intervention family itself is varied.
- **Numerical floor**: floating floors/thresholds use
  `error_coupling_simulator.numerics.NUMERICAL_ZERO == 1e-12`, never for structural zeros
  (Pauli entries, bit values, integer indices, counts, labels).

## Claim boundary

- **No physical ground truth.** A noise process is a model we specify; the oracles (QuTiP-derived
  channels, closed forms, the exact density-matrix engine) are FORMAL bug-catchers, never
  "validated against reality." No claim of correspondence to a real device is made from a noise
  process.
- **No provenance laundering.** A claim-bearing number must identify whether it is paper/data
  measured, paper-derived, calibrated, project-designed, a convenience default, or numerical-only,
  with an exact source pointer and transformation chain where applicable. Cross-paper/device tuples
  are composite benchmarks, not physical device cells (`docs/NUMERICAL_PROVENANCE.md`).
- **Passive record only.** The simulator characterizes the passive syndrome record; the full
  process tensor (active causal breaks / designed control / parameter recovery) is a distinct
  access class and is **out of scope**.
- **Every d5/d7 distributional claim is PROVISIONAL** (there is no external oracle above d3):
  reportable and usable for go/no-go gating, but never a premise for a definition, derivation,
  or further conclusion.
- Metrics (NLL, TVD, CMI/G², %ΔLER, ε_d/Λ) are **instruments** on the record — evidence for
  distributional fidelity, not the object.
