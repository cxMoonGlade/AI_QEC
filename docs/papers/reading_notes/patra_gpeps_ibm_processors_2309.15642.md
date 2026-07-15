# Reading note (精读): Patra et al., “Efficient tensor network simulation of IBM’s largest quantum processors”

> **Provenance (2026-07-14): pinned-PDF full read.** The user supplied the unversioned
> arXiv PDF URL; this note pins the then-current `arXiv:2309.15642v3` rather than silently
> leaving the version floating. The seven-page PDF, every equation, every figure/caption, and
> Appendices A–C were read; load-bearing formulae and plots were also checked against rendered
> PDF pages. Local artifacts:
> [`2309.15642v3.pdf`](../../../outputs/papers/2309.15642v3.pdf),
> [`2309.15642v3.txt`](../../../outputs/papers/2309.15642v3.txt), and
> [`provenance.json`](../../../outputs/papers/2309.15642v3.provenance.json).
>
> **Integrity:** PDF SHA-256
> `aafacaf117d5a3a536760900800f473ef2c806f0c4485838e24db44712bc7fc6`;
> 7 pages; 30,740 extracted characters; extraction by PyMuPDF.
>
> `read_status: complete`  
> `evidence_status: persisted`  
> `source_role: primary for the reported heavy-hex gPEPS experiment; not a primary source for
> the update formulae it cites, open-system evolution, or QEC records`

## Metadata [paper]

