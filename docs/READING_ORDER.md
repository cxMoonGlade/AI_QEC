# Reading order — what matters at the current stage

Reconciled 2026-07-29 against `736683c`.
Verify with `python tools/check_reading_order.py`.

`CLAUDE.md` holds the rules that always bind and a routing table for which surface owns which
question. Those are static. **This file holds the part that changes**: what is worth reading right
now, what is in flight, and what has been superseded so you do not read it. If a statement here
conflicts with `docs/SIMULATOR.md`, `docs/SIMULATOR.md` wins.

Keep it short. A long reading list is not read, which is the failure this file exists to fix.

## Current stage

Producing a product that can run a real code, on a one-month clock, accepted as **uncertified**.
Mutation testing is retired; verification is unit tests plus the coverage gate.

## Read first, in this order

1. **`docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_LITERATURE_CLOSURE_2026-07-29.md` and its matching preregistration** —
   freezes the pending `2 x w`, `w=3,5,7`, persistent-memory benchmark: native
   bond-32 plain Quimb versus Clifford-frame/tree-routed GCAPEPS, bounded dense
   complete-state faithfulness, BLP trace-distance backflow, SDIM/Stim frame
   corroboration, positive local truncation evidence, and layered per-case and
   per-substep timing.  It is not a QEC Record, generic PEPS certificate,
   monotonic-entanglement theorem, or universal efficiency claim.  Its primary
   witness audit starts at
   `docs/simulator_validation/BLP_0908_0238V2_NONMARKOVIAN_WITNESS_AUDIT_2026-07-29.md`;
   the closure routes the remaining collision-model and sign audits.
2. **`docs/simulator_validation/GCAPEPS_N8_R3_DUAL_CANDIDATE_DIFFERENTIAL_LITERATURE_CLOSURE_2026-07-29.md` and its matching preregistration** —
   freezes the pending n=8, active-rank-3 plain-Quimb-versus-GCAPEPS candidate state-action
   differential, one untimed NumPy exact-small anchor, and the fixture-only timing protocol. There
   is no target result yet; neither candidate is ground truth, and no Record, generic faithfulness,
   truncation, scaling, or general-efficiency claim is authorized.
3. **`docs/simulator_validation/PEPS_D5_COMPLETE_STATE_FIDELITY_RESULTS_2026-07-26.md`** —
   the first direct 25-qubit 5-by-5 PEPS result. Quimb and Pepsy both exceed
   `F=0.9998` at `D=2` and `F=0.9999995` at `D=4`; both are
   resource-unavailable at `D=8,16`, so the registered five-point verdict is
   `inconclusive_partial`. This is a high-fidelity coherent pure-state result,
   not leakage, Kraus, a QEC Record, or a scaling claim.
4. **`docs/simulator_validation/CUDAQ_PECOS_XZZX_D7_REPRODUCTION_2026-07-26.md`** — read this
   **before** the capability record below. An independent rerun finds that **neither runtime
   produces a usable XZZX d7 multi-round non-Pauli Record**: both execute, and both emit Records
   dominated by bond truncation. The capability record's PECOS "YES" is wrong; its CUDA-Q "NO" is
   right in substance and wrong in its reason. Contains the controls that decide it — a noiseless
   injection control, a stabilizer reference, and a p→0 control on the same code path — plus the
   d3 exactness threshold that validates the probe.
5. **`docs/simulator_validation/CUDAQ_PECOS_XZZX_D7_CAPABILITY_2026-07-26.md`** — the original
   environment-and-execution check prompted by the failed broad differentiator claim. CUDA-Q
   completes an ideal d7/r2 XZZX Record but its full-data two-Kraus target times out or
   native-crashes; PECOS natively builds d7/r7 checkerboard XZZX and executes coherent non-Pauli
   MPS Records, but its scalable MPS has no dissipative Kraus binding. Read its exact boundary
   before saying either "existing products already do the whole leakage job" or "nothing else can
   do XZZX d7 non-Pauli multi-round."
6. **`docs/simulator_validation/PEPS_PEPO_LITERATURE_LIBRARY_LANDSCAPE_2026-07-26.md`** — the
   AnySearch-backed PEPS/PEPO literature and software audit. `pepsy` is the closest adjacent
   product but does not compose its PEPS and leakage-trajectory paths; TNQS is the best inspected
   qutrit-PEPS adapter base; YASTN is the independent finite-PEPS comparator. Schuch supplies an
   exact worst-case complexity boundary, not a d7 impossibility or resource estimate.
