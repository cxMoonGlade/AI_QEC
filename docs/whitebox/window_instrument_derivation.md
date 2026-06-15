# Window measurement-instrument derivation — the 9q runtime object

> Theory-first derivation for the step-2 representation redirect (decision brief 2026-06-15, §2).
> The white-box runtime object is a CPTP map on the window's **9 data qubits** with syndromes read
> out by **per-stabilizer measurement instruments** — the explicit ancilla is traced out
> analytically, not carried in the register. This doc states the construction, its epistemic
> status, the caveats it must bound, and the numerical-validation plan against the faithful oracle.
> A derivation + prediction record, not a claim of results.
>
> Scope tags follow the project convention: **(a)** exact (theorem/identity/zero-tolerance),
> **(b)** prediction band (a falsifiable bet; a miss is a finding, never later citable as fact),
> **(c)** heuristic gate/decision rule.
>
> Companion docs: [`window_covering_architecture.md`](window_covering_architecture.md) (the field
> + covering),
> [`window_covering_RESULTS.md`](window_covering_RESULTS.md) (step-1 circuit-derived facts),
> [`surface_recover_registration.md`](surface_recover_registration.md) (the recover registration),
> [`window_channel_spec.md`](window_channel_spec.md) (the `WindowChannel` build spec).

## 0. Why this object exists (the cost + scope forcing function)

Two facts force the redirect from a data+ancilla faithful register to a 9q data register:

1. **Cost.** The bare density matrix scales as `4^n × 16 B`. A 9q data register is
   `4^9 × 16 B = 4.2 MB`. A d7 interior window's faithful register (9 data + ~4 full-in ancilla =
   13 q) is `4^13 × 16 B = 1.07 GB` — a `4^4 = 256×` blow-up over 9q. A d3 patch's faithful
   register (9 data + 8 stabilizers = 17 q) is `4^17 × 16 B = 275 GB` — a `4^8 = 65536×` blow-up,
   infeasible on any single GPU.
2. **White-box scope.** The white-box only models mechanisms that live **entirely inside a window**;
   the d3 patch is the white-box rung (9 data + 8 full-in XZZX stabilizers). Carrying all 8
   ancillas explicitly is exactly the 17q object above. So for d3 the 9q register is not an
   optimisation — it is the only feasible path.

The construction below shows the 9q data register can carry the within-window syndrome and the
data-state evolution **without** an explicit ancilla register, by reducing each stabilizer's local
sub-circuit to a measurement instrument. The faithful explicit-ancilla circuit is **retained only as
a numerical oracle** for validating this reduction (§5) — it is not the runtime representation. Since
the white-box runtime is the **d3 patch**, the oracle is built on the SAME d3 patch (d7 cross-window
is deferred); the full d3 faithful register is 17q (infeasible), so the oracle is run as a
**progressive d3 sub-system** (§5).

## 1. Setup — the faithful single round of one internal stabilizer

A window = 9 data qubits (a 3×3 block; 9 interior, fewer at the boundary). An internal ("full-in")
stabilizer `S` has CZ support `D_S ⊆ {9 data}` with `|D_S| ≤ 4`, plus a dedicated ancilla `a_S`.

One faithful syndrome-extraction round, on the local sub-system `(D_S ⊗ a_S)`, in circuit order:

1. **reset** `a_S → |0>`;
2. **4 CZ layers** coupling `D_S ↔ a_S`, each gate carrying its learnable noise mechanisms
   (CZ-location 2q mechanisms; idle / 1q-gate mechanisms on the spectators) — the coherent
   entangling map that writes the stabilizer parity onto `a_S`;
3. **DD echo + H on data** (the dynamical-decoupling echo and the data-side Hadamards of the XZZX
   schedule);
4. **measure** `a_S` in the computational basis with a **readout flip `p = 0.005`**, then
   **reset** `a_S`.

Everything in steps 1–4 except the final classical readout flip is a fixed (circuit-derived)
sequence of gates and noise channels on `(D_S ⊗ a_S)`; the mechanism strengths are the only free
parameters. The 4-CZ-layer / DD-echo / `p = 0.005` facts are the real-circuit parameters parsed in
step-1 (see [`window_covering_RESULTS.md`](window_covering_RESULTS.md)).

## 2. Key structural fact — the ancilla is reset-decoupled across rounds

`a_S` is **reset to |0> at the start of the round** (step 1) and **measured-then-reset at the end**
(step 4). Therefore `a_S` carries **no information across round boundaries**: there is no
inter-round ancilla entanglement, and the joint state at the start of every round factorises as
`ρ_{D_S} ⊗ |0><0|_{a_S}`.

**Tag (a), conditioned.** This decoupling is **exact under perfect, leakage-free reset** — i.e. the
reset is the ideal channel `· → |0><0|` with no residual population, no leakage out of the
computational subspace, and no reset-correlated coherence left on `a_S`. Under that condition the
ancilla can be **traced out exactly within each round** (the partial trace of a system that is
reset-initialised and measured-and-discarded within the round loses nothing that survives to the
next round). Imperfect reset / leakage breaks the exactness — bounded as caveat (ii) in §4, not
assumed away.