- **Authors:** Siddhartha Patra, Saeed S. Jahromi, Sukhbinder Singh, Román Orús.
- **Source:** [arXiv:2309.15642v3](https://arxiv.org/abs/2309.15642v3), submitted
  27 September 2023; v3 dated 2 April 2024.
- **Publication:** *Physical Review Research* **6**, 013326 (2024).
- **Type:** primary numerical methods/application paper: noiseless real-time pure-state gPEPS
  simulation of a kicked-Ising circuit on IBM heavy-hex graphs.
- **Question assigned here:** Can this paper supply a method, formula, control, or falsifier for
  the current full-`d×d` qutrit PEPS trajectory and its full multi-round QEC-record gate?

## Executive summary

The paper shows that a particularly cheap combination—graph PEPS (`gPEPS`), simple-update
truncation, and a mean-field observable environment—can be extremely accurate for the authors’
specific problem: closed, unitary kicked-Ising evolution from a product state on IBM’s locally
tree-like heavy-hex graph. At five Trotter steps, the average magnetization agrees with an
available light-cone exact result at about `10^-15`; deeper and higher-entanglement regimes need
larger bond dimension and do not always show saturation. The authors themselves attribute the
success to the absence of nearby short loops and short correlation length away from the critical
region (Appendix C).

For this repository the result is useful as an **engineering baseline and an applicability
falsifier**, not as a solution to the active carrier problem. Our square/rotated-square QEC
geometry has short four-cycles; our object is a qutrit trajectory with Kraus evolution,
selective stabilizer measurements, reset, and a complete multi-time detector/observable record.
None of those objects occurs in the paper. Its most important project implication is therefore
negative: the spectacular heavy-hex numbers do not justify simple update or a mean-field/BP
environment for our loopy full-record product.

## Selection and evidence coverage

| Assigned evidence row | Where checked | Result |
|---|---|---|
| Scientific object and evolution | Eq. (1)–(3), pp. 1–2 | Closed spin-1/2, pure-state, unitary kicked Ising |
| State representation and update | §III, p. 2 | gPEPS + simple update; implementable equations deferred to Refs. 15–19 |
| Observable contraction | §III–IV.A, Appendix B | mean-field/local environment; special Clifford rewrite for high-weight observables |
| Accuracy/convergence | Figs. 2–7, pp. 2–6 | exact shallow oracle in a limited arm; otherwise bond-dimension comparisons or external TN estimates |
| Geometry/failure regime | Appendix A and C, pp. 6–7 | critical/long-correlation and short-loop limitations explicitly exposed |
| Open-system/qutrit/QEC record bridge | whole paper | absent |
| FET/NTU/WTG or record-faithful truncation | whole paper | absent |

No competing source was supplied with the request. For project-level contradiction checks this
note was compared with the current binding simulator documents, ADR 0011, the truncation
literature closure, and the existing Rudolph–Tindall planar-PEPS note. Those project documents
do not change what this paper proves; they determine whether it transfers.

## Notation ledger

| Paper symbol | Meaning in the paper | Closest project object | Transfer warning |
|---|---|---|---|
| `m` | number of spin-1/2 sites | number of physical qutrit sites | local dimension differs: 2 versus 3 |
| `n` | applications of one kicked-Ising Trotter unitary | circuit depth/round count only loosely | no measurement/reset between steps |
| `theta_h` | transverse-field angle in Eq. (2) | no direct simulator knob | not a noise, leakage, or schedule parameter |
| `chi` | gPEPS state bond dimension and truncation cap | PEPS state-bond cap | distinct from boundary-MPS contraction `chi_b` |
| `U(theta_h)` | closed-system unitary Trotter step | one fragment of a trajectory step | no Kraus branch or selective instrument |
| `M_z`, `W_10`, `W_17` | terminal expectation values | terminal/local observable only | not a joint detector/observable record law |
| BP regauging | optional PEPS gauge update after a Trotter step | BP loop diagnostic is the nearest current feature | repository BP is read-only diagnostic, not this regauging operation |

## Scientific operation reconstructed [paper]

The paper’s model is

`H = -J sum_<i,j> Z_i Z_j + h sum_i X_i` (Eq. 1),

with the first-order kicked unitary

`U(theta_h) = [prod_<i,j> exp(i pi Z_i Z_j / 4)]
               [prod_i exp(-i theta_h X_i / 2)]` (Eq. 2),

and state `|psi(theta_h,n)> = U(theta_h)^n |0>^⊗m` (Eq. 3). The graph is the finite
127/433/1121-site heavy-hex connectivity, or an infinite heavy-hex lattice with a ten-site unit
cell. The state is advanced with simple update at bond dimension `chi`; expectation values use a
mean-field environment. An optional arm re-gauges with BP after each Trotter step.

The paper does **not** print the local simple-update tensor equations, the BP message equations,
stopping tolerances, gauge convention, or code. Those details are delegated to earlier sources,
so this paper alone is not an implementation-fidelity reference for any update routine.

### Operation replay

| Input | Transformation | Assumption/control | Output | Source-local status |
|---|---|---|---|---|
| product state on heavy-hex | repeat Eq. (2), truncate gPEPS with simple update | low enough inter-bond entanglement | approximate pure state | described, not implementable from this paper alone |
| approximate gPEPS | contract a product/mean-field environment | environment correlations are weak | local expectation | described, uncontrolled outside tested regime |
| same five-step circuit | optionally BP-regauge after each step | BP improves conditioning/gauge | local observables | tested: no accuracy gain; runtime rose from about 2 s to 9.2 s/point |
| weight-10/17 Pauli string | conjugate through a Clifford circuit, Eqs. (B1)–(B4) | exact Clifford identity | local `Z` read after extra evolution | algebraically matched |
| long evolution | scan `chi`, compare to maximum reachable `chi` | observed convergence indicates adequacy | magnetization curve | internal convergence only, not an independent oracle |

## Results and what they actually establish [paper]

1. **Shallow, local heavy-hex arm.** For 127 sites and five Trotter steps, Fig. 2 compares
   magnetization against a light-cone exact value. The reported absolute error is about `10^-15`
   at `chi=32`, with about two seconds per data point on the stated desktop. This is the strongest
   independent accuracy evidence in the paper.

2. **BP regauging is not the source of that success.** The independent five-step BP-regauged arm
   does not improve accuracy and raises the average time to 9.2 seconds (§IV.A, p. 2).

3. **Higher-weight observables are not contracted generically.** Appendix B exploits the
   Clifford point to rewrite weight-10/17 strings as a one-site `Z` expectation after additional
   exact conjugation, Eqs. (B1)–(B4). This is a valuable structural control, but it bypasses the
   generic loopy high-weight contraction problem.

4. **Depth and interaction strength expose the boundary.** At 20 steps the Clifford endpoints
   are exact at `chi=64`, while `chi=64` is reported reliable only through roughly
   `theta_h <= 3pi/16`; increasing `chi` improves much of the remaining range. At
   `theta_h=1.0`, Fig. 3(c) shows no clear saturation even through `chi=512`.

5. **The critical region is non-monotone.** Appendix A identifies a critical point near
   `theta_h≈0.6`, where the correlation length diverges. Lower `chi` can appear more accurate
   than higher `chi`; the authors explicitly say simple update plus local measurement struggles
   there. A single monotone bond scan is therefore not a safe certificate.

6. **Largest-system “errors” are internal.** For 37–39 steps on 127/433/1121 sites, Figs. 5–6
   plot relative differences from the largest *reachable* bond dimension (`560/370/270`), not
   from an independent exact state or record oracle.

7. **Geometry is load-bearing.** Appendix C states that a square-lattice edge sees loops beyond
   first neighbours, whereas the heavy-hex edge sees them only beyond fifth neighbours. The
   authors’ explanation for simple update’s performance is explicitly “locally tree-like plus
   short-range correlation,” not a general theorem about 2D PEPS.

## Mapping to the live simulator [ours]

| Paper object | Current repository locus | What transfers | What does not transfer |
|---|---|---|---|
| graph-native gPEPS | `carrier/peps/state.py::PepsState` | motivation to match TN to geometry | current state is a strict `d×d` square layout, not an arbitrary graph |
| simple-update truncation | `carrier/peps/trajectory.py` and PEPO SVD/NTU helpers | cheap deliberately weak baseline | cannot replace environment-aware NTU/FET or certify records |
| mean-field local readout | `carrier/peps/contraction.py` | possible negative control | our Born reads change later conditional branches; not merely terminal reporting |
| BP regauging | `carrier/peps/diagnostics.py::eps_l` is the nearest object | BP/loop sensitivity deserves monitoring | current BP is a diagnostic fixed point, not a state-regauging implementation |
| state bond `chi` scan | `bond_profile`, truncation policy | retain multi-`chi` stress tests | do not conflate with contraction boundary dimension `chi_b` |
| Clifford high-weight rewrite | exact leak-off/dense anchors | useful corruption/structural control when an exact identity exists | cannot certify leaky, non-Clifford, multi-time record branches |
| local heavy-hex observable | `terminal_obs_prob` only loosely | terminal-observable baseline | not the full joint `{detector, observable}_{1:R}` product |

The paper’s `gPEPS` is a **Schrödinger-picture pure state**. It must also not be confused with
the repository’s doubled-wire qutrit density-matrix `carrier/pepo/dynamics.py`, nor with the
Heisenberg-observable PEPO discussed in other IBM benchmark papers.

## Can it help us?

### Yes, in bounded ways

- Add or retain simple update / mean-field as a **weak negative-control baseline**, never as the
  production accuracy argument.
- Report state bond `chi`, boundary contraction `chi_b`, and the loop diagnostic separately.
- Use a Clifford/leak-off identity as a de-circularized corruption falsifier when the scheduled
  circuit permits one.
- Treat geometry and correlation length as explicit carrier-selection variables. If a future
  product really targets heavy-hex or another locally tree-like graph, arbitrary-graph gPEPS
  becomes much more relevant.
- Use the paper’s non-monotone critical-region behaviour as a warning: apparent `chi`
  convergence or one better low-`chi` point is not sufficient evidence.

### No, it does not close the active blockers

- no qutrit leakage or computational/leakage coherence;
- no density matrix, Kraus map, Lindblad/GKSL evolution, or MCWF trajectory;
- no selective mid-circuit stabilizer measurement or ancilla reset;
- no multi-round syndrome/detector record and no logical-error-rate observable;
- no FET, WTG, NTU, ALS, or stabilizer-entropy formula;
- no theorem or empirical bridge from local/state truncation to full-record TV/KL/LER;
- no diagnosis of the current FET stabilizer-entropy mismatch.

Consequently it does not change the current `single-wire full-d×d PEPS + NTU/FET + exact-d3
full-record gate` direction. Replacing the current truncation with simple update would weaken the
evidence rather than repair the blocker.

## Failure and disconfirmation ledger

| Tempting inference | Paper evidence that defeats it | Project consequence |
|---|---|---|
| “`10^-15` means simple update is generally exact” | exact arm is five-step, local, heavy-hex, short-correlation | do not transfer to square QEC records |
| “larger `chi` monotonically improves accuracy” | Appendix A gives non-monotone critical-region behaviour | require independent oracle and multiple diagnostics |
| “large-qubit success proves scalable QEC fidelity” | largest runs are closed/unitary and internally compared to max reachable `chi` | qubit count is not a record-faithfulness certificate |
| “BP makes the update controlled” | BP did not improve the tested observable; BP is exact only on trees in general | BP remains a diagnostic/baseline |
| “high-weight strings were contracted accurately” | authors map them to a local read using a Clifford identity | do not infer generic high-weight/full-record contraction quality |

**Project kill condition:** if this paper were proposed as direct support for a production update,
the claim must fail unless an independent exact small-system experiment shows the same update
preserves the *entire joint record distribution* under the project’s fixed schedule, leakage, and
measurement/reset semantics. The paper contains no such experiment.

## Source-local closure

| Assigned row | Status | Reason |
|---|---|---|
| Heavy-hex kicked-Ising gPEPS result | `closed` | direct primary experiment, with stated model and observables |
| Five-step magnetization accuracy | `closed` | independent light-cone exact comparison |
| Deep/largest-system exactness | `partial` | mostly convergence to largest reachable `chi`, no independent oracle |
| Implementable simple-update/BP equations | `missing` | delegated to prior references |
| Generic square-lattice applicability | `missing / adverse evidence` | Appendix C explicitly identifies earlier loops on square lattices |
| Open-system/qutrit/QEC applicability | `missing` | scientific object absent |
| Truncation to full-record/LER bridge | `missing` | observable and metric absent |
| Current FET-entropy blocker | `missing` | method absent |

## Trust and open questions

- Trust is **high** for the stated heavy-hex model, shallow exact comparison, and the explicit
  geometry/failure observations.
- Trust is **moderate** for deep-run accuracy because convergence is often internal rather than
  checked against an independent oracle.
- Transfer trust to the current QEC carrier is **low** because geometry, local dimension,
  dynamics, measurement semantics, and target observable all change.
- If arbitrary-graph support becomes a product requirement, the next evidence step is to read
  the primary gPEPS/simple-update references and a modern arbitrary-planar implementation—not to
  reconstruct the algorithm from this seven-page application paper.

## Tags

`gPEPS` · `simple update` · `belief propagation` · `heavy-hex` · `kicked Ising` ·
`geometry-matched tensor network` · `bond-dimension convergence` · `critical failure regime` ·
`no open-system bridge` · `no QEC-record bridge`
