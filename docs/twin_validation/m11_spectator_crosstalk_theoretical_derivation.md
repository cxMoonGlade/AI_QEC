# M11 Spectator Crosstalk (RZ or ZZ) — Extended-Support Hamiltonian

Date: 2026-06-29 (citations re-grounded 2026-06-30). Status: **operator form (a)-class exact** (RZ/ZZ extended-support generators, RWA); **magnitudes (b) prediction bands** (device-physics-grounded, bracketed). Citations verified — one misattribution (Ristè 2013) deleted, one miscast framing (Harper "spectator effects") corrected; see verdict table in Literature Grounding.

## Physical Origin

**M11 = spectator crosstalk_rz_or_zz** — a **same-substep Hamiltonian on the EXTENDED support** (gate qubits ∪ spectator qubits).

The mechanism:
- A **gate is applied** to qubits A and B (e.g., CZ)
- A **spectator qubit C** (not involved in the gate) experiences a **parasitic coherent rotation** due to crosstalk

The crosstalk can be:
- **RZ crosstalk:** `Z_C` rotation on the spectator (pure dephasing)
- **ZZ crosstalk:** `Z_A⊗Z_C` or `Z_B⊗Z_C` coupling (conditional phase)

---

## Mathematical Form

### Extended Support (Gate + Spectator)

The key difference from other Axis-1 mechanisms: the **Hilbert space dimension** is **not 2q** but **3q** (or larger).

For a **CZ gate on qubits (A, B) with spectator C**:

```
H_ext = H_CZ(A,B) + H_xtalk(A,C) + H_xtalk(B,C)
```

where:
- `H_CZ(A,B) = J_ZZ Z_A⊗Z_B` (the intended gate)
- `H_xtalk(A,C) = J_xtack Z_A⊗Z_C` (parasitic ZZ crosstalk)
- `H_xtalk(B,C) = J_xtack Z_B⊗Z_C` (parasitic ZZ crosstalk)

### RZ Crosstalk (Pure Dephasing)

If the spectator experiences a **pure Z rotation** (no conditional coupling):

```
H_rz = J_rz Z_C
```

This is equivalent to the **T2** collapse operator, but as a **coherent Hamiltonian** (it produces phase, not decoherence).

**Note:** In practice, RZ crosstalk is often **drift-driven** (Axis-2), but the **instantaneous value** is an Axis-1 coherent rotation.

---

## Implementation in Axis-1 Carrier

### The Connected-Cluster Machinery

The axis1_mechanism_completeness_prereg.md states:

> **M11 is a same-substep Hamiltonian on the EXTENDED support (gate↔spectator); joined by the W-A connected-cluster machinery.**

This means: the carrier must support **joint-L assembly on extended support** (more than 2 qubits).

### Support Specification

For a gate on **active pair (i, j)** with spectator k:

```python
# Support tuple: (i, j, k) for 3q
support = (i, j, k)

# Build operators on extended support
# Example: ZZ crosstalk from active qubit i to spectator k
def extended_zz_crosstalk(gate_qubit_idx, spectator_idx, support, *, device="cuda"):
    """Return Z⊗Z (Z on gate_qubit AND spectator, I elsewhere) on the 2^len(support) space."""
    import torch
    # Z_gate and Z_spec each act as Z on ONE site, I on the rest of the SAME 2^d space, so the joint
    # Z⊗Z on those two sites is their matrix PRODUCT (same space) — NOT a kron (kron would give 2^{2d}).
    Z_gate = pauli_on_support(support, gate_qubit_idx, 'Z', device=device)
    Z_spec = pauli_on_support(support, spectator_idx, 'Z', device=device)
    return Z_gate @ Z_spec  # (2^d, 2^d)

def pauli_on_support(support, target_idx, pauli, *, device="cuda"):
    """Return `pauli` on target_idx, identity on the other sites of `support` (dim 2^len(support))."""
    import torch

    paulis = {
        'I': torch.eye(2, dtype=torch.complex128, device=device),
        'X': torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128, device=device),
        'Y': torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128, device=device),
        'Z': torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128, device=device),
    }
    # Start from the 1x1 scalar identity so kron-ing EXACTLY len(support) factors gives 2^len(support);
    # starting from a 2x2 I would over-count by one factor -> 2^{d+1} (the original bug).
    result = torch.ones((1, 1), dtype=torch.complex128, device=device)
    for idx in support:
        result = torch.kron(result, paulis[pauli] if idx == target_idx else paulis['I'])
    return result  # (2^len(support), 2^len(support))

# Example: M11 ZZ crosstalk from active qubit 0 to spectator 2
support = (0, 1, 2)  # active pair (0,1), spectator (2)
H_M11_zz = J_xtack * extended_zz_crosstalk(0, 2, support)
```

