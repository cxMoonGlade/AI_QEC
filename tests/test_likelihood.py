import pytest
import torch

from scope_static.fault_graph import FaultGraph
from scope_static.likelihood import (
    build_window_nll_caches,
    exact_dem_nll,
    exact_detector_dem_nll,
    local_window_exact_nll_from_caches,
    local_window_exact_nll,
    parity_distribution,
    projected_window_mask_states,
    resolve_likelihood_backend,
)
from scope_static.windows import ObservationWindow, build_windows_from_config, build_windows_from_detector_geometry


def _tiny_graph():
    masks = torch.tensor(
        [
            [1, 0, 1],
            [0, 1, 1],
        ],
        dtype=torch.bool,
    )
    return FaultGraph.from_raw_masks(
        masks,
        num_detectors=2,
        num_observables=0,
        residual_rank=1,
        canonicalize_duplicate_masks=False,
    )


def test_exact_distribution_matches_closed_form():
    graph = _tiny_graph()
    logits = torch.tensor([-1.2, -2.0, -3.0], dtype=torch.float64, requires_grad=True)
    dist = parity_distribution(graph, logits)
    probs = torch.sigmoid(logits)
    expected = torch.zeros(4, dtype=torch.float64)
    for e0 in [0, 1]:
        for e1 in [0, 1]:
            for e2 in [0, 1]:
                prob = (
                    (probs[0] if e0 else 1 - probs[0])
                    * (probs[1] if e1 else 1 - probs[1])
                    * (probs[2] if e2 else 1 - probs[2])
                )
                state = (e0 ^ e2) + 2 * (e1 ^ e2)
                expected[state] = expected[state] + prob
    assert torch.allclose(dist, expected)
    assert torch.isclose(dist.sum(), torch.tensor(1.0, dtype=torch.float64))


def test_aggregated_nll_matches_unaggregated_and_has_gradients():
    graph = _tiny_graph()
    logits = torch.tensor([-1.2, -2.0, -3.0], dtype=torch.float64, requires_grad=True)
    observations = torch.tensor(
        [
            [0, 0],
            [0, 0],
            [1, 0],
            [1, 1],
        ],
        dtype=torch.bool,
    )
    nll_agg = exact_dem_nll(graph, logits, observations, aggregate_unique=True)
    nll_raw = exact_dem_nll(graph, logits, observations, aggregate_unique=False)
    assert torch.allclose(nll_agg, nll_raw)
    nll_agg.backward()
    assert logits.grad is not None
    assert torch.isfinite(logits.grad).all()


def test_window_projection_and_local_nll_match_full_window():
    graph = _tiny_graph()
    logits = torch.tensor([-1.2, -2.0, -3.0], dtype=torch.float64, requires_grad=True)
    observations = torch.tensor(
        [
            [0, 0],
            [1, 0],
            [1, 1],
        ],
        dtype=torch.bool,
    )
    fault_ids, mask_states = projected_window_mask_states(graph, (0,))
    assert fault_ids.tolist() == [0, 2]
    assert mask_states.tolist() == [1, 1]

    full_window = ObservationWindow(name="full", bits=(0, 1), kind="test")
    local_nll = local_window_exact_nll(graph, logits, observations, [full_window])
    cached_nll = local_window_exact_nll_from_caches(
        logits,
        build_window_nll_caches(graph, observations, [full_window]),
    )
    global_nll = exact_dem_nll(graph, logits, observations)
    assert torch.allclose(local_nll, global_nll)
    assert torch.allclose(cached_nll, global_nll)
    local_nll.backward()
    assert logits.grad is not None
    assert torch.isfinite(logits.grad).all()


def test_detector_geometry_window_builder_starts_with_local_windows():
    graph = _tiny_graph()
    windows = build_windows_from_detector_geometry(graph, include_radius1=False, max_window_bits=2)
    assert {window.kind for window in windows} >= {"single_detector", "detector_pair"}
    assert all(window.size <= 2 for window in windows)


def test_window_config_can_limit_count_for_fast_smoke_runs():
    graph = _tiny_graph()
    windows = build_windows_from_config(
        graph,
        {
            "enabled": True,
            "builders": ["detector_geometry"],
            "include_radius1": False,
            "max_window_bits": 2,
            "max_windows": 2,
        },
    )
    assert len(windows) == 2


