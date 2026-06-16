from __future__ import annotations

"""Window-local FAITHFUL single-round noisy circuit — the WindowChannel object.

Step-2 mainline (`docs/cf_wr/window_channel_spec.md`, LOCKED decision 1 + §3 + the §10 frozen
contract). The WindowChannel is **not** an abstract CPTP composition: it is the real circuit's
single steady-state syndrome-extraction round, restricted to one 3x3 window's data qubits + their
ancilla, with a **learnable mechanism channel inserted at the modelled noise locations** (post-1q-gate
on data, at each in-window CZ pair, and at each in-window ``(data, data)`` spectator pair), evolved
exactly in circuit gate order on the ``2**(window data + ancilla)`` density matrix. This is the
window-local toy-free model that step-3 fits to real hardware syndrome data and that the step-4 seam
composes; building it as the faithful noisy circuit (not a canonical-order abstraction) is what keeps
it debuggable and aligned with the step-3 multi-round forward by construction (decision 1;
[[feedback-no-toy-models-real-target]]).

Modelled noise locations (the 3-class LOCKED scope) vs. the known omissions
--------------------------------------------------------------------------
The implemented placement is the 3-class enumeration of ``outputs/placement_enumerate.py`` (counts
cross-checked in ``test_placement_counts_match_sidecar``): the per-data 1q coherent slot, the per-CZ
2q slot + its 2q depolarizing baseline, and the per-(data,data) spectator slot. Two SI1000 footprints
are **deliberately NOT built** in step-2 and are recorded here as known model-class limitations of the
locked scope (see ``build_placement`` for specifics):
  * the single-qubit baseline (``DEFAULT_ONEQ_BASELINE``) is a learnable single-Pauli-**X** stochastic
    channel, **not** the isotropic SI1000 ``DEPOLARIZE1`` — it cannot express Y/Z stochastic 1q noise
    (``MECH_1Q`` has no 1q-depolarizing builder; the §10 1q keys are frozen);
  * idle / measure / reset ``DEPOLARIZE1`` locations (incl. the wide idle-during-CZ layers, the
    largest 1q-noise footprint of the round) get **no** baseline slot — only the post-1q-gate data
    location carries a 1q baseline.
Closing either gap is a §3 scope amendment (LOCKED decision, commit-gated), not a free edit.

Design (against the §10 contract)
----------------------------------
* ``build_placement(round_schedule, window_data, ancilla, adjacency) -> placement`` walks the parsed
  single-round schedule in **circuit order**, restricts every operation to the window register, and
  emits an ordered build program: ideal gates (Y / H / X / CZ unitaries; reset / measure as CPTP
  ancilla ops) interleaved with learnable noise SLOTS at the modelled locations. Per the LOCKED
  granularity (§3, 3-class scope): a 1q over-rotation/dephasing slot per data qubit at each in-window
  1q gate + a single-Pauli-X stochastic baseline at that same location; a 2q coherent slot + a 2q
  depolarizing (SI1000 ``DEPOLARIZE2``) baseline per in-window CZ ``(data, measure)`` pair; a 2q
  coherent slot per in-window ``(data, data)`` adjacent spectator pair. Idle / measure / reset 1q
  baselines are out of the locked 3-class scope (see the omissions note above).
* ``WindowChannel`` builds the θ leaves from the placement, **tied per (mechanism-type, global
  support-tuple)** so overlapping windows share parameters (§5). ``apply`` evolves a state through
  the program; ``rho_bc`` reduces to an overlap region (the seam anchor); ``coherence_budget``
  reports the PTM off-diagonal mass discarded by a Pauli/DEM export; ``sensitivity`` is the autograd
  ∂apply/∂θ hook for step-3's Fisher-rank identifiability.

Disciplines: ``complex128``; **GPU-only** (§3 "GPU-only (HARD gate)") — ``device`` defaults to cuda and
there is NO cuda-if-available-else-cpu fallback (an explicit/absent CPU device raises). **Register
bound** (§3, HARD): the isolated step-2 register is window data + ``full_in_ancilla`` only (CZ support
⊆ the window data); seam ancilla are deferred to step-4, so an interior 9-data window is ≤ 13 qubits
on the real d7 covering — ``__init__`` asserts ``n ≤ MAX_WINDOW_QUBITS`` and GPU-memory headroom so the
forbidden data + ALL-touching register (~25 q) can never be instantiated and ``apply`` never OOMs.
CPTP-by-construction (mechanism Kraus + ideal-unitary conjugation + CPTP reset/measure → the composed
map is CPTP, never twirled to Pauli — coherence is the point). Evolution reuses ``apply_channel_local``
(`exact.circuit_sim`, itself built
on ``embed_operator`` / ``apply_kraus``) and ``hermitianize`` (`cptp_channel`); the mechanism Kraus
come from the §10 sibling ``mechanisms_torch`` (``MECH_1Q`` / ``MECH_2Q``); the coherence budget /
seam reduction come from ``window_diagnostics`` (``coherence_budget`` / ``partial_trace``, which use
its ``ptm``). The model body is always Kraus (no manual numeric floor here — the mechanism builders
own their ``NUMERICAL_ZERO`` floors).
"""

