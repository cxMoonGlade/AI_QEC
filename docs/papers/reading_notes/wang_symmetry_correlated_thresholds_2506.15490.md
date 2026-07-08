# Body-read — Wang, Yan, Xia & Wang, "Symmetry in Multi-Qubit Correlated Noise Errors Enhances Surface Code Thresholds" (arXiv:2506.15490v1; PRA 112, 062419 (2025))

> **Provenance.** Body-read by opus subagent 2026-07-02, targeted scope: **A9 adjudication** (does this
> paper compress our "collective flip = logical operator" component from (b) to (a)?). PDF downloaded
> `arxiv.org/pdf/2506.15490` (`outputs/papers/fetch_and_extract.py`, 4.14 MB, 7 pp) → text
> `outputs/papers/2506.15490.txt` (fitz). All §/Eq/Fig refs from that text; figure curves not
> pixel-extracted (the threshold NUMBERS are in the running text + captions, captured here). **Pending
> principal spot-verification.** Tags: **[paper]** = stated in the paper; **[ours]** = our inference for
> `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** SiYing Wang, Yue Yan, ZhiXin Xia, Xiang-Bin Wang (Tsinghua, State Key Lab of
  Low Dimensional Quantum Physics). Corresponding: xbwang@mail.tsinghua.edu.cn.
- **Venue / status.** arXiv:2506.15490v1 [quant-ph], 18 Jun 2025; dated Aug 25 2025 → PRA 112, 062419 (2025).
- **Type.** **Analytic threshold theory** (syndrome-based equivalence / stabilizer-group symmetry) +
  **Stim/PyMatching-2.0 numerical confirmation** of the rotated surface code under two families of
  **data-qubit⊗data-qubit spatially-correlated Z (or X) errors** from NNN coupling. Code-capacity +
  circuit-level.

## Executive summary [paper]
The paper's object is the **threshold `pth`** (and LER) of the surface code under **spatially-correlated
multi-qubit Pauli errors**, NOT the error RATE of any specific logical-failure channel. Its central
mechanism: when a correlated error's support is itself (or is a product with) a **stabilizer**, that error
is **syndrome-trivial AND acts trivially on the codespace** (a stabilizer fixes the state), so it costs the
decoder nothing → the threshold can be raised, in the limiting case to `pth = 1`. Two error families:
- **Type-1** (`q1`,`q2`): `k` Z errors on a **straight line** of data qubits (`E(ρ)=(1−p1)ρ+p1 Z₁…Zₙ ρ Z†…`).
- **Type-2** (`q3`,`q4`): Z errors on a **pair of adjacent** data qubits (`E(ρ)=(1−p2)ρ+p2 Z₁Z₂ ρ Z₂†Z₁†`).

Results:
- **Type-1, `d/j ∉ ℤ` (line length j does not divide d):** the symmetry subgroup `Ssym` **excludes logical
  operators**, giving **`Psuccess = 1`, `pth = 1`** (Eq 3–4). Numerically (Fig 5a, d=9,15,21) the 2-qubit
  Type-1 line errors are **"perfectly corrected without producing logical errors."**
- **Type-1, `d/j ∈ ℤ`:** threshold **= i.i.d. value 10.9%** (Eq 6); numerically 10.54% for 3-qubit lines.
- **Type-2 (adjacent pair):** `2pth(1−pth)=10.9% ⇒ pth = 5.8%` (Eq 5); numerically 4.7% (Fig 5b) — a
  **REDUCED** threshold.
- **Circuit-level (Fig 6):** with combined circuit noise, Type-1 line correlations give higher threshold /
  lower LER than Type-2. Practical upshot: choose qubit frequency detuning so correlations lie along lines
  (Type-1), not adjacent pairs (Type-2).

## The exact "P_success = 1" mechanism (§III.A — the load-bearing derivation) [paper]
This is the question the A9 adjudication hinges on. The mechanism is a **coset/symmetry argument on the
stabilizer group, NOT a rate calculation.**
- Errors `E={E1,E2,…}` all commute. Define `Ssys = C(G) ∩ E` (Eq 1), a subgroup of the centralizer `C(G)`.
  Under correlated (non-i.i.d.) noise, recovery need only be sought within cosets of `Ssys`. Key fact:
  **for `i ∈ Ssys`, `E†iE = i`.** [paper, §III.A] This generalizes the biased-noise symmetry `E†AvE=Av`,
  `E†BpE=Bp` of Tuckett et al. [refs 27,28].
- Success probability (Eq 2):
  `Psuccess = P(RE ∈ Ssys∩G) / P(RE ∈ Ssys∩C(G))`.
- **`Ssym` is built from products of stabilizers over square regions of side `k`** (Fig 2 shows k=2
  examples, e.g. `Z1Z2Z3Z10Z11Z15Z16Z17`). "Evidently, `Ssym` excludes logical operators when `d/j ∉ ℤ`
  (Eq 3). In this case, `Psuccess = 1` and the threshold of surface code is `pth = 1` (Eq 4)." [paper, verbatim]
- **Physical content (§III.B / Fig 3(b), verbatim):** "when errors occur simultaneously in both of the
  encircled pairs, **they generate a stabilizer, which does not change the state** of the surface code. In
  this scenario, there is no error in the virtual data qubit." And the paired-pair→virtual-qubit map gives
  virtual error probability **`2p2(1−p2)`** (the two-pairs-both-fire term cancels as a stabilizer).

**Adjudication-critical readings of the two decision questions:**

**(i) Does the paper state/compute the RATE at which correlated errors produce a zero-syndrome LOGICAL
error?** — **NO, and in fact the paper's mechanism is the OPPOSITE of ours.** Its syndrome-trivial
correlated errors are stabilizer(-adjacent), i.e. **they act trivially on the codespace** ("does not change
the state") — so they are **harmless** (raise `pth`), not silent logical failures. The paper never isolates
a rate of "zero-syndrome events that DO flip the logical." When a line error IS in `C(G)\G` it is a logical
error, but the paper handles this via the coset threshold, not via an isolated silent-logical-flip rate.
The one place logical operators enter is the exclusion condition `d/j∉ℤ` (Eq 3) — a **divisibility
geometry** statement, not a numeric rate of silent logical flips.

**(ii) Does the paper state/compute how the DETECTION-EVENT rate changes with correlation (at fixed
marginals)?** — **NO.** There is no detector/detection-event-rate analysis at all, and no fixed-marginal
construction. The paper works at the level of `pth` and end-of-run LER (Fig 5/6) with the decoder given the
correlated error model (PyMatching 2.0 "reassigns weights to the relevant edges for correlated errors,"
§IV) — i.e. a **correlation-AWARE** decoder, not a correlation-blind fixed-marginal one. So the specific
observable A9 flags as apparently-novel — the **detection-event-rate DECREASE at fixed marginals** — is
neither present nor contradicted here.

## Distance from common-mode Gaussian dephasing [ours, grounded in the paper's model]
- **The correlation model is discrete NNN-coupling Pauli correlation, NOT a common bath.** Type-1/Type-2
  are **fixed-support, fixed-probability** two-/k-qubit Pauli events on specific geometric sets (lines /
  adjacent pairs), motivated by NNN transmon coupling [refs 24=Harper-Flammia, 25=Tiurev, 26=Marxer]. This
  is a *phenomenological correlated-Pauli channel*, one geometric term at a time.
- **Common-mode Gaussian dephasing (our A9 mechanism) is different in kind:** a single shared fluctuator /
  collective `Σ g_j Z_j` couples ALL qubits simultaneously with a continuous (Gaussian-distributed) phase,
  producing a *weighted mixture over all even-weight Z strings* with double-factorial (1,3,15,…) moment
  structure (Clader 2101.11631). Wang et al.'s Type-1 is the closest analog (a coherent multi-Z string) but
  is (a) a single fixed line at a fixed rate, (b) analyzed for its THRESHOLD not its moment law, and (c)
  explicitly the *beneficial* (stabilizer-symmetric) case, not a silent-failure case. The paper cites
  common-bath work [refs 12 Novais-Mucciolo, 14 Hutter-Loss] only to contrast ("limited to the specific
  type of correlated error due to Bose baths"). **So this paper is ADJACENT to, not a treatment of, the
  common-mode Gaussian mechanism.**

## A9 verdict [ours]
**MAINTAIN (b). This paper does NOT compress our "collective flip = logical operator ⇒ zero syndrome"
component to (a).** Reasoning, tightly:
1. The paper's syndrome-trivial correlated errors are **codespace-trivial (stabilizer-like), i.e. benign**
   — they *raise* `pth`. Our component is the *opposite regime*: a zero-syndrome event that **does** enact a
   logical flip. The two are complementary faces of "correlated error hits `C(G)`," but the paper only
   develops the harmless (`Ssys∩G`) face quantitatively.
2. The paper gives **no isolated rate** for silent logical failures and **no detection-event-rate**
   analysis at fixed marginals — the two quantitative objects A9's provisional (b)/(c) split turns on.
3. What the paper DOES pin is a *threshold-geometry* fact (`d/j∉ℤ ⇒ pth=1`, Eq 3–4) and a
   *pair-cancellation* probability (`2p(1−p)`, Eq 5) — neither is our observable.

So A9's existing phrasing is right to place 2506.15490 under **(b) "folklore/framing that
line-correlated errors are correctable"** — the paper *frames* line-correlated errors as correctable (even
`pth=1`) but does not *quantify the silent-logical-flip rate*. It remains **prior framing to cite, not prior
art that owns our rate**. (The genuine (a) prior art for the moment-law enhancement is still Clader
2101.11631, per A9.)

## Decisive verbatim quotes [paper]
- **`P_success=1` mechanism:** "Evidently, `Ssym` excludes logical operators when `d/j ∉ ℤ`. (3) In this
  case, `Psuccess = 1` and the threshold of surface code is `pth = 1`. (4)" (§III.A, p3)
- **Stabilizer-trivial, not silent-failure:** "when errors occur simultaneously in both of the encircled
  pairs, they generate a stabilizer, which does not change the state of the surface code. In this scenario,
  there is no error in the virtual data qubit. Therefore, we conclude that the error probability for the
  virtual qubits is `2p2(1−p2)`." (§III.B, p4)
- **Numerical confirmation (no logical errors):** "the 2 qubit correlated errors of type-1 are perfectly
  corrected without producing logical errors, while the threshold for 3 qubit correlated errors of type-1 is
  10.54%." (Fig 5 caption, p4)
- **Model = discrete NNN Pauli, not bath:** "in superconducting quantum architectures of surface code, the
  Next-Nearest-Neighbor (NNN) coupling can cause correlation between data-data qubits and lead to correlated
  errors occurring simultaneously on two data qubits." (§II.B, p2)
- **Correlation-aware decoder (not fixed-marginal blind):** "PyMatching 2.0 generates a detector graph based
  on the input error model. It reassigns weights to the relevant edges for correlated errors, thus
  possessing the capability to handle correlated errors that produce two syndromes." (§IV, p4)

## Limitations [paper]
- **L1.** Threshold-level object only; no detection-event / detector-rate observable, no fixed-marginal
  construction, no silent-logical-flip RATE.
- **L2.** Correlation model is phenomenological fixed-support Pauli (Type-1 line / Type-2 pair), one term at
  a time, from NNN coupling — not a microscopic bath / collective Gaussian dephasing.
- **L3.** Analytic `pth=1`/`5.8%`/`10.9%` are code-capacity limits (infinite-size, boundary-independent);
  circuit-level numbers (Fig 5/6) are finite-d (d=9,15,21 and d=11,13,15).
- **L4.** Decoder is correlation-AWARE (PyMatching-2 reweighting), so the paper measures the *achievable*
  benefit of the symmetry, not the cost to a naive/correlation-blind twin — the misspecification framing our
  program uses is absent.
