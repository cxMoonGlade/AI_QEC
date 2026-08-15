# GCAPEPS exact-tree versus Quimb-native forced truncation — preregistration

Status: **FROZEN BEFORE NATIVE-CARRIER IMPLEMENTATION AND FORMAL TARGET
EXECUTION, 2026-07-29; EFFECTIVE IN THE FIRST COMMIT CONTAINING THIS PACKET**

Closure packet:
`docs/simulator_validation/GCAPEPS_NATIVE_FORCED_TRUNCATION_LITERATURE_CLOSURE_2026-07-29.md`.

This is a bounded state-action experiment, not canonical ECS Record acceptance.

## -1. Question charter

- **Decision:** determine whether a Quimb-native one/two-site compilation
  agrees with the exact tree-PEPO lane when untruncated, and whether
  `max_bond=1` after every native two-site gate produces the analytically
  predicted transient-truncation error.
- **Reusable object:** a deterministic Pauli-rotation compiler seam, a
  per-split cause ledger, and an independently reproducible bridge fixture.
- **Strong competing explanations:** cutoff rather than cap caused the loss;
  the compiled gate is wrong; the SVD is degenerate; only an exact zero was
  removed; or the final target intrinsically needs bond dimension above one.
- **Kill condition:** an untruncated candidate misses the independent anchor;
  the positive pre-cut spectrum differs from \((12/13,5/13)\); the cap-only
  lane uses nonzero cutoff; no positive singular value is discarded; the
  final exact state has rank above one; dtype is not NumPy `complex128`; or the
  cause ledger cannot distinguish cap from cutoff.

## 0. Grounding ledger

| Object | Grounding |
|---|---|
| Exact Pauli rotation | \(e^{-i\theta P/2}=\cos(\theta/2)I-i\sin(\theta/2)P\) and the frozen GCAPEPS tree construction |
| Native two-site identity | complete identity \(CX(I\otimes R_Z(\theta))CX=e^{-i\theta ZZ/2}\) |
| Leading-SVD truncation | Paeckel et al., Sec. 2.6.1, PDF p. 9 |
| Bridge Schmidt meaning | Evenbly, Sec. III, PDF pp. 3–4 |
| Gate discarded weight | Rudolph–Tindall, Sec. II Eq. (1), PDF p. 3 |
| Whole-state fidelity | Evenbly, Sec. V Eq. (12), PDF p. 6 |
| Quimb split semantics | fork base `6fbbf74cd36686ed30a4d8865697ce46e47056c1`, `CircuitPEPSSimpleUpdate` and `tensor_network_ag_gate_simple` |

## 1. Pilot exclusion

The already inspected \((4/5,3/5,\pi/3)\) API pilot is not a target row and
cannot support the final finding. It may appear only in unit tests that lock
Quimb coordinate and gate conventions.

The held-out formal target below uses different coefficients and angle. No
formal target output had been inspected at freeze time.

## 2. Frozen held-out fixture

Fixture schema:
`error_coupling_simulator.external.gcapeps_native_forced_truncation_fixture.v1`.

### 2.1 Coordinate and numerical policy

```text
n_qubits = 2
sites = (0, 1)
edges = ((0, 1),)
basis = (|00>, |01>, |10>, |11>)
q0 = most-significant flat-vector bit
frame = identity
state/gate/PEPO dtype = NumPy complex128
gauge/singular-value dtype = float64
contraction_optimize = greedy
renorm = false
gauge_smudge = 0.0
equilibrate_every = None
two_site_contract = reduce-split
svd_method = svd
cutoff_mode = rel
```

All candidate lanes start from the same `complex128` product PEPS. Single-site
preparation is outside the measured update and cannot invoke a split.

### 2.2 Input

Let

\[
a=\frac{12}{13},\qquad b=\frac{5}{13},
\]

and prepare

\[
|\phi\rangle
=(a|0\rangle+b|1\rangle)\otimes|0\rangle
=
\begin{pmatrix}a&0&b&0\end{pmatrix}^{T}.
\]

The raw one-site preparation matrix is

\[
G_{\rm prep}=
\begin{pmatrix}
a&-b\\
b&a
\end{pmatrix}.
\]

It must be applied on site 0 as a literal C-contiguous `complex128` matrix.

### 2.3 Target

Freeze

\[
\theta=\frac{\pi}{5},\qquad
U_{ZZ}=e^{-i\theta Z_0Z_1/2}.
\]

