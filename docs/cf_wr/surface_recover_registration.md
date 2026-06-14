# Real XZZX d3 surface noise model — registration

> The white-box noise model on the real Google XZZX d3 surface code, fit to real hardware syndrome data.
> The code is XZZX (8/8 mixed stabilizers), parsed from the real circuit.

## 1. Geometry — parsed from the real circuit

Read the stabilizers + logical from the real d3 `circuit_ideal.stim` (e.g. set2 `d3_at_q5_5`): 9 data
qubits; 8 mixed XZZX stabilizers (bulk weight-4 `X-Z-Z-X`, boundary weight-2 mixed); logical from
`OBSERVABLE_INCLUDE`. d3 = 9 data = 2⁹ fits the exact backend; the stabilizers are Hermitian /
square-to-I / mutually commuting (verified).

## 2. Measured structure — the model target

Measured on real set2 `d3_at_q5_5/X/r15` sample_00 (`docs/cf_wr/surface_recover_RESULTS.md`): device vs
SI1000 — detection 2.4×, edge-pij 3.6×, 3-body cumulant 2×. An independent-edges model is insufficient;
the model must carry correlations + the higher magnitude.

## 3. The model — window-channel field over the mechanism catalog

A field of window channels (`docs/cf_wr/window_covering_architecture.md`): each window = a weight-≤t
composition of catalog mechanisms (M0–M34, including the correlated/coherent M8/M9/M10/M11/M12/M21/
M22–M33) on the window's density matrix, strengths fit to the real syndrome data. The taxonomy is
`docs/error_mechanisms.md`; the channel operators are built differentiably (torch) so strengths can be
fit by gradient. Coherence is preserved end-to-end — the model does not reduce to a Pauli channel.

The real instance is multi-round (9 data + 8 ancilla, many rounds). The forward fits the coherent window
channels via window-local coherent spacetime marginals (per-round ancilla measure/reset, exact within
the backend wall); the approximation/scope is stated explicitly, never reduced to a Pauli twirl.

## 4. Validation — real data, no synthetic ground truth

Held-out per-shot syndrome **NLL** (field-standard: nats/shot/window, paired bootstrap, one-sided) + the
**structure-residual** check (reproduce the measured detection / 2-body / 3-body). There is no exact
"recovery vs teacher" on real data; claims are observation-fit + residual structure, with honest bands.

## 5. Discipline

Real data; `sample_00` training, held-out 05–09 / escrow 15–19 reserved; decoder-independent for the
structure read; shipped `decoding_results/` priors are evaluator/baseline-only, never learner input.
GPU; scripted-execution. Plain reporting.
