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
earlier "SCOPE / Symmetry-Compressed Orbit-Physical Emulator" thesis and
orbit-sharing as an identifiability lever — is **ADR 0009**. The current build is
the small-scale exact-CPTP counterfactual loop (the "B path"): ADR 0006 (build
order), 0007 (B validation methodology), 0008 (derivatives-calibration framing of
B5). The main-line model **architecture is deliberately open**: the four
capabilities are the spec, candidate parameterizations are judged against them,
and scalability is a future selection criterion, not a now-decision (ADR 0009).

## Doc routing

- `CONTEXT.md`: glossary and claim boundaries (read first).
- `docs/ARCHITECTURE.md`: code architecture and module map.
- `docs/RUNBOOK.md`: install, test, GPU, and the full experiment command set.
- `docs/teacher_learner.md`: teacher / learner roles and the isolation contract.
- `docs/TWIN.md`: binding twin spec — object contract `p(y|c)=Tr[M_y C(c)(rho0)]`,
  the four capabilities, finance methodology, and reserved notation.
- `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`: causal-representation-learning,
  identifiable-latent-variable, and finance tools for the alias-quotient and
  counterfactual-validity problems; action items + reference list.
- `docs/papers/`: local PDF cache of the load-bearing references (index in
  `README.md`). Check here before web-searching.
- `docs/BENCHMARKS_AND_BASELINES.md`: benchmark ladder and baseline selection.
- `docs/error_mechanisms.md`: physical-error mechanism taxonomy.
- `docs/PHYSICALITY.md`: CPTP/readout implementation and claim boundary.
- `docs/adr/`: durable decisions. Current spine is 0006 → 0009.

## Package and module rules

The implemented package is `scope_static` — a stable code identifier retained by
ADR 0009 (do NOT rename it; the name is a handle, not the thesis). New code goes
in the responsibility package that owns it; do not add flat modules directly under
`src/scope_static/` or rebuild a broad `scope_static.physical` package.

```
scope_static.primitives       low-level channel/PTM/probe/CPTP/POVM/density-sim/preflight, plus the
                              differentiable substrate (diff_cptp_channel, diff_circuit_sim, diff_rep_code)
scope_static.dem              DEM/Bernoulli parity core
scope_static.google           Google/Willow readers, inventory, S3 visible surface
scope_static.data_preparation teacher generator (mechanism records, probes, sampled obs, audits)
scope_static.teacher          teacher self-audit
scope_static.learner          label-free learner: visible recovery + replay quality
scope_static.identifiability  observational alias quotient + identifiability diagnostics
scope_static.mechanism_observability  local inverse, typed SPAM/gate features, calibration
scope_static.mechanism_discovery      latent assignment, prototype, transfer, robustness, effect audits
scope_static.catalog_pipeline controlled-catalog orchestration
scope_static.experiments      thin CLI/config wrappers, grouped by family: static/, qec_noise_catalog/,
                              stage3/, stage4/, stage5/, willow_data/, scope_twin/
scope_static.cuda             C++/CUDA exact DEM/window kernels
```

Experiment wrappers stay grouped by family; do not add flat `run_*` modules under
`scope_static.experiments`. The current B-path / twin work lives in
`scope_static.experiments.scope_twin` and `scope_static.primitives.diff_*`.

## Notation (keep aligned across code and docs)

- `A` — DEM parity map `F_2^{B×M}` (never an assignment matrix).
- `e ∈ {0,1}^M` latent effective-fault vector; `y ∈ {0,1}^B` observed detector/logical bits.
- `lambda_j = logit(p_j)` — fault logit (never `ell_j`).
- `S` or `Pi` — learned discovery assignment (never `A`).
- `omega(j)` — a known DEM orbit (grouping) assignment; a symbol reservation only,
  not an identifiability claim (ADR 0009).
- `m` — logical observable (never `o`).

## Numerical floor policy

Use `scope_static.numerics.NUMERICAL_ZERO == 1e-12` for floating numerical floors,
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
reinstall editable or use the module entrypoint. See `docs/RUNBOOK.md` for the
full command set.

## Claim discipline

- The label-free learner must consume only learner-visible observations and
  approved public metadata. Evaluator-only labels, exact channels, PTMs, Kraus
  matrices, teacher IDs, and oracle prototypes stay outside the learner path.
- Identifiability is bounded by the observational alias quotient and by the
  learnable degrees of freedom of the observation map. **Report honest
  alias/uncertainty bands; never assume identifiability a parameter-tying prior
  did not earn** (ADR 0009). Probe richness (data) is the demonstrated cure for
  observational alias, not parameter sharing.
- Counterfactual validity is not established by calibration fit alone; it is
  validated against controlled-teacher `do()` ground truth at small scale
  (ADR 0006/0007). On real Google data there is no realized counterfactual, so no
  Google physical-mechanism, public-label, Born-rule, or CPTP/GKSL-learning claim
  is made until the loop is validated and the real-data stage is reached.
- Controlled catalog evidence (teacher generator → teacher self-audit → label-free
  learner → discovery/effect audits) is valid as the teacher-learner substrate.
  Keep it claim-bounded: it demonstrates controlled recovery/replay under the
  declared visible surface, not hardware physical-mechanism recovery.
