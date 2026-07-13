# Finite-RTN exact reduced-map diagnostic — result (2026-07-13)

> **Verdict:** `GATE_PASS_DIAGNOSTIC_ONLY`. Both registered free-induction diagnostic lifts show
> BLP-positive excursions and agree with independent full-`2^8` oracles. An unled reconstruction
> independently reproduced the result. The production `z -> Theta -> QEC channel -> syndrome record`
> bridge was not tested and remains open.

## Frozen inputs and artifacts

- Literature closure:
  [`finite_rtn_exact_cpdiv_literature_closure_2026-07-13.md`](finite_rtn_exact_cpdiv_literature_closure_2026-07-13.md)
- Prediction/gate document, written before the first run but not committed before first inspection:
  [`finite_rtn_exact_cpdiv_prereg_2026-07-13.md`](finite_rtn_exact_cpdiv_prereg_2026-07-13.md)
- Committed execution source:
  [`scripts/finite_rtn_exact_cpdiv_gate.py`](../../scripts/finite_rtn_exact_cpdiv_gate.py)
- Raw JSON (generated locally and gitignored):
  `outputs/twin_validation/finite_rtn_exact_cpdiv_gate.json`. It is not delivered by a clean
  checkout; the committed script and bound inputs reproduce it with the command below.
- Artifact content hash:
  `de04160d0c5a2d22a773fbeffe8805c3c2be7a6d68c7239daa09e528d99c5ffd`
- Artifact byte hash:
  `ad2011fa0ae9a2f35590341e6c95f2bdfd66c4b3e57aae120f2700b3035a569b`
- Bound clean execution commit:
  `e35ff7d89ef6e656b8e0205abae0753630459f7d`
- Command: `conda run -n aiqec python scripts/finite_rtn_exact_cpdiv_gate.py`
- Exit status: `0`.

The source defaults were unchanged. In cycle units, all eight amplitudes are
`a_k=(1e-4/sqrt(8))*1000=0.035355...`; the amplitude-to-rate ratios are

```text
[7.0711, 3.6624, 1.8970, 0.9825, 0.5089, 0.2636, 0.1365, 0.0707].
```

Thus exactly the first three modes are in the strong `a_k>g_k` regime. These are project-design
defaults, not hardware-calibrated values.

## Registered-gate-to-result table

| registered prediction/gate | result | verdict |
|---|---:|---|
| continuous product equals full 256-state CTMC Feynman–Kac oracle | max absolute error `1.33e-15` | pass (`<=1e-10`) |
| earliest strong-factor zero followed by recovery | `t0=48.9340966114` cycles; `|L(t0)|=7.84e-84`; `|L(t0+1)|=1.5318e-4` | positive exact witness |
| continuous diagnostic BLP-positive within 200 cycles | grid estimate `0.00208060`; max `0.01`-cycle step `2.09e-6` | confirmed diagnostic only |
| held-cycle product equals full 256-state transfer oracle | max absolute error `1.55e-15` | pass (`<=1e-10`) |
| held-cycle diagnostic BLP-positive within 200 integer cycles | positive excursion `0.00196887`; max step `1.4406e-4` | confirmed diagnostic only |
| Gaussian second-cumulant negative control monotone | positive excursion `0` | pass |
| all-weak exact-RTN negative control monotone | positive excursion `0` | pass |
| wrong factor-of-two rate convention is rejected | max oracle mismatch `0.09311` | corruption trips |
| omit one RTN factor is rejected | max oracle mismatch `0.09180` | corruption trips |

The load-bearing continuous verdict is not grid-created: an analytic strong-factor zero and an
80-decimal-digit nonzero recovery witness the increase. The grid value is only a finite-horizon BLP
estimate. Exact zeros make a log-generator RHP integral singular, so no headline RHP number is
reported.

The JSON also carries the bound SHA-256 and Git blob IDs for the prediction document,
production source, and execution script; 9 continuous-oracle rows, 10 held-oracle rows, and
the full 201-point held sequence are serialized rather than reconstructed from this summary.

## Protocol-integrity caveat

The first result was inspected while the prediction document and execution script were still
uncommitted. They were subsequently committed, provenance-bound, corrected under hostile review,
and rerun cleanly at the commit above. The current artifact is therefore reproducible and
tamper-evident for that rerun, but repository history cannot establish a pristine Git
preregistration before first result inspection. The evidence class is **independently reproduced
exact diagnostic with imperfect preregistration provenance**, not an audit-pristine preregistered
prediction. This caveat changes the historical label, not the exact diagnostic calculation.

## What this establishes

1. The earlier `RHP=BLP=0` calculation belongs only to the positive-covariance Gaussian surrogate.
2. If the production endpoint process is embedded as the declared continuous symmetric-CTMC
   longitudinal free-induction model, its default exact product coherence is non-monotone.
3. If the same endpoints are instead embedded as the declared cycle-held longitudinal phase model,
   the integer-time characteristic function is also non-monotone within 200 cycles.
4. For each named pure-dephasing diagnostic, the positive `|L|` excursion is a BLP backflow witness
   and rules out divisibility of that diagnostic dynamical-map family.

## What this does not establish

- `OneOverFDriftSource` by itself has no CP-divisibility property; a stochastic source is not a
  reduced dynamical map.
- Production code does not directly apply either diagnostic Hamiltonian. It fans `z_r` into several
  mechanism parameters through `SourceCouplingConfig`.
- The result does not determine CP-divisibility of the production coupled QEC map, whether a
  quarter-CZ/measurement/reset instrument exposes the diagnostic revival, record Markov order,
  quantum versus classical process memory, PEPS record fidelity, or LER.
- Agreement of continuous and held lifts does not bound either lift's error relative to the
  production QEC record. That simplification remains unbounded, so propagation stops at the
  diagnostic.

## Gate conclusion

`F3` and `F4` in the literature packet are closed for their explicitly named diagnostic objects.
`F5` remains `missing/open`. The correct current wording is:

> The Gaussian surrogate is CP-divisible. Two exact, independently checked free-induction lifts of
> the finite-RTN defaults exhibit BLP backflow. The production source fan-out/QEC channel and full
> record have no notion-1 verdict until the missing channel/instrument bridge is built and bounded.

Stress-test record:
[`finite_rtn_exact_cpdiv_stress_test_2026-07-13.md`](finite_rtn_exact_cpdiv_stress_test_2026-07-13.md).
