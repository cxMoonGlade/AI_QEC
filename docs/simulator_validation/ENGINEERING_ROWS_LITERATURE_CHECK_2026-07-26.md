# Engineering differentiator rows checked against the literature

Date: 2026-07-26. Status: **all three rows OCCUPIED, and all three narrow residuals came back partially occupied
after forward citation. The positioning record's "What remains unoccupied" section is refuted in
full, and nothing survives it as a novelty claim.**

This record is deliberately separate from
`docs/simulator_validation/EXTERNAL_LANDSCAPE_AUDIT_2026-07-26.md` rather than an edit to it. The
audit is the document under test here, and the conclusion is that its central section is wrong;
keeping the finding in its own file means the correction can be reviewed before the audit is
rewritten.

Scope: positioning only. No carrier status, service status, metric, or faithfulness claim changes.

## Why this check was run

The audit's four "unoccupied" rows were established by surveying about nine already-cloned
codebases. Row 1 had already been refuted by external search (Varbanov et al. arXiv:2002.07119v1
run Surface-17 with leakage-prone qubits as three-level systems over multiple cycles). Rows 2 to 4
had never been checked against the literature at all. The audit carries its own warning on the
remainder of row 1 — "Neither has been checked against the literature. Do not restate this row as a
differentiator without doing so." — and that warning was never applied to rows 2, 3 and 4.

Method: ten agents. Two independent finders per row (academic literature; software, repositories and
documentation), each instructed to **refute** its row rather than confirm it and to translate the
row out of this project's internal vocabulary before searching. One adversarial verifier per row,
defaulting to "occupied" and required to name the exact section or file a human must open. One
completeness critic. Roughly 150 queries. The external search ran on an exhausted anonymous quota
for much of the survey; see the limitations section.

## Verdicts

| row | verdict | strongest occupant, with the locator to open |
|---|---|---|
| 2 — replayable time-correlated source process | **occupied** (high confidence) | Clader, Trout, Barnes, Schultz, Quiroz, Titum, *Impact of correlations and heavy-tails on quantum error correction*, arXiv:2101.11631v2 / Phys. Rev. A **103**, 052428 (2021), DOI `10.1103/PhysRevA.103.052428`, Section III |
| 3 — Record as a versioned, provenance-bound artifact with fail-closed truncation | **occupied** (high confidence) | TeNPy at `main` = `7f1d95560645` (2026-07-22): `tenpy/algorithms/algorithm.py:493` in `TimeEvolutionAlgorithm.evolve` |
| 4 — evaluator/certify boundary with negative controls | **occupied** (high confidence) | `qecsim` at `24d6b8a320b292461b66b68fe4fba40c9ddc2257`: `src/qecsim/cli.py:247-250` and `:318-321`, `src/qecsim/model.py:136-157`, `tests/core/test_model.py:14-32` |

### Row 2

Clader et al. §III defines the rotation angle at circuit time location `k` for qubit `l` as an
explicit ARMA process, `theta_k^(l) = sum_i a_i theta_{k-i}^(l) + sum_j b_j x_{k-j}^(l)`, with
moving-average weights `b_j = N exp(-ln(2) j / T_h)` and the statement that "each gate in the
circuit [takes] a single unit of time, so the parameter `j` corresponds exactly to the circuit
depth". It then simulates "three rounds of faulty syndrome extraction with errors inserted after
every location where a gate exists" on a distance-3 rotated surface code, with decoding. The paper
sweeps the moving-average half-life against the syndrome cycle and reports that "the slope reduction
occurs as the half-life approaches the syndrome cycle" — the source-process correlation time tuned
against the QEC round, which is the row's stated novelty, published in 2021.

Read via ar5iv HTML, not the published PRA. The simulator is not named and there is no
code-availability statement.

Second occupant, closer to the row's "process drives gate **parameters**" reading:
arXiv:2507.08713v1 §II.3 and §III.2, which generates `1/f` traces by Fourier filtering and drives
the Larmor frequency and exchange coupling, then runs the distance-3 rotated surface code and its
XZZX variant with syndrome extraction repeated five hundred times and MWPM decoding. Read as HTML;
its author list was not verified.

Third occupant, at source level: `corrqec2` at `b71e1c280778571f6c393600bb937c08f85018d3`,
`src/corrqec2/noisemodels/storm_model.py` — `StormModel` builds a two-state Markov transfer matrix
and `_sample_storm_hmm_batch` steps it forward over rounds, emitting a per-qubit per-round error
array consumed by the sampler, which returns detection events and observable flips. A genuine hidden
Markov source process in time, plus syndrome extraction, plus decoding, in one simulator. Related
paper: Kam, Gicev, Modi, Southwell, Usman, arXiv:2410.23779, Quantum Sci. Technol. **10**, 035060
(2025), DOI `10.1088/2058-9565/adebab`.

