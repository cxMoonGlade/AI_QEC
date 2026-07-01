# Critical review — coupled-teacher architecture synthesis after 精读 + n=2 pilot

**Date:** 2026-07-01  
**Target:** `docs/twin_validation/coupled_teacher_architecture_synthesis.md`  
**Mode:** read-only architecture / claim-boundary review. This document does not authorize
`src/qec_twin/**` changes.

## Executive verdict

The architecture should continue, but `coupled_teacher_architecture_synthesis.md` is not yet a
safe build contract or novelty contract.

The direction is scientifically plausible and now much better grounded: the coupled-Lindblad
pseudomode carrier is real, the matrix-valued shared-bath construction is published, and the n=2
prototype is a meaningful first certification of the embedding + closed-form oracle methodology.
But the synthesis still carries old overbroad claims from before the five-paper 精读 pass, and the
n=2 result must not be extrapolated into a validated correlated cross-qubit teacher.

The correct status is:

> Strong candidate architecture, currently entering a staged falsification program.

Not:

> Architecture proven feasible at QEC scale.

## Evidence reviewed

- `docs/twin_validation/coupled_teacher_architecture_synthesis.md`
- `docs/twin_validation/coupled_pseudomode_pilot_prereg.md`
- `docs/twin_validation/coupled_pseudomode_pilot_v1_results.md`
- `docs/papers/reading_notes/coupled_lindblad_pseudomode_2506.10308.md`
- `docs/papers/reading_notes/markovian_embeddings_nonmarkovian_2602.21430.md`
- `docs/papers/reading_notes/markovian_embedding_correlated_noise_2509.19685.md`
- `docs/papers/reading_notes/tn_decoders_process_tensor_nonmarkovian_2412.13739.md`
- `docs/papers/reading_notes/exact_threshold_correlated_surface_code_2510.24181.md`
- `docs/papers/reading_notes/ace_process_tensor_toolkit_2405.19319.md`
- `docs/papers/reading_notes/tepepo_2d_open_system_tn_2512.01781.md`
- `docs/papers/reading_notes/t_tedopa_crossed_baths_2606.30569.md`
- `docs/twin_validation/coupled_teacher_rate_and_observable_grounding.md`
- `CONTEXT.md`

## Findings

### 1. High — novelty contract is internally inconsistent

The synthesis still contains two incompatible contribution stories.

Older section:

- `coupled_teacher_architecture_synthesis.md:53-73` says the contribution is the composition
  "pseudomodes-on-2D-iPEPO, oracle-validated" because no single paper has it.

Later section:

- `coupled_teacher_architecture_synthesis.md:85-135` correctly says the core method is published,
  and the contribution narrows to QEC application, independent-oracle certification, PT-vs-Markov
  decode-relevant `ΔLER`, full-2D composition, real-device BCF grounding, and the non-Markovian
  coherence-revival wedge.

**Why this matters:** a reviewer will treat the old section as overclaiming the published
coupled-Lindblad pseudomode method. The synthesis should explicitly mark the earlier
"composition is novel" section as pre-update / superseded, or rewrite it into a historical
motivation.

**Required correction before this doc becomes a contract:** contribution = QEC application +
oracle-certified adaptation + decoder/observable evaluation + 2D composition stress test. The
pseudomode shared-bath method itself is cited infrastructure, not the invention.

### 2. High — `1/f/TLS = Lorentzian bank = bounded/exact` is too strong

The synthesis says a finite Lorentzian pseudomode bank is both physically faithful and in the
bounded regime. This is only conditionally true.

The reading notes support a narrower statement:

- `coupled_lindblad_pseudomode_2506.10308.md:273-293`: Gaussian bath, linear coupling, BCF
  analyticity, factorized initial state, and Eq. 7 feasibility are assumptions.
- `coupled_lindblad_pseudomode_2506.10308.md:378-412`: Gaussian-only, conditional polylog scaling,
  SDP feasibility not guaranteed, Fock truncation practical, SDP scalability finite.
- `gle_memory_kernel_learning_apriori_2402.11705.md:147-173`: a-priori bounds cover
  exponentially decaying kernels; true power-law / hard 1/f long memory voids the bound.
- `gle_memory_kernel_learning_apriori_2402.11705.md:224-247`: Lorentzian/TLS exponential-envelope
  memory can be bounded; hard 1/f tail must be downgraded to empirical fit or bracketed tail.

**Why this matters:** if the build claims hard 1/f or strongly coupled non-Gaussian TLS as
theorem-grade, the architecture overstates its physics. The correct claim is:

- finite Lorentzian / Gaussian BCF approximation: bounded if the fit residual and Fock truncation
  are measured and the assumptions hold;
- hard 1/f tail: empirical / bracketed, not theorem-bounded;
- strongly coupled non-Gaussian single TLS: out of the coupled-Lindblad Gaussian scope unless handled
  by an explicitly different oracle/model.

### 3. High — the n=2 pilot is valuable but narrow

