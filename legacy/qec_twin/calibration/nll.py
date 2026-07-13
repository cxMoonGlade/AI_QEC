from __future__ import annotations

"""B3: label-free calibration of the rep-code twin via exact observation-NLL.

Recovers a per-location CPTP channel field by minimizing, over the calibration
contexts ``C_cal(r)``, the exact Born-rule negative log-likelihood of the
teacher's observations (ADR 0003). The twin sees only the joint distribution of
``(s, m)`` -- detector events ``s`` and logical readout ``m`` -- never the
teacher's mechanism labels, so the fit is label-free.

Exact-distribution form. In the infinite-data limit the per-context NLL is the
cross-entropy ``H(p_teacher, p_twin) = - sum_{s,m} p_T(s,m) log p_twin(s,m)``;
the calibration KL ``H(p_T, p_twin) - H(p_T) >= 0`` is the clean "did the joint
match" metric (zero iff the distributions agree). Because teacher and twin run
the same measurement structure, their trajectory enumerations align index-by-
index with identical ``(s, m)`` per branch, so the cross-entropy is a sum over
aligned branch probabilities (a scatter-add by ``(s, m)`` code keeps it correct
even where the record -> ``(s, m)`` map is not injective).

Claim boundary. Matching the joint pins the channel only up to the observational
alias quotient: a Z-basis ``|0_L>``/``|1_L>`` ladder fixes each location's
effective bit-flip action but leaves phase-only components free. So small
calibration *and* held-out KL means the twin is observationally adequate and
generalizes across contexts; it does NOT by itself mean the channel is recovered.
Quantifying recovery vs probe richness (and the coherent / non-Clifford slice
where the alias bites) is the B5 study.
"""

from dataclasses import dataclass

import torch

from qec_twin.contexts.ladder import RepCodeContext, run_context
from qec_twin.mechanisms.teachers import zz_coupling_kraus
from qec_twin.numerics import NUMERICAL_ZERO
from qec_twin.forward.cptp_channel import RDTYPE, StinespringChannel
from qec_twin.forward.exact.rep_code import RepCodeForward


# --------------------------------------------------------------------------- #
# Joint distribution / divergences over the enumerated trajectories             #
# --------------------------------------------------------------------------- #
def joint_codes(forward: RepCodeForward) -> torch.Tensor:
    """Integer code of each branch's ``(detector_events, observable)`` outcome.

    Distinct codes across branches certify the record -> ``(s, m)`` bijection, so
    the per-branch ``probs`` are exactly the joint ``p(s, m)``.
    """
    det = forward.detector_events.round().long()
    obs = forward.observable.round().long().unsqueeze(1)
    bits = torch.cat([det, obs], dim=1)
    weights = (2 ** torch.arange(bits.shape[1], device=bits.device)).long()
    return (bits * weights).sum(1)


def joint_cross_entropy(
    teacher: RepCodeForward, twin: RepCodeForward, *, floor: float = NUMERICAL_ZERO
) -> torch.Tensor:
    """``- sum_{s,m} p_teacher(s,m) log p_twin(s,m)`` (the per-context exact NLL).

    Teacher and twin enumerate the same trajectory structure, so branch ``b``
    carries the same ``(s, m)`` in both; twin mass is aggregated by ``(s, m)``
    code (differentiable scatter-add) before scoring.
    """
    code = joint_codes(teacher)
    uniq, inverse = torch.unique(code, return_inverse=True)
    twin_agg = torch.zeros(uniq.shape[0], dtype=twin.probs.dtype, device=twin.probs.device)
    twin_agg = twin_agg.scatter_add(0, inverse, twin.probs)
    p_twin = twin_agg[inverse].clamp_min(floor)
    return -(teacher.probs * torch.log(p_twin)).sum()


def joint_entropy(forward: RepCodeForward, *, floor: float = NUMERICAL_ZERO) -> torch.Tensor:
    """``- sum p log p`` of the joint -- the cross-entropy floor."""
    p = forward.probs.clamp_min(floor)
    return -(forward.probs * torch.log(p)).sum()


def joint_kl(teacher: RepCodeForward, twin: RepCodeForward, *, floor: float = NUMERICAL_ZERO) -> torch.Tensor:
    """``KL(p_teacher || p_twin) >= 0`` -- zero iff the joints agree."""
    return joint_cross_entropy(teacher, twin, floor=floor) - joint_entropy(teacher, floor=floor)


# --------------------------------------------------------------------------- #
# Twin model: a per-location CPTP channel field                                 #
# --------------------------------------------------------------------------- #
@dataclass
class RepCodeTwin:
    """One learnable single-qubit CPTP channel per data location (time-shared).

    ``field()`` is the ``(round_t, data_index_i) -> Kraus`` callable the forward
    model consumes; the channel is shared across rounds, matching a
    time-independent storage mechanism.
    """

    distance: int
    channels: list[StinespringChannel]

    @classmethod
    def random(
        cls,
        distance: int,
        *,
        num_kraus: int = 2,
        seed: int = 0,
        scale: float = 0.1,
        device: str | torch.device = "cpu",
    ) -> "RepCodeTwin":
        channels = [
            StinespringChannel.random(2, num_kraus, seed=seed + i, scale=scale, device=device)
            for i in range(int(distance))
        ]
        return cls(distance=int(distance), channels=channels)

    def parameters(self) -> list[torch.Tensor]:
        params: list[torch.Tensor] = []
        for channel in self.channels:
            params.extend(channel.parameters())
        return params

    def field(self):
        return lambda t, i: self.channels[i].kraus()

    def edge_field(self):
        """Factorized model class: no edge channels (returns ``None``)."""
        return None


