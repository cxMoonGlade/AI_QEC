from __future__ import annotations

"""XZZX code-spec constructors for the simulator frontend.

The first constructor is intentionally a small compiler/schedule slice: a 3x3
checkerboard XZZX stabilizer layout that exercises mixed-basis checks, repeated
syndrome extraction, final data closure detectors, and one deterministic
observable. It is not a claim that distance, a full memory experiment, or a
Google-style layout has been certified.
"""

from dataclasses import dataclass

from qec_twin.simulator.code_spec import (
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    PauliTerm,
    StabilizerCheck,
)


@dataclass(frozen=True)
class XZZXCodeSpec:
    """Factory wrapper for XZZX-family frontend code specs."""

    layout_size: int = 3
    rounds: int = 2
    variant: str = "checkerboard_compiler_smoke"

    def to_code_spec(self) -> CodeSpec:
        if self.layout_size != 3:
            raise NotImplementedError("only the 3x3 XZZX frontend slice is implemented")
        if self.variant != "checkerboard_compiler_smoke":
            raise NotImplementedError(
                "only variant='checkerboard_compiler_smoke' is implemented in this frontend slice"
            )
        return make_xzzx_3x3_compiler_smoke_spec(rounds=self.rounds)


def make_xzzx_3x3_compiler_smoke_spec(*, rounds: int = 2) -> CodeSpec:
    """Return the current 3x3 XZZX compiler-smoke spec."""

    data_qubits = tuple(
        CodeQubit(_data_index(row, col), "data", (float(row), float(col)))
        for row in range(3)
        for col in range(3)
    )
    ancilla_qubits = tuple(
        CodeQubit(9 + i, "ancilla", coords)
        for i, coords in enumerate(
            (
                (0.5, 0.5),
                (0.5, 1.5),
                (1.5, 0.5),
                (1.5, 1.5),
                (-0.5, 0.5),
                (0.5, 2.5),
                (2.5, 1.5),
                (1.5, -0.5),
            )
        )
    )

    checks = (
        _plaquette("p00", 9, (0, 0), (0.5, 0.5)),
        _plaquette("p01", 10, (0, 1), (0.5, 1.5)),
        _plaquette("p10", 11, (1, 0), (1.5, 0.5)),
        _plaquette("p11", 12, (1, 1), (1.5, 1.5)),
        _edge("top", 13, ((0, 0), (0, 1)), (-0.5, 0.5)),
        _edge("right", 14, ((0, 2), (1, 2)), (0.5, 2.5)),
        _edge("bottom", 15, ((2, 1), (2, 2)), (2.5, 1.5)),
        _edge("left", 16, ((1, 0), (2, 0)), (1.5, -0.5)),
    )
    logicals = (
        LogicalObservableSpec(
            "observable_smoke_z1",
            (PauliTerm(1, "Z"),),
            index=0,
        ),
    )
    return CodeSpec(
        name="xzzx_3x3_checkerboard_compiler_smoke",
        num_qubits=17,
        data_qubits=data_qubits,
        ancilla_qubits=ancilla_qubits,
        checks=checks,
        logical_observables=logicals,
        rounds=rounds,
        metadata={
            "family": "xzzx",
            "layout_size": 3,
            "variant": "checkerboard_compiler_smoke",
            "encoded_distance_certified": False,
            "claim_boundary": (
                "frontend compiler/schedule smoke; not a certified distance-3 memory, "
                "hardware schedule, or analog coupling teacher"
            ),
        },
    )


def _plaquette(
    name: str,
    ancilla: int,
    top_left: tuple[int, int],
    coords: tuple[float, float],
) -> StabilizerCheck:
    row, col = top_left
    corners = ((row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1))
    return StabilizerCheck(name, ancilla, tuple(_term(r, c) for r, c in corners), coords)


def _edge(
    name: str,
    ancilla: int,
    sites: tuple[tuple[int, int], tuple[int, int]],
    coords: tuple[float, float],
) -> StabilizerCheck:
    return StabilizerCheck(name, ancilla, tuple(_term(r, c) for r, c in sites), coords)


def _term(row: int, col: int) -> PauliTerm:
    return PauliTerm(_data_index(row, col), _checkerboard_basis(row, col))


def _data_index(row: int, col: int) -> int:
    return 3 * int(row) + int(col)


def _checkerboard_basis(row: int, col: int) -> str:
    return "X" if (int(row) + int(col)) % 2 == 0 else "Z"