def test_detector_nll_ignores_logical_only_faults():
    masks = torch.tensor(
        [
            [1, 0],
            [0, 1],
        ],
        dtype=torch.bool,
    )
    graph = FaultGraph.from_raw_masks(
        masks,
        num_detectors=1,
        num_observables=1,
        residual_rank=0,
        canonicalize_duplicate_masks=False,
    )
    logits = torch.tensor([-2.0, -0.3], dtype=torch.float64, requires_grad=True)
    observations = torch.tensor(
        [
            [0, 0],
            [1, 0],
            [1, 1],
        ],
        dtype=torch.bool,
    )

    detector_nll = exact_detector_dem_nll(graph, logits, observations)
    p_detector = torch.sigmoid(logits[0])
    expected = -(torch.log1p(-p_detector) + 2 * torch.log(p_detector)) / 3
    assert torch.allclose(detector_nll, expected)

    detector_nll.backward()
    assert logits.grad is not None
    assert torch.isclose(logits.grad[1], torch.tensor(0.0, dtype=torch.float64))


def test_cuda_tensor_path_matches_cpu_when_available():
    if not torch.cuda.is_available():
        return
    graph = _tiny_graph()
    cpu_logits = torch.tensor([-1.2, -2.0, -3.0], dtype=torch.float64, requires_grad=True)
    cuda_logits = cpu_logits.detach().clone().cuda().requires_grad_(True)
    observations = torch.tensor([[0, 0], [1, 1]], dtype=torch.bool)
    cpu_nll = exact_dem_nll(graph, cpu_logits, observations)
    cuda_nll = exact_dem_nll(graph, cuda_logits, observations)
    assert torch.allclose(cuda_nll.cpu(), cpu_nll)
    cpu_nll.backward()
    cuda_nll.backward()
    assert torch.allclose(cuda_logits.grad.cpu(), cpu_logits.grad)


def test_auto_backend_resolves_to_pytorch_on_cpu():
    logits = torch.tensor([-1.0], dtype=torch.float64)
    assert resolve_likelihood_backend(logits, "auto") == "pytorch"


def test_cuda_extension_forward_and_backward_match_pytorch_when_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available")
    graph = _tiny_graph()
    base_logits = torch.tensor([-1.2, -2.0, -3.0], device="cuda", dtype=torch.float64)
    oracle_logits = base_logits.detach().clone().requires_grad_(True)
    extension_logits = base_logits.detach().clone().requires_grad_(True)
    observations = torch.tensor([[0, 0], [1, 1], [1, 0]], dtype=torch.bool)

    try:
        oracle_nll = exact_dem_nll(graph, oracle_logits, observations, backend="pytorch")
        extension_nll = exact_dem_nll(graph, extension_logits, observations, backend="cuda_extension")
    except RuntimeError as exc:
        pytest.skip(f"CUDA extension is not buildable in this environment: {exc}")

    assert torch.allclose(extension_nll, oracle_nll, atol=1e-12, rtol=1e-12)
    oracle_nll.backward()
    extension_nll.backward()
    assert extension_logits.grad is not None
    assert torch.allclose(extension_logits.grad, oracle_logits.grad, atol=1e-12, rtol=1e-12)


def test_cuda_extension_forward_inference_has_no_grad_when_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available")
    graph = _tiny_graph()
    logits = torch.tensor([-1.2, -2.0, -3.0], device="cuda", dtype=torch.float64)
    try:
        dist = parity_distribution(graph, logits, backend="cuda_extension")
    except RuntimeError as exc:
        pytest.skip(f"CUDA extension is not buildable in this environment: {exc}")

    assert not dist.requires_grad
    assert torch.allclose(dist, parity_distribution(graph, logits, backend="pytorch"), atol=1e-12, rtol=1e-12)


def test_auto_backend_matches_best_available_backend_when_cuda_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available")
    graph = _tiny_graph()
    logits = torch.tensor([-1.2, -2.0, -3.0], device="cuda", dtype=torch.float64)
    resolved = resolve_likelihood_backend(logits, "auto")
    assert resolved in {"cuda_extension", "pytorch"}
    auto_dist = parity_distribution(graph, logits, backend="auto")
    expected_dist = parity_distribution(graph, logits, backend=resolved)
    assert torch.allclose(auto_dist, expected_dist)
