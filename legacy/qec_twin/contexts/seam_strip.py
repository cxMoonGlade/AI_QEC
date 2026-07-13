from __future__ import annotations

"""ADR 0008 C3 seam-test instrument: the disjoint two-window ``SeamStrip``.

Registration item 1 of the frozen SEAM-TEST pre-registration
(``docs/metric_results.md`` "ADR 0008 SEAM-TEST PRE-REGISTRATION", recorded
2026-06-10 BEFORE build/run; the 13-item skeleton in
``docs/.reports/adr0008_panel/R2_c3prep_verdict.md`` is the binding blueprint),
as adjudicated by **SEAM-TEST PRE-RUN AMENDMENT 1** (same section; rulings 1-3
govern this module). The instrument is REP-CODE-SHAPED -- the K2-T1 footprint
collapse does NOT apply to its teacher -- and it is the K1 discharge vehicle
for the C1 composed-carrier architecture.

Object (amendment ruling 1: the DISJOINT two-window strip)
----------------------------------------------------------
Two repetition-code windows laid on one strip of ``D = window_a + window_b``
data qubits. The windows are DISJOINT contiguous index ranges; they share the
**seam DATA pair** ``(window_a - 1, window_a)`` ACROSS the seam (one qubit each
side). **NO check is measured on the seam pair**: extraction is per-window
checks only (window A: adjacent pairs ``(j, j+1)`` for ``j < window_a - 1``;
window B likewise on ``window_a .. D-1``). The seam pair hosts only the
two-qubit channel slot: the seam teachers act ON it
(``mechanisms.seam_teachers``); the composed carrier (S2, ``forward/scalable``)
factorizes ACROSS it; the seam residual the carrier leaves on phi-sensitive
functionals is THE K1 measurement (registration item 4, P-c).

Scored family (amendment ruling 2): the strip joint law over per-window
``(s, m)`` code-record pairs -- the ``StripObservations`` family of
``forward/scalable/composed.py`` -- declared once, scored identically by every
arm. :meth:`SeamStripLaw.observations` produces it via the carrier side's OWN
splitter (:func:`qec_twin.forward.scalable.split_strip_record` /
``strip_observations_from_records``), so the record-layout convention is THE
SAME function on both sides, never a re-implementation that could drift.

Record layout (the binding convention, ``composed.py`` "Record / code
conventions" + ``split_strip_record``): round ``t`` emits window A's check
records (local ``j = 0..window_a-2``) then window B's (local
``j = 0..window_b-2``); after the last round, window A's data qubits then
window B's. ``K = rounds * (D - 2) + D`` columns -- there is NO seam-check
column.

Tiling discipline ((c)-class, registered): the tiling is FAMILY DESIGN, never a
fit knob -- two tilings = two registrations; this run is FIRST-READ-ONLY
(amendment ruling 5). This module builds the single declared family
:data:`TILING_FAMILY` = ``"two-window-v1"`` -- the SAME family string as the
carrier's ``StripSpec.tiling``, because amendment ruling 1 declares ONE
instrument shared by every arm. A seam-straddling re-tiling is a new
registration, not a parameter sweep.

Size envelope ((c)-class, registered; amendment ruling 3): total instrument
qubits ``2*D - 2`` (``D`` data + one ancilla per MEASURED check -- the
disjoint-extraction accounting; the seam pair carries no ancilla) must stay
``<= 13``; enforced at construction. The registration's "13q <= 1.1 GB; 15q =
17.2 GB" parenthetical is the DM-feasibility justification of the cap, not a
layout pin (amendment ruling 1). The registered production instrument is
:data:`PRODUCTION_WINDOW_SIZES` = ``(3, 4)``: ``D = 7`` data, **12** instrument
qubits (the largest admissible strip: ``D = 8`` would be 14). Unit tests run
the law toy ``(2, 2)`` (``D = 4``, 6 qubits -- the same data count as the
carrier side's structural-pin instrument ``StripSpec(2, 2)``) and the layout
toy ``(3, 3)`` (``D = 6``, 10 qubits) for the splitter cross-check.

The oracle
----------
:meth:`SeamStrip.oracle_law` realizes the exact whole-strip law of the disjoint
layout by ``forward/exact`` primitives ONLY (the trajectory-enumerated
density-matrix forward on the ``2**D`` data register; ``forward/exact`` exposes
no check mask, so the disjoint extraction is realized here from the same
primitives -- noise layer, parity projections, qubit measurements -- that
``simulate_rep_code_memory`` composes, with the seam parity pair skipped). The
registered noise class is data-qubit storage channels + the data-data seam edge
with NOISELESS extraction, for which this data-only parity realization is
exact. The H2 placement ``[ (prod_i E_i) ; U_edge ]^repeats`` then extraction
is realized by the SAME ``rep_code._apply_noise_layer`` the validated B-path
forward uses (deliberate private import: the placement must be the same
function). The law is evaluator-side ground truth for scoring and is NEVER a
carrier input (isolation contract, ``docs/teacher_learner.md``).

Oracle evaluation (FIX R2-1, ``build_R2_seam_postfix_review.md`` section B)
---------------------------------------------------------------------------
ONE law, two evaluation strategies -- the mathematical definition above is
untouched; only the evaluation is routed (the original branch-doubling
enumeration is memory-infeasible at production: 2**K branches, K = rounds*(D-2)
+ D, i.e. 34 GB at (3,4) rounds=2 and 35 TB at rounds=4):

* ``evaluator="monolithic"`` (toy scale; the oracle for the equivalence pins):
  the original full trajectory enumeration, byte-for-byte the pre-fix op
  sequence -- ``(B, K)`` records + ``(B,)`` branch probabilities. ``"auto"``
  selects it whenever the final branch tensor fits
  :data:`MONOLITHIC_ORACLE_MAX_BYTES` ((c) routing constant).
* ``evaluator="grouped"`` (production): memory-bounded chunked evaluation,
  built on two (a)-class exact identities plus one (c)-class execution
  constant:

  (a1) **diagonal final readout.** After the LAST noise layer every remaining
  operation -- the last round's parity projections and the final transversal
  data readout -- is Z-basis diagonal. Each branch's density-matrix diagonal
  therefore carries the exact joint over (last-round check outcomes, data
  bits): the check outcomes are the deterministic adjacent parities of the
  basis index (combinations with mismatched parity carry exactly zero mass,
  matching the monolithic path's exactly-zero masked branches). No
  final-readout or last-round branch doubling is ever materialized -- a
  x 2**(2D-2) saving in live branches at the leaf level.

  (a2) **record <-> code-pair bijection.** Per window the record -> (s, m)
  detector map (``rep_code._detectors_and_observable``) is an invertible
  triangular GF(2) transform (round-0 checks are absolute; round t < R XORs
  round t-1; the final detector row XORs data parities with the last check
  round; the observable is data qubit 0 -- each step is solvable in sequence),
  so strip records biject with per-window code pairs. Every cell of the dense
  code-pair grid receives EXACTLY ONE enumeration leaf: the on-the-fly
  accumulation is collision-free, hence BIT-EXACT against the monolithic
  path's grouping (no summation-order ambiguity anywhere on the joint-law
  path; pinned by ``tests/test_carrier_seam_instrument.py``).

  (c) :data:`ORACLE_LIVE_BRANCH_CAP` -- the declared live-branch cap. A
  chunked depth-first walk of the check-outcome tree bounds RESIDENT branch
  tensors; it NEVER truncates or prunes: every branch is eventually visited
  and the evaluated law is exactly the registered strip joint. Both evaluators
  run under :func:`_pinned_einsum_path` (the einsum contraction association is
  otherwise batch-size-dependent via opt_einsum -- the only re-association
  source between the two paths; with the path pinned, equivalence is
  bit-exact).

  Grouped laws return :class:`SeamStripLaw` with ``grouped=True``: ``probs``
  is the full code-pair law in lexicographic cell order (cell-aligned across
  teachers -- the cell space is teacher-independent); per-branch records are
  never materialized (the (B, K) record matrix at production rounds=4 would
  itself be 29 GB). :func:`oracle_memory_probe` supplies the W2-gate memory
  estimate for a ``(window_sizes, rounds)`` request before any allocation.

Contexts: the H2 probe ladder ``C_cal(r)``, ``r <= 4``, reused VERBATIM from
:mod:`qec_twin.contexts.ladder` at the strip data count -- including the
repeated-storage sandwich rungs and the k2ry probe -- plus the held-out seam
evals. The context set is unchanged in substance by the amendment (ruling
"context ladder + teachers unchanged"); no context construction depends on a
seam check existing (the knobs are rounds / logical / repeats / pre_rotation,
all check-set-agnostic).
"""

