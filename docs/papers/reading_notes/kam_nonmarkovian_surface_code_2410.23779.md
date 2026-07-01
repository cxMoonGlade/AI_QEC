# Full-text review — Kam, Gicev, Modi, Southwell & Usman, "Detrimental non-Markovian errors for surface code memory" (arXiv:2410.23779v4, 2025)

> **Provenance (2026-06-25): FULL-TEXT read (精读).** PDF downloaded `arxiv.org/pdf/2410.23779`
> (`outputs/papers/fetch_and_extract.py`, 1.83 MB, 20 pp) → text `outputs/papers/2410.23779.txt` (fitz).
> All §/Eq/Table/Fig refs from that text; the 9 figures' plotted curves are not pixel-extracted (the
> threshold/teraquop/fit NUMBERS are in the running text + Table I, captured here). Open-source code:
> github.com/jkfids/corrqec [ref 67]. Tags: **[paper]** = stated in the paper; **[twin]** = our
> application/inference for `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** John F. Kam, Spiro Gicev, Kavan Modi, Angus Southwell, Muhammad Usman
  (Monash; Data61/CSIRO; Univ. Melbourne; SUTD Singapore). Same Usman group as the Harper crosstalk paper.
- **Venue / status.** arXiv:2410.23779v4 [quant-ph], dated 18 Jul 2025; 14 pp body + refs + 2 appendices.
- **Type.** Classical **forward simulation** (Stim stabilizer) of rotated-surface-code MEMORY under
  TEMPORALLY-correlated (non-Markovian) circuit-level noise; MWPM/PyMatching decoding.

## Executive summary [paper]
The paper isolates the **STRUCTURE** of temporal noise correlation from the marginal rate: it compares
surface-code memory under a **temporally-correlated** model vs a **marginalized-independent** model
**while holding each qubit's per-timestep marginal error rate FIXED** (Appendix A). Findings:
- **Two-time ("pairwise") temporal correlations are BENIGN** — LER scaling ≈ the independent model
  (teraquop d≈27 both); the surface code is robust to them.
- **Multi-time ("streaky") correlations are CATASTROPHIC** — slower-than-exponential LER suppression,
  NO feasible teraquop distance; at d=15 the streaky LER is ~58× the matched-marginal independent LER.
- **By error class (the key result):** correlations on **DATA qubits (Class 0) are benign** (even
  slightly better than independent), but on **SYNDROME qubits (Class 1 SPAM) and two-qubit GATES
  (Class 2) they are catastrophic.** ⇒ the surface code is **resilient to temporal correlations on data
  qubits but highly sensitive on syndrome qubits**, because correlated syndrome errors form **timelike
  string errors** (temporal chains) that combine with spatial strings into logical errors. This
  CHALLENGES the standard "surface code is least sensitive to Class 1" (true for iid RATES, false for
  temporal CORRELATIONS).
- Streaky correlations must decay at least **quadratically** (n≥2), ideally cubically, for a realistic
  teraquop; at high q the LER becomes **non-monotonic** in d (Appendix B).
- **Detector pairwise autocorrelation `¯p_{t,t'}` does NOT distinguish benign from catastrophic** — the
  multi-time streak (timelike string) is the real signature, not the 2-point correlation.

## Error classes + channels (§II.A, Eq 1) [paper]
Circuit-level noise = an error channel after each gate, in three classes [ref 38]:
- **Class 0** = idling/memory on **DATA** qubits → `E1_D` 1-qubit depolarizing.
- **Class 1** = SPAM (reset + measurement) on **SYNDROME** qubits → `E1_X` bit-flip.
- **Class 2** = two-qubit entangling-gate (CNOT) on a **data–syndrome PAIR** → `E2_D` 2-qubit depol.
Channels: `E1_X(p,ρ)=(1−p)ρ+pXρX`; `E1_D(p,ρ)=(1−p)ρ+(p/3)(XρX+YρY+ZρZ)`;
`E2_D(p,ρ)=(1−p)ρ+(p/15)Σ_{P≠II}PρP` (Eq 1a–c).

## Detectors + stringlike errors (§II.B) [paper]
`D_{s,t} = M_{s,t−1} ⊕ M_{s,t}` (Eq 2). Detection event = `D=1`. **Spacelike** error (data error → 2
detectors, same time, diff space); **timelike** (syndrome error → 2 detectors, same space, diff time);
**spacetimelike/hook** (mid-circuit, faulty 2q gate). **Stringlike** error = a chain triggering ≤2
detectors (purely spatial = data-error line in one round; purely **temporal = syndrome-error line over
rounds**; or mixed). A spatial stringlike error of length `⌈(d+1)/2⌉` causes a logical error. Under iid:
`P(stringlike length L) ~ exp(−L)`; under correlated noise it can become **power-law (heavy-tailed)** —
the detrimental regime.

## The two temporal-correlation MODELS (§III.A — the mechanism to implement) [paper]
Correlations are only WITHIN a class. Two structures:
- **Pairwise (two-time):** a correlated error on the same qubit (or pair) at rounds `t1, t2`. Class 0 →
  a two-time depolarizing channel (`ItXt'`,…,`ZtZt'`, each 1/15); Class 1 → two-time `Xt Xt'`; Class 2 →
  two-time 2-qubit depol after the CNOT. `(N choose 2)` rolls per qubit. Pair probability decays
  **polynomially `A q/Δt^n`** (`Δt=|t1−t2|`) or **exponentially `A q/n^{Δt}`**.
- **Streaky (multi-time):** an event maximally MIXES the qubit/pair over a STREAK of length-`t` rounds
  (Class 0: data depolarized each round; Class 1: syndrome 0.5-prob X each round; Class 2: pair 2q-depol
  each CNOT). Streak length decays poly `A q/t^n` or exp. (Middle rounds get the highest rate; the
  marginalized model is made identically inhomogeneous.)
- Parameters: `A` (model), `n` (decay), `q` (characteristic correlated rate ≈1e-3); `A_C0=A_C1=2·A_C2`.

## Sampling method (§III.B — how they OPERATE it) [paper]
**Stim `FlipSimulator`** (dynamic per-timestep Pauli injection). Build an **error mask** `M_{ij}` (i=qubit,
j=timestep). Probability matrix `R_{ik}` (corr error on qubit i at the time-pair k=(t1,t2)) per the decay
model → sample → binary `O_{ik}` → map to errors via a transformation `T_{kj}`: **pairwise** `T_{kj}=1` if
`j∈{t1,t2}`; **streaky** `T_{kj}=1` if `j∈[t1,t2]`. Then `M_{ij}=⊕_k O_{ik}T_{kj}` (Class 1: logical-OR +
a 4/3 rescale, Eq 4). Decode: **MWPM/PyMatching with the SAME marginalized-independent DEM for both** the
correlated and independent syndrome data — i.e. **the decoder is correlation-BLIND** (the misspecification).
Memory experiments are `2d` rounds; 10M shots.

## Marginalization (Appendix A — the FIXED-marginal construction) [paper]
Reparametrize each channel as "maximally MIX with prob `p'`": `E(p',ρ)=(1−p')ρ+p'M[ρ]`, `M∘M=M`, with
`p'=C_E·p`, `C_E = 2 (E1_X), 4/3 (E1_D), 16/15 (E2_D)` (Eq A1–A2). The per-(s,t) marginal:
`1−p'(s,t)=∏_{i<j}(1−Pr(E_{s,i,j})·1{t∈{i,j}})` (pairwise, Eq A6) or `1{t∈[i,j]}` (streaky, Eq A7), and
`p(s,t)=(1/C_E)(1−∏_{i<j}(1−u_{ij}(t)))` (Eq A8). This yields the per-qubit-per-timestep marginal the
INDEPENDENT model is set to match — so correlated vs independent differ ONLY in structure.

## Findings + numbers (§III.C, §IV, Table I) [paper]
- Circuit-level pairwise poly(n=2): `p_L=6.56e-3·e^{-0.827d}` (corr) vs `4.03e-3·e^{-0.820d}` (indep);
  teraquop d=27 both. **Streaky poly(n=2): `9.51e-3·d^{-2.35}` (power-law!) → no teraquop**; indep
  `2.51e-3·e^{-0.595d}`, d=37.
- By class (poly n=2, q=2e-3): **Class 0 streaky robust** (d=36 vs indep 40); **Class 1 streaky
  `5.38e-2·d^{-3.13}` → no teraquop** (d=15: 97× indep); **Class 2 streaky `1.62e-2·d^{-2.07}` → no
  teraquop**. Pairwise variants all keep ~exponential scaling.
- Decay sweep (Class 1/2 streaky): poly needs `n≥2` (ideally `≥3`); `n→∞` (streak≤2 rounds) recovers
  near-exponential. Table I lists all fits/teraquop projections.
- **Autocorrelation `¯p_{t,t'}=(1/N_s)Σ_{s=s'}p_{ij}` (Eq 5):** nonzero to `|t−t'|=8`; Class 2 streaky
  strongest. **But the degree of pairwise detector correlation does NOT track the severity** — pairwise
  correlations can't distinguish a continuous timelike string from disjoint localized errors. Multi-time
  characterization is needed.
- Non-monotonic LER (Appendix B): for q≥2e-3, `p_L(d=11) > p_L(d=13)` etc. — the streaky LER can
  INCREASE with d (no true threshold), while the matched independent model stays monotonic.

## Real-device connection [paper]
Google's "below-threshold" experiment [ref 10, 2408.13687] saw a ~1e-10 logical-error-per-cycle floor on
high-d repetition codes, attributed to rare correlated events; one type — "a single noisy detector event
over thousands of rounds" — IS a multi-time streaky SYNDROME error. So streaky-Class-1 is the canonical
real correlated-error floor.

## Limitations [paper]
- **L1.** Forward simulation with a FIXED, correlation-blind (marginalized) decoder — shows the COST of
  temporal correlations, does not learn/exploit them.
- **L2.** Phenomenological correlation models (pairwise/streaky × poly/exp), not derived from a microscopic
  bath; "flexible but grounded." Only correlations WITHIN a class.
- **L3.** `2d`-round memory experiments (practical cap); rotated XZ surface code (claims extend to XZZX).
- **L4.** Pairwise detector autocorrelation is an insufficient discriminator (their own §IV.C caveat).

## Relevance to the twin — grounds WS2 ⑤b (temporal) [twin]
1. **The mechanism for ⑤b is the streaky/pairwise temporal-correlation model, BY CLASS.** Reuse:
   pairwise (two-time) + streaky (multi-time) Pauli correlations, poly `Aq/Δt^n` / exp `Aq/n^{Δt}` decay,
   on Class 0 (data) / Class 1 (syndrome SPAM) / Class 2 (2q gate). For the d3-XZZX teacher this is a
   per-round mechanism schedule (the within-cycle marshalling already has per-round op slots; the carrier
   `round_pre(eng,r)` can inject a round-correlated Pauli mask). The grounded "interesting" cell =
   **streaky Class 1/2** (detrimental); Class 0 is the benign control.
2. **The METHODOLOGY is exactly the twin's misspecification framing.** "Correlated vs
   marginalized-independent at FIXED marginals, decoded with the marginalized DEM" = "the iid-Pauli
   learner fits the per-(round,stab) marginals but MISSES the temporal correlation". The detrimental
   ΔLER (correlated − independent at matched marginals) is the **misspecification's decode-relevant
   signature** — the WS-framework's `B_misspec` / excess-LER for the temporal axis. Appendix A's `C_E`
   marginalization is how to hold the marginals fixed.
3. **⚠ CORRECTS the WS2 ⑤b observable I had invented.** My WS2 pre-reg said ⑤b → "round-dependent
   `(θ_r,γ_r)` drift + long-lag `RR_CORR`". That is (a) a RATE-drift, not the correlation STRUCTURE, and
   (b) the long-lag `RR_CORR` is exactly the **2-point detector autocorrelation `¯p_{t,t'}` the paper
   PROVES is insufficient** (§IV.C) to distinguish benign vs catastrophic. The correct ⑤b observable is
   **the LER-degradation (slower-than-exp / non-monotonic suppression) under streaky SYNDROME-qubit
   correlations** — the multi-time timelike-string signature, NOT the 2-point round-to-round correlation.
   The honest temporal misspecification observable is decode-relevant (ΔLER), and the 2-point `RR_CORR`
   is a known-insufficient summary (carry this caveat).
4. **Data-vs-syndrome asymmetry is a load-bearing design constraint.** The teacher's temporal
   correlations must be sited on SYNDROME qubits / 2q gates (Class 1/2) to produce a genuine
   misspecification the twin must handle; data-qubit (Class 0) temporal correlations are benign (a null
   control). Our d3 carrier currently models DATA qutrits with idealized ancilla (the carrier
   excludes per-round soft-syndrome / ancilla dynamics — `project-soft-readout-d1`); so faithfully
   siting Class-1/2 temporal correlations needs the ancilla/syndrome-qubit axis the carrier defers ⇒
   a declared scope question for WS2 ⑤b (likely needs the ancilla-resolved carrier or an
   effective syndrome-error injection), NOT a trivial round_pre drift.
5. **Open code (corrqec) is an independent reference** for the FlipSimulator mask construction +
   the marginalization, should we reproduce the LER curves as a cross-check.

## How to use / trust + open questions [twin]
- **Trust:** high (full text; standard Stim+MWPM; numbers in Table I). Carry L4 (autocorrelation
  insufficiency) as a hard caveat on any 2-point temporal-correlation observable.
- **Open for WS2 ⑤b:** (i) site the temporal correlation on syndrome/2q-gate (Class 1/2) — but our
  carrier's idealized ancilla means the SYNDROME-qubit error axis is not natively modeled (the carrier
  injects DATA-qutrit channels); resolve whether ⑤b is done on the carrier (effective syndrome-error
  injection) or deferred until the ancilla-resolved axis. (ii) The observable is decode-relevant
  LER-degradation, validated against a frozen MWPM decoder with the marginalized DEM (NOT the 2-point
  `RR_CORR`). (iii) Distinguish a RATE-drift (the `2511.09491` adaptive-estimation axis) from a
  correlation-STRUCTURE (this paper) — they are different ⑤b sub-axes with different observables.
