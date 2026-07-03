"""oracles — independent QuTiP-derived {H, c} channel primitives (evaluator-only).

FORMAL reference computations (bug-catchers), NOT physical ground truth. Derived first-principles
from QuTiP Hamiltonians / Lindbladians; used to certify the carrier's channels via an INDEPENDENT
path.

- ``single_qubit`` (<- qutip_single_qubit_channels.py): single-transmon physical channels.
- ``two_qubit``    (<- qutip_twoqubit_channels.py): two-transmon coherent channels (uses ``leakage``).
- ``leakage``      (<- qutip_cz_leakage_channel.py): per-CZ leakage-transport channel.
- ``opensystem``   (<- qutip_opensystem_channels.py): open-system / bath (near-resonant, pseudomode).

The ``opensystem`` docstring shows an ``qec_twin.forward.exact.qutrit_dm`` usage EXAMPLE in prose —
that is documentation, not an import (verified: no real qec_twin import). The engine binding is a
later-phase concern.
"""
