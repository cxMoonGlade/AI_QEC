from __future__ import annotations

import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest


def test_peps_sampler_default_host_rejects_the_retired_namespace() -> None:
    probe = textwrap.dedent(
        """
        import builtins
        import sys

        real_import = builtins.__import__

        retired_root = "qec" + "_" + "twin"

        def reject_retired(name, *args, **kwargs):
            if name == retired_root or name.startswith(retired_root + "."):
                raise AssertionError(f"forbidden legacy import: {name}")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = reject_retired

        from error_coupling_simulator.carrier.peps.trajectory import PepsSampler

        sampler = PepsSampler(device="cpu")
        assert sampler.host.__class__.__module__.startswith(
            "error_coupling_simulator.")
        assert not any(name.startswith(retired_root) for name in sys.modules)
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", probe],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_peps_sampler_accepts_an_injected_package_host() -> None:
    from error_coupling_simulator.carrier.peps import trajectory

    host = object()
    sampler = trajectory.PepsSampler(device="cpu", host=host)

    assert sampler.host is host


def test_grown_bond_abort_remains_fail_closed(monkeypatch) -> None:
    from error_coupling_simulator.carrier.peps import trajectory

    class TensorNetworkStub:
        @staticmethod
        def ind_size(bond: str) -> int:
            assert bond == "B0_1"
            return 5

    state = SimpleNamespace(
        tn=TensorNetworkStub(),
        layout=object(),
        device="cpu",
        ledger=[],
    )
    stab_tt = SimpleNamespace(path=(0, 1), ranks=(2,))

    monkeypatch.setattr(trajectory, "born_read_stab", lambda *args, **kwargs: (1.0, 1.0, 1.0))
    monkeypatch.setattr(trajectory, "stab_tt_singlewire", lambda *args, **kwargs: stab_tt)
    monkeypatch.setattr(trajectory, "apply_stab_branch", lambda *args, **kwargs: None)
    monkeypatch.setattr(trajectory, "_bond_between", lambda *args, **kwargs: "B0_1")
    monkeypatch.setattr(trajectory, "bond_profile", lambda _state: {(0, 1): 5})
    monkeypatch.setattr(
        trajectory,
        "truncate_path_bonds",
        lambda *args, **kwargs: pytest.fail("abort path continued into truncation"),
    )

    with pytest.raises(trajectory.BondAbortError) as caught:
        trajectory.sample_stab(
            state,
            {0: "Z", 1: "Z"},
            0.0,
            0.9,
            "A",
            trajectory.TruncationPolicy("lossless"),
            d_abort=4,
        )

    err = caught.value
    assert str(err) == (
        "D_abort=4: grown bond 'B0_1' dim 5 exceeds the pre-metric abort threshold"
    )
    assert err.bond == "B0_1"
    assert err.dim == 5
    assert err.profile == {(0, 1): 5}
