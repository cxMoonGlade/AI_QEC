# WindowChannel — build spec (step-2, mainline)

> Specification for the window-channel object on the real XZZX surface code — white-box rung = d3
> (the standalone d3 patches; the d7 covering is deferred to the black-box). step-1 PASS:
> [`window_covering_RESULTS.md`](window_covering_RESULTS.md). Mainline code under
> `src/qec_twin/forward/`; **commit-gated** (user confirms before commit). Decisions below are
> LOCKED (owner, 2026-06-14; D1/D3 redirect 2026-06-15). Build via ≥3 disjoint implementer agents +
> a realtime reviewer.

## 0. Locked decisions

**D1 — White-box scope = the d3 patch (9 data + 8 stabilizers).** The white-box object covers only
mechanisms that live entirely inside one window; cross-window (seam) composition is the black-box's
job. Mapped to the dataset, the white-box **validation rung is d=3**: the nine standalone
`d3_at_q*` patches (`d3_at_q2_7, q4_5, q4_9, q6_3, q6_7, q6_11, q8_5, q8_9, q10_7`), each = 9 data +
8 XZZX stabilizers, all internal, no seam, fully observed — a clean single-window twin (step-1
RESULTS §3.1: each d7 interior window equals its standalone d3 patch). The d7 covering (49 windows +
seam) is the black-box rung, with d5 (4 patches) the intermediate. This spec builds the per-window
white-box object; the d3 patch IS the 3×3 window, standalone.

**D3 — Runtime representation = a 9q data register + per-stabilizer measurement instrument; the
faithful explicit-ancilla circuit is RETAINED ONLY AS A NUMERICAL ORACLE.** The runtime white-box
object is a CPTP map on the window's **9 data qubits** (`ρ_data`, `4^9 × 16 B = 4.2 MB`), NOT
data+ancilla. Syndromes come from **per-stabilizer measurement instruments** — each internal
stabilizer's local sub-circuit (ancilla init |0> → CZ chain to its ≤4 data with the CZ noise
mechanisms → ancilla measure with readout flip p=0.005 → reset) is reduced by tracing out the
ancilla to a quantum instrument acting on the stabilizer's data support (the derivation is in
[`window_instrument_derivation.md`](window_instrument_derivation.md)). The faithful
explicit-ancilla circuit is **retained only as a numerical ORACLE** to validate the 9q instrument's
equivalence; it is not the runtime representation. Because the white-box runtime is the **d3 patch**,
the oracle is the same d3 patch run as a **progressive faithful sub-system** (9 data + 1 ancilla = 10q
per stabilizer; 9 data + k≤4 ancilla ≤ 13q for circuit-order sub-sets; the full 17q d3 register =
275 GB is never run whole, established by decomposition — see
[`window_instrument_derivation.md`](window_instrument_derivation.md) §5); d7 cross-window is deferred.
The already-drafted faithful `WindowChannel` (generic over window data + ancilla) is that oracle engine.
**Epistemic status (b)/pending:** the 9q-instrument↔faithful-oracle equivalence is a DERIVATION +
PREDICTION, NOT yet numerically confirmed; the "exact" claim is conditioned on perfect leakage-free
ancilla reset (degrades to an approximation under imperfect reset / leakage). Mainline code for the
9q instrument lands only AFTER the equivalence is validated against the oracle, through the
commit-gate.

The faithful-circuit RATIONALE in decisions 1–4 below is **reframed under D3 as the oracle's
construction**: the faithful single-round noisy circuit is the numerical oracle; the runtime object
is its exact ancilla-traced 9q instrument (equivalence pending). The decisions below describe the
oracle and the shared mechanism/precision/build disciplines that carry to both representations.

1. **Composition = strict circuit gate-order (physically faithful) — the ORACLE.** The faithful
   WindowChannel (the oracle) is the **window-local noisy circuit**, not an abstract CPTP
   composition: take the real circuit's single-round gate schedule restricted to the window's data +
   their ancilla (the 4 CZ layers, H, the DD X/Y, measure/reset), and insert **learnable mechanism
   channels at the real noise locations** (post-gate, idle, pre-measure), evolved in circuit order.
   Rationale: a canonical-order abstraction is a toy that, once reused as a foundation, cannot be
   debugged (prior lesson; see [[feedback-no-toy-models-real-target]]). The runtime 9q instrument
   (D3) is this same faithful circuit with the ancilla traced out per round (equivalence pending);
   it inherits the faithful circuit-order composition on the shared 9q data register. This aligns
   step-2 with the step-3 multi-round forward (same window-local circuit, R rounds) by construction.