## 3. Construction — the per-stabilizer measurement instrument

Fix one internal stabilizer `S`. Let `U_S` denote the full noisy round map (steps 1–3 above) acting
on `(D_S ⊗ a_S)` with `a_S` initialised to `|0>`, expressed as a CPTP channel on `D_S` followed by
the final projective ancilla measurement of step 4. Tracing `a_S` out of this local sub-circuit
yields a **quantum instrument** `{E_s}_{s∈{0,1}}` on `D_S` — a pair of completely positive,
trace-non-increasing maps with `E_0 + E_1` trace-preserving — defined by, for any data state
`ρ_{D_S}`:

- **syndrome probability** (the Born rule for outcome `s`):
  `P(s | ρ) = Tr( E_s(ρ_{D_S}) )`;
- **post-measurement data update** (the conditional state given outcome `s`):
  `ρ_{D_S} → E_s(ρ_{D_S}) / P(s)`;
- the **unselected** (outcome-averaged) data channel is `ρ → E_0(ρ) + E_1(ρ)`, which is CPTP.

Concretely, `E_s(ρ) = Tr_{a_S}[ (I_{D_S} ⊗ |s><s|_{a_S}) · N_S(ρ ⊗ |0><0|_{a_S}) · (I_{D_S} ⊗
|s><s|_{a_S}) ]`, where `N_S` is the noisy unitary-plus-channel map of steps 1–3. Each `E_s` is a
≤5q → ≤9q-restricted object built on at most `|D_S| + 1 ≤ 5` qubits, so the **construction touches
only a ≤5q local sub-system**, even though the runtime register it acts on is the 9q data block.

**Readout flip.** The `p = 0.005` measurement flip is a **classical mixture** that swaps the two
outcome branches: the realised instrument is

`Ẽ_0 = (1−p) E_0 + p E_1`,  `Ẽ_1 = (1−p) E_1 + p E_0`,  with `p = 0.005`,

so the reported syndrome `s̃` is the true `s` flipped with probability `p`. (Sanity: at `p = 0`,
`Ẽ_s = E_s`; the mixture is trace-preserving in total since `Ẽ_0 + Ẽ_1 = E_0 + E_1`.)

**Tag (a), conditioned.** Given the §2 reset-decoupling assumption, the per-stabilizer instrument
`{Ẽ_s}` is an **exact** reduction of that stabilizer's local sub-circuit: the partial trace of a
reset-decoupled ancilla is exact, and the readout flip is an exact classical post-processing of the
ancilla measurement. The conditioning is the same leakage-free-reset condition as §2.

## 4. Equivalence proposition — the END-TO-END claim (PENDING, tag (b))

**Proposition (to verify, not yet confirmed).** Applying the instruments `{Ẽ_s}` of all internal
stabilizers **in faithful circuit order** on the shared 9q `ρ_data` reproduces both

- the **internal (full-in) syndrome distribution**, and
- the **data-state evolution**

of the faithful data+ancilla circuit (the d3 patch's full 17q register, validated progressively
through its feasible ≤13q sub-systems — §5), **exactly under perfect leakage-free ancilla reset**.

**Epistemic status — explicit.** The proposition has two layers with different tags:

- The **per-stabilizer trace** of §2–§3 is **(a)-grade exact**, *conditioned* on perfect,
  leakage-free reset. This is the only part with theorem-grade status, and even it carries the
  reset condition.
- The **end-to-end equivalence on the real multi-stabilizer circuits** — 9q instruments in faithful
  circuit order vs the faithful d3 data+ancilla evolution (its 17q register, checked via the feasible
  ≤13q sub-systems of §5), for **both** the internal syndrome distribution **and** the data ρ — is a
  **(b) PREDICTION**. It is **NOT yet numerically confirmed**
  against the oracle. It must be labelled pending everywhere; a miss is a finding, never later
  citable as fact.

The reason the end-to-end claim is not a free corollary of the per-stabilizer exactness is the three
caveats below: composition order, imperfect reset, and coherence preservation each have to hold for
the per-stabilizer exactness to lift to the whole window.

### Caveats to bound (each must be discharged, not hand-waved)

- **(i) Shared data + interleaved CZ layers ⇒ circuit-order composition, not independent factors.**
  Adjacent internal stabilizers share data qubits, and their CZ layers interleave in the real
  schedule. The ancilla trace is **per-stabilizer** (each `a_S` is local and reset-decoupled), but
  the data-side instruments **do not commute and do not factor**: they must be composed in the
  faithful CIRCUIT ORDER on the shared 9q register, exactly as the gates appear in the parsed
  circuit. Treating the window's syndrome as a product of independent per-stabilizer instruments
  would be wrong; the data composition is sequential and order-sensitive. (This is why the
  equivalence is (b) and not a direct (a) lift — the composition is where the per-stabilizer
  exactness has to be re-established for the full window.)

