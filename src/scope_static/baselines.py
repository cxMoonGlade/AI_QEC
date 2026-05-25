from __future__ import annotations

import torch

from .fault_graph import FaultGraph
from .fields import FaultLogitField

DMLE_QEC_SOURCE_REPOSITORY = "https://github.com/cxMoonGlade/DMLE-QEC"
DMLE_QEC_SOURCE_COMMIT = "e3b34106a07e65e130fa9cb5f58744ca18ca963f"


class DMLEQECIndependentField(FaultLogitField):
    """DMLE-QEC-style independent DEM prior-logit MLE baseline.

    DMLE-QEC optimizes independent DEM/prior logits against detector syndrome
    NLL. In this Stage-1 DEM parity-map setting, the compatible baseline is a
    fully local Bernoulli fault-logit field initialized from the DEM's own
    effective probabilities and trained with detector-only likelihood.
    """

    name = "dmle_qec"
    source_repository = DMLE_QEC_SOURCE_REPOSITORY
    source_commit = DMLE_QEC_SOURCE_COMMIT

    def __init__(
        self,
        init_probabilities: torch.Tensor,
        *,
        dtype: torch.dtype = torch.float64,
        seed: int | None = None,
        perturb_scale: float = 0.0,
    ):
        super().__init__()
        probabilities = torch.as_tensor(init_probabilities, dtype=dtype).clamp(1e-9, 1 - 1e-9)
        if perturb_scale:
            generator = torch.Generator(device="cpu")
            if seed is not None:
                generator.manual_seed(int(seed))
            signs = 2 * torch.bernoulli(torch.full_like(probabilities, 0.5), generator=generator) - 1
            perturb = torch.rand(probabilities.shape, generator=generator, dtype=dtype)
            probabilities = (probabilities + signs * probabilities * perturb * float(perturb_scale)).clamp(1e-9, 1 - 1e-9)
        self.priors_logits = torch.nn.Parameter(torch.logit(probabilities))

    @classmethod
    def from_graph(
        cls,
        graph: FaultGraph,
        *,
        dtype: torch.dtype = torch.float64,
        seed: int | None = None,
        perturb_scale: float = 0.0,
    ) -> "DMLEQECIndependentField":
        if graph.effective_probabilities is None:
            init_probabilities = torch.full((graph.M,), 1e-3, dtype=dtype)
        else:
            init_probabilities = graph.effective_probabilities.to(dtype=dtype)
        return cls(
            init_probabilities,
            dtype=dtype,
            seed=seed,
            perturb_scale=perturb_scale,
        )

    def realized_logits(self, graph: FaultGraph | None = None) -> torch.Tensor:
        return self.priors_logits


def baseline_metadata(model_name: str) -> dict[str, object]:
    if model_name == DMLEQECIndependentField.name:
        return {
            "baseline_family": "dmle_qec",
            "baseline_source_repository": DMLE_QEC_SOURCE_REPOSITORY,
            "baseline_source_commit": DMLE_QEC_SOURCE_COMMIT,
            "baseline_note": "Independent DEM prior-logit MLE baseline adapted from DMLE-QEC; trained on detector-syndrome NLL and evaluated with the common Stage-1 metrics.",
        }
    return {"baseline_family": model_name}
