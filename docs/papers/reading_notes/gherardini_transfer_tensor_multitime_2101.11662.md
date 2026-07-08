# Reading note (精读): Gherardini, Smirne, Huelga & Caruso, "Transfer-tensor description of memory effects in open-system dynamics and multi-time statistics" (arXiv:2101.11662)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** PDF → txt `outputs/papers/2101.11662.txt`
> (13 pages). All §/Eq refs from that text.
> Adjudication target: does this provide a framework for understanding how different
> measurement choices (projective vs non-projective, different bases) affect the
> observed memory structure? **Verdict: YES — the stochastic transfer tensor framework
> explicitly shows instrument-dependence of memory effects.**

## Metadata [paper]
- **Authors:** Stefano Gherardini (Firenze/LENS), Andrea Smirne (Ulm/Milano), Susana Huelga (Ulm),
  Filippo Caruso (Firenze/LENS)
- **Venue / status:** arXiv:2101.11662 (Jan 2021). Published in Phys. Rev. A.
- **Type:** theory (stochastic transfer tensors for multi-time statistics)

## Executive summary [paper]
Introduces **stochastic transfer tensors (TTs)** that depend on the sequence of measurement
outcomes. The TT framework decomposes multi-time joint probabilities into a hierarchy of
tensors encoding memory from two sources: (1) **system-environment correlations** (quantum
memory) and (2) **dependence of the environmental state on previous outcomes** (classical
feedback). Key finding: **projective measurements (λ = 0) vs non-projective measurements
(λ > 0) produce distinct memory behaviors** — at early times, more invasive measurements
REDUCE memory effects; this can reverse near equilibrium.

## Key results [paper]

### Stochastic transfer tensor decomposition
Multi-time joint probabilities factor through a hierarchy of transfer tensors T^{(n)}
that encode n-step memory. Markovian ⇔ T^{(n)} = 0 for n ≥ 2. Non-Markovian
contributions are isolated in higher-order TTs.

### Instrument-dependence
- **Projective measurements** can still have non-zero multi-step TTs due to environmental
  state dependence (classical feedback from previous outcomes)
- **Non-projective (weak) measurements** show distinct memory behavior; at early times,
  more invasive measurements REDUCE memory effects (counter-intuitive)
- Near equilibrium, the trend can reverse

### Two-source decomposition
Memory = quantum S-E correlations + classical environmental-state dependence on outcomes.
The TT framework cleanly separates these two contributions at the level of multi-time
statistics.

## Relevance to project [ours]
**Dimension 5 (measurement invasiveness selectivity) — INSTRUMENT-DEPENDENCE CONFIRMED.**
The TT framework provides the mathematical language for our central claim: the observed
memory/non-classicality depends on the measurement instrument. Specifically:

1. Our joint-parity extraction (ancilla-mediated, Born-rule readout) is a **specific
   instrument** — not a simple projective measurement on data qubits. The TT hierarchy
   would capture how this instrument shapes the observed memory.

2. The two-source decomposition (quantum S-E correlations vs classical outcome-dependence)
   maps to our question: when K > 0 (Kolmogorov violation), is it from quantum bath
   correlations or from classical feedback through the ancilla reset? The TT framework
   can distinguish these.

3. The counter-intuitive finding that "more invasive measurements reduce memory at early
   times" suggests that our ancilla-mediated parity extraction (highly invasive on the
   data qubits) may actually SUPPRESS quantum memory signatures, consistent with the
   r=1 collapse being so dramatic (∼178×).

## Limitations
- General framework; no specific QEC or stabilizer-measurement instantiation
- Requires full multi-time statistics for TT reconstruction (exponential scaling)
- Markovian embedding assumed (time-independent generator between measurements)

## Tags
- `[paper]` stochastic transfer tensors = instrument-dependent memory hierarchy
- `[paper]` memory = quantum S-E correlations + classical outcome-dependent environmental state
- `[paper]` more invasive measurements can REDUCE memory at early times
- `[ours]` ancilla-mediated parity extraction is a specific instrument → TT framework
  would predict its memory signature
- `[ours]` K(r) shape may be partially explained by instrument-dependence, not just
  coupling geometry
