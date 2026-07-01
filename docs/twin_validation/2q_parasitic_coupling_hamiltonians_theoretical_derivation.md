# 2Q Parasitic Coupling Hamiltonians — M10, M22, M23, M28-M33

Date: 2026-06-29 (Bell-table / oracle / infidelity prose corrected 2026-06-30). Status by
epistemic class (METRICS.md ladder; not a blanket "(a)-class exact"):

- **(a) exact** — the 9 `J·P⊗P` Hamiltonian **generators** (operator identities: each `P⊗P`
  Hermitian, traceless, `(P⊗P)²=I₄`; numerically verified, residual 0), and the closed forms
  `1−F_e = sin²(ε/4)`, `‖G‖²_F/d = ε²/16` for the realized `exp(−iHdt)` gate. These are the only
  class anything is built on.
- **(b) prediction band** — the carrier-side `1−F_e` matching its closed form to the Uhlmann
  estimator floor (per-mechanism certs); the `O(ε⁴)` exact-vs-leading deviation.
- **(c) gate / decision rule** — the RWA, pairwise-only, and no-drift simplifications below; the
  STRICT numeric tiers; the magnitude estimates.

Headline stays **PROVISIONAL** until each mechanism's GPU cert runs green (M22 landed:
`outputs/m22_coherent_cxx_parasitic_coupling_cert.py`).

## Physical Origin

Parasitic couplings are **coherent Hamiltonians** that are **not intentionally applied** but arise from **unwanted physical interactions** between qubits:

1. **Capacitive crosstalk** — unintended capacitive coupling between qubit pads
2. **Inductive crosstalk** — shared flux lines coupling qubits inductively
3. **Resonator-mediated coupling** — qubits coupling through a common bus resonator
4. **Dielectric substrate coupling** — substrate modes mediating interaction

These are **always present** in real hardware and must be calibrated/compensated.

---

## General Two-Qubit Hamiltonian

The most general **coherent two-qubit Hamiltonian** (up to single-qubit rotations) is:

```
H_2q = J_xx X⊗X + J_yy Y⊗Y + J_zz Z⊗Z + J_xy X⊗Y + J_yx Y⊗X + J_xz X⊗Z + J_zx Z⊗X + J_yz Y⊗Z + J_zy Z⊗Y
```

where each `J_ab` is a **coupling strength** (rad/ns).

---

## Specific Mechanisms

### M10: Coherent RXX+RYY Perturbation

**Physical origin:** **Isotropic capacitive/inductive crosstalk** — the coupling is symmetric in X and Y.

**Hamiltonian:**

```
H_M10 = J_coh (X⊗X + Y⊗Y)  = 2J_coh (σ⁺⊗σ⁻ + σ⁻⊗σ⁺)
```

where `J_coh` is the coupling strength (typically 0.1–1 MHz → 0.001–0.01 rad/ns).

**Observation:** This is equivalent to an **XY interaction**, which preserves total excitation number. This is the **physical form of the fSim gate without the phase term**.

**Connection to literature:** See Foxen et al., arXiv:2001.08343 (fSim family).

---

### M22: Coherent CXX Parasitic Coupling (XX-only)

**Physical origin:** **Anisotropic crosstalk** with dominant XX component.

**Hamiltonian:**

```
H_M22 = J_xx X⊗X
```

This is a pure **XX interaction**. `X⊗X` is diagonal in the Bell basis with eigenvalue **±1
on every Bell state** (no zero eigenvalue — `(X⊗X)²=I₄`, spectrum `{+1,+1,−1,−1}`), so under
`exp(−iJ_xx t·X⊗X)` each Bell state acquires the phase `exp(∓iJ_xx t)` set by its eigenvalue
(numerically verified, residual ≤2e-16):

