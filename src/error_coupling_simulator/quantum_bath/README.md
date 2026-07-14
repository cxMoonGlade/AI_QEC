# quantum_bath — pseudomode-enlarged shared-bath GKSL carrier (dual-axis X+Z)

The genuinely-quantum shared-bath carrier for the coupling-error simulator's non-classicality
record-characterization line. Exact-DM (CPU), consolidated from the certified
`outputs/twin_validation/` scripts.

**What it is.** 2 data (d0,d1) + 2 ancilla (a_X,a_Z) + ONE shared bosonic mode, on the full
(d0,d1,a_X,a_Z,mode) density matrix. Per round: idle-evolve under a shared GKSL bath
(H = ζ b†b + (g0z sz0+g1z sz1)(b+b†) + [(g0m sm0+g1m sm1) b† + h.c.], collapse √(2γ)b — sigma_z
dephasing + sigma_minus EMISSION into the shared mode), then extract X0X1 via a_X (H-conjugation) and
Z0Z1 via a_Z (CX-parity) sequentially. X0X1 and Z0Z1 commute → the joint (sX,sZ) outcome is a valid
surface-code-cycle instrument. All branches kept → EXACT 3-round distribution.

**Modules.**
- `gksl.py` — bosonic GKSL primitives: `boson_ops`, the shared-bath Liouvillian
  `build_shared_bath_liouvillian` + `round_superop` (reduced (d0,d1,mode) superop, 4·nmax).
- `carrier.py` — the dual-ancilla dual-axis exact-DM carrier: parity extraction unitaries,
  reduced-idle apply (both ancillas idle spectators), `dual_extract`, `dual_point`, and the
  per-round-reset reduced-map/QRT comparator `dual_point_qrt`.
- `observables.py` — multi-time record observables: Milz/Budini `K_stat_joint`/`K_stat_binary`,
  `exact_cmi_bits` (CMI), `M_mem_stat`, `project_axis`, `tv_distance`/`record_distance`, `M_ALPHABET`.
- `crow_joynt.py` — the crow_joynt classical-field null (Gaussian sigma_z field via 3D Gauss-Hermite
  quadrature) + the closed-form phase covariance (`gamma_unit_closed`, `build_sigma`); the
  independent-GT dephasing floor.
- `nulls.py` — axis-aligned incoherent AD, coherent-unitary and collective-AD null families + the
  model-free `min_tv_to_incoherent` discriminator.
- `memory_witness.py` — the independent Choi/concurrence `quantum_memory_witness`; this is separate
  from forgeable record-only K/backflow summaries.
- `ground_truth.py` — the anti-toy GTs (factorization, extraction, sigma_z indep-boson,
  sigma_minus emission ODE, no-bath sanity).

**Boundary.** Exact-DM feasibility-only (dim = 16·nmax), CPU, evaluator-side research carrier. It is
not part of emitted-record production. SIMULATOR frame: there is **no physical ground truth**; the oracles here
are FORMAL reference computations (implementation-bug catchers), never a claim of correspondence to
reality. K/K_X/K_Z are all forgeable (basis-symmetric instrument) → the honest discriminator is the
model-free record-distance, not any single K.

**Science + corrections.** See `docs/twin_validation/notion3_relaxation_dualaxis_prereg.md` for the
derivation and the two registered false-positive corrections (the field-null K is NOT 0 under the
non-commuting dual measurement; K_X is forgeable by an X-basis AD).
