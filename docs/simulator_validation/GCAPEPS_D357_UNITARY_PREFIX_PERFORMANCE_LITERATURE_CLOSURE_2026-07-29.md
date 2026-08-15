# GCAPEPS \(d=3,5,7\) unitary-prefix performance sweep — literature closure

Date: 2026-07-29

Status: **closed for one bounded, equal-status, performance-only comparison;
not closed for state faithfulness, a measurement/reset/Record claim, or a
general speedup claim**

## Frozen claim

On one frozen machine and process envelope, compare two implementations of the
same complex128, surface-code-shaped unitary workload:

1. ordinary Quimb physically applies the full Clifford prefix to an
   arbitrary-graph PEPS and then applies one local non-Clifford Pauli rotation;
2. GCAPEPS stores the identical Clifford prefix in a Stim tableau and lowers
   the signed pullback of the identical physical Pauli rotation into its Quimb
   residual by the current tree-routed carrier.

The only claim-bearing outputs are current-implementation elapsed time,
completion/censoring, process memory, and representation-resource ledgers for
the frozen \(d=3,5,7\) fixtures. The two lanes are equal-status candidates.
Neither is a truth source.

The workload stops before the first measurement. It therefore computes no
Born mass, conditional state, reset, detector/observable Record, logical error
rate, or whole-state fidelity. The absence of those objects is an exclusion,
not an unimplemented surrogate.

## Mechanism and observable bridge

The algebraic state split is

\[
|\psi\rangle=C|\phi\rangle ,
\qquad
R_Y^{(a)}(\theta)
=\exp[-i\theta Y_a/2].
\]

The ordinary lane evaluates \(R_Y^{(a)}(\theta)C|0^n\rangle\) by physical
Quimb gate application. The GCAPEPS lane updates the frame by \(C\), computes

\[
Q=C^\dagger Y_a C,
\qquad
R_Y^{(a)}(\theta)C
=C\exp[-i\theta Q/2],
\]

and applies the rank-two Pauli rotation to the residual. The signed pullback,
support, route, and construction-resource ledger are fixture invariants.
Above ten qubits, the carrier's same-IR dense action audit is deliberately
unavailable; no full vector, norm, or contraction-derived scalar is requested.

The sweep uses Quimb's documented arbitrary-graph
`CircuitPEPSSimpleUpdate`, so the active widths are
\(n(d)=2d^2-1=17,49,97\). No rectangular dummy sites are introduced.

## Coverage ledger

| load-bearing row | source | exact locator | status and use |
|---|---|---|---|
| Clifford-frame/tensor-residual split and Pauli pull-through | Harper et al. source review | `docs/papers/reading_notes/harper_hybrid_surface_code_2605.29514v1_source_review.md`, Secs. III–IV and source-located equations recorded there | `CLOSED_ADJACENT`; the paper supplies an MPS precedent, not a PEPS speed theorem |
| rotated-surface-code-shaped repeated workload motivation | Harper et al. source review | same note, Secs. II and V, Fig. 1 discussion | `CLOSED_ADJACENT`; this packet uses only a first-measurement unitary prefix |
| exact uncompressed tree-routed Pauli-sum representation | project theorem and correspondence audit | `GCAPEPS_MATHEMATICAL_FEASIBILITY_THEOREM_2026-07-27.md`, Lemma 3 and Eqs. (9), (11), (13), (16), (17); `GCAPEPS_IMPLEMENTATION_THEOREM_CORRESPONDENCE_2026-07-28.md`, §§2–7 | closed only for the bounded construction/resource contract; generic equivalence remains open |
| exact-small implementation anchor | completed \(n=8,r=3\) closure/prereg and formal run | `GCAPEPS_N8_R3_DUAL_CANDIDATE_DIFFERENTIAL_LITERATURE_CLOSURE_2026-07-29.md` and its preregistration | construction prerequisite only; it does not transfer large-state truth |
| arbitrary-graph plain carrier | frozen Quimb fork public API | `quimb/tensor/circuit/peps.py`, `CircuitPEPSSimpleUpdate` class and constructor | closed engineering input path |
| runtime, RSS, and representation ledgers | project benchmark definition | this packet and its preregistration | direct engineering observables; not literature claims |
| generic contraction boundary | Schuch et al. VOR source review | `docs/papers/reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md`, VOR PDF pp. 2–3 | forbids promotion to generic efficient contraction or scalable state correctness |

## Disconfirmation and exclusions

- A fixture, signed-pullback, route, dtype, cutoff, operation-count, or import
  isolation failure makes timing ineligible.
- A timeout, memory limit, or preregistered construction-resource guard is a
  censored performance result and is not relabelled as a correctness failure.
- A lower GC bond or tensor count does not imply a lower wall time.
- Three finite distances do not establish an asymptotic exponent.
- The active rank in this sweep is two. It must not be joined to the separate
  \(n=8,r=3\) point as a one-parameter scaling series.
- Stim and an untimed SDIM-qubit check may corroborate signed Clifford
  pullbacks. Neither supplies a PEPS truth state.
- Generic coherent Pauli sums currently request a full candidate norm. This
  sweep instead uses the carrier's algebraically certified unitary
  `apply_pauli_rotation` path and never calls a PEPS norm.
- The common SimpleUpdate floating cutoff is the repository numerical
  constant \(10^{-12}\), with no finite bond cap. This is not an exact-state or
  matched-accuracy certificate.

## Search record and verdict

The artifact-verified local corpus was audited. The admitted Harper hybrid
surface-code note, the GCAPEPS theorem/correspondence packet, the completed
exact-small packet, and the Schuch complexity note were read at their
source-located sections. No external acquisition was required because this
packet makes no novelty, literature-gap, physical-calibration, or universal
performance claim; the benchmark metrics and workload are explicitly
project-defined.

```text
closure_status =
  CLOSED_FOR_BOUNDED_EQUAL_STATUS_D357_UNITARY_PREFIX_PERFORMANCE
PASS_TO_PREREG = yes
PASS_TO_CODE = yes, after the preregistration is committed before experiment code
independent_large_state_truth_required = no, because no state/faithfulness estimand exists
Record_or_measurement_claim = excluded
generic_speedup_or_scaling_claim = forbidden
```
