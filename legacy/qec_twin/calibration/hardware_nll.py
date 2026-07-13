from __future__ import annotations

"""R2-lite M3: label-free window calibration on hardware detector-block histograms.

Pre-registration: docs/metric_results.md "2026-06-09 -- R2-lite M3". The learner
consumes ONLY the empirical 256-bin block histogram (isolation contract: no
teacher/circuit/decoder material crosses this module). The window twin is the
frozen-design Candidate A object: 5 learnable Stinespring channels (one per
window data qubit) driving the exact stationary d=5 parity-backend block law
(:mod:`qec_twin.forward.exact.steady_state`), composed with a classical
per-site readout-flip layer ``q_j`` on the recorded syndromes (quantum
extraction noiseless; sector structure preserved). Per the registered exact
reset/readout gauge, every fitted ``q_j`` is ``q^eff`` ONLY -- a record-flip
rate absorbing any readout/reset split, never a physical readout claim.

Readout convolution (derived; the M3 build derivation, verified by P1c/P1g)
---------------------------------------------------------------------------
A readout flip of record ``r_t`` at a site flips the two detectors
``d_t = r_t XOR r_{t-1}`` and ``d_{t+1} = r_{t+1} XOR r_t`` -- the consecutive
detector pair. A 2-layer block ``(d_t, d_{t+1})`` therefore feels the iid
Bernoulli(q) flips ``(a, b, c)`` of the THREE records ``(r_{t-1}, r_t, r_{t+1})``
through the induced detector-flip pattern ``e = (a XOR b, b XOR c)``:

    P(e = 00) = (1-q)^3 + q^3 = 1 - 3q(1-q)
    P(e = 10) = P(e = 01) = P(e = 11) = q(1-q)

(the registration's quoted ``P(00) = 1 - 3q(1-q)`` kernel, confirmed). In the
Walsh-Hadamard domain every non-identity 2-bit character has exactly two
records in its support (``d_t -> a XOR b``, ``d_{t+1} -> b XOR c``,
``d_t XOR d_{t+1} -> a XOR c``), so all three are damped by the SAME factor
``(1-2q)^2`` -- which is also why two independent record-flip layers compose
exactly into one with ``(1-2q')=(1-2q)(1-2r)`` (the P1g gauge identity). For
``R`` records per site (``R-1`` detector layers) the kernel generalizes to the
2-to-1 preimage sum ``kappa(e) = q^{|a|}(1-q)^{R-|a|} + q^{R-|a|}(1-q)^{|a|}``
where ``a`` is either record-flip preimage of ``e``. Flips at different sites
are independent, so the full convolution is the per-site XOR product -- exact
and differentiable in ``q``.

Execution modes (the 2026-06-10 amendment)
------------------------------------------
Binding registration: docs/metric_results.md, "M3 PRE-RUN ADJUDICATIONS"
item 7. The twin's channel field is HOISTED -- ``WindowTwin.field()``
evaluates each channel's Kraus stack ONCE per call (the
``m3_report.in_class_field`` idiom) and every closure reuses the stacks across
rounds. ``calibrate_window(graph_mode=...)`` selects execution only, never
math: ``"off"`` is the amended hoisted eager closure (the reference mode);
``"auto"``/``"on"`` run STATIC-KRAUS-INPUT CUDA-graph replay --
``torch.matrix_exp`` host-syncs and cannot be captured (measured; in the
ledger), so it stays eager and the capture boundary sits at the five Kraus
stacks (:class:`_StaticKrausGraphedClosure`).

Bit convention: pinned in :mod:`qec_twin.forward.exact.steady_state` (site j,
layer l -> bit ``(R-1) * j + l``).
"""

import contextlib
from dataclasses import dataclass

import torch

from qec_twin.forward.cptp_channel import RDTYPE, StinespringChannel
from qec_twin.forward.exact.steady_state import (
    DEFAULT_BURN_IN,
    DEFAULT_FP_TOL,
    DEFAULT_MAX_BURN_IN,
    diagonal_markov_pair,
    fixed_point_residual,
    simulate_steady_block,
)
from qec_twin.numerics import NUMERICAL_ZERO

