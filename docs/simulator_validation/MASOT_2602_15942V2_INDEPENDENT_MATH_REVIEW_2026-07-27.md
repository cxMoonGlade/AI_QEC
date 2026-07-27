# Independent mathematical review — Masot-Llima et al., arXiv:2602.15942v2

Date: 2026-07-27

Review outcome: **FAIL**

Allowed next action: **STOP — wire fired. Reopen the theorem/no-go evidence
row.**

This is an independent adversarial review of:

- Theorem III.1 and its quantifiers;
- Appendix B, especially Eqs. (B1), (B5)--(B8), (B18), and (B25)--(B32);
- the two-qubit local-equivalence statement and 20-representative count on
  PDF p. 3.

It does not modify or approve the existing source note or source-only audit.

## 1. Source and inspection record

Primary source:
`docs/papers/2602.15942v2.pdf`

Source SHA-256:
`ec572bd96d4a937667c2c6fb9c1996da92ff359072050c2fe47b501ed80aa83e`

Comparator:
`docs/papers/1210.7011v2.pdf`

Comparator SHA-256:
`d0d52308fa0e23e7a8a10eab0291c3d02a9b28cb94893375d36693a602b1543f`

The complete relevant text on Masot et al. PDF pp. 3, 6--7, and 13--17 was
read. PDF pp. 3, 6--7, and 13--17 were rendered and visually inspected. The
following printed details were checked against the page images rather than
trusted to text extraction:

- the double-sided relation and the number 20 on p. 3;
- every quantifier printed in Theorem III.1 on p. 6;
- Eq. (B1) on p. 13;
- the plus sign, missing modulus, and square in the denominator of Eq. (B5);
- Eqs. (B6)--(B8) on p. 14;
- Eqs. (B17)--(B18) on p. 15;
- the coefficients and denominators in Eqs. (B25)--(B27) on p. 16;
- the divisions and equality statements in Eqs. (B29)--(B32) on p. 17.

Córcoles et al. PDF p. 8 (supplement internal p. 3), “Decomposition of the
two-qubit Clifford operations,” was also rendered and visually inspected.

## 2. Executive verdict

| object | verdict | reason |
|---|---|---|
| Theorem III.1 as printed | **FAIL** | Its literal characterization of \(U\) has a direct counterexample, and its angle quantifier admits Clifford-angle counterexamples under the pointwise reading. |
| Appendix B proof | **FAIL** | Eq. (B1) is false for a general unitary; Eq. (B5) is not a Gram--Schmidt normalization; the later operator and purity arguments contain independent defects. |
| A narrower existential no-go with repaired quantifiers | **NOT ESTABLISHED** | It may be true, but it is not the printed theorem and Appendix B does not prove it. |
| “double-sided local equivalence leaves 20 classes” | **FAIL** | \(20=11520/24^2\) is a one-sided coset index. The complete local/core/local partition has four classes. |
| “20 output-local one-sided representatives” | **POSSIBLY REPAIRABLE** | This is the quotient compatible with a fixed-input entanglement objective, but it requires a one-sided definition and an independently validated transversal. |

The theorem row must not be admitted as a proved no-go. The result is stronger
than “a typo exists”: the proof begins with a false structural assertion, and
the theorem's literal quantifiers are themselves false.

## 3. Quantifier audit

Theorem III.1, PDF p. 6, does not fix an unambiguous quantifier order. Its
printed prose can be read as

\[
\forall U:\quad
\left[
  \forall\theta,\forall\lvert\Psi\rangle,\;
  U R_\theta
  \bigl(\lvert\Psi\rangle\lvert\phi_n\rangle\bigr)
  \text{ is product across }B|n
\right]
\Longrightarrow
\left[
  U\in\mathrm{Cliff}
  \Longleftrightarrow
  \lvert\phi_n\rangle\text{ is stabilizer}
\right],
\tag{Q1}
\]

where \(R_\theta=e^{-i\theta P_B\otimes P_n}\).