from dataclasses import dataclass, field
import math

import torch

from qec_twin.forward.cptp_channel import CDTYPE, hermitianize
from qec_twin.forward.exact.circuit_sim import apply_channel_local
from qec_twin.forward.mechanisms_torch import MECH_1Q, MECH_2Q
from qec_twin.forward.window_diagnostics import coherence_budget, partial_trace


# --------------------------------------------------------------------------- #
# Mechanism-class -> dictionary-key map (which faithful mechanism sits where)  #
# --------------------------------------------------------------------------- #
# The LOCKED-granularity slot classes (§3) and the mechanism each inserts. Coherent-first
# (correction 2): the differentiator is the coherent over-rotation / RZZ, not a Pauli rate. The 2q CZ
# baseline IS the faithful SI1000 DEPOLARIZE2; the 1q baseline is an X-only stochastic surrogate, NOT
# the isotropic SI1000 DEPOLARIZE1 (a known model-class limitation — see the module docstring).
DEFAULT_ONEQ_MECH = "rz"        # 1q over-rotation / dephasing slot (coherent, PTM-off-diagonal live)
DEFAULT_CZ_MECH = "rzz"         # 2q coherent slot at the real CZ (data, measure) gate
DEFAULT_SPECTATOR_MECH = "rzz"  # 2q coherent slot at a (data, data) share-a-stabilizer pair
# NOTE: this is a learnable single-Pauli-X stochastic baseline at the post-1q-gate DATA location only
# — NOT the isotropic SI1000 DEPOLARIZE1 (no Y/Z stochastic content) and NOT placed at idle / measure
# / reset locations. MECH_1Q (frozen §10 keys) has no 1q-depolarizing builder; widening this is a §3
# scope amendment (module docstring "known model-class limitations").
DEFAULT_ONEQ_BASELINE = "pauli_x"   # learnable single-Pauli-X stochastic 1q baseline (see NOTE above)
DEFAULT_CZ_BASELINE = "depol2"      # faithful SI1000 DEPOLARIZE2 baseline (learnable 2q depolarizing)

# Slot-class tags carried in the build program (printed-evidence / audit friendly).
SLOT_ONEQ = "oneq"            # per-data 1q over-rotation / dephasing
SLOT_ONEQ_BASELINE = "oneq_baseline"
SLOT_CZ = "cz"               # 2q coherent at a real CZ pair
SLOT_CZ_BASELINE = "cz_baseline"
SLOT_SPECTATOR = "spectator"  # 2q coherent at a (data, data) adjacent pair

# Register bound (§3 "Register bound (memory, HARD)"). The isolated step-2 window register is
# window data + FULL-IN ancilla only (stabilizers whose CZ support ⊆ the window data); seam ancilla
# (support reaches outside the window) are DEFERRED to step-4 and never enter the register. An interior
# 9-data window is then ≤ 13 qubits on the real d7 covering (measured: 9 data + 4 full-in;
# outputs/window_register_probe.py); the spec caps it at MAX_WINDOW_QUBITS so the full data +
# ALL-touching-ancilla register (~25 q, 4**25 ≈ 1e6 GB — infeasible anywhere) can NEVER be built.
MAX_WINDOW_QUBITS = 14        # 4**14 ≈ 4.3 GB complex128 — the GPU-feasible ceiling (§3)
# Fraction of free GPU memory the bare density matrix (4**n * 16 bytes) may claim at construction; a
# headroom guard so apply()/eigvalsh/autograd intermediates do not OOM (epistemic tag (c): a tripwire,
# not a premise). The bare ρ is ≤ ~0.07 GB at n=13, so this never bites a full-in window — it only
# fires if a caller smuggled in a forbidden oversized register on a memory-starved device.
_RHO_MEM_FRACTION = 0.25

# Ideal single-qubit / two-qubit gates that appear in the steady-state round (faithful, fixed).
# The real XZZX d7 round uses only {Y, H, X}; the rest are recognised so a basis/patch variant links.
_IDEAL_1Q = {"H", "X", "Y", "Z", "S", "S_DAG",
             "SQRT_X", "SQRT_X_DAG", "SQRT_Y", "SQRT_Y_DAG", "SQRT_Z", "SQRT_Z_DAG"}