### Row 3, and the determination made in this repository

The completeness critic named one question as the only reading that could still move a row: does
TeNPy's truncation check **gate what a caller consumes**, or fire only after the algorithm has
returned and persisted its result? If it gates, row 3's last residual is dead.

That was settled here by reading the source at `main` = `7f1d95560645`. There are three call sites of
`tenpy.tools.misc.consistency_check`, at three different placements:

| call site | checked quantity | default threshold | when it fires |
|---|---|---|---|
| `algorithms/algorithm.py:103`, `Algorithm.__init__` | `max_N_sites_per_ring` | 18 | at construction, before any computation |
| `algorithms/algorithm.py:493`, `TimeEvolutionAlgorithm.evolve` | `max_trunc_err` | 0.01 | **inside the loop**, after every `evolve_step(dt)` |
| `algorithms/mps_common.py:810`, `IterativeSweeps.run` | `max_trunc_err` | 1e-4 | after the sweep loop and after `post_run_cleanup()`, before `return result` |

The middle one settles it:

```python
for _ in range(N_steps):
    trunc_err += self.evolve_step(dt)
    consistency_check(trunc_err.eps, self.options, 'max_trunc_err', 0.01,
                      'Maximum truncation error (``max_trunc_err``) exceeded.')
```

Accumulated truncation error exceeding a declared budget aborts the evolution mid-run.
`consistency_check` raises `TenpyInconsistencyError` by default; the threshold must be explicitly set
to `None` to downgrade to a `TenpyInconsistencyWarning`. Introduced in `doc/changelog/v0.99.0.rst`,
2024-03-19.

One distinction worth keeping: the third call site gates the **return value**, not the state.
`IterativeSweeps` mutates `psi` in place and the caller owns `psi`, so raising there withholds
`result` while leaving the truncated state in the caller's hands. That is a real difference from
gating the computation, and it is the only part of row 3's fail-closed claim that is not directly
occupied — but the `evolve` site occupies it, so the row does not survive on that distinction.

### Row 4

`qecsim` runs `code.validate()` under an `# INPUT` comment immediately before `app.run`, in both the
`run` and `run-ftp` entry points. `StabilizerCode.validate` performs three symplectic checks, each
raising `QecsimError`. `tests/core/test_model.py:14-32` constructs three deliberately corrupted
codes and asserts the exact failure message of each. That is a precondition gate plus deliberate
corruption controls, which is what row 4 claims has no counterpart.

`qecsim` is already cloned in this repository at `external/baselines/qecsim/`, at exactly the
commit cited above. The audit surveyed it and dismissed it on an unrelated taxonomy point.

## Checkable errors in the rows, about code this repository had already cloned

These are the sharpest part of the result, because none of them required external search.

- Row 2 asserts qiskit-aer's `NoiseModel` "structurally cannot" express a correlated timeline.
  Contradicted by Qiskit/qiskit-aer PR #2413, which implements it as a window-chunking wrapper and
  returns the drift trajectory in result metadata.
- Row 4 asserts `tn_qsim` lacks naive-reference cross-checking. `tests/test_mps.py` in the clone at
  `ef5f0016bef4653e037c913e925281a4d2badee5` consists of nothing else.
- Row 4 dismisses `qecsim` on a Carrier-taxonomy point while `qecsim` occupies the verification
  architecture the row actually claims.
- Rows 2 and 3 cite OQuPy, OpenQMC and ITensorMPS at no ref or commit, violating this repository's
  own external-citation rule in `CLAUDE.md`. The ITensorMPS negative-probability sub-claim remains
  unverified by anyone.

## Second round: the three residuals, put through forward citation

Run after the above, with the search quota repaired. Workflow `wf_512fa03d-6e0`, ten agents:
per residual a forward-citation traversal via Semantic Scholar and OpenAlex, a sweep of the
communities the first round never touched, and an adversarial verifier required to report how many
citing works were screened across which seeds — with `search_inconclusive` mandated instead of
"survives" when it could not.

**All three residuals came back `partially_occupied`. None supports a novelty claim.**