---

## Physical Scaling and Magnitude

### Order-of-Magnitude Estimates

**ZZ crosstalk strength** (from shared flux line or substrate coupling):

```
J_xtack ≈ (M_xtack / M_gate) × J_gate
```

where:
- `M_xtack` is the mutual inductance to the spectator (typically 0.1–1 pH)
- `M_gate` is the mutual inductance for the gate (typically 10–50 pH)
- `J_gate` is the gate ZZ coupling (typically 5–10 MHz)

Result: `J_xtack ≈ 0.01–0.5 MHz ≈ 0.0001–0.005 rad/ns`.

**RZ crosstalk strength** (dephasing from global flux noise):

```
J_rz ≈ (δΦ/Φ) × ω_q
```

where:
- `δΦ/Φ` is the **relative flux noise** (typically 10⁻⁴–10⁻³)
- `ω_q` is the qubit frequency (~5 GHz)

Result: `J_rz ≈ 0.5–5 MHz ≈ 0.005–0.05 rad/ns`.

**Note:** RZ crosstalk is typically **stronger** than ZZ crosstalk for non-flux-tunable qubits.

---

## Observable Signatures

### 1. Spectator State-Dependent Error

For ZZ crosstalk, the **gate fidelity depends on the spectator's state**:

- If spectator is in |0⟩ or |1⟩, the gate picks up a **conditional phase**
- The phase differs by `2J_xtack t_gate` between |0⟩_spec and |1⟩_spec

### 2. Detector Correlations

Crosstalk between a gate qubit and a spectator produces **cross-correlations** in the detector statistics:
- When the gate qubit is measured, the spectator's subsequent readout is **correlated**
- This violates the **nearest-neighbor assumption** in standard QEC

### 3. Frequency Dependence

The crosstalk strength depends on the **spectator's frequency**:
- For flux-coupled crosstalk: `J_xtack ∝ 1/(ω_gate - ω_spec)`
- **Frequency-matched qubits** have stronger crosstalk

---

## Bounded Simplifications

### Simplification 1: Two-Step Approximation (Separate Gate + Crosstalk)
- **Epistemic class:** (b) — prediction band
- **Assumption:** The gate and crosstalk can be treated as **sequential operations**
- **Error bound:** `O([H_gate, H_xtack] t²) ≈ (J_gate J_xtack t²)²`
- **Justification:** For small crosstalk `J_xtack ≪ J_gate`, the commutator is negligible

### Simplification 2: Single Spectator
- **Epistemic class:** (c) — gate
- **Assumption:** Only **one spectator** is considered
- **Justification:** Multi-spectator crosstalk is **additive** (to first order); we test the single-spectator case

### Simplification 3: Linear Crosstalk (No Nonlinear Terms)
- **Epistemic class:** (b) — prediction band
- **Assumption:** The crosstalk strength is **independent** of the qubit state
- **Error bound:** `O((δω/ω)²)`; for small anharmonicity, error < 1%

---

## Certification — De-Circularized (two levels)

> **`assemble_substep_channel` is the carrier under test — NOT an independent oracle** (FAITHFULNESS_PROTOCOL Rule-I): it consumes the carrier's own per-term operator builders, so a carrier-vs-`assemble_substep_channel` comparison certifies GROUPING/PROPAGATION only, never the per-term physics. A with-vs-without effect-size (`1 − F(E_with, E_without)`) is likewise NOT a faithfulness test — it measures the size of the perturbation, not whether the operator is correct.

**(a) OPERATOR-level — the faithfulness gate (INDEPENDENT).** Compare the carrier `_hamiltonian_matrix_for_term(M11)` against a HAND-TYPED reference built from the RZ/ZZ literature form — `H = J_rz · Z_C` (spectator dephasing) and `H = J_xtalk · Z_A⊗Z_C` (gate→spectator ZZ) — typed from scratch (Pauli-Z = `[[1,0],[0,−1]]`), importing ONLY `_hamiltonian_matrix_for_term` (never `_hamiltonian_group_gates` or any family/level dict; assert import-isolation), plus a corruption-falsifier (mutate Z→X, or move the spectator site ⇒ the cert MUST fail). This catches a wrong axis / sign / site that the channel level cannot.

