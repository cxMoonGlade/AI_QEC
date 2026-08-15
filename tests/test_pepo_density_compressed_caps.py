"""Process-isolated compressed-cap check for the current PEPO carrier."""

from __future__ import annotations

import math

import torch

from _support.pepo_density import (
    ARM,
    B_BIAS,
    max_bond_dim,
    pepo_modules,
    prep_state,
    release_cuda,
    requires_cuda,
    sched,
    wc,
)


@requires_cuda
def test_compressed_site_cap_contraction_executes(wc):
    """Exercise the compressed contraction route against its exact contraction."""
    _, dynamics, sampler = pepo_modules()
    stabilizers = [dict(paulis) for paulis in wc["stabs"]]
    state = prep_state(wc, seed=161, n_ops=5, leak_pump=(1, 5))

    dynamics.nonselective_round(state, stabilizers, B_BIAS, ARM, 16)
    assert max_bond_dim(state) > 4, (
        "no virtual bond exceeds R_n=4; compressed contraction would be vacuous"
    )
    caps = {
        site: torch.diag(torch.tensor(diagonal, dtype=torch.complex128)).to("cuda")
        for site, diagonal in (
            (1, (0.8, 0.3, 0.6)),
            (7, (0.5, 0.9, 0.4)),
        )
    }
    exact = complex(sampler.expect_site_caps(state, caps))
    assert abs(exact) >= 0.05, exact
    compressed = complex(sampler.expect_site_caps(state, caps, R_n=4))
    assert math.isfinite(compressed.real) and math.isfinite(compressed.imag), compressed
    assert abs(compressed - exact) <= 0.20 * abs(exact), (compressed, exact)
    del state
    release_cuda()
