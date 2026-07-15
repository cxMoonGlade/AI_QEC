# Full-text review — Breuer, Laine, Piilo, “Measure for the degree of non-Markovian behavior of quantum processes in open systems” (arXiv:0908.0238v2)

> **Provenance (2026-07-15): FULL-TEXT clean-room read.** Local PDF
> `outputs/papers/0908.0238.pdf`, SHA-256
> `9e05b98a5b6a902be4fa8d4d2662b7e9b7592d150ddef6bf74a8d6e9f9bf4553`, four
> pages; full extracted text `outputs/papers/0908.0238.txt` traversed. PDF pages 2 and 3 were
> rendered and visually inspected for Eqs. (5), (9)–(13) and their quantifiers. This note contains
> paper facts and source-local gaps only. Application-specific inference is kept in a separate
> simulator claim packet.

## Metadata [paper]

- Heinz-Peter Breuer, Elsi-Mari Laine, and Jyrki Piilo.
- *Physical Review Letters* **103**, 210401 (2009), DOI
  `10.1103/PhysRevLett.103.210401`; arXiv:0908.0238v2, 5 January 2010.
- Theory paper defining a trace-distance information-backflow measure.

## Executive summary [paper]

The paper defines non-Markovian behavior through temporary growth of the trace distance between a
pair of evolving system states. A divisible family with positive trace-preserving intermediate maps
cannot increase trace distance; therefore any observed increase witnesses non-divisibility. The BLP
measure sums all positive trace-distance excursions and maximizes over initial-state pairs.

## Selection and coverage [ours]

Assigned rows: observable definition, divisibility-to-contraction implication, positive-excursion
witness, and pure-dephasing maximizing-pair example. The paper does not identify a classical noise
source alone with a quantum dynamical-map family and does not bridge a reduced-state witness to a
multi-time measurement record.

## Notation and source-location ledger [paper]

| symbol | domain and meaning | quantifier/assumption | source location |
|---|---|---|---|
| `D(rho_1,rho_2)` | half trace norm of the state difference | density operators on the same system | Eq. (1), PDF p. 1 |
| `Phi(t,0)` | dynamical map from time zero to `t` | physical state map | Eqs. (6)–(9), PDF p. 2 |
| `Phi(tau+t,t)` | intermediate map | CPT for the paper's divisible class | Eq. (9), PDF p. 2 |
| `sigma(t,rho_1,2(0))` | time derivative of trace distance | fixed initial pair | Eq. (10), PDF p. 2 |
| `N(Phi)` | total positive trace-distance growth | maximum over all initial pairs | Eqs. (11)–(12), PDF pp. 2–3 |

## Method and observable [paper]

Trace distance is

```text
D(rho_1,rho_2) = (1/2) tr |rho_1-rho_2|.                    Eq. (1)
```

A completely positive trace-preserving map is contractive for this metric, Eq. (2). For a divisible
family,

```text
Phi(tau+t,0) = Phi(tau+t,t) Phi(t,0),                       Eq. (9)
```

where the intermediate map is also CPT. Contractivity therefore gives

```text
D(rho_1(tau+t),rho_2(tau+t)) <= D(rho_1(t),rho_2(t)).       Eq. (5)
```

The paper notes that the contraction also holds for positive trace-preserving maps. Thus a positive
rate

```text
sigma(t) = d D(rho_1(t),rho_2(t)) / dt > 0                 Eq. (10)
```

for at least one initial pair is a sufficient witness that the corresponding dynamics lacks that
divisibility property.

The measure is

```text
N(Phi) = max over initial pairs integral_{sigma>0} sigma(t) dt,  Eq. (11)
```

equivalently the maximum of the sum of trough-to-peak trace-distance increases, Eq. (12).

## Mechanism examples [paper]

The first example is a damped Jaynes–Cummings model with a time-local decay rate. Negative-rate
intervals produce positive trace-distance rate for the chosen excited/ground pair, Eq. (13). The
paper explicitly distinguishes a negative instantaneous rate from failure of complete positivity of
the full map: the integrated rate remains nonnegative in that example.

The second example is exact pure dephasing of a central spin. Its coherences are multiplied by
`f(t)=cos^N(2At)` and

```text
D(t) = sqrt(a^2 + f(t)^2 |b|^2),                            Eq. (14)
```

where `a` is the population difference and `b` the coherence difference of the initial pair. For
antipodal equatorial states, `a=0` and `|b|=1`, so `D(t)=|f(t)|`; repeated revivals make the example's
infinite-time BLP sum diverge.

## Findings and limits [paper]

- Any observed trace-distance growth is already a sufficient witness and a lower bound on the
  optimized measure.
- Exact `N(Phi)` generally requires the complete reduced dynamics and maximization over initial
  pairs.
- `N(Phi)=0` for the paper's divisible class. The paper does not establish the converse that absence
  of trace-distance backflow proves complete-positive divisibility for every dynamics.
- A temporary backflow does not imply absence of long-time thermalization.

## Contrary evidence and failure regimes [paper]

The witness is a property of a specified family of system maps acting on specified initial states.
A stochastic source distribution, a single trajectory, or a different multi-time record is not the
object in Eqs. (1), (9), or (11). The examples do not establish which initial pair is optimal for an
arbitrary multi-qubit channel.

## Project kill conditions [ours]

An application fails if it has not defined a common system state space and a dynamical-map family,
if its plotted quantity is not trace distance for a fixed initial pair, or if a discrete grid is used
to claim absence of all possible backflow. Propagation from reduced-state backflow to a measurement
record or downstream estimator requires a separate bridge.

## Operation replay ledger [ours; source-checked]

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| two density operators | half trace norm | common system state space | distinguishability `D` | Eq. (1), PDF p. 1 | matched |
| divisible map family | compose with positive/CPT intermediate map | same fixed initial pair | non-increasing `D` | Eqs. (2), (5), (9), PDF pp. 1–2 | matched |
| one interval with increasing `D` | integrate or take endpoint difference | `sigma>0` on the interval | positive BLP contribution | Eqs. (10)–(12), PDF pp. 2–3 | matched |
| pure-dephasing coherence factor `f(t)` | choose antipodal equatorial pair | populations equal, coherence difference one | `D(t)=|f(t)|` | Eq. (14) and following text, PDF p. 4 | matched |
| classical endpoint source alone | infer a quantum dynamical-map family | not supplied | BLP or divisibility verdict | no source location | missing |

## Relevance and trust [ours]

Use this paper for the trace-distance observable, the one-way divisibility implication, and the
positive-excursion measure. Assigned rows have source-local status `closed`; a bridge from a source
alone or a reduced-state diagnostic to a different record has source-local status `missing`. No
project-specific claim is stored in this literature note.
