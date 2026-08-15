# Residual review of the representation–interface–computation framework

## Question

Does any load-bearing literature found in the coverage pass resist the current comparison frame:

1. representation carrying temporal dependence;
2. QEC-facing variables or abstraction;
3. numerical/computational method;
4. scale and type of repeated-QEC result actually demonstrated?

The frame is evaluated as a reader-facing comparison device for selected concrete approaches, not
as a universal ontology of the field.

## Finding

**F1 passes with one necessary amendment.** The four scientific elements remain valid for all six
Section 3 bundles and for the newly reviewed persistent-loss, calibration-conditioned and formal
robustness sources. No important physical or mathematical approach requires collapsing mechanism,
interface and solver.

However, the frame is insufficient for comparing data-trained or adaptive decoders unless it also
makes the **calibration/training/adaptation protocol** explicit. That protocol is cross-cutting, not
a fifth memory-mechanism family.

## Residual cases

| literature bundle | why the four elements alone can mislead | correct treatment |
|---|---|---|
| **QAdapt** | “zero-shot” is uninterpretable without knowing the simulation training distribution, target-hardware exposure, comparator training and whether any target update occurs | record the training domains, target data/metadata access, frozen parameters and comparator exposure in Section 5 |
| **Stein FiLM** | learned parameters are frozen, yet fresh target calibration generates new FiLM values and effective CNN weights; calling the model simply frozen would erase the operative adaptation | distinguish learned parameters, target-conditioned effective parameters and update cadence |
| **Yan et al.** | a fixed checkpoint transfers to matched hardware only after device-calibrated synthetic pretraining; it also survives lower rates only inside its training generator family | state training generator, target calibration, per-distance granularity and fine-tuning/test split |
| **Transformer-QEC** | a shared architecture is described as transferable, but target distances receive fine-tuning and positional adjustment | separate architecture portability from frozen-model transfer |
| **AlphaQubit and other recurrent decoders** | the network has an internal recurrent state and consumes history, but neither object is automatically the physical carrier that generated temporal dependence | keep decoder state distinct from physical/latent generator state; require a history/state ablation for causal benefit |
| **Wang loss decoder** | a persistent absorbing physical loss state and an STGNN's learned hidden state coexist | place the loss state under representation and the learned state under computation; do not merge them into one “memory” |

## Literature that should not be forced into the matrix

- **Hardware mechanism/intervention studies** primarily establish observation, attribution or
  control. Their intervention, comparator and cost belong in Sections 4–5; making each a Section 3
  approach row would turn the matrix into a study inventory.
- **Formal threshold or robustness analyses** may operate on a declared QEC error abstraction
  without a distinct memory-bearing object. Molavi et al. is useful computational/evidence context,
  but its independent-rate hyperrectangle is not a temporal-memory representation.
- **Generic neural decoders** consume an ordered record but often do not state a generative
  temporal process. They belong in the decoder consequence/evidence synthesis unless they expose a
  scientifically interpretable carrier or matched memory-information contrast.
- **Pure observational studies** may infer covariance, bursts or signatures without selecting a
  unique physical representation. That non-identifiability is a Section 5 result, not a failure of
  the Section 3 comparison.

## Required comparison dimensions

For the six Section 3 rows, retain the existing columns:

- memory-bearing representation;
- QEC-facing variables;
- computational strategy;
- physical resolution;
- temporal horizon;
- calibration requirements;
- demonstrated repeated-QEC reach.

When a data-trained or adaptive decoder is included in the comparison or discussed as evidence,
also state, compactly:

- training data/generator and split unit;
- target-domain data or metadata supplied;
- which learned, calibrated or effective parameters are updated;
- whether a separate model is trained by device, code, distance, basis or round count;
- whether transfer is zero-shot, target-conditioned, fine-tuned or online-adaptive.

These fields determine the scientific meaning of robustness and transfer; they are not
implementation trivia.

## Outline consequence

The seven-section narrative and the six-row Section 3 ceiling do not need restructuring. One
reader-facing sentence should be added to Section 3:

> For data-trained or adaptive approaches, comparisons also state how training and calibration are
> partitioned, what target-domain information is supplied, and which parameters are frozen or
> updated, because these choices determine what claims of robustness or transfer mean.

Section 5 should then use the same distinctions when judging decoder benefit, robustness and
transfer. No universal physical-model-to-decoder architecture diagram is warranted.
