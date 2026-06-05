"""B3: label-free calibration via exact observation-NLL.

Checks the joint-distribution machinery (the record -> (s,m) bijection, the KL
that is exactly zero when the twin equals the teacher) and the calibration loop
itself: a per-location bit-flip teacher is recovered to a machine-precision joint
across the r=1 ladder and -- the load-bearing signal -- generalizes to a held-out
longer circuit. (Channel *recovery* vs probe richness, where the alias quotient
bites, is the separate B5 study; here we validate the loop is observationally
adequate and cross-context valid.)
"""

from __future__ import annotations

import torch

from scope_static.experiments.scope_twin.calibration import (
    RepCodeTwin,
    calibrate,
    evaluate_kl,
    joint_codes,
    joint_kl,
)
from scope_static.experiments.scope_twin.contexts import (
    RepCodeContext,
    calibration_contexts,
    held_out_eval_context,
    run_context,
)
from scope_static.primitives.diff_circuit_sim import bit_flip


def _per_location_bitflip(rates):
    def field(t: int, i: int):
        return bit_flip(rates[i])

    return field


def test_record_to_sm_is_a_bijection() -> None:
    # K = R(d-1)+d record bits map invertibly onto D+1 detector+observable bits,
    # so every branch is a distinct (s,m): the per-branch probs ARE the joint.
    for rounds in (1, 2, 3):
        forward = run_context(
            RepCodeContext(3, rounds, 0, 0, "t"), data_channel=bit_flip(0.07)
        )
        codes = joint_codes(forward)
        assert codes.unique().shape[0] == codes.shape[0]


def test_kl_is_zero_when_twin_equals_teacher() -> None:
    teacher_field = _per_location_bitflip([0.05, 0.05, 0.05])
    ctx = calibration_contexts(1)[2]  # an r=1 multi-round context
    teacher = run_context(ctx, channel_field=teacher_field)
    # Twin identical to teacher -> KL exactly 0 (up to rounding).
    twin_same = run_context(ctx, channel_field=teacher_field)
    assert abs(joint_kl(teacher, twin_same).item()) < 1e-12


def test_calibration_recovers_joint_and_generalizes_cross_context() -> None:
    teacher_field = _per_location_bitflip([0.04, 0.09, 0.06])
    contexts = calibration_contexts(1)

    result = calibrate(teacher_field, contexts, distance=3, num_kraus=2, steps=300, seed=0)

    # The twin matches the teacher's exact joint on every calibration context...
    assert result["total_kl"] < 1e-9
    for kl in result["per_context_kl"].values():
        assert kl < 1e-9

    # ...and -- the real signal -- generalizes to a held-out longer circuit it
    # never calibrated on (cross-context validity, not context memorization).
    held_out = held_out_eval_context()
    assert held_out.key not in {c.key for c in contexts}
    assert evaluate_kl(result["twin"], teacher_field, held_out) < 1e-9


def test_twin_field_is_a_per_location_cptp_channel() -> None:
    twin = RepCodeTwin.random(distance=3, num_kraus=2, seed=1)
    field = twin.field()
    # Each location is an independent trace-preserving channel.
    for i in range(3):
        kraus = field(0, i)
        completeness = torch.einsum("eij,eik->jk", kraus.conj(), kraus)
        identity = torch.eye(2, dtype=completeness.dtype)
        assert torch.linalg.matrix_norm(completeness - identity).item() < 1e-9
