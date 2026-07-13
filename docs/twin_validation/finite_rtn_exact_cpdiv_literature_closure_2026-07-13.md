# Finite-RTN reduced-map diagnostic — literature closure packet (2026-07-13)

> **Workflow:** `theory-fix -> close-literature -> deep-read-paper -> stress-test-claim`.
> **Frozen object:** the default `OneOverFDriftSource` latent process under explicitly declared
> single-qubit free-induction diagnostic lifts. The source object by itself is a classical stochastic
> process and has no RHP/BLP status. This packet does **not** identify the diagnostic with the
> production `SourceCouplingConfig` fan-out, the coupled QEC channel, or its syndrome record.

## Frozen atomic claims

| id | atomic claim | status sought |
|---|---|---|
| F1 | `gamma_per_cycle` is a per-direction symmetric CTMC jump rate times one cycle, so the endpoint kernel has `p_flip=(1-exp(-2 gamma_per_cycle))/2` and autocorrelation `exp(-2 gamma_per_cycle lag)` | literature + code convention |
| F2 | if a stationary RTN value `v s(t)` is declared as a longitudinal free-induction splitting, its exact coherence is the Bergli/Wold factor, and independent RTNs multiply | literature-closed diagnostic formula |
| F3 | substituting the repository defaults into that continuous-time CTMC diagnostic produces a non-monotone `|L(t)|`, hence BLP backflow and non-CP-divisibility of that diagnostic reduced map | project derivation grounded by F1/F2 + BLP/RHP |
| F4 | a separately declared cycle-held phase diagnostic has an exact finite-state transfer-matrix characteristic function | project-defined algebra + independent oracle, not a literature claim |
| F5 | either diagnostic is the production coupled QEC channel or determines the syndrome-record memory | must remain unsupported unless a bridge is found |

## Object identity and code mapping

The production class in `src/error_coupling_simulator/source/process.py` samples `K` independent
two-state chains at cycle boundaries. It emits

```text
z_r = sum_k v_k s_{k,r},
v_k = amplitude_radns / sqrt(K),
gamma_k = geomspace(gamma_min_per_cycle, gamma_max_per_cycle, K),
p_k = (1-exp(-2 gamma_k))/2.
```

Production `CoupledCycleTeacher` does not apply `z_r Z/2` as the Bergli Hamiltonian. It sends `z_r`
through `trajectory_to_params`, which modulates multiple rates/parameters. Therefore:

- **continuous-CTMC FID lift:** interpolate each endpoint chain by the symmetric CTMC whose
  semigroup exactly gives the implemented endpoint kernel, then declare `z(t) Z/2`;
- **cycle-held FID lift:** hold the sampled `s_{k,r}` fixed inside each cycle and declare the same
  longitudinal phase only for this diagnostic;
- **production coupled teacher:** a third, different object, not adjudicated by either lift.

## Coverage ledger

| row | required evidence | source(s) | directness | status | consequence |
|---|---|---|---|---|---|
| symmetric RTN rate convention | directional versus total rate and autocorrelation | Bergli et al., NJP 11, 025002 (2009), Eq. (15); Wold et al., PRB 86, 205404 (2012), Eqs. (9)–(10) | two direct primary sources | closed | use `Gamma=2 gamma`, not `Gamma=gamma` |
| exact single-RTN FID coherence | exact non-Gaussian characteristic function | Bergli Eq. (35); Wold Eq. (12) under `Gamma=2 gamma`, `xi=v` | two direct primary sources | closed | Gaussian surrogate cannot replace strong finite RTN |
| independent product coherence | factorization of independent characteristic functions | Bergli text immediately before Eq. (39); elementary probability factorization | one direct source + transparent algebra | closed as algebra, not a two-paper empirical claim | multiply exact factors only under independence |
| BLP revival criterion | increase of trace distance witnesses non-divisibility | Breuer–Laine–Piilo, PRL 103, 210401 (2009), Eqs. (9)–(12) | direct primary | closed |
| RHP CP-divisibility criterion | intermediate CP maps / pure-dephasing negative-rate criterion | Rivas–Huelga–Plenio, PRL 105, 050403 (2010), Eqs. (2)–(4) | direct primary | closed |
| code endpoint mapping | implemented flip kernel and independent states | `RTNSource`, `OneOverFDriftSource`, source closed-form tests | direct implementation evidence | closed for endpoints | does not specify an intra-cycle Hamiltonian |
| continuous intra-cycle path | CTMC semigroup interpolation | declared diagnostic lift | project choice consistent with endpoints | bounded/project-defined | never call it production semantics |
| cycle-held path | phase held at each emitted endpoint | declared diagnostic lift | project choice | bounded/project-defined | score separately from CTMC lift |
| source-to-production reduced map | actual multi-parameter `Theta` fan-out plus gates/reset | no paper or exact project derivation found | missing | open | no production RHP/BLP verdict |
| reduced map to full QEC record | channel/instrument/full-record bridge | no direct paper found | missing | open | no notion-2 or LER inference |

## Full-text evidence

### Bergli, Galperin, Altshuler (2009)

Deep note:
[`bergli_galperin_altshuler_rtn_0904.4597.md`](../papers/reading_notes/bergli_galperin_altshuler_rtn_0904.4597.md).
The rendered PDF verifies that `gamma_12=gamma_21=gamma` gives
`C(t)=exp(-2 gamma t)` (Eq. 15), that Eq. (35) solves the exact single-fluctuator FID problem, and
that independent partial coherences multiply immediately before Eq. (39).

