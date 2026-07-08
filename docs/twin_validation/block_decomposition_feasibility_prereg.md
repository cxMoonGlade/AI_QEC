# Pre-registration — is the BLOCK DECOMPOSITION of correlated non-Markovian QEC noise feasible?

**Date 2026-07-01. Theory-first (literature-anchored), pre-code.** Verifies the load-bearing claim behind
(A)'s tractability: a large QEC circuit under correlated non-Markovian noise can be represented as a set of
**local {single-qubit + nearest-neighbor two-qubit} CPTP pseudomode blocks** (each fit from its 1- or
2-qubit matrix-BCF `C_ij(t)` via the 2506.10308 SDP), processed in parallel — IFF the noise's **spatial
correlation length ξ is short** (≲ nearest-neighbor). Grounding = the `docs/papers/reading_notes/` 精读 corpus
(no new fetch: the mechanisms were already read). Classes: **(a) exact**, **(b) prediction band**, **(c) gate/bracket**.

## 0. The decomposition (what "block" means)
Pseudomode embedding (PILOT 1, `mainline_A_sdp_feasibility_pilot.py`) turns **temporal** non-Markovianity into
**spatial** Markovianity in an enlarged space. Whether the enlarged GKSL is **local (block-decomposable)** or
**global** is inherited from the bath's SPATIAL structure — the matrix BCF `C_ij(t)` (2506.10308 SM §S2,
matrix `g∈C^{N×n}`): `C_ij` short-range ⇒ `g` banded ⇒ shared modes couple only near qubits ⇒ blocks;
`C_ij≈const` ⇒ `g` dense ⇒ all-to-all shared mode ⇒ no blocks. **The pseudomode method solves TIME; SPACE is a
physical property of the noise to be GROUNDED, not assumed.**

