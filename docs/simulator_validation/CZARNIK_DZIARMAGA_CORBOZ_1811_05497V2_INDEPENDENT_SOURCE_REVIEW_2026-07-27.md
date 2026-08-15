# Independent source-only admission review — Czarnik, Dziarmaga, and Corboz, arXiv:1811.05497v2

Date: 2026-07-27

Reviewer: `codex-independent-source-review-czarnik-1811.05497v2-2026-07-27`

Verdict: **PASS — the candidate source-only note and audit are semantically
faithful and may proceed to controlled admission**

The packet correctly reconstructs the infinite-PEPS bond-growth and local
compression algorithm, preserves the approximate finite-\(\chi\) CTMRG and
local-to-global boundaries, reports the numerical results only for the source's
displayed Ising workloads, and keeps every QEC/CAPEPS/instrument/Record bridge
outside the paper's claims. I found no blocking formula, locator, numerical,
relation, or source-local-gap defect.

This review did not modify the candidate note, source-only audit, source PDF,
or `docs/papers/CURRENT_CORPUS.toml`.

## Reviewed byte identities

| object | SHA-256 |
|---|---|
| pinned source, `docs/papers/1811.05497v2.pdf` | `a29c4bf23e381c50cae91a708456d6240792302bf1c0e127348cd2c6fdc5639c` |
| candidate note, `docs/papers/reading_notes/czarnik_dziarmaga_corboz_ipeps_time_evolution_1811.05497v2_source_review.md` | `5595b56d0be7d6a915aca7872c1d3db26af3757246d5b825f1a29b7a2f18f786` |
| source-only audit, `docs/simulator_validation/CZARNIK_DZIARMAGA_CORBOZ_1811_05497V2_SOURCE_ONLY_AUDIT_2026-07-27.md` | `8cbca6a0b180a78ac566ec3bf31b211d32e7a53a427f2b586de598e2b8bc71d6` |

The source and audit hashes stored in the candidate note equal the actual
source and audit hashes above.

## Independent full-source pass

The pinned object has a valid PDF 1.5 byte stream, is unencrypted, contains
3,499,982 bytes, and has 13 renderable pages. PDF page 1 visibly carries the
title, the three-author block, title-page date `January 15, 2019`, and the
stamp `arXiv:1811.05497v2 [cond-mat.str-el] 14 Jan 2019`.

The complete source was traversed from title through bibliography. All 13
pages were freshly rendered and visually inspected. The visual pass covered:

- Eqs. (2)--(5), the purification, and the ancilla gauge on PDF p. 3;
- Eqs. (6)--(11), the Trotter layers and rank-two \(ZZ\)-gate factorization,
  on PDF pp. 3--4;
- Fig. 2 and Eqs. (12)--(13), including the \(2D\) enlarged bond and the
  printed global and one-bond objectives, on PDF p. 4;
- Figs. 3--4 and Eqs. (14)--(18), including the approximate rank-six CTMRG
  environment and local optimizer, on PDF pp. 5--6;
- Figs. 5--6 and Eqs. (19)--(20), including the real-time and ensemble
  Lindblad benchmarks, on PDF pp. 6--7;
- Figs. 7--13, Eqs. (21)--(23), and Tables I--III, including every retained
  numerical estimate and comparison, on PDF pp. 7--11; and
- Fig. 14, Eqs. (A1)--(A3), the \(10^{-10}\) CTMRG stopping rule, and the
  5--6-day CPU statement on PDF pp. 11--12.

Text extraction was used for complete traversal and bounded absence searches,
not as formula ground truth. A case-insensitive full-text search for
measurement/instrument, outcome, trajectory, reset, Born, Record, Clifford,
stabilizer, tableau, repository, software, implementation, and code found no
substantive method match; `Kraus` occurred only as an author's surname in the
bibliography. No legacy note, RAG/KG result, project synthesis, or previous
output verdict was used as source evidence.

## Structural preflight and admission semantics

The artifact-verifying parser rejects the actual candidate at the intended
draft gate:

```text
admission_status must be 'source_only_reviewed'
```

A no-write in-memory diagnostic intercepted only the parsed value of
`admission_status`, replacing `draft_pending_review` with
`source_only_reviewed`. Source and audit artifact verification, section
parsing, checked-page validation, and relation resolution then all passed:

```text
total=44 paper_fact=33 literature_gap=11 relations=10
```

No candidate path, source ID, source hash, or candidate-note hash appears in
`docs/papers/CURRENT_CORPUS.toml`. That exclusion is correct until the
controlled promotion step.

## Formula and operation review

