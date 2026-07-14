"""Loader for the P4a state-vector MCWF trajectory kernel (``sv_traj_d3.cu``).

JIT-compiles and binds the block-per-trajectory leakage kernel and exposes the
§7 host↔kernel signatures.  TWO entry points share one compiled module:

* :func:`sv_traj_d3` — the LUMPED per-round model (``[all gates] -> [ONE full-cycle
  leak] -> [measure]``; the §7 gate-CSR signature).
* :func:`sv_traj_d3_wc` — the circuit-faithful WITHIN-CYCLE op-schedule (Agent H's
  ``WithinCycleMarshalled`` CSR: per round, interleaved per-qutrit gate+``exp(L/4)``
  LEAK ops -> measure (UNCHANGED) -> post-M ``Y``; model
  ``docs/nonpauli_teacher/p4a_within_cycle_model.md``).

Mirrors the compile/load style of :mod:`error_coupling_simulator.carrier.accel`
(``torch.utils.cpp_extension.load`` with nvcc from ``/usr/local/cuda``;
``QEC_TWIN_NO_KERNELS=1`` disables; GPU-only — no CPU compute fallback in the
trajectory path).

Two precision builds are compiled lazily and cached separately, selected by the
``dtype`` arg of :func:`sv_traj_d3`:

* ``c128`` (default, ``-DSV_REAL=double``) — the precision-first build; the
  state vector is ``complex128`` (315 KB/shot in global).
* ``c64`` (opt-in, ``-DSV_REAL=float``) — an optimization/screening build.  Its
  outputs are not final evidence and require confirmation by the default c128
  engine.  Compiled on demand the first time it is requested.

The active host API is
``error_coupling_simulator.carrier.within_cycle.FusedWithinCycleSampler`` and calls
:func:`sv_traj_d3_wc` explicitly.  The lumped entry point is retained only for
legacy compatibility.  This module is the pure compile/bind boundary — it builds no
schedule and reads no disk.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import torch

_log = logging.getLogger(__name__)

# JIT extension handles, cached per precision.
_EXT: dict[str, object] = {}
_EXT_TRIED: dict[str, bool] = {}

_SV_DIM = 3 ** 9
_MAX_STAB = 16
_MAX_SUPP = 8
_MAX_KRAUS = 8
_MAX_LOG_SUPP = 12
_PRECISION_DTYPES = {
    "c128": (torch.complex128, torch.float64),
    "c64": (torch.complex64, torch.float32),
}


def _precision_dtypes(precision: str) -> tuple[torch.dtype, torch.dtype]:
    try:
        return _PRECISION_DTYPES[precision]
    except KeyError as exc:
        raise ValueError(
            f"precision must be 'c128' or 'c64' (got {precision!r})"
        ) from exc


def _require_tensor(name: str, value: object) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor")
    return value


def _require_dtype(
    name: str, tensor: torch.Tensor, expected: torch.dtype,
) -> None:
    if tensor.dtype != expected:
        raise TypeError(
            f"{name} must have dtype {expected} (got {tensor.dtype})")


def _require_1d(name: str, tensor: torch.Tensor) -> None:
    if tensor.ndim != 1:
        raise ValueError(f"{name} must be 1D (got shape {tuple(tensor.shape)})")


def _require_complex_stack(
    name: str,
    tensor: torch.Tensor,
    expected: torch.dtype,
) -> None:
    _require_dtype(name, tensor, expected)
    if (
        tensor.ndim != 3
        or tensor.shape[0] < 1
        or tuple(tensor.shape[1:]) != (3, 3)
    ):
        raise ValueError(
            f"{name} must have shape [K, 3, 3] with K >= 1 "
            f"(got {tuple(tensor.shape)})")


def _require_cuda_same_device(
    name: str, tensor: torch.Tensor, reference: torch.Tensor,
) -> None:
    if not tensor.is_cuda:
        raise RuntimeError(f"{name} must be CUDA")
    if tensor.device != reference.device:
        raise RuntimeError(
            f"{name} must be on {reference.device} (got {tensor.device})")


def _require_host_copyable_index(
    name: str,
    tensor: torch.Tensor,
    reference: torch.Tensor | None = None,
) -> None:
    if tensor.device.type not in ("cpu", "cuda"):
        raise RuntimeError(f"{name} must be CPU or CUDA (got {tensor.device})")
    if (
        reference is not None
        and tensor.is_cuda
        and tensor.device != reference.device
    ):
        raise RuntimeError(
            f"{name} must be CPU or on {reference.device} (got {tensor.device})")


def _int_values(tensor: torch.Tensor) -> list[int]:
    return [int(value) for value in tensor.detach().cpu().reshape(-1).tolist()]


def _validate_csr(name: str, ptr: torch.Tensor, item_count: int) -> None:
    values = _int_values(ptr)
    if not values or values[0] != 0:
        raise ValueError(f"{name} must start at 0")
    if any(left > right for left, right in zip(values, values[1:])):
        raise ValueError(f"{name} must be nondecreasing")
    if values[-1] != item_count:
        raise ValueError(
            f"{name} terminal entry must equal item count {item_count} "
            f"(got {values[-1]})")


def _validate_support_tables(
    *,
    stab_supp_len: torch.Tensor,
    stab_supp: torch.Tensor,
    stab_supp_isx: torch.Tensor,
    log_supp: torch.Tensor,
    log_supp_isx: torch.Tensor,
    codestate: torch.Tensor | None = None,
) -> None:
    named = {
        "stab_supp_len": stab_supp_len,
        "stab_supp": stab_supp,
        "stab_supp_isx": stab_supp_isx,
        "log_supp": log_supp,
        "log_supp_isx": log_supp_isx,
    }
    for name, tensor in named.items():
        _require_tensor(name, tensor)
        _require_dtype(name, tensor, torch.int32)
        _require_host_copyable_index(name, tensor, codestate)

    _require_1d("stab_supp_len", stab_supp_len)
    n_stab = stab_supp_len.numel()
    if n_stab > _MAX_STAB:
        raise ValueError(
            f"stab_supp_len has {n_stab} stabilizers; maximum is {_MAX_STAB}")
    if stab_supp.ndim != 2:
        raise ValueError(
            f"stab_supp must be 2D (got shape {tuple(stab_supp.shape)})")
    if stab_supp.shape[0] != n_stab or stab_supp.shape[1] > _MAX_SUPP:
        raise ValueError(
            "stab_supp must have shape [n_stab, K] with "
            f"K <= {_MAX_SUPP} (got {tuple(stab_supp.shape)})")
    if stab_supp_isx.shape != stab_supp.shape:
        raise ValueError(
            "stab_supp_isx shape must equal stab_supp shape "
            f"(got {tuple(stab_supp_isx.shape)} vs {tuple(stab_supp.shape)})")

    _require_1d("log_supp", log_supp)
    if log_supp.numel() > _MAX_LOG_SUPP:
        raise ValueError(
            f"log_supp has {log_supp.numel()} sites; maximum is {_MAX_LOG_SUPP}")
    if log_supp_isx.shape != log_supp.shape:
        raise ValueError(
            "log_supp_isx shape must equal log_supp shape "
            f"(got {tuple(log_supp_isx.shape)} vs {tuple(log_supp.shape)})")

    lengths = _int_values(stab_supp_len)
    sites = stab_supp.detach().cpu().tolist()
    flags = stab_supp_isx.detach().cpu().tolist()
    width = int(stab_supp.shape[1])
    for stab_index, support_len in enumerate(lengths):
        if not 0 <= support_len <= width:
            raise ValueError(
                f"stab_supp_len[{stab_index}]={support_len} is outside [0,{width}]")
        for offset in range(support_len):
            site = int(sites[stab_index][offset])
            is_x = int(flags[stab_index][offset])
            if not 0 <= site < 9:
                raise ValueError(
                    f"stab_supp[{stab_index},{offset}]={site} is outside [0,9)")
            if is_x not in (0, 1):
                raise ValueError(
                    f"stab_supp_isx[{stab_index},{offset}] must be 0 or 1")
    for offset, (site, is_x) in enumerate(zip(
        _int_values(log_supp), _int_values(log_supp_isx), strict=True,
    )):
        if not 0 <= site < 9:
            raise ValueError(f"log_supp[{offset}]={site} is outside [0,9)")
        if is_x not in (0, 1):
            raise ValueError(f"log_supp_isx[{offset}] must be 0 or 1")


def _validate_urandom(
    urandom: torch.Tensor | None,
    *,
    expected_dtype: torch.dtype,
    codestate: torch.Tensor,
    N: int,
    urandom_stride: int,
) -> None:
    if urandom is None:
        return
    _require_tensor("urandom", urandom)
    if urandom.numel() == 0:
        return
    _require_dtype("urandom", urandom, expected_dtype)
    if (
        urandom.ndim != 2
        or urandom.shape[0] != N
        or urandom_stride <= 0
        or urandom.shape[1] != urandom_stride
    ):
        raise ValueError(
            "urandom must have shape [N, urandom_stride] with "
            f"urandom_stride > 0 (got {tuple(urandom.shape)}, "
            f"N={N}, urandom_stride={urandom_stride})")
    _require_cuda_same_device("urandom", urandom, codestate)


def _validate_shared_inputs(
    *,
    precision: str,
    codestate: torch.Tensor,
    R: int,
    N: int,
    arm: int,
    b: float,
    readout_conv: int,
    logical_m: int,
    shot_id_offset: int,
    wave: int,
    gate_unitaries: torch.Tensor,
    kraus_name: str,
    kraus: torch.Tensor,
    stab_supp_len: torch.Tensor,
    stab_supp: torch.Tensor,
    stab_supp_isx: torch.Tensor,
    log_supp: torch.Tensor,
    log_supp_isx: torch.Tensor,
    urandom: torch.Tensor | None,
    urandom_stride: int,
) -> tuple[torch.dtype, torch.dtype]:
    expected_complex, expected_real = _precision_dtypes(precision)
    _require_tensor("codestate", codestate)
    _require_dtype("codestate", codestate, expected_complex)
    if codestate.ndim != 1 or codestate.numel() != _SV_DIM:
        raise ValueError(
            f"codestate must have shape [{_SV_DIM}] (got {tuple(codestate.shape)})")
    if int(R) < 1:
        raise ValueError(f"R must be >= 1 (got {R})")
    if int(N) < 1:
        raise ValueError(f"N must be >= 1 (got {N})")
    if int(arm) not in (0, 1, 2, 3):
        raise ValueError(f"arm must be in {{0,1,2,3}} (got {arm})")
    if not 0.0 <= float(b) <= 1.0:
        raise ValueError(f"b must be in [0,1] (got {b})")
    if int(readout_conv) not in (0, 1):
        raise ValueError(
            f"readout_conv must be 0 or 1 (got {readout_conv})")
    if int(logical_m) not in (0, 1):
        raise ValueError(f"logical_m must be 0 or 1 (got {logical_m})")
    if int(shot_id_offset) < 0:
        raise ValueError(
            f"shot_id_offset must be >= 0 (got {shot_id_offset})")
    if int(wave) < 1:
        raise ValueError(f"wave must be >= 1 (got {wave})")

    _require_tensor("gate_unitaries", gate_unitaries)
    _require_complex_stack("gate_unitaries", gate_unitaries, expected_complex)
    _require_tensor(kraus_name, kraus)
    _require_complex_stack(kraus_name, kraus, expected_complex)
    if kraus.shape[0] > _MAX_KRAUS:
        raise ValueError(
            f"{kraus_name} has {kraus.shape[0]} operators; maximum is {_MAX_KRAUS}")
    _validate_support_tables(
        stab_supp_len=stab_supp_len,
        stab_supp=stab_supp,
        stab_supp_isx=stab_supp_isx,
        log_supp=log_supp,
        log_supp_isx=log_supp_isx,
        codestate=codestate,
    )

    _validate_urandom(
        urandom,
        expected_dtype=expected_real,
        codestate=codestate,
        N=int(N),
        urandom_stride=int(urandom_stride),
    )
    _require_cuda_same_device("codestate", codestate, codestate)
    _require_cuda_same_device("gate_unitaries", gate_unitaries, codestate)
    _require_cuda_same_device(kraus_name, kraus, codestate)
    return expected_complex, expected_real


def _validate_lumped_schedule_structure(
    *,
    R: int,
    round_gptr: torch.Tensor,
    gate_uid: torch.Tensor,
    gate_site: torch.Tensor,
) -> None:
    for name, tensor in {
        "round_gptr": round_gptr,
        "gate_uid": gate_uid,
        "gate_site": gate_site,
    }.items():
        _require_tensor(name, tensor)
        _require_dtype(name, tensor, torch.int32)
        _require_1d(name, tensor)
    if round_gptr.numel() != int(R) + 1:
        raise ValueError(
            f"round_gptr must have shape [R+1] (got {tuple(round_gptr.shape)}, R={R})")
    if gate_uid.numel() != gate_site.numel():
        raise ValueError(
            "gate_uid and gate_site must have equal length "
            f"(got {gate_uid.numel()} and {gate_site.numel()})")


def _validate_lumped_schedule_values(
    *,
    round_gptr: torch.Tensor,
    gate_uid: torch.Tensor,
    gate_site: torch.Tensor,
    n_gate: int,
) -> None:
    _validate_csr("round_gptr", round_gptr, gate_uid.numel())
    for offset, (uid, site) in enumerate(zip(
        _int_values(gate_uid), _int_values(gate_site), strict=True,
    )):
        if not 0 <= uid < n_gate:
            raise ValueError(
                f"gate_uid[{offset}]={uid} is outside [0,{n_gate})")
        if not 0 <= site < 9:
            raise ValueError(
                f"gate_site[{offset}]={site} is outside [0,9)")


def _validate_wc_schedule_structure(
    *,
    R: int,
    round_op_ptr: torch.Tensor,
    op_kind: torch.Tensor,
    op_uid: torch.Tensor,
    op_site: torch.Tensor,
) -> None:
    for name, tensor in {
        "round_op_ptr": round_op_ptr,
        "op_kind": op_kind,
        "op_uid": op_uid,
        "op_site": op_site,
    }.items():
        _require_tensor(name, tensor)
        _require_dtype(name, tensor, torch.int32)
        _require_1d(name, tensor)
    if round_op_ptr.numel() != 2 * int(R) + 1:
        raise ValueError(
            "round_op_ptr must have shape [2R+1] "
            f"(got {tuple(round_op_ptr.shape)}, R={R})")
    if not (op_kind.numel() == op_uid.numel() == op_site.numel()):
        raise ValueError(
            "op_kind, op_uid, and op_site must have equal length "
            f"(got {op_kind.numel()}, {op_uid.numel()}, {op_site.numel()})")


def _validate_wc_schedule_values(
    *,
    round_op_ptr: torch.Tensor,
    op_kind: torch.Tensor,
    op_uid: torch.Tensor,
    op_site: torch.Tensor,
    n_gate: int,
) -> None:
    _validate_csr("round_op_ptr", round_op_ptr, op_kind.numel())
    for offset, (kind, uid, site) in enumerate(zip(
        _int_values(op_kind),
        _int_values(op_uid),
        _int_values(op_site),
        strict=True,
    )):
        if kind not in (0, 1):
            raise ValueError(f"op_kind[{offset}] must be 0 or 1 (got {kind})")
        if kind == 0 and not 0 <= uid < n_gate:
            raise ValueError(f"op_uid[{offset}]={uid} is outside [0,{n_gate})")
        if not 0 <= site < 9:
            raise ValueError(f"op_site[{offset}]={site} is outside [0,9)")


def _validate_schedule_devices(
    codestate: torch.Tensor, **tensors: torch.Tensor,
) -> None:
    for name, tensor in tensors.items():
        _require_cuda_same_device(name, tensor, codestate)


def _kernels_dir() -> Path:
    return Path(__file__).resolve().parent


def _load_ext(precision: str = "c128"):
    """JIT-load (or fetch the cached) extension for ``precision`` in {c128, c64}.

    Returns the bound module exposing ``sv_traj_d3``, or ``None`` on the CLEAN
    "kernel disabled / CUDA absent / source missing" path (``QEC_TWIN_NO_KERNELS=1``,
    no CUDA device, or no ``.cu`` source).  A GENUINE compile failure (nvcc/ninja
    present but the build errors) is NOT swallowed: the underlying exception is
    logged and re-raised with context so a misconfigured toolchain surfaces the real
    nvcc/ninja error instead of masquerading as "kernel unavailable" (GPU-only rule —
    a silent ``None`` there would hide a broken build).  The two precisions are
    SEPARATE compiled modules (distinct ``name=``) so they coexist.
    """
    if precision not in ("c128", "c64"):
        raise ValueError(f"precision must be 'c128' or 'c64' (got {precision!r})")
    if _EXT_TRIED.get(precision):
        return _EXT.get(precision)
    _EXT_TRIED[precision] = True
    # CLEAN unavailable paths (no compile attempted) -> None, no error.
    if os.environ.get("QEC_TWIN_NO_KERNELS") == "1" or not torch.cuda.is_available():
        return None
    src = _kernels_dir() / "sv_traj_d3.cu"
    if not src.exists():
        return None
    real = "double" if precision == "c128" else "float"
    try:
        from torch.utils.cpp_extension import load

        ext = load(
            name=f"qec_twin_sv_traj_{precision}",
            sources=[str(src)],
            extra_cuda_cflags=["-O3", f"-DSV_REAL={real}"],
            verbose=False,
        )
    except Exception as exc:
        # A real compile/link failure (CUDA IS present and the source exists): do
        # NOT mask it as "unavailable".  Cache the failure so we don't recompile on
        # every call, log the full traceback, and re-raise with context.
        _EXT[precision] = None
        _log.error(
            "sv_traj_d3 (%s) FAILED to JIT-compile (nvcc/ninja toolchain present, "
            "source exists) — this is a genuine build error, not 'CUDA absent'.",
            precision,
            exc_info=True,
        )
        raise RuntimeError(
            f"sv_traj_d3 kernel ({precision}) failed to compile (CUDA present, "
            f"source {src} exists). Surface the underlying nvcc/ninja error above; "
            f"set QEC_TWIN_NO_KERNELS=1 only to intentionally disable the kernel."
        ) from exc
    _EXT[precision] = ext
    return ext


def available(precision: str = "c128") -> bool:
    """True iff the kernel for ``precision`` JIT-loads on this machine.

    Returns ``False`` on the CLEAN unavailable paths (``QEC_TWIN_NO_KERNELS=1``, no
    CUDA device, or no ``.cu`` source).  A GENUINE compile failure (CUDA present, the
    build errors) RAISES ``RuntimeError`` (from :func:`_load_ext`) rather than
    reporting ``False`` — a broken toolchain must not look like "kernel absent".
    """
    return _load_ext(precision) is not None


# Argument order the kernel binding expects (kept in lock-step with the
# PYBIND11 ``sv_traj_d3`` C++ signature in sv_traj_d3.cu).
def sv_traj_d3(
    *,
    codestate: torch.Tensor,
    R: int,
    round_gptr: torch.Tensor,
    gate_uid: torch.Tensor,
    gate_site: torch.Tensor,
    gate_unitaries: torch.Tensor,
    stab_supp_len: torch.Tensor,
    stab_supp: torch.Tensor,
    stab_supp_isx: torch.Tensor,
    kraus: torch.Tensor,
    log_supp: torch.Tensor,
    log_supp_isx: torch.Tensor,
    arm: int,
    b: float,
    readout_conv: int,
    logical_m: int,
    N: int,
    base_seed: int,
    shot_id_offset: int = 0,
    wave: int = 256,
    urandom: torch.Tensor | None = None,
    urandom_stride: int = 0,
    dtype: str = "c128",
) -> tuple[torch.Tensor, torch.Tensor]:
    """Run the P4a MCWF trajectory sampler (§7 host↔kernel call).

    State, gate/Kraus, schedule-CSR, and nonempty RNG tensors must be CUDA tensors
    on the codestate device.  The small support/logical int32 tables may instead
    be CPU tensors because the launcher copies them into its POD before launch.
    The return is ``(packed_shot_bits, norm_drift)``:

    * ``packed_shot_bits`` — ``uint8`` ``[N, out_stride]`` shot-major bit-array
      (§6): per shot, ``R*n_stab`` syndrome bits packed (round-major, then stab),
      then the ``logical_flip`` in the trailing byte (the byte right after the
      syndrome bits; value 0/1).  ``out_stride = ceil(R*n_stab/8) + 1``.
    * ``norm_drift`` — real ``[N]`` diagnostic: ``|1 - <psi|psi>|`` just before the
      terminal readout per shot (the mean over shots is the §7 ``mean_norm_drift``).

    Marshalling contract (§2/§3/§4/§5/§8) — Agent H supplies:

    * ``codestate`` complex ``[3^9]`` — the ``|m>_L`` pure state vector (qutrit 0 =
      most-significant trit), prepared per §8.  dtype must match ``dtype``
      (complex128 for c128, complex64 for c64).
    * ``round_gptr`` int32 ``[R+1]`` — CSR offsets into ``(gate_uid, gate_site)``;
      round ``r``'s gates are indices ``[round_gptr[r], round_gptr[r+1])``.
    * ``gate_uid`` / ``gate_site`` int32 ``[G]`` — per gate-apply, the unitary index
      (into ``gate_unitaries``) and the data-qutrit site.
    * ``gate_unitaries`` complex ``[n_gate, 3, 3]`` — the qutrit gate matrices used.
    * ``stab_supp_len`` int32 ``[n_stab]``; ``stab_supp`` / ``stab_supp_isx`` int32
      ``[n_stab, K]`` — per stabilizer, the support data-qutrit indices and a 0/1
      flag marking X-type support sites (Hadamard-rotated to Z before the diagonal
      measurement).  In schedule order.
    * ``kraus`` complex ``[n_kraus, 3, 3]`` — the WG leakage channel Kraus stack
      (CPTP, asserted host-side).
    * ``log_supp`` / ``log_supp_isx`` int32 ``[L]`` — the logical observable support
      + X-type flags (for the terminal readout parity).
    * ``arm`` in {0:A, 1:C, 2:B1, 3:B2}; ``b`` the leaked-readout bias (A/C);
      ``readout_conv`` in {0:biased_b, 1:half} (the terminal leaked convention);
      ``logical_m`` the prepared logical value (XORed into ``logical_flip``).
    * ``N`` total shots; ``base_seed`` + ``shot_id_offset`` the §5 RNG key
      (per-shot stream = ``hash(base_seed, shot_id_offset + i)``); ``wave`` the
      blocks-per-wave width (Gate-5 micro-bench).
    * ``urandom`` (optional) real ``[N, urandom_stride]`` host-pre-generated uniform
      stream consumed in the §5 NORMATIVE order — the §9 bit-faithful test path.
      When ``None`` (or empty) the kernel uses curand keyed by the §5 hash.
    * ``dtype`` in {"c128", "c64"} selects the compiled precision build.

    Raises ``RuntimeError`` if the kernel is unavailable for ``dtype`` (no CUDA /
    no nvcc / ``QEC_TWIN_NO_KERNELS=1``) — there is no CPU fallback (GPU-only rule).
    """
    _precision_dtypes(dtype)
    _validate_lumped_schedule_structure(
        R=R,
        round_gptr=round_gptr,
        gate_uid=gate_uid,
        gate_site=gate_site,
    )
    _validate_shared_inputs(
        precision=dtype,
        codestate=codestate,
        R=R,
        N=N,
        arm=arm,
        b=b,
        readout_conv=readout_conv,
        logical_m=logical_m,
        shot_id_offset=shot_id_offset,
        wave=wave,
        gate_unitaries=gate_unitaries,
        kraus_name="kraus",
        kraus=kraus,
        stab_supp_len=stab_supp_len,
        stab_supp=stab_supp,
        stab_supp_isx=stab_supp_isx,
        log_supp=log_supp,
        log_supp_isx=log_supp_isx,
        urandom=urandom,
        urandom_stride=urandom_stride,
    )
    _validate_schedule_devices(
        codestate,
        round_gptr=round_gptr,
        gate_uid=gate_uid,
        gate_site=gate_site,
    )
    _validate_lumped_schedule_values(
        round_gptr=round_gptr,
        gate_uid=gate_uid,
        gate_site=gate_site,
        n_gate=int(gate_unitaries.shape[0]),
    )
    ext = _load_ext(dtype)
    if ext is None:
        raise RuntimeError(
            f"sv_traj_d3 kernel ({dtype}) unavailable: needs CUDA + nvcc and "
            f"QEC_TWIN_NO_KERNELS unset (GPU-only, no CPU fallback)."
        )
    if urandom is None:
        urandom = torch.empty(0, dtype=codestate.real.dtype, device=codestate.device)
    return ext.sv_traj_d3(
        codestate,
        int(R),
        round_gptr,
        gate_uid,
        gate_site,
        gate_unitaries,
        stab_supp_len,
        stab_supp,
        stab_supp_isx,
        kraus,
        log_supp,
        log_supp_isx,
        int(arm),
        float(b),
        int(readout_conv),
        int(logical_m),
        int(N),
        int(base_seed),
        int(shot_id_offset),
        int(wave),
        urandom,
        int(urandom_stride),
    )


# Argument order the within-cycle kernel binding expects (kept in lock-step with
# the PYBIND11 ``sv_traj_d3_wc`` C++ signature in sv_traj_d3.cu).
def sv_traj_d3_wc(
    *,
    codestate: torch.Tensor,
    R: int,
    round_op_ptr: torch.Tensor,
    op_kind: torch.Tensor,
    op_uid: torch.Tensor,
    op_site: torch.Tensor,
    gate_unitaries: torch.Tensor,
    stab_supp_len: torch.Tensor,
    stab_supp: torch.Tensor,
    stab_supp_isx: torch.Tensor,
    leak_kraus: torch.Tensor,
    log_supp: torch.Tensor,
    log_supp_isx: torch.Tensor,
    arm: int,
    b: float,
    readout_conv: int,
    logical_m: int,
    N: int,
    base_seed: int,
    shot_id_offset: int = 0,
    wave: int = 256,
    urandom: torch.Tensor | None = None,
    urandom_stride: int = 0,
    dtype: str = "c128",
) -> tuple[torch.Tensor, torch.Tensor]:
    """Run the P4a WITHIN-CYCLE MCWF trajectory sampler (model
    ``p4a_within_cycle_model.md``; Agent H's ``WithinCycleMarshalled`` CSR).

    The circuit-faithful replacement for :func:`sv_traj_d3`'s LUMPED per-round
    body ``[all gates] -> [ONE full-cycle leak] -> [measure]``.  Per round the
    kernel walks the per-qutrit interleaved op-schedule, measures the 8
    stabilizers (UNCHANGED — ``stab_supp_isx`` X-support rotation kept), then
    applies the post-M ops (the transversal ``Y``, dropped on the terminal
    round).  The MEASUREMENT IS UNCHANGED from :func:`sv_traj_d3`; only the
    per-round op-schedule and the per-CZ ``exp(L/4)`` leak change.

    Marshalling contract (Agent H's :class:`WithinCycleMarshalled`):

    * ``codestate`` complex ``[3^9]`` — ``|m>_L`` (§8), dtype matching ``dtype``.
    * ``round_op_ptr`` int32 ``[2R+1]`` — CSR row-pointer with TWO segments per
      round: round ``r``'s PRE-measure ops are indices
      ``[round_op_ptr[2r], round_op_ptr[2r+1])`` and its POST-measure ops are
      ``[round_op_ptr[2r+1], round_op_ptr[2r+2])``.
    * ``op_kind`` / ``op_uid`` / ``op_site`` int32 ``[T]`` — per op, the kind
      (``WC_OP_GATE=0`` ⇒ apply ``gate_unitaries[op_uid]`` on ``op_site``;
      ``WC_OP_LEAK=1`` ⇒ Kraus-sample ``leak_kraus`` on ``op_site``, ``op_uid``
      unused), and the data-qutrit site.  Serialized per qutrit in
      engine-position order within each segment.
    * ``gate_unitaries`` complex ``[n_gate, 3, 3]`` — the qutrit gate matrices.
    * ``leak_kraus`` complex ``[n_kraus, 3, 3]`` — the per-CZ leak slice
      ``exp(L/4)`` (NOT the full-cycle ``exp(L)``); applied once per ``WC_OP_LEAK``
      op, so a qutrit in ``n_cz`` CZ layers leaks ``exp(L·n_cz/4)``.  CPTP +
      composition asserted host-side.
    * ``stab_supp_len`` / ``stab_supp`` / ``stab_supp_isx`` / ``log_supp`` /
      ``log_supp_isx`` / ``arm`` / ``b`` / ``readout_conv`` / ``logical_m`` /
      ``N`` / ``base_seed`` / ``shot_id_offset`` / ``wave`` / ``urandom`` /
      ``dtype`` — EXACTLY as :func:`sv_traj_d3` (the measurement + instrument +
      RNG + I/O are unchanged).

    §5 RNG draw order (updated for the op-schedule): one uniform per categorical
    draw, in op-schedule order — each ``WC_OP_LEAK`` op's Kraus draw as the
    pre-segment is walked, then each stabilizer's measurement draw(s), then (after
    round ``R``) the 9 terminal-readout draws.  ``WC_OP_GATE`` ops draw nothing.
    ``urandom_stride ≥ R·(n_leak_per_round + Σ_s (supp_len_s + 1)) + 9`` for Arm C
    (``R·(n_leak_per_round + n_stab) + 9`` for A/B1/B2), where
    ``n_leak_per_round = Σ_q n_cz_q`` (the total LEAK ops per round).

    Returns ``(packed_shot_bits, norm_drift)`` — same ``[N, out_stride]`` uint8
    layout + real ``[N]`` diagnostic as :func:`sv_traj_d3` (§6).
    """
    _precision_dtypes(dtype)
    _validate_wc_schedule_structure(
        R=R,
        round_op_ptr=round_op_ptr,
        op_kind=op_kind,
        op_uid=op_uid,
        op_site=op_site,
    )
    _validate_shared_inputs(
        precision=dtype,
        codestate=codestate,
        R=R,
        N=N,
        arm=arm,
        b=b,
        readout_conv=readout_conv,
        logical_m=logical_m,
        shot_id_offset=shot_id_offset,
        wave=wave,
        gate_unitaries=gate_unitaries,
        kraus_name="leak_kraus",
        kraus=leak_kraus,
        stab_supp_len=stab_supp_len,
        stab_supp=stab_supp,
        stab_supp_isx=stab_supp_isx,
        log_supp=log_supp,
        log_supp_isx=log_supp_isx,
        urandom=urandom,
        urandom_stride=urandom_stride,
    )
    _validate_schedule_devices(
        codestate,
        round_op_ptr=round_op_ptr,
        op_kind=op_kind,
        op_uid=op_uid,
        op_site=op_site,
    )
    _validate_wc_schedule_values(
        round_op_ptr=round_op_ptr,
        op_kind=op_kind,
        op_uid=op_uid,
        op_site=op_site,
        n_gate=int(gate_unitaries.shape[0]),
    )
    ext = _load_ext(dtype)
    if ext is None:
        raise RuntimeError(
            f"sv_traj_d3_wc kernel ({dtype}) unavailable: needs CUDA + nvcc and "
            f"QEC_TWIN_NO_KERNELS unset (GPU-only, no CPU fallback)."
        )
    if urandom is None:
        urandom = torch.empty(0, dtype=codestate.real.dtype, device=codestate.device)
    return ext.sv_traj_d3_wc(
        codestate,
        int(R),
        round_op_ptr,
        op_kind,
        op_uid,
        op_site,
        gate_unitaries,
        stab_supp_len,
        stab_supp,
        stab_supp_isx,
        leak_kraus,
        log_supp,
        log_supp_isx,
        int(arm),
        float(b),
        int(readout_conv),
        int(logical_m),
        int(N),
        int(base_seed),
        int(shot_id_offset),
        int(wave),
        urandom,
        int(urandom_stride),
    )
