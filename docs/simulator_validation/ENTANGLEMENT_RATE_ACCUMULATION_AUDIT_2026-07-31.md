# Claim audit — what the literature proves about accumulated entanglement generation

## Status and decision

This packet audits two matched sources on one question: given many weak non-local
interactions applied in sequence, what is provably bounded about the entanglement they
generate together?

- arXiv:1304.5931v2, Van Acoleyen, Mariën, Verstraete, *Entanglement rates and area laws*
  (Phys. Rev. Lett. 111, 170501).
- arXiv:1302.3865v4, Lieb and Vershynina, *Upper bounds on mixing rates*.

They are audited together because the first proves the entangling-rate bound this
repository needs, and the second establishes that the *shape* of that bound which matches
the exact single-gate value is a conjecture, not a theorem.

**Decision.** An accumulation rule exists and is proven: the entangling rate is bounded, so
the total is bounded by the sum of per-gate contributions. It is linear in the rotation
angle and additive over gates. It is therefore vacuous in the small-angle regime this
repository works in, where measurement shows the true accumulation is both quadratic in
angle and strongly sub-additive. This closes an earlier statement in this repository that
"no accumulation rule exists in the literature" — that statement was wrong; the correct
statement is that the existing rule is loose here.

Both PDFs were read in full and every page was opened visually: 1304.5931v2 has five
pages, 1302.3865v4 has nine and pages 1–4 carry every row used here.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Entangling rate definition | 1304.5931 Eq. (1), PDF p. 1 | \(\Gamma=\frac{dS_{aA}(t)}{dt}\big|_{t=0}\), with non-interacting local ancillas \(a,b\) that influence the rate only through their entanglement with the rest. | It is a bound at one reference time, "as opposed to a bound on the average rate over some period". | closed |
| Ancilla-free constant | 1304.5931, paragraph 1 of PDF p. 2 | "in the absence of ancillas, \(\Gamma_{\max}\equiv\max_\Psi\Gamma\le\beta\|H\|\) … and \(\beta\simeq1.9123\)", citing Dür et al. | It does not re-derive that constant. | closed |
| SIE conjecture | 1304.5931 Eq. (2), PDF p. 2 | \(\Gamma_{\max}\le c\|H\|\log d\), \(d=\min(d_A,d_B)\), \(c\) an order-one constant independent of \(d\); attributed to Kitaev, put forward by Bravyi. | — | closed |
| SIE proved | 1304.5931, PDF p. 2 ("We will obtain \(c=18\)") and Eq. (15), PDF p. 3; conclusion, PDF p. 5 | The conjecture is proved with \(c=18\), via \(\Lambda(p)\le 9p\log(1/p)\); the conclusion states the bound is "optimal to within a constant" with logarithmic scaling in the subsystem dimension. | The prefactor is stated as "probably not optimal"; Bravyi's numerical constant is \(c''=1\). | closed |
| Improvement over prior | 1304.5931, text following Eq. (15), PDF p. 3 | \(\Lambda(p)\le9p\log(1/p)\) improves on \(\Lambda(p)\le\frac{4}{\ln 2}\sqrt{p(1-p)}\) of ref. [16] for \(p<0.0085\). | — | closed |
| Mixing-rate theorem | 1302.3865 Thm 2.2, PDF p. 4; abstract, PDF p. 1 | For a binary ensemble, \(\Lambda(\mathcal E_2)\le4\sqrt{p(1-p)}\) for any Hamiltonian of norm one, independent of Hilbert-space dimension. | — | closed |
| Binary-entropy shape is a conjecture | 1302.3865 §2.1 and PDF p. 2 | Bravyi's Small Incremental Mixing conjecture is \(\Lambda(\mathcal E_2)\le S(p)=-p\ln p-(1-p)\ln(1-p)\); "The question of bounding a mixing rate by a binary entropy for an ensemble of two states is **still open**." Bravyi proved \(\Lambda\le 6S(p)\) only when \(\rho\) has at most two distinct eigenvalues. | It is not proved in general. | closed |
| Proven bound is loose as \(p\to0\) | 1302.3865, PDF p. 2 | "our \(\sqrt p\) behavior near \(p=0\) is significantly worse than \(p\ln p\)." | — | closed |
| Total-change bound | 1302.3865, "Small Total Entangling", PDF p. 4 | The total change of the entanglement is at most \(2\ln d\), \(d=\min(\dim A,\dim B)\). | For qubits this is \(2\ln2\), which is weaker than the trivial one-ebit ceiling of a single cut. | closed |
| Sub-additive accumulation | full-text scope of both | Both bound a rate, and integrate additively over time. | **Neither** supplies a sub-additive accumulation rule, nor any statement conditioned on the generators being repeated, dependent, or supported off a cut. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Bipartite pure state, non-local \(H_{AB}\) | \(\Gamma=-i\,\mathrm{Tr}(H_{AB}[\rho_{aA},\log\rho_A\otimes I_B])\) | \(a,b\) are non-interacting ancillas; \(\|H\|=1\) | Entangling rate | 1304.5931 Eq. (3), PDF p. 2 | complete |
| \(\Gamma\) | Recast as \(\Gamma=\frac1p\Lambda(p)\), \(p=1/d_B^2\le1/2\) | \(X=\rho_{aA}/d_B^2\), \(Y=\rho_A\otimes I_B/d_B\) | Variational problem over projectors, Eq. (6) | 1304.5931 Eqs. (4)–(6), PDF p. 2 | complete |
| \(\Lambda(p)\) | Interval decomposition of the spectrum, Kittaneh commutator inequality, Cauchy–Schwarz | \(p<1/e^2\) | \(\Lambda(p)\le9p\log(1/p)\) | 1304.5931 Eqs. (8)–(15), PDF pp. 2–3 | complete |
| Binary ensemble \(\{(p,\rho_1),(1-p,\rho_2)\}\) | \(\Lambda(\mathcal E_2)=p\|[\rho_1,\ln\rho]\|_1\), maximised at \(H=1-2R\) with \(R\) the projector on the negative eigenspace of \(i[\rho_1,\ln\rho]\) | \(\|H\|=1\) | \(\Lambda(\mathcal E_2)\le4\sqrt{p(1-p)}\) | 1302.3865 Eq. (2.1) and Thm 2.2, PDF pp. 3–4 | complete |

