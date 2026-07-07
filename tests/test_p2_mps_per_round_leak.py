"""P2-ii gate (a) + entry guards: the T1 MPS per-round leak seam (prereg
``docs/twin_validation/p2_conjunction_wiring_prereg.md`` §1, API pin 2026-07-06).

Registered gate (a): a per-round sequence of IDENTICAL slices must reproduce today's
static arm BYTE-identically (same seeds) — the pure-refactor guarantee that the
per-round seam changes NO physics until a caller actually varies the tables. Plus the
C1 entry guards (per-round tables are CPTP-asserted, never trusted) and the header
provenance contract (``leak_slices_mode`` / ``leak_slices_sha256``).

The record-level gates (b)/(c) — per-round-varied records vs the T0 DM law under the
SEQUENTIAL-measurement null, and the liveness control with a pre-derived effect size —
are committed gate scripts under ``outputs/twin_validation/`` (they need the full-9q
sequential-null machinery + a registered N), NOT this modest-N ledger.

GPU-only model compute; needs the shipped d3_at_q6_7 r01/r10 patch (skips otherwise).
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from qec_twin.forward.exact import xzzx_parser as xp

_HAS_CUDA = torch.cuda.is_available()
_R01_CIRC, _R01_META = xp.default_r01_paths()
_R10_CIRC, _R10_META = xp.default_r10_paths()
_HAS_DATA = (_R01_CIRC.is_file() and _R01_META.is_file()
             and _R10_CIRC.is_file() and _R10_META.is_file())

requires_cuda = pytest.mark.skipif(not _HAS_CUDA, reason="GPU-only model compute (MPS carrier)")
requires_data = pytest.mark.skipif(not _HAS_DATA, reason="shipped d3_at_q6_7 r01/r10 patch absent")

DEVICE = "cuda"
CDTYPE = torch.complex128

# a plain physical cell (gate (a) certifies CODE-PATH identity, not a physics claim;
# the value only needs to be a valid, leak-active point of the registered sweep).
THETA, G_SEEP, G_HEAT, B_BIAS, ARM = 0.30, 0.09, 0.0, 0.9, "A"


def _sched_and_spec(R: int, N: int, seed: int = 11):
    from qec_twin.forward.scalable.sv_sampler import RunSpec

    sched = xp.parse_xzzx_circuit(_R01_CIRC, _R01_META, verify=True)
    sched = sched.with_within_cycle_streams(xp.parse_within_cycle_streams(_R10_CIRC, _R10_META))
    spec = RunSpec(circuit_path=_R01_CIRC, metadata_path=_R01_META, m=0, theta=THETA,
                   g_seep=G_SEEP, g_heat=G_HEAT, arm=ARM, b=B_BIAS, readout_conv="biased_b",
                   N=N, base_seed=seed, R=R, dtype="c128")
    return sched, spec


def _base_leak(spec) -> torch.Tensor:
    """The spec-built exp(L/4) slice via the SAME builder the static arm uses (CPTP +
    composition asserted inside — reusing the C1 source of truth, not re-deriving it)."""
    from qec_twin.forward.scalable.sv_sampler import SvSampler

    host = SvSampler(device=DEVICE)
    leak, _ = host.build_within_cycle_leak(spec)
    return leak


@requires_cuda
@requires_data
def test_p2ii_a_single_set_byte_identity():
    """Gate P2-ii (a): leak_slices=[base]*R (per-round mode, identical tables) must be
    BYTE-identical to leak_slices=None (the static arm) on the same seeds — packed
    syndrome+flip buffer, per-qubit terminal bits, and the truncation ledger all equal.
    Only the header provenance may differ (mode static vs per_round + the sha)."""
    from qec_twin.forward.scalable.mps_forward import MpsLeakageForward

    R, N = 2, 3
    sched, spec = _sched_and_spec(R=R, N=N)
    fwd = MpsLeakageForward(device=DEVICE)
    leak = _base_leak(spec)

    ss_static, led_static = fwd.sample(spec, sched=sched)
    ss_pr, led_pr = fwd.sample(spec, sched=sched, leak_slices=[leak] * R)

    assert ss_static.shots is not None and ss_pr.shots is not None
    assert bytes(np.ascontiguousarray(ss_static.shots).tobytes()) == \
        bytes(np.ascontiguousarray(ss_pr.shots).tobytes()), \
        "per-round[identical tables] packed record != static arm (gate (a) BYTE identity)"
    tb_s = np.asarray(ss_static.diag["terminal_bits"])
    tb_p = np.asarray(ss_pr.diag["terminal_bits"])
    assert np.array_equal(tb_s, tb_p), "terminal bit side-channel differs (gate (a))"
    # ledgers: same chi, same cuts, same discarded totals (both structurally 0 at exact grade)
    rep_s, rep_p = led_static.report(), led_pr.report()
    for key in ("chi", "n_truncating_ops", "worst_cut_discarded_weight",
                "sum_discarded_weight", "n_shots"):
        assert rep_s[key] == rep_p[key], f"ledger field {key} differs (gate (a))"
    # provenance contract
    assert ss_static.header["leak_slices_mode"] == "static"
    assert "leak_slices_sha256" not in ss_static.header
    assert ss_pr.header["leak_slices_mode"] == "per_round"
    assert isinstance(ss_pr.header["leak_slices_sha256"], str) and \
        len(ss_pr.header["leak_slices_sha256"]) == 64


@requires_cuda
@requires_data
def test_p2ii_entry_guards_reject_bad_tables():
    """C1 entry guards: the carrier never trusts caller tables — wrong count, wrong
    shape, and CPTP-violating tables are all rejected BEFORE any trajectory runs."""
    from qec_twin.forward.scalable.mps_forward import MpsLeakageForward

    R, N = 2, 1
    sched, spec = _sched_and_spec(R=R, N=N)
    fwd = MpsLeakageForward(device=DEVICE)
    leak = _base_leak(spec)

    with pytest.raises(ValueError, match="one .* table per round"):
        fwd.sample(spec, sched=sched, leak_slices=[leak] * (R + 1))
    with pytest.raises(ValueError, match=r"\(n_kraus, 3, 3\)"):
        fwd.sample(spec, sched=sched, leak_slices=[torch.eye(3, dtype=CDTYPE)] * R)
    # a genuinely non-CPTP table: scale the DOMINANT Kraus so sum K^H K != I. The
    # Choi-eigh builder returns Kraus in ASCENDING weight order, so leak[-1] is the
    # near-identity no-jump branch (weight ~1) — scaling IT gives residual ~2e-2.
    # (Scaling leak[0], the smallest kept dust branch, was MEASURED to give 1.18e-12 —
    # a hair above CPTP_TOL, an evil-marginal test; the precondition below caught it
    # on the first gate run, 2026-07-06.)
    bad = leak.clone()
    bad[-1] = bad[-1] * 1.01
    from qec_twin.forward.scalable.sv_sampler import SvSampler
    resid = SvSampler(device=DEVICE).cptp_residual(bad)
    assert resid > 1e-8, f"PRECONDITION: engineered CPTP violation too small ({resid:.3e})"
    with pytest.raises(AssertionError, match="CPTP residual"):
        fwd.sample(spec, sched=sched, leak_slices=[bad] * R)


@requires_cuda
@requires_data
def test_p2ii_per_round_varied_smoke_and_provenance():
    """Per-round mode with GENUINELY different tables runs end-to-end and stamps the
    provenance. This is a SMOKE + contract test only — the statistical record gate vs
    the T0 DM (sequential null) and the liveness effect-size gate are the committed
    scripts of prereg §1 (b)/(c), registered-N territory, never this modest-N ledger."""
    from qec_twin.forward.scalable.mps_forward import MpsLeakageForward
    from qec_twin.forward.scalable.sv_sampler import RunSpec

    R, N = 2, 2
    sched, spec = _sched_and_spec(R=R, N=N)
    fwd = MpsLeakageForward(device=DEVICE)
    leak_lo = _base_leak(spec)
    # a second, physically distinct round table: +30% g_seep (the registered class-(c)
    # modulation bracket), built by the SAME asserted builder.
    spec_hi = RunSpec(circuit_path=_R01_CIRC, metadata_path=_R01_META, m=0, theta=THETA,
                      g_seep=G_SEEP * 1.3, g_heat=G_HEAT, arm=ARM, b=B_BIAS,
                      readout_conv="biased_b", N=N, base_seed=11, R=R, dtype="c128")
    leak_hi = _base_leak(spec_hi)
    assert leak_hi.shape == leak_lo.shape, \
        "PRECONDITION: retained Choi rank differs between the two cells (re-pick the cell)"
    assert torch.max(torch.abs(leak_hi - leak_lo)).item() > 1e-6, \
        "the two round tables must be genuinely different (else this smoke is vacuous)"

    ss, led = fwd.sample(spec, sched=sched, leak_slices=[leak_lo, leak_hi])
    assert ss.header["leak_slices_mode"] == "per_round"
    sha = ss.header["leak_slices_sha256"]
    assert isinstance(sha, str) and len(sha) == 64
    assert ss.n_shots == N and led.report()["n_shots"] == N
    # sha is CONTENT-derived: same tables -> same sha; different order -> different sha
    ss2, _ = fwd.sample(spec, sched=sched, leak_slices=[leak_lo, leak_hi])
    assert ss2.header["leak_slices_sha256"] == sha
    ss3, _ = fwd.sample(spec, sched=sched, leak_slices=[leak_hi, leak_lo])
    assert ss3.header["leak_slices_sha256"] != sha


# --------------------------------------------------------------------------- #
# F1 discriminators (review 2026-07-06): the tests above cannot see an INERT   #
# or MISINDEXED seam — these two can, deterministically.                       #
# --------------------------------------------------------------------------- #
# a GROSSLY different second cell: the discriminators rely on the two tables
# producing different branch selections under the same u stream, so the gap is
# deliberately extreme (still a valid CPTP cell — the builder asserts it).
THETA_HI, G_SEEP_HI = 1.2, 0.5


def _spec_at(theta: float, g_seep: float, R: int, N: int, seed: int = 11):
    from qec_twin.forward.scalable.sv_sampler import RunSpec

    return RunSpec(circuit_path=_R01_CIRC, metadata_path=_R01_META, m=0, theta=theta,
                   g_seep=g_seep, g_heat=G_HEAT, arm=ARM, b=B_BIAS,
                   readout_conv="biased_b", N=N, base_seed=seed, R=R, dtype="c128")


def _packed(ss) -> bytes:
    return bytes(np.ascontiguousarray(ss.shots).tobytes())


@requires_cuda
@requires_data
def test_p2ii_table_injection_positive_control():
    """POSITIVE control (catches an INERT seam): at R=1, feeding the lo-cell spec the
    HI cell's table must reproduce the hi-cell STATIC run byte-for-byte (same seeds —
    the trajectory dynamics depend on the tables, not on the spec's theta/g_seep once
    the table is injected). An implementation that silently keeps its internal
    spec-built table would instead reproduce the LO static run — asserted distinct."""
    from qec_twin.forward.scalable.mps_forward import MpsLeakageForward

    R, N = 1, 2
    sched, _ = _sched_and_spec(R=R, N=N)
    fwd = MpsLeakageForward(device=DEVICE)
    spec_lo = _spec_at(THETA, G_SEEP, R, N)
    spec_hi = _spec_at(THETA_HI, G_SEEP_HI, R, N)
    leak_hi = _base_leak(spec_hi)

    ss_hi_static, _ = fwd.sample(spec_hi, sched=sched)
    ss_injected, _ = fwd.sample(spec_lo, sched=sched, leak_slices=[leak_hi])
    ss_lo_static, _ = fwd.sample(spec_lo, sched=sched)

    assert _packed(ss_injected) == _packed(ss_hi_static), \
        "injected hi-table run != hi static run: the caller table is not driving the dynamics"
    assert np.array_equal(np.asarray(ss_injected.diag["terminal_bits"]),
                          np.asarray(ss_hi_static.diag["terminal_bits"]))
    assert _packed(ss_injected) != _packed(ss_lo_static), \
        "hi-injected == lo static: the two cells are indistinguishable at this N/seed " \
        "(re-pick the discriminator cell — this must hold for the test to have teeth)"


@requires_cuda
@requires_data
def test_p2ii_round_indexing_discriminator():
    """ROUND-INDEX discriminator (catches constant-index, shifted, and reversed
    indexing). EXACT leg: with the same seeds, the ROUND-0 syndrome block of the
    [lo,hi] run must equal the [lo,lo] run's (round 0 consumes the same table and the
    same u prefix — byte-identical for a correct implementation; a reversed/shifted
    index puts hi into round 0 and breaks it). Same for [hi,lo] vs [hi,hi].
    INEQUALITY legs: the full records must differ where round 1's table differs
    (an inert round-1 index makes them equal)."""
    from qec_twin.forward.scalable.mps_forward import MpsLeakageForward
    from qec_twin.forward.scalable.sv_sampler import SvSampler

    R, N = 2, 3
    sched, spec = _sched_and_spec(R=R, N=N)
    fwd = MpsLeakageForward(device=DEVICE)
    leak_lo = _base_leak(spec)
    leak_hi = _base_leak(_spec_at(THETA_HI, G_SEEP_HI, R, N))

    runs = {}
    for name, tables in (("lh", [leak_lo, leak_hi]), ("hl", [leak_hi, leak_lo]),
                         ("ll", [leak_lo, leak_lo]), ("hh", [leak_hi, leak_hi])):
        ss, _ = fwd.sample(spec, sched=sched, leak_slices=tables)
        n_stab = int(ss.header["n_stab"])
        syn, _flips = SvSampler.unpack_shots(np.asarray(ss.shots), n_stab, R)
        runs[name] = (_packed(ss), syn)

    # EXACT round-0 prefix identity (round-major layout: bits [0, n_stab) are round 0)
    n_stab = runs["lh"][1].shape[1] // R
    assert np.array_equal(runs["lh"][1][:, :n_stab], runs["ll"][1][:, :n_stab]), \
        "round-0 block of [lo,hi] != [lo,lo]: round 0 is NOT consuming leak_slices[0]"
    assert np.array_equal(runs["hl"][1][:, :n_stab], runs["hh"][1][:, :n_stab]), \
        "round-0 block of [hi,lo] != [hi,hi]: round 0 is NOT consuming leak_slices[0]"
    # round 1's table must matter (an inert/constant index makes these EQUAL)
    assert runs["lh"][0] != runs["ll"][0], \
        "[lo,hi] == [lo,lo]: round 1 ignores its table (inert per-round seam)"
    assert runs["hl"][0] != runs["hh"][0], \
        "[hi,lo] == [hi,hi]: round 1 ignores its table (inert per-round seam)"
    assert runs["lh"][0] != runs["hl"][0], \
        "[lo,hi] == [hi,lo]: the seam is order-blind"