_MEAS_NAMES = {"M", "MX", "MY", "MZ", "MR", "MRX", "MRY", "MRZ"}
_RESET_NAMES = {"R", "RX", "RY", "RZ"}


# --------------------------------------------------------------------------- #
# GPU-only device resolution + register-bound guard (§3 HARD gates)            #
# --------------------------------------------------------------------------- #
def _resolve_device(device) -> torch.device:
    """Resolve the WindowChannel compute device under the §3 GPU-only HARD gate.

    The default (``device=None``) is **cuda**, never a cuda-if-available-else-cpu fallback: all model
    compute (the forward ``apply``, CPTP / eigvalsh, gradients) runs on the GPU. If CUDA is
    unavailable we raise rather than silently falling back to CPU (running the window tests on CPU to
    dodge memory is the exact defect this build removes — the register is bounded instead; §3). An
    explicit CPU ``device`` is likewise refused: the model body has no admissible CPU path.
    """
    dev = torch.device(device) if device is not None else torch.device("cuda")
    if dev.type != "cuda":
        raise RuntimeError(
            f"WindowChannel is GPU-only (spec §3 'GPU-only (HARD gate)'); got device={dev}. "
            "All model compute must run on cuda — bound the register (full-in ancilla only, "
            "MAX_WINDOW_QUBITS) instead of retreating to CPU."
        )
    if not torch.cuda.is_available():
        raise RuntimeError(
            "WindowChannel requires CUDA (spec §3 'GPU-only (HARD gate)') but torch.cuda.is_available()"
            " is False — no CPU fallback is allowed."
        )
    return dev


def _assert_register_bound(n_qubits: int, device: torch.device) -> None:
    """Assert the register obeys the §3 memory bound and the device has headroom (never OOM).

    Two HARD checks (§3 "Register bound (memory, HARD)"):
      1. ``n_qubits <= MAX_WINDOW_QUBITS`` — the full-in register (window data + full-in ancilla) of an
         interior 9-data window is ≤ 13 on the real d7 covering; a larger ``n`` means seam ancilla
         leaked in (the forbidden data + ALL-touching-ancilla register, ~25 q / 4**25 ≈ 1e6 GB), which
         must NEVER be instantiated. We refuse here rather than letting the 4**n density matrix OOM.
      2. The bare density matrix (``4**n`` complex128 = ``4**n * 16`` bytes) fits the device's FREE
         memory with headroom (``_RHO_MEM_FRACTION``), so ``apply`` / ``eigvalsh`` / autograd
         intermediates have room. At n=13 ρ is ≈ 0.07 GB, so this never bites a full-in window — it is
         the belt-and-braces guard that an oversized register cannot OOM a memory-starved GPU.
    """
    if n_qubits > MAX_WINDOW_QUBITS:
        raise ValueError(
            f"window register n={n_qubits} exceeds the §3 bound MAX_WINDOW_QUBITS={MAX_WINDOW_QUBITS} "
            f"(4**{n_qubits} complex128 = {4.0 ** n_qubits * 16 / 1e9:.3e} GB). The isolated step-2 "
            "register is window data + FULL-IN ancilla only (support ⊆ window data); seam ancilla are "
            "deferred to step-4. Build the register with full_in_ancilla(window_data, supports) — the "
            "data + ALL-touching-ancilla register (~25 q) is forbidden, not a thing to instantiate."
        )
    rho_bytes = (4.0 ** n_qubits) * 16.0  # complex128 dense (2**n, 2**n)
    free_bytes, _total = torch.cuda.mem_get_info(device)
    if rho_bytes > _RHO_MEM_FRACTION * free_bytes:
        raise MemoryError(
            f"window register n={n_qubits}: the density matrix needs {rho_bytes / 1e9:.3f} GB but only "
            f"{free_bytes / 1e9:.3f} GB is free on {device} (headroom fraction {_RHO_MEM_FRACTION}); "
            "refusing to build to avoid an OOM (spec §3 'never OOM')."
        )


# --------------------------------------------------------------------------- #
# Placement program (the output of build_placement / the input to WindowChannel)
# --------------------------------------------------------------------------- #
@dataclass
class GateStep:
    """An ideal (noiseless) gate in the window-local round, in circuit order."""

    kind: str               # "gate1q" | "gate2q" | "reset" | "measure"
    name: str               # the circuit instruction name (H / X / Y / CZ / R / M ...)
    local_targets: tuple[int, ...]   # window-local qubit indices this gate acts on
    global_targets: tuple[int, ...]  # the global circuit qubit ids (identity / audit)


