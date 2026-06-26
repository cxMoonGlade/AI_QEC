# Full-text note (精读) — Tan, Pattison, McEwen, Preskill, "Resilience of the surface code to error bursts" (arXiv:2406.18897)

> **Provenance (2026-06-25): FULL-TEXT 精读.** PDF → txt `outputs/papers/2406.18897.txt` (13 pp). Caltech/
> UMD/Google, *Phys. Rev. A* (2025). The **burst-error MODELING + resilience** anchor for the teacher's
> burst mechanism (the user's "burst 需要" teacher-completion item). Sibling burst notes pending: McEwen
> 2104.05219 (phenomenology), Kurilovich 2506.18228 (deployed phase-burst signature).

## Why load-bearing [ours]
The paper that (a) gives the **burst CHANNEL recipe** a teacher needs (single-round elevated depolarizing,
uniform across the block), (b) gives the **decode-independent observable** (per-round syndrome-density spike,
their Fig 5 is a **d=3, 20-round** example), and (c) proves **surface-code RESILIENCE to bursts** (detect +
standard decode suffices) → directly sets the strategic verdict that **burst-DECODING is owned**, so burst's
value for us is purely as a **teacher misspecification-axis**.

## The noise model [paper]
- Surface-code memory experiment, duration `T = 2d`, a SINGLE error burst at round `T/2`; failure = logical-Z
  flip after MWPM correction. Stim-simulated.
- Two background models, each assigning one noise parameter `p` per round: **phenomenological** (data-qubit
  Pauli-X at rate `p` + perfect SE + measurement flip `p`) and **circuit-level depolarizing** (1-/2-qubit
  depolarizing rate `p` after each gate + measurement flip `p`).
- **Burst = replace `p` with the burst rate `pB` for the single burst round.** Circuit-level: ALL gate ops in
  that round fail w.p. `pB`. (The assumption: after hardware mitigation the burst is limited to ONE SE cycle;
  spatially the elevated rate is pessimistically **uniform across the entire code block**.)
- Decoding: MWPM on the weighted decoding graph; the decoder is GIVEN the burst time and updates that round's
  edge weights. (They note the burst time is trivially inferable from the per-round syndrome Hamming weight;
  decoder performs nearly as well without the prior — App 2 has an MLE-of-which-rate example.)

## Key findings + numbers [paper]
- **Burst threshold `pB*` ≫ sustainable threshold.** Phenomenological: a burst of `pB = 7%` only depresses the
  sustainable threshold from ≈3% → ≈2.7%; `pB* = 9.05(2)%` at background `p=2%` (Fig 2). The surface code is
  **stable to even large single-round bursts** at finite background — *a priori not obvious*.
- **Circuit-level burst bleeds into the NEXT round.** Fig 5 (d=3, 20 rounds, burst @ round 11, `p=0.1%`,
  `pB=1%`): the marginal syndrome-bit value (= error-density proxy averaged over a time slice) spikes at the
  burst round, **confined to 1 slice (phenom) but 2 slices (circuit-level)** — because some burst-round errors
  aren't detected until the following SE cycle. Circuit-level burst threshold depends more strongly on `p`.
- **Rare-event regime.** After a burst the error population settles in ~`d` cycles; the single-burst idealization
  is valid for `d ≪ 1/Γ` (burst mean-time τ). For τ = 1 min @ 10 µs cycle → `τ ≈ 10⁷` logical cycles.
- **Teraquop footprint** (eq 3): per-cycle-qubit logical failure `P_L(pB,p) ≈ (1/τ)·q̃_{d,B}(pB,p) +
  (1−1/τ)·q̃_d(p)`; `2d²` qubits at distance `d`. Result: a burst **15× the background** with τ=1min, p=0.1%
  raises the teraquop footprint **< 2×**. "An error burst an order of magnitude above background does not
  appreciably affect the footprint."
- Stat-mech mapping: 3D random-bond Ising with increased disorder on a 2D immersed surface.

## Limitations / what does NOT apply [paper → ours]
- **Idealized**: (1) burst = single round (real cosmic-ray bursts last **hundreds–thousands of cycles** before
  mitigation — the paper explicitly assumes gap-engineering/QP-traps shorten this); (2) **no inter-round
  correlation** within the burst (assumed independent "for simplicity"); (3) burst rate **uniform across the
  whole block** (pessimistic; real bursts spatially decay from the impact). Extending to multi-round +
  spatially-structured bursts is named as future work.
- It's a RESILIENCE/threshold paper, not a channel-derivation paper — the operator content is just depolarizing.

## Relevance to the burst teacher [ours]
- **Teacher recipe (grounded):** inject elevated depolarizing `pB` (≈10–100× background, per McEwen T1↓1–2
  orders) across ALL code qubits for a burst window. Tan's idealized = 1 round; we can also do the **realistic
  multi-round** (exponential decay over ~tens of cycles) — the catastrophic/uncorrectable case Tan omits.
- **Burst is Pauli depolarizing, spatially + temporally CORRELATED** → it REUSES the existing ⑤a (spatial-corr)
  + ⑤b (Kam temporal-corr, `kam_nonmarkovian_surface_code_2410.23779`) machinery; it is **NOT a new operator**
  (unlike leakage). Cheap to build: a rare, chip-wide, multi-round elevated-depolarizing trigger + a detection
  flag. (Connects burst to the streaky Class-1/2 temporal correlation Kam proves → power-law LER.)
- **Observable (decode-independent):** the per-round detection-density spike (Fig 5 proxy) + chip-wide
  simultaneity (all stabilizers at once) — distinct from leakage (localized) and always-on ZZ. This is the
  falsifiable fingerprint the teacher must reproduce and the certify moment-check target.
- **Strategic [ours]:** Tan + Willow (~1/hr residual, 10⁻¹⁰ floor) + detect-and-discard ⇒ **burst-DECODING is
  OWNED**. Build burst ONLY as a teacher misspecification-axis: a rare chip-wide correlated event the iid-Pauli
  learner misses, to test whether the **learner's UQ bands widen / flag out-of-model** correctly.

## Trust [ours]
Full-text 精读 of all 13 pp (model §II, results §III incl. Figs 2–7, teraquop, conclusion). The single-round
depolarizing model, `pB*`≫sustainable result, the d=3 Fig-5 density observable, and the <2× teraquop at 15×
background are directly-quoted, load-bearing facts.
