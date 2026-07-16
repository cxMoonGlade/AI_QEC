# error_coupling_simulator

The standalone, independently-releasable **specified-noise QEC simulator**. It applies declared
coupling, leakage, and memoryful noise processes to a QEC circuit and emits the multi-time syndrome
record. The implementation is consolidated behind this package boundary. Setuptools uses an
exact package allowlist (`error_coupling_simulator` plus its subpackages). It is importable as
`import error_coupling_simulator`.

## Why this package exists
The simulator is the deliverable we intend to **release independently**. Keeping its code in one
cohesive package gives it a clean boundary, a cohesive public surface, and a releasable unit.

## Boundary / disciplines (binding)
- **No physical ground truth.** A noise process is a model we SPECIFY; oracles (QuTiP / closed forms)
  are FORMAL bug-catchers, never "validated vs reality." Product = the full record; LER and other
  metrics are instruments on it.
- **Isolation.** Evaluator-only process truth must never enter emitted records or public artifact
  metadata. Certification may read it only through the declared evaluator-side seam.
- **GPU-first** for model compute (no `cuda if available else cpu`); `NUMERICAL_ZERO = 1e-12` is
  only a floating comparison threshold and never probability mass.
- **Representability is fail-closed.** Shared scaled product/exponential and odds-domain helpers
  recover a finite binary64 result when only an intermediate is unsafe, and reject a nonzero result
  that cannot be represented without becoming a structural endpoint.
- **Precision-purpose boundary.** Only the fused within-cycle SV-MC carrier uses c64, and only for
  optimization/screening. Final and certification runs are c128 candidates; PEPS/MPS remain
  c128-only. Declared leakage-channel/codestate construction and CPTP checks stay c128, with only checked
  execution tables cast afterward. c64 never authorizes tolerance or FET changes.

## Layout

- `source/` — Axis-2 classical non-Markovian sources, including the finite log-spaced RTN
  construction of `OneOverFDriftSource`, replayable timelines, and explicit `Theta(z_t)`
  source-to-mechanism fan-out.
- `carrier/` — exact DM, joint-Lindbladian channels, CUDA kernels, the retained DM-PEPO research
  carrier, and the single-wire 2D-PEPS research carrier.
- `mechanisms/`, `noise_processes/` — mechanism primitives and controlled generative processes.
- `frontend/` — CircuitIR / CodeSpec / compiler / schedule / carrier execution / artifact emission.
- `certify/` — evaluator-only anchor and certification seam.
- `quantum_bath/` — feasibility-only pseudomode-enlarged GKSL research carrier; not the product
  mainline and not a passive-record quantum-memory certificate.
- `numerics.py` — shared float64 representability arithmetic and comparison-threshold policy; not a
  physical mechanism or probability-mass source.

## Runtime and distribution boundary

- Core runtime requires Python 3.11 or newer. SciPy is a core dependency because package runtime
  modules import it directly; PyMatching remains opt-in through `[hw]`.
- Google r01/r10 circuit and metadata files are explicit external circuit/geometry/schedule
  inputs. They are not package assets, their measurement data are not consumed by the preset
  facade, and they do not supply noise parameters.
- Ququart transport accepts explicit `CZParams` for package-owned in-process channel derivation,
  an in-memory Kraus/channel object, or an explicit serialized channel cache. Kraus operators are
  a derived channel representation, not external scientific data; repository scratch under
  `outputs/` is neither a default nor package data.
- The CUDA-Q Grover adapter remains public through the `cudaq-grover` optional extra, but it is an
  isolated plugin workload. It runs in the retained `aiqec` environment and a separate process,
  not in canonical `ecs` beside the fused extension.
- Release acceptance uses the real-checkout sdist → wheel → isolated-install gate in
  `tests/test_distribution_boundary.py`. That gate removes the checkout from import resolution,
  exercises package import and core smokes, and rejects unowned modules, old entry points, or
  repository-only assets. Editable-install tests alone do not prove the distribution boundary.
- The installed service inventory is not implicit: `docs/service_status.json` and its generated
  `docs/CODE_MAP.md` ship under `share/doc/error-coupling-simulator/`. The generator classifies every
  shipped Python module as service implementation or explicit support and fails on any future
  unclassified module; the generated map records the current exact count.

## Status
**The self-contained code boundary is closed; scientific carrier certification remains open.**
Source, carrier, mechanisms, noise processes, frontend, certification, and the retained
quantum-bath research slice live in this package and use package-local runtime ownership. The PEPS
schedule host and `frontend.experiments` are package-local. External circuit inputs, explicit
mechanism parameters/channel
injections, and isolated optional plugins are declared boundaries, not hidden package back-edges.

The classical `1/f` path is an active core service:
`OneOverFDriftSource -> SourceTimeline -> Theta(z_t) -> CoupledCycleNoiseProcess -> {det, obs}`.
It ships with a matched-marginal permutation control and a source-off control. Bayes decoder-floor
analysis is downstream analysis and is not a simulator service.

`PhaseBurstSource` and `TemporalStormSPPSource` are shipped RESEARCH timeline primitives, not
turnkey `CoupledCycleNoiseProcess` record arms. A caller can route a timeline through explicit
`SourceStimPauliProjectionSpec` rules, but that path is a reduced Stim-Pauli comparator and never
analog truth. The generic dense qudit MCWF carrier is also distinct from its optional Grover
workload adapter.

The shipped 1D MPS route is the restricted Axis-1 MCWF/QT execution slice; it is executable
verification, not a production-scalable/full-record carrier. The scientific frontier is the
full-`d x d` single-wire 2D-PEPS trajectory carrier. Its d3
state-level spike is implemented, but finite-truncation fidelity of the complete multi-round record
is still open. The doubled-wire DM-PEPO remains a research carrier with known record-law failures,
and d5/d7 distributional results remain provisional. Binding status and claim boundaries live in
[`docs/SIMULATOR.md`](../../docs/SIMULATOR.md), [`CLAUDE.md`](../../CLAUDE.md), and the current
[PEPS truncation contract](carrier/peps/README.md#truncation-contract); this README must not be used
to promote a carrier or a synthetic parameter set beyond them.
