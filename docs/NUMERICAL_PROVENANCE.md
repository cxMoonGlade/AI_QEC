# Numerical provenance ledger

**Status:** binding value-level claim boundary, first audit 2026-07-13.  This ledger covers the
current claim-bearing simulator presets, source defaults, acceptance gates, and active PEPS
frontier.  It is not a claim that every historical literal under `docs/` or `outputs/` has already
been inventoried.  Historical artifacts remain immutable evidence, but their embedded verdict text
does not override this ledger.

## 1. What a citation can and cannot support

A paper that supplies a channel equation supports the **functional form**, not automatically the
number substituted into it.  A software test or local run supports implementation behavior under
its frozen configuration, not correspondence to hardware.  Every claim-bearing value must use one
of these provenance kinds:

| kind | meaning | may support a hardware claim? |
|---|---|---|
| `paper-measured` | value directly measured in a named experiment | yes, within the paper's device/protocol scope |
| `paper-derived` | value follows from a cited equation using cited inputs | yes, within the derivation assumptions |
| `dataset-measured` | value read from a named local hardware artifact | yes, for that artifact and declared transform |
| `calibrated-to-paper` | project-model parameter chosen to reproduce a paper target | only as a model calibration, not as a measured device parameter |
| `project-design` | scientific design choice, synthetic comparator, or sweep point | no |
| `convenience-default` | API/runtime default chosen for usability | no |
| `numerical-only` | tolerance, solver setting, resource cap, or software gate | no |

For every `paper-*` or `dataset-*` value, record the exact page/figure/table/equation or artifact
field, units, device/protocol, and transformation chain.  Missing any of these fields fails closed.

### The project's one-source/two-source rule

- One primary experimental source can ground a **device- and protocol-specific measured value** if
  the exact locator is present.
- Calling a range **transferable**, **representative**, or **realistic across devices** requires at
  least two independent, compatible primary measurements, or one directly matched hardware dataset
  plus a declared uncertainty/sensitivity analysis.
- Two papers that separately ground two coordinates do **not** jointly validate their Cartesian
  product.  A cross-paper/device tuple must be called a **literature-scale composite benchmark**.
- A complete “physical cell” claim requires provenance and compatibility for every load-bearing
  coordinate, not merely two citations somewhere in the paragraph.

This is a project evidence policy, not a claim that publication count alone establishes truth.
Compatibility and object identity remain mandatory.

## 2. Active leakage presets: component-by-component audit

The public presets are defined in `src/error_coupling_simulator/frontend/experiments.py`
(`PRESET_LEAK_THETA_0P30`, `PRESET_LEAK_WG_L1_5E3`).
The Google `d3_at_q6_7` inputs provide verified geometry and within-cycle token streams
(`experiments.py:144-169`); they do **not** calibrate the noise coordinates below.

| coordinate | active value | provenance | exact anchor / transform | allowed interpretation |
|---|---:|---|---|---|
| raw exchange angle | `theta=0.30 rad` | `project-design` | registered p2-era point; no direct device measurement located | synthetic strong-angle preset |
| leakage target | project `WG_L1_target=5e-3/cycle` | `project-design` | Miao et al., Nature Physics 19 (2023), Fig. 3c, supplies only an approximate scale anchor: around `5e-3/cycle` for leakage population generated in the DQLR cycle. This is not the Wood–Gambetta uniform-subspace average `WG_L1`; the old identity transform is invalid | synthetic project target chosen near the Miao source-term scale, not an exact paper-measured `WG_L1` |
| resolved exchange angle | `theta≈0.102444 rad` | `project-design` | project bisection through the exact project WG channel to hit the project-selected `WG_L1_target=5e-3`; the paper measured neither this angle nor this WG channel value | project parameter transformed from a paper-scale-inspired project target, not a paper calibration |
| seepage coordinate | `g_seep=0.09` | `project-design` | McEwen et al., Nature Communications 12 (2021), Table S1 supplies a literature-scale comparator: no-reset data `gamma_down=9.1%/round`; mapping it into a different project channel/device is not a fit | cross-paper scale comparator, not a calibration |
| heating coordinate | `g_heat=0` | `project-design` | incoherent-heating-off ablation/default | declared simplification |
| leaked-readout bias | `b=0.9` | `project-design`, unsupported | no magnitude measurement found; the cited McEwen model gives a random leaked-measure-qubit hard outcome (detection fraction `0.5`), while Miao's four-level IQ separability does not imply binary `b>0.5`. Thus even the claimed direction `b>0.5` is not directly supported by those citations. The registered nuisance sweep remains a project choice | **must not support a physical/realistic claim; no cited two-paper support even for its direction** |
| measurement arm / convention | `arm=A`, `biased_b` | `project-design` | project instrument choice | named synthetic instrument only |