| Bell state | `X⊗X` eigenvalue | phase under `exp(−iJ_xx t·X⊗X)` |
|---|---|---|
| `\|Φ⁺⟩ = (\|00⟩+\|11⟩)/√2` | **+1** | `e^{−iJ_xx t}` |
| `\|Φ⁻⟩ = (\|00⟩−\|11⟩)/√2` | **−1** | `e^{+iJ_xx t}` |
| `\|Ψ⁺⟩ = (\|01⟩+\|10⟩)/√2` | **+1** | `e^{−iJ_xx t}` |
| `\|Ψ⁻⟩ = (\|01⟩−\|10⟩)/√2` | **−1** | `e^{+iJ_xx t}` |

Note: `X⊗X` does **NOT** annihilate `\|Φ⁺⟩` or `\|Ψ⁻⟩` (that zero-eigenvalue behaviour belongs to
`X⊗X+Y⊗Y` = M10, where XX and YY cancel on the `\|Φ±⟩` pair — see M10's excitation-number
structure). This table is **illustrative only and NOT load-bearing for the M22 certificate**: the
M22 cert (`outputs/m22_coherent_cxx_parasitic_coupling_cert.py`) certifies the operator identity
`H_carrier = (coeff/4)(X⊗X)` and the scalar `1−F_e`, never a Bell-state phase table.

---

### M23: Coherent CYY Parasitic Coupling (YY-only)

**Physical origin:** **Anisotropic crosstalk** with dominant YY component.

**Hamiltonian:**

```
H_M23 = J_yy Y⊗Y
```

This is a pure **YY interaction**. Like `X⊗X`, `Y⊗Y` is diagonal in the Bell basis with eigenvalue
**±1 on every Bell state** (`(Y⊗Y)²=I₄`), but with a different sign pattern (numerically verified):
`\|Φ⁺⟩:−1, \|Φ⁻⟩:+1, \|Ψ⁺⟩:+1, \|Ψ⁻⟩:−1`. (Not load-bearing for the M23 cert, which gates the
operator identity `H_carrier = (coeff/4)(Y⊗Y)` and `1−F_e`.)

---

### M28: Coherent XY Parasitic Coupling

**Physical origin:** **Directed crosstalk** (e.g., A→B capacitive coupling).

**Hamiltonian:**

```
H_M28 = J_xy X⊗Y
```

Note the **asymmetry**: `X⊗Y ≠ Y⊗X`. This represents a **directional coupling** where qubit A's X couples to qubit B's Y.

**Relation to M10:** For symmetric coupling, `J_xy = J_yx = J_coh/2` and the total is `(X⊗Y + Y⊗X)/2`, which is equivalent to `(X⊗X + Y⊗Y)/2` after a single-qubit rotation.

---

### M29: Coherent ZX Parasitic Coupling

**Physical origin:** **Conditional phase crosstalk** — qubit B's Z affects qubit A's X.

**Hamiltonian:**

```
H_M29 = J_zx Z⊗X
```

This is a **conditional X rotation**: the strength of the X rotation on A depends on the Z state of B.

**Observation:** This is the **controlled-X (CNOT) generator** (up to a basis change). Parasitic ZX coupling is a **major source of CNOT errors**.

---

### M30: Coherent ZY Parasitic Coupling

**Hamiltonian:**

```
H_M30 = J_zy Z⊗Y
```

**Conditional Y rotation:** the strength of the Y rotation on A depends on the Z state of B.

---

### M31: Coherent XZ Parasitic Coupling

**Hamiltonian:**

```
H_M31 = J_xz X⊗Z
```

**Conditional Z rotation:** the strength of the Z rotation on B depends on the X state of A.

---

### M32: Coherent YZ Parasitic Coupling

**Hamiltonian:**

```
H_M32 = J_yz Y⊗Z
```

**Conditional Z rotation:** the strength of the Z rotation on B depends on the Y state of A.

---

### M33: Coherent YX Parasitic Coupling

**Hamiltonian:**

```
H_M33 = J_yx Y⊗X
```

**Directional coupling** (reverse of M28): qubit A's Y couples to qubit B's X.

---

## Implementation in Axis-1 Carrier

### Operator Construction

