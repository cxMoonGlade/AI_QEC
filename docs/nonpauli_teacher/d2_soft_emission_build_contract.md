# D2 — soft emission build contract (terminal-soft scope)

**Status:** build spec / interface contract for D2 (the soft-emission deliverable of the soft-readout
③ phase). Governs the ≥3-disjoint-builder build. Authority: `d1_soft_readout_grounding_prereg.md`
(the grounding + pre-reg, §2 model, §6 D2, the L-soft ledger). Binding: `docs/FAITHFULNESS_PROTOCOL.md`,
`CLAUDE.md` (scripted-execution, GPU-only model-compute, commit-gate on `src/`).

**Scope (user decision 2026-06-22): TERMINAL-SOFT.** Soft analog IQ is emitted ONLY at the terminal
per-data-qubit readout (the carrier models 9 data qutrits; the syndrome is a hard joint-parity POVM —
no per-qubit level there; per-round soft-syndrome needs explicit ancillas → 3^17 DM → no oracle →
DEFERRED/PROVISIONAL, NOT D2). The per-round syndrome stays byte-identical to ⑦ (hard).

---

## 0. What D2 delivers

A soft-IQ EMISSION layer at the terminal readout + its seam + its emission-level certification. NO
floor (D3), NO decoder/headroom (D4). Three disjoint builds (A/B/C) + an un-led review.

## 1. The emission model (the load-bearing physics — A owns; I, the orchestrator, fix the math here)

IQ point `z=(I,Q) ∈ ℝ²`. Per-level Gaussian `f^{(k)}(z)=𝒩(z; c_k, Σ_k)`, `k∈{0,1,2}`:

- **Computational blobs (1-D-lossless, §2.1):** `c_0=(+1,0)`, `c_1=(−1,0)` (means ±1 on the I
  discriminant axis, separation 2); `Σ_0=Σ_1=σ²·I₂` isotropic. `σ=1/SNR`, `SNR=Φ⁻¹(1−p_m)` (the
  (a)-exact relation; the Q axis is pure noise for `|0⟩/|1⟩` ⇒ the I-projection is lossless).
- **`|2⟩` blob (the bracket, §2.2/§3.2):** `c_2=(c_2I, c_2Q)`, `Σ_2=σ_2²·I₂` (default `σ_2=σ`; `σ_2`
  is the F2 residual-freedom knob). Parameterized by GROUNDED knobs, geometry DERIVED:
  - `b` (the ⑦ leaked-readout bias, the anchor) fixes the I-projection: the 2-state threshold at `I=0`
    (bit=0 if I>0 [`|0⟩` side], bit=1 if I<0 [`|1⟩` side]) gives `β₁=P(I<0 | |2⟩)=Φ((0−c_2I)/σ_2)`;
    **set `β₁=b` ⇒ `c_2I = −σ_2·Φ⁻¹(b)`** (b>0.5 ⇒ c_2I<0, the `|1⟩` side — matches "`|2⟩` reads 1").
  - `P(2→2)_target` (correct-`|2⟩`-ID, the bracket, §3.2: worst 0.5–0.7 / repr 0.85–0.90 / cap 0.94)
    fixes the OFF-AXIS magnitude `|c_2Q|`: solve `P(2→2)=∫_{R_2} f^{(2)}(z)dz = P(2→2)_target` where
    `R_2 = {z : f^{(2)}(z) ≥ f^{(0)}(z), f^{(1)}(z)}` is the 3-state ML decision region (numerically,
    by quadrature/MC on the 2-D plane). `c_2Q=0` ⇒ `|2⟩` collinear (worst-for-soft); larger `|c_2Q|`
    ⇒ better-separated; capped at the literature `P(2→2)≤0.94`.
  - **Round-trip cert (A's deliverable):** from the SOLVED `(σ, c_2I, c_2Q, σ_2)`, recompute `β₁` and
    `P(2→2)` and assert they match `(b, P(2→2)_target)` to tol; assert `P(2→2)≤0.94` (reject
    unphysical). This is the anti-toy guard that the geometry is pinned by grounded knobs, not free.
- **Level draw:** given a measured level `k̄∈{0,1,2}`, draw `z∼f^{(k̄)}(z)` (GPU; one 2-D normal).
- **Hardening map:** `bit(z) = 0 if I>0 else 1` (the ML 2-state threshold) — recovers ⑦'s `hard-2`.
- **Soft likelihood + LLR (decode/floor side):** `P(z|k)=f^{(k)}(z)`; the `|0⟩/|1⟩` soft edge weight
  reduces to Pattison's `(2/σ²)|I|` (L-soft-2 closed-form check); the 3-class posterior `P(k|z)` (Ali
  Eq. 1 / Varbanov §3.2) for the `|2⟩`-aware weight.

## 2. Terminal-soft integration (B owns) — the forward + seam

