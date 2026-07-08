"""Shared test fixtures + guard helpers (Wave 1, contract row C2).

Binding contract: ``docs/twin_validation/api_hardening_ownership_design.md`` (row C2,
NAMING STANDARD, DEVIOUS-TEST STANDARD). Scope rule (see ``README.md``): shared test
support ONLY -- never production code, never a home for anything with an independence
constraint against a specific backend (references that referee a backend stay
deliberately local per the contract's "Explicitly NOT centralized" list).

Contents:
  * ``require_precondition`` -- class-(c) precondition asserts with the ONE
    machine-greppable prefix (a precondition failure is never a gate miss).
  * ``assert_control_trips`` -- the anti-vacuous control SHAPE (the bespoke broken
    inputs themselves stay local to each test, by contract).
  * ``assert_with_margin`` -- the Side-B MARGIN discipline (two-sided per-unit
    extension): a tolerance-bearing gate assert that ALSO rejects knife-edge passes
    (margin factor < ``min_margin``) with the distinct greppable
    ``EVIL-MARGINAL (class c): `` prefix (the 1.181e-12-vs-1e-12 lesson).
  * ``random_cptp_kraus`` / ``random_density_matrix`` -- the one random-input builder
    each (backend + return-shape flags), CPTP/trace asserted internally at 1e-12.
    Random INPUT generation is not a reference -- safe to centralize.
  * ``load_outputs_module`` -- importlib shim for committed scripts under ``outputs/``.
  * ``canonical_rep_code_spec`` / ``canonical_mixed_code_spec`` / ``canonical_circuit_ir`` /
    ``canonical_sealed_schedule`` / ``canonical_stim_circuit`` -- deterministic VALID INPUT
    fixtures (INPUTS, not references) the schema/compiler batches previously re-derived per
    file; import these instead of re-rolling a rep-code CodeSpec / CircuitIR / schedule.

Self-tested by ``tests/_support/test_support_selftest.py`` (meta-tests: the DEVIOUS-TEST
STANDARD's "test infrastructure defends itself" requirement).
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np

try:
    import torch
except Exception:  # noqa: BLE001 -- the numpy backend must work on a torch-less box
    torch = None

#: repo root (tests/_support/fixtures.py -> tests/_support -> tests -> root)
_REPO_ROOT = Path(__file__).resolve().parents[2]

#: The ONE machine-greppable precondition prefix (contract C2). A message with this
#: prefix marks a class-(c) harness precondition failure, NEVER a gate miss.
PRECONDITION_PREFIX = "PRECONDITION (class c, not a gate miss): "

#: The ONE machine-greppable EVIL-MARGINAL prefix (two-sided extension, Side B (i)).
#: A message with this prefix marks a class-(c) KNIFE-EDGE PASS: the gated claim
#: held, but with a margin factor below ``min_margin`` -- not evidence, a re-engineer
#: signal (the measured 1.181e-12-vs-1e-12 lesson, made structural). Never a gate miss.
EVIL_MARGINAL_PREFIX = "EVIL-MARGINAL (class c): "

#: Internal build tolerance for the random-input builders (an (a)-class identity on the
#: builder's own output -- distinct from any test's registered gate tolerance).
BUILDER_TOL = 1.0e-12


def require_precondition(cond, msg: str, remedy: str = "re-seed this case") -> None:
    """Assert a harness PRECONDITION (epistemic class (c)) with the greppable prefix.

    A precondition failure means the test CASE is malformed (bad seed / missing input /
    knife-edge draw), not that the gated claim failed -- gate-result triage greps
    ``PRECONDITION (class c, not a gate miss): `` to separate the two.
    """
    if not cond:
        raise AssertionError(f"{PRECONDITION_PREFIX}{msg}; remedy: {remedy}")


def assert_control_trips(check_fn, broken_input, gate_tol) -> None:
    """The anti-vacuous control SHAPE (KILLER requirement): assert that ``check_fn``
    FAILS (raises AssertionError) on ``broken_input`` at the real ``gate_tol``.

    ``check_fn(broken_input, gate_tol)`` must ASSERT (raise AssertionError) when its
    input violates the gate; returning normally on the broken input means the control
    is INERT and this helper itself raises (a check that has never been shown to fail
    is unproven -- scrutinize-vacuous-checks discipline). Non-AssertionError exceptions
    PROPAGATE: a crashing harness is a bug, never a fired control. The bespoke broken
    inputs stay local to each test (contract C2 -- that bespokeness IS the discipline).
    ``gate_tol`` defaults to nothing here on purpose: pass the real check's registered
    gate tolerance, never an ad-hoc value.
    """
    tripped = False
    try:
        check_fn(broken_input, gate_tol)
    except AssertionError:
        tripped = True
    if not tripped:
        name = getattr(check_fn, "__name__", repr(check_fn))
        raise AssertionError(
            f"CONTROL INERT (vacuous check): {name} did not trip on the broken input "
            f"at gate_tol={gate_tol!r} -- the positive check it guards is unproven")


def assert_with_margin(value: float, threshold: float, *, mode: str,
                       min_margin: float = 10.0, what: str) -> float:
    """Threshold assert WITH the Side-B margin discipline (two-sided extension (i)).

    Asserts ``value`` passes ``threshold`` in the given direction (``mode="le"``:
    ``value <= threshold``; ``mode="ge"``: ``value >= threshold``) AND that the
    measured MARGIN FACTOR (``threshold/value`` for ``"le"``, ``value/threshold``
    for ``"ge"``) is ``>= min_margin``. Three outcomes:

      * wide pass -> returns the measured margin factor (printable evidence);
      * violation -> plain ``AssertionError`` (a genuine GATE MISS; no special
        prefix -- greppably DISTINCT from the marginal case below);
      * knife-edge pass (margin factor < ``min_margin``) -> ``AssertionError``
        with the machine-greppable ``EVIL-MARGINAL (class c): `` prefix NAMING the
        measured margin. A pass within ``min_margin``x of its gate is treated as a
        class-(c) precondition failure of the CASE (too weak an effect / too tight
        an engineered violation -- the measured 1.181e-12-vs-CPTP_TOL=1e-12 lesson,
        K-4), never as evidence and never as a reason to relax the gate.

    ``what`` names the gated quantity in both messages. ``NaN`` on either side
    NEVER passes (K-7: a NaN-swallowed comparison must fail loud). Margin factors
    are meaningful for positive denominators (tolerance/score gates -- the intended
    use); a non-positive denominator under a passing value is treated as INFINITE
    margin (documented permissiveness, not a gate).
    """
    if mode not in ("le", "ge"):
        raise ValueError(f"assert_with_margin: mode must be 'le' or 'ge' (got {mode!r})")
    v, t = float(value), float(threshold)
    if math.isnan(v) or math.isnan(t):
        raise AssertionError(
            f"{what}: NaN in threshold check (value={value!r}, threshold={threshold!r})"
            f" -- NaN never passes a gate (K-7 degenerate-input shadowing)")
    passed = (v <= t) if mode == "le" else (v >= t)
    if not passed:
        raise AssertionError(
            f"{what}: value {v:.6e} FAILS threshold {t:.6e} (mode {mode!r})")
    if mode == "le":
        margin = math.inf if v <= 0.0 else t / v
    else:
        margin = math.inf if t <= 0.0 else v / t
    if margin < float(min_margin):
        raise AssertionError(
            f"{EVIL_MARGINAL_PREFIX}{what}: value {v:.6e} passes threshold {t:.6e} "
            f"(mode {mode!r}) with measured margin factor {margin:.6g} < min_margin "
            f"{float(min_margin):.6g} -- a knife-edge pass is not evidence (the "
            f"1.181e-12-vs-1e-12 lesson, K-4); remedy: widen the effect / "
            f"re-engineer the case, never relax the gate")
    return margin


# --------------------------------------------------------------------------- #
# Random-input builders (one each; backend + return-shape flags -- contract C2)#
# --------------------------------------------------------------------------- #
def _assert_cptp(stack, tol: float = BUILDER_TOL) -> None:
    """Internal completeness check on a stacked ``[K, d, d]`` Kraus set:
    ``sum_k K_k^H K_k == I_d`` elementwise within ``tol``. Exposed (module-private) so
    the self-test can DEMONSTRATE it trips on a sabotaged stack (DEVIOUS-TEST STANDARD:
    an internal assert that has never fired is unproven)."""
    k = np.asarray(stack)
    d = k.shape[-1]
    gram = np.einsum("kij,kil->jl", k.conj(), k)
    resid = float(np.abs(gram - np.eye(d)).max())
    if resid > tol:
        raise AssertionError(
            f"random_cptp_kraus internal CPTP check tripped: completeness residual "
            f"{resid:.3e} > {tol:.1e} on a [K={k.shape[0]}, d={d}] stack")


def _assert_density(rho, tol: float = BUILDER_TOL) -> None:
    """Internal density-matrix check on a ``[d, d]`` matrix: unit trace
    (``|Re tr - 1| <= tol`` and ``|Im tr| <= tol``) AND hermiticity
    (``max|rho - rho^H| <= tol``). Exposed (module-private) so the self-test can
    DEMONSTRATE it trips on a sabotaged rho (DEVIOUS-TEST STANDARD: an internal assert
    that has never fired is unproven). Behaviour-identical to the inline checks it
    replaces -- the raise-side branch is structurally unreachable for the algebraic
    construction ``rho = A A^H / tr(A A^H)`` (a registered defensive_assert), covered
    here by the sabotaged-rho meta-test plus the Hermitian+PSD+unit-trace property
    test on the legitimate path."""
    r = np.asarray(rho)
    tr = np.trace(r)
    if abs(tr.real - 1.0) > tol or abs(tr.imag) > tol:
        raise AssertionError(
            f"random_density_matrix internal trace check tripped: tr={tr!r}")
    if float(np.abs(r - r.conj().T).max()) > tol:
        raise AssertionError(
            "random_density_matrix internal hermiticity check tripped")


def random_cptp_kraus(n_kraus: int, dim: int, rng: np.random.Generator, *,
                      backend: str = "torch", stacked: bool = True,
                      device=None, dtype=None):
    """A random CPTP Kraus set via QR of a stacked Gaussian block (exactly complete:
    ``Q^H Q = I_dim`` => ``sum_k K_k^H K_k = I``), CPTP-asserted internally at 1e-12.

    Returns (contract C2 return-shape flags):
      * ``backend="torch"``  -> stacked ``[n_kraus, dim, dim]`` complex tensor
        (``stacked=True``) or a list of ``[dim, dim]`` tensors (``stacked=False``);
        ``device``/``dtype`` forwarded (default: torch.complex128 on the default device).
      * ``backend="numpy"``  -> the same shapes as ``np.complex128`` arrays
        (``device``/``dtype=None`` only).
    """
    require_precondition(n_kraus >= 1 and dim >= 2,
                         f"random_cptp_kraus needs n_kraus>=1, dim>=2 (got {n_kraus}, {dim})",
                         remedy="fix the builder call")
    block = (rng.standard_normal((n_kraus * dim, dim))
             + 1j * rng.standard_normal((n_kraus * dim, dim)))
    qmat, _ = np.linalg.qr(block)  # (n_kraus*dim, dim) with qmat^H qmat = I_dim
    stack = np.ascontiguousarray(qmat.reshape(n_kraus, dim, dim)).astype(np.complex128)
    _assert_cptp(stack)
    if backend == "numpy":
        if device is not None or dtype is not None:
            raise ValueError("backend='numpy' takes no device/dtype")
        return stack if stacked else [stack[k] for k in range(n_kraus)]
    if backend == "torch":
        if torch is None:
            raise RuntimeError("backend='torch' requested but torch is not importable")
        t = torch.tensor(stack, dtype=(dtype or torch.complex128), device=device)
        return t if stacked else [t[k] for k in range(n_kraus)]
    raise ValueError(f"unknown backend {backend!r} (use 'torch' or 'numpy')")


def random_density_matrix(dim: int, rng: np.random.Generator, *,
                          backend: str = "torch", device=None, dtype=None):
    """A random full-rank mixed density matrix ``rho = A A^H / tr(A A^H)`` (PSD by
    construction), with unit trace + hermiticity asserted internally at 1e-12.

    ``backend="torch"`` -> ``[dim, dim]`` complex tensor (``device``/``dtype`` forwarded,
    default torch.complex128); ``backend="numpy"`` -> ``np.complex128`` array.
    """
    require_precondition(dim >= 2, f"random_density_matrix needs dim>=2 (got {dim})",
                         remedy="fix the builder call")
    a = rng.standard_normal((dim, dim)) + 1j * rng.standard_normal((dim, dim))
    rho = a @ a.conj().T
    rho = rho / np.trace(rho).real
    _assert_density(rho)
    if backend == "numpy":
        if device is not None or dtype is not None:
            raise ValueError("backend='numpy' takes no device/dtype")
        return rho.astype(np.complex128)
    if backend == "torch":
        if torch is None:
            raise RuntimeError("backend='torch' requested but torch is not importable")
        return torch.tensor(rho, dtype=(dtype or torch.complex128), device=device)
    raise ValueError(f"unknown backend {backend!r} (use 'torch' or 'numpy')")


# --------------------------------------------------------------------------- #
# outputs/ script import shim                                                  #
# --------------------------------------------------------------------------- #
def load_outputs_module(relpath: str):
    """Import a committed script under ``outputs/`` as a module (spec_from_file_location).

    ``relpath`` is relative to the REPO ROOT (e.g.
    ``"outputs/teacher_prereg/exact_floor_run.py"``). The script must be
    ``__main__``-guarded (scripted-execution discipline) -- importing it must run no
    side effects. Missing file -> a loud class-(c) precondition failure.
    """
    path = (_REPO_ROOT / relpath).resolve()
    require_precondition(path.is_file(), f"outputs script missing: {path}",
                         remedy="check the relpath / local outputs checkout")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# Canonical code / circuit / schedule / stim INPUT fixtures                    #
# --------------------------------------------------------------------------- #
# Deterministic VALID inputs to FEED the units under test. These are INPUTS, not
# references -- like ``random_cptp_kraus`` they carry no independence constraint, so they
# are safe to centralize (an independent RECOMPUTE that referees a specific module's
# OUTPUT stays LOCAL per contract C2). Every schema/compiler batch (D15-D19) re-derived a
# near-identical ``_valid_rep_spec`` / ``_rep_spec`` / ``_mixed_spec`` / ``_rich_circuit``;
# these are the shared canonical versions so later batches ``import`` instead of re-rolling.
# Lazy imports keep this module's import-time deps minimal (numpy + optional torch) for the
# many tests that use only the helpers above. Frozen dataclasses => each call is fresh+safe.

def canonical_rep_code_spec(rounds: int = 3):
    """A clean d=3 Z-memory repetition ``CodeSpec`` (5 qubits): checks z0=Z0Z1 (anc3),
    z1=Z1Z2 (anc4); logical LZ=Z0. The minimal valid all-Z spec (schema / record-layout /
    code-spec batches). ``rounds`` >= 2 (the detector-delta requirement)."""
    from error_coupling_simulator.frontend.code_spec import (
        CodeSpec, CodeQubit, PauliTerm, StabilizerCheck, LogicalObservableSpec)
    return CodeSpec(
        name="rep3z", num_qubits=5,
        data_qubits=(CodeQubit(0, "data", (0.0,)), CodeQubit(1, "data", (1.0,)),
                     CodeQubit(2, "data", (2.0,))),
        ancilla_qubits=(CodeQubit(3, "ancilla"), CodeQubit(4, "ancilla")),
        checks=(StabilizerCheck("z0", 3, (PauliTerm(0, "Z"), PauliTerm(1, "Z")), (0.5,)),
                StabilizerCheck("z1", 4, (PauliTerm(1, "Z"), PauliTerm(2, "Z")), (1.5,))),
        logical_observables=(LogicalObservableSpec("LZ", (PauliTerm(0, "Z"),), index=0),),
        rounds=int(rounds))


def canonical_mixed_code_spec(rounds: int = 2):
    """A d=3 mixed X/Z memory ``CodeSpec`` so the compiler emits ALL substep kinds
    (H / CX / reset / measurement / barrier): check x0=X0 (anc3), z1=Z1 (anc4); logical
    logical_z2=Z2. Use when a batch needs a compiled schedule exercising every kind."""
    from error_coupling_simulator.frontend.code_spec import (
        CodeSpec, CodeQubit, PauliTerm, StabilizerCheck, LogicalObservableSpec)
    return CodeSpec(
        name="axis1_mixed", num_qubits=5,
        data_qubits=(CodeQubit(0, "data", (0.0,)), CodeQubit(1, "data", (1.0,)),
                     CodeQubit(2, "data", (2.0,))),
        ancilla_qubits=(CodeQubit(3, "ancilla", (0.0, 0.5)),
                        CodeQubit(4, "ancilla", (1.0, 0.5))),
        checks=(StabilizerCheck("x0", 3, (PauliTerm(0, "X"),), (0.0, 0.5)),
                StabilizerCheck("z1", 4, (PauliTerm(1, "Z"),), (1.0, 0.5))),
        logical_observables=(LogicalObservableSpec("logical_z2", (PauliTerm(2, "Z"),), index=0),),
        rounds=int(rounds))


def canonical_circuit_ir():
    """A curated 3-qubit ``CircuitIR`` exercising all six substep kinds in schedule order:
    H0 -> CX(1,2) -> TICK -> R2 -> idle(0,1 @50ns) -> MR0."""
    from error_coupling_simulator.frontend.circuit_ir import CircuitBuilder
    b = CircuitBuilder(num_qubits=3)
    b.h(0)
    b.cx((1, 2))
    b.tick()
    b.reset(2)
    b.idle((0, 1), duration_ns=50.0)
    b.measure((0,), key="m0", reset=True)
    return b.build()


def canonical_sealed_schedule(*, from_spec: bool = True):
    """A SEALED ``SubstepSchedule`` (passes ``has_valid_compiler_schedule_seal``) built via
    the code-spec compiler from :func:`canonical_mixed_code_spec` (``from_spec=True``) or via
    the circuit-IR compiler from :func:`canonical_circuit_ir` (``from_spec=False``). Use as a
    valid schedule INPUT (e.g. for the axis-1 selection / bridge units); do NOT use it as a
    reference for the compiler's OWN output (that would be circular -- keep such recomputes local)."""
    from error_coupling_simulator.frontend.analog_schedule import (
        compile_code_spec_to_substep_schedule, circuit_ir_to_substep_schedule)
    if from_spec:
        return compile_code_spec_to_substep_schedule(canonical_mixed_code_spec())
    return circuit_ir_to_substep_schedule(canonical_circuit_ir())


def canonical_stim_circuit():
    """A small valid ``stim.Circuit`` (QUBIT_COORDS + H + CX + M + a DETECTOR) for the stim
    importer / adapter units. Lazy-imports stim (not a hard dependency of this module)."""
    import stim
    c = stim.Circuit()
    c.append("QUBIT_COORDS", [0], [0.0, 0.0])
    c.append("QUBIT_COORDS", [1], [1.0, 0.0])
    c.append("H", [0])
    c.append("CX", [0, 1])
    c.append("M", [0, 1])
    c.append("DETECTOR", [stim.target_rec(-1), stim.target_rec(-2)])
    return c
