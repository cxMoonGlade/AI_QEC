+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1503.01603"
source_version = "v1"
source_uri = "https://arxiv.org/abs/1503.01603v1"
source_artifact = "docs/papers/1503.01603v1.pdf"
source_sha256 = "5673ef9f128ff9dae19848e63fac634fdc521ba1ff2a75c6f7336caedba3779b"
title = "External Validity: From Do-Calculus to Transportability Across Populations"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "outputs/researchwrite/qec-memory-directed-research-report/manuscript_v0/source_audits/pearl_bareinboim_2014_transportability_source_audit.md"
audit_packet_sha256 = "ae6385f4f9c9c1f4821b65860977c8126b6bddf32d119296593d00f87c922448"
admission_status = "draft_pending_review"
admission_reviewer = "codex-framework_notes_s2-semantic-pass-schema-path-blocked"
admission_date = "2026-08-06"
visually_checked_pages = [1, 9, 10, 11, 12, 14, 15]
+++
# Full-text review — Pearl and Bareinboim, “External Validity: From Do-Calculus to Transportability Across Populations”

## Source identity [paper_fact]
Fact ID: pearl-bareinboim-source-identity
Source locator: Title page and publication header
PDF page: 1
Claim: The reviewed object is Judea Pearl and Elias Bareinboim's 2014 Statistical Science article “External Validity: From Do-Calculus to Transportability Across Populations,” DOI 10.1214/14-STS486, deposited as arXiv:1503.01603v1.

The electronic reprint identifies the article as Statistical Science 29, 579–595 (2014).

## Article scope [paper_fact]
Fact ID: pearl-bareinboim-article-scope
Source locator: Abstract and Sec. 1
PDF page: 1
Claim: The article formalizes when causal conclusions learned in one population can be transported to another by combining experimental and observational information with assumptions about population differences.

Its central query concerns causal relations across populations, not generic predictive-model accuracy under distribution shift.

## Observational disparity does not locate the changed mechanism [paper_fact]
Fact ID: pearl-bareinboim-mechanism-context
Source locator: Sec. 4.1, discussion of Figs. 3–4
PDF page: 9
Claim: The source shows that the same observed source–target disparity can be compatible with different causal mechanisms and can therefore require different transport formulas.

It concludes that population differences must be represented through assumptions about local changes in causally encoded mechanisms.

## Selection-diagram definition [paper_fact]
Fact ID: pearl-bareinboim-selection-diagram
Source locator: Sec. 4.1, Definition 4
PDF page: 10
Claim: A selection diagram augments a shared causal graph with an arrow from a selection variable to a node whenever that node's structural function or exogenous distribution may differ between source and target populations.

The absence of such a selection arrow represents an invariance assumption for the corresponding mechanism.

## Causal transportability definition [paper_fact]
Fact ID: pearl-bareinboim-transportability-definition
Source locator: Sec. 4.2, Definition 5
PDF page: 11
Claim: A target causal relation is transportable when it is uniquely computable from source observational and interventional distributions together with the target observational distribution in every model inducing the selection diagram.

The definition is relative to a source population, target population, causal query, supplied distributions, and selection diagram.

## Do-calculus reduction criterion [paper_fact]
Fact ID: pearl-bareinboim-do-calculus-criterion
Source locator: Sec. 4.2, Theorem 1
PDF page: 11
Claim: Theorem 1 gives a sufficient transportability criterion when do-calculus reduces the source expression so that selection variables appear only as conditioning variables in terms without intervention operators.

The source states that this criterion was proven necessary and sufficient for causal-effect queries in cited earlier work, while a separate cited algorithm supplies a complete procedure.

## Trivial transportability [paper_fact]
Fact ID: pearl-bareinboim-trivial-transportability
Source locator: Sec. 4.2, Definition 6
PDF page: 11
Claim: A causal relation is trivially transportable when it is identifiable directly from the target causal graph and target observational distribution.

This case requires no experimental information from the source population.

## Direct transportability [paper_fact]
Fact ID: pearl-bareinboim-direct-transportability
Source locator: Sec. 4.2, Definition 7 and following graphical test
PDF page: 12
Claim: A causal relation is directly transportable when it has the same value in the source and target populations, with the source giving a graphical invariance test for the stated query.

Direct transportability is distinguished from recalibration formulas that combine source experiments with target observations.

## Theorem 3 is not a complete decision procedure [paper_fact]
Fact ID: pearl-bareinboim-theorem-three-limit
Source locator: Sec. 5, paragraph following Example 10
PDF page: 14
Claim: The source explicitly states that its recursive Theorem 3 is not guaranteed to approve every transportable relation or reject every nontransportable relation.

It points to an alternative necessary-and-sufficient graphical and algorithmic result in cited earlier work.

## Background-knowledge and idealization limits [paper_fact]
Fact ID: pearl-bareinboim-limitations
Source locator: Sec. 6, final substantive paragraphs
PDF page: 15
Claim: The method requires qualitative background knowledge about where populations may differ and does not directly address measurement error, selection bias, finite-sample variability, graph uncertainty, or possible unmeasured confounding.

The article presents its graphical results as idealized analyses that make their assumptions explicit.

## No generic predictive-transfer guarantee [literature_gap]
Fact ID: pearl-bareinboim-gap-predictive-transfer
Source locator: Article, PDF pages 1–18
PDF page: 1
Claim: This source does not provide a task-independent guarantee for transfer of an arbitrary predictive model or decoder under unspecified source–target change.
Gap scope: source_local

Its formal transportability object is a causal relation defined relative to a selection diagram and specified observational and interventional distributions.

## No repeated-QEC transfer demonstration [literature_gap]
Fact ID: pearl-bareinboim-gap-repeated-qec
Source locator: Article, PDF pages 1–18
PDF page: 1
Claim: This source does not demonstrate cross-device, cross-code, or cross-schedule transfer of a quantum-error-correction model, decoder, or intervention.
Gap scope: source_local

Any such use would require separate QEC evidence and an explicit connection to the source's causal transport query.