The n=2 result is a real success, but it certifies a narrower object than the architecture needs.

`coupled_pseudomode_pilot_v1_results.md:52-66` states the right boundary:

- PASS certifies the single-shared-mode `N=1` CPTP pseudomode embedding of collective pure dephasing
  and the independent closed-form oracle methodology;
- it is not a validated correlated cross-qubit non-Markovian shared-bath teacher;
- the `|01><10|` decoherence-free subspace protection is a `Δs=0` tautology of the collective
  operator;
- the real load-bearing pieces are deferred to n=3-4: matrix-valued BCF off-diagonals, SDP/Loewner
  fit, ACE second oracle, and amplitude-damping/RWA-cost arm.

**Why this matters:** the synthesis must absorb this result as "methodology smoke test passed," not
as "shared-bath cross-qubit teacher validated."

**Required next gate:** n=3-4 partial-correlation matrix BCF with off-diagonal `C_ij(t)` and
`Δs != 0`, plus SDP/Loewner and ACE.

### 4. High — iPEPO composition remains a central feasibility risk

tePEPO is a strong 2D Markovian open-system carrier candidate, but it does not solve the
non-Markovian part by itself.

Relevant reading-note boundaries:

- `tepepo_2d_open_system_tn_2512.01781.md:77-84`: Markovian/Lindblad only; simple-update truncation
  is uncontrolled; no certified error bound off exact lines.
- `tepepo_2d_open_system_tn_2512.01781.md:86-98`: non-Markovianity requires explicit bath/pseudomode
  sites or a new influence-functional layer; added bath sites increase local and bond dimension; `ξ
  >= 2` is already marginal.

**Why this matters:** "pseudomode-on-2D-iPEPO" is the right composition to test, but not yet
de-risked. The synthesis should not imply d=7/d=9 feasibility before the bath-site composition is
tested.

**Required next gate:** pure iPEPO Markovian baseline first, then one-pseudomode-site augmentation,
then convergence under increasing bond dimension / CTMRG or full-update fallback.

### 5. Medium — observable ledger conflates coherence diagnostics with strict decoder metrics

The synthesis correctly moves away from raw syndrome correlation, but it risks bundling multiple
different objects into one "coherence-sensitive `ΔLER`" story.

The PT-aware decoder note says:

- `tn_decoders_process_tensor_nonmarkovian_2412.13739.md:176-188`: the paper does not compare
  PT-aware decoding against MWPM / Markov decoding; that head-to-head `ΔLER` is our gap.
- `tn_decoders_process_tensor_nonmarkovian_2412.13739.md:229-234`: HS metric is coherence-blind; CD
  sees coherence but is not a strict probability; diamond distance is mentioned but not run.
- `tn_decoders_process_tensor_nonmarkovian_2412.13739.md:282-299`: `ΔLER` should compare a Markov
  decoder and PT-aware decoder on the same process, not compare two different noise processes.

The rate/observable grounding also says:

- `coupled_teacher_rate_and_observable_grounding.md:76-91`: record-level gate should be
  decode-relevant `ΔLER`, not two-point cross-cycle detector correlation; coherence revival is a
  source-layer object, excluded from record-level gating.

**Required correction:** split the ledger:

1. source-layer: BCF reproduction, RHP/BLP, coherence revival, CP-divisibility breaking;
2. process/channel layer: process tensor / diamond / CD diagnostic, with caveats;
3. decoder layer: strict LER and `ΔLER = LER_MarkovDecoder(on same process) - LER_PTDecoder(on same process)`.

### 6. Medium — independent oracle layer is strong but operationally not automatic

ACE, chain-mapping, and T-TEDOPA are valid small-system oracle candidates, but each has a sharp scope.

ACE:

- `ace_process_tensor_toolkit_2405.19319.md:191-217`: strong few-qubit shared/collective-bath oracle,
  not a carrier; dense system register limits code-scale use.

T-TEDOPA / crossed baths:

- `t_tedopa_crossed_baths_2606.30569.md:189-215`: good small-patch oracle for correlated dephasing from
  shared Gaussian bath; not a full 2D surface-code carrier; general multi-site correlations may require
  multiple chains and have no a-priori bound.

Chain mapping:

- `chain_mapping_block_lanczos_shared_bath_2407.10140.md:188-195`: quasi-exact few-qubit oracle in a
  constrained shared-bath regime; not scalable QEC carrier; QEC circuit wrapper is extra work.

**Required correction:** the n=3-4 plan should treat ACE / T-TEDOPA / chain-mapping as separate install,
reproduction, convergence, and agreement gates. They are not just named references.

### 7. Medium — spatial-Markovian baseline is now stronger than the synthesis fully exploits

The exact correlated-threshold note gives a theorem-grade baseline for the spatial-Markovian part:

- `exact_threshold_correlated_surface_code_2510.24181.md:267-324`: closed-form `pbar_2 =
  2(1-p_2)p_2` is a Rule-I anchor; threshold gap quantifies how much spatial-Markovian correlation is
  already owned / removable.
