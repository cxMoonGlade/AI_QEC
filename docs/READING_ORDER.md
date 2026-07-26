# Reading order — what matters at the current stage

Reconciled 2026-07-26 against `7301632`.
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

1. **`docs/simulator_validation/ENGINEERING_ROWS_LITERATURE_CHECK_2026-07-26.md`** — read this
   **before** the landscape audit below, because it refutes that audit's central section. All three
   surviving engineering differentiator rows are occupied: row 2 by Clader et al. PRA 103, 052428
   (2021) §III, row 3 by TeNPy `7f1d95560645` `algorithms/algorithm.py:493` (a truncation-budget
   abort inside the evolution loop), row 4 by `qecsim` `24d6b8a` `cli.py:247-250` plus
   `tests/core/test_model.py:14-32`. With row 1 already refuted, the audit's "What remains
   unoccupied" section has nothing left in it. Three of the rows also contain checkable errors about
   code already cloned under `external/`. Read before writing any scope, novelty, or completion
   sentence.
2. **`docs/simulator_validation/EXTERNAL_LANDSCAPE_AUDIT_2026-07-26.md`** — still the record of what
   was surveyed and of what is already solved elsewhere, which remains useful. Its "What remains
   unoccupied" section is superseded by the check above and is pending rewrite. `stim` supplies
   geometry, schedule and detector fold at any distance, and the nearest published work is listed
   with locators.
3. **`docs/simulator_validation/LEAKAGE_FRAME_LITERATURE_CLOSURE_2026-07-26.md`** — closes the
   current leakage-conditioned frame question at documentation scope. It distinguishes physical
   parity-Record content, a one-bit marginal relabeling, and an unestablished exact
   trajectory-conditioned frame. Its source-only companions are the Ghosh, Bultink, Varbanov, and
   Miyamura notes in `docs/papers/reading_notes/`.
4. **`docs/simulator_validation/2002.07119-claim-audit.md`** — project application of Varbanov v1.
   Read it for the individual-defect/supercheck distinction, Appendix-G ancilla bookkeeping analog,
   Appendix-B schedule-scoped coherence null, and the printed D11-D13 algebra defects.
5. **`docs/simulator_validation/HANDOFF_MUTATION_SCOPE_AND_BASELINE_LEGS_2026-07-25.md`** — open
   items 2 through 7 are still open. Item 1 is discharged; its follow-on was deliberately reverted
   rather than fixed, because the mutation layer is being retired.
6. **`docs/service_status.json`**, the `restricted_axis1_1d_mps` note and `excluded_surfaces` — the
   claim boundary. It answers most scope questions outright.

## Recently landed — read before touching the same surface

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
  identifiability remains project inference rather than a literature theorem. The rebuilt current
  corpus contains 29 admitted notes and 348 retrievable `paper_fact` records.

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
3. **Only then d5 non-Pauli.** The wall is verified and fundamental: `sv_traj_d3_wc` is specialized
   to 9 data qutrits, and 3**25 state-vector amplitudes is unreachable regardless — arXiv:2308.08186
   records that state-vector simulation needs "a few petabytes of memory for 30 qutrit systems".
   The route is a 2D ansatz (`carrier/peps`, `carrier/pepo`, neither in any coverage registry), which
   is month-scale work and must not precede items 1 and 2.

Explicitly not doing: the withdrawn heralding claim, and any PEPS work before 1 and 2 land.

## Open decisions

- Which `quantumsim` ref matches arXiv:2002.07119. Five carry the device model; none is confirmed.
- Whether and how to bound the declared leaked-block echo representative against an independent
  device model. The present literature pass documents the convention but does not certify it.
- What replaces the retired mutation layer in the release evidence order.
- Whether to add `hw` to the canonical `ecs` sync so the Pauli leg can report a decoded logical
  error rate instead of a raw observable-flip rate. Everything else for that is already in place.

## Retained external material

The leakage PDFs are now fully read and routed through the closure packet above. Repositories cloned
under `external/reference_repos/` remain pinned at the refs at which they were inspected:
`qutrits` at `fe24c42`, `restless-simulator` at `92e8a62`, `surface-code-simulator` at `f06123e`,
`Located-decoder-for-Rydberg-decay` at `1bf10b6`.

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

Left in the scratchpad and expendable: roughly a hundred one-off probes. Two files are deliberately
not committed -- `gen_external_code_map.py` and `EXTERNAL_CODE_MAP.md`, written by a subagent and
duplicating the committed `tools/gen_external_tn_code_map.py`.

## Maintenance

Update this file when the stage changes, when a read-first entry stops mattering, or when something
lands. Its value is that it is short and current; adding to it without removing is how it dies.