**Verdict:** neither active preset is a calibrated physical device cell.  The `WG_L1` preset is a
**Miao/McEwen literature-scale cross-paper composite benchmark with project instrument choices**.
The raw-angle preset is a synthetic benchmark.  Until `b` is swept or calibrated, no point result
using `b=0.9` can be promoted to a hardware prediction. Whole-cell direct published support found
count in the recorded search corpus is **0**; no current preset/teacher tuple passes the `>=2 independent
direct sources on the same object` gate.

The two direct primary anchors support only these atomic statements:

1. Miao et al. estimated an approximately `5e-3/cycle` leakage-population source scale in their
   DQLR surface-code experiment (Fig. 3c). This is not an exact measurement of project `WG_L1`.
2. McEwen et al. fitted approximately `8.1-9.1%/round` no-reset seepage in their bit-flip-code
   experiment (Supplementary Table S1).

They do not jointly measure the project channel, `theta`, `g_heat`, `b`, arm A, the XZZX schedule, or
their compatibility as one cell.

The registered `WG_L1_REGIME=(1e-3,5e-3)` is therefore not a paper-measured WG-rate band. In Miao,
`~1e-3` is a DQLR steady leakage-population level and `~5e-3/cycle` is an estimated generated source
term; neither is the same observable as the project Wood–Gambetta `WG_L1`. Both endpoints remain
project sweep/target choices with paper-scale context only.

## 3. Other current physical and source defaults

| object | values entering the active path | provenance | current claim boundary |
|---|---|---|---|
| Axis-1 G2 demonstration | `zeta/2pi=370 kHz`, `T1=30 us`, pure-dephasing `T_phi=30 us` (therefore implied total `T2=20 us`), drive `pi/25 ns`, registered `dt`/effect bands | `project-design` | formal BCH/channel implementation fixture; `gamma_1=1/T1`, `gamma_phi=1/T_phi`, so `1/T2=gamma_1/2+gamma_phi`; explicitly not an idle-Google calibration |
| Axis-1 primitive defaults | e.g. readout dephasing `1e-3/ns`, zero upward rate, zero residual fSim terms | `project-design` | class-(c) lowering inputs, including fail-inert choices; not measured primitive rates |
| analog schedule fallback | 1q `20-30 ns`, 2q `25-45 ns`, measurement `100-1000 ns`, reset `100-500 ns` | `project-design` | used only when no calibrated duration is supplied; channel strengths inherit this uncertainty |
| shared-source coupling defaults | representative 6/6.1 GHz qubits, `alpha=-300 MHz`, 25 ns gate, base phase `1.6e-4`, `T_phi=75 us`, SPAM/depolarization bases and sensitivities | `convenience-default` | formulas may be literature-derived; these constants are usability defaults, not device calibration, and “Calibration” in a class name does not change that. Miao's simulation setting `T1=T2=75 us` does not measure project pure-dephasing `T_phi=75 us` |
| Static-ZZ phase convention | project coefficient `phi_ZZ=zeta*t/4` | `project-design` | declared Hamiltonian convention; do not compare this number directly with a paper's conditional phase `Phi=zeta*t`, because they can differ by a factor of four |
| qutrit rate bands/sweeps | `WG_L1_REGIME=(.001,.005)`, `WG_L2_REGIME=(.05,.10)`, `theta=(0,.045,.07,.10)`, `g_seep=(.05,.09,.10)`, `g_heat=(0,.005)`, defaults `(.07,.09,0)` | `project-design` | selected endpoints have one-paper scale context only; no whole band/sweep/default tuple is paper-measured. Miao's `.001` steady population and `.005/cycle` source estimate are different observables; McEwen's `.081-.091/round` population-decay rate is not project `WG_L2` |
| leaked-readout sweep | `b=(.5,.75,1)` and any point such as `.9` | `project-design` | nuisance sweep; neither magnitude nor direction is grounded by the cited sources; report it as sensitivity, not a hardware range |
| within-cycle leakage slice | `WC_LEAK_FRAC=.25`, `exp(L/4)` | `project-design` normalization/siting | no published physical quarter-CZ derivation found; the compose tolerance `1e-12` is `numerical-only`, and the current comparison is a single-input same-model self-check |
| `OneOverFDriftSource` | total amplitude `1e-4 rad/ns`, 8 finite RTNs, rates `0.005...0.5/cycle`, cycle `1000 ns` | `project-design` | a synthetic finite-RTN source; form is literature-inspired, values are not hardware-grounded |
| single `RTNSource` | amplitude `1e-4 rad/ns`, `gamma=0.05/cycle`, cycle `1000 ns` | `project-design` | controlled source/comparator only |
| phase burst | `-2 MHz`, `1 ms`, `T1=10 us`, echo factor `0.05`, default event probability `0` | `project-design` | Kurilovich-like paper values are scale anchors only; the mapping, multiplicative `0.05`, and complete tuple are not directly measured as implemented |
| temporal storm HMM | `a=.01`, `b=.10`, calm/storm categorical probabilities | `project-design` | controlled HMM comparator only |
| seam teachers | e.g. `phi=.1`, backdrop `.01/.2`, telegraph rates | `project-design` | controlled teachers, no hardware claim |
| public MCWF/MPS execution defaults | microstep count `1`, trajectory count `1`, leaked-readout `b=1`, mass-residual budget `.1` | `convenience-default` | routing/smoke defaults only; one trajectory is not distribution evidence and `b=1` is not calibrated |
| Stim projection fallback | base probability `1e-3`, sensitivity `1`, scale `1e-4`, logit clip `+/-60` | `project-design` | an explicit reduced Pauli projection, not analog/non-Pauli truth |