## Project application

The statements in this section are inferences drawn here, not claims made by either source.

1. **The accumulation rule exists and this repository was wrong to say otherwise.** From
   1304.5931 Eq. (2) with \(c=18\), or from the ancilla-free \(\beta\simeq1.9123\), the
   entanglement after a sequence of rotations of angles \(\theta_j\) generated by
   norm-one Paulis is bounded by \(\beta\sum_j\theta_j\) without ancillas. That is a
   theorem and it applies directly to a crosstalk schedule.
2. **It is vacuous in the regime of interest, and the reason is structural.** The bound is
   linear in \(\theta\) and additive over gates. The exact single-gate value from
   Dür et al. is the binary entropy of \(\sin^2\theta\), which is quadratic in \(\theta\)
   for small \(\theta\). Per gate at \(\theta=2.25\times10^{-2}\) the gap is about a
   factor of seven; summed over a few hundred gates the measured residual entropy in this
   repository is about \(10^{-2}\) bit against a bound of order ten bits.
3. **The shape that does match is unproven as a rate bound.** 1302.3865 §2.1 records the
   binary-entropy form as Bravyi's conjecture and states it is still open, and its own
   proven \(4\sqrt{p(1-p)}\) is explicitly worse than \(p\ln p\) near \(p=0\). So a
   per-gate binary-entropy figure is justified only as the *exact value for a product-state
   input* (Dür et al.), not as a rate bound.
4. **What is missing is specific.** Neither source conditions on the generators being
   repeated or linearly dependent, which is exactly the structure measured in this
   repository's surface-code workload — of 2592 pulled-back crosstalk generators at
   distance nine, only 104 are distinct. A sub-additive accumulation rule using that
   structure is not supplied by either source, and this packet does not claim it is absent
   from the wider literature.

## Competing evidence, anomalies, and kill conditions

- **Anomaly, unresolved here.** 1304.5931 PDF p. 5 states "During completion of our
  manuscript, Audenaert constructed an alternative proof of the SIM conjecture [25]"
  (arXiv:1304.5935, May 2013). 1302.3865 **v4**, dated later (5 Nov 2013), states on PDF
  p. 2 that bounding the mixing rate by a binary entropy "is still open". These two
  statements are in apparent conflict. This audit does not adjudicate it; resolving it
  requires reading arXiv:1304.5935, which has not been fetched. Any claim that the
  binary-entropy rate bound is proven must resolve this first.
- **Kill condition for any accumulated estimate.** Multiplying a per-gate binary-entropy
  value by a count of gates is neither of the two published bounds: it is smaller than the
  proven additive bound and it assumes a shape proven only for the single-gate
  product-state case. It is an estimate. Presenting it as a bound is unsupported.
- **Kill condition for the ancilla-free constant.** \(\beta\simeq1.9123\) holds without
  ancillas. In a tensor-network residual the remaining sites act as ancillas, so the
  applicable constant is the ancilla-assisted one, and 1304.5931 Eq. (2) with \(c=18\)
  and the \(\log d\) factor is the applicable form.