2. **Precision = complex128 on GPU** (matches `cptp_channel.py`). The runtime 9q `ρ_data` is
   `4^9 × 16 B = 4.2 MB`; the faithful d3 oracle sub-system is 2^≤13 (9 data + 1 ancilla = 10q =
   16 MB per stabilizer; ≤13q = ≤1 GB for circuit-order sub-sets), GPU-feasible on a 5090.
3. **Dictionary scope = full 1q + full 2q now (overcomplete); 3q ready-but-OFF.** 3q primitives are
   objectively redundant under decision 1 (the ≤2q dictionary composed in circuit order already
   generates 3-body correlations via fault propagation; a 3q primitive aliases with those and has no
   ≤2q-gate circuit origin) and unidentifiable absent an irreducible-3-body residual. The
   arity-general interface supports 3q slots; they are switched on only when a step-3 held-out
   model-class residual demands a *specific* data-pointed 3q mechanism (correction 3/4).
4. **Build = ≥3 disjoint implementer agents + a realtime reviewer** (reviews each file the moment it
   is produced; messy code / obvious logic errors caught on the spot), integrator runs the
   self-checks, then user confirmation before commit (commit-gate).

## 1. Files

- `src/qec_twin/forward/mechanisms_torch.py` — the θ-parameterised, differentiable,
  CPTP-by-construction mechanism dictionary (torch port of the `channels.py` NumPy builders).
- `src/qec_twin/forward/window_channel.py` — the `WindowChannel` object: window-local single-round
  noisy-circuit channel + `ρ_BC` + PTM coherence budget + CPTP self-check API.
- `tests/test_window_channel.py` — the executable spec (self-checks, each with a positive control).

## 2. Mechanism dictionary (`mechanisms_torch.py`)

Each mechanism: `θ (torch leaf, requires_grad) → Kraus stack (r, d, d) complex128`, CPTP by
construction. Coherent-non-Pauli/non-Clifford first (correction 2).

- **Coherent unitary** (the differentiator): `U(θ) = matrix_exp(-i θ G / 2)`, Kraus = `[U]`,
  generator `G` per mechanism — 1q X/Y/Z (M6/M7/M20), 2q ZZ (M8), XX/YY (M22/M23/M10),
  controlled-phase (M21), two-Pauli combinations (M27–M33). θ free, fully differentiable.
- **Non-unitary CPTP**: amplitude damping (M4), 2q depolarizing (M9), correlated relaxation (M12),
  custom non-Pauli (M15), thermal (M24), leakage surrogate (M34), Pauli-stochastic (M0/M5/M25/M26).
  Strength reparameterised `p = sigmoid(raw)` to stay in (0,1) and differentiable everywhere (avoid
  the √0 infinite-gradient; `probability_floor` is the hard floor only).
- Each torch builder is the exact differentiable mirror of the `channels.py` builder of the same
  name (cross-validated in the tests, §6.4). 1q set + 2q set; 3q interface present, default off.
- Readout (M1/M2/M3) is the ancilla measurement-flip model (the circuit `M(0.005)`), handled in the
  forward, **not** in the window-data dictionary.

## 3. WindowChannel (`window_channel.py`)

- **Placement granularity (LOCKED)**: faithful placement (decision 1) — at each noise location in the
  window-local round, insert a learnable mechanism of the matching type/arity; **strengths tied per
  (mechanism-type, support-tuple) across rounds**: 1q per data qubit (× 1q-gate/idle class), 2q-coherent
  per CZ (data,measure) gate and per (data,data) adjacent spectator pair; the SI1000 baseline
  (idle/measure/reset/CZ depolarizing) is learnable at its own locations; 3q off. Build stage 0 enumerates
  the exact per-class placement counts from the parsed single-round schedule.
