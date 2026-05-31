"""Public data-preparation contract helpers.

The implementation lives in :mod:`scope_static.backend.probe_contract` because
probe names, depth semantics, and bit-matrix conversion are backend support for
multiple teacher paths. This module is the stable public import surface for
data-preparation callers and older tests.
"""

from scope_static.backend.probe_contract import *  # noqa: F401,F403
