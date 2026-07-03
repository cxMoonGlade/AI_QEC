"""SHIM package — moved to ``error_coupling_simulator.carrier.kernels`` (MIGRATION P2, 2026-07-03).

The CUDA/C++ kernel sources + loaders now live in the standalone package. This shim keeps every
importer of ``qec_twin.forward.kernels`` working: consumers do lazy submodule imports like
``from qec_twin.forward.kernels import sv_traj_d3_loader`` / ``qutrit_mcwf_ops_loader``
(sv_sampler, mcwf_executor, mcwf_backend), so we bind those submodules here AND alias them in
``sys.modules`` so both ``from ... import <loader>`` and ``import ...kernels.<loader>`` resolve.
"""
import sys as _sys

from error_coupling_simulator.carrier import kernels as _pkg
from error_coupling_simulator.carrier.kernels import (  # the loaders consumers import by name
    sv_traj_d3_loader,
    qutrit_mcwf_ops_loader,
)

globals().update({_k: _v for _k, _v in vars(_pkg).items() if not _k.startswith("__")})
_sys.modules[__name__ + ".sv_traj_d3_loader"] = sv_traj_d3_loader
_sys.modules[__name__ + ".qutrit_mcwf_ops_loader"] = qutrit_mcwf_ops_loader
del _sys, _pkg
