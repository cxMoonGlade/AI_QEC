# Claim audit — Dür et al., entanglement produced by a two-qubit non-local interaction

## Status and decision

This packet audits arXiv:quant-ph/0006034v2 (Phys. Rev. Lett. 87, 137901) for one thing:
the exact amount of entanglement a two-qubit non-local Hamiltonian produces as a function
of evolution time, and the conditions under which that amount is maximal.

The source closes it. Its Eq. (6) gives the entropy of entanglement as the binary entropy
of the Schmidt coefficient, Eq. (13) gives the Schmidt coefficient as
\(P(t)=\sin^2[h_{\max}t+\varphi_0]\), and Eq. (20) gives \(h_{\max}=\mu_1+\mu_2\) from the
singular values of the interaction matrix. Together these fix the per-interaction figure
exactly, with no free parameter.

The source also supplies a limitation this repository did not have: by Eq. (14) the
entanglement rate is **not** maximal starting from a product state; the optimal starting
Schmidt coefficient is \(P_0\simeq0.0832\), \(E(P_0)\simeq0.413\), and that optimum is
independent of the Hamiltonian.

An independent source-only reviewer read the fixed v2 PDF. All four pages were opened
visually; the artifact has exactly four pages and no appendix.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Entanglement measure | Eq. (6), PDF p. 2 | For the Schmidt form of Eq. (4), the entropy of entanglement is \(E(P)=-P\log_2 P-(1-P)\log_2(1-P)\), the binary entropy of the Schmidt coefficient. | Nothing about Rényi indices other than the von Neumann case. | closed |
| Schmidt trajectory | Eq. (13), PDF p. 2 | Under the optimally driven evolution, \(P(t)=\sin^2[h_{\max}t+\varphi_0]\) with \(P(0)=\sin^2\varphi_0\). | This is the trajectory under continuous local re-optimisation, not the bare evolution of an arbitrary fixed input. | closed |
| Interaction strength | Eqs. (15), (16), (20), PDF p. 3 | Any two-qubit Hamiltonian reduces by local unitaries to \(\hat H=\sum_k \mu_k\sigma^A_k\otimes\sigma^B_k\) with \(\mu_1\ge\mu_2\ge\mu_3\ge0\) the sorted singular values of \(\gamma\), and \(h_{\max}=\mu_1+\mu_2\). | The single-qubit terms \(\vec\alpha,\vec\beta\) contribute nothing to \(h_{\max}\) and are explicitly neglected. | closed |
| Rate factorisation | Eqs. (10), (11a), (11b), (12), PDF p. 2 | \(\Gamma=f(P)\,|h(\varphi,\chi)|\) with \(f(P)=2\sqrt{P(1-P)}\,E'(P)\) and \(h_{\max}=\max_{\|\varphi\|,\|\chi\|=1}|\langle\varphi,\chi|H|\varphi^\perp,\chi^\perp\rangle|\). | The factorisation is for two qubits without ancillas. | closed |
| Product start is not optimal | Eq. (14) and the paragraph following it, PDF p. 3 | \(\ln\frac{1-P_0}{P_0}=\frac{2}{1-2P_0}\) gives \(P_0\simeq0.0832\), \(E(P_0)\simeq0.413\); "it is better to start with some initially entangled state rather than a product state", and the optimal initial entanglement is independent of the Hamiltonian. | It does not give the entanglement produced from a product start as a separate closed form. | closed |
| Maximal rate | Eq. (21b) and following text, PDF p. 3 | \(\Gamma_E=f(P)h_{\max}\), and \(\Gamma_{\max}\) is attained at \(P=P_0\) with \(f(P_0)\simeq1.9123\). | No statement about many-qubit circuits or accumulation over gates. | closed |
| Ancillas | Eqs. (26)–(29), PDF p. 4 | With local ancillas the effective strength becomes \(\tilde h_{\max}=\mu_1+\mu_2+\mu_3\); for \(\mu_1=\mu_2=\mu_3\), \(\tilde\Gamma_{\max}\simeq1.3220\,\Gamma_{\max}\), attained at \(\tilde P_0\simeq0.8515\) with the Bell-state choice of Eq. (29). | Ancilla assistance is shown for a specific family, not proven optimal in general. | closed |
| Accumulation over a circuit | full-text scope | The source treats one interaction on one qubit pair. | It defines no accumulation rule over many gates, no tensor-network truncation error, and no Clifford frame. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Two-qubit \(H\) | Reduce by local unitaries to \(\hat H=\sum\mu_k\sigma_k\otimes\sigma_k\) | \(\mu_k\) are the sorted singular values of \(\gamma\) from Eq. (15) | Standard form Eq. (16) | Eqs. (15)–(17), PDF p. 3 | complete |
| Standard form | \(h_{\max}=\mu_1+\mu_2\) | Maximum of Eq. (19) at \(|\varphi\rangle\) an eigenstate of \(\sigma_3\) | Interaction strength | Eq. (20), PDF p. 3 | complete |
| \(h_{\max}\), initial \(\varphi_0\) | Integrate Eq. (9) under optimal local driving | Continuous local re-optimisation at every step | \(P(t)=\sin^2[h_{\max}t+\varphi_0]\) | Eq. (13), PDF p. 2 | complete |
| \(P\) | \(E(P)=-P\log_2P-(1-P)\log_2(1-P)\) | Entropy of entanglement as the measure | Entanglement in ebits | Eq. (6), PDF p. 2 | complete |

## Project application

The statements in this section are inferences drawn here, not claims made by Dür et al.

1. **The per-rotation figure used in this repository is exactly theirs.** For a crosstalk
   generator \(H=Z\otimes Z\) the matrix \(\gamma\) of Eq. (15) is \(\mathrm{diag}(0,0,1)\),
   so \(\mu_1=1\), \(\mu_2=\mu_3=0\) and by Eq. (20) \(h_{\max}=1\). A rotation
   \(\exp(i\theta Z\otimes Z)\) is that Hamiltonian run for time \(\theta\), so Eq. (13)
   with \(\varphi_0=0\) gives \(P=\sin^2\theta\), and Eq. (6) gives
   \(E=-\sin^2\theta\log_2\sin^2\theta-\cos^2\theta\log_2\cos^2\theta\). This is the
   quantity this repository has been calling \(h(\sin^2\theta)\); it is not a new
   construction and must be cited to Eqs. (6), (13) and (20).
2. **A local estimate of the form \(S\approx r\cdot h(\sin^2\theta)\) is not an upper
   bound.** Eq. (14) shows the rate is larger when the state already carries entanglement,
   with the optimum at \(P_0\simeq0.0832\). A residual that is not a product state can
   therefore gain more per rotation than the product-start figure, so any bound built by
   multiplying the product-start value by a count is an estimate, not a bound.
3. **Ancilla assistance does not apply as stated.** Eqs. (26)–(29) allow the two qubits to
   be entangled with local ancillas. In a tensor-network residual the "ancillas" are the
   rest of the chain and are not free, so \(\tilde h_{\max}=\mu_1+\mu_2+\mu_3\) should not
   be assumed. For \(Z\otimes Z\) it makes no difference anyway, since \(\mu_2=\mu_3=0\).
4. **Nothing here licenses an accumulation rule.** The source treats one gate on one pair.
   Any statement about entanglement after many rotations in a circuit requires a separate
   argument, which this source does not supply.

## Competing evidence, anomalies, and kill conditions

- arXiv:2412.17209 (already admitted) bounds the Clifford-augmented MPS bond by
  \(2^{\text{nullity}}\) of a GF(2) matrix. That bound is a **rank** statement and carries
  no rotation angle; this source supplies the **weight** side. The two are complementary
  and neither subsumes the other.
- **Kill condition for the per-rotation figure.** If a workload's crosstalk generator is
  not of the form \(\mu_1\sigma\otimes\sigma\) with \(\mu_2=0\), then \(h_{\max}=\mu_1+\mu_2\)
  differs and \(\sin^2\theta\) is the wrong argument. The generator must be reduced to the
  standard form of Eq. (16) before the figure is quoted.
- **Kill condition for any accumulated estimate.** By project application 2, multiplying
  the product-start value by a count is an estimate. Presenting it as a bound is
  unsupported unless the residual is shown to remain near a product state, which is
  itself the thing being estimated.