import contextlib
from dataclasses import dataclass
from typing import Callable, Protocol, runtime_checkable

import torch

from qec_twin.contexts.ladder import (
    RepCodeContext,
    calibration_contexts,
    held_out_eval_context,
    held_out_exotic_contexts,
    held_out_sandwich_context,
)
from qec_twin.forward.cptp_channel import RDTYPE
from qec_twin.forward.exact.circuit_sim import (
    apply_unitary,
    measure_parity_enumerate,
    measure_qubit_enumerate,
    pauli_x,
    ry,
    zero_state,
)

# The H2 noise placement must be THE SAME function as the validated B-path
# forward (deliberate private import; the convention must never be a
# re-implementation that could drift -- the pattern composed.py uses for
# _detectors_and_observable).
from qec_twin.forward.exact.rep_code import _apply_noise_layer

# Record-layout / family conventions shared with the carrier arm (S2). These
# are pure record-bookkeeping functions (index maps and grouping) -- the LAW is
# computed by forward/exact primitives above; no carrier compute and no
# learner-side object is touched here (isolation contract intact).
from qec_twin.forward.scalable.composed import (
    StripObservations,
    StripSpec,
    split_strip_record,
    strip_observations_from_records,
    window_joint_codes,
)

#: Registered DM-oracle envelope ((c)-class): total instrument qubits
#: (data + one ancilla per measured check) above which the exact oracle is out
#: of DM feasibility (13q <= 1.1 GB; 15q = 17.2 GB wall -- registration item 1;
#: the parenthetical is the cap's justification, not a layout pin --
#: amendment ruling 1).
MAX_ORACLE_QUBITS = 13

#: The ONE declared tiling family (family design; two tilings = two
#: registrations; this run is FIRST-READ-ONLY -- amendment ruling 5). Equals
#: the carrier's ``StripSpec.tiling`` string: amendment ruling 1 declares ONE
#: shared instrument -- disjoint contiguous windows, seam data pair unchecked.
TILING_FAMILY = "two-window-v1"

#: Registered production size (amendment ruling 3): windows (3, 4) -- D = 7
#: data qubits, 12 instrument qubits under the 2D-2 disjoint-extraction
#: accounting (the envelope maximum: D = 8 would be 14 > 13).
PRODUCTION_WINDOW_SIZES = (3, 4)

#: Default law toy for unit tests (D = 4 data, 6 total qubits) -- the same
#: window sizes as the carrier side's structural-pin instrument
#: ``StripSpec(2, 2)``, and the same data count (4) as the validated pre-fix
#: toy, so every ladder-count pin carries over verbatim. The (3, 3) layout toy
#: (D = 6, 10 qubits) is feasible only at small round counts (the enumeration
#: is 2**K branches, K = rounds*(D-2) + D) and is used for the rounds=1
#: splitter cross-check.
TOY_WINDOW_SIZES = (2, 2)