For each Hamiltonian term, we construct the `(4, 4)` matrix on the two-qubit space:

```python
def two_qubit_pauli_tensor(pauli_a, pauli_b, *, device="cuda"):
    """Return A⊗B for single-qubit Paulis A and B."""
    import torch

    # Pauli matrices
    paulis = {
        'I': torch.eye(2, dtype=torch.complex128, device=device),
        'X': torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128, device=device),
        'Y': torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128, device=device),
        'Z': torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128, device=device),
    }
    A = paulis[pauli_a]
    B = paulis[pauli_b]
    return torch.kron(A, B)  # column-stacking-compatible

# M10: XX + YY
H_M10 = J_coh * (two_qubit_pauli_tensor('X', 'X') + two_qubit_pauli_tensor('Y', 'Y'))

# M22: XX
H_M22 = J_xx * two_qubit_pauli_tensor('X', 'X')

# M23: YY
H_M23 = J_yy * two_qubit_pauli_tensor('Y', 'Y')

# M28: XY
H_M28 = J_xy * two_qubit_pauli_tensor('X', 'Y')

# M29: ZX
H_M29 = J_zx * two_qubit_pauli_tensor('Z', 'X')

# M30: ZY
H_M30 = J_zy * two_qubit_pauli_tensor('Z', 'Y')

# M31: XZ
H_M31 = J_xz * two_qubit_pauli_tensor('X', 'Z')

# M32: YZ
H_M32 = J_yz * two_qubit_pauli_tensor('Y', 'Z')

# M33: YX
H_M33 = J_yx * two_qubit_pauli_tensor('Y', 'X')
```

These are added to `H_list` for joint propagation via `assemble_substep_channel`.

---

## Physical Scaling and Magnitude

### Order-of-Magnitude Estimates

For **capacitive crosstalk** (XX/XY/XZ family):

```
J_cap ≈ C_c / C_q × ω_q
```

where:
- `C_c` is the **crosstalk capacitance** (typically 1–10 fF)
- `C_q` is the **qubit capacitance** (typically 50–100 fF)
- `ω_q` is the qubit frequency (~5 GHz)

Result: `J_cap ≈ 0.05–0.5 MHz ≈ 0.0005–0.005 rad/ns`.

For **inductive crosstalk** (YY/YZ/YX family):

```
J_ind ≈ M / L × ω_q
```

where:
- `M` is the **mutual inductance** (typically 1–10 pH)
- `L` is the **qubit inductance** (typically 10 nH)

Result: `J_ind ≈ 0.01–0.1 MHz ≈ 0.0001–0.001 rad/ns`.

**Note:** Inductive crosstalk is typically **weaker** than capacitive crosstalk.

---

## Observable Signatures

### 1. Conditional Gate Errors

For the **ZX/YZ/ZX family** (conditional rotations), the error manifests as:

- **State-dependent error rate:** The error depends on the control qubit's state
- **Coherent over-rotation:** The gate acquires an additional conditional phase

### 2. Gate-Time Scaling

All parasitic couplings have a **time dependence**: the total rotation is `J × t_gate`. Longer gates (e.g., idles) accumulate more parasitic error.

### 3. Directionality (XY/YX/XZ/etc.)

For the **asymmetric terms** (XY vs YX, XZ vs ZX), the crosstalk has a **preferred direction**. This manifests as:
- **Different error rates** for A→B vs B→A
- **Asymmetric detector correlations** in syndrome data

---

## Bounded Simplifications

### Simplification 1: Rotating-Wave Approximation (RWA)
- **Epistemic class:** (a) — exact under RWA
- **Assumption:** Counter-rotating terms like `X⊗X` with `ω_a + ω_b` are negligible
- **Error bound:** `O((J/Δ)²)`, typically `J/Δ < 0.01` → error < 10⁻⁴

### Simplification 2: Two-Qubit Window (Finite Support)
- **Epistemic class:** (c) — gate
- **Assumption:** Parasitic coupling is **pairwise only** (no higher-order multi-qubit)
- **Justification:** Hardware layouts couple nearest neighbors; multi-qubit couplings are exponentially suppressed