| residual | verdict | strongest occupant | screening depth |
|---|---|---|---|
| R2 — first-class time-correlated noise source object plus measurement in one run | partially occupied (high) | `corrqec2` at ref `v1-arxiv` = `b71e1c280778571f6c393600bb937c08f85018d3`: `src/corrqec2/noisemodels/storm_model.py` (`StormModel.__init__`, `self._T = [[1-a,a],[b,1-b]]`) and `src/corrqec2/simulation/simulator.py` (`CircuitSimulator.simulate_batch` returning `get_detector_flips()` and `get_observable_flips()`). Second, missed by both finders: `leakysim` 0.5.0 on PyPI, "an implementation of Google's Pauli+ simulator", `inmzhang/leaky` at `035a9881fe5cd6a86c4140d8e7a00e8295df8b11` — `src/leaky/core/simulator.h` carries `LeakageStatus leakage_status` and a dedicated `std::mt19937_64 leakage_rng` | 1,744 citing works screened, which produced nothing; the row was settled by repository probing instead |
| R3 — self-describing versioned record refusing unknown versions | partially occupied (medium) | PECOS at `fa974197f0debd6478343c760af47f6faa4f04d2`, `crates/pecos-phir-json/src/common.rs:16-36` — `detect_version` reads `version` from inside the payload and returns `Err(PecosError::Input("Unsupported PHIR-JSON version"))` on anything unknown. That is the mechanism, applied to the program IR rather than to the record | 5,917 citing works across 8 seeds, plus an independent 1,799-work pass |
| R4 — permutation/surrogate null on a record as a harness self-check | partially occupied (high) | IceCube SkyLLH at `074426a81d4d4b79230553765e6c584149de12db`, `skyllh/core/scrambling.py` — `DataScramblingMethod` (abstract, line 19), `UniformRAScramblingMethod.scramble` randomising at line 120, driven by `DataScrambler` at line 223: a randomisation null on a detector record as a first-class pluggable harness component. Also gravitational-wave time slides, DOI `10.1088/0264-9381/27/1/015005` | 5,486 citing works fully enumerated across Theiler 1992 (n=3,786), Adebayo 2018 (n=609) and Stim (n=387 / n=704) |

Three verification catches worth keeping, because each was a finder error that would have changed a
verdict:

- The R2 forward-citation finder reported `corrqec2` as 404 and substituted `corrqec`, a different
  repository for a different paper, then called its `base.py` "a 15-line stub" and nearly saved the
  row on that basis. `corrqec2`'s default branch is `v1-arxiv`, not `main`; requesting `main` 404s.
  Its `base_noise_model.py` is 6797 bytes and a genuine ABC.
- The R2 sweep finder dismissed `jaq-lab/qec-control-gym` because grepping for `ornstein|uhlenbeck`
  returned nothing. The grep is correct and the mechanism is Ornstein-Uhlenbeck anyway:
  `qec_control.py:52-58` is the exact OU Euler update with user-configurable correlation times. A
  vocabulary lens lost a hit to vocabulary.
- The R4 sweep finder called `shard`'s negative control a Theiler-class surrogate. Line 338 is
  `S_iid = (rng.uniform(size=(50000, 22)) < rate)` — a fresh Bernoulli stream at a matched rate, not
  anything derived from the record. A surrogate is by construction generated *from* the data.

The R3 verifier also read the Google Zenodo archives' ZIP central directories over HTTP range
requests rather than downloading gigabytes, and found a machine-readable `metadata.json` in the 2024
deposit that neither finder had found — the sharpest available test of its own row. The 2023 deposit
(6804040) has 2,095 entries and zero matching `schema|version|manifest|.json|meta`; its
`properties.yml` carries `type`, basis, rounds, distance and `circuit_detectors` but no format
version, and its README states the shot width is supplied out of band, which is the direct
consequence of headerlessness.

## What may be stated, and in what words

R2 should be dropped from any positioning document outright. Every clause is individually occupied at
a named commit; what is left is one `pip publish` and one `rng=` parameter away from false, and turns
on two adjectives — "installable" and "general-purpose" — that were never operationalised.

R3 and R4 are statable only as **design rationale**, never near the word "first":

