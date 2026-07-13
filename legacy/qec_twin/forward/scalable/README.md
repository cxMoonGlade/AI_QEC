# forward/scalable — scalable forward backend (first content: the C1 composed-carrier arm)

Reserved for the >50-qubit forward model that replaces `forward/exact` beyond the
density-matrix wall. **Status (2026-06-10):** ADR 0008 picked the **C1 composed
architecture** (DEM/HMM bulk + window-exact CPTP coherent corrections) as the
conditionally-admissible shortlist; this module now holds its first real content —
the **seam-test-scale composed-carrier arm** (ADR 0008 C3, seam-test
pre-registration item 3 in `docs/metric_results.md`). The d=5/d=7 bulk engine
(DEM/HMM bulk; dMLE-TN as bulk engine + mandatory baseline) is NOT built yet and
stays gated on the seam-test verdict (K1).

**Contract.** Same `forward` contract `context c → p(s,m|c)`: `composed_strip_law`
returns the exact-Born strip observation law for a strip context, so
`calibration` / `knobs` / `audit` patterns apply unchanged (`fit_composed_carrier`
is the `calibration.nll.calibrate` loop on strip observations; `do_on_*` follows
the `knobs` channel-level discipline). The channel object and the four
capabilities stay backend-agnostic.

## The declared seam composition rule (the ONLY approximation in the arm)

Two repetition-code windows, each with its own checks; **no check straddles the
seam** (declared tiling `two-window-v1`; tiling is family design — a
seam-straddling re-tiling is a second registration). The carrier's strip state is
constrained to the product manifold `rho_L ⊗ rho_R`; in-window slots evolve
EXACTLY (`forward/exact` density-matrix engine per window). The seam slot
(Kraus stack on the seam pair) is applied at the H2 placement
`[ (prod_i E_i) ; E_seam ]^repeats` then extraction — **never commuted past
extraction** — through the pair of synchronous conditional reductions

```
Phi_L[sigma_R](rho_L) = Tr_R[ E_seam( rho_L ⊗ sigma_R ) ]
Phi_R[sigma_L](rho_R) = Tr_L[ E_seam( sigma_L ⊗ rho_R ) ]
```

where `sigma_L, sigma_R` are the two windows' record-averaged reduced seam-qubit
states, snapshotted together before either update. Each reduction is CPTP by
construction (`seam_conditional_reduction`). The strip law is the branch product
of the window laws. Dropped (tier-3 `B_misspec`, functional-indexed `B_carrier`,
never folded into `eps_log`): cross-window record/state correlation + the
record-conditioning of the seam action. With an identity/absent seam slot the
rule is exactly the identity, so the composed law equals the whole-strip
`forward/exact` oracle to float64 round-off — the zero-seam exactness pin.

## Module map

- `composed.py` — `StripSpec`/`StripContext`/`StripObservations` (the thin
  instrument interface), `seam_conditional_reduction`, `composed_strip_law`,
  `StripLaw`, the declared record/code conventions (`split_strip_record`,
  `window_joint_codes`, `strip_observations_from_records`), exact Born-NLL
  scoring (`strip_cross_entropy`/`strip_joint_kl`), `ComposedCarrier` with the
  W2-gated class manifest (`CarrierManifest` — the gate must run BEFORE any fit)
  and channel-level `do_on_seam`/`do_on_location`, and `fit_composed_carrier`
  (label-free; observations only — isolation contract).
- `marginals.py` — fit-free bunching functionals from two-block marginals of the
  stationary carrier law: `r_det_lag` (R_k) and `t3_triple` (T3). Record
  convention DECLARED: data-record-chain (D5↔K2 pin); attribution lags k ≥ 2.
- `pins.py` — structural pin callables (normalization, zero negative mass,
  fixed point ≤ 1e-9, seam-reduction TP, T-A Pauli-ablation R=1, unital-diagonal
  R=1, zero-seam exactness ≤ 1e-10) + `CarrierErrorAccounting` (`eps_log` =
  float64 round-off only; `B_carrier` = measured seam residuals, functional-
  indexed; two books, never merged).

## The leakage MCWF-on-MPS forward backend (ADR 0010, task 8c)

`mps_forward.py` is the **scalable forward carrier for the leakage / non-Pauli axis**
(ADR 0010 — a SEPARATE carrier from the composed-carrier arm above; leakage is not
DEM-reducible). It is the `quimb` MPS lift of the dense state-vector MCWF
(`sv_sampler.py` + `forward/kernels/sv_traj_d3.cu`): each shot is a pure qutrit
**Matrix-Product State** (`phys_dim=3`, torch backend on cuda, `complex128`,
snake/boustrophedon ordering), Wood-Gambetta leakage **Kraus-sampled** on the dim-3 leg,
stabilizers **Born-sampled + projected**, each per-stabilizer measurement truncated at
`max_bond=chi` with the discarded Schmidt weight tracked (`MpsTruncationLedger`, the
state-fidelity book — class (a); never merged with the d3-DM-certified LER/floor error
map of task 8e).

- `MpsLeakageForward.sample(spec, sched, chi)` → `(ShotSet, ledger)`: REUSES `SvSampler`
  for the within-cycle marshalling (the per-qutrit `[H?] LEAK [H?] LEAK X LEAK [H?] LEAK
  M Y` op stream incl. the **per-round transversal X/Y DD echoes** — C5, load-bearing),
  the WG `exp(L/4)` leak slice (CPTP-asserted — C1), the codestate `|m>_L` (`<S>`/`<L>`
  self-checked), and the ShotSet pack/header (byte-identical to the dense backend). The
  trajectory body is the exact MPS lift of `sv_traj_wc_kernel`, RNG draw order matched so
  a host uniform stream reproduces the dense engine at full χ.
