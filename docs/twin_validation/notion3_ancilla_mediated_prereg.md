# notion-3 on the FAITHFUL ancilla-mediated carrier — Pre-Registration (theory-first)

Status: PRE-REGISTRATION, 2026-07-05. Predictions written BEFORE the run; a miss is a finding, not a re-fit.

**Purpose.** The notion-3 SEPARATION (quantum K>0 vs classical K=0, corner-confined) was demonstrated on the
FAIR-TEST's **single-qubit σx proxy** (measure the data qubit's X directly each round). A real QEC circuit
NEVER measures the data qubit directly — it extracts a **joint stabilizer parity via an ancilla** (CX → Born
→ reset). The memory ([[project-cpdiv-notion-hierarchy-passive-record]]) flags this as **a STRONGER twirl than
the σx toy**. This run tests whether the quantum non-classicality signature **K survives the faithful
ancilla-mediated joint-parity extraction**, or is twirled out — the load-bearing faithfulness question for the
whole notion-3 result. Scope: SIMULATOR record-char faithfulness (does the quantum signature survive the REAL
measurement), NOT twin recovery.

## 0. Grounding ledger (all read; reuse)

| claim | anchor | reuse |
|---|---|---|
| notion-3 = K (Milz Kolmogorov violation) on the record; corner-confined | `notion3_quantum_vs_classical_prereg.md` §8 (SEPARATION HOLDS CORNER) | K_stat/M_mem/pseudomode `build_L` verbatim |
| ancilla-mediated stabilizer extraction (CX → Born → reset) is the faithful measurement | `corrected_multitime_observable_run.py` (classical notion-2 carrier: `cnot3`, `syndrome_unitary`, Born-measure ancilla, reset) | the carrier structure (adapt Z-parity → X-parity for σz-dephasing) |
| joint-parity ancilla-mediated is a STRONGER twirl than single-qubit; the deepen joint-parity twirl did NOT kill K (on a toy) | [[project-cpdiv-notion-hierarchy-passive-record]]; deepen DM2 | the prediction |
| dephasing σz is detected by an X-type stabilizer (anti-commutes) | Kam Class-1; C4-analog v2 (K(X)>0 for σz bath) | X-stabilizer choice |

## 1. Mechanism (anchored)

Exact-DM: **2 data (d0,d1) + 1 ancilla (a) + 1 pseudomode** (Fock nmax, convergence-checked; dim 8·nmax —
declared feasibility-bounded, use expm/expm_multiply + an OOM guard; cap nmax at the converged value if the
top of the ladder is infeasible). Bath σz-coupled to **d0** (`H = ζ b†b + σz^{d0}·g(b+b†)`, collapse √(2γ)b,
mode persists). Per round: idle-evolve under the GKSL; extract the **X_{d0}X_{d1} joint stabilizer** via the
ancilla (H a → CX/CZ entangling → H a → Born-measure a in Z → reset a) — the faithful joint-parity syndrome.
Record = the ancilla syndrome M_t. Classical contrast arm: incoherent σz-dephasing on d0 with a time-correlated
latent, SAME ancilla-mediated X-parity extraction.

## 2. Observable (unchanged — the RIGHT one)

Per arm, on the ancilla syndrome record: **K** (Milz Kolmogorov violation, notion-3), **CMI** I(s1;s3|s2)
(beyond-Markov-1), **M_mem** (L1). Same statistics as `notion3_quantum_vs_classical_run.py`; only the CARRIER
changes (σx proxy → ancilla-mediated joint parity). The DIRECT comparison is K_ancilla vs K_proxy.

## 3. Predicted behavior (falsifiable) + epistemic classes

- **(a) exact — the null still holds:** CLASSICAL arm ⇒ **K=0** on the ancilla carrier too (incoherent
  dephasing is non-invasive regardless of the readout path; C4-analog). The K-witness null must survive the
  carrier change.
- **(b) band — THE faithfulness question:** the QUANTUM arm ⇒ **K>0 SURVIVES** the ancilla-mediated joint-parity
  extraction (deepen: joint-parity twirl did not kill K), but **ATTENUATED** vs the σx proxy (the joint-parity
  projection + CX + ancilla Born + reset is a stronger twirl) ⇒ the corner is **the same or SHRUNK/shifted**
  (K smaller ⇒ N_detect(K) larger ⇒ possibly narrower feasible-g). Registered direction: `0 < K_ancilla ≤
  K_proxy`. **Falsifier (weighty either way):** if `K_ancilla → 0`, the σx proxy OVERESTIMATED — the faithful
  stabilizer extraction twirls out the quantum signature ⇒ notion-3 is NOT visible on a real QEC record (a
  strong finding that would re-open the whole quantum-contribution claim); if `K_ancilla ≈ K_proxy`, the proxy
  was faithful and notion-3 stands on the real carrier.
- **(c) gate:** Fock convergence (to 1e-4 within the feasible nmax); classical K < 1e-8; P_all normalized;
  ideal-extraction sanity (a NO-bath run ⇒ K=0, flat record).

## 4. Independent ground truth (non-circular)