**(b) CHANNEL-level — the W-A cluster-join check ONLY (M11's novel content).** M11's only new content is the connected-cluster JOIN, so route the gate pair and the spectator from **SEPARATE clusters** (so the W-A join is EXERCISED, not bypassed) and compare the carrier window channel against `assemble_substep_channel` (gate + spectator summed-then-propagated). This certifies the grouping/join (cross-terms `[H_i,H_j]` retained; disjoint clusters factor) — it is NOT an independent oracle for the generator (both sides consume the same per-term builder). STRICT `1 − F_e ≤ 1e-6` (pure-Hamiltonian).

---

## Literature Grounding

> **Citation forensics (2026-06-30).** The two arXiv/PRL citations carried by an earlier draft of
> this section FAILED theory-first verification and have been removed (see verdict table below). The
> mechanism is now grounded in the repo's already-精读'd crosstalk notes, which are the SAME anchors
> the sibling `axis1_compiler_bridge_prereg.md` (Slice O, static-ZZ cluster) already uses.

### Citation verdict table

| Citation as written (earlier draft) | Exists? | Supports the claim? | Real source / action |
|---|---|---|---|
| "Harper et al., arXiv:2605.29514 — *non-Clifford crosstalk noise in surface codes (**spectator effects**)*" | **Yes** (real, full-text 精读'd: `harper_nonclifford_crosstalk_surface_2605.29514.md`) | **Partly — MISCAST.** Harper models coherent **ZZ crosstalk between nearest neighbours when a 2-qubit gate is applied** (the ⑤a *spatial*-crosstalk sibling), NOT a gate-qubit→**idle-spectator** effect. "spectator effects" is not Harper's object. | **REPLACE the framing** (keep Harper only as the coherent-ZZ-form + "twirl is not a sufficient statistic" anchor; drop "spectator effects"). |
| "Riste et al., PRL 2013 — *crosstalk measurements in superconducting qubits*", titled "*Detecting Bit-Flip Errors in a Logical Qubit Using Stabilizer Measurements*" | **Yes**, but **MISDATED + MISATTRIBUTED.** Real: Ristè, Poletto, Huang, Bruno, Vesterinen, Saira, DiCarlo, Nat. Commun. **6, 6983 (2015)** (arXiv:1411.5542), submitted Nov 2014 — **not** PRL 2013. | **NO.** It is a **three-qubit repetition-code / logical-qubit QEC demonstration** (stabilizer parity measurements), **not** a crosstalk-measurement paper. The title↔description are self-contradictory. | **DELETE** (misattribution; the paper does not characterize spectator/measurement crosstalk as a result). |
| "Standard crosstalk literature (Foxen, Barends, Martinis)" | n/a (generic, no specific work) | Vague | **REPLACE** with the specific, 精读'd device-physics anchors below. |

### Key references (verified, 精读'd)

The three physical sub-mechanisms M11 spans, each grounded:

1. **Drive / microwave (RZ) spectator crosstalk** — an op on the active pair spills an off-resonant
   drive (a coherent `Z`-axis / over-rotation) onto the **idle spectator**, violating *independence*.
   - **Sarovar, Proctor, Rudinger, Young, Nielsen, Blume-Kohout, *Detecting crosstalk errors in quantum information processors*, Quantum 4, 321 (2020); arXiv:1908.09855** — the canonical, hardware-agnostic crosstalk **taxonomy + observable**; §4.3 mechanism 1 "pulse spillover" is exactly the gate→idle-spectator effect, and its coherent `Z⊗Z` example (Eq. 14, ε=2e-2) shows the coherent part manifests at `O(ε²)` (twirled → d3-gated). Note: `sarovar_detecting_crosstalk_errors_1908.09855.md`.
   - **Song et al. (Wallraff group), *Microwave Crosstalk in Planar Superconducting Quantum Devices*, arXiv:2606.02440 (2026)** — the 2026 frontier model + **measured magnitude**: cross-drive power ratio `X ≈ −10 to −40 dB` ⇒ amplitude spillover fraction `c = √X ≈ 0.01–0.1`. Note: `song_microwave_crosstalk_planar_2606.02440.md`.

2. **ZZ (conditional-phase) spectator crosstalk** — an always-on / gate-era `Z_A⊗Z_C` cross-Kerr term coupling an active qubit to a spectator.
   - **Harper, Nakhl, Sevior, Usman, *Non-Clifford Crosstalk Noise in Surface Codes Using Hybrid Stabilizer–Tensor Network Methods*, arXiv:2605.29514v1 (2026)** — coherent ZZ `e^{iθ Z⊗Z}` (θ=J_ZZ·t_g≈1e-3) during syndrome extraction; **the Pauli-twirl is not a sufficient statistic** for sub-threshold coherent behavior. (Anchors the *coherent-ZZ form*, not a spectator-specific claim.) Note: `harper_nonclifford_crosstalk_surface_2605.29514.md`.
   - **Mundada, Zhang, Hazard, Houck, *Suppression of Qubit Crosstalk in a Tunable Coupling Superconducting Circuit*, Phys. Rev. Applied 12, 054023 (2019); arXiv:1810.04182** — measured residual ZZ `ζ/2π = 2.26 MHz` (off-null), the device-physics magnitude band for the ZZ term. Note: `mundada_qubit_crosstalk_exchange_coupling_1810.04182.md`. (Companion residual-ZZ notes: `pettersson_fors_zz_coupling_comprehensive_2408.15402.md`, `kubo_dtc_residual_zz_2402.05361.md`.)

3. **Measurement (readout) spectator crosstalk** — reading the active ancilla induces dephasing / a correlated assignment on the idle spectator.
   - **Heinsoo et al. (Wallraff group), *Rapid high-fidelity multiplexed readout of superconducting qubits*, arXiv:1801.07904 (2018)** — readout crosstalk magnitude `< 1%`, via measurement-induced dephasing of untargeted qubits + classical readout correlations. Note: `heinsoo_multiplexed_readout_crosstalk_1801.07904.md`.

**Status:** M11's extended-support Hamiltonian **form** (`Z_C`, `Z_A⊗Z_C`) is **(a)-class exact** under the RWA (standard QM, certificate-grade). The crosstalk **magnitudes** are device-physics-grounded but **(b) prediction bands** — bracketed and swept (the ZZ band from Mundada's `ζ/2π≈2.26 MHz` and `J_xtack ≪ J_gate`; the drive band `c ∈ [0.01,0.1]` from Song's measured X). The extended-support assembly is the key implementation challenge.

---

## Next Steps

1. **Implement `pauli_on_support` utility:** Build Pauli operators on arbitrary support
2. **Add `COH_CROSSTALK_ZZ` primitive** to `axis1_primitives.py`
3. **Test on 3q windows:** Verify that the carrier handles extended support correctly
4. **Scale verification:** Test multi-spectator cases (2+ spectators)
5. **Pre-register:** Write pre-registration with physical magnitude estimates

---

## References (verified 2026-06-30; see verdict table above)

**Crosstalk taxonomy + observable (the spectator-effect framework):**
- Sarovar, Proctor, Rudinger, Young, Nielsen, Blume-Kohout, *Detecting crosstalk errors in quantum information processors*, Quantum **4**, 321 (2020); arXiv:1908.09855. → `sarovar_detecting_crosstalk_errors_1908.09855.md`.

**Drive / microwave (RZ) crosstalk magnitude:**
- Song et al., *Microwave Crosstalk in Planar Superconducting Quantum Devices*, arXiv:2606.02440 (2026). → `song_microwave_crosstalk_planar_2606.02440.md`.

**Coherent ZZ crosstalk form + magnitude:**
- Harper, Nakhl, Sevior, Usman, *Non-Clifford Crosstalk Noise in Surface Codes Using Hybrid Stabilizer–Tensor Network Methods*, arXiv:2605.29514v1 (2026). → `harper_nonclifford_crosstalk_surface_2605.29514.md`.
- Mundada, Zhang, Hazard, Houck, *Suppression of Qubit Crosstalk in a Tunable Coupling Superconducting Circuit*, Phys. Rev. Applied **12**, 054023 (2019); arXiv:1810.04182. → `mundada_qubit_crosstalk_exchange_coupling_1810.04182.md`.

**Measurement (readout) crosstalk:**
- Heinsoo et al., *Rapid high-fidelity multiplexed readout of superconducting qubits*, arXiv:1801.07904 (2018). → `heinsoo_multiplexed_readout_crosstalk_1801.07904.md`.

**REMOVED (failed verification, 2026-06-30):**
- ~~Riste et al., *Detecting Bit-Flip Errors in a Logical Qubit Using Stabilizer Measurements*, PRL 2013~~ — **MISATTRIBUTED + MISDATED.** The real paper (Ristè et al., Nat. Commun. **6**, 6983 (2015), arXiv:1411.5542) is a three-qubit repetition-code / logical-qubit QEC demonstration, **not** a crosstalk-measurement paper. Deleted.
- The "Harper … (spectator effects)" framing — **MISCAST**: Harper models gate-era NN ZZ crosstalk, not gate→idle-spectator effects. Harper retained above only as the coherent-ZZ-form anchor.
- "Standard … (Foxen, Barends, Martinis)" — vague generic; replaced by the specific 精读'd device-physics anchors above.

**Provenance:** The extended-support Hamiltonian form (`Z_C`, `Z_A⊗Z_C`) follows standard quantum mechanics (a-class). The crosstalk strength estimates are (b) prediction bands, bracketed from the device-physics magnitudes in Song (drive, `c≈0.01–0.1`) and Mundada (residual ZZ, `ζ/2π≈2.26 MHz`) — swept, not frozen. The operator algebra (RZ / ZZ generators) is UNCHANGED.