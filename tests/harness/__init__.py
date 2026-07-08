"""error_coupling_simulator (ECS) test/coverage HARNESS -- a proper PYTHON package (this is a
python+CUDA+C++ project; the harness belongs in Python, not fragile shell scripts).

Modules:
  proc      -- process-group-aware subprocess launcher (the orphan-process fix: children run in
               their own session/process-group and are killed atomically via os.killpg).
  gpu_pool  -- GPU semaphore (N slots, CUDA_VISIBLE_DEVICES pinning) for multi-GPU parallelism.
  gate      -- registry-driven per-unit coverage gate (100% stmt+branch minus named exemptions).
  mutation  -- registry-driven mutmut runner (kill-rate >= bar), using proc for a clean process
               tree (no orphaned mutmut workers).

Rationale (2026-07-07): the shell runners kept hitting shell-quoting traps (pre-expanded $VARs,
pkill self-match) and ORPHANED mutmut worker pools when a wrapper was killed. Python subprocess
with arg-lists (no shell) + process groups fixes both classes at the root.
"""
