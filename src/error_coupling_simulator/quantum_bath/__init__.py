"""quantum_bath — the pseudomode-enlarged shared-bath GKSL carrier (dual-axis X+Z syndrome record).

2 data + 2 ancilla + ONE shared bosonic mode, exact-DM (CPU, feasibility-only), measured dual-axis
(X via a_X, Z via a_Z). Provides the shared sigma_z-dephasing + sigma_minus-emission GKSL carrier,
the multi-time record observables (Milz/Budini K, CMI, TV/record-distance), the crow_joynt
classical-field null (the independent-GT dephasing floor), the incoherent-AD null family (the matched
relaxation nulls + the model-free min-TV discriminator), and the anti-toy ground-truth checks.

Boundary: exact-DM feasibility-only (dim = 16*nmax), CPU, evaluator-side research carrier; it is not
an emitted-record production backend. There is no physical ground truth -- oracles are formal
implementation references. Current ownership and tests are documented in this package's README and
``docs/service_status.json``. Wider scientific interpretation remains pending a clean literature audit.
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
    # Bäcker et al., Phys. Rev. Lett. 132, 060402 (2024), arXiv:2310.01205:
    # assisted-entanglement inequality diagnostic. ``inequality_violated=False`` is inconclusive;
    # a positive numerical flag still requires the theorem-hypothesis audit.
    "quantum_memory_witness",
    "concurrence",
    "concurrence_of_assistance",
    "jc_reduced_choi",
    # crow_joynt classical-field null
    "field_null_point",
    "gamma_unit_closed",
    "build_sigma",
    # incoherent-AD nulls + the broader coherent-unitary null
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
