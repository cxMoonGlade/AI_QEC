"""Compatibility wrapper for the archived S2D.6 targeted-representation runner."""

from scope_static.archive.experiments.stage2_learner_limit import run_s2d6_targeted_representation_v3 as _archived

globals().update({name: getattr(_archived, name) for name in dir(_archived) if not name.startswith("__")})


if __name__ == "__main__":
    _archived.main()
