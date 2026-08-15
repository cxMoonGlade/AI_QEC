#!/usr/bin/env python3
"""Probe whether the narrowed default suite scope can publish a suite report.

The suite orchestrator authenticates the shared semantic-disposition registry
across the batches it actually ran (``_authenticate_suite_disposition_partition``,
``tests/harness/mutation.py``), and that authentication requires every reviewed
row in the registry to be applied by exactly one executed batch.  The default
scope now schedules the ``certify`` batch alone, whose owned modules are
disjoint from every reviewed row.

This probe answers one question against real published evidence: does the
documented default command
``python tests/harness/mutation.py tests/_support/restricted_mps_mutation_suite.json``
reach a published suite report, and does that report disclose the reviewed rows
it did not authenticate?

It is the standing check for that question over the *real* 204-row registry and
the *real* published shard documents. The unit tests in
``tests/harness/test_mutation.py`` cover the same contract over synthetic
fixtures; only this probe binds it to the artefacts the repository actually
ships.

It executes no mutants.  It replays the suite's own authentication step over
already-published batch documents, so it is read-only with respect to the
repository and the GPU.

Preconditions
-------------
* The suite plan, the disposition registry, and the published ``certify`` batch
  document exist.
* The published ``cpu`` batch document exists, to serve as the control leg.
* No mutation shard is executing (the probe reads ``tests/`` but writes nothing
  under it).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
LOGDIR = REPO / "outputs" / "simulator_validation" / "logs"
SUITE = REPO / "tests" / "_support" / "restricted_mps_mutation_suite.json"
REGISTRY = (
    REPO / "tests" / "_support" / "restricted_mps_mutation_semantic_dispositions.json"
)
CERTIFY_REPORT = (
    LOGDIR / "restricted_mps_mutation_gpu_05_certification_mutation_survivors.json"
)
CPU_REPORT = LOGDIR / "restricted_mps_mutation_cpu_mutation_survivors.json"

sys.path.insert(0, str(REPO / "tests" / "harness"))


def emit(line: str = "") -> None:
    print(line, flush=True)


def require(path: Path, what: str) -> None:
    if not path.is_file():
        raise SystemExit(f"precondition failed: missing {what}: {path}")


def load_batch(path: Path) -> dict:
    """Load only the fields the suite authentication reads."""

    document = json.loads(path.read_text(encoding="utf-8"))
    return {
        "tag": document["tag"],
        "disposition_authentication": document["disposition_authentication"],
        "semantic_classification": document["semantic_classification"],
    }


def describe_partition(name: str, batch: dict) -> None:
    auth = batch["disposition_authentication"]
    emit(f"  {name}")
    emit(f"    tag                        {batch['tag']}")
    emit(f"    registry sha256            {auth['sha256']}")
    emit(f"    reviewed_count             {auth['reviewed_count']}")
    emit(f"    applied_reviewed_count     {auth['applied_reviewed_count']}")
    emit(f"    out_of_scope_reviewed_count {auth['out_of_scope_reviewed_count']}")
    emit(f"    scope_complete             {auth['scope_complete']}")
    for module in auth["scope_modules"]:
        emit(f"    owns                       {module}")


def attempt(label: str, batches: list[dict], mutation) -> str:
    emit(f"[{label}] batches = {[b['tag'] for b in batches]}")
    try:
        result = mutation._authenticate_suite_disposition_partition(
            batches,
            disposition_path=REGISTRY,
            repo=REPO,
            require_classifications=True,
        )
    except Exception as exc:  # noqa: BLE001 - the failure mode is the evidence
        text = str(exc)
        emit(f"[{label}] RAISED {type(exc).__name__}")
        emit(f"[{label}]   {text[:220]}{'...' if len(text) > 220 else ''}")
        return f"raised {type(exc).__name__}"
    emit(f"[{label}] authentication passed")
    emit(f"[{label}]   executed_batches            {result['executed_batches']}")
    emit(f"[{label}]   applied_exactly_once_count  {result['applied_exactly_once_count']}")
    emit(f"[{label}]   batch_application_counts    {result['batch_application_counts']}")
    emit(f"[{label}]   deferred_reviewed_count     {result['deferred_reviewed_count']}")
    emit(f"[{label}]   covers_registry_completely  {result['covers_registry_completely']}")
    return "passed"


def main() -> int:
    emit(f"mutation suite scope/disposition probe  {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}")
    emit(f"repo {REPO}")
    emit()

    require(SUITE, "suite plan")
    require(REGISTRY, "semantic disposition registry")
    require(CERTIFY_REPORT, "published certify batch document")
    require(CPU_REPORT, "published cpu batch document (control leg)")

    import mutation  # noqa: PLC0415 - path is set above

    plan = mutation.load_mutation_suite(SUITE)
    scheduled = [b for b in plan["batches"] if b["default_scope"]]
    deferred = [b for b in plan["batches"] if not b["default_scope"]]
    emit("suite plan")
    emit(f"  scheduled by default  {[b['name'] for b in scheduled]}")
    emit(f"  deferred by default   {[b['name'] for b in deferred]}")
    emit(f"  registry bound        {plan['semantic_dispositions_path']}")
    emit()

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    emit(f"registry rows {len(registry['reviewed'])}")
    emit()

    certify = load_batch(CERTIFY_REPORT)
    cpu = load_batch(CPU_REPORT)
    emit("published batch partitions")
    describe_partition("certify (the only default-scope batch)", certify)
    describe_partition("cpu (deferred)", cpu)
    emit()

    narrowed = attempt("narrowed-default-scope", [certify], mutation)
    emit()
    control = attempt("control-cpu-plus-certify", [cpu, certify], mutation)
    emit()

    emit("verdict")
    emit(f"  default scope as shipped : {narrowed}")
    emit(f"  same code, both batches   : {control}")
    if narrowed != "passed" and control == "passed":
        emit(
            "  the failure is caused by the scope narrowing, not by the registry "
            "or the published batch documents"
        )
        return 1
    if narrowed == "passed":
        emit("  the narrowed default scope publishes a suite report")
        return 0
    emit("  inconclusive: the control leg did not pass either")
    return 2


if __name__ == "__main__":
    sys.exit(main())
