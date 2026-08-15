+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "doi:10.1093/biomet/82.4.669"
source_version = "version-of-record"
source_uri = "https://doi.org/10.1093/biomet/82.4.669"
source_artifact = "docs/papers/pearl_causal_diagrams_r218b.pdf"
source_sha256 = "0a9dd3218e541acbf26aeff5865e3c70cb662cd7de50e1234d016f1af5da8927"
title = "Causal diagrams for empirical research"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "outputs/researchwrite/qec-memory-directed-research-report/manuscript_v0/source_audits/pearl_1995_causal_identifiability_source_audit.md"
audit_packet_sha256 = "f800c9df7c96f77fbb4ef03ee4854d74f9c2bc4e2a764b1f6bdb2bbd94ade6c2"
admission_status = "draft_pending_review"
admission_reviewer = "codex-framework_notes_s2-semantic-pass-schema-path-blocked"
admission_date = "2026-08-06"
visually_checked_pages = [1, 4, 5, 6, 7, 9, 16]
+++
# Full-text review — Pearl, “Causal diagrams for empirical research”

## Source identity and pagination [paper_fact]
Fact ID: pearl-1995-source-identity
Source locator: Article title page and full artifact pagination
PDF page: 1
Claim: The reviewed object is Judea Pearl's 1995 Biometrika article “Causal diagrams for empirical research,” DOI 10.1093/biomet/82.4.669, in UCLA report R-218-B with the published discussions and rejoinder.

Artifact PDF pages 1–20 correspond to published pages 669–688; artifact pages 21–42 contain the published discussions and rejoinder on pages 689–710.

## Article scope [paper_fact]
Fact ID: pearl-1995-article-scope
Source locator: Summary and Sec. 1
PDF page: 1
Claim: The article develops graphical criteria and inference rules for determining when causal effects can be estimated from nonexperimental data under a causal-diagram model.

The source treats the diagram and its causal interpretation as model assumptions rather than as consequences of observational association alone.

## Nonparametric structural-equation model [paper_fact]
Fact ID: pearl-1995-structural-model
Source locator: Sec. 2.2, Eqs. (3)–(4)
PDF page: 4
Claim: The source represents each endogenous variable as a deterministic function of its graph parents and an exogenous disturbance, while leaving the functional forms and disturbance distributions unspecified.

Shared exogenous influences that violate disturbance independence are represented as unmeasured variables in the graph.

## Causal effect as an intervention-induced distribution [paper_fact]
Fact ID: pearl-1995-causal-effect-definition
Source locator: Sec. 2.2, Definition 2
PDF page: 5
Claim: The source defines the causal effect of X on Y as the distribution of Y induced by deleting the structural equations for X, fixing X to a specified value, and leaving the remaining equations in place.

This definition makes the causal query a model transformation rather than an ordinary observational conditioning operation.

## Identifiability definition [paper_fact]
Fact ID: pearl-1995-identifiability-definition
Source locator: Sec. 3.1, Definition 4
PDF page: 6
Claim: The source calls a causal effect identifiable when it is uniquely computable from any positive distribution over the observed variables that is compatible with the causal graph.

The definition is relative to the declared graph and observed-variable distribution.

## Observational-equivalence witness for nonidentifiability [paper_fact]
Fact ID: pearl-1995-nonidentifiability-witness
Source locator: Sec. 3.1, paragraph following Definition 4
PDF page: 7
Claim: The source states that nonidentifiability can be proved by constructing two compatible structural-equation models that induce the same observed-variable distribution but different causal effects.

Thus even an arbitrarily large observational sample cannot distinguish the causal query in that witness class.

## Back-door adjustment criterion [paper_fact]
Fact ID: pearl-1995-backdoor-theorem
Source locator: Sec. 3.1, Theorem 1, Eq. (6)
PDF page: 7
Claim: Theorem 1 states that a set satisfying the defined back-door criterion makes the causal effect identifiable by adjustment over that set.

The adjustment formula is sufficient only when the graphical back-door conditions hold.

## Three intervention-calculus rules [paper_fact]
Fact ID: pearl-1995-do-calculus-rules
Source locator: Sec. 4.3, Theorem 3, Eqs. (10)–(12)
PDF page: 9
Claim: Theorem 3 gives three rules for inserting or deleting observations, exchanging actions and observations, and inserting or deleting actions under stated d-separation conditions in manipulated graphs.

The source's Corollary 1 makes reduction to an observed, intervention-free expression a sufficient route to identifiability. The article states that completeness of these three rules remained open at that time.

## Graph assumptions and asymptotic identification limit [paper_fact]
Fact ID: pearl-1995-limitations
Source locator: Sec. 6, first two paragraphs
PDF page: 16
Claim: The source states that its results rest on causal assumptions encoded in the graph that generally cannot be tested observationally and that identification analysis assumes sampling variability can be ignored.

It presents derivation of an estimand as a first step that must be followed by statistical estimation and uncertainty assessment.

## Identification does not establish finite-sample precision [literature_gap]
Fact ID: pearl-1995-gap-finite-sample-precision
Source locator: Sec. 6, second paragraph
PDF page: 16
Claim: This source does not provide a general finite-sample accuracy or precision guarantee merely from identifying a causal effect.
Gap scope: source_local

The article explicitly separates the mathematical identification step from confidence intervals, significance levels, and estimation choices.

## No repeated-QEC attribution result [literature_gap]
Fact ID: pearl-1995-gap-repeated-qec
Source locator: Article, discussions, and rejoinder, PDF pages 1–42
PDF page: 1
Claim: This source does not identify a microscopic mechanism in repeated quantum error correction or analyze a syndrome record, decoder, quantum code, or hardware experiment.
Gap scope: source_local

Its formal definitions can distinguish association from an identified causal query only after application-specific variables, interventions, and model assumptions are supplied elsewhere.
