"""Import-boundary regressions for the legacy experiments compatibility facade."""

from __future__ import annotations

import subprocess
import sys
import textwrap


def test_experiment_presets_do_not_import_legacy_qec_twin() -> None:
    """Reading/validating presets must not load the legacy carrier runtime."""
    probe = textwrap.dedent(
        """
        import builtins
        import sys

        real_import = builtins.__import__

        def reject_legacy_qec_twin(name, *args, **kwargs):
            if name == "qec_twin" or name.startswith("qec_twin."):
                raise AssertionError(f"forbidden legacy import: {name}")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = reject_legacy_qec_twin

        import error_coupling_simulator.frontend

        assert not any(name.startswith("qec_twin") for name in sys.modules)

        from error_coupling_simulator.frontend.experiments import (
            ExperimentPreset,
            PRESET_LEAK_THETA_0P30,
            PRESET_LEAK_WG_L1_5E3,
            resolve_theta,
        )

        assert PRESET_LEAK_THETA_0P30.name == "leak_theta_0p30"
        assert PRESET_LEAK_WG_L1_5E3.name == "leak_wg_l1_5e3"
        assert resolve_theta(PRESET_LEAK_THETA_0P30) == 0.30
        ExperimentPreset(
            name="import_boundary_probe",
            theta_rad=0.1,
            g_seep=0.0,
            g_heat=0.0,
            b_bias=0.5,
            arm="A",
            readout_conv="biased_b",
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


def test_experiment_vocabulary_matches_legacy_runtime_abi() -> None:
    """The copied pure-data vocabulary must stay exact at the adapter seam."""
    from error_coupling_simulator.frontend import experiments
    from qec_twin.forward.scalable.sv_sampler import (
        SV_ARMS as legacy_arms,
        SV_READOUT_CONVENTIONS as legacy_readout_conventions,
    )

    assert experiments.SV_ARMS == legacy_arms
    assert experiments.SV_READOUT_CONVENTIONS == legacy_readout_conventions
