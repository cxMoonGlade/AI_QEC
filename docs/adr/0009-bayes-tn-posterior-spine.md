# ADR 0009: Bayes-TN Posterior Spine, Residual Discovery, And Stitching

## Status

Accepted (2026-06-18) for the downstream inference/decoder program. Implementation pending.

## Simulator-product boundary amendment (2026-07-14)

ADR 0009 is **not** an `error_coupling_simulator` product decision. Bayesian posterior modeling,
decoder selection, Bayes decoding floors, and decoder-headroom analysis consume simulator records;
they do not define or certify the forward simulator. Their retained implementations stay under
`legacy/` or downstream projects and are excluded from the simulator wheel. The historical design
discussion below remains the decision record for that downstream program and must not be used to
add inference or Bayes-floor services to the simulator package.

This ADR fixes the model-architecture contract after the Bayes tensor-network
literature review in `docs/papers/reading_notes/`: the main scientific object is a
Bayesian posterior computed by an exact-window or tensor-network likelihood engine.
Walsh-Fourier, temporal Laplace/Z features, and GNNs are allowed only as residual
discovery, proposal, stitching, or amortization layers unless a later ADR promotes
them into a declared likelihood family with its own scoring rule.

## Context

The project needs a surface-code architecture that can be compared to canonical
Bayes-TN decoders and logical-channel TNs (Bravyi-Suchara-Vargo,
Darmawan-Poulin, qecsim MPS/RMPS where the data interface is compatible),
differentiable DEM-likelihood baselines such as dMLE, and AlphaQubit-style
decoders without giving up the twin contract: recover, understand, manipulate,
and predict over a declared observation law with honest uncertainty and alias
bands. The current pressure point is not "pairwise edges versus hyperedges" in
isolation. The pressure point is which object owns the posterior.

The local Bayes-TN reading notes separate two posterior levels:

```text
P(theta | syndrome history)
P(logical class or logical channel | syndrome, theta)
```

The resulting posterior predictive object is:

```text
P(logical | s, data)
  = integral P(logical | s, theta) P(theta | data) dtheta
```

or the analogous posterior over logical channels. This is a model object, not a
preset probability table. DEM edges, `p_ij`, SI1000-style priors, and hypergraph
exports may be useful interfaces or baselines, but they do not define the model
spine.

ADR 0008 already constrains the scalable carrier. C1, the conditionally
admissible shortlist, is DEM/HMM bulk plus window-exact CPTP coherent
corrections. This ADR does not upgrade dMLE into the canonical TN baseline:
dMLE is a differentiable DEM-likelihood / published-bar comparator and may be a
DEM bulk engineering reference where its own data interface is valid, but the
classic Bayes-TN baseline lineage is the BSV/Darmawan/qecsim MPS or
logical-channel decoder family. ADR 0008 also binds the hardware claim boundary:
on the released memory-only surface-code contexts, bulk coherent and non-unital
structure is aliased to its Pauli twirl, with only thin exceptions. Hardware
edge claims are therefore twirled hyperedge/rate claims unless a
controlled-teacher or later richer context earns more.

## Decision

Adopt a three-layer architecture:

```text
Layer 1: Bayes-TN / exact-window posterior = the model
Layer 2: Walsh-Fourier + temporal Laplace/Z residuals = the microscope
Layer 3: GNN / state-space stitching = the composer, not the proof
```

### 1. Layer 1: posterior spine

Layer 1 owns the likelihood and posterior.

For d=3 surface-code work, use dense exact-window or composite exact-window
likelihood where feasible. The object is an observation likelihood and posterior
over a declared channel/noise field, not a hand-set BP-OSD or SI1000 prior.

For d=5/d=7 work, use the ADR 0008 C1 direction: scalable TN/DEM/HMM bulk as
the log-domain engine, plus trigger-gated exact-window CPTP corrections where
the claim is identifiable and feasible. Canonical TN comparator status belongs
to the BSV/Darmawan/qecsim MPS/logical-channel line when the data interface is
valid. dMLE-style DEM likelihood is a separate published-bar comparator and
engineering reference, not the canonical TN baseline and not by itself the
non-Pauli carrier.

