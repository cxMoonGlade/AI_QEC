# Full-text review — Amos Chan, Rahul M. Nandkishore, Michael Pretko, Graeme Smith, "Unitary-projective entanglement dynamics" (arXiv:1808.05949v3, cond-mat.stat-mech, 2019)

> **Provenance (2026-07-11): FULL-TEXT read (精读).** Source txt:
> `docs/papers/chan_nandkishore_pretko_smith_unitary_projective_entanglement_1808.05949.txt`
> (3156 lines total; main text + Conclusions read end-to-end lines 1-1852, Appendix A/B
> [proof details of Eq. 26/29, lines 1853-3156] skimmed for structure only — the appendix
> proves claims already stated in the main text and is not separately load-bearing). ID/title
> verified against the paper header (arXiv:1808.05949v3 [cond-mat.stat-mech], "Unitary-projective
> entanglement dynamics", Chan/Nandkishore/Pretko/Smith, dated 20 Mar 2019). Note the paper's
> own erratum: "The results presented here supersede those of all previous versions of this
> manuscript, which contained some erroneous claims" (abstract) — v1/v2 wrongly claimed area
> law for *any* nonzero measurement rate in *all* models; v3 corrects this to a model-dependent
> statement (Introduction, ln 314-320).

## Metadata [paper]

- **Authors / affiliation:** Amos Chan (Theoretical Physics, Oxford), Rahul M. Nandkishore
  (Physics + Center for Theory of Quantum Matter, U. Colorado Boulder), Michael Pretko (U.
  Colorado Boulder), Graeme Smith (U. Colorado Boulder + JILA).
- **Venue / status:** arXiv:1808.05949v3 [cond-mat.stat-mech], dated 20 Mar 2019 (v3, erratum
  version). Foundational measurement-induced-phase-transition (MIPT) theory paper, contemporary
  with the numerical discovery papers by Li-Chen-Fisher and Skinner-Ruhman-Nahum (both cited,
  refs 30-32) which this paper's results are shown to be consistent with (Sec. VI).
- **Type:** Analytic/toy-model theory paper — no numerics of its own. Constructs a hierarchy of
  exactly or asymptotically solvable models (Bell-pair hydrodynamics → cluster model → 1D Clifford
  stabilizer dynamics → large-q Floquet random circuits → a fully general information-theoretic
  bound) to explain WHY and WHEN measurement-induced area law emerges.
- **Key relationship to our work:** this is the **theory backbone of the MIPT literature** that
  our crux borrows its "p≈1 ⇒ area law" intuition from. It is emphatically NOT a paper about
  stabilizer/syndrome-extraction circuits specifically — it studies *random* unitary-projective
  circuit ensembles (Haar-random 2-qubit gates, random Clifford gates, Haar-random Floquet
  circuits) with *randomly placed* measurements at rate `f`, plus one fully general (model-
  independent) entropy bound. Mapping its `f` to our syndrome circuit's effective measurement
  density is an ANALOGY, not an identity — flagged explicitly below.

## Executive summary [paper]

The paper asks: under alternating layers of local unitary evolution (entangling) and projective
measurement (disentangling) at measurement rate `f` (fraction of sites measured per layer), does
the steady-state entanglement entropy obey an area law (bounded) or a volume law (extensive,
growing with subsystem size)? The answer, established across a hierarchy of models, is **model-
dependent**: the simplest model (Bell pairs) gives area law for *any* nonzero `f`; a slightly
richer "cluster" model gives a genuine area-to-volume phase **transition at a finite critical
f_c**; 1D random Clifford evolution gives the same kind of transition, with an explicit
differential equation for the stabilizer-size distribution and two fixed points (area-law,
volume-law) separated by a critical point with a logarithmic area-law violation; large-onsite-
Hilbert-space-dimension (q→∞) Floquet random circuits give an area law for *any* nonzero `f` **if
q→∞ is taken before the thermodynamic limit L→∞**, but the authors can only argue (not prove) that
area law persists "at least for large enough `f`" if L→∞ is taken first — the conclusion is
sensitive to the **order of limits**. Finally, Section V proves a fully general, model-independent
theorem: a strict/strong volume law (S = γ|A| with no subleading correction) is **information-
theoretically impossible** under any nonzero measurement rate f>0, in any spatial dimension — it
must saturate to a bounded region size ~ (log q / f)^d. The paper's own headline conclusion:
"projective measurements can generically restrict systems to area law entanglement, **at least
for a sufficiently high measurement rate**" (Sec. VI) — the "sufficiently high" qualifier matters
and is model-dependent.

## Method (deep) [paper]

**Setup (Fig. 1, Introduction):** alternating circuit layers of local unitary gates (`U`) and
projective single-site measurements (`P`), each site measured independently with probability `f`
per measurement layer. `f→1` (constant measurement) trivially resets the system to a product
state every step; `f→0` recovers pure unitary dynamics (generic volume-law growth). The interesting
regime is intermediate/finite `f`.

**Bell-pair toy model (Sec. II.A):** restricts entanglement structure to two-body Bell pairs of
spatial extent `x`, described by a probability distribution `P(x,t)`. Unitary evolution diffuses
`x` (grow/shrink with prob. p_g/p_s per step); measurement resets a pair to `x=0` with an effective
rate `f̃ = 2f - f²` (probability at least one of the pair's two sites gets measured). The
steady-state PDE (Eq. 2) `∂_t P = -(1-f̃)γ∂_x P - f̃P` (γ = p_g - p_s) has an **exponentially
decaying steady state** `P(x) ~ e^{-λx}` with `λ = f̃/[γ(1-f̃)]` (Eq. 4) for **any** f̃ ∈ (0,1) —
i.e. area law entanglement entropy (Eq. 5, S ~ const, independent of system size L) for ANY
nonzero measurement rate. Entanglement entropy shows an initial ballistic overshoot (linear growth
at velocity `v_E = γ(1-f̃)`, Eq. 7) before decaying to the area-law plateau — Fig. 3/4.

**Cluster model (Sec. II.B, the key generalization):** relaxes the Bell-pair restriction to allow
n-body mutually-entangled clusters of size `x`. Now a measurement on a terminal spin of a cluster
can drop the cluster's size to *anywhere* between 0 and x (not only reset it to 0), with
probability decaying exponentially in the size reduction (parameter `μ`). The modified steady-state
condition (Eq. 9) `λ(1-f̃)γ - f̃ + f̃/(λ+μ) = 0` has REAL solutions for λ (⇒ exponential/area-law
steady state) only when **f̃ > f̃_c**, with the critical rate given by Eq. 10:

  `f̃_c = γμ² / [2 - 2√(1-μ) - μ + γμ²]`

For `f̃ < f̃_c` no exponential (or even power-law) steady state exists; the distribution runs
toward uniform ⇒ **volume law**. This is the paper's first genuine area-to-volume **phase
transition** at a finite critical measurement rate, and the authors flag explicitly that the
Bell-pair model's "area law for any f" was an *artifact of its restricted (two-body-only)
entanglement structure* — richer entanglement structure produces a genuine transition (ln 528-538).

**1D Clifford evolution (Sec. III):** random Clifford-gate circuit acting on a stabilizer state;
entanglement across a cut = half the number of independent nonlocal stabilizer generators
(`|S_AB|/2`). A single-site measurement at rate `f` throws out the lowest-weight anticommuting
stabilizer generator. The steady-state stabilizer-weight distribution `P_w` obeys (Eq. 12-14) the
same area-law/volume-law dichotomy: an exponential ansatz `P_w ~ e^{-λw}` (area law) solves the
self-consistent equation only for **f > f_c** given by Eq. 17:

  `f_c = λ²e^{1/λ} / (λ² - λ + γ⁻¹)`

Below `f_c`, no decaying solution exists; the marginal/critical case is a power law `P_w ~ w⁻²`
(Eq. 18) giving a **logarithmic area-law violation**, S ~ log L (Eq. 19) — the critical fixed
point. Below the critical power `n<2` the distribution runs to volume law; above `n>2` it decays
to the area-law exponential. A companion quasiparticle/hydrodynamic picture (Sec. III.B, building
on Ref. 1's stabilizer-endpoint particles) recovers the same physics as a biased-diffusion-with-
decay equation (Eq. 21-22, 24) in the area-law phase.

**Floquet random circuits (Sec. IV):** two large-onsite-dimension (`q`) Floquet circuit models
(Haar-random unitary gates, and Haar+random-diagonal-phase gates) admit an exact 1/q-perturbative
mapping to a domain-wall (DW) statistical-mechanics problem for Rényi-α≥2 entropies (building on
refs 8,9). **The crucial finding is order-of-limits sensitivity** (explicitly flagged, ln
949-1019): three limits are in play — L→∞ (thermodynamic), t→∞ (long time), q→∞ (large local
Hilbert space). If **t→∞ then q→∞ then L→∞** (this paper's order): a rigorous proof (Eq. 26-27,
App. A) shows area-law saturation `S_α ≤ (p-1)⌈1/(2f)⌉` for **any non-vanishing f**, at any finite
but arbitrarily large L — i.e. no volume-law phase at all in this order of limits. If **L→∞ is
taken before q→∞** (Sec. IV.C), only a *heuristic, non-rigorous* argument is given (counting an
exponential number of "staircase" domain-wall diagrams, Eq. 29-32) that area-law saturation is
"plausible... at least for large enough f" — the transition to volume law at low f **cannot be
excluded** in this order. The other cited order (L→∞ before t→∞, attributed to Skinner-Ruhman-
Nahum, ref 31) is explicitly stated to give a genuine **low-f volume-law / high-f area-law phase
transition** — this is the numerically-observed MIPT that the field usually refers to.

**Section V — general model-independent bound (the strongest, most rigorous result):** using only
subadditivity, the Araki-Lieb inequality, and strong subadditivity of Von Neumann entropy, the
authors PROVE (not conjecture) two bounds that hold for *any* local-unitary + projective-
measurement dynamics on a finite-local-dimension lattice in *any* spatial dimension `d`:
1. A single bipartite unitary on `D×D` dims can increase entanglement entropy by at most `2 log D`
   (Eq. 33-35) — i.e. unitary-driven entropy growth is bounded by the *boundary* size (Eq. 46:
   `ΔS_uni ≤ 2|∂A| log q`).
2. Measuring a fraction `f` of subsystems removes entropy at a rate proportional to the *bulk*
   size (region-dependent, Eq. 36-37).
Combining these (Eq. 47-63): a putative strict volume law `S(A)=γ|A|` cannot be sustained once
`|A|` exceeds `(2 log q / (γf))^d` (Eq. 62) — **beyond that size the system MUST fall back to area
law** (or a sub-volume correction). This is a rigorous exclusion of "strong" volume law at any
nonzero `f>0`, in any dimension, independent of unitary/measurement gate details — the only
assumption is finite local Hilbert space dimension `q`. A simpler 1D argument (Eq. 64-65) gives the
saturation scale directly: `|A| ≲ 4/f`, i.e. **the maximum entangleable region size shrinks
linearly as `f` increases toward 1.**

## Results + numbers [paper]

| Model | Control parameter | Regime boundary / critical value | Regime at high f (→1) |
|---|---|---|---|
| Bell-pair toy (Sec. II.A) | measurement rate f (→ effective f̃=2f-f²) | none — area law for **any** f̃∈(0,1) (own artifact of 2-body-only structure) | area law |
| Cluster model (Sec. II.B) | f̃, cluster-collapse parameter μ | f̃_c = γμ²/[2-2√(1-μ)-μ+γμ²] (Eq. 10) | area law (f̃>f̃_c) |
| 1D Clifford stabilizer dynamics (Sec. III) | measurement rate f, growth-bias γ | f_c = λ²e^{1/λ}/(λ²-λ+γ⁻¹) (Eq. 17); critical pt = P_w~w⁻² (log-violated area law) | area law fixed point (large f) |
| Floquet random circuit, order t→∞,q→∞,then L→∞ | f, period p | **none** — rigorous area law for any f>0 at any finite L (Eq. 27) | area law (rigorous) |
| Floquet random circuit, order L→∞ then q→∞ | f, period p | heuristic only: plausible for "large enough f" (Eq. 32); transition at low f not excluded | area law (plausible, not proven) |
| Floquet random circuit, order L→∞ then t→∞ (cited: Skinner-Ruhman-Nahum, ref 31) | f | genuine phase transition at finite critical f (this paper does not derive its value, only cites it) | area law (above f_c) |
| General bound, Sec. V, any d | f, local dim q, spatial dim d | strong volume law excluded for |A| > (2 log q/(γf))^d (Eq. 62); simple 1D: |A| ≲ 4/f (Eq. 65) | area law forced (saturation region shrinks as f→1) |
| Log-corrected area law (Sec. V.B) | f | f_c = 1 − q^(2/γ) (Eq. 68's threshold) | true area law above f_c; log-violated area law sustainable below |

## The regime boundary [paper → the crux]

**What makes entanglement bounded vs growing, precisely:** every model in this paper reduces to a
*competition between two rates*: (1) unitary-driven entanglement growth, which is **boundary-
limited** (only gates straddling a cut/subsystem edge contribute, Eq. 33-35, 46: `ΔS_uni ≤
2|∂A| log q`) — i.e. it scales with the *surface area* of the region, not its volume; and (2)
measurement-driven entanglement removal, which is **bulk-limited** (any measured site inside the
region removes entropy, Eq. 36-37) — scales with the *volume* `f|A|`. Since removal scales with
volume and growth scales with surface, for large enough region size the bulk (volume) removal term
always eventually dominates the boundary (surface) growth term **for any nonzero f** — this is
literally the content of the Section V bound and is why a **strict, uncorrected volume law is
impossible under any nonzero measurement rate in any dimension** (Eq. 62-63). The only question the
paper's model hierarchy actually disputes is *whether the system reaches a genuinely area-law
steady state* (exponentially-suppressed correlations, Sec. II.A/II.B/III) *or gets stuck at a
sub-volume-law-but-still-growing intermediate state* (log-corrected area law, Sec. V.B, or a
volume law that saturates only at very large system size before a genuine transition kicks in,
Sec. IV order-of-limits caveat) at LOW-TO-INTERMEDIATE measurement rates.

**Where p≈1 (near-maximal measurement rate) sits:** every single model in this paper, when its
measurement rate parameter is pushed toward 1, lands unambiguously in the area-law phase — and
several results are proven (not just numerically suggested) to hold for the *entire* range of
nonzero f, meaning f≈1 is deep inside a rigorously-established area-law region, never close to
any of the paper's critical points. Concretely: (a) the general Sec. V bound gives a maximum
volume-law region size `|A| ≲ 4/f` (1D) or `(2 log q/(γf))^d` (general d) — as f→1 this bound
shrinks to O(1)/O(log q), i.e. essentially NO region can sustain volume-law growth; (b) even the
models exhibiting a genuine phase transition (cluster model f̃_c, Clifford f_c) place their critical
point at some f_c < 1 (the algebra of Eq. 10/17 shows f_c is generically well below 1 for
"reasonable" γ, μ — no scenario in the paper produces f_c → 1), so f≈1 sits solidly on the
area-law side of every transition studied; (c) even the Floquet order-of-limits caveat (Sec. IV.C)
only leaves the LOW-f regime uncertain — the rigorous Eq. 27 result (t→∞,q→∞ before L→∞ order)
proves area law for "any non-vanishing f," and the weaker heuristic order only doubts area law at
"not large enough f," never at f near 1.

**Geometry / lattice / stabilizer-structure dependence — the biggest caveat for our use case:**
this paper's models are ALL either (i) fully 1D chains (Bell pair, cluster, Clifford, both Floquet
circuits are explicitly L-site 1D chains, Fig. 6-10) or (ii) a fully general but structure-blind
bound (Sec. V, which only assumes finite local dimension and treats "boundary vs bulk" abstractly
in `d` dimensions without ever specifying lattice connectivity, stabilizer weight, or code
distance). **No stabilizer/surface-code/QEC-circuit structure is modeled anywhere in this paper.**
The "measurement rate f" in every model is a UNIFORM, RANDOMLY-PLACED per-site measurement
probability in a RANDOM unitary-gate circuit (Haar-random 2-qubit gates, or Haar-random Clifford
gates) — not a fixed, deterministic pattern of weight-4 stabilizer measurements on a fixed 2D
lattice with a fixed circuit schedule, and not specifically a surface-code syndrome-extraction
circuit. Mapping our syndrome-extraction circuit's "≈all ancillas measured every round" onto this
paper's scalar parameter `f≈1` is therefore an ANALOGY across model classes (deterministic
structured Clifford circuit vs. random Clifford/Haar circuit), not a result this paper derives or
proves for our specific circuit family.

**Caveats that could push toward growth (flagged explicitly by the paper itself):**
1. Order-of-limits sensitivity (Sec. IV) is a genuine, PROVEN sensitivity — for a *fixed, finite*
   circuit (which is our actual situation: d=5, ~40 rounds, not an L→∞/t→∞ asymptotic limit), the
   paper's own rigorous area-law proof (Eq. 27) requires q→∞ (large local Hilbert space) taken
   *before* the thermodynamic limit; our carrier's local dimension (qubit, or qutrit with leakage)
   is small/finite, not `q→∞`, so the cleanest rigorous guarantee does not directly transfer — we
   are closer to the "L→∞ before q→∞" heuristic-only regime, where area-law persistence is
   "plausible... at least for large enough f" but not proven at all `f`.
2. The paper's models with a genuine phase transition (cluster, Clifford) show that RICHER
   entanglement structure (n-body clusters vs. Bell pairs) LOWERS the critical measurement rate
   needed and introduces a genuine transition where a simpler model had none (ln 528-538) — i.e.
   structural richness (which our stabilizer/leakage carrier certainly has, well beyond the 2-body
   Bell-pair toy) is exactly the kind of feature the paper shows CAN introduce growth at
   insufficiently high `f`. This does NOT by itself indicate growth at `f≈1` (see above), but it
   is the mechanism by which "more structure ⇒ possibly harder to stay area-law" operates.
3. All results assume PROJECTIVE, IDEAL, single-site measurements. Leakage (our carrier's central
   non-Pauli ingredient) is out of scope entirely — no leaked/qutrit degree of freedom, no
   imperfect/soft measurement, no correlated multi-site measurement operators (a real weight-4
   stabilizer POVM is NOT a single-site projective measurement; it's a joint measurement of 4 data
   qubits mediated by an ancilla) is modeled anywhere in this paper.

## Relevance to the d5 PEPS crux [ours]

This paper is a strong **qualitative supporting reference for the "bond should saturate at p≈1"
intuition**, but it is NOT direct evidence for our specific circuit and should not be over-cited
as such:

- **Supports bounded/area-law:** the paper's entire model hierarchy, every rigorous or heuristic
  result, and its general Sec. V theorem all agree that near-maximal measurement rate (f≈1) sits
  deep in the area-law phase, far from any critical point the paper identifies. The mechanistic
  reason — unitary growth is boundary-limited, measurement removal is bulk-limited, so removal
  wins at high enough f in any dimension — is a genuinely general, dimension-agnostic argument
  (Sec. V) that is agnostic to the *specific* circuit details, which is reassuring: it means our
  observed 4→18→>40 bond blowup in 2 rounds is NOT what this paper's physics would predict for a
  near-p=1 measurement circuit, and is consistent with our suspicion that it is an **instrument
  artifact** (the compiled weight-4 √E_s POVM injecting spurious entanglement, and/or non-optimal
  truncation) rather than the genuine physics of a syndrome-extraction circuit.
- **Does NOT prove it for our circuit:** every model here is either fully 1D, or a structure-blind
  general bound, or a RANDOM circuit ensemble (Haar/Clifford-random gates with randomly placed
  measurements). Our syndrome circuit is a FIXED, deterministic, geometrically-structured 2D
  circuit (specific weight-4 XZZX stabilizers on a fixed rotated-surface-code lattice, same
  pattern every round) — none of that geometric/stabilizer structure is modeled here. The paper's
  "f" is a scalar knob in an ensemble-averaged, translationally-disordered circuit; our "p≈1" is a
  qualitative description of a fully structured circuit measuring nearly all ancillas (but never
  the data qubits) every round. This is an ANALOGY, and the paper itself would likely file our
  circuit under "a specific realization / structured circuit, not covered by the random-circuit
  ensemble results" — its own remarks about richer entanglement structure lowering the critical
  measurement rate (cluster vs. Bell-pair) is a reminder that structure matters and this paper
  does not characterize OUR structure.
- **On leakage specifically:** entirely out of scope for this paper (finite/qubit local dimension,
  ideal projective measurement only) — it offers no direct guidance on whether leakage (our
  carrier's headline non-Pauli mechanism) could push the bond dimension toward growth even at
  p≈1. That question needs a different reference (e.g. the Manabe-Suzuki-Darmawan leakage-MPS
  paper already in this repo's reading notes, or a dedicated MIPT-with-leakage paper if one exists).
- **Net verdict for the crux:** AREA-LAW/BOUNDED is the theoretically-expected regime at p≈1 across
  every model studied here, which weakly-to-moderately supports "our observed growth is an
  instrument artifact, not real physics" — but this is a GEOMETRY-DEPENDENT / STRUCTURAL-CAVEAT
  supported conclusion, not a proof for our exact circuit: the paper's own tools (random circuits,
  1D chains, ensemble-averaged f) do not directly model a fixed 2D deterministic stabilizer circuit
  with leakage, so the mapping from "p≈1" to "f≈1" is an informed analogy that should be corroborated
  by literature that studies actual Clifford/stabilizer syndrome-extraction circuits (e.g. the
  numerical MIPT-on-stabilizer-circuit literature, or direct measurement of our own PEPS bond after
  fixing the suspected instrument bugs) before being treated as settled.

## How to use / trust + open questions [ours]

- **Trust level:** FULL-TEXT 精読 of the entire main text (Introduction through Conclusions, ln
  1-1852) plus a structural skim of the appendix (which only supplies proof details for Eq. 26/29
  already stated in the main text). This is a foundational, widely-cited (500+ citations as of
  writing) analytic MIPT theory paper; its rigorous results (Bell pair exact solution, Clifford
  stabilizer-distribution ODE, Sec. V general bound) are proven in the text with explicit algebra
  we can re-derive if needed; its Floquet-circuit results rely on machinery from refs 8-9 (not
  independently re-derived here) and are flagged by the paper itself as order-of-limits-sensitive
  and partly heuristic (Sec. IV.C).
- **Distinguish PROVEN vs conjectured, precisely (for citation discipline):** PROVEN — Bell-pair
  exact PDE solution (Eq. 1-7); cluster-model critical-rate algebra (Eq. 8-10); Clifford
  stabilizer-distribution fixed points (Eq. 11-19, modulo the differential-equation ansatz being an
  assumed form, not derived from first principles); Floquet area law in the t→∞,q→∞-then-L→∞ order
  (Eq. 25-27, App. A); the general Sec. V entropy bound (Eq. 33-65, uses only subadditivity +
  Araki-Lieb + strong subadditivity — the strongest, most trustworthy result in the paper).
  HEURISTIC/NOT FULLY RIGOROUS — the L→∞-before-q→∞ Floquet staircase-diagram counting (Sec. IV.C,
  explicitly flagged "not completely rigorous," ln 1392-1394); the L→∞-before-t→∞ genuine phase
  transition is CITED from other authors (refs 30-32), not derived here.
- **Open questions for our use:**
  1. Does the Sec. V general bound's boundary-vs-bulk mechanism transfer cleanly to a PEPS/PEPO
     representation of a *mixed* (density-matrix, not pure-state) trajectory with leaked
     population, or does leakage break the "finite local Hilbert space dimension" premise the bound
     relies on (it assumes finite q, which leakage formally preserves if the qutrit space is used,
     but the effective *entangling* capacity of a leakage channel may not obey the same "unitary
     growth is boundary-limited" premise if the leakage process itself is non-unitary/dissipative
     with different growth-rate scaling)?
  2. Is there a companion paper that runs this same random-circuit-vs-structured-circuit distinction
     explicitly for STABILIZER syndrome-extraction circuits (rather than random Clifford circuits)?
     That would close the "analogy, not identity" gap flagged above and should be sought before
     treating "p≈1 ⇒ bounded" as settled for our exact circuit.
  3. Given the order-of-limits caveat (Sec. IV), and given that our simulation is FINITE (~40
     rounds, d=5, not an asymptotic L→∞ limit), it would be worth checking whether our observed
     bond growth (4→18→>40 in just 2 rounds) is even consistent with EITHER phase's short-time
     transient behavior (recall the Bell-pair model's own "overshoot" phenomenon, Sec. II.A, Fig. 4:
     bond/entanglement can overshoot before settling to its area-law plateau) — i.e. some of the
     observed growth could be the expected transient overshoot, not evidence of volume-law scaling,
     and the diagnostic should be whether growth SATURATES over more rounds, not whether it grows
     at all in the first 2 rounds.
  4. Recommend citing this paper for the qualitative "high measurement rate favors area law,
     mechanistically because growth is boundary-limited and removal is bulk-limited" claim, but
     NOT for a quantitative prediction of our bond dimension's saturation value — no model here
     gives a number applicable to a d=5 rotated-XZZX stabilizer circuit.