The “few-kHz” source-coupling point has literature-order comparisons but is not calibrated to the
shipped Google patch.  The existing rate note's claim that it is *the faithful Google value* is
withdrawn; exact device work must parse the relevant hardware circuit/calibration artifact and retain
its device/protocol scope.

`SourceCouplingConfig.to_manifest()` currently supplies one bulk epistemic class `(c)`. That label is
not a substitute for the per-value manifest row required by Section 8 and does not give any base or
sensitivity a paper provenance.

## 4. CP-divisibility object mismatch and exact diagnostic resolution

`outputs/twin_validation/cpdiv_passive_record_check.py` evaluates the amplitudes/rates through a
second-cumulant **Gaussian coherence surrogate**.  The production `OneOverFDriftSource` instead
samples an explicit sum of eight finite RTNs (`src/error_coupling_simulator/source/process.py`).
With total amplitude `1e-4 rad/ns`, each fluctuator has
`v=1e-4/sqrt(8)≈3.54e-5 rad/ns`; the slowest default rate is
`gamma=0.005/1000=5e-6/ns`, hence `v/gamma≈7.07`, not uniformly a weak-RTN limit.

Therefore the committed `BLP=RHP=0` result proves only the Gaussian surrogate specified in that
calculation. A registered exact gate now evaluates two **separately declared free-induction
diagnostic lifts** of the finite-RTN endpoint process. Its prediction document was written before the
first run but was not committed before first inspection, so this is an independently reproduced
diagnostic with imperfect preregistration provenance, not a pristine Git-preregistered result. Both
the continuous-CTMC and cycle-held lifts
show BLP-positive excursions and match independent full-`2^8` oracles to `<1.6e-15`; the wrong
factor-of-two rate convention and an omitted factor fail at `~9e-2`. See
`docs/twin_validation/finite_rtn_exact_cpdiv_result_2026-07-13.md`.

This result does not assign CP-divisibility to `OneOverFDriftSource` itself: a stochastic source is
not a reduced dynamical map. Production routes `z` through `SourceCouplingConfig` into several
mechanism parameters rather than applying either diagnostic Hamiltonian. The production coupled QEC
map and record therefore retain an open channel/instrument bridge. The exact result corrects the
Gaussian proxy without laundering a diagnostic into a production claim.

## 5. Metrics, thresholds, and acceptance gates

Standard metric definitions do not make the chosen thresholds standard.

