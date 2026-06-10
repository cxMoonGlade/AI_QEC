"""Execution-amendment equality pins: hoisted field + CUDA-graph fits (R2-lite M3).

Binding registration: docs/metric_results.md "M3 PRE-RUN ADJUDICATIONS" item 7
(recorded 2026-06-10, BEFORE any production fit). The twin's channel field
evaluates each channel's Kraus stack ONCE per closure (hoisted); graph
execution is a static-Kraus-input CUDA-graph capture with ``torch.matrix_exp``
kept eager OUTSIDE the graph (it host-copies during capture). The registered
pins implemented here:

  (i)  PIN A -- amended (hoisted) closure vs the naive per-(t, i) closure:
       law ``torch.equal`` (forward bit-exact: identical tensor values into
       identical ops in identical order); every channel-parameter and
       ``q_logit`` gradient <= 1e-12 RELATIVE (the backward differs only by
       ulp re-association of the per-round cotangent sum through the linear
       ``matrix_exp`` vjp). Runs on CPU AND CUDA -- the amendment is not a
       CUDA-only claim.
  (ii) PIN B / PIN C -- graph execution vs the amended-eager reference:
       closure losses and ALL ``.grad`` buffers ``torch.equal`` per replay
       (PIN B drives an in-test REFERENCE capture of the registered scheme,
       deliberately independent of the production capture internals), and a
       whole short-fit record bit-exact through the public
       ``calibrate_window`` graph_mode "on" vs "off" (PIN C). The
       full-registered-steps real-window executable of pin (ii) is
       ``outputs/m3_graph_realpin.py``.
       PIN D2: the burn-in pre-check fallback must reproduce the eager fit
       bit-exactly while recording ``fallback=True``.

Bit-exact means ``torch.equal`` / ``==`` -- never ``allclose``; any mismatch
fails loudly so the orchestrator adjudicates. No dataset needed: the target
histogram is synthesized from a known in-class stationary block law
(heterogeneous flip-channel field + readout convolution -- the
``m3_report.in_class_block_law`` idiom, inlined to avoid the hardware stack).
"""
from __future__ import annotations

import os

import pytest
import torch

from qec_twin.calibration import hardware_nll
from qec_twin.forward.cptp_channel import CDTYPE, RDTYPE
from qec_twin.forward.exact.steady_state import (
    DEFAULT_BURN_IN,
    DEFAULT_FP_TOL,
    DEFAULT_MAX_BURN_IN,
    fixed_point_residual,
    simulate_steady_block,
)
from qec_twin.numerics import NUMERICAL_ZERO

cuda_ok = torch.cuda.is_available()
requires_cuda = pytest.mark.skipif(not cuda_ok, reason="CUDA unavailable")

GRAPH_WARMUP_ITERS = 3  # official whole-network-capture recipe: ~3 eager side-stream iters

SYNTH_SHOTS = 4.0e5
SYNTH_F = (0.008, 0.012, 0.010, 0.014, 0.009)  # heterogeneous (the P1a pin idiom)
SYNTH_DELTA = 0.002
SYNTH_Q = (0.012, 0.015, 0.013, 0.011)

_RESULT_TENSOR_KEYS = ("block_law", "q_eff", "markov_pairs")
_RESULT_SCALAR_KEYS = ("ce_per_block", "fp_residual", "fp_rounds", "seed")

# The registered relative gradient gap for the hoisted-vs-naive backward
# (re-association of a linear vjp's cotangent sum; metric_results.md item 7 pin (i)).
PIN_A_REL_GRAD_TOL = 1.0e-12


@pytest.fixture()
def deterministic():
    """The fleet's execution contract (``m3_parallel._enable_determinism``):
    deterministic algorithms ON so bit-exactness is well-posed. Restores both
    the torch flag and the env var to their prior state."""
    env_was_unset = "CUBLAS_WORKSPACE_CONFIG" not in os.environ
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    previous = torch.are_deterministic_algorithms_enabled()
    torch.use_deterministic_algorithms(True)
    yield
    torch.use_deterministic_algorithms(previous)
    if env_was_unset:
        os.environ.pop("CUBLAS_WORKSPACE_CONFIG", None)