Writing \(u=e^{-i\pi/10}\),

\[
U_{ZZ}
=\cos(\pi/10)I-i\sin(\pi/10)Z_0Z_1
=\operatorname{diag}(u,\bar u,\bar u,u).
\]

The exact coherent rank is two; both coefficients are structurally nonzero.

## 3. Frozen lanes

### A — independent dense anchor

A NumPy-only module constructs the literal input, CNOT, \(R_Z\), diagonal
\(U_{ZZ}\), exact/capped vectors, analytic singular values, and all metrics.
It imports no Quimb, Stim, SDIM, or GCAPEPS code. It also verifies

\[
CX(I\otimes R_Z)CX=U_{ZZ}
\]

on all four basis columns. The anchor is never timed and is not physical
ground truth; it is an independent exact-small reference for this object.

### T — exact tree-PEPO

Apply

\[
\cos(\pi/10)I-i\sin(\pi/10)ZZ
\]

as one existing tree-PEPO update with:

```text
max_bond = None
cutoff = 0.0
compression = false
truncation = false
```

The graph bond grows from stored dimension one to two. The final physical
Schmidt rank is measured separately and must not be inferred from that stored
dimension.

### N0 — native untruncated qualification

Chronologically apply:

```text
CX 0 1
RZ(pi/5) 1
CX 0 1
```

with `max_bond=None`, `cutoff=0.0`, and the numerical policy in §2.1.

N0 must pass the full operator identity and complete-vector comparison before
any lossy row is eligible for interpretation.

### N1 — cap-only target

Use the identical compilation and settings except:

```text
max_bond = 1
cutoff = 0.0
```

The target is eligible only if at least one split has independently
reconstructed positive discarded weight.

### N2 — high-cap negative control

Use `max_bond=2`, `cutoff=0.0`. It may retain a structural-zero singular
direction, but it must discard no positive weight and must reproduce the exact
complete vector.

### D1 — direct-final-gate cap control

Apply the literal two-site \(U_{ZZ}\) as one Quimb native two-site gate with
`max_bond=1`, `cutoff=0.0`. Because the exact output is a product state, this
lane must have no positive discarded weight and must reproduce the anchor.
This control isolates decomposition-induced transient entanglement from final
state representability.

### K0/K1 — cutoff-cause controls

Use the N0 compilation with no cap:

| Lane | `max_bond` | relative cutoff | Expected cause |
|---|---:|---:|---|
| K0 | `None` | `0.4` | inert because \(5/13>0.4(12/13)\) |
| K1 | `None` | `0.5` | cutoff-only because \(5/13<0.5(12/13)\) |

K1 is predicted to produce the same final vector as N1. Their equal output
must **not** be used to infer equal truncation cause.

## 4. Exact predictions

After the first CNOT,

\[
|\eta\rangle=a|00\rangle+b|11\rangle,\qquad
M_\eta=
\begin{pmatrix}a&0\\0&b\end{pmatrix}.
\]

The unique ordered Schmidt values and gap are

\[
s_1=\frac{12}{13},\qquad
s_2=\frac{5}{13},\qquad
s_1-s_2=\frac{7}{13}.
\]

N1 retains \(s_1\) and discards the nonzero tail

\[
w_{\rm discard}=s_2^2=\frac{25}{169},\qquad
\epsilon_{\rm SVD}=\sqrt{w_{\rm discard}}=\frac{5}{13}.
\]

The exact and capped raw outputs are

\[
|y_{\rm exact}\rangle=
\begin{pmatrix}
\frac{12}{13}u\\0\\\frac{5}{13}\bar u\\0
\end{pmatrix},
\qquad
|y_{\rm cap}\rangle=
\begin{pmatrix}
\frac{12}{13}u\\0\\0\\0
\end{pmatrix}.
\]

| Quantity | Frozen exact value |
|---|---:|
| \(\|y_{\rm exact}\|_2\) | \(1\) |
| \(\|y_{\rm cap}\|_2\) | \(12/13\) |
| \(\|y_{\rm cap}\|_2^2\) | \(144/169\) |
| \(d_2=\|y_{\rm exact}-y_{\rm cap}\|_2\) | \(5/13\) |
| \(d_\infty\) | \(5/13\) |
| relative norm error | \(1/13\) |
| normalized squared fidelity \(F\) | \(144/169\) |
| normalized pure-state trace distance | \(5/13\) |
| positive discarded squared weight | \(25/169\) |
| kept bond dimension | \(1\) |

