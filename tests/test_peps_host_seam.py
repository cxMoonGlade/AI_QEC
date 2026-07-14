from __future__ import annotations

import subprocess
import sys
import textwrap


def test_peps_sampler_default_host_does_not_import_qec_twin() -> None:
    probe = textwrap.dedent(
        """
        import builtins
        import sys

        real_import = builtins.__import__

        def reject_qec_twin(name, *args, **kwargs):
            if name == "qec_twin" or name.startswith("qec_twin."):
                raise AssertionError(f"forbidden legacy import: {name}")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = reject_qec_twin

        from error_coupling_simulator.carrier.peps.trajectory import PepsSampler

        sampler = PepsSampler(device="cpu")
        assert sampler.host.__class__.__module__.startswith(
            "error_coupling_simulator.")
        assert not any(name.startswith("qec_twin") for name in sys.modules)
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