#: (c)-class EXECUTION constant (FIX R2-1; declared per the silent-constant
#: rule): the memory-bounded grouped evaluator's live-branch cap. It bounds the
#: number of branch density matrices RESIDENT at any moment of the chunked
#: check-tree walk -- it NEVER truncates or prunes (every branch is eventually
#: visited; the evaluated law is exactly the registered strip joint, pinned
#: bit-exact vs the monolithic path at toy scale). Derivation of the default:
#: at production (3, 4) one branch DM is 128 x 128 complex128 = 256 KiB; the
#: modeled worst transient is the leaf-chunk noise layer at
#: ``_NOISE_TRANSIENT_BRANCH_FACTOR x cap`` branches = 5 x 512 x 256 KiB
#: = 640 MiB -- under the registered item-13 oracle live-set letter (13q DM
#: = 1.07 GB) with margin. A pure execution knob: any admissible value
#: (>= 2**(D-2)) evaluates the IDENTICAL law.
ORACLE_LIVE_BRANCH_CAP = 512

#: (c)-class routing constant (FIX R2-1): ``evaluator="auto"`` keeps the
#: monolithic (full-record) enumeration whenever its FINAL branch tensor is at
#: most this many bytes, and routes to the memory-bounded grouped evaluator
#: above it. 64 MiB keeps every toy-suite law monolithic ((2,2) at rounds<=4 is
#: 16 MiB; (3,3) at rounds=1 is exactly 64 MiB) while every production-geometry
#: context (>= 1 GiB at rounds=1) routes to the bounded evaluator.
MONOLITHIC_ORACLE_MAX_BYTES = 64 * 1024 * 1024

#: (c)-class transient-memory MODEL constants (used identically by the
#: instrumented walk and the :func:`oracle_memory_probe` dry-run, so the probe
#: is consistent with the implementation by construction -- pinned in tests).
#: A parity doubling holds input + rho0 + rho1 + cat(2B) = 5 x the pre-doubling
#: branch count; a noise layer holds input + (k <= 3) Kraus-term intermediates
#: + output = ~5 x the layer's branch count.
_DOUBLING_TRANSIENT_BRANCH_FACTOR = 5
_NOISE_TRANSIENT_BRANCH_FACTOR = 5


@contextlib.contextmanager
def _pinned_einsum_path():
    """Pin ``torch.einsum`` to its fixed left-to-right pairwise contraction for
    the duration of an oracle evaluation (FIX R2-1 bit-exactness support).

    Measured (2026-06-10, CPU float64): with opt_einsum's size-dependent path
    optimization active, ``apply_kraus``'s three-operand einsum chooses
    DIFFERENT contraction associations at different branch-batch sizes, so the
    chunked walk (batch = chunk size) and the monolithic enumeration (batch =
    full branch count) re-associate the same sums differently -- a ~1e-20
    max-abs law gap. Disabling the optimizer fixes the association
    independently of batch size: the chunked evaluator is then BIT-EXACT
    against the monolithic path at every admissible cap (pinned in
    ``tests/test_carrier_seam_instrument.py``). Scope: oracle evaluation only,
    BOTH modes (so the two paths always run under the identical kernel-path
    setting); the global flag is restored on exit. The law change vs an
    unpinned evaluation is pure float64 re-association, orders below every
    registered tolerance.
    """
    backend = getattr(torch.backends, "opt_einsum", None)
    if backend is None:  # older torch: no optimizer, paths already fixed
        yield
        return
    prev = backend.enabled
    backend.enabled = False
    try:
        yield
    finally:
        backend.enabled = prev


@runtime_checkable
class ObservationTeacher(Protocol):
    """The D8 equal-treatment observation surface (checklist R-NLL item 7).

    Every teacher arm exposes exactly this interface to the instrument, so
    every arm induces the SAME declared block family -- the strip joint over
    per-window ``(s, m)`` code pairs (amendment ruling 2) -- and all arms are
    scored identically. The fields are evaluator-side ground truth (isolation
    contract): the carrier/learner never reads them -- it consumes only the
    observations the evaluator derives from the law.
    """

    name: str
    channel_field: Callable
    edge_field: Callable | None


@dataclass(frozen=True)
class SeamTiling:
    """Frozen declared-tiling descriptor (family design; K2 gauge class (iii)).

    ``family`` names the registered tiling family; ``window_a`` / ``window_b``
    are the DISJOINT data-qubit index tuples of the two windows; ``seam_pair``
    is the unchecked adjacent data pair they share across the seam (one qubit
    each side).
    """

    family: str
    window_a: tuple[int, ...]
    window_b: tuple[int, ...]
    seam_pair: tuple[int, int]


