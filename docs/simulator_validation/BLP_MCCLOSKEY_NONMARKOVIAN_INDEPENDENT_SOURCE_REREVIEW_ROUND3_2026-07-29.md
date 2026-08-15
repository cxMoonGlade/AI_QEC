# BLP / McCloskey–Paternostro non-Markovianity — independent source-only rereview, Round 3

Date: 2026-07-29
Review basis: the two fixed PDFs, the newly repaired source notes, and their named audit packets only
Verdict: **PASS**

This is a fresh semantic source-only rereview of all seven repairs required by
Round 2. Both fixed PDFs were reopened through a new temporary extraction,
read in full, freshly rendered, and inspected directly at every load-bearing
equation, conclusion, and figure. Candidate prose was not treated as source
evidence. No candidate note, audit packet, PDF, or corpus manifest was edited
by this review.

## 1. Exact reviewed identities

| object | SHA-256 | independent check |
|---|---|---|
| `docs/papers/0908.0238v2.pdf` | `9e05b98a5b6a902be4fa8d4d2662b7e9b7592d150ddef6bf74a8d6e9f9bf4553` | valid four-page fixed PDF; freshly extracted and rendered |
| repaired BLP note | `963430fc7ea0bf2ed6810c123e56bc0a5d157942c3a6cf822c8db66425bc4f9f` | source and audit hashes resolve |
| BLP audit | `4151228066fc7e6e195c43debc3435dce7484b8169ab46352adfd356a2fa6b19` | exactly equals the note's `audit_packet_sha256` |
| `docs/papers/1402.4639v3.pdf` | `eee6e79e1f217b1c041ae524867c2785c773a9eb9050020927d1b485a0a846cc` | valid seven-page fixed PDF; freshly extracted and rendered |
| repaired McCloskey–Paternostro note | `e2534e34945a329cfc98a5e59db19caeafbdbc327ca9f44770f0240643f81c4b` | source and audit hashes resolve |
| repaired McCloskey–Paternostro audit | `4b28940ef532ff180f1e83a558ab5db3bee8de142b8283e17117712bb548577e` | exactly equals the note's `audit_packet_sha256` |

Fresh temporary extraction root:
`/tmp/deep-read-paper.t4cb5f2a`. The extractor independently returned the
same two source hashes, four pages and 19,461 text characters for BLP, and
seven pages and 30,888 text characters for McCloskey–Paternostro.

Fresh direct visual checks covered BLP PDF pages 2–4 and
McCloskey–Paternostro PDF pages 2, 3, 5, and 6. The remaining pages were
traversed in the full-text read.

## 2. Round-2 required-repair disposition

| Round-2 Section 9 item | Round-3 source check | disposition |
|---|---|---|
| define BLP \(\sigma\) as the trace-distance rate and reserve “positive” for \(\sigma>0\) | Eq. (10), PDF p. 2, defines the derivative without a sign restriction; the following text separately imposes \(\sigma>0\) for the witness | **PASS** |
| split BLP Eq. (11), p. 2, from Eq. (12), p. 3 | the note now has separate `blp-integrated-measure` and `blp-positive-interval-endpoint-sum` records with exact pages | **PASS** |
| narrow `blp-optimization-limit` to the complete-reduced-dynamics requirement on p. 4 | the record now cites only the concluding paragraph, PDF p. 4, and states only that requirement | **PASS** |
| narrow `mp-retention-threshold` to Fig. 4 and name \(\delta\) precisely | the record now cites Fig. 4 and Sec. II.A, PDF p. 5, and calls \(\delta\) the intra-environment interaction strength | **PASS** |
| restrict `mp-interaction-strength-dependence` to displayed \(\delta\) dependence at fixed \(\gamma=0.05\) | the Claim and body now state fixed \(\gamma=0.05\), the two Fig. 3 values of \(\delta\), and the Fig. 4 \(\delta\) scan | **PASS** |
| restore the source symbol \(\widehat E_{j,j+1}(\delta)\) in the adjacent-ancilla replay | the audit replay now uses exactly that symbol; Eq. (3), PDF p. 2, visually confirms it | **PASS** |
| recompute hashes and repeat semantic plus real-parser review before admission | both note-to-audit hashes resolve; this review and the artifact-verifying shadow below complete the requested gate | **PASS** |

