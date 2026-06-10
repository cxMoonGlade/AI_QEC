# Agent Notes

Start with `CONTEXT.md` (glossary + claim boundaries), then route by topic below.

## Main line (2026-06)

The project builds a **teacher-learner digital twin of QEC error mechanisms**,
structured like a quantitative-finance calibration/risk system, delivering four
capabilities over hardware-realistic noise:

- **recover** — label-free calibration of error mechanisms from observations
  (finance: volatility-surface calibration / inverse problem);
- **understand** — interpret mechanisms and report honest uncertainty / alias
  bands (finance: model-uncertainty, factor interpretation);
- **manipulate** — channel-level `do()` knobs → ΔLER (finance: Greeks / hedging /
  scenario);
- **predict** — drift, rare-failure, and decoder-impact forecasting (finance:
  state-space / regime / multiscale stochastic volatility).

`teacher-learner` is the training mechanism; the finance analogy is the
organizing principle. The decision record for this framing — and for retiring the
earlier orbit-symmetry-compression thesis and
orbit-sharing as an identifiability lever — is **ADR 0005**. The current build is
the small-scale exact-CPTP counterfactual loop (the "B path"): ADR 0002 (build
order), 0003 (B validation methodology), 0004 (derivatives-calibration framing of
B5). The main-line model **architecture is deliberately open**: the four
capabilities are the spec, candidate parameterizations are judged against them,
and scalability is a future selection criterion, not a now-decision (ADR 0005).

## Doc routing

- `CONTEXT.md`: glossary and claim boundaries (read first).
- `docs/ARCHITECTURE.md`: code architecture and module map.- `docs/teacher_learner.md`: teacher / learner roles and the isolation contract.
- `docs/TWIN.md`: binding twin spec — object contract `p(y|c)=Tr[M_y C(c)(rho0)]`,
  the four capabilities, finance methodology, and reserved notation.
- `docs/PLAN.md`: whole-project roadmap — phase gates (B → HARDEN → C), strict
  physical/mathematical/aim↔object invariants, and what stays open (ADR 0005).
- `docs/METRICS.md`: the metric ledger and the **forced standard-metric ladder** — every score is
  named with its field-standard reference and convention; new metrics go through ledger → frontier
  research → flagged project-defined (dated numbers in `docs/metric_results.md`).
- `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`: causal-representation-learning,
  identifiable-latent-variable, and finance tools for the alias-quotient and
  counterfactual-validity problems; action items + reference list.
- `docs/papers/`: local PDF cache of the load-bearing references (index in
  `README.md`). Check here before web-searching.
- `docs/.datasets/`: reading notes for the four local Google QEC datasets (Zenodo 13273331 family,
  under `/home/cx/Document/`) — design, file formats, logicals, layout, shipped decoder baselines,
  and per-dataset relevance to the R2 rungs (ADR 0007); `_sources/` caches the CC-BY README
  originals (dot-prefixed ⇒ gitignored, local-only). Read the matching note — including
  layout/figure facts — before touching any hardware data; dataset documentation is a mandatory
  derivation input for every R2 pre-registration.- `docs/error_mechanisms.md`: physical-error mechanism taxonomy.- `docs/adr/`: durable decisions. Current spine is 0002 → 0006.

## Package and module rules

The implemented package is `qec_twin`. New code goes in the responsibility package
that owns it; do not add flat modules directly under `src/qec_twin/` or rebuild a
broad `qec_twin.physical` package.

Three tiers (flat packages; the tiering is documentation, not import paths). **Each
module has a `README.md` bounding it — read it before adding code there.**

```
# model — the four capabilities
calibration/  [RECOVER]     label-free exact Born-NLL calibration
understand/   [UNDERSTAND]  interpret recovered channel (placeholder)
knobs/        [MANIPULATE]  channel-level do() -> ΔLER
prediction/   [PREDICT]     drift / forecast (placeholder)
# substrate
forward/      exact differentiable forward; channels + cptp_channel + exact/ (density-matrix,
              ⚠ feasibility-only <=~15q) + scalable/ (placeholder, >50q) +
              kernels/ (package-local CUDA/C++ acceleration assets)
mechanisms/   mechanism definitions + controlled teachers
contexts/     probe-richness ladder C_cal(r) + probes
decoder/      frozen-MWPM DEM substrate
# non-core
audit/        gating / bands / validity (evaluator-side)
util/         placeholder for small helpers;  numerics.py = NUMERICAL_ZERO floor (root)
```

Full map + per-module scope: `docs/ARCHITECTURE.md`. The SCOPE / discovery /
observability / catalog / Google / DEM-fault-logit program was removed (ADR 0005).
⚠ `forward/exact` (density matrix) is feasibility-only — the 50+ qubit target needs
the `forward/scalable` placeholder.

## Notation (keep aligned across code and docs)

- `A` — DEM parity map `F_2^{B×M}` (never an assignment matrix).
- `e ∈ {0,1}^M` latent effective-fault vector; `y ∈ {0,1}^B` observed detector/logical bits.
- `lambda_j = logit(p_j)` — fault logit (never `ell_j`).
- `S` or `Pi` — learned discovery assignment (never `A`).
- `omega(j)` — a known DEM orbit (grouping) assignment; a symbol reservation only,
  not an identifiability claim (ADR 0005).
