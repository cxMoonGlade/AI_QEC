+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:1101.0891"
source_version = "v1"
source_uri = "https://arxiv.org/abs/1101.0891v1"
source_artifact = "docs/papers/1101.0891v1.pdf"
source_sha256 = "69b9212fa7c75a790d7dcdac352b22a19bb9813961d6c5d27c3fca092e9b197e"
title = "To Explain or to Predict?"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "outputs/researchwrite/qec-memory-directed-research-report/manuscript_v0/source_audits/shmueli_2010_prediction_explanation_source_audit.md"
audit_packet_sha256 = "7a5486aec28615e5113fbc37607d7184396c8763e25676a969d65567320d83ef"
admission_status = "draft_pending_review"
admission_reviewer = "codex-framework_notes_s2-semantic-pass-schema-path-blocked"
admission_date = "2026-08-06"
visually_checked_pages = [1, 2, 3, 5, 11, 12, 18, 20]
+++
# Full-text review — Shmueli, “To Explain or to Predict?”

## Source identity [paper_fact]
Fact ID: shmueli-source-identity
Source locator: Title page and publication header
PDF page: 1
Claim: The reviewed object is Galit Shmueli's 2010 Statistical Science article “To Explain or to Predict?”, DOI 10.1214/10-STS330, deposited as arXiv:1101.0891v1.

The electronic reprint identifies the article as Statistical Science 25, 289–310 (2010).

## Article scope [paper_fact]
Fact ID: shmueli-article-scope
Source locator: Abstract and Sec. 1 opening
PDF page: 1
Claim: The article examines how statistical modelling for causal explanation differs from modelling for empirical prediction and how that distinction affects the modelling process.

Its stated purpose is methodological; it is not an empirical comparison of a particular application-domain model.

## Explanatory-modelling definition [paper_fact]
Fact ID: shmueli-explanatory-definition
Source locator: Sec. 1.1, definition paragraph
PDF page: 2
Claim: The article defines explanatory modelling as the use of statistical models to test causal explanations.

The definition is tied to a causal theoretical model and to hypotheses about theoretical constructs; it is not a synonym for every kind of interpretation.

## Predictive-modelling definition [paper_fact]
Fact ID: shmueli-predictive-definition
Source locator: Sec. 1.2, opening paragraph
PDF page: 3
Claim: The article defines predictive modelling as applying a statistical model or data-mining algorithm to predict new or future observations.

The definition includes temporal forecasting and allows different statistical or algorithmic approaches.

## Descriptive modelling is a third category [paper_fact]
Fact ID: shmueli-descriptive-third-category
Source locator: Sec. 1.3
PDF page: 3
Claim: The article separately defines descriptive modelling as compactly summarizing or representing data structure, without making prediction its aim.

The article therefore does not present explanation and prediction as an exhaustive binary classification of modelling activity.

## Explanation and prediction have different scientific goals [paper_fact]
Fact ID: shmueli-distinct-goals
Source locator: Sec. 1, paragraph preceding Sec. 1.1
PDF page: 2
Claim: The article assigns causal explanation and empirical prediction distinct scientific goals and uses the terms explanatory and predictive modelling for the corresponding end-to-end modelling processes.

Those processes include goal definition, study design, data collection, analysis, and scientific use, rather than only the fitted model object.

## Predictive validation concerns generalization [paper_fact]
Fact ID: shmueli-predictive-validation
Source locator: Sec. 2.6.1, opening and following paragraphs
PDF page: 11
Claim: The article defines validation in predictive modelling in terms of generalization to new data and evaluates overfitting by comparing training and holdout performance.

This criterion differs from the model-specification, construct-validation, and fit checks described for explanatory modelling.

## Explanatory and predictive power require separate assessment [paper_fact]
Fact ID: shmueli-separate-performance-assessment
Source locator: Sec. 2.6.2
PDF page: 12
Claim: The article states that explanatory power and predictive power are different and should be assessed separately, with predictive performance ordinarily evaluated out of sample.

It specifically warns against inferring predictive power from explanatory power and notes that association measures do not by themselves establish causation.

## Predictive usefulness need not await causal explanation [paper_fact]
Fact ID: shmueli-two-dimensional-usefulness
Source locator: Sec. 4.2, final substantive paragraphs
PDF page: 18
Claim: The article treats explanatory power and predictive accuracy as two dimensions and states that a predictive model can be scientifically useful without a causal explanation.

It also says that relating a predictive model to causal theory remains important for theory building; predictive usefulness is not presented as proof of causal correctness.

## Underspecification can reduce prediction error in a stated linear case [paper_fact]
Fact ID: shmueli-underspecified-epe-example
Source locator: Appendix, Eqs. (2)–(6) and text following Eq. (6)
PDF page: 20
Claim: In the appendix's linear-regression example, an intentionally underspecified model can have lower expected prediction error than the correctly specified model under the displayed bias–variance condition.

The article lists high noise, small omitted coefficients, correlated predictors, and small samples or a narrow omitted-variable range as settings that can favour the underspecified predictor.

## No repeated-QEC evidence [literature_gap]
Fact ID: shmueli-gap-repeated-qec
Source locator: Article, PDF pages 1–23
PDF page: 1
Claim: This source does not report a repeated-quantum-error-correction experiment, syndrome-record analysis, decoder comparison, or microscopic quantum-memory attribution.
Gap scope: source_local

Its contribution is a general distinction among modelling goals and their validation criteria.
