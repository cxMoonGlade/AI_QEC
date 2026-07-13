from __future__ import annotations

"""theta-parameterised, differentiable, CPTP-by-construction mechanism dictionary.

Torch port of the <=2q NumPy builders in :mod:`qec_twin.forward.channels`
(window-channel build spec, ``docs/cf_wr/window_channel_spec.md`` sections 2 and
10). Each builder maps a single real scalar leaf ``theta`` (``requires_grad`` ok)
to a Kraus stack ``(r, d, d)`` in ``complex128``, CPTP by construction:

- **Coherent unitary** (the differentiator): ``U(theta) = matrix_exp(-i theta G / 2)``
  for a fixed Hermitian Pauli generator ``G`` per mechanism; the Kraus stack is the
  single operator ``[U]`` so ``U^dag U = I`` exactly (TP) and the map is unitary
  (CP). Coherence is the point: these stay unitary and are NEVER collapsed to a
  Pauli rate.
- **Non-unitary CPTP**: amplitude/phase damping, thermal excitation, leakage
  surrogate, 2q depolarizing, correlated relaxation, Pauli-stochastic. The physical
  strength is reparameterised ``p = sigmoid(theta)`` so it stays in ``(0, 1)`` and is
  differentiable everywhere (no ``sqrt(0)`` infinite gradient). ``NUMERICAL_ZERO`` is
  the hard floor only, applied via ``clamp`` so the ``sqrt`` gradient stays finite at
  the boundary; in the ``sigmoid`` interior the floor is a no-op.

Each torch builder is the exact differentiable mirror of the same-named
``channels.py`` NumPy builder (cross-validated in ``tests/test_window_channel.py``,
spec section 6.4). Registries :data:`MECH_1Q` and :data:`MECH_2Q` expose exactly the
section-10 keys. The arity-general builder signature
``def <name>(theta, *, device=None) -> Tensor`` lets the concurrently-built
``window_channel.py`` / ``window_diagnostics.py`` siblings link against the frozen
section-10 contract.

Precision is ``complex128`` (matches :mod:`qec_twin.forward.cptp_channel`); a
``device`` kwarg is honoured everywhere so model compute can stay on GPU.
"""

import torch

from qec_twin.numerics import NUMERICAL_ZERO

__all__ = [
    "CDTYPE",
    "RDTYPE",
    # 1q coherent
    "rx",
    "ry",
    "rz",
    # 1q non-unitary CPTP
    "amp_damp",
    "phase_damp",
    "pauli_x",
    "pauli_y",
    "pauli_z",
    "thermal",
    "custom_nonpauli",
    "leakage",
    # 2q coherent
    "rzz",
    "rxx",
    "ryy",
    "rxx_ryy",
    "cphase",
    "two_pauli_xy",
    "two_pauli_zx",
    "two_pauli_zy",
    # 2q non-unitary CPTP
    "depol2",
    "corr_relax",
    # registries
    "MECH_1Q",
    "MECH_2Q",
]

CDTYPE = torch.complex128
RDTYPE = torch.float64


# --------------------------------------------------------------------------- #
# Generator / parameter plumbing                                              #
# --------------------------------------------------------------------------- #
def _effective_device(theta: torch.Tensor, device):
    """Resolve the device fixed operators must live on.

    The §10 default is ``device=None``. When omitted, fixed operators (generators,
    Pauli tables) must follow ``theta``'s device so a CUDA leaf with ``device=None``
    builds entirely on CUDA — otherwise a CUDA ``theta`` times a CPU-default
    generator raises a device mismatch. Returns ``device`` verbatim when given.
    """

    if device is not None:
        return device
    if isinstance(theta, torch.Tensor):
        return theta.device
    return None


