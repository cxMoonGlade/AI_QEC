# Product spec + build plan — the coupled-error QEC record generator (2026-07-06)

**One line.** A usable tool that GENERATES faithful QEC error records `{det,obs}` + a DEM from the CONJUNCTION
[**leakage** + **non-Markovian temporal** coupling + **shared-latent cross-mechanism** coupling], at **d3–d5**,
**oracle-bounded**, **Stim/DEM-interoperable** — the thing you reach for when Stim's Pauli noise (and even
Deltakit/PECOS/Tsim's phenomenological leakage/coherent models) can't give you that faithful *coupled* record.
Positioning + gates: `conjunction_ownership_duediligence_2026-07-06.md` (① provisional-unowned, ② d3–d5 usable);
`HANDOFF_static_simulator_notion2_2026-07-06.md` §0/§0b. Judged by **faithfulness + adoption**, not novelty.

**Who it's for.** Decoder developers (test robustness to leakage/correlated noise Stim can't make), hardware teams
(validate decoders under their real coupled noise), QEC theorists (thresholds under realistic coupled noise). Anchor
ONE first user/use-case before scaling effort.

## Interface (the contract)
- **Input:** a device-noise spec = per-mechanism rates + a latent-source config (`source/process.py`:
  `OneOverFDrift` / `RTN` / `TemporalStormSPP`) + a coupling map (`source/coupling.py` Θ: one latent → which
  channels).
- **Output:** (a) `{det,obs}` cube (the faithful coupled record, incl. the leakage-induced correlated-detection
  structure Stim-Pauli can't produce); (b) a **DEM** (correlated-Pauli reduction of the record — the decoder-facing
  summary, via `hardware/pij.py::spitz_pij`); (c) a Stim circuit for the Pauli-representable part.
- **Interop:** PyMatching / Deltakit / CUDA-Q decode the `{det,obs}`+DEM directly. The faithful non-Pauli/leakage
  content lives in `{det,obs}`; the DEM is the Stim-compatible hand-off.

## Faithfulness contract (leg (i) = the moat) — the mechanism × oracle × bound × d table (FILL IT)
| mechanism | independent oracle | error bound | usable d |
|---|---|---|---|
| leakage (qutrit) | exact qutrit-DM ≤9q (`carrier/exact/qutrit_dm.py`) | TVD / p_ij on a d3 tile | d3 exact; d5 MPS-thin |
| non-Markov temporal (classical latent) | closed-form autocov / from-scratch MC | analytic (exact) | any d (free) |
| shared-latent Θ fan-out | closed-form cross-mechanism corr | analytic (exact) | any d (free) |
| readout/reset SPAM (MA(1)) | MA(1) closed form (`g6_null_model_rederivation`) | exact | any d |
| coherent (if kept) | QuTiP `mcsolve` / DM | missing full-record bridge | d3 only; record visibility is schedule/instrument dependent, not universally twirled |
- **Rule (`FAITHFULNESS_PROTOCOL.md`): every mechanism DECLARED + BOUNDED vs its oracle before "done"; unbounded = STOP.**

## Reuse map — this is UNIFY + PACKAGE, not from-scratch
- **have:** `source/process.py` (latents) · `source/coupling.py` (Θ shared-latent) · `carrier/` + `quantum_bath/`
  (qutrit leakage forward) · `carrier/exact/qutrit_dm.py` (oracle) · `teachers/coupled_cycle.py` (emit → {det,obs}) ·
  `gates/g4–g7` (validation) · `certify/` (oracle ports) · `hardware/pij.py` (DEM/p_ij).
- **new (the actual work):** (1) the `emit → Stim/DEM` export/interop; (2) the mechanism×oracle×bound table filled +
  automated; (3) the conjunction wired end-to-end at d3 (leakage carrier + latent + Θ, one call); (4) packaging (API,
  docs, one demo); (5) d5-thin via MPS.

## Build plan (phased; each phase has a check)
- **P0 — interop spike (unblocks "usable"):** `emit → Stim circuit / DEM` for a d3 record; decode it with PyMatching.
  Check: a round-trips through the standard stack. **✅ DONE 2026-07-06 — GATE P0_INTEROP_ROUNDTRIP PASS
  (`p0_interop_spike_notes.md`): d3 rep-code arm decodes at z=18 improvement; 6/6 injection wiring checks; honest
  cost ~1.2 s/trajectory-manifest at R=4. Residual ① (Quiroz leakage) also resolved — no leakage in 2412.16092.**
- **P1 — faithfulness table:** fill the mechanism×oracle×bound table for the CURRENT mechanisms at d3 (bounded vs
  qutrit-DM / closed forms). Check: every cell bounded; unbounded ⇒ STOP.
- **P2 — the conjunction @ d3 (core deliverable):** one call = latent (non-Markov) → Θ (shared-latent) → qutrit
  carrier (leakage) → `{det,obs}`+DEM, oracle-bounded. Check: matches the qutrit-DM oracle on a tile to the declared
  bound.
- **P3 — the KILLER DEMO:** a d3 leakage+non-Markov+shared-latent record whose oracle-bounded generation makes a
  decoder (or threshold estimate) behave **differently from the Stim-Pauli prediction**. Check: the difference is real
  + the generation is bounded. *This one artifact is the whole value proposition's evidence.*
- **P4 — scale + package (later):** d5-thin (MPS, bounded on tiles); clean API + docs; anchor one user.

## Success criteria (candidate → contribution) + honest status
1. oracle-bounded engine + the filled faithfulness table ✓ when P1/P2 done;
2. Stim/DEM interop ✓ when P0 done; 3. killer demo ✓ when P3 done; 4. one real user (P4).
**Standing caveats (do not hide):** ① "unowned" is PROVISIONAL (Quiroz is close + productizable — time pressure);
② the usable envelope is d3–d5 (d7+ needs adopting Darmawan's PEPS); it is a conjunction+packaging contribution, not
new physics. **Residual checks before P2:** full-Quiroz leakage question; a small confirmatory d3 GPU run to validate
the ② cost numbers (needs GPU go-ahead, no-concurrent discipline).

## Immediate first move
**P0 (interop spike) + the residual d3 confirmatory run** — both cheap, both de-risk the two things that matter most
(is it adoptable? does the envelope hold?). Then P1→P3 toward the killer demo.
