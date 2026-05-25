from __future__ import annotations

from dataclasses import dataclass

import torch

from .fault_graph import FaultGraph


@dataclass(frozen=True)
class StimDemData:
    circuit: object
    raw_masks: torch.Tensor
    raw_probabilities: torch.Tensor
    num_detectors: int
    num_observables: int
    detector_coordinates: torch.Tensor


def generated_surface_code_circuit(
    *,
    family: str = "surface_code:rotated_memory_x",
    distance: int = 3,
    rounds: int = 1,
    noise: dict[str, float] | None = None,
):
    import stim

    noise = dict(noise or {})
    return stim.Circuit.generated(
        family,
        distance=int(distance),
        rounds=int(rounds),
        **noise,
    )


def extract_dem_data(circuit, *, decompose_errors: bool = True) -> StimDemData:
    dem = circuit.detector_error_model(decompose_errors=decompose_errors)
    num_detectors = int(dem.num_detectors)
    num_observables = int(dem.num_observables)
    b = num_detectors + num_observables
    masks: list[torch.Tensor] = []
    probabilities: list[float] = []

    for instruction in dem.flattened():
        if instruction.type != "error":
            continue
        mask = torch.zeros(b, dtype=torch.bool)
        for target in instruction.targets_copy():
            if target.is_separator():
                continue
            if target.is_relative_detector_id():
                mask[int(target.val)] ^= True
            elif target.is_logical_observable_id():
                mask[num_detectors + int(target.val)] ^= True
        masks.append(mask)
        probabilities.append(float(instruction.args_copy()[0]))

    raw_masks = torch.stack(masks, dim=1) if masks else torch.empty((b, 0), dtype=torch.bool)
    coords_dict = circuit.get_detector_coordinates()
    max_dim = max((len(v) for v in coords_dict.values()), default=0)
    coords = torch.zeros((num_detectors, max_dim), dtype=torch.float64)
    for detector, values in coords_dict.items():
        coords[int(detector), : len(values)] = torch.tensor(values, dtype=torch.float64)

    return StimDemData(
        circuit=circuit,
        raw_masks=raw_masks,
        raw_probabilities=torch.tensor(probabilities, dtype=torch.float64),
        num_detectors=num_detectors,
        num_observables=num_observables,
        detector_coordinates=coords,
    )


def build_surface_code_graph(
    *,
    family: str = "surface_code:rotated_memory_x",
    distance: int = 3,
    rounds: int = 1,
    noise: dict[str, float] | None = None,
    residual_rank: int = 0,
    canonicalize_duplicate_masks: bool = True,
) -> FaultGraph:
    circuit = generated_surface_code_circuit(
        family=family,
        distance=distance,
        rounds=rounds,
        noise=noise,
    )
    dem_data = extract_dem_data(circuit)
    return FaultGraph.from_raw_masks(
        dem_data.raw_masks,
        num_detectors=dem_data.num_detectors,
        num_observables=dem_data.num_observables,
        raw_probabilities=dem_data.raw_probabilities,
        detector_coordinates=dem_data.detector_coordinates,
        residual_rank=residual_rank,
        canonicalize_duplicate_masks=canonicalize_duplicate_masks,
    )


def sample_stim_observations(circuit, *, shots: int, seed: int | None = None) -> torch.Tensor:
    sampler = circuit.compile_detector_sampler(seed=seed)
    samples = sampler.sample(int(shots), append_observables=True)
    return torch.as_tensor(samples, dtype=torch.bool)


def sample_observations_from_logits(
    graph: FaultGraph,
    logits: torch.Tensor,
    *,
    shots: int,
    seed: int | None = None,
) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    if seed is not None:
        generator.manual_seed(int(seed))
    probs = torch.sigmoid(logits.detach().to(device="cpu", dtype=torch.float64))
    faults = torch.bernoulli(probs.expand(int(shots), graph.M), generator=generator).to(dtype=torch.bool)
    return graph.dem_parity_map.apply_faults(faults)