- The GKSL `build_L` reuses the notion-3 build (already GT-checked vs the independent-boson closed form to
  1.8e-10) — re-assert. The ANCILLA-extraction unitary checked: (i) on a known X-eigenstate of (d0,d1) the
  ancilla reads the correct parity deterministically (a closed-form check, no oracle); (ii) with the bath OFF,
  the record is flat (Markov-0) and K=0 (the extraction adds no spurious memory/invasiveness).
- Cross-check: at the σx-proxy limit (if the joint parity is reduced to a single-qubit X readout), K must
  match the FAIR-TEST/notion3 proxy value — bridging the two carriers.

## 5. Bounded simplifications (declared; unbounded ⇒ STOP)

- **(c) 2 data + 1 ancilla single stabilizer** (not full d=3) — the joint-parity twirl question is exercised on
  one X-stabilizer; full-d3 is a separate MCWF/exact-DM stage.
- **(c) ideal CX / ancilla reset** (the twirl from the extraction itself is the object; gate/reset ERRORS are a
  deferred Class-2 axis).
- **(c) Fock truncation nmax** — convergence-checked within the feasible dim bound (declare the bound; if the
  converged nmax is infeasible at 8·nmax, STOP and report the dim wall).
- **(c) pure-dephasing coupling** (amplitude-damping/leakage = the separate stronger axis).
- **(c) CPU exact-DM** (dim 8·nmax; NOT production GPU compute; OOM-guarded).

## 6. Verdict (provisional, pre-code)

GROUNDED: the K/M_mem/CMI observables + the pseudomode bath (notion-3 run) and the ancilla-mediated extraction
(classical notion-2 carrier) both exist and are reusable; the joint-parity X-stabilizer is the faithful
adaptation. The load-bearing NEW result = does K survive the faithful (stronger-twirl) extraction. PROVISIONAL
until measured; K-survival, K-attenuation-magnitude, and a K→0 twirl-out are all real findings.

## 7. Build org (scouts + builder + un-led reviewer)

Reuse `notion3_quantum_vs_classical_run.py` (K/M_mem/CMI/arms/controls) + `corrected_multitime_observable_run.py`
(ancilla-mediated carrier: cnot3, ancilla Born + reset). Builder writes
`outputs/twin_validation/notion3_ancilla_mediated_run.py` (2data+1anc+mode, X-parity extraction, both arms,
K/CMI/M_mem, Fock convergence within the dim bound + OOM guard, coupling sweep + corner, the K_ancilla-vs-K_proxy
comparison, classical-K null, no-bath sanity, extraction GT). Scripted-execution + smoke. Un-led reviewer vs
this prereg. Then serial CPU run (exact-DM, no GPU, no concurrency).

## 8. POST-BUILD FINDING (2026-07-05) — the §1 design is DEGENERATE; question NOT yet answered

