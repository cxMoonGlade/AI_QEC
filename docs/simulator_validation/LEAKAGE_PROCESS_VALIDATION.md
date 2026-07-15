# Leakage-process validation status

Status: **current bounded implementations; synthetic numerical presets; wider scientific audit
pending**.

## Current owners

- `mechanisms/qutrit_leakage.py` owns the physically named qutrit leakage channel, Kraus conversion,
  Wood-Gambetta diagnostics, leaked-readout instrument, and homogeneous/heterogeneous process
  factories.
- `mechanisms/cz_leakage.py` owns explicit transmon/CZ parameters, Hamiltonian and channel
  construction, tracked-subspace Kraus conversion, and transport diagnostics.
- `carrier/exact/qutrit_dm.py` provides the bounded exact-density reference route.

The service registry binds the following current acceptance files:

- `tests/test_qutrit_leakage_units.py`
- `tests/test_qutrit_leakage_certification_independence.py`
- `tests/test_simulator_qutrit_leakage.py`
- `tests/test_cz_leakage_mechanism_units.py`
- `tests/test_simulator_ququart_transport.py`

## Current evidence boundary

The listed tests establish API ownership, CPTP/channel algebra for registered cases, parser and
manifest rejection, independent-reference behavior, and explicit channel-input selection. They are
formal implementation checks, not hardware validation.

Current angles, seepage/heating coordinates, leaked-readout bias values, within-cycle placement, and
rate sweeps are `project-design` or `convenience-default` unless an emitted manifest gives a complete
value-level provenance row. The Google d3 circuit files provide geometry and schedule inputs; they do
not calibrate leakage parameters.

The source-conditioned dense-qubit process and the static qutrit XZZX leakage process remain separate
routes. No integrated source-driven qutrit XZZX record claim is permitted until an implemented
channel/schedule bridge, independent reference, current acceptance test, and primary-source closure
all exist.

The next formula audit must bind each retained operation to its physical name, implemented formula,
independent falsifier, and exact primary-source locator. Until then, implementation tests may support
software correctness only.
