# quantum_bath

Status: **feasibility-only research carrier; not a production record backend**.

This package evaluates a bounded two-data-qubit, two-ancilla, shared-pseudomode GKSL model on an
exact density matrix. It provides a dual-axis three-round instrument, formal reference
computations, declared comparison families, and record diagnostics. The package is CPU-only and
evaluator-side.

Modules:

- `gksl.py` — bosonic operators, the shared-mode Liouvillian, and the round propagator.
- `carrier.py` — dual-axis parity extraction and exact three-round branch enumeration.
- `observables.py` — finite-record statistics, conditional mutual information, and record distance.
- `crow_joynt.py` — a Gaussian classical-field comparison for the dephasing sector.
- `nulls.py` — declared amplitude-damping comparison families.
- `memory_witness.py` — a bounded Choi/concurrence diagnostic.
- `ground_truth.py` — independent factorization, extraction, closed-form, and no-bath checks.

Current acceptance files are registered under `quantum_bath_research` in
`docs/service_status.json`. They cover each module in a fresh process where appropriate.

These computations are formal implementation checks, not physical ground truth. A statistic on the
fixed three-round record does not by itself identify a quantum environmental origin, certify a
process tensor, or transfer to the production record path. Wider scientific claims remain withheld
until a clean primary-literature audit binds the exact object, access model, formula, and falsifier.
