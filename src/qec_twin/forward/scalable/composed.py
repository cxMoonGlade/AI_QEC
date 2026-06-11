from __future__ import annotations

"""C1 composed-carrier arm (ADR 0008 C3 SEAM TEST, registration item 3).

Two window-exact CPTP factors joined by a DECLARED seam composition rule. This is
the first real content of ``forward/scalable``: the seam-test-scale instance of
the C1 composed architecture (ADR 0008 "C2 outcome" -- DEM/HMM bulk + window-exact
CPTP coherent corrections; here, at two-window strip scale, both windows are
window-exact and the bulk engine is not yet involved).

The instrument geometry (declared tiling ``two-window-v1``)
-----------------------------------------------------------
A strip of ``d_left + d_right`` data qubits split into two repetition-code
windows. Each window carries its OWN adjacent parity checks (window L: pairs
``(j, j+1)`` for ``j < d_left - 1``; window R likewise on its local register).
NO check straddles the seam: the seam pair ``(d_left - 1, d_left)`` (global
indices; window-local ``(d_left - 1 | L, 0 | R)``) hosts only a two-qubit channel
slot (teacher side: the registered coherent edge ``U_phi = exp(-i phi Z(x)Z)``;
carrier side: the declared seam slot). With zero seam mass the two windows are
exactly dynamically uncoupled, which is what makes the zero-seam exactness pin
(registration item 7) a true float64-round-off pin. Tiling is FAMILY DESIGN,
declared at freeze; a seam-straddling re-tiling is a second registration
(registration items 1 and 8), never a fit knob.

THE DECLARED SEAM COMPOSITION RULE (the ONLY approximation in this arm)
-----------------------------------------------------------------------
Conditional-product (synchronous mean-field) composition at the declared
per-round placement:

* The carrier's strip state is constrained to the product manifold
  ``rho_strip = rho_L (x) rho_R`` at every point of the round schedule. Every
  channel slot supported inside one window applies EXACTLY (forward/exact
  density-matrix evolution on that window's own register).
* The seam slot -- a Kraus stack ``{K_e}`` on the seam pair, qubit order
  ``(left (x) right)`` -- is applied at the H2 placement
  ``[ (prod_i E_i) ; E_seam ]^repeats`` then extraction, i.e. once per repeat
  pass, after that pass's location channels and BEFORE that round's extraction.
  The composition is NEVER commuted past extraction: the seam application and
  the partner snapshots below both sit strictly inside the round, at the same
  declared extraction boundary.
* At each application the two windows' record-averaged reduced seam-qubit
  states ``sigma_L, sigma_R`` (the partial trace of the branch-summed window
  state onto its seam qubit) are snapshotted SYNCHRONOUSLY -- both snapshots
  taken before either window is updated -- and each window receives the
  conditional reduction of the seam channel against the partner's snapshot:

      Phi_L[sigma_R](rho_L) = Tr_R[ E_seam( rho_L (x) sigma_R ) ]
      Phi_R[sigma_L](rho_R) = Tr_L[ E_seam( sigma_L (x) rho_R ) ]

  Each conditional reduction is CPTP by construction: with any factorization
  ``sigma = sum_c x_c x_c^dag`` its Kraus operators are
  ``A_e^{(m,c)} = (I (x) <m|) K_e (I (x) x_c)`` (left side; mirrored for the
  right), and ``sum A^dag A = I * Tr(sigma) = I``
  (:func:`seam_conditional_reduction`).
* The strip law is the branch product of the two window laws:
  ``p(s_L, m_L, s_R, m_R) = p_L(s_L, m_L) * p_R(s_R, m_R)``.

What the rule DROPS -- the tier-3, functional-indexed ``B_carrier``
(= ``B_misspec`` of the composition; registration items 3 and 8): (i) all
cross-window record/state correlation (the product constraint), and (ii) the
record-conditioning of the seam action (each window sees the partner's
branch-AVERAGED seam marginal, not its per-branch state). Nothing else is
approximate: when the seam slot is the identity (or absent) the conditional
reduction is exactly the identity map and the composed law equals the
whole-strip ``forward/exact`` law up to float64 round-off. The seam residual is
measured per functional against the exact oracle (evaluator-side) and recorded
in :class:`qec_twin.forward.scalable.pins.CarrierErrorAccounting`; it is NEVER
folded into ``eps_log`` (which is float64 round-off only).

Record / code conventions (declared; shared with the instrument side)
---------------------------------------------------------------------
Whole-strip record column layout (the oracle / instrument convention,
:func:`split_strip_record`): round ``t`` emits window L's check records
(local ``j = 0..d_left-2``) then window R's (local ``j = 0..d_right-2``);
after the last round, window L's data qubits then window R's. Per window, the
split record is exactly the ``forward/exact`` rep-code layout, so detectors and
the per-window logical observable come from the SAME map the validated B-path
uses (``rep_code._detectors_and_observable``), and a window's ``(s, m)`` code is
:func:`window_joint_codes`. ``StripObservations`` carries the teacher's strip
joint grouped by the per-window code pair -- observations ONLY (isolation
contract: no teacher channel, parameter, or label ever enters this module's
fit path).
"""

