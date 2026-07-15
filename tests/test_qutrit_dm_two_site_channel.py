"""Independent checks for the exact qutrit engine's two-site channel seam."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from error_coupling_simulator.carrier.cptp_channel import apply_kraus
from error_coupling_simulator.carrier.exact.qutrit_dm import QutritDM


requires_cuda = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="the exact qutrit density-matrix engine is GPU-only",
)


def _embed_two_site_reference(
    operator: torch.Tensor,
    left_site: int,
    right_site: int,
    n_sites: int,
) -> torch.Tensor:
    """Embed a 9x9 operator by Kronecker product plus an explicit axis permutation."""

    operator = operator.to(torch.complex128)
    remaining = n_sites - 2
    if remaining:
        full = torch.kron(
            operator,
            torch.eye(
                3**remaining,
                dtype=torch.complex128,
                device=operator.device,
            ),
        )
    else:
        full = operator
    other_sites = [
        site for site in range(n_sites) if site not in (left_site, right_site)
    ]
    current_order = [left_site, right_site, *other_sites]
    row_permutation = [current_order.index(site) for site in range(n_sites)]
    permutation = row_permutation + [
        n_sites + axis for axis in row_permutation
    ]
    dimension = 3**n_sites
    return (
        full.reshape([3] * (2 * n_sites))
        .permute(*permutation)
        .contiguous()
        .reshape(dimension, dimension)
    )


def _random_cptp_kraus(
    rng: np.random.Generator,
    dimension: int,
    n_kraus: int,
    device: str,
) -> torch.Tensor:
    matrix = torch.tensor(
        rng.standard_normal((dimension * n_kraus, dimension))
        + 1j * rng.standard_normal((dimension * n_kraus, dimension)),
        dtype=torch.complex128,
        device=device,
    )
    isometry, _ = torch.linalg.qr(matrix)
    return isometry.reshape(n_kraus, dimension, dimension).contiguous()


def _random_density_matrix(
    rng: np.random.Generator,
    dimension: int,
    device: str,
) -> torch.Tensor:
    matrix = torch.tensor(
        rng.standard_normal((dimension, dimension))
        + 1j * rng.standard_normal((dimension, dimension)),
        dtype=torch.complex128,
        device=device,
    )
    rho = matrix @ matrix.conj().transpose(-1, -2)
    return rho / torch.trace(rho).real


@requires_cuda
def test_two_site_channel_matches_independent_dense_embedding() -> None:
    rng = np.random.default_rng(7)
    worst = 0.0
    for n_sites in (3, 4, 5):
        dimension = 3**n_sites
        pairs = [(0, 1), (1, 0), (0, n_sites - 1), (n_sites - 1, 0)]
        if n_sites >= 4:
            pairs += [(1, n_sites - 1), (n_sites - 1, 1)]
        for left_site, right_site in pairs:
            for n_kraus in (1, 2, 4):
                kraus = _random_cptp_kraus(rng, 9, n_kraus, "cuda")
                rho = _random_density_matrix(rng, dimension, "cuda")
                engine = QutritDM(n_sites, device="cuda")
                engine.set_state(rho.clone())
                engine.apply_channel_2site(kraus, left_site, right_site)

                embedded = torch.stack([
                    _embed_two_site_reference(
                        operator, left_site, right_site, n_sites
                    )
                    for operator in kraus
                ])
                reference = apply_kraus(rho, embedded)
                reference = 0.5 * (
                    reference + reference.conj().transpose(-1, -2)
                )
                worst = max(
                    worst,
                    float(torch.max(torch.abs(engine.rho - reference))),
                )
    assert worst < 1.0e-12


@requires_cuda
def test_two_site_product_channel_reduces_to_two_local_channels() -> None:
    rng = np.random.default_rng(11)
    worst = 0.0
    for n_sites in (3, 4, 5):
        dimension = 3**n_sites
        pairs = [(0, 1), (0, n_sites - 1)]
        if n_sites >= 4:
            pairs.append((n_sites - 1, 1))
        for left_site, right_site in pairs:
            left_kraus = _random_cptp_kraus(rng, 3, 2, "cuda")
            right_kraus = _random_cptp_kraus(rng, 3, 3, "cuda")
            product = torch.stack([
                torch.kron(left, right)
                for left in left_kraus
                for right in right_kraus
            ])
            rho = _random_density_matrix(rng, dimension, "cuda")

            joint = QutritDM(n_sites, device="cuda")
            joint.set_state(rho.clone())
            joint.apply_channel_2site(product, left_site, right_site)

            local = QutritDM(n_sites, device="cuda")
            local.set_state(rho.clone())
            local.apply_channel(left_kraus, left_site)
            local.apply_channel(right_kraus, right_site)
            worst = max(worst, float(torch.max(torch.abs(joint.rho - local.rho))))
    assert worst < 1.0e-12


def _zz_unitary(phi: float, device: str) -> torch.Tensor:
    unitary = torch.eye(9, dtype=torch.complex128, device=device)
    indices = {(0, 0): 0, (0, 1): 1, (1, 0): 3, (1, 1): 4}
    phases = {(0, 0): -phi, (0, 1): phi, (1, 0): phi, (1, 1): -phi}
    for levels, phase in phases.items():
        unitary[indices[levels], indices[levels]] = np.exp(1j * phase)
    return unitary.reshape(1, 9, 9)


@requires_cuda
def test_two_site_zz_unitary_preserves_density_matrix_constraints() -> None:
    rng = np.random.default_rng(13)
    rho = _random_density_matrix(rng, 3**4, "cuda")
    identity9 = torch.eye(9, dtype=torch.complex128, device="cuda")
    for phi in (1.0e-3, 0.05, 0.10, 0.15):
        unitary = _zz_unitary(phi, "cuda")
        torch.testing.assert_close(
            unitary[0].conj().transpose(-1, -2) @ unitary[0],
            identity9,
            rtol=0.0,
            atol=1.0e-12,
        )
        engine = QutritDM(4, device="cuda")
        engine.set_state(rho.clone())
        engine.apply_channel_2site(unitary, 0, 1)
        output = engine.rho
        assert abs(float(torch.trace(output).real) - 1.0) < 1.0e-12
        assert float(torch.max(torch.abs(output - output.conj().T))) < 1.0e-12
        assert float(torch.linalg.eigvalsh(output).min().real) > -1.0e-10

    identity_engine = QutritDM(4, device="cuda")
    identity_engine.set_state(rho.clone())
    identity_engine.apply_channel_2site(_zz_unitary(0.0, "cuda"), 0, 1)
    torch.testing.assert_close(identity_engine.rho, rho, rtol=0.0, atol=1.0e-12)


@requires_cuda
def test_reversed_site_order_corruption_is_detected() -> None:
    swap01 = torch.tensor(
        [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
        dtype=torch.complex128,
        device="cuda",
    )
    operator = torch.kron(swap01, torch.eye(3, dtype=torch.complex128, device="cuda"))
    basis = torch.zeros(27, dtype=torch.complex128, device="cuda")
    basis[3] = 1.0  # |0,1,0>
    rho = torch.outer(basis, basis.conj())

    engine = QutritDM(3, device="cuda")
    engine.set_state(rho.clone())
    engine.apply_channel_2site(operator.reshape(1, 9, 9), 0, 1)

    correct = _embed_two_site_reference(operator, 0, 1, 3)
    corrupted = _embed_two_site_reference(operator, 1, 0, 3)
    expected = correct @ rho @ correct.conj().T
    wrong = corrupted @ rho @ corrupted.conj().T
    torch.testing.assert_close(engine.rho, expected, rtol=0.0, atol=1.0e-12)
    assert float(torch.max(torch.abs(engine.rho - wrong))) > 0.5