- `m` — logical observable (never `o`).

## Numerical floor policy

Use `qec_twin.numerics.NUMERICAL_ZERO == 1e-12` for floating numerical floors,
simulation thresholds, probability floors, and leftover/complement probabilities
that would otherwise become exact `0.0`. This value survives square/cube
operations in GPU float32. `NUMERICAL_FLOOR` is a descriptive alias only. Do not
replace structural zeros: Pauli/operator matrix entries, bit values, integer
indices, counts, labels, array sizes, empty-artifact metrics, and exact algebraic
identities must remain exact zeros where required.

## GPU-first execution

Treat this as a GPU-heavy QEC research program. Assume the target workstation has
a CUDA device, at least RTX 5090 class, even if the current sandbox/session cannot
see it. For any serious training, likelihood, local-window, Google-data, or large
ablation workflow, prefer native GPU execution.

Verify CUDA visibility from the `aiqec` environment before long runs; failure to
see CUDA in one session is an environment-visibility problem to diagnose, not a
reason to fall back to CPU-first design:

```bash
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
```

Wrappers such as `/usr/bin/time` or Conda's `--no-capture-output` can run inside
the sandbox and make Torch report no CUDA/NVML even though the GPU is healthy.
Prefer in-process `time.perf_counter()` for benchmark metrics, or get the wrapped
command approved before treating CUDA invisibility as a real failure. If GPU
utilization is low, first check whether the workload is launch-bound or
CPU-preprocessing-bound (window/cache construction, `.b8` loading, Stim/DEM
parsing) before assuming the GPU path is broken.

## Commands

```bash
conda run -n aiqec python -m pip install -e .      # install (editable)
conda run -n aiqec python -m pytest -q             # full suite
```

Do not set `PYTHONPATH="$PWD/src"` on this WSL/CUDA setup; it can interfere with
PyTorch CUDA/NVML discovery. If a console script is missing after code changes,
reinstall editable or use the module entrypoint.

## Claim discipline

- The label-free learner must consume only learner-visible observations and
  approved public metadata. Evaluator-only labels, exact channels, PTMs, Kraus
  matrices, teacher IDs, and oracle prototypes stay outside the learner path.
- Identifiability is bounded by the observational alias quotient and by the
  learnable degrees of freedom of the observation map. **Report honest
  alias/uncertainty bands; never assume identifiability a parameter-tying prior
  did not earn** (ADR 0005). Probe richness (data) is the demonstrated cure for
  observational alias, not parameter sharing.
- Counterfactual validity is not established by calibration fit alone; it is
  validated against controlled-teacher `do()` ground truth at small scale
  (ADR 0002/0003). On real Google data there is no realized counterfactual, so no
  Google physical-mechanism, public-label, Born-rule, or CPTP/GKSL-learning claim
  is made until the loop is validated and the real-data stage is reached.
- Controlled catalog evidence (teacher generator → teacher self-audit → label-free
  learner → discovery/effect audits) is valid as the teacher-learner substrate.
  Keep it claim-bounded: it demonstrates controlled recovery/replay under the
  declared visible surface, not hardware physical-mechanism recovery.
- Every quantitative claim is scored by a **field-standard** metric via `docs/METRICS.md` (forced
  ladder: ledger → frontier research → explicitly flagged project-defined). No silent non-standard
  stand-in; carry each metric's convention with its numbers.
- **Baseline discipline (2026-06-10).** Baselines come from `external/baselines/` (16 pristine
  vendored repos: DMLE-QEC, PyMatching, Stim, fusion-blossom, qecGPT, pyro, pgmpy, …) and the
  datasets' own shipped baselines (SI1000 circuits, RL-prior decoding artifacts). Run them
  comprehensively, at their OWN recommended/default settings, and NEVER modify their code —
  minimal adaptors/helpers only, in our tree (never patches under `external/`). Declare baseline
  version/commit + settings with every number.
- **Epistemic-status declaration (2026-06-10).** Every pre-registration classifies each
  quantitative item: **(a) exact** (theorem/identity — the only class usable as a premise or
  derivation basis), **(b) prediction band** (falsifiable bet; miss = finding, never later cited
  as fact), or **(c) heuristic gate/decision rule** (go/no-go gating and tripwires ONLY — never a
  premise, definition, derivation step, error bound, or conclusion basis). Undeclared ⇒ (c).
  Rule text: METRICS.md; binding instances: window-closure X1/X2 (`hardware/windows.py` STATUS
  WARNING), the M1/M2 retro-audit (`metric_results.md` 2026-06-10).
- **Theory first, runs verify (2026-06-09).** The mathematics/physics derivation — predicted
  direction, scaling, threshold — is written down *before* every code experiment (controlled or
  real-data); experiments verify derived predictions, never explore-then-rationalize. HARDEN's
  predict-before-measure gates are the template (PLAN.md §3; ADR 0007 extends it to R2-lite).
- **Novelty is sequenced, not ceded (2026-06-09).** Deferred ambitions (Claim-B band engine,
  composed prioritization engine, d=5/d=7 surface-code twin) keep recorded re-open triggers
  (ADR 0007); the current gated cut completes before new ambitions open.
