# Conjunction ownership + scale-envelope due-diligence — 2026-07-06

**Burden of proof is on the CLAIM of an open niche.** This adjudicates whether the project's target — *a usable QEC
error-record generator doing the CONJUNCTION [leakage + non-Markovian TEMPORAL coupling + shared-latent CROSS-MECHANISM
coupling], together* — is (①) genuinely unowned and (②) deliverable at a usable scale. Method mirrors
`novelty_ownership_adjudication_2026-07-02.md`: per-sub-claim ownership ledger + a **negative-coverage log** + honest
confidence labels. All verdicts **PROVISIONAL** (search is never exhaustive). Provenance: local RAG (精读 corpus) +
4 adversarial "prove-ownership" web searches (2026-07 index) + fetches (Deltakit GitHub, QuEra Tsim, Quiroz abstract);
carrier limits read from source.

## The claim under test
> No existing tool/framework GENERATES QEC error records `{det,obs}` (+ DEM, Stim-interoperable) from the CONJUNCTION
> [leakage (qutrit/non-Pauli) + non-Markovian temporal coupling + shared-latent cross-mechanism coupling], TOGETHER,
> as a usable tool, with each mechanism's generation error bounded vs an independent exact oracle.

## ① Ownership ledger (grounded)

| Sub-claim | Owner(s) found | But — why it does NOT own the target |
|---|---|---|
| non-Markovian **temporal** coupling | **Quiroz 2412.16092** (PRX Q 2026; 39q real IBM; LME+stochastic-Hamiltonian; 0.5% err, 7× vs default) · SPP 2603.05474 · Kam 2410.23779 | Quiroz is a **gate-noise model for RB/DD/VQE expectation values — NOT a QEC syndrome-record generator**, leakage not its focus; SPP **twirls to Pauli**; Kam is a *study* of the effect |
| **shared-latent** cross-mechanism (KEEPS coupling) | **chain-mapping 2407.10140** (keeps shared-bath coupling exactly) · Quiroz (ZZ crosstalk) | chain-mapping is a **bath oracle**, not a record generator, no leakage; time-invariant-PT 2603.06840 explicitly **can't do multi-site coupling** |
| **leakage** (as QEC error) | Darmawan qutrit-MPS 2308.08186 (1D) · Deltakit `SI1000`(`pL`) · Fowler 1308.6642 · PECOS | each does leakage **alone**, not in the conjunction, not latent-driven |
| pair {non-Markov + crosstalk} | Quiroz (strongest) | gate-level, not QEC records |
| pair {shared-bath + non-Markov, coupling kept} | chain-mapping 2407.10140 | bath oracle, not a tool |
| **TRIPLE {leakage + non-Markov + shared-latent} as a QEC-record generator** | **none found** | — |
| **usable TOOL (Stim/DEM interop + oracle bounds)** | **none found** | all owners = research code / characterization models / gate-level / bath-oracles; web: "no unified open-source package combining non-Markovian + leakage + correlated" |

**① VERDICT (PROVISIONAL, moderate confidence): the triple conjunction, packaged as a usable QEC-record generator, is
UNOWNED** — no owner found across the RAG精读 corpus + 4 adversarial web searches + fetches. Every axis and every
*pair* is owned separately; the closest single work (Quiroz) does non-Markov+crosstalk on real hardware but is a
gate-noise model, not a QEC-record generator, and not leakage-in-the-conjunction. ⇒ the contribution is a genuine
**CONJUNCTION + PACKAGING** (usability + interop + oracle-bounds), NOT new physics/territory (as the user framed it).

### Negative-coverage log
Searched (no owner of the triple-as-a-tool found): RAG精读 notes — Quiroz 2412.16092, chain-mapping 2407.10140,
time-invariant-PT 2603.06840, silicon-spin-NM 2507.08713, Giarmatzi 2308.00750, RB-forecasting 2312.06062, SPP
2603.05474, Darmawan 2308.08186, Kam 2410.23779; web (prove-ownership phrasing) ×4; fetches — Deltakit GitHub, QuEra
Tsim, Quiroz abstract. **NOT searched:** patents (beyond one crosstalk-analysis patent glimpsed), vendor
unreleased/internal roadmaps, non-English literature. ~~the full Quiroz PDF (leakage-in-extended-Hilbert-space
unresolved at abstract level — a residual check)~~ **RESOLVED 2026-07-06, full-text close-read — see below.**

### Residual check ① RESOLVED (2026-07-06): full-Quiroz leakage question — NO leakage anywhere in the model
Full-text close-read of arXiv 2412.16092 v1 (Oda, Schultz, Norris, Shehab & Quiroz, "Sparse Non-Markovian Noise
Modeling of Transmon-Based Multi-Qubit Operations"; note
`docs/papers/reading_notes/quiroz_nonmarkovian_crosstalk_2412.16092.md`, cached PDF
`docs/papers/2412.16092_sparse_nonmarkovian_transmon.pdf`):
- **The "extended Hilbert space" is qubits-only** — `H = H_D ⊗ H_Sp ⊗ H_TLS` (data ⊗ spectator qubits ⊗ TLSs), with
  "TLSs are defined on a computational basis {|0⟩_TLS, |1⟩_TLS}" treated "as an effective qubit that couples to the
  main qubit via a static ZZ interaction" (Sec. II, II C, IV B 1). An exhaustive text scan finds **zero** occurrences
  of leakage / qutrit / |2⟩ / anharmonic / higher-level. Temporal correlations are **classical** stochastic variables
  ("System operators couple to stochastic, time-dependent, variables as opposed to additional quantum degrees of
  freedom", Sec. I).
- **No QEC records:** QEC appears only as a background citation; validation = characterization suite / RB / CPMG /
  ECR / 4-qubit DD / 2-qubit VQE. Zero hits for syndrome / detector / surface code / repetition code.
- **No released tool:** no code/data-availability statement, no repo link (one uncited "mezze" mention, App. G).
- ⇒ **Ownership-ledger conclusion UNCHANGED and STRENGTHENED:** Quiroz owns {classical-temporal non-Markov + ZZ
  crosstalk} as a gate-noise characterization model (39q characterized, ≤4q dynamics demos) — it does **not** touch
  the leakage axis at all (not even in-model), does not generate QEC records, and ships no tool. Risk #1 (Quiroz
  extends to leakage + QEC generation) remains a *future-motion* risk only; nothing in the paper is positioned there
  today.