7. **`docs/simulator_validation/ENGINEERING_ROWS_LITERATURE_CHECK_2026-07-26.md`** — read this
   **before** the landscape audit below, because it refutes that audit's central section. All three
   surviving engineering differentiator rows are occupied: row 2 by Clader et al. PRA 103, 052428
   (2021) §III, row 3 by TeNPy `7f1d95560645` `algorithms/algorithm.py:493` (a truncation-budget
   abort inside the evolution loop), row 4 by `qecsim` `24d6b8a` `cli.py:247-250` plus
   `tests/core/test_model.py:14-32`. With row 1 already refuted, the audit's "What remains
   unoccupied" section has nothing left in it. Three of the rows also contain checkable errors about
   code already cloned under `external/`. Read before writing any scope, novelty, or completion
   sentence.
8. **`docs/simulator_validation/EXTERNAL_LANDSCAPE_AUDIT_2026-07-26.md`** — still the record of what
   was surveyed and of what is already solved elsewhere, which remains useful. Its "What remains
   unoccupied" section is superseded by the check above and is pending rewrite. `stim` supplies
   geometry, schedule and detector fold at any distance, and the nearest published work is listed
   with locators.
9. **`docs/simulator_validation/LEAKAGE_FRAME_LITERATURE_CLOSURE_2026-07-26.md`** — closes the
   current leakage-conditioned frame question at documentation scope. It distinguishes physical
   parity-Record content, a one-bit marginal relabeling, and an unestablished exact
   trajectory-conditioned frame. Its source-only companions are the Ghosh, Bultink, Varbanov, and
   Miyamura notes in `docs/papers/reading_notes/`.
10. **`docs/simulator_validation/2002.07119-claim-audit.md`** — project application of Varbanov v1.
   Read it for the individual-defect/supercheck distinction, Appendix-G ancilla bookkeeping analog,
   Appendix-B schedule-scoped coherence null, and the printed D11-D13 algebra defects.
11. **`docs/simulator_validation/HANDOFF_MUTATION_SCOPE_AND_BASELINE_LEGS_2026-07-25.md`** — open
   items 2 through 7 are still open. Item 1 is discharged; its follow-on was deliberately reverted
   rather than fixed, because the mutation layer is being retired.
12. **`docs/service_status.json`**, the `restricted_axis1_1d_mps` note and `excluded_surfaces` — the
   claim boundary. It answers most scope questions outright.

## Recently landed — read before touching the same surface

- **PEPS d5 complete-state execution** (`a95ba0f` run). Both commit-bound
  candidates materialize every d5 amplitude at `D<=4`; `D=2` is already
  useful and `D=4` is near unity. Higher bonds fail the registered resource
  gate, so this lands as bounded pure-state evidence rather than a complete
  five-point pass. The terminal artifact is corruption-sensitive and
  independently hash-checked.
- **PEPS/PEPO landscape and Schuch admission**. The bounded AnySearch plus
  official-source audit found no integrated finite-qutrit PEPS/PEPO leakage Record engine, but it
  did find much closer prior product surfaces than the earlier notes recorded. The Schuch
  version-of-record note is independently reviewed and admitted; its conclusion concerns the
  paper-defined exact PEPS scalar primitives and general contraction, not every approximation or
  physical instance.
- **External d7 capability probe** (current worktree). Two isolated installed-state environments,
  frozen XZZX fixtures, workers, locks, and corruption tests now separate three questions that were
  previously conflated: ideal Record execution, coherent non-Pauli execution, and actual
  dissipative Kraus execution. None is qutrit leakage or a finite-bond faithfulness result.
- **Transversal-echo frame repair** (`0553a55`), `src/error_coupling_simulator/carrier/within_cycle.py`. The emitted observable carried a
  deterministic `(R-1)*w mod 2` echo sign on top of the logical-flip bit and was inverted at even
  round counts. The parity is derived from the emitted ops and cross-checked by measuring the frame
  on the noiseless codestate, refusing a non-deterministic frame — the construction the exact
  density-matrix leg already used. Reproducers: `scripts/within_cycle_echo_parity_check.py`,
  `scripts/within_cycle_echo_trajectory_frame_probe.py`.