## 3. BLP semantic and atomicity check

The repaired positive-rate record now says that Eq. (10) defines the
**trace-distance rate**

\[
\sigma(t,\rho_{1,2}(0))
=\frac{d}{dt}D(\rho_1(t),\rho_2(t)),
\]

and separately says that the source calls a process non-Markovian when this
rate is positive for some pair and time. This matches the source's explicit
discussion of both \(\sigma\leq0\) and \(\sigma>0\). Its relation now uses:

```toml
object_id = "blp-trace-distance-rate"
object_label = "trace-distance rate"
```

The relation target resolves and its label occurs in the target Claim.

The integrated-measure material is now atomic:

- `blp-integrated-measure` cites Eq. (11), PDF page 2, and states the
  maximized positive-rate integral.
- `blp-positive-interval-endpoint-sum` cites Eq. (12), PDF page 3, and states
  the endpoint-difference sum over positive-rate intervals.

Direct visual inspection confirms that Eq. (11) is at the foot of page 2 and
Eq. (12), with its explanatory paragraph, begins page 3.

`blp-optimization-limit` now cites only the concluding paragraph, PDF page 4,
and states only that exact evaluation generally requires complete knowledge
of the reduced dynamics. The distinct fixed-pair lower-bound record remains
source-faithful and its relation continues to resolve.

The repaired BLP note therefore contains 12 atomic paper facts, five
source-local gaps, and three valid relations across checked pages 1–4.

**BLP semantic result: PASS.**

## 4. McCloskey parameter and symbol check

Figure 4 and its caption, PDF page 5, plot the optimized measure against the
intra-environment strength \(\delta\), explicitly at
\(\gamma=0.05\). The accompanying text states that Strategy 2 has the smaller
threshold in \(\delta\) above which the dynamics is signaled as non-Markovian.
The repaired `mp-retention-threshold` Claim and locator now match exactly
that evidence.

Figure 3 compares \(\delta=\pi/2\) and
\(\delta=0.95\,\pi/2\) while fixing \(\gamma=0.05\); Figure 4 scans 100
values of \(\delta\in[0,\pi/2]\), also at fixed \(\gamma=0.05\). The repaired
`mp-interaction-strength-dependence` record now limits itself to the
source-supported dependence on \(\delta\) in that displayed fixed-\(\gamma\)
study. It no longer claims that those figures sweep both couplings.

Equation (3), PDF page 2, visibly names the adjacent-ancilla operation
\(\widehat E_{j,j+1}(\delta)\). The repaired operation-replay row uses that
symbol. Its Pauli replay remains algebraically correct:

\[
\widehat E_{j,j+1}(\delta)
=e^{+i\delta/2}
 e^{i\delta XX/2}
 e^{i\delta YY/2}
 e^{i\delta ZZ/2},
\]

so an API convention \(R_{PP}(\theta)=e^{-i\theta PP/2}\) requires
\(\theta=-\delta\). The distinct source strengths \(\gamma\) and \(\delta\),
the positive global phase, and the consuming-API sign are all preserved.

**McCloskey parameter-scope and source-symbol result: PASS.**

## 5. Regression checks on the previously closed boundaries

The repaired artifacts still preserve both independent defects in printed
McCloskey Eq. (8), PDF page 3:

1. its second distance is the self-distance
   \(D(\rho^S_{2,n-1},\rho^S_{2,n-1})\); and
2. its unrestricted sum lacks the positive-growth selector required by
   Eq. (7).

The audit's fixed-pair sum of positive increments remains explicitly labeled
a cross-source project derivation from BLP, not a corrected
McCloskey–Paternostro equation or the fully optimized measure.

The stochastic boundary also remains intact. PDF page 6 supplies a
draw-and-threshold rule and the displayed \(\delta=\pi/2\) period/amplitude
finding, but no random-variable distribution. The note keeps the unspecified
distribution as a source-local gap, while the audit labels a uniform draw and
Bernoulli mask as a project choice.