- `exact_threshold_correlated_surface_code_2510.24181.md:329-369`: limitation is static, spatial,
  Pauli-Z, no temporal/non-Markovian/coherence.

**Why this matters:** the contribution must be tested against this baseline, not just against iid noise.
If the non-Markovian wedge does not beat or qualitatively differ from this baseline in the declared
decoder metric, the result is still useful but should be reported as source-layer physics, not a decoder
headline.

## n=2 v1 evidence ledger

### Certified by n=2 v1

- Single Lorentzian BCF read-off reproduces target BCF to machine precision.
- Enlarged qubits+pseudomode GKSL evolution preserves CPTP numerically.
- Closed-form independent-boson oracle matches the `|00><11|` coherence wedge.
- DFS `|01><10|` behavior matches the collective-operator prediction.
- Negative control with wrong `g` fails loudly.
- Lamb-phase correction in single-qubit reduced coherence is nontrivial and correctly caught.

### Not certified by n=2 v1

- Matrix-valued BCF with partial cross-qubit correlations.
- SDP/Loewner polylog mode-count claim.
- ACE / path-integral oracle agreement.
- Non-commuting gates under shared bath.
- Amplitude-damping / JC coupling.
- RWA-breaking `n_max` cost in the regime where excitation preservation fails.
- QEC multi-round records.
- PT-vs-Markov decode-relevant `ΔLER`.
- 2D iPEPO + pseudomode composition.

## Recommended revised gates

### Gate A — n=3-4 matrix-valued pure dephasing

**Purpose:** move beyond collective rank-1 tautology.

Required:

- matrix-valued target `C_ij(t)` with nontrivial off-diagonal partial correlations;
- Loewner/SDP fit to `{H, Gamma, g}`;
- BCF residual ledger;
- closed-form multi-qubit independent-boson oracle;
- negative controls: wrong off-diagonal sign / decorrelated `g` / rank-1 collapse.

Pass only if partial-correlation coherences match the oracle and the DFS behavior is not the only signal.

### Gate B — ACE second oracle

**Purpose:** avoid circularity once leaving exactly solvable pure dephasing.

Required:

- ACE installed/reproduced on a minimal shared-bath config;
- convergence in timestep and PT-MPO threshold;
- agreement with the closed-form oracle on a pure-dephasing case before ACE is trusted for harder cases;
- documented failure modes if trace drift or compression instability appears.

### Gate C — amplitude damping / JC arm

**Purpose:** test the real RWA-breaking and Fock-truncation cost.

Required:

- collective or partially collective relaxation bath;
- non-commuting QEC-like pulse/gate insertion;
- `n_max` convergence curve;
- ACE or chain-mapping oracle;
- report whether `n_max <= 10` is actually stable.

This is the gate that decides whether the QEC application is tractable, not n=2 pure dephasing.

### Gate D — decoder/observable arm

**Purpose:** define the QEC-facing value.

Required:

- same process tensor / same emitted process;
- Markov/MWPM or frozen DEM decoder baseline;
- PT-aware decoder;
- strict LER and `ΔLER`;
- separate coherence/channel diagnostics, not substituted for LER.

### Gate E — 2D carrier composition

**Purpose:** test scale substrate, not just physics.

Required:

- pure iPEPO Markovian baseline certified first;
- add one pseudomode site / memory site;
- sweep bond dimension and local Fock truncation;
- compare small windows against Gate B/C oracles;
- if simple update fails, explicitly branch to full update / CTMRG / alternative carrier.

## Architecture decision

Proceed, but with narrowed claims.

Approved claim:

> We are adapting published coupled-Lindblad pseudomode shared-bath machinery to a QEC controlled
> teacher, and we will certify it with independent few-qubit oracles before any code-scale carrier
> claim.

Not approved yet:

> We have a validated correlated non-Markovian cross-qubit QEC teacher.

Not approved yet:

> Full-2D pseudomode+iPEPO is feasible at d=7/d=9.

Not approved yet:

> Hard 1/f / non-Gaussian TLS is theorem-bounded by the current Gaussian pseudomode construction.

## Suggested edits to the synthesis later

No edits were made in this review pass, but when editing is allowed:

1. Add a "Superseded by recent-literature update" marker before the old `no single paper has it`
   section.
2. Replace hard `1/f/TLS exact regime` wording with `finite Lorentzian / Gaussian BCF fit, with
   residual + tail bracket`.
3. Insert the n=2 scope box from `coupled_pseudomode_pilot_v1_results.md:52-66`.
4. Add a dedicated "Gate ladder" section using Gate A-E above.
5. Split metrics into source-layer, channel/process-layer, and decoder-layer.
6. State that ACE / T-TEDOPA / chain mapping are few-qubit oracles requiring their own convergence
   evidence.

## Bottom line

The synthesis has the right scientific spine. The risky parts are not fatal; they are exactly the
right things to test next. But the document should stop reading like a solved architecture and start
reading like a falsification-ready architecture contract.
