# Deep review — Squires, Wang & Uhler, Permutation-Based Causal Structure Learning with Unknown Intervention Targets (UT-IGSP)

> Deep reading note (academic-paper-review format; full read Secs. 1–3 incl. the causal-DAG
> /I-MEC setup, perfect-vs-imperfect interventions, the I-Markov invariance Eqs. 1–2, the JCI
> framework, the unknown-target identifiability result, and Assumption 1 + its necessity;
> Sec. 4 algorithm + Secs. 5–6 experiments at the result level). **Relevance to the twin**
> centerpiece — the interventional-discovery tool matching the twin's `do()`-like access.

## Metadata
- **Authors.** Chandler Squires, Yuhao Wang, Caroline Uhler (MIT LIDS/IDSS; Statistical Laboratory, Cambridge).
- **Venue / status.** UAI 2020 (PMLR 124); arXiv:1910.09007. Code: `uhlerlab.github.io/causaldag/utigsp`.
- **Domain / type.** Causal structure learning; **methods** (algorithm + consistency theorem) + synthetic & biological (gene-expression) experiments.

## Executive summary
The paper learns a causal **DAG** from a **mix of observational + interventional data when the intervention targets are partially or completely UNKNOWN** — the realistic case (CRISPR knockouts have off-target effects; a twin probe-context perturbs an unknown subset of noise mechanisms). Observational data identifies only the **Markov-equivalence class (MEC)**; interventional data refines this to the smaller **interventional MEC (I-MEC)**. The key invariance (the **I-Markov property**, Eq. 1): for a **non-intervened** node `j`, `f^I(x_j|x_{pa(j)})=f^obs(x_j|x_{pa(j)})` — *the conditionals of untouched variables are invariant across the observational and interventional regimes* (the same invariance ICP exploits), giving the factorization Eq. 2. The framework covers both **perfect** interventions (remove all dependence on causes) and **imperfect** ones (merely *modify* the mechanism — e.g. partial gene inhibition). Targets are estimated as `Î^k={x_i: f^k(x_i|x_S)≠f^obs(x_i|x_S) ∀S}`.

The headline result: under **Assumption 1 (direct I-faithfulness)** — an intervened node `i` must show a conditional difference from observational for *some* conditioning set — **all intervention targets are identifiable**, so **the degree of identifiability with *unknown* targets equals that with *known* targets** (and Example 1 shows Assumption 1 is *necessary*: violate it and the I-MEC may be unidentifiable). The algorithm, **UT-IGSP**, is a greedy **permutation search** minimizing a nonparametric score (handling non-Gaussian/nonlinear data), provably consistent for the I-MEC *and* the targets, and improves on JCI-GSP (which wrongly treats intervention variables like system variables). It is framed within Mooij et al.'s **Joint Causal Inference (JCI)**: add a binary **intervention node `I_k`**, with the JCI-DAG fusing the causal DAG with edges `I_k→x_i` iff `i∈I_k`.

For the twin this is **the interventional structure-discovery tool that matches its access model** — and its single most encouraging result is *unknown-target = known-target identifiability*: the twin's probes are **imperfect interventions on an unknown subset of mechanisms** (no probe surgically isolates one), and UT-IGSP says the mechanism graph (and *which mechanisms each probe touches*, `Î^k`) is recoverable anyway, turning the probe ladder into labeled interventional environments without hand-specifying targets.

## Contributions (claim → evidence → strength)
- **C1. Characterize the I-MEC identifiable from observational+interventional data with unknown targets (Sec. 3).** Via the I-DAG/I-essential graph (Yang 2018). *Strength: strong.*
- **C2. Unknown-target identifiability = known-target, under direct I-faithfulness (Asm. 1); necessity shown (Example 1).** *Strength: strong — the headline.*
- **C3. UT-IGSP: consistent greedy permutation search learning the I-MEC *and* the targets (Sec. 4).** Nonparametric; improves over JCI-GSP. *Strength: strong.*
- **C4. Empirical efficacy on synthetic + biological data (Secs. 5–6).** Works where parametric methods misfire (non-Gaussian/nonlinear). *Strength: moderate-strong.*

## Method (deep)
- **Setup.** DAG `G=([p],E)`, `f(x)=∏f_i(x_i|x_{pa(i)})`; MEC from observational (same skeleton + v-structures); I-MEC from interventional (Hauser–Bühlmann, Yang).
- **I-Markov.** Non-intervened conditionals invariant (Eq. 1); `f^I(x)=∏_{i∉I}f^obs(x_i|x_{pa(i)})∏_{i∈I}f^I(x_i|x_{pa(i)})` (Eq. 2). I-essential graph = partially directed graph for the I-MEC.
- **JCI.** Intervention node `I_k` (binary), `f^joint(x,I)=f^obs(x)^{1_{I=0}}∏_k f^k(x)^{1_{I_k=1}}`; JCI-DAG adds `I_k→x_i` iff `i∈I_k`; background: exogeneity + generic context.
- **Targets.** `Î^k` = nodes whose conditional differs from observational for all `S`; Asm. 1 ⇒ `Î^k=I^k`.
- **Algorithm.** Greedy permutation (sparsest-permutation family) minimizing a CI-test-based score over the JCI structure; consistent for I-MEC + targets.

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | I-MEC characterization + consistency rigorous; Assumption 1 necessity proven (Example 1). |
| Novelty | **4** | First consistent permutation-based unknown-target learner; the "unknown=known identifiability" result is the notable contribution. |
| Reproducibility | **5** | Public code + reproducible experiments; algorithm + score explicit. |
| Experimental design | **4** | Synthetic + biological (gene-expression) data; perfect + imperfect interventions. |
| Statistical rigor | **4** | Consistency under faithfulness; finite-sample rests on the CI tests. |
| Scalability | **3** | Permutation search is combinatorial; greedy heuristics manage moderate `p`. |