Appendix B instead derives a candidate \(U_2\) containing
\(\alpha=\cos\theta\) and \(\beta=-i\sin\theta\), so its construction allows
\(U\) to depend on \(\theta\). PDF p. 15 explicitly says the proof does not
allow the gadget to depend on \(\lvert\Psi\rangle\). That behavior is closer to

\[
\forall\theta,\forall\lvert\phi_n\rangle,\;
\exists U_{\theta,\phi}
\;\forall\lvert\Psi\rangle.
\tag{Q2}
\]

These are different claims. Neither the theorem nor the proof states all of
the following necessary restrictions:

1. whether \(U\) is fixed across \(\theta\);
2. whether the claim is existential in \(U\), or classifies every
   disentangling \(U\);
3. that the angle is genuinely non-Clifford,
   \(\theta\notin(\pi/4)\mathbb Z\);
4. whether \(P_n\lvert\phi_n\rangle\) must be nonparallel to
   \(\lvert\phi_n\rangle\);
5. which quantities the output factors may depend on.

No theorem-grade citation is safe until those quantifiers are frozen.

## 4. Direct counterexamples to the printed statement

### 4.1 Stabilizer input does not force every disentangler to be Clifford

Take \(N=2\),

\[
P_B=P_n=X,\qquad
\lvert\phi_2\rangle=\lvert0\rangle,
\]

so \(P_n\) acts nontrivially on the stabilizer input. Let

\[
D=\operatorname{CNOT}_{2\rightarrow1}.
\]

For every \(\theta\) and every one-qubit state \(\lvert\Psi\rangle\),

\[
\begin{aligned}
D e^{-i\theta X_1X_2}
  \lvert\Psi\rangle\lvert0\rangle
&=
D\left(
  \cos\theta\,\lvert\Psi\rangle\lvert0\rangle
  -i\sin\theta\,X\lvert\Psi\rangle\lvert1\rangle
\right)\\
&=
\lvert\Psi\rangle
\left(
  \cos\theta\,\lvert0\rangle
  -i\sin\theta\,\lvert1\rangle
\right).
\end{aligned}
\tag{C1}
\]

Now post-compose on the first subsystem with a non-Clifford \(T\) gate:

\[
U=(T_1\otimes I_2)D.
\]

Then

\[
U e^{-i\theta X_1X_2}
\lvert\Psi\rangle\lvert0\rangle
=
T\lvert\Psi\rangle
\otimes
\left(
  \cos\theta\,\lvert0\rangle
  -i\sin\theta\,\lvert1\rangle
\right)
\tag{C2}
\]

is product for all \(\theta,\lvert\Psi\rangle\), but \(U\) is not Clifford.
Indeed, if \(U\) were Clifford, then
\((T_1\otimes I_2)=UD^\dagger\) would be Clifford, which it is not.

Thus the literal implication

\[
\lvert\phi_n\rangle\text{ stabilizer}
\Longrightarrow
\text{every qualifying }U\text{ is Clifford}
\]

is false. A potentially repairable claim must be existential:
“a Clifford disentangler exists,” not “the disentangler \(U\) is Clifford iff.”

### 4.2 The theorem does not exclude Clifford rotation angles

For every Pauli string \(P\),

\[
e^{-i(\pi/4)P}
\]

is a Clifford unitary. Under the pointwise-in-\(\theta\) reading used by
Appendix B, choose

\[
\theta=\pi/4,\qquad U=e^{+i(\pi/4)P}.
\]

Then \(Ue^{-i(\pi/4)P}=I\), so \(U\) disentangles every
\(\lvert\Psi\rangle\lvert\phi_n\rangle\), including every non-stabilizer
\(\lvert\phi_n\rangle\), while \(U\) is Clifford. The still simpler
\(\theta=0,\;U=I\) endpoint gives the same contradiction.

The paper's final paragraph mentions only \(\lvert\beta\rvert^2=1\) as a
Clifford rotation. A Pauli rotation is Clifford for