The final exact coefficient matrix is

\[
M_{\rm exact}=
\begin{pmatrix}
\frac{12}{13}u&0\\
\frac{5}{13}\bar u&0
\end{pmatrix},
\]

whose Schmidt spectrum is \((1,0)\). Thus the final exact physical state fits
bond one. Any N1 loss is caused by an intermediate split, not by the final
state manifold.

## 5. Metrics and numerical gates

For complete vectors \(x\) (anchor) and \(y\) (candidate), emit:

\[
d_\infty=\max_j|x_j-y_j|,\qquad
d_2=\|x-y\|_2,
\]

\[
d_{\rm rel}=\frac{\|x-y\|_2}{\|x\|_2},\qquad
d_{\rm norm}=\frac{|\|x\|_2-\|y\|_2|}{\|x\|_2},
\]

\[
F_{\rm raw}=
\frac{|\langle x|y\rangle|^2}
{\langle x|x\rangle\langle y|y\rangle}.
\]

Zero/non-finite denominators fail closed. Fidelity may be clipped to \([0,1]\)
only after recording
`fidelity_roundoff_correction=max(0,F_raw-1)` and requiring it at most
\(10^{-12}\).

Frozen software bands:

- exact lanes A/T/N0/N2/D1 and inert K0:
  `d_rel <= 1e-12`, `d_norm <= 1e-12`, `1-F <= 1e-12`;
- N1 and K1 exact-value checks:
  every scalar above within absolute \(10^{-12}\);
- singular values, gap, and discarded weight:
  each within absolute \(10^{-12}\);
- all vectors and gates must be genuine NumPy `complex128`.

These are class-(a) finite-dimensional identities with class-(c) numerical
software bands, not physical error bars.

## 6. Per-split cause ledger

The public Quimb simple-update API retains only the kept gauge spectrum.
Evidence mode must therefore replay each two-site step from the owned
candidate pre-state on an uncapped shadow with identical raw gate and
numerical settings. The shadow is diagnostic only and never becomes the
candidate state or a performance sample.

Every two-site row records:

```text
step_index
gate_role
edge and ordered gate targets
configured max_bond
configured cutoff and cutoff_mode
full singular values from the uncapped shadow
kept singular values from the candidate
full and kept dimensions
pre_split_weight = sum(abs(s_full)**2)
discarded_squared_weight
discarded_fraction
keep_by_cutoff
keep_by_cap
actual_keep
cause = none | max_bond | cutoff | both
dimension_reduced
positive_discarded_weight
not_a_global_error_bound = true
```

The validator independently recomputes:

