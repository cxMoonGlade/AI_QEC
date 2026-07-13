from __future__ import annotations

"""P4a state-vector Monte-Carlo (MCWF) leakage-teacher HOST driver (Agent H).

The host side of the P4a engine (design ``docs/nonpauli_teacher/p4_sv_mc_engine_design.md``;
interface contract ``docs/nonpauli_teacher/p4a_build_contract.md``). It marshals the
static d3 XZZX schedule + the Wood-Gambetta leakage Kraus + the measurement-instrument
arm into the FIXED flat arrays the trajectory kernel consumes (§2/§3/§7), prepares the
pure logical codestate ``|m>_L`` with the ⟨S⟩/⟨L⟩ self-check (§8), drives the kernel
wave-by-wave (§7), and streams the packed self-describing shot buffer to disk (§6).

Ownership (contract §0): Agent H owns this module + the ``qutrit_dm.py`` arm additions.
The trajectory CUDA kernel ``sv_traj_d3`` + its loader are Agent K's (``forward/kernels/
sv_traj_d3_loader.py``); the §6/§9 correctness harness + Gates 4/5 are Agent V's. H calls
the kernel only through K's loader, coded to the §7 signature; the kernel import is LAZY +
GUARDED so this module imports cleanly (and the codestate/marshalling are unit-testable)
before K lands the ``.cu``/loader on disk.

GPU-only compute (binding): the codestate SV + every trajectory live on ``cuda``; only the
disk streaming is host-side (allowed, §6). complex128 default (§1); complex64 is a Gate-5/P-D
decision, not defaulted here.

Scripted-execution (binding): this module is a LIBRARY; every run is a committed script under
``outputs/teacher_prereg/p4a_host_*.py`` with precondition asserts + printed evidence + flushed
stdout + an ``if __name__ == "__main__"`` guard.

Registered sweeps, not pinned (§3): ``(theta, g_seep, g_heat)`` and ``b`` are taken per-run
from the registered grids (``qutrit_teachers.THETA_SWEEP`` / ``G_SEEP_SWEEP`` / ``G_HEAT_SWEEP``
/ ``LEAKED_READOUT_BIAS_SWEEP``); no headline point is hard-coded.
"""

import json
import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import torch

from qec_twin.forward.channels import (
    _lindbladian_super,
    _qutrit_op,
    _super_to_kraus,
    leakage_kraus,
)
from qec_twin.forward.exact.qutrit_dm import (
    QUDIT,
    QutritDM,
    qutrit_eye,
    qutrit_hadamard,
)
from qec_twin.forward.exact.xzzx_parser import (
    WithinCycleStream,
    XZZXSchedule,
    parse_xzzx_circuit,
)
from qec_twin.mechanisms.qutrit_teachers import leakage_kraus_torch
from qec_twin.numerics import NUMERICAL_ZERO

CDTYPE = torch.complex128
RDTYPE = torch.float64

#: CPTP residual tolerance for the marshalled leakage Kraus (§3, ``< 1e-12``).
CPTP_TOL = 1e-12
#: Codestate ⟨S⟩=+1 / ⟨L⟩=(−1)^m tolerance (§8, ``< 1e-10``).
CODESTATE_TOL = 1e-10
#: P4a within-cycle leak-slice composition tolerance (model §3): the four ``exp(L/4)`` per-CZ
#: slices must compose to the registered full-cycle channel, ``‖exp(L) − (exp(L/4))⁴‖ < 1e-12``.
WC_LEAK_COMPOSE_TOL = 1e-12
#: P4a within-cycle fractional leak rate: the per-CZ-layer slice is ``exp(L · WC_LEAK_FRAC)``
#: (a FIXED per-CZ rate; 4 layers/round, so ``1/4``). ``global_per_cz`` convention (model §3).
WC_LEAK_FRAC = 0.25

#: Shared single-qutrit gate-id enumeration (interface contract §2: the ``SV_GATE_IDS``
#: header shared by K+H). The host marshals the gate CSR (``gate_uid``) + ``gate_unitaries``
#: keyed by this map; the KERNEL (Agent K) MUST consume the identical mapping. ``I`` is id 0 so an
#: absent/identity gate marshals to 0. The d3 XZZX schedule's data-side single-qutrit alphabet is
#: H (the X-support Z-rotation, carried inside the measurement) PLUS the per-round transversal DD
#: echo it injects into the leakage CSR: ``X`` (mid-cycle) and ``Y`` (post-M) — both |0><->|1>
#: with ``|2>`` inert (FIX-1; see marshal_schedule). ``S``/``S_DAG`` are reserved so the table is
#: stable if the schedule grows. CZ is NOT here: in P4a it is compiled into the stabilizer parity
#: (§2), never an explicit 2-qutrit data gate.
SV_GATE_IDS: dict[str, int] = {"I": 0, "H": 1, "X": 2, "Y": 3, "S": 4, "S_DAG": 5}
SV_GATE_NAMES: tuple[str, ...] = tuple(k for k, _ in sorted(SV_GATE_IDS.items(), key=lambda kv: kv[1]))

#: Measurement-instrument arms (§4). Arm A is the default representative.
SV_ARMS: tuple[str, ...] = ("A", "C", "B1", "B2")
#: Terminal-readout convention (§4 "Terminal readout"): biased-``b`` leaked readout vs 50/50.
SV_READOUT_CONVENTIONS: tuple[str, ...] = ("biased_b", "half")


# --------------------------------------------------------------------------- #
# Single-qutrit gate unitaries (the SV_GATE_IDS table, as (3,3) complex)       #
# --------------------------------------------------------------------------- #
def _qutrit_x(device) -> torch.Tensor:
    """``X`` on the computational ``{|0>,|1>}`` subspace; ``|2>`` inert (leaked)."""
    m = torch.zeros((QUDIT, QUDIT), dtype=CDTYPE, device=device)
    m[0, 1] = 1.0
    m[1, 0] = 1.0
    m[2, 2] = 1.0
    return m


def _qutrit_y(device) -> torch.Tensor:
    """``Y`` on the computational ``{|0>,|1>}`` subspace; ``|2>`` inert."""
    m = torch.zeros((QUDIT, QUDIT), dtype=CDTYPE, device=device)
    m[0, 1] = -1.0j
    m[1, 0] = 1.0j
    m[2, 2] = 1.0
    return m


def _qutrit_s(device) -> torch.Tensor:
    """``S`` (phase) on the computational ``{|0>,|1>}`` subspace; ``|2>`` inert."""
    m = torch.zeros((QUDIT, QUDIT), dtype=CDTYPE, device=device)
    m[0, 0] = 1.0
    m[1, 1] = 1.0j
    m[2, 2] = 1.0
    return m


def _qutrit_s_dag(device) -> torch.Tensor:
    m = torch.zeros((QUDIT, QUDIT), dtype=CDTYPE, device=device)
    m[0, 0] = 1.0
    m[1, 1] = -1.0j
    m[2, 2] = 1.0
    return m


def gate_unitary(name: str, device) -> torch.Tensor:
    """The ``(3,3)`` complex unitary for a ``SV_GATE_IDS`` gate name (qutrit, ``|2>`` inert)."""
    name = str(name).upper()
    if name == "I":
        return qutrit_eye(device)
    if name == "H":
        return qutrit_hadamard(device)
    if name == "X":
        return _qutrit_x(device)
    if name == "Y":
        return _qutrit_y(device)
    if name == "S":
        return _qutrit_s(device)
    if name == "S_DAG":
        return _qutrit_s_dag(device)
    raise ValueError(f"unsupported gate {name!r} (known: {SV_GATE_NAMES})")


def gate_unitaries_table(device, dtype=CDTYPE) -> torch.Tensor:
    """The ``(n_gates, 3, 3)`` stack of gate unitaries, indexed by ``SV_GATE_IDS`` (§2).

    Row ``g`` is ``gate_unitary(SV_GATE_NAMES[g])`` — so ``table[gate_id]`` is the matrix
    the kernel applies for that ``gate_id``. CZ is excluded (compiled into the stabilizer
    parity in P4a). The kernel consumes this as the ``gate_unitaries`` argument (§7).
    """
    rows = [gate_unitary(name, device) for name in SV_GATE_NAMES]
    return torch.stack(rows).to(dtype=dtype, device=device).contiguous()


# --------------------------------------------------------------------------- #
# P4a within-cycle leak-slice Kraus (the per-CZ exp(L*frac) slice, model §3)    #
# --------------------------------------------------------------------------- #
def leak_slice_kraus_torch(
    theta: float, g_seep: float, g_heat: float = 0.0, *, frac: float = WC_LEAK_FRAC,
    device: str | torch.device = "cuda", dtype: torch.dtype = CDTYPE,
) -> list[torch.Tensor]:
    """The per-CZ-layer leak slice ``exp(L · frac)`` as engine-native torch CUDA Kraus (model §3).

    A FRACTIONAL-time slice of the WG Lindbladian channel (the SAME ``L`` as
    ``forward.channels.leakage_kraus``): ``H = theta(|1><2| + |2><1|)``, jump
    ``J_seep = √g_seep |1><2|`` (and optional ``J_heat = √g_heat |2><1|``). With ``frac = 1/4``
    (``WC_LEAK_FRAC``) the four per-CZ slices compose to the registered full-cycle channel
    (``‖exp(L) − (exp(L/4))⁴‖ < 1e-12`` — asserted by :meth:`SvSampler.build_within_cycle_leak`).

    Single source of truth for the algebra is ``channels._lindbladian_super`` + ``_super_to_kraus``
    (the same algebra ``leakage_kraus`` uses at ``frac = 1``); this only lifts the carrier
    (numpy → torch CUDA), mirroring ``mechanisms.qutrit_teachers.leakage_kraus_torch``. No
    re-derivation. Returns the rank-many ``(3,3)`` Kraus on ``device``.
    """
    import scipy.linalg as sla  # local: the WG-channel path is the only scipy user

    ham = float(theta) * (_qutrit_op(1, 2) + _qutrit_op(2, 1))
    jumps = []
    if float(g_seep) > 0.0:
        jumps.append(math.sqrt(float(g_seep)) * _qutrit_op(1, 2))
    if float(g_heat) > 0.0:
        jumps.append(math.sqrt(float(g_heat)) * _qutrit_op(2, 1))
    superop = sla.expm(_lindbladian_super(ham, jumps) * float(frac))
    return [torch.as_tensor(k, dtype=dtype, device=device) for k in _super_to_kraus(superop)]


