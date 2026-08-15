# Claim audit — Kobayashi et al. process-tensor decoder

Date: 2026-08-05

## Fixed source object

| field | value |
|---|---|
| source | Fumiyoshi Kobayashi, Hidetaka Manabe, Gregory A. L. White, Terry Farrelly, Kavan Modi and Thomas M. Stace, *Tensor-network decoders for process tensor descriptions of non-Markovian noise* |
| identity | arXiv:2412.13739v1 [quant-ph], 18 December 2024; preprint |
| local artifact | `outputs/papers/2412.13739.pdf` |
| SHA-256 | `3d53154051bdc5a331238ba9c573ecff0237e4f52853e6f463e02090617b8ef1` |
| PDF checks | `%PDF-1.5` signature, terminal `%%EOF`, 1,577,697 bytes, 27 A4 pages, unencrypted |
| full-text traversal | PDF pp. 1–27, including all scientific sections, conclusion and references |
| visually checked pages | 1, 5–23 |
| reviewer | `codex-independent-source-review-kobayashi-2026-08-05` |

The PDF title page pins the local artifact to arXiv v1. Text extraction was regenerated from the
local PDF for navigation only; formulae, plots and tabulated values used below were checked on the
rendered PDF pages.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| M3 — process-tensor representation applied to QEC | Sec. 2.4, Eqs. (17)–(23), PDF pp. 6–8; Sec. 3.1, Eqs. (25)–(30), PDF pp. 8–9; Fig. 5, PDF p. 11 | A process tensor maps an interleaved control sequence to a conditional state or outcome probability. Stabilizer projectors and the syndrome-conditioned recovery are assembled into a tester with classical feed-forward. | It does not demonstrate a surface-code process tensor, repeated QEC cycles, noisy ancilla readout/reset, or a multicycle detector-record law. | **closed narrowly** for a multi-time representation and its single-round stabilizer-QEC instantiation |
| C1 — QEC-facing variables and decoder interface | Sec. 3.1, Eqs. (25)–(30), PDF pp. 8–9; Sec. 3.2, Eqs. (31)–(49), PDF pp. 10–12 | The QEC-facing variables are the ordered stabilizer-syndrome vector, a syndrome-conditioned logical Pauli choice, the recovered logical channel, and two source-defined logical-failure objectives. | It does not expose a repeated-round detector record, a circuit-level decoder graph, online decoding, or decoder access to hidden bath states. The channel-distance quantity in Eq. (49) is explicitly not a strict probability. | **closed narrowly** for the stated single-round ML interface |
| B1 — demonstrated benefit from memory-aware decoding or control | Abstract, PDF p. 1; Secs. 4.2–4.3, PDF pp. 16–22; Conclusion, PDF p. 23 | The source compares approximate and exact contractions of its process-tensor-conditioned decoder and reports when the approximation preserves the source's decoder performance. | It does not run a matched memory-aware versus memory-blind decoder/control comparison, so it does not establish an intervention benefit attributable to memory awareness. | **missing** |
| N1 — tensor-network computation demonstrated on persistent-memory repeated-QEC output | Sec. 4.1, Eqs. (50)–(52) and Figs. 7–8, PDF pp. 14–15; Sec. 4.2 and Fig. 9, PDF pp. 16–17; Sec. 4.3, Eqs. (53)–(56), Fig. 12 and Table 2, PDF pp. 18–22; Conclusion, PDF p. 23 | Exact tensor-network contraction is demonstrated for the five-qubit and Steane codes; an MPS approximation of the process tensor plus tester is compared with exact contraction for the Steane code. | The demonstrated task contains one sequence of stabilizer measurements, not repeated syndrome-extraction rounds. Multiple rounds, noisy measurements, circuit-based decoding and surface-code decoding are future work. | **closed only for single-round small-code TN computation; missing for repeated-QEC reach** |

## Representation, interface, computation and demonstrated reach