def _flip_kraus(p01: float, p10: float) -> torch.Tensor:
    """Strictly diagonal/antidiagonal flip-channel Kraus (in-class member)."""
    p01_t = torch.tensor(p01, dtype=RDTYPE)
    p10_t = torch.tensor(p10, dtype=RDTYPE)
    zero = torch.zeros((), dtype=CDTYPE)
    k0 = torch.stack(
        [
            torch.stack([torch.sqrt(1 - p01_t).to(CDTYPE), zero]),
            torch.stack([zero, torch.sqrt(1 - p10_t).to(CDTYPE)]),
        ]
    )
    k1 = torch.stack(
        [
            torch.stack([zero, torch.sqrt(p10_t).to(CDTYPE)]),
            torch.stack([torch.sqrt(p01_t).to(CDTYPE), zero]),
        ]
    )
    return torch.stack([k0, k1])


def _synth_histogram(device: str) -> torch.Tensor:
    """Expected block counts of a known in-class stationary law (no dataset)."""
    stacks = [_flip_kraus(f + SYNTH_DELTA, f - SYNTH_DELTA).to(device) for f in SYNTH_F]
    field = lambda t, i: stacks[i]  # noqa: E731
    q = torch.tensor(SYNTH_Q, dtype=RDTYPE, device=device)
    with torch.no_grad():
        law = simulate_steady_block(field, device=device)
        law = hardware_nll.readout_convolution(law, q)
    return (law * SYNTH_SHOTS).cpu()


def _target_probs(device: str) -> torch.Tensor:
    counts = torch.as_tensor(_synth_histogram(device), dtype=RDTYPE, device=device).reshape(-1)
    return counts / counts.sum()


def _counting(bound_method, counter: dict):
    """Wrap a bound method to count invocations (anti-vacuity instrumentation)."""

    def counted(*args, **kwargs):
        counter["count"] += 1
        return bound_method(*args, **kwargs)

    return counted


def _assert_results_bit_exact(result_a: dict, result_b: dict) -> None:
    for key in _RESULT_TENSOR_KEYS:
        assert torch.equal(result_a[key], result_b[key]), (
            key,
            float((result_a[key] - result_b[key]).abs().max()),
        )
    for key in _RESULT_SCALAR_KEYS:
        assert result_a[key] == result_b[key], (key, result_a[key], result_b[key])


# --------------------------------------------------------------------------- #
# PIN A -- amendment pin (i): hoisted closure vs naive per-(t, i) closure      #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=requires_cuda)])
def test_pin_a_hoisted_closure_matches_naive_closure(deterministic, device) -> None:
    """PIN A: amended field (Kraus stacks hoisted, once per closure) vs the
    naive field re-evaluating ``channels[i].kraus()`` at every (t, i).

    Law ``torch.equal``; every parameter gradient within the registered
    1e-12 RELATIVE gap ``max|g_h - g_n| / max(|g_n|.max(), tiny)``.

    Anti-vacuity: Kraus-call counters prove the two arms genuinely differ in
    evaluation count -- were the hoisted arm secretly naive (or vice versa)
    the comparison would be an identical computation against itself and the
    pin would pass without testing the amendment at all.
    """
    target_probs = _target_probs(device)

    twin_hoisted = hardware_nll.WindowTwin.random(num_kraus=2, seed=0, device=device)
    twin_naive = hardware_nll.WindowTwin.random(num_kraus=2, seed=0, device=device)
    for p_h, p_n in zip(twin_hoisted.parameters(), twin_naive.parameters()):
        assert torch.equal(p_h, p_n)  # same seed -> bit-identical leaves

    hoisted_calls = {"count": 0}
    for channel in twin_hoisted.channels:
        channel.kraus = _counting(channel.kraus, hoisted_calls)

    # Hoisted arm: the amended closure forward exactly as calibrate_window
    # runs it (public block_law: hoisted field -> stationary law -> readout
    # convolution), then backward.
    law_hoisted = twin_hoisted.block_law(
        burn_in=DEFAULT_BURN_IN,
        max_burn_in=DEFAULT_MAX_BURN_IN,
        fp_tol=DEFAULT_FP_TOL,
        rounds=3,
        device=device,
    )
    loss_hoisted = hardware_nll.block_cross_entropy(target_probs, law_hoisted)
    loss_hoisted.backward()

    # Naive arm: per-(t, i) Kraus re-evaluation fed straight into the same
    # pipeline on a fresh same-seed twin (the closure semantics the amendment
    # replaced -- it never produced a production record).
    naive_calls = {"count": 0}

    def naive_field(t, i):
        naive_calls["count"] += 1
        return twin_naive.channels[i].kraus()

    law_naive = simulate_steady_block(
        naive_field,
        distance=twin_naive.distance,
        burn_in=DEFAULT_BURN_IN,
        max_burn_in=DEFAULT_MAX_BURN_IN,
        fp_tol=DEFAULT_FP_TOL,
        rounds=3,
        device=device,
    )
    law_naive = hardware_nll.readout_convolution(law_naive, twin_naive.q_eff())
    loss_naive = hardware_nll.block_cross_entropy(target_probs, law_naive)
    loss_naive.backward()

    # Anti-vacuity: hoisted evaluates each stack ~once per closure; naive
    # re-evaluates per (t, i) across init + burn-in + extraction rounds.
    n_channels = hardware_nll.WINDOW_DISTANCE
    assert hoisted_calls["count"] <= 2 * n_channels, hoisted_calls
    assert naive_calls["count"] >= (DEFAULT_BURN_IN + 3) * n_channels, naive_calls
    assert hoisted_calls["count"] < naive_calls["count"]
    # Anti-vacuity: nontrivial objective and a nonzero reference gradient.
    assert float(loss_naive) > 0.0
    grads_naive = [p.grad for p in twin_naive.parameters()]
    assert all(g is not None for g in grads_naive)
    assert max(float(g.abs().max()) for g in grads_naive) > 0.0

    assert torch.equal(law_hoisted, law_naive)  # registered: forward law bit-exact
    assert torch.equal(loss_hoisted, loss_naive)

    max_rel_gap = 0.0
    for p_h, p_n in zip(twin_hoisted.parameters(), twin_naive.parameters()):
        assert p_h.grad is not None and p_n.grad is not None
        denom = max(float(p_n.grad.abs().max()), NUMERICAL_ZERO)
        rel_gap = float((p_h.grad - p_n.grad).abs().max()) / denom
        max_rel_gap = max(max_rel_gap, rel_gap)
    print(
        f"PIN A [{device}]: max relative gradient gap hoisted-vs-naive = {max_rel_gap:.3e} "
        f"(kraus calls: hoisted {hoisted_calls['count']}, naive {naive_calls['count']})"
    )
    assert max_rel_gap <= PIN_A_REL_GRAD_TOL, max_rel_gap


