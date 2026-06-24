# Space-TIME leakage decodable-headroom — effect-size estimate (faithfulness-first DESIGN draft)

**Status: DESIGN ONLY — for review BEFORE any code (prevent-toy rule, `feedback-prevent-toy-from-the-start`).**
No build (and no Phase-1b carrier extension, see §7) until this is reviewed + the effect-size bar (§4)
is shown plausibly met. Supersedes the terminal-soft direction (D1–D2 = TOY, review 2026-06-22) and the
earlier time-only draft of this doc.

> **ANALYTIC-GATE RESULT (2026-06-22, `outputs/teacher_prereg/xround_analytic_gate.py`):
> the bar FAILS over the deployed frontier → the sim is NOT warranted as scoped.** Miao-anchored,
> normalization-independent read-off: the correlated-excess fraction (the part a cluster-aware decoder
> recovers over a pairwise-`pij` corrMatch) is **0 with deployed DQLR/LRU** — Miao MEASURED that DQLR
> decorrelates leakage to Pauli-like (Fig 5c: `1/Λ` LINEAR in `P_L`, at d3 AND d5/d7-sim). So the
> space-time leakage headroom is **OWNED by the deployed DQLR + corrMatch frontier**; it is non-zero +
> R-growing **only WITHOUT / with PARTIAL** hardware leakage removal. (The gate's absolute % numbers are
> unreliable — a normalization bug — and are NOT used; the verdict rests only on the correlated-excess
> fraction → 0 with DQLR, a direct Miao read-off. Fix the normalization only IF the non-DQLR target is
> chosen.) ⇒ STRATEGIC fork (do not build until resolved): the unowned contribution is likely NOT in
> leakage-decoding-over-the-frontier.

**The redirect (user, 2026-06-22):** leakage's dominant *decodable* signature is the **space-TIME
correlated cluster** — BOTH (i) **time:** a leaked `|2⟩` persists (~4.4-cycle lifetime, Miao) and ruins
subsequent rounds on that qubit → cross-round `p̄_{t,t'>1}`; AND (ii) **space:** a leaked qubit, via the
diabatic CZ, **transports leakage to neighbours (Miao `|30⟩↔|12⟩` ~18–19%, `|31⟩↔|22⟩` ~58–61%) and
imprints a ~0.65π phase on them** — spreading "like a virus." Together they are the **high-decomposed-
weight, space-time-correlated** event a standard *local* matcher (nearest-neighbour-in-space,
consecutive-in-time edges) structurally cannot represent — the genuine non-Pauli signal.

**Carrier reality (verified from source, `mechanisms/qutrit_teachers.py`):** the carrier models **TIME
only** — per-data-qutrit **single-qubit** WG leakage (`|1⟩↔|2⟩` + seepage) that persists across rounds.
The **SPACE channel is NOT built**: `QutritLeakageTeacher.edge_field = None`, `"edge_present": False`,
`"transport_deferred": True` ("coherent transport is the deferred **Phase-1b** extension, registration
§2.4"); and the ancilla is idealized into a parity-POVM (no explicit CZ where transport/phase could
occur). ⇒ the space channel can only be estimated **from scratch** here; building it faithfully is the
Phase-1b prerequisite (§7).

---

## 0. The real question

Is there **leakage-specific decodable logical headroom** in the full **space-time** correlated
structure that the **strongest DEPLOYED decoder** (LRU removal + a space-time-correlation-aware Pauli
decoder, e.g. corrMatch on the `pij`) does NOT capture — large enough, and growing with the
correlation scale (R for time, footprint for space), to justify **building** the Phase-1b transport
carrier + a joint space-time decoder?

**Method (effect-size first, no full build):** estimate the headroom `= LER_deployed − F_optimal`. The
optimal floor `F` (using ALL space-time leakage info) is the ceiling: `LER_deployed ≈ F` ⇒ owned;
`LER_deployed ≫ F` and growing ⇒ a better (space-time-aware) decoder exists ⇒ worth the Phase-1b build.

## 1. Real vs owned (both channels; both on the table)

- **Time (real, carrier-modeled):** persistence → `p̄_{t,t'>1}`; builds with R. ⑦'s "capped" was R≤5
  (`p7b` §2) on sub-registers — small-R, untested at large R (memory: "the gap lives at large R").
- **Space (real, NOT carrier-modeled — the more distinctive signal):** CZ transport + 0.65π neighbour
  phase → spatially-correlated **high-decomposed-weight** clusters. Miao: this is *why* leakage is
  "uniquely dangerous" and *worst for MWPM* — precisely what pairwise-`pij`/local matching cannot
  represent. So the unowned headroom is plausibly **larger in space than in time**; a time-only
  estimate UNDER-states it.
- **Owned (forces a strong baseline — anti-strawman):** LRU/DQLR removes leakage every round →
  suppresses BOTH persistence and spread (steady-state ~1e-3 w/ LRU vs ~5% w/o); corrMatch's `pij`
  captures **pairwise** space-time correlations. ⇒ the unowned residual = the **higher-order**
  (3-body+, non-Pauli) space-time leakage correlations surviving LRU + a pairwise-`pij` decoder. The
  baseline MUST include both LRU and the space-time-`pij` corrMatch.

