# Full-text review — Artag, Awaya, Kanezashi, Nagata, Tsukayama, Shimada, Shirakashi, "Complementary quantum and classical records of qubit decoherence" (arXiv:2605.15882v2)

> **Provenance (2026-07-02): FULL-TEXT read (精读).** txt `outputs/papers/2605.15882.txt` (fetch_and_extract.py → PyMuPDF), 16 pages. All page/Eq/Fig/Thm refs from that text via `===== PAGE N =====` markers. Figures not pixel-extracted — figure facts = captions + numbers stated in text.

## Metadata [paper]
- Authors: Jargalsaikhan Artag, Koki Awaya, Takumi Kanezashi, Haruya Nagata, Daisuke Tsukayama, Moe Shimada, Jun-ichi Shirakashi. Dept. of Electrical Engineering and Computer Science, Tokyo University of Agriculture and Technology, Koganei, Tokyo.
- Venue / status: arXiv:2605.15882v2 [quant-ph], 30 Jun 2026. No journal yet. Code: github.com/shrakashlab/QuantumReservoirTomography.
- Type: **simulation** (tensor-network / TDVP spin–boson) + analytic theorems + proposed circuit-QED experiment. Not QEC, not a stabilizer paper.

## Executive summary [paper]
A single decoherence process writes **two complementary records into the SAME environment (bath)** of an unbiased spin–boson model. (1) A **recoverable quantum record**: after a transverse (+x) qubit measurement, the bath is projected onto a Schrödinger-cat-like state concentrated in ONE mode-matched collective bath coordinate (one natural orbital carries >95%, typically 0.97–0.98, of the bath one-body occupation); it has visible Wigner negativity. (2) A **redundant classical which-path record** distributed across physical frequency-band fragments (Quantum-Darwinism-style redundancy R≈13 at T=0 pure dephasing). A parity symmetry gives an **exact non-perturbative identity** |σ_x(t)| = |⟨ψ↑(t)|ψ↓(t)⟩| (qubit coherence = environmental branch overlap) and a **complementarity relation V²+D²=1** (coherent overlap V=|σ_x|, which-path distinguishability D=√(1−V²)) at T=0. Finite temperature **smooths** the quantum record (negativity falls 0.60→~0.10 smoothly, no sharp threshold) while INCREASING classical redundancy (R→~19). All at strong coupling (α_std=1.6, non-perturbative).

## Method (deep) [paper]

===== PAGE 1 =====
```
H= sigma_x + SUM_k omega_k b_k^dag b_k + sigma_z SUM_k lambda_k(b_k^dag + b_k),   (1)
```
Unbiased spin–boson: tunnelling amplitude Δ (written "" in extraction; the Δσ_x term), sub-Ohmic spectral density (Eq. 2) J(ω)=2πα ω_c^{1−s} ω^s e^{−ω/ω_c}, exponent s=0.5, cutoff ω_c=4Δ. Primary coupling α=0.4 ⇒ **α_std = 4α = 1.6, "a strongly coupled, nonperturbative regime"** [PAGE 1].

Chain-mapped (Eq. 3), evolved by two-site TDVP; at each time the **leading natural orbital** c_f(t)=Σ_k f_k(t) c_k of the bath one-body density matrix C_mn=⟨c_m^dag c_n⟩ is the "mode-matched collective coordinate."

===== PAGE 2 =====
Conditional bath state (the object of interest):
```
|psi_B^(+x)(t)> = <+x|psi(t)> / sqrt(P_+x(t)),   P_+x(t)=<Pi_+x>,   (4)
```
Global state in pointer (z) basis:
```
|psi(t)> = c_up(t)|up>|psi_up(t)> + c_down(t)|down>|psi_down(t)>,   (5)
```
The +x projection prepares the branch superposition ∝ c_up|ψ_up⟩+c_down|ψ_down⟩ — "a Schrödinger cat of the two displaced environment branches." Negativity volume V_nc(t)=2∬_{W<0} dq dp |W(q,p;t)| (Eq. 6).

## The theorems / the split (LOAD-BEARING) [paper]

**Definitions of the two records** [PAGE 3]:
```
===== PAGE 3 =====
We denote the remaining coherent overlap by V = |sigma_x| and
the which-path distinguishability by D = sqrt(1 - V^2). A
large V means that the branches still overlap. A large D
means that the environment can tell them apart
```

