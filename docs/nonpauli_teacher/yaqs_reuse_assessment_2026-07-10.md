# MQT YAQS — reuse / validation assessment for the single-wire PEPS QEC carrier (2026-07-10)

**Target:** `external/yaqs/` (gitignored vendored, read-only, NEVER modify) = **MQT YAQS
v0.6.0** (TUM Chair for Design Automation), **MIT** license. The reference implementation
of the **Tensor Jump Method (TJM**, Sander et al. *Nature Comms* 16 11074 (2025) =
arXiv:2501.17913) — our contract SF12's grounding, by the theory's own authors
(Sander/Fröhlich/Wille/Mendl). Deps: numpy/scipy/**qiskit≥1.1**/opt-einsum/**numba**/cma;
optional `torch` (surrogate NN only). **CPU-only core** (no CUDA).

## One-line verdict
YAQS is a **strictly 1D MPS/MPO** engine — **no 2D/PEPS**, **no QEC syndrome circuits**
(digital path forbids mid-circuit measurement), memory subsystem is **single-qubit-probe +
Hamiltonian-backend**. BUT: qutrit/leakage is real in the **analog** path, and it has **two
independent trajectory unravelings + an exact Lindblad master-equation backend** (dense, no
shared truncation code) = a legitimate **anti-circular independent ground truth**. **The 2D
PEPS carrier remains entirely ours to build.**

## Findings (evidence: `external/yaqs/src/mqt/yaqs/`)
1. **Representation — strictly 1D.** `grep peps|2D|boundary|lattice|tebd|snake|plaquette`
   finds only `core/libraries/circuit_library.py::create_2d_*` = a 2D *Hamiltonian* on a
   **1D snaking MPS ordering** (docstring "snaking MPS ordering"; `create_lattice_to_qubit_mapping`
   "2D lattice → 1D qubit-line"). All evolution is 1D MPS (TDVP `core/methods/tdvp/`, TEBD
   `digital/digital_tjm.py`, BUG `core/methods/bug.py`); `MPS` = list of rank-3 tensors. **No
   PEPS, no boundary-MPS, no double-layer machinery.**
2. **Qutrit / heterogeneous dims — real (analog), not (circuit).** `MPS.__init__` carries
   `physical_dimensions: list[int]`; `MPO`/`Hamiltonian(physical_dimension=3)`; a **|1⟩⟨2|
   leakage jump is directly supported** via `NoiseModel` custom `matrix` (test_simulator.py
   `qutrit_decay_2_to_1`; `docs/examples/transmon_emulation.md` qubit_dim=3). Trajectory math
   is dimension-agnostic (`dissipation.py`/`stochastic_process.py` split on
   `physical_dimensions[site]`). **Caveats:** built-in `NoiseLibrary` is 2×2 only (you supply
   qutrit jumps); `MPS.measure_single_shot` hardcodes 2×2 readout; **digital gate path is
   power-of-2 only** (`gate_library.BaseGate` raises on non-2^n) → qutrit lives ONLY in the
   analog/channel path.
3. **Trajectory machinery — two clean independent unravelings + an exact backend.**
   (a) dense MCWF `analog/mcwf.py` (`H_eff = H − i/2 ΣL†L`, jump w.p. `‖L_kψ‖²`, sparse full
   Hilbert, exact ≤2^14); (b) MPS TJM `analog/analog_tjm.py` + `core/methods/{dissipation,
   stochastic_process,scheduled_jumps}` (deterministic `exp(−½dt ΣL†L)` sweep — Pauli case is
   the SF12 bond-inert scalar — + norm-based stochastic jump); (c) **exact Lindblad ME**
   `analog/lindblad.py` (dense `dρ/dt=−i[H,ρ]+Σ(LρL†−½{L†L,ρ})`, ≤~10 sites, NO sampling/
   truncation). (a)+(c) share **zero** code with any TN truncation engine → a true
   independent oracle. **Friction:** YAQS is continuous-time Lindblad/Hamiltonian, our carrier
   applies discrete compiled √E_s Kraus insertions — near-direct for the leakage-MCWF
   component, adaptor work (Lindblad+dt / scheduled_jumps) for the discrete stabilizer channels.