### Bond growth and exact local gate application

Section II states the general nearest-neighbour enlargement

\[
D\longrightarrow kD,\qquad k\le d^2,
\]

followed by approximation back to retained bond \(D\). For the displayed
Ising gate, Eq. (11) visually confirms

\[
e^{i d\tau Z_jZ_{j'}}
=\sum_{\mu=0,1}z_{j,\mu}z_{j',\mu},\qquad
z_{j,\mu}=\sqrt{\Lambda_\mu}(Z_j)^\mu,
\]

with \(\Lambda_0=\cos d\tau\) and \(\Lambda_1=i\sin d\tau\). Figure 2 shows
that contraction into \(A,B\) produces exact post-gate tensors \(A',B'\)
joined by \(2D\), before replacement by \(A'',B''\) joined by \(D\). The
candidate note and audit reproduce both the general \(kD\) statement and the
source-specific \(2D\) specialization without conflating them.

### Global objective, local surrogate, and tiling

Equations (12)--(13) visibly print

\[
F=\frac{\langle\psi''|\psi'\rangle
\langle\psi'|\psi''\rangle}{\langle\psi''|\psi''\rangle},
\qquad
\widetilde F=\frac{\langle\widetilde\psi''|\psi'\rangle
\langle\psi'|\widetilde\psi''\rangle}
{\langle\widetilde\psi''|\widetilde\psi''\rangle}.
\]

The packet correctly retains three separate statements:

1. the source calls these objectives fidelities;
2. neither printed denominator contains \(\langle\psi'|\psi'\rangle\); and
3. locally optimized tensors are tiled globally only as a source-declared
   approximation, justified heuristically when \(D\) is large enough for
   negligible truncation error.

It does not manufacture a normalized absolute fidelity, a theorem connecting
\(\widetilde F\) to \(F\), or an accumulated repeated-step error bound.

### Approximate environment and optimizer

Figures 3--4 and the surrounding Sec. III.E text support a rank-six bond
environment obtained approximately by CTMRG with environment bond \(\chi\).
The source says results were checked as \(\chi\) increased and calls CTMRG the
cost bottleneck; it does not turn either practice into an error certificate.

Equations (15)--(18) support the packet's operation replay: update
\(g=uv^\dagger\) from an SVD \(E(g)=u\lambda v^\dagger\), update the local
tensors with metric pseudoinverses, and repeat
\(\cdots\to g\to A''\to B''\to\cdots\) until self-consistency and convergence
of \(\widetilde F\). Appendix B's relative \(2\)-norm change below
\(10^{-10}\) is correctly typed as an iterative CTMRG stopping rule only.

### Empirical benchmark and resource scope

The retained values match the rendered figures and tables:

| workload | retained source value | source location | result |
|---|---:|---|---|
| \(h_x=2.5\), \(D=5\) | \(T_c=1.2745(7)\), \(1/\widetilde\beta\delta=0.549(4)\) | Fig. 9, PDF p. 8 | pass |
| \(h_x=2.9\), \(D=5\) | \(T_c=0.6055(10)\), \(1/\widetilde\beta\delta=0.563(4)\) | Fig. 10, PDF p. 9 | pass |
| disentangler comparison | roughly one-order improvement at \(D=4\), similar accuracy at \(D=5\) | Table I, PDF p. 10 | pass |
| old versus enlarged environment | FU and eeFU agree within reported errors for the two displayed fits | Table II, PDF p. 10 | pass |
| simple versus full update | \(D=12\) SU is poorer and reported slower than \(D=5\) FU in this example | Table III, PDF p. 11 | pass |
| reduced tensors | \(4D^4\) full, \(16D^2\) with disentangler, \(4D^2\) without | Appendix A, PDF p. 12 | pass |
| CPU workload | 5--6 days, 14-core 2.20 GHz Xeon Gold 5120 | Appendix B, PDF p. 12 | pass |

The packet correctly treats the QMC numbers as cited external reference data,
not as computations reproduced by this source. It also correctly refuses to
infer peak memory, asymptotic complexity, a universal real-time horizon, or a
matched CAPEPS/full-PEPS resource advantage.

## Atomic record review

### Source facts

| Fact ID | independent result |
|---|---|
| `czarnik1811-source-identity` | pass; title, authors, dates, version, and 13-page extent match |
| `czarnik1811-evolution-scope` | pass; abstract covers real, Lindbladian, and imaginary time and Ising tests |
| `czarnik1811-bond-growth-compression` | pass; Sec. II gives \(D\to kD\to D\), \(k\le d^2\) |
| `czarnik1811-local-auxiliary-state` | pass; the one-bond auxiliary construction and later tiling are explicit |
| `czarnik1811-real-time-entanglement-barrier` | pass; the finite-time statement is retained qualitatively, not as a law |
| `czarnik1811-thermal-purification` | pass; Eqs. (2)--(5) support purification and the cancelling ancilla gauge |
| `czarnik1811-trotter-decomposition` | pass; Eqs. (6)--(10) support the second-order step and four gate layers |
| `czarnik1811-zz-gate-bond-doubling` | pass; Eq. (11) and Fig. 2 support the rank-two factorization and \(2D\) |
| `czarnik1811-global-fidelity-objective` | pass; Eq. (12) is transcribed exactly and its scope is bounded |
| `czarnik1811-local-bond-fidelity` | pass; Eq. (13) and optimization variables match |
| `czarnik1811-local-to-global-placement` | pass; the source explicitly calls global placement an approximation |
| `czarnik1811-ctmrg-environment` | pass; rank six, approximate CTMRG, and refinement \(\chi\) match |
| `czarnik1811-ctmrg-bottleneck` | pass; the p. 5 paragraph supports both \(\chi\)-checking and bottleneck claims |
| `czarnik1811-reused-local-environment` | pass; the environment-independence and cancellation statements match |
| `czarnik1811-disentangler-svd-update` | pass; Eq. (15) gives \(g=uv^\dagger\) under the source convention |
| `czarnik1811-local-optimization-loop` | pass; Eqs. (16)--(18) support pseudoinverse updates and loop order |
| `czarnik1811-old-environment-error-concern` | pass; assumptions and nonvanishing-step-error concern are retained |
| `czarnik1811-real-time-fu-reduction` | pass; Sec. III.H explicitly reduces pure real-time eeFU to FU |
| `czarnik1811-real-time-benchmark` | pass; Fig. 5 wording remains source-reported apparent convergence |
| `czarnik1811-lindblad-vectorization` | pass; Eq. (19) is ensemble density-operator evolution, not trajectories |
| `czarnik1811-lindblad-benchmark` | pass; Fig. 6 is correctly called proof-of-principle/apparent convergence |
| `czarnik1811-near-critical-cost` | pass; slow CTMRG, step sensitivity, and finite-bias workaround match |
| `czarnik1811-critical-scaling` | pass; Eqs. (21)--(23) and the overloaded \(\widetilde\beta\) are correct |
| `czarnik1811-critical-result-hx25` | pass; values and \(d\beta,\chi\) settings match |
| `czarnik1811-critical-result-hx29` | pass; values, settings, and source-reported relative comparison match |
| `czarnik1811-disentangler-resource-tradeoff` | pass; accuracy/iteration/reduced-tensor tradeoff is explicit |
| `czarnik1811-disentangler-benchmark` | pass; Table I and its same-reduced-tensor qualification match |
| `czarnik1811-fu-eefu-comparison` | pass; Fig. 12/Table II support only the displayed workload comparison |
| `czarnik1811-simple-update` | pass; pair SVD and ignored long-range environment are explicit |
| `czarnik1811-su-fu-comparison` | pass; Table III and the present-example qualifier are retained |
| `czarnik1811-reduced-tensor-cost` | pass; Appendix-A element counts and fixed isometries match |
| `czarnik1811-ctmrg-stopping-rule` | pass; Appendix-B \(10^{-10}\) criterion matches |
| `czarnik1811-cpu-runtime` | pass; workload, duration, core count, clock, and processor match |

### Source-local gaps

| Fact ID | independent result |
|---|---|
| `czarnik1811-gap-fidelity-normalization` | pass; no target norm or stated target-normalization convention appears |
| `czarnik1811-gap-local-global-guarantee` | pass; no local-surrogate/global-objective theorem or accumulated error bound appears |
| `czarnik1811-gap-ctmrg-error-certificate` | pass; finite-\(\chi\) diagnostics are not converted into certified errors |
| `czarnik1811-gap-real-time-horizon` | pass; no universal quantitative reach law versus \(D\) appears |
| `czarnik1811-gap-selective-instrument` | pass; Eq. (19) is ensemble evolution and defines no outcome instrument |
| `czarnik1811-gap-reset` | pass; continuous lowering dissipation is not a reset transaction |
| `czarnik1811-gap-born-history` | pass; no branch masses, conditional branches, or prefix law appears |
| `czarnik1811-gap-complete-record` | pass; no raw history, detector/observable fold, or Record law appears |
| `czarnik1811-gap-clifford-augmentation` | pass; the ancilla gauge is not a Clifford frame or stabilizer residual |
| `czarnik1811-gap-matched-capeps-resources` | pass; no CAPEPS arm or matched resource comparison appears |
| `czarnik1811-gap-executable-provenance` | pass; no repository, version, commit, executable, or run artifact appears |

## Relation review

All ten relations resolve to existing `paper_fact` records. Every object label
names a source concept present in the associated claim:

| fact ID | relation | object label | result |
|---|---|---|---|
| `czarnik1811-bond-growth-compression` | defines | iPEPS bond-growth-and-compression step | pass |
| `czarnik1811-local-auxiliary-state` | uses | one-bond auxiliary iPEPS | pass |
| `czarnik1811-global-fidelity-objective` | defines | global fidelity objective | pass |
| `czarnik1811-local-bond-fidelity` | uses | local bond-fidelity objective | pass |
| `czarnik1811-ctmrg-environment` | uses | CTMRG bond environment | pass |
| `czarnik1811-real-time-entanglement-barrier` | limits | finite real-time convergence horizon | pass |
| `czarnik1811-critical-scaling` | measures | thermal critical-temperature scaling | pass |
| `czarnik1811-simple-update` | uses | simple-update truncation | pass |
| `czarnik1811-reduced-tensor-cost` | uses | reduced-tensor optimization | pass |
| `czarnik1811-cpu-runtime` | measures | reported full-update CPU workload | pass |

## Audit-packet review

The separate audit satisfies the required source/project separation:

- its notation ledger distinguishes \(d\), physical PEPS bond \(D\),
  transient \(D'\)/\(kD\)/\(2D\), and contraction bond \(\chi\);
- its variant ledger correctly distinguishes eeFUd, eeFU, FUd, FU, and SU;
- it explicitly warns that “exact-environment” names the enlarged-state
  environment choice while finite-\(\chi\) CTMRG remains approximate;
- every operation-replay row has a source-located input, transformation,
  assumption, and bounded output;
- the anomaly ledger retains the missing target norm, local-to-global
  approximation, finite-\(\chi\) non-certification, workload-limited FU/eeFU
  comparison, and qualitative real-time barrier; and
- the project-application section labels finite-QEC/CAPEPS use,
  measurement/Record certification, and resource extrapolation as project
  inference rather than paper claims.

The audit's replay closes at the source's published algorithmic or empirical
level. It does not fill absent stochastic-instrument transformations with
plausibility.

## Bounded source verdict

After controlled promotion, this source may support only:

1. the infinite-PEPS local-gate bond-growth pattern \(D\to kD\to D\), with
   the displayed Ising specialization \(D\to2D\to D\);
2. the printed global objective and one-bond surrogate, including the missing
   target-norm and local-to-global qualifications;
3. approximate finite-\(\chi\) CTMRG bond environments and the source's local
   optimization mechanics;
4. the qualitative fixed-resource real-time entanglement barrier;
5. the source's selected real-time, ensemble-Lindblad, and thermal Ising
   benchmarks;
6. the reported reduced-tensor counts, stopping rule, and one CPU workload;
   and
7. workload-specific comparisons among source-defined eeFUd, eeFU, FU, and
   SU variants.

It cannot support:

- exact or certified finite-\(\chi\) PEPS contraction;
- a theorem connecting the local objective to global state or Record error;
- a universal real-time reach, accuracy, complexity, or resource law;
- a finite XZZX syndrome circuit, selective measurement instrument, reset,
  Born branch/prefix mass, or detector/observable Record distribution;
- a Clifford frame, stabilizer tableau, GCAMPS/CAPEPS residual, or Clifford
  disentangler; or
- a matched CAPEPS/full-PEPS runtime, peak-memory, throughput, or
  Record-accuracy advantage.

## Admission disposition

No packet repair is required. The controlled admission owner may now:

1. set a non-pending independent reviewer identity and
   `admission_status = "source_only_reviewed"` in the note;
2. validate the promoted note with artifact verification enabled;
3. compute the promoted note's new SHA-256;
4. add exactly that promoted identity to `CURRENT_CORPUS.toml`; and
5. rebuild and audit the current manifest, concept index, RAG, and KG surfaces.

This PASS authorizes source-only corpus admission, not acceptance of a CAPEPS
claim, preregistration, experiment, or implementation.

- `read_status: complete`
- `evidence_status: persisted`
- `independent_source_review: pass`
- `semantic_packet_admissibility: pass`
- `structural_promotion_preflight: pass`
- `current_corpus_admission: pending_controlled_promotion`
