# AI QEC Domain Context

This repository is currently centered on the SCOPE family of QEC noise-learning experiments.

## Terms

- **SCOPE-Twin**: the larger future model class that maps QEC circuit/control context into a physically constrained noise parameter field.
- **SCOPE-Static**: the fixed-context DEM/Bernoulli path. Stage 1 uses known orbit labels; Stage 2 static discovery learns hidden sharing assignments.
- **SCOPE-Static Discovery**: the Stage 2 fixed-context prototype that replaces the known orbit map with a learned assignment matrix `S[j, k]` over DEM-fault prototypes.
- **DEM parity map**: a binary matrix `A in F_2^{B x M}` mapping Bernoulli DEM fault bits to observed detector/logical bits via `y = A e mod 2`.
- **Fault activation vector**: `e in {0,1}^M`; `e_j ~ Bernoulli(p_j)` records whether effective DEM fault `j` occurred in one shot.
- **Observation bits**: the concatenation of detector bits and logical observable bits. Their count is `B`.
- **Observation vector**: `y in {0,1}^B`; the sampled detector/logical bits for one shot.
- **Fault mechanisms**: DEM error mechanisms. After duplicate-mask canonicalization, their effective count is `M`.
- **Stage-1 fault logit**: `lambda_j = logit(p_j)`. Do not write this as `ell_j`.
- **Orbit**: a known grouping of effective fault mechanisms used for hard sharing or soft feature sharing. Its count is `O`.
- **Soft feature orbit field**: a compressed fault-logit field `lambda_j = alpha[omega(j)] + dot(beta[omega(j)], phi[j])`, where `phi[j]` is a fixed centered residual feature.
- **Discovery assignment**: a learned row-stochastic matrix `S` or `Pi`. Do not call it `A`; `A` is reserved for the DEM parity map.
- **Prototype count**: `K` is the number of discovered Stage 2 DEM-fault prototypes. `K_t` is reserved for later template-specific SCOPE-Discovery.
- **d_Q^DEM**: the Stage-1 quotient-aware logit distance over only DEM-preserving fault permutations.
- **Window plan**: a reproducible set of observation-bit windows used by local exact likelihood training/evaluation, including builder config and audit metadata.
- **Logical-aware window plan**: a window plan that includes the logical observable bit directly, especially through deduplicated logical fault-support windows, so local exact likelihood evidence tests detector-logical coupling rather than detector-local syndromes alone.
- **Excess window NLL**: local-window model cross-entropy minus the heldout empirical entropy of the same projected windows. It is reported in nats per window and is the real-data analogue of an oracle delta NLL when no hidden teacher distribution is available.
- **Model-comparison effect sizes**: derived evidence fields that rescale excess window NLL into milli-nats per window, paired deltas versus the uncompressed `local` baseline, and diagnostic pseudo-likelihood deltas per shot. These make small but real local-window gaps readable; they do not change the training objective and are not global exact NLL claims.
- **Likelihood objective**: a prepared training objective over the DEM parity map, such as global exact, detector-only exact, or local-window exact likelihood.
- **Exact local-window parity likelihood**: the Stage-1 mathematical objective that evaluates the Bernoulli DEM parity model exactly on a prepared set of observation-bit windows. It consumes logits over effective DEM fault columns and is independent of orbit, discovery, Google schedule, or preprocessing choices. It does not choose the windows; detector/logical coverage belongs to the window plan and evidence audit.
- **GPU batched local-window exact adapter**: the C++/CUDA implementation of local-window exact likelihood that evaluates all prepared windows in one extension call and returns a first-order gradient for SCOPE-Static training.
- **Evidence record**: one metrics row for a trained SCOPE-Static model, including likelihood source, compression audit, baseline metadata, and threshold inputs.
- **Experiment plan**: the normalized SCOPE-Static run matrix compiled from YAML, including residual ranks, teacher cases, shot budgets, model names, backend choice, and output identity.
- **Catalog pipeline**: the pre-release controlled-catalog workflow. `data_preparation`, `teacher`, and `learner` are the public code responsibilities. `PHYC1/PHYC2/PHYC3` remain legacy artifact aliases.
- **Data Preparation (Prep)**: generates mechanism-catalog records, probe schedules, sampled observations, teacher config, sampling audits, and active probe manifests. Legacy alias: `PHYC1`.
- **Teacher Self-Distinguishment (Teacher)**: asks whether the declared teacher/catalog can distinguish every generated mechanism from teacher-internal mechanism evidence. A pass establishes teacher/catalog identifiability; it is not a no-leakage learner claim. Legacy alias: `PHYC2`.
- **Learner Classification and Noise Generation (Learner)**: consumes learner-visible observations to classify mechanisms and score generated noise/error quality with channel-distance, NLL, and MAE diagnostics. It must not consume teacher-self predictions or hidden/oracle feature inputs. Legacy alias: `PHYC3`.
- **Z/X visible repair**: the strict Y-free, Z/X-only visible probe surface that raises the deterministic visible ceiling before learner-head claims.
- **Distributional Gaussian learner head**: the accepted multi-context learner head on Z/X visible features; it recovers drifted M13 only under a valid multi-context protocol.
- **M13/M14 catalog distinction**: M13 is a context-varying coherent overrotation on its declared operation axis. M14 is operation-dependent error with a visible operation axis and a separate coherent error-generator axis; the first Stage 3 catalog default is `operation_axis=rx`, `error_axis=rz`.
- **2+1 public program surface**: the pre-release toolbox has two supported capabilities plus one active research object: generate teacher-declared noisy QEC observations from a controlled physical-mechanism catalog; learn from learner-visible observations and replay similar visible noisy observation distributions; and, as the "+1", discover the latent mechanism quotient through Stage 3 discovery.
- **Stage 3 discovery**: learning a latent mechanism quotient from observations, not predicting a provided mechanism label. The learner receives only visible noisy observations and approved visible features; evaluator-only labels, channels, PTMs, Kraus matrices, teacher IDs, and oracle prototypes are withheld from the learner path.
- **Observational alias class**: a quotient class for mechanisms that induce indistinguishable or near-indistinguishable visible distributions. If `p(y | m_a) ~= p(y | m_b)` on the declared visible surface, the correct discovery output is `m_a ~_obs m_b`, not an arbitrary forced split.
- **Physicality boundary**: data-preparation mechanism definitions are implemented as unitary channels, Kraus channels, or classical readout assignment matrices. Enabling a mechanism ID selects that catalog definition. The current learner does not yet learn an arbitrary CPTP/GKSL channel family by construction.
- **CPTP guardrail audit**: the data-preparation artifact `cptp_guardrail_audit.json`; it checks complete-positivity representation class, channel dimension, unitary unitarity, Kraus trace preservation, readout stochasticity, and parameter validity for every enabled mechanism record.
- **separability_v2**: the engineered local-observable sampled-response stress teacher. It is useful for separability and leakage-control evidence, but it is not a Born-rule physical baseline.
- **Born-local**: an exact local Born-rule diagnostic where sampled local observations come from exact local Born probabilities for CPTP/readout mechanisms. It has effective depth one and is not the full-circuit teacher.
- **full-circuit-cudaq**: the literal full n-qubit CUDA-Q teacher source at configured circuit depth.
- **Six-axis physical generation problem**: the project-level SCOPE-Twin target. A physical constraint generation model is not validated merely by emitting CPTP/GKSL objects; it must hold simultaneously across generation fidelity, interpretability, decoder utility, cross-context generalization, drift prediction, and identifiability.
- **Numerical floor**: floating numerical floors, thresholds, and probability leftovers use `scope_static.numerics.NUMERICAL_ZERO == 1e-12` instead of exact `0.0`. This value survives square/cube operations in GPU float32. It does not apply to structural zeros such as Pauli matrix entries, bit values, integer indices, counts, labels, or genuinely absent artifacts.
- **Google S3 V2 visible surface**: the current Google real-data Stage 3
  closeout surface. It maps public Google detection-event and observable-flip
  data into public syndrome-response signatures with raw marginal, spatial
  correlation, temporal correlation, logical-coupling, stability, and public
  geometry blocks. It is not a true physical-mechanism label source.
