from __future__ import annotations

"""Backend seam for the Bayes decoding floor (ADR 0010 §"Integration", item 8b).

The floor logic in ``qec_twin.audit.bayes_floor`` (the unbiased exact-per-sample MC
estimator, the ``[plugin, crossfit]`` bracket, the L6 sanity arithmetic, the no-drift
report) is *backend-agnostic*: it averages ``min(P(s,0),P(s,1))/P(s)`` over Born-drawn
records and never needs to know HOW the per-record syndrome-conditioned (s, L) sector
weights are produced. THIS module makes that seam explicit.

``PathJointEvaluator`` is the Protocol the floor calls; ``DMPathEvaluator`` is the
certified d3 density-matrix implementation (the current oracle — ADR 0010 keeps the d3
DM as the certification ORACLE). Its faithfulness is established COMPONENT-WISE by the
#11 L1 independent lane (vs the raw ``.stim`` + a from-scratch qutrit oracle, NOT the
engine's own oracle): the within-cycle schedule is byte-identical to the raw ``.stim``
(gates, the X/Y DD echoes, leak placement); the leak dynamics |2⟩(R) match a from-scratch
scipy/numpy qutrit oracle to 1.4e-15; the WG slice exp(L/4) matches an independent scipy
expm to 1.75e-13 (and exp(L)==(exp(L/4))^4 to 1.1e-16); ⟨S⟩=+1, the logical {0,2,5}, and
the deterministic detectors are verified vs stim. (The ``1.5e-18`` cited elsewhere is the
PARSING/geometry — tokenizer/stabilizer-support — cert, NOT a DM-output-distribution
residual; the leakage is INJECTED by our WG model, so there is no external circuit-leakage
output distribution to certify against — the faithfulness IS component-wise.) The bodies here are a
PURE RELOCATION of the ``_*_batched`` helpers + the ``QutritDM`` constructions + the
``enumerate_floor`` recursion that previously lived inline in ``bayes_floor``: identical
math, identical numbers (``tests/test_bayes_floor.py`` L1/L2/L3/L6 are the bit-identical
regression guard).

WHY A PROTOCOL (ADR 0010). The upcoming quimb LPDO carrier (the scalable >d3 floor
backend, ADR 0010 §Decision-2) is a DIFFERENT mathematical object — a locally-purified
MPDO, ``ρ = X X†`` — not a dense density matrix. It implements the SAME six seams
(sample a record + keep the syndrome-conditioned mixed-state handle, re-evolve the other
m onto a fixed record, read the logical-sector traces, the path trace, the exact
small-R history, the CPTP residual), so it plugs in as ``evaluator=`` without touching
the floor logic. The Protocol must therefore carry NO dense-DM assumption — the handle
is opaque (``Any``); the only contract is the seam signatures + their probability
semantics (an UNNORMALIZED conditional whose trace is ``P(s|m)``, and sector traces
whose sum is that trace).

The composed object ``path_joint(path, R) -> (P(s,0), P(s,1))`` (the brief's name) is
NOT a backend method — it is the backend-free composition
``reevolve_onto_records → logical_sector_traces → _joint_sf_from_conditionals`` that the
floor already performs in ``mc_floor`` / ``enumerate_floor``; it stays in ``bayes_floor``.

GPU-only (binding, ``CLAUDE.md`` model-compute rule): the DM evaluator runs on
``device='cuda'`` (no CPU fallback); only host-side bookkeeping is CPU. complex128
throughout (precision-first; mirrors ``QutritDM``).
"""

from typing import Any, Protocol, runtime_checkable

import torch

from qec_twin.forward.exact.qutrit_dm import QUDIT, _site_trit, qutrit_hadamard

CDTYPE = torch.complex128
RDTYPE = torch.float64