**Theorem 1 (coherence–overlap identity)** [PAGE 3]:
```
===== PAGE 3 =====
Exact identity (Theorem 1: coherence-overlap).
For the unbiased spin-boson model evolving from a
parity-even bath state, the qubit coherence equals the
conditional environmental branch overlap at all times,
couplings, and tunnelling amplitudes:
|sigma_x(t)| = |<psi_up(t)|psi_down(t)>|.
```
"They agree to about 10^-16 at zero temperature and 10^-11 at the highest temperature" [PAGE 3] — an exact numerical check.

**Theorem 2 (quantum–classical duality / complementarity)** [PAGE 3]:
```
===== PAGE 3 =====
Record complementarity (Theorem 2: quantum-
classical duality). At zero temperature the coherent
branch overlap V = |sigma_x| and the environment's which-
path distinguishability D = sqrt(1 - V^2) obey V^2 + D^2 = 1.
```
"Decoherence thus converts coherent overlap into which-path information. As V decreases, D increases ... The two quantities are measured in different ways and are stored in different parts of the environment." [PAGE 3]

## The MECHANISM driving the split [paper]

The split is driven by **measurement CONDITIONING (transverse readout) + environmental which-path redundancy**, NOT by bath spectral asymmetry / thermal occupation. Verbatim on what exposes the quantum record [PAGE 1]:
```
===== PAGE 1 =====
Coherence between the environmental branches can still be recovered by measuring the qubit in
a transverse basis and selecting the environmental state
associated with one outcome. We refer to this selection
as conditioning. It exposes a second, quantum
record: the branch superposition hidden when the qubit
is simply traced out.
```
And "Why it works" [PAGE 5]:
```
===== PAGE 5 =====
Free evolution entangles the qubit
pointer states |up>, |down> with the two displaced branches
|psi_up>, |psi_down> of the collective bath coordinate. A
transverse (x) readout of the qubit projects the bath
onto the superposition |psi_up> - |psi_down> - the conditional cat
```
The classical record is measurement-basis-free, distributed: "The classical which-path record is redundant and distributed across physical frequency-band fragments" [PAGE 1], quantified by accessible Holevo information over fragments and a redundancy count R [PAGE 4].

## Where temperature / thermal occupation N̄ enters [paper]

Temperature (thermal occupation) is ONLY a **degradation / smoothing knob on the quantum record**, NOT the driver of the quantum-vs-classical split. [PAGE 4–5]:
```
===== PAGE 4 =====
V. THERMAL SMOOTHING OF THE RECORD
Thermal noise does not turn the two-record picture
into a single classical blur. Instead, it smooths the re-
coverable quantum record while leaving the redundant
pointer record visible in fragments.
```
Thermofield relation with n(ω)=(e^{ω/T}−1)^{−1}; added thermal occupation n_g=Σ_j n(ω_j)|g_j|² of the collective mode. **Theorem 3**: in the pure-dephasing limit the conditional physical mode is "exactly a thermal mixture of displaced cat states" [PAGE 5]; "the Wigner negativity, decrease smoothly as the temperature rises." Negativity falls 0.60→~0.10, "remains nonzero throughout," "no sharp threshold" — even where n_g>1/2 [PAGE 5, Fig 5b]. Heating INCREASES classical redundancy R (13→19) while decreasing quantum negativity [PAGE 4, Fig 4c].

## The OBSERVABLE / metric [paper]
- **Quantum record**: conditional Wigner function W^{(+x)}(q,p;t) of the mode-matched collective mode; negativity volume V_nc (Eq. 6). Read out by transverse qubit measurement + condition + mode-matched cavity capture + Wigner tomography (displacement + photon-parity) [PAGE 5–6].
- **Classical record**: accessible pointer (Holevo) information χ(S:F) of frequency-band fragments; redundancy R = number of disjoint fragments each carrying ≥(1−δ) of the full classical record, δ=0.1 (90% threshold) [PAGE 4]. Supplementary S8 for formulas.
- **The identity Thm 1** is both a physical result and a strict machine-precision numerical check.