from dataclasses import dataclass, field as dataclass_field, replace

import torch

from qec_twin.forward.cptp_channel import (
    RDTYPE,
    StinespringChannel,
    hermitianize,
)
from qec_twin.forward.exact.circuit_sim import (
    apply_channel_local,
    apply_unitary,
    measure_parity_enumerate,
    measure_qubit_enumerate,
    pauli_x,
    ry,
    zero_state,
)

# Shared record -> (detectors, observable) convention with the validated B-path
# forward (private import, deliberate: the convention must be THE SAME function,
# not a re-implementation that could drift).
from qec_twin.forward.exact.rep_code import _detectors_and_observable
from qec_twin.mechanisms.teachers import zz_coupling_kraus  # pure Kraus builder (no teacher state)
from qec_twin.numerics import NUMERICAL_ZERO


# --------------------------------------------------------------------------- #
# Strip geometry and contexts                                                  #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StripSpec:
    """The declared two-window tiling: window sizes + the (derived) seam pair."""

    d_left: int
    d_right: int
    tiling: str = "two-window-v1"

    def __post_init__(self) -> None:
        if int(self.d_left) < 2 or int(self.d_right) < 2:
            raise ValueError("each window needs >= 2 data qubits (>= 1 check)")

    @property
    def n_total(self) -> int:
        return int(self.d_left) + int(self.d_right)

    @property
    def seam_pair(self) -> tuple[int, int]:
        """Global data indices of the seam pair (left qubit, right qubit)."""
        return (int(self.d_left) - 1, int(self.d_left))


@dataclass(frozen=True)
class StripContext:
    """One runnable strip context (duck-typed: the instrument may pass any object
    with these attributes). ``logical`` prepares BOTH windows in ``|1_L>`` when 1;
    ``repeats`` / ``pre_rotation`` are the H2 coherence-exposing probe knobs."""

    rounds: int
    logical: int = 0
    repeats: int = 1
    pre_rotation: float = 0.0
    label: str = ""


@dataclass
class StripObservations:
    """Teacher/hardware strip joint over per-window ``(s, m)`` codes -- the ONLY
    object the carrier fit consumes (isolation contract).

    ``codes_left`` / ``codes_right`` are ``(N,)`` int64 window codes
    (:func:`window_joint_codes`); ``probs`` the ``(N,)`` float64 joint masses of
    each code pair (sums to 1)."""

    context: StripContext
    codes_left: torch.Tensor
    codes_right: torch.Tensor
    probs: torch.Tensor


# --------------------------------------------------------------------------- #
# Window codes + the declared whole-strip record splitter                       #
# --------------------------------------------------------------------------- #
def window_joint_codes(outcomes: torch.Tensor, distance: int, rounds: int) -> torch.Tensor:
    """Integer ``(s, m)`` code of each branch's window record (rep-code layout).

    Identical bit-weight convention to ``calibration.nll.joint_codes`` so the
    carrier and any instrument/oracle side agree cell-by-cell."""
    det, obs = _detectors_and_observable(outcomes, distance, rounds)
    bits = torch.cat([det.round().long(), obs.round().long().unsqueeze(1)], dim=1)
    weights = (2 ** torch.arange(bits.shape[1], device=bits.device)).long()
    return (bits * weights).sum(1)


