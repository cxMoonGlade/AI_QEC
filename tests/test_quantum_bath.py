"""Package-level verification of error_coupling_simulator.quantum_bath (the P6 pseudomode/shared-bath carrier).

Independently reproduces the CERTIFIED ground-truth numbers of the notion-3 relaxation x dual-axis study
(prereg docs/SIMULATOR.md) THROUGH the migrated package -- so a
migration bug (wrong index/reshape, dropped ft/n3 substitution) fails here. Exact-DM CPU, small nmax; fast.

The load-bearing anti-toy facts this locks in:
  - the dual-ancilla reduced-superop factorization is exact (E_red (x) I_aX (x) I_aZ == full 16*nmax Liouvillian);
  - the sigma_minus EMISSION Liouvillian matches the exact single-excitation amplitude ODE (+ is non-unital);
  - the sigma_z-sector collective-dephasing matches the independent-boson closed form;
  - the crow_joynt covariance closed forms (Gamma_unit + Sigma) match the certified values;
  - K / K_X / K_Z are ALL FORGEABLE by an incoherent AD oriented to the right Bloch axis (the two false-positive
    corrections) -- so the honest discriminator is the model-free record-distance, not K.
"""
import math

import numpy as np
import pytest

qb = pytest.importorskip("error_coupling_simulator.quantum_bath")

ZETA, GAMMA, TAU = 1.0, 0.15, 2.0


def test_crow_joynt_covariance_closed_forms():
    gu = qb.gamma_unit_closed(TAU, ZETA, GAMMA)
    assert gu == pytest.approx(1.32329713, abs=1e-6)
    Sig = qb.build_sigma(3, TAU, ZETA, GAMMA)
    scout = np.array([[2.646594, -0.670271, -1.146587],
                      [-0.670271, 2.646594, -0.670271],
                      [-1.146587, -0.670271, 2.646594]])
    assert np.max(np.abs(Sig - scout)) < 1e-5
    assert np.all(np.linalg.eigvalsh(Sig) > 0)               # positive-definite
    assert Sig[0, 0] == pytest.approx(2.0 * gu, abs=1e-9)     # diagonal = 2*Gamma_unit


def test_factorization_reduced_superop_exact():
    fac = qb.factorization_check(3, ZETA, GAMMA, 0.5, 0.5, 0.35, 0.35, TAU)
    assert fac["max_abs_err"] < 1e-10


def test_extraction_reads_both_parities():
    ext = qb.extraction_gt_check()
    assert ext["worst_err_X"] < 1e-9 and ext["worst_err_Z"] < 1e-9


def test_sigma_z_sector_indep_boson_gt():
    gt = qb.two_qubit_indep_boson_gt(nmax=16, zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5, tau=TAU)
    assert gt["worst_err"] < 1e-6


def test_sigma_minus_emission_matches_amplitude_ode_and_is_non_unital():
    gt = qb.sigma_minus_emission_gt(nmax=16, zeta=ZETA, gamma=GAMMA, g=0.35, tau=TAU)
    assert gt["worst_err"] < 1e-7                              # GKSL p_e(t) == exact 1-excitation ODE
    assert gt["pe_final_gksl"] == pytest.approx(0.7241, abs=1e-3)
    assert gt["pe_final_gksl"] < 0.999                         # non-unital: population genuinely decays


def test_no_bath_record_is_trivial():
    nb = qb.no_bath_sanity(8)
    assert max(nb["K_joint"], nb["K_X"], nb["K_Z"], nb["M_mem"], nb["CMI"]) < 1e-8


def test_quantum_relaxation_record_certified_values():
    r = qb.dual_point(10, ZETA, GAMMA, 0.0, 0.0, 0.35, 0.35, TAU)   # relaxation-only, r=1
    assert sum(r["P_all"].values()) == pytest.approx(1.0, abs=1e-8)
    assert r["K_X"] == pytest.approx(0.056694, abs=2e-4)
    assert r["K_Z"] == pytest.approx(0.201494, abs=2e-4)
    assert r["CMI"] == pytest.approx(0.026479, abs=2e-4)


def test_K_is_forgeable_on_every_axis():
    # the two false-positive corrections: an incoherent AD forges K on the axis it relaxes toward.
    adZ = qb.axis_ad_null_point(p0=0.5, theta0=0.0, phi0=0.0)
    adX = qb.axis_ad_null_point(p0=0.5, theta0=math.pi / 2, phi0=0.0)
    assert adZ["K_Z"] == pytest.approx(0.25, abs=1e-3) and adZ["K_X"] < 1e-6   # Z-AD forges K_Z, not K_X
    assert adX["K_X"] == pytest.approx(0.25, abs=1e-3) and adX["K_Z"] < 1e-6   # X-AD forges K_X, not K_Z


def test_field_null_reproduces_dephasing_and_is_z_inert():
    null = qb.field_null_point(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5, tau=TAU, n_gh=12)
    assert null["norm"] == pytest.approx(1.0, abs=1e-6)
    assert null["K_Z"] < 1e-6                                  # sigma_z field is Z-inert (only X picks up dephasing)
    assert null["K_joint"] < 1e-2                              # small classically-achievable dephasing floor (not 0)


def test_record_distance_relaxation_is_distinguishable_from_incoherent():
    r = qb.dual_point(10, ZETA, GAMMA, 0.0, 0.0, 0.35, 0.35, TAU)
    mintv, _desc = qb.min_tv_to_incoherent(r["P_all"], nm_list=((0.2, 0.2, 1.6),))
    assert mintv >= 1e-3                                       # feasibly distinguishable (not incoherent-reproducible)