**Eq. (8), partial-SWAP algebra, and stochastic-boundary regressions: PASS.**

## 6. Real artifact-verifying parser shadow

The production parser sources used were:

| parser object | SHA-256 |
|---|---|
| `tools/literature_schema.py` | `6ab50f261fb64e11319831cc796bad341c4c73638144ad58cdae33d080eb23e3` |
| `tools/literature_rag.py` | `47092f7cd0f62965e7451d5f5c318fa66f4a7e03687cb86af8cd9eb50a49d00d` |

Runtime: Python 3.12.13 in the `ecs` environment.

An isolated root was created at
`/tmp/blp-mccloskey-round3-shadow.MEqMZS`. Exact copies of the two PDFs, two
notes, and two audit packets were placed at their declared
repository-relative paths. Diff inspection confirmed that only these two
fields changed in each temporary note:

```toml
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-rereview-blp-mccloskey-round3-2026-07-29"
```

No Claim, body, locator, PDF page, relation, source hash, or audit hash was
changed. The real production command

```text
conda run -n ecs python tools/literature_rag.py \
  --repo-root /tmp/blp-mccloskey-round3-shadow.MEqMZS \
  audit --notes-dir docs/papers/reading_notes --strict
```

returned `verification_mode="artifact_verified"`,
`validated_count=2`, and `excluded_count=0`:

| shadow note | paper facts | source hash resolved | diagnostic shadow SHA-256 |
|---|---:|---|---|
| BLP | 12 | yes | `50c3eb8d8bd9db226e8a7f1b216ae4e5363353891cac9a3aae9c76c6cf842de6` |
| McCloskey–Paternostro | 14 | yes | `7ac36da1ef52995c5737eb7d0e50767a1fc902dcbc83812bef1150e470927984` |

Those two diagnostic hashes belong only to admission-field-modified
temporary copies and must not be written to the corpus manifest.

**Real parser-shadow result: PASS.**

## 7. Source-local completion table

| assigned row | exact source location | paper says | paper does not say | status |
|---|---|---|---|---|
| BLP trace-distance rate and witness | Eq. (10), PDF p. 2 | \(\sigma\) is the trace-distance rate; \(\sigma>0\) for some pair/time is the witness | \(\sigma\) is not positive by definition | closed |
| BLP optimized positive growth | Eq. (11), PDF p. 2; Eq. (12), PDF p. 3 | the measure maximizes integrated positive growth and can be written as a positive-interval endpoint sum | the paper does not print the audit's sampled discrete formula | closed in two atomic records |
| BLP evaluation requirement | concluding paragraph, PDF p. 4 | exact evaluation generally requires complete reduced dynamics; observed growth supplies a lower bound | a fixed-pair null result does not establish Markovianity | closed |
| McCloskey retention threshold | Fig. 4 and Sec. II.A, PDF p. 5 | Strategy 2 has the lower displayed threshold in intra-environment strength \(\delta\) | the figure does not sweep \(\gamma\) | closed |
| McCloskey interaction-strength dependence | Figs. 3–4 and Sec. II.A, PDF p. 5 | at fixed \(\gamma=0.05\), degree and qualitative features depend on \(\delta\) | the displayed study does not establish a two-parameter sweep | closed |
| McCloskey adjacent-ancilla primitive | Eq. (3), PDF p. 2 | the operation is \(\widehat E_{j,j+1}(\delta)=\cos\delta I+i\sin\delta\,\mathrm{SWAP}\) | the paper does not print the Pauli-product decomposition | source row closed; project replay passes |
| Eq. (8) and stochastic boundaries | Eqs. (7)–(8), PDF p. 3; Sec. II.B and Fig. 6, PDF p. 6 | Eq. (7) selects positive growth; the stochastic section gives a draw-and-threshold rule | Eq. (8) has two independent defects; no draw distribution is supplied | contradictions/gap preserved |

- independent `read_status`: `complete` for both fixed PDFs
- candidate `evidence_status`: `persisted`
- parser-shadow status: `PASS`
- semantic admission verdict at the reviewed hashes: **PASS**
- remaining source-only repairs from Round 2: **none**

