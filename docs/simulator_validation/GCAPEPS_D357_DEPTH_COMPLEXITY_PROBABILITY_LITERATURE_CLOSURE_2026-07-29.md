# GCAPEPS distance/depth/noise-complexity/probability sweep — closure

Date: 2026-07-29

Status: **closed for a bounded performance-only unitary-layer sweep; not
closed for measured QEC rounds, stochastic trajectories, Record faithfulness,
or a generic speedup claim**

## Frozen extension

This packet extends the already closed \(d=3,5,7\) equal-status carrier
benchmark with three project-defined axes:

- \(L\): persistent coherent unitary-layer count;
- \(K\): distinct local non-Clifford Pauli-rotation locations per layer;
- \(p_{\mathrm{twirl}}\): the Pauli-error probability of the channel obtained
  by twirling each coherent rotation.

For a Hermitian Pauli \(P\),

\[
U_P(\theta)=e^{-i\theta P/2}
=\cos(\theta/2)I-i\sin(\theta/2)P.
\]

Pauli twirling removes the two interference terms, giving

\[
\mathcal T[U_P](\rho)
=\cos^2(\theta/2)\rho+\sin^2(\theta/2)P\rho P.
\]

The sweep therefore defines

\[
p_{\mathrm{twirl}}=\sin^2(\theta/2),
\qquad
\theta(p)=2\arcsin\sqrt p.
\]

This is a calibration coordinate for a coherent rotation. It is not a sampled
Bernoulli event and supplies no trajectory occurrence count.

Each layer reuses the same first-measurement XZZX H/CX unitary shell on a
persistent state and then applies \(K\) physical \(R_Y\) errors. It omits
measurement and reset. Consequently \(L\) is not a syndrome-extraction-round
claim and cannot be used as evidence about a multi-round detector/observable
Record.

## Grounding and no-go ledger

| premise | source or derivation | status |
|---|---|---|
| Clifford-frame plus tensor residual and Pauli pull-through | Harper et al. source review, `docs/papers/reading_notes/harper_hybrid_surface_code_2605.29514v1_source_review.md`, Sec. IV.A source locators | `CLOSED_ADJACENT`; MPS precedent only |
| coherent Pauli rotation and its twirled error probability | complete two-term derivation above; Harper source review Secs. III.B–III.C provides adjacent coherent/twirled surface-code context | `CLOSED_BY_DERIVATION` |
| multiple coherent updates may multiply routed bonds | GCAPEPS theorem Eq. (17) and current carrier resource ledger | `CLOSED_REPRESENTATION_BOUND`; no small-bond promise |
| measurement/reset/Record across physical rounds | current GCAPEPS carrier and Harper source audit | `OPEN_AND_EXCLUDED` |
| generic exact/approximately certified PEPS contraction | Schuch VOR source review, PDF pp. 2–3 | `NO_GO_BOUNDARY` |
| runtime, RSS, completion, bonds, tensor elements | project benchmark definition | direct engineering observables |

No new field-wide prior-art or novelty claim is made, so no external search is
load-bearing for this bounded benchmark extension.

## Closure verdict

```text
PASS_TO_PREREG = yes
PASS_TO_CODE = yes, only after the grid preregistration is committed
large_state_truth_required = no, because no state/Record estimand is present
physical_multi_round_QEC_claim = forbidden
stochastic_error_occurrence_claim = forbidden
generic_speedup_or_asymptotic_claim = forbidden
```
