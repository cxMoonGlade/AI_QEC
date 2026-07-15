from __future__ import annotations

import subprocess
import sys
import textwrap


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