@dataclass
class SlotStep:
    """A learnable mechanism channel inserted at a real noise location, in circuit order."""

    slot_class: str         # one of the SLOT_* tags
    mech_arity: int         # 1 or 2
    mech_type: str          # a key into MECH_1Q / MECH_2Q
    local_targets: tuple[int, ...]   # window-local qubit indices
    global_support: tuple[int, ...]  # global qubit ids — the θ-tying key support (canonical, sorted)
    layer: int              # the originating round-schedule layer index (provenance)


@dataclass
class WindowPlacement:
    """The ordered build program for one window's faithful single-round noisy circuit.

    ``program`` interleaves :class:`GateStep` (ideal gates) and :class:`SlotStep` (learnable noise)
    in strict circuit order. ``local_of`` maps a global qubit id to its window-local index;
    ``n_qubits`` is the window register size (``len(window_data) + len(ancilla)``).
    """

    window_data: tuple[int, ...]
    ancilla: tuple[int, ...]
    local_of: dict[int, int]
    n_qubits: int
    program: list[object] = field(default_factory=list)        # [GateStep | SlotStep, ...]

    def slots(self) -> list[SlotStep]:
        return [s for s in self.program if isinstance(s, SlotStep)]

    def gates(self) -> list[GateStep]:
        return [s for s in self.program if isinstance(s, GateStep)]


# --------------------------------------------------------------------------- #
# Ideal-gate builders (fixed, noiseless; complex128, device-aware)             #
# --------------------------------------------------------------------------- #
def _ideal_1q(name: str, device) -> torch.Tensor:
    """The fixed ideal single-qubit gate matrix (the noiseless syndrome-extraction gate).

    The real XZZX d7 round uses only ``Y``, ``H`` and ``X`` (DD echo + basis change; see
    ``placement_enumerate_results.json``), given here as exact literals. The remaining Clifford 1q
    gates are derived from their generators via ``matrix_exp`` so any matrix is provably correct (no
    hand-transcription risk) should a sibling patch/basis introduce them.
    """
    s = 2 ** -0.5
    literal = {
        "H": [[s, s], [s, -s]],
        "X": [[0, 1], [1, 0]],
        "Y": [[0, -1j], [1j, 0]],
        "Z": [[1, 0], [0, -1]],
        "S": [[1, 0], [0, 1j]],
        "S_DAG": [[1, 0], [0, -1j]],
    }
    if name in literal:
        return torch.tensor(literal[name], dtype=CDTYPE, device=device)
    # SQRT_P = exp(-i (pi/4) P) up to global phase: U = cos(pi/4) I - i sin(pi/4) P (DAG -> +pi/4).
    half_gens = {
        "SQRT_X": ("X", -1.0), "SQRT_X_DAG": ("X", 1.0),
        "SQRT_Y": ("Y", -1.0), "SQRT_Y_DAG": ("Y", 1.0),
        "SQRT_Z": ("Z", -1.0), "SQRT_Z_DAG": ("Z", 1.0),
    }
    if name in half_gens:
        p_label, sign = half_gens[name]
        p = torch.tensor(literal[p_label], dtype=CDTYPE, device=device)
        return torch.matrix_exp(sign * 1j * (math.pi / 4.0) * p)
    raise ValueError(f"unsupported ideal 1q gate {name!r}")


def _ideal_cz(device) -> torch.Tensor:
    """The fixed ideal CZ gate (the syndrome-extraction entangling gate)."""
    return torch.diag(torch.tensor([1, 1, 1, -1], dtype=CDTYPE, device=device))


def _reset_kraus(device) -> torch.Tensor:
    """CPTP reset-to-|0> on one qubit: ``{|0><0|, |0><1|}`` (the density-matrix analogue of stim R).

    Trace-preserving (``K0^dag K0 + K1^dag K1 = I``) and completely positive — keeps ``apply`` a
    bona-fide channel so the CPTP self-check (§6.1) holds on the whole single-round map.
    """
    k0 = torch.tensor([[1, 0], [0, 0]], dtype=CDTYPE, device=device)
    k1 = torch.tensor([[0, 1], [0, 0]], dtype=CDTYPE, device=device)
    return torch.stack([k0, k1])


