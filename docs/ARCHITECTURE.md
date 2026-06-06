# Architecture

`qec_twin` is the code for **the twin** — a teacher-learner, finance-structured QEC
error-mechanism digital twin. Binding spec: `docs/TWIN.md`. **Every module under
`src/qec_twin/` carries a `README.md`** that bounds its scope; read it before
adding code there.

## Module map (`src/qec_twin/`)

Three conceptual tiers. The tiering is **documentation, not import paths** — the
packages are flat (no `model/` / `substrate/` parents); deep nesting only where
there is real cohesion (`forward/` backends).

### Model — the four capabilities

| module | capability | status |
|---|---|---|
| `calibration/` | **RECOVER** — label-free exact Born-NLL calibration of the channel field | has code |
| `understand/` | **UNDERSTAND** — interpret recovered `E` into mechanism terms | placeholder |
| `knobs/` | **MANIPULATE** — channel-level `do()` → ΔLER | has code |
| `prediction/` | **PREDICT** — drift / rare-failure / decoder-impact forecast | placeholder |

### Substrate — what the model is built on

| module | role |
|---|---|
| `forward/` | exact differentiable forward model (physics engine); backend-swappable |
| `forward/exact/` | density-matrix backend — **⚠ FEASIBILITY-ONLY** (`2^n×2^n`, ≤~15q), abandoned after |
| `forward/scalable/` | placeholder for the **>50-qubit** backend (carrier deferred, ADR 0005) |
| `mechanisms/` | noise-mechanism definitions + controlled teachers |
| `contexts/` | probe-richness ladder `C_cal(r)` + probe definitions |
| `decoder/` | frozen-MWPM DEM substrate (`parity_map`, `fault_graph`, `stim_dem`) |

### Non-core

| module | role |
|---|---|
| `audit/` | evaluator-side: `gating` (identifiability), `bands` (uncertainty), `validity` (curve) |
| `util/` | placeholder for future small helpers |
| `numerics.py` | `NUMERICAL_ZERO` floor (root) |

## Flow

```
context c            (contexts)
  → forward[/exact]  exact forward  p(s,m | c)
  → calibration      minimize exact Born-NLL over C_cal(r)  →  recovered field E_hat
  → knobs            channel-level do(E_i) → ΔLER under a frozen decoder (decoder/)
  → audit            bands over the calibration-consistent set; validity vs controlled-teacher truth
```

## Backend boundary (critical)

`forward/exact` (density matrix) is `2^n × 2^n` → **feasibility-only**, unusable past
~15 qubits. The target is 50+ qubit noise circuits, so a **scalable backend**
(`forward/scalable`, placeholder) replaces it once the B-path loop is validated. The
channel object (`forward/cptp_channel`) and the four capabilities are
backend-agnostic, so the swap is a backend replacement, not a rewrite.

## History

The SCOPE thesis and the discovery / observability / catalog / Google /
DEM-fault-logit program were retired and removed (ADR 0005): they solved a different
problem (mechanism clustering + visible replay) than the twin (channel calibration +
counterfactual ΔLER). History is in git.