@dataclass(frozen=True)
class SeamStripLaw:
    """Exact whole-strip oracle law (ONE law, two storage modes -- FIX R2-1).

    Monolithic mode (``grouped=False``; toy scale): ``measurement_record`` is
    ``(B, K)`` with ``K = rounds*(D-2) + D`` -- round ``t`` emits window A's
    checks then window B's; after the last round, window A's data then window
    B's (the ``composed.split_strip_record`` convention, binding). ``probs`` is
    the exact ``(B,)`` branch probability (sums to 1).

    Grouped mode (``grouped=True``; the memory-bounded production evaluator):
    ``measurement_record`` is ``None`` -- per-branch records are deliberately
    never materialized -- and ``probs`` is the exact ``(2**K,)`` strip joint
    over per-window ``(s, m)`` code pairs (the declared scored family,
    amendment ruling 2) in lexicographic ``(code_left, code_right)`` cell
    order. The cell set is the FULL code-pair space (the record -> code-pair
    map is a GF(2) bijection, module docstring (a2)) and is
    teacher-independent, so two grouped laws of the same shape are
    CELL-ALIGNED exactly as monolithic laws are branch-aligned: evaluator-side
    aligned TV/KL comparators apply verbatim to ``probs`` in both modes (in
    grouped mode they score the declared family itself).

    Evaluator-side ground truth; never a carrier input.
    """

    window_a_size: int
    window_b_size: int
    rounds: int
    context: RepCodeContext
    measurement_record: torch.Tensor | None
    probs: torch.Tensor
    grouped: bool = False

    @property
    def num_data(self) -> int:
        return self.window_a_size + self.window_b_size

    @property
    def code_bits(self) -> tuple[int, int]:
        """Per-window code widths in bits: ``(rounds+1)*(d_w - 1) + 1``
        (detectors + observable). Their sum equals the record width ``K`` --
        the bijection (a2)."""
        r = int(self.rounds)
        return (
            (r + 1) * (self.window_a_size - 1) + 1,
            (r + 1) * (self.window_b_size - 1) + 1,
        )

    def spec(self) -> StripSpec:
        """The carrier-convention :class:`StripSpec` of this strip."""
        return StripSpec(self.window_a_size, self.window_b_size)

    def total_probability(self) -> torch.Tensor:
        return self.probs.sum()

    def window_records(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Per-window rep-code-layout records via the carrier's OWN splitter
        (:func:`split_strip_record` -- the same function, no drift).
        Monolithic mode only: grouped laws never materialize branch records."""
        if self.grouped:
            raise RuntimeError(
                "grouped (memory-bounded) oracle laws do not materialize "
                "per-branch records (FIX R2-1: the full record matrix is the "
                "production memory blow-up -- 29 GB at (3,4) rounds=4); use "
                "observations() or window_marginal_laws() instead"
            )
        return split_strip_record(self.measurement_record, self.spec(), self.rounds)

    def observations(self) -> StripObservations:
        """The declared scored family (amendment ruling 2): the strip joint
        grouped by per-window ``(s, m)`` code pairs. Monolithic mode groups via
        the carrier side's own helper; grouped mode IS that family already
        (lexicographic cell order == ``torch.unique`` pair order, full-support
        cell space) -- the two are pinned bit-exact in the unit tests.
        Observations ONLY -- this is the object an evaluator may hand across
        the learner boundary. NOTE (memory): in grouped mode the code columns
        are materialized on call -- ``2**K * 24`` bytes (3.2 GB at production
        rounds=4); see :func:`oracle_memory_probe` ``observations_bytes``."""
        if self.grouped:
            bits_l, bits_r = self.code_bits
            idx = torch.arange(self.probs.numel(), device=self.probs.device)
            return StripObservations(
                context=self.context,
                codes_left=(idx >> bits_r).contiguous(),
                codes_right=(idx & ((1 << bits_r) - 1)).contiguous(),
                probs=self.probs,
            )
        return strip_observations_from_records(
            self.measurement_record, self.probs, self.spec(), self.context
        )

    def _cell_grid(self) -> torch.Tensor:
        """The full ``(2**bits_l, 2**bits_r)`` code-pair law grid, both modes.

        Valid because the cell space is always full-support: the monolithic
        enumeration's ``2**K`` branches biject with the ``2**K`` code pairs
        (a2), so its lexicographically grouped observations reshape exactly."""
        bits_l, bits_r = self.code_bits
        probs = self.probs if self.grouped else self.observations().probs
        if probs.numel() != (1 << bits_l) * (1 << bits_r):
            raise AssertionError(
                "full-support code-pair space expected (record <-> code-pair "
                f"bijection): got {probs.numel()} cells, expected "
                f"{(1 << bits_l) * (1 << bits_r)}"
            )
        return probs.reshape(1 << bits_l, 1 << bits_r)

    def window_marginal_laws(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Dense per-window marginal record-code laws ``(P_A, P_B)``, indexed
        by window code -- computed through the SAME lexicographic-grid path in
        both modes, so monolithic and grouped laws of the same strip agree
        BIT-EXACTLY (given their bit-exact observations). The alternative
        splitter-route scatter over per-branch records sums the identical
        per-cell multiset in a different ORDER -- a pure float64 re-association,
        pinned <= 1e-14 in the unit tests with the derivation."""
        grid = self._cell_grid()
        return grid.sum(dim=1), grid.sum(dim=0)


@dataclass(frozen=True)
class SeamStrip:
    """Two DISJOINT rep-code windows on one strip, sharing one unchecked seam
    data pair (amendment ruling 1).

    ``window_a_size`` / ``window_b_size`` are the data-qubit counts of the two
    windows (each ``>= 2`` so every window carries at least one internal
    check). The strip has ``distance = window_a_size + window_b_size`` data
    qubits (disjoint windows) and ``2*distance - 2`` total instrument qubits
    (data + one ancilla per measured check; the seam pair carries no check),
    capped at :data:`MAX_ORACLE_QUBITS` (registered envelope).
    """

    window_a_size: int
    window_b_size: int

    def __post_init__(self) -> None:
        if self.window_a_size < 2 or self.window_b_size < 2:
            raise ValueError(
                "each seam-strip window needs >= 2 data qubits (>= 1 internal "
                "check; the seam pair is unchecked -- amendment ruling 1); got "
                f"({self.window_a_size}, {self.window_b_size})"
            )
        if self.total_qubits > MAX_ORACLE_QUBITS:
            raise ValueError(
                f"strip of {self.total_qubits} total qubits exceeds the registered "
                f"DM-oracle envelope ({MAX_ORACLE_QUBITS}q <= 1.1 GB; 15q = 17.2 GB "
                "wall -- ADR 0008 seam-test registration item 1 / amendment ruling 3)"
            )

    # ----------------------------------------------------------------- sizes
    @property
    def distance(self) -> int:
        """Data-qubit count of the strip (windows are disjoint)."""
        return self.window_a_size + self.window_b_size

    @property
    def num_checks(self) -> int:
        """Measured checks per round: ``D - 2`` (the seam pair is unchecked)."""
        return self.distance - 2

    @property
    def total_qubits(self) -> int:
        """Total instrument qubits: data + one ancilla per MEASURED check --
        the ``2D - 2`` disjoint-extraction accounting (amendment ruling 3)."""
        return 2 * self.distance - 2

    # -------------------------------------------------------------- geometry
    @property
    def data_qubits(self) -> tuple[int, ...]:
        return tuple(range(self.distance))

    @property
    def seam_pair(self) -> tuple[int, int]:
        """The unchecked adjacent data pair shared across the seam (last qubit
        of window A, first qubit of window B)."""
        return (self.window_a_size - 1, self.window_a_size)

    @property
    def seam_pair_index(self) -> int:
        """Adjacent-pair index of the seam pair (pair ``k`` couples data
        ``(k, k+1)``). This pair is NOT measured -- there is no seam check."""
        return self.window_a_size - 1

    @property
    def window_a(self) -> tuple[int, ...]:
        return tuple(range(self.window_a_size))

    @property
    def window_b(self) -> tuple[int, ...]:
        return tuple(range(self.window_a_size, self.distance))

    @property
    def window_a_checks(self) -> tuple[int, ...]:
        """Measured adjacent-pair indices inside window A (pair ``k`` couples
        data ``(k, k+1)``)."""
        return tuple(range(self.window_a_size - 1))

    @property
    def window_b_checks(self) -> tuple[int, ...]:
        """Measured adjacent-pair indices inside window B."""
        return tuple(range(self.window_a_size, self.distance - 1))

    @property
    def tiling(self) -> SeamTiling:
        """The frozen declared-tiling descriptor (attribute, per registration)."""
        return SeamTiling(
            family=TILING_FAMILY,
            window_a=self.window_a,
            window_b=self.window_b,
            seam_pair=self.seam_pair,
        )

    # -------------------------------------------------------------- contexts
    def calibration_contexts(self, richness: int) -> list[RepCodeContext]:
        """The H2 probe ladder ``C_cal(r)`` at the strip data count (r <= 4,
        including the repeats=2 sandwich rungs and the k2ry probe)."""
        return calibration_contexts(richness, distance=self.distance)

    def memory_eval_context(self) -> RepCodeContext:
        """Held-out repeats=1 memory eval (R4-L0) -- a T1 phi-blind functional."""
        return held_out_eval_context(distance=self.distance)

    def sandwich_eval_context(self) -> RepCodeContext:
        """Held-out repeats=2 sandwich eval (R4-k2) -- the phi^2 seam functional."""
        return held_out_sandwich_context(distance=self.distance)

    def exotic_eval_contexts(self) -> list[RepCodeContext]:
        """Held-out phase-sensitive exotics (incl. the k2ry phi-linear pair)."""
        return held_out_exotic_contexts(distance=self.distance)

    def seam_eval_contexts(self) -> dict[str, object]:
        """The held-out eval set the seam residual is scored on (P-a/P-b/P-c)."""
        return {
            "memory": self.memory_eval_context(),
            "sandwich": self.sandwich_eval_context(),
            "exotics": tuple(self.exotic_eval_contexts()),
        }

    # ---------------------------------------------------------------- oracle
    def _prep_state(
        self, context: RepCodeContext, device
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Shared prep (both evaluators -- the identical op sequence):
        ``|0...0>`` plus logical flips and the RY pre-rotation; empty record."""
        n = self.distance
        rho = zero_state(n, device=device).unsqueeze(0)
        outcomes = torch.zeros((1, 0), dtype=RDTYPE, device=device)
        flips = context.initial_flips()
        if flips:
            for q in flips:
                rho = apply_unitary(rho, pauli_x(device), [q], n)
        if context.pre_rotation:
            gate = ry(context.pre_rotation)
            for q in range(n):
                rho = apply_unitary(rho, gate, [q], n)
        return rho, outcomes

    def _noise_layer(
        self, rho: torch.Tensor, t: int, teacher: ObservationTeacher, context: RepCodeContext
    ) -> torch.Tensor:
        """One round's H2 noise placement -- THE SAME ``_apply_noise_layer``
        function as the validated B-path forward, on the strip's seam pair."""
        n = self.distance
        return _apply_noise_layer(
            rho,
            t,
            teacher.channel_field,
            teacher.edge_field,
            (self.seam_pair,),
            list(range(n)),
            n,
            context.repeats,
            n,
        )

    def _measure_round_checks(
        self, rho: torch.Tensor, outcomes: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """One round's disjoint extraction: window A checks ascending, then
        window B checks ascending (the binding record-column order)."""
        n = self.distance
        for j in self.window_a_checks:
            rho, outcomes = measure_parity_enumerate(rho, outcomes, j, j + 1, n)
        for j in self.window_b_checks:
            rho, outcomes = measure_parity_enumerate(rho, outcomes, j, j + 1, n)
        return rho, outcomes

    def oracle_law(
        self,
        context: RepCodeContext,
        teacher: ObservationTeacher,
        *,
        device: str | object = "cpu",
        evaluator: str = "auto",
        live_branch_cap: int | None = None,
        memory_stats: dict | None = None,
    ) -> SeamStripLaw:
        """Exact whole-strip ground-truth law under ``teacher`` (disjoint
        extraction: per-window checks only; the seam pair is never measured).

        Computed by ``forward/exact`` primitives ONLY (registration item 2:
        the teacher side never runs on the carrier) on the ``2**D`` data
        register -- exact for the registered noiseless-extraction class.
        ``teacher`` is any object exposing the :class:`ObservationTeacher`
        surface; its ``edge_field`` is evaluated on the strip's seam pair (the
        single declared edge slot) at the H2 placement
        ``[ (prod_i E_i) ; U_edge ]^repeats`` then extraction. The record
        columns follow the carrier's ``split_strip_record`` convention by
        construction (per round: window A checks ascending, then window B
        checks ascending; finally window A data, then window B data).
        Evaluator-side: the returned law is ground truth for scoring, never a
        learner input.

        FIX R2-1 (module docstring "Oracle evaluation"): ``evaluator`` routes
        between the monolithic full-record enumeration (toy scale) and the
        memory-bounded grouped evaluator (production) -- ``"auto"`` selects by
        the monolithic final-tensor footprint against
        :data:`MONOLITHIC_ORACLE_MAX_BYTES`. ``live_branch_cap`` (grouped mode)
        overrides the declared (c) execution constant
        :data:`ORACLE_LIVE_BRANCH_CAP`; it bounds RESIDENT branches only, never
        truncating the enumeration. ``memory_stats`` (optional dict) receives
        the walk's measured branch-count counters -- by construction equal to
        :func:`oracle_memory_probe`'s dry-run plan (pinned in tests).
        """
        if int(context.distance) != self.distance:
            raise ValueError(
                f"context distance {context.distance} != strip data count "
                f"{self.distance} (build contexts via this strip)"
            )
        rounds = int(context.rounds)
        if rounds < 1:
            raise ValueError(f"oracle_law needs rounds >= 1 (got {rounds})")
        if evaluator == "auto":
            evaluator = (
                "monolithic"
                if _monolithic_final_bytes(self.distance, rounds)
                <= MONOLITHIC_ORACLE_MAX_BYTES
                else "grouped"
            )
        if evaluator == "monolithic":
            if memory_stats is not None:
                memory_stats["evaluator"] = "monolithic"
            with _pinned_einsum_path():
                return self._oracle_monolithic(context, teacher, device)
        if evaluator == "grouped":
            cap = (
                ORACLE_LIVE_BRANCH_CAP if live_branch_cap is None else int(live_branch_cap)
            )
            with _pinned_einsum_path():
                return self._oracle_grouped(
                    context, teacher, device, cap=cap, memory_stats=memory_stats
                )
        raise ValueError(
            f"evaluator must be 'auto', 'monolithic' or 'grouped' (got {evaluator!r})"
        )

    def _oracle_monolithic(
        self, context: RepCodeContext, teacher: ObservationTeacher, device
    ) -> SeamStripLaw:
        """The original full trajectory enumeration (toy scale; the oracle for
        the R2-1 equivalence pins). Byte-for-byte the pre-fix op sequence."""
        n = self.distance
        rho, outcomes = self._prep_state(context, device)
        for t in range(int(context.rounds)):
            rho = self._noise_layer(rho, t, teacher, context)
            rho, outcomes = self._measure_round_checks(rho, outcomes)
        for i in range(n):
            rho, outcomes = measure_qubit_enumerate(rho, outcomes, i, n, reset=False)
        probs = torch.diagonal(rho, dim1=-2, dim2=-1).real.sum(-1)
        return SeamStripLaw(
            window_a_size=self.window_a_size,
            window_b_size=self.window_b_size,
            rounds=int(context.rounds),
            context=context,
            measurement_record=outcomes,
            probs=probs,
        )

    def _oracle_grouped(
        self,
        context: RepCodeContext,
        teacher: ObservationTeacher,
        device,
        *,
        cap: int,
        memory_stats: dict | None = None,
    ) -> SeamStripLaw:
        """Memory-bounded chunked evaluation of the IDENTICAL law (FIX R2-1).

        Depth-first walk of the per-round check-outcome tree with the declared
        live-branch cap; the last round is never branch-doubled -- after its
        noise layer the per-branch diagonal carries the exact joint over
        (last-round checks, data readout) (identity (a1)); each visited
        (branch, basis-index) leaf lands in EXACTLY ONE cell of the dense
        code-pair grid (identity (a2)), so the accumulation is collision-free
        and the grouped law is bit-exact against the monolithic path's
        grouping. The record -> code conversion at the leaves goes through the
        carrier's OWN ``split_strip_record`` / ``window_joint_codes`` (the
        binding convention, never a re-implementation). Runs under
        ``torch.no_grad()`` -- oracle laws are evaluator-side ground truth and
        never a differentiation path."""
        n = self.distance
        rounds = int(context.rounds)
        c = self.num_checks
        if cap < (1 << c):
            raise ValueError(
                f"live_branch_cap={cap} is below one round's doubling factor "
                f"2**{c} = {1 << c}; the chunked walk needs cap >= {1 << c}"
            )
        last = rounds - 1
        bits_l = (rounds + 1) * (self.window_a_size - 1) + 1
        bits_r = (rounds + 1) * (self.window_b_size - 1) + 1
        spec = StripSpec(self.window_a_size, self.window_b_size)
        stats = {
            "evaluator": "grouped",
            "live_branch_cap": int(cap),
            "peak_resident_branches": 0,
            "peak_transient_branches": 0,
            "leaf_chunks": 0,
            "leaf_branches": 0,
            "max_leaf_chunk_branches": 0,
        }

        def _note(resident: int, transient: int) -> None:
            stats["peak_resident_branches"] = max(
                stats["peak_resident_branches"], resident
            )
            stats["peak_transient_branches"] = max(
                stats["peak_transient_branches"], transient
            )

        dim = 1 << n
        idx = torch.arange(dim, device=device)
        shifts = torch.arange(n - 1, -1, -1, device=device)
        # bit q of basis index x is (x >> (n - 1 - q)) & 1 (qubit 0 = MSB; the
        # project_parity / measure_qubit_enumerate convention)
        data_bits = (idx[:, None] >> shifts[None, :]) & 1  # (dim, n) int64
        last_round_checks = torch.stack(
            [
                data_bits[:, j] ^ data_bits[:, j + 1]
                for j in (*self.window_a_checks, *self.window_b_checks)
            ],
            dim=1,
        ).to(RDTYPE)  # (dim, D-2): window A checks ascending, then window B
        data_cols = data_bits.to(RDTYPE)  # (dim, D): data qubits 0..D-1
        weight_r = 1 << bits_r

        with torch.no_grad():
            grid = torch.zeros(
                (1 << bits_l) * (1 << bits_r), dtype=RDTYPE, device=device
            )

            def finalize(rho: torch.Tensor, outcomes: torch.Tensor, anc: int) -> None:
                b = rho.shape[0]
                _note(anc + b, anc + _NOISE_TRANSIENT_BRANCH_FACTOR * b)
                rho = self._noise_layer(rho, last, teacher, context)
                # identity (a1): the exact joint over (last-round checks, data)
                diag = torch.diagonal(rho, dim1=-2, dim2=-1).real  # (b, dim)
                k_prev = outcomes.shape[1]
                rec = torch.cat(
                    [
                        outcomes[:, None, :].expand(b, dim, k_prev).reshape(b * dim, k_prev),
                        last_round_checks[None].expand(b, dim, c).reshape(b * dim, c),
                        data_cols[None].expand(b, dim, n).reshape(b * dim, n),
                    ],
                    dim=1,
                )
                out_l, out_r = split_strip_record(rec, spec, rounds)
                code_l = window_joint_codes(out_l, self.window_a_size, rounds)
                code_r = window_joint_codes(out_r, self.window_b_size, rounds)
                # identity (a2): collision-free -- exactly one leaf per cell
                grid.index_put_(
                    (code_l * weight_r + code_r,), diag.reshape(-1), accumulate=True
                )
                stats["leaf_chunks"] += 1
                stats["leaf_branches"] += b
                stats["max_leaf_chunk_branches"] = max(
                    stats["max_leaf_chunk_branches"], b
                )

            def walk(rho: torch.Tensor, outcomes: torch.Tensor, t: int, anc: int) -> None:
                b = rho.shape[0]
                if t == last:
                    finalize(rho, outcomes, anc)
                    return
                rem = last - t  # doubling rounds before the last (diagonal) round
                if b * (1 << (c * rem)) <= cap:
                    # straight through: the cap is never exceeded by construction
                    for tt in range(t, last):
                        _note(
                            anc + b * (1 << c),
                            anc + _DOUBLING_TRANSIENT_BRANCH_FACTOR * (b << (c - 1)),
                        )
                        rho = self._noise_layer(rho, tt, teacher, context)
                        rho, outcomes = self._measure_round_checks(rho, outcomes)
                        b = rho.shape[0]
                    finalize(rho, outcomes, anc)
                    return
                if b == 1:
                    # a single branch's remaining subtree still exceeds the cap:
                    # expand exactly one round, then descend
                    _note(
                        anc + (1 << c),
                        anc + _DOUBLING_TRANSIENT_BRANCH_FACTOR * (1 << (c - 1)),
                    )
                    rho = self._noise_layer(rho, t, teacher, context)
                    rho, outcomes = self._measure_round_checks(rho, outcomes)
                    walk(rho, outcomes, t + 1, anc)
                    return
                # split into chunks sized to go straight through where possible;
                # the parent tensor (b branches) stays resident while children run
                step = max(1, cap // (1 << (c * rem)))
                for i in range(0, b, step):
                    walk(rho[i : i + step], outcomes[i : i + step], t, anc + b)

            rho0, out0 = self._prep_state(context, device)
            walk(rho0, out0, 0, 0)

        if memory_stats is not None:
            memory_stats.update(stats)
        return SeamStripLaw(
            window_a_size=self.window_a_size,
            window_b_size=self.window_b_size,
            rounds=rounds,
            context=context,
            measurement_record=None,
            probs=grid,
            grouped=True,
        )


def production_strip() -> SeamStrip:
    """The registered production instrument (amendment ruling 3): windows
    (3, 4), D = 7 data, 12 instrument qubits."""
    return SeamStrip(*PRODUCTION_WINDOW_SIZES)


def toy_strip() -> SeamStrip:
    """The default unit-test law toy: windows (2, 2), D = 4, 6 total qubits."""
    return SeamStrip(*TOY_WINDOW_SIZES)


# --------------------------------------------------------------------------- #
# FIX R2-1: oracle memory probe (W2-gate hook) + the evaluator's dry-run plan  #
# --------------------------------------------------------------------------- #
def _record_bits(distance: int, rounds: int) -> int:
    """``K = rounds*(D-2) + D`` -- record width == code-pair width (a2)."""
    return int(rounds) * (int(distance) - 2) + int(distance)


def _monolithic_final_bytes(distance: int, rounds: int) -> int:
    """Final branch-tensor bytes of the monolithic enumeration: ``2**K``
    branches of one ``2**D x 2**D`` complex128 density matrix each."""
    branch_bytes = (1 << int(distance)) ** 2 * 16
    return (1 << _record_bits(distance, rounds)) * branch_bytes


def _walk_plan(c: int, rounds: int, cap: int) -> dict[str, int]:
    """Integer dry-run of ``SeamStrip._oracle_grouped``'s chunked walk.

    Mirrors the implementation's control flow and transient-model bookkeeping
    LINE FOR LINE (same ``_DOUBLING_TRANSIENT_BRANCH_FACTOR`` /
    ``_NOISE_TRANSIENT_BRANCH_FACTOR`` formulas at the same points), so the
    probe's counters equal the instrumented walk's measured counters exactly --
    an (a)-class consistency pin in the unit tests. Branch counts only; no
    tensor is allocated."""
    c = int(c)
    rounds = int(rounds)
    cap = int(cap)
    if cap < (1 << c):
        raise ValueError(
            f"live_branch_cap={cap} is below one round's doubling factor "
            f"2**{c} = {1 << c}; the chunked walk needs cap >= {1 << c}"
        )
    last = rounds - 1
    stats = {
        "peak_resident_branches": 0,
        "peak_transient_branches": 0,
        "leaf_chunks": 0,
        "leaf_branches": 0,
        "max_leaf_chunk_branches": 0,
    }

    def _note(resident: int, transient: int) -> None:
        stats["peak_resident_branches"] = max(stats["peak_resident_branches"], resident)
        stats["peak_transient_branches"] = max(stats["peak_transient_branches"], transient)

    def finalize(b: int, anc: int) -> None:
        _note(anc + b, anc + _NOISE_TRANSIENT_BRANCH_FACTOR * b)
        stats["leaf_chunks"] += 1
        stats["leaf_branches"] += b
        stats["max_leaf_chunk_branches"] = max(stats["max_leaf_chunk_branches"], b)

    def walk(b: int, t: int, anc: int) -> None:
        if t == last:
            finalize(b, anc)
            return
        rem = last - t
        if b * (1 << (c * rem)) <= cap:
            for _ in range(t, last):
                _note(
                    anc + b * (1 << c),
                    anc + _DOUBLING_TRANSIENT_BRANCH_FACTOR * (b << (c - 1)),
                )
                b <<= c
            finalize(b, anc)
            return
        if b == 1:
            _note(
                anc + (1 << c),
                anc + _DOUBLING_TRANSIENT_BRANCH_FACTOR * (1 << (c - 1)),
            )
            walk(1 << c, t + 1, anc)
            return
        step = max(1, cap // (1 << (c * rem)))
        i = 0
        while i < b:
            walk(min(step, b - i), t, anc + b)
            i += step

    walk(1, 0, 0)
    return stats


def oracle_memory_probe(
    window_sizes: tuple[int, int],
    rounds: int,
    *,
    live_branch_cap: int | None = None,
    monolithic_max_bytes: int | None = None,
) -> dict[str, object]:
    """Estimated oracle-evaluation memory for a ``(window_sizes, rounds)``
    request -- the W2-gate / smoke-timing-gate hook (FIX R2-1 deliverable 4).

    Pure arithmetic (no allocation). Keys: ``evaluator`` (the ``"auto"``
    routing decision), ``grid_bytes`` (the grouped law object itself -- the
    dense float64 code-pair grid), ``dm_peak_bytes`` (modeled peak transient of
    the live branch-DM working set -- the registered item-13 oracle-envelope
    quantity), ``finalize_bytes`` (leaf record/code conversion buffers),
    ``observations_bytes`` (the on-call ``StripObservations`` materialization a
    downstream consumer triggers), ``est_peak_bytes`` (the headline total), and
    the exact integer walk counters (equal to a ``memory_stats``-instrumented
    run by construction). The transient model constants are declared (c)
    estimates of allocator behavior; the branch COUNTS are exact."""
    a, b = int(window_sizes[0]), int(window_sizes[1])
    if a < 2 or b < 2:
        raise ValueError(f"each window needs >= 2 data qubits (got ({a}, {b}))")
    d = a + b
    c = d - 2
    r = int(rounds)
    if r < 1:
        raise ValueError(f"rounds must be >= 1 (got {r})")
    cap = ORACLE_LIVE_BRANCH_CAP if live_branch_cap is None else int(live_branch_cap)
    mono_max = (
        MONOLITHIC_ORACLE_MAX_BYTES
        if monolithic_max_bytes is None
        else int(monolithic_max_bytes)
    )
    branch_bytes = (1 << d) ** 2 * 16  # one complex128 branch density matrix
    k_bits = _record_bits(d, r)
    cells = 1 << k_bits
    mono_final_bytes = _monolithic_final_bytes(d, r)
    evaluator = "monolithic" if mono_final_bytes <= mono_max else "grouped"
    plan = _walk_plan(c, r, cap)
    grid_bytes = cells * 8
    dm_peak_bytes = plan["peak_transient_branches"] * branch_bytes
    finalize_bytes = plan["max_leaf_chunk_branches"] * (1 << d) * (k_bits * 8 + 24)
    observations_bytes = cells * 24  # codes_left + codes_right (int64) + probs (f64)
    if evaluator == "monolithic":
        # cat-doubling transient of the original enumeration ~ 2.5 x final
        est_peak_bytes = mono_final_bytes * 5 // 2
    else:
        est_peak_bytes = grid_bytes + dm_peak_bytes + finalize_bytes
    return {
        "window_sizes": (a, b),
        "rounds": r,
        "distance": d,
        "checks_per_round": c,
        "record_bits": k_bits,
        "cells": cells,
        "branch_bytes": branch_bytes,
        "evaluator": evaluator,
        "live_branch_cap": cap,
        "monolithic_final_bytes": mono_final_bytes,
        "grid_bytes": grid_bytes,
        "dm_peak_bytes": dm_peak_bytes,
        "finalize_bytes": finalize_bytes,
        "observations_bytes": observations_bytes,
        "est_peak_bytes": est_peak_bytes,
        "peak_resident_branches": plan["peak_resident_branches"],
        "peak_transient_branches": plan["peak_transient_branches"],
        "leaf_chunks": plan["leaf_chunks"],
        "leaf_branches": plan["leaf_branches"],
        "max_leaf_chunk_branches": plan["max_leaf_chunk_branches"],
    }
