"""Process-isolated NTU pre-compression check for the current PEPO carrier."""

from __future__ import annotations

import copy
import math

from _support.pepo_density import (
    ARM,
    B_BIAS,
    pepo_modules,
    pick_stabilizers,
    prep_state,
    release_cuda,
    requires_cuda,
    sched,
    wc,
)


@requires_cuda
def test_ntu_precut_reports_in_regime_and_zero_out_of_regime(wc):
    """Prove the pre-cut branch executes and distinguish its no-precut image."""
    _, dynamics, _ = pepo_modules()
    stabilizers = [dict(paulis) for paulis in wc["stabs"]]
    bond_cap = 2
    state = prep_state(
        wc,
        seed=163,
        n_ops=6,
        leak_pump=(0, 2, 4, 6),
    )

    dynamics.nonselective_round(state, stabilizers, B_BIAS, ARM, 8)
    weight_four, _ = pick_stabilizers(wc["sched"])
    stabilizer_tt = dynamics.stab_channel_tt(
        weight_four,
        0,
        B_BIAS,
        ARM,
        state.layout,
        "cuda",
    )
    dynamics.apply_stab_branch(state, stabilizer_tt)
    candidates = [
        (index, int(state.tn.ind_size(index)))
        for index, tensor_ids in state.tn.ind_map.items()
        if len(tensor_ids) == 2
    ]
    bond, dimension = max(candidates, key=lambda candidate: candidate[1])
    assert dimension > 4 * bond_cap, (
        f"largest grown bond {dimension} did not enter the pre-cut regime"
    )

    mirror = copy.deepcopy(state)
    entry = dynamics.ntu_truncate(state, bond, bond_cap)
    assert int(entry["exact_rank"]) > 4 * bond_cap, entry
    assert float(entry["precut_discarded"]) > 0.0, entry
    assert int(entry["dim_out"]) == bond_cap, entry
    assert math.isfinite(float(entry["ntu_eps"])), entry

    no_precut_cap = int(entry["exact_rank"]) + 8
    no_precut = dynamics.ntu_truncate(mirror, bond, no_precut_cap)
    assert int(no_precut["exact_rank"]) > 4 * bond_cap, no_precut
    assert int(no_precut["exact_rank"]) <= 4 * no_precut_cap, no_precut
    assert float(no_precut["precut_discarded"]) == 0.0, no_precut
    del state, mirror
    release_cuda()
