# carrier/pepo

This package implements a qutrit density-matrix PEPO carrier for a rotated
`d×d` XZZX data patch.  A site uses the fused physical leg
`k = 3·t_ket + t_bra` of dimension nine.  Execution is GPU-only and
`torch.complex128`; the implementation is dimension-generic, while the current
independent dense-reference checks are bounded to the real d3 patch.

This is a retained research carrier, not the simulator's canonical record output
and not evidence of physical-device validity.  Exact density-matrix comparisons
are implementation bug catchers.  Record-level finite-truncation faithfulness
remains open.

Binding status: `docs/simulator_validation/PEPO_VALIDATION.md`.

Modules:

- `layout.py` owns the integer-grid transform, frozen cut, plaquette paths,
  codestate construction, `PepoState`, and the bounded dense bridge.
- `dynamics.py` owns within-cycle site superoperators, stabilizer-channel tensor
  trains, NTU truncation, nonselective rounds, and truncation ledgers.
- `sampler.py` owns boundary-MPS norm caches, cap contractions,
  stabilizer expectations, terminal-observable probabilities,
  record folding exports, and negativity diagnostics.

Selective per-stabilizer sampling is not a PEPO entry point. Terminal-observable
sampling rejects invalid raw weights instead of clipping them.

The shared index contract is fixed by `layout.py`: site tag `Q{pos}`, physical
index `k{pos}`, and virtual bond `B{p}_{q}` for `p < q`.  There is no global
canonical gauge; per-bond dimensions and `PepoState.ledger` are the explicit
truncation state.  Positivity is not assumed.

Current tests:

- `tests/test_pepo_density_layout_guards.py` — host-only layout, rank, fold, and
  negativity guards.
- `tests/test_pepo_density_state.py`, `tests/test_pepo_density_token_ops.py`,
  `tests/test_pepo_density_stabilizer.py`, `tests/test_pepo_density_killers.py`,
  and `tests/test_pepo_density_observables.py` — process-isolated state,
  dense-reference algebra, local dynamics, corruption, and contraction gates.
- `tests/test_pepo_density_nonselective_round.py` — two-round truncation check.
- `tests/test_pepo_density_ntu_precut.py` — in-regime/out-of-regime NTU pre-cut.
- `tests/test_pepo_density_compressed_caps.py` — compressed cap contraction.
- `tests/test_pepo_host_seam.py` — package ownership and host seam.

Every repeated exact-density group and each high-memory integration check is a
separate service-acceptance file. The canonical supervisor starts them in fresh
processes so each file owns one bounded native/CUDA lifetime.