## Strengths
- **S1 — unknown-target = known-target identifiability (Asm. 1).** That you lose *nothing* by not knowing the intervention targets (under a checkable faithfulness condition) is a strong, encouraging, and directly applicable result.
- **S2 — handles imperfect interventions.** Real interventions *modify* rather than *remove* mechanisms; covering the imperfect case (not just perfect knockouts) matches physical reality (and the twin's probes).
- **S3 — nonparametric + consistent + public code.** Works on non-Gaussian/nonlinear data with a provably consistent permutation search and a reproducible implementation.

## Weaknesses / limitations
- **W1 — faithfulness (Assumption 1) is necessary and can fail.** Direct I-faithfulness is required; correlated/cancelling effects (coherent cross-talk) can violate it, and then the I-MEC is not identifiable (Example 1).
- **W2 — returns an equivalence class, not point identification.** Output is the I-MEC + targets, not a unique DAG or a quantitative effect — it *feeds* a band, doesn't replace it.
- **W3 — combinatorial search; continuous-CI-test default.** Permutation search scales poorly in `p`; the CI tests assume continuous data (discrete syndromes need adaptation).

## Relevance to the twin
This is **the interventional structure-discovery tool whose access model matches the twin's (action P3)** — and it is the strongest CRL result for the twin's realistic probe structure:
1. **The twin's probes are imperfect interventions on an unknown mechanism subset — exactly UT-IGSP's setting.** No `C_cal(r)` context surgically isolates a single noise mechanism; each perturbs an unknown subset, and basis-rotated probes *modify* (not remove) a mechanism's effect. UT-IGSP is built for precisely this (imperfect + unknown-target), so it is the right discovery tool for the probe ladder.
2. **Unknown-target = known-target identifiability (Asm. 1) is the formal "the ladder still works."** The most important transfer: even though the twin cannot pre-specify which mechanisms each probe touches, the mechanism graph *and* the per-probe targets `Î^k` are recoverable — turning the probe ladder into **labeled interventional environments discovered, not hand-specified**. This underwrites treating the ladder as interventional data of full identifying power.
3. **I-Markov invariance (Eq. 1) = the shared backbone with ICP and the frozen-baseline idea.** "Untouched conditionals are invariant across regimes" is the same invariance Heinze-Deml uses for prediction and the same logic as the twin's *frozen matched baseline across `r`*. UT-IGSP (discover targets/structure), ICP (find LER's causal parents), and Perry's MSS (orient from sparse shifts) are **three faces of one multi-environment principle**; UT-IGSP is the *interventional* face matching `do()`.
4. **`Î^k` = which mechanisms each probe perturbs — a free labeling.** Discovering the per-context targets is operationally valuable: the twin gets, for each probe level, the set of mechanisms it actually moves — the empirical content of "phase-sensitive probes touch the coherent mechanism," without assuming it. This is the discovery counterpart to the *structural* gate (Lachapelle sparsity / Moran anchors) and the *distributional* gate (iVAE auxiliary).
5. **Returns an I-MEC (a quotient), not a point — feeds the band; and Asm. 1 is a named harden risk.** The output is an equivalence class, consistent with the twin's "identifiable up to the alias quotient": UT-IGSP *narrows* the quotient with interventional data, the band quantifies what remains. And Assumption 1 (direct I-faithfulness) is exactly what **coherent cross-talk** (correlated mechanisms) could violate — a pre-registered harden-stage check (does identifiability survive when mechanisms cancel?).

## How to use / trust + open questions
- **Trust:** high as the *interventional-discovery* tool matching the twin's access; carry W1 (faithfulness may fail under cross-talk), W2 (equivalence class, not band), W3 (continuous CI tests — use discrete/polarization tests).
- **Open questions for the project:** (i) Run UT-IGSP on the twin's **probe-ladder data** to discover `Î^k` (which mechanisms each probe touches) and the mechanism I-essential graph — does it recover "phase-sensitive probes → coherent mechanism" without being told? (ii) Use the **unknown=known identifiability** result as the formal justification that the ladder (with undisclosed per-context targets) has full identifying power. (iii) **Stress-test Assumption 1 under correlated/coherent mechanisms** (harden axis) — the I-MEC-collapse failure mode, pre-registered. (iv) Position UT-IGSP/ICP/MSS explicitly as the *interventional / predictive / observational* faces of the one multi-environment lever, all feeding (not replacing) the ΔLER band, all running *after* `recover` in recovered-mechanism space with discrete-appropriate CI tests.