- **S4 neural syndrome-response discovery**: the next research stage after the
  Stage 3 Google V2 closeout. It should use a neural representation with an
  auditable prototype or VQ bottleneck while preserving the Stage 3 no-oracle,
  no-surrogate-ID, shuffle/scramble, and public-stratified-null controls.
- **Google-unit controlled source teacher**: the S4.6 visible-source expansion
  path. It constructs synthetic source rows at the same assignment unit as
  Google V2 public syndrome-response signatures, using design-split Google
  visible modes plus controlled-catalog mechanism mixtures. It is a visible
  syndrome-response source repair, not a Born-rule physical generation model.
- **S4.6 robustness closeout**: the artifact layer that can upgrade a
  current-split S4.6 positive result to a robust positive. It requires paired
  heldout bootstrap, seed/split repeat, stronger statistical controls including
  the visible-surface dMLE-style marginal MLE comparator, and mechanism/source
  structure ablations. These audits never use Google mechanism labels.

## Claim Boundary

The long-horizon problem for the project is the six-axis physical generation
problem: prove that physically constrained generation is faithful, interpretable,
useful to decoders, cross-context generalizing, drift-predictive, and
identifiable at the same time. CPTP/GKSL parameterization is only one constraint
mechanism, not the claim by itself.

The current implemented evidence package studies sample efficiency, compression,
quotient-aware recovery, and controlled-catalog physical-mechanism observations.
Data-preparation mechanisms are implemented as unitary/Kraus/readout
definitions, but the learner does not yet learn an arbitrary CPTP/GKSL channel
family by construction. The package does not claim unsupervised latent
mechanism discovery, real-hardware ground-truth mechanism recovery, Born-rule
likelihood, context-conditioned amortization, OOD transfer, temporal drift
tracking, decoder utility, or a complete solution to the six-axis physical
generation problem.

