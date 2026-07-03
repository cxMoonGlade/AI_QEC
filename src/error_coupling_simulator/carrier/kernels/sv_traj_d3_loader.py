"""Loader for the P4a state-vector MCWF trajectory kernel (``sv_traj_d3.cu``).

JIT-compiles + binds the block-per-trajectory leakage-teacher kernel and exposes the
§7 host↔kernel signatures.  TWO entry points share one compiled module:

* :func:`sv_traj_d3` — the LUMPED per-round model (``[all gates] -> [ONE full-cycle
  leak] -> [measure]``; the §7 gate-CSR signature).
* :func:`sv_traj_d3_wc` — the circuit-faithful WITHIN-CYCLE op-schedule (Agent H's
  ``WithinCycleMarshalled`` CSR: per round, interleaved per-qutrit gate+``exp(L/4)``
  LEAK ops -> measure (UNCHANGED) -> post-M ``Y``; model
  ``docs/nonpauli_teacher/p4a_within_cycle_model.md``).

Mirrors the compile/load style of :mod:`qec_twin.forward.accel`
(``torch.utils.cpp_extension.load`` with nvcc from ``/usr/local/cuda``;
``QEC_TWIN_NO_KERNELS=1`` disables; GPU-only — no CPU compute fallback in the
trajectory path).

Two precision builds are compiled lazily and cached separately, selected by the
``dtype`` arg of :func:`sv_traj_d3`:

* ``c128`` (default, ``-DSV_REAL=double``) — the precision-first build; the
  state vector is ``complex128`` (315 KB/shot in global).
* ``c64`` (gated, ``-DSV_REAL=float``) — the throughput build; only used after the
  Gate-5 / P-D ``complex64``-vs-``complex128`` syndrome-distribution equivalence
  (≲1e-6) clears.  Compiled on demand the first time it is requested.

Agent H wraps :func:`sv_traj_d3` inside
``forward.scalable.sv_sampler.SvSampler.sample`` (the public host API); Agent V
calls only that wrapper.  This module is the pure compile/bind boundary — it builds
no schedule and reads no disk.
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

    All tensor arguments are CUDA tensors marshalled by Agent H (§2/§3/§8).  The
    return is ``(packed_shot_bits, norm_drift)``:

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
