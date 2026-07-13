# Notion 1/2/3 taxonomy — literature closure and correction (2026-07-13)

> **Authority/status:** this note supersedes the old interpretation that notion-1 is
> “quantum CP-divisibility breaking,” notion-2 is every classical residue, or notion-3 is certified by
> the project's `K` statistic. It corrects terminology and access boundaries; it does not authorize a
> new experiment or delete a physical mechanism. `closure_status: partial/open`.
>
> **Evidence gate used here:** a positive load-bearing claim passes only with at least two independent
> peer-reviewed primary sources that address the same atomic object. A project derivation, an internal
> counterexample, or a logical consequence is labeled as such. One counterexample is logically enough to
> refute a universal statement; where available, two published QEC counterexamples are retained.

## Corrected object map

The three labels are **non-exclusive coordinates**, not mutually exclusive notions and not a strength
ladder.

1. **Notion-1 — reduced-dynamics criteria.** RHP CP-divisibility and BLP trace-distance
   backflow are two distinct reduced-map diagnostics. They are not generally equivalent and neither
   certifies that the underlying environment or memory carrier is quantum.
2. **Notion-2 — observed-record memory/order.** This concerns the joint outcome law
   `P(M_1,...,M_R)` under a declared instrument. Markov order is a conditional-independence property of
   this law. It does not identify the reduced dynamical map, bath type, or classical-versus-quantum
   origin without an additional bridge.
3. **Notion-3 — process-level memory carrier/backaction.** Classical versus quantum memory is a
   property of the multi-time process/process tensor and its allowed interventions or testers. A
   process-tensor entanglement witness is sufficient evidence for quantum memory in its stated scope;
   it is **not** a complete `iff` classification. Taranto et al. explicitly distinguish classical-memory,
   separable, and more general quantum-memory process classes.

## Claim-by-claim evidence gate

| atomic claim | primary evidence | gate | permitted wording |
|---|---|---|---|
| RHP CP-indivisibility and BLP backflow are different reduced-map criteria | Rivas–Huelga–Plenio, PRL 105, 050403 (2010), Eqs. 2–4; Breuer–Laine–Piilo, PRL 103, 210401 (2009), Eqs. 9–12; Chruściński–Kossakowski–Rivas, PRA 83, 052128 (2011), inequivalent examples | **pass, 3 direct** | name the criterion actually computed; never write `RHP=BLP` as a general identity |
| reduced-map non-Markovianity/backflow does not certify a quantum bath | Lo Franco et al., PRA 85, 032318 (2012), classical random fields without system-bath backaction; Cialdi et al., PRA 100, 052104 (2019), classical Markov RTN with trace-distance revival; also Megier et al., Sci. Rep. 7, 6379 (2017), classical Markov realization of non-CP-divisible dynamics | **pass, >=2 direct counterexamples** | `N1 is not a quantum-origin certificate`; do not claim all N1 dynamics are classical |
| the repository's positive-exponential-covariance **Gaussian surrogate** is CP-divisible, while two declared finite-RTN free-induction lifts show BLP backflow | Bergli et al., NJP 11, 025002 (2009), Eq. 35; Wold et al., PRB 86, 205404 (2012), Eqs. 10/12; BLP criterion; exact project product/256-state gate | **two direct formula sources + exact project diagnostic; not a production-channel bridge** | report the mathematical object actually evaluated; do not transfer either the surrogate null or diagnostic-positive result to the production `z -> Theta` QEC map |
| Markov-1 of the record requires independence from the entire earlier history, conditioned on the immediate past | Milz et al., PRX 10, 041049 (2020), K-Markov definition; Anderson–Goodman, Ann. Math. Stat. 28, 89 (1957), finite-order Markov definitions/tests | **pass, 2 direct** | `I(M_r;M_{<r-1}|M_{r-1})=0` over all relevant times/histories is the process-wide condition |
| lag-2 CMI is local and a finite order ladder can miss longer/infinite-order structure | the preceding full-history definitions; Marzen–Crutchfield, J. Stat. Phys. 163, 1312 (2016); Crutchfield–Feldman, Chaos 13, 25 (2003), finite-context counterexamples | **pass for the limited diagnostic boundary** | three-time CMI and finite `G^2` are diagnostics, not global Markov/HMM no-go theorems |
| CP-divisibility and multi-time process Markovianity are different objects | Pollock et al., PRL 120, 040405 (2018), explicit CP-divisible/non-Markovian process; Milz et al., PRL 123, 040401 (2019), classification of CP-divisible processes with temporal correlations | **object distinction supported; conservative status remains open for a two-independent-construction gate** | never infer record memory or its absence from CP-divisibility alone |
| classical versus quantum memory belongs at the multi-time process level | Giarmatzi–Costa, Quantum 5, 440 (2021), process-memory witnesses; Taranto et al., Quantum 8, 1328 (2024), multi-time classical-memory hierarchy | **pass, 2 direct** | process-level, instrument-relative wording only; temporal entanglement is sufficient evidence, not an `iff` |
| general process-memory identification needs a family of interventions/testers | Pollock et al., PRA 97, 012127 (2018), process tensor; Giarmatzi–Costa (2021), CP-map interventions; White et al., PRX Quantum 3, 020344 (2022), restricted-process-tensor boundary | **pass, 3 direct** | a fixed instrument accesses a restricted process; do not claim full process identification from one record law |
| the project's `K` is a Kolmogorov/non-invasiveness protocol comparison, not a one-record quantum-memory metric | Milz et al. (2020), measure-versus-omit Kolmogorov condition; Smirne et al., QST 4, 01LT01 (2019), non-classical statistics from Markovian coherence-generating-and-detecting dynamics | **pass for the weaker object/scope claim** | `K>0` can witness inconsistency/invasiveness for that protocol family; it does not by itself identify a quantum bath or quantum memory |
| the specific Markovian amplitude-damping `K` forgery in this repository is published externally | only the project's own control currently instantiates that exact counterexample | **internal counterexample only** | retain as a bug-catching negative control, not literature fact |
| one fixed finite record distribution has a classical history-dependent chain-rule generator | elementary probability factorization; related process papers discuss fixed-instrument classical distributions, but two papers were not found proving this exact no-go as their atomic theorem | **transparent mathematical inference, not a 2-paper literature closure** | use only as an identifiability statement; it does not imply the physical mechanism is classical |

