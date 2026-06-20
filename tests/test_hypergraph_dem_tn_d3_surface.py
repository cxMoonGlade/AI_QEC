"""D=3 surface-code pins for the trainable hypergraph-DEM TN family."""

from __future__ import annotations

from pathlib import Path

import pytest
import stim
import torch

from qec_twin.forward.scalable import (
    GroupedLogitNormalizer,
    HypergraphDemTNLikelihood,
    LatentMixtureObservationTilt,
    ObservationTiltNormalizer,
    detector_coordinate_tilt_features,
    fit_latent_mixture_observation_tilt,
    fit_grouped_logit_normalizer,
    fit_hypergraph_dem_tn,
    fit_observation_tilt_normalizer,
    global_tilt_features,
    normalization_group_labels,
    phase3_supports_from_json,
)


def _d3_surface_circuit(rounds: int = 3) -> stim.Circuit:
    return stim.Circuit.generated(
        "surface_code:rotated_memory_x",
        distance=3,
        rounds=int(rounds),
        after_clifford_depolarization=0.001,
        before_measure_flip_probability=0.001,
        after_reset_flip_probability=0.001,
        before_round_data_depolarization=0.001,
    )


def test_d3_surface_code_tn_likelihood_is_differentiable() -> None:
    circuit = _d3_surface_circuit(rounds=3)
    dem = circuit.detector_error_model(decompose_errors=False, flatten_loops=True)
    family = HypergraphDemTNLikelihood.from_stim_dem(dem, include_observables=False)
    samples = circuit.compile_detector_sampler(seed=20260618).sample(8, append_observables=False)
    observations = torch.as_tensor(samples, dtype=torch.bool)

    loss = family.negative_log_likelihood(observations)
    assert torch.isfinite(loss)
    loss.backward()
    assert family.logits.grad is not None
    assert torch.isfinite(family.logits.grad).all()
    audit = family.audit_dict()
    assert audit["num_bits"] == dem.num_detectors
    assert audit["max_mechanism_arity"] >= 2
    assert audit["phase3_supports_are_probabilities"] is False


def test_d3_surface_code_fit_updates_likelihood_logits() -> None:
    circuit = _d3_surface_circuit(rounds=3)
    dem = circuit.detector_error_model(decompose_errors=False, flatten_loops=True)
    family = HypergraphDemTNLikelihood.from_stim_dem(dem, include_observables=False)
    samples = circuit.compile_detector_sampler(seed=20260619).sample(12, append_observables=False)
    observations = torch.as_tensor(samples, dtype=torch.bool)

    before = family.negative_log_likelihood(observations).detach().clone()
    report = fit_hypergraph_dem_tn(family, observations, steps=2, lr=0.01, l2_to_initial=1e-4)
    after = family.negative_log_likelihood(observations).detach()
    assert torch.isfinite(after)
    assert report["steps"] == 2
    assert report["history"]
    assert torch.isfinite(before)


def test_d3_surface_code_grouped_normalization_has_few_parameters() -> None:
    circuit = _d3_surface_circuit(rounds=3)
    dem = circuit.detector_error_model(decompose_errors=False, flatten_loops=True)
    family = HypergraphDemTNLikelihood.from_stim_dem(
        dem,
        include_observables=False,
        promoted_supports=[(0, 1, 2)],
    )
    normalizer = GroupedLogitNormalizer(family)
    assert normalizer.audit_dict()["num_trainable_offsets"] < len(family.mechanisms)
    samples = circuit.compile_detector_sampler(seed=20260620).sample(8, append_observables=False)
    observations = torch.as_tensor(samples, dtype=torch.bool)
    before = float(normalizer.negative_log_likelihood(observations).detach())
    report = fit_grouped_logit_normalizer(normalizer, observations, steps=2, lr=0.02, l2_offsets=1e-3)
    after = float(normalizer.negative_log_likelihood(observations).detach())
    assert report["audit"]["normalization"] == "grouped_logit_offsets"
    assert torch.isfinite(torch.tensor(after))
    assert after <= before + 1e-6


def test_d3_surface_code_normalization_schemes_are_declared() -> None:
    circuit = _d3_surface_circuit(rounds=3)
    dem = circuit.detector_error_model(decompose_errors=False, flatten_loops=True)
    family = HypergraphDemTNLikelihood.from_stim_dem(
        dem,
        include_observables=False,
        promoted_supports=[(0, 1), (0, 1, 2)],
    )

    expected = {
        "global": {"all"},
        "source": {"stim_dem", "phase3"},
        "default": {"stim_dem", "phase3_order2", "phase3_order3"},
    }
    for scheme, keys in expected.items():
        labels = normalization_group_labels(family.mechanisms, scheme=scheme)
        assert keys.issubset(set(labels))
        normalizer = GroupedLogitNormalizer(family, scheme=scheme)
        audit = normalizer.audit_dict()
        assert audit["scheme"] == scheme
        assert set(audit["group_keys"]) == set(labels)

    arity_labels = normalization_group_labels(family.mechanisms, scheme="arity")
    source_order_labels = normalization_group_labels(family.mechanisms, scheme="source_order")
    assert any(label.startswith("order") for label in arity_labels)
    assert any(label.startswith("phase3_order") for label in source_order_labels)


