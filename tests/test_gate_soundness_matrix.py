"""Side A of the TWO-SIDED PER-UNIT standard: the MUTANT x GATE soundness matrix.

THIS FILE IS SIDE A (should-fail-must-fail) of the two-sided verification standard
(``docs/twin_validation/api_hardening_ownership_design.md``, "TWO-SIDED PER-UNIT
EXTENSION"): each row installs ONE surgical sabotage (a MUTANT) on the REAL
module/class attribute of a hardened public unit -- never on the gate's probe side --
and DEMONSTRATES that the corresponding registered gate FAILS. A row that stops
failing means the gate lost its teeth (a Side-A soundness violation); a row must
therefore never be weakened to keep the matrix green -- fix the gate. Side B lives in
``tests/_support/fixtures.py::assert_with_margin`` (margin discipline),
``tests/_support/skip_allowlist.json`` + ``outputs/twin_validation/skip_audit.py``
(skip-allowlist audit), and the precondition-never-fires-in-suite rule.

MATRIX (row -> unit -> mutant -> gate; K-classes per row):

  a  ShotSet.to_det_obs               stab-major transposed det layout      -> test_shotset_records::test_am3_to_det_obs_matches_hand_roll        [K-8/K-2; cuda+data]
  b  ShotSet.syndrome_prefix_bytes    raw-byte-slice (mid-byte bits leak)   -> test_shotset_records::test_a2_syndrome_prefix_midbyte_repack       [K-2; CPU]
  b2 ShotSet.syndrome_prefix_bytes    dead n_rounds (always full R)         -> test_shotset_records::test_a2_syndrome_prefix_midbyte_repack       [K-1; CPU]
  c  ShotSet.packed_bytes             syndrome-bytes-only (flip byte drop)  -> test_shotset_records::test_a2_packed_and_syndrome_prefix_bytes     [K-2; cuda+data]
  d  MpsLeakageForward._leak_sample   strict-< tie-break (registry drift)   -> test_shotset_records::test_am5_leak_sample_tiebreak_registry       [K-3; cuda]
  e  MpsLeakageForward.attach_layout  un-inverted eng<->mps direction       -> test_shotset_records::test_a3_attach_layout_pure_addition          [K-6/K-1; cuda+data]
  f  mps_forward.mps_from_statevector order ignored (identity build)        -> test_shotset_records::test_a3_mps_from_statevector_roundtrip       [K-8/K-1; cuda]
  g  MpsLeakageForward._run_trajectory constant round leak table            -> test_p2_mps_per_round_leak::test_p2ii_round_indexing_discriminator [K-1/K-2; cuda+data]
  h  SvSampler.cptp_residual (sample() entry guard) residual forced to 0.0  -> test_p2_mps_per_round_leak::test_p2ii_entry_guards_reject_bad_tables [K-5/K-4; cuda+data]
  i  experiments._dataset_files       existence-check-only (default reads)  -> test_frontend_experiments::test_env_override_partial_root_resolves_under_override [K-1; data]
  j  experiments.run_spec_from_preset hardcoded seed 0 (arg ignored)        -> test_frontend_experiments::test_run_spec_from_preset_raw_and_wg    [K-1; data]
  k  experiments.leak_slice_table     preset-arm g_seep<->g_heat knob swap  -> test_frontend_experiments::test_leak_slice_table_preset_arm_matches_spec_arm [K-1/K-8; cuda+data]
  l  ExperimentPreset.__post_init__   no-op validator                       -> test_frontend_experiments::test_experiment_preset_validation_killers [K-1; CPU]

NOT-COVERED rows: none -- all 13 registered rows are reachable from a plain call
(rows whose gates take fixtures get them wired explicitly below).

DETECTION SEMANTICS. A gate "fails" when the call raises ``AssertionError`` (plain /
helper asserts) OR ``pytest.fail.Exception`` (``Failed``): a ``pytest.raises(...)``
block that sees NO exception fails via ``pytest.fail``, which raises ``Failed`` --
NOT an AssertionError subclass -- so both channels count as detection. Documented
per-row expected channels: rows i and l detect via ``Failed`` (their sabotage makes
an expected raise not happen); row e's surgical mutant PRESERVES the Mapping/
permutation guards (only the inversion flips), so its gate reaches the direction
assert and detects via ``AssertionError``; row h is detected by the gate's OWN
engineered-violation precondition leg (``assert resid > 1e-8`` measures the residual
through the mutated unit) -- still an ``AssertionError``, and the later
``pytest.raises(AssertionError)`` leg would fail via ``Failed`` regardless.
``pytest.skip.Exception`` PROPAGATES (a skipping gate detected nothing -- the very
escape hatch Side B's allowlist kills); any other exception propagates as a harness
crash, never counted as detection.

FIXTURE WIRING. The gate modules' autouse ``_no_d3_env_override(monkeypatch)``
fixture does NOT run when a gate is called as a plain function, so every row's
MonkeyPatch context deletes ``QEC_TWIN_D3_DATA`` itself before applying the mutant.
Gates with ``(monkeypatch, tmp_path)`` signatures (row i) receive a manually entered
``pytest.MonkeyPatch.context()`` plus this test's own ``tmp_path``.

ALIAS NOTE (row f, the contract's patch-every-alias warning): the roundtrip gate
reaches the unit ONLY via the module object (``mf.mps_from_statevector``), and
``MpsLeakageForward._mps_from_statevector`` delegates through the same module global
at call time (verified by reading both), so the single module-attribute patch covers
every route -- there is no from-import alias to patch.

GPU/data rows carry the canonical conftest markers; CPU rows are unmarked.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Callable, NamedTuple

import numpy as np
import pytest

torch = pytest.importorskip("torch")

# gate modules imported AS MODULES (never `from ... import test_*` -- a name import
# would make pytest collect the gate functions a second time in this module).
import test_frontend_experiments as gate_frontend  # noqa: E402
import test_p2_mps_per_round_leak as gate_p2  # noqa: E402
import test_shotset_records as gate_records  # noqa: E402

from conftest import requires_cuda, requires_data  # noqa: E402
from qec_twin.forward.exact import xzzx_parser as xp  # noqa: E402
from qec_twin.forward.scalable import mps_forward as mf  # noqa: E402
from qec_twin.forward.scalable.mps_forward import MpsLeakageForward  # noqa: E402
from qec_twin.forward.scalable.sv_sampler import RunSpec, ShotSet, SvSampler  # noqa: E402

#: the A1 facade module (same object test_frontend_experiments importorskip'd).
experiments = gate_frontend.experiments

#: ratified decision 7 -- the ONE dataset-root env var (deleted per-row, see docstring).
_ENV = "QEC_TWIN_D3_DATA"


# =========================================================================== #
# Mutants (each reimplements/wraps the REAL unit with EXACTLY ONE behavior     #
# flipped -- surgical sabotage, all guards/conventions otherwise preserved).   #
# =========================================================================== #
def _mutant_to_det_obs_stab_major(self):
    """Row a (K-8 layout drift): decode correctly, then emit the det block
    STAB-MAJOR (stab outer, round inner) instead of the pinned round-major."""
    packed = np.asarray(self.shots)
    n_stab, n_rounds = int(self.header["n_stab"]), int(self.header["R"])
    det, obs = SvSampler.unpack_shots(packed, n_stab, n_rounds)
    n = det.shape[0]
    det_sm = np.ascontiguousarray(
        det.reshape(n, n_rounds, n_stab).transpose(0, 2, 1).reshape(n, n_rounds * n_stab)
    ).astype(np.uint8)
    return {"det": det_sm, "obs": obs}


def _mutant_prefix_raw_byte_slice(self, n_rounds):
    """Row b (K-2 mid-byte boundary): the devious raw byte slice -- leaks the next
    round's bits sharing the boundary byte instead of unpack+truncate+repack."""
    packed = np.asarray(self.shots)
    n_stab = int(self.header["n_stab"])
    return np.ascontiguousarray(
        packed[:, : (int(n_rounds) * n_stab + 7) // 8]).tobytes()


def _mutant_prefix_dead_n_rounds(self, n_rounds):  # noqa: ARG001 -- the sabotage
    """Row b2 (K-1 dead parameter): ``n_rounds`` ignored -- always the full-R
    syndrome repack (correct at n_rounds == R, wrong at every true prefix)."""
    packed = np.asarray(self.shots)
    n_stab, n_rounds_hdr = int(self.header["n_stab"]), int(self.header["R"])
    syn, _flip = SvSampler.unpack_shots(packed, n_stab, n_rounds_hdr)
    return np.packbits(syn, axis=1, bitorder="little").tobytes()


def _mutant_packed_bytes_drop_flip(self):
    """Row c (K-2 boundary): packed buffer WITHOUT the trailing logical-flip byte
    (syndrome bytes only)."""
    packed = np.asarray(self.shots)
    n_stab, n_rounds = int(self.header["n_stab"]), int(self.header["R"])
    return np.ascontiguousarray(packed[:, : (n_rounds * n_stab + 7) // 8]).tobytes()


def _mutant_leak_sample_strict_lt(self, mps, kraus, mps_site, u):
    """Row d (K-3 tie-break drift): the real ``_leak_sample`` body (same RDM-route
    pk, same accumulation order, same apply/renormalize) with the registry's
    NON-STRICT ``u*tot <= cumsum_k`` flipped to strict ``<`` -- the exact drift the
    prereg registry (batched_mps_backend_prereg v2/v5) forbids."""
    site = int(mps_site)
    info: dict = {}
    pk = [float(mps.local_expectation_canonical(
                K.conj().transpose(-1, -2) @ K, site, normalized=False, info=info).real)
          for K in kraus]
    tot = float(sum(pk))
    target = float(u) * tot
    cum = 0.0
    sel = len(pk) - 1
    for k, p in enumerate(pk):
        cum += p
        if target < cum:  # SABOTAGE: strict '<' (registry says NON-STRICT '<=')
            sel = k
            break
    mps.gate_(kraus[sel], where=int(mps_site), contract=True)
    self._renormalize(mps, norm_sq=pk[sel])
    return int(sel)


def _mutant_attach_layout_uninverted(self, order, logical_support):
    """Row e (K-6 direction drift): the real ``attach_layout`` (Mapping rejection
    and permutation validation PRESERVED -- surgical mutant) except ``_eng_to_mps``
    is primed with the UN-INVERTED site->engine reading."""
    if isinstance(order, Mapping):
        raise TypeError(
            "order must be a sequence with order[k] = engine position at MPS "
            "site k (site->engine); got a Mapping -- pass the ORDER TUPLE, not "
            "the eng_to_mps dict")
    order_t = tuple(int(x) for x in order)
    if sorted(order_t) != list(range(len(order_t))):
        raise ValueError(
            f"attach_layout: order must be a permutation of 0..{len(order_t) - 1} "
            f"(got {order!r})")
    self._mps_order = order_t
    # SABOTAGE: un-inverted (site->engine stored as if it were engine->site).
    self._eng_to_mps = {k: order_t[k] for k in range(len(order_t))}
    self._log_eng_support = [int(x) for x in logical_support]


def _apply_mutant_f_ignore_order(mp: pytest.MonkeyPatch) -> None:
    """Row f (K-1 dead order / K-8 convention): ``mps_from_statevector`` builds with
    the IDENTITY order regardless of the ``order`` argument (see ALIAS NOTE)."""
    real = mf.mps_from_statevector

    def _mutant(psi, order, device):
        return real(psi, tuple(range(len(order))), device)  # SABOTAGE: order dropped

    mp.setattr(mf, "mps_from_statevector", _mutant)


def _apply_mutant_g_constant_round(mp: pytest.MonkeyPatch) -> None:
    """Row g (K-1 inert seam / K-2 constant index): wrap the REAL ``_run_trajectory``
    and freeze ``leak_by_round`` to round 0's table for every round."""
    real = MpsLeakageForward._run_trajectory

    def _mutant(self, codestate_mps, marsh, leak_by_round, *args, **kwargs):
        frozen = [leak_by_round[0]] * len(leak_by_round)  # SABOTAGE: constant index
        return real(self, codestate_mps, marsh, frozen, *args, **kwargs)

    mp.setattr(MpsLeakageForward, "_run_trajectory", _mutant)


def _apply_mutant_h_guard_disabled(mp: pytest.MonkeyPatch) -> None:
    """Row h (K-5 vacuity / K-4): ``SvSampler.cptp_residual`` forced to 0.0 --
    the sample() per-round CPTP entry guard can never fire. staticmethod-wrapped so
    both the ``self._host.cptp_residual(t)`` and ``SvSampler(...).cptp_residual(t)``
    call shapes keep working (a bare function would eat ``self``)."""
    mp.setattr(SvSampler, "cptp_residual", staticmethod(lambda kraus: 0.0))


def _apply_mutant_i_existence_only(mp: pytest.MonkeyPatch) -> None:
    """Row i (K-1 dead resolution): the existence-check-only devious implementation
    -- resolves the root with the real arg>env precedence and CHECKS it is a
    directory, then silently reads the DEFAULT root's files anyway."""
    import os

    def _mutant_dataset_files(dataset_root=None):
        from pathlib import Path

        if dataset_root is not None:
            root = Path(dataset_root)
        elif experiments.QEC_TWIN_D3_DATA_ENV in os.environ:
            env_root = os.environ[experiments.QEC_TWIN_D3_DATA_ENV].strip()
            if not env_root:
                raise ValueError(f"env var {experiments.QEC_TWIN_D3_DATA_ENV} is SET but empty")
            root = Path(env_root)
        else:
            root = None
        if root is not None and not root.is_dir():
            raise FileNotFoundError(f"d3 dataset root {root} does not exist")
        # SABOTAGE: root verified, files silently resolved from the DEFAULT root.
        r01_circ, r01_meta = xp.default_r01_paths()
        r10_circ, r10_meta = xp.default_r10_paths()
        return {"r01_circ": r01_circ, "r01_meta": r01_meta,
                "r10_circ": r10_circ, "r10_meta": r10_meta}

    mp.setattr(experiments, "_dataset_files", _mutant_dataset_files)


def _apply_mutant_j_hardcoded_seed(mp: pytest.MonkeyPatch) -> None:
    """Row j (K-1 dead plumbing): ``run_spec_from_preset`` ignores its ``seed``
    argument (always 0); everything else delegates to the real function."""
    real = experiments.run_spec_from_preset

    def _mutant(preset, *, n_shots, n_rounds, seed, m=0, dataset_root=None):  # noqa: ARG001
        return real(preset, n_shots=n_shots, n_rounds=n_rounds, seed=0, m=m,
                    dataset_root=dataset_root)  # SABOTAGE: seed dropped

    mp.setattr(experiments, "run_spec_from_preset", _mutant)


def _apply_mutant_k_knob_swap(mp: pytest.MonkeyPatch) -> None:
    """Row k (K-1/K-8 knob swap): ``leak_slice_table``'s PRESET arm builds its
    sentinel spec with ``g_seep`` and ``g_heat`` SWAPPED; the RunSpec arm delegates
    to the real function (so only the preset arm drifts -- exactly the devious
    implementation the preset-vs-spec equality gate was registered to kill)."""
    real = experiments.leak_slice_table

    def _mutant(preset_or_params, *, device, as_list=False):
        if isinstance(preset_or_params, experiments.ExperimentPreset):
            spec = RunSpec(
                circuit_path="__leak_slice_table_only__",
                theta=experiments.resolve_theta(preset_or_params),
                g_seep=float(preset_or_params.g_heat),   # SABOTAGE: swapped
                g_heat=float(preset_or_params.g_seep),   # SABOTAGE: swapped
                arm=str(preset_or_params.arm),
                b=float(preset_or_params.b_bias),
                readout_conv=str(preset_or_params.readout_conv),
                N=1,
                base_seed=0,
            )
            return real(spec, device=device, as_list=as_list)
        return real(preset_or_params, device=device, as_list=as_list)

    mp.setattr(experiments, "leak_slice_table", _mutant)


def _apply_mutant_l_noop_validator(mp: pytest.MonkeyPatch) -> None:
    """Row l (K-1 validator that never fires): ``ExperimentPreset.__post_init__``
    replaced by a no-op (frozen dataclasses only freeze INSTANCE attribute writes;
    the class attribute patch is legal and is exactly how validation would rot)."""
    mp.setattr(experiments.ExperimentPreset, "__post_init__", lambda self: None)


# =========================================================================== #
# The registry + driver                                                        #
# =========================================================================== #
class Row(NamedTuple):
    unit: str
    mutant_id: str
    gate_name: str
    apply: Callable[[pytest.MonkeyPatch], None]
    call: Callable[..., None]           # call(tmp_path) -> runs the gate
    detection_note: str                 # expected failure channel (docstring detail)


def _call_gate_with_env_fixtures(gate_fn):
    """Wrap a gate that takes (monkeypatch, tmp_path): give it its OWN MonkeyPatch
    context (teardown guaranteed) + this test's tmp_path."""

    def _call(tmp_path):
        with pytest.MonkeyPatch.context() as gate_mp:
            gate_fn(gate_mp, tmp_path)

    return _call


_ROWS = [
    pytest.param(Row(
        unit="ShotSet.to_det_obs", mutant_id="stab_major_transpose",
        gate_name="test_am3_to_det_obs_matches_hand_roll",
        apply=lambda mp: mp.setattr(ShotSet, "to_det_obs", _mutant_to_det_obs_stab_major),
        call=lambda tmp_path: gate_records.test_am3_to_det_obs_matches_hand_roll(),
        detection_note="AssertionError (hand-roll equality / synthetic asymmetric killer)"),
        marks=[requires_cuda, requires_data], id="a-to_det_obs-stab_major_transpose"),
    pytest.param(Row(
        unit="ShotSet.syndrome_prefix_bytes", mutant_id="raw_byte_slice",
        gate_name="test_a2_syndrome_prefix_midbyte_repack",
        apply=lambda mp: mp.setattr(ShotSet, "syndrome_prefix_bytes",
                                    _mutant_prefix_raw_byte_slice),
        call=lambda tmp_path: gate_records.test_a2_syndrome_prefix_midbyte_repack(),
        detection_note="AssertionError (mid-byte transcription mismatch at n_rounds=1)"),
        marks=[], id="b-syndrome_prefix_bytes-raw_byte_slice"),
    pytest.param(Row(
        unit="ShotSet.syndrome_prefix_bytes", mutant_id="dead_n_rounds",
        gate_name="test_a2_syndrome_prefix_midbyte_repack",
        apply=lambda mp: mp.setattr(ShotSet, "syndrome_prefix_bytes",
                                    _mutant_prefix_dead_n_rounds),
        call=lambda tmp_path: gate_records.test_a2_syndrome_prefix_midbyte_repack(),
        detection_note="AssertionError (full-R repack != 1-round prefix)"),
        marks=[], id="b2-syndrome_prefix_bytes-dead_n_rounds"),
    pytest.param(Row(
        unit="ShotSet.packed_bytes", mutant_id="drop_flip_byte",
        gate_name="test_a2_packed_and_syndrome_prefix_bytes",
        apply=lambda mp: mp.setattr(ShotSet, "packed_bytes",
                                    _mutant_packed_bytes_drop_flip),
        call=lambda tmp_path: gate_records.test_a2_packed_and_syndrome_prefix_bytes(),
        detection_note="AssertionError (packed_bytes != contiguous buffer: length)"),
        marks=[requires_cuda, requires_data], id="c-packed_bytes-drop_flip_byte"),
    pytest.param(Row(
        unit="MpsLeakageForward._leak_sample", mutant_id="strict_lt_tiebreak",
        gate_name="test_am5_leak_sample_tiebreak_registry",
        apply=lambda mp: mp.setattr(MpsLeakageForward, "_leak_sample",
                                    _mutant_leak_sample_strict_lt),
        call=lambda tmp_path: gate_records.test_am5_leak_sample_tiebreak_registry(),
        detection_note="AssertionError (exact-boundary leg: '<' selects 1, registry says 0)"),
        marks=[requires_cuda], id="d-_leak_sample-strict_lt_tiebreak"),
    pytest.param(Row(
        unit="MpsLeakageForward.attach_layout", mutant_id="uninverted_direction",
        gate_name="test_a3_attach_layout_pure_addition",
        apply=lambda mp: mp.setattr(MpsLeakageForward, "attach_layout",
                                    _mutant_attach_layout_uninverted),
        call=lambda tmp_path: gate_records.test_a3_attach_layout_pure_addition(),
        detection_note="AssertionError (_eng_to_mps != hand-inverted map; guards preserved)"),
        marks=[requires_cuda, requires_data], id="e-attach_layout-uninverted_direction"),
    pytest.param(Row(
        unit="mps_forward.mps_from_statevector", mutant_id="ignore_order",
        gate_name="test_a3_mps_from_statevector_roundtrip",
        apply=_apply_mutant_f_ignore_order,
        call=lambda tmp_path: gate_records.test_a3_mps_from_statevector_roundtrip(),
        detection_note="AssertionError (raw dense != snake-basis vector at 1e-13)"),
        marks=[requires_cuda], id="f-mps_from_statevector-ignore_order"),
    pytest.param(Row(
        unit="MpsLeakageForward._run_trajectory", mutant_id="constant_round_leak",
        gate_name="test_p2ii_round_indexing_discriminator",
        apply=_apply_mutant_g_constant_round,
        call=lambda tmp_path: gate_p2.test_p2ii_round_indexing_discriminator(),
        detection_note="AssertionError ([lo,hi] == [lo,lo]: round 1 ignores its table)"),
        marks=[requires_cuda, requires_data], id="g-_run_trajectory-constant_round_leak"),
    pytest.param(Row(
        unit="SvSampler.cptp_residual (sample() entry guard)",
        mutant_id="guard_disabled_zero_residual",
        gate_name="test_p2ii_entry_guards_reject_bad_tables",
        apply=_apply_mutant_h_guard_disabled,
        call=lambda tmp_path: gate_p2.test_p2ii_entry_guards_reject_bad_tables(),
        detection_note="AssertionError (gate's own engineered-violation precondition "
                       "measures 0.0 through the mutated unit; the pytest.raises leg "
                       "would fail via Failed regardless)"),
        marks=[requires_cuda, requires_data], id="h-cptp_residual-guard_disabled"),
    pytest.param(Row(
        unit="experiments._dataset_files", mutant_id="existence_check_only",
        gate_name="test_env_override_partial_root_resolves_under_override",
        apply=_apply_mutant_i_existence_only,
        call=_call_gate_with_env_fixtures(
            gate_frontend.test_env_override_partial_root_resolves_under_override),
        detection_note="pytest.fail.Exception (expected FileNotFoundError never raised: "
                       "the mutant silently reads the default root)"),
        marks=[requires_data], id="i-_dataset_files-existence_check_only"),
    pytest.param(Row(
        unit="experiments.run_spec_from_preset", mutant_id="hardcoded_seed_zero",
        gate_name="test_run_spec_from_preset_raw_and_wg",
        apply=_apply_mutant_j_hardcoded_seed,
        call=lambda tmp_path: gate_frontend.test_run_spec_from_preset_raw_and_wg(),
        detection_note="AssertionError (base_seed 0 != 17 in the passthrough tuple)"),
        marks=[requires_data], id="j-run_spec_from_preset-hardcoded_seed_zero"),
    pytest.param(Row(
        unit="experiments.leak_slice_table (preset arm)", mutant_id="seep_heat_knob_swap",
        gate_name="test_leak_slice_table_preset_arm_matches_spec_arm",
        apply=_apply_mutant_k_knob_swap,
        call=lambda tmp_path:
            gate_frontend.test_leak_slice_table_preset_arm_matches_spec_arm(),
        detection_note="AssertionError (preset-arm table != spec-arm table, torch.equal)"),
        marks=[requires_cuda, requires_data], id="k-leak_slice_table-seep_heat_knob_swap"),
    pytest.param(Row(
        unit="ExperimentPreset.__post_init__", mutant_id="noop_validator",
        gate_name="test_experiment_preset_validation_killers",
        apply=_apply_mutant_l_noop_validator,
        call=lambda tmp_path: gate_frontend.test_experiment_preset_validation_killers(),
        detection_note="pytest.fail.Exception (expected ValueError never raised: "
                       "the no-op validator accepts both-theta-conventions-set)"),
        marks=[], id="l-ExperimentPreset_post_init-noop_validator"),
]


def _expect_gate_failure(gate_call: Callable[[], None]):
    """Run the gate under the installed mutant; PASS iff it raises AssertionError or
    pytest Failed (see DETECTION SEMANTICS in the module docstring). Skipped and any
    other exception PROPAGATE (a skip or a harness crash is never a detection)."""
    try:
        gate_call()
    except AssertionError as exc:
        return exc
    except pytest.fail.Exception as exc:  # Failed: a pytest.raises saw no exception
        return exc
    pytest.fail(
        "MUTANT NOT DETECTED: the sabotaged unit PASSED its gate cleanly -- the gate "
        "lost its teeth (Side-A soundness violation; fix the GATE, never this row)")


@pytest.mark.parametrize("row", _ROWS)
def test_mutant_defeats_gate(row: Row, tmp_path):
    """THE matrix driver: install row.apply's sabotage on the REAL unit inside a
    private MonkeyPatch context, call the registered gate as a plain function, and
    require a failure (should-fail-must-fail). The context guarantees the sabotage
    is UNDONE before the next row (K-9: no cross-row contamination)."""
    with pytest.MonkeyPatch.context() as mp:
        # replicate the gate modules' autouse env-isolation fixture (see docstring).
        mp.delenv(_ENV, raising=False)
        row.apply(mp)
        exc = _expect_gate_failure(lambda: row.call(tmp_path))
    assert isinstance(exc, (AssertionError, pytest.fail.Exception)), row.detection_note