- **Construction**: given a window (≤9 data ids) + its ancilla + the parsed single-round gate
  schedule (restricted to those qubits) + the slot placement (1q@data, 2q@CZ-adjacent pairs from
  step-1) + θ, build the window-local single-round noisy circuit: ideal gates in circuit order with a
  learnable mechanism channel inserted at each noise location.
- **Embedding**: reuse `forward/exact/circuit_sim.py` `embed_operator` / `apply_channel_local`
  (arity-general) to act a k-qubit mechanism on the **9q data register** (`2^9` state space,
  `4^9` density-matrix space). Under D3 a mechanism's support is the data qubits it touches; the
  instrument reduction (tracing the ancilla per stabilizer) keeps the acted-on space at the 9 data
  qubits, so this is consistent with the register bound below — both the embedding target and the
  materialised register are the 9 data qubits (no data+ancilla register at runtime). In the faithful
  oracle the same embedding additionally targets the in-window ancilla.
- **Evolution**: `apply_kraus` (from `cptp_channel.py`, device-aware, differentiable) in circuit
  order → the single-round window density-matrix map.
- **`ρ_BC`**: partial trace of the window state to an overlap region (the seam anchor, step-4). Add a
  torch partial-trace helper if `forward/exact` lacks one.
- **Register bound (memory, HARD) — D3 9q-data register + instruments**: the runtime white-box
  register is the window's **9 data qubits** (`ρ_data`, `4^9 × 16 B = 4.2 MB` complex128), NOT
  data+ancilla. Syndromes are produced by **per-stabilizer measurement instruments** that trace the
  ancilla out per round (D3 / §0); instrument construction touches at most a ≤5q local sub-system
  (one plaquette's ≤4 data + 1 ancilla), and the materialised runtime register stays 9q.
  - The **faithful explicit-ancilla register is the ORACLE only**, and its size is the cost
    motivation for D3: the full d3 patch faithful register = **17 qubits** (9 data + 8 ancilla,
    `4^17 × 16 B = 275 GB`, i.e. `4^(17-9) = 65536×` the 9q register) — infeasible on any single GPU,
    which is why the runtime object is the 9q instrument and the oracle is run as a **progressive d3
    sub-system** (9 data + 1 ancilla = 10q; 9 data + k≤4 ancilla ≤ 13q), never the full 17q. (The d7
    interior window's 13q = `1.07 GB` / `256×` is the analogous ratio for the deferred cross-window
    stage.) The full data + ALL-touching-ancilla register (~23 q) is infeasible anywhere and is
    FORBIDDEN.
  - Assert the runtime register = 9q (`ρ_data` shape `2^9 × 2^9`) and GPU-memory headroom at
    construction; never OOM. The faithful oracle sub-system, when run for the equivalence check,
    asserts its own ≤13q bound and GPU headroom separately.
- **GPU-only (HARD gate)**: all model compute (the forward `apply`, CPTP/eigvalsh, gradients, tests)
  runs on **cuda** — `device` defaults to cuda and tests require cuda (assert `torch.cuda.is_available()`,
  raise otherwise; NO `cuda if available else cpu` fallback). Any `device="cpu"` in model-compute code
  is a defect → cuda. Only RNG-seed generators may stay CPU then `.to(cuda)`. Never run window tests on
  CPU to dodge memory — bound the register instead (above). This is a blocking reviewer criterion.

## 4. Representation & invariants (correction 2 + PTM)

- **Source of truth = Kraus/Stinespring** (complex128). The model body is always this.
- **Derived lenses** computed from the Kraus: `choi_matrix` (CP check via PSD), `tp_residual` (TP),
  and an **n-qubit PTM generalised from `pauli_transfer_matrix`** (currently single-qubit only) for
  small supports (1q 4×4, 2q 16×16).
- **Coherence budget = PTM off-diagonal Frobenius mass** = exactly what a Pauli/DEM export discards
  (band-tracked, a reportable result). **Never diagonal-truncate the PTM in the model** (that is the
  Pauli twirl = DEM = the forbidden collapse); diagonal-truncation is only the downstream export.

## 5. Parameters (field-level; correction 3/4)

- θ lives on the FIELD, indexed by support-tuple, canonical-home deduped: 1q = 49, 2q = 156 (step-1).
  Overlapping windows are evaluation units; shared parameters are tied, not duplicated.
- Expose a per-mechanism sensitivity interface (∂output/∂θᵢ) for step-3's Fisher-rank
  identifiability / alias band. Step-2 provides the interface only; it does not fit.

## 6. Self-checks (`tests/test_window_channel.py`) — every check carries a POSITIVE CONTROL

Per [[feedback-adversarial-self-verification]]: a check that cannot distinguish "broken" from
"passed" is worthless; each test asserts it is alive.

1. **CPTP**: every mechanism + the composed window map has `tp_residual < NUMERICAL_ZERO` (1e-12) and
   a PSD Choi (min eigenvalue ≥ −1e-12). *Positive control:* a deliberately non-TP map is flagged.
2. **Coherence representable**: coherent mechanisms (rzz, …) have PTM off-diagonal mass > 0.
   *Positive control:* a Pauli-stochastic mechanism has ~0 off-diagonal (diagonal PTM).
3. **Placement correctness**: an embedded operator acts on the intended qubits (permutation check).
4. **Cross-validation oracle**: torch builder vs `channels.py` NumPy builder at the same θ, elementwise
   < 1e-10.
5. **`ρ_BC` self-consistency**: partial trace matches a brute-force reference; window-internal
   consistency.
6. **Gradient**: ∂(simple functional)/∂θ matches finite difference. Any fault-injection-based
   teacher check uses a Pauli `*_ERROR(1.0)` channel, **not** a Pauli gate (the
   `compile_detector_sampler` gate-absorption trap; [[feedback-adversarial-self-verification]]).

GPU; complex128; scripted-execution; `tests/test_window_channel.py` is the executable spec.

## 7. Reuse vs new

- **Reuse**: `apply_kraus` / `tp_residual` / `choi_matrix` / `pauli_transfer_matrix` /
  `StinespringChannel` (`cptp_channel.py`); `embed_operator` / `apply_channel_local`
  (`forward/exact/circuit_sim.py`); `NUMERICAL_ZERO` (`numerics.py`); `channels.py` (NumPy oracle).
- **New**: θ-parameterised torch builders; the window-local single-round noisy-circuit assembly;
  n-qubit PTM generalisation; partial-trace helper; coherence-budget.

## 8. Deferred (trigger-gated, never dropped)

True-3q mechanisms (residual-triggered, §0.3); the multi-round spacetime-marginal forward + NLL fit
(step-3, reuses `calibration/hardware_nll.py`); the seam composition (step-4); Fisher / alias scoring
(step-3). **Asymmetric `rxx_ryy` (M10 two-angle, `theta_x != theta_y`) is a deferred two-leaf slot:**
the §10 single-leaf signature ties `theta_x = theta_y = theta`, so the torch builder cannot represent
the oracle M10 default (`epsilon_y = 0.7*epsilon_x`); a conscious modeling limitation on record — any
step-3 attempt to recover an asymmetric XX/YY coupling is mis-specified by construction and must fall
back to the NumPy oracle (`channels.rxx_ryy_unitary`) or this future two-leaf slot, never silently
aliased during identifiability scoring.

## 9. Build orchestration — PARALLEL (disjoint files, against the §10 contract)

Four implementers run **concurrently** (not sequentially), each owning a disjoint file and coding
against the frozen §10 interface contract; each file is **reviewed the moment its implementation
finishes** (realtime, adversarial) with a conditional fix; placement enumeration runs in parallel.
- **A** — `forward/mechanisms_torch.py` (dictionary, §2). **D** — `forward/window_diagnostics.py`
  (n-qubit PTM / coherence budget / Choi-PSD / partial-trace, §4). **B** — `forward/window_channel.py`
  (assembly, §3). **C** — `tests/test_window_channel.py` (§6). **P** — `outputs/placement_enumerate.py`.
- A and D self-smoke-test (no deps); B and C code strictly against §10 (their deps are built
  concurrently) and are executed by the integrator.
- **Reviewers** (one per file, parallel) — adversarial static review vs §10 + the spec; block on findings.
- **Integrator (me)** — reconcile any interface drift, run the GPU suite, report evidence; **user
  confirmation before any commit** (commit-gate).

## 10. Interface contract (FROZEN — the parallel build codes against this)

All `complex128`; a `device` kwarg everywhere; reuse `apply_kraus` / `tp_residual` / `choi_matrix`
from `cptp_channel.py`; floors via `NUMERICAL_ZERO`.

**`forward/mechanisms_torch.py`** — θ-parameterised differentiable CPTP builders. Each builder
`def <name>(theta: torch.Tensor, *, device=None) -> torch.Tensor` returns a Kraus stack `(r, d, d)`
(d = 2 for 1q, 4 for 2q); `theta` is a real scalar leaf — coherent builders use it as the rotation
angle, non-unitary CPTP builders use `p = torch.sigmoid(theta)`. Registries mirror the same-named
`channels.py` NumPy builders:
- `MECH_1Q: dict[str, builder]` keys `{rx, ry, rz, amp_damp, phase_damp, pauli_x, pauli_y, pauli_z, thermal, custom_nonpauli, leakage}`
- `MECH_2Q: dict[str, builder]` keys `{rzz, rxx, ryy, rxx_ryy, cphase, two_pauli_xy, two_pauli_zx, two_pauli_zy, depol2, corr_relax}`

**`forward/window_diagnostics.py`** — small-support channel diagnostics:
- `pauli_basis(n: int, *, device=None) -> Tensor`  # (4**n, 2**n, 2**n) normalised n-qubit Paulis
- `ptm(kraus: Tensor, n: int, *, device=None) -> Tensor`  # (4**n, 4**n) real PTM R_ab=(1/2**n)Tr[P_a Φ(P_b)]
- `coherence_budget(kraus: Tensor, n: int) -> float`  # Frobenius mass of the PTM off-diagonal
- `choi_min_eig(kraus: Tensor) -> float`  # min eigenvalue of choi_matrix(kraus); CP iff >= -NUMERICAL_ZERO
- `partial_trace(rho: Tensor, keep: list[int], n: int) -> Tensor`  # keep `keep` (order preserved), trace the rest

**`forward/window_channel.py`** — the object. Under D3 there are two paths: the **runtime path** is
the 9q-data-register + per-stabilizer instrument; the **faithful `apply` is the ORACLE** used to
validate the runtime path's equivalence (pending). The signatures below are the frozen oracle
contract; the runtime 9q-instrument signatures are marked **pending the 9q implementation** and are
not over-specified here — they are settled when the instrument code is written (after equivalence
validation, through the commit-gate).
- `class WindowChannel`:
  - `__init__(self, window_data: list[int], ancilla: list[int], round_schedule, placement, *, device=None)` — builds the learnable θ leaves from `placement` (faithful, tied per (type, support-tuple)).
  - `apply(self, rho: Tensor) -> Tensor` — **the ORACLE**: faithful single-round window map (Kraus composition in circuit order on the data+in-window-ancilla register).
  - `rho_bc(self, rho: Tensor, overlap_data: list[int]) -> Tensor` — reduced state on the overlap.
  - `coherence_budget(self) -> dict` — per-mechanism + total PTM off-diagonal mass.
  - `parameters(self) -> list[Tensor]` — the θ leaves (for the step-3 fit).
  - `sensitivity(self, rho: Tensor, index: int) -> Tensor` — ∂apply/∂θ_index hook (interface; autograd ok).
- **Runtime instrument interface (pending the 9q implementation)** — the 9q-data-register path of
  D3. It applies per-stabilizer measurement instruments `{E_s}` (ancilla traced out, §0 / the
  derivation doc) in faithful circuit order on the 9q `ρ_data`, returning the internal syndrome
  distribution and the post-measurement data update. Exact method names / signatures (e.g. a
  `step_round(rho_data, ...) -> (syndrome_dist, rho_data')` and an instrument builder) are **not
  fixed here** — they are settled by the 9q implementation once the equivalence to the `apply`
  oracle is numerically confirmed; this spec only fixes that the runtime register is the 9 data
  qubits and that the instruments compose in faithful circuit order on the shared register.
- `build_placement(round_schedule, window_data, ancilla, adjacency) -> placement` — faithful placement from the schedule per the LOCKED granularity (§3).