WINDOW_DISTANCE = 5
NUM_INTERIOR_CHECKS = WINDOW_DISTANCE - 1
Q_LOGIT_INIT = -4.5  # sigmoid ~ 1.1e-2, generic small record-flip start

GRAPH_MODES = ("auto", "off", "on")
GRAPH_WARMUP_ITERS = 3  # official capture recipe: ~3 side-stream iterations of the EXACT
# captured-region body (static-Kraus forward + backward) so allocator / cuBLAS /
# fused-extension / cached-mask state initializes outside the capture


def _site_flip_kernel(q: torch.Tensor, num_records: int) -> torch.Tensor:
    """``(2**(R-1),)`` XOR kernel ``kappa(e)`` of one site's detector-flip law."""
    r = int(num_records)
    entries = []
    for e in range(2 ** (r - 1)):
        a = [0]
        for layer in range(r - 1):
            a.append(a[-1] ^ ((e >> layer) & 1))  # the a_0 = 0 record-flip preimage of e
        weight = sum(a)
        entries.append(
            q**weight * (1 - q) ** (r - weight) + q ** (r - weight) * (1 - q) ** weight
        )
    return torch.stack(entries)


def readout_convolution(block_law: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Exact XOR convolution of the detector-block law with per-site readout flips.

    ``block_law`` is the flattened ``(2**(4*(R-1)),)`` stationary law (pinned
    bit convention); ``q`` is the ``(4,)`` per-site record-flip probabilities
    ``q^eff``. The number of records ``R`` is inferred from the law size.
    Differentiable in both arguments.
    """
    size = int(block_law.shape[-1])
    total_bits = size.bit_length() - 1
    if 2**total_bits != size or total_bits % NUM_INTERIOR_CHECKS:
        raise ValueError(f"law size {size} is not 2**({NUM_INTERIOR_CHECKS}*k)")
    bits_per_site = total_bits // NUM_INTERIOR_CHECKS
    num_records = bits_per_site + 1
    pair_dim = 2**bits_per_site

    # Reshape so axis a holds site (NUM_INTERIOR_CHECKS - 1 - a)'s 2-bit pair
    # (the pattern code is little-endian in the site index).
    law = block_law.reshape([pair_dim] * NUM_INTERIOR_CHECKS)
    letters = "abcdefgh"
    for j in range(NUM_INTERIOR_CHECKS):
        kernel = _site_flip_kernel(q[j], num_records)
        idx = torch.arange(pair_dim, device=block_law.device)
        site_matrix = kernel[idx[:, None] ^ idx[None, :]]  # M[out, in] = kappa(out XOR in)
        axis = NUM_INTERIOR_CHECKS - 1 - j
        spec_in = letters[:NUM_INTERIOR_CHECKS]
        spec_out = spec_in.replace(spec_in[axis], "z")
        law = torch.einsum(f"z{spec_in[axis]},{spec_in}->{spec_out}", site_matrix, law)
    return law.reshape(-1)


@dataclass
class WindowTwin:
    """The M3 window learner: 5 CPTP channels + 4 per-site readout logits.

    ``q_logit`` (NEVER ``lambda``: that symbol is reserved for DEM logits,
    docs/TWIN.md) parameterizes ``q^eff = sigmoid(q_logit)`` per interior
    check. ``field()`` is the time-shared rep_code-convention channel callable.
    """

    distance: int
    channels: list[StinespringChannel]
    q_logit: torch.Tensor  # (4,) requires_grad

    @classmethod
    def random(
        cls,
        *,
        num_kraus: int = 2,
        seed: int = 0,
        scale: float = 0.1,
        device: str | torch.device = "cpu",
        q_logit_init: float = Q_LOGIT_INIT,
    ) -> "WindowTwin":
        channels = [
            StinespringChannel.random(2, num_kraus, seed=seed + i, scale=scale, device=device)
            for i in range(WINDOW_DISTANCE)
        ]
        q_logit = torch.full(
            (NUM_INTERIOR_CHECKS,), float(q_logit_init), dtype=RDTYPE, device=device
        ).requires_grad_(True)
        return cls(distance=WINDOW_DISTANCE, channels=channels, q_logit=q_logit)

    def parameters(self) -> list[torch.Tensor]:
        params: list[torch.Tensor] = []
        for channel in self.channels:
            params.extend(channel.parameters())
        params.append(self.q_logit)
        return params

    def field(self):
        """Time-shared channel field with the Kraus stacks HOISTED.

        Execution-mode amendment (docs/metric_results.md, "M3 PRE-RUN
        ADJUDICATIONS" item 7, registered 2026-06-10): each channel's Kraus
        stack is evaluated ONCE per ``field()`` call -- the
        ``m3_report.in_class_field`` idiom -- and the returned callable reuses
        that stack for every ``(t, i)`` reading. ``block_law`` invokes
        ``field()`` exactly once per evaluation, so each fit closure builds
        ONE fresh autograd Kraus subgraph per channel and shares the tensor
        across the burn-in init and all rounds (the naive per-``(t, i)``
        re-evaluation was host-dispatch-bound: ~215 ``kraus()`` calls per
        closure). Forward law: provably BIT-exact vs the naive field --
        identical tensor values into identical ops in identical order.
        Backward: differs only by re-association of the per-round cotangent
        sum through the linear ``matrix_exp`` vjp -- mathematically identical,
        float-level <= ulp; disclosed in the amendment, and the P1h
        bit-exactness pins bind execution modes WITHIN this amended closure.
        """
        stacks = [channel.kraus() for channel in self.channels]
        return lambda t, i: stacks[i]

    def q_eff(self) -> torch.Tensor:
        return torch.sigmoid(self.q_logit)

    def markov_pairs(self) -> torch.Tensor:
        """``(5, 2)`` per-qubit ``(p01, p10)`` -- the recoverable diagonal pairs."""
        with torch.no_grad():
            rows = [torch.stack(diagonal_markov_pair(c.kraus())) for c in self.channels]
        return torch.stack(rows)

    def block_law(
        self,
        *,
        burn_in: int = DEFAULT_BURN_IN,
        max_burn_in: int = DEFAULT_MAX_BURN_IN,
        fp_tol: float = DEFAULT_FP_TOL,
        rounds: int = 3,
        device: str | torch.device = "cpu",
        check_residual: bool = True,
        channel_field=None,
    ) -> torch.Tensor:
        """The twin's full model law: stationary block law + readout convolution.

        ``channel_field`` (default ``self.field()``, the hoisted stacks)
        overrides the channel field; the static-Kraus CUDA-graph capture
        passes ``(t, i) -> static_kraus[i]`` so the captured forward reads the
        graph's static input buffers. ``q^eff`` is always read live from
        ``q_logit`` (``sigmoid`` by address -- exactly what the capture
        needs: ``q_logit`` is a real parameter inside the graph).
        """
        law = simulate_steady_block(
            self.field() if channel_field is None else channel_field,
            distance=self.distance,
            burn_in=burn_in,
            max_burn_in=max_burn_in,
            fp_tol=fp_tol,
            rounds=rounds,
            device=device,
            check_residual=check_residual,
        )
        return readout_convolution(law, self.q_eff())


def block_cross_entropy(
    target_probs: torch.Tensor, model_law: torch.Tensor, *, floor: float = NUMERICAL_ZERO
) -> torch.Tensor:
    """``-sum_z phat(z) log p_model(z)`` per block (nats); the M3 fit objective."""
    return -(target_probs * torch.log(model_law.clamp_min(floor))).sum()


class _StaticKrausGraphedClosure:
    """One fit's STATIC-KRAUS-INPUT CUDA-graph closure: capture once, replay per call.

    Execution-mode amendment (docs/metric_results.md, "M3 PRE-RUN
    ADJUDICATIONS" item 7): ``torch.matrix_exp`` performs a host copy during
    capture (measured; confirmed loudly by the equality pins), so the closure
    CANNOT be captured whole. The capture boundary is therefore placed at the
    five Kraus stacks -- ``matrix_exp`` stays eager, everything downstream is
    one recorded graph.

    Static state (per fit, instance-local, freed with the fit): five leaf
    buffers ``static_kraus[i]`` (same shape/dtype/device as channel ``i``'s
    Kraus stack, ``requires_grad=True``), the captured graph + its private
    memory pool, and ``static_loss``.

    CAPTURED REGION (recorded once, after ``GRAPH_WARMUP_ITERS`` warmup
    iterations of the IDENTICAL body on a side stream):

    1. zero the ``.grad`` buffers of ``static_kraus`` AND ``q_logit`` (each
       replay starts clean; the buffers are pre-created so the addresses are
       stable from the first warmup iteration on);
    2. forward: the stationary block law from the field
       ``(t, i) -> static_kraus[i]`` with ``check_residual=False`` (fixed
       shapes, sync-free), readout convolution with
       ``q_eff = sigmoid(q_logit)`` -- ``q_logit`` is a REAL parameter read by
       address, so its gradient is produced inside the graph;
    3. cross-entropy vs the static ``target_probs``;
    4. ``loss.backward()`` to the ``static_kraus`` leaves and ``q_logit``.

    EAGER BRIDGE (every closure call, outside the graph; the exact order):

    (a) zero the channel-parameter ``.grad`` buffers eagerly
        (``set_to_none=False`` semantics: created as zeros on the first call,
        zeroed in place afterwards -- stable buffers);
    (b) evaluate the five EAGER Kraus stacks -- five ``matrix_exp`` calls,
        autograd-tracked to the channel parameters; host syncs allowed here;
    (c) ``static_kraus[i].copy_(stacks[i])`` under ``no_grad`` (the graph
        reads these buffers by address);
    (d) ``graph.replay()``;
    (e) ``torch.autograd.backward(stacks, grad_tensors=[sk.grad ...])`` --
        splice the graph-produced cotangents into the eager Kraus subgraph,
        accumulating the channel-parameter gradients;
    (f) return ``static_loss`` (LBFGS reads / ``float()``s it after the
        closure returns, which also host-syncs the stream).

    Correctness vs the hoisted eager closure (``graph_mode="off"``)
    ---------------------------------------------------------------
    FORWARD is bit-exact: by (c) the static-Kraus VALUES equal the eager
    Kraus values bit-for-bit, and the replay executes a recording of the
    identical kernel sequence the hoisted eager forward launches on those
    values -- identical kernels on identical values, in identical order
    (deterministic-algorithms mode is the orchestrator's execution contract).

    GRADIENT FLOW is exact w.r.t. the hoisted closure: the graph's backward
    runs the same engine-ordered kernels the hoisted eager backward would run
    for the segment above the Kraus tensors, computing
    ``dloss/dstatic_kraus`` and ``dloss/dq_logit``; the bridge then runs
    exactly the eager Kraus-subgraph backward (``matrix_exp`` vjp -> isometry
    slice/reshape -> Hermitian adjoint -> parameter accumulation) with the
    same cotangent values -- same ops, same order, same inputs.

    DISCLOSED CAVEAT (cotangent-injection boundary -- flagged for the
    reviewer; Builder E's bit-exact pins adjudicate empirically): backward
    executes as TWO engine passes cut at the ``static_kraus`` leaves instead
    of one. The cut sits at a node boundary the single-pass engine also
    materializes -- eager autograd fully accumulates a tensor's cotangent
    buffer before invoking its producer's vjp and never fuses or reorders
    across a node boundary -- so no reduction crosses the cut. Two identified
    bit-level escape hatches: (i) the graphed pass materializes the cotangent
    via AccumulateGrad's ``grad += new`` into a zeroed buffer, and
    ``0.0 + (-0.0) = +0.0``, so a negative-zero cotangent component flips its
    sign-of-zero (value-identical; ``==`` / ``torch.equal`` cannot see it; it
    can only surface as a +-0 bit in a parameter gradient); (ii) the
    multi-consumer per-round cotangent accumulation order must coincide
    between the recorded capture and a fresh eager pass -- both are the
    deterministic single-device engine order of the same graph topology, but
    this is asserted, not proven.

    Why (e) reads ``sk.grad`` DIRECTLY (no clone): the only writer of
    ``sk.grad`` is the replay (its zero + accumulate kernels are inside the
    capture); every kernel here is enqueued on the same stream, and the next
    replay -- the next overwrite -- cannot be enqueued before this closure
    returns. Stream order alone therefore guarantees the bridge's vjp kernels
    read the cotangents this replay just produced -- no host sync, no copy.

    The graph reads/writes storages by ADDRESS: LBFGS updates parameters
    strictly in place (``add_`` / ``copy_``), the static grads are pre-created
    and zeroed in place, and :meth:`verify_static_storage` asserts every
    captured address on every call and after the fit. No module-level state.
    """

    def __init__(
        self,
        twin: WindowTwin,
        target_probs: torch.Tensor,
        *,
        burn_in: int,
        max_burn_in: int,
        fp_tol: float,
        rounds: int,
        device: str | torch.device,
    ) -> None:
        dev = torch.device(device)
        if dev.type != "cuda":
            raise RuntimeError(f"CUDA-graph capture requires a CUDA device (got {dev})")
        self._twin = twin
        self._channel_params = [
            p for channel in twin.channels for p in channel.parameters()
        ]
        guard = (
            torch.cuda.device(dev.index) if dev.index is not None else contextlib.nullcontext()
        )
        with guard:
            # Static input leaves, filled from the INITIAL parameters (sane
            # warmup values; same shape/dtype/device as each Kraus stack).
            with torch.no_grad():
                init_stacks = [channel.kraus() for channel in twin.channels]
            self.static_kraus = [
                stack.clone().requires_grad_(True) for stack in init_stacks
            ]
            static_leaves = [twin.q_logit, *self.static_kraus]
            for leaf in static_leaves:
                if leaf.grad is None:
                    leaf.grad = torch.zeros_like(leaf)
                else:
                    leaf.grad.zero_()

            def static_field(t: int, i: int) -> torch.Tensor:
                return self.static_kraus[i]

            def body() -> torch.Tensor:
                for leaf in static_leaves:
                    leaf.grad.zero_()
                law = twin.block_law(
                    burn_in=burn_in,
                    max_burn_in=max_burn_in,
                    fp_tol=fp_tol,
                    rounds=rounds,
                    device=device,
                    check_residual=False,
                    channel_field=static_field,
                )
                loss = block_cross_entropy(target_probs, law)
                loss.backward()
                return loss

            side = torch.cuda.Stream(device=dev)
            side.wait_stream(torch.cuda.current_stream(dev))
            with torch.cuda.stream(side):
                for _ in range(GRAPH_WARMUP_ITERS):
                    body()
            torch.cuda.current_stream(dev).wait_stream(side)

            # Addresses the recorded graph reads/writes; channel parameters are
            # included for the LBFGS in-place-update contract even though the
            # graph itself never touches them (the bridge reads them eagerly).
            self._tracked = [
                ("q_logit", twin.q_logit),
                ("target_probs", target_probs),
                *[(f"static_kraus[{i}]", sk) for i, sk in enumerate(self.static_kraus)],
                *[(f"channel_param[{i}]", p) for i, p in enumerate(self._channel_params)],
            ]
            self._tracked_ptrs = [tensor.data_ptr() for _, tensor in self._tracked]
            self._grad_tracked = [
                ("q_logit", twin.q_logit),
                *[(f"static_kraus[{i}]", sk) for i, sk in enumerate(self.static_kraus)],
            ]
            self._grad_ptrs = [owner.grad.data_ptr() for _, owner in self._grad_tracked]

            self.graph = torch.cuda.CUDAGraph()
            with torch.cuda.graph(self.graph):
                self.static_loss = body()
        self.verify_static_storage()  # capture itself must not re-allocate storages

    def __call__(self) -> torch.Tensor:
        self.verify_static_storage()
        # (a) zero channel-parameter grads eagerly (set_to_none=False semantics).
        for p in self._channel_params:
            if p.grad is None:
                p.grad = torch.zeros_like(p)
            else:
                p.grad.zero_()
        # (b) the five eager Kraus stacks: matrix_exp stays eager by design; a
        # fresh autograd subgraph to the channel parameters, one per closure.
        stacks = [channel.kraus() for channel in self._twin.channels]
        # (c) feed the graph's static inputs by address.
        with torch.no_grad():
            for sk, stack in zip(self.static_kraus, stacks):
                sk.copy_(stack)
        # (d) replay: zero static grads -> forward -> loss -> backward-to-leaves.
        self.graph.replay()
        # (e) splice the cotangents into the eager Kraus subgraph; direct read
        # of sk.grad is stream-safe (class docstring), no clone needed.
        torch.autograd.backward(
            stacks, grad_tensors=[sk.grad for sk in self.static_kraus]
        )
        # (f) LBFGS reads / items the static loss after the closure returns.
        return self.static_loss

    def verify_static_storage(self) -> None:
        """The graph reads/writes storages by address: any re-allocation invalidates it."""
        for (name, tensor), ptr in zip(self._tracked, self._tracked_ptrs):
            if tensor.data_ptr() != ptr:
                raise RuntimeError(
                    f"CUDA-graph invariant violated: {name} was re-allocated on the "
                    "graph path; replayed results are invalid"
                )
        for (name, owner), ptr in zip(self._grad_tracked, self._grad_ptrs):
            if owner.grad is None or owner.grad.data_ptr() != ptr:
                raise RuntimeError(
                    f"CUDA-graph invariant violated: {name}.grad was re-allocated on "
                    "the graph path; replayed results are invalid"
                )


def calibrate_window(
    target_histogram,
    *,
    steps: int = 300,
    seed: int = 0,
    device: str | torch.device = "cpu",
    num_kraus: int = 2,
    burn_in: int = DEFAULT_BURN_IN,
    max_burn_in: int = DEFAULT_MAX_BURN_IN,
    fp_tol: float = DEFAULT_FP_TOL,
    rounds: int = 3,
    graph_mode: str = "off",  # reviewer-endorsed default: graphs enter only through
    # the explicitly verified fleet path (m3_parallel --graph), never silently
) -> dict[str, object]:
    """Fit a :class:`WindowTwin` to one window's empirical 256-bin block histogram.

    Mirrors ``calibration.nll.calibrate`` (LBFGS, ``strong_wolfe``, history 50,
    double precision), minimizing the block cross-entropy of the model law
    against the normalized histogram -- the finite-sample held-in form of the
    ledgered observation-NLL (METRICS.md hardware section). The input is the
    histogram alone (isolation contract).

    ``graph_mode`` selects the EXECUTION of the registered fit, never its math
    (pin P1h + the 2026-06-10 execution-mode amendment, docs/metric_results.md
    "M3 PRE-RUN ADJUDICATIONS" item 7): ``"off"`` is the amended HOISTED eager
    closure exactly -- one Kraus evaluation per channel per closure
    (:meth:`WindowTwin.field`), NO graph machinery -- the reference mode every
    equality pin compares against; ``"auto"`` runs the fit through
    STATIC-KRAUS-INPUT CUDA-graph replay when ``device`` is CUDA (eager
    elsewhere); ``"on"`` additionally requires a CUDA device and a working
    capture (raises otherwise). ``torch.matrix_exp`` host-syncs and cannot be
    captured (measured; in the ledger), so the capture boundary sits at the
    five Kraus stacks: ``matrix_exp`` stays eager in EVERY mode, the captured
    graph evaluates the block law from five static Kraus input buffers +
    ``q_logit`` (read by address), and a per-closure eager bridge feeds the
    buffers and splices the Kraus-subgraph backward
    (:class:`_StaticKrausGraphedClosure` -- design, exact bridge/zeroing
    order, and the bit-exactness argument). Replayed losses / gradients / fit
    trajectories must reproduce the amended sequential eager records
    bit-exactly (pinned by ``tests/test_hardware_nll_graph_mode.py``; LBFGS
    hyperparameters are registered and untouched).

    Graph-validity pre-check (eager, before any capture): one ``no_grad``
    evaluation of :func:`fixed_point_residual` at the INITIAL parameters must
    converge at exactly ``burn_in`` rounds (``rounds_used == burn_in`` and
    ``residual <= fp_tol``). A fixed-shape graph cannot represent the eager
    doubling schedule, so otherwise the fit FALLS BACK to the fully eager path
    and the returned dict records ``fallback=True`` (in ``"auto"`` AND
    ``"on"``: an unconverged-at-``burn_in`` schedule is a data property, and
    the registered behavior is the recorded eager fallback, never a wrong
    capture or a refusal). The pre-check cannot change the fit trajectory: the
    hoisted ``field()`` builds its Kraus stacks at call time, so the whole
    evaluation -- field construction included -- runs under ``torch.no_grad()``
    (untracked temporaries), writing neither parameters nor ``.grad``
    buffers; closure evaluations in general have no side effects beyond
    ``.grad``, which the first fit closure re-zeroes before LBFGS ever reads
    it, so the extra evaluation is safe.

    The final law / q_eff / markov / fixed-point recompute below stays eager
    in every mode; the graph object and its private memory pool are local to
    this call and freed with the fit.
    """
    if graph_mode not in GRAPH_MODES:
        raise ValueError(f"graph_mode must be one of {GRAPH_MODES} (got {graph_mode!r})")
    dev = torch.device(device)
    if graph_mode == "on" and dev.type != "cuda":
        raise RuntimeError(f"graph_mode='on' requires a CUDA device (got {dev})")

    counts = torch.as_tensor(target_histogram, dtype=RDTYPE, device=device).reshape(-1)
    target_probs = counts / counts.sum()

    twin = WindowTwin.random(num_kraus=num_kraus, seed=seed, device=device)
    optimizer = torch.optim.LBFGS(
        twin.parameters(),
        lr=1.0,
        max_iter=int(steps),
        line_search_fn="strong_wolfe",
        tolerance_grad=1e-16,
        tolerance_change=1e-18,
        history_size=50,
    )

    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        law = twin.block_law(
            burn_in=burn_in, max_burn_in=max_burn_in, fp_tol=fp_tol, rounds=rounds, device=device
        )
        loss = block_cross_entropy(target_probs, law)
        loss.backward()
        return loss

    graph_used = False
    fallback = False
    fallback_reason: str | None = None
    if graph_mode != "off" and dev.type == "cuda":
        with torch.no_grad():  # hoisted field(): keep its kraus() calls untracked
            residual0, rounds0 = fixed_point_residual(
                twin.field(),
                distance=twin.distance,
                burn_in=burn_in,
                max_burn_in=max_burn_in,
                tol=fp_tol,
                device=device,
            )
        if rounds0 != int(burn_in) or residual0 > float(fp_tol):
            fallback = True
            fallback_reason = (
                f"burn-in not converged at burn_in={int(burn_in)} "
                f"(rounds_used={rounds0}, residual={residual0:.3e}, fp_tol={float(fp_tol):.3e})"
            )
        else:
            try:
                graphed = _StaticKrausGraphedClosure(
                    twin,
                    target_probs,
                    burn_in=burn_in,
                    max_burn_in=max_burn_in,
                    fp_tol=fp_tol,
                    rounds=rounds,
                    device=device,
                )
            except RuntimeError as error:
                if graph_mode == "on":
                    raise
                torch.cuda.synchronize(dev)  # settle the failed capture before going eager
                fallback = True
                fallback_reason = f"capture failed: {error}"
            else:

                def graphed_closure() -> torch.Tensor:
                    return graphed()

                optimizer.step(graphed_closure)
                graphed.verify_static_storage()
                graph_used = True
                del graphed  # frees the graph + its private memory pool with the fit

    if not graph_used:
        optimizer.step(closure)

    with torch.no_grad():
        law = twin.block_law(
            burn_in=burn_in, max_burn_in=max_burn_in, fp_tol=fp_tol, rounds=rounds, device=device
        )
        ce_per_block = float(block_cross_entropy(target_probs, law))
        residual, fp_rounds = fixed_point_residual(
            twin.field(),
            distance=twin.distance,
            burn_in=burn_in,
            max_burn_in=max_burn_in,
            tol=fp_tol,
            device=device,
        )
    return {
        "twin": twin,
        "block_law": law.detach(),
        "ce_per_block": ce_per_block,
        "q_eff": twin.q_eff().detach(),
        "markov_pairs": twin.markov_pairs(),
        "fp_residual": residual,
        "fp_rounds": fp_rounds,
        "seed": int(seed),
        "graph_used": graph_used,
        "fallback": fallback,
        "fallback_reason": fallback_reason,
    }