def test_backer_witness_finite_gamma_memory_is_genuinely_quantum():
    # Control 3 (Backer PRL 132, 230401, Theorem 1) -- the GENUINE quantum-memory witness: fires on C#(t1)<C(t2),
    # the E#<E CLASSICAL-BOUND violation (keeps the '#'), silent on classical processes (Control 0b). Zero-T AD
    # (our vacuum-mode JC, Choi rank-2 => C#=C) with UNDERDAMPED coupling (g > gamma/2) violates the bound; the
    # OVERDAMPED (Markovian) limit does not. CAVEAT: sufficient-not-necessary; single-time-channel-TOMOGRAPHY
    # (ACTIVE) quantity, NOT the passive record (Flag #1 open); the C#<C margin (~3e-3) convergence is unverified.
    w_phys = qb.quantum_memory_witness(0.35, 0.15, ZETA, TAU, 12)         # underdamped (g=0.35 > gamma/2=0.075)
    w_mark = qb.quantum_memory_witness(0.35, 50.0, ZETA, TAU, 12)         # overdamped / Markovian
    assert w_phys["quantum_memory_required"] is True                      # C#<C fires (genuine, provisional margin)
    assert w_phys["concurrence_revival"] > 1e-3
    assert w_mark["quantum_memory_required"] is False                     # no revival => no quantum memory
    # sanity on the 2-qubit concurrence helpers: a Bell state has C = C# = 1, a product state 0
    bell = 0.5 * np.array([[1, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]], dtype=complex)
    assert qb.concurrence(bell) == pytest.approx(1.0, abs=1e-9)
    assert qb.concurrence_of_assistance(bell) == pytest.approx(1.0, abs=1e-9)


def test_qrt_null_memory_vanishes_in_markovian_limit():
    # Luppi 2605.06427 Eq.24: dual_point_qrt = same model, mode reset to vacuum each round (no cross-round
    # memory). eps_QRT = TV(exact, QRT) = Phi_memory. Prediction (Luppi): Phi_memory -> 0 as gamma -> infinity.
    ex_nm = qb.dual_point(12, ZETA, 0.15, 0.0, 0.0, 0.35, 0.35, TAU)      # non-Markovian
    qrt_nm = qb.dual_point_qrt(12, ZETA, 0.15, 0.0, 0.0, 0.35, 0.35, TAU)
    assert qrt_nm["norm"] == pytest.approx(1.0, abs=1e-8)
    mem_nm = qb.tv_distance(ex_nm["P_all"], qrt_nm["P_all"])
    ex_mk = qb.dual_point(12, ZETA, 50.0, 0.0, 0.0, 0.35, 0.35, TAU)      # Markovian (bad-cavity) limit
    qrt_mk = qb.dual_point_qrt(12, ZETA, 50.0, 0.0, 0.0, 0.35, 0.35, TAU)
    mem_mk = qb.tv_distance(ex_mk["P_all"], qrt_mk["P_all"])
    assert mem_nm > 0.05                                                  # substantial memory at finite gamma
    assert mem_mk < 1e-4                                                  # Phi_memory -> 0 in the Markovian limit


def test_collective_ad_null_absorbs_the_r1_markovian_residual():
    # Control 2 (Fanchini 1301.3146: collective NM is super-additive). At r=1, gamma=50 (Markovian, memory~0)
    # the residual to PER-QUBIT incoherent AD is the COLLECTIVE structure; the Dicke collective-AD null
    # (L=sqrt(Gamma)(sm0+sm1)) should absorb it (per-qubit AD cannot).
    ex = qb.dual_point(12, ZETA, 50.0, 0.0, 0.0, 0.35, 0.35, TAU)        # r=1, Markovian
    per_qubit, _ = qb.min_tv_to_incoherent(ex["P_all"], nm_list=((0.2, 0.2, 1.6),))
    best = min(qb.tv_distance(ex["P_all"], qb.collective_ad_null_point(gamma_c=gc, tau=TAU)["P_all"])
               for gc in (0.002, 0.005, 0.01, 0.02, 0.05))
    assert qb.collective_ad_null_point(gamma_c=0.01, tau=TAU)["norm"] == pytest.approx(1.0, abs=1e-8)
    assert best < 0.1 * per_qubit                                        # collective absorbs what per-qubit cannot


def test_coherent_null_reduces_to_incoherent_and_carries_coherence():
    # (#1) the broader coherent-null family: at U=I, zz=0 it MUST equal the incoherent axis-AD (legitimacy);
    # with a coherent rotation it produces coherence-derived K (unlike the incoherent AD -> ~0 on the Z axis).
    ad = qb.axis_ad_null_point(p0=0.5, theta0=0.0, phi0=0.0)
    coh_id = qb.coherent_ad_null_point(u0=(0, 0, 0), u1=(0, 0, 0), ad0=(0.5, 0.0, 0.0), ad1=(0.5, 0.0, 0.0), zz=0.0)
    assert qb.tv_distance(ad["P_all"], coh_id["P_all"]) < 1e-9          # reduces to the incoherent AD at U=I
    coh = qb.coherent_ad_null_point(u0=(0.0, math.pi / 2, 0.0), u1=(0, 0, 0), ad0=(0.3, 0.0, 0.0),
                                    ad1=(0.3, 0.0, 0.0), zz=0.3)
    assert coh["norm"] == pytest.approx(1.0, abs=1e-6)                  # CPTP (normalized)
    assert coh["K_X"] > 0.05                                            # the coherent rotation genuinely imprints