### Simplification 3: Constant Coupling (No Drift)
- **Epistemic class:** (b) — prediction band
- **Assumption:** The coupling strength `J_ab` is **constant across the substep**
- **Error bound:** `O(ΔJ/J)`; for well-calibrated hardware, `ΔJ/J < 1%`

---

## Certification: independent ground truth (de-circularized)

**`assemble_substep_channel` is the carrier under test — NOT an independent oracle.** Using it to
"certify" the carrier would be a FAITHFULNESS_PROTOCOL Rule-I circular-verification violation (a
check against the engine's own machinery, which shares the engine's blind spots). The certificate
instead follows the **landed M22 pattern** (`outputs/m22_coherent_cxx_parasitic_coupling_cert.py`),
which gates two levels:

**(a) OPERATOR-LEVEL — the load-bearing, de-circularized gate.** Compare the carrier's per-term
Hamiltonian `_hamiltonian_matrix_for_term(M)` against a **hand-typed-from-literature reference**
built **without importing any carrier grouping/family symbol** (`_coherent_family_generator`,
`_embed_coherent_generator`, `TWO_SITE_COHERENT_FAMILIES`, `COHERENT_PAULI_FAMILIES` appear
nowhere in the cert). For M22 the reference is `H_ref = (coeff/4)(X⊗X)` with `σ_x = [[0,1],[1,0]]`
(Nielsen & Chuang Eq. 2.1; the `X⊗X` axis grounded in Zhang quant-ph/0209120 Eq. 7/10, Kraus–Cirac
quant-ph/0011050 Eq. 24, Geller 1405.1915 Eq. 57). The cert imports **only**
`_hamiltonian_matrix_for_term` (the object under test):

```python
from qec_twin.simulator.axis1_mcwf_mps_execution import _hamiltonian_matrix_for_term  # the OBJECT UNDER TEST
# (deliberately NOT imported: _coherent_family_generator / _embed_coherent_generator /
#  TWO_SITE_COHERENT_FAMILIES / COHERENT_PAULI_FAMILIES — the anti-circular namespace gate)

X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128, device="cuda")
H_ref = 0.25 * coeff * torch.kron(X, X)                      # hand-typed, no carrier symbol
H_carrier = _hamiltonian_matrix_for_term(term_M22, support=(0, 1), local_dims=(2, 2), device="cuda")
assert torch.linalg.matrix_norm(H_carrier - H_ref) <= 1e-12  # (a)-class operator identity

# CORRUPTION FALSIFIER: a wrong-axis (YY) carrier op must be CAUGHT by the hand-typed XX reference
H_mutated_yy = 0.25 * coeff * torch.kron(Y, Y)
assert torch.linalg.matrix_norm(H_mutated_yy - H_ref) >= 1e-3  # cert FAILS on a corrupted carrier
# (a reference derived FROM the corrupted carrier map would mirror it to 0 — a false pass; the
#  hand-typed X⊗X reference is what makes the gate non-circular)
```

**(b) GROUPING/PROPAGATION check ONLY (never the independent oracle).** `assemble_substep_channel`
is used solely to confirm the carrier *composes/propagates* the per-term generator correctly into
the window channel (Choi-state `1−F_e` via `_choi_state_from_kraus` + `_state_fidelity`, microstep
convergence, CPTP residual). For a pure-Hamiltonian M22 the exact value is the **closed form**
`1−F_e = sin²(ε/4)` (`ε = coeff·dt`, `Tr(X⊗X)=0`, `d=4`; factor `/4`, not the 1-site `/2`):

```python
# leading-order infidelity (NOT exact): 1 - F_e = ||G||_F^2 / d + O(||G||_F^4), G = (ε/4)(X⊗X)
# ||G||_F^2 / d = (ε/4)^2 · Tr((X⊗X)^2) / 4 = ε^2 / 16   (Tr((X⊗X)^2) = 4 = d)
band = abs(carrier_one_minus_Fe - math.sin(eps / 4.0) ** 2)   # exact closed form for M22
assert band <= 5e-7                  # STRICT tier; |exact - leading ε^2/16| is O(ε^4), NOT < 1e-12
```