## `K` correction

The repository's statistic compares two protocols:

```text
measure every intermediate time -> P_all
omit an intermediate measurement -> P_skip
```

It therefore does **not** live inside one passive `P(M_1,...,M_R)`. It tests whether marginalizing the
measured protocol agrees with the omitted-measurement protocol, i.e. a Kolmogorov consistency /
non-invasiveness condition for that declared family. The literature supports the following narrow
interpretation:

- `K>0` rules out a shared non-invasive Kolmogorov model for the tested protocols;
- `K>0` does not identify the bath, memory carrier, CP-indivisibility, or quantum memory;
- `K=0` does not rule out quantum dynamics or quantum memory, because visibility is instrument dependent.

The old phrase “no classical process can reproduce `K>0`” was too broad: invasive, contextual, or
protocol-dependent classical models were not excluded. The project may keep notion-3 out of scope as a
product decision, but not as a universal physical no-go theorem derived from `K`.

## Interaction with coherent leakage

Coherent leakage is first a **channel -> instrument -> full-record reachability** question. It is not
automatically notion-1, notion-2, or notion-3:

- it is notion-1 only if the relevant reduced-map criterion fires;
- it contributes to notion-2 only if it changes cross-time dependencies in the observed record;
- it bears on notion-3 only if the process-level memory carrier/backaction is being certified.

Two peer-reviewed QEC papers directly refute the old universal “syndrome extraction exactly twirls the
coherent leakage away” premise: Marshall–Kafri (PRApplied 23, 054025, 2025) find nonzero exact-versus-STA
differences in d3 detector/LER observables, and Manabe–Suzuki–Darmawan (NJP 27, 114512, 2025) find a
more-than-threefold GTA LER overestimate in a repetition-code MLR regime. Varbanov et al. (npj Quantum
Information 6, 102, 2020) provide a useful opposite, schedule-specific null. The permitted conclusion is
therefore **“coherence can survive and matter, depending on channel, schedule, and instrument,”** not
“always survives.” The project's quarter-CZ XZZX full-record bridge remains open.

## Interaction with long-range/loopy truncation

WTG/FET/ZMT quantities describe virtual-loop structure and state/environment approximation. They are not
notion-2 temporal Markov-order metrics. The following distinctions are mandatory:

- virtual loop/gauge structure;
- physical spatial correlations;
- temporal dependencies in the observed record;
- classical versus quantum process memory.

