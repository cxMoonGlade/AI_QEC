import math

import pytest
import torch

from scope_static.dem.fault_graph import FaultGraph
from scope_static.dem.likelihood import (
    build_window_batch_nll_cache,
    build_window_batch_nll_cache_from_observations,
    build_window_nll_caches,
    exact_dem_nll,
    exact_detector_dem_nll,
    local_window_exact_nll_batched_from_cache,
    local_window_exact_nll_from_caches,
    local_window_exact_nll,
    local_window_cuda_kernel_audit,
    local_window_workload_audit,
    parity_distribution,
    projected_window_mask_states,
    resolve_likelihood_backend,
    subset_window_batch_nll_cache,
)
from scope_static.dem.likelihoods.local_window_parity import ExactLocalWindowParityLikelihood
from scope_static.dem.objectives import build_likelihood_objective
from scope_static.dem.fields import HardOrbitFaultLogitField
from scope_static.dem.metrics import (
    augment_model_comparison_metrics,
    empirical_window_entropy,
    empirical_window_entropy_from_batch_cache,
    evaluate_real_data_model,
)
from scope_static.dem.training import fit_field
from scope_static.dem.windows import (
    ObservationWindow,
    WindowPlan,
    build_windows_from_config,
    build_windows_from_detector_geometry,
    build_windows_from_logical_observables,
    window_coverage_audit_dict,
)


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


def _tiny_logical_graph():
    masks = torch.tensor(
        [
            [1, 0, 1, 1, 1, 0, 0],
            [0, 1, 1, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1, 1],
            [0, 0, 0, 1, 1, 1, 1],
        ],
        dtype=torch.bool,
    )
    return FaultGraph.from_raw_masks(
        masks,
        num_detectors=3,
        num_observables=1,
        residual_rank=1,
        canonicalize_duplicate_masks=False,
    )


