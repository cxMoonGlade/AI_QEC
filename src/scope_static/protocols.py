from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogProtocolStage:
    index: int
    title: str
    short_name: str
    role: str
    produces: tuple[str, ...]

    @property
    def public_name(self) -> str:
        return self.title

    def metadata(self, *, artifact_stage: str | None = None, substage: str | None = None) -> dict[str, object]:
        return {
            "schema": "scope_static_catalog_protocol_stage_v1",
            "stage_index": int(self.index),
            "stage_name": self.public_name,
            "stage_short_name": self.short_name,
            "layer_index": int(self.index),
            "layer_name": self.public_name,
            "layer_short_name": self.short_name,
            "artifact_stage": artifact_stage,
            "substage": substage,
            "role": self.role,
            "produces": list(self.produces),
        }


DATA_PREPARATION_STAGE = CatalogProtocolStage(
    index=1,
    title="Layer1 preprocessing - teacher generator",
    short_name="Layer1",
    role="Generate mechanism-catalog records, probe schedules, sampled observations, and teacher metadata.",
    produces=(
        "oracle_mechanisms.json",
        "observations.npz",
        "teacher_config.json",
        "sampling_audit.json",
        "active_probe_manifest.json",
    ),
)

TEACHER_VALIDATION_STAGE = CatalogProtocolStage(
    index=2,
    title="Layer 2 teacher self-audit",
    short_name="Layer2",
    role="Audit whether the declared teacher/catalog can self-distinguish every generated mechanism.",
    produces=(
        "teacher_self_distinguishment metrics",
        "BA/ARI/NMI/min-recall teacher gates",
        "coverage and no-learner-prediction audits",
    ),
)

LEARNER_VALIDATION_STAGE = CatalogProtocolStage(
    index=3,
    title="Layer 3 learner",
    short_name="Layer3",
    role="Recover mechanisms from learner-visible observations and score generated noise/error quality without hidden feature leakage.",
    produces=(
        "visible feature schema",
        "deterministic visible ceiling",
        "learner predictions",
        "channel/readout prototype quality",
        "visible-generation NLL and MAE",
    ),
)

CATALOG_VALIDATION_STAGES = (DATA_PREPARATION_STAGE, TEACHER_VALIDATION_STAGE, LEARNER_VALIDATION_STAGE)


def catalog_validation_stage_metadata() -> list[dict[str, object]]:
    return [stage.metadata() for stage in CATALOG_VALIDATION_STAGES]