def split_strip_record(
    outcomes: torch.Tensor, spec: StripSpec, rounds: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """Split a whole-strip record (declared column layout, module docstring) into
    the two per-window rep-code-layout records.

    ``outcomes`` is ``(B, K)`` with ``K = rounds * (checks_L + checks_R) + n_total``.
    Returns ``(outcomes_L, outcomes_R)`` each in the per-window layout
    ``[anc round 0 .. anc round rounds-1, data]`` that
    :func:`window_joint_codes` expects."""
    c_left = int(spec.d_left) - 1
    c_right = int(spec.d_right) - 1
    r = int(rounds)
    per_round = c_left + c_right
    cols_left: list[int] = []
    cols_right: list[int] = []
    for t in range(r):
        cols_left.extend(t * per_round + j for j in range(c_left))
        cols_right.extend(t * per_round + c_left + j for j in range(c_right))
    data0 = r * per_round
    cols_left.extend(data0 + i for i in range(spec.d_left))
    cols_right.extend(data0 + spec.d_left + i for i in range(spec.d_right))
    return outcomes[:, cols_left], outcomes[:, cols_right]


def strip_observations_from_records(
    outcomes: torch.Tensor,
    probs: torch.Tensor,
    spec: StripSpec,
    context: StripContext,
) -> StripObservations:
    """Group a whole-strip enumeration ``(record, prob)`` into the per-window-code
    joint (evaluator-side helper for the instrument / test oracle; consumes
    records + probabilities only)."""
    out_left, out_right = split_strip_record(outcomes, spec, int(context.rounds))
    code_l = window_joint_codes(out_left, spec.d_left, int(context.rounds))
    code_r = window_joint_codes(out_right, spec.d_right, int(context.rounds))
    pairs = torch.stack([code_l, code_r], dim=1)
    uniq, inverse = torch.unique(pairs, dim=0, return_inverse=True)
    agg = torch.zeros(uniq.shape[0], dtype=probs.dtype, device=probs.device)
    agg = agg.scatter_add(0, inverse, probs)
    return StripObservations(
        context=context,
        codes_left=uniq[:, 0].contiguous(),
        codes_right=uniq[:, 1].contiguous(),
        probs=agg,
    )


# --------------------------------------------------------------------------- #
# The seam conditional reduction (the composition rule's CPTP kernel)           #
# --------------------------------------------------------------------------- #
def _psd_sqrt_2x2(sigma: torch.Tensor) -> torch.Tensor:
    """Closed-form PSD square root of a 2x2 density matrix (differentiable).

    ``sqrt(sigma) = (sigma + sqrt(det) I) / sqrt(tr + 2 sqrt(det))``. ``det`` is
    floored at ``NUMERICAL_ZERO**2`` inside the sqrt -- a floating round-off
    guard (gradient regularity at pure partner states), perturbing the
    factorization by O(1e-24), far below every registered pin tolerance."""
    sigma = hermitianize(sigma)
    det = torch.linalg.det(sigma).real.clamp_min(0.0)
    tr = torch.diagonal(sigma, dim1=-2, dim2=-1).real.sum(-1)
    s = torch.sqrt(det + NUMERICAL_ZERO**2)
    denom = torch.sqrt((tr + 2.0 * s).clamp_min(NUMERICAL_ZERO))
    eye = torch.eye(2, dtype=sigma.dtype, device=sigma.device)
    return (sigma + s.to(sigma.dtype) * eye) / denom.to(sigma.dtype)


def seam_conditional_reduction(
    seam_kraus: torch.Tensor, partner_sigma: torch.Tensor, *, side: str
) -> torch.Tensor:
    """Conditional reduction of the seam channel against the partner's snapshot.

    ``seam_kraus`` is ``(k, 4, 4)`` over ``(left (x) right)``; ``partner_sigma``
    the partner window's reduced seam-qubit state. Returns the ``(4k, 2, 2)``
    Kraus stack of ``rho -> Tr_partner[E_seam(rho (x) sigma)]`` (``side="left"``)
    or ``rho -> Tr_partner[E_seam(sigma (x) rho)]`` (``side="right"``) -- CPTP by
    construction (module docstring). Exactly the identity map when
    ``seam_kraus`` is the identity stack (the do(E -> I) pushforward pin)."""
    k = seam_kraus.shape[0]
    kr = seam_kraus.reshape(k, 2, 2, 2, 2)  # [e, a, m, b, c]: rows (a,m), cols (b,c)
    x = _psd_sqrt_2x2(partner_sigma.to(seam_kraus.dtype))
    if side == "left":
        # contract the right-qubit column index with sigma^(1/2); Kraus indexed (e, m, d)
        t = torch.einsum("eambc,cd->eambd", kr, x)
        reduced = t.permute(0, 2, 4, 1, 3).reshape(k * 4, 2, 2)
    elif side == "right":
        # contract the left-qubit column index with sigma^(1/2); Kraus indexed (e, a, d)
        t = torch.einsum("eambc,bd->eamdc", kr, x)
        reduced = t.permute(0, 1, 3, 2, 4).reshape(k * 4, 2, 2)
    else:
        raise ValueError(f"side must be 'left' or 'right' (got {side!r})")
    return reduced


def reduced_qubit_state(rho: torch.Tensor, qubit: int, n: int) -> torch.Tensor:
    """Partial trace of an ``(dim, dim)`` register state onto one qubit."""
    nn = int(n)
    t = rho.reshape([2] * (2 * nn))
    q = int(qubit)
    rest = [a for a in range(nn) if a != q]
    perm = [q] + rest + [nn + q] + [nn + a for a in rest]
    t = t.permute(perm).reshape(2, 2 ** (nn - 1), 2, 2 ** (nn - 1))
    return torch.einsum("aibi->ab", t)


# --------------------------------------------------------------------------- #
# The composed strip forward                                                    #
# --------------------------------------------------------------------------- #
@dataclass
class WindowLaw:
    """One window's grouped ``(s, m)`` law: sorted unique ``codes`` + ``probs``."""

    codes: torch.Tensor  # (U,) int64, sorted (torch.unique)
    probs: torch.Tensor  # (U,) float64

    def lookup(self, query_codes: torch.Tensor, *, floor: float = NUMERICAL_ZERO,
               counter: dict | None = None) -> torch.Tensor:
        """Window mass at each query code; ``floor`` where the carrier carries
        no support (differentiable through ``probs``).

        ``counter`` (checklist item 5, reviewer §E): when provided, missing-support
        cells increment ``counter["floor_hits_model_class"]`` — the model-class
        floor book, kept separate from the evaluator book and never harvested in
        production scoring."""
        idx = torch.searchsorted(self.codes, query_codes)
        idx_c = idx.clamp(max=self.codes.numel() - 1)
        hit = self.codes[idx_c] == query_codes
        if counter is not None:
            counter["floor_hits_model_class"] = (
                counter.get("floor_hits_model_class", 0) + int((~hit).sum())
            )
        floor_t = torch.full_like(self.probs[idx_c], float(floor))
        return torch.where(hit, self.probs[idx_c], floor_t)


@dataclass
class StripLaw:
    """The composed strip law: the branch product of the two window laws."""

    spec: StripSpec
    context: StripContext
    left: WindowLaw
    right: WindowLaw

    def normalization_defect(self) -> tuple[float, float]:
        """``|sum p - 1|`` per window -- the measured float64 eps_log proxy."""
        return (
            abs(float(self.left.probs.sum()) - 1.0),
            abs(float(self.right.probs.sum()) - 1.0),
        )

    def joint_probs(self, codes_left: torch.Tensor, codes_right: torch.Tensor,
                    *, floor: float = NUMERICAL_ZERO,
                    counter: dict | None = None) -> torch.Tensor:
        return (
            self.left.lookup(codes_left, floor=floor, counter=counter)
            * self.right.lookup(codes_right, floor=floor, counter=counter)
        )

    def full_joint(self) -> torch.Tensor:
        """The full ``(U_L, U_R)`` product grid (toy scale only)."""
        return self.left.probs[:, None] * self.right.probs[None, :]


def _group_window_law(outcomes: torch.Tensor, probs: torch.Tensor, distance: int, rounds: int) -> WindowLaw:
    codes = window_joint_codes(outcomes, distance, rounds)
    uniq, inverse = torch.unique(codes, return_inverse=True)
    agg = torch.zeros(uniq.shape[0], dtype=probs.dtype, device=probs.device)
    agg = agg.scatter_add(0, inverse, probs)
    return WindowLaw(codes=uniq, probs=agg)


def composed_strip_law(
    spec: StripSpec,
    context: StripContext,
    *,
    left_field,
    right_field,
    seam_kraus: torch.Tensor | None = None,
    device: str | torch.device = "cpu",
) -> StripLaw:
    """Exact-forward both windows in lockstep under the declared composition rule.

    ``left_field`` / ``right_field`` are rep-code-convention callables
    ``(round_t, local_data_index) -> (k, 2, 2) Kraus stack | None`` over each
    window's OWN register; ``seam_kraus`` is the seam slot's ``(k, 4, 4)`` stack
    (``None`` = no seam slot). Differentiable in any leaf parameters of the
    fields and of ``seam_kraus``. Cost: each window is a full ``forward/exact``
    enumeration on its own ``2**d_w`` register -- the strip register
    ``2**(dL+dR)`` is never built (that is the point of the composition)."""
    n_l, n_r = int(spec.d_left), int(spec.d_right)
    rounds = int(context.rounds)
    repeats = int(context.repeats)

    rho_l = zero_state(n_l, device=device).unsqueeze(0)
    rho_r = zero_state(n_r, device=device).unsqueeze(0)
    out_l = torch.zeros((1, 0), dtype=RDTYPE, device=device)
    out_r = torch.zeros((1, 0), dtype=RDTYPE, device=device)

    # Device threading (mechanical fix, 2026-06-11): callers may hand a
    # CPU-built seam stack (e.g. a fresh zz_coupling_kraus in an evaluator-side
    # mirror arm) while the windows evolve on CUDA — move it once, here, so the
    # seam reduction never sees mixed devices.
    if seam_kraus is not None:
        seam_kraus = seam_kraus.to(device=rho_l.device, dtype=rho_l.dtype)

    if int(context.logical):
        gate = pauli_x(device)
        for q in range(n_l):
            rho_l = apply_unitary(rho_l, gate, [q], n_l)
        for q in range(n_r):
            rho_r = apply_unitary(rho_r, gate, [q], n_r)
    if float(context.pre_rotation):
        gate = ry(context.pre_rotation).to(device)
        for q in range(n_l):
            rho_l = apply_unitary(rho_l, gate, [q], n_l)
        for q in range(n_r):
            rho_r = apply_unitary(rho_r, gate, [q], n_r)

    for t in range(rounds):
        for _ in range(repeats):
            for i in range(n_l):
                kraus = left_field(t, i)
                if kraus is not None:
                    rho_l = apply_channel_local(rho_l, kraus, [i], n_l)
            for i in range(n_r):
                kraus = right_field(t, i)
                if kraus is not None:
                    rho_r = apply_channel_local(rho_r, kraus, [i], n_r)
            if seam_kraus is not None:
                # synchronous snapshots: BOTH partner marginals read before either update
                sigma_l = reduced_qubit_state(rho_l.sum(0), n_l - 1, n_l)
                sigma_r = reduced_qubit_state(rho_r.sum(0), 0, n_r)
                rho_l = apply_channel_local(
                    rho_l, seam_conditional_reduction(seam_kraus, sigma_r, side="left"), [n_l - 1], n_l
                )
                rho_r = apply_channel_local(
                    rho_r, seam_conditional_reduction(seam_kraus, sigma_l, side="right"), [0], n_r
                )
        for j in range(n_l - 1):
            rho_l, out_l = measure_parity_enumerate(rho_l, out_l, j, j + 1, n_l)
        for j in range(n_r - 1):
            rho_r, out_r = measure_parity_enumerate(rho_r, out_r, j, j + 1, n_r)

    for i in range(n_l):
        rho_l, out_l = measure_qubit_enumerate(rho_l, out_l, i, n_l, reset=False)
    for i in range(n_r):
        rho_r, out_r = measure_qubit_enumerate(rho_r, out_r, i, n_r, reset=False)

    probs_l = torch.diagonal(rho_l, dim1=-2, dim2=-1).real.sum(-1)
    probs_r = torch.diagonal(rho_r, dim1=-2, dim2=-1).real.sum(-1)
    return StripLaw(
        spec=spec,
        context=context,
        left=_group_window_law(out_l, probs_l, n_l, rounds),
        right=_group_window_law(out_r, probs_r, n_r, rounds),
    )


# --------------------------------------------------------------------------- #
# Label-free Born-NLL scoring on strip observations                             #
# --------------------------------------------------------------------------- #
def strip_cross_entropy(
    observations: StripObservations, law: StripLaw, *, floor: float = NUMERICAL_ZERO,
    counter: dict | None = None
) -> torch.Tensor:
    """``- sum p_obs log p_carrier`` over the strip joint (exact Born-NLL form).

    The observation joint retains all cross-window correlation; the carrier's
    law is the composed product, so any seam deficiency shows up here and in the
    per-functional residuals -- never hidden by the family.

    ``counter`` (checklist item 5): model-class floor hits are booked by the
    lookups under ``floor_hits_model_class``; cells whose product still needs
    the log-clamp are booked under ``evaluator_nonpositive``. Two books, never
    combined, never harvested in production scoring."""
    q = law.joint_probs(
        observations.codes_left, observations.codes_right, floor=floor, counter=counter
    )
    if counter is not None:
        counter["evaluator_nonpositive"] = (
            counter.get("evaluator_nonpositive", 0) + int((q < floor).sum())
        )
    return -(observations.probs * torch.log(q.clamp_min(floor))).sum()


def strip_entropy(observations: StripObservations, *, floor: float = NUMERICAL_ZERO) -> torch.Tensor:
    p = observations.probs.clamp_min(floor)
    return -(observations.probs * torch.log(p)).sum()


def strip_joint_kl(observations: StripObservations, law: StripLaw, *, floor: float = NUMERICAL_ZERO,
                   counter: dict | None = None) -> torch.Tensor:
    """``KL(p_obs || p_carrier) >= 0`` -- zero iff the strip joints agree."""
    return (
        strip_cross_entropy(observations, law, floor=floor, counter=counter)
        - strip_entropy(observations, floor=floor)
    )


@torch.no_grad()
def strip_law_total_variation(law: StripLaw, observations: StripObservations) -> dict[str, float]:
    """Exact TV and max-abs cell gap between the composed law and an observation
    joint (toy scale: builds the full product grid). Evaluator-side comparator —
    runs under ``no_grad`` (reviewer §C5: never a differentiation path)."""
    grid = law.full_joint().clone()
    idx_l = torch.searchsorted(law.left.codes, observations.codes_left)
    idx_r = torch.searchsorted(law.right.codes, observations.codes_right)
    idx_l_c = idx_l.clamp(max=law.left.codes.numel() - 1)
    idx_r_c = idx_r.clamp(max=law.right.codes.numel() - 1)
    hit = (law.left.codes[idx_l_c] == observations.codes_left) & (
        law.right.codes[idx_r_c] == observations.codes_right
    )
    flat = idx_l_c[hit] * law.right.codes.numel() + idx_r_c[hit]
    grid = grid.reshape(-1)
    grid = grid.index_add(0, flat, -observations.probs[hit])
    missing = observations.probs[~hit]
    tv = 0.5 * (float(grid.abs().sum()) + float(missing.sum()))
    max_abs = float(grid.abs().max())
    if missing.numel():
        max_abs = max(max_abs, float(missing.max()))
    return {"tv": tv, "max_abs": max_abs}


# --------------------------------------------------------------------------- #
# The carrier object: declared slots, W2-gate hook, channel-level do()          #
# --------------------------------------------------------------------------- #
@dataclass
class SlotState:
    """One declared channel slot of the class manifest."""

    name: str  # "L.loc{i}" | "R.loc{i}" | "seam"
    kind: str  # model-class tag, e.g. "stinespring-k{n}" | "coherent-zz"
    active: bool
    note: str = ""


@dataclass
class CarrierManifest:
    """The class manifest: every fittable slot declared up front; the W2/Fisher
    gate (audit machinery; S3 wires it) must run BEFORE any fit and may freeze
    slots. ``fit_composed_carrier`` refuses to run while ``gated`` is False
    (registration item 11)."""

    slots: list[SlotState]
    gated: bool = False
    gate_record: dict | None = None

    def apply_gate(self, gate_record: dict, *, freeze: tuple[str, ...] = ()) -> None:
        """Record the W2/Fisher gate outcome; freeze the named slots (a frozen
        slot stays in the forward at its current value but is not fittable)."""
        for slot in self.slots:
            if slot.name in freeze:
                slot.active = False
                slot.note = (slot.note + " " if slot.note else "") + "frozen-by-gate"
        self.gated = True
        self.gate_record = dict(gate_record)

    def active_names(self) -> list[str]:
        return [s.name for s in self.slots if s.active]


@dataclass
class ComposedCarrier:
    """The fittable composed-carrier arm: per-window per-location CPTP slots
    (Stinespring, time-shared) + an optional coherent-ZZ seam slot ``phi_hat``,
    forwarded through :func:`composed_strip_law`.

    do() discipline: :meth:`do_on_location` / :meth:`do_on_seam` apply a
    channel-level, parameterization-independent transform to the slot's CURRENT
    Kraus stack and store the transformed STACK as an override -- never a
    parameter edit -- so the strip pushforward is exactly the declared composed
    forward run on the transformed channel field (registration item 5)."""

    spec: StripSpec
    left_channels: list[StinespringChannel]
    right_channels: list[StinespringChannel]
    seam_phi: torch.Tensor | None
    manifest: CarrierManifest
    location_overrides: dict = dataclass_field(default_factory=dict)  # (window, i) -> Kraus stack
    seam_override: torch.Tensor | None = None

    @classmethod
    def random(
        cls,
        spec: StripSpec,
        *,
        num_kraus: int = 2,
        seed: int = 0,
        scale: float = 0.1,
        seam_phi_init: float | None = None,
        device: str | torch.device = "cpu",
    ) -> "ComposedCarrier":
        left = [
            StinespringChannel.random(2, num_kraus, seed=seed + i, scale=scale, device=device)
            for i in range(spec.d_left)
        ]
        right = [
            StinespringChannel.random(2, num_kraus, seed=seed + spec.d_left + i, scale=scale, device=device)
            for i in range(spec.d_right)
        ]
        phi = None
        if seam_phi_init is not None:
            phi = torch.tensor(float(seam_phi_init), dtype=RDTYPE, device=device, requires_grad=True)
        slots = (
            [SlotState(f"L.loc{i}", f"stinespring-k{num_kraus}", True) for i in range(spec.d_left)]
            + [SlotState(f"R.loc{i}", f"stinespring-k{num_kraus}", True) for i in range(spec.d_right)]
            + ([SlotState("seam", "coherent-zz", True)] if phi is not None else [])
        )
        return cls(
            spec=spec,
            left_channels=left,
            right_channels=right,
            seam_phi=phi,
            manifest=CarrierManifest(slots=slots),
        )

    # -- channel field (channel-level view; overrides take precedence) -------- #
    def seam_kraus(self) -> torch.Tensor | None:
        if self.seam_override is not None:
            return self.seam_override
        if self.seam_phi is None:
            return None
        return zz_coupling_kraus(self.seam_phi)

    def left_field(self):
        overrides = self.location_overrides
        channels = self.left_channels
        return lambda t, i: overrides.get(("L", i), None) if ("L", i) in overrides else channels[i].kraus()

    def right_field(self):
        overrides = self.location_overrides
        channels = self.right_channels
        return lambda t, i: overrides.get(("R", i), None) if ("R", i) in overrides else channels[i].kraus()

    # -- fittable leaves (active slots only) ---------------------------------- #
    def parameters(self) -> list[torch.Tensor]:
        active = set(self.manifest.active_names())
        params: list[torch.Tensor] = []
        for i, ch in enumerate(self.left_channels):
            if f"L.loc{i}" in active and ("L", i) not in self.location_overrides:
                params.extend(ch.parameters())
        for i, ch in enumerate(self.right_channels):
            if f"R.loc{i}" in active and ("R", i) not in self.location_overrides:
                params.extend(ch.parameters())
        if self.seam_phi is not None and "seam" in active and self.seam_override is None:
            params.append(self.seam_phi)
        return params

    # -- forward --------------------------------------------------------------- #
    def strip_law(self, context: StripContext, *, device: str | torch.device = "cpu") -> StripLaw:
        return composed_strip_law(
            self.spec,
            context,
            left_field=self.left_field(),
            right_field=self.right_field(),
            seam_kraus=self.seam_kraus(),
            device=device,
        )

    # -- channel-level do() (parameterization-independent) --------------------- #
    def do_on_seam(self, intervention) -> "ComposedCarrier":
        """``do(E_seam -> intervention(E_seam))`` -- acts on the seam slot's Kraus
        stack; the strip pushforward is pinned to the declared composed forward."""
        current = self.seam_kraus()
        if current is None:
            raise ValueError("carrier has no seam slot to intervene on")
        return replace(self, seam_override=intervention(current))

    def do_on_location(self, window: str, i: int, intervention) -> "ComposedCarrier":
        """``do(E_{window,i} -> intervention(E_{window,i}))`` on a location slot."""
        if window not in ("L", "R"):
            raise ValueError(f"window must be 'L' or 'R' (got {window!r})")
        field = self.left_field() if window == "L" else self.right_field()
        current = field(0, int(i))
        if current is None:
            raise ValueError(f"location slot {window}.loc{i} carries no channel")
        overrides = dict(self.location_overrides)
        overrides[(window, int(i))] = intervention(current)
        return replace(self, location_overrides=overrides)


# --------------------------------------------------------------------------- #
# Label-free calibration of the carrier (exact Born-NLL; calibration/ pattern)  #
# --------------------------------------------------------------------------- #
def fit_composed_carrier(
    observations: list[StripObservations],
    spec: StripSpec,
    *,
    carrier: ComposedCarrier | None = None,
    num_kraus: int = 2,
    steps: int = 200,
    seed: int = 0,
    seam_phi_init: float | None = None,
    device: str | torch.device = "cpu",
) -> dict[str, object]:
    """Fit the carrier's ACTIVE slots to strip observations by exact Born-NLL
    (LBFGS, double precision -- the ``calibration.nll.calibrate`` pattern).

    The learner consumes only ``StripObservations`` (isolation contract). The
    W2/Fisher gate must have run first: ``carrier.manifest.gated`` is enforced
    (registration item 11; S3 wires the audit gate -- tests may record a stub
    gate outcome for toy smoke fits, clearly labeled). Production fits are
    reviewer-gated and are NOT run from this module's tests."""
    if carrier is None:
        carrier = ComposedCarrier.random(
            spec, num_kraus=num_kraus, seed=seed, seam_phi_init=seam_phi_init, device=device
        )
    if not carrier.manifest.gated:
        raise RuntimeError(
            "W2/Fisher identifiability gate must run before any fit "
            "(seam-test registration item 11): call manifest.apply_gate(...) first"
        )
    params = carrier.parameters()
    if not params:
        raise RuntimeError("no active fittable slots after gating")
    optimizer = torch.optim.LBFGS(
        params,
        lr=1.0,
        max_iter=int(steps),
        line_search_fn="strong_wolfe",
        tolerance_grad=1e-16,
        tolerance_change=1e-18,
        history_size=50,
    )

    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        loss = torch.zeros((), dtype=RDTYPE, device=device)
        for obs in observations:
            law = carrier.strip_law(obs.context, device=device)
            loss = loss + strip_cross_entropy(obs, law)
        loss.backward()
        return loss

    optimizer.step(closure)

    with torch.no_grad():
        per_context_kl: dict[str, float] = {}
        total_nll = 0.0
        for obs in observations:
            law = carrier.strip_law(obs.context, device=device)
            per_context_kl[obs.context.label] = float(strip_joint_kl(obs, law))
            total_nll += float(strip_cross_entropy(obs, law))

    return {
        "carrier": carrier,
        "total_nll": total_nll,
        "total_kl": sum(per_context_kl.values()),
        "per_context_kl": per_context_kl,
    }
