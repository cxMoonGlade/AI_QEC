"""Package-ownership gates for the retained, archived PEPO surface."""

from __future__ import annotations

import subprocess
import sys
import textwrap


def test_pepo_layout_resolves_without_the_legacy_namespace() -> None:
    probe = textwrap.dedent(
        """
        import builtins
        import sys
        from types import SimpleNamespace

        real_import = builtins.__import__

        def reject_legacy(name, *args, **kwargs):
            if name == "qec_twin" or name.startswith("qec_twin."):
                raise AssertionError(f"forbidden legacy import: {name}")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = reject_legacy

        from error_coupling_simulator.carrier.pepo import PepoLayout

        schedule = SimpleNamespace(
            data_coords=((0.0, 0.0), (1.0, 1.0), (1.0, -1.0), (2.0, 0.0)),
        )
        layout = PepoLayout.from_sched(schedule)

        assert layout.d == 2
        assert set(layout.grid.values()) == {(0, 0), (0, 1), (1, 0), (1, 1)}
        assert layout.__class__.__module__ == (
            "error_coupling_simulator.carrier.pepo.layout"
        )
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
