from __future__ import annotations

r"""LEARNER-side CPTP channel-recovery loop (split out of the shared cptp_channel, MIGRATION screen).

The differentiable channel SUBSTRATE (Stinespring parameterization + DM ops) is shared by the
simulator carrier and the learner, and lives in the simulator package
(``error_coupling_simulator.carrier.cptp_channel``, reachable as ``qec_twin.forward.cptp_channel``).
The RECOVERY PROCEDURE below — fit a CPTP channel to a target via its action on an
informationally-complete input set — is LEARNER-only (it recovers a channel from observations; the
simulator never recovers). It was pulled out of the simulator package so the package holds only what
the simulator needs (user screening, 2026-07-03).

``recover_channel`` + ``informationally_complete_inputs`` were previously
``qec_twin.forward.cptp_channel.{recover_channel,informationally_complete_inputs}``; import them from
here now.
"""

import torch

from qec_twin.forward.cptp_channel import (
    CDTYPE,
    StinespringChannel,
    apply_kraus,
    choi_matrix,
    tp_residual,
)


def _ic_single_qubit_states(device: str | torch.device = "cpu") -> torch.Tensor:
    """The IC set {|0>, |1>, |+>, |+i>} as density matrices, spanning Herm(2)."""
    ket0 = torch.tensor([1.0, 0.0], dtype=CDTYPE, device=device)
    ket1 = torch.tensor([0.0, 1.0], dtype=CDTYPE, device=device)
    plus = torch.tensor([1.0, 1.0], dtype=CDTYPE, device=device) / (2 ** 0.5)
    plus_i = torch.tensor([1.0, 1.0j], dtype=CDTYPE, device=device) / (2 ** 0.5)
    return torch.stack([torch.outer(k, k.conj()) for k in (ket0, ket1, plus, plus_i)])


def informationally_complete_inputs(dim: int, device: str | torch.device = "cpu") -> torch.Tensor:
    """IC input density matrices for a ``dim``-dimensional system.

    Single-qubit IC states tensored across ``log2(dim)`` qubits stay IC.
    """
    num_qubits = int(round(float(torch.log2(torch.tensor(float(dim))))))
    if 2 ** num_qubits != dim:
        raise ValueError("dim must be a power of two")
    states = _ic_single_qubit_states(device=device)
    acc = states
    for _ in range(num_qubits - 1):
        acc = torch.stack([torch.kron(a, b) for a in acc for b in states])
    return acc


def recover_channel(
    target_kraus: torch.Tensor,
    *,
    num_kraus: int | None = None,
    steps: int = 200,
    seed: int = 0,
    device: str | torch.device = "cpu",
) -> dict[str, object]:
    """Fit a CPTP-by-construction channel to ``target_kraus`` via its action on
    an informationally-complete input set, using LBFGS in double precision.

    Returns the recovered channel plus action loss, Choi distance, and TP
    residual diagnostics. Zero action loss on IC inputs implies the recovered
    channel equals the target (up to nothing -- the action determines the map).
    """
    target_kraus = target_kraus.to(CDTYPE).to(device)
    dim = target_kraus.shape[-1]
    num_kraus = int(num_kraus or dim * dim)  # full Kraus rank can represent any CPTP map

    inputs = informationally_complete_inputs(dim, device=device)
    target_outputs = apply_kraus(inputs, target_kraus)

    channel = StinespringChannel.random(dim, num_kraus, seed=seed, device=device)
    opt = torch.optim.LBFGS(
        channel.parameters(), lr=1.0, max_iter=steps, line_search_fn="strong_wolfe",
        tolerance_grad=1e-18, tolerance_change=1e-20, history_size=50,
    )

    def closure() -> torch.Tensor:
        opt.zero_grad()
        outs = apply_kraus(inputs, channel.kraus())
        loss = ((outs - target_outputs).abs() ** 2).sum()
        loss.backward()
        return loss

    opt.step(closure)

    with torch.no_grad():
        recovered = channel.kraus()
        outs = apply_kraus(inputs, recovered)
        action_loss = float(((outs - target_outputs).abs() ** 2).sum())
        choi_distance = float(torch.linalg.matrix_norm(choi_matrix(recovered) - choi_matrix(target_kraus)))
        residual = float(tp_residual(recovered))
    return {
        "channel": channel,
        "recovered_kraus": recovered,
        "action_loss": action_loss,
        "choi_distance": choi_distance,
        "tp_residual": residual,
    }