def _as_real_scalar(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coerce ``theta`` to a real ``float64`` scalar on ``device`` (grad-preserving)."""

    if not isinstance(theta, torch.Tensor):
        theta = torch.as_tensor(theta, dtype=RDTYPE)
    theta = theta.to(RDTYPE)
    if device is not None:
        theta = theta.to(device)
    return theta.reshape(())


def _pauli_1q(device=None) -> dict[str, torch.Tensor]:
    i = torch.eye(2, dtype=CDTYPE, device=device)
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE, device=device)
    y = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE, device=device)
    z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE, device=device)
    return {"I": i, "X": x, "Y": y, "Z": z}


def _two_pauli(left: str, right: str, device=None) -> torch.Tensor:
    one = _pauli_1q(device=device)
    return torch.kron(one[left.upper()], one[right.upper()])


def _coherent_kraus(generator: torch.Tensor, theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """``U(theta) = matrix_exp(-i theta G / 2)`` as a single-operator Kraus stack ``(1, d, d)``.

    Exact differentiable mirror of the closed-form ``channels.py`` unitaries
    (``rx_unitary`` etc.): ``cos(t/2) I - i sin(t/2) G == exp(-i t G / 2)`` for an
    involutory Hermitian generator ``G``. Unitary => CPTP by construction; coherence
    is preserved (never twirled to a Pauli rate).
    """

    dev = _effective_device(theta, device)
    t = _as_real_scalar(theta, device=dev)
    gen = generator.to(CDTYPE)
    if dev is not None:
        gen = gen.to(dev)
    exponent = (-0.5j) * t.to(CDTYPE) * gen
    unitary = torch.matrix_exp(exponent)
    return unitary.unsqueeze(0)


def _strength(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Non-unitary CPTP strength ``p = sigmoid(theta) in (0, 1)`` (real ``float64`` scalar)."""

    return torch.sigmoid(_as_real_scalar(theta, device=device))


def _sqrt_floor(value: torch.Tensor) -> torch.Tensor:
    """``sqrt`` with a ``NUMERICAL_ZERO`` floor (keeps the gradient finite at 0).

    Differentiable mirror of ``positive_floor`` before ``math.sqrt`` in ``channels.py``;
    a no-op in the ``sigmoid`` interior where the argument is already ``> NUMERICAL_ZERO``.
    """

    return torch.sqrt(torch.clamp(value, min=NUMERICAL_ZERO))


def _kraus_stack(ops: list[torch.Tensor], *, device=None) -> torch.Tensor:
    return torch.stack([op.to(CDTYPE) for op in ops]).to(device) if device is not None else torch.stack(
        [op.to(CDTYPE) for op in ops]
    )


# --------------------------------------------------------------------------- #
# 1q coherent unitaries  (G = X / Y / Z)                                       #
# --------------------------------------------------------------------------- #
def rx(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent 1q X-rotation ``exp(-i theta X / 2)`` (channels.py ``rx_unitary``; M6)."""

    p = _pauli_1q(device=device)
    return _coherent_kraus(p["X"], theta, device=device)


def ry(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent 1q Y-rotation ``exp(-i theta Y / 2)`` (channels.py ``ry_unitary``; M20)."""

    p = _pauli_1q(device=device)
    return _coherent_kraus(p["Y"], theta, device=device)


def rz(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent 1q Z-rotation ``exp(-i theta Z / 2)`` (channels.py ``rz_unitary``; M7)."""

    p = _pauli_1q(device=device)
    return _coherent_kraus(p["Z"], theta, device=device)


# --------------------------------------------------------------------------- #
# 1q non-unitary CPTP  (strength p = sigmoid(theta))                           #
# --------------------------------------------------------------------------- #
def amp_damp(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Amplitude damping, ``gamma = sigmoid(theta)`` (channels.py ``amplitude_damping_kraus``; M4)."""

    g = _strength(theta, device=device)
    zero = torch.zeros((), dtype=RDTYPE, device=g.device)
    one = torch.ones((), dtype=RDTYPE, device=g.device)
    k0 = torch.stack(
        [torch.stack([one, zero]), torch.stack([zero, _sqrt_floor(1.0 - g)])]
    ).to(CDTYPE)
    k1 = torch.stack(
        [torch.stack([zero, _sqrt_floor(g)]), torch.stack([zero, zero])]
    ).to(CDTYPE)
    return _kraus_stack([k0, k1], device=device)


def phase_damp(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Phase damping, ``gamma_phi = sigmoid(theta)`` (channels.py ``phase_damping_kraus``)."""

    g = _strength(theta, device=device)
    pauli = _pauli_1q(device=g.device)
    k0 = _sqrt_floor(1.0 - g).to(CDTYPE) * pauli["I"]
    k1 = _sqrt_floor(g).to(CDTYPE) * pauli["Z"]
    return _kraus_stack([k0, k1], device=device)


def _pauli_stochastic_kraus(
    probs: dict[str, torch.Tensor], *, device=None
) -> torch.Tensor:
    """Differentiable mirror of ``channels.py`` ``pauli_stochastic_kraus``.

    ``K_I = sqrt(1 - sum p) I`` then ``K_P = sqrt(p_P) P`` for P in X, Y, Z. Each
    incoming ``p`` is a ``sigmoid`` strength in ``(0, 1)`` floored via ``_sqrt_floor``.
    """

    dev = device
    if dev is None:
        for key in ("X", "Y", "Z"):
            if key in probs and isinstance(probs[key], torch.Tensor):
                dev = probs[key].device
                break
    pauli = _pauli_1q(device=dev)
    total = None
    for key in ("X", "Y", "Z"):
        if key in probs:
            total = probs[key] if total is None else total + probs[key]
    if total is None:
        total = torch.zeros((), dtype=RDTYPE, device=dev)
    ops = [_sqrt_floor(1.0 - total).to(CDTYPE) * pauli["I"]]
    for key in ("X", "Y", "Z"):
        if key in probs:
            ops.append(_sqrt_floor(probs[key]).to(CDTYPE) * pauli[key])
    return _kraus_stack(ops, device=device)


def pauli_x(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """1q stochastic X flip, ``p = sigmoid(theta)`` (channels.py ``pauli_stochastic_kraus({X})``; M25)."""

    p = _strength(theta, device=device)
    return _pauli_stochastic_kraus({"X": p}, device=device)


def pauli_y(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """1q stochastic Y flip, ``p = sigmoid(theta)`` (channels.py ``pauli_stochastic_kraus({Y})``; M26)."""

    p = _strength(theta, device=device)
    return _pauli_stochastic_kraus({"Y": p}, device=device)


def pauli_z(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """1q stochastic Z flip, ``p = sigmoid(theta)`` (channels.py ``pauli_stochastic_kraus({Z})``; M5)."""

    p = _strength(theta, device=device)
    return _pauli_stochastic_kraus({"Z": p}, device=device)


def thermal(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Thermal excitation, ``gamma_up = sigmoid(theta)`` (channels.py ``thermal_excitation_kraus``; M24)."""

    g = _strength(theta, device=device)
    zero = torch.zeros((), dtype=RDTYPE, device=g.device)
    one = torch.ones((), dtype=RDTYPE, device=g.device)
    k0 = torch.stack(
        [torch.stack([_sqrt_floor(1.0 - g), zero]), torch.stack([zero, one])]
    ).to(CDTYPE)
    k1 = torch.stack(
        [torch.stack([zero, zero]), torch.stack([_sqrt_floor(g), zero])]
    ).to(CDTYPE)
    return _kraus_stack([k0, k1], device=device)


def custom_nonpauli(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent/non-Pauli CPTP perturbation, ``eta = sigmoid(theta)``.

    Mirror of ``channels.py`` ``custom_non_pauli_kraus``: amplitude damping at
    strength ``eta`` post-composed with the FIXED rotation ``rz(0.37) rx(0.23)``
    (the rotation constants are part of the mechanism definition, not learnable).
    """

    base = amp_damp(theta, device=device)  # eta = sigmoid(theta) is the channel strength
    dev = base.device
    # fixed (non-learnable) coherent dressing, exact mirror of channels.py constants
    rot = (
        _coherent_kraus(_pauli_1q(device=dev)["Z"], torch.tensor(0.37, dtype=RDTYPE, device=dev), device=dev)[0]
        @ _coherent_kraus(_pauli_1q(device=dev)["X"], torch.tensor(0.23, dtype=RDTYPE, device=dev), device=dev)[0]
    )
    ops = [base[idx] @ rot for idx in range(base.shape[0])]
    return _kraus_stack(ops, device=device)


def leakage(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Leakage relaxation surrogate, ``p = sigmoid(theta)``.

    Mirror of ``channels.py`` ``leakage_relaxation_surrogate_kraus``: every
    ``amp_damp(p)`` operator post-composed with every ``phase_damp(p)`` operator
    (``damp @ phase``), 4 Kraus total.
    """

    damp = amp_damp(theta, device=device)
    phase = phase_damp(theta, device=device)
    ops = [damp[di] @ phase[pi] for di in range(damp.shape[0]) for pi in range(phase.shape[0])]
    return _kraus_stack(ops, device=device)


# --------------------------------------------------------------------------- #
# 2q coherent unitaries  (G = ZZ / XX / YY / ... )                            #
# --------------------------------------------------------------------------- #
def rzz(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent ZZ-rotation ``exp(-i theta ZZ / 2)`` (channels.py ``rzz_unitary``; M8)."""

    return _coherent_kraus(_two_pauli("Z", "Z", device=device), theta, device=device)


def rxx(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent XX-rotation ``exp(-i theta XX / 2)`` (channels.py ``rxx_unitary``; M22)."""

    return _coherent_kraus(_two_pauli("X", "X", device=device), theta, device=device)


def ryy(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent YY-rotation ``exp(-i theta YY / 2)`` (channels.py ``ryy_unitary``; M23)."""

    return _coherent_kraus(_two_pauli("Y", "Y", device=device), theta, device=device)


def rxx_ryy(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent XX-then-YY rotation ``exp(-i theta YY / 2) exp(-i theta XX / 2)``.

    Mirror of ``channels.py`` ``rxx_ryy_unitary`` (M10) with a SHARED angle
    ``theta_x = theta_y = theta`` (single-leaf section-10 signature; the
    asymmetric two-angle form stays available via the NumPy oracle for tests).
    ``XX`` and ``YY`` commute, so the ordered product equals
    ``exp(-i theta (XX + YY) / 2)``; computed as the explicit product to mirror the
    NumPy builder elementwise.
    """

    u_xx = rxx(theta, device=device)[0]
    u_yy = ryy(theta, device=device)[0]
    return (u_yy @ u_xx).unsqueeze(0)


def cphase(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Controlled-phase error ``diag(1, 1, 1, exp(-i theta))`` (channels.py ``controlled_phase_error_unitary``; M21).

    Generator form: ``exp(-i theta G / 2)`` with ``G = diag(0, 0, 0, 2)`` so
    ``U = diag(1, 1, 1, exp(-i theta))`` exactly.
    """

    t = _as_real_scalar(theta, device=device)
    generator = torch.diag(torch.tensor([0.0, 0.0, 0.0, 2.0], dtype=CDTYPE, device=t.device))
    return _coherent_kraus(generator, theta, device=device)


def two_pauli_xy(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent two-Pauli ``exp(-i theta (X (x) Y) / 2)`` (channels.py ``two_pauli_rotation(X, Y)``; M28)."""

    return _coherent_kraus(_two_pauli("X", "Y", device=device), theta, device=device)


def two_pauli_zx(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent two-Pauli ``exp(-i theta (Z (x) X) / 2)`` (channels.py ``two_pauli_rotation(Z, X)``; M29)."""

    return _coherent_kraus(_two_pauli("Z", "X", device=device), theta, device=device)


def two_pauli_zy(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Coherent two-Pauli ``exp(-i theta (Z (x) Y) / 2)`` (channels.py ``two_pauli_rotation(Z, Y)``; M30)."""

    return _coherent_kraus(_two_pauli("Z", "Y", device=device), theta, device=device)


# --------------------------------------------------------------------------- #
# 2q non-unitary CPTP  (strength p = sigmoid(theta))                          #
# --------------------------------------------------------------------------- #
def depol2(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """2q depolarizing, ``p = sigmoid(theta)`` (channels.py ``two_qubit_depolarizing_kraus``; M9).

    ``K_II = sqrt(1 - p) I_4`` then ``K_PQ = sqrt(p / 15) (P (x) Q)`` over the 15
    non-identity 2q Paulis.
    """

    p = _strength(theta, device=device)
    pauli = _pauli_1q(device=p.device)
    labels = [
        (left, right)
        for left in ("I", "X", "Y", "Z")
        for right in ("I", "X", "Y", "Z")
    ]
    non_identity = [(l, r) for (l, r) in labels if not (l == "I" and r == "I")]
    eye4 = torch.eye(4, dtype=CDTYPE, device=p.device)
    ops = [_sqrt_floor(1.0 - p).to(CDTYPE) * eye4]
    each = p / len(non_identity)
    sqrt_each = _sqrt_floor(each).to(CDTYPE)
    for left, right in non_identity:
        ops.append(sqrt_each * torch.kron(pauli[left], pauli[right]))
    return _kraus_stack(ops, device=device)


def corr_relax(theta: torch.Tensor, *, device=None) -> torch.Tensor:
    """Correlated relaxation, ``gamma = sigmoid(theta)`` (channels.py ``correlated_relaxation_kraus``; M12).

    ``K0 = diag(1, 1, 1, sqrt(1 - g))`` and a single jump ``K1`` with
    ``K1[0, 3] = sqrt(g)`` (|11> -> |00>).
    """

    g = _strength(theta, device=device)
    diag = torch.stack(
        [
            torch.ones((), dtype=RDTYPE, device=g.device),
            torch.ones((), dtype=RDTYPE, device=g.device),
            torch.ones((), dtype=RDTYPE, device=g.device),
            _sqrt_floor(1.0 - g),
        ]
    ).to(CDTYPE)
    k0 = torch.diag(diag)
    # single |11> -> |00> jump; index/zeros are structural, only the amplitude is learnable
    jump = torch.zeros((4, 4), dtype=CDTYPE, device=g.device)
    jump[0, 3] = 1.0
    k1 = _sqrt_floor(g).to(CDTYPE) * jump
    return _kraus_stack([k0, k1], device=device)


# --------------------------------------------------------------------------- #
# Registries — EXACTLY the section-10 keys                                     #
# --------------------------------------------------------------------------- #
MECH_1Q: dict[str, object] = {
    "rx": rx,
    "ry": ry,
    "rz": rz,
    "amp_damp": amp_damp,
    "phase_damp": phase_damp,
    "pauli_x": pauli_x,
    "pauli_y": pauli_y,
    "pauli_z": pauli_z,
    "thermal": thermal,
    "custom_nonpauli": custom_nonpauli,
    "leakage": leakage,
}

MECH_2Q: dict[str, object] = {
    "rzz": rzz,
    "rxx": rxx,
    "ryy": ryy,
    "rxx_ryy": rxx_ryy,
    "cphase": cphase,
    "two_pauli_xy": two_pauli_xy,
    "two_pauli_zx": two_pauli_zx,
    "two_pauli_zy": two_pauli_zy,
    "depol2": depol2,
    "corr_relax": corr_relax,
}