Layer 1 must expose:

- parameter posterior or calibrated set over `theta`;
- posterior predictive `P(y | data)` and, where relevant,
  `P(logical | syndrome, data)`;
- held-out syndrome NLL on declared identical splits;
- uncertainty summaries: Fisher/Godambe when point-estimate asymptotics are used,
  posterior credible summaries when Bayesian sampling is used, and alias bands
  when observational identifiability is not earned;
- decoder-facing export only as a secondary product: DEM priors, hypergraph
  priors, or correction reranking artifacts are lossy exports from the posterior
  model.

The posterior and the alias band are distinct. A Bayesian posterior is
prior-dependent; the alias band is the claim-boundary object over observationally
indistinguishable or near-indistinguishable mechanisms. Posterior concentration
inside a tied parameterization does not erase the alias quotient.

### 2. Layer 2: residual discovery

Layer 2 is diagnostic and proposal-generating. It does not replace Layer 1's
likelihood.

Use Walsh/parity-character coefficients on binary syndrome data to find residual
structure after the declared Layer-1 bulk has been fitted. Low-order coefficients
connect to the ledgered `p_ij`/Spitz sector; irreducible connected coefficients
of order three or higher are high-order residual candidates. Significant
coefficients may propose a promotion into Layer 1's declared family, but until
promoted they are model-class misspecification evidence, not hidden likelihood
terms.

Use temporal Laplace/Z or equivalent state-space summaries for multi-lag decay,
bursting, drift, and hidden-timescale proposals. The ADR 0008 discriminator is
the multi-lag `R_k` curve: mechanism attribution must be earned by the lag
structure and controls, not assumed from a single spectrum or burst score.

Layer 2 outputs:

- residual spectrum and connected-cumulant summaries;
- candidate edges, hyperedges, latent temporal modes, or seam residuals to be
  tested by Layer 1;
- negative controls and FDR/uncertainty summaries;
- residual-reduction accounting after a proposed family member is promoted and
  the Layer-1 likelihood is refit.

### 3. Layer 3: stitching and amortization

Layer 3 composes local posteriors across windows and time. It may use a GNN,
state-space model, or neural proposal mechanism, but it is not the source of
truth for the scientific claim.

Allowed inputs:

- window posterior summaries from Layer 1;
- covariance, nullspace, alias-band, and abstain summaries;
- Layer-2 residual features with provenance;
- overlap edges, circuit-operation edges, time adjacency, and dataset metadata
  that are learner-visible under the isolation contract.

Allowed outputs:

- stitched global field or posterior summary;
- uncertainty and abstain flags;
- proposals for Layer-1 family promotion or retile/rewindow decisions;
- amortized proposals for Bayesian inference.

Forbidden use: treating a GNN-discovered field as proof of a real hardware
mechanism without held-out likelihood, residual-reduction, ablation, null-control,
and alias-band evidence.

## Scoring And Acceptance

Every quantitative claim follows `docs/METRICS.md`; no toy/proxy metric may be
silently substituted for a ledgered metric.

Required primary scores for model quality:

- held-out per-shot syndrome NLL on predeclared identical splits;
- posterior predictive calibration and finite-sample uncertainty coverage where
  posterior intervals are claimed;
- Bayes-optimal or MAP syndrome-decoding LER floor where exact or bounded;
- `%Delta LER` under a frozen named decoder when exporting DEM/hypergraph priors
  or correction rerankers.

Required residual scores:

- Walsh/parity-character residual spectrum with connected cumulants for
  higher-order structure;
- multi-lag temporal statistics, including `R_k`, for bunching/drift claims;
- residual reduction after any promoted family member is refit inside Layer 1.

Required comparator arms, when available for the same dataset/split:

- SI1000 / naive calibration prior as a baseline or initialization prior, not as
  the model;
