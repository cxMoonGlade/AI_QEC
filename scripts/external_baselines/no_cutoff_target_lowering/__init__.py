"""Static, cutoff-free target-lowering research objects.

This package deliberately contains no target recurrence, ADD root update,
tensor contraction, structure metric, probability solver, or product code.
"""

from .neutral import lower_frozen_declared_error_record

__all__ = ["lower_frozen_declared_error_record"]