| layer | source object | exact locator | boundary |
|---|---|---|---|
| memory-bearing representation | Process tensor built from sequential system–environment interaction blocks, with one local bath qubit per data qubit and the bath traced after the sequence | Eq. (17), PDF p. 6; Eqs. (50)–(52), Fig. 7 and following construction paragraph, PDF p. 14; Fig. 8(a), PDF p. 15 | This is the representation carrying temporal dependence. It is not the decoder and is not a detector-error model. |
| QEC-facing abstraction | Direct projective measurement of each stabilizer generator, ordered syndrome vector, pure-error representative, candidate logical Pauli and syndrome-conditioned recovery | Eqs. (25)–(37), PDF pp. 8–11 | The syndrome operations act directly on data qubits; the numerical model does not include a circuit of measurement ancillas, faulty readout or reset. |
| reported QEC quantities | Hilbert–Schmidt success objective and its derived `p_fail`; channel 2-norm objective and its weighted aggregate; MPS estimate `p_est`; exact-process performance of approximate decoder `p_perf` | Eqs. (43)–(49), PDF p. 12; Eqs. (54)–(56), PDF p. 20 | Eq. (49) is not a probability under strict axioms, by the source's own statement. These quantities are not an ordered detector-record law. |
| exact computation | Tensor-network contraction implemented with quimb and cotengra/HyperOptimizer | Sec. 4.2, PDF p. 16 | “Exact” means contraction without the MPS truncation used in Sec. 4.3; the source does not provide an independent numerical implementation or certified error bound. |
| approximate computation | MPS representation of the process tensor and tester; MPO–MPS updates; maximum bond dimension and singular-value truncation | Sec. 4.3.1, Fig. 10 and Eq. (53), PDF pp. 18–20 | Accuracy depends on index ordering, noise strength and entanglement; no general approximation guarantee is supplied. |
| demonstrated code/scale | `[[5,1,3]]` code with four stabilizer measurements and `[[7,1,3]]` Steane code with six stabilizer measurements | Sec. 4.2 and Table 1, PDF pp. 16–18; Sec. 4.3.2, PDF p. 20 | The conclusion explicitly calls this “just single round syndrome measurement”; no code-distance scaling, threshold or repeated-QEC cycle study is demonstrated. |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Initial joint system–environment state and a sequence of CP control maps | Interleave each CP map with a joint unitary and trace the environment only at the end | CP maps act only on the system; joint unitaries act on system and environment | Process tensor acting on the control sequence and returning a conditional system state | Eq. (17), PDF p. 6 | complete |
| Process tensor, instruments and outcomes | Contract the Choi state of the selected CP maps with the process tensor | Instruments may be independent; a tester may retain classical or ancillary memory | Joint outcome probability and conditional state | Eqs. (18)–(23), PDF pp. 6–8 | complete |
| `[[n,k,d]]` stabilizer code | Measure the `n-k` stabilizer generators sequentially with projectors and collect the binary outcomes | Ideal direct projective syndrome instruments | Ordered syndrome vector and conditional data state | Eqs. (24)–(27), PDF pp. 8–9 | complete |
| Syndrome vector | Select a pure-error representative and a logical Pauli recovery; feed the recorded syndrome to the recovery leg of the tester | Recovery is classically conditioned on the full syndrome vector | Recovered logical state/channel candidate | Eqs. (28)–(41), PDF pp. 9–11 | complete |
| Candidate recovered channel | Append perfect syndrome measurement/decoding and compare with a logical identity channel | The perfect final decoding layer is an evaluation device; it is not part of the noisy syndrome sequence | `chi_HS` or `chi_CD`, optimized logical recovery and aggregate `p_fail` | Eqs. (42)–(49), PDF p. 12 | complete, with Eq. (49)'s source-stated non-probability limitation |
| Data qubits, one bath qubit per data qubit and nearest-neighbour data pairs | At each step apply the printed depolarising map, local Heisenberg system–bath unitary and nearest-neighbour `ZZ` crosstalk unitary; trace bath after the sequence | The same finite bath qubits are retained between the interleaved stabilizer operations | Concrete process-tensor TN used for numerical examples | Eqs. (50)–(52), Figs. 7–8(a), PDF pp. 14–15 | **source ambiguity:** Eq. (50) as printed is not trace preserving for `p_err>0`; no normalization repair is supplied in the PDF |
| Five-qubit code and the concrete process tensor | Contract the whole process tensor/tester network and optimize the logical recovery | quimb contraction order optimized by cotengra; one A100 40GB system is reported | Source-reported failure curves for four sequential stabilizer measurements | Sec. 4.2 and Fig. 9, PDF pp. 16–17 | reconstruction complete; numerical values remain quarantined by the Eq. (50) ambiguity and lack of independent execution |
| Steane code process-tensor/tester network | Represent the auxiliary, alternating data/bath and syndrome-classical indices as an MPS; apply MPO updates; cap bond dimension and discard singular values below `10^-8` | Index ordering is selected for the local data–bath pattern; truncation is heuristic | Approximate process-tensor/tester state | Sec. 4.3.1 and Sec. 4.3.2 opening, PDF pp. 18–20 | complete |
| Approximate and exact Steane tensors | Compute `p_est` from the approximate process and choose `tilde L`; evaluate that decoder against the exact process as `p_perf` | Exact TN contraction is available for the seven-qubit instance | Approximation-versus-reference curves and timing table | Eqs. (54)–(56), Fig. 12 and Table 2, PDF pp. 20–22 | complete as a source-reported comparison, not independently validated |

## Printed depolarising-map ambiguity

Equation (50), visually checked on PDF p. 14, prints

`E_dep(rho,p_err) = (1-p_err) rho + p_err sum_{sigma in {X,Y,Z}} sigma rho sigma†`.