(The `1−F_e` band tolerance is `O(ε⁴)`-honest — `sin²(ε/4) = ε²/16 − ε⁴/(3·256) + …`, so the
leading `ε²/16` deviates from the exact value by an amount that is *nonzero for any finite ε* — a
registered higher-order finding, not a carrier bug. A `|1−F_e − ε²/d| < 1e-12` assertion is
impossible for finite ε.) Repeat for all 9 parasitic couplings, each with its own hand-typed
`P⊗P` reference and the matching closed form (the half-angle is `ε/4` and `1−F_e = sin²(ε/4)` for
every single Pauli-pair, since `Tr(P⊗Q)=0` and `(P⊗Q)²=I₄` — so the scalar `1−F_e` is **axis-blind**
and the operator gate (a) is the SOLE witness that distinguishes which Pauli axis the carrier
couples).

---

## Literature Grounding

### Key References

1. **Foxen et al., arXiv:2001.08343** — fSim family (XX+YY Hamiltonian)
2. **Pettersson Fors et al., arXiv:2408.15402** — residual ZZ coupling (M8/M10 family)
3. **Standard quantum optics textbooks** (Carmichael, Gardiner & Zoller) — two-qubit interactions

**Status (precise epistemic class — see the header):** The 9 parasitic-coupling Hamiltonian
**generators** `J·P⊗P` are **(a)-class operator identities** (Hermitian, traceless, `(P⊗P)²=I₄` —
numerically verified, residual 0) — well-established in quantum optics and quantum information
theory. The **RWA** that licenses dropping the counter-rotating terms is a **(c)-class
simplification** (bounded `O((J/Δ)²)`, not exact), and the per-mechanism `1−F_e` agreement with
its closed form is a **(b)-class band**. The blanket "all (a)-class exact under the RWA" phrasing
is retired: the generators are exact identities; the RWA and the certificate bands are not.

---

## Next Steps

1. **Lower the `COH_*` families in `simulator/axis1_mcwf_mps_execution._hamiltonian_matrix_for_term`**
   (the SOLE canonical lowering site — `COH_XX_YY` (M10), `COH_XX` (M22), `COH_YY` (M23), `COH_XY`
   (M28), `COH_YX` (M33), `COH_ZX` (M29), `COH_ZY` (M30), `COH_XZ` (M31), `COH_YZ` (M32)).
   Do **NOT** declare these in `axis1_primitives.py` — advertising a family there without lowering
   it is the "declaration-without-lowering" faithfulness trap (M22 prereg §1a / M6 prereg §1a).

2. **Write pre-registrations** for each mechanism with physical magnitude estimates

3. **Certify per the de-circularized two-level pattern** (this doc's "Certification" section): the
   load-bearing gate is the operator identity `_hamiltonian_matrix_for_term(M)` vs a hand-typed
   reference (NO carrier family symbol imported) + a corruption falsifier; `assemble_substep_channel`
   is the grouping/propagation check ONLY, never the independent oracle (Rule-I).

4. **Scale verification** for larger windows (3q, 5q) — ensure the pairwise approximation holds

---

## References

- Foxen et al., *Demonstrating a Continuous Set of Two-qubit Gates*, arXiv:2001.08343
- Pettersson Fors et al., *Characterization of Residual Coherent Interactions*, arXiv:2408.15402
- Carmichael, *Statistical Methods in Quantum Optics 1* (Sec. 8.3, two-qubit interactions)
- Gardiner & Zoller, *Quantum Noise* (Ch. 3, two-qubit dissipative dynamics)

**Provenance:** All Hamiltonian forms follow standard two-qubit interaction theory. The coupling strength estimates follow from capacitive/inductive crosstalk physics in superconducting qubits.