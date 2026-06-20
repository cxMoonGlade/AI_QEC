"""forward/kernels/ — CUDA/C++ acceleration kernels (sources + their loaders).

See ``README.md`` for scope.  The ``.cu``/``.cpp`` sources are JIT-compiled on first
use; their Python loaders live beside them:

* ``fused_kraus_local.cu`` / ``.cpp`` — the fused subsystem-Kraus kernel (loaded by
  the sibling :mod:`qec_twin.forward.accel`, not from here).
* ``sv_traj_d3.cu`` + :mod:`sv_traj_d3_loader` — the P4a state-vector MCWF
  leakage-teacher trajectory kernel (block-per-trajectory; exposes the §7
  ``sv_traj_d3`` host call).
"""