- **`mps_forward.py:_terminal_readout`** gains a soft mode. The faithful terminal read: realize each
  data qutrit's LEVEL `k̄∈{0,1,2}` by the 3-outcome projective measurement (`{|0⟩⟨0|,|1⟩⟨1|,|2⟩⟨2|}`,
  Born-sampled) — the terminal IS the last op, so the post-measurement state is irrelevant (NO
  backaction concern; L-soft-4 is satisfied by construction at the terminal). Then:
  - `hard-2` mode = `bit(k̄)`: 0→0, 1→1, 2→Bernoulli(b) — REPRODUCES ⑦'s biased-bit terminal exactly.
  - `hard-3` mode = report `k̄` (the level / leakage flag).
  - `soft` mode = draw `z∼f^{(k̄)}(z)` (via A's emitter) and report `z`.
  The within-cycle (per-round) path is UNCHANGED (the X/Y DD echoes + the hard parity syndrome stay
  byte-identical — L-soft-8). The logical flip = `parity(bit(k̄) over the logical support) XOR m` in
  hard-2 (== ⑦); the hard-3/soft modes emit `k̄`/`z` (the decoder computes the flip).
- **`seam.py`** gains `teacher_shots_to_soft_events` (or a soft `sample` path): per shot emit
  `(detection_events[N, R·n_stab] uint8  — the HARD syndrome, byte-identical to ⑦,
    terminal_levels[N, n_data] uint8 (hard-3) OR terminal_iq[N, n_data, 2] float (soft),
    obs_flips[N] uint8)`. The hard detector path is byte-identical (regression-guarded).

## 3. Certification ledger (C owns) — `tests/test_soft_readout.py`, INDEPENDENT ground truths

Each test FAILS LOUDLY on a broken input (a positive control). C must NOT import A's likelihood for
the ground-truth leg (anti-circular).

| Test | Invariant | Independent ground truth + the broken-input control |
|---|---|---|
| **L-soft-1** | Thresholding the soft terminal (`bit(z)` / `bit(k̄)`) reproduces ⑦'s biased-bit terminal: at `p_m→0` EXACT vs ⑦'s DM terminal `P(flip|m)` at matched `b`; at finite `p_m` vs a `p_m`-generalized biased-bit model. | GT = ⑦'s DM/forward biased-bit terminal (`qutrit_dm`/`floor_backend`, NOT A's code). Control: a wrong `c_2I↔b` map ⇒ thresholded `β₁≠b` ⇒ mismatch trips. |
| **L-soft-2** | The `|0⟩/|1⟩` soft edge weight = Pattison's `(2/σ²)|I|` closed form. | GT = the analytic `(2/σ²)|I|` (hand-coded in the test). Control: a wrong σ-power deviates. |
| **L-soft-6** | (i) the forward stays CPTP (residual <1e-12); (ii) the soft likelihood + the 3-class posterior NUMERICALLY normalize (`∫f^{(k)}dz=1` by quadrature; `Σ_k P(k|z)=1`). | GT = explicit Kraus residual (`floor_backend.cptp_residual`) + a numerical 2-D quadrature (NOT the analytic normalizer). Control: an unnormalized mixture / a non-CPTP slice trips. |
| **L-soft-8** | The terminal-soft path leaves the within-cycle X/Y DD echoes + the hard syndrome byte-identical to ⑦. | GT = ⑦'s hard `sample()` detector record on the SAME seed (byte-identical regression); the seam `g2_positive_control` extended. Control: dropping an echo / perturbing the syndrome fold trips. |
| **L-soft-10** | The `|2⟩` 2-D likelihood + its `(P(2→2), β₁)` round-trip is correct vs an INDEPENDENT 3-Gaussian computation. | GT = an independent (from-scratch, no shared code) 2-D Gaussian Bayes-error / decision-region computation. Control: a mis-placed `c_2` gives the wrong `P(2→2)`. State that L-soft-2 covers only `|0⟩/|1⟩`. |

(L-soft-3/5/9 are D3/D4 — they need the floor/decoder. L-soft-4 is satisfied by the terminal being
the last op — state this, with the structural reason.)

## 4. Protocol (binding)

- **GPU-only model compute** (`device='cuda'`, no CPU fallback); `complex128` for the carrier path,
  `float64` for the IQ. The IQ draws/likelihood can be `float64` on cuda.
- **Scripted execution:** every run is a committed script under `outputs/teacher_prereg/` with
  precondition asserts + printed evidence (shapes/seeds/residuals) + flushed output + an
  `if __name__=="__main__"` guard if it touches multiprocessing.
- **commit-gate:** every `src/` addition (`soft_readout.py`, the `mps_forward`/`seam` edits) is STAGED,
  awaiting user confirmation — do NOT commit. Tests + the contract doc follow the normal flow.
- **Disjoint ownership:** A = `soft_readout.py` (the emitter + its own round-trip + L-soft-2/10 unit
  checks). B = `mps_forward._terminal_readout` soft mode + `seam` soft variant (+ L-soft-1/8 wiring).
  C = `tests/test_soft_readout.py` (the full ledger with INDEPENDENT GTs + broken-input controls).
  A is the foundation (B/C consume A's API — §1); build A → review → (B ∥ C).
- **No `external/` edits.** Reuse the certified `sv_sampler` marshalling / WG leak / codestate / DD
  echoes via `mps_forward` (never reinvent — ADR 0010).

## 5. The interface (the A↔B↔C contract — pin it so the handoff is clean)

```python
# soft_readout.py (A) — the public API B and C build against:
@dataclass(frozen=True)
class SoftReadoutModel:
    p_m: float; b: float; p22_target: float; sigma2_scale: float = 1.0  # grounded knobs
    # derived (solved in __post_init__ / a builder): sigma, c0, c1, c2 (2-vec), Sigma2
    def draw_iq(self, levels: "Tensor[int] (...,)", gen) -> "Tensor[float] (..., 2)": ...   # z ~ f^{(k)}
    def loglik(self, z: "Tensor (..., 2)") -> "Tensor (..., 3)": ...                        # log f^{(k)}(z), k=0,1,2
    def harden_bit(self, z) -> "Tensor[int]": ...                                            # ML 2-state threshold
    def posterior(self, z) -> "Tensor (..., 3)": ...                                         # P(k|z), uniform prior
    def realized(self) -> dict:  # {sigma, c2, beta1, p22, p22<=0.94} — the round-trip cert evidence
```

B's `_terminal_readout(..., soft_model: SoftReadoutModel | None, mode: str)` returns the hard-2 flip
(mode='hard2', == ⑦) or `(levels)`/`(iq)` for hard3/soft. C tests A.realized() + B's three modes.