\[
k_{\rm cutoff}=
\begin{cases}
d,&c=0,\\
\max(1,\#\{j:s_j>c\,s_1\}),&\text{relative cutoff }c>0,
\end{cases}
\]

\[
k_{\rm cap}=
\begin{cases}
d,&\chi_{\max}=\text{None},\\
\min(d,\chi_{\max}),&\text{otherwise},
\end{cases}
\qquad
k_{\rm kept}=\min(k_{\rm cutoff},k_{\rm cap}).
\]

A cap being configured is not evidence that truncation happened. N1 must
contain a row with independently reconstructed positive weight \(25/169\).
Removing only a structural zero is recorded but does not satisfy this gate.

## 7. Native compiler boundary

The implementation may add a native strategy only for Hermitian signed-Pauli
rotations. Generic coherent Pauli sums remain on the exact tree-PEPO path.

For future graph support, the compiler must use:

1. local basis changes on Pauli support only;
2. a deterministic route;
3. graph-edge raw `complex128` SWAP/CNOT operations that restore every routing
   workspace site;
4. one signed root \(R_Z\);
5. exact reverse uncomputation and inverse basis changes.

Sites in \(T\setminus W\) are temporary routers, not Pauli factors.
`CircuitPEPSSimpleUpdate` special SWAP gates are forbidden; SWAP/CNOT matrices
must be literal raw `complex128` gates with target order bound in the plan.

The exact-tree strategy remains the default. Native execution must be opt-in,
atomic on validation failure, and must not write its split factors into the
theorem Eq. (17) PEPO/refactor rank ledger.

## 8. Implementation and execution surface

Planned fork files:

```text
quimb/experimental/gcapeps/native.py
quimb/experimental/gcapeps/carrier.py
quimb/experimental/gcapeps/state.py
quimb/experimental/gcapeps/__init__.py
tests/test_experimental/test_gcapeps_native.py
tests/test_experimental/test_gcapeps_native_truncation.py
```

Planned parent-repository owners:

```text
scripts/external_baselines/gcapeps_forced_truncation_dense_anchor.py
scripts/external_baselines/run_gcapeps_native_forced_truncation.py
tests/test_external_gcapeps_native_forced_truncation.py
```

The fork implementation must be a scoped descendant of base commit
`6fbbf74cd36686ed30a4d8865697ce46e47056c1`. Its exact commit, tree, scoped
diff, dependency lock, import origins, and clean ignored-inclusive status must
be recorded before formal target execution. Existing n=8 and d357 packets
remain pinned to their old fork identity and are not rewritten.

Every nontrivial runner has explicit preconditions and a guarded `__main__`.
Formal target execution is forbidden until:

1. this preregistration-only parent commit exists;
2. fork tests and the scoped upstream regression subset pass;
3. the fork implementation is committed and clean;
4. parent anchor/runner/tests are committed and clean;
5. cause-corruption controls pass;
6. the target runner records the exact fork and parent identities.

No result from an uncommitted or dirty target tree is claim-bearing.

## 9. Required falsifiers

| Constraint | Deliberate corruption | Required failure |
|---|---|---|
| Full native operator | put \(R_Z\) on site 0 rather than site 1 | all-four-column operator comparison fails, even if one input is insensitive |
| Signed angle/order | flip the angle or omit final CNOT | operator and output anchors fail |
| Cap-only cause | run K1 but label it N1 | output may match, but configuration/cause ledger fails |
| Positive loss | run N0 while claiming N1 | required positive-tail row fails |
| Discarded weight | emit zero or alter one spectrum value | independent spectrum/weight reconstruction fails |
| Leading-vector retention | keep \(5/13\) rather than \(12/13\) | norm and fidelity exact-value gates fail |
| Shared candidate corruption | corrupt both tree and native outputs identically | pairwise agreement may pass; independent anchor must fail |
| Proxy firewall | substitute local tail, cap, or gauge residual for whole-state \(F\) | schema/metric validation fails |
| Global phase | multiply a candidate by \(e^{i0.37}\) | fidelity remains one while raw-vector metrics respond |
| Dtype | cast a state or gate to `complex64` | fail before update |
| Non-degeneracy | replace the target coefficients by equal amplitudes | fixture gap gate fails |
| Final-rank explanation | report stored tree bond two as physical Schmidt rank two | independent final coefficient-matrix rank gate fails |
| Router semantics | on a four-site construction test, include \(T\setminus W\) as Pauli support or omit reverse SWAP | full-basis operator reconstruction fails |

## 10. Decision rule and allowed conclusion

`PASS_BOUNDED_BRIDGE_TRANSIENT_TRUNCATION` requires:

1. all exact candidate qualification rows pass the anchor;
2. N1 contains the expected positive cap-only truncation row;
3. N1 matches every frozen exact error value;
4. N2 and D1 show no positive loss and return to the exact state;
5. K0/K1 distinguish inert and cutoff-only causes;
6. every corruption control fails for the intended reason;
7. source/environment/commit/provenance gates pass.

Allowed conclusion:

> On the frozen two-site bridge, untruncated Quimb-native compilation agrees
> with the exact tree-PEPO state action, while per-gate `max_bond=1` discards a
> nonzero transient Schmidt component and produces the preregistered
> complete-state error even though the final exact state fits bond one.

Forbidden promotions:

- generic PEPS truncation faithfulness or a global a posteriori certificate;
- equivalence of local discarded weight and whole-state error on loops;
- accumulated-round, measurement/reset, Born-mass, or complete Record
  correctness;
- general runtime, memory, contraction, or scaling advantage;
- claim that equal `max_bond` means two update decompositions make the same
  approximation;
- qutrit/SDIM/leakage GCAPEPS conclusions.

## 11. P1 boundary

A loopy \(2\times2\) fixture is the next phase, not part of this verdict. It
must use an independent 16-amplitude dense anchor and directly measure
whole-state fidelity. Its local simple-update tail is diagnostic only, and the
bridge identity must not be copied into that preregistration.