Stage 2A static discovery is implemented as a synthetic-first identifiability
path. It may claim latent assignment recovery only when synthetic teacher runs
report permutation-invariant discovery metrics such as ARI/NMI and heldout NLL
close to matched known-orbit oracles. Google hardware datasets are external
empirical validation data, not oracle hidden-partition teachers.

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train learner models
that recover and replay learner-visible noisy observation distributions without
oracle leakage. Stage 3 is the next claim boundary: remove direct
mechanism-label supervision and test whether latent mechanism structure can be
inferred from visible observations alone. The catalog pipeline remains
the pre-release validation surface for data preparation, teacher/catalog
self-distinguishment, and no-leakage learner classification/visible-generation
quality.

Stage 3's Google real-data closeout is bounded to no-oracle replay of public
raw syndrome-response structure, not real physical mechanism recovery. The V2
surface beats global/mean-only, assignment-shuffle, feature-scramble, and public
stratified-null controls on raw-target-only scoring; Google still provides no
ground-truth mechanism partition. Stronger learned representations belong to
S4 neural syndrome-response discovery. The S4 execution roadmap is
`docs/STAGE4_ROADMAP.md`; its first gate is bridge-surface survival, not neural
training.

S4.6 may use Google visible data to design source modes only through the declared
design split, then score transfer only on heldout Google rows. Its final claim
boundary remains visible syndrome-response replay and source-to-Google visible
structure transfer. It must not claim true Google physical mechanism recovery,
Google `M*` label recovery, Born-rule physical generation, or CPTP/GKSL channel
learning.