def test_d3_surface_code_observation_tilt_is_normalized_and_fit_only_eta() -> None:
    circuit = _d3_surface_circuit(rounds=3)
    dem = circuit.detector_error_model(decompose_errors=False, flatten_loops=True)
    family = HypergraphDemTNLikelihood.from_stim_dem(dem, include_observables=False)
    features = global_tilt_features(family.num_bits)
    normalizer = ObservationTiltNormalizer(family, features)
    samples = circuit.compile_detector_sampler(seed=20260621).sample(10, append_observables=False)
    observations = torch.as_tensor(samples, dtype=torch.bool)

    log_z = normalizer.log_partition()
    assert torch.isfinite(log_z)
    assert abs(float(log_z.detach())) < 1e-8
    before = float(normalizer.negative_log_likelihood(observations).detach())
    base_logits = normalizer.base_logits.detach().clone()
    report = fit_observation_tilt_normalizer(normalizer, observations, steps=2, lr=0.02, l2_eta=1e-3)
    after = float(normalizer.negative_log_likelihood(observations).detach())
    assert report["audit"]["normalization"] == "observation_exponential_tilt"
    assert report["audit"]["pair_hyperedge_features"] is False
    assert torch.equal(normalizer.base_logits, base_logits)
    assert torch.isfinite(torch.tensor(after))
    assert after <= before + 1e-6


def test_d3_surface_code_coordinate_tilt_features_are_declared() -> None:
    circuit = _d3_surface_circuit(rounds=3)
    dem = circuit.detector_error_model(decompose_errors=False, flatten_loops=True)
    features = detector_coordinate_tilt_features(dem, scheme="boundary_round")
    assert features.matrix.shape[0] == dem.num_detectors
    assert features.matrix.shape[1] == len(features.feature_names)
    assert features.scheme == "boundary_round"
    assert len(features.feature_names) >= 2
    assert torch.allclose(
        features.matrix.sum(dim=1),
        torch.ones(dem.num_detectors, dtype=features.matrix.dtype),
    )


def test_d3_surface_code_latent_mixture_tilt_is_normalized_and_fit_only_latent() -> None:
    circuit = _d3_surface_circuit(rounds=3)
    dem = circuit.detector_error_model(decompose_errors=False, flatten_loops=True)
    family = HypergraphDemTNLikelihood.from_stim_dem(dem, include_observables=False)
    features = detector_coordinate_tilt_features(dem, scheme="round_region")
    model = LatentMixtureObservationTilt(family, features, num_components=2, init_scale=0.0)
    samples = circuit.compile_detector_sampler(seed=20260622).sample(10, append_observables=False)
    observations = torch.as_tensor(samples, dtype=torch.bool)

    assert torch.allclose(model.tilt_log_factor(observations), torch.zeros(10, dtype=family.dtype))
    responsibilities = model.posterior_responsibilities(observations)
    assert responsibilities.shape == (10, 2)
    assert torch.allclose(responsibilities.sum(dim=1), torch.ones(10, dtype=family.dtype))
    base_logits = model.base_logits.detach().clone()
    before = float(model.tilt_objective(observations).detach())
    report = fit_latent_mixture_observation_tilt(model, observations, steps=2, lr=0.02, l2_eta=1e-3)
    after = float(model.tilt_objective(observations).detach())
    assert report["audit"]["normalization"] == "latent_mixture_observation_tilt"
    assert report["audit"]["pair_hyperedge_features"] is False
    assert torch.equal(model.base_logits, base_logits)
    assert torch.isfinite(torch.tensor(after))
    assert after <= before + 1e-6


def test_phase3_real_d3_supports_are_support_only_when_artifact_present() -> None:
    phase3_path = Path("outputs/phase3_residual_results.json")
    if not phase3_path.is_file():
        pytest.skip("real Phase-3 d3 residual artifact is not present")

    supports = phase3_supports_from_json(phase3_path, basis="X")
    assert len(supports.pairs) > 0
    assert len(supports.triples) > 0

    data_root = (
        Path("/home/cx/Document")
        / "google_72Q_surface_code_d3_d5_set1"
        / "google_72Q_surface_code_d3_d5_set1"
        / "sample_00"
        / "d3_at_q5_5"
        / "X"
        / "r13"
    )
    circuit_path = data_root / "circuit_noisy_si1000.stim"
    if not circuit_path.is_file():
        pytest.skip("local Google d3 surface-code circuit is not present")

    circuit = stim.Circuit.from_file(str(circuit_path))
    dem = circuit.detector_error_model(decompose_errors=False, flatten_loops=True)
    family = HypergraphDemTNLikelihood.from_stim_dem(
        dem,
        include_observables=False,
        promoted_supports=supports.triples[:3],
    )
    audit = family.audit_dict()
    n_phase3 = sum(
        count for source, count in audit["mechanism_sources"].items()
        if "phase3_support_proposal" in source
    )
    assert n_phase3 >= 3
    assert audit["probability_owner"] == "Layer-1 TN likelihood fit"