| values | role | provenance | allowed use |
|---|---|---|---|
| full-record TV/KL and generative NLL | d3 certification metrics | standard probability metrics; **project-selected QEC ladder** | compare frozen record laws; do not call a universal QEC standard |
| process infidelity strict `1e-6`, gross `0.1`; record-TV strict `1e-6`, gross `0.2`, ceiling `0.45`; confidence `0.999` | dense MCWF tripwires | `numerical-only` | implementation routing and no-op rejection only; a gross pass is not physical faithfulness |
| `p_ro=.01`, `p_reset=.005`, drift `s<=.3`, `Z=3`, `N<=1e6` | notion-2 Class-1 go/no-go | `project-design` | conditional bandwidth calculation; `s<=.3` is not a hardware-calibrated realistic ceiling |
| generic anchor bands such as `6/sqrt(N)`, `8/sqrt(N)`, scalar `1e-9` | certification heuristics | `numerical-only` | declared project gates, not coverage theorems |
| DEM edge floor `1e-5`, `>4 sigma`, probability cap | record-to-DEM selection | `project-design` | named reduction rule; it changes the exported graph and must not be hidden in decoder claims |
| `NUMERICAL_ZERO=1e-12`, matrix-exp/commutator tolerances | floating-point control | `numerical-only` | implementation diagnostics only, never a structural or physical zero |

Every reported result must state both the metric and whether its threshold is theorem-derived,
calibrated, or project-chosen.

## 6. Long-range truncation and resource numbers

- Manabe et al.'s truncated-singular-vector 2-norm thresholds (`1e-6` repetition,
  `1e-4` surface) are published settings for their geometry and observable.  The project's squared
  discarded-weight values (`1e-12`, `1e-8`) are a transparent algebraic conversion only; neither
  supplies a theorem for this full PEPS record or rare LER.
- FET/WTG/ZMT settings such as `eps_fid=1e-8`, `delta=1e-8/1e-6`, `chi_cap=32`, ALS iterations,
  f-gap floors, and large gap ratios are `project-design` or `numerical-only`.  Evenbly and Sokolov
  ground algorithmic objects and exact boundary cases, not these project thresholds.
- `W_max=160`, `D_abort=40`, PEPS bond plateaus, and VRAM projections are resource guards.  They do
  not establish record faithfulness.
- The single-wire WP2 prediction `epsilon_l<=1e-2` was not met by its own reported values
  (codestate mean about `.1875`, R1 about `.2186`). The registered `N=8,R=40` plateau run was not
  completed; the available pilot was `N=1` and aborted after R1. Neither may be reported as a
  validated truncation regime.
- d5/d7 memory figures and bond extrapolations are project resource extrapolations unless accompanied
  by a committed artifact and a stated ordering/representation.  They are not theorems for every
  tensor-network ordering.

The long-range truncation-to-full-record bridge remains open in
`nonpauli_teacher/coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md`.

## 7. Corrected artifact interpretation

`outputs/nonpauli_teacher/peps_leakon_d3_entropy_out/summary.json` requested `N_traj=6, R=4`,
but all six trajectories have `status=BondAbortError` after a single recorded round.  At that round:

```text
codestate baseline S_A = 2.0
maximum leak-on S_A     = 2.000000369882518
difference              = 3.69882518e-7
```

Thus the artifact shows six identical **R=1 near-baseline** values, not equality to `2e-16`, zero
added entropy, or multi-round confirmation.  Its embedded `CONFIRMED` verdict is invalidated by the
artifact's own fields.  The output file remains unchanged as historical evidence.

### Other historical numerical results that remain narrowly scoped

- The PEPO `dp/bar≈0.0167` result is arithmetic on a d3, single-cut, once-per-round optimistic
  proxy. It is reportable as that proxy, not as a record-faithful carrier certificate.
- The notion-3 `K`/CMI/`N_detect` values are outputs of frozen project toy models with uncalibrated
  parameters. They do not support the retracted universal claim that no classical process can
  reproduce the protocol result.
- The `notion3_Kpeak` prose reports a fine-grid peak near `r=.3`, ratio `~1.38`, while the committed
  smoke artifact peaks at `r=.4`, ratio `1.359`. Without the missing fine-grid artifact, the prose
  number has a provenance gap.
- `403.5 s/trajectory` is a local machine/backend/configuration benchmark, not an algorithmic
  complexity constant or transferable runtime.

## 8. Required manifest row for every claim-bearing run

Before execution, freeze one row per value:

```text
parameter | semantic object | value | units | provenance kind
source DOI/artifact | exact locator | device/protocol scope
transformation/calibration chain | compatibility assumptions
sweep/uncertainty | claim this value may support | claim it may not support
```

No row means no claim-bearing run.  A literal may still be used as a fail-loud software fixture, but
the result must remain implementation-only.

## 9. Source-code correction queue

### Previously completed for the active registered-preset path (2026-07-13)

The authorized source-change phase completed the following active registered-preset corrections:

1. `PRESET_LEAK_WG_L1_5E3` is emitted as a synthetic cross-source composite benchmark; whole-cell
   direct-paper support count is zero.