def _measure_dephase_kraus(device) -> torch.Tensor:
    """Non-selective Z measurement on one qubit: ``{|0><0|, |1><1|}`` (record-discarded CPTP map).

    The single-round channel is the *unconditional* map (coherence between the two measurement
    eigenspaces is destroyed, populations preserved); step-3 replaces this with the per-shot
    projector trajectory (architecture doc, "Multi-round forward"). CPTP + TP by construction.
    """
    k0 = torch.tensor([[1, 0], [0, 0]], dtype=CDTYPE, device=device)
    k1 = torch.tensor([[0, 0], [0, 1]], dtype=CDTYPE, device=device)
    return torch.stack([k0, k1])


# --------------------------------------------------------------------------- #
# build_placement — faithful placement from the parsed single-round schedule   #
# --------------------------------------------------------------------------- #
def build_placement(round_schedule, window_data, ancilla, adjacency) -> WindowPlacement:
    """Faithful window-local placement from the single-round gate schedule (§3, LOCKED granularity).

    Parameters
    ----------
    round_schedule
        The parsed single steady-state round, in circuit order: a sequence of layers
        ``{"name": str, "qubits": [global_id, ...], "pairs": [(g, g), ...] | None}`` (the
        ``outputs/placement_enumerate.py::steady_round_instructions`` structure; an optional
        ``"layer"`` index is honoured for provenance, else the enumeration order is used).
    window_data, ancilla
        Global qubit ids of the window's ≤9 data qubits and their ancilla (measure) qubits. The
        window register is ``window_data`` then ``ancilla`` (order preserved); a basis index encodes
        qubit ``q`` (local) in bit ``(i >> (n - 1 - q)) & 1`` (the ``circuit_sim`` convention).
    adjacency
        The share-a-stabilizer ``(data, data)`` edges (undirected, global ids) — the spectator-ZZ
        crosstalk graph (``outputs/placement_enumerate.py::spectator_pairs``). Only edges with both
        endpoints in ``window_data`` become in-window spectator slots.

    Returns
    -------
    WindowPlacement
        The ordered build program: ideal gates + learnable noise slots, restricted to the window, in
        strict circuit order. A 1q over-rotation/dephasing slot follows each in-window 1q gate (per
        gated data qubit) plus a single-Pauli-X stochastic 1q baseline at that same location; a 2q
        coherent slot + the SI1000 ``DEPOLARIZE2`` baseline follow each in-window CZ pair; the
        spectator-ZZ slots are appended at the round boundary (crosstalk slots, not circuit gates —
        §3, class 3 of ``placement_enumerate``).

        Scope note (3-class LOCKED): the 1q baseline is X-only (not isotropic ``DEPOLARIZE1``) and is
        placed only at the post-1q-gate data location — idle / measure / reset ``DEPOLARIZE1``
        footprints (incl. the wide idle-during-CZ layers) get NO baseline slot. These omissions are
        the locked model-class limitations recorded in the module docstring, not oversights.
    """
    window_data = tuple(int(q) for q in window_data)
    ancilla = tuple(int(q) for q in ancilla)
    register = list(window_data) + [q for q in ancilla if q not in window_data]
    local_of = {g: i for i, g in enumerate(register)}
    win_set = set(register)
    data_set = set(window_data)

    # Normalise adjacency to a set of canonical (sorted) global (data, data) pairs in-window.
    spectator_in_window: set[tuple[int, int]] = set()
    for edge in adjacency:
        a, b = int(edge[0]), int(edge[1])
        if a in data_set and b in data_set and a != b:
            spectator_in_window.add((min(a, b), max(a, b)))

    program: list[object] = []

    def _loc(g: int) -> int:
        return local_of[int(g)]

    for layer_idx, op in enumerate(round_schedule):
        name = str(op["name"])
        layer = int(op.get("layer", layer_idx)) if hasattr(op, "get") else layer_idx
        if name == "CZ":
            pairs = op.get("pairs") if hasattr(op, "get") else op["pairs"]
            pairs = pairs or []
            for (ga, gb) in pairs:
                ga, gb = int(ga), int(gb)
                if ga not in win_set or gb not in win_set:
                    continue  # cross-boundary CZ: the *other* qubit is outside this window
                lt = (_loc(ga), _loc(gb))
                gt = (ga, gb)
                support = (min(ga, gb), max(ga, gb))
                program.append(GateStep("gate2q", "CZ", lt, gt))
                program.append(SlotStep(SLOT_CZ, 2, DEFAULT_CZ_MECH, lt, support, layer))
                program.append(SlotStep(SLOT_CZ_BASELINE, 2, DEFAULT_CZ_BASELINE, lt, support, layer))
        elif name in _IDEAL_1Q:
            gated = [int(q) for q in op["qubits"] if int(q) in win_set]
            for g in gated:
                lt = (_loc(g),)
                gt = (g,)
                support = (g,)
                program.append(GateStep("gate1q", name, lt, gt))
                # The learnable 1q over-rotation/dephasing slot sits on DATA qubits (the §3 class:
                # "1q per data qubit at each 1q-gate location"); ancilla 1q noise is folded into the
                # X-only baseline below (readout is handled in the forward, not the dictionary). Idle
                # qubits in this layer get no slot — that DEPOLARIZE1 footprint is out of the locked
                # 3-class scope (module docstring "known model-class limitations").
                if g in data_set:
                    program.append(SlotStep(SLOT_ONEQ, 1, DEFAULT_ONEQ_MECH, lt, support, layer))
                program.append(
                    SlotStep(SLOT_ONEQ_BASELINE, 1, DEFAULT_ONEQ_BASELINE, lt, support, layer)
                )
        elif name in _RESET_NAMES:
            for g in (int(q) for q in op["qubits"] if int(q) in win_set):
                program.append(GateStep("reset", name, (_loc(g),), (g,)))
        elif name in _MEAS_NAMES:
            for g in (int(q) for q in op["qubits"] if int(q) in win_set):
                program.append(GateStep("measure", name, (_loc(g),), (g,)))
        # any other annotation-like op restricted to the window is a no-op here.

    # Class (3): (data, data) spectator-ZZ crosstalk slots — not circuit CZ gates, so they are not
    # tied to a gate layer; appended once per in-window adjacent pair at the round boundary.
    for (ga, gb) in sorted(spectator_in_window):
        lt = (_loc(ga), _loc(gb))
        support = (ga, gb)
        program.append(SlotStep(SLOT_SPECTATOR, 2, DEFAULT_SPECTATOR_MECH, lt, support, -1))

    return WindowPlacement(
        window_data=window_data,
        ancilla=ancilla,
        local_of=local_of,
        n_qubits=len(register),
        program=program,
    )


