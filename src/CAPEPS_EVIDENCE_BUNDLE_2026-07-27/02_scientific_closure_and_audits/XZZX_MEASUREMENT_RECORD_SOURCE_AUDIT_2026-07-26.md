# XZZX measurement and detector source audit

Date: 2026-07-26
Status: source-only second pass complete

## Audited sources

| source | pinned artifact | SHA-256 | pages |
|---|---|---|---:|
| Bonilla Ataides et al., *The XZZX surface code* | arXiv:2009.07851v3 | `4b4f244f949b0d1e862ff44e6328f33abab93654cd64a7e5f1ada0467ccaafd7` | 16 |
| Darmawan et al., *Practical quantum error correction with the XZZX code and Kerr-cat qubits* | arXiv:2104.09539v2 | `809149344e94392151a3935a4ec9615930e19d7aee414a9d022a7ac07036e5e5` | 21 |

The primary reviewer read both pinned full texts and visually checked Bonilla PDF pp. 2, 6, and
10 and Darmawan PDF pp. 3, 7, 10, and 17. A separate source-only reviewer independently read both
full texts, checked the same hashes, and visually checked those pages. The second pass was given
only the source questions: XZZX geometry, the ancilla parity circuit, repeated-round defect
semantics, reset/re-preparation, and source-local limits.

## Source findings

### XZZX geometry

Bonilla PDF p. 2, Fig. 1 and caption place data qubits on square-lattice vertices and define each
bulk face by one two-X/two-Z check. The same figure shows a truncated boundary check and a
rectangular rotated-lattice boundary choice. It does not enumerate a complete d3 or d5 circuit
coordinate table.

Darmawan PDF p. 3, Sec. II and Fig. 2(a) write the bulk check as
`S_f = X tensor Z tensor Z tensor X`. The visual placement is X on the left and right sites and Z
on the upper and lower sites. Its standard-layout weight-three boundary discussion must not be
substituted for the separate rotated n=9 layout, whose open boundaries are weight two.

### Ordered ancilla parity shell

Darmawan PDF p. 3, Fig. 2(b) and adjacent text prepare a face ancilla in `|+>`, apply the ordered
shell

```text
CZ(A,D1), CX(A->D2), CX(A->D3), CZ(A,D4),
```

then measure the ancilla in the X basis. Fig. 2(a) fixes the spatial D1--D4 order. A missing
boundary neighbor leaves its slot idle. The source says that every second face of the rotated n=9
layout swaps the two CX slots to mitigate hook errors, but it does not publish a complete
eight-check coordinate/schedule table.

Bonilla PDF p. 6 supplies only a leading-order verbal version of this shell as motivation for a
phenomenological measurement-flip rate. It does not supply gate order, control/target assignment,
or a selective instrument.

### Repeated-round defect

Bonilla PDF p. 6, Fig. 5 and caption define a spacetime defect when a stabilizer result differs
from its preceding result. Darmawan PDF p. 3, Sec. II.B states the same rule as
`S_f(t-1) S_f(t) = -1`.

Mapping signs to bits makes this a consecutive-outcome XOR. Neither source defines the project's
first-round reference row or its `d[0]` convention. Those are fixture fields, not paper facts.

### Measurement and re-preparation

Darmawan PDF pp. 6--7, Sec. III.B.4 and Fig. 6 give an X-basis projective readout. Conditional on
the homodyne result, the measured ancilla is projected to `|0>` or `|1>`; inverse rotations then
prepare the corresponding `|+>` or `|->` for the next syndrome round. This is branch-conditioned
re-preparation, not a branch-erasing reset to one fixed X eigenstate.

The fixed-state reset used by the proposed adapter is instead grounded by Ghosh et al.,
arXiv:1306.0925v2, PDF p. 2, Fig. 1 and caption: every repeated ancilla-assisted measurement cycle
begins by resetting the ancilla to `|0>`. The selective branch probability and normalized
post-measurement state are separately grounded by Czajkowski and Grilo, arXiv:2101.08313v2,
Sec. 2.2, Eq. (1), PDF p. 5.

## Operation replay

| source input | source operation | source output | replay | boundary |
|---|---|---|---|---|
| four data qubits and `|+>` ancilla | ordered two-CZ/two-CX shell, X readout | one XZZX check sign | matched to Darmawan Fig. 2 | no complete rotated coordinate table |
| check signs at `t-1,t` | multiply signs | defect iff product is `-1` | matched to Darmawan Sec. II.B | first-round anchor absent |
| measured Kerr-cat ancilla branch | inverse readout rotations | corresponding `|+>` or `|->` | matched to Darmawan Fig. 6 | not fixed-state reset |
| repeated transmon ancilla cycle | reset to `|0>`, H, CZ, H, readout | next recorded outcome | matched to Ghosh Fig. 1 | only one data--ancilla check |
| residual Kerr-cat leakage | suppress, then omit from code simulation | qubit circuit-level channel | matched to Darmawan p. 10 | no retained leakage Record |

## Source-local limitations and anomalies

- Bonilla's repeated-measurement result is phenomenological: independent Pauli data errors and an
  independent outcome flip. Its circuit paragraph is not the simulated object.
- Darmawan's physical carrier is a bosonic Kerr-cat. PDF p. 10 explicitly suppresses and then
  neglects residual leakage in subsequent surface-code simulations; PDF p. 13 also makes the small
  exact code simulation strictly two-level.
- Darmawan's fixed-`|+>` circuit shell and its Fig. 6 branch-conditioned `|+>`/`|->`
  re-preparation leave a feedback or frame convention unstated.
- Fig. 6 calls the measured upper wire a data qubit, while the surrounding syndrome-extraction
  discussion uses the same operation for the ancilla. No data reset is inferred from the caption.
- Darmawan Appendix B, PDF p. 18 contains an S-gate comparison sentence whose direction conflicts
  with the preceding mechanism and Fig. 10. It is irrelevant to the parity shell and is preserved
  as a likely textual reversal rather than silently repaired.

## Project application boundary

The sources support the XZZX operator geometry, an ordered ancilla parity shell, consecutive-round
defect semantics, projective measurement, and explicit ancilla reset/re-preparation components.
They do not support a complete rotated d3/d5 coordinate schedule, an arbitrary first-round
detector anchor, a PEPS implementation, a full joint Record guarantee, or retained leakage.

The implementation target must therefore bind its exact coordinates, gate order, measurement
keys, reset flags, and absolute detector/observable XOR rows to the already corruption-tested
neutral Stim fixture. The PEPS adapter remains the object under test. No source claim is made that
finite PEPS bond dimension preserves the Record law.
