+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:quant-ph/0006034"
source_version = "v2"
source_uri = "https://arxiv.org/abs/quant-ph/0006034v2"
source_artifact = "docs/papers/quant-ph_0006034v2.pdf"
source_sha256 = "9b9c6a7b00857728ae3550c7c24eaac69bdace5cb2b9986b66fddd38d74928bb"
title = "Entanglement capabilities of non-local Hamiltonians"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/DUR_0006034_ENTANGLING_RATE_AUDIT_2026-07-31.md"
audit_packet_sha256 = "b16c626bb8f20c088c06d5ff6bcdc375cb33beea0bd524c199f7a9bfd2aec85f"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_entangling_rate_source_review_2026_07_31"
admission_date = "2026-07-31"
visually_checked_pages = [1, 2, 3, 4]

[[relations]]
predicate = "defines"
object_id = "dur-entanglement-rate"
object_type = "observable"
object_label = "entanglement rate"
fact_id = "dur-rate-definition"

[[relations]]
predicate = "defines"
object_id = "dur-schmidt-parametrisation"
object_type = "method"
object_label = "Schmidt decomposition"
fact_id = "dur-schmidt-form"

[[relations]]
predicate = "measures"
object_id = "dur-binary-entropy-of-schmidt-coefficient"
object_type = "observable"
object_label = "entropy of entanglement"
fact_id = "dur-entropy-of-entanglement"

[[relations]]
predicate = "derives"
object_id = "dur-rate-factorisation"
object_type = "model"
object_label = "entanglement rate"
fact_id = "dur-rate-factorisation-fact"

[[relations]]
predicate = "derives"
object_id = "dur-sine-squared-trajectory"
object_type = "model"
object_label = "Schmidt coefficient"
fact_id = "dur-sine-trajectory"

[[relations]]
predicate = "derives"
object_id = "dur-hmax-from-singular-values"
object_type = "theorem"
object_label = "singular values"
fact_id = "dur-hmax-mu1-mu2"

[[relations]]
predicate = "limits"
object_id = "dur-product-start-suboptimal"
object_type = "limitation"
object_label = "product state"
fact_id = "dur-optimal-initial-entanglement"

[[relations]]
predicate = "defines"
object_id = "dur-standard-form-hamiltonian"
object_type = "model"
object_label = "standard form"
fact_id = "dur-standard-form"

[[relations]]
predicate = "supports"
object_id = "dur-ancilla-assisted-rate"
object_type = "concept"
object_label = "ancillas"
fact_id = "dur-ancilla-enhancement"

[[relations]]
predicate = "limits"
object_id = "dur-two-qubit-scope"
object_type = "limitation"
object_label = "two qubits"
fact_id = "dur-scope"
+++
# Full-text review — Dür, Vidal, Cirac, Linden, and Popescu, “Entanglement capabilities of non-local Hamiltonians”

## Source identity [paper_fact]
Fact ID: dur-source-identity
Source locator: Title page, author block, and arXiv stamp
PDF page: 1
Claim: The reviewed source is arXiv:quant-ph/0006034v2 by W. Dür, G. Vidal, J. I. Cirac, N. Linden, and S. Popescu, four pages, later published as Physical Review Letters 87, 137901.

The arXiv stamp on the left margin reads 20 Jun 2000. The affiliations are Innsbruck,
Bristol Mathematics, Bristol Physics, and BRIMS Hewlett-Packard. The artifact has four
pages and no appendix.

## Scope [paper_fact]
Fact ID: dur-scope
Source locator: Abstract, first sentence; Sec. “We consider two qubits”, PDF p. 1
PDF page: 1
Claim: The source analyses the entanglement capability of an arbitrary non-local Hamiltonian acting on **two qubits**, optionally supplemented by local unitary operations and by local ancillas.

The abstract states the object as the entanglement rate for evolution under a non-local
Hamiltonian, and reports that the optimal initial entanglement is independent of the
Hamiltonian. No many-body or circuit-level accumulation is considered.

## Entanglement rate definition [paper_fact]
Fact ID: dur-rate-definition
Source locator: Eq. (1) and the sentence introducing it
PDF page: 1
Claim: The entanglement rate is defined as \(\Gamma(t)\equiv dE(t)/dt\), the entanglement produced per time step of the non-local evolution.

The source notes that this quantity depends on the state \(|\Psi(t)\rangle\) not only
through its entanglement \(E\), and poses two questions: the state maximising the rate at
fixed \(E\), and the maximal achievable rate \(\Gamma_{\max}=\max_E\Gamma_E\) of Eq. (2).

## Schmidt parametrisation [paper_fact]
Fact ID: dur-schmidt-form
Source locator: Eq. (4) and Eqs. (5a)–(5b)
PDF page: 2
Claim: The two-qubit state is written in **Schmidt decomposition** as \(|\Psi\rangle=\sqrt{P}\,|\varphi,\chi\rangle+e^{i\alpha}\sqrt{1-P}\,|\varphi^\perp,\chi^\perp\rangle\) with \(\langle\varphi|\varphi^\perp\rangle=\langle\chi|\chi^\perp\rangle=0\) and \(P\le1/2\).

Equations (5a)–(5b) record that the reduced density operators satisfy
\(\rho_A|\varphi\rangle=P|\varphi\rangle\) and \(\rho_B|\chi\rangle=P|\chi\rangle\), so every
entanglement measure depends on the state only through the single Schmidt coefficient
\(P\).

