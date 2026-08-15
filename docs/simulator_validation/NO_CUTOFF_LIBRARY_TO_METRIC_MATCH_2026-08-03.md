# No-cutoff routes — library-to-metric semantic match

Date: 2026-08-03.  Status: **current library audit; no route disposition**.

## Bottom line

No inspected library natively owns the full semantics of the frozen exact pair,
dynamic exact ADD, or retained-boundary TN headline.  Several libraries are
strong implementation substrates.  Therefore:

- absence of a one-stop owner is not evidence that a route fails;
- availability of a substrate is not evidence that the route scales;
- the historical d=3/5 missing-owner cells remain unavailable until canonical
  target lowering exists;
- minimal exact-small owners can now test the metric semantics without
  authorizing a solver or a route-kill decision.

The audit used AnySearch for discovery and then inspected official source,
documentation, or papers.  Temporary full clones were kept outside the
repository; inspected external repositories were not modified.

## Verdict vocabulary

- `OWNER`: implements the complete frozen metric semantics and eligible
  certificates without a project-defined semantic layer.
- `SUBSTRATE`: supplies exact data-structure or optimization primitives, but
  still needs a project-owned codec, recurrence, boundary, objective, or proof.
- `ADAPTOR/CORROBORATOR`: useful for parsing, graph construction, upper bounds,
  or an independent oracle, but cannot populate the headline.
- `INELIGIBLE_DIRECT`: a native tolerance, floating terminal, weighted-edge
  normalization, different objective, or missing certificate conflicts with
  the frozen metric.

## Pair recurrence