- **Known residual**: the correction is exact only on a leakage-free reference. Under leakage the
  frame is trajectory-dependent, and the deviation is entirely leakage-conditioned
  (`Y^dag Z Y = -Z + 2|2><2|`). That residual is declared noise reaching the record, not a
  bookkeeping error. The literature closure now grounds that semantics: divide out only the
  deterministic leakage-free sign, retain the residual as physical Record content, and do not call
  it an exactly reconstructed frame. It remains unbounded, and the two legs share the leaked-inert
  convention by design so they cannot referee each other on it.
- **Leakage source reset closed for this question**: four full-text, source-located notes now cover
  single-check paralysis, physical data echo and temporal syndromes, Surface-17
  gauge/supercheck/HMM behavior, and direct heralded leakage measurement. Exact frame
  identifiability remains project inference rather than a literature theorem. With the independent
  Schuch source review, the rebuilt current corpus contains 30 admitted notes and 360 retrievable
  `paper_fact` records.

## Superseded — do not act on these

- The mutation-gate scope work and its adjudication issues under `.scratch/mutation-gate-adjudication/`.
  Issue 04 is `wontfix`; the fix was written, validated, and reverted.
- Any claim that the transversal echo converting leakage occupancy into detector signal is novel.
  Withdrawn: arXiv:1905.12731 explicitly attributes the repeated-ZZ leakage pattern to the physical
  data echo flipping the effective stabilizer, with arXiv:1306.0925 supplying the preceding
  phase/paralysis mechanism.
- Any argument that a one-half individual defect marginal makes the complete Record
  unobservable. The XOR relabeling symmetry is only a one-bit marginal statement; temporal and
  supercheck products can still carry information.
- Any statement that "no external precedent exists" derived from local retrieval alone. Local
  absence is not a gap; see the rule in `CLAUDE.md`.

## Next, in this order

1. **Done** — both legs are packaged as `scripts/run_real_code_records.py`. `--leg pauli` runs a
   Stim-generated rotated surface code at any distance through our own `StimCircuitSource` and
   `Simulator`, with `shortest_graphlike_error` as an executable distance falsifier; `--leg analog`
   runs the real d3 XZZX patch through the within-cycle carrier under a registered qutrit leakage
   preset. Next on this line is a decoder for the Pauli leg, since every rate it reports is
   undecoded — **blocked on one decision, not on code**. `frontend/decoder.py` already implements
   `decode_dem` against pymatching 2.4.0 with a frozen wheel sha256 that matches `uv.lock`, and
   `pyproject.toml` declares it as the `hw` extra. But `scripts/sync_core_environment.py` hardcodes
   `--extra cuda-extension gpu-cu130 test` and omits `hw`, matching the standing rule that the
   default record path is decoder-free; pymatching is installed in neither `ecs` nor `aiqec`.
   Turning the decoder on means amending the canonical environment contract.
2. **Done, and smaller than advertised** — `scripts/mps_accuracy_versus_chi.py`. The curve exists:
   at n=4, noiseless, against the registered dense Born oracle, `chi` 1/2/4 gives
   max|dp| 7.5e-1 / 2.46e-1 / 1.33e-15, the exact bond certifying PASS against the 1e-8 gate.
   Reported discarded weight over-predicts the record error (0.5 discarded, 0.246 actual), so it is
   an upper proxy and not the error.

   I wrote the n<=8 premise here from `_RECORD_EVIDENCE_QUBIT_CAP = 8` without running it, and
   three parts of it were wrong. Measured instead: the dense oracle loses
   `full_positive_duration_coverage` at n>=6 (the one-qubit-gate layer is dropped once it holds
   three or more simultaneous gates; serializing exposes a stricter rule, one selected row per
   (active, idle) pair, and scores worse); exact branch enumeration under noise reaches n=2 at the
   default 4096 branch cap, needs 65536 at n=3, and exceeds that at n=4; and the noisy exact-bond
   residual is 1.1e-3 against a 1e-8 gate, which the noiseless 1.3e-15 control identifies as the
   noise finite step, not a carrier defect. That floor cannot be refined away --
   `microstep_count=2` already blows the branch cap at n=2, because every collapse term splits
   every branch once per Kraus operator per substep.

   Next on this line, if it is worth it: a custom selection plan to restore coverage past n=4.
   That is a real piece of work, not a parameter change.