Evenbly (PRB 98, 085155, 2018) proves direct top-WTG optimality only at zero cycle entropy and proposes
iterative FET when the direct argument is lost. McKeever–Szymańska (PRX 11, 021035, 2021) optimize a
CTMRG-environment normalized Hilbert-Schmidt alternative fidelity. Sokolov–Zhang–Dziarmaga (PRE 112,
055307, 2025) give exact zero-mode identities and ZMT initializers. These are **scope facts from separate
papers**, not two no-go theorems about QEC records. They do not supply a full-record TV/comb-norm/rare-LER
guarantee, but the audit also does not prove that such a guarantee is impossible. The project-specific
PEPS-truncation-to-record bridge remains `missing/open`.

## Correct verdicts for notion 1/2/3

- **Notion-1:** corrected definition is literature-grounded. The Gaussian-surrogate null and exact
  finite-RTN diagnostic-positive results are model-specific. A stochastic source alone has no
  reduced-map status; the production fan-out/QEC map and its reachability from the syndrome record
  remain open.
- **Notion-2:** the record-memory object and full-history Markov condition are grounded. Lag-2 CMI,
  asymptotic `G^2`, and project-defined `E(k)` must remain diagnostics with declared assumptions.
- **Notion-3:** the process-level object and need for richer intervention/tester access are grounded.
  The old identification `K == quantum memory` and the universal physical-twirl closure are retracted.
- **Cross-object use:** none of these labels authorizes deleting coherent leakage or declaring a
  long-range PEPS truncation record-faithful.

## Open rows and propagation gate

1. A source-to-production-reduced-map derivation that includes the actual multi-parameter `Theta`
   fan-out, gates, measurement, and reset; the completed free-induction diagnostic is not that map.
2. A published or independently exact bridge from this repository's finite-RTN implementation to the specific QEC
   record instrument.
3. The exact quarter-CZ coherent-versus-pinched XZZX full-record comparison with explicit ancilla dynamics.
4. A global cq-record/comb-norm or direct exact-d3 certificate for PEPS/FET/ZMT truncation, including
   `epsilon << p_L` for rare logical events.

Until these rows close: documentation correction is allowed; scientific claim propagation, code deletion,
and new truncation choices justified by the old notion taxonomy are stopped.

## Primary references

- Rivas, Huelga, Plenio, PRL 105, 050403 (2010), DOI `10.1103/PhysRevLett.105.050403`.
- Breuer, Laine, Piilo, PRL 103, 210401 (2009), DOI `10.1103/PhysRevLett.103.210401`.
- Chruściński, Kossakowski, Rivas, PRA 83, 052128 (2011), DOI `10.1103/PhysRevA.83.052128`.
- Lo Franco et al., PRA 85, 032318 (2012), DOI `10.1103/PhysRevA.85.032318`.
- Cialdi et al., PRA 100, 052104 (2019), DOI `10.1103/PhysRevA.100.052104`.
- Pollock et al., PRL 120, 040405 (2018), DOI `10.1103/PhysRevLett.120.040405`.
- Milz et al., PRL 123, 040401 (2019), DOI `10.1103/PhysRevLett.123.040401`.
- Milz et al., PRX 10, 041049 (2020), DOI `10.1103/PhysRevX.10.041049`.
- Smirne et al., QST 4, 01LT01 (2019), DOI `10.1088/2058-9565/aaebd5`.
- Giarmatzi, Costa, Quantum 5, 440 (2021), DOI `10.22331/q-2021-04-26-440`.
- Taranto et al., Quantum 8, 1328 (2024), DOI `10.22331/q-2024-05-02-1328`.
- Marshall, Kafri, PRApplied 23, 054025 (2025), DOI `10.1103/PhysRevApplied.23.054025`.
- Manabe, Suzuki, Darmawan, NJP 27, 114512 (2025), DOI `10.1088/1367-2630/ae1529`.
- Varbanov et al., npj Quantum Information 6, 102 (2020), DOI `10.1038/s41534-020-00330-w`.
- Evenbly, PRB 98, 085155 (2018), DOI `10.1103/PhysRevB.98.085155`.
- McKeever, Szymańska, PRX 11, 021035 (2021), DOI `10.1103/PhysRevX.11.021035`.
- Sokolov, Zhang, Dziarmaga, PRE 112, 055307 (2025), DOI `10.1103/4lgp-ld2s`.