## 1. Grounded spatial ranges of QEC noise mechanisms (the load-bearing physics)
| Mechanism | Spatial range | Continuous? | Anchor (精读) |
|---|---|---|---|
| **Single-qubit TLS** (dominant) | **1 qubit** | yes | Gao 2605.23385 ("common case is a local single-qubit TLS"); Klimov [16] |
| **Gate crosstalk / coherent ZZ** | **nearest-neighbor** | yes | Harper 2605.29514 (coherent ZZ); Geller 1405.1915 (gmon XX/ZZ) |
| **Shared-coupler TLS** (rare) | **nearest-neighbor** (the coupler's 2 qubits; non-local in mm but LOCAL in connectivity) | yes (rare) | Gao 2605.23385 (`g̃∝g_kg_T/Δ`, coupler-hosted defect on 2 adjacent qubits) |
| **Collective 2-qubit relaxation** (M12) | **nearest-neighbor** IF shared bath is local (resistor/coupler); `γ_ij∝g_ig_j` | yes | Cattaneo 2005.06229 (Eq A1 `γ_12=g1g2(...)`, nonzero ONLY via common bath) |
| **Cosmic-ray / phonon / QP BURSTS** | **GLOBAL / chip-wide** (all stabilizers at once; decays from impact but chip-scale) | **NO — rare (~1/hr)** | Tan 2406.18897 (uniform across block); Kurilovich 2506.18228; McEwen 2104.05219 |
| **Chip-wide common-mode bath** (substrate/global phonon) | potentially GLOBAL; `∝g_ig_j` decays with distance from bath | uncertain | Cattaneo/Ojanen 0705.1085 (global relaxation) — largely frequency-planned-out |

**Verdict from the corpus:** the **dominant CONTINUOUS background** noise (TLS, crosstalk, ZZ, local collective)
is **LOCAL — single-qubit or nearest-neighbor** (`ξ ≲ 1` lattice site). The **only documented GLOBAL** mechanism
(bursts) is **RARE (~1/hr) AND decode-OWNED** (surface code resilient; detect-and-discard, Tan §III; Willow
~1/hr, 10⁻¹⁰ floor).

## 2. Predicted behavior (falsifiable bets) + epistemic classes
- **(a) EXACT (theorem):** if `C_ij(t)=0` for `dist(i,j) > R`, the noise factorizes over blocks of radius `R`
  EXACTLY (no correlation beyond the block ⇒ blocks independent). Definitional; the block error = the correlation
  MASS beyond the block boundary. *No falsifier — a theorem.*
- **(b) PREDICTION BAND:** the dominant continuous QEC noise has `ξ ≲ 1–2` lattice sites, so **{1-qubit + NN
  2-qubit} blocks capture the background correlation to small residual** (block-truncation error ~ the
  next-nearest-neighbor correlation tail, grounded-small: TLS local [Gao], ZZ NN [Harper], collective `∝g_ig_j`
  decaying [Cattaneo]). *Falsifier:* a measured/derived CONTINUOUS long-range correlation tail (`C_ij` for
  `|i−j|≥2`) that is NOT negligible vs the NN term — would force ≥3-qubit blocks or a global object.
- **(c) GATE / BRACKET:** the block decomposition models the **continuous background ONLY**. The **GLOBAL burst
  regime is BRACKETED OUT** as an orthogonal, rare (~1/hr), chip-wide detect-and-discard event (Tan/Kurilovich —
  OWNED), NOT represented by the blocks; a residual continuous chip-wide bath (if any) is a bracketed sensitivity
  (bound its `∝g_ig_j` tail). *This bracket is a scope declaration, never a premise for a decode claim.*

## 3. Observable (the RIGHT one, not invented)
The block-truncation error = the **spatial correlation mass beyond the block radius**, measured on the matrix
BCF and on the resulting reduced channel:
- **source layer:** `‖C_ij(t)‖` vs `dist(i,j)` — the correlation length `ξ` (decay of the off-diagonal matrix-BCF).
- **channel layer (ledgered, METRICS.md):** `D_Choi` between the full reduced channel and the block-truncated
  reconstruction — the STANDARD channel distance (same metric as the owned-baseline separation). NOT MI, NOT LER.

## 4. Independent ground-truth check (Rule I, non-circular)
Build a SMALL exact multi-qubit + shared-bath model (n=3–4 qubits in a line, exact DM ≤ safe dims), compute the
EXACT reduced channel, and compare to the **block-truncated** reconstruction (1-qubit + NN-2-qubit blocks fit
from the same exact `C_ij`). The exact DM is independent of the block construction. Also cross-check the
correlation-length decay against the grounded mechanism ranges (Table §1).

## 5. Bounded simplifications (Rule III)
- **(c) NN-block truncation:** error = the ≥2-hop correlation tail — MEASURED (bet §2b), not assumed.
- **(c) burst bracket:** the global regime is declared out-of-block-scope (rare+owned); its footprint is the
  Tan teraquop bound (<2× at 15× background), handled by a separate chip-wide flag, not the block model.
- **(a) matrix-BCF blocks:** each block's CPTP construction is the PILOT-1-validated SDP (exact per block).

## 6. Code experiment (step 6 — only after this prereg)
`outputs/`: (1) exact DM of n=3–4 qubits sharing a bath with a TUNABLE spatial coupling profile g(dist)
(local → global); (2) measure `ξ` (decay of `‖C_ij‖`) + `D_Choi`(exact channel, NN-block reconstruction) vs the
coupling range; (3) confirm: local profile ⇒ D_Choi(block) → 0 (blocks exact); global profile ⇒ D_Choi(block)
large (blocks fail — the bracketed regime). Standard metrics only (`D_Choi`, §METRICS.md). Safe dims, MCWF-free.

## 7. Verdict (provisional, pre-code)
**Block decomposition is FEASIBLE for the continuous background correlated non-Markovian QEC noise** — the
dominant mechanisms are LOCAL (grounded §1), so {1-qubit + NN 2-qubit} blocks suffice; the code experiment §6
quantifies the residual. The GLOBAL regime (bursts) is real but RARE + OWNED + orthogonal → explicitly bracketed,
not a block. This RESOLVES the scale-up worry for the object (A) actually models (the background noise), and it
is the tractable, parallelizable path to (B) syndrome shots (block-local correlated noise → Stim-class sampling).
**§6 MEASURED (2026-07-01, `outputs/block_decomposition_sec6.py`, exact DM, positive control ε=0→D_Choi=0):**
`D_Choi ≈ 0.20·ε_tail` (linear, 1st-order; D/ε=0.20 constant across the sweep) ⇒ **crossover to D_Choi<1e-3 at
2-hop rate ε_tail ≈ 5e-3 (~0.5% of the single-qubit rate).** LOCAL mechanisms (crosstalk/TLS 2-hop ~1e-4–1e-3)
⇒ D_Choi ~1e-4 ≪ 1e-3 ⇒ **BLOCKS OK** (conclusive: measured value is an UPPER bound — the true block
reconstruction fits the full model's NN marginals, so does better). POWER-LAW phonon (2-hop ~0.05–0.11) ⇒
D_Choi ~1–2e-2 ⇒ **BLOCKS FAIL** ⇒ bracketed (next-nearest blocks, or the rare global bath). **VERDICT
CONFIRMED (no longer provisional): block decomposition is FEASIBLE for the dominant local continuous background;
the crossover is 2-hop ≈ 0.5%.** CAVEATS: the 1e-3 bar is use-dependent; D_Choi(full,NN-only) is an upper bound
(a Petz/Markov block reconstruction from the full NN marginals would refine the power-law threshold); scaling
constant 0.20 is at these params (c_NN=0.45).
