# Independent review: Campbell–McCloskey partial-SWAP sign cross-audit

Date: 2026-07-29

Verdict: **PASS**

## 1. Reviewed candidate and primary artifacts

This review is bound to the candidate
`docs/simulator_validation/CAMPBELL_MCCLOSKEY_PARTIAL_SWAP_SIGN_CROSS_AUDIT_2026-07-29.md`
with SHA-256
`c03915a4f91aae7c5c746871120ca2d9d904fbcaaac2a8a78d9de236899dc1a0`.

The following frozen local primary artifacts were independently checked:

| artifact | SHA-256 | visually checked locator |
|---|---|---|
| `docs/papers/1805.09626v2.pdf` | `619f3a5fe047481ef1fc434255e63e0ca3428ca594805a34d9897ec0e9fb4fd5` | Campbell et al. Eq. (2), Eqs. (3)–(4), and the paragraph immediately after Eq. (4), PDF p. 2 |
| `docs/papers/1402.4639v3.pdf` | `eee6e79e1f217b1c041ae524867c2785c773a9eb9050020927d1b485a0a846cc` | McCloskey–Paternostro Eqs. (1)–(4), PDF p. 2 |

The visual check confirms that Campbell Eq. (2) gives the negative-sign
isotropic exchange Hamiltonian and Eqs. (3)–(4) use \(e^{-iH\tau}\), while the
sentence after Eq. (4) prints a negative-sign partial SWAP.  McCloskey–
Paternostro Eqs. (1) and (3) print the positive-sign partial-SWAP convention.
The candidate therefore reports the source text faithfully and does not infer
an unstated authorial correction.

## 2. Independent algebraic replay

Using

\[
\mathrm{SWAP}=\frac{I+XX+YY+ZZ}{2},
\]

the isotropic specialization of Campbell Eq. (2) is

\[
H=-\frac{J}{2}(XX+YY+ZZ)
  =-J\,\mathrm{SWAP}+\frac{J}{2}I.
\]

Consequently,

\[
\begin{aligned}
e^{-iH\tau}
&=e^{-iJ\tau/2}e^{+iJ\tau\,\mathrm{SWAP}}\\
&=e^{-iJ\tau/2}
  \left[\cos(J\tau)I+i\sin(J\tau)\,\mathrm{SWAP}\right].
\end{aligned}
\]

This independently reproduces the candidate's conclusion: Campbell's
Hamiltonian-plus-evolution equations select the positive-sign branch, up to
the analytic global phase, whereas Campbell's later sentence prints the
negative-sign branch.

The two branches

\[
U_\pm(\gamma)=\cos\gamma I\pm i\sin\gamma\,\mathrm{SWAP}
\]

are not globally phase-equivalent at generic \(0<\gamma<\pi/2\).  On the
\(\mathrm{SWAP}=\pm1\) eigenspaces their eigenvalues are
\((e^{\pm i\gamma},e^{\mp i\gamma})\); a common phase relating \(U_+\) and
\(U_-\) would require \(e^{4i\gamma}=1\), which does not hold in that generic
interval.

With the project convention
\(R_{PP}(\theta)=e^{-i\theta PP/2}\), the commuting products \(XX\), \(YY\),
and \(ZZ\) give

\[
\begin{aligned}
R_{XX}(-\gamma)R_{YY}(-\gamma)R_{ZZ}(-\gamma)
&=\exp\!\left[\frac{i\gamma}{2}(XX+YY+ZZ)\right]\\
&=e^{-i\gamma/2}e^{i\gamma\,\mathrm{SWAP}}\\
&=e^{-i\gamma/2}U_{\rm MP}(\gamma).
\end{aligned}
\]

The candidate's frozen choice \(\theta=-\gamma\), its analytic global phase,
and its proposed independent matrix controls are therefore algebraically
correct.

## 3. Claim-boundary review

The candidate correctly closes only the executable sign convention and
analytic global-phase relation for the bounded project collision primitive.
Its explicit project choice does **not** establish:

- equivalence to Campbell's printed negative-sign partial SWAP;
- equivalence to either paper's complete collision stream or memory model;
- a physical probability law, device-noise calibration, or BLP witness;
- PEPS contraction or truncation accuracy, a whole-state error certificate,
  or a GCAPEPS speed or memory advantage;
- measurement/reset/Record correctness; or
- qutrit/SDIM, composite-\(d\), or leakage correctness.

The candidate preserves these boundaries, labels the two restricted axis
families as project-defined, and forbids transferring Campbell memory results
to the project ladder without a separate bridge.

## 4. Final disposition

- Candidate hash match: **PASS**
- Primary-source visual locator check: **PASS**
- Independent algebraic replay: **PASS**
- Executable sign and analytic-phase disposition: **PASS**
- Claim-boundary discipline: **PASS**
- Remaining repair required for this candidate: **none**

This independent review admits the frozen candidate cross-audit for its stated
bounded purpose only.  It is not a PASS for the wider finite-memory benchmark,
its preregistration, or any downstream implementation.