4. **Digital circuit sim — CANNOT run syndrome circuits.** `digital/digital_tjm.py` takes a
   Qiskit `QuantumCircuit`, but a **non-terminal (mid-circuit) measure raises `ValueError`**
   ("Non-terminal measure operations are not supported … would ignore state collapse"), no
   classical feedback, power-of-2 gates only. Surface-code syndrome extraction (ancilla
   measure+reset each round) is structurally impossible. **NOT-APPLICABLE for QEC.**
5. **Memory characterization — rigorous CMI/QMI, single-qubit-probe/Hamiltonian-only.**
   `MemoryCharacterizer.characterize(...)`: split-cut **operational memory** (past/future
   single-qubit intervention sequences → response matrix → SVD spectrum), the full **process
   tensor Υ** (`backends/tomography/process_tensors.py` Choi form), and genuine
   non-Markovian metrics `qmi()` + **`cmi()` = I(F:P_{<k}|P_k)** (the quantum-Markov-order
   witness, CMI→0 ⟺ Markovian). Backend = analog MCWF/TJM over a Hamiltonian MPO. **Reusable
   as CONCEPTS/FORMULAS** (CMI/QMI Markov-order, operational-memory SVD — self-contained in
   `process_tensors.py`), **not plug-and-play** (hardwired single-qubit 2×2 legs, analog-
   Hamiltonian backend — not multi-site QEC records).
6. **Noise.** `NoiseModel(processes=[{name,sites,strength,matrix|factors}])`, strength=γ,
   jump=√γ·L; built-ins 2×2 Pauli/raising/lowering (no leakage — supply your own); strengths
   can be distributions (static disorder).

## Reuse / validation verdict table
| Capability we want | Verdict | Reason |
|---|---|---|
| Independent-GT referee for `mps_forward` (RUNG-A) + deferred #4 | **REUSABLE-VIA-ADAPTOR** | exact-Lindblad ME + dense MCWF share no truncation code, take `NoiseModel`+`MPO`, qutrit-capable; adaptor = express √E_s as Lindblad+dt; CPU referee |
| RUNG-C non-Markovian memory (`characterization/memory/`) | **REFERENCE-ONLY** | CMI/QMI + operational-memory-SVD are the right multi-time metrics + self-contained math, but plumbing is single-qubit-probe over an analog Hamiltonian — lift the formulas, not the pipeline |
| noise/jump/TDVP–TEBD–BUG (`core/methods/*`, `analog/*`) | **REUSABLE-VIA-ADAPTOR (1D only)** | dimension-agnostic 1D-MPS TJM, qutrit-capable — a clean reference of what `mps_forward` does; NOT-APPLICABLE to the 2D PEPS |
| digital circuit sim for QEC syndrome circuits | **NOT-APPLICABLE** | mid-circuit measure raises, no feedback, 2^n gates — cannot do stabilizer measure/reset rounds |

## What YAQS does NOT give us (still ours)
1. The **2D PEPS** / single-wire 2D TN carrier — no 2D anywhere; RUNG-B is unique.
2. A **discrete-Kraus-channel QEC circuit engine** (YAQS = continuous Lindblad + Clifford circuits).
3. **Syndrome extraction with mid-circuit measure/reset/feedback + shot-based syndrome records.**
4. **Qutrit circuit gates + qutrit shot readout** (analog-only qutrit).
5. **GPU** for the core carrier (CPU numpy/scipy/numba).

**Note:** cTJM (2607.01323, our SF12-iv bond-2 parity anchor) is NOT in the v0.6.0 tree by
name — the shipped unraveling is standard TJM.

## Net recommendation
Use YAQS as an **independent Lindblad/MCWF anti-circular referee** (esp. the exact
`density_matrix` backend + the qutrit-leakage MCWF) to validate `mps_forward` / leak-sampling
at d3 (RUNG-A + the deferred #4), and **lift the CMI/QMI + operational-memory metric
definitions** for RUNG-C. Do NOT expect it to run QEC syndrome circuits or to contribute any
2D machinery — the 2D PEPS d5 crux (WP1 bond saturation) remains ours to build.
