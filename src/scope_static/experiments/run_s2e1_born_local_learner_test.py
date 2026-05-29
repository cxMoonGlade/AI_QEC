"""Compatibility wrapper for the archived S2E.1 Born-local learner test."""

from scope_static.archive.experiments.stage2_born_local_gate import run_s2e1_born_local_learner_test as _archived

globals().update({name: getattr(_archived, name) for name in dir(_archived) if not name.startswith("__")})


if __name__ == "__main__":
    _archived.main()