# --------------------------------------------------------------------------- #
# Run spec + outputs                                                          #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RunSpec:
    """One P4a sampling run (the ``SvSampler.sample`` input).

    All physics knobs are REGISTERED SWEEPS (§3), passed in per run — never defaulted to a
    headline point. The circuit is the shipped d3 XZZX ``circuit_ideal.stim`` (use the r01
    instance for R=1; multi-round instances for R>1). ``W`` is the wave size (≤ blocks per
    wave) from the Gate-5 micro-bench; ``N`` shots are produced in ceil(N/W) waves.
    """

    circuit_path: str | Path
    metadata_path: str | Path | None = None
    sweep_word: dict[int, int] | None = None
    # logical input m ∈ {0,1} (the prepared codestate; the emitted label is the SAMPLED
    # terminal-readout flip relative to m, §4 — never m itself).
    m: int = 0
    # leakage channel (registered sweep, §3)
    theta: float = 0.0
    g_seep: float = 0.0
    g_heat: float = 0.0
    # instrument (§4)
    arm: str = "A"
    b: float = 1.0
    readout_conv: str = "biased_b"
    # sampling / RNG (§5)
    N: int = 1000
    base_seed: int = 0
    W: int = 1024  # wave size (blocks per wave); Gate-5 micro-bench pins it
    # number of QEC rounds R; default None ⇒ take it from the parsed schedule.
    R: int | None = None
    # precision (§1; complex64 is a Gate-5/P-D decision, not defaulted on)
    dtype: str = "c128"
    # output (the packed shot buffer + the §6 header are written alongside)
    out_path: str | Path | None = None
    # Optional value-level provenance supplied by a registered experiment facade.
    # It is copied verbatim into the emitted shot header. Absence means the run is
    # implementation-only; it must never be inferred to be device-calibrated.
    numerical_provenance: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if int(self.m) not in (0, 1):
            raise ValueError(f"logical m must be 0 or 1 (got {self.m})")
        if str(self.arm).upper() not in SV_ARMS:
            raise ValueError(f"arm must be one of {SV_ARMS} (got {self.arm!r})")
        if str(self.readout_conv) not in SV_READOUT_CONVENTIONS:
            raise ValueError(f"readout_conv must be one of {SV_READOUT_CONVENTIONS} (got {self.readout_conv!r})")
        if str(self.dtype) not in ("c128", "c64"):
            raise ValueError(f"dtype must be 'c128' or 'c64' (got {self.dtype!r})")
        if not 0.0 <= float(self.b) <= 1.0:
            raise ValueError(f"readout bias b must be in [0,1] (got {self.b})")
        if int(self.N) < 1 or int(self.W) < 1:
            raise ValueError("N and W must be >= 1")
        if self.numerical_provenance is not None:
            try:
                json.dumps(self.numerical_provenance, sort_keys=True)
            except (TypeError, ValueError) as exc:
                raise ValueError("numerical_provenance must be JSON-safe") from exc


#: Arm name → kernel int code (§4; Agent K's loader: 0:A, 1:C, 2:B1, 3:B2).
SV_ARM_CODE: dict[str, int] = {"A": 0, "C": 1, "B1": 2, "B2": 3}
#: Terminal-readout convention name → kernel int code (Agent K's loader: 0:biased_b, 1:half).
SV_READOUT_CODE: dict[str, int] = {"biased_b": 0, "half": 1}

#: P4a WITHIN-CYCLE op kinds (the per-qutrit gate+leak CSR, the §2/§3 circuit-faithful model).
#: An op is either a single-qutrit GATE (apply ``gate_unitaries[op_uid]`` on ``op_site``) or a
#: LEAK sub-step (apply the ``exp(L/4)`` leakage Kraus channel on ``op_site`` — one per CZ layer
#: the qutrit touches). Agent K's within-cycle kernel consumes ``op_kind`` to branch.
WC_OP_GATE: int = 0
WC_OP_LEAK: int = 1


@dataclass(frozen=True)
class MarshalledSchedule:
    """The FIXED flat CUDA arrays the kernel consumes (interface contract §2/§7).

    Marshalled ONCE per run from an :class:`XZZXSchedule` (the d3 circuit is static). The
    field shapes/dtypes/semantics are exactly Agent K's ``sv_traj_d3`` loader signature
    (``forward/kernels/sv_traj_d3_loader.py``) — H owns the marshalling, K owns the kernel,
    and these arrays are the agreed boundary (§7). All tensors live on ``device`` (int32 for
    the index arrays; complex for the unitaries).

    Gates use the CSR layout K pins: ``round_gptr[R+1]`` offsets into the flat
    ``(gate_uid, gate_site)`` per-apply arrays; round ``r``'s applies are
    ``[round_gptr[r], round_gptr[r+1])``. Stabilizers are ``stab_supp[n_stab, K]`` +
    ``stab_supp_isx`` (1 on X-type support sites → Hadamard-rotated to Z by the kernel) +
    ``stab_supp_len``. The logical is ``log_supp`` + ``log_supp_isx``.
    """

    n_data: int
    n_stab: int
    R: int
    # gates (CSR; K's format). round_gptr int32 [R+1]; gate_uid/gate_site int32 [G].
    round_gptr: torch.Tensor           # int32 [R+1] CSR offsets into the per-apply arrays
    gate_uid: torch.Tensor             # int32 [G] unitary index into gate_unitaries
    gate_site: torch.Tensor            # int32 [G] data-qutrit site
    # stabilizers (K's format): support + per-site X-flag + length, padded to K=w_max.
    stab_supp: torch.Tensor            # int32 [n_stab, w_max]: data-qutrit indices (0 pad)
    stab_supp_isx: torch.Tensor        # int32 [n_stab, w_max]: 1 on X-type sites (0 pad)
    stab_supp_len: torch.Tensor        # int32 [n_stab]: support size
    # logical observable
    log_supp: torch.Tensor             # int32 [L]: logical support sites
    log_supp_isx: torch.Tensor         # int32 [L]: 1 on X-type logical sites
    logical_kind: int                  # 0=X, 1=Z (provenance; redundant with log_supp_isx)
    # gate unitaries, indexed by SV_GATE_IDS (§2)
    gate_unitaries: torch.Tensor       # [n_gates, 3, 3] complex (device)
    # provenance
    w_max: int = 0
    gate_names: tuple[str, ...] = SV_GATE_NAMES
    # the per-round transversal X-echo + post-M Y supports (the FIX-1 leakage frame; () if none
    # parsed). BOTH are marshalled into the gate CSR as the PRE-leakage gates of rounds 1..R-1
    # (the following-slot placement; Y AFTER X — see marshal_schedule). Recorded for provenance +
    # the DM-oracle parity. The X;Y pair = diag(i,-i,1) is the DD echo that refocuses the |1><->|2>
    # leakage exchange (Y was previously DROPPED on a wrong detector-frame argument, over-stating
    # the R>1 leaked population ~10x).
    x_echo_sites: tuple[int, ...] = ()
    y_frame_sites: tuple[int, ...] = ()