### Wold, Brox, Galperin, Bergli (2012)

Deep note:
[`wold_brox_galperin_classical_telegraph_1206.2174.md`](../papers/reading_notes/wold_brox_galperin_classical_telegraph_1206.2174.md).
The rendered PDF verifies `Gamma=Gamma_-+ + Gamma_+-` (Eq. 10) and the exact symmetric-telegraph
coherence (Eq. 12). With equal directional rates, `Gamma=2 gamma`, so the formula independently
matches Bergli Eq. (35).

### Reduced-map criteria

The existing full-text notes
[`blp_nonmarkovianity_measure_0908.0238.md`](../papers/reading_notes/blp_nonmarkovianity_measure_0908.0238.md)
and
[`rhp_nonmarkovianity_measure_0911.4270.md`](../papers/reading_notes/rhp_nonmarkovianity_measure_0911.4270.md)
ground the observable and CP-divisibility criteria. They do not identify the classical source with
a production QEC dynamical map.

## Search-exhaustion record for the missing QEC bridge

Local discovery was run first with the repository RAG for exact finite RTN, product coherence,
CP-divisibility, PEPS/QEC records, and with the knowledge-graph query tool. AnySearch then queried
the `academic.search` vertical on 2026-07-13 with:

1. `exact random telegraph noise dephasing surface code syndrome measurement full record`;
2. `finite telegraph fluctuator CP divisibility quantum error correction`;
3. `random telegraph noise QEC multi-round syndrome record non-Markovian`;
4. `process tensor random telegraph noise quantum error correction instrument`;
5. `independent random telegraph fluctuators product coherence CP divisibility`.

The search returned adjacent RTN/open-system or QEC studies, but no primary paper deriving this
repository's `z -> Theta -> quarter-CZ/measurement/reset -> full record` bridge. Five external
queries are enough to mark the row **missing**, not enough to claim a globally
`confirmed-literature-gap`; no nonexistence claim is made.

## Operation replay ledger

| input | transformation | assumption | output | evidence | status |
|---|---|---|---|---|---|
| `gamma_per_cycle` | `p=(1-e^-2gamma)/2` | stationary symmetric chain | endpoint transition matrix | Bergli Eq. (15) + source code | matched |
| `v,gamma` | solve second-order FID ODE | longitudinal pure dephasing | `L_k(t)` | Bergli Eq. (35), Wold Eq. (12) | matched |
| `K` chains | multiply characteristic functions | statistical independence | `L(t)=product_k L_k(t)` | Bergli before Eq. (39) + source construction | matched |
| default values | unit conversion `v cycle`, `gamma cycle` | diagnostic Hamiltonian declared | three strong modes | project arithmetic + registered gate (imperfect Git preregistration provenance) | matched |
| `L(t)` | test positive excursions of `|L|` | pure dephasing optimal pair | BLP witness | BLP Eqs. (9)–(12) + exact gate | matched for both named lifts |
| source endpoints | full production fan-out and instrument | actual schedule/gates/reset | QEC record law | no bridge | unsupported |

## Disconfirmation and contrary evidence

- The positive-covariance Gaussian second-cumulant surrogate is monotone, but Bergli shows that
  identical two-point information is insufficient for a strongly coupled non-Gaussian RTN. It is a
  negative control, not ground truth for F2/F3.
- The source's endpoint kernel does not choose a unique physical intra-cycle trajectory; CTMC and
  held-cycle lifts must be reported separately.
- Even a positive BLP witness for either lift establishes only the declared one-qubit reduced map.
  It does not certify a quantum bath, process-tensor quantum memory, record Markov order, or decoder
  relevance.
- Zeros of `L(t)` make a logarithmic time-local generator singular. The primary robust witness is a
  zero-to-nonzero or trough-to-peak increase of `|L|`, not a numerically integrated log-rate through
  the singularity.

## Closure verdict and propagation gate

- `closure_status: open`
- `F1: closed`
- `F2: closed for the declared free-induction diagnostic`
- `F3: closed for the continuous-CTMC free-induction diagnostic`
- `F4: closed for the project-defined held-cycle free-induction diagnostic`
- `F5: missing/open`

**Post-closure gate:** the registered two-formulation diagnostic passed and was independently
reproduced, but its first run preceded the prediction document's Git commit; see
[`finite_rtn_exact_cpdiv_result_2026-07-13.md`](finite_rtn_exact_cpdiv_result_2026-07-13.md). This
changes F3/F4 only and does not close F5.

**Stopped propagation:** regardless of the gate outcome, do not write “the production source/channel
is CP-indivisible,” “the syndrome record exposes notion-1,” or any QEC/LER conclusion without the
missing fan-out/channel/instrument bridge.

## Primary references

- Bergli, Galperin, Altshuler, *New J. Phys.* **11**, 025002 (2009), DOI
  `10.1088/1367-2630/11/2/025002`.
- Wold, Brox, Galperin, Bergli, *Phys. Rev. B* **86**, 205404 (2012), DOI
  `10.1103/PhysRevB.86.205404`.
- Breuer, Laine, Piilo, *Phys. Rev. Lett.* **103**, 210401 (2009), DOI
  `10.1103/PhysRevLett.103.210401`.
- Rivas, Huelga, Plenio, *Phys. Rev. Lett.* **105**, 050403 (2010), DOI
  `10.1103/PhysRevLett.105.050403`.
