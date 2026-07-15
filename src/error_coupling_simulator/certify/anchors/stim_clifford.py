from __future__ import annotations

"""The stim-Clifford anchor — the implementation-INDEPENDENT wiring check.

stim is a SEPARATE Clifford simulator (not our DM, not our carrier), so comparing a Pauli/Clifford
SLICE of the controlled process (non-Clifford noise off, a per-round bit-flip
``X_ERROR(p_x)``) against stim certifies the
geometry→record WIRING — the stabilizer supports, the seam fold (first-round-raw + interior
round-to-round XOR), and the logical — against a reference that shares NONE of our code. It catches a
bug in our own geometry/seam that the DM and the carrier would otherwise share.

The transversal X/Y DD echoes are deliberately NOT reconstructed here. On a Pauli/Clifford slice a
deterministic transversal Pauli frame is code-normalizer-invariant — it only shifts the noiseless
reference, which stim's detector/observable definitions factor out — so it is byte-for-byte inert on
every statistic this anchor answers (verified ON vs OFF on the ZZ/XX stubs and the real d3 XZZX
geometry: identical raw det+obs). A Clifford statistic therefore cannot certify (nor catch a bug in)
the echo; reconstructing it here would only be un-killable equivalent-mutant scaffolding. The echo is
load-bearing ONLY for the NON-Pauli qutrit-leakage trajectory — it symmetrises the |0>/|1>-asymmetric
energy-relaxation error (McEwen 2102.06131 §3.2/§3.4; Wood–Gambetta 1704.03081) — and that is where it
is applied and certified: the physical DM/carrier path (``RoundDataFrame`` / ``dm_round_callbacks``),
NOT this Clifford referee, which is structurally blind to it.

It keeps ``_stim_mpp_oracle`` / ``_pauli_targets`` in one current owner. It is
``emit_kind() == "clifford_slice"``
(the controlled process emits the matching bit-flip slice) and STATISTICAL (stim samples ``N`` shots → an
empirical dist; band ~ C/sqrt(N), class (b)). stim is Clifford-cheap (host-side), feasible at any R.
"""

import numpy as np

from ..types import AnchorValue, Capability, Exactness, Regime, Statistic

_ANSWERS = frozenset({Statistic.SYNDROME_DIST, Statistic.DETECTOR_MARG, Statistic.FULL_JOINT})


class StimCliffordAnchor:
    """The implementation-independent Clifford-slice wiring anchor (wraps stim)."""

    name = "stim_clifford"
    independence = (
        "a SEPARATE Clifford simulator (stim) — not the engine's DM, not the carrier; shares none of "
        "our geometry/seam code, so it catches a shared wiring bug the DM and carrier would both miss")

    def __init__(self, *, p_x: float = 0.03, seed: int = 4242):
        self.p_x = float(p_x)  # the bit-flip slice rate (read by the core for the matching emit)
        self._seed = int(seed)

    def emit_kind(self) -> str:
        return "clifford_slice"

    def answers(self) -> frozenset[Statistic]:
        return _ANSWERS

    def capability(self, statistic: Statistic, regime: Regime) -> Capability:
        if statistic not in _ANSWERS:
            return Capability(statistic, Exactness.STATISTICAL, False, "stim does not answer this", "b")
        # Clifford-cheap; feasible at any R. STATISTICAL (sampled) -> the band is C/sqrt(N), class (b).
        return Capability(statistic, Exactness.STATISTICAL, True, "", "b", 0)

    def answer(self, process, statistic: Statistic, regime: Regime,
               *, N=None, generator=None, corrupt=None) -> AnchorValue:
        from ..core import emitted_statistic

        n = int(N or 200_000)
        corrupt_stab = corrupt.get("stab") if corrupt else None
        det, obs = _stim_slice_records(process.sched, self.p_x, regime, m=0, N=n, seed=self._seed,
                                       corrupt_stab=corrupt_stab)
        val = emitted_statistic({"det": det, "obs": obs}, statistic, regime)
        band = 6.0 / np.sqrt(n)  # the stim MC band (the GT side's sampling error)
        return AnchorValue(statistic, regime, val, Exactness.STATISTICAL, band, "b",
                           {"anchor": self.name, "p_x": self.p_x, "corrupt_stab": corrupt_stab})


def _pauli_targets(paulis: dict):
    """stim ``MPP`` target list for a stabilizer/logical Pauli product ``{site -> 'X'|'Z'}``."""
    import stim

    ts = []
    for i, (s, p) in enumerate(sorted(paulis.items())):
        if i:
            ts.append(stim.target_combiner())
        ts.append(stim.target_x(s) if str(p).upper() == "X" else stim.target_z(s))
    return ts


def _stim_slice_records(sched, p_x: float, regime: Regime, *, m: int, N: int, seed: int,
                        corrupt_stab=None):
    """The independent stim oracle's emitted (folded detectors, logical-flip) for the bit-flip slice:
    prepare ``|m>_L``, per round [``X_ERROR(p_x)`` → ``MPP`` all stabilizers], then the logical
    ``MPP``; detectors = first-round-raw + interior round-to-round XOR (the seam). ``corrupt_stab``
    flips that stabilizer's X<->Z (the corrupt-stabilizer control). The emitted surface (R*n_stab
    detectors, 1 observable) matches the controlled process's emitted record bit-for-bit. The
    transversal X/Y DD echoes
    are omitted — a deterministic Pauli frame is provably inert on a Clifford slice (module docstring)."""
    import stim

    stabs = [dict(s.paulis) for s in sched.stabilizers]
    if corrupt_stab is not None:
        fl = {"X": "Z", "Z": "X"}
        stabs[corrupt_stab] = {k: fl[str(v).upper()] for k, v in stabs[corrupt_stab].items()}
    n_data = int(sched.n_data)
    n_stab = len(stabs)
    R = int(regime.R)
    logical = dict(sched.logical)
    data_q = list(range(n_data))

    c = stim.Circuit()
    for q in data_q:
        c.append("QUBIT_COORDS", [q], [float(q), 0.0])
    c.append("R", data_q)
    if int(m) == 1:
        c.append("X", [sorted(logical)[0]])
    for supp in stabs:  # warm-up reference syndrome (no detectors)
        c.append("MPP", _pauli_targets(supp))
    for r in range(R):
        c.append("X_ERROR", data_q, float(p_x))
        for supp in stabs:
            c.append("MPP", _pauli_targets(supp))
        for j in range(n_stab):
            rn = -(n_stab - j)
            rp = -(n_stab - j) - n_stab
            c.append("DETECTOR", [stim.target_rec(rn), stim.target_rec(rp)], [float(j), float(r)])
    c.append("MPP", _pauli_targets(logical))
    c.append("OBSERVABLE_INCLUDE", [stim.target_rec(-1)], 0.0)

    smp = c.compile_detector_sampler(seed=seed)
    det, obs = smp.sample(int(N), separate_observables=True)
    return det.astype(np.uint8), obs.astype(np.uint8).reshape(-1)
