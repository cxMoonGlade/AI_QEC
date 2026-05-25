import torch

from scope_static.baselines import DMLE_QEC_SOURCE_COMMIT, DMLE_QEC_SOURCE_REPOSITORY, baseline_metadata
from scope_static.fields import make_field
from scope_static.fault_graph import FaultGraph


def test_dmle_qec_baseline_initializes_from_effective_dem_probabilities():
    raw_masks = torch.tensor(
        [
            [1, 1, 0],
            [0, 0, 1],
        ],
        dtype=torch.bool,
    )
    raw_probabilities = torch.tensor([0.1, 0.2, 0.3], dtype=torch.float64)
    graph = FaultGraph.from_raw_masks(
        raw_masks,
        num_detectors=2,
        num_observables=0,
        raw_probabilities=raw_probabilities,
        residual_rank=0,
    )
    field = make_field("dmle_qec", graph, dtype=torch.float64)
    assert field.parameter_count == graph.M
    assert torch.allclose(torch.sigmoid(field.realized_logits()).sort().values, graph.effective_probabilities.sort().values)


def test_dmle_qec_metadata_is_reportable():
    metadata = baseline_metadata("dmle_qec")
    assert metadata["baseline_family"] == "dmle_qec"
    assert metadata["baseline_source_repository"] == DMLE_QEC_SOURCE_REPOSITORY
    assert metadata["baseline_source_commit"] == DMLE_QEC_SOURCE_COMMIT