# =========================================================================== #
# The backend Protocol the floor calls                                         #
# =========================================================================== #
@runtime_checkable
class PathJointEvaluator(Protocol):
    """The seams ``qec_twin.audit.bayes_floor`` needs from a forward backend to score the
    Bayes floor — and NOTHING else (no dense-DM leakage).

    A ``handle`` is an opaque, backend-specific carrier of the UNNORMALIZED
    syndrome-conditioned state ``ρ_{s|m}`` (``tr = P(s|m)``); the floor never inspects it
    except through these methods. ``records`` is the ``(B, R*n_stab)`` per-path syndrome
    record (uint8). All model-compute is on ``prob``'s device (GPU-only for the DM arm).

    The six seams (ADR 0010 §Integration / p7b §3):

    * ``cptp_residual(prob)`` — ``max|Σ_k K_k^dag K_k − I|`` of the channel(s) (the L6
      CPTP gate; scalar, device-agnostic return).
    * ``sample_paths(prob, m_draw, B, generator)`` — Born-branch ``B`` paths for the
      per-path logical prep ``m_draw`` (a length-B int tensor) down a random measurement
      path; return ``(handle, records)`` with the handle the kept UNNORMALIZED
      ``ρ_{s|m_draw}`` and ``records`` the sampled syndrome history.
    * ``reevolve_onto_records(prob, m, records)`` — DETERMINISTICALLY evolve the prep
      ``m`` (a length-B int tensor) onto FIXED ``records`` → the handle ``ρ_{s|m}`` for
      the SAME records (the "other m" leg of the (s, f) joint).
    * ``logical_sector_traces(handle, logical)`` — the per-path UNNORMALIZED logical-parity
      sector traces ``(P(L=0), P(L=1)) = tr(Π_{L=ℓ} ρ)`` (each ``(B,)`` real; their sum
      = ``tr ρ = P(s|m)``).
    * ``path_trace(handle)`` — the per-path ``tr ρ = P(s|m)`` (``(B,)`` real; the L6
      trace-conservation proxy — replaces the floor's old dense ``torch.diagonal`` read).
    * ``enumerate_history(prob, m)`` — EXACT (small R): the full within-cycle history map
      ``{path_tuple -> (P(s,L=0|m), P(s,L=1|m))}`` (the L1 enumeration anchor leg).
    """

    def cptp_residual(self, prob: Any) -> float: ...

    def sample_paths(self, prob: Any, m_draw: torch.Tensor, B: int,
                     generator: torch.Generator) -> tuple[Any, torch.Tensor]: ...

    def reevolve_onto_records(self, prob: Any, m: torch.Tensor,
                              records: torch.Tensor) -> Any: ...

    def logical_sector_traces(self, handle: Any,
                              logical: dict[int, str]) -> tuple[torch.Tensor, torch.Tensor]: ...

    def path_trace(self, handle: Any) -> torch.Tensor: ...

    def enumerate_history(self, prob: Any, m: int) -> dict[tuple, tuple[float, float]]: ...


# =========================================================================== #
# GPU-only batched density-matrix primitives (the engine math, batched)        #
# =========================================================================== #
# These mirror QutritDM.apply_channel / project_stabilizer / the logical readout EXACTLY (the
# same site-superoperator einsum + diagonal-POVM algebra), with a leading batch axis so B
# independent Monte-Carlo paths evolve in one GPU pass. They are validated against the scalar
# QutritDM in tests/test_bayes_floor.py (the batched-vs-scalar identity) — but the LOAD-BEARING
# independent ground truth is the from-scratch enumerator in the test (L1), which shares no code.
def _require_cuda(device: torch.device) -> None:
    if device.type != "cuda":
        raise RuntimeError(
            "bayes_floor model-compute is GPU-only (binding): pass device='cuda'. "
            f"got device={device} — no CPU fallback.")


def _site_superop(kraus: list[torch.Tensor]) -> torch.Tensor:
    """``S[a,c,b,e] = Σ_k K_k[a,b] conj(K_k[c,e])`` (the (3,3,3,3) site superoperator)."""
    ks = torch.stack([k.to(CDTYPE) for k in kraus]).contiguous()
    return torch.einsum("kab,kce->acbe", ks, ks.conj())


def cptp_residual(kraus: list[torch.Tensor]) -> float:
    """``max|Σ_k K_k^dag K_k − I|`` for a single-qutrit Kraus list (the L6 CPTP residual). A
    faithful leak slice is CPTP to < 1e-9; a non-CPTP slice is caught HERE (the ratio floor
    itself is scale-invariant, so the CPTP gate must be the explicit Kraus residual)."""
    s = sum(k.conj().transpose(-1, -2) @ k for k in (kr.to(CDTYPE) for kr in kraus))
    eye = torch.eye(s.shape[-1], dtype=CDTYPE, device=s.device)
    return float((s - eye).abs().max().item())


