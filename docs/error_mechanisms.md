# Implemented physical operations

This is the current implementation map for `error_coupling_simulator.mechanisms`. It is not a
historical catalog and exposes no numbered mechanism identity. Product framing is binding in
`docs/SIMULATOR.md`; exact owners and acceptance files are in `docs/service_status.json`.

## Local Axis-1 primitives

`mechanisms/axis1_primitives.py` lowers declared names into Hamiltonian terms or collapse operators
on a two-qubit local window. `carrier/joint_lindbladian.py` assembles all active terms for a substep
into one generator.

The current implementation dictionary is:

| primitive | implemented local object | parameter role |
|---|---|---|
| `DR` | `H = (Omega/2) X_a` | area-preserving or explicit drive rate |
| `ZZ` | `H = zeta n_a n_b` | static number-number coupling |
| `T2`, `T2_B` | `c = sqrt(2 gamma_phi) n` | pure dephasing on either site |
| `T1`, `T1_B` | `c = sqrt(gamma_1) sigma_minus` | relaxation on either site |
| `T1_UP`, `T1_UP_B` | `c = sqrt(gamma_up) sigma_plus` | excitation on either site |
| `RD`, `RD_B` | `c = sqrt(2 gamma_readout_phi) n` | declared readout-window dephasing |
| `FSIM_SWAP` | `H = (delta_theta/dt) (|01><10| + |10><01|)` | residual swap angle |
| `FSIM_PHASE` | `H = (delta_phi/dt) n_a n_b` | residual conditional phase |

These rows describe current code, not a claim that the default numerical values are measured device
parameters. `Axis1PrimitiveParams.to_manifest()` classifies the current defaults as project gates.
Primary-source closure for every retained formula is part of the restarted formula audit; until then,
tests establish implementation behavior only.

Current owner tests include `tests/test_joint_lindbladian.py`,
`tests/test_coherent_pauli_generators.py`, `tests/test_collective_decay_finite_step_guard.py`, and
the registered Axis-1 schedule/record tests.

## Qutrit leakage

`mechanisms/qutrit_leakage.py` owns:

- the declared three-level Hamiltonian/Lindblad channel;
- conversion of the superoperator to a Kraus representation;
- leakage, seepage, and coherence diagnostics;
- leaked-readout effects and their manifest;
- homogeneous and heterogeneous qutrit leakage process factories.

The current angles, rates, readout biases, and sweeps are synthetic project choices unless a complete
value-level manifest says otherwise. They are not calibrated by the external XZZX circuit files.
Current evidence and tests are listed in
`docs/simulator_validation/LEAKAGE_PROCESS_VALIDATION.md`.

## Explicit multi-level CZ transport

`mechanisms/cz_leakage.py` owns an explicit `CZParams` object, transmon and coupling Hamiltonians,
time-dependent flux/coupling profiles, calibrated propagator construction, tracked-subspace Kraus
conversion, and transport diagnostics. The caller supplies parameters, an in-memory channel, or an
explicit serialized derived-channel cache. No default path searches repository scratch.

The current acceptance files are `tests/test_cz_leakage_mechanism_units.py` and
`tests/test_simulator_ququart_transport.py`.

## Source-conditioned process parameters

`source/coupling.py` maps a replayable source value into a named `CoupledNoiseParameters` record;
`noise_processes/coupled_cycle.py` lowers the currently supported coupling and dephasing coordinates
into per-round Axis-1 parameters. Deferred fields remain visible as deferred and are not silently
applied.

The source-conditioned dense route and qutrit leakage route are separate. A shared source does not
currently drive the qutrit XZZX carrier.

## Interpretation rules

- A coherent or leakage-capable implementation does not prove that a particular record distinguishes
  it from every Pauli reduction.
- PTM off-diagonal entries indicate basis-specific non-Pauli structure; they do not uniquely identify
  a coherent cause.
- A numerical floor must never replace structural zero probability.
- Each scientific mechanism claim must bind physical name, formula, owner, current falsifier, and
  exact primary-source or complete-derivation locator.
