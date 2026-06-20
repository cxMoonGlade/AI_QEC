# Phase-1 build interface contract (exact CP/Markovian core)

Fixed contract for the parallel Phase-1 build. Spec authority = `phase1_qutrit_leakage_registration.md`. Build
the **exact CP/Markovian core only** (the exact 9-data-qutrit density-matrix engine + leakage channel + teacher
+ XZZX parser + exact R=1 floor). The transport QT-MC (§2.6) and large-R sampler (Phase-1b/2) are NOT in this
build. Every agent codes to the signatures below so the pieces integrate at assembly.

## File ownership (disjoint — do not edit outside your set)
- **Agent A (ENGINE):** `src/qec_twin/forward/exact/qutrit_dm.py` (NEW).
- **Agent B (PHYSICS):** `src/qec_twin/forward/channels.py` (ADD `leakage_kraus` only, append; do not edit
  existing functions) + `src/qec_twin/mechanisms/qutrit_teachers.py` (NEW).
- **Agent C (HARNESS):** `src/qec_twin/forward/exact/xzzx_parser.py` (NEW) +
  `outputs/teacher_prereg/exact_floor_run.py` (NEW) + `tests/test_qutrit_dm_exact.py` (NEW).

## Data formats
- **Kraus** = `list` of `(3,3)` complex tensors (torch CUDA, complex128); CPTP `Σ Kᵢ†Kᵢ = I` to ≤1e-12.
- **Qutrit index** = data qutrits `0..8` in the parsed circuit's data-coordinate order. Basis `{|0⟩,|1⟩,|2⟩}`.
- **Schedule** (parser → engine) = ordered list of rounds; each round = list of ops:
  - `("gate", U, site)` — 1-qutrit unitary `U:(3,3)` (H/X/Y embedded on `{0,1}`, identity on `|2⟩`).
  - `("chan", kraus, site)` — 1-qutrit channel.
  - `("stab", paulis, stab_id)` — stabilizer parity measurement; `paulis: dict[data_site -> 'X'|'Z']` (the
    XZZX stabilizer support, compiled from the data↔ancilla CZ + ancilla M; **surplus qubits dropped, sweep-CX
    resolved to X/I at parse time**).

## Engine API — `forward/exact/qutrit_dm.py` (Agent A)
```
class QutritDM:
    def __init__(self, n_data: int, device='cuda', dtype=torch.complex128)   # holds 3^n_data x 3^n_data rho
    def init_logical(self, m: int) -> None          # prepare logical |m>, m in {0,1} (codestate)
    def apply_gate(self, U, site: int) -> None
    def apply_channel(self, kraus, site: int) -> None              # rho -> sum_i K_i rho K_i^dag
    def project_stabilizer(self, paulis, outcome: int, leaked_map) -> float
                                                    # project rho onto the syndrome-bit eigenspace
                                                    # (incl. leaked-readout per leaked_map); RETURN Tr(prob);
                                                    # leaves rho UN-normalized for sequential enumeration
    def syndrome_distribution(self, stabs, leaked_map) -> dict[tuple, float]
                                                    # EXACT P(s) over all 2^len(stabs) joint syndromes
                                                    # by enumeration (NO Monte-Carlo); 256 cells for 8 stabs
    def logical_distribution(self) -> tuple        # (p0, p1) final logical readout
    def trace(self) -> float
```
Extend the existing `forward/exact` parity-projection primitives (`project_parity`,
`measure_parity_enumerate`, `apply_channel_local`, `apply_kraus`) from `2^n` to `3^n`. GPU (torch CUDA); **no
CPU fallback** for the DM evolution.

## Leaked-ancilla readout map (Agent B supplies; Agents A/C consume)
`leaked_map(data_site_state)` → the syndrome-bit assignment for a data qutrit found in `|2⟩` during a
stabilizer measurement (pinned `(c)` design constant per §2.2 — leaked reads predominantly `|1⟩`-like). Default
first pass: a leaked component contributes a fixed biased bit; documented + parameterized, NOT a coin flip.

## Floor (Agent C harness)
`LER* = ½(1 − TV(P0, P1))`, `P_m = syndrome_distribution` under `init_logical(m)`; `TV = ½ Σ_s |P0[s]−P1[s]|`.

## Correctness gates (each agent's committed check must print PASS)
- **A:** `apply_channel == Σ Kᵢ ρ Kᵢ†` vs `density_sim.apply_kraus` (≤1e-12); `project_stabilizer` Tr exact vs a
  brute-force projector; total syndrome prob sums to 1; CPTP-state preserved.
- **B:** `leakage_kraus(L1,L2)` CPTP ≤1e-12; matches a qutip leakage channel ≤1e-10; `{0,1}`-restriction at
  `L1=L2=0` == identity bit-for-bit.
- **C:** parsed 17-qubit schedule (3 surplus dropped, sweep-CX resolved); at `L1=L2=0` the engine's `(s,m)`
  distribution reproduces the existing **9-data 2⁹ exact qubit path bit-for-bit** (P2-ii); the **exact R=1
  floor** `LER*` computed by 256-cell enumeration (no MC).

## Discipline (binding)
- **GPU only** for DM evolution (torch CUDA); no `cpu` fallback in model-compute paths.
- **Scripted execution:** every check/harness is a committed script under `outputs/teacher_prereg/` (precondition
  asserts + printed evidence + flushed stdout + `if __name__=='__main__'` guard). Small-scale unit checks only;
  do **NOT** run the full 5.77 GiB d3 floor concurrently (that is the assembly/integration step).
- **Commit-gate:** all `src/qec_twin/` changes are HELD for the user's confirmation — do not `git commit`.
- English; no inflation ("exact" only for operator/byte-count claims; the floor here IS exact-by-enumeration).