def _apply_channel_batched(rho: torch.Tensor, sop: torch.Tensor, site: int, n: int) -> torch.Tensor:
    """Batched ``rho -> Σ_k K_k rho K_k^dag`` on ``site`` via the site superoperator, IN ONE
    contraction (no per-Kraus loop). ``rho`` is ``(B, dim, dim)``; identical math to
    ``QutritDM.apply_channel`` per batch element."""
    B = rho.shape[0]
    dim = QUDIT ** n
    left, right = QUDIT ** site, QUDIT ** (n - 1 - site)
    t = torch.einsum("acbe,BlbrLeR->BlarLcR", sop,
                     rho.reshape(B, left, QUDIT, right, left, QUDIT, right)).reshape(B, dim, dim)
    return 0.5 * (t + t.conj().transpose(-1, -2))


def _apply_gate_batched(rho: torch.Tensor, U: torch.Tensor, site: int, n: int) -> torch.Tensor:
    """Batched ``rho -> U rho U^dag`` (a one-Kraus channel)."""
    return _apply_channel_batched(rho, _site_superop([U]), site, n)


def _povm_diag_weight_batched(paulis: dict[int, str], outcome: int, b: float, arm: str,
                              n: int, device: torch.device) -> torch.Tensor:
    """The diagonal of the stabilizer syndrome-bit POVM ``E_s`` (length ``dim``), EXACTLY as
    ``QutritDM._povm_diag_weight``: ``E_s[i,i] = 1/2 (1 + (-1)^s Π_q d_q)``, ``d_q = +1 (t=0),
    -1 (t=1), d2 (t=2)``; arm sets ``d2`` (A/C: 1-2b; B1: +1; B2: -1)."""
    a = str(arm).upper()
    if a in ("A", "C"):
        d2 = 1.0 - 2.0 * float(b)
    elif a == "B1":
        d2 = 1.0
    elif a == "B2":
        d2 = -1.0
    else:
        raise ValueError(f"unknown measurement arm {arm!r} (expected A, C, B1 or B2)")
    dim = QUDIT ** n
    idx = torch.arange(dim, device=device)
    prod = torch.ones(dim, dtype=RDTYPE, device=device)
    for site in paulis:
        t = _site_trit(idx, site, n)
        d = torch.where(t == 0, torch.ones(dim, dtype=RDTYPE, device=device),
                        torch.where(t == 1, torch.full((dim,), -1.0, dtype=RDTYPE, device=device),
                                    torch.full((dim,), d2, dtype=RDTYPE, device=device)))
        prod = prod * d
    sign = 1.0 if (int(outcome) & 1) == 0 else -1.0
    return 0.5 * (1.0 + sign * prod)


def _project_apply_batched(rho: torch.Tensor, paulis: dict[int, str], outcomes: torch.Tensor,
                           b: float, arm: str, n: int, device: torch.device) -> torch.Tensor:
    """Batched stabilizer projection: per batch element apply the diagonal POVM Kraus
    ``sqrt(E_{outcome_B})`` (X-supports Hadamard-rotated to Z first, then back). ``outcomes`` is
    a length-B int tensor (the per-path chosen outcome). ``rho`` updated UNNORMALIZED (tr tracks
    the running joint probability — the exactness invariant). Mirrors
    ``QutritDM.project_stabilizer`` per element."""
    a = str(arm).upper()
    x_sites = [s for s, p in paulis.items() if str(p).upper() == "X"]
    H = qutrit_hadamard(device)
    for s in x_sites:
        rho = _apply_gate_batched(rho, H, s, n)
    if a == "C":
        rho = _leak_flag_dephase_batched(rho, paulis, n, device)
    e0 = _povm_diag_weight_batched(paulis, 0, b, arm, n, device)
    e1 = _povm_diag_weight_batched(paulis, 1, b, arm, n, device)
    e_diag = torch.where(outcomes.view(-1, 1) == 0, e0.view(1, -1), e1.view(1, -1))  # (B, dim)
    sqrt_e = torch.sqrt(torch.clamp(e_diag, min=0.0)).to(CDTYPE)
    rho = rho * sqrt_e[:, :, None]
    rho = rho * sqrt_e[:, None, :].conj()
    for s in x_sites:
        rho = _apply_gate_batched(rho, H, s, n)
    return rho