- Pure-MPS positivity is structural (C2); coherence (`C_L`) is carried exactly by the
  amplitudes (C4); the only simplification is the bond truncation (C7/C8). Multi-site (≥3,
  non-contiguous) stabilizer `sqrt(E_s)` is applied via quimb `contract='nonlocal'` (the
  mode that compresses the resulting state bond at `max_bond=chi`). The within-cycle path
  REQUIRES a `sched` with interior streams attached (the r01-geometry + r10-interior split,
  model §1).

Self-validation (BUILD phase, NOT the full rung-1 cert — that is 8e):
`outputs/teacher_prereg/p7d_mps_forward_selfval.py` — C8 zero-truncation exactness
(snake-MPS codestate, gate+leak-sample, stabilizer measurement vs from-scratch dense — all
~1e-16) + C6 MCWF-exactness (ensemble `P(s)` vs exact dense DM). GPU-only; tiny systems
(a heavy full-9q DM job runs concurrently; the full-9q rung-1 certification is 8e).

### The batched-MPS sibling arm (OPT2, scaling line)

`batched_mps.py` is the **quimb-free batched op core** for the batch-shots lift of the
serial per-shot loop above (the OPT2 scaling line; prereg + registered gates:
`docs/twin_validation/batched_mps_backend_prereg.md`, "OPT2-1 DESIGN"). Every site tensor
carries a leading batch dim `[B, cap_{k-1}, 3, cap_k]` at ZERO-PADDED FIXED cap shapes
(`bond_caps`; uniform kernels — the Doi batch-shots pattern; our op stream is
shot-independent, divergence lives in operator VALUES only). Recompression routes per
split by cap arithmetic: batched reduced **QR** where no truncation is structurally
possible (exact grade: every split; discarded ≡ 0.0 literally), **Gram + batched-eigh**
otherwise (the OPT2-0 measured lever). The SERIAL arm (`mps_forward.py`) is the referee,
never modified; per-op ≤1e-12 equivalence gates live in `tests/test_batched_mps_ops.py`
(G-OP-1..7). The trajectory DRIVER (RunSpec→ShotSet seam) is OPT2-2, not in this module.

## The teacher output → decoder-input seam (ADR 0010)

`seam.py` is the **teacher's output contract** — the single host-side adaptor that turns the
leakage teacher's emitted `ShotSet` (the dense `sv_sampler` / MPS `mps_forward` carriers) into
the `(detection_events, obs_flips)` arrays the decoder substrate (`hardware/m4_decode`,
`decoder/`) and the Bayes floor (`audit/bayes_floor`) consume. The floor scores it and the
coming decoder/foil decodes it, so the fold convention lives in ONE place here. Graduated from
`outputs/teacher_prereg/p7_seam.py` (pre-reg §1.5 G2 — "the single most error-prone seam");
no GPU model-compute (stim/pymatching are the frozen evaluator tooling).

- **The fold (G2, `teacher_shots_to_events`).** The kernel buffer is, per shot, `R*n_stab` raw
  per-round ancilla-syndrome bits (LSB-first, round-major then stab-order) + a trailing
  `logical_flip` byte (`parity(terminal data) XOR m`). The detectors are formed as
  `det[:,0,:]=s[:,0,:]` (first round raw) and `det[:,r,:]=s[:,r,:]^s[:,r-1,:]` for r≥1 (interior
  round-to-round XOR; detector index `r*n_stab+j`). This is the SAME convention
  `audit.bayes_floor.sample_teacher_records` inlines on its GPU draw — `seam.py` is the
  canonical statement of it, exposed for packed-buffer / decoder consumers.
- **The matched-Pauli-DEM foil (G1, `build_matched_pauli_dem`).** The shipped Google d3 XZZX
  DEM's detectors fold in the TERMINAL per-data-qubit readout (verified on the RAW circuit:
  ALL 8 at r01, ALL 80 at r10 — `inspect_raw_detectors`), which the teacher does NOT emit. So
  the foil DEM is built over the teacher's EMITTED ancilla-syndrome detector space
  (`R*n_stab` detectors + the single logical observable), from the parsed real XZZX geometry
  (`xzzx_parser`), at a DEPOLARIZE budget matched to the WG leak rate, with LEAKAGE
  DELIBERATELY ABSENT (the foil — anti-circular, ledger invariant ii: built from the qubit
  circuit, never from a Pauli reduction of the leakage channel). `gap_off ≈ 0` is the
  falsifiable proof the seam + match are faithful.
- Executable spec: `tests/test_seam.py` — the ledger-(v) positive control (a planted single
  fault round-trips through the XOR fold to the hand-computed detectors; the matched foil
  decodes the zero-syndrome shot to observable 0; the MSB-first teeth prove the LSB convention
  is load-bearing) + the raw-circuit-detector control (the shipped detectors use terminal data).

Executable spec: `tests/test_carrier_seam_composition.py` (composed arm). Production seam-test
fits/runs are reviewer-gated and GPU-only (project rule); the tests there are
toy-scale pins and a clearly-labeled smoke fit.

**Boundaries.** Isolation contract absolute: the carrier consumes only
observations (`StripObservations`); teacher channels/parameters are
evaluator-side and never enter the fit path. Scalability beyond the seam-test
strip (the bulk engine, window fleets, d=5/d=7) is deferred ADR 0008 work — no
claim past the controlled seam-test scale issues from this module.