def _one_bit_graph():
    masks = torch.tensor([[1]], dtype=torch.bool)
    return FaultGraph.from_raw_masks(
        masks,
        num_detectors=1,
        num_observables=0,
        residual_rank=0,
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


def test_likelihood_probability_floor_caps_tiny_probabilities():
    graph = _one_bit_graph()
    observations = torch.tensor([[1]], dtype=torch.bool)

    for dtype, floor, atol in ((torch.float64, 1e-12, 1e-12), (torch.float32, 1e-7, 1e-6)):
        logits = torch.tensor([-1000.0], dtype=dtype, requires_grad=True)

        loss = exact_dem_nll(graph, logits, observations)

        expected = torch.tensor(-math.log(floor), dtype=dtype)
        assert torch.allclose(loss, expected, atol=atol, rtol=0)
        loss.backward()
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


def test_logical_observable_windows_deduplicate_fault_supports():
    graph = _tiny_logical_graph()

    windows = build_windows_from_logical_observables(graph, max_window_bits=4)
    audit = window_coverage_audit_dict(graph, windows)

    assert audit["logical_fault_support_raw"] == 4
    assert audit["logical_fault_support_unique"] == 3
    assert audit["duplicate_logical_windows_removed"] == 1
    assert audit["logical_window_type_counts"]["logical_single"] == 1
    assert audit["logical_window_type_counts"]["logical_fault_support"] == 3
    assert audit["logical_bit_coverage"]["fraction_logical_bits_covered"] == pytest.approx(1.0)
    assert audit["fraction_logical_faults_with_support_window"] == pytest.approx(1.0)


def test_window_family_budgets_do_not_silently_drop_logical_windows():
    graph = _tiny_logical_graph()
    plan = WindowPlan.from_config(
        graph,
        {
            "enabled": True,
            "builders": ["detector_geometry", "logical_observable"],
            "include_radius1": False,
            "include_boundary_logical": False,
            "max_window_bits": 4,
            "max_windows": 1,
            "window_family_budgets": {
                "single_detector": "all",
                "detector_pair": 1,
                "logical_single": "all",
                "logical_detector_pair": 1,
                "logical_fault_support": "all",
            },
        },
    )

    audit = plan.audit_dict()
    coverage = window_coverage_audit_dict(graph, list(plan.windows))

    assert audit["window_family_budget_mode"] == "family_aware"
    assert audit["window_family_counts"]["single_detector"] == 3
    assert audit["window_family_counts"]["detector_pair"] == 1
    assert audit["window_family_counts"]["logical_single"] == 1
    assert audit["window_family_counts"]["logical_fault_support"] == 3
    assert coverage["num_windows_containing_logical"] >= 4
    assert coverage["logical_fault_support_selected"] == 3


def test_window_plan_carries_audit_metadata():
    graph = _tiny_graph()
    plan = WindowPlan.from_config(
        graph,
        {
            "enabled": True,
            "builders": ["detector_geometry"],
            "include_radius1": False,
            "max_window_bits": 2,
        },
    )
    audit = plan.audit_dict()
    assert len(plan) == audit["num_windows"]
    assert audit["window_plan_enabled"] is True
    assert audit["window_plan_builders"] == ["detector_geometry"]


def test_likelihood_objective_plan_owns_local_window_cache():
    graph = _tiny_graph()
    logits = torch.tensor([-1.2, -2.0, -3.0], dtype=torch.float64, requires_grad=True)
    observations = torch.tensor([[0, 0], [1, 0], [1, 1]], dtype=torch.bool)
    window = ObservationWindow(name="full", bits=(0, 1), kind="test")
    objective = build_likelihood_objective(
        graph,
        observations,
        likelihood_objective="local_exact",
        observation_mode="full",
        windows=[window],
    )

    assert objective.audit_dict()["num_train_windows"] == 1
    assert torch.allclose(objective.loss(logits), exact_dem_nll(graph, logits, observations))


def test_exact_local_window_parity_likelihood_is_the_public_local_interface():
    graph = _tiny_graph()
    logits = torch.tensor([-1.2, -2.0, -3.0], dtype=torch.float64, requires_grad=True)
    observations = torch.tensor([[0, 0], [1, 0], [1, 1]], dtype=torch.bool)
    window = ObservationWindow(name="full", bits=(0, 1), kind="test")

    likelihood = ExactLocalWindowParityLikelihood.prepare(
        graph,
        observations,
        windows=[window],
        backend="pytorch",
        device="cpu",
    )

    audit = likelihood.audit_dict()
    assert audit["likelihood_objective"] == "exact_local_window_bernoulli_parity"
    assert audit["num_windows"] == 1
    assert audit["likelihood_gpu_batch_available"] is False
    assert audit["adapter"] == "python_window_loop_exact"
    assert torch.allclose(likelihood.loss(logits), exact_dem_nll(graph, logits, observations))


def test_likelihood_objective_audit_names_local_window_parity_contract():
    graph = _tiny_graph()
    observations = torch.tensor([[0, 0], [1, 0], [1, 1]], dtype=torch.bool)
    window = ObservationWindow(name="full", bits=(0, 1), kind="test")

    objective = build_likelihood_objective(
        graph,
        observations,
        likelihood_objective="local_exact",
        observation_mode="full",
        windows=[window],
    )

    audit = objective.audit_dict()
    assert audit["train_likelihood_math_objective"] == "exact_local_window_bernoulli_parity"
    assert audit["train_likelihood_gpu_batch_available"] is False


def test_real_data_metrics_report_logical_specific_window_nlls():
    graph = _tiny_logical_graph()
    windows = build_windows_from_logical_observables(graph, max_window_bits=4)
    observations = torch.tensor(
        [
            [0, 0, 0, 0],
            [1, 0, 0, 1],
            [0, 1, 1, 1],
            [1, 1, 0, 0],
        ],
        dtype=torch.bool,
    )
    logits = torch.full((graph.M,), -2.0, dtype=torch.float64)

    metrics = evaluate_real_data_model(
        graph,
        logits,
        observations,
        backend="pytorch",
        windows=windows,
    )

    assert metrics["heldout_combined_window_nll"] == metrics["heldout_local_window_nll"]
    assert metrics["heldout_combined_window_empirical_entropy"] is not None
    assert metrics["heldout_combined_window_excess_nll"] == pytest.approx(
        metrics["heldout_combined_window_nll"] - metrics["heldout_combined_window_empirical_entropy"]
    )
    assert metrics["heldout_logical_window_nll"] is not None
    assert metrics["heldout_logical_window_empirical_entropy"] is not None
    assert metrics["heldout_logical_window_excess_nll"] == pytest.approx(
        metrics["heldout_logical_window_nll"] - metrics["heldout_logical_window_empirical_entropy"]
    )
    assert metrics["logical_single_nll"] is not None
    assert metrics["logical_single_empirical_entropy"] is not None
    assert metrics["logical_single_excess_nll"] is not None
    assert metrics["logical_fault_support_nll"] is not None
    assert metrics["logical_fault_support_empirical_entropy"] is not None
    assert metrics["logical_fault_support_excess_nll"] is not None
    assert metrics["logical_detector_pair_nll"] is not None
    assert metrics["logical_detector_pair_empirical_entropy"] is not None
    assert metrics["logical_detector_pair_excess_nll"] is not None
    assert metrics["window_nll_weighting"] == "equal_window"
    assert metrics["window_evidence_groups"]["combined"]["num_windows"] == len(windows)


def test_window_batch_cache_subsets_and_entropies_reuse_prepared_counts():
    graph = _tiny_logical_graph()
    windows = build_windows_from_logical_observables(graph, max_window_bits=4)
    observations = torch.tensor(
        [
            [0, 0, 0, 0],
            [1, 0, 0, 1],
            [0, 1, 1, 1],
            [1, 1, 0, 0],
        ],
        dtype=torch.bool,
    )
    caches = build_window_nll_caches(graph, observations, windows, aggregate_unique=True)
    batch = build_window_batch_nll_cache(caches)
    indices = [0, 2]

    subset = subset_window_batch_nll_cache(batch, indices)

    expected_fault_ids = torch.cat([caches[index].fault_ids for index in indices])
    expected_states = torch.cat([caches[index].states for index in indices])
    expected_counts = torch.cat([caches[index].counts for index in indices if caches[index].counts is not None])
    expected_total_counts = torch.tensor(
        [int(caches[index].counts.sum().item()) for index in indices if caches[index].counts is not None],
        dtype=torch.long,
    )
    assert torch.equal(subset.flat_fault_ids.cpu(), expected_fault_ids)
    assert torch.equal(subset.flat_states.cpu(), expected_states)
    assert torch.equal(subset.flat_counts.cpu(), expected_counts)
    assert torch.equal(subset.window_total_counts.cpu(), expected_total_counts)
    assert subset.num_windows == len(indices)
    assert subset.max_state_count == max(1 << windows[index].size for index in indices)
    assert empirical_window_entropy_from_batch_cache(batch, indices) == pytest.approx(
        empirical_window_entropy(observations, [windows[index] for index in indices])
    )


def test_model_comparison_metrics_scale_small_excess_gaps():
    records = [
        {
            "sample_id": "sample_00",
            "patch_id": "d3",
            "basis": "X",
            "rounds_label": "r13",
            "dem_source": "decoder",
            "preprocessing_mode": "fault_graph_heuristic",
            "seed": 0,
            "model": "local",
            "parameter_count": 100,
            "heldout_combined_window_excess_nll": 0.001,
            "heldout_detector_window_excess_nll": 0.0002,
            "heldout_logical_window_excess_nll": 0.0015,
            "num_combined_windows": 50,
            "train_heldout_split": {"heldout_shots": 10},
        },
        {
            "sample_id": "sample_00",
            "patch_id": "d3",
            "basis": "X",
            "rounds_label": "r13",
            "dem_source": "decoder",
            "preprocessing_mode": "fault_graph_heuristic",
            "seed": 0,
            "model": "hard_orbit",
            "parameter_count": 10,
            "heldout_combined_window_excess_nll": 0.0014,
            "heldout_detector_window_excess_nll": 0.0003,
            "heldout_logical_window_excess_nll": 0.0018,
            "num_combined_windows": 50,
            "train_heldout_split": {"heldout_shots": 10},
        },
    ]

    augment_model_comparison_metrics(records)

    local, hard = records
    assert local["excess_mnats_per_window"] == pytest.approx(1.0)
    assert local["excess_delta_mnats_vs_baseline"] == pytest.approx(0.0)
    assert hard["excess_delta_mnats_vs_baseline"] == pytest.approx(0.4)
    assert hard["pseudo_delta_nats_per_shot_vs_baseline"] == pytest.approx(0.02)
    assert hard["pseudo_delta_bits_per_shot_vs_baseline"] == pytest.approx(0.02 / math.log(2))
    assert hard["logical_excess_delta_mnats_vs_baseline"] == pytest.approx(0.3)
    assert hard["parameter_fraction_of_baseline"] == pytest.approx(0.1)
    assert local["combined_excess_parameter_pareto_status"] == "pareto"
    assert hard["combined_excess_parameter_pareto_status"] == "pareto"


def test_fit_field_can_reuse_prepared_local_window_objective():
    graph = _tiny_graph()
    observations = torch.tensor([[0, 0], [1, 0], [1, 1]], dtype=torch.bool)
    window = ObservationWindow(name="full", bits=(0, 1), kind="test")
    objective = build_likelihood_objective(
        graph,
        observations,
        likelihood_objective="local_exact",
        observation_mode="full",
        windows=[window],
    )
    field = HardOrbitFaultLogitField.from_graph(graph, dtype=torch.float64)

    fit = fit_field(
        graph,
        field,
        observations,
        steps=1,
        lr=0.01,
        likelihood_objective="local_exact",
        windows=[window],
        prepared_objective=objective,
    )

    assert fit["num_train_windows"] == 1
    assert fit["likelihood_adapter"] == "python_window_loop_exact"


def test_cuda_batched_local_window_nll_matches_pytorch_when_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available")
    graph = _tiny_graph()
    windows = [
        ObservationWindow(name="left", bits=(0,), kind="test"),
        ObservationWindow(name="full", bits=(0, 1), kind="test"),
    ]
    observations = torch.tensor([[0, 0], [1, 0], [1, 1]], dtype=torch.bool)
    cpu_logits = torch.tensor([-1.2, -2.0, -3.0], dtype=torch.float64, requires_grad=True)
    cuda_logits = cpu_logits.detach().clone().cuda().requires_grad_(True)

    expected = local_window_exact_nll(graph, cpu_logits, observations, windows, backend="pytorch")
    try:
        actual = local_window_exact_nll(graph, cuda_logits, observations, windows, backend="cuda_extension")
    except RuntimeError as exc:
        pytest.skip(f"CUDA extension is not buildable in this environment: {exc}")

    assert torch.allclose(actual.cpu(), expected, atol=1e-12, rtol=1e-12)
    with torch.no_grad():
        inference_actual = local_window_exact_nll(
            graph,
            cuda_logits.detach(),
            observations,
            windows,
            backend="cuda_extension",
        )
    assert not inference_actual.requires_grad
    assert torch.allclose(inference_actual.cpu(), expected.detach(), atol=1e-12, rtol=1e-12)
    expected.backward()
    actual.backward()
    assert cuda_logits.grad is not None
    assert torch.allclose(cuda_logits.grad.cpu(), cpu_logits.grad, atol=1e-12, rtol=1e-12)


def test_cuda_batched_local_window_probability_floor_matches_pytorch_when_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available")
    graph = _one_bit_graph()
    windows = [ObservationWindow(name="bit", bits=(0,), kind="test")]
    observations = torch.tensor([[1]], dtype=torch.bool)

    for dtype, atol in ((torch.float64, 1e-12), (torch.float32, 1e-5)):
        cpu_logits = torch.tensor([-1000.0], dtype=dtype, requires_grad=True)
        cuda_logits = cpu_logits.detach().clone().cuda().requires_grad_(True)
        expected = local_window_exact_nll(graph, cpu_logits, observations, windows, backend="pytorch")
        try:
            actual = local_window_exact_nll(graph, cuda_logits, observations, windows, backend="cuda_extension")
            with torch.no_grad():
                inference_actual = local_window_exact_nll(
                    graph,
                    cuda_logits.detach(),
                    observations,
                    windows,
                    backend="cuda_extension",
                )
        except RuntimeError as exc:
            pytest.skip(f"CUDA extension is not buildable in this environment: {exc}")

        assert torch.allclose(actual.cpu(), expected.detach(), atol=atol, rtol=0)
        assert torch.allclose(inference_actual.cpu(), expected.detach(), atol=atol, rtol=0)
        expected.backward()
        actual.backward()
        assert cuda_logits.grad is not None
        assert torch.isfinite(cuda_logits.grad).all()
        assert torch.allclose(cuda_logits.grad.cpu(), cpu_logits.grad, atol=atol, rtol=0)


def test_cuda_window_batch_cache_builder_matches_cpu_when_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available")
    graph = _tiny_graph()
    windows = [
        ObservationWindow(name="left", bits=(0,), kind="test"),
        ObservationWindow(name="right", bits=(1,), kind="test"),
        ObservationWindow(name="full", bits=(0, 1), kind="test"),
    ]
    observations = torch.tensor(
        [
            [0, 0],
            [1, 0],
            [1, 1],
            [1, 1],
            [0, 1],
        ],
        dtype=torch.bool,
    )
    cpu_batch = build_window_batch_nll_cache(
        build_window_nll_caches(graph, observations, windows, aggregate_unique=True),
        device="cuda",
    )
    try:
        cuda_batch = build_window_batch_nll_cache_from_observations(
            graph,
            observations,
            windows,
            aggregate_unique=True,
            device="cuda",
            cache_backend="cuda_extension",
        )
    except RuntimeError as exc:
        pytest.skip(f"CUDA extension is not buildable in this environment: {exc}")

    assert cuda_batch.num_windows == cpu_batch.num_windows
    assert cuda_batch.max_state_count == cpu_batch.max_state_count
    assert torch.equal(cuda_batch.flat_fault_ids.cpu(), cpu_batch.flat_fault_ids.cpu())
    assert torch.equal(cuda_batch.flat_masks.cpu(), cpu_batch.flat_masks.cpu())
    assert torch.equal(cuda_batch.fault_offsets.cpu(), cpu_batch.fault_offsets.cpu())
    assert torch.equal(cuda_batch.window_num_bits.cpu(), cpu_batch.window_num_bits.cpu())

    for window_index in range(cuda_batch.num_windows):
        expected_begin = int(cpu_batch.state_offsets[window_index].item())
        expected_end = int(cpu_batch.state_offsets[window_index + 1].item())
        actual_begin = int(cuda_batch.state_offsets[window_index].item())
        actual_end = int(cuda_batch.state_offsets[window_index + 1].item())
        expected = {
            int(state): int(count)
            for state, count in zip(
                cpu_batch.flat_states[expected_begin:expected_end].cpu().tolist(),
                cpu_batch.flat_counts[expected_begin:expected_end].cpu().tolist(),
            )
        }
        actual = {
            int(state): int(count)
            for state, count in zip(
                cuda_batch.flat_states[actual_begin:actual_end].cpu().tolist(),
                cuda_batch.flat_counts[actual_begin:actual_end].cpu().tolist(),
            )
        }
        assert actual == expected

    logits = torch.tensor([-1.2, -2.0, -3.0], dtype=torch.float64, device="cuda")
    expected_nll = local_window_exact_nll_from_caches(
        logits,
        build_window_nll_caches(graph, observations, windows, aggregate_unique=True, device="cuda"),
        backend="cuda_extension",
    )
    assert torch.allclose(
        local_window_exact_nll_batched_from_cache(logits, cuda_batch).cpu(),
        expected_nll.cpu(),
        atol=1e-12,
        rtol=1e-12,
    )


def test_local_window_workload_audit_reports_active_fault_shape():
    graph = _tiny_graph()
    windows = [
        ObservationWindow(name="left", bits=(0,), kind="test"),
        ObservationWindow(name="full", bits=(0, 1), kind="test"),
    ]
    observations = torch.tensor([[0, 0], [1, 0], [1, 1], [1, 1]], dtype=torch.bool)
    cache = build_window_batch_nll_cache(
        build_window_nll_caches(graph, observations, windows, aggregate_unique=True),
    )

    audit = local_window_workload_audit(cache)

    assert audit["num_windows"] == 2
    assert audit["max_window_bits"] == 2
    assert audit["total_window_state_count"] == 6
    assert audit["mean_active_faults_per_window"] == pytest.approx(2.5)
    assert audit["max_active_faults_per_window"] == 3
    assert audit["total_active_fault_window_pairs"] == 5
    assert audit["unique_local_observation_patterns"] == 5


def test_cuda_spectral_local_window_training_kernel_matches_dp_when_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available")
    graph = _tiny_graph()
    windows = [
        ObservationWindow(name="left", bits=(0,), kind="test"),
        ObservationWindow(name="right", bits=(1,), kind="test"),
        ObservationWindow(name="full", bits=(0, 1), kind="test"),
    ]
    observations = torch.tensor([[0, 0], [1, 0], [1, 1], [1, 1], [0, 1]], dtype=torch.bool)
    cache = build_window_batch_nll_cache(
        build_window_nll_caches(graph, observations, windows, aggregate_unique=True),
        device="cuda",
    )
    for dtype, loss_atol, grad_atol in ((torch.float64, 1e-10, 1e-8), (torch.float32, 1e-5, 1e-4)):
        base = torch.tensor([-1.2, -2.0, -3.0], dtype=dtype, device="cuda")
        dp_logits = base.detach().clone().requires_grad_(True)
        spectral_logits = base.detach().clone().requires_grad_(True)

        try:
            dp_loss = local_window_exact_nll_batched_from_cache(dp_logits, cache, cuda_kernel_variant="dp")
            spectral_loss = local_window_exact_nll_batched_from_cache(
                spectral_logits,
                cache,
                cuda_kernel_variant="spectral",
            )
        except RuntimeError as exc:
            pytest.skip(f"CUDA extension is not buildable in this environment: {exc}")

        assert torch.allclose(spectral_loss, dp_loss, atol=loss_atol, rtol=loss_atol)
        dp_loss.backward()
        spectral_loss.backward()
        assert spectral_logits.grad is not None
        assert torch.allclose(spectral_logits.grad, dp_logits.grad, atol=grad_atol, rtol=grad_atol)

        shadow_logits = base.detach().clone().requires_grad_(True)
        shadow_loss = local_window_exact_nll_batched_from_cache(
            shadow_logits,
            cache,
            cuda_kernel_variant="spectral_shadow",
        )
        assert torch.allclose(shadow_loss, dp_loss.detach(), atol=loss_atol, rtol=loss_atol)

        auto_logits = base.detach().clone().requires_grad_(True)
        assert (
            local_window_cuda_kernel_audit(cache, requested_kernel_variant="auto")[
                "selected_cuda_kernel_variant"
            ]
            == "spectral"
        )
        auto_loss = local_window_exact_nll_batched_from_cache(auto_logits, cache, cuda_kernel_variant="auto")
        assert torch.allclose(auto_loss, dp_loss.detach(), atol=loss_atol, rtol=loss_atol)
        auto_loss.backward()
        assert auto_logits.grad is not None
        assert torch.allclose(auto_logits.grad, dp_logits.grad, atol=grad_atol, rtol=grad_atol)


def test_cuda_spectral_kernel_rejects_unsafe_zero_factor_when_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA is not available")
    graph = _tiny_graph()
    windows = [ObservationWindow(name="left", bits=(0,), kind="test")]
    observations = torch.tensor([[0, 0], [1, 0]], dtype=torch.bool)
    cache = build_window_batch_nll_cache(
        build_window_nll_caches(graph, observations, windows, aggregate_unique=True),
        device="cuda",
    )
    logits = torch.tensor([0.0, -2.0, -3.0], dtype=torch.float64, device="cuda", requires_grad=True)

    with pytest.raises(RuntimeError, match="spectral_min_abs_factor"):
        local_window_exact_nll_batched_from_cache(logits, cache, cuda_kernel_variant="spectral")


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
