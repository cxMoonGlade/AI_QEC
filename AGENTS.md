# Agent Notes

Use `CONTEXT.md` first for glossary and claim boundaries, then route to the
stage-specific docs:

- `docs/SCOPE_STATIC_MVP.md`: Stage 1 known-orbit DEM fault-logit MVP.
- `docs/SCOPE_STATIC_DISC.md`: Stage 2 static discovery plan.
- `docs/SCOPE_TWIN.md`: full SCOPE-Twin notation and future object contract.

## Current Scope

The implemented package is `scope_static`. It is a fixed-context DEM/Bernoulli
research stack, not a CPTP/GKSL physical-channel learner.

Stage 1 learns fault logits over a canonicalized detector error model:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
```

Keep notation aligned with `docs/SCOPE_TWIN.md`:

- `A` is the DEM parity map.
- `lambda_j` is the Stage 1 fault logit.
- `omega(j)` is a known orbit assignment.
- `S` or `Pi` is a learned Stage 2 discovery assignment.
- Do not use `o` for orbit or observable.
- Do not use `ell_j` for logits.

## Commands

Install:

```bash
conda run -n aiqec python -m pip install -e .
```

Test:

```bash
conda run -n aiqec python -m pytest -q
```

Run MVP05 smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static --config configs/scope_static/d3_r1_MVP05_windows.yaml
```

Run MVP05 full:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static --config configs/scope_static/d3_r1_MVP05_windows_full.yaml
```

Do not use `PYTHONPATH="$PWD/src"` for normal runs on this WSL/CUDA setup. The
package should be installed editable; setting `PYTHONPATH` can interfere with
PyTorch CUDA/NVML discovery.

## Evidence Discipline

Stage 1 evidence must include seed-aware summaries, graph/window audits,
compression accounting, and baseline comparisons against `local`, `dmle_qec`,
`hard_orbit`, and `soft_feature_orbit`.

Soft residual claims require nonzero centered within-orbit feature rank.
Compression claims require explicit parameter audits.

Stage 2 discovery should begin with synthetic teachers and report ARI/NMI before
using Google repetition-code or surface-code data as external empirical
validation.
