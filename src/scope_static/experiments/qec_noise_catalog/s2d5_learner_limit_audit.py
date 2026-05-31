"""Compatibility wrapper for the archived S2D.5 learner-limit audit."""

from scope_static.archive.experiments.stage2_learner_limit import run_s2d5_learner_limit_audit as _archived

globals().update({name: getattr(_archived, name) for name in dir(_archived) if not name.startswith("__")})


if __name__ == "__main__":
    _archived.main()