- **(ii) Imperfect reset / leakage ⇒ approximation; residual must be bounded.** If `a_S` reset is
  imperfect (residual population, leakage out of the computational subspace, or reset-correlated
  coherence), the §2 decoupling fails and the instrument reduction degrades from exact to an
  approximation: residual cross-round ancilla information leaks the per-round factorisation. The
  residual must be **bounded** against the oracle (§5), not assumed zero. The reported equivalence
  band must cover this term.

- **(iii) Coherent CZ mechanisms ⇒ the data-side map must preserve the coherence budget.** The CZ
  mechanisms act coherently on `(data, ancilla)`. After tracing `a_S`, the data-side instrument must
  be checked to **preserve the data-side coherent content** where physical — i.e. the reduction must
  not silently twirl coherence away. Concretely: the PTM off-diagonal mass of the unselected
  data channel `E_0 + E_1` (the coherence budget) must match the oracle's data-side coherence to
  within the equivalence band. A reduction that diagonalises the PTM would be the forbidden twirl
  (the model's representation invariant; cf. README "never diagonal-truncate the PTM in the model").

## 5. Numerical-validation plan — the faithful d3 oracle adjudicates

The faithful explicit-ancilla circuit is the **numerical oracle**, built on the **same d3 white-box
patch** as the runtime (not the d7 window — d7 cross-window is deferred). The full d3 faithful
register (9 data + 8 ancilla = 17q = 275 GB) is infeasible, but the oracle does **not** need it: the
equivalence decomposes into a per-stabilizer part and a circuit-order part (§3–§4), so the oracle is
run as a **progressive d3 faithful sub-system** that is runtime-isomorphic (same 9 data) and feasible:

| oracle sub-system | size | what it validates | feasible |
|---|---|---|---|
| 9 data + 1 ancilla | **10q** (`4^10 × 16 B = 16 MB`) | one stabilizer's instrument vs its faithful sub-circuit (the §3 per-stabilizer (a)-claim, incl. its back-action on the full 9q ρ) | ✅ |
| 9 data + k≤4 ancilla | **≤13q** (`≤ 1 GB`) | circuit-order composition of a stabilizer sub-set on the shared 9q register (caveat i) | ✅ |
| 9 data + 8 ancilla | 17q (275 GB) | full end-to-end | ❌ — **not run**; covered by the per-stabilizer (10q) + sub-set (≤13q) checks + the linear-composition argument. The honest limit: the full-d3 end-to-end oracle is infeasible, so end-to-end equivalence is established by decomposition, not a single 17q comparison. |

The already-drafted faithful `WindowChannel` (generic over window data + ancilla) is the oracle
engine, instantiated on these d3 sub-systems. The plan compares the 9q instrument against the oracle
on two quantities (on a real d3 patch):

1. **Internal syndrome distribution** — **KL divergence** + **total-variation distance** between the
   9q-instrument syndrome distribution and the faithful sub-system's (both field-standard; carry the
   convention per `docs/METRICS.md`).
2. **Data state ρ** — **trace distance** between the 9q-instrument data ρ and the faithful data ρ
   after the matched circuit, tracking the PTM off-diagonal (coherence) mass per caveat (iii).

**Decision rule (tag (c)).** Adopt the 9q instrument as the runtime object **only if** the residual
(syndrome KL/TV + data trace distance, including the imperfect-reset term of caveat (ii)) is within a
**pre-registered band**, written down before the comparison run (theory-first). Otherwise keep the
faithful circuit, or fall back to the ADR 0008 **C1 composed architecture** (Clifford / non-Clifford
split). The comparison runs on GPU (GPU-only model compute; no `device="cpu"`, no cuda-if-available
fallback). Any mainline code change for the 9q instrument lands **after** the equivalence passes the
band, through the commit-gate.

**Cost anchor.** The size ratios are exact density-matrix counts: the d3 runtime is 9q = 4.2 MB; the
full d3 faithful is 17q = 275 GB (`4^8 = 65536×`) — the reason the runtime cannot be the faithful
register. (The d7 interior window's 13q = 1.07 GB / `256×` is the analogous ratio for the deferred
cross-window stage.)

## 6. Status

This is a step-2 **representation redirect**, theory-first. The 9q instrument is a **derivation +
prediction**: the per-stabilizer trace is (a)-grade exact under leakage-free reset; the end-to-end
equivalence on real circuits is a **(b) prediction, not yet numerically confirmed** against the
oracle. The runtime 9q representation is adopted only on passing the §5 band; until then the faithful
d3 circuit (run as the progressive sub-system oracle of §5) remains the oracle and the model of record. Disciplines carried forward unweakened:
GPU-only model compute, coherence preserved end-to-end (PTM off-diagonal tracked), circuit-derived
adjacency, and the mainline commit-gate.