\[
\theta\in(\pi/4)\mathbb Z,
\]

which also includes \(\lvert\beta\rvert^2=0\) and
\(\lvert\beta\rvert^2=1/2\).

This counterexample does not apply if one instead demands one fixed \(U\) for
all \(\theta\), but Appendix B's \(\theta\)-dependent \(U_2\) is then not a
proof of that different claim.

## 5. Appendix B: independent equation audit

### 5.1 Eq. (B1) is false

Eq. (B1), PDF p. 13, asserts that for an arbitrary unitary \(U\) and a fixed
one-qubit state \(\lvert\phi_n\rangle\), there are operators \(U_1,U_2\) and
an output basis \(\{\lvert\omega\rangle,\lvert\bar\omega\rangle\}\) such that

\[
U
=
U_1\otimes\lvert\omega\rangle\langle\phi_n\rvert
+
U_2\otimes\lvert\bar\omega\rangle
\langle\bar\phi_n\rvert.
\tag{B1'}
\]

A general bipartite unitary has four operator blocks, not two. Equation
(B1') additionally requires the entire subspace
\(\mathcal H_B\otimes\lvert\phi_n\rangle\) to be mapped into
\(\mathcal H_B\otimes\lvert\omega\rangle\), with one fixed output state on
qubit \(n\).

Counterexample: let \(U=\operatorname{CNOT}_{1\rightarrow2}\) and
\(\lvert\phi_2\rangle=\lvert0\rangle\). For
\(\lvert\Psi\rangle=\lvert+\rangle\),

\[
U\lvert+\rangle\lvert0\rangle
=
\frac{\lvert00\rangle+\lvert11\rangle}{\sqrt2},
\]

which is entangled and therefore cannot equal
\(U_1\lvert+\rangle\otimes\lvert\omega\rangle\).

This is a fatal defect independent of every later normalization issue. The
rest of Appendix B proves, at most, a result for a restricted two-block class
of unitaries that was never established to contain every candidate
disentangler.

### 5.2 Eq. (B5) is not Gram--Schmidt

With normalized states and

\[
z=\langle\Omega_1\vert\Omega_2\rangle,
\]

the correct second Gram--Schmidt vector is

\[
\lvert\widetilde\Omega_2\rangle
=
\frac{
  \lvert\Omega_2\rangle-z\lvert\Omega_1\rangle
}{
  \sqrt{1-\lvert z\rvert^2}
},
\qquad \lvert z\rvert<1.
\tag{G1}
\]

The paper instead prints

\[
\frac{
  \lvert\Omega_2\rangle-z\lvert\Omega_1\rangle
}{
  \sqrt{1+z^2}
}.
\tag{B5'}
\]

For example, with

\[
\lvert\Omega_1\rangle=\lvert0\rangle,\qquad
\lvert\Omega_2\rangle=(\lvert0\rangle+\lvert1\rangle)/\sqrt2,
\]

Eq. (B5') gives \(\lvert1\rangle/\sqrt3\), whose norm squared is
\(1/3\), not one. For complex \(z\), the printed denominator can also be
complex or vanish.

### 5.3 Eqs. (B6)--(B8) lose the complex phase and a Pauli factor

No Gram--Schmidt basis is needed. For

\[
\lvert\psi_f\rangle
=
\alpha\lvert\Omega_1\rangle\lvert\omega\rangle
+
\beta\lvert\Omega_2\rangle\lvert\bar\omega\rangle,
\]

the reduced density matrix has determinant

\[
\det\rho_n
=
\lvert\alpha\beta\rvert^2
\left(1-\lvert z\rvert^2\right).
\tag{G2}
\]

Away from \(\alpha\beta=0\), purity requires

\[
\lvert z\rvert=1,
\]

not \(z=\pm1\). Collinearity carries an arbitrary phase.

If

\[
A=U_1^\dagger U_2P_B
\]

is unitary and
\(\lvert\langle\Psi\vert A\vert\Psi\rangle\rvert=1\) for every
\(\lvert\Psi\rangle\), then

\[
A=e^{i\chi}I,
\qquad
U_2=e^{i\chi}U_1P_B.
\tag{G3}
\]

The phase can sometimes be absorbed into a basis convention, but it cannot
be silently replaced by the printed \(\pm1\) argument. Moreover, Eq. (B8) as
printed says

\[
U_1^\dagger U_2=I
\Longleftrightarrow
U_2=U_1P_B,
\]

which is algebraically inconsistent: its left side is missing \(P_B\).

### 5.4 The general proof omits the \(\beta\delta=0\) branches

In Eqs. (B13)--(B16), let

\[
D=1-\lvert\beta\rvert^2\lvert\delta\rvert^2.
\]

After the paper's normalization, the two branch amplitudes have magnitudes
\(\sqrt D\) and \(\lvert\beta\delta\rvert\). The corrected determinant is

\[
\det\rho_n
=
D\lvert\beta\delta\rvert^2
\left(1-\lvert z\rvert^2\right).
\tag{G4}
\]

Therefore separability follows if any of the following holds:

- \(\beta=0\);
- \(\delta=0\), i.e. \(P_n\lvert\phi_n\rangle\) is parallel to
  \(\lvert\phi_n\rangle\);
- \(D=0\);
- \(\lvert z\rvert=1\).

The paper carries only the last branch into Eq. (B17). This is not a harmless
boundary omission: \(\delta=0\) includes Pauli-eigenstate stabilizer inputs for
which no entanglement is created across the target cut.

### 5.5 Eq. (B18) does not follow from Eq. (B17)

In the generic nonzero branch, the strongest operator conclusion, up to a
constant phase, is

\[
\frac{\alpha^*I+\beta^*\gamma^*P_B}{\sqrt D}
U_1^\dagger U_2P_B
=
e^{i\chi}I.
\tag{G5}
\]

Under the paper's \(\alpha,\gamma\in\mathbb R\) convention, this gives

\[
U_2
=
e^{i\chi}
U_1
\frac{\alpha P_B+\beta\gamma I}{\sqrt D}.
\tag{G6}
\]

The printed Eq. (B18) instead:

- writes a scalar expectation as equal to \(I\);
- drops the allowed phase;
- gives \(U_1(\alpha I+\beta\gamma P_B)/\sqrt D\), missing the final
  \(P_B\) multiplication;
- is not consistent with the differently ordered, conjugated expression in
  Eq. (B19).

The proof chain into Eqs. (B19)--(B24) therefore does not follow as written.

### 5.6 Eqs. (B25)--(B27) contain independent density-matrix errors

Writing the state in Eq. (B24) as

\[
a\lvert r,\phi_n\rangle
+b\lvert\bar r,\bar\phi_n\rangle
+c\lvert r,\bar\phi_n\rangle,
\]

the full projector contains nine terms. The displayed Eq. (B25):

- uses \(1/\sqrt D\), rather than \(1/D\), in the
  \(\lvert b\rvert^2\) diagonal term;
- omits the \(\lvert c\rvert^2\) diagonal term;
- omits the \(bc^*\) and \(cb^*\) terms;
- consequently is not the projector of Eq. (B24).

The \(bc^*\) terms vanish after tracing because
\(\langle r\vert\bar r\rangle=0\), but the omitted
\(\lvert c\rvert^2\) term does not. Equation (B26) then jumps to a normalized
lower diagonal \(\lvert\nu\rvert^2\), implicitly using the missing
\(\lvert c\rvert^2\) contribution.

The denominator printed in the \(\rho_n^2\) display of Eq. (B26) also has a
minus sign where Eqs. (B16) and (B27) require

\[
D=1-\lvert\beta\rvert^2
+\lvert\beta\rvert^2\lvert\gamma\rvert^2.
\]

Equation (B27) can be recovered from a separately corrected \(2\times2\)
reduction, but it does not follow reliably from the displayed Eq. (B25).

### 5.7 Eqs. (B29)--(B32) do not support the stated equality cases

Define, where \(D>0\),

\[
q=
\frac{
  \lvert\beta\rvert^2\lvert\gamma\rvert^2
}{
  1-\lvert\beta\rvert^2
  +\lvert\beta\rvert^2\lvert\gamma\rvert^2
},
\qquad 0\le q\le1,
\]

and \(m=\lvert\mu\rvert^2\). The corrected Eq. (B27) is

\[
\operatorname{Tr}\rho_n^2
=
m^2+(1-m)^2+2m(1-m)q.
\tag{G7}
\]

Its exact endpoint conditions are:

\[
\operatorname{Tr}\rho_n^2=1
\Longleftrightarrow
m\in\{0,1\}\ \text{or}\ q=1,
\tag{G8}
\]

and

\[
\operatorname{Tr}\rho_n^2=\frac12
\Longleftrightarrow
m=\frac12\ \text{and}\ q=0.
\tag{G9}
\]

Consequently:

1. Eq. (B29) divides by
   \(\lvert\beta\rvert^2\lvert\gamma\rvert^2\), so it is undefined on the
   \(\beta\gamma=0\) cases that are required for the lower endpoint.
2. The “rightmost term” is nonnegative, not always strictly positive.
3. \(x=\pi/4\) is necessary but not sufficient for the lower bound; one also
   needs \(\beta\gamma=0\).
4. Equal computational-basis magnitudes do not characterize a one-qubit
   stabilizer state.

With \(\mu\ge0\), the one-qubit state

\[
\lvert\phi_n\rangle
=
\mu\lvert0\rangle+\nu\lvert1\rangle
\]

is stabilizer only if either \(\mu\nu=0\), or

\[
\lvert\mu\rvert=\lvert\nu\rvert=1/\sqrt2
\]

and the relative phase is one of
\(0,\pi/2,\pi,3\pi/2\). The continuum

\[
\frac{\lvert0\rangle+e^{i\varphi}\lvert1\rangle}{\sqrt2}
\]

contains non-stabilizer states for generic \(\varphi\), despite \(x=\pi/4\).

For example, choose

\[
\lvert\phi_n\rangle
=
\frac{\lvert0\rangle+e^{i\pi/4}\lvert1\rangle}{\sqrt2},
\qquad P_n=Z.
\]

Then \(\gamma=\langle\phi_n|Z|\phi_n\rangle=0\), so Eq. (G7) reaches
purity \(1/2\) for a non-stabilizer input. This does not by itself construct a
Clifford disentangler, but it defeats the paper's proposed purity witness.

The endpoint errors are therefore fatal to the claimed necessity proof, even
if Eqs. (B1), (B5), and (B18) were repaired first.

## 6. Two-qubit quotient audit

Let

\[
\mathcal K=\mathcal C_1\otimes\mathcal C_1,
\qquad
\lvert\mathcal C_2\rvert=11520,
\qquad
\lvert\mathcal K\rvert=24^2=576.
\]

The number

\[
\frac{\lvert\mathcal C_2\rvert}{\lvert\mathcal K\rvert}=20
\tag{Q3}
\]

is the cardinality of a **one-sided** coset space. It is not a calculation of
the double quotient

\[
\mathcal K\backslash\mathcal C_2/\mathcal K.
\]

Masot et al. PDF p. 3 instead defines

\[
V=(L_1\otimes L_2)U(R_1\otimes R_2)
\tag{Q4}
\]

and immediately reports 20 equivalence classes. Those two statements are not
group-theoretically consistent.

Córcoles et al., PDF p. 8, independently gives a complete four-class
decomposition of the 11,520 two-qubit Cliffords:

| class | count |
|---|---:|
| local | \(24^2=576\) |
| CNOT-like | \(24^2 3^2=5184\) |
| iSWAP-like | \(24^2 3^2=5184\) |
| SWAP-like | \(24^2=576\) |

The counts sum to 11,520. The source presents this as a local/core/local
decomposition, not in formal double-coset notation, but it is consistent with
four nonlocal local-equivalence types, not 20 double-sided types.

For a fixed-input objective

\[
f_\psi(U)=E(U\lvert\psi\rangle),
\]

post-action local Cliffords can be removed:

\[
f_\psi(LU)=f_\psi(U).
\]

Pre-action locals cannot generally be removed because

\[
f_\psi(UR)=f_{R\psi}(U)
\]

need not equal \(f_\psi(U)\). A direct counterexample is

\[
U=\operatorname{CNOT},\qquad
R=H\otimes I,\qquad
\lvert\psi\rangle=\lvert00\rangle.
\]

Then \(U\lvert00\rangle=\lvert00\rangle\), while

\[
UR\lvert00\rangle
=
\frac{\lvert00\rangle+\lvert11\rangle}{\sqrt2}.
\]

Thus a 20-candidate fixed-input search can be coherent only as an
output-local **one-sided** transversal. The paper's double-sided explanation
cannot certify that catalogue or its completeness.

This group-theory defect is locally repairable only if:

1. Eq. (Q4) is replaced by the intended one-sided relation;
2. the action side is frozen consistently with the state-vector convention;
3. the actual 20 representatives are enumerated and shown to cover disjoint
   one-sided cosets.

Changing “20” to “4” would not repair a fixed-input optimizer, because
pre-action local gates can change the score.

## 7. Fatal versus repairable findings

### Fatal to Theorem III.1 as a proved result

1. Eq. (B1) is false for arbitrary \(U\).
2. Eq. (B5) is not an orthonormalization.
3. The literal “\(U\) is Clifford iff” statement is refuted by Eq. (C2).
4. The angle domain includes Clifford angles under the proof's pointwise
   reading.
5. Eqs. (B6)--(B8) replace unit-modulus collinearity by \(\pm1\) and lose an
   operator factor.
6. The general proof omits \(\beta\delta=0\) branches.
7. Eq. (B18) does not solve Eq. (B17).
8. Eqs. (B25)--(B32) do not establish the advertised stabilizer-only purity
   endpoints.

These defects require a new theorem statement and a new proof. They are not a
single-sign erratum.

### Repairable, but only with new evidence

1. A theorem of the form

   > For fixed weight-at-least-two \(P\), fixed genuinely non-Clifford
   > \(\theta\), and fixed \(\lvert\phi_n\rangle\), there exists a Clifford
   > \(U_{P,\theta,\phi}\), independent of \(\lvert\Psi\rangle\), that
   > disentangles qubit \(n\) for every \(\lvert\Psi\rangle\) iff
   > \(\lvert\phi_n\rangle\) is stabilizer

   may be close to the intended statement. This review neither proves nor
   disproves it. It requires a fresh proof that does not assume Eq. (B1).
2. The 20-gate count may be retained as a one-sided output-local coset count,
   provided an exact representative catalogue and coverage proof are supplied.
3. Several isolated typesetting defects in Eqs. (B4), (B8), (B18), (B25), and
   (B26) are individually repairable, but repairing them does not repair the
   theorem because the independent counterexamples and Eq. (B1) remain.

## 8. Weakest claims safe to cite

The following are the strongest safe uses of this source after this review:

1. **Safe as a source report:** Masot et al. propose and numerically study a
   Clifford entanglement-cooling heuristic for tensor-network states.
2. **Safe as a source report:** the paper says its two-qubit heuristic uses
   20 candidates. Do not call those 20 candidates double-sided local
   equivalence classes on the authority of PDF p. 3.
3. **Safe constructive sufficiency statement:** Definition 3 and Appendix A
   describe a controlled-Pauli construction when the residual contains an
   affected separable stabilizer site. This is a sufficient construction, not
   the necessity/no-go of Theorem III.1.
4. **Safe limitation wording:** the paper *states* a no-go theorem for
   universal Clifford disentangling, but its printed theorem/proof fails this
   independent mathematical review.

The following are not safe:

- “Masot et al. prove that a universal exact Clifford disentangler exists only
  for a stabilizer target.”
- “Every state-agnostic disentangler \(U\) is Clifford iff the target state is
  stabilizer.”
- “The two-qubit double quotient has 20 classes.”
- “Theorem III.1 proves that all non-stabilizer residuals must spread in
  CAPEPS or PEPS.”

## 9. Stress-test wires

| wire | result | evidence |
|---|---|---|
| theorem / symmetry | **fires** | Eqs. (C1)--(C2) refute the literal characterization of \(U\); Clifford-angle endpoints refute the pointwise angle reading. |
| formulation invariance | **fires** | Universal-in-\(\theta\), pointwise-in-\(\theta\), existential-in-\(U\), and universal-in-\(U\) formulations are inequivalent; the source mixes them. |
| independent ground truth | **fires against the source claim** | Direct block-matrix algebra gives Eqs. (G1)--(G9); Córcoles independently supplies the complete four-class partition. |
| degenerate design | **fires** | \(\theta=0\), \(\theta=\pi/4\), and \(\delta=0\) are permitted by the printed theorem but bypass its claimed constraint. |
| suppressing lens | **fires** | Single-qubit reduced purity in \(\{1,1/2\}\) is only necessary for a global stabilizer state; the equality analysis does not characterize stabilizer inputs. |
| un-led adversarial reproduction | `pending` | This reviewer was independent of the original note but was explicitly directed to the suspect equations, so the stricter un-led wire is not claimed. |
| predict-before-measure | `not_applicable` | No new numerical experiment is reviewed here. |
| propagation | **fires** | At least one current closure packet says the paper “proves” the no-go. |

Overall stress-test outcome:

`STOP — wire fired`

## 10. Propagation audit

The following current consumers need reconciliation by the parent workflow:

1. `docs/simulator_validation/CAPEPS_DISENTANGLER_THEORY_FIRST_CLOSURE_2026-07-27.md`,
   line containing “the same paper proves that a universal exact Clifford
   disentangler...” — **premise-bearing false promotion; must be downgraded to
   an unresolved/failed source theorem**.
2. The copied closure under
   `docs/CAPEPS_EVIDENCE_BUNDLE_2026-07-27/02_scientific_closure_and_audits/`
   contains the same sentence — **derived bundle copy; regenerate only after
   the authority document is repaired**.
3. `docs/simulator_validation/CAPEPS_EXACT_SMALL_DISENTANGLER_PREREGISTRATION_2026-07-27.md`
   calls cited no-go limitations “Source facts” — **the preregistration is
   already blocked, but this no-go cannot be counted as a closed source fact**.
4. `docs/simulator_validation/MASOT_2602_15942V2_SOURCE_ONLY_AUDIT_2026-07-27.md`
   already marks the proof unresolved and blocks use. This independent review
   strengthens that barrier: the printed theorem is not merely unverified; its
   literal quantifiers are refuted.
5. `docs/simulator_validation/CAPEPS_XZZX_PAPER_FULL_REWRITE_2026-07-27.md`
   already distinguishes one-sided 20 representatives from four double-sided
   classes. No theorem/no-go dependence was found there in this propagation
   search.

No source-code conclusion follows from this review. The current CAPEPS
literature-closure and preregistration gates must remain open/blocked.

## 11. Final decision

### Theorem III.1

`FAIL_AS_PRINTED`

### Appendix B

`FAIL_MULTIPLE_INDEPENDENT_FATAL_ERRORS`

### Double-sided 20-class claim

`FAIL`

### Narrow existential stabilizer-restriction no-go

`OPEN_REQUIRES_NEW_STATEMENT_AND_PROOF`

### Evidence action

`REOPEN_EVIDENCE`

Do not admit or propagate the no-go theorem. Retain only the weakest
source-report and constructive-sufficiency claims listed in Section 8.