For a trace-one input, the printed right-hand side has trace `1+2 p_err`, because each of the
three Pauli-conjugated terms has trace one. It therefore cannot be the CPTP single-qubit
depolarising channel that the surrounding prose says it is when `p_err>0`. The PDF does not state
whether the intended coefficient of the sum is `p_err/3`, whether `p_err` denotes a per-Pauli rate,
or whether the executed code uses a different convention. Consequently:

- the structural representation, QEC interface and TN/MPS construction remain source-supported;
- the direction of the source-reported Fig. 9/Fig. 12 comparisons may be reported only as what the
  paper states;
- the numerical values and claims of normalized channel execution are not admissible without a
  separately pinned implementation or corrected source object.

This audit leaves Eq. (50) exactly as printed and does not infer which, if any, normalized channel
was executed. No implementation repository was inspected for this audit.

## Numerical findings at their source-supported strength

- Figure 9 reports that increasing either local system–bath coupling `J_NM` or `ZZ` crosstalk
  coupling `J_CT` raises the five-qubit code's plotted logical-failure quantities. The authors also
  state that a fair comparison of non-Markovian and crosstalk effects must account for the extra
  noise introduced by coupling to bath qubits, and that concrete conclusions require care.
- Figure 12 and Table 2 compare MPS bond caps `128`, `256`, `512` and `1024` with untruncated TN
  contraction for the Steane instance. Moderate bond dimension is faster and close to the exact
  source values in the low-noise table; at high noise, larger bond dimensions can take longer than
  the exact contraction.
- PDF p. 22 states that low MPS state fidelity does not by itself imply decoder-performance loss:
  strong non-Markovian coupling shows a clear performance decrease, whereas the plotted strong
  depolarising or crosstalk regions do not show the same deterioration.

These are source-reported small-instance results. They do not establish threshold scaling,
surface-code reach, a hardware observation, a microscopic attribution in a device, or transfer to
other codes and decoders.

## Project application

For a reader-facing comparison of modelling approaches, this source can support one concrete row
only if the row keeps four columns distinct:

1. **representation:** a process tensor generated by a finite retained bath;
2. **QEC-facing interface:** ideal sequential stabilizer outcomes and a syndrome-conditioned logical
   Pauli recovery;
3. **computation:** exact TN contraction or MPS/MPO approximation of the process tensor plus tester;
4. **demonstrated reach:** one syndrome-measurement round of the five-qubit and Steane codes.

The paper must not be used as evidence that PT-MPO or influence-functional methods were executed in
its QEC examples. In the conclusion, the authors identify PT-MPO as a known open-system method but
say it is unsuitable for their large local memory dimensions; their implemented approximation is an
MPS representation of the combined process tensor and tester.

The source does not support a claim of memory-aware-decoder benefit because it does not include a
matched memory-blind decoder arm. It also does not close a repeated-QEC tensor-network row: multiple
rounds of noisy syndrome measurement, circuit-based decoding and surface-code decoding are stated
future work on PDF p. 23.

## Competing evidence and kill conditions

- The source cites the strategic-code formalism of Tanggara, Gu and Bharti as prior formal work. Its
  own incremental contribution is a process-tensor-conditioned ML decoder plus small-code numerical
  implementations; it does not establish that all process-tensor QEC problems have this cost or
  scale.
- Kill any use that labels the four or six sequential stabilizer measurements as four or six QEC
  cycles. The conclusion explicitly limits the construction to a single syndrome-measurement round.
- Kill any use that describes the numerical examples as surface-code, circuit-level, faulty-readout,
  reset-inclusive or hardware demonstrations.
- Kill any benefit claim unless a separate source provides a matched memory-aware versus
  memory-blind intervention comparison.
- Kill any quantitative reuse of Fig. 9, Fig. 12 or Table 2 until the Eq. (50) normalization
  ambiguity is resolved against a pinned executable implementation or corrected primary source.
- Kill any statement that Eq. (49) is a literal logical-failure probability; the source says that
  this 2-norm aggregate does not satisfy strict probability axioms.
- Kill any generic scalability guarantee from the MPS results. PDF p. 20 says there is no guarantee
  that MPS represents larger, more strongly noisy or more deeply measured systems well.

## Source-local verdict

- read_status: complete
- evidence_status: persisted
- M3: closed narrowly for process-tensor representation plus a single-round stabilizer-QEC tester
- C1: closed narrowly for the ordered-syndrome/ML-logical-recovery interface used in the paper
- B1: missing; no matched memory-aware intervention benefit is demonstrated
- N1: closed for single-round five-qubit/Steane TN computation, missing for persistent-memory
  repeated-QEC records or logical output
- quantitative result status: source-reported only and quarantined for unconditional reuse because
  Eq. (50) is not trace preserving as printed
- admission review: independently source-checked against the fixed PDF by
  `codex-independent-source-review-kobayashi-2026-08-05`