## Findings + numbers [paper]
- α_std=1.6 (strong coupling), s=0.5, ω_c=4Δ, T/Δ ∈ [0,1].
- One natural orbital carries 1/Σ_j λ_j² ≈ 0.96 (0.97–0.98; exactly 1 in pure dephasing) of bath one-body occupation [PAGE 2].
- T=0: peak conditional V_nc ≈ 0.60, W_min ≈ −0.51; rises only mildly with coupling (0.53 at α=0.2 → 0.61 at α=0.5) [PAGE 4].
- Unconditional negativity peak ≈ 0.13 (several-fold smaller) — conditioning is what exposes it [PAGE 4].
- Redundancy R≈13 (T=0, pure dephasing, 90% threshold) → ~19 at T/Δ=1 [PAGE 4–5].
- Thm1 identity agreement: 10^{-16} (T=0), 10^{-11} (hottest) [PAGE 3].
- P_+x ≈ 1/2 (cat recovered in ~half the runs, not a rare outcome) [PAGE 4].
- Representative device: Δ/2π≈1 GHz ⇒ T/Δ=1 is 48 mK [PAGE 6].

## Limitations [paper]
- Single qubit, single decoherence process — NOT a QEC code, NOT repeated stabilizer rounds.
- "Record" = ENVIRONMENTAL (info written into the bosonic bath), NOT a repeated-readout / syndrome-measurement record.
- Complementarity V²+D²=1 is a **T=0** statement; finite-T uses thermofield-purified overlap and mixed-state distinguishability bounds [PAGE 3].
- n_g is regularization (IR-cutoff)-dependent for the sub-Ohmic bath; only negativity is robust [PAGE 5].
- Proposed experiment (mode-matched capture + Wigner tomography) not performed; recoherence-fidelity left to future work.

## Relevance to AI_QEC / Bone A [ours]
**Different axis — does NOT pre-empt our Bone A record decomposition.** Point-by-point against the 4 extraction questions:

1. **Their records**: quantum = recoverable **environmental** cat state in one collective BATH mode (conditioned on transverse qubit readout); classical = which-path pointer info distributed across BATH frequency fragments. Related by V²+D²=1 (V=|σ_x|=branch overlap, D=which-path distinguishability). [ours] This is a **coherence-vs-which-path (visibility/distinguishability) complementarity** — Englert-style — living entirely in the environment.

2. **Driver**: measurement CONDITIONING (transverse basis) + Quantum-Darwinism redundancy, NOT bath spectral asymmetry / N̄. Our Bone A quantum part is driven by **bath spectral ASYMMETRY / thermal occupation N̄** (the non-unital emission↔absorption imbalance). Here N̄ enters only as a **smoothing/degradation** of the quantum record (Thm 3, Fig 5) and as a booster of classical redundancy — it is NOT the object that splits quantum from classical. **Orthogonal drivers.**

3. **Record type**: **ENVIRONMENTAL** (info written into the bosonic bath), read by collective-mode Wigner tomography / fragment Holevo info. Our record is the **repeated stabilizer / readout MEASUREMENT record** (a monitored measurement stream), and our comparator is the best CLASSICAL IMITATOR of that record, not an environmental branch overlap. **Different object.**

4. **Coupling / scaling structure**: strong coupling α_std=1.6, non-perturbative TDVP. **No g²/g⁴ perturbative expansion and no additive-floor (non-unital floor + measurement-modulated part) decomposition** — confirmed absent. Their split is the exact algebraic V²+D²=1, not our floor+modulation additive split. Our g⁴-saturating power / non-unital-floor structure has no counterpart here.

**Bottom line for novelty adjudication**: nearest-neighbor in VOCABULARY ("quantum record" / "classical record" / "decoherence") but a DIFFERENT physical axis. Theirs is Zurek/Darwinism environmental complementarity (visibility↔which-path, V²+D²=1) driven by conditioning; ours is a monitored-measurement-record distance decomposed into an N̄-driven non-unital floor + a measurement-modulated part. Cite as prior art for the "two-records" framing and the coherence–overlap identity, but it does NOT own our record-wedge decomposition. No overlap on driver, object, or perturbative structure.

## How to use / trust + open questions [ours]
- Trust: full 16-page text read; figures not pixel-extracted (figure facts from captions + in-text numbers, which are explicit here).
- Reusable methodology (not the physics): thermofield/T-TEDOPA chain mapping [21], TDVP with shifted-boson basis, characteristic-function-as-MPS-overlap Wigner reconstruction — all standard bosonic-bath TN tooling, potentially relevant if we ever build a bosonic-bath teacher, but NOT our current carrier.
- Reference to cite in the Bone A prior-art paragraph as the near-neighbor "complementary records" work that is a DIFFERENT axis (environmental which-path vs our measurement-record floor).
- Open question [ours]: their Thm 1 (coherence = branch overlap) is an exact system–environment identity — worth noting our non-unital floor is NOT such an identity but a spectral-asymmetry-sourced object; the contrast sharpens our positioning.
