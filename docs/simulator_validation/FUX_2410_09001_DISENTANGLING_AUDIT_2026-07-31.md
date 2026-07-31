# Claim audit — Fux et al., when a Clifford frame can completely disentangle a doped state

## Status and decision

This packet audits arXiv:2410.09001v3 for one question only: under what exact
condition a Clifford unitary can be chosen so that a state produced by Clifford
circuits interspersed with non-Clifford phase gates becomes a Clifford acting on
a product (or low-bond) magic state. The source closes that condition as a
quantum-error-correction statement (Theorem 1), supplies an analytic average
budget for deep random Clifford blocks, confirms it numerically with a
Clifford-augmented matrix product state ansatz, and states an explicit negative
consequence for Trotterized Hamiltonian dynamics.

An independent source-only reviewer read the fixed v3 PDF and checked every
claim and locator against it. Pages 1–6 were opened visually; pages 7–8 are
references and were not used for any row.

This paper was already a dangling reference inside two sources this repository
had admitted: it is cited by arXiv:2511.06672v2 and by arXiv:2412.17209v2, and
was never fetched, read, or admitted. This audit closes that gap. It changes no
implementation and grants no code permission by itself.

## Assigned closure rows

| row | exact source location | source says | source does not say | status |
|---|---|---|---|---|
| Disentangling criterion | Theorem 1 and Eq. (1), PDF p. 2 | If the Pauli operator \(P\) carried by the next phase gate is **not a logical operator** of the \([N,k]\) stabilizer code defined by the current Clifford encoding, then a Clifford \(\tilde C\) exists that absorbs the gate and grows the logical register by exactly one qubit. | The theorem does not assert anything when \(P\) *is* a logical operator, and it does not bound the entanglement in that case. | closed |
| Criterion is not commutation | Theorem 1 statement and proof, Eqs. (2)–(3c), PDF p. 2 | The hypothesis is membership in the code's logical-operator set, split by the proof into the two cases \(P\in\mathcal S\) and \(PS_j=-S_jP\) for some \(j>k\). | The source never states, or uses, a pairwise-commutation condition on the accumulated phase-gate axes. | closed |
| Average gate budget | Paragraph after the proof of Theorem 1, PDF p. 2 | For deep random Clifford blocks the probability that a uniformly random \(P\) is not logical for an \([N,k]\) code is \(p_{k+1}=1-(4^{k}-1)2^{N-k}/(4^{N}-1)\), giving \(\langle\tau\rangle=\langle N-t^{*}\rangle\approx1.607\) with \(\sigma_\tau\approx1.6565\). | The estimate is explicitly probabilistic and assumes deep random Clifford circuits generating random stabilizer codes. It is not claimed for shallow or structured Clifford layers. | closed |
| Numerical confirmation | Paragraph beginning "Clifford gates on random (non-local) pairs", PDF p. 4 | Complete disentangling holds for \(t\lesssim N\); for large \(N\), full disentangling up to \(t^{*}=N-\tau\) with \(\langle\tau\rangle=1.61\pm0.09\), \(\sigma_\tau=1.60\pm0.12\). | The Clifford blocks used are \(2N^{2}\) two-qubit gates on random non-local pairs — deep and global. No structured or geometrically local Clifford schedule is tested. | closed |
| Arbitrary rotation angles | Paragraph beginning "Although we phrased our argument using T-gates", PDF p. 2; Discussion, PDF p. 5 | Theorem 1 applies unchanged to any \(e^{i\phi_j P_j}\), so the result is not restricted to \(\pi/8\) phases. | The explicit product ansatz applies only while the \(P_j\) are not logical operators and \(t<t^{*}\). | closed |
| Per-gate magic calibration | Fig. 3 caption and the paragraph preceding it, PDF p. 4 | \(\mathcal M(T\lvert+\rangle)\approx0.4150\) and \(\mathcal M(\sqrt{T}\lvert+\rangle)\approx0.2075\), i.e. exactly half; the reachable stabilizer Rényi entropy at bond dimension one is halved accordingly. | The source does not tabulate magic for a general rotation angle, and it does not convert an arbitrary-angle gate into a "T-equivalent" count. | closed |
| Candidate-set reduction | Paragraph describing the greedy entanglement-cooling search, PDF p. 3; Acknowledgements, PDF p. 5 | The two-qubit Clifford search reduces to the quotient \(\tilde{\mathcal C}_2=\mathcal C_2/(\mathcal C_1\otimes\mathcal C_1)\), leaving 20 Cliffords to check at each step, with \(\lvert\mathcal C_1\rvert=24\) and \(\lvert\mathcal C_2\rvert=11520\). | The source does not claim the 20-element quotient is optimal for objectives other than reducing the entanglement entropy across the selected bond. | closed |
| Trotterized dynamics | Sec. "Consequences for Hamiltonian dynamics", PDF p. 4 | For \(H=\sum_{j=1}^{M}\omega_j P_j\) with \(M>N\) Pauli strings, one Trotter step already needs \(M\) non-Clifford gates, so "Hamiltonian dynamics will generically not admit a completely disentangled CAMPS representation, not even at early times." | This is stated as a consequence for generic Hamiltonians; the source does not prove it for every structured Hamiltonian. | closed |
| Ising confirmation | End Matter, Sec. "Hamiltonian dynamics", Eq. (8) and Fig. 4, PDF p. 5 | For a non-integrable one-dimensional Ising chain the transient state "can only be partly disentangled with Clifford circuits at very early times", and this "suggests that generic Hamiltonian dynamics does not profit from the CAMPS ansatz". | The tested sizes are \(N=4,8,16\); no larger system and no two-dimensional lattice is tested. | closed |
| First-step obstruction | End Matter, paragraph beginning "find Clifford unitaries that partially disentangle", PDF p. 6 | The state cannot be disentangled completely even immediately after the first time step, because preparing it already needs \(3N-1\) gates of the form \(e^{i\phi_j P_j}\). | The source gives no repair for this case beyond noting matchgate disentanglers as future work. | closed |
| Sampling cost | Paragraph beginning "Our results extend beyond Clifford + T circuits", PDF p. 5 | Pauli expectation values are polynomial-time, but sampling from \(O(N)\) output qubits appears to need exponential classical resources; sampling from \(O[\log(N)]\) qubits stays efficient. | No sampling claim is made for the regime \(t>t^{*}\). | closed |
| Two-dimensional lattices | Full-text scope | The tensor-network object throughout is a matrix product state in one dimension. | The source defines no projected entangled pair state, no two-dimensional routing, no bond-cap truncation certificate, and no detector or observable record bound. | missing |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Encoded state \(\lvert\psi\rangle=C(\lvert\varphi\rangle\otimes\lvert0\rangle^{\otimes(N-k)})\) and next phase gate \(e^{i\phi P}\) | Test whether \(P\) is a logical operator of the induced \([N,k]\) code | \(0\le k<N\); \(P\in\mathcal P_N\) | If not logical, a Clifford \(\tilde C\) with \(e^{i\phi P}\lvert\psi\rangle\propto\tilde C(\lvert\varphi\rangle\otimes\lvert x(\phi)\rangle\otimes\lvert0\rangle^{\otimes(N-k-1)})\) | Theorem 1 and Eq. (1), PDF p. 2 | complete |
| The two failure branches \(P\in\mathcal S\) and \(PS_j=-S_jP\) | Conjugate, relabel \(j=k+1\), and absorb the residual rotation into \(V=e^{i(\pi/4)LZ_{k+1}}\) and \(W=e^{i(\pi/4)L}\) | \(R=X_{k+1}\) without loss of generality after replacing \(C\) | Eq. (3c) with \(\lvert x(\phi)\rangle=e^{i\phi Y}\lvert0\rangle\) | Proof of Theorem 1, Eqs. (2)–(3c), PDF p. 2 | complete |
| A random \([N,k]\) stabilizer code and a uniformly random \(P\) | Count the \(2^{N-k}\) representatives of each of the \(4^{k}-1\) logical Paulis against \(4^{N}-1\) non-trivial strings | Deep random Clifford circuits generate random stabilizer codes | \(p_{k+1}=1-(4^{k}-1)2^{N-k}/(4^{N}-1)\) | Paragraph after the proof of Theorem 1, PDF p. 2 | complete |
| The per-step probabilities \(p_k\) | Form \(\Pr(t^{*})=(1-p_{t^{*}+1})\prod_{k=1}^{t^{*}}p_k\) and take the large-\(N\) limit | \(q\)-Pochhammer asymptotics as written | \(\langle\tau\rangle\approx1.607\), \(\sigma_\tau\approx1.6565\) | Paragraph after the proof of Theorem 1, PDF p. 2 | complete |
| A doped state at step \(s\le t\) | Apply Theorem 1 at each intermediate step | Each \(P_{s+1}\) is tested against the code induced by the current Clifford | \(\lvert\psi(s)\rangle=\tilde C_s(\lvert\mathrm{MPS}^{(k)}\rangle\otimes\lvert0\rangle^{\otimes(N-k)})\) with bond dimension at most \(2^{t-k}\) | Eq. (4) and the following paragraph, PDF p. 3 | complete |
| A two-qubit Clifford search step | Quotient by the local subgroup \(\mathcal C_1\otimes\mathcal C_1\) | The score is the entanglement entropy across the selected bond, invariant under one-qubit factors | 20 candidates per step | Paragraph on the entanglement-cooling search, PDF p. 3 | complete |

