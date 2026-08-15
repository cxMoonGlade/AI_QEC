# PEPS XZZX measurement/reset/Record bridge — pre-target implementation audit

Date: 2026-07-27
Status: **RED for preregistration v1; no formal tracer, d3, or d5 result is admissible**

## Scope and chronology

This audit was performed after the literature packet and preregistration v1
were frozen in commit `15bb541`, but before any formal target execution. It
reviews implementation paths, source semantics, artifact seams, and
corruption controls. It does not inspect a PEPS target score.

One earlier d3 plumbing smoke was executed before the implementation freeze.
It is explicitly non-admissible, is not quoted here, cannot select a branch,
band, bond dimension, graph radius, or reference route, and must be rerun from
a later committed target bundle if the replacement preregistration passes.
The ignored directory
`outputs/simulator_validation/xzzx_record_aer_d3_IpisfjL4/` is excluded from
all evidence and final verdicts.

The v1 identities remain byte-frozen:

- literature closure SHA-256:
  `ab035b00d3ee05c4e4e43d1db7289b985b0673bd252a1993dc20112401a4518a`;
- preregistration v1 SHA-256:
  `158cc67e40d3c7a7988326dfc82f54651355e58d1bd007fc954f3061b355d007`;
- d3 fixture / run-spec:
  `3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c`
  /
  `11e86c8d205899d51440a7fab32dc31f046e723a047c4c7bc8fe9fed3f7e15b9`;
- d5 fixture / run-spec:
  `659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495`
  /
  `092353542f2e9e329f4d3ed735d0e6a10caa88bc048478ee15cc06aefc60ef23`.

## 1. Aer-MPS reference kill

Pinned Qiskit Aer clone:

- commit `837c3ef3c39248aae936580360c22224dcefb265`;
- clean, non-shallow worktree at audit time.

The v1 preregistration required a true zero-truncation Aer-MPS reference.
That requirement is impossible for the pinned implementation:

1. `external/baselines/qiskit-aer/src/simulators/matrix_product_state/svd.hpp`
   line 25 defines `CHOP_THRESHOLD` as `1e-16`.
2. `svd.cpp` lines 83-96 first reduces the retained singular-value count
   using squared magnitude greater than that fixed threshold. Positive
   Schmidt coefficients with magnitude at most `1e-8` can therefore be
   removed even when the user option is `0.0`.
3. `svd.cpp` lines 123-131 computes `discarded_value` only inside the already
   reduced singular-value range. The hidden fixed-chop loss is not reported
   by the metadata that v1 intended to audit.

Consequently, the tuple

```text
user threshold = 0
discarded_value_count = 0
discarded_value_sum = 0
```

does not prove an untruncated MPS. No independent d5 oracle in v1 could prove
that no positive coefficient entered the hidden chop interval during the
whole trajectory. This directly fires the v1 kill condition “Aer applies a
hidden MPS cap/truncation.” Aer-MPS is unavailable as exact d5 ground truth;
its installed environment may be retained only for non-claim-bearing
diagnostics.

Additional Aer blockers found before the kill was applied included incomplete
per-reset trace-distance evidence, a metadata-only rather than executed
Bell/cap-one corruption, weak environment/source provenance, silent dtype
coercions, and a summary/branch seam that could not bind the sampled primary
branch into the dense replay.

## 2. Quimb candidate blockers

Pinned Quimb clone:

- commit `3c89529fe0a3487133a3928201691161e110abdf`;
- tree `d81d043a27b7abf20e6c3a423f9b772682bbef40`;
- clean, non-shallow worktree at audit time.

The first candidate implementation is also target-red:

1. The d2 enumerator classified every finite
   `0 < p <= (64*eps)^2 ~= 2.019e-28` as structural zero. This is a forbidden
   probability floor. A positive candidate probability must be propagated or
   the whole point must become `UNAVAILABLE`.
2. The measurement path clamped small negative probabilities to zero and
   values above one to one. Invalid Born operators must instead fail closed.
3. The reset path first accepted an RDM within a tolerance of `|0><0|` and
   then reapplied `P0`. This can delete real contamination and improve the
   fidelity operand. The direct normalized rank-one reset
   `A_b=|0><b|` already produces an exact physical-one tensor zero in CPU and
   CUDA probes; that exact slice must be checked without a corrective
   projection.
4. Reconstructing `CircuitPEPSSimpleUpdate(psi0=poststate)` invokes upstream
   `gauge_all_simple_` with default smudge and measurably contaminates reset
   slices. Direct rank-one application avoids this, but the continued
   simple-update gauge rule must be separately frozen and falsified.
   A subsequent public zero-smudge equilibration probe passed a Bell state
   but failed at the first d2 reset: the upstream simple-bond gauge routine
   forms `1/s` for outer gauges and exact-zero entries produced non-finite
   tensors/RDMs. That refresh route is therefore also rejected. V2 instead
   freezes byte-preservation of the existing heuristic gauges across the
   one-site rank-one gate and makes its downstream approximation part of the
   measured error.
