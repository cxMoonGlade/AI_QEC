from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalMechanismLayer:
    index: int
    title: str
    short_name: str
    legacy_alias: str
    role: str
    produces: tuple[str, ...]

    @property
    def public_name(self) -> str:
        return f"Layer {self.index}: {self.title} ({self.short_name})"

    def metadata(self, *, artifact_stage: str | None = None, substage: str | None = None) -> dict[str, object]:
        return {
            "schema": "scope_static_physical_mechanism_layer_v1",
            "layer_index": int(self.index),
            "layer_name": self.public_name,
            "layer_short_name": self.short_name,
            "legacy_alias": self.legacy_alias,
            "artifact_stage": artifact_stage,
            "substage": substage,
            "role": self.role,
            "produces": list(self.produces),
        }


LAYER1_PREP = PhysicalMechanismLayer(
    index=1,
    title="Data Preparation",
    short_name="Prep",
    legacy_alias="PHYC1",
    role="Generate mechanism-catalog records, probe schedules, sampled observations, and teacher metadata.",
    produces=(
        "oracle_mechanisms.json",
        "observations.npz",
        "teacher_config.json",
        "sampling_audit.json",
        "active_probe_manifest.json",
    ),
)

LAYER2_TEACHER = PhysicalMechanismLayer(
    index=2,
    title="Teacher Self-Distinguishment",
    short_name="Teacher",
    legacy_alias="PHYC2",
    role="Audit whether the declared teacher/catalog can self-distinguish every generated mechanism.",
    produces=(
        "teacher_self_distinguishment metrics",
        "BA/ARI/NMI/min-recall teacher gates",
        "coverage and no-learner-prediction audits",
    ),
)

LAYER3_LEARNER = PhysicalMechanismLayer(
    index=3,
    title="Learner Classification and Noise Generation",
    short_name="Learner",
    legacy_alias="PHYC3",
    role="Recover mechanisms from learner-visible observations and score generated noise/error quality without hidden feature leakage.",
    produces=(
        "visible feature schema",
        "deterministic visible ceiling",
        "learner predictions",
        "channel/readout prototype quality",
        "visible-generation NLL and MAE",
    ),
)

PHYSICAL_MECHANISM_LAYERS = (LAYER1_PREP, LAYER2_TEACHER, LAYER3_LEARNER)


def layer_stack_metadata() -> list[dict[str, object]]:
    return [layer.metadata() for layer in PHYSICAL_MECHANISM_LAYERS]