## Project application

The statements in this section are inferences drawn here, not claims made by
Fux et al.

1. **The disentangling criterion is code membership, not commutation.** An
   earlier working note in this repository proposed a criterion built on the
   symplectic Gram rank of the accumulated rotation axes — "all axes commute"
   as an exact condition for a perfect frame. That criterion is strictly weaker
   than Theorem 1 and its stated consequence is wrong: a commuting family of
   Pauli operators admits simultaneous Clifford diagonalization into the Z
   algebra, but when the family is **dependent** the images are multi-qubit Z
   strings, which are entangling. The commutation route is retracted; the
   source's logical-operator test replaces it.
2. **The constant does not transfer; the criterion does.** \(t^{*}\approx
   N-1.607\) is derived and measured for Clifford blocks built from \(2N^{2}\)
   two-qubit gates on random non-local pairs. A workload whose Clifford layers
   are shallow and geometrically structured does not inherit that number, and
   any budget claim for such a workload must be re-derived from Theorem 1
   directly.
3. **Workloads with more Pauli generators than qubits per step are excluded a
   priori.** The source's Trotter argument (PDF p. 4) and its Ising numerics
   (PDF pp. 5–6) together say that a schedule applying \(M>N\) non-Clifford
   phase generators per time step generically admits no completely disentangled
   representation, not even at the first step. A benchmark built that way tests
   the ansatz outside its established regime, and a negative result on it is
   not evidence against the method.