@dataclass
class CoupledRepCodeTwin(RepCodeTwin):
    """Non-factorized learner: ``RepCodeTwin`` + ONE real edge DOF ``phi_hat`` (H2).

    The minimal ADR-0006 candidate-(b) escalation: the factorized per-location
    channels plus a single learnable coherent coupling ``exp(-i phi_hat Z(x)Z)``
    on the declared data ``pair`` -- so any closure of ``B_misspec`` is
    attributable to that one DOF. ``phi_hat`` is a leaf in ``parameters()``.
    """

    phi_hat: torch.Tensor = None
    pair: tuple[int, int] = (0, 1)

    @classmethod
    def random(
        cls,
        distance: int,
        *,
        num_kraus: int = 2,
        seed: int = 0,
        scale: float = 0.1,
        device: str | torch.device = "cpu",
        phi_init: float = 0.0,
        pair: tuple[int, int] = (0, 1),
    ) -> "CoupledRepCodeTwin":
        base = RepCodeTwin.random(distance, num_kraus=num_kraus, seed=seed, scale=scale, device=device)
        phi = torch.tensor(float(phi_init), dtype=RDTYPE, device=device, requires_grad=True)
        return cls(distance=base.distance, channels=base.channels, phi_hat=phi, pair=tuple(pair))

    def parameters(self) -> list[torch.Tensor]:
        return super().parameters() + [self.phi_hat]

    def edge_field(self):
        pair = tuple(self.pair)
        phi = self.phi_hat
        return lambda t, e: zz_coupling_kraus(phi) if tuple(e) == pair else None


# --------------------------------------------------------------------------- #
# Calibration loop                                                              #
# --------------------------------------------------------------------------- #
def calibrate(
    teacher_field,
    contexts: list[RepCodeContext],
    *,
    distance: int = 3,
    num_kraus: int = 2,
    steps: int = 200,
    seed: int = 0,
    device: str | torch.device = "cpu",
    teacher_edge_field=None,
    twin_edge: bool = False,
    twin_phi_init: float = 0.0,
    twin_pair: tuple[int, int] = (0, 1),
) -> dict[str, object]:
    """Fit the twin to the teacher's observations across ``contexts`` by exact NLL.

    Teacher forwards are constant and precomputed; the twin's per-location
    channels are optimized (LBFGS, double precision) to minimize the summed
    cross-entropy. Returns the fitted twin plus calibration NLL/KL diagnostics.

    ``teacher_edge_field`` (H2) is EVALUATOR-ONLY: it generates the teacher's
    observation distributions and is never handed to the learner (isolation
    contract -- the learner consumes only ``p(s,m|c)``). ``twin_edge`` selects the
    learner class: ``False`` = factorized :class:`RepCodeTwin` (edge-free
    forwards); ``True`` = :class:`CoupledRepCodeTwin` whose single ``phi_hat``
    edge DOF starts at ``twin_phi_init`` on ``twin_pair``.
    """
    teacher_forwards = [
        run_context(c, channel_field=teacher_field, edge_field=teacher_edge_field, device=device)
        for c in contexts
    ]
    if twin_edge:
        twin = CoupledRepCodeTwin.random(
            distance, num_kraus=num_kraus, seed=seed, device=device,
            phi_init=twin_phi_init, pair=twin_pair,
        )
    else:
        twin = RepCodeTwin.random(distance, num_kraus=num_kraus, seed=seed, device=device)
    optimizer = torch.optim.LBFGS(
        twin.parameters(),
        lr=1.0,
        max_iter=steps,
        line_search_fn="strong_wolfe",
        tolerance_grad=1e-16,
        tolerance_change=1e-18,
        history_size=50,
    )

    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        field = twin.field()
        edge = twin.edge_field()
        loss = torch.zeros((), dtype=RDTYPE, device=device)
        for context, teacher in zip(contexts, teacher_forwards):
            twin_forward = run_context(context, channel_field=field, edge_field=edge, device=device)
            loss = loss + joint_cross_entropy(teacher, twin_forward)
        loss.backward()
        return loss

    optimizer.step(closure)

    with torch.no_grad():
        field = twin.field()
        edge = twin.edge_field()
        per_context_kl: dict[str, float] = {}
        total_nll = 0.0
        for context, teacher in zip(contexts, teacher_forwards):
            twin_forward = run_context(context, channel_field=field, edge_field=edge, device=device)
            per_context_kl[context.label] = float(joint_kl(teacher, twin_forward))
            total_nll += float(joint_cross_entropy(teacher, twin_forward))

    result = {
        "twin": twin,
        "total_nll": total_nll,
        "total_kl": sum(per_context_kl.values()),
        "per_context_kl": per_context_kl,
        "teacher_forwards": teacher_forwards,
    }
    if twin_edge:
        result["phi_hat"] = float(twin.phi_hat.detach())
    return result


def evaluate_kl(
    twin: RepCodeTwin, teacher_field, context: RepCodeContext, *, teacher_edge_field=None, device="cpu"
) -> float:
    """Held-out cross-context check: ``KL(p_teacher || p_twin)`` on ``context``."""
    with torch.no_grad():
        teacher = run_context(
            context, channel_field=teacher_field, edge_field=teacher_edge_field, device=device
        )
        twin_forward = run_context(
            context, channel_field=twin.field(), edge_field=twin.edge_field(), device=device
        )
        return float(joint_kl(teacher, twin_forward))
