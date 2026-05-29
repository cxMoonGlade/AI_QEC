"""Compatibility wrapper for the archived S2D.8c RZZ observability runner."""

from scope_static.archive.experiments.stage2_rzz_probe_design import run_s2d8c_rzz_observability_ceiling as _archived

globals().update({name: getattr(_archived, name) for name in dir(_archived) if not name.startswith("__")})


if __name__ == "__main__":
    _archived.main()