# --------------------------------------------------------------------------- #
# Full-in ancilla selection (the §3 register bound)                            #
# --------------------------------------------------------------------------- #
def full_in_ancilla(window_data, supports) -> list[int]:
    """The window's FULL-IN ancilla: measure qubits whose CZ support ⊆ the window data (§3).

    The isolated step-2 register bound (``docs/cf_wr/window_channel_spec.md`` §3 "Register bound"):
    only stabilizers *contained* in the window enter the register. A measure qubit ``m`` is full-in
    iff its (nonempty) CZ data-support ``supports[m]`` is a subset of ``window_data``; a measure qubit
    whose support intersects the window but also reaches OUTSIDE it is a SEAM ancilla, deferred to the
    step-4 seam composition and excluded here (including it would pull in out-of-window data and blow
    the register up to the forbidden data + ALL-touching size — ~25 q on the real d7 covering).

    Parameters
    ----------
    window_data
        Global ids of the window's ≤9 data qubits.
    supports
        ``{measure_global_id: set(data_global_id, ...)}`` — each measure qubit's CZ data-support
        (``outputs/placement_enumerate.py::supports_from_cz`` / the parsed-round ``supp`` map).

    Returns
    -------
    list[int]
        The full-in measure-qubit ids, sorted. Building the register as ``window_data + this`` keeps
        an interior 9-data window at ≤ :data:`MAX_WINDOW_QUBITS` qubits (measured 13 on the real d7
        covering; ``outputs/window_register_probe.py``) — GPU-feasible.
    """
    wd = {int(q) for q in window_data}
    out: list[int] = []
    for m, s in supports.items():
        sup = {int(q) for q in s}
        if sup and sup <= wd:
            out.append(int(m))
    return sorted(out)