### ① Risks (honest)
1. **Quiroz is the nearest threat and is productizable** — non-Markov+crosstalk, real IBM, oracle-validated, PRX
   Quantum 2026. If it (or IBM/Qiskit) extends to leakage + QEC-record generation, that half of the conjunction is
   occupied. **Time pressure.**
2. **"No owner found" ≠ certainty** — moderate confidence; provisional per burden-of-proof discipline.
3. **The surviving room is narrow:** {leakage-in-the-conjunction + QEC-record-generation + usability + oracle-bounds}.
   Defensible but narrow.

## ② Scale-envelope (grounded from carrier limits — the "usable" gate)

The conjunction's cost = the **leakage-qutrit carrier** cost; the non-Markovian temporal part is a **classical latent**
(`source/process.py`) and the shared-latent fan-out (`source/coupling.py` Θ) are **parameter modulation — free**
(no state-space cost). notion-3 closure justifies the classical-latent temporal model (the record's temporal structure
is classical). So the envelope is set entirely by the leakage carrier:

| scale | leakage carrier | conjunction status |
|---|---|---|
| **d3** (9 data qutrits) | exact SV `3^9 = 19683` fits (**measured 2026-07-06 post-memory-lean-fix: 670,839 shots/min SV kernel at 0.63 GiB; MPS exact-χ ~0.8–1.0 s/shot**); exact qutrit-DM oracle: **full-9q DETECTOR_MARG DEMONSTRATED at 18.92 GiB / 11 s** on the 32 GB card (deliberate `dm_safety` budget; the pre-fix k≈5.2 path would have needed 31.4 GiB — root-caused as apply-path temporaries and fixed the same day, measured k now 3.3; capability declares a conservative 4×copy) + sub-register oracle ms-scale (n=8: 0.3 s, 2.1 GiB) | **USABLE, exact carrier + exact full-register oracle (deliberate budget) + sub-register tiles at the conservative default** |
| **d5** (25 data qutrits) | SV `3^25 = 13.5 TB` DEAD; **MPS bond-truncated** (`mps_forward.py`, `max_bond=χ`, per-stabilizer projection) → thin/approximate, bounded on ≤8-qutrit tiles vs the qutrit-DM oracle | **USABLE (thin/approx, oracle-bounded on tiles)** |
| **d7+** (full) | 1D-MPS bond → 2^{O(d)} wall; **PEPS / boundary-MPS** the known extension (Darmawan 2308.08186's method — ADOPTABLE, not built) | deferred (known path) |

**② VERDICT: PASS with a scoped envelope (numbers now MEASURED — residual ② 2026-07-06,
`residual2_d3_conjunction_cost_prereg.md` OUTCOMES).** The conjunction is **deliverable and USABLE at d3 (exact
carrier, sub-register-exact oracle) and d5 (MPS-truncated, oracle-bounded on tiles)** — exactly the range where
decoders/thresholds are benchmarked. Generation cost is a non-issue (5×10⁴ shots/min). Full-d5+ hits the
leakage-qutrit wall — the **same wall every competitor hits** — and the extension is a *known* method (adopt
Darmawan's PEPS/boundary-MPS). The classical couplings (non-Markov temporal + shared-latent) add **zero** scale cost
(measured: 0.63 ms/round Kraus rebuild, ~1e-3 of a real carrier round), so keeping the *coupling* is free; only the
*leakage level count* sets the wall. One oracle-leg correction stands: exact-DM comparisons run on sub-registers
(n ≤ 8) — full-9q exact-DM record laws await a memory-lean apply path (src fix flagged).

## Overall verdict — CONDITIONAL GREEN
- **① unowned (provisional, moderate confidence)** — the conjunction-as-a-usable-tool is plausibly open.
- **② deliverable at d3–d5** — a genuinely usable tool scope, oracle-bounded, with a known d7+ extension path.
- ⇒ the direction ("a usable tool doing the conjunction") is **evidence-supported**, with three standing caveats:
  Quiroz is close + time-pressured; "unowned" is provisional; the differentiation is a narrow conjunction+packaging
  (not new physics — accepted).

## Next
Turn this into a **one-page product spec + build plan**: the target conjunction, the d3–d5 usable envelope, the
`emit → Stim/DEM` interop, the per-mechanism oracle-bound table (`certify/`), and the reuse map (`source/` +
`coupling/` + `carrier`/`quantum_bath` + `teachers/coupled_cycle` + `gates/` are the pieces — this is unify + package,
not from-scratch). Residual checks before locking: the full-Quiroz leakage question; a small confirmatory d3-conjunction
run (GPU, user go-ahead) to validate the envelope's cost numbers empirically.