5. Pinned Quimb `Circuit.copy()` shares `_backend_gate_cache` between
   siblings, while the cache key is the Python identity of a transient NumPy
   gate array. A CUDA probe observed stale-ID collisions in 198 of 200
   iterations, applying an old sibling gate to a new branch. Each branch must
   isolate this cache and pass a CUDA regression.
6. The emitted branch accepted and republished arbitrary extra fields,
   violating the bits-only reference firewall. The candidate must reconstruct
   an exact neutral branch object from validated outcome bits.
7. The worker/comparator seam disagreed on reset-slice representation and the
   worker omitted the required explicit `forbidden_substitute_used=false`.

No 1024-path Quimb tracer target and no d5 target was run during this audit.

After the no-refresh policy was selected, a test-first d3/D8 reset-policy
control used dense-greedy bits under the v1 fixture/spec. It was not the v1
Aer primary, the v2 hash-selector primary, or the alternate. The test computed
its comparison only in memory, emitted only pytest PASS, and wrote no
summary/state/target artifact; no numeric value was printed or inspected.
This is retained solely as a reset-policy implementation control and is
excluded from every formal d3/d5 result. The v1 bands predate it and the v2
bands are unchanged.

## 3. Fixture/dense and artifact-seam blockers

The fixture hashes, operation directions, two RY placements, dense tensor-axis
conventions, exact d2 1024 support, and absolute ragged XOR fold passed their
focused semantic tests. The first formal CLI still failed closed-evidence
requirements:

- a public `greedy` mode and an arbitrary root-level `branch.v1` input could
  masquerade as the frozen primary;
- alternate output dropped its flip column and parent-primary provenance;
- emitter and dense outputs used replacement publication, permitted aliases,
  and could overwrite an existing artifact;
- input bytes, environment lock, interpreter/NumPy identity, and branch
  artifact were not completely bound;
- the `MR -> M` corruption did not separately demonstrate the reset-state
  failure.

The route-independent immutability, alias, provenance, second-RY, and
reset-corruption defects were repaired under tests before any target run.
Reference/branch authority remains governed by the replacement
preregistration, not by the old CLI modes.

## 4. Exact-reference recovery probe

The noiseless syndrome shells contain Clifford gates, with the only
non-Clifford intervention applied to data qubits between complete rounds. A
pre-target `/tmp`-only prototype therefore eliminated reset ancillas exactly.
For each measured ancilla `a`, Clifford back-propagation produced

```text
U_round^dagger Z_a U_round = + Z_a S_a,
Pi(a,b) = (I + (-1)^b S_a) / 2
```

on a data-only state. The checks commute pairwise. Both frozen rounds have the
same tableau, and the actual interleaved shell is tableau-equivalent to the
grouped independent-ancilla measurement shell. For d5 there are 24 checks:
eight weight-two and sixteen weight-four.

Pre-target equivalence evidence, not a target result:

- four robust d2 forced branches;
- d3 greedy, frozen-alternate, and three independently sampled forced
  branches;
- maximum per-column `p0/p1` disagreement with the existing complete
  7/17-qubit dense route about `1.7e-15`;
- maximum phase-aligned checkpoint-amplitude disagreement about `5.6e-17`;
- fidelity error at most `4.4e-16`.

A generic, non-fixture 24-qubit one-thread memory benchmark measured
`0.922401339 s` for six projector updates and `2.170934623 s` for one
all-qubit RY layer. GNU time measured peak RSS `1,094,204 KiB` for the whole
validation/benchmark process. A linear kernel estimate for 25 data qubits is
about `22.45 s` for 73 selections plus `9.05 s` for two RY layers; the formal
worker/I/O budget remains a conservative one to three minutes and below
`4 GiB`. This is expected to remain far inside the frozen
`1800 s / 64 GiB` gate. The estimate is a resource hypothesis, not a d5
result.

This route is scientifically stronger than Aer-MPS for the bounded fixture:
it uses a complete `2^25` complex128 vector, has no tensor truncation or
probability floor, and shares no Quimb tensors, gauges, contraction paths, or
probabilities. It is permitted only through a new preregistration frozen
before its formal branch is generated.

## 5. Disposition

- Preregistration v1: **killed before target execution**.
- V1 bands and claim boundaries: not relaxed and not re-fit.
- Formal Aer-MPS d5 fidelity: **forbidden**.
- Existing plumbing smoke: **non-admissible**.
- Next possible gate: a superseding v2 preregistration with the exact
  data-projector reference, an implementation-fixed Quimb reset/gauge/cache
  path, unchanged PEPS bands, and new hash-bound branch-selector specs.
- Current target gate: **RED** until v2 is independently reviewed, committed,
  implemented, corruption-tested, and reviewed again as committed artifacts.