# --------------------------------------------------------------------------- #
# WindowChannel — the faithful single-round noisy-circuit map                  #
# --------------------------------------------------------------------------- #
class WindowChannel:
    """The window-local FAITHFUL single-round noisy circuit (§3 / §10).

    Builds learnable θ leaves from ``placement`` (faithful, **tied per (mechanism-type, global
    support-tuple)** so overlapping windows share parameters — §5). ``apply`` evolves a window
    density matrix through the ideal gates + learnable mechanism channels in strict circuit order
    (Kraus composition); the model body is always Kraus/Stinespring (complex128), never twirled to
    Pauli (coherence is the point — §4/§6).
    """

    def __init__(self, window_data, ancilla, round_schedule, placement, *, device=None):
        """Build the window channel.

        ``placement`` MUST be a :class:`WindowPlacement` (from :func:`build_placement`); any other
        type raises ``TypeError``. The canonical path is to build the placement once and share it
        across overlapping windows (the integrator does this), so the placement is always prebuilt.

        ``device`` defaults to **cuda** (§3 "GPU-only (HARD gate)" — all model compute runs on the
        GPU; there is NO cuda-if-available-else-cpu fallback). At construction the register is asserted
        ≤ :data:`MAX_WINDOW_QUBITS` qubits (the §3 register bound — window data + full-in ancilla only;
        the forbidden data + ALL-touching-ancilla register can never be built) and to have GPU-memory
        headroom for the density matrix, so ``apply`` / ``eigvalsh`` / autograd never OOM.
        """
        self.device = _resolve_device(device)
        self.window_data = tuple(int(q) for q in window_data)
        self.ancilla = tuple(int(q) for q in ancilla)
        self.round_schedule = round_schedule
        if not isinstance(placement, WindowPlacement):
            raise TypeError(
                "WindowChannel requires a WindowPlacement (build it with build_placement); "
                f"got {type(placement)!r}"
            )
        self.placement = placement
        self.n_qubits = placement.n_qubits

        # Register bound (§3, HARD). The full-in register must stay ≤ MAX_WINDOW_QUBITS; a larger n
        # means seam ancilla leaked in (the forbidden data + ALL-touching register) — refuse to build
        # the infeasible density matrix rather than OOM. Then verify the bare ρ (4**n * 16 bytes) fits
        # the device's free memory with headroom (a GPU tripwire; CPU device-resolution is already
        # blocked above).
        _assert_register_bound(self.n_qubits, self.device)

        # θ leaves, tied per (mech_type, global support-tuple). One real scalar leaf per tie key;
        # coherent builders read it as the rotation angle, non-unitary builders as sigmoid(theta).
        self._theta: dict[tuple[str, tuple[int, ...]], torch.Tensor] = {}
        self._slot_keys: list[tuple[str, tuple[int, ...]]] = []  # parallel to placement.slots()
        for slot in placement.slots():
            key = (slot.mech_type, slot.global_support)
            if key not in self._theta:
                leaf = torch.zeros((), dtype=torch.float64, device=self.device, requires_grad=True)
                self._theta[key] = leaf
            self._slot_keys.append(key)

        # A stable, de-duplicated parameter order for parameters() / sensitivity(index).
        self._param_keys: list[tuple[str, tuple[int, ...]]] = list(self._theta.keys())

    # ----- helpers -------------------------------------------------------- #
    def _builder(self, slot: SlotStep):
        if slot.mech_arity == 1:
            if slot.mech_type not in MECH_1Q:
                raise KeyError(f"unknown 1q mechanism {slot.mech_type!r} (MECH_1Q keys: {sorted(MECH_1Q)})")
            return MECH_1Q[slot.mech_type]
        if slot.mech_type not in MECH_2Q:
            raise KeyError(f"unknown 2q mechanism {slot.mech_type!r} (MECH_2Q keys: {sorted(MECH_2Q)})")
        return MECH_2Q[slot.mech_type]

    def _step_kraus(self, gate: GateStep) -> torch.Tensor:
        """The fixed Kraus stack for an ideal gate / reset / measure step (complex128, device)."""
        if gate.kind == "gate1q":
            u = _ideal_1q(gate.name, self.device)
            return u.unsqueeze(0)
        if gate.kind == "gate2q":
            return _ideal_cz(self.device).unsqueeze(0)
        if gate.kind == "reset":
            return _reset_kraus(self.device)
        if gate.kind == "measure":
            return _measure_dephase_kraus(self.device)
        raise ValueError(f"unknown gate kind {gate.kind!r}")

    # ----- the single-round map ------------------------------------------- #
    def apply(self, rho: torch.Tensor, *, theta_override=None) -> torch.Tensor:
        """Single-round window map: Kraus composition of ideal gates + mechanism channels in order.

        ``rho`` is ``(2**n, 2**n)`` complex128 on ``self.device`` (n = window register size). Each
        ideal gate is a single-Kraus channel (unitary conjugation); each noise slot's Kraus is built
        from its tied θ leaf and applied with :func:`apply_channel_local`. The result is the exact,
        differentiable single-round density-matrix map (CPTP by construction).

        ``theta_override`` (internal) maps a θ-tie key to a substitute scalar tensor used in place of
        the stored leaf — :meth:`sensitivity` uses it to differentiate the map w.r.t. one θ without
        mutating the leaves.
        """
        if rho.device != self.device:
            rho = rho.to(self.device)
        if rho.dtype != CDTYPE:
            rho = rho.to(CDTYPE)
        n = self.n_qubits
        slot_i = 0
        for step in self.placement.program:
            if isinstance(step, GateStep):
                kraus = self._step_kraus(step)
                rho = apply_channel_local(rho, kraus, list(step.local_targets), n)
            else:  # SlotStep
                key = self._slot_keys[slot_i]
                slot_i += 1
                theta = self._theta[key]
                if theta_override is not None and key in theta_override:
                    theta = theta_override[key]
                kraus = self._builder(step)(theta, device=self.device)
                rho = apply_channel_local(rho, kraus, list(step.local_targets), n)
        return hermitianize(rho)

    def rho_bc(self, rho: torch.Tensor, overlap_data: list[int]) -> torch.Tensor:
        """Reduced window state on an overlap region (the seam anchor ρ_BC, step-4).

        Evolves ``rho`` through the single round, then partial-traces to ``overlap_data`` (global
        qubit ids that must be a subset of this window's register), order preserved. Delegates the
        trace to ``window_diagnostics.partial_trace`` (the §10 helper).
        """
        evolved = self.apply(rho)
        keep_local = []
        for g in overlap_data:
            g = int(g)
            if g not in self.placement.local_of:
                raise KeyError(f"overlap qubit {g} is not in this window's register {sorted(self.placement.local_of)}")
            keep_local.append(self.placement.local_of[g])
        return partial_trace(evolved, keep_local, self.n_qubits)

    def coherence_budget(self) -> dict:
        """Per-mechanism + total PTM off-diagonal mass — what a Pauli/DEM export discards (§4).

        For each θ-tie key the slot's mechanism Kraus is built at the current θ and scored with
        ``window_diagnostics.coherence_budget`` (Frobenius mass of the PTM off-diagonal). The model
        is NEVER diagonal-truncated (that is the forbidden Pauli twirl); this only measures the
        coherent content as a band-tracked, reportable result. Returns
        ``{"per_mechanism": {key_str: mass}, "total": float}``.
        """
        # One representative slot per tie key (the Kraus depends only on (type, θ), not on support).
        rep: dict[tuple[str, tuple[int, ...]], SlotStep] = {}
        for slot, key in zip(self.placement.slots(), self._slot_keys):
            rep.setdefault(key, slot)
        per: dict[str, float] = {}
        total = 0.0
        for key, slot in rep.items():
            theta = self._theta[key]
            kraus = self._builder(slot)(theta, device=self.device)
            mass = float(coherence_budget(kraus, slot.mech_arity))
            label = f"{key[0]}@{','.join(str(q) for q in key[1])}"
            per[label] = mass
            total += mass
        return {"per_mechanism": per, "total": float(total)}

    def parameters(self) -> list[torch.Tensor]:
        """The θ leaves (de-duplicated, stable order) — for the step-3 fit (§5)."""
        return [self._theta[k] for k in self._param_keys]

    def sensitivity(self, rho: torch.Tensor, index: int) -> torch.Tensor:
        """∂apply/∂θ_index — the per-mechanism sensitivity hook (interface only; step-3 Fisher rank).

        Returns the elementwise derivative of the single-round output ``apply(rho)`` w.r.t. the
        ``index``-th θ (the ``parameters()`` order) as a complex128 tensor **shaped like the output**
        (``(2**n, 2**n)``). Because each θ is a real scalar leaf, this Jacobian is exactly the
        directional derivative of the output along that θ; it is computed by differentiating a fresh
        forward that substitutes a leaf-cloned scalar for that θ (so the stored leaves are
        untouched). Step-2 provides the interface; it does not fit (§5).
        """
        if index < 0 or index >= len(self._param_keys):
            raise IndexError(f"sensitivity index {index} out of range [0, {len(self._param_keys)})")
        key = self._param_keys[index]
        if rho.device != self.device:
            rho = rho.to(self.device)
        if rho.dtype != CDTYPE:
            rho = rho.to(CDTYPE)
        base = float(self._theta[key].detach())

        def _forward(scalar: torch.Tensor) -> torch.Tensor:
            out = self.apply(rho, theta_override={key: scalar})
            # Stack real/imag into a real-valued tensor so autograd.functional.jacobian (which
            # requires real outputs) returns ∂Re/∂θ and ∂Im/∂θ; recombined below into the complex
            # ∂(output)/∂θ, shaped like the output. θ is real, so this is the exact derivative.
            return torch.stack([out.real, out.imag])

        scalar = torch.tensor(base, dtype=torch.float64, device=self.device)
        jac = torch.autograd.functional.jacobian(_forward, scalar, vectorize=False)
        # jac shape: (2, 2**n, 2**n) — [0] = ∂Re/∂θ, [1] = ∂Im/∂θ.
        return (jac[0] + 1j * jac[1]).to(CDTYPE)