| Library | Exact source finding | Match | Consequence |
|---|---|---|---|
| Stim, current HEAD `79ae4f118ca11c615d6d8de7c6eed7d189d3a6eb`; project pin `v1.16.0/e2fc1ec` | The Python API supplies [PauliString and Tableau operations](https://github.com/quantumlib/Stim/blob/79ae4f118ca11c615d6d8de7c6eed7d189d3a6eb/glue/python/README.md#L113-L138); PauliString phase is restricted to [±1 and ±i](https://github.com/quantumlib/Stim/blob/79ae4f118ca11c615d6d8de7c6eed7d189d3a6eb/doc/stim.pyi#L10016-L10035). | `ADAPTOR` | Owns schedule/Clifford/Pauli mechanics, not `A_j`, left/right coset plus latent/frame/Record-prefix keys, or the `Q(sqrt(2),i)` coefficient map. |
| SymPy, current HEAD `2af2aca14684997bfce7bcd7224a90b29b6d0f11`; project pin `1.14.0/16fa855` | `QQ(a)` provides [exact algebraic-number arithmetic](https://github.com/sympy/sympy/blob/2af2aca14684997bfce7bcd7224a90b29b6d0f11/sympy/polys/domains/algebraicfield.py#L112-L146) and [multiple extensions](https://github.com/sympy/sympy/blob/2af2aca14684997bfce7bcd7224a90b29b6d0f11/sympy/polys/domains/algebraicfield.py#L163-L181).  A checked `QQ.algebraic_field(sqrt(2),I)` round trip is exact, but its primitive-element ANP bytes differ from the frozen four-rational tuple. | `CORROBORATOR` | Use as an independent exact oracle.  The owner must retain explicit `(a,b,c,d)` Fractions and the project recurrence/key codec. |
| SOFT/SymFT `bc9a8d2e33b1e03d411c4088f8255299c80a51eb` | Current core coefficients are [`std::complex<double>`](https://github.com/haoliri0/SOFT/blob/bc9a8d2e33b1e03d411c4088f8255299c80a51eb/cpp/src/core/common.hpp#L11-L14).  Legacy documentation declares [epsilon pruning and numerical error even when disabled](https://github.com/haoliri0/SOFT/blob/bc9a8d2e33b1e03d411c4088f8255299c80a51eb/legacy/softv1/docs/UsingCli.md#L43-L54), and the legacy CPU update contains [hard-coded `1e-6` pruning](https://github.com/haoliri0/SOFT/blob/bc9a8d2e33b1e03d411c4088f8255299c80a51eb/legacy/softv1/soft-cpu-lib/src/stabilizers.cpp#L1271-L1285). | `INELIGIBLE_DIRECT` | Valuable generalized-stabilizer structure/performance precedent; cannot certify a cutoff-free exact pair count. |

There is no pair `OWNER`.  The minimal qualification owner must therefore be a
small project recurrence with explicit exact coefficients, while Stim and
SymPy remain separated adaptor and oracle surfaces.

## Dynamic exact ADD

| Library | Exact source finding | Match | Consequence |
|---|---|---|---|
| Sylvan `614d3e134e2bfd8fd5c7f9b2aa6b354a0e3cd717` | Supports [custom terminal hash/equality/lifetime](https://github.com/trolando/sylvan/blob/614d3e134e2bfd8fd5c7f9b2aa6b354a0e3cd717/src/sylvan_mt.h#L60-L97), an exact GMP example with [`mpq_equal` and GC ownership](https://github.com/trolando/sylvan/blob/614d3e134e2bfd8fd5c7f9b2aa6b354a0e3cd717/src/sylvan_gmp.c#L37-L99) and [`mpq_canonicalize`](https://github.com/trolando/sylvan/blob/614d3e134e2bfd8fd5c7f9b2aa6b354a0e3cd717/src/sylvan_gmp.c#L146-L170), [custom apply/abstract callbacks](https://github.com/trolando/sylvan/blob/614d3e134e2bfd8fd5c7f9b2aa6b354a0e3cd717/src/sylvan_mtbdd.h#L397-L444), and [compose plus reachable-node counting](https://github.com/trolando/sylvan/blob/614d3e134e2bfd8fd5c7f9b2aa6b354a0e3cd717/docs/index.rst#L253-L276).  It deliberately has [no dynamic reordering](https://github.com/trolando/sylvan/blob/614d3e134e2bfd8fd5c7f9b2aa6b354a0e3cd717/docs/index.rst#L335-L339). | strongest `SUBSTRATE` | Best inspected target-scale candidate for a fixed order, but still needs a four-`mpq` terminal, event relation, codec, exact zero semantics, post-event GC, and canonical export.  Its native count [excludes Boolean false/true](https://github.com/trolando/sylvan/blob/614d3e134e2bfd8fd5c7f9b2aa6b354a0e3cd717/src/sylvan_mtbdd.h#L386-L394), so it cannot directly populate the project count. |
| OxiDD `6bc9548d2e467d46eff89cb4cb50f73f5e76f0d7` | MTBDD accepts [generic exact-capable terminals](https://github.com/oxidd/oxidd/blob/6bc9548d2e467d46eff89cb4cb50f73f5e76f0d7/crates/oxidd/src/mtbdd.rs#L17-L33) through [`NumberBase`](https://github.com/oxidd/oxidd/blob/6bc9548d2e467d46eff89cb4cb50f73f5e76f0d7/crates/oxidd-core/src/function.rs#L1369-L1400), with [canonical reduction](https://github.com/oxidd/oxidd/blob/6bc9548d2e467d46eff89cb4cb50f73f5e76f0d7/crates/oxidd-rules-mtbdd/src/lib.rs#L25-L58), [terminal-inclusive root count](https://github.com/oxidd/oxidd/blob/6bc9548d2e467d46eff89cb4cb50f73f5e76f0d7/crates/oxidd-core/src/function.rs#L146-L165), and [GC](https://github.com/oxidd/oxidd/blob/6bc9548d2e467d46eff89cb4cb50f73f5e76f0d7/crates/oxidd-core/src/lib.rs#L857-L869).  Current native MTBDD operations expose only [arithmetic, ITE, and restrict](https://github.com/oxidd/oxidd/blob/6bc9548d2e467d46eff89cb4cb50f73f5e76f0d7/crates/oxidd-rules-mtbdd/src/lib.rs#L76-L95); no MTBDD sum-abstraction/substitution owner was located. | `SUBSTRATE` | Strong canonical MTBDD base, but needs more direct-recurrence primitives than Sylvan. |
| CUDD `cudd-3.0.0/f54f533303640afd5dbe47a05ebeabb3066f2a25` | ADD terminal type is fixed to [`double`](https://github.com/ivmai/cudd/blob/f54f533303640afd5dbe47a05ebeabb3066f2a25/cudd/cudd.h#L186-L190), although the C++ API has [plus/times/abstract/compose](https://github.com/ivmai/cudd/blob/f54f533303640afd5dbe47a05ebeabb3066f2a25/cplusplus/cuddObj.hh#L313-L375). | `INELIGIBLE_DIRECT` | Useful algorithm/API reference; cannot carry exact `Q(sqrt(2),i)` terminals. |
| MQT Core DD `db37b93e199a44c0f0e991259c8fc188d1ba9ab5` | Uses [`fp=double`](https://github.com/munich-quantum-toolkit/core/blob/db37b93e199a44c0f0e991259c8fc188d1ba9ab5/include/mqt-core/dd/DDDefinitions.hpp#L40-L46), [weighted edges with tolerance equality](https://github.com/munich-quantum-toolkit/core/blob/db37b93e199a44c0f0e991259c8fc188d1ba9ab5/include/mqt-core/dd/Edge.hpp#L38-L55), and a [nonzero default epsilon](https://github.com/munich-quantum-toolkit/core/blob/db37b93e199a44c0f0e991259c8fc188d1ba9ab5/include/mqt-core/dd/RealNumber.hpp#L217-L221). | `INELIGIBLE_DIRECT` | Conflicts with exact terminals, unweighted edges, and no tolerance merging; retain as quantum-DD precedent. |

There is no dynamic ADD `OWNER`.  Sylvan is the strongest future target
substrate.  The minimal qualification owner should nevertheless be a compact,
transparent exact reference implementation: this isolates the metric semantics
from a new C/GMP build and gives Sylvan a byte-level oracle for later adoption.

## Retained-boundary TN

| Library | Exact source finding | Match | Consequence |
|---|---|---|---|
| NetworkX, project pin `3.6.1/7530809` | Exposes min-degree/min-fill, both explicitly [heuristic treewidth decompositions](https://github.com/networkx/networkx/blob/7530809bfa1ea7ed6fdf918a4d1431488953cb1f/networkx/algorithms/approximation/treewidth.py#L39-L85). | `ADAPTOR` | Graph container and upper diagnostic only; no exact KEEP-constrained mixed-weight proof. |
| cotengra, current HEAD `9b8b03212dd0d774f2390174975add812dfeba10`; project pin `v0.8.2/2182a79` | Accepts explicit [`output`](https://github.com/jcmgray/cotengra/blob/9b8b03212dd0d774f2390174975add812dfeba10/cotengra/interface.py#L199-L236), preserves [output indices](https://github.com/jcmgray/cotengra/blob/9b8b03212dd0d774f2390174975add812dfeba10/cotengra/core.py#L246-L258), and has exact-small DP for pairwise paths including [maximum intermediate size](https://github.com/jcmgray/cotengra/blob/9b8b03212dd0d774f2390174975add812dfeba10/cotengra/pathfinders/path_basic.py#L1251-L1324). | `ADAPTOR/CORROBORATOR` | Excellent retained-output contraction planner, but its path/objective is not the frozen internal-only vertex-elimination width/weighted bucket pair and it emits no matching project lower-proof packet. |
| Jdrasil `eafaa4cc76df9d938ac85b88e5c4218a4fbb6c1a` | Owns [ordinary unweighted simple-graph exact treewidth](https://github.com/maxbannach/Jdrasil/blob/eafaa4cc76df9d938ac85b88e5c4218a4fbb6c1a/README.md#L6-L9); its exact decomposition combines lower/upper logic and exact search [in source](https://github.com/maxbannach/Jdrasil/blob/eafaa4cc76df9d938ac85b88e5c4218a4fbb6c1a/subprojects/core/src/main/java/jdrasil/algorithms/ExactDecomposer.java#L38-L50). | `CORROBORATOR` | Can check ordinary unweighted treewidth, not KEEP-last constraints, domain weights, `w0/lambda0`, or the project subset-DP proof artifact. |

There is no retained-boundary `OWNER`.  A minimal exact owner must reconstruct
the primal graph from frozen factor scopes, keep Record vertices non-eliminable,
run separate unweighted and mixed-domain subset DPs, return replayable orders,
and expose the complete DP tables to an independent verifier.  NetworkX,
cotengra, and Jdrasil remain deliberately non-headline checks.

## Implementation decision before route decisions

The bounded next step is:

1. project exact pair micro-owner plus SymPy independent oracle;
2. project dynamic ADD micro-owner consuming only its current root and exact
   transition relation, with Sylvan retained as the first target-scale adapter;
3. project retained-boundary exact-small subset-DP owner plus independent
   permutation oracle.

These owners close only the algorithm/metric qualification gap.  They do not
close the target circuit-to-key/factor lowering gap.  Only after reviewed target
lowering produces d=3/5 histories may the preregistered growth rule kill or
retain a route.