3. **Next: a small complete-Record qutrit PEPS bridge, not d7.** The pure-state d5 question is now
   answered positively at `D<=4`, but none of that exercises Kraus, leakage, reset, or a Record.
   TNQS remains the first qutrit adapter candidate; Pepsy/Quimb are now measured pure-state
   references rather than hypothetical adjacent products. Freeze a d3 circuit with dense qutrit
   truth; compare raw branch mass, post-reset state, detector/observable bits, full Record TV, and
   LER while sweeping state and boundary bonds independently. Only a passing
   corruption-sensitive bridge permits a d5 Record experiment, followed by a profile-based d7
   decision.

Explicitly not doing: the withdrawn heralding claim, an unrestricted exact/scalable PEPS claim, or
a direct d7 implementation before the small complete-Record bridge.

## Open decisions

- Which `quantumsim` ref matches arXiv:2002.07119. Five carry the device model; none is confirmed.
- Whether and how to bound the declared leaked-block echo representative against an independent
  device model. The present literature pass documents the convention but does not certify it.
- What replaces the retired mutation layer in the release evidence order.
- Whether to add `hw` to the canonical `ecs` sync so the Pauli leg can report a decoded logical
  error rate instead of a raw observable-flip rate. Everything else for that is already in place.
- Whether the measured pure-state d5 success is enough to prioritize the repository-owned d3
  qutrit/Kraus Record bridge over the current product-facing work.

## Retained external material

The leakage PDFs are now fully read and routed through the closure packet above. Repositories cloned
under `external/reference_repos/` remain pinned at the refs at which they were inspected:
`qutrits` at `fe24c42`, `restless-simulator` at `92e8a62`, `surface-code-simulator` at `f06123e`,
`Located-decoder-for-Rydberg-decay` at `1bf10b6`.

The PEPS execution baselines under `external/baselines/` are full, non-shallow, pristine clones:
Pepsy at `27cb956e`, Quimb at `3c89529f`, TensorNetworkQuantumSimulator.jl at `b5d40898`, and YASTN
at `595bd802`. Only Pepsy and Quimb expose an admitted bounded route to the required global d5
`complex128` vector.

The generated `docs/external_baselines/EXTERNAL_CODE_MAP.md` is the complete structural first-hop
inventory for all 51 Git clones under `external/`; it records exact commits, clone modes, recognized
suffix profiles, manifests, code-bearing roots, lexical entry candidates, tests, examples, and
documentation. The curated `docs/external_baselines/TENSOR_NETWORK_CODE_MAP.md` is the deeper
semantic route for the seven MPS/PEPS implementations relevant here. Neither map is scientific
evidence.

`quantumsim` is the simulator arXiv:2002.07119 used, but **not at the ref we cloned**: its default
`292fce9` has no `quantumsim/models/transmons.py` at all. Five of its 34 remote refs do —
`origin/circuit_classes`, `origin/enh/compiler_refactor`, `origin/enh/cphase_netzero`,
`origin/enh/naming`, `origin/feature/circuit_plotting`. Which one matches the paper is undetermined;
`origin/enh/cphase_netzero` is the obvious first candidate because the paper's CZ is the Net-Zero
implementation. Do not cite "quantumsim" for that paper without naming a ref.

## Live only in the session scratchpad

The load-bearing ones are promoted: both record legs into `scripts/run_real_code_records.py`, and
the qiskit-aer MPS non-Pauli prototype into
`scripts/external_baselines/aer_mps_nonpauli_record_prototype.py` plus
`scripts/external_baselines/emit_stim_circuit_json.py`, headed with the fact that its numbers were
never independently reproduced.

Left in the scratchpad and expendable: roughly a hundred one-off probes. The earlier scratch
codemap drafts are superseded by the committed `tools/gen_external_code_map.py` complete inventory
and `tools/gen_external_tn_code_map.py` curated tensor-network map.

## Maintenance

Update this file when the stage changes, when a read-first entry stops mattering, or when something
lands. Its value is that it is short and current; adding to it without removing is how it dies.