@dataclass(frozen=True)
class WithinCycleMarshalled:
    """The FIXED flat CUDA arrays for the P4a circuit-faithful WITHIN-CYCLE leakage model.

    The within-cycle replacement for :class:`MarshalledSchedule` (the LUMPED per-round model).
    Where the lumped model applied ``[gates → ONE exp(L) leak per qutrit → measure]`` per round
    (over-stating the leaked ``|2>`` ~15x at R=3 / up to ~149x for the no-Y engine — model §6),
    the within-cycle model interleaves the leakage with the per-qutrit H/X gates at their REAL
    circuit positions: per round, per qutrit, the ordered stream ``[H?] LEAK [H?] LEAK X LEAK
    [H?] LEAK M Y`` with a ``exp(L/4)`` leak slice at EACH CZ layer the qutrit touches (so a
    2-CZ qutrit leaks ``exp(L·2/4)`` total — genuinely less). The mid-cycle X echo + the
    per-qutrit H pattern (``H X H = Z``) REFOCUS the coherent ``|1><->|2>`` exchange (model §4).

    PER-QUTRIT GATE+LEAK CSR FORMAT (H DEFINES this; Agent K's within-cycle kernel CONSUMES it).
    -----------------------------------------------------------------------------------------
    Per round ``r`` the round is split into TWO op segments — the PRE-measurement ops and the
    POST-measurement ops — with the 8-stabilizer measurement (a PURE diagonal Z-parity; see
    ``stab_supp_isx`` below) applied BETWEEN them:

        round r:  [pre-ops in order]  →  measure all stabilizers  →  [post-ops in order]

    The CSR row-pointer ``round_op_ptr[2R+1]`` has TWO entries per round: round ``r``'s
    pre-segment is the op range ``[round_op_ptr[2r], round_op_ptr[2r+1])`` and its post-segment
    is ``[round_op_ptr[2r+1], round_op_ptr[2r+2])``. Each op ``t`` is the triple
    ``(op_kind[t], op_uid[t], op_site[t])``:

      * ``op_kind[t] == WC_OP_GATE (0)``: apply the single-qutrit unitary
        ``gate_unitaries[op_uid[t]]`` (the ``SV_GATE_IDS`` table — H/X/Y) on data qutrit
        ``op_site[t]`` (the strided subsystem apply, ``|2>`` inert).
      * ``op_kind[t] == WC_OP_LEAK (1)``: Kraus-SAMPLE the ``exp(L/4)`` leakage channel
        (``leak_kraus`` below) on data qutrit ``op_site[t]`` (``op_uid[t]`` is 0, unused). One
        LEAK op == one CZ layer the qutrit participates in.

    The ops are serialized PER QUTRIT in engine-position order (q0's tokens, then q1's, …)
    within each segment; because single-qutrit ops on DISTINCT qutrits commute, this serial
    order is identical to the true global interleaving (only the per-qutrit internal order is
    load-bearing). The POST-measurement segment carries the transversal ``Y`` (one GATE op per
    data qutrit), and is EMPTY for the TERMINAL round (it drops the post-M Y — model §1/§8).

    LEAKAGE CALIBRATION (model §3). ``leak_kraus`` is the per-CZ-layer slice ``exp(L/4)`` (NOT
    the full-cycle ``exp(L)``): four slices compose to the registered per-round channel,
    ``‖exp(L) − (exp(L/4))⁴‖ < 1e-12`` (asserted host-side, ``WC_LEAK_COMPOSE_TOL``). A qutrit
    in ``n_cz`` CZ layers receives ``exp(L·n_cz/4)`` (genuinely less leakage — it sees fewer CZ
    gates; the fixed per-CZ rate is physical since ``DEPOLARIZE2`` sits on each CZ).

    MEASUREMENT (the CORRECTED reconciliation — see the IMPORTANT note below). ``stab_supp_isx``
    carries the REAL per-support X-flag (X-type support sites ⇒ Hadamard-rotate to Z for the
    diagonal measurement, then back), EXACTLY as in :class:`MarshalledSchedule`. The within-cycle
    H's in the gate stream are KEPT (they refocus the ``|2>`` leak — load-bearing for the §5
    ``|2>(R)`` trajectory), but they NET TO IDENTITY per qutrit per round (exactly 2 H's, even),
    so at the M the data is back in the COMPUTATIONAL basis — they do NOT leave the X-supports
    Z-rotated, hence ``stab_supp_isx`` is STILL needed for the X-stabilizer measurement. The
    ``b``-POVM + arms A/C/B1/B2 are unchanged.

    .. important::
       **Corrected vs the model-§4-R3 spec text.** The spec text (``p4a_within_cycle_model.md``
       §4 R3) states ``stab_supp_isx`` should be dropped (pure diagonal Z), arguing the explicit
       H's leave the X-supports Z-rotated at the M. That is INCONSISTENT with §4 R1 (each qutrit
       has exactly 2 H's per round → EVEN → net identity on ``{0,1}`` → the qutrit returns to the
       computational basis at the M). Verified directly on the d3 codestate (GPU,
       ``p4a_host_wc_marshal.py`` §3): with ``stab_supp_isx`` DROPPED (pure-Z) the X-type
       stabilizers read ``<Z-parity> = 0`` (the codestate is NOT a Z-parity eigenstate on an
       X-support) → the syndrome is wrong; with ``stab_supp_isx`` KEPT, every stabilizer reads
       ``<S> = +1`` (trivial syndrome). There is no "double-H" because the in-stream H's net to
       identity — they leave the computational basis at M, and ``stab_supp_isx`` then performs the
       single X-support rotation for the measurement. The ``|2>`` trajectory (§5/§6) is unaffected
       by this choice (the §5 derivation has no measurement; the measurement only sets the
       SYNDROME, applied AFTER the leak dynamics). This implementation uses the verified-correct
       behavior; the spec text's R3 conclusion is a derivation slip (R1 ⊥ R3).

    Stabilizer support (``stab_supp`` / ``stab_supp_len``), the logical (``log_supp`` /
    ``log_supp_isx`` — the logical readout keeps its OWN X-rotation; it is the terminal data
    readout, not a within-cycle stabilizer), the leak Kraus, and the gate unitaries are
    otherwise as in :class:`MarshalledSchedule`. All index arrays are int32 on ``device``.
    """

    n_data: int
    n_stab: int
    R: int
    # per-qutrit gate+leak CSR (H's FORMAT; K consumes). 2 segments/round (pre|post measure).
    round_op_ptr: torch.Tensor         # int32 [2R+1] CSR offsets; round r: pre=[2r,2r+1) post=[2r+1,2r+2)
    op_kind: torch.Tensor              # int32 [T]  WC_OP_GATE (0) | WC_OP_LEAK (1)
    op_uid: torch.Tensor               # int32 [T]  gate-unitary index (GATE ops; 0 for LEAK)
    op_site: torch.Tensor              # int32 [T]  data-qutrit site
    # stabilizers: support + per-site X-flag (REAL X-flag — the in-stream H's net to identity, so
    # the X-support rotation is STILL needed; see the dataclass docstring's IMPORTANT note) + len.
    stab_supp: torch.Tensor            # int32 [n_stab, w_max]
    stab_supp_isx: torch.Tensor        # int32 [n_stab, w_max]  1 on X-type sites (Hadamard-rotate)
    stab_supp_len: torch.Tensor        # int32 [n_stab]
    # logical observable (keeps its own X-flag for the terminal readout)
    log_supp: torch.Tensor             # int32 [L]
    log_supp_isx: torch.Tensor         # int32 [L]
    logical_kind: int                  # 0=X, 1=Z
    # the per-CZ-layer leak slice exp(L/4) (NOT the full exp(L)); CPTP + composition asserted.
    leak_kraus: torch.Tensor           # complex [n_kraus, 3, 3] (device)
    # gate unitaries, indexed by SV_GATE_IDS
    gate_unitaries: torch.Tensor       # [n_gates, 3, 3] complex (device)
    # provenance
    w_max: int = 0
    gate_names: tuple[str, ...] = SV_GATE_NAMES
    #: per-qutrit interior token streams (engine-position order), the parsed §2 authority.
    streams_by_pos: dict[int, tuple[str, ...]] = field(default_factory=dict)
    #: per-qutrit CZ-layer leak counts {pos -> n_cz} (2/3/4) — the leak placement audit.
    n_cz_by_pos: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ShotSet:
    """The result of a sampling run: the on-disk packed buffer + the §6 header.

    ``shots`` is the host-side ``uint8`` packed bit-array (shot-major: ``shot_id`` outer,
    then round, then stab; ``logical_flip`` in a trailing bitplane) when materialized;
    ``path`` / ``header_path`` are the streamed files. ``diag`` carries the kernel's
    ``{accept_rate, mean_norm_drift, peak_mem}`` (§7) when the real kernel ran.
    """

    header: dict[str, Any]
    path: Path | None
    header_path: Path | None
    n_shots: int
    syndrome_bits_per_shot: int
    diag: dict[str, Any] = field(default_factory=dict)
    shots: np.ndarray | None = None

    # ----------------------------------------------------------------------- #
    # Record accessors (ownership contract row A2: to_det_obs / packed_bytes / #
    # syndrome_prefix_bytes)                                                   #
    # ----------------------------------------------------------------------- #
    def _require_shots(self, method: str) -> np.ndarray:
        """The materialized packed buffer, or a clear error (never a silent None)."""
        if self.shots is None:
            raise ValueError(
                f"ShotSet.{method}: shots is None (the run was not materialized). "
                f"Re-run with materialize=True or load the packed buffer from "
                f"path={self.path}.")
        return self.shots

    def _header_geometry(self) -> tuple[int, int]:
        """``(n_stab, R)`` from the self-describing header, or a clear error."""
        missing = [k for k in ("n_stab", "R") if k not in self.header]
        if missing:
            raise KeyError(
                f"ShotSet header lacks {missing} (need both 'n_stab' and 'R' to "
                f"decode the packed buffer; header format "
                f"{self.header.get('format', '<absent>')!r}).")
        return int(self.header["n_stab"]), int(self.header["R"])

    def to_det_obs(self) -> dict[str, np.ndarray]:
        """Certify-ready unpack: ``{"det": (N, R*n_stab) uint8, "obs": (N,) uint8}``.

        Decodes the packed buffer via :meth:`SvSampler.unpack_shots` (the single
        inverse of :meth:`SvSampler.pack_shots`), with ``n_stab``/``R`` read from
        ``self.header`` (raises ``KeyError`` if absent, ``ValueError`` if
        ``shots is None`` -- never a silent guess). ROUND-MAJOR layout, pinned by the
        header's ``syndrome_layout`` text: "shot_major: shot_id outer, then round,
        then stab (round-major, LSB-first packbits); logical_flip in the trailing
        byte (value 0/1)" -- i.e. ``det[i, r * n_stab + s]`` is shot ``i``, round
        ``r``, stabilizer ``s``, and ``obs[i]`` is the sampled terminal logical flip
        (relative to the prepared ``m``, never ``m`` itself).

        AM-3 (contract): before any consumer deletes its hand-rolled unpack+reshape,
        it gates once that this method equals the hand-roll on a committed seeded
        ShotSet (round-major layout pinned).
        """
        packed = self._require_shots("to_det_obs")
        n_stab, R = self._header_geometry()
        det, obs = SvSampler.unpack_shots(packed, n_stab, R)
        return {"det": det, "obs": obs}

    def packed_bytes(self) -> bytes:
        """The packed shot buffer as raw bytes -- the CANONICAL byte-compare surface.

        Byte-identity claims between two runs (dense kernel vs MPS carrier; static vs
        per-round leak arm; pre/post-refactor regressions) compare THIS value: the
        contiguous shot-major packed buffer exactly as streamed to disk
        (``out_stride = ceil(R*n_stab/8) + 1`` bytes/shot; see
        :meth:`SvSampler.pack_shots`). Raises if ``shots`` was not materialized.
        """
        return np.ascontiguousarray(self._require_shots("packed_bytes")).tobytes()

    def syndrome_prefix_bytes(self, n_rounds: int) -> bytes:
        """The first ``n_rounds`` rounds' syndrome bits of EVERY shot, as bytes.

        The prefix-identity comparison surface (e.g. round-0-block EXACT equality
        between two arms): per shot, the leading ``n_rounds * n_stab`` syndrome bits
        (round-major, header-pinned layout) packed LSB-first, shots concatenated in
        shot order. ``n_rounds`` is explicit (N-4); it must satisfy
        ``0 <= n_rounds <= R`` (``n_rounds == R`` covers all syndrome bits but never
        the trailing logical-flip byte).

        BIT-EXACT boundary handling: bits-per-round ``= n_stab`` comes from the
        header. When the prefix ends mid-byte (``n_rounds * n_stab`` not a multiple
        of 8), the prefix is extracted by UNPACK + truncate-at-the-round-boundary +
        REPACK (:meth:`SvSampler.unpack_shots` then LSB-first ``packbits``; the final
        byte's tail bits are zero-padded) -- NOT by raw byte slicing, which would leak
        round ``n_rounds``'s bits sharing the boundary byte. When the boundary IS
        byte-aligned the raw per-shot byte slice is returned directly (identical to
        the unpack+repack result, cheaper).
        """
        packed = self._require_shots("syndrome_prefix_bytes")
        n_stab, R = self._header_geometry()
        n_rounds = int(n_rounds)
        if not 0 <= n_rounds <= R:
            raise ValueError(
                f"n_rounds must be in [0, R={R}] (got {n_rounds})")
        prefix_bits = n_rounds * n_stab
        if prefix_bits == 0:
            return b""
        if prefix_bits % 8 == 0:
            # byte-aligned round boundary: the per-shot leading bytes ARE the prefix
            # (LSB-first packing fills bytes in bit order, so no foreign bits leak in).
            return np.ascontiguousarray(packed[:, : prefix_bits // 8]).tobytes()
        syn, _flip = SvSampler.unpack_shots(packed, n_stab, R)
        prefix = np.packbits(syn[:, :prefix_bits], axis=1, bitorder="little")
        return np.ascontiguousarray(prefix).tobytes()


# --------------------------------------------------------------------------- #
# Lazy / guarded kernel loader (Agent K owns the real one)                     #
# --------------------------------------------------------------------------- #
def _load_sv_traj_kernel(dtype: str = "c128"):
    """Lazily import Agent K's ``sv_traj_d3`` kernel callable; ``None`` if absent.

    The loader is ``qec_twin.forward.kernels.sv_traj_d3_loader`` (K's, §7); it exposes
    ``sv_traj_d3(**kwargs)`` and ``available(precision)``. If K's loader is not yet on disk
    (or the precision build will not JIT here) this returns ``None``, so the host imports
    cleanly and the marshalling / codestate checks are independently testable. The SV-MC
    production call then raises a clear 'kernel not available' error — never a silent CPU
    fallback (GPU-only model compute, binding).
    """
    try:
        from qec_twin.forward.kernels import sv_traj_d3_loader as _loader  # type: ignore
    except Exception:
        return None
    avail = getattr(_loader, "available", None)
    fn = getattr(_loader, "sv_traj_d3", None)
    if fn is None:
        return None
    if avail is not None:
        try:
            if not avail(dtype):
                return None
        except Exception:
            return None
    return fn


def kernel_available(dtype: str = "c128") -> bool:
    """True iff Agent K's ``sv_traj_d3`` kernel loader is importable + exposes the call."""
    return _load_sv_traj_kernel(dtype) is not None


# --------------------------------------------------------------------------- #
# The host driver                                                             #
# --------------------------------------------------------------------------- #
class SvSampler:
    """P4a host driver: ``sample(run_spec) -> ShotSet`` (interface contract §7).

    Steps (per the contract):
      1. parse the circuit (reuse :func:`parse_xzzx_circuit`);
      2. marshal the schedule → the §2 fixed arrays (:meth:`marshal_schedule`);
      3. build the leakage Kraus (§3) + assert CPTP residual ``< 1e-12``;
      4. prep the codestate ``|m>_L`` (§8) + assert ⟨S⟩=+1 / ⟨L⟩=(−1)^m ``< 1e-10``;
      5. call K's ``sv_traj_d3`` (§7) — the kernel tiles ``N`` into waves of ``≤ W`` blocks
         internally (the ``wave`` arg), so the host issues ONE call;
      6. stream the packed shot buffer + the self-describing header to disk (§6).

    GPU-only compute; CPU-side disk I/O is allowed.
    """

    def __init__(self, device: str | torch.device = "cuda") -> None:
        self.device = torch.device(device)

    # ----------------------------------------------------------------------- #
    # (1) parse                                                                #
    # ----------------------------------------------------------------------- #
    def parse(self, spec: RunSpec) -> XZZXSchedule:
        sched = parse_xzzx_circuit(spec.circuit_path, spec.metadata_path,
                                   sweep_word=spec.sweep_word, verify=True)
        return sched

    # ----------------------------------------------------------------------- #
    # (2) marshal the schedule → the §2 fixed arrays                           #
    # ----------------------------------------------------------------------- #
    def marshal_schedule(self, sched: XZZXSchedule, *, R: int | None = None) -> MarshalledSchedule:
        """Marshal an :class:`XZZXSchedule` into Agent K's FIXED kernel arrays (§2/§7).

        Produces exactly the shapes/dtypes/semantics of K's ``sv_traj_d3`` loader signature
        (``forward/kernels/sv_traj_d3_loader.py``): the gate CSR (``round_gptr``/``gate_uid``/
        ``gate_site``), the stabilizer block (``stab_supp``/``stab_supp_isx``/``stab_supp_len``),
        and the logical (``log_supp``/``log_supp_isx``). Asserts the schedule's two-method
        stabilizer self-check already passed (the parser runs it under ``verify=True``) and
        that the marshalled arrays round-trip ``stab_paulis()`` (a built-in (a)-class
        consistency check; the project's adversarial-self-verification rule). ``R`` defaults
        to the schedule's round count. All arrays are int32 on ``self.device``.

        The gate CSR carries the per-round transversal DATA Pauli FRAME -- the load-bearing
        mid-cycle ``X`` echo the shipped XZZX circuit applies (FIX-1; see the inline note + the
        :meth:`_per_round_x_echo_sites` derivation). It is marshalled at the faithful
        following-round (pre-leakage) slot so the kernel realizes the per-round ``leakage -> X``
        order; an R=1 floor (or a frame-less schedule) marshals an empty CSR (no inter-round
        echo). ``R`` is the operative round count (``RunSpec.R`` override): the r01 geometry is
        reused for R>1, with the (round-invariant) transversal echo replicated per round.
        """
        n_data = int(sched.n_data)
        n_stab = len(sched.stabilizers)
        R_eff = int(sched.rounds if R is None else R)
        if R_eff < 1:
            raise ValueError(f"R must be >= 1 (got {R_eff})")
        dev = self.device

        # --- stabilizers: K's stab_supp / stab_supp_isx / stab_supp_len, padded to w_max ---
        # stab_supp_isx[s,k] = 1 iff support site k of stab s is X-type (kernel Hadamard-
        # rotates it to Z before the diagonal measurement, then back). Padding is 0 (the
        # kernel reads only the first stab_supp_len[s] entries).
        stab_paulis = sched.stab_paulis()
        if len(stab_paulis) != n_stab:
            raise AssertionError(f"stab_paulis() count {len(stab_paulis)} != n_stab {n_stab}")
        w_max = max((len(p) for p in stab_paulis), default=0)
        stab_supp = np.zeros((n_stab, w_max), dtype=np.int32)
        stab_supp_isx = np.zeros((n_stab, w_max), dtype=np.int32)
        stab_supp_len = np.zeros((n_stab,), dtype=np.int32)
        for s_i, paulis in enumerate(stab_paulis):
            sites = sorted(paulis)
            stab_supp_len[s_i] = len(sites)
            for k, site in enumerate(sites):
                kind = str(paulis[site]).upper()
                if kind not in ("X", "Z"):
                    raise ValueError(f"stab {s_i} site {site}: non-X/Z pauli {kind!r} (XZZX expects X/Z)")
                stab_supp[s_i, k] = int(site)
                stab_supp_isx[s_i, k] = 1 if kind == "X" else 0

        # built-in round-trip self-check: the marshalled arrays reproduce stab_paulis()
        for s_i, paulis in enumerate(stab_paulis):
            recon = {}
            for k in range(int(stab_supp_len[s_i])):
                site = int(stab_supp[s_i, k])
                recon[site] = "X" if int(stab_supp_isx[s_i, k]) == 1 else "Z"
            assert recon == {int(k): str(v).upper() for k, v in paulis.items()}, (
                f"marshalled stab {s_i} {recon} != schedule {paulis}")

        # --- logical observable: log_supp + log_supp_isx (X-flag per logical site) -------
        log_sites = sorted(sched.logical)
        log_supp = np.array(log_sites, dtype=np.int32)
        log_supp_isx = np.array(
            [1 if str(sched.logical[s]).upper() == "X" else 0 for s in log_sites], dtype=np.int32)
        logical_kind = 0 if str(sched.logical_kind).upper() == "X" else 1

        # --- gate CSR (per-round transversal DATA Pauli FRAME — the X echo + the post-M Y) ----
        # The shipped XZZX circuit applies a per-round transversal single-qutrit DATA Pauli
        # FRAME OUTSIDE the stabilizer-extraction basis rotations: a mid-cycle transversal X
        # echo AND a post-measurement transversal Y (RoundDataFrame). The H-rotations ARE carried
        # by the per-stabilizer X-flag (stab_supp_isx, rotated inside the measurement); but the X
        # echo and the post-M Y are NOT — and they are LOAD-BEARING for the multi-round leakage
        # dynamics: the WG leakage channel is |0>/|1> ASYMMETRIC (heating acts on |1>, |0> is
        # leakage-inert), so the X;Y pair = diag(i,-i,1) (a Z-like phase, |2> inert) is a physical
        # |0><->|1> DYNAMICAL-DECOUPLING echo that REFOCUSES the coherent |1><->|2> exchange,
        # SUPPRESSING the leaked |2> population ~10x. Dropping the Y (X-only model) over-states the
        # R>1 |2| ~10x — a temporal-memory error growing with R: from |1>, |2|(R=1/3/5/10) is
        # 0.0047/0.0042/0.0041/0.0065 (≈FLAT, refocused) WITH the Y vs 0.0047/0.0170/0.0346/0.0693
        # (GROWING) without it (the single-qutrit circuit-faithful target; verified in
        # outputs/teacher_prereg/p4a_host_y_target_derivation.py). An earlier build EXCLUDED the Y
        # on a "detector-invariant frame" argument — that was WRONG: the Y is a BARE UNCONDITIONAL
        # transversal Pauli on the 9 data qutrits (NOT a CY/sweep-controlled correction; ZERO
        # measurement-conditioned data Paulis exist in the circuit), i.e. a PHYSICAL DD pulse in
        # the leakage path. It is injected here.
        #
        # FAITHFUL PLACEMENT vs the kernel's frozen op order. The faithful per-INTERIOR-round
        # order is  leakage -> X (mid-cycle) -> M -> Y (post-M) ; the X and Y both act on the
        # data between consecutive leakage lumps, X BEFORE Y. Agent K's kernel applies gate-CSR
        # gates ONLY PRE-leakage (per round: gates -> leakage -> measure, frozen). So each
        # physical cycle's (X then Y) pair is marshalled as the PRE-leakage gates of the FOLLOWING
        # round (X first, then Y): the kernel then realizes
        #     L_0 M_0 | X Y L_1 M_1 | X Y L_2 M_2 | ...
        # whose free per-round leakage seed carries cycle (c-1)'s X then Y. The LAST physical
        # cycle (round R) applies its X but its post-M Y is the TERMINAL readout frame and is
        # ABSENT (RoundDataFrame.post_measure is empty on the final round); in the following-slot
        # scheme that last cycle's lone X would land on the dropped round R, so BOTH its X and the
        # (non-existent) Y are correctly absent — identical to the prior X-only handling, now with
        # the Y added. The kernel's measurement is a diagonal Z-basis POVM and X/Y are |2>-inert
        # on the computational frame, so the detection events stay the deterministic Pauli frame
        # they were (X-frame robustness verified in p4a_host_x_vs_measure_order.py; the Y adds an
        # |0><->|1> phase + flip that is likewise detector-absorbed). The DM oracle
        # (qutrit_dm.QutritDM.apply_round_data_gates) applies the IDENTICAL per-round [X, Y] in the
        # SAME position so Gate-4 (SV-MC vs DM) stays valid.
        #
        # The transversal X echo + post-M Y are replicated per round from the parsed per-round
        # frame (each is identical every interior round for d3 XZZX); ``per_round_x_sites`` /
        # ``per_round_y_sites`` are the data positions the X / Y act on (all 9). They are emitted
        # X-then-Y so the kernel applies them in the physical order. round_gptr/gate_uid/gate_site
        # are the §7 CSR.
        per_round_x_sites = self._per_round_x_echo_sites(sched)
        per_round_y_sites = self._per_round_y_frame_sites(sched)

        # r01-REUSED-GEOMETRY Y inference (the load-bearing R>1 subtlety). The SV sampler reuses
        # the SINGLE-cycle r01 circuit's geometry for R>1 (RunSpec.R replicates the round-invariant
        # frame). But r01 is ONE cycle ending in the terminal readout, so it carries the mid-cycle
        # X echo yet NO post-M Y (the Y exists only BETWEEN consecutive cycles — verified: the r10
        # parse shows the transversal post-M Y on every INTERIOR round 0..R-2, support IDENTICAL to
        # the X echo = all 9 data, and absent on the final round). So when R>1 is requested from a
        # schedule that has the X echo but no parsed post-M Y (the r01 reuse), the interior-round Y
        # is the transversal frame on the SAME data the X echo acts on (the physical R>1 circuit's
        # interior Y, which r01 cannot show). When the schedule DID parse an explicit post-M Y
        # (a directly-parsed multi-round circuit), we use it and ASSERT it matches the X support
        # (the transversal DD pair X;Y acts on the same data). Either way the Y is the SAME
        # transversal support as the X — never silently absent at R>1. (a)-class self-check.
        if per_round_y_sites:
            if per_round_x_sites and per_round_y_sites != per_round_x_sites:
                raise NotImplementedError(
                    f"parsed post-M Y support {per_round_y_sites} != X echo support "
                    f"{per_round_x_sites}; the transversal DD pair X;Y is expected on the SAME "
                    f"data qutrits. A circuit with mismatched X/Y supports needs a per-round CSR.")
        elif per_round_x_sites and R_eff > 1:
            # r01 reuse at R>1: the interior-round post-M Y = the transversal X-echo support.
            per_round_y_sites = per_round_x_sites

        x_uid = SV_GATE_IDS["X"]
        y_uid = SV_GATE_IDS["Y"]
        round_gptr_list = [0]
        gate_uid_list: list[int] = []
        gate_site_list: list[int] = []
        for r in range(R_eff):
            if r >= 1:
                # cycle (r-1)'s transversal X echo THEN its post-M Y, applied PRE-leakage of round
                # r (§7 order; X before Y = the physical mid-cycle-then-post-M order).
                for site in per_round_x_sites:
                    gate_uid_list.append(x_uid)
                    gate_site_list.append(int(site))
                for site in per_round_y_sites:
                    gate_uid_list.append(y_uid)
                    gate_site_list.append(int(site))
            round_gptr_list.append(len(gate_uid_list))
        round_gptr = np.asarray(round_gptr_list, dtype=np.int32)
        gate_uid = np.asarray(gate_uid_list, dtype=np.int32)
        gate_site = np.asarray(gate_site_list, dtype=np.int32)

        gate_unis = gate_unitaries_table(dev)

        def _i32(a: np.ndarray) -> torch.Tensor:
            return torch.as_tensor(a, dtype=torch.int32, device=dev).contiguous()

        return MarshalledSchedule(
            n_data=n_data,
            n_stab=n_stab,
            R=R_eff,
            round_gptr=_i32(round_gptr),
            gate_uid=_i32(gate_uid),
            gate_site=_i32(gate_site),
            stab_supp=_i32(stab_supp),
            stab_supp_isx=_i32(stab_supp_isx),
            stab_supp_len=_i32(stab_supp_len),
            log_supp=_i32(log_supp),
            log_supp_isx=_i32(log_supp_isx),
            logical_kind=logical_kind,
            gate_unitaries=gate_unis,
            w_max=int(w_max),
            x_echo_sites=tuple(int(s) for s in per_round_x_sites),
            y_frame_sites=tuple(int(s) for s in per_round_y_sites),
        )

    @staticmethod
    def _per_round_x_echo_sites(sched: XZZXSchedule) -> tuple[int, ...]:
        """The data positions the per-round transversal X echo acts on (sorted), or ``()``.

        Reads the parsed per-round DATA Pauli frame (``sched.per_round_data_frame``) and returns
        the support of the mid-cycle ``X`` echo — a load-bearing leakage frame (FIX-1). The
        echo is the SAME every round for d3 XZZX (a transversal X on all 9 data); this ASSERTS
        that consistency (a built-in ``(a)``-class self-check: a circuit whose per-round X echo
        VARIES round-to-round, or mixes non-X pre-measure frame gates, would need a per-round CSR
        and must not be silently collapsed). Returns ``()`` when the schedule carries no parsed
        per-round frame (so a frame-less parse marshals an empty CSR, the prior behavior).

        This reads only the PRE-measurement frame (the ``X`` echo). The POST-measurement ``Y``
        frame is read by the companion :meth:`_per_round_y_frame_sites`; BOTH are load-bearing
        physical DD pulses in the leakage path and BOTH are marshalled into the gate CSR (X then
        Y) — see the marshalling note in :meth:`marshal_schedule` and ``RoundDataFrame``.
        """
        frames = getattr(sched, "per_round_data_frame", ())
        if not frames:
            return ()
        x_supports: list[tuple[int, ...]] = []
        for r, rf in enumerate(frames):
            pre = list(rf.pre_measure)
            # only X is expected pre-measure for d3 XZZX; a non-X pre-measure frame gate (Y/Z/S)
            # would be a different per-round dynamics the once-per-round X marshalling does not
            # model — fail loudly rather than drop it (adversarial-self-verification rule).
            non_x = [g for g, _ in pre if str(g).upper() != "X"]
            if non_x:
                raise NotImplementedError(
                    f"round {r}: pre-measurement DATA frame has non-X gate(s) {non_x} "
                    f"({pre}); the per-round X-echo marshalling models only the transversal X. "
                    f"Extend marshal_schedule to a per-round gate CSR for this circuit.")
            xs = [tuple(sites) for g, sites in pre if str(g).upper() == "X"]
            if len(xs) > 1:
                raise NotImplementedError(
                    f"round {r}: multiple pre-measurement X frames {xs}; expected one transversal X")
            x_supports.append(xs[0] if xs else ())
        # the echo support must be identical across rounds that HAVE one (the transversal echo).
        nonempty = [s for s in x_supports if s]
        if nonempty and any(s != nonempty[0] for s in nonempty):
            raise NotImplementedError(
                f"the per-round transversal X echo varies across rounds ({set(x_supports)}); "
                f"the once-per-round X marshalling requires a fixed transversal echo")
        return tuple(sorted(nonempty[0])) if nonempty else ()

    @staticmethod
    def _per_round_y_frame_sites(sched: XZZXSchedule) -> tuple[int, ...]:
        """The data positions the per-round POST-measurement transversal ``Y`` acts on, or ``()``.

        The companion to :meth:`_per_round_x_echo_sites` for the POST-measurement frame. Reads the
        parsed per-round DATA Pauli frame (``sched.per_round_data_frame``) ``post_measure`` field
        and returns the support of the transversal ``Y`` — the physical post-M dynamical-decoupling
        pulse (a BARE UNCONDITIONAL transversal Pauli on all 9 data qutrits in the real circuit,
        NOT a measurement-conditioned ``CY``/sweep correction). The pair ``(X mid-cycle ; Y post-M)
        = diag(i,-i,1)`` is a Z-like DD echo that refocuses the WG ``|1><->|2>`` leakage exchange;
        it is LOAD-BEARING for the multi-round leakage trajectory (it suppresses the leaked ``|2>``
        population ~10x and was previously, wrongly, dropped).

        The ``Y`` is the SAME every INTERIOR round for d3 XZZX (a transversal Y on all 9 data); the
        FINAL round's ``post_measure`` is EMPTY (the terminal readout — no post-M frame), so that
        round contributes ``()`` and the following-slot marshalling never emits a Y for it. This
        ASSERTS the per-round consistency (a built-in ``(a)``-class self-check: a non-Y post-measure
        frame gate, or a Y support that VARIES across interior rounds, would need a per-round CSR
        and must not be silently collapsed). Returns ``()`` when no per-round frame was parsed (a
        frame-less parse marshals an empty CSR — the prior behavior) OR when no round carries a
        post-M Y (e.g. the r01 single-cycle circuit, whose one round ends in the terminal readout
        and has no post-M frame; the R>1 model adds the Y that r01 cannot show).
        """
        frames = getattr(sched, "per_round_data_frame", ())
        if not frames:
            return ()
        y_supports: list[tuple[int, ...]] = []
        for r, rf in enumerate(frames):
            post = list(rf.post_measure)
            # only Y is expected post-measure for d3 XZZX; a non-Y post-measure frame gate (X/Z/S)
            # would be a different per-round dynamics the once-per-round Y marshalling does not
            # model — fail loudly rather than drop it (adversarial-self-verification rule).
            non_y = [g for g, _ in post if str(g).upper() != "Y"]
            if non_y:
                raise NotImplementedError(
                    f"round {r}: post-measurement DATA frame has non-Y gate(s) {non_y} "
                    f"({post}); the per-round post-M Y marshalling models only the transversal Y. "
                    f"Extend marshal_schedule to a per-round gate CSR for this circuit.")
            ys = [tuple(sites) for g, sites in post if str(g).upper() == "Y"]
            if len(ys) > 1:
                raise NotImplementedError(
                    f"round {r}: multiple post-measurement Y frames {ys}; expected one transversal Y")
            y_supports.append(ys[0] if ys else ())
        # the Y support must be identical across rounds that HAVE one (the transversal post-M Y);
        # the final round legitimately has none (terminal readout).
        nonempty = [s for s in y_supports if s]
        if nonempty and any(s != nonempty[0] for s in nonempty):
            raise NotImplementedError(
                f"the per-round transversal post-M Y varies across rounds ({set(y_supports)}); "
                f"the once-per-round Y marshalling requires a fixed transversal frame")
        return tuple(sorted(nonempty[0])) if nonempty else ()

    # ----------------------------------------------------------------------- #
    # (3) leakage Kraus (§3) + CPTP assert                                     #
    # ----------------------------------------------------------------------- #
    def build_leakage_kraus(self, spec: RunSpec) -> torch.Tensor:
        """Build the WG leakage Kraus ``(n_kraus, 3, 3)`` (§3) + assert CPTP ``< 1e-12``.

        Reuses :func:`leakage_kraus_torch` (the single source of truth for the validated WG
        ``exp(Lindbladian)`` algebra). ``(theta, g_seep, g_heat)`` are the registered sweep
        from ``spec`` (never a pinned headline). Returns a contiguous device tensor stack.
        """
        kr_list = leakage_kraus_torch(spec.theta, spec.g_seep, spec.g_heat,
                                      device=self.device, dtype=CDTYPE)
        kraus = torch.stack(kr_list).contiguous()
        resid = self.cptp_residual(kraus)
        if resid >= CPTP_TOL:
            raise AssertionError(
                f"leakage Kraus CPTP residual {resid:.3e} >= {CPTP_TOL:.0e} "
                f"(theta={spec.theta}, g_seep={spec.g_seep}, g_heat={spec.g_heat})")
        return kraus

    @staticmethod
    def cptp_residual(kraus: torch.Tensor) -> float:
        """``max|sum_k K_k^dag K_k - I|`` for a ``(n_kraus, d, d)`` stack (the §3 check).

        BL-1 PAIR doctrine (binding; v2 review dispositions of
        ``docs/twin_validation/api_hardening_ownership_design.md``).
        This is the ARM-SIDE precondition check:
        the arm's own build + entry guards route HERE (:meth:`build_leakage_kraus`,
        :meth:`build_within_cycle_leak`, and ``mps_forward.MpsLeakageForward.sample``'s
        per-round ``leak_slices`` entry guard). The AUDIT-SIDE cert implementation is
        ``qec_twin.audit.floor_backend.cptp_residual`` -- every cert gate (e.g.
        L-soft-6) must route THERE, never here. The two implementations remain
        INDEPENDENT FOREVER and must never be aliased, merged, or re-exported as one:
        a single shared implementation would let one conjugation bug pass both the
        precondition and the cert gate (FAITHFULNESS_PROTOCOL Rule I -- a check vs the
        arm's own residual function is not certification).

        Tolerance conventions (AM-8; THREE distinct constants, never interchangeable):

        * ``CPTP_TOL = 1e-12`` -- the (a)-class build/entry GATE this residual is
          compared against (a faithful channel must be CPTP below it);
        * ``1e-8`` -- the ENGINEERED-VIOLATION precondition floor: a harness-side
          sabotaged/control input must violate CPTP by MORE than 1e-8 to count as a
          valid non-vacuous control (a knife-edge violation just above the gate --
          the measured 1.181e-12 class -- is a K-4 trap, not a control);
        * ``1e-9`` -- ``floor_backend.cptp_residual``'s documented build tolerance
          ("a faithful leak slice is CPTP to < 1e-9"): the audit side's documented
          expectation of faithful inputs, not a gate constant here.
        """
        d = kraus.shape[-1]
        acc = torch.einsum("kab,kac->bc", kraus.conj(), kraus)
        eye = torch.eye(d, dtype=acc.dtype, device=acc.device)
        return float(torch.max(torch.abs(acc - eye)).real)

    # ----------------------------------------------------------------------- #
    # P4a within-cycle: the per-CZ exp(L/4) leak slice + composition assert     #
    # ----------------------------------------------------------------------- #
    def build_within_cycle_leak(self, spec: RunSpec) -> tuple[torch.Tensor, dict[str, Any]]:
        """The per-CZ-layer leak slice ``exp(L/4)`` Kraus + the model-§3 composition assert.

        Builds the fractional slice (:func:`leak_slice_kraus_torch`, ``frac = WC_LEAK_FRAC =
        1/4``) and ASSERTS, BEFORE marshalling (model §3 build checklist 2):

          * CPTP residual ``< 1e-12`` (``Σ K†K = I`` for the slice);
          * the COMPOSITION identity ``‖exp(L) − (exp(L/4))⁴‖ < 1e-12`` (``WC_LEAK_COMPOSE_TOL``) —
            four ``exp(L/4)`` slices compose to the registered full-cycle channel
            ``leakage_kraus(θ, g_seep, g_heat)``, so a 4-CZ qutrit receives EXACTLY the registered
            per-round channel and an ``n_cz``-CZ qutrit ``exp(L·n_cz/4)`` (genuinely less).

        ``(theta, g_seep, g_heat)`` are the registered sweep from ``spec`` (never pinned).
        Returns ``(leak_kraus, evidence)`` — ``leak_kraus`` is the contiguous ``(n_kraus,3,3)``
        device slice; ``evidence`` carries the asserted residuals (printed by the dev scripts).
        """
        slice_list = leak_slice_kraus_torch(
            spec.theta, spec.g_seep, spec.g_heat, frac=WC_LEAK_FRAC,
            device=self.device, dtype=CDTYPE)
        leak = torch.stack(slice_list).contiguous()
        resid = self.cptp_residual(leak)
        if resid >= CPTP_TOL:
            raise AssertionError(
                f"within-cycle leak slice exp(L/4) CPTP residual {resid:.3e} >= {CPTP_TOL:.0e} "
                f"(theta={spec.theta}, g_seep={spec.g_seep}, g_heat={spec.g_heat})")
        compose_gap = self._leak_compose_residual(spec, leak)
        if compose_gap >= WC_LEAK_COMPOSE_TOL:
            raise AssertionError(
                f"within-cycle leak composition ‖exp(L) − (exp(L/4))^4‖ = {compose_gap:.3e} "
                f">= {WC_LEAK_COMPOSE_TOL:.0e} (theta={spec.theta}, g_seep={spec.g_seep}, "
                f"g_heat={spec.g_heat}); the per-CZ slice does not compose to the full channel")
        evidence = {
            "frac": float(WC_LEAK_FRAC),
            "n_kraus_slice": int(leak.shape[0]),
            "cptp_residual": float(resid),
            "compose_residual": float(compose_gap),
            "theta": float(spec.theta),
            "g_seep": float(spec.g_seep),
            "g_heat": float(spec.g_heat),
        }
        return leak, evidence

    def _leak_compose_residual(self, spec: RunSpec, leak: torch.Tensor) -> float:
        """``max|exp(L)(|1><1|) − (exp(L/4))^4(|1><1|)|`` — the model-§3 composition check.

        Applies the FULL-cycle channel ``leakage_kraus`` and the four-fold ``exp(L/4)`` slice to
        the same probe ``|1><1|`` (the leakage-active input) and returns the worst-element gap.
        ``|1><1|`` is the load-bearing probe (``|0>`` is leakage-inert, so the full 3x3 channel
        difference is concentrated on the ``|1>``/``|2>`` sector). GPU; complex128.
        """
        full_list = leakage_kraus_torch(spec.theta, spec.g_seep, spec.g_heat,
                                        device=self.device, dtype=CDTYPE)
        full = torch.stack(full_list).contiguous()
        rho = torch.zeros((QUDIT, QUDIT), dtype=CDTYPE, device=self.device)
        rho[1, 1] = 1.0
        r_full = torch.einsum("kab,bc,kdc->ad", full, rho, full.conj())
        r_comp = rho
        for _ in range(int(round(1.0 / WC_LEAK_FRAC))):
            r_comp = torch.einsum("kab,bc,kdc->ad", leak, r_comp, leak.conj())
        return float(torch.max(torch.abs(r_full - r_comp)).real)

    # ----------------------------------------------------------------------- #
    # P4a within-cycle: the per-qutrit gate+leak CSR (the §2/§3 model)          #
    # ----------------------------------------------------------------------- #
    def marshal_within_cycle(self, sched: XZZXSchedule, leak_kraus: torch.Tensor, *,
                             R: int | None = None) -> WithinCycleMarshalled:
        """Marshal the circuit-faithful WITHIN-CYCLE per-qutrit gate+leak CSR (model §2/§3/§4).

        Produces :class:`WithinCycleMarshalled` — the per-qutrit interleaved gate+leak schedule
        that REPLACES the lumped :meth:`marshal_schedule`. For each round, the per-qutrit
        interior token streams (``sched.within_cycle_streams``, the §2 authority parsed from a
        MULTI-ROUND circuit's interior round) are serialized into TWO op segments — PRE-measure
        and POST-measure — per the ``WithinCycleMarshalled`` CSR format (the format H DEFINES;
        Agent K consumes):

          * PRE-measure ops: per qutrit (engine-position order) its ordered tokens up to ``M`` —
            ``H``/``X`` → a ``WC_OP_GATE`` (the qutrit unitary), ``LEAK`` → a ``WC_OP_LEAK`` (the
            ``exp(L/4)`` channel on that qutrit). One LEAK op per CZ layer the qutrit touches.
          * (the kernel then measures all 8 stabilizers — a PURE diagonal Z-parity)
          * POST-measure ops: the transversal ``Y`` (one ``WC_OP_GATE`` per data qutrit),
            DROPPED on the TERMINAL round (the round count's last round — model §1/§8).

        The cross-qutrit serial order is faithful (single-qutrit ops on distinct qutrits
        commute). ``stab_supp_isx`` carries the REAL per-support X-flag (X-supports Hadamard-
        rotated to Z for the diagonal measurement): the in-stream H's net to identity per qutrit
        (2 H's/round), so the data is back in the COMPUTATIONAL basis at the M and the X-support
        rotation is STILL required — the spec text's "drop stab_supp_isx / pure-Z" (model §4 R3)
        is a derivation slip (it contradicts §4 R1's even-H-count → net-identity; verified on the
        d3 codestate, see the :class:`WithinCycleMarshalled` IMPORTANT note +
        ``p4a_host_wc_marshal.py`` §3). The logical keeps its OWN X-flag (the terminal readout is
        not a within-cycle stabilizer). ``R`` defaults to the schedule's round count; the interior
        stream is replicated for every round, the terminal round dropping the post-M Y.

        Requires ``sched.within_cycle_streams`` to be populated (a MULTI-ROUND source circuit;
        r01 has none — model §1 caveat). ``leak_kraus`` is the asserted ``exp(L/4)`` slice from
        :meth:`build_within_cycle_leak`.
        """
        streams = list(sched.within_cycle_streams)
        n_data = int(sched.n_data)
        n_stab = len(sched.stabilizers)
        R_eff = int(sched.rounds if R is None else R)
        if R_eff < 1:
            raise ValueError(f"R must be >= 1 (got {R_eff})")
        if not streams:
            raise ValueError(
                "marshal_within_cycle requires the per-qutrit within-cycle interior streams "
                "(sched.within_cycle_streams). They are populated ONLY from a MULTI-ROUND circuit "
                "(r10); r01's single round is first+terminal, not a clean interior round (model §1).")
        if len(streams) != n_data:
            raise AssertionError(
                f"within-cycle streams count {len(streams)} != n_data {n_data}")
        dev = self.device

        # streams keyed + ordered by engine position; assert the §2 self-checks survived parse.
        by_pos: dict[int, WithinCycleStream] = {s.pos: s for s in streams}
        if sorted(by_pos) != list(range(n_data)):
            raise AssertionError(
                f"within-cycle stream positions {sorted(by_pos)} != 0..{n_data - 1}")

        # --- stabilizers (REAL X-flag: in-stream H's net to identity, so X-rotation still needed) -
        stab_paulis = sched.stab_paulis()
        if len(stab_paulis) != n_stab:
            raise AssertionError(f"stab_paulis() count {len(stab_paulis)} != n_stab {n_stab}")
        w_max = max((len(p) for p in stab_paulis), default=0)
        stab_supp = np.zeros((n_stab, w_max), dtype=np.int32)
        stab_supp_isx = np.zeros((n_stab, w_max), dtype=np.int32)
        stab_supp_len = np.zeros((n_stab,), dtype=np.int32)
        for s_i, paulis in enumerate(stab_paulis):
            sites = sorted(paulis)
            stab_supp_len[s_i] = len(sites)
            for k, site in enumerate(sites):
                kind = str(paulis[site]).upper()
                if kind not in ("X", "Z"):
                    raise ValueError(f"stab {s_i} site {site}: non-X/Z pauli {kind!r} (XZZX expects X/Z)")
                stab_supp[s_i, k] = int(site)
                stab_supp_isx[s_i, k] = 1 if kind == "X" else 0  # X-supports Hadamard-rotate to Z

        # --- logical observable (keeps its own X-flag for the terminal readout) -----------
        log_sites = sorted(sched.logical)
        log_supp = np.array(log_sites, dtype=np.int32)
        log_supp_isx = np.array(
            [1 if str(sched.logical[s]).upper() == "X" else 0 for s in log_sites], dtype=np.int32)
        logical_kind = 0 if str(sched.logical_kind).upper() == "X" else 1

        # --- per-qutrit gate+leak CSR: 2 op-segments per round (pre|post measure) ----------
        h_uid = SV_GATE_IDS["H"]
        x_uid = SV_GATE_IDS["X"]
        y_uid = SV_GATE_IDS["Y"]
        round_op_ptr: list[int] = [0]
        op_kind: list[int] = []
        op_uid: list[int] = []
        op_site: list[int] = []

        def _emit_gate(uid: int, site: int) -> None:
            op_kind.append(WC_OP_GATE); op_uid.append(int(uid)); op_site.append(int(site))

        def _emit_leak(site: int) -> None:
            op_kind.append(WC_OP_LEAK); op_uid.append(0); op_site.append(int(site))

        for r in range(R_eff):
            is_terminal = (r == R_eff - 1)
            # PRE-measure segment: per qutrit, its ordered pre-M tokens (H/X gates + LEAK slices).
            for p in range(n_data):
                for tok in by_pos[p].pre_measure_tokens():
                    if tok == "H":
                        _emit_gate(h_uid, p)
                    elif tok == "X":
                        _emit_gate(x_uid, p)
                    elif tok == "LEAK":
                        _emit_leak(p)
                    else:
                        raise AssertionError(
                            f"within-cycle pos {p}: unexpected pre-M token {tok!r} "
                            f"(only H/X/LEAK expected before the M boundary)")
            round_op_ptr.append(len(op_kind))  # end of pre-segment (measurement happens here)
            # POST-measure segment: the transversal Y (one GATE op per data qutrit), unless terminal.
            if not is_terminal:
                for p in range(n_data):
                    post = by_pos[p].post_measure_tokens()
                    for tok in post:
                        if tok == "Y":
                            _emit_gate(y_uid, p)
                        else:
                            raise AssertionError(
                                f"within-cycle pos {p}: unexpected post-M token {tok!r} "
                                f"(only the transversal Y is expected post-M)")
            round_op_ptr.append(len(op_kind))  # end of post-segment

        def _i32(a) -> torch.Tensor:
            return torch.as_tensor(np.asarray(a, dtype=np.int32), dtype=torch.int32, device=dev).contiguous()

        # leak Kraus dtype follows the requested precision elsewhere; the slice is c128 by default.
        leak = leak_kraus.to(dev).contiguous()
        gate_unis = gate_unitaries_table(dev)

        return WithinCycleMarshalled(
            n_data=n_data,
            n_stab=n_stab,
            R=R_eff,
            round_op_ptr=_i32(round_op_ptr),
            op_kind=_i32(op_kind),
            op_uid=_i32(op_uid),
            op_site=_i32(op_site),
            stab_supp=_i32(stab_supp),
            stab_supp_isx=_i32(stab_supp_isx),
            stab_supp_len=_i32(stab_supp_len),
            log_supp=_i32(log_supp),
            log_supp_isx=_i32(log_supp_isx),
            logical_kind=logical_kind,
            leak_kraus=leak,
            gate_unitaries=gate_unis,
            w_max=int(w_max),
            streams_by_pos={p: tuple(by_pos[p].tokens) for p in range(n_data)},
            n_cz_by_pos={p: int(by_pos[p].n_cz) for p in range(n_data)},
        )

    # ----------------------------------------------------------------------- #
    # P4a within-cycle: DM-oracle drivers (the §5 / Gate-4 / codestate harness) #
    # ----------------------------------------------------------------------- #
    def within_cycle_dm_engine(self, sched: XZZXSchedule) -> QutritDM:
        """A 9-data-qutrit :class:`QutritDM` with the schedule's code geometry, for the
        within-cycle DM oracle (the Gate-4 ground truth / codestate-validity harness).

        Sets the stabilizers + logical so ``init_logical`` / ``logical_distribution`` use the
        real XZZX geometry. The caller drives it with :meth:`apply_within_cycle_round`, whose
        stabilizer measurement KEEPS the X-support rotation (``stab_supp_isx``; the in-stream
        within-cycle H's net to identity, so the X-rotation is still needed — see
        :class:`WithinCycleMarshalled`).
        """
        n = int(sched.n_data)
        logical = dict(sched.logical)
        logical_kind = str(sched.logical_kind).upper()
        eng = QutritDM(n, device=self.device)
        eng.set_code(
            stabilizers=sched.stab_paulis(),
            logical_z=logical if logical_kind == "Z" else None,
            logical_x=logical if logical_kind == "X" else None,
        )
        return eng

    def apply_within_cycle_round(self, eng: QutritDM, marsh: WithinCycleMarshalled, *,
                                 measure: bool = False, b: float = 1.0, arm: str = "A",
                                 terminal: bool = False) -> dict[tuple, float] | None:
        """Evolve ``eng.rho`` through ONE circuit-faithful WITHIN-CYCLE round (model §2/§4).

        Applies, in the faithful order: (1) the per-qutrit PRE-measurement streams (H's + the
        ``exp(L/4)`` leak slices at each touched CZ layer + the mid-cycle X), via
        :meth:`QutritDM.apply_within_cycle_premeasure`; (2) if ``measure``, the EXACT stabilizer
        syndrome distribution (``syndrome_distribution`` with the REAL X-flag — X-supports
        Hadamard-rotated to Z; the in-stream H's net to identity so the X-rotation is STILL
        needed, the spec text's pure-Z is a derivation slip — see
        :class:`WithinCycleMarshalled`; the returned dict is ``P(s)``, ``eng.rho`` left at the
        parent state); (3) the POST-measurement transversal Y (dropped when ``terminal``), via
        :meth:`QutritDM.apply_within_cycle_postmeasure`.

        The DM oracle implements the IDENTICAL per-round stream the host marshals for the SV-MC
        kernel (model §4 build note), so Gate-4 (``TV(SV-MC, DM) ~ C/√N``) stays valid against
        the within-cycle model. Returns ``P(s)`` when ``measure`` else ``None``.
        """
        streams = dict(marsh.streams_by_pos)
        leak = list(marsh.leak_kraus)
        eng.apply_within_cycle_premeasure(streams, leak)
        dist = None
        if measure:
            dist = eng.syndrome_distribution(
                self._marshalled_stab_paulis(marsh), b=b, arm=arm, diagonal_z=False)
        eng.apply_within_cycle_postmeasure(streams, terminal=terminal)
        return dist

    @staticmethod
    def _marshalled_stab_paulis(marsh: WithinCycleMarshalled) -> list[dict[int, str]]:
        """Reconstruct the per-stabilizer support dicts (with the REAL X/Z type) from the
        marshalled arrays. The X/Z label IS load-bearing: the measurement Hadamard-rotates the
        X-supports to Z (the in-stream within-cycle H's net to identity, so the X-rotation is
        still required — see the :class:`WithinCycleMarshalled` IMPORTANT note)."""
        supp = marsh.stab_supp.detach().cpu().numpy()
        isx = marsh.stab_supp_isx.detach().cpu().numpy()
        slen = marsh.stab_supp_len.detach().cpu().numpy()
        out: list[dict[int, str]] = []
        for s_i in range(int(marsh.n_stab)):
            out.append({int(supp[s_i, k]): ("X" if int(isx[s_i, k]) == 1 else "Z")
                        for k in range(int(slen[s_i]))})
        return out

    # ----------------------------------------------------------------------- #
    # (8) codestate prep + ⟨S⟩/⟨L⟩ self-check                                  #
    # ----------------------------------------------------------------------- #
    def build_codestate(self, sched: XZZXSchedule, m: int) -> tuple[torch.Tensor, dict[str, Any]]:
        """Build the pure logical codestate ``|m>_L`` as a state vector + the §8 check.

        Reuses the Phase-1 ``QutritDM`` codestate machinery in SV form: it sets the code
        geometry then projects a seed through the stabilizer group + the logical-Z sector
        (``QutritDM._codestate_vector``), giving the EXACT pure ``|m>_L`` (no DM ever
        materialized at full scale — this is a single 3^n vector). It then ASSERTS, in SV
        form, ``<S> = +1`` for every stabilizer and ``<L> = (-1)^m`` to ``< 1e-10`` BEFORE
        the state is handed to the kernel (so a bad geometry fails loudly, never samples).

        Returns ``(psi, evidence)`` where ``psi`` is the normalized ``3^n`` device SV and
        ``evidence`` carries the measured ⟨S⟩ list, ⟨L⟩, and the worst residual (printed by
        the dev scripts).
        """
        m = int(m)
        if m not in (0, 1):
            raise ValueError("logical m must be 0 or 1")
        n = int(sched.n_data)
        stabs = sched.stab_paulis()
        logical = dict(sched.logical)
        logical_kind = str(sched.logical_kind).upper()

        eng = QutritDM(n, device=self.device)
        eng.set_code(
            stabilizers=stabs,
            logical_z=logical if logical_kind == "Z" else None,
            logical_x=logical if logical_kind == "X" else None,
        )
        psi = eng._codestate_vector(m)  # pure SV via stabilizer + logical projection (§8)
        nrm = torch.linalg.vector_norm(psi)
        if nrm.real <= NUMERICAL_ZERO:
            raise RuntimeError(f"codestate |{m}>_L collapsed to zero norm (geometry inconsistent)")
        psi = (psi / nrm.to(CDTYPE)).contiguous()

        # ⟨S⟩ for every stabilizer + ⟨L⟩ for the logical, as SV expectations ⟨ψ|O|ψ⟩.
        s_vals = [self._expectation(eng, psi, s) for s in stabs]
        l_val = self._expectation(eng, psi, logical)
        l_target = float((-1) ** m)
        worst_s = max((abs(v - 1.0) for v in s_vals), default=0.0)
        worst_l = abs(l_val - l_target)
        worst = max(worst_s, worst_l)
        if worst >= CODESTATE_TOL:
            raise AssertionError(
                f"codestate |{m}>_L check failed: max|<S>-1|={worst_s:.2e}, "
                f"|<L>-(-1)^m|={worst_l:.2e} (tol {CODESTATE_TOL:.0e}); <S>={s_vals}, <L>={l_val}")
        evidence = {
            "m": m,
            "stab_expectations": [float(v) for v in s_vals],
            "logical_expectation": float(l_val),
            "logical_target": l_target,
            "worst_S_residual": float(worst_s),
            "worst_L_residual": float(worst_l),
            "norm": float(nrm.real),
        }
        return psi, evidence

    @staticmethod
    def _expectation(eng: QutritDM, psi: torch.Tensor, op: dict[int, str]) -> float:
        """``<psi| O |psi>`` (real part) for a multi-site computational-Pauli operator ``O``
        (``{site -> 'X'|'Z'}``), via the engine's operator-on-vector helper (``|2>`` inert)."""
        op_psi = eng._apply_logical_vector(psi.clone(), op)
        return float(torch.vdot(psi, op_psi).real)

    # ----------------------------------------------------------------------- #
    # (6) shot I/O — packing + header                                          #
    # ----------------------------------------------------------------------- #
    @staticmethod
    def syndrome_bits_per_shot(n_stab: int, R: int) -> int:
        return int(n_stab) * int(R)

    def build_header(self, spec: RunSpec, marsh: MarshalledSchedule, sched: XZZXSchedule) -> dict[str, Any]:
        """The self-describing run header (§6): every field needed to reproduce + decode.

        ``out_stride`` (the packed bytes/shot) matches Agent K's kernel return
        (``ceil(R*n_stab/8) + 1``: the syndrome bytes + the trailing logical-flip byte).
        """
        bits = self.syndrome_bits_per_shot(marsh.n_stab, marsh.R)
        header = {
            "format": "p4a_sv_mc_shots/v1",
            "n_data": marsh.n_data,
            "n_stab": marsh.n_stab,
            "R": marsh.R,
            "N": int(spec.N),
            "m": int(spec.m),
            "arm": str(spec.arm).upper(),
            "arm_code": SV_ARM_CODE[str(spec.arm).upper()],
            "b": float(spec.b),
            "readout_conv": str(spec.readout_conv),
            "readout_conv_code": SV_READOUT_CODE[str(spec.readout_conv)],
            "theta": float(spec.theta),
            "g_seep": float(spec.g_seep),
            "g_heat": float(spec.g_heat),
            "base_seed": int(spec.base_seed),
            "wave": int(spec.W),
            "dtype": str(spec.dtype),
            "logical_kind": str(sched.logical_kind).upper(),
            "logical_support": [int(x) for x in marsh.log_supp.tolist()],
            "syndrome_bits_per_shot": bits,
            "out_stride_bytes": (bits + 7) // 8 + 1,
            "syndrome_layout": "shot_major: shot_id outer, then round, then stab (round-major, "
                               "LSB-first packbits); logical_flip in the trailing byte (value 0/1)",
            "git_commit": _git_commit(),
            "source_circuit": str(spec.circuit_path),
            "gate_ids": dict(SV_GATE_IDS),
        }
        if spec.numerical_provenance is not None:
            header["numerical_provenance"] = spec.numerical_provenance
        return header

    @staticmethod
    def pack_shots(syndromes: np.ndarray, logical_flips: np.ndarray) -> np.ndarray:
        """Pack ``(N, n_stab*R)`` syndrome bits + ``(N,)`` logical-flip bits → shot-major uint8.

        Matches Agent K's kernel buffer format EXACTLY (so the host shim and the kernel emit an
        identical layout; V decodes either from the header alone): per shot, the ``n_stab*R``
        syndrome bits (shot-major: round outer, then stab — round-major) packed **LSB-first**
        within each byte into ``ceil(bits/8)`` bytes, then the ``logical_flip`` as the trailing
        byte holding the raw VALUE 0/1 (NOT bit-packed). ``out_stride = ceil(bits/8) + 1``.
        ``syndromes`` / ``logical_flips`` are ``{0,1}`` int arrays.

        LSB-FIRST (``bitorder='little'``) is MANDATORY: the CUDA kernel packs bit ``bitpos`` as
        the ``(bitpos & 7)``-th LEAST-significant bit of its byte (``out_bits[...] |= 1u << off``,
        ``sv_traj_d3.cu``). numpy ``packbits`` defaults to MSB-first, which would scramble the
        syndrome bits within each byte when decoding the kernel buffer (verified: 0/32 shots
        decode MSB-first, 32/32 LSB-first — ``p4a_gate_bug_bitorder.py``). The §6 header text is
        kept in lock-step ("LSB-first").
        """
        syndromes = np.ascontiguousarray(syndromes).astype(np.uint8)
        logical_flips = np.ascontiguousarray(logical_flips).astype(np.uint8)
        n = syndromes.shape[0]
        if logical_flips.shape[0] != n:
            raise ValueError(f"shot-count mismatch: {n} syndromes vs {logical_flips.shape[0]} flips")
        syn_packed = np.packbits(syndromes, axis=1, bitorder="little")  # (N, ceil(bits/8)) LSB-first
        flip_byte = logical_flips[:, None]                         # (N, 1) raw value 0/1
        return np.concatenate([syn_packed, flip_byte], axis=1)     # (N, ceil(bits/8)+1)

    @staticmethod
    def unpack_shots(packed: np.ndarray, n_stab: int, R: int) -> tuple[np.ndarray, np.ndarray]:
        """Inverse of :meth:`pack_shots` (and K's kernel buffer): →
        ``(syndromes (N, n_stab*R), logical_flips (N,))``. Syndrome bits are unpacked
        **LSB-first** (``bitorder='little'``) to match the kernel's within-byte packing (see
        :meth:`pack_shots`); the trailing byte is the raw flip VALUE 0/1 (per K's format), so it
        is read directly, not bit-unpacked."""
        bits = int(n_stab) * int(R)
        syn_bytes = (bits + 7) // 8
        syn = np.unpackbits(packed[:, :syn_bytes], axis=1, bitorder="little")[:, :bits]
        flip = packed[:, syn_bytes].astype(np.uint8)  # trailing byte = raw 0/1 value
        return syn.astype(np.uint8), flip

    # ----------------------------------------------------------------------- #
    # (5)/(7) the wave loop + kernel call                                      #
    # ----------------------------------------------------------------------- #
    def sample(self, spec: RunSpec, *, materialize: bool = True,
               urandom: torch.Tensor | None = None, urandom_stride: int = 0) -> ShotSet:
        """Run a full P4a sampling job: parse → marshal → Kraus → codestate → kernel → I/O.

        Calls Agent K's ``sv_traj_d3`` loader once with the §7 marshalled arrays; the KERNEL
        tiles the ``N`` shots into waves of ``≤ W`` blocks internally (the ``wave`` arg), so
        the host does not allocate all ``N`` states. GPU-only compute; the packed shot buffer
        is streamed to disk host-side (allowed, §6). ``urandom`` (optional) is the §9
        bit-faithful host-pre-generated stream passed straight through to the kernel.

        If Agent K's kernel is not on disk / will not JIT for ``dtype``, this raises a clear
        'kernel not available' error AFTER the codestate/marshalling/CPTP checks pass (so the
        host preconditions are still validated) — never a silent CPU fallback (GPU-only model
        compute, binding).
        """
        if not torch.cuda.is_available():
            raise RuntimeError("GPU-only contract: CUDA must be available for the P4a SV-MC engine")

        sched = self.parse(spec)
        marsh = self.marshal_schedule(sched, R=spec.R)
        kraus = self.build_leakage_kraus(spec)
        codestate, code_evidence = self.build_codestate(sched, spec.m)
        # the kernel's c64 build needs a complex64 codestate; c128 needs complex128.
        if str(spec.dtype) == "c64":
            codestate = codestate.to(torch.complex64)
            kraus = kraus.to(torch.complex64)
            marsh = self._cast_unitaries(marsh, torch.complex64)
            # the c64 kernel reads urandom via const_data_ptr<float>() — a float64 stream would
            # throw a dtype error. Cast the bit-faithful urandom stream to float32 to match
            # (FIX-3; the float64 c128 path passes a float64 stream, unchanged).
            if urandom is not None:
                urandom = urandom.to(torch.float32)
        header = self.build_header(spec, marsh, sched)
        header["codestate_check"] = code_evidence

        kfn = _load_sv_traj_kernel(str(spec.dtype))
        if kfn is None:
            raise RuntimeError(
                "sv_traj_d3 kernel not available (Agent K's "
                "qec_twin.forward.kernels.sv_traj_d3_loader not importable / will not JIT for "
                f"dtype={spec.dtype!r}). Host marshalling / codestate / CPTP checks PASSED; the "
                "production sample() awaits the kernel. (No CPU fallback — GPU-only model compute.)")

        n_stab, R = marsh.n_stab, marsh.R
        bits = self.syndrome_bits_per_shot(n_stab, R)

        packed_t, norm_drift_t = kfn(
            codestate=codestate,
            R=R,
            round_gptr=marsh.round_gptr,
            gate_uid=marsh.gate_uid,
            gate_site=marsh.gate_site,
            gate_unitaries=marsh.gate_unitaries,
            stab_supp_len=marsh.stab_supp_len,
            stab_supp=marsh.stab_supp,
            stab_supp_isx=marsh.stab_supp_isx,
            kraus=kraus,
            log_supp=marsh.log_supp,
            log_supp_isx=marsh.log_supp_isx,
            arm=SV_ARM_CODE[str(spec.arm).upper()],
            b=float(spec.b),
            readout_conv=SV_READOUT_CODE[str(spec.readout_conv)],
            logical_m=int(spec.m),
            N=int(spec.N),
            base_seed=int(spec.base_seed),
            shot_id_offset=0,
            wave=int(spec.W),
            urandom=urandom,
            urandom_stride=int(urandom_stride),
            dtype=str(spec.dtype),
        )

        packed = packed_t.detach().cpu().numpy()
        if packed.dtype != np.uint8:
            raise TypeError(f"kernel packed buffer must be uint8 (got {packed.dtype})")
        out_stride = (bits + 7) // 8 + 1
        if packed.ndim != 2 or packed.shape != (int(spec.N), out_stride):
            raise AssertionError(
                f"kernel buffer shape {packed.shape} != expected {(int(spec.N), out_stride)}")
        norm_drift = norm_drift_t.detach().cpu().numpy().astype(np.float64)

        out_path = Path(spec.out_path) if spec.out_path is not None else None
        header_path = None
        if out_path is not None:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            header_path = out_path.with_suffix(out_path.suffix + ".header.json")
            header_path.write_text(json.dumps(header, indent=2))
            with open(out_path, "wb") as fh:
                fh.write(np.ascontiguousarray(packed).tobytes())

        diag = {
            "mean_norm_drift": float(np.mean(norm_drift)) if norm_drift.size else 0.0,
            "max_norm_drift": float(np.max(norm_drift)) if norm_drift.size else 0.0,
        }
        return ShotSet(
            header=header,
            path=out_path,
            header_path=header_path,
            n_shots=int(spec.N),
            syndrome_bits_per_shot=bits,
            diag=diag,
            shots=(packed if materialize else None),
        )

    @staticmethod
    def _cast_unitaries(marsh: MarshalledSchedule, dtype) -> MarshalledSchedule:
        """Return a copy of ``marsh`` with ``gate_unitaries`` cast to ``dtype`` (c64 build)."""
        from dataclasses import replace
        return replace(marsh, gate_unitaries=marsh.gate_unitaries.to(dtype))


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _git_commit() -> str:
    """The short git commit for the run header (§6 reproducibility); '' if unavailable."""
    try:
        root = Path(__file__).resolve().parents[4]
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(root),
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""
