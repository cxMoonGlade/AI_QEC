#!/usr/bin/env python3
"""Is the transversal-echo frame sign trajectory-dependent under leakage?

The within-cycle carrier applies a transversal Y echo after every non-terminal
round.  On a qutrit that gate is Pauli Y on the {|0>,|1>} subspace and IDENTITY
on the leaked level |2>.  The emitted observable is currently corrected by a
single GLOBAL parity bit derived from the ops the schedule emits.

That correction is exact only if every trajectory receives the same effective
echo count.  A qutrit that is LEAKED when an echo fires receives no flip; if it
later seeps back into the qubit subspace, its history contains fewer effective
echoes than a qutrit that never left.  This script decides, by explicit operator
algebra, whether that difference actually reaches the logical readout.

The question is local: it needs one qutrit of the logical support, not the whole
patch.  A weight-3 Z logical multiplies three such single-site signs, so a single
site flipping its sign flips the logical outcome.

No GPU, no kernel, no sampling -- exact 3x3 and 9x9 matrices only.
"""

from __future__ import annotations

import sys

import numpy as np


def emit(line: str = "") -> None:
    print(line, flush=True)


KET = np.eye(3, dtype=complex)
P_QUBIT = np.diag([1.0, 1.0, 0.0]).astype(complex)


def qutrit_y() -> np.ndarray:
    """Pauli Y on {|0>,|1>}, identity on the leaked level |2>."""

    y = np.zeros((3, 3), dtype=complex)
    y[0, 1] = -1j
    y[1, 0] = 1j
    y[2, 2] = 1.0
    return y


def qutrit_z() -> np.ndarray:
    """The Z observable the logical is built from, restricted to the qubit space."""

    return np.diag([1.0, -1.0, 0.0]).astype(complex)


def leak_out() -> np.ndarray:
    """|1> -> |2>: the coherent-leakage limit, as a Kraus operator."""

    k = np.zeros((3, 3), dtype=complex)
    k[2, 1] = 1.0
    return k


def seep_back() -> np.ndarray:
    """|2> -> |1>: the seepage limit, as a Kraus operator."""

    k = np.zeros((3, 3), dtype=complex)
    k[1, 2] = 1.0
    return k


def apply(ops: list[np.ndarray], state: np.ndarray) -> np.ndarray:
    for op in ops:
        state = op @ state
    return state


def z_sign(state: np.ndarray) -> str:
    """The single-site Z eigenvalue, or a report that the site is not readable."""

    norm = float(np.vdot(state, state).real)
    if norm < 1e-12:
        return "annihilated"
    qubit_weight = float(np.vdot(state, P_QUBIT @ state).real) / norm
    if qubit_weight < 1e-12:
        return "leaked (readout randomised by the CP-instrument)"
    value = float(np.vdot(state, qutrit_z() @ state).real) / norm
    if abs(abs(value) - 1.0) > 1e-9:
        return f"not a Z eigenstate (<Z> = {value:+.6f})"
    return f"{value:+.0f}"


def main() -> int:
    Y = qutrit_y()
    emit("qutrit Y")
    emit("    " + str(np.round(Y, 3)).replace("\n", "\n    "))
    emit(f"    Y @ |2> = {np.round(Y @ KET[:, 2], 6)}   (identity on the leaked level)")
    emit(f"    Y**2 == I : {np.allclose(Y @ Y, np.eye(3))}")
    emit()

    rounds = 3          # two non-terminal echoes
    echoes = rounds - 1
    emit(f"R = {rounds}  ->  {echoes} non-terminal echoes")
    emit(f"global parity applied by the carrier today: (R-1)*w mod 2 with w=3  ->  "
         f"{(echoes * 3) % 2}")
    emit()

    start = KET[:, 1].copy()          # |1>, a Z = -1 eigenstate
    emit(f"start |1>, single-site Z = {z_sign(start)}")
    emit()

    emit("history A -- never leaves the qubit subspace")
    emit("    echo, echo")
    a = apply([Y, Y], start)
    sign_a = z_sign(a)
    emit(f"    single-site Z = {sign_a}")
    emit()

    emit("history B -- leaks before the first echo, seeps back after it")
    emit("    leak(|1>->|2>), echo, seep(|2>->|1>), echo")
    b = apply([Y, seep_back(), Y, leak_out()][::-1], start)
    sign_b = z_sign(b)
    emit(f"    single-site Z = {sign_b}")
    emit()

    emit("history C -- leaks and stays leaked")
    c = apply([Y, Y, leak_out()][::-1], start)
    emit(f"    single-site Z = {z_sign(c)}")
    emit()

    # Negative controls: neither ingredient alone moves the readout. Without them
    # a deviation in the interleaved case could be blamed on the leak/seep pair
    # rather than on its non-commutation with the echo.
    emit("negative controls")
    ctrl_leak_only = apply([seep_back(), leak_out()][::-1], start)
    ctrl_echo_only = apply([Y, Y], start)
    emit(f"    leak+seep, no echo    -> {z_sign(ctrl_leak_only)}")
    emit(f"    echo twice, no leak   -> {z_sign(ctrl_echo_only)}")
    emit()

    # The coherent regime: partial leakage amplitude at echo time. Here the echo
    # does not merely flip a sign, because it acts as Y on the qubit-subspace
    # amplitude and as identity on the leaked amplitude at the same time.
    emit("coherent partial leakage -- is there even a sign to book?")

    def u_leak(angle: float) -> np.ndarray:
        u = np.eye(3, dtype=complex)
        u[1, 1] = np.cos(angle)
        u[1, 2] = -np.sin(angle)
        u[2, 1] = np.sin(angle)
        u[2, 2] = np.cos(angle)
        return u

    commutator = float(np.abs(Y @ u_leak(0.25 * np.pi) - u_leak(0.25 * np.pi) @ Y).max())
    emit(f"    ||[Y, U_leak(pi/4)]|| = {commutator:.6f}   (echo and leakage do not commute)")
    for angle in (0.0, 0.15, 0.25):
        theta = angle * np.pi
        state = apply(
            [Y, u_leak(-theta), Y, u_leak(theta)][::-1], start
        )
        emit(f"    theta = {angle:.2f}pi  ->  {z_sign(state)}")
    emit()

    differs = sign_a != sign_b and "leaked" not in sign_b and "annihilated" not in sign_b
    emit("verdict")
    emit(f"    A (never leaked)      -> {sign_a}")
    emit(f"    B (leaked and back)   -> {sign_b}")
    if differs:
        emit()
        emit("    The two histories end in DIFFERENT single-site Z eigenstates while the")
        emit("    carrier applies the SAME global parity bit to both. The echo frame is")
        emit("    trajectory-dependent under leakage, and a global correction cannot be")
        emit("    exact for a trajectory that leaks and returns.")
        return 1
    emit()
    emit("    The two histories agree: a global parity bit is exact for this case.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