def _branch_trace_batched(rho: torch.Tensor, paulis: dict[int, str], outcome: int, b: float,
                          arm: str, n: int, device: torch.device) -> torch.Tensor:
    """The (B,) trace of the ``outcome`` branch WITHOUT mutating rho: ``Σ_i E_s[i,i] rho[i,i]``
    in the (possibly Hadamard-rotated) basis. For arm C the diagonal is rotation- and
    dephase-invariant on the diagonal, so the branch trace uses the diagonal directly after the
    X-support rotation (the dephasing only zeroes off-diagonals)."""
    x_sites = [s for s, p in paulis.items() if str(p).upper() == "X"]
    H = qutrit_hadamard(device)
    r = rho
    for s in x_sites:
        r = _apply_gate_batched(r, H, s, n)
    e_diag = _povm_diag_weight_batched(paulis, outcome, b, arm, n, device)  # (dim,)
    diag = torch.diagonal(r, dim1=-2, dim2=-1).real  # (B, dim)
    return (diag * e_diag.view(1, -1)).sum(dim=-1)


def _leak_flag_dephase_batched(rho: torch.Tensor, paulis: dict[int, str], n: int,
                               device: torch.device) -> torch.Tensor:
    """Arm-C leak-flag dephasing (batched): zero ``rho[...,i,j]`` where the per-support leak-flag
    keys differ. Mirrors ``QutritDM._leak_flag_dephase``."""
    dim = QUDIT ** n
    idx = torch.arange(dim, device=device)
    flag = torch.zeros(dim, dtype=torch.long, device=device)
    for bit, site in enumerate(paulis):
        t = _site_trit(idx, site, n)
        flag = flag | ((t == 2).to(torch.long) << bit)
    mask_off = (flag[:, None] != flag[None, :]).view(1, dim, dim)
    return rho.masked_fill(mask_off, 0)


def _init_logical_batched(prob: Any, m: int, B: int, device: torch.device) -> torch.Tensor:
    """The ``|m⟩_L`` codestate replicated into a ``(B, dim, dim)`` batch (one scalar codestate
    build via the certified ``QutritDM`` path, then broadcast). The codestate prep is exact +
    geometry-validated in ``QutritDM`` / ``exact_floor_run.assert_commuting_code``."""
    from qec_twin.forward.exact.qutrit_dm import QutritDM
    e = QutritDM(prob.n, device=device)
    e.set_code(stabilizers=prob.stabs, logical_z=prob.logical)
    e.init_logical(m)
    return e.rho.unsqueeze(0).expand(B, -1, -1).clone()