## 2. The from-scratch model + arms

A **from-scratch minimal d3 surface code** (the carrier lacks space, so space must be modeled here;
reuse L4's `outputs/soft_readout_review/` d3 stim+MWPM scaffolding where sound), with the full
space-time leakage footprint, grounded in Miao (every rate cited; device-specific ⇒ bracketed):
- **leakage generation** ~5e-3/cycle; **persistence** ~4.4-cycle lifetime (time);
- **CZ transport** per CZ-layer (`|30⟩↔|12⟩` ~18–19%, `|31⟩↔|22⟩` ~58–61% — **bracketed**, Sycamore-CZ-
  specific) + the **0.65π neighbour phase** (space) → spatially-correlated clusters.
- **arms (same data, frozen decoders):**
  - `F_optimal` — the optimal (Bayes/MLD) decoder using the full space-time structure (the ceiling).
  - `LER_deployed` — space-time-`pij` corrMatch (the deployed pairwise decoder) + an LRU/DQLR arm.
  - (control) leak-0 → headroom → 0; transport-off → only the time channel remains (isolates space).

## 3. Metrics

- `headroom(R, footprint) = LER_deployed − F_optimal`.
- **Two signatures (the discriminating tests, not an absolute number — A1 lesson):** does it **grow
  with R** (time channel) AND **grow with the leaked-qubit footprint / CZ-neighbour count** (space
  channel)? A genuine space-time leakage effect grows in both; a per-round/local effect is flat.
- **LRU test:** headroom with-LRU vs without-LRU (does LRU own it).
- `%ΔLER` (Sivak) for magnitude; report time-only vs space-only vs joint (transport-off control).

## 4. The bar (decision rule, class (c) gate)

**Build the Phase-1b transport carrier + a joint space-time decoder IFF** the headroom grows with R
AND with footprint, reaches **≳0.5–1% %ΔLER** at the realistic scale, AND survives the deployed-LRU
baseline (or is meaningful in the realistic *partial*-LRU regime). Otherwise (flat / small / killed by
LRU) ⇒ the leakage axis is **owned/capped** ⇒ pivot. Report the space-only and time-only contributions
separately (the transport-off control) so we know which channel (if any) carries it.

## 5. Faithfulness bar (fixed BEFORE code)

- **Independent ground truth:** `F` from an independent optimal/MLD computation; `LER_deployed` from
  frozen corrMatch (`stim`+`pymatching`, external) on held-out shots. No circular check.
- **Isolate leakage-specific + higher-order:** headroom over the best **pairwise-`pij`** space-time
  decoder ⇒ it is the **higher-order / non-Pauli** residual by construction; + leak-0 + transport-off
  controls.
- **Anti-strawman baseline:** deployed = space-time-`pij` corrMatch + LRU (NOT plain MWPM, NOT ⑦'s weak
  rate-matched foil).
- **Space grounding bracketed (device-specific):** Miao's transport (18–61%) + 0.65π phase are
  Sycamore-CZ-specific ⇒ **swept as a bracket**, never pinned; report the headroom as a band over the
  transport/phase bracket (the §2.2-style discipline — don't let a pinned transport rate hand the answer).
- **Declared + bounded simplifications:** the from-scratch model is phenomenological (declare every
  reduction + bound it — e.g. is the transport a classical level-mixing map or coherent? the LRU model;
  the `pij` order); the floor's precision; the R + footprint grids.
- **Carrier cross-check:** the existing certified carrier gives the **time-only** floor-gap as an
  independent, certified cross-check / lower bound on the time channel.

## 6. Execution (single controlled job — GPU-serial, monitored)

- **ONE committed script** under `outputs/`, single (GPU-serial) job, **monitored**; NOT a fan-out.
- First an **analytic gate** (do the R-growth + footprint-growth + magnitude even clear the bar in
  principle?), then the single sim at the declared precision.
- Re-confirm ⑦'s exact R-grid (≤5) + its rate-matched (not space-time-`pij`) foil at the start.
- Scripted-execution (asserts + printed evidence + flushed + `__main__` guard).

## 7. What this is / is NOT — and the Phase-1b prerequisite

- This is an **effect-size estimate**, from scratch, to decide whether to BUILD. It is NOT the build.
- The **space channel needs the Phase-1b two-qutrit transport carrier extension** (the registered,
  deferred §2.4 piece) to be tested *faithfully on the certified carrier* — that build is **gated on
  this estimate** (don't build it before the estimate says the headroom is there). The from-scratch
  model here is the cheap pre-check, explicitly phenomenological + bracketed, NOT the faithful carrier.
- NOT soft-readout (HARD binary syndromes). NOT a new certified carrier yet. NOT a fan-out.

## 8. Epistemic status

`F`/floor-gap = (a) estimator + band; the two growth signatures + the deployed comparison = measured;
the transport/phase grounding = **bracketed** (device-specific, swept); the "build-iff" bar = (c) gate;
the prediction (real vs owned, which channel) = (b) band — a miss (owned-by-LRU) is the important
finding. From-scratch model = explicitly phenomenological, declared + bounded; the faithful test is the
gated Phase-1b carrier. d3; any d5/d7 PROVISIONAL.
