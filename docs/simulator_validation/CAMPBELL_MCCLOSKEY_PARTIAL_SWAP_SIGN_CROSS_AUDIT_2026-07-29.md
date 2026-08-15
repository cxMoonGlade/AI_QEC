# Campbell–McCloskey partial-SWAP sign cross-audit

Date: 2026-07-29

Status: **frozen candidate cross-source anomaly closure; code and claim use
remain blocked until independent PASS**

This packet resolves which collision sign the GCAPEPS finite-memory bond-32
benchmark will implement.  It does not repair either paper, infer authorial
intent, or make the project model equivalent to Campbell et al.'s collision
stream.

## 1. Frozen primary artifacts

| source | version | SHA-256 | visually checked locator |
|---|---|---|---|
| Campbell et al., arXiv:1805.09626 | v2 | `619f3a5fe047481ef1fc434255e63e0ca3428ca594805a34d9897ec0e9fb4fd5` | Eq. (2), Eqs. (3)–(4), and the paragraph immediately after Eq. (4), PDF p. 2 |
| McCloskey–Paternostro, arXiv:1402.4639 | v3 | `eee6e79e1f217b1c041ae524867c2785c773a9eb9050020927d1b485a0a846cc` | Eqs. (1)–(4), PDF p. 2 |

Both downloaded bytes reproduce the hashes already bound by the admitted
source reviews.

## 2. What is printed

Campbell et al. Eq. (2) prints

\[
H_{ij}=-\frac12(J_xXX+J_yYY+J_zZZ),
\]

while Eqs. (3)–(4) print collision factors \(e^{-iH_{ij}\tau}\).  For the
isotropic case the paragraph following Eq. (4) separately prints

\[
U_{\rm Campbell,printed}
=\cos(J\tau)I-i\sin(J\tau)\,\mathrm{SWAP}.
\]

McCloskey–Paternostro Eq. (1) independently prints

\[
U_{\rm MP}(\gamma)
=\cos\gamma I+i\sin\gamma\,\mathrm{SWAP},
\]

and Eq. (3) uses the same positive sign for the ancilla–ancilla collision.

## 3. Algebraic replay

For qubits,

\[
\mathrm{SWAP}=\frac12(I+XX+YY+ZZ),
\quad
XX+YY+ZZ=2\,\mathrm{SWAP}-I.
\]

Setting \(J_x=J_y=J_z=J\) in Campbell Eq. (2) gives

\[
H=-J\,\mathrm{SWAP}+\frac J2 I.
\]

Therefore the unitary specified by Campbell Eqs. (2)–(4) is

\[
e^{-iH\tau}
=e^{-iJ\tau/2}e^{+iJ\tau\mathrm{SWAP}}
=e^{-iJ\tau/2}
 \left[\cos(J\tau)I+i\sin(J\tau)\mathrm{SWAP}\right].
\]

Thus Campbell's Hamiltonian-plus-evolution equations agree, up to the displayed
global phase, with the positive-sign McCloskey unitary and disagree with
Campbell's own later negative-sign sentence.  The positive- and negative-sign
partial SWAPs are adjoints, not globally phase-equivalent at a generic
\(0<J\tau<\pi/2\).  This is a printed internal source inconsistency; the source
does not state which occurrence should be treated as a correction.

## 4. Frozen project disposition

The benchmark makes an explicit choice rather than silently harmonizing the
papers:

1. its collision primitive is McCloskey–Paternostro Eq. (1),
   \(U_{\rm MP}(\gamma)=\cos\gamma I+i\sin\gamma\mathrm{SWAP}\);
2. with \(R_{PP}(\theta)=e^{-i\theta PP/2}\), each active project Pauli
   rotation uses \(\theta=-\gamma\);
3. the product obeys
   \[
   R_{XX}(-\gamma)R_{YY}(-\gamma)R_{ZZ}(-\gamma)
   =e^{-i\gamma/2}U_{\rm MP}(\gamma);
   \]
4. Campbell Eq. (2) is used only to motivate the available \(XX,YY,ZZ\)
   coupling coordinates, and the Campbell memory-depth results remain adjacent
   background; the benchmark does not claim to implement Campbell's printed
   negative-sign partial SWAP or either source collision stream;
5. axis families 1 and 2 are project-defined restrictions of the available
   Pauli coordinates, not partial SWAPs or literature-defined complexity
   classes; and
6. no result from the Campbell memory embedding is transferred to the closed
   two-row persistent-memory ladder without a separate bridge.

## 5. Frozen executable controls

Before any calibration or target execution, an independent NumPy matrix
control must construct `complex128` \(I,X,Y,Z,\mathrm{SWAP}\) directly and,
for every registered \(\gamma\), verify

\[
\left\|R_{XX}(-\gamma)R_{YY}(-\gamma)R_{ZZ}(-\gamma)
-e^{-i\gamma/2}U_{\rm MP}(\gamma)\right\|_\infty\le10^{-12}.
\]

The phase \(e^{-i\gamma/2}\) is analytic and frozen; phase fitting is
forbidden.  All six Pauli-rotation orders must pass because the three Pauli
products commute.  Directly substituting \(\theta=+\gamma\), replacing the
operator product by a sum, removing the analytic phase, or using Campbell post-
Eq. (4) negative sign must trigger its intended corruption control.  At every
registered nonzero, non-Clifford-special angle, the positive- and negative-sign
partial SWAP matrices must also be shown not globally phase-equivalent.

## 6. Closed and open claims

This audit closes only the executable sign and analytic global-phase relation
for the bounded project collision.  It does not close equivalence to either
paper model, a device-noise calibration, a probability law, a non-Markovian
witness, PEPS contraction accuracy, truncation error, or GCAPEPS efficiency.
Those objects remain governed by their own closure and preregistration rows.