4. **Two independent local results reduce to prior art.** A local search that
   rediscovered 20 two-qubit Clifford coset representatives reproduces the
   quotient stated on PDF p. 3 and credited in the Acknowledgements on PDF p. 5.
   A local measurement of \(0.41504\) for the stabilizer Rényi entropy of one
   \(\pi/8\) phase gate reproduces \(\mathcal M(T\lvert+\rangle)\approx0.4150\)
   on PDF p. 4. Neither is a new finding.
5. **Nothing here extends to two dimensions.** The source is one-dimensional
   throughout. No projected entangled pair state, no routing on a lattice, and
   no bond-cap truncation certificate follows from it.

## Competing evidence, anomalies, and kill conditions

- arXiv:2602.15942 (already admitted) proves a complementary negative: beyond
  stabilizer settings no Clifford operation universally disentangles even one
  qubit from an arbitrary non-Clifford rotation. The two are consistent —
  Theorem 1 is conditional on the code test, and the negative result covers the
  unconditional case.
- **Anomaly to watch.** A workload can fail the \(M>N\) screen and still show
  complete disentangling at its first step through angle or axis structure that
  is special rather than generic. Observing that does not contradict the source,
  whose statement is about generic Hamiltonians, but it also does not license
  extrapolating to later steps.
- **Kill condition for any budget claim.** If a schedule's Clifford layers are
  not deep random and global, quoting \(t^{*}\approx N-1.607\) for it is
  unsupported. The claim dies unless the logical-operator test of Theorem 1 is
  evaluated on that schedule's own pulled-back operators.
- **Kill condition for any two-dimensional claim.** Any statement that this
  source supports a projected-entangled-pair-state method dies on the scope row
  above: the source defines no such object.