> **R3.** QEC record tooling is uniformly headerless — Stim's raw formats, sinter's CSV, Deltakit's
> b8/01/c64, decoder-bench's HDF5, FlamingPy, and both Google Zenodo deposits all ship records with
> no in-file schema identity. We version and gate ours instead. The mechanism is ordinary (Braket's
> `braketSchemaHeader`, Qiskit QPY, PECOS's PHIR-JSON loader); the departure is that we apply it to
> the record.

> **R4.** We gate record emission on a surrogate null. This is standard in adjacent detector sciences
> (IceCube SkyLLH's `DataScrambler`; gravitational-wave time slides) and in quantum software testing
> (Huang & Martonosi, ISCA 2019); QEC resamples its detector record only for uncertainty, never to
> construct a null.

Both are engineering statements about packaging. Neither is evidence that anything about the
simulator's physics or capability is new.

## What this check did not do

Recorded so the negative results are not read as stronger than they are.

- **Authenticated GitHub global code search was unavailable to every agent in both rounds**, and it
  is the single largest hole, for all three rows. Unauthenticated `/search/code` returns 401,
  grep.app is behind a checkpoint, and Sourcegraph's public index returns false negatives. Every
  real hit in either round came from reading repositories, not from citation graphs.
- **Patent-office full-text and CPC-class search** was never run in either round; only ad-hoc
  keyword passes. G06N10/70 crossed with format-version and noise-model claims is the obvious query.
- **Non-English literature and dissertation repositories** (CNKI, J-STAGE, theses.fr, DissOnline)
  were never searched.
- **Closed and industrial stacks** are structurally invisible: Riverlane's server side behind
  `deltakit.explorer.Client`, the Google/IBM/Quantinuum/PsiQuantum internal harnesses, and QC
  Design's Plaquette, now absent from both PyPI and GitHub.
- **Named documents still unread**: arXiv:2607.08767 body and TeX source, whose XPauli "environment
  sector" is the one architecture that could still take R2 outright; PECOS's error-generator
  internals and its `feat/experimental` (`34cf40fd4c`) and `more-py-to-rs` (`538ebb50f9`) branches;
  cudaq-qec 0.6.0's noise API; three of the five Google 2024 Zenodo archives; DOI
  `10.1049/qtc2.70037` (403).
- **Full-text sweep of the QEC-touching Stim citers** was not run — roughly 360 works were screened
  on titles and abstracts only, never on strings like "shuffled shots" or "permuted rounds".
- **Quota, first round only.** The first round ran anonymously and exhausted its free quota
  mid-survey; two finders fell back to another tool. An API key is now configured and the second
  round ran with quota.
- **Evidence quality.** One finder never opened a PDF. Clader et al. §III was read via ar5iv, not
  the published PRA. arXiv:2507.08713v1 was read as HTML with an unverified author list.
  arXiv:2511.09491 and arXiv:2512.07815 rest on abstracts. arXiv:2603.05474, the formalism paper
  `corrqec2` implements, was never opened. Huo & Li, New J. Phys. **19** (2017),
  DOI `10.1088/1367-2630/aa916e`, rests on the IOP landing page and its article number was never
  determined.
- **Communities never searched.** The Julia QEC ecosystem entirely — `QuantumClifford.jl` appears in
  none of the queries despite this repository already depending on Julia for ITensorMPS. Classical
  FEC frameworks were name-checked but never opened; AFF3CT is a plausible occupant of row 2's whole
  conjunction. JOSS was never searched as a venue. Patents were never searched at all.
- **Vocabulary never tried.** Filter-function formalism, noise spectroscopy, Kubo-Anderson process,
  sample-and-hold, quasi-static disorder ensemble (row 2); schema-registry and data-contract
  vocabulary, NeXus application definitions and `nxvalidate` (row 3); lattice-QCD run-time
  self-validation — reversibility checks, Gauss-law violation gates, solver-residual tolerance
  gates (row 4). One probe in the last of these immediately returned candidate material.

## Recommendation

1. **Delete rows 2 and 4** from the audit's "What remains unoccupied" section.
2. **Delete row 3** as well. Its last residual was the TeNPy question, and the source read above
   closes it. If any part is kept, it must be rewritten as an explicit composition claim naming the
   ground it stands on — Stim's record formats and `analyze_errors` aborts, QCSchema's
   `schema_name`/`schema_version`/`provenance`, TeNPy's `max_trunc_err`, Model Cards and MODA for
   scope declaration — and never as a statement that these have no counterpart.
3. **Drop residual R2 outright; keep R3 and R4 only as design rationale**, in the exact words given
   above. All three came back `partially_occupied` after forward citation, and none of them is a
   capability claim.
4. **Forward-citation traversal is now run** and is recorded above with screening counts. The method
   is worth keeping as the standing requirement for any future absence claim: a negative that cannot
   state which seeds were traversed and how many citing works were screened is not a negative.
5. **Get authenticated GitHub code search working before the next round.** It is the one hole that
   affects every row, and both rounds found their real hits by reading repositories rather than by
   following citations — which is exactly the capability that search would industrialise.

## Provenance

Round one: workflow `wf_c5b0873b-cd6`, 10 agents, 0 errors, ~1.19M subagent tokens, 345 tool calls,
1494 s. Round two: workflow `wf_512fa03d-6e0`, 10 agents, 0 errors, ~1.30M subagent tokens,
442 tool calls, 1633 s. Per-agent returns in that run's `journal.jsonl`. The TeNPy determination in the
row-3 section was made in this repository by reading the fetched sources directly, not by an agent.