## Entropy of entanglement [paper_fact]
Fact ID: dur-entropy-of-entanglement
Source locator: Eq. (6) and the sentence preceding it
PDF page: 2
Claim: Choosing the **entropy of entanglement** as the measure gives \(E(P)=-P\log_2 P-(1-P)\log_2(1-P)\), the binary entropy of the Schmidt coefficient.

The source notes that this quantity is the asymptotic ratio of maximally entangled pairs
distillable from, or needed to create, the state.

## Rate factorisation [paper_fact]
Fact ID: dur-rate-factorisation-fact
Source locator: Eqs. (9), (10), (11a), (11b), and (12)
PDF page: 2
Claim: The **entanglement rate** factorises as \(\Gamma=f(P)\,|h(\varphi,\chi)|\) with \(f(P)=2\sqrt{P(1-P)}\,E'(P)\) and \(h(H,\varphi,\chi)=\langle\varphi,\chi|H|\varphi^\perp,\chi^\perp\rangle\), and the maximum of the second factor is \(h_{\max}=\max_{\||\varphi\rangle\|,\||\chi\rangle\|=1}|\langle\varphi,\chi|H|\varphi^\perp,\chi^\perp\rangle|\).

Equation (9) supplies \(dP/dt=2\sqrt{P(1-P)}\,\mathrm{Im}[e^{i\alpha}\langle\varphi,\chi|H|\varphi^\perp,\chi^\perp\rangle]\)
from first-order perturbation theory on Eq. (8). Because \(f\) and \(|h|\) depend on
different parameters they can be maximised independently.

## Sine-squared trajectory [paper_fact]
Fact ID: dur-sine-trajectory
Source locator: Eq. (13) and the sentence introducing it
PDF page: 2
Claim: Driving the state with local operations so that it is optimal at every instant gives the **Schmidt coefficient** \(P(t)=\sin^2[h_{\max}t+\varphi_0]\), with \(P(0)=\sin^2(\varphi_0)\).

The source obtains this by solving the differential equation (9) and states that the
evolution of the entanglement then follows by substituting \(P(t)\) into \(E(P)\), so the
whole evolution is characterised by \(h_{\max}\) alone.

## Standard form of the interaction [paper_fact]
Fact ID: dur-standard-form
Source locator: Eqs. (15), (16), (17) and the surrounding paragraphs
PDF page: 3
Claim: Any two-qubit Hamiltonian can be brought by local unitaries to the **standard form** \(\hat H=\sum_{k=1}^{3}\mu_k\,\sigma^A_k\otimes\sigma^B_k\), where \(\mu_1\ge\mu_2\ge\mu_3\ge0\) are the sorted singular values of the matrix \(\gamma\) of Eq. (15).

The source states that the single-qubit terms \(\vec\alpha\) and \(\vec\beta\) in Eq. (15)
give no contribution to \(h_{\max}\) and can therefore be neglected, and that the local
operations \(U,V\) applied at the beginning and \(U^\dagger,V^\dagger\) at the end
implement the singular value decomposition of \(\gamma\).

## Interaction strength from singular values [paper_fact]
Fact ID: dur-hmax-mu1-mu2
Source locator: Eqs. (18), (19), (20)
PDF page: 3
Claim: For the standard form, \(h_{\max}=\mu_1+\mu_2\), the sum of the two largest **singular values** of the interaction matrix.

Equation (19) reduces \(h\) to \(\sum_k\mu_k-\sum_k\mu_k\langle\varphi|\sigma_k|\varphi\rangle^2\)
using the Cauchy–Schwarz inequality and \(|\chi\rangle=|\varphi\rangle\), and the maximum
is attained when \(|\varphi\rangle\) is an eigenstate of \(\sigma_3\).

## Optimal initial entanglement [paper_fact]
Fact ID: dur-optimal-initial-entanglement
Source locator: Eq. (14) and the paragraph following it
PDF page: 3
Claim: For the entropy of entanglement the maximal rate is reached not at a **product state** but at \(P_0\simeq0.0832\), the solution of \(\ln\frac{1-P_0}{P_0}=\frac{2}{1-2P_0}\), giving \(E(P_0)\simeq0.413\), and this optimal initial entanglement is independent of the Hamiltonian.

The source states plainly that "in order to increase the entanglement of a two-qubit
system in an optimal way, it is better to start with some initially entangled state rather
than a product state". Equation (21b) then gives \(\Gamma_E=f(P)h_{\max}\), with
\(f(P_0)\simeq1.9123\) at the optimum.

## Ancilla enhancement [paper_fact]
Fact ID: dur-ancilla-enhancement
Source locator: Eqs. (26), (27a), (27b), (28), (29) and the closing paragraph
PDF page: 4
Claim: Allowing each qubit to be entangled with local **ancillas** raises the effective strength to \(\tilde h_{\max}=\mu_1+\mu_2+\mu_3\); for \(\mu_1=\mu_2=\mu_3\) this gives \(\tilde\Gamma_{\max}\simeq1.3220\,\Gamma_{\max}\).

The enhancement is attained at \(\tilde P_0\simeq0.8515\), corresponding to
\(E(\tilde P_0)\simeq0.8415\), with the maximally entangled qubit-ancilla states of
Eq. (29) built from the Bell states. The source also records that
\(|\tilde f(\tilde P_0)|\simeq1.6853\) is smaller than \(f(P_0)\), so the gain comes
entirely from the larger \(\tilde h_{\max}\).
