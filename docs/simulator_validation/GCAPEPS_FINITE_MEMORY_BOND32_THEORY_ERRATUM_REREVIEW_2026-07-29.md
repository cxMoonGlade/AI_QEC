# GCAPEPS finite-memory bond-32 theory erratum — independent no-science-change rereview

Date: 2026-07-29

Verdict: **PASS_NO_SCIENTIFIC_CHANGE_TO_IMPLEMENTATION_GATE**

```text
scientific-content change = no
metric change             = no
threshold change          = no
selection change          = no
claim change              = no
result inspected          = no
run authorized            = no
```

This is a narrow, source-byte rereview of the two-file wording erratum in
commit `77602826a002a2325376a89841c4eeffdf0cc17b`. The reviewer changed only
this rereview file. No implementation patch, calibration output, held-out
output, target amendment, experimental raw artifact, or reserved result note
was inspected.

The verdict preserves the implementation gate opened by the original full
preregistration rereview. It does not authorize calibration, held-out
execution, result publication, or any scientific claim.

## 1. Bound objects

### 1.1 Original full review and theory checkpoint

The full scientific and protocol review remains:

| artifact | complete-file SHA-256 |
|---|---|
| `docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_PREREG_INDEPENDENT_REREVIEW_2026-07-29.md` | `58f81cf31e34c3e27bc0e1ad00a91cbf3ec6db8525abb75daba43b2b6815137b` |

That review authorized the theory-only checkpoint:

| identity | value |
|---|---|
| commit | `9f4b4d2cd3241717d8b1cdee1b0b2daad042be8c` |
| tree | `5355eb3c20a0b228d04e2a1a59222e22589c4065` |

This rereview does not replace any scientific, protocol, source-review, or
preregistration finding in that full review.

### 1.2 Erratum checkpoint

| identity | value |
|---|---|
| commit | `77602826a002a2325376a89841c4eeffdf0cc17b` |
| tree | `30886878321846cd5e3cd1fc601a65d32e0fecfc` |
| parent commit | `9f4b4d2cd3241717d8b1cdee1b0b2daad042be8c` |
| parent tree | `5355eb3c20a0b228d04e2a1a59222e22589c4065` |
| changed tracked files | exactly `docs/METRICS.md`, `docs/NUMERICAL_PROVENANCE.md` |

### 1.3 Superseded byte identities

| artifact | original reviewed SHA-256 | erratum SHA-256 |
|---|---|---|
| `docs/METRICS.md` | `c21b68f5badef20e30e080920b2d2d38864cc9dafc8613552577eddce0ff802f` | `9634a53696d1d17718f8b9174c029b012659e4611589978990d2b5c7518b3b9d` |
| `docs/NUMERICAL_PROVENANCE.md` | `fe0f8fc2ecd4d3e581d7f7aa6e695322643453e4ab92cf0e7a12c53444e95cd8` | `1d6d3a40b88708794af83488b27ba3d7141a058d7769596d59cf1dddaec499bf` |

This artifact supersedes the original full rereview only for these two
complete-file byte identities. All other bound hashes, reviewed findings,
conditions, exclusions, and gates remain unchanged.

## 2. Exact two-file diff

The following is the exact zero-context patch from the parent theory
checkpoint to the erratum checkpoint:

```diff
diff --git a/docs/METRICS.md b/docs/METRICS.md
index e5ef89e..8ac48df 100644
--- a/docs/METRICS.md
+++ b/docs/METRICS.md
@@ -877,3 +877,4 @@ and retains `result_projection_sha256`.  After publication the outer runner
-hashes the exact destination bytes; tracked note
-`docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_RESULT_2026-07-29.md`
-later persists that SHA without claiming its own containing commit.
+hashes the exact destination bytes.  The reserved future result-note path is
+docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_RESULT_2026-07-29.md;
+it is intentionally absent until a formal held-out run, after which the
+tracked note persists that SHA without claiming its own containing commit.
diff --git a/docs/NUMERICAL_PROVENANCE.md b/docs/NUMERICAL_PROVENANCE.md
index 84b0995..5f9cb38 100644
--- a/docs/NUMERICAL_PROVENANCE.md
+++ b/docs/NUMERICAL_PROVENANCE.md
@@ -247 +247 @@ tree.
-| Held-out sweep and propagation | Frozen hash seed; exact-deduped lexicographic five-integer union with ordered memberships, 11 cells if `R_star=4` else 12; stress in all slices; ensemble iff probability member; amendment-bound list/hash; terminal `heldout_report.json` under `.bond32_comparison.v1` | `project-design` | Scientific censor skips later current-cell nodes, marks sweep incomplete, continues next cell; performance-only censor alone continues current cell; invalid stops all. Report binds every child envelope/launch-receipt SHA but forbids its own complete SHA field. The outer publisher hashes destination bytes and later tracked `GCAPEPS_FINITE_MEMORY_BOND32_RESULT_2026-07-29.md` persists that SHA without self-binding its Git commit. Partial workflow durations never aggregate. |
+| Held-out sweep and propagation | Frozen hash seed; exact-deduped lexicographic five-integer union with ordered memberships, 11 cells if `R_star=4` else 12; stress in all slices; ensemble iff probability member; amendment-bound list/hash; terminal `heldout_report.json` under `.bond32_comparison.v1` | `project-design` | Scientific censor skips later current-cell nodes, marks sweep incomplete, continues next cell; performance-only censor alone continues current cell; invalid stops all. Report binds every child envelope/launch-receipt SHA but forbids its own complete SHA field. The outer publisher hashes destination bytes; the reserved future result-note path docs/simulator_validation/GCAPEPS_FINITE_MEMORY_BOND32_RESULT_2026-07-29.md is intentionally absent until a formal held-out run, after which it persists that SHA without self-binding its Git commit. Partial workflow durations never aggregate. |
```

## 3. No-science-change determination

Both edits replace wording that could imply that the reserved result-note path
already existed with an explicit statement that it remains absent until a
formal held-out run. The post-run publication rule is unchanged: after such a
run, the tracked note may persist the externally computed report SHA without
self-binding its containing Git commit.

The patch changes none of the following:

- physical mechanism, finite-memory model, operation order, or sign convention;
- observable, metric formula, normalization, aggregation rule, or epistemic
  class;
- numerical threshold, tolerance, prediction band, resource cap, timeout, or
  censor rule;
- calibration grid, lexicographic selection rule, seed, held-out cell
  construction, or event-mask law;
- worker role, dependency graph, partition, schema, serialization, timing, or
  memory-accounting definition;
- independent-reference, evaluator-firewall, SDIM, comparator, faithfulness, or
  bond gate;
- allowed claim, forbidden claim, result interpretation, or authorization
  boundary.

The reserved result-note path was absent at rereview time. The patch therefore
clarifies repository state; it does not introduce, inspect, summarize, or
authorize a result.

## 4. Supersession and gate

For later source-identity packets and the calibration target amendment:

1. retain the original full rereview as the authority for all scientific and
   protocol content;
2. retain theory commit/tree
   `9f4b4d2cd3241717d8b1cdee1b0b2daad042be8c` /
   `5355eb3c20a0b228d04e2a1a59222e22589c4065`;
3. additionally bind erratum commit/tree
   `77602826a002a2325376a89841c4eeffdf0cc17b` /
   `30886878321846cd5e3cd1fc601a65d32e0fecfc`;
4. use the erratum SHA-256 values in section 1.3 as the current
   `docs/METRICS.md` and `docs/NUMERICAL_PROVENANCE.md` byte identities; and
5. bind this superseding rereview by its externally computed complete-file
   SHA-256.

This is a pass only through the no-scientific-change implementation gate.
Every preregistered manager preflight, implementation review, calibration
firewall, target-amendment commit, held-out identity check, and terminal
acceptance condition remains mandatory. No experiment or run is authorized by
this artifact.