# --------------------------------------------------------------------------- #
# PIN B -- static-Kraus-input capture: per-replay closure equality (CUDA)      #
# --------------------------------------------------------------------------- #
class _StaticKrausGraphClosure:
    """In-test REFERENCE implementation of the registered capture scheme.

    Registration item 7: graph execution = static-Kraus-input capture with
    ``torch.matrix_exp`` eager OUTSIDE the graph (it performs a host copy
    during capture). The graph records zero-grad + the fixed-``burn_in``
    stationary law (``check_residual=False``: fixed shapes, no host sync) +
    readout convolution + cross-entropy + backward, reading 5 STATIC Kraus
    leaves and ``q_logit`` by address. Each call refreshes the static leaves
    from an eager ``kraus()`` evaluation, replays, then bridges the graph's
    d(loss)/d(Kraus) cotangents through the eager ``matrix_exp`` vjp into the
    channel-parameter ``.grad`` buffers.

    Deliberately independent of the production capture internals in
    ``hardware_nll`` (which this build replaces): PIN B pins the SCHEME's
    per-replay bit-exactness at closure granularity; PIN C and
    ``outputs/m3_graph_realpin.py`` pin the production path end-to-end through
    the public ``calibrate_window``.
    """

    def __init__(
        self,
        twin,
        optimizer,
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
        self.twin = twin
        self.optimizer = optimizer
        with torch.no_grad():
            stacks = [channel.kraus() for channel in twin.channels]
        self.static_kraus = [s.clone().requires_grad_(True) for s in stacks]
        static = self.static_kraus

        def static_field(t, i):
            return static[i]

        def captured_body() -> torch.Tensor:
            # In-graph zeroing on stable buffers makes every replay a fresh
            # closure (zero-then-accumulate == fresh grad assignment bit-for-bit).
            for s in static:
                if s.grad is not None:
                    s.grad.zero_()
            if twin.q_logit.grad is not None:
                twin.q_logit.grad.zero_()
            law = simulate_steady_block(
                static_field,
                distance=twin.distance,
                burn_in=burn_in,
                max_burn_in=max_burn_in,
                fp_tol=fp_tol,
                rounds=rounds,
                device=device,
                check_residual=False,
            )
            law = hardware_nll.readout_convolution(law, twin.q_eff())
            loss = hardware_nll.block_cross_entropy(target_probs, law)
            loss.backward()
            return loss

        # Official whole-network-capture recipe: eager warmup iterations on a
        # side stream (allocates stable .grad buffers, initializes handles /
        # cached masks outside the capture), then a single capture.
        side = torch.cuda.Stream(device=dev)
        side.wait_stream(torch.cuda.current_stream(dev))
        with torch.cuda.stream(side):
            for _ in range(GRAPH_WARMUP_ITERS):
                captured_body()
        torch.cuda.current_stream(dev).wait_stream(side)
        self.graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(self.graph):
            self.static_loss = captured_body()
        self._static_ptrs = self._current_ptrs()

    def _current_ptrs(self) -> list[int]:
        ptrs = [s.data_ptr() for s in self.static_kraus]
        ptrs += [s.grad.data_ptr() for s in self.static_kraus]
        ptrs.append(self.twin.q_logit.grad.data_ptr())
        return ptrs

    def verify_static_storage(self) -> None:
        """The graph reads storages by address: any re-allocation invalidates it."""
        if self._current_ptrs() != self._static_ptrs:
            raise RuntimeError(
                "CUDA-graph invariant violated: a static Kraus input / grad buffer "
                "was re-allocated; replayed results are invalid"
            )

    def __call__(self) -> torch.Tensor:
        # Same storage discipline as the eager closure: zero ALL param grads
        # in place (set_to_none would drop the q_logit buffer the graph writes).
        self.optimizer.zero_grad(set_to_none=False)
        stacks = [channel.kraus() for channel in self.twin.channels]  # eager matrix_exp
        with torch.no_grad():
            for static_input, fresh in zip(self.static_kraus, stacks):
                static_input.copy_(fresh)
        self.graph.replay()
        # Eager bridge: the graph's d(loss)/d(Kraus) through the matrix_exp vjp
        # accumulates into the channel-parameter .grad buffers (zeroed above).
        torch.autograd.backward(stacks, [s.grad for s in self.static_kraus])
        return self.static_loss


@requires_cuda
def test_pin_b_graph_replays_equal_hoisted_eager_closures(deterministic) -> None:
    """PIN B: N=5 graph replays == N=5 hoisted-eager closures, loss AND all grads.

    One twin, one optimizer: replays and eager closures hit the SAME parameter
    and ``.grad`` storages, so any replay-accumulation bug (e.g. missing zero
    kernels doubling grads on replay 2, or a stale static input) fails here at
    the exact iteration index.
    """
    device = "cuda"
    target_probs = _target_probs(device)

    twin = hardware_nll.WindowTwin.random(num_kraus=2, seed=0, device=device)
    params = twin.parameters()
    optimizer = torch.optim.LBFGS(
        params,
        lr=1.0,
        max_iter=1,
        line_search_fn="strong_wolfe",
        tolerance_grad=1e-16,
        tolerance_change=1e-18,
        history_size=50,
    )

    # Graph-validity precondition (what calibrate_window's pre-check asserts):
    # the doubling schedule converges at exactly burn_in, so the captured
    # check_residual=False forward computes the identical law.
    residual0, rounds0 = fixed_point_residual(
        twin.field(),
        distance=twin.distance,
        burn_in=DEFAULT_BURN_IN,
        max_burn_in=DEFAULT_MAX_BURN_IN,
        tol=DEFAULT_FP_TOL,
        device=device,
    )
    assert rounds0 == DEFAULT_BURN_IN and residual0 <= DEFAULT_FP_TOL, (residual0, rounds0)

    graphed = _StaticKrausGraphClosure(
        twin,
        optimizer,
        target_probs,
        burn_in=DEFAULT_BURN_IN,
        max_burn_in=DEFAULT_MAX_BURN_IN,
        fp_tol=DEFAULT_FP_TOL,
        rounds=3,
        device=device,
    )
    graph_evals = []
    for _ in range(5):
        loss = graphed()
        graph_evals.append(
            (loss.detach().clone(), [p.grad.detach().clone() for p in params])
        )

    # Eager arm: the amended hoisted closure (calibrate_window's "off"
    # reference) on the same storages.
    eager_evals = []
    for _ in range(5):
        optimizer.zero_grad(set_to_none=False)
        law = twin.block_law(
            burn_in=DEFAULT_BURN_IN,
            max_burn_in=DEFAULT_MAX_BURN_IN,
            fp_tol=DEFAULT_FP_TOL,
            rounds=3,
            device=device,
        )
        loss = hardware_nll.block_cross_entropy(target_probs, law)
        loss.backward()
        eager_evals.append(
            (loss.detach().clone(), [p.grad.detach().clone() for p in params])
        )

    graphed.verify_static_storage()
    # Anti-vacuity: nontrivial objective, nonzero reference gradients (two
    # all-zero arms would compare equal without testing the replay at all).
    assert float(eager_evals[0][0]) > 0.0
    assert max(float(g.abs().max()) for g in eager_evals[0][1]) > 0.0

    for i in range(5):
        loss_graph, grads_graph = graph_evals[i]
        loss_eager, grads_eager = eager_evals[i]
        assert torch.equal(loss_graph, loss_eager), (
            i,
            float(loss_graph),
            float(loss_eager),
        )
        for j, (grad_graph, grad_eager) in enumerate(zip(grads_graph, grads_eager)):
            assert torch.equal(grad_graph, grad_eager), (
                i,
                j,
                float((grad_graph - grad_eager).abs().max()),
            )


# --------------------------------------------------------------------------- #
# PIN C -- short-fit trajectory through the public calibrate_window (CUDA)     #
# --------------------------------------------------------------------------- #
@requires_cuda
def test_pin_c_short_fit_trajectory_bit_exact(deterministic) -> None:
    """PIN C: steps=25, same seed -- graph_mode='on' vs 'off' records bit-exact.

    ``graph_used`` must be True on the 'on' arm (a silent eager fallback would
    make this comparison eager-vs-eager, i.e. vacuous) and False with no
    fallback on the 'off' reference arm.
    """
    hist = _synth_histogram("cuda")
    result_graph = hardware_nll.calibrate_window(
        hist, steps=25, seed=0, device="cuda", graph_mode="on"
    )
    assert result_graph["graph_used"] is True
    assert result_graph["fallback"] is False
    assert not result_graph["fallback_reason"]
    result_eager = hardware_nll.calibrate_window(
        hist, steps=25, seed=0, device="cuda", graph_mode="off"
    )
    assert result_eager["graph_used"] is False
    assert result_eager["fallback"] is False
    assert float(result_eager["ce_per_block"]) > 0.0  # nontrivial fit, not a degenerate record
    _assert_results_bit_exact(result_graph, result_eager)


# --------------------------------------------------------------------------- #
# PIN D2 -- burn-in pre-check fallback reproduces the eager fit (CUDA)         #
# --------------------------------------------------------------------------- #
@requires_cuda
@pytest.mark.parametrize("mode", ["auto", "on"])
def test_pin_d2_precheck_fallback_matches_eager(deterministic, mode) -> None:
    """PIN D2: pre-check miss -> recorded eager fallback, bit-exact vs 'off'.

    The unreachable ``fp_tol=0.0`` forces the registered non-convergence
    condition (residual > fp_tol at exactly ``burn_in`` rounds -- the code
    path a slow-mixing field would take) deterministically;
    ``max_burn_in == burn_in`` caps the eager doubling schedule at 40 rounds
    so the comparison fit stays cheap. The fallback applies in 'auto' AND
    'on': an unconverged schedule is a data property, never a capture-support
    failure, and the registered behavior is the recorded eager fallback.
    """
    hist = _synth_histogram("cuda")
    kwargs = dict(steps=5, seed=0, device="cuda", burn_in=40, max_burn_in=40, fp_tol=0.0)
    result_fallback = hardware_nll.calibrate_window(hist, graph_mode=mode, **kwargs)
    assert result_fallback["fallback"] is True
    assert result_fallback["graph_used"] is False
    assert result_fallback["fallback_reason"]  # recorded, never silent
    result_eager = hardware_nll.calibrate_window(hist, graph_mode="off", **kwargs)
    assert result_eager["fallback"] is False
    assert result_eager["graph_used"] is False
    _assert_results_bit_exact(result_fallback, result_eager)


# --------------------------------------------------------------------------- #
# Mode plumbing (CPU)                                                          #
# --------------------------------------------------------------------------- #
def test_graph_mode_validation_and_cpu_semantics(deterministic) -> None:
    """Mode plumbing: bad mode raises, 'on' requires CUDA, 'auto' on CPU is eager."""
    with pytest.raises(ValueError):
        hardware_nll.calibrate_window(torch.ones(256), steps=1, device="cpu", graph_mode="never")
    with pytest.raises(RuntimeError):
        hardware_nll.calibrate_window(torch.ones(256), steps=1, device="cpu", graph_mode="on")
    result = hardware_nll.calibrate_window(
        _synth_histogram("cpu"), steps=1, seed=0, device="cpu", graph_mode="auto"
    )
    assert result["graph_used"] is False
    assert result["fallback"] is False
