"""forward/kernels/ — CUDA/C++ acceleration kernels (sources + their loaders).

See ``README.md`` for scope.  The ``.cu``/``.cpp`` sources are JIT-compiled on first
use; their Python loaders live beside them:

* ``fused_kraus_local.cu`` / ``.cpp`` — the fused subsystem-Kraus kernel (loaded by
  the sibling :mod:`error_coupling_simulator.carrier.accel`, not from here).
* ``sv_traj_d3.cu`` + :mod:`sv_traj_d3_loader` — the fused within-cycle
  state-vector MCWF leakage-trajectory kernel (block per trajectory;
  ``sv_traj_d3_wc`` host call).
* ``qutrit_mcwf_ops.cu`` + :mod:`qutrit_mcwf_ops_loader` — generic qutrit
  statevector MCWF primitives for the simulator frontend carrier: 1/2/3-qubit
  gates on the computational subspace, multi-controlled phase, one-site
  finite-Kraus branch sampling, fused all-sites one-Kraus-family sampling, and
  the native cached-op-stream runner used by ``NativeOpStreamMcwfExecutor``.
  The runner includes an exact adjacent-X-layer permutation lowering and an
  experimental one-CUDA-block-per-trajectory executor kernel.
"""
