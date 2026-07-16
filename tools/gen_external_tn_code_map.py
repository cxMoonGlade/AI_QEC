#!/usr/bin/env python
"""Generate the learning-oriented MPS/PEPS map for pristine external baselines.

The external repositories are read-only inputs.  This tool verifies every curated
path, records the exact upstream commit, hashes those inputs, and writes only to
``docs/external_baselines/TENSOR_NETWORK_CODE_MAP.md``.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "external" / "baselines"
OUTPUT = ROOT / "docs" / "external_baselines" / "TENSOR_NETWORK_CODE_MAP.md"
MARKER = "<!-- external-tn-code-map-inputs-sha256:"


BASELINES = {
    "Qiskit Aer": {
        "repo": "qiskit-aer",
        "environment": "ecs-baseline-aer",
        "scope": "Independent C++ qubit-MPS circuit executor and sampler; no PEPS or qutrit carrier.",
        "flow": "Aer method/config -> MPS state dispatcher -> local tensor updates/SVD -> measurement/sample -> saved MPS/results",
        "routes": [
            ("Configuration and public controls", "src/framework/config.hpp", "truncation threshold, maximum bond, sampling algorithm, logging"),
            ("Executor boundary", "src/simulators/matrix_product_state/matrix_product_state.hpp", "operation dispatch, measurement, save/set MPS"),
            ("State and update core", "src/simulators/matrix_product_state/matrix_product_state_internal.hpp", "MPS ownership and gate/update algorithms"),
            ("Update implementation", "src/simulators/matrix_product_state/matrix_product_state_internal.cpp", "concrete contractions, swaps, probabilities"),
            ("Site tensor representation", "src/simulators/matrix_product_state/matrix_product_state_tensor.hpp", "left/right tensors and bond-local operations"),
            ("SVD policy", "src/simulators/matrix_product_state/svd.hpp", "rank selection and truncation interface"),
            ("SVD implementation", "src/simulators/matrix_product_state/svd.cpp", "discard logic and decomposition backend"),
            ("Resource estimator", "src/simulators/matrix_product_state/matrix_product_state_size_estimator.hpp", "memory estimates, not accuracy evidence"),
            ("Save/restore test", "test/terra/backends/aer_simulator/test_save_matrix_product_state.py", "external representation round trip"),
        ],
        "questions": [
            "How are threshold and max-bond combined when choosing a retained rank?",
            "Where are nonlocal gates converted into swaps, and does swap direction change truncation order?",
            "How do direct MPS measurement and probability-vector sampling differ?",
        ],
    },
    "YASTN": {
        "repo": "yastn",
        "environment": "ecs-baseline-yastn",
        "scope": "Independent Python tensor stack with OBC MPS plus finite/infinite PEPS, NTU, CTM, BP, and BoundaryMPS.",
        "flow": "geometry/state -> gates/evolution -> selected environment metric -> bond truncation -> measurement/sampling",
        "routes": [
            ("MPS representation", "yastn/tn/mps/_mps_obc.py", "OBC MPS/MPO structure and canonical operations"),
            ("MPS compression", "yastn/tn/mps/_compression.py", "variational compression and truncation"),
            ("MPS environments", "yastn/tn/mps/_env.py", "left/right environments and contractions"),
            ("MPS measurement", "yastn/tn/mps/_measure.py", "expectations and sampling"),
            ("MPS TDVP", "yastn/tn/mps/_tdvp.py", "time evolution separate from gate-level truncation"),
            ("PEPS state", "yastn/tn/fpeps/_peps.py", "finite/infinite PEPS container and tensor conventions"),
            ("PEPS gates", "yastn/tn/fpeps/gates.py", "gate construction and path semantics"),
            ("PEPS evolution", "yastn/tn/fpeps/_evolution.py", "gate application, optimization, truncation reports"),
            ("Exact-cluster NTU", "yastn/tn/fpeps/envs/_env_ntu.py", "positive local metric and neighborhood update"),
            ("Boundary-MPS environment", "yastn/tn/fpeps/envs/_env_boundary_mps.py", "finite contraction approximation"),
            ("CTM environment", "yastn/tn/fpeps/envs/_env_ctm.py", "CTMRG update and full-environment approximation"),
            ("Bond-metric test", "tests/peps/test_bond_metric.py", "metric construction and corruption-sensitive checks"),
            ("Truncation-method test", "tests/peps/test_truncation_methods.py", "SVD/EAT/optimized truncation comparisons"),
            ("MPS truncation test", "tests/mps/test_truncate.py", "canonical MPS rank and error behavior"),
        ],
        "questions": [
            "Which reported truncation error is a true cluster norm and which is only an estimator?",
            "How do EnvNTU, EnvBoundaryMPS, and EnvCTM change the same bond metric?",
            "How are non-Hermitian or indefinite approximate metrics diagnosed or repaired?",
        ],
    },
    "variPEPS Python": {
        "repo": "variPEPS_Python",
        "environment": "ecs-baseline-varipeps",
        "scope": "JAX iPEPS, CTMRG/split-CTMRG, expectations, correlations, and variational optimization; not a finite trajectory executor.",
        "flow": "periodic unit cell -> double-layer contractions -> CTMRG projectors/absorption -> converged environment -> observables/gradient",
        "routes": [
            ("PEPS tensor", "varipeps/peps/tensor.py", "site tensor, environment tensors, and local dimensions"),
            ("Periodic unit cell", "varipeps/peps/unitcell.py", "iPEPS topology and translation structure"),
            ("Contraction definitions", "varipeps/contractions/definitions.py", "named contraction networks and index conventions"),
            ("Contraction application", "varipeps/contractions/apply.py", "JAX contraction execution"),
            ("CTMRG projectors", "varipeps/ctmrg/projectors.py", "projector construction and truncation surface"),
            ("CTMRG absorption", "varipeps/ctmrg/absorption.py", "directional environment update"),
            ("CTMRG convergence", "varipeps/ctmrg/routine.py", "iteration, convergence, and custom rules"),
            ("SVD utilities", "varipeps/utils/svd.py", "decomposition backend and custom differentiation"),
            ("Expectation model", "varipeps/expectation/model.py", "observable aggregation boundary"),
            ("One-site expectation", "varipeps/expectation/one_site.py", "smallest observable read path"),
            ("Correlation length", "varipeps/corrlength/corrlength.py", "transfer spectrum diagnostic"),
            ("Square-lattice example", "examples/heisenberg_afm_square.py", "end-to-end construction/optimization/readout"),
        ],
        "questions": [
            "How do ordinary and split CTMRG control double-layer growth?",
            "Which convergence tests monitor environment spectra versus physical observables?",
            "Which pieces can validate a frozen PEPS contraction without importing iPEPS assumptions into a finite patch?",
        ],
    },
    "ITensorMPS.jl": {
        "repo": "ITensorMPS.jl",
        "environment": "ecs-baseline-itensor",
        "scope": "Independent Julia canonical MPS/MPO implementation with explicit apply, truncate, TDVP, and sweep policies; no PEPS.",
        "flow": "site indices/state -> gate or MPO apply -> orthogonalize/SVD -> cutoff/maxdim truncation -> expectation/sample",
        "routes": [
            ("Core MPS representation", "src/mps.jl", "construction, tensors, canonical position, sampling"),
            ("Shared MPS algorithms", "src/abstractmps.jl", "orthogonalize, truncate!, gate apply, MPS algebra"),
            ("MPO application", "src/mpo.jl", "density-matrix, zip-up, and exact-then-truncate algorithms"),
            ("Default numerical policy", "src/defaults.jl", "default max dimension and cutoff"),
            ("Sweep policy", "src/sweeps.jl", "per-sweep cutoff/maxdim/mindim/noise"),
            ("TDVP driver", "src/solvers/tdvp.jl", "time-evolution entry point"),
            ("Sweep update", "src/solvers/sweep_update.jl", "factorization and truncation during solver sweeps"),
            ("MPS tests", "test/base/test_mps.jl", "representation and operation invariants"),
            ("Contraction tests", "test/base/test_solvers/test_contract.jl", "MPO/MPS application algorithms"),
            ("Gate-evolution example", "examples/gate_evolution/quantum_simulator.jl", "circuit-style gate application"),
        ],
        "questions": [
            "What Spectrum/truncation information is available from each SVD callback?",
            "How do density-matrix, zip-up, and exact-then-truncate MPO application differ?",
            "Which canonicalization invariants make discarded Schmidt weight globally interpretable?",
        ],
    },
}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def inputs_hash() -> str:
    h = hashlib.sha256(Path(__file__).read_bytes())
    for data in BASELINES.values():
        repo = EXTERNAL / data["repo"]
        h.update(data["repo"].encode())
        h.update(git(repo, "rev-parse", "HEAD").encode())
        for _, rel, _ in data["routes"]:
            path = repo / rel
            if not path.is_file():
                raise FileNotFoundError(f"missing curated code-map path: {path}")
            h.update(rel.encode())
            h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def render(digest: str) -> str:
    lines = [
        "# External tensor-network implementation code map",
        "",
        f"{MARKER} {digest} -->",
        "",
        "Generated by `python tools/gen_external_tn_code_map.py`. The four upstream repositories",
        "are pristine read-only inputs; adapters and comparison scripts belong in this repository.",
        "This is a learning/navigation map, not scientific evidence or an oracle verdict.",
        "",
        "## Fast routing",
        "",
        "| Question | First implementation | Independent cross-check | Important boundary |",
        "|---|---|---|---|",
        "| Qubit circuit MPS gate/update/sampling | Qiskit Aer | ITensorMPS gate application | Aer is qubit-only |",
        "| Canonical MPS truncation and discarded Schmidt weight | ITensorMPS | YASTN MPS | Do not transfer a 1D bound to PEPS |",
        "| Finite PEPS gate evolution and local environment truncation | YASTN | exact d3 plus our carrier | YASTN diagnostics are not record-law certificates |",
        "| Boundary-MPS contraction | YASTN | exact finite contraction | Separate contraction error from state truncation |",
        "| CTMRG and split-CTMRG | variPEPS | YASTN CTM | variPEPS is periodic iPEPS, not finite OBC trajectory |",
        "| Full multi-round detector/observable record | none of these directly | our exact d3 record oracle | External state metrics require an explicit record bridge |",
        "",
        "## Comparison architecture",
        "",
        "```text",
        "frozen circuit / gates / tensors / seeds",
        "        |",
        "        +-- Aer MPS -------- qubit circuit record/state comparator",
        "        +-- ITensorMPS ----- canonical MPS/truncation comparator",
        "        +-- YASTN ---------- finite MPS/PEPS evolution + environment comparator",
        "        `-- variPEPS ------- periodic CTMRG/contraction comparator",
        "                         |",
        "                 neutral artifact manifest",
        "                         |",
        "             repo-owned comparison and falsifier",
        "```",
        "",
    ]
    for name, data in BASELINES.items():
        repo = EXTERNAL / data["repo"]
        head = git(repo, "rev-parse", "HEAD")
        branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        lines += [
            f"## {name}",
            "",
            f"- Clone: `external/baselines/{data['repo']}`",
            f"- Environment: `{data['environment']}`",
            f"- Frozen input: `{branch}` at `{head}`",
            f"- Scope: {data['scope']}",
            f"- Data flow: `{data['flow']}`",
            "",
            "| Read in this order | Path | What to learn |",
            "|---|---|---|",
        ]
        for label, rel, purpose in data["routes"]:
            lines.append(f"| {label} | `external/baselines/{data['repo']}/{rel}` | {purpose} |")
        lines += ["", "Questions to carry while reading:", ""]
        lines += [f"- {question}" for question in data["questions"]]
        lines.append("")
    lines += [
        "## Safe use rules",
        "",
        "1. Keep every upstream clone clean; never place adapters, patches, or generated artifacts inside it.",
        "2. Exchange neutral arrays/circuits/manifests across fresh processes; do not co-load JAX, Torch, Aer, and Julia runtimes.",
        "3. Freeze index order, physical dimension, boundary condition, gate convention, precision, and measurement coordinate.",
        "4. Compare no-truncation/full-rank paths before finite-rank paths.",
        "5. Separate state truncation, environment approximation, contraction approximation, sampling error, and record folding.",
        "6. Require an independent deliberate corruption before treating agreement as evidence.",
        "7. A local fidelity, discarded weight, CTM convergence, or bond metric is not by itself a bound on full record TV.",
        "",
        "## Regeneration",
        "",
        "```bash",
        "python tools/gen_external_tn_code_map.py",
        "python tools/gen_external_tn_code_map.py --check",
        "```",
        "",
        "Regenerate after deliberately updating any external baseline commit or changing the curated learning routes.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    digest = inputs_hash()
    expected = render(digest)
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != expected:
            print(f"STALE: {OUTPUT.relative_to(ROOT)}")
            return 1
        print(f"CURRENT: {OUTPUT.relative_to(ROOT)} ({digest})")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected)
    print(f"WROTE: {OUTPUT.relative_to(ROOT)} ({digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
