# Body-read — Layden, Chen & Cappellaro, "Efficient quantum error correction of dephasing induced by a common fluctuator" (arXiv:1903.01046v2; PRL 124, 020504 (2020))

> **Provenance.** Body-read by opus subagent 2026-07-02, targeted scope: **A9 adjudication** (is this the
> prior art, or merely adjacent, for our f-interpolation + syndrome-silent-floor claims?; what is the exact
> common-fluctuator model + code design; does it compute any syndrome/silent rate under common-mode
> dephasing for a STABILIZER code; what is the `t^O(2ⁿ)` collective-error scaling). PDF downloaded
> `arxiv.org/pdf/1903.01046` (`outputs/papers/fetch_and_extract.py`, 0.54 MB, 6 pp main text; Supplemental
> Material NOT in this PDF — see L1) → text `outputs/papers/1903.01046.txt` (fitz). Full main text read;
> Supplemental Material [ref 31] contents inferred only from main-text pointers, NOT read.
> **Pending principal spot-verification.** Tags: **[paper]** = stated in the paper; **[ours]** = our
> inference for `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** David Layden, Mo Chen (陈墨), Paola Cappellaro (MIT — RLE / Nuclear Sci. &
  Eng. / Mech. Eng.).
- **Venue / status.** arXiv:1903.01046v2 [quant-ph], 17 Jan 2020 → PRL 124, 020504 (2020).
- **Type.** **QEC code-design theory** (Knill-Laflamme construction of noise-tailored codes) + illustrative
  numerics (Fig 1, Gaussian-θ model). NOT a surface-code / stabilizer-threshold paper; NOT a hardware
  experiment. The relevant object is a *new family of bespoke small codes*, contrasted against the
  repetition code.

## Executive summary [paper]
Introduces "**common-fluctuator dephasing (CFD)**" — a register dephased by eigenstate-preserving coupling
of each qubit to ONE shared fluctuator — and designs QEC codes **tailored to CFD** that achieve an
**EXPONENTIAL overhead reduction**: where the repetition code on `n` qubits corrects to order `t^O(n)`,
these codes correct to order **`t^O(2ⁿ)`** (abstract). The smallest instance encodes 1 logical qubit into
**2 physical qubits** (vs 3 for the smallest repetition code) and corrects CFD to leading order with a
constant number of 1- and 2-qubit ops. The trick: correct the specific error span
`E = span{I, H_E, H_E², …, H_E^q}` (powers of the collective dephasing generator), NOT arbitrary
weight-≤w Paulis — a **noise-adapted, non-Pauli** code.

## The exact CFD model (Eq 1–2 — the load-bearing common-mode Hamiltonian) [paper]
This is the mechanism most directly comparable to our A9 common-mode dephasing.
- **Hamiltonian (Eq 1):** `H = H_f⁰ + ½ Σ_j ω_j Z_j + H_f^int ⊗ Σ_j g_j Z_j`, with `[H_f⁰, H_f^int]=0` and a
  fluctuator jumping incoherently between eigenstates `{|ℓ⟩_f}` (dissipative term in the master equation).
- **Interaction picture (Eq 2):** `H̃ = Σ_ℓ λ_ℓ |ℓ⟩⟨ℓ|_f ⊗ H_E`, where **`H_E := Σ_{j=1}^n g_j Z_j`** and
  `H_f^int = Σ_ℓ λ_ℓ |ℓ⟩⟨ℓ|_f`. **This `H_E = Σ_j g_j Z_j` is exactly the collective-Z-dephasing generator
  our A9 mechanism uses.** When the fluctuator is in state `|ℓ⟩`, qubit j feels `λ_ℓ g_j Z_j`; fluctuator
  jumps ⇒ **spatially-correlated random telegraph dephasing** [refs 8,9]. Per-run the register evolves as
  `U(θ)=e^{−iθ H_E}` for a random `θ ∈ [tλ_min, tλ_max]` set by the fluctuator trajectory.
- **DFS relationship:** "Note that CFD does **not** generally produce a decoherence-free subspace (DFS)."
  [paper, verbatim] The codes **reduce to a DFS only in the degenerate limit `|g1|=|g2|`** (Eqs 10–11
  remark) — "**but this is in practice rare.**" So the code is **DFS-adjacent but explicitly NOT a DFS
  code**; it is a genuine detect-and-correct code with a stabilizer-like measured operator `S` (Eq 13).

## Code design & the `t^O(2ⁿ)` scaling [paper]
- **Counting (Eq 3):** to correct `E=span{I,H_E,…,H_E^q}` to order `O(t^q)` needs `n = ⌈1 + log₂(q+1)⌉`
  qubits — exponentially fewer than the repetition code's `n=2q+1`. Saturating the ceiling ⇒ `q = 2^{n-1}−1`,
  hence **corrects to order `t^{O(2ⁿ)}`** (this is what the abstract's `t^O(2ⁿ)` means: the *order in the
  short-time expansion* of the corrected collective error, exponential in qubit count `n`).
- **KL conditions (Eq 4–5):** `⟨0_l|H_E^m|0_l⟩=⟨1_l|H_E^m|1_l⟩`, `⟨0_l|H_E^m|1_l⟩=0` for `0≤m≤2q`. Solved
  by an ansatz (Eq 6) with the `|1_l⟩` amplitudes = `|0_l⟩` amplitudes reversed; the odd-`m` conditions
  reduce to `⃗z ⊥ span{⃗v_m}` (Eq 7), always solvable since there are `q` vectors `⃗v_m` in dimension `q+1`.
- **n=2 explicit code (Eqs 9–12):** `H_E=g1Z1+g2Z2` (a sum of **weight-1** Paulis, NOT a weight-2 Pauli);
  `|0_l⟩=|χ0⟩|0⟩`, `|1_l⟩=|χ1⟩|1⟩` with `|χ0⟩,|χ1⟩` unequal-amplitude superpositions set by `g1,g2`.
  **"by design, however, it does not correct for `Z1Z2`, nor `Z1` or `Z2` individually, none of which belong
  to `E`."** [paper] Recovery = measure a separable `S = P_l − P_e = U_z ⊗ Z₂` (Eq 13) via phase kickback,
  correct with `U_x` — Fig 2. `S` "behaves like a stabilizer" on `C0,C1` but is **not in the Pauli group**
  and `{H_E,S}≠0` generically (non-standard stabilizer formalism).

## Does the paper compute a syndrome / SILENT rate under common-mode dephasing for a STABILIZER code? [paper]
**NO. This is the decisive point for A9.** Two aspects:
1. **No stabilizer-code syndrome/detection analysis.** The paper is about *bespoke non-Pauli codes*; its
   "syndrome" is the measurement of the tailored operator `S` (Eq 13), not surface-/repetition-code parity
   checks. There is **no detection-event rate, no zero-syndrome-logical-flip rate, no fixed-marginal
   correlated-vs-independent comparison** — none of A9's observables.
2. **The repetition code is discussed only as a correction-ORDER baseline, not a syndrome-rate object.**
   The paper notes the 3-qubit repetition code corrects CFD "at order `O(t)`" and to `O(t^q)` needs
   `n=2q+1` (§ around Eq legends) — a *code-distance/order* statement, again not a silent-syndrome rate.
   Performance in Fig 1 is reported as an **effective post-recovery bit/phase-flip probability `p`**
   (`ρ ↦ (1−p)ρ + p AρA`), averaged over `{g_j}` with `A=Z_l` (bespoke), `X_l` (repetition), `Z`
   (physical), under a **Gaussian `θ ∼ N(0,σ)`** — i.e. an *infidelity-vs-noise-strength* curve, NOT a
   syndrome/silent-rate.

So the closest common-mode-Gaussian object the paper contains is the **Fig 1 residual error `p` vs σ** for a
**Gaussian-distributed collective phase θ** — the same physical driver as our f→common limit, but scored as
a *bespoke-code infidelity*, never as a *stabilizer-code syndrome-silent-flip rate*.

## Generalization to correlated normal-mode dephasing (the one bridge to our program) [paper]
The paper's penultimate paragraph is the most relevant to us:
- "they can correct **spatially-correlated phase noise** beyond that arising from common fluctuators. For
  instance, classical white noise in the energy gaps of register qubits leads to Lindblad error operators
  **`L_j = √λ_j ⃗c_j · (Z1,…,Zn)`**, where `{√λ_j ⃗c_j}` describes the noise's **normal modes** [ref 43].
  In the limit of spatially uncorrelated noise the `L_j`'s become Pauli Z operators; however, **correlated
  noise produces `L_j`'s with unequal amplitudes `√λ_j`.**" [paper, verbatim]
- This is precisely the **normal-mode picture of collective dephasing** our source layer uses (shared bath /
  1/f / TLF pushing correlated `Σ c_j Z_j`), and it comes with an explicit **code-design response** (correct
  strong modes to higher order via choice of `V`). But it is a *code-tailoring* remark, still not a
  syndrome/silent-rate for a stabilizer code.

## A9 verdict [ours]
**MAINTAIN (b)/(c) — this paper is ADJACENT, not prior art, for our specific claims. It does NOT compress
either the f-interpolation or the syndrome-silent-floor component to (a).** Reasoning:
1. **Shared generator, different object.** It uses the **identical common-mode dephasing generator
   `H_E=Σ g_j Z_j`** (Eq 2) and even the **normal-mode `L_j=√λ_j ⃗c_j·(Z⃗)` correlated-dephasing picture**
   (last §) that our source layer rests on — so it is a legitimate, strong citation for the *physics* of the
   common-mode/collective-dephasing mechanism and for the common↔uncorrelated limit ("uncorrelated ⇒ Paulis;
   correlated ⇒ unequal amplitudes"). This validates the *existence and physicality* of our `f`
   common↔local axis.
2. **But it never computes any stabilizer-code syndrome, detection-event, or silent-logical-flip rate**, and
   it is a **bespoke non-Pauli-code design paper**, not a surface/repetition-code twin. So it owns neither
   (i) our syndrome-silent-RUN rate as an observable, (ii) the detection-event DECREASE at fixed marginals,
   nor (iii) the `f`-knob *scored on the syndrome-silent floor*. The `t^O(2ⁿ)` scaling is a
   *correction-order* of a bespoke code, unrelated to any silent-syndrome rate.
3. Net for A9: cite Layden as the **physics grounding for the common-mode-dephasing generator + the
   correlated-normal-mode limit (an (a)-grade citation for the MECHANISM `H_E=Σg_jZ_j`)**, but it is
   **adjacent** to our silent-floor / detection-drop / stabilizer-code observables, which remain **(b)
   folklore-unquantified + (c) apparently-novel** as A9 currently classifies them. It does not disturb the
   Clader 2101.11631 moment-law attribution either (Layden's Fig 1 is a Gaussian-θ infidelity curve, not the
   double-factorial moment law).

## Decisive verbatim quotes [paper]
- **The common-mode generator (our A9 mechanism):** `H̃ = Σ_ℓ λ_ℓ|ℓ⟩⟨ℓ|_f ⊗ H_E` where `H_E := Σ_{j=1}^n
  g_j Z_j`; "Jumps of the fluctuator therefore induce spatially-correlated random telegraph noise in the
  register, which causes dephasing." (Eq 2 + surrounding, p1)
- **NOT a DFS (DFS-adjacent):** "Note that CFD does not generally produce a decoherence-free subspace
  (DFS)." (p2) / "Eqs. (10) and (11) reduce to a DFS in the limit where one exists (`|g1|=|g2|`), but this
  is in practice rare." (p3)
- **The `t^O(2ⁿ)` scaling (correction ORDER, exponential in n):** "while the repetition code on n qubits
  corrects errors to order `t^O(n)`, with t the time between recoveries, our codes correct to order
  `t^O(2n)`." (abstract) / `n = ⌈1 + log₂(q+1)⌉` (Eq 3) ⇒ saturating gives `q = 2^{n−1}−1`.
- **It corrects the collective error, NOT individual/2-qubit Paulis:** "by design, however, it does not
  correct for `Z1Z2`, nor `Z1` or `Z2` individually, none of which belong to `E`. Rather, it corrects CFD
  with fewer qubits than the smallest repetition code precisely because we have chosen not to correct
  individual Pauli operators." (p3)
- **Correlated normal-mode dephasing (the bridge to our source layer):** "classical white noise in the
  energy gaps of register qubits leads to Lindblad error operators `L_j = √λ_j ⃗c_j·(Z1,…,Zn)`, where
  `{√λ_j ⃗c_j}` describes the noise's normal modes. In the limit of spatially uncorrelated noise the
  `L_j`'s become Pauli Z operators; however, correlated noise produces `L_j`'s with unequal amplitudes
  `√λ_j`." (p4)
- **Performance object = infidelity vs σ (not a syndrome rate):** "CFD followed by a QEC recovery (if
  applicable) results in an effective phase- or bit-flip channel `ρ ↦ (1−p)ρ + p AρA`, where `A = Z` for
  the physical qubits, `X_l` for the repetition codes, and `Z_l` for hardware-efficient codes." (Fig 1
  caption, θ∼N(0,σ))

## Limitations [paper / read-coverage]
- **L1 (read-coverage).** The **Supplemental Material [ref 31]** (pseudothresholds for n=2,3; miscalibration
  robustness; the non-eigenstate-preserving `H_E∼Σ ⃗g_j·⃗σ_j` analysis) is **NOT in the downloaded PDF** and
  was **not read** — pseudothreshold numbers exist there but are unread; this note covers the 6-page main
  text only.
- **L2.** Bespoke **non-Pauli, non-stabilizer** codes (measured operator `S∉` Pauli group, `{H_E,S}≠0`);
  the framework is code-DESIGN, not surface/repetition-code twin analysis. No detection-event / syndrome-
  rate / silent-flip object anywhere.
- **L3.** Explicitly small/intermediate-scale: "these codes are designed expressly for small- and
  medium-scale qubit registers, and … the exponential reduction in overhead should be understood to apply
  only in such devices." Manifestly **not fault-tolerant** in current form. So no large-d surface-code
  relevance beyond the shared *generator* physics.
- **L4.** Fig 1 uses an "illustrative model of a normally-distributed θ" — a Gaussian collective-phase
  toy, not a measured hardware fluctuator spectrum.
