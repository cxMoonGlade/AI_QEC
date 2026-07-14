"""quantum_bath — the pseudomode-enlarged shared-bath GKSL carrier (dual-axis X+Z syndrome record).

2 data + 2 ancilla + ONE shared bosonic mode, exact-DM (CPU, feasibility-only), measured dual-axis
(X via a_X, Z via a_Z). Provides the shared sigma_z-dephasing + sigma_minus-emission GKSL carrier,
the multi-time record observables (Milz/Budini K, CMI, TV/record-distance), the crow_joynt
classical-field null (the independent-GT dephasing floor), the incoherent-AD null family (the matched
relaxation nulls + the model-free min-TV discriminator), and the anti-toy ground-truth checks.

Boundary: exact-DM feasibility-only (dim = 16*nmax), CPU, evaluator-side research carrier; it is not
an emitted-record production backend. There is no physical ground truth -- oracles are FORMAL. See
docs/twin_validation/notion3_relaxation_dualaxis_prereg.md for the science + the two registered
false-positive corrections (K/K_X/K_Z are all forgeable; the field-null K is NOT 0).
"""

from .carrier import dual_point, dual_point_qrt
from .crow_joynt import build_sigma, field_null_point, gamma_unit_closed
from .gksl import build_shared_bath_liouvillian
from .memory_witness import (
    concurrence,
    concurrence_of_assistance,
    jc_reduced_choi,
    quantum_memory_witness,
)
from .ground_truth import (
    extraction_gt_check,
    factorization_check,
    no_bath_sanity,
    sigma_minus_emission_gt,
    two_qubit_indep_boson_gt,
)
from .nulls import (
    axis_ad_null_point,
    coherent_ad_null_point,
    collective_ad_null_point,
    min_tv_to_incoherent,
)
from .observables import (
    K_stat_binary,
    K_stat_joint,
    M_mem_stat,
    exact_cmi_bits,
    project_axis,
    record_distance,
    tv_distance,
)

__all__ = [
    # carrier
    "dual_point",
    "dual_point_qrt",
    # observables
    "K_stat_joint",
    "K_stat_binary",
    "project_axis",
    "tv_distance",
    "record_distance",
    "M_mem_stat",
    "exact_cmi_bits",
    # gksl
    "build_shared_bath_liouvillian",
    # Backer GENUINE quantum-memory witness (Control 3): concurrence C#(t1)<C(t2) = E#<E classical-bound
    # violation (2310.01205 Thm 1; single-qubit zero-T AD, C#=C rank-2). This one is a real quantum-memory witness.
    "quantum_memory_witness",
    "concurrence",
    "concurrence_of_assistance",
    "jc_reduced_choi",
    # NB (2026-07-07): the BACKFLOW / NON-MARKOVIANITY witnesses (entropic_memory_witness_single/_two_qubit)
    # + their machinery (negativity, von_neumann_entropy) were RETRACTED as quantum-memory witnesses
    # (2026-07-06, Control 0b: a bare revival drops Backer's classical bound '#', forgeable by classical RTN
    # dephasing -- 2601.18822, 1608.05970) and RETIRED from the package (record: retired/quantum_bath/).
    # crow_joynt classical-field null
    "field_null_point",
    "gamma_unit_closed",
    "build_sigma",
    # incoherent-AD nulls + the broader coherent-unitary null (#1)
    "axis_ad_null_point",
    "coherent_ad_null_point",
    "collective_ad_null_point",
    "min_tv_to_incoherent",
    # anti-toy ground truths
    "factorization_check",
    "extraction_gt_check",
    "two_qubit_indep_boson_gt",
    "sigma_minus_emission_gt",
    "no_bath_sanity",
]