def _logical_sector_traces_batched(rho: torch.Tensor, logical: dict[int, str], n: int,
                                   device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    """Per-batch UNNORMALIZED logical-parity sector traces ``(P(L=0), P(L=1))`` = ``tr(Π_{L=ℓ}
    rho)``, from the logical-operator parity (X-support Hadamard-rotated to Z; leaked logical
    support split evenly — the engine's neutral default). Each (B,) real; their sum = tr rho =
    P(s|m). Mirrors ``QutritDM.logical_distribution`` (unnormalized)."""
    x_sites = [s for s, p in logical.items() if str(p).upper() == "X"]
    H = qutrit_hadamard(device)
    r = rho
    for s in x_sites:
        r = _apply_gate_batched(r, H, s, n)
    diag = torch.diagonal(r, dim1=-2, dim2=-1).real  # (B, dim)
    dim = QUDIT ** n
    idx = torch.arange(dim, device=device)
    parity = torch.zeros(dim, dtype=torch.long, device=device)
    leaked = torch.zeros(dim, dtype=torch.bool, device=device)
    for site in logical:
        t = _site_trit(idx, site, n)
        bit = torch.where(t == 2, torch.zeros_like(t), t)
        parity = parity ^ (bit & 1)
        leaked = leaked | (t == 2)
    m0 = ((parity == 0) & (~leaked)).to(RDTYPE)
    m1 = ((parity == 1) & (~leaked)).to(RDTYPE)
    half_leak = 0.5 * leaked.to(RDTYPE)
    p0 = (diag * (m0 + half_leak).view(1, -1)).sum(dim=-1)
    p1 = (diag * (m1 + half_leak).view(1, -1)).sum(dim=-1)
    return p0, p1


# =========================================================================== #
# Within-cycle batched evolution (the certified per-round op stream)           #
# =========================================================================== #
def _apply_premeasure_batched(rho: torch.Tensor, prob: Any, sops: dict[int, torch.Tensor],
                              device: torch.device) -> torch.Tensor:
    """Apply each qutrit's pre-M within-cycle stream (H / X gates + exp(L/4) LEAK slices) to the
    batch, IN ORDER. Mirrors ``QutritDM.apply_within_cycle_premeasure``; single-qutrit ops on
    distinct qutrits commute, so per-qutrit replay equals the true interleaving."""
    from qec_twin.forward.exact.qutrit_dm import QutritDM
    eng = QutritDM(1, device=device)  # tiny helper for the single-qutrit frame gates
    X = eng.single_qutrit_gate("X")
    H = qutrit_hadamard(device)
    leak_sop = sops["__leak__"]
    for q, toks in prob.streams.items():
        site = int(q)
        for tok in toks:
            if tok == "LEAK":
                rho = _apply_channel_batched(rho, leak_sop, site, prob.n)
            elif tok == "H":
                rho = _apply_gate_batched(rho, H, site, prob.n)
            elif tok == "X":
                rho = _apply_gate_batched(rho, X, site, prob.n)
            elif tok in ("M", "Y"):
                continue  # M is a marker; Y is post-M (applied after the projection)
            else:
                raise ValueError(f"within-cycle pre-measure: unknown token {tok!r} at site {site}")
    return rho


def _apply_postmeasure_Y_batched(rho: torch.Tensor, prob: Any, device: torch.device,
                                 *, terminal: bool) -> torch.Tensor:
    """Apply the post-M transversal Y on every site (dropped on the terminal round). Mirrors
    ``QutritDM.apply_within_cycle_postmeasure`` (the uniform-Y interior convention used by
    ``dm_floor_history``)."""
    if terminal:
        return rho
    from qec_twin.forward.exact.qutrit_dm import QutritDM
    eng = QutritDM(1, device=device)
    Y = eng.single_qutrit_gate("Y")
    for site in range(prob.n):
        rho = _apply_gate_batched(rho, Y, site, prob.n)
    return rho


def _sample_paths_batched(rho: torch.Tensor, prob: Any, sops: dict[int, torch.Tensor],
                          device: torch.device, generator: torch.Generator) -> tuple[torch.Tensor, torch.Tensor]:
    """Born-branch B paths down a random measurement path → the (B,dim,dim) UNNORMALIZED
    conditional ``ρ_{s|m}`` (per-path tr = P(s|m)) and the (B, R*n_stab) sampled syndrome
    records. One linear pass (no recursion)."""
    B = rho.shape[0]
    R, n_stab = prob.R, prob.n_stab
    records = torch.empty((B, R * n_stab), dtype=torch.uint8, device=device)
    col = 0
    for r in range(R):
        is_term = (r == R - 1)
        rho = _apply_premeasure_batched(rho, prob, sops, device)
        for k, supp in enumerate(prob.stabs):
            parent_tr = torch.diagonal(rho, dim1=-2, dim2=-1).real.sum(dim=-1)  # (B,)
            tr0 = _branch_trace_batched(rho, supp, 0, prob.b, prob.arm, prob.n, device)  # (B,)
            p0 = torch.where(parent_tr > 0, tr0 / parent_tr.clamp_min(1e-300),
                             torch.zeros_like(parent_tr))
            u = torch.rand(B, generator=generator, device=device, dtype=RDTYPE)
            outcomes = (u >= p0).to(torch.uint8)  # 0 if u<p0 else 1
            rho = _project_apply_batched(rho, supp, outcomes, prob.b, prob.arm, prob.n, device)
            records[:, col] = outcomes
            col += 1
        rho = _apply_postmeasure_Y_batched(rho, prob, device, terminal=is_term)
    return rho, records


def _reevolve_onto_records_batched(rho: torch.Tensor, prob: Any, records: torch.Tensor,
                                   sops: dict[int, torch.Tensor], device: torch.device) -> torch.Tensor:
    """Deterministically evolve the batch (init to the OTHER m) onto fixed per-path syndrome
    records → the (B,dim,dim) UNNORMALIZED conditional ``ρ_{s|m'}`` (per-path tr = P(s|m'))."""
    R, n_stab = prob.R, prob.n_stab
    col = 0
    for r in range(R):
        is_term = (r == R - 1)
        rho = _apply_premeasure_batched(rho, prob, sops, device)
        for k, supp in enumerate(prob.stabs):
            outcomes = records[:, col]
            rho = _project_apply_batched(rho, supp, outcomes, prob.b, prob.arm, prob.n, device)
            col += 1
        rho = _apply_postmeasure_Y_batched(rho, prob, device, terminal=is_term)
    return rho


# =========================================================================== #
# The dense-DM PathJointEvaluator (the certified d3 oracle)                     #
# =========================================================================== #
class DMPathEvaluator:
    """The certified d3 density-matrix backend for the Bayes floor (the current oracle).

    Pure relocation of the ``_*_batched`` helpers + the ``QutritDM`` codestate / enumeration
    that previously lived inline in ``bayes_floor``. Effectively stateless (the only field is the
    enumeration ``prune`` constant): each method recomputes the leak site-superoperator from
    ``prob.leak_kraus`` (``_site_superop`` is deterministic), so two runs with the same seed are
    bit-identical, and a single default instance is safe to share across calls. A handle is the
    dense ``(B, dim, dim)`` UNNORMALIZED conditional ``ρ_{s|m}`` (``tr ρ = P(s|m)``). GPU-only
    model compute (``device='cuda'``).
    """

    def __init__(self, *, prune: float = 1e-15) -> None:
        # small-weight drop in enumerate_history (matches the prior inline enumerate_floor default).
        self._prune = float(prune)

    # -- the leak channel CPTP residual (the L6 gate) -- #
    def cptp_residual(self, prob: Any) -> float:
        """``max|Σ_k K_k^dag K_k − I|`` of the within-cycle leak slice (CPTP to < 1e-9 when
        faithful; a non-CPTP slice trips HERE — the floor ratio is scale-invariant)."""
        return cptp_residual(prob.leak_kraus)

    # -- Born-sample a batch of paths, keep the conditional handle -- #
    def sample_paths(self, prob: Any, m_draw: torch.Tensor, B: int,
                     generator: torch.Generator) -> tuple[torch.Tensor, torch.Tensor]:
        """Build the per-path ``|m_draw⟩_L`` codestate batch, Born-branch B paths down a random
        measurement path, return ``(ρ_{s|m_draw}, records)``. ``m_draw`` is a length-B int tensor
        (the codestate differs by m); the generator drives ONLY the branch draws (the codestate
        build is deterministic), so the generator stream is identical to the prior inline path."""
        device = m_draw.device
        _require_cuda(device)
        sops = {"__leak__": _site_superop(prob.leak_kraus)}
        rho = torch.empty((B, QUDIT ** prob.n, QUDIT ** prob.n), dtype=CDTYPE, device=device)
        for mval in (0, 1):
            mask = (m_draw == mval)
            if not bool(mask.any()):
                continue
            rho[mask] = _init_logical_batched(prob, mval, int(mask.sum()), device)
        return _sample_paths_batched(rho, prob, sops, device, generator)

    # -- deterministically re-evolve a (different) m onto fixed records -- #
    def reevolve_onto_records(self, prob: Any, m: torch.Tensor,
                              records: torch.Tensor) -> torch.Tensor:
        """Build the per-path ``|m⟩_L`` codestate batch and DETERMINISTICALLY evolve it onto the
        FIXED ``records`` → ``ρ_{s|m}`` for the same records (the "other m" leg of the (s, f)
        joint). ``m`` is a length-B int tensor; ``records`` is ``(B, R*n_stab)`` uint8."""
        device = records.device
        _require_cuda(device)
        sops = {"__leak__": _site_superop(prob.leak_kraus)}
        B = records.shape[0]
        rho = torch.empty((B, QUDIT ** prob.n, QUDIT ** prob.n), dtype=CDTYPE, device=device)
        for mval in (0, 1):
            mask = (m == mval)
            if bool(mask.any()):
                rho[mask] = _init_logical_batched(prob, mval, int(mask.sum()), device)
        return _reevolve_onto_records_batched(rho, prob, records, sops, device)

    # -- the logical-parity sector traces (P(L=0), P(L=1)) on a handle -- #
    def logical_sector_traces(self, handle: torch.Tensor,
                              logical: dict[int, str]) -> tuple[torch.Tensor, torch.Tensor]:
        """``(P(L=0), P(L=1)) = tr(Π_{L=ℓ} ρ)`` per path on the UNNORMALIZED handle (each (B,)
        real; their sum = ``tr ρ = P(s|m)``)."""
        n = _n_from_dim(int(handle.shape[-1]))
        return _logical_sector_traces_batched(handle, logical, n, handle.device)

    # -- the per-path trace tr ρ = P(s|m) (the L6 trace-conservation proxy) -- #
    def path_trace(self, handle: torch.Tensor) -> torch.Tensor:
        """``tr ρ = P(s|m)`` per path (``(B,)`` real). Replaces the floor's old dense
        ``torch.diagonal(rho_kept).real.sum`` read — the one flagged DM coupling, now routed
        through the backend so an LPDO handle supplies its own trace."""
        return torch.diagonal(handle, dim1=-2, dim2=-1).real.sum(dim=-1)

    # -- EXACT small-R within-cycle history (the L1 enumeration anchor leg) -- #
    def enumerate_history(self, prob: Any, m: int) -> dict[tuple, tuple[float, float]]:
        """The full within-cycle history map ``{path_tuple -> (P(s,L=0|m), P(s,L=1|m))}`` by EXACT
        depth-first projection enumeration on the dense DM (the L1 ground-truth leg). Feasible on a
        sub-register at small R; the depth-(R*n_stab) recursive ``rho.clone()`` of the full 3^9 DM
        is memory-marginal (flagged in ``enumerate_floor`` / ``p7_floor_rgt1``). PURE RELOCATION of
        the ``history_with_L`` recursion that previously lived inside ``enumerate_floor``."""
        from qec_twin.forward.exact.qutrit_dm import QutritDM
        device = prob.leak_kraus[0].device
        _require_cuda(device)
        leak_t = [k.to(CDTYPE) for k in prob.leak_kraus]

        eng0 = QutritDM(prob.n, device=device)
        eng0.set_code(stabilizers=prob.stabs, logical_z=prob.logical)
        eng0.init_logical(m)
        base0 = eng0.rho.clone()
        out: dict[tuple, tuple[float, float]] = {}

        def recurse(rho_in: torch.Tensor, r: int, prefix: tuple) -> None:
            e = QutritDM(prob.n, device=device)
            e.set_code(stabilizers=prob.stabs, logical_z=prob.logical)
            e.set_state(rho_in.clone())
            e.apply_within_cycle_premeasure(prob.streams, leak_t)
            is_term = (r == prob.R - 1)
            base = e.rho.clone()
            dist = e.syndrome_distribution(prob.stabs, b=prob.b, arm=prob.arm, diagonal_z=False)
            for s, ps in dist.items():
                if ps <= self._prune:
                    continue
                e.rho = base.clone()
                for k, sk in enumerate(s):
                    e.project_stabilizer(prob.stabs[k], sk, prob.b, prob.arm, diagonal_z=False)
                new_prefix = prefix + tuple(int(x) for x in s)
                if is_term:
                    L0, L1 = _logical_sector_traces_batched(
                        e.rho.unsqueeze(0), prob.logical, prob.n, device)
                    L0, L1 = float(L0.item()), float(L1.item())
                    prev = out.get(new_prefix, (0.0, 0.0))
                    out[new_prefix] = (prev[0] + L0, prev[1] + L1)
                else:
                    tr = e.trace()
                    if tr <= 1e-300:
                        continue
                    e.rho = e.rho / tr
                    Yg = e.single_qutrit_gate("Y")
                    for p in range(prob.n):
                        e.apply_gate(Yg, p)
                    recurse(e.rho * tr, r + 1, new_prefix)  # rescale back to UNNORMALIZED weight

        recurse(base0, 0, ())
        return out


def _n_from_dim(dim: int) -> int:
    """Resolve ``n`` from a dense ``3^n`` handle dimension by EXACT integer division (no float
    ``log`` — bulletproof for any power of 3). Raises if ``dim`` is not a power of 3."""
    n, d = 0, dim
    while d > 1 and d % QUDIT == 0:
        d //= QUDIT
        n += 1
    if d != 1:
        raise ValueError(f"handle dim {dim} is not a power of {QUDIT} (n undefined)")
    return n
