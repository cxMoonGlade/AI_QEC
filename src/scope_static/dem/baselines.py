from __future__ import annotations

import torch

from .fault_graph import FaultGraph
from .fields import FaultLogitField

DMLE_QEC_SOURCE_REPOSITORY = "https://github.com/cxMoonGlade/DMLE-QEC"
DMLE_QEC_SOURCE_COMMIT = "e3b34106a07e65e130fa9cb5f58744ca18ca963f"
DMLE_QEC_BASELINE_IMPLEMENTATION = "scope_static_dmle_qec_style_independent_dem_mle"
DMLE_QEC_COMPATIBILITY_SCOPE = (
    "Independent DEM prior-logit MLE initialized from DEM effective probabilities, "
    "trained on detector-syndrome likelihood, and evaluated through the common "
    "scope_static DEM parity-map metrics."
)
DMLE_QEC_MISSING_UPSTREAM_COMPONENTS = [
    "PlanarNet repetition-code Kac-Ward optimizer",
    "TensorNetwork/PCM contraction optimizer",
    "contraction-path search/load workflow",
    "GateNoiseToDEM gate-to-DEM parameterization and sharing modes",
    "upstream mini-batch training schedules and optimizer choices",
    "upstream decoder-utility and real-data scripts",
]
DMLE_QEC_UPSTREAM_ADAPTER_IMPLEMENTATION = "upstream_dmle_qec_tensor_network_adapter"


class DMLEQECIndependentField(FaultLogitField):
    """DMLE-QEC-style independent DEM prior-logit MLE baseline.

    This is not the full upstream DMLE-QEC implementation. It is the compatible
    independent DEM-prior slice used by scope_static: a fully local Bernoulli
    fault-logit field initialized from the DEM's own effective probabilities and
    trained with detector-only likelihood.
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
            "baseline_display_name": "DMLE-QEC-style independent DEM MLE",
            "baseline_variant": DMLE_QEC_BASELINE_IMPLEMENTATION,
            "baseline_implementation": DMLE_QEC_BASELINE_IMPLEMENTATION,
            "baseline_source_repository": DMLE_QEC_SOURCE_REPOSITORY,
            "baseline_source_commit": DMLE_QEC_SOURCE_COMMIT,
            "upstream_dmle_qec_complete_implementation": False,
            "upstream_dmle_qec_compatibility_scope": DMLE_QEC_COMPATIBILITY_SCOPE,
            "upstream_dmle_qec_missing_components": DMLE_QEC_MISSING_UPSTREAM_COMPONENTS,
            "baseline_note": (
                "DMLE-QEC-style independent DEM prior-logit MLE baseline. "
                "It is source-aligned to the upstream repository and commit, but it is "
                "not the complete upstream PlanarNet/TensorNetwork/gate-to-DEM implementation."
            ),
        }
    if model_name == "dmle_qec_upstream":
        return {
            "baseline_family": "dmle_qec",
            "baseline_display_name": "Upstream DMLE-QEC TensorNetwork",
            "baseline_variant": DMLE_QEC_UPSTREAM_ADAPTER_IMPLEMENTATION,
            "baseline_implementation": DMLE_QEC_UPSTREAM_ADAPTER_IMPLEMENTATION,
            "baseline_source_repository": DMLE_QEC_SOURCE_REPOSITORY,
            "baseline_source_commit": DMLE_QEC_SOURCE_COMMIT,
            "upstream_dmle_qec_direct_adapter": True,
            "upstream_dmle_qec_component": "TensorNetwork",
            "upstream_dmle_qec_complete_implementation": False,
            "upstream_dmle_qec_compatibility_scope": (
                "Direct adapter to the upstream TensorNetwork/PCM surface-code DEM MLE path. "
                "PlanarNet and GateNoiseToDEM are separate upstream components and are not used "
                "for this Google surface-code DEM baseline."
            ),
            "baseline_note": (
                "Direct upstream DMLE-QEC TensorNetwork baseline. Enabling this baseline requires "
                "the upstream repository and its dependencies; it must fail rather than fall back "
                "to the scope_static DMLE-QEC-style implementation."
            ),
        }
    if model_name in {"known_hard_orbit", "known_soft_feature_orbit"}:
        return {
            "baseline_family": "known_orbit_oracle",
            "synthetic_oracle_baseline": True,
            "baseline_note": "Synthetic-only oracle baseline using hidden omega(j); do not use for real-data recovery claims.",
        }
    if model_name in {"disc_hard", "disc_soft"}:
        return {
            "baseline_family": "scope_static_discovery",
            "synthetic_oracle_baseline": False,
            "baseline_note": "Stage 2A learned DEM-fault assignment model; free assignments are an identifiability probe, not a compression claim.",
        }
    return {"baseline_family": model_name}