- `p_ij` / correlation prior;
- canonical TN decoder / posterior baseline from the BSV-Darmawan-qecsim line
  when its native syndrome/logical interface is proven compatible;
- dMLE-style DEM-likelihood baseline at its own declared recommended settings,
  reported as differentiable DEM likelihood, not as the canonical TN baseline;
- AlphaQubit-style learned decoder comparator for held-out logical accuracy or
  LER, with source/version/settings declared.

## Non-Decisions

This ADR does not choose a pairwise-only or full-hyperedge parameterization as
the final Layer-1 family. Pairwise and hyperedge objects are possible exports,
priors, diagnostics, or promoted family members. The model selection question is
whether a declared posterior family improves held-out NLL, decoder utility, and
residual structure under the same scoring rule.

This ADR does not claim hardware coherent/non-Pauli recovery from the released
Google memory-only surface-code contexts. ADR 0008's K2-T1 boundary remains
binding: bulk coherent and non-unital hardware claims are twirled/aliased unless
future contexts or controlled teachers earn them.

This ADR does not replace canonical TN baselines (BSV/Darmawan/qecsim where
compatible), AlphaQubit, BP-OSD, PyMatching, dMLE-style DEM likelihood, or
SI1000 baselines. They remain comparator arms or decoder/export consumers under
their own native interfaces. The twin's claim is the posterior/noise model plus
uncertainty and alias discipline, not a black-box decoder win by itself.

This ADR does not authorize toy-data proof runs for the surface-code decision.
Experiments supporting this architecture must use the declared d=3 surface-code
path first, then d=5/d=7 when the carrier and data pipeline are registered.

## Consequences

Benefits:

- The architecture keeps the likelihood, posterior uncertainty, alias bands, and
  decoder utility in one disciplined stack.
- TN methods are treated as a real posterior/decoder model class rather than as
  a thin SI1000 correction.
- Fourier/Laplace tools remain valuable because they discover residual structure
  in standard observable coordinates without becoming an unscored black box.
- GNNs can help stitch windows and amortize inference while staying downstream
  of the posterior contract.

Costs and risks:

- Bayesian TN inference is computationally heavier than point-estimate DEM
  fitting; approximation error and TN truncation bias need declared budgets.
- Posterior summaries can look overconfident if alias bands are collapsed into
  priors or parameter tying.
- Neural stitching can overclaim unless every result is backed by held-out NLL,
  residual reduction, decoder utility, and null controls.
- The coherent/non-Pauli slot is architecturally real but hardware-claim-limited
  under ADR 0008; controlled-teacher validation remains necessary.

## Implementation Order

1. Register the d=3 surface-code Layer-1 posterior interface: observation
   likelihood, posterior summary schema, held-out split discipline, and decoder
   export format.
2. Run the Layer-2 residual spectrum only after the Layer-1 bulk fit exists on
   the same split; score residuals by the ledgered Walsh/parity-character and
   temporal metrics.
3. Promote residual families only through a preregistered refit: add the declared
   family member, refit Layer 1, compare held-out NLL, `%Delta LER`, and residual
   reduction.
4. Introduce Layer-3 stitching only when cross-window residuals or global-field
   consistency require it; validate by ablation and null controls.
5. Move to d=5/d=7 only through ADR 0008's carrier conditions and baseline
   discipline.

## References

- `docs/adr/0008-scalable-carrier-feasibility-study.md`
- `docs/METRICS.md`
- `docs/papers/reading_notes/bayes_tn_qec_posterior_models_overview.md`
- `docs/papers/reading_notes/ferris_poulin_tensor_networks_qec_1312.4578.md`
- `docs/papers/reading_notes/bravyi_suchara_vargo_mld_surface_code_1405.4883.md`
- `docs/papers/reading_notes/darmawan_poulin_realistic_noise_1607.06460.md`
- `docs/papers/reading_notes/darmawan_poulin_linear_time_decoder_1801.01879.md`
- `docs/papers/reading_notes/kobori_todo_bayesian_noise_parameters_2406.08981.md`