**Registered prediction b1 turned out STRUCTURALLY UNTESTABLE in the built configuration — a (b) miss surfaced
as a finding (not a re-fit), per epistemic-status discipline.** The v1 build
(`outputs/twin_validation/notion3_ancilla_mediated_run.py`, smoke only) was mechanically CORRECT + honest (all
5 controls fired: extraction-GT 1e-15, classical-K null genuine on a non-degenerate record, K = genuine Milz
not error-A, reproducible sha; builder flagged the issue in its own caveat) — but the un-led reviewer (blocker)
proved: **with the bath σz-coupled to d0 ONLY, d1 stays |+> so X_{d0}X_{d1} ≡ X_{d0} EXACTLY** ⇒ the joint-parity
record is byte-identical (5e-16) to the single-qubit σx proxy, for BOTH arms ⇒ `K_ancilla == K_proxy` is a
mathematical IDENTITY, not a measured survival. The v1 also just re-derives deepen DM2 (already "K survives the
joint-parity twirl"). ⇒ **the "stronger twirl" question the §1-§3 design promised is NOT answered by v1; the
`NOTION3_ANCILLA_K_SURVIVES_INTACT` gate is a tautology and is VOID.** The genuinely-different test needs a
**non-inert d1** (both data qubits bath-coupled).

## 9. REDESIGN (v2) — shared bath coupling BOTH data qubits (the genuine, non-degenerate test)

**Mechanism (corrected):** shared pseudomode bath coupling BOTH data qubits,
`H = ζ b†b + (g₀ σz^{d0} + g₁ σz^{d1})(b+b†)`, collapse √(2γ)b, mode persists; data init |++>. Now d1 genuinely
dephases (non-inert), `(g₀σz^{d0}+g₁σz^{d1})` anti-commutes with X_{d0}X_{d1} (the coupling imprints on the joint
parity), and the joint-parity record is NO LONGER the single-qubit proxy. This is ALSO the CORRELATED
shared-bath configuration central to the simulator's contribution (not just a faithfulness upgrade).

**The genuine observable:** sweep **r = g₁/g₀ ∈ {0, 0.25, 0.5, 0.75, 1.0}** (r=0 ≡ the proxy = the v1 identity
= a built-in bridge; r=1 = symmetric fully-correlated shared bath). Measure K on the joint-parity ancilla
record vs r. **Registered prediction (b, falsifiable):** K DEPARTS from K_proxy as r grows (the joint-parity
twirl turns on); at r=1 either K SURVIVES (>0, the quantum non-classicality of the correlated shared bath
reaches the coarse joint-parity syndrome — deepen suggests survival) or is ATTENUATED/TWIRLED-OUT (the coarse
joint measurement kills the correlated-common-mode quantum signature — a strong finding, connects to
Srivastava blind-spots). Non-degenerate ⇔ record(r>0) ≠ record(proxy) (assert byte-difference > 1e-6 at r=1).
Classical shared-bath arm ⇒ K=0 at all r (the null survives). Controls + Fock convergence + corner as before.
**Falsifier for the design itself:** if record(r=1) is STILL identical to the proxy, the redesign is also
degenerate ⇒ STOP + rethink (the reviewer must confirm non-degeneracy at r=1 before the full run).

## 10. Post-run results (v2, 2026-07-05) — K SURVIVES but is LARGELY TWIRLED OUT by the faithful joint parity

`outputs/twin_validation/notion3_ancilla_mediated_run.py` v2 (FULL; `python-exit=0`; evidence
`notion3_ancilla_mediated.json` sha256 `823342df…` over script+json bytes + sidecar). Built via workflow
(builder v1→v2 + un-led reviewer `meets_spec=true`, `nondegenerate=true` — reviewer independently reproduced
from scratch: own full 8·nmax Liouvillian AND own reduced superop + factorization proof); the wording minor
fixed. **NON-DEGENERACY CONFIRMED: max|P_all(r=1) − P_all(proxy)| = 0.410 ≫ 1e-6** (the v1 tautology is broken;
r=0 bridge exact 9.4e-16). Fock-converged nmax=18.

**The ratio sweep r = g₁/g₀ (g₀=0.5) — K is NON-MONOTONE; memory grows monotonically:**

| r | K(ancilla) | K/K_proxy | M_mem | CMI | max\|dP vs proxy\| |
|---|---|---|---|---|---|
| 0.0 (proxy) | 5.91e-2 | 1.00 | 0.028 | 0.00065 | 9e-16 |
| 0.25 | 7.83e-2 | **1.33** ↑ | 0.038 | 0.0012 | 0.067 |
| 0.5 | 6.84e-2 | 1.16 | 0.090 | 0.015 | 0.214 |
| 0.75 | 2.06e-2 | 0.35 ↓ | 0.148 | 0.050 | 0.353 |
| 1.0 (symmetric) | **3.32e-4** | **0.0056** ↓↓ | 0.166 | 0.069 | 0.410 |

**Finding.** As the shared bath goes from single-qubit (proxy) to fully-correlated (r=1), the quantum
non-classicality K **first rises ~1.3× (partial correlation) then COLLAPSES ~178×** at full correlation, while
the record MEMORY (M_mem/CMI) grows monotonically. At r=1, K SURVIVES (3.3e-4, a real Kolmogorov violation, a
MEASURED departure) but is **detection-INFEASIBLE at g₀=0.5 (N_detect(K)=8.2e7)** and feasible only in a
**middle g₀ band [0.1, 0.35]** (non-monotone in g₀ too; corner_only=False — infeasible both below g₀=0.1 and
above g₀=0.35). ⇒ **the coarse joint-parity syndrome LARGELY TWIRLS OUT the correlated-common-mode quantum
signature; the single-qubit σx proxy OVERESTIMATED the fully-correlated K by ~178×.**

**Controls (all fire):** factorization GT 1.3e-17 (reduced (d0,d1,mode) ⊗ I_a == full Liouvillian); extraction
GT 1.3e-15; 2-qubit collective-dephasing independent-boson GT 6.8e-10 (adapted for the shared bath, NOT
dropped); no-bath sanity K=8.9e-16 flat; classical shared-bath null K=7.2e-16 with real memory
(M_mem=0.087/CMI=0.0119, both qubits dephased). K = genuine Milz Kolmogorov violation on the ancilla record
(reviewer-verified from scratch, not error-A).

**Verdict / roadmap (sharpened).** notion-3 (quantum discord on the record) **survives the faithful
ancilla-mediated joint-parity carrier but is FAR more fragile than the σx proxy showed** — for a
fully-correlated shared bath it is ~178× attenuated and detection-infeasible except a middle g₀ band. This is a
**Srivastava-type blind-spot**: the coarse joint-parity stabilizer is largely blind to the correlated
common-mode quantum signature. Combined roadmap: **notion-2 (classical multi-time memory) = broadly achievable
AND strengthens with correlation; notion-3 (quantum non-classicality) = real but corner/band-confined AND the
faithful joint-parity measurement twirls most of it out.** The proxy-level notion-3 result stands as an upper
bound; the faithful carrier is the honest one. PROVISIONAL; faithful upgrades remaining: the
amplitude-damping/leakage axis (a non-benign, non-common-mode coupling that the joint parity may NOT twirl
out — potentially the broader quantum signature); full d=3 surface-code stabilizers. Nothing built on it yet.