2. `b=0.9` is an explicit synthetic nuisance point and the required registered sweep
   `(0.5,0.75,1.0)` is carried in the manifest; it is not a physical headline value.
3. `StaticZZCalibration` and Axis-2 source defaults emit `project-design` value provenance and deny
   hardware-calibration status.
4. The Gaussian-surrogate historical gate is separated from the exact finite-RTN diagnostic gate;
   both diagnostic lifts and the still-open production bridge are named explicitly.
5. `RunSpec` and emitted sampler headers now carry a JSON-safe `numerical_provenance` block that
   separates Google geometry/schedule use from noise-parameter calibration and fails closed for
   caller-defined presets. Caller-supplied dictionaries and copied preset objects cannot self-declare
   `complete_for_registered_preset`; only the registered facade binds a canonical manifest digest.
   `RunSpec` validates the manifest against its run fields and emits from an immutable canonical JSON
   snapshot, so later mutation of the exposed dictionary cannot change the header.

Final focused regression batch: `202 passed, 23 skipped`, including the exact gate and registered-preset
provenance path. Downstream APIs that bypass the registered preset may
still choose convenience defaults such as `b=1`; those remain implementation-only under Section 3.

### Reopened by the literature/metric hostile audit (2026-07-13; source edits not authorized here)

The following live source comments/manifests still conflict with this binding ledger:

1. `frontend/experiments.py` labels `wg_l1_target=5e-3` as `paper-measured` and records an identity
   transform from Miao Fig. 3c. The paper reports an approximate leakage-population source term,
   not the project Wood–Gambetta average. The field must become a project target with a
   paper-scale approximate anchor.
2. `mechanisms/qutrit_teachers.py` says the direction `b>0.5` is device-grounded by Miao/McEwen.
   McEwen's hard leaked-measure-qubit model is random (`0.5` detection fraction), and Miao's IQ
   clusters do not determine this binary mapping. The nuisance sweep is still allowed, but its
   direction and endpoints are project choices.
3. `forward/scalable/sv_sampler.py` still calls the per-touch `exp(L/4)` rate physical because
   `DEPOLARIZE2` appears at every CZ. That placement does not calibrate a qutrit leakage generator;
   `exp(L/4)` remains a project normalization/siting convention.
4. The exact qutrit record oracle returns a full joint only at `R=1`, while its certification router
   can declare small-register `R>=2 FULL_JOINT/SYNDROME_DIST` feasible and then read a missing
   `joint` field. This is a metric/oracle contract bug, not literature evidence.
5. `ShotSet.to_det_obs()` currently places round-major raw syndrome bits in the field named `det`
   without the temporal XOR fold. `R=1` hides the mismatch. Full-joint TV/KL/NLL remain invariant only
   when both exact laws receive the same bijective push-forward; DEF, marginals, `p_ij`, lag/CMI,
   Markov-order, DEM, and decoder semantics do not. Until the source accessor is repaired and locked
   by `R>=2` controls, affected artifacts must be labeled `raw syndrome + terminal obs` or identify an
   explicit trusted fold.

No `src/**` changes were made in this literature-only pass. These corrections require the explicit
source-change authorization mandated by the simulator spec.

## Primary anchors used in this audit

- Miao et al., “Overcoming leakage in quantum error correction,” *Nature Physics* 19 (2023),
  DOI `10.1038/s41567-023-02226-w`, Fig. 3c.
- McEwen et al., “Removing leakage-induced correlated errors in superconducting quantum error
  correction,” *Nature Communications* 12 (2021), DOI `10.1038/s41467-021-21982-y`, Supplementary
  Table S1.
- Wood and Gambetta, “Quantification and characterization of leakage errors,” *Physical Review A* 97,
  032306 (2018), DOI `10.1103/PhysRevA.97.032306`, definitions of `L1/L2`.
- Rivas, Huelga, and Plenio, *Physical Review Letters* 105, 050403 (2010), DOI
  `10.1103/PhysRevLett.105.050403`; Breuer, Laine, and Piilo, *Physical Review Letters* 103,
  210401 (2009), DOI `10.1103/PhysRevLett.103.210401`, reduced-map criteria only.
- Evenbly, *Physical Review B* 98, 085155 (2018), DOI `10.1103/PhysRevB.98.085155`; Manabe,
  Suzuki, and Darmawan, *New Journal of Physics* 27, 114512 (2025), DOI
  `10.1088/1367-2630/ae1529`, truncation and leakage-approximation scopes.
