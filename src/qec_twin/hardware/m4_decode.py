"""M4 decoder-side machinery (R2-lite M4, decoder-prior utility rung).

Registration of record: docs/metric_results.md "M4 PRE-REGISTRATION
(decoder-prior utility; recorded 2026-06-10 BEFORE build/run)" -- FROZEN.
Panel blueprint: docs/.reports/m4_panel/ (M4B section 2 machinery pins,
section 3 dependency decision, section 1.6 two-pass; M4C guard G4).

This module owns the decoder side ONLY:

  * S1 decoder pin -- pymatching==2.4.0 at upstream defaults, nothing changed
    (``decode_dem`` / ``decode_with_weights``); decoding is CPU, evaluator-side
    (user-ratified R1: frozen external evaluator, never trained / tuned /
    differentiated -- same category as stim m2d in M1).
  * S6 machinery pins P1a/P1b/P1d/P1e/P1f/P1g as parameterized runners (sample
    lists are ARGUMENTS; the build-phase smoke scope is sample_00 ONLY).
  * S2 per-unit ACTUAL observables (reviewer change-list item 2):
    ``unit_actual_observables`` -- per-shot actual observable bits for
    (data_lo, data_hi) units (the unit's LEFTMOST data qubit's final
    transversal readout XOR its sweep-bit reference, the registered S2
    construction), generalizing the P1b full-chain machinery;
    ``pin_p1b_units`` is the (a)-class full-chain cross-check. Samples 01-99
    are structurally refused without the explicit ``allow_heldout`` flag
    (held-out contract documented on the function).
  * G4 determinism guards: ``jitter_control`` (+/- 1e-9 weight jitter, pinned
    seed 20260610) and ``sim_round_trip`` (decode self-sampled shots from a
    DEM; a miss is a pipeline bug, nothing downstream);
    ``sim_round_trip_check`` applies the DECLARED pass rule (reviewer
    change-list item 5 / C-5): exact-enumeration comparison (a) at toy scale,
    finite/sane/bit-exact-reproducible + second-seed binomial consistency
    ((c), constants declared in ``SIM_ROUND_TRIP_RULE``) at production scale.
  * S4 A3c two-pass temporal reweighting driver (``two_pass_decode``), the
    ONLY arm carrying R-hat into decoding; built-in negative control: exact
    no-op when R-hat == 1.
  * S11 process-parallel CPU decode fleet driver (``decode_fleet``) --
    deterministic ordering and chunking; BUILD ONLY, no fleet runs here.

Isolation: the shipped ``decoding_results/`` artifacts consumed by P1e/P1f are
evaluator-only material, reached exclusively through
``RepCodeD29.evaluator_decoding_artifacts`` (module README contract). Nothing
here feeds the learner.

Epistemic status: every quantity returned here is a measurement; the
certification rules, bands and routing live in the registration (S6/S9/S10)
and are applied by the scoring driver, never re-derived here.
"""

from __future__ import annotations

import hashlib
import multiprocessing
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import numpy as np

from qec_twin.hardware import b8_io, dataset, m1_report, stim_artifacts
from qec_twin.hardware.dataset import RepCodeD29
from qec_twin.numerics import NUMERICAL_ZERO

# --------------------------------------------------------------------------- #
# S1 decoder pin + provenance                                                  #
# --------------------------------------------------------------------------- #

#: The registered decoder version (S1 decoder pin; M4B section 3). The vendored
#: pristine copy under external/baselines is the auditable binary-semantics
#: reference and is NEVER built or imported.
PYMATCHING_PIN = "2.4.0"

#: Wheel provenance, recorded at build per the registration:
#:   conda run -n aiqec python -m pip download --no-deps pymatching==2.4.0 -d /tmp/pm_wheel
#:   sha256sum /tmp/pm_wheel/*.whl
#: Fill both constants from that output (or call ``record_wheel_provenance``).
#: ``None`` means the provenance record is INCOMPLETE and
#: ``pymatching_provenance()["provenance_complete"]`` stays False -- a loud
#: flag, never a silent default.
PYMATCHING_WHEEL_FILENAME: str | None = (
    "pymatching-2.4.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
)
PYMATCHING_WHEEL_SHA256: str | None = (
    "15e6d73153713a8f383f44ba4497d478fb4c4d765fbdd30f9fc1e1d47af75760"
)

#: Registered seed for ALL new M4 randomness (user-ratified R3).
M4_SEED = 20260610

#: S4 clamp convention [1e-6, 1/2 - 1e-6] (declared design constant, class c);
#: used as the default ``eps`` of the A3c bump target min(r*R, 1/2 - eps).
DEFAULT_CLAMP_EPS = 1e-6


def _require_pymatching():
    import pymatching

    return pymatching


def record_wheel_provenance(wheel_path: Path | str) -> dict:
    """sha256 a downloaded pymatching wheel; returns the values to pin above."""

    wheel_path = Path(wheel_path)
    if wheel_path.is_dir():
        wheels = sorted(wheel_path.glob("*.whl"))
        if len(wheels) != 1:
            raise ValueError(f"expected exactly one wheel in {wheel_path}, found {len(wheels)}")
        wheel_path = wheels[0]
    digest = hashlib.sha256(wheel_path.read_bytes()).hexdigest()
    return {"wheel_filename": wheel_path.name, "wheel_sha256": digest}


def pymatching_provenance() -> dict:
    """Decoder provenance record (S1 pin): pinned + installed version, wheel
    sha256 (build-recorded constant) and a live sha256 of the installed
    compiled extension as a supplementary binary fingerprint."""

    installed_version: str | None = None
    binary_sha256: str | None = None
    binary_path: str | None = None
    try:
        import pymatching

        installed_version = getattr(pymatching, "__version__", None)
        try:
            from pymatching import _cpp_pymatching

            binary_path = getattr(_cpp_pymatching, "__file__", None)
            if binary_path:
                binary_sha256 = hashlib.sha256(Path(binary_path).read_bytes()).hexdigest()
        except Exception:  # fingerprint is best-effort, never masks the pin
            pass
    except ImportError:
        pass
    return {
        "pinned_version": PYMATCHING_PIN,
        "installed_version": installed_version,
        "version_match": installed_version == PYMATCHING_PIN,
        "wheel_filename": PYMATCHING_WHEEL_FILENAME,
        "wheel_sha256": PYMATCHING_WHEEL_SHA256,
        "installed_binary_path": binary_path,
        "installed_binary_sha256": binary_sha256,
        "provenance_complete": (
            installed_version == PYMATCHING_PIN and PYMATCHING_WHEEL_SHA256 is not None
        ),
    }


# --------------------------------------------------------------------------- #
# DEM handling + the frozen decode path                                        #
# --------------------------------------------------------------------------- #


def as_dem(dem_like):
    """Coerce to ``stim.DetectorErrorModel``.

    Accepts a stim DEM, a path, DEM text, or any object exposing a ``.dem``
    attribute (duck-typed hook for ``dem_compose`` skeleton objects -- the
    import of that module is never required here).
    """

    import stim

    if isinstance(dem_like, stim.DetectorErrorModel):
        return dem_like
    if hasattr(dem_like, "dem"):
        return as_dem(dem_like.dem)
    if isinstance(dem_like, Path):
        return stim.DetectorErrorModel.from_file(str(dem_like))
    if isinstance(dem_like, str):
        # a single-line existing file path wins (e.g. ".../error_model.dem");
        # anything else is treated as DEM text and parsed by stim
        if "\n" not in dem_like and Path(dem_like).is_file():
            return stim.DetectorErrorModel.from_file(dem_like)
        return stim.DetectorErrorModel(dem_like)
    raise TypeError(f"cannot interpret {type(dem_like).__name__} as a detector error model")


def build_matching(dem_like):
    """``Matching.from_detector_error_model`` at upstream defaults -- the S1
    pin verbatim: no argument is ever passed beyond the DEM itself."""

    pymatching = _require_pymatching()
    return pymatching.Matching.from_detector_error_model(as_dem(dem_like))


def _normalize_dets(num_detectors: int, dets: np.ndarray) -> tuple[np.ndarray, bool]:
    """Explicit bit-packed vs bool handling (S1 pin: never guessed silently).

    bool [shots, D]   -> unpacked uint8, bit_packed=False
    uint8 [shots, ceil(D/8)] -> passed through, bit_packed=True
    Anything else raises (ambiguity is an error, not a guess).
    """

    dets = np.asarray(dets)
    if dets.ndim != 2:
        raise ValueError(f"detection events must be 2D [shots, ...], got shape {dets.shape}")
    packed_width = (int(num_detectors) + 7) // 8
    if dets.dtype == np.bool_:
        if dets.shape[1] != num_detectors:
            raise ValueError(
                f"bool dets width {dets.shape[1]} != num_detectors {num_detectors}"
            )
        return np.ascontiguousarray(dets.astype(np.uint8)), False
    if dets.dtype == np.uint8:
        if dets.shape[1] == packed_width and packed_width != num_detectors:
            return np.ascontiguousarray(dets), True
        if dets.shape[1] == num_detectors and dets.max(initial=0) <= 1:
            # explicit 0/1 uint8 (unpacked); only legal when unambiguous
            if dets.shape[1] == packed_width:
                raise ValueError(
                    "ambiguous uint8 dets: width equals both the packed and the "
                    "unpacked layout -- pass bool for unpacked input"
                )
            return np.ascontiguousarray(dets), False
        raise ValueError(
            f"uint8 dets width {dets.shape[1]} matches neither packed ({packed_width}) "
            f"nor 0/1 unpacked ({num_detectors}) layout"
        )
    raise ValueError(f"dets dtype must be bool or uint8, got {dets.dtype}")


def _unpack_dets(num_detectors: int, dets: np.ndarray) -> np.ndarray:
    """Bool [shots, D] view of either accepted input layout."""

    arr, packed = _normalize_dets(num_detectors, np.asarray(dets))
    if packed:
        return b8_io.unpack_bits(arr, num_detectors)
    return arr.astype(np.bool_)


def decode_dem(dem, dets: np.ndarray) -> np.ndarray:
    """Frozen decode: pymatching at upstream defaults, predictions uint8
    ``[shots, num_observables]``. Bit-packed vs bool input handled explicitly."""

    dem = as_dem(dem)
    matching = build_matching(dem)
    arr, packed = _normalize_dets(dem.num_detectors, dets)
    preds = matching.decode_batch(arr, bit_packed_shots=packed)
    return np.asarray(preds, dtype=np.uint8).reshape(arr.shape[0], -1)


def decode_with_weights(dem, dets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Frozen decode with ``return_weights=True`` (the P1e tie diagnostic)."""

    dem = as_dem(dem)
    matching = build_matching(dem)
    arr, packed = _normalize_dets(dem.num_detectors, dets)
    preds, weights = matching.decode_batch(arr, bit_packed_shots=packed, return_weights=True)
    return (
        np.asarray(preds, dtype=np.uint8).reshape(arr.shape[0], -1),
        np.asarray(weights, dtype=np.float64).reshape(-1),
    )


# --------------------------------------------------------------------------- #
# DEM error parsing (shared by the exact reference, P1e margins, geometry)     #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DemError:
    """One canonicalized DEM error: XOR-folded detector set + observable parity."""

    detectors: tuple[int, ...]
    observables: tuple[int, ...]
    probability: float


def dem_errors(dem) -> list[DemError]:
    dem = as_dem(dem)
    out: list[DemError] = []
    for instruction in dem.flattened():
        if instruction.type != "error":
            continue
        dets: set[int] = set()
        obs: set[int] = set()
        for target in instruction.targets_copy():
            if target.is_separator():
                continue
            if target.is_relative_detector_id():
                dets ^= {int(target.val)}
            elif target.is_logical_observable_id():
                obs ^= {int(target.val)}
        out.append(
            DemError(
                detectors=tuple(sorted(dets)),
                observables=tuple(sorted(obs)),
                probability=float(instruction.args_copy()[0]),
            )
        )
    return out


def _weight(p: float) -> float:
    p = float(p)
    if not 0.0 < p < 1.0:
        raise ValueError(f"edge probability {p} outside (0, 1)")
    return float(np.log((1.0 - p) / p))


# --------------------------------------------------------------------------- #
# In-repo exact minimum-weight reference (P1g; G4 exact prediction)            #
# --------------------------------------------------------------------------- #

#: Tie-detection tolerance for the exact reference (declared comparison
#: convention; ties are excluded-and-counted, never silently broken).
EXACT_TIE_TOL = 1e-9

MAX_ENUM_ERRORS = 20
MAX_ENUM_DETECTORS = 16


@dataclass(frozen=True)
class ExactReference:
    """Brute-force exact minimum-weight decoder over an enumerable toy DEM.

    Enumerates ALL 2^M fault subsets; per syndrome s and observable parity o
    it records the minimum total weight W[s, o] and the exact probability
    P[s, o]. The minimum-weight prediction is argmin_o W[s, o]; a tie is
    |W[s,0] - W[s,1]| <= EXACT_TIE_TOL. On graphlike DEMs this is exactly the
    object MWPM optimizes (per-edge weights log((1-p)/p)), so agreement with
    pymatching is an exact (class a) pin wherever the minimizer is unique.
    """

    num_detectors: int
    num_errors: int
    min_weight: np.ndarray  # [2^D, 2] float64, inf where parity class unreachable
    pred: np.ndarray  # [2^D] int8 argmin parity
    margin: np.ndarray  # [2^D] |W[s,0] - W[s,1]|
    syndrome_prob: np.ndarray  # [2^D, 2] exact joint probability

    @property
    def tie_mask(self) -> np.ndarray:
        finite = np.isfinite(self.min_weight).all(axis=1)
        return finite & (self.margin <= EXACT_TIE_TOL)

    def predictions(self, dets: np.ndarray) -> np.ndarray:
        bits = _unpack_dets(self.num_detectors, dets)
        synd = (bits.astype(np.int64) << np.arange(self.num_detectors, dtype=np.int64)).sum(axis=1)
        return self.pred[synd].astype(np.uint8)


def build_exact_reference(dem, *, max_errors: int = MAX_ENUM_ERRORS) -> ExactReference:
    dem = as_dem(dem)
    if dem.num_observables != 1:
        raise ValueError(f"exact reference requires exactly 1 observable, got {dem.num_observables}")
    if dem.num_detectors > MAX_ENUM_DETECTORS:
        raise ValueError(f"exact reference caps at {MAX_ENUM_DETECTORS} detectors")
    errors = dem_errors(dem)
    if len(errors) > max_errors:
        raise ValueError(f"exact reference caps at {max_errors} errors, got {len(errors)}")

    num_det = int(dem.num_detectors)
    synd = np.zeros(1, dtype=np.int64)
    weight = np.zeros(1, dtype=np.float64)
    parity = np.zeros(1, dtype=np.int64)
    log_odds = np.zeros(1, dtype=np.float64)
    base_log = 0.0
    for err in errors:
        mask = 0
        for d in err.detectors:
            mask |= 1 << d
        par = len(err.observables) & 1
        w = _weight(err.probability)
        base_log += float(np.log1p(-err.probability))
        synd = np.concatenate([synd, synd ^ mask])
        weight = np.concatenate([weight, weight + w])
        parity = np.concatenate([parity, parity ^ par])
        log_odds = np.concatenate(
            [log_odds, log_odds + float(np.log(err.probability) - np.log1p(-err.probability))]
        )
    prob = np.exp(base_log + log_odds)

    n_synd = 1 << num_det
    min_weight = np.full((n_synd, 2), np.inf, dtype=np.float64)
    np.minimum.at(min_weight, (synd, parity), weight)
    syndrome_prob = np.zeros((n_synd, 2), dtype=np.float64)
    np.add.at(syndrome_prob, (synd, parity), prob)
    pred = np.argmin(min_weight, axis=1).astype(np.int8)
    margin = np.abs(min_weight[:, 0] - min_weight[:, 1])
    return ExactReference(
        num_detectors=num_det,
        num_errors=len(errors),
        min_weight=min_weight,
        pred=pred,
        margin=margin,
        syndrome_prob=syndrome_prob,
    )


def all_syndromes(num_detectors: int) -> np.ndarray:
    """Bool ``[2^D, D]`` enumeration, row i = the bits of integer i."""

    idx = np.arange(1 << num_detectors, dtype=np.int64)
    return ((idx[:, None] >> np.arange(num_detectors, dtype=np.int64)[None, :]) & 1).astype(np.bool_)


def exact_decoded_ler(ref: ExactReference, preds_by_syndrome: np.ndarray) -> float:
    """Exact decoded LER of a per-syndrome prediction table under the DEM law."""

    preds = np.asarray(preds_by_syndrome).reshape(-1).astype(np.int64)
    if preds.size != ref.syndrome_prob.shape[0]:
        raise ValueError("prediction table must cover all 2^D syndromes")
    wrong0 = ref.syndrome_prob[np.arange(preds.size), 1 - preds]
    return float(wrong0.sum())


# --------------------------------------------------------------------------- #
# Toy DEM builder (rep-code chain; tests + P1g suite)                          #
# --------------------------------------------------------------------------- #


def _pval(p, *idx) -> float:
    if callable(p):
        return float(p(*idx))
    if isinstance(p, (list, tuple, np.ndarray)):
        return float(p[idx[-1]])
    return float(p)


def toy_chain_dem(
    num_chains: int,
    num_layers: int,
    *,
    p_space=0.05,
    p_time=0.02,
    p_left=0.04,
    p_right=0.06,
):
    """Repetition-code chain DEM with detector coords ``(chain, layer)``.

    Detector id = layer * num_chains + chain. Left boundary edges (the leftmost
    data qubit's column) carry L0 -- the registered window observable
    convention (leftmost data qubit; M4B 2.3). ``p_left`` / ``p_right`` accept
    a scalar or a per-layer sequence; ``p_space`` / ``p_time`` accept a scalar
    or a callable ``(chain_index, layer) -> p``.
    """

    import stim

    if num_chains < 2:
        raise ValueError("toy chain needs >= 2 chains (measure qubits)")
    c_count, l_count = int(num_chains), int(num_layers)

    def det(c: int, layer: int) -> int:
        return layer * c_count + c

    lines: list[str] = []
    for layer in range(l_count):
        lines.append(f"error({_pval(p_left, layer):.17g}) D{det(0, layer)} L0")
        for c in range(c_count - 1):
            lines.append(
                f"error({_pval(p_space, c, layer):.17g}) D{det(c, layer)} D{det(c + 1, layer)}"
            )
        lines.append(f"error({_pval(p_right, layer):.17g}) D{det(c_count - 1, layer)}")
    for c in range(c_count):
        for layer in range(l_count - 1):
            lines.append(
                f"error({_pval(p_time, c, layer):.17g}) D{det(c, layer)} D{det(c, layer + 1)}"
            )
    for layer in range(l_count):
        for c in range(c_count):
            lines.append(f"detector({c}, {layer}) D{det(c, layer)}")
    return stim.DetectorErrorModel("\n".join(lines))


# --------------------------------------------------------------------------- #
# S6 pin runners                                                               #
# --------------------------------------------------------------------------- #


def pin_p1a(ds: RepCodeD29, samples, basis: str, *, chunk_shots: int = 10_000) -> dict:
    """P1a -- m2d parity re-verified via the M1 bit-exact construction
    (literal reuse of ``m1_report.run_p2_sample``; zero new conversion code).
    ``samples`` is an argument: the build-phase smoke scope is sample_00 ONLY."""

    results = [
        m1_report.run_p2_sample(ds, basis, int(s), chunk_shots=chunk_shots, verbose=False)
        for s in samples
    ]
    return {
        "pin": "P1a",
        "basis": basis,
        "samples": [int(s) for s in samples],
        "passed": all(r["passed"] for r in results),
        "results": results,
    }


# ---- P1b: our observable construction at window == full chain ---------------

_MEAS_BASIS = {
    "M": "Z",
    "MZ": "Z",
    "MR": "Z",
    "MRZ": "Z",
    "MX": "X",
    "MRX": "X",
    "MY": "Y",
    "MRY": "Y",
}
_UNSUPPORTED_MEAS = {
    "MPP",
    "MPAD",
    "MXX",
    "MYY",
    "MZZ",
    "HERALDED_ERASE",
    "HERALDED_PAULI_CHANNEL_1",
}
_SWEEP_PAULI = {"CX": "X", "CY": "Y", "CZ": "Z"}


@dataclass(frozen=True)
class ObservableSpec:
    """Static observable construction extracted from a circuit:
    XOR of measurement-record bits + XOR of sweep reference bits."""

    measurement_indices: tuple[int, ...]
    sweep_indices: tuple[int, ...]
    qubits: tuple[int, ...]
    measurement_bases: tuple[str, ...]
    qubit_coords: tuple
    num_measurements: int


def observable_spec(circuit, *, observable_index: int = 0) -> ObservableSpec:
    """Parse OBSERVABLE_INCLUDE(k): absolute record indices of its targets and
    the sweep bits whose controlled Pauli anticommutes with each record's
    measurement basis (the deterministic reference frame). For the d=29
    release this is exactly "final readout of the leftmost data qubit XOR its
    sweep reference" (registered fact I-5)."""

    meas_qubits: list[int] = []
    meas_bases: list[str] = []
    obs_meas: set[int] = set()
    obs_sweep: set[int] = set()
    sweep_gates: list[tuple[int, int, str]] = []  # (sweep bit, qubit, pauli)

    for inst in circuit.flattened():
        name = inst.name
        if name in _MEAS_BASIS:
            for t in inst.targets_copy():
                q = t.qubit_value if t.qubit_value is not None else int(t.value)
                meas_qubits.append(int(q))
                meas_bases.append(_MEAS_BASIS[name])
        elif name in _UNSUPPORTED_MEAS:
            raise NotImplementedError(f"unsupported measuring gate {name} in circuit")
        elif name == "OBSERVABLE_INCLUDE" and int(inst.gate_args_copy()[0]) == observable_index:
            for t in inst.targets_copy():
                if t.is_measurement_record_target:
                    obs_meas ^= {len(meas_qubits) + int(t.value)}
                elif t.is_sweep_bit_target:
                    obs_sweep ^= {int(t.value)}
                else:
                    raise NotImplementedError(
                        f"OBSERVABLE_INCLUDE target {t!r} not a record/sweep target"
                    )
        elif name in _SWEEP_PAULI:
            targets = inst.targets_copy()
            for a, b in zip(targets[0::2], targets[1::2]):
                if a.is_sweep_bit_target:
                    sweep_gates.append((int(a.value), int(b.value), _SWEEP_PAULI[name]))
                elif b.is_sweep_bit_target:
                    sweep_gates.append((int(b.value), int(a.value), _SWEEP_PAULI[name]))

    if not obs_meas:
        raise ValueError(f"no OBSERVABLE_INCLUDE({observable_index}) record targets found")
    indices = tuple(sorted(obs_meas))
    qubits = tuple(meas_qubits[i] for i in indices)
    bases = tuple(meas_bases[i] for i in indices)
    sweep_idx: set[int] = set(obs_sweep)
    for q, basis in zip(qubits, bases):
        for k, gate_q, pauli in sweep_gates:
            if gate_q == q and pauli != basis:  # anticommuting single Paulis differ
                sweep_idx ^= {k}
    coords = circuit.get_final_qubit_coordinates()
    return ObservableSpec(
        measurement_indices=indices,
        sweep_indices=tuple(sorted(sweep_idx)),
        qubits=qubits,
        measurement_bases=bases,
        qubit_coords=tuple(tuple(coords.get(q, ())) for q in qubits),
        num_measurements=len(meas_qubits),
    )


def _bit_column(packed: np.ndarray, bit_index: int) -> np.ndarray:
    return (packed[:, bit_index // 8] >> (bit_index % 8)) & np.uint8(1)


def _compare_observable_construction(
    spec: ObservableSpec, paths, *, chunk_shots: int = 10_000
) -> dict:
    sweep_packed = b8_io.read_b8(paths.sweep_bits, dataset.NUM_SWEEP_BITS)
    sweep_parity = np.zeros(sweep_packed.shape[0], dtype=np.uint8)
    for k in spec.sweep_indices:
        sweep_parity ^= _bit_column(sweep_packed, k)
    shipped = b8_io.read_b8(paths.obs_flips_actual, dataset.NUM_OBSERVABLES)[:, 0] & np.uint8(1)

    mismatched = 0
    first: int | None = None
    total = 0
    for start, packed in b8_io.iter_b8_chunks(
        paths.measurements, dataset.NUM_MEASUREMENTS, chunk_shots=chunk_shots
    ):
        stop = start + packed.shape[0]
        ours = np.zeros(packed.shape[0], dtype=np.uint8)
        for mi in spec.measurement_indices:
            ours ^= _bit_column(packed, mi)
        ours ^= sweep_parity[start:stop]
        diff = np.nonzero(ours != shipped[start:stop])[0]
        if diff.size and first is None:
            first = start + int(diff[0])
        mismatched += int(diff.size)
        total = stop
    return {"total_shots": total, "mismatched_shots": mismatched, "first_mismatch_shot": first}


def pin_p1b(ds: RepCodeD29, basis: str, *, sample: int = 0, chunk_shots: int = 10_000) -> dict:
    """P1b -- our observable construction (leftmost data qubit final readout
    XOR sweep reference) at window == full chain reproduces shipped
    ``obs_flips_actual`` bit-exactly. Circuit choice (ideal first, noisy
    fallback) is reported, never tuned -- the M1 P2 adjudication verbatim."""

    paths = ds.paths(basis, sample)
    attempts: list[dict] = []
    for name, circuit_path in (
        ("circuit_ideal", paths.circuit_ideal),
        ("circuit_noisy_si1000", paths.circuit_noisy_si1000),
    ):
        circuit = stim_artifacts.load_circuit(circuit_path)
        spec = observable_spec(circuit)
        comparison = _compare_observable_construction(spec, paths, chunk_shots=chunk_shots)
        attempts.append({"circuit": name, "spec": spec, **comparison})
        if comparison["mismatched_shots"] == 0:
            break
    final = attempts[-1]
    spec = final["spec"]
    return {
        "pin": "P1b",
        "basis": basis,
        "sample": int(sample),
        "circuit_used": final["circuit"],
        "measurement_indices": spec.measurement_indices,
        "sweep_indices": spec.sweep_indices,
        "qubits": spec.qubits,
        "measurement_bases": spec.measurement_bases,
        "qubit_coords": spec.qubit_coords,
        "total_shots": final["total_shots"],
        "mismatched_shots": final["mismatched_shots"],
        "first_mismatch_shot": final["first_mismatch_shot"],
        "bit_exact": final["mismatched_shots"] == 0,
        "passed": final["mismatched_shots"] == 0,
        "attempts": [
            {k: v for k, v in a.items() if k != "spec"} | {"circuit": a["circuit"]}
            for a in attempts
        ],
    }


# ---- S2 per-unit actual observables (reviewer change-list item 2) ------------


@dataclass(frozen=True)
class UnitObservableSpec:
    """Chain-ordered final-transversal-readout map extracted from a circuit.

    ``data_records[p]`` is the absolute measurement-record index of the final
    transversal readout of the data qubit at CHAIN position ``p`` (0 = the
    leftmost data qubit, the OBSERVABLE_INCLUDE anchor); ``sweep_refs[p]`` is
    that qubit's sweep-bit reference: the sweep bits whose sweep-controlled
    Pauli ANTICOMMUTES with its readout basis (XOR-folded with the
    observable's explicit sweep targets at position 0 -- exactly the P1b
    construction at the anchor, so unit == full chain is the P1b path).

    Chain order is derived STRUCTURALLY, never from record order: the final
    measurement instruction's records form the data block; final-layer
    detectors referencing exactly two block records are the data-adjacency
    edges; the unique path through that graph, walked from the
    OBSERVABLE_INCLUDE anchor (which must be a degree-1 endpoint), is the
    chain order. Every structural violation raises -- never guessed.
    """

    num_measurements: int
    num_data: int
    data_records: tuple[int, ...]
    data_qubits: tuple[int, ...]
    data_bases: tuple[str, ...]
    sweep_refs: tuple[tuple[int, ...], ...]
    anchor_record: int


def unit_observable_spec(circuit, *, observable_index: int = 0) -> UnitObservableSpec:
    """Parse a rep-code circuit into the per-data-qubit observable map
    (the S2 registered construction, generalizing ``observable_spec``)."""

    meas_qubits: list[int] = []
    meas_bases: list[str] = []
    obs_meas: set[int] = set()
    obs_sweep: set[int] = set()
    sweep_gates: list[tuple[int, int, str]] = []  # (sweep bit, qubit, pauli)
    detector_recs: list[frozenset] = []
    last_block: tuple[int, int] | None = None  # (first record, count)

    for inst in circuit.flattened():
        name = inst.name
        if name in _MEAS_BASIS:
            start = len(meas_qubits)
            for t in inst.targets_copy():
                q = t.qubit_value if t.qubit_value is not None else int(t.value)
                meas_qubits.append(int(q))
                meas_bases.append(_MEAS_BASIS[name])
            last_block = (start, len(meas_qubits) - start)
        elif name in _UNSUPPORTED_MEAS:
            raise NotImplementedError(f"unsupported measuring gate {name} in circuit")
        elif name == "DETECTOR":
            recs: set[int] = set()
            for t in inst.targets_copy():
                if t.is_measurement_record_target:
                    recs ^= {len(meas_qubits) + int(t.value)}
            detector_recs.append(frozenset(recs))
        elif name == "OBSERVABLE_INCLUDE" and int(inst.gate_args_copy()[0]) == observable_index:
            for t in inst.targets_copy():
                if t.is_measurement_record_target:
                    obs_meas ^= {len(meas_qubits) + int(t.value)}
                elif t.is_sweep_bit_target:
                    obs_sweep ^= {int(t.value)}
                else:
                    raise NotImplementedError(
                        f"OBSERVABLE_INCLUDE target {t!r} not a record/sweep target"
                    )
        elif name in _SWEEP_PAULI:
            targets = inst.targets_copy()
            for a, b in zip(targets[0::2], targets[1::2]):
                if a.is_sweep_bit_target:
                    sweep_gates.append((int(a.value), int(b.value), _SWEEP_PAULI[name]))
                elif b.is_sweep_bit_target:
                    sweep_gates.append((int(b.value), int(a.value), _SWEEP_PAULI[name]))

    if last_block is None:
        raise ValueError("circuit contains no measurement instruction")
    block = tuple(range(last_block[0], last_block[0] + last_block[1]))
    block_set = set(block)
    if len(block) < 2:
        raise ValueError("final measurement block has < 2 records; no chain to order")
    if len(obs_meas) != 1:
        raise ValueError(
            f"OBSERVABLE_INCLUDE({observable_index}) must anchor exactly one final-readout "
            f"record, got {sorted(obs_meas)}"
        )
    anchor = next(iter(obs_meas))
    if anchor not in block_set:
        raise ValueError(
            f"observable anchor record {anchor} is not in the final measurement block "
            f"[{block[0]}, {block[-1]}]"
        )

    adjacency: dict[int, set[int]] = {r: set() for r in block}
    for recs in detector_recs:
        inter = sorted(recs & block_set)
        if len(inter) > 2:
            raise ValueError(
                f"a detector touches {len(inter)} final-readout records (expected <= 2)"
            )
        if len(inter) == 2:
            a, b = inter
            adjacency[a].add(b)
            adjacency[b].add(a)

    degrees = {r: len(n) for r, n in adjacency.items()}
    endpoints = [r for r, d in degrees.items() if d == 1]
    if any(d not in (1, 2) for d in degrees.values()) or len(endpoints) != 2:
        raise ValueError(
            f"final-readout adjacency is not a single path (degree census "
            f"{sorted(degrees.values())})"
        )
    if anchor not in endpoints:
        raise ValueError(f"observable anchor record {anchor} is not a chain endpoint")
    order = [anchor]
    prev: int | None = None
    while len(order) < len(block):
        nxt = [n for n in adjacency[order[-1]] if n != prev]
        if len(nxt) != 1:
            raise ValueError("final-readout path walk is ambiguous (not a simple path)")
        prev = order[-1]
        order.append(nxt[0])
    if set(order) != block_set:
        raise ValueError("final-readout path does not cover the full data block")

    sweep_refs: list[tuple[int, ...]] = []
    for rec in order:
        q, basis = meas_qubits[rec], meas_bases[rec]
        ref: set[int] = set(obs_sweep) if rec == anchor else set()
        for k, gate_q, pauli in sweep_gates:
            if gate_q == q and pauli != basis:  # anticommuting single Paulis differ
                ref ^= {k}
        sweep_refs.append(tuple(sorted(ref)))
    return UnitObservableSpec(
        num_measurements=len(meas_qubits),
        num_data=len(order),
        data_records=tuple(order),
        data_qubits=tuple(meas_qubits[r] for r in order),
        data_bases=tuple(meas_bases[r] for r in order),
        sweep_refs=tuple(sweep_refs),
        anchor_record=int(anchor),
    )


def _spec_circuit(paths) -> tuple[object, str]:
    """Ideal-first / noisy-fallback circuit choice for spec parsing (the M1 P2
    adjudication order; correctness is pinned by ``pin_p1b_units``, never by
    the file choice itself)."""

    for name, candidate in (
        ("circuit_ideal", paths.circuit_ideal),
        ("circuit_noisy_si1000", paths.circuit_noisy_si1000),
    ):
        if Path(candidate).is_file():
            return stim_artifacts.load_circuit(candidate), name
    raise FileNotFoundError(
        f"no circuit artifact found under {Path(paths.circuit_ideal).parent}"
    )


def _validate_sample_access(sample: int, allow_heldout: bool) -> int:
    """HELD-OUT CONTRACT (S1 splits): samples 01-99 are refused without an
    explicit ``allow_heldout=True``. The staged M4 runner (m4_report) sets the
    flag ONLY inside its held-out stage (S12 order freeze: after the G2
    manifest checks and the persisted one-pass attempt record); build code,
    pins and tests never pass it."""

    sample = int(sample)
    if not 0 <= sample <= 99:
        raise ValueError(f"sample {sample} outside the release range 0..99")
    if sample >= 1 and not allow_heldout:
        raise ValueError(
            f"sample_{sample:02d} is held-out/escrow material: samples 01-99 are "
            "refused without allow_heldout=True (set ONLY by the staged runner's "
            "held-out stage; see _validate_sample_access)"
        )
    return sample


def _validate_units(units, num_data: int) -> list[tuple[int, int]]:
    """Units are ``(data_lo, data_hi)`` INCLUSIVE data-qubit index pairs in
    B1's subchain/window convention: window w => ``(w + 1, w + 5)``; a d'
    partition passes its ``(lo, hi)``; full chain => ``(0, num_data - 1)``.
    Only ``data_lo`` selects the observable; ``data_hi`` is validated only."""

    validated: list[tuple[int, int]] = []
    for unit in units:
        if isinstance(unit, (int, np.integer)):
            raise ValueError(
                f"unit {unit!r} must be a (data_lo, data_hi) pair, not a bare index"
            )
        try:
            pair = tuple(int(v) for v in unit)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"unit {unit!r} must be a (data_lo, data_hi) pair") from exc
        if len(pair) != 2:
            raise ValueError(f"unit {unit!r} must be a (data_lo, data_hi) pair")
        lo, hi = pair
        if not 0 <= lo < hi <= num_data - 1:
            raise ValueError(
                f"unit ({lo}, {hi}) outside the data-qubit range 0..{num_data - 1} "
                "(data_lo < data_hi required)"
            )
        validated.append((lo, hi))
    if not validated:
        raise ValueError("units must be a non-empty sequence of (data_lo, data_hi) pairs")
    return validated


def unit_actual_observables(
    ds: RepCodeD29,
    basis: str,
    sample: int,
    units,
    *,
    allow_heldout: bool = False,
    chunk_shots: int = 10_000,
) -> np.ndarray:
    """S2 per-unit ACTUAL observable bits (reviewer change-list item 2: the
    error-array source for every statistic).

    For each unit -- a ``(data_lo, data_hi)`` INCLUSIVE data-qubit subchain
    or window in B1's convention (window w => ``(w+1, w+5)``; a d' partition
    => its ``(lo, hi)``; full chain => ``(0, 28)`` on the d=29 release) --
    returns the per-shot actual observable: the unit's LEFTMOST data qubit's
    final transversal readout XOR its sweep-bit reference (the registered S2
    construction). Class (a) anchor: at unit == full chain this reproduces
    shipped ``obs_flips_actual`` bit-exactly (``pin_p1b_units``; the P1b
    machinery generalized, the P1b path itself untouched).

    Returns uint8 ``[n_shots, len(units)]`` (shots-first; column j = unit j).
    Efficiency: ONE chunk-streamed pass over ``measurements.b8`` plus one
    read of ``sweep_bits.b8`` per (basis, sample), vectorized over units and
    shots (per-chunk byte-column XORs, deduped across units sharing a
    leftmost qubit) -- the ``pin_p1e`` streaming pattern.

    HELD-OUT CONTRACT: ``sample`` in 1..99 raises ValueError unless
    ``allow_heldout=True`` is passed explicitly; the staged M4 runner sets it
    ONLY inside the held-out stage (after the G2 freeze checks and the
    persisted one-pass attempt record). Build code, pins and tests operate on
    sample_00 at the default False.
    """

    sample = _validate_sample_access(sample, allow_heldout)
    paths = ds.paths(basis, sample)
    circuit, _ = _spec_circuit(paths)
    spec = unit_observable_spec(circuit)
    validated = _validate_units(units, spec.num_data)

    n_shots = b8_io.num_shots_in_file(paths.measurements, spec.num_measurements)
    out = np.empty((n_shots, len(validated)), dtype=np.uint8)
    if n_shots == 0:
        return out

    sweep_size = Path(paths.sweep_bits).stat().st_size
    if sweep_size % n_shots != 0:
        raise ValueError(
            f"sweep_bits size {sweep_size} is not a multiple of the measurement "
            f"shot count {n_shots}"
        )
    sweep_bytes = sweep_size // n_shots
    positions = [lo for lo, _ in validated]
    max_sweep = max((max(spec.sweep_refs[p], default=-1) for p in positions), default=-1)
    if max_sweep >= 8 * sweep_bytes:
        raise ValueError(
            f"sweep bit {max_sweep} outside the {8 * sweep_bytes}-bit packed sweep layout"
        )
    sweep_packed = np.fromfile(str(paths.sweep_bits), dtype=np.uint8).reshape(
        n_shots, sweep_bytes
    )
    parity_by_pos: dict[int, np.ndarray] = {}
    for p in set(positions):
        par = np.zeros(n_shots, dtype=np.uint8)
        for k in spec.sweep_refs[p]:
            par ^= _bit_column(sweep_packed, k)
        parity_by_pos[p] = par

    records = [spec.data_records[p] for p in positions]
    for start, packed in b8_io.iter_b8_chunks(
        paths.measurements, spec.num_measurements, chunk_shots=chunk_shots
    ):
        stop = start + packed.shape[0]
        col_by_record = {rec: _bit_column(packed, rec) for rec in set(records)}
        for j, (p, rec) in enumerate(zip(positions, records)):
            out[start:stop, j] = col_by_record[rec] ^ parity_by_pos[p][start:stop]
    return out


def pin_p1b_units(
    ds: RepCodeD29,
    basis: str,
    *,
    sample: int = 0,
    extra_units=(),
    chunk_shots: int = 10_000,
) -> dict:
    """P1b-units -- the (a)-class cross-check for ``unit_actual_observables``
    (registered S2 cross-check, generalizing pin P1b):

    (i) the per-unit spec at chain position 0 is IDENTICAL to the registered
        P1b full-chain spec (record index + sweep set) -- so the P1b
        bit-exact pin transfers to the per-unit construction by identity;
    (ii) the streamed unit construction at unit == full chain reproduces
        shipped ``obs_flips_actual`` bit-exactly (one measurements pass).

    ``extra_units`` are reported (mean, constancy) for plausibility, never
    gated here. Build smoke scope: sample_00 ONLY (samples 01-99 are refused
    structurally; the pin never passes ``allow_heldout``)."""

    sample = _validate_sample_access(sample, allow_heldout=False)
    paths = ds.paths(basis, sample)
    circuit, circuit_used = _spec_circuit(paths)
    uspec = unit_observable_spec(circuit)
    p1b_spec = observable_spec(circuit)
    spec_match = (
        (uspec.data_records[0],) == p1b_spec.measurement_indices
        and uspec.sweep_refs[0] == p1b_spec.sweep_indices
    )

    full = (0, uspec.num_data - 1)
    units = [full, *extra_units]
    arr = unit_actual_observables(ds, basis, sample, units, chunk_shots=chunk_shots)
    shipped = b8_io.read_b8(paths.obs_flips_actual, dataset.NUM_OBSERVABLES)[:, 0] & np.uint8(1)
    if shipped.shape[0] != arr.shape[0]:
        raise ValueError(
            f"obs_flips_actual has {shipped.shape[0]} shots, measurements stream "
            f"has {arr.shape[0]}"
        )
    diff = np.nonzero(arr[:, 0] != shipped)[0]
    extra_rows = []
    for j, unit in enumerate(units[1:], start=1):
        col = arr[:, j]
        extra_rows.append(
            {
                "unit": tuple(int(v) for v in unit),
                "mean": float(col.mean()) if col.size else float("nan"),
                "nonconstant": bool(col.size and col.min() != col.max()),
            }
        )
    return {
        "pin": "P1b-units",
        "basis": basis,
        "sample": int(sample),
        "circuit_used": circuit_used,
        "num_data": uspec.num_data,
        "full_unit": full,
        "spec_match": bool(spec_match),
        "anchor_record": uspec.anchor_record,
        "anchor_sweep_ref": uspec.sweep_refs[0],
        "total_shots": int(arr.shape[0]),
        "mismatched_shots": int(diff.size),
        "first_mismatch_shot": int(diff[0]) if diff.size else None,
        "bit_exact": bool(diff.size == 0),
        "extra_units": extra_rows,
        "passed": bool(diff.size == 0 and spec_match),
    }


# ---- P1d: pymatching determinism --------------------------------------------


def pin_p1d(dem, dets: np.ndarray) -> dict:
    """P1d -- two independent decode runs (fresh ``Matching`` builds) plus a
    same-object repeat are bit-identical."""

    dem = as_dem(dem)
    arr, packed = _normalize_dets(dem.num_detectors, dets)
    m_a = build_matching(dem)
    m_b = build_matching(dem)
    p_a = np.asarray(m_a.decode_batch(arr, bit_packed_shots=packed), dtype=np.uint8)
    p_b = np.asarray(m_b.decode_batch(arr, bit_packed_shots=packed), dtype=np.uint8)
    p_a2 = np.asarray(m_a.decode_batch(arr, bit_packed_shots=packed), dtype=np.uint8)
    bit_identical = bool(np.array_equal(p_a, p_b) and np.array_equal(p_a, p_a2))
    return {
        "pin": "P1d",
        "n_shots": int(arr.shape[0]),
        "bit_identical": bit_identical,
        "passed": bit_identical,
    }


# ---- P1e: shipped-prediction reproduction -----------------------------------


def _forced_observable_matching(dem):
    """Matching over the DEM with L0 rewritten as an extra detector D(num_det):
    decoding ``[dets | b]`` returns the minimum weight over the b-parity class.
    The weight margin |w1 - w0| on a shot is the registered tie diagnostic."""

    import stim

    dem = as_dem(dem)
    if dem.num_observables != 1:
        raise ValueError(f"forced matching requires exactly 1 observable, got {dem.num_observables}")
    d_obs = int(dem.num_detectors)
    lines: list[str] = []
    for err in dem_errors(dem):
        dets = list(err.detectors)
        if not dets and not err.observables:
            continue  # XOR-cancelled no-op error: invisible to any decoder
        if len(err.observables) & 1:
            if len(dets) >= 2:
                raise NotImplementedError(
                    "L0 on a 2-detector error would force a hyperedge; the margin "
                    "diagnostic covers boundary-carried observables only (the d=29 "
                    "release's RL DEM carries L0 on arity-1 errors exclusively)"
                )
            dets.append(d_obs)
        targets = " ".join(f"D{d}" for d in dets)
        lines.append(f"error({err.probability:.17g}) {targets}")
    lines.append(f"detector D{d_obs}")
    forced_dem = stim.DetectorErrorModel("\n".join(lines))
    return build_matching(forced_dem)


@dataclass(frozen=True)
class P1eSampleResult:
    basis: str
    sample: int
    n_shots: int
    n_mismatch: int
    mismatch_fraction: float
    mismatch_shot_ids: tuple[int, ...]
    weight_margins: np.ndarray  # |w(forced=1) - w(forced=0)| on mismatched shots
    margin_cap_hit: bool
    ours_vs_actual_flips: int  # context only: XOR(our pred, obs_flips_actual)
    shipped_vs_actual_flips: int  # context only: XOR(shipped pred, obs_flips_actual)


def pin_p1e(
    ds: RepCodeD29,
    samples,
    basis: str,
    *,
    chunk_shots: int = 2_000,
    margin_cap: int = 10_000,
    shot_slice=None,
) -> dict:
    """P1e -- decode the shipped RL ``error_model.dem`` with the frozen
    decoder and compare per shot against shipped ``obs_flips_predicted``.

    Returns the MEASUREMENTS only (mismatch fraction + weight-margin
    distribution on mismatched shots); the certification rule and routing
    (bit-exact OR tie-attributed; >1e-3 => halt + degeneracy audit) live in
    the registration and are applied by the scoring driver. ``samples`` is an
    argument; the build-phase smoke scope is sample_00 ONLY (train-side).
    """

    per_sample: list[P1eSampleResult] = []
    for sample in samples:
        sample = int(sample)
        art = ds.evaluator_decoding_artifacts(basis, sample)
        paths = ds.paths(basis, sample)
        dem = as_dem(art.error_model_dem)
        if dem.num_detectors != dataset.NUM_DETECTORS:
            raise ValueError(
                f"shipped DEM has {dem.num_detectors} detectors, "
                f"expected {dataset.NUM_DETECTORS}"
            )
        matching = build_matching(dem)

        mismatch_ids: list[int] = []
        ours_vs_actual = 0
        shipped_vs_actual = 0
        total = 0
        for start, packed in b8_io.iter_b8_chunks(
            paths.detection_events,
            dataset.NUM_DETECTORS,
            chunk_shots=chunk_shots,
            shot_slice=shot_slice,
        ):
            stop = start + packed.shape[0]
            preds = np.asarray(
                matching.decode_batch(packed, bit_packed_shots=True), dtype=np.uint8
            ).reshape(packed.shape[0], -1)[:, 0]
            shipped = (
                b8_io.read_b8(art.obs_flips_predicted, dataset.NUM_OBSERVABLES, (start, stop))[:, 0]
                & np.uint8(1)
            )
            actual = (
                b8_io.read_b8(paths.obs_flips_actual, dataset.NUM_OBSERVABLES, (start, stop))[:, 0]
                & np.uint8(1)
            )
            diff = np.nonzero(preds != shipped)[0]
            mismatch_ids.extend(int(start + i) for i in diff)
            ours_vs_actual += int(np.count_nonzero(preds != actual))
            shipped_vs_actual += int(np.count_nonzero(shipped != actual))
            total += packed.shape[0]

        margin_ids = mismatch_ids[: int(margin_cap)]
        margins = np.zeros(0, dtype=np.float64)
        if margin_ids:
            forced = _forced_observable_matching(dem)
            rows = []
            for shot in margin_ids:
                packed_row = b8_io.read_b8(
                    paths.detection_events, dataset.NUM_DETECTORS, (shot, shot + 1)
                )
                rows.append(b8_io.unpack_bits(packed_row, dataset.NUM_DETECTORS)[0])
            base = np.stack(rows).astype(np.uint8)
            forced0 = np.concatenate([base, np.zeros((base.shape[0], 1), np.uint8)], axis=1)
            forced1 = np.concatenate([base, np.ones((base.shape[0], 1), np.uint8)], axis=1)
            _, w0 = forced.decode_batch(forced0, return_weights=True)
            _, w1 = forced.decode_batch(forced1, return_weights=True)
            margins = np.abs(np.asarray(w1, np.float64) - np.asarray(w0, np.float64))

        per_sample.append(
            P1eSampleResult(
                basis=basis,
                sample=sample,
                n_shots=total,
                n_mismatch=len(mismatch_ids),
                mismatch_fraction=len(mismatch_ids) / total if total else 0.0,
                mismatch_shot_ids=tuple(mismatch_ids),
                weight_margins=margins,
                margin_cap_hit=len(mismatch_ids) > len(margin_ids),
                ours_vs_actual_flips=ours_vs_actual,
                shipped_vs_actual_flips=shipped_vs_actual,
            )
        )
    return {
        "pin": "P1e",
        "basis": basis,
        "samples": [int(s) for s in samples],
        "results": per_sample,
        "max_mismatch_fraction": max((r.mismatch_fraction for r in per_sample), default=0.0),
    }


# ---- P1f: cross-sample DEM hash audit (report-only) --------------------------


def pin_p1f(ds: RepCodeD29, samples, *, bases=None) -> dict:
    """P1f -- sha256 of each shipped RL ``error_model.dem`` file, grouped by
    identical digest across (basis, sample). REPORT-ONLY (no gate)."""

    bases = tuple(bases) if bases is not None else ds.bases
    hashes: dict[tuple[str, int], str] = {}
    for basis in bases:
        for sample in samples:
            path = ds.evaluator_decoding_artifacts(basis, int(sample)).error_model_dem
            hashes[(basis, int(sample))] = hashlib.sha256(path.read_bytes()).hexdigest()
    groups: dict[str, list[tuple[str, int]]] = {}
    for key, digest in hashes.items():
        groups.setdefault(digest, []).append(key)
    return {
        "pin": "P1f",
        "report_only": True,
        "hashes": hashes,
        "groups": {d: sorted(ks) for d, ks in groups.items()},
        "num_distinct": len(groups),
    }


# ---- P1g: pymatching vs the in-repo exact reference on toy DEMs --------------


def _p1g_toys() -> list[tuple[str, object]]:
    """Fixed enumerable toy suite (seeded generic probabilities: no exact ties
    by design; tie count is asserted zero, never silently broken)."""

    rng = np.random.default_rng(M4_SEED)

    def draw():
        return float(rng.uniform(0.02, 0.25))

    toys: list[tuple[str, object]] = []
    toys.append(
        (
            "chain_c2_l3",
            toy_chain_dem(
                2,
                3,
                p_space=lambda c, layer: 0.03 + 0.011 * c + 0.007 * layer,
                p_time=lambda c, layer: 0.02 + 0.009 * c + 0.005 * layer,
                p_left=[draw() for _ in range(3)],
                p_right=[draw() for _ in range(3)],
            ),
        )
    )
    toys.append(
        (
            "chain_c3_l3",
            toy_chain_dem(
                3,
                3,
                p_space=lambda c, layer: 0.025 + 0.013 * c + 0.006 * layer,
                p_time=lambda c, layer: 0.018 + 0.008 * c + 0.004 * layer,
                p_left=[draw() for _ in range(3)],
                p_right=[draw() for _ in range(3)],
            ),
        )
    )
    toys.append(
        (
            "chain_c2_l4_asym",
            toy_chain_dem(
                2,
                4,
                p_space=lambda c, layer: 0.21 - 0.017 * layer,
                p_time=lambda c, layer: 0.012 + 0.019 * layer,
                p_left=[draw() for _ in range(4)],
                p_right=[draw() for _ in range(4)],
            ),
        )
    )
    return toys


def pin_p1g() -> dict:
    """P1g -- exact agreement between pymatching (upstream defaults) and the
    in-repo brute-force exact minimum-weight reference on enumerable toy DEMs,
    over ALL 2^D syndromes per toy. Class (a): zero disagreements, zero ties."""

    results = []
    for name, dem in _p1g_toys():
        ref = build_exact_reference(dem)
        dets = all_syndromes(ref.num_detectors)
        pm_preds = decode_dem(dem, dets)[:, 0]
        ties = ref.tie_mask
        disagree = np.nonzero((pm_preds.astype(np.int8) != ref.pred) & ~ties)[0]
        nonzero_margin = ref.margin[np.isfinite(ref.margin) & (ref.margin > EXACT_TIE_TOL)]
        results.append(
            {
                "toy": name,
                "num_detectors": ref.num_detectors,
                "num_errors": ref.num_errors,
                "num_syndromes": int(dets.shape[0]),
                "num_ties": int(ties.sum()),
                "num_disagreements": int(disagree.size),
                "first_disagreement": int(disagree[0]) if disagree.size else None,
                "min_nonzero_margin": float(nonzero_margin.min()) if nonzero_margin.size else None,
                "passed": bool(disagree.size == 0 and ties.sum() == 0),
            }
        )
    return {"pin": "P1g", "results": results, "passed": all(r["passed"] for r in results)}


# --------------------------------------------------------------------------- #
# G4 guards: jitter control + sim round-trip                                   #
# --------------------------------------------------------------------------- #


def _edge_key(node1: int, node2) -> tuple:
    if node2 is None or node2 < 0:
        return (int(node1), None)
    a, b = int(node1), int(node2)
    return (a, b) if a <= b else (b, a)


def jitter_control(
    dem,
    dets: np.ndarray,
    eps: float = 1e-9,
    seed: int = M4_SEED,
    *,
    n_repeats: int = 1,
) -> float:
    """G4 jitter guard -- re-decode under independent uniform(+/-eps) weight
    jitter (pinned seed 20260610); returns the decision-flip rate.

    The registered consequence (flip rate >= 1/3 of a claimed delta-p =>
    downgrade to class b) is applied by the scoring driver.
    """

    pymatching = _require_pymatching()
    dem = as_dem(dem)
    base = build_matching(dem)
    arr, packed = _normalize_dets(dem.num_detectors, dets)
    base_preds = np.asarray(base.decode_batch(arr, bit_packed_shots=packed), dtype=np.uint8)
    edges = base.edges()
    rng = np.random.default_rng(int(seed))

    flips = 0
    total = 0
    for _ in range(int(n_repeats)):
        jittered = pymatching.Matching()
        for node1, node2, attrs in edges:
            w = float(attrs["weight"]) + float(rng.uniform(-eps, eps))
            ep = attrs.get("error_probability")
            ep = None if ep is None or ep < 0 else float(ep)
            fault_ids = attrs.get("fault_ids") or set()
            if node2 is None:
                jittered.add_boundary_edge(
                    int(node1), fault_ids=fault_ids, weight=w, error_probability=ep
                )
            else:
                jittered.add_edge(
                    int(node1), int(node2), fault_ids=fault_ids, weight=w, error_probability=ep
                )
        if jittered.num_detectors != base.num_detectors:
            raise ValueError(
                "jittered graph lost detectors (edge-free detectors in the DEM); "
                "jitter control unavailable for this DEM"
            )
        preds = np.asarray(jittered.decode_batch(arr, bit_packed_shots=packed), dtype=np.uint8)
        if preds.shape != base_preds.shape:
            raise ValueError("jittered decode changed the prediction shape")
        flips += int(np.count_nonzero(np.any(preds != base_preds, axis=1)))
        total += int(arr.shape[0])
    return flips / total if total else 0.0


class SimRoundTripResult(NamedTuple):
    """``sim_ler``  = decoded logical error rate measured on shots sampled
    from the DEM itself (decode prediction XOR sampled actual observable).
    ``predicted_ler`` = exact decoded-LER prediction by full enumeration of
    the same DEM under the same decoder (NaN when the DEM is not enumerable).
    Conservative-reading note (flagged in the build report): the registration
    names the pair "(sim LER, predicted LER)" without defining either; this
    mapping makes the G4 check sharp (MC measurement vs exact expectation)."""

    sim_ler: float
    predicted_ler: float
    raw_flip_rate: float
    n_shots: int
    seed: int


def _sample_and_decode(dem, n_shots: int, seed: int):
    """One sim-round-trip leg: sample from the DEM itself (stim, seeded),
    decode with the frozen decoder; returns (preds, obs, sim_ler, raw_rate)."""

    sampler = dem.compile_sampler(seed=int(seed))
    det_data, obs_data, _ = sampler.sample(int(n_shots))
    det_data = np.asarray(det_data, dtype=np.bool_)
    obs_data = np.asarray(obs_data, dtype=np.uint8).reshape(det_data.shape[0], -1)
    preds = decode_dem(dem, det_data)
    sim_ler = float(np.mean(np.any(preds != obs_data, axis=1)))
    raw_flip_rate = float(np.mean(np.any(obs_data != 0, axis=1)))
    return preds, obs_data, sim_ler, raw_flip_rate


def _enumerable_predicted_ler(dem) -> float:
    """Exact decoded-LER expectation by full enumeration (class a) when the
    DEM is enumerable; NaN otherwise (declared, never silent)."""

    if (
        dem.num_observables == 1
        and dem.num_detectors <= MAX_ENUM_DETECTORS
        and len(dem_errors(dem)) <= MAX_ENUM_ERRORS
    ):
        ref = build_exact_reference(dem)
        pm_table = decode_dem(dem, all_syndromes(ref.num_detectors))[:, 0]
        return exact_decoded_ler(ref, pm_table)
    return float("nan")


def sim_round_trip(dem, n_shots: int, seed: int = M4_SEED) -> SimRoundTripResult:
    """G4 sim round-trip -- sample shots from the DEM itself via stim, decode
    them back. MEASUREMENTS only; the registered pass rule lives in
    ``sim_round_trip_check`` / ``SIM_ROUND_TRIP_RULE``."""

    dem = as_dem(dem)
    _, _, sim_ler, raw_flip_rate = _sample_and_decode(dem, n_shots, seed)
    return SimRoundTripResult(
        sim_ler=sim_ler,
        predicted_ler=_enumerable_predicted_ler(dem),
        raw_flip_rate=raw_flip_rate,
        n_shots=int(n_shots),
        seed=int(seed),
    )


# ---- G4 sim-round-trip PASS RULE (reviewer change-list item 5; C-5) ----------

#: Declared constants of the registered sim-round-trip pass rule -- no silent
#: constants (S6/G4; epistemic classes per the registration discipline):
#:   * exact enumeration of an enumerable toy DEM is class (a);
#:   * SIM_ROUND_TRIP_Z (binomial sigmas) is the declared (c) significance
#:     convention for every MC comparison inside the rule;
#:   * SIM_ROUND_TRIP_SECOND_SEED_OFFSET derives the second INDEPENDENT
#:     sampling seed (seed2 = seed + offset), declared (c) design constant;
#:   * SIM_ROUND_TRIP_SANE_LER_BOUNDS is the (c) OPEN-interval sanity
#:     tripwire on the production-scale measured LER.
SIM_ROUND_TRIP_Z = 5.0
SIM_ROUND_TRIP_SECOND_SEED_OFFSET = 1
SIM_ROUND_TRIP_SANE_LER_BOUNDS = (0.0, 0.5)

#: Serializable declaration of the pass rule -- the staged runner (B3) embeds
#: this verbatim in the G2 freeze-manifest ``extra`` (reviewer item 5), so the
#: rule is frozen BEFORE the held-out stage and never re-derived at scoring.
SIM_ROUND_TRIP_RULE = {
    "guard": "G4 sim round-trip (per arm)",
    "toy_enumerable": (
        "predicted_ler by full enumeration is exact (a); pass iff "
        "|sim_ler - predicted_ler| <= Z binomial sigmas of the prediction "
        "((c) declared band) AND the sample+decode is bit-exactly "
        "reproducible across two runs at the same seed AND a second "
        "independent sampling seed agrees within a two-sample binomial "
        "band ((c))"
    ),
    "production": (
        "exact enumeration unavailable (predicted_ler = NaN, declared); the "
        "G4 role is the PIPELINE check, all components (c): decoded LER on "
        "self-sampled shots must be FINITE, sane (inside the open interval "
        "sane_ler_bounds), bit-exactly reproducible across two independent "
        "sample+decode runs at the same seed, and consistent with the MC "
        "estimate from a second independent sampling seed within a "
        "two-sample binomial band; any failure = pipeline bug, nothing "
        "downstream"
    ),
    "z_sigmas": SIM_ROUND_TRIP_Z,
    "second_seed_offset": SIM_ROUND_TRIP_SECOND_SEED_OFFSET,
    "sane_ler_bounds": SIM_ROUND_TRIP_SANE_LER_BOUNDS,
    "epistemic": {
        "exact_enumeration": "a",
        "comparison_bands": "c",
        "sanity_tripwire": "c",
        "reproducibility": "a (bit-exact identity check)",
    },
}


class SimRoundTripCheck(NamedTuple):
    """G4 sim-round-trip pass-rule evaluation (reviewer change-list item 5).

    ``passed`` is the field the staged runner consumes (the measurement-only
    ``SimRoundTripResult`` carries no pass field by design); ``failures``
    names every tripped component. ``exact_within_band`` is None at
    production scale (the exact branch does not apply); ``predicted_ler`` is
    NaN there (declared, never silent)."""

    scale: str  # "toy-enumerable" | "production"
    passed: bool
    failures: tuple[str, ...]
    sim_ler: float
    predicted_ler: float
    raw_flip_rate: float
    reproducible_bit_exact: bool
    sim_ler_second_seed: float
    second_seed: int
    binomial_consistent: bool
    binomial_band: float
    exact_within_band: bool | None
    n_shots: int
    seed: int


def sim_round_trip_check(dem, n_shots: int, seed: int = M4_SEED) -> SimRoundTripCheck:
    """Apply the REGISTERED G4 sim-round-trip pass rule (``SIM_ROUND_TRIP_RULE``;
    reviewer change-list item 5 / adjudication C-5).

    Toy scale (enumerable DEM, auto-detected by the P1g enumeration caps): the
    exact-enumeration prediction is class (a); the MC-vs-exact comparison band
    (SIM_ROUND_TRIP_Z binomial sigmas + the NUMERICAL_ZERO floor) is (c).
    Production scale (every real window/subchain arm): the G4 role is the
    PIPELINE check, all components declared (c) -- finite, sane (open
    SIM_ROUND_TRIP_SANE_LER_BOUNDS), bit-exactly reproducible across two
    independent sample+decode runs at the same seed, and binomially consistent
    with a second independent sampling seed (seed + offset). Both scales gate
    on reproducibility and second-seed consistency. A failed check is a
    pipeline bug -- nothing downstream runs (S6/G4 routing, applied by the
    scoring driver)."""

    dem = as_dem(dem)
    n_shots = int(n_shots)
    if n_shots <= 0:
        raise ValueError(f"n_shots must be positive, got {n_shots}")
    preds1, obs1, sim_ler, raw_flip_rate = _sample_and_decode(dem, n_shots, seed)
    preds2, obs2, sim_ler_repeat, _ = _sample_and_decode(dem, n_shots, seed)
    reproducible = bool(
        np.array_equal(obs1, obs2)
        and np.array_equal(preds1, preds2)
        and sim_ler == sim_ler_repeat
    )
    second_seed = int(seed) + SIM_ROUND_TRIP_SECOND_SEED_OFFSET
    _, _, sim_ler_b, _ = _sample_and_decode(dem, n_shots, second_seed)
    p_bar = 0.5 * (sim_ler + sim_ler_b)
    binomial_band = float(
        SIM_ROUND_TRIP_Z * np.sqrt(max(p_bar * (1.0 - p_bar), 0.0) * 2.0 / n_shots)
        + NUMERICAL_ZERO
    )
    binomial_consistent = bool(abs(sim_ler - sim_ler_b) <= binomial_band)

    predicted_ler = _enumerable_predicted_ler(dem)
    enumerable = bool(np.isfinite(predicted_ler))
    scale = "toy-enumerable" if enumerable else "production"

    failures: list[str] = []
    if not np.isfinite(sim_ler):
        failures.append("sim_ler is not finite")
    if not reproducible:
        failures.append("sample+decode not bit-exactly reproducible across two runs")
    if not binomial_consistent:
        failures.append(
            f"second-seed MC estimate {sim_ler_b:.6g} deviates from {sim_ler:.6g} "
            f"beyond the (c) two-sample binomial band {binomial_band:.3g}"
        )
    exact_within_band: bool | None = None
    if enumerable:
        sigma = float(np.sqrt(predicted_ler * (1.0 - predicted_ler) / n_shots))
        exact_within_band = bool(
            abs(sim_ler - predicted_ler) <= SIM_ROUND_TRIP_Z * sigma + NUMERICAL_ZERO
        )
        if not exact_within_band:
            failures.append(
                f"MC sim_ler {sim_ler:.6g} outside the (c) band around the exact (a) "
                f"enumeration prediction {predicted_ler:.6g}"
            )
    else:
        lo, hi = SIM_ROUND_TRIP_SANE_LER_BOUNDS
        if not (np.isfinite(sim_ler) and lo < sim_ler < hi):
            failures.append(
                f"production sim_ler {sim_ler:.6g} outside the open sane interval "
                f"({lo}, {hi})"
            )
    return SimRoundTripCheck(
        scale=scale,
        passed=not failures,
        failures=tuple(failures),
        sim_ler=sim_ler,
        predicted_ler=predicted_ler,
        raw_flip_rate=raw_flip_rate,
        reproducible_bit_exact=reproducible,
        sim_ler_second_seed=sim_ler_b,
        second_seed=second_seed,
        binomial_consistent=binomial_consistent,
        binomial_band=binomial_band,
        exact_within_band=exact_within_band,
        n_shots=n_shots,
        seed=int(seed),
    )


# --------------------------------------------------------------------------- #
# A3c two-pass temporal reweighting (S4; window instrument only, never gate)   #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SpaceEdgeGeometry:
    """Space-edge identification from DEM detector coordinates.

    Convention (declared; composed window DEMs must follow it): detector
    coordinate[0] = chain index, coordinate[-1] = layer index. A bulk space
    edge is a same-layer adjacent-chain pair -> qubit key
    ``(c, c+1)``; a weight-1 boundary edge at the min/max chain is the
    boundary data qubit's space edge -> keys ``(min_chain-1, min_chain)`` /
    ``(max_chain, max_chain+1)`` (the registered sub-chain projection turns
    one-detector-outside errors into exactly these). Time edges, diagonals
    and unclassified singles are never bumped and never trigger.
    """

    classify: dict  # edge key (u, v|None) -> ("space", qubit_key, layer)
    by_qubit_layer: dict  # (qubit_key, layer) -> edge key
    num_space_edges: int
    num_unclassified_singles: int


def space_edge_geometry(dem) -> SpaceEdgeGeometry:
    dem = as_dem(dem)
    coords = dem.get_detector_coordinates()
    if len(coords) < dem.num_detectors:
        raise ValueError("DEM lacks detector coordinates; A3c geometry unavailable")

    def chain_layer(det: int) -> tuple[int, int]:
        vals = coords[det]
        if len(vals) < 2:
            raise ValueError(f"detector D{det} coordinates {vals} lack (chain, ..., layer)")
        c, layer = float(vals[0]), float(vals[-1])
        ci, li = int(round(c)), int(round(layer))
        if abs(c - ci) > 1e-9 or abs(layer - li) > 1e-9:
            raise ValueError(f"detector D{det} coordinates {vals} are not integral (chain, layer)")
        return ci, li

    chains = [chain_layer(d)[0] for d in range(dem.num_detectors)]
    min_chain, max_chain = min(chains), max(chains)

    classify: dict = {}
    by_qubit_layer: dict = {}
    unclassified = 0
    for err in dem_errors(dem):
        dets = err.detectors
        if len(dets) == 1:
            c, layer = chain_layer(dets[0])
            if c == min_chain:
                qkey = (min_chain - 1, min_chain)
            elif c == max_chain:
                qkey = (max_chain, max_chain + 1)
            else:
                unclassified += 1
                continue
            key = (dets[0], None)
        elif len(dets) == 2:
            (c0, l0), (c1, l1) = chain_layer(dets[0]), chain_layer(dets[1])
            if l0 == l1 and abs(c0 - c1) == 1:
                qkey = (min(c0, c1), max(c0, c1))
                layer = l0
                key = _edge_key(dets[0], dets[1])
            else:
                continue  # time / diagonal / long-range: never bumped
        else:
            continue  # hyperedge: outside the graphlike contract, never bumped
        classify[key] = ("space", qkey, layer)
        existing = by_qubit_layer.get((qkey, layer))
        if existing is not None and existing != key:
            raise ValueError(
                f"two distinct space edges at qubit {qkey} layer {layer}: {existing} vs {key}"
            )
        by_qubit_layer[(qkey, layer)] = key
    return SpaceEdgeGeometry(
        classify=classify,
        by_qubit_layer=by_qubit_layer,
        num_space_edges=len(by_qubit_layer),
        num_unclassified_singles=unclassified,
    )


def two_pass_decode(
    dem_or_skel,
    dets: np.ndarray,
    rR_table: dict,
    eps: float = DEFAULT_CLAMP_EPS,
) -> np.ndarray:
    """A3c per the registration (S4): pass-1 static decode via
    ``decode_to_edges_array``; for every space edge (j, t) in the pass-1
    correction set, reweight that qubit's space edges at t+-1 from r-hat to
    ``min(r_hat * R_hat, 1/2 - eps)``; re-decode. Exact identity carried:
    P(flip_{t+1} | flip_t) = p01 p10 / r = r R (class a).

    ``rR_table`` maps qubit keys (see :class:`SpaceEdgeGeometry`) to
    ``(r_hat, R_hat)``; qubits absent from the table are never reweighted
    (conservative: only declared qubits carry R-hat into decoding). Exact
    no-op guarantee: a bump whose target probability equals the edge's current
    probability (e.g. R_hat == 1 on the static-arm value r-hat) is skipped, so
    the w20/w21 negative control is bit-exact by construction.

    WINDOW instrument only, never the gate. Returns uint8
    ``[shots, num_observables]``.
    """

    dem = as_dem(dem_or_skel)
    geometry = space_edge_geometry(dem)
    matching = build_matching(dem)
    num_obs = int(matching.num_fault_ids)

    edge_attrs: dict = {}
    for node1, node2, attrs in matching.edges():
        edge_attrs[_edge_key(node1, node2)] = {
            "weight": float(attrs["weight"]),
            "error_probability": attrs.get("error_probability"),
            "fault_ids": set(attrs.get("fault_ids") or set()),
        }

    def _apply(key: tuple, weight: float, probability, fault_ids: set) -> None:
        ep = None if probability is None or probability < 0 else float(probability)
        if key[1] is None:
            matching.add_boundary_edge(
                key[0], fault_ids=fault_ids, weight=weight, error_probability=ep,
                merge_strategy="replace",
            )
        else:
            matching.add_edge(
                key[0], key[1], fault_ids=fault_ids, weight=weight, error_probability=ep,
                merge_strategy="replace",
            )

    bits = _unpack_dets(dem.num_detectors, dets)
    preds = np.zeros((bits.shape[0], num_obs), dtype=np.uint8)
    for shot in range(bits.shape[0]):
        row = np.ascontiguousarray(bits[shot], dtype=np.uint8)
        pass1 = np.asarray(matching.decode_to_edges_array(row))

        bumped: dict = {}  # edge key -> p_new
        for u, v in pass1.reshape(-1, 2):
            key = _edge_key(int(u), int(v) if int(v) >= 0 else None)
            cls = geometry.classify.get(key)
            if cls is None:
                continue
            _, qkey, layer = cls
            rr = rR_table.get(qkey)
            if rr is None:
                continue
            r_hat, big_r = float(rr[0]), float(rr[1])
            p_new = max(min(r_hat * big_r, 0.5 - float(eps)), NUMERICAL_ZERO)
            for dt in (-1, 1):
                nb_key = geometry.by_qubit_layer.get((qkey, layer + dt))
                if nb_key is None:
                    continue
                current = edge_attrs[nb_key]["error_probability"]
                if current is not None and float(current) == p_new:
                    continue  # exact no-op (the R-hat == 1 negative control)
                bumped[nb_key] = p_new

        if not bumped:
            # pass-1 stands: the prediction is the correction set's parity
            pred_row = np.zeros(num_obs, dtype=np.uint8)
            for u, v in pass1.reshape(-1, 2):
                key = _edge_key(int(u), int(v) if int(v) >= 0 else None)
                for fid in edge_attrs[key]["fault_ids"]:
                    pred_row[fid] ^= 1
            preds[shot] = pred_row
            continue

        try:
            for key, p_new in bumped.items():
                attrs = edge_attrs[key]
                _apply(key, _weight(p_new), p_new, attrs["fault_ids"])
            second = np.asarray(matching.decode(row), dtype=np.uint8).reshape(-1)
            preds[shot, : second.size] = second
        finally:
            for key in bumped:
                attrs = edge_attrs[key]
                _apply(key, attrs["weight"], attrs["error_probability"], attrs["fault_ids"])
    return preds


# --------------------------------------------------------------------------- #
# S11 decode fleet driver (process-parallel CPU; BUILD ONLY -- never run here) #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DecodeJob:
    """One fleet unit: a DEM (as text, pickle-safe) + a shot source.

    Exactly one of ``dets`` (in-memory bool/packed array) or ``dets_path``
    (a stim .b8 file streamed in ``chunk_shots`` pieces) must be set.
    ``mode``: "static" (frozen decode) or "two_pass" (A3c; window arm only).
    """

    job_id: str
    dem_text: str
    dets: np.ndarray | None = None
    dets_path: str | None = None
    bits_per_shot: int | None = None
    shot_slice: tuple[int, int] | None = None
    chunk_shots: int = 20_000
    mode: str = "static"
    rR_table: dict | None = None
    eps: float = DEFAULT_CLAMP_EPS


@dataclass(frozen=True)
class FleetResult:
    job_id: str
    n_shots: int
    preds: np.ndarray  # uint8 [shots, num_observables]


def _job_chunks(job: DecodeJob, num_detectors: int):
    if (job.dets is None) == (job.dets_path is None):
        raise ValueError(f"job {job.job_id}: exactly one of dets / dets_path must be set")
    if job.dets is not None:
        dets = np.asarray(job.dets)
        step = max(int(job.chunk_shots), 1)
        for start in range(0, dets.shape[0], step):
            yield dets[start : start + step]
    else:
        bits = int(job.bits_per_shot or num_detectors)
        for _, packed in b8_io.iter_b8_chunks(
            job.dets_path, bits, chunk_shots=int(job.chunk_shots), shot_slice=job.shot_slice
        ):
            yield packed


def _run_decode_job(job: DecodeJob) -> FleetResult:
    import stim

    dem = stim.DetectorErrorModel(job.dem_text)
    chunks: list[np.ndarray] = []
    if job.mode == "static":
        matching = build_matching(dem)
        for chunk in _job_chunks(job, dem.num_detectors):
            arr, packed = _normalize_dets(dem.num_detectors, chunk)
            preds = matching.decode_batch(arr, bit_packed_shots=packed)
            chunks.append(np.asarray(preds, dtype=np.uint8).reshape(arr.shape[0], -1))
    elif job.mode == "two_pass":
        for chunk in _job_chunks(job, dem.num_detectors):
            chunks.append(two_pass_decode(dem, chunk, job.rR_table or {}, job.eps))
    else:
        raise ValueError(f"job {job.job_id}: unknown mode {job.mode!r}")
    preds = (
        np.concatenate(chunks, axis=0) if chunks else np.zeros((0, dem.num_observables), np.uint8)
    )
    return FleetResult(job_id=job.job_id, n_shots=int(preds.shape[0]), preds=preds)


def decode_fleet(jobs, n_workers: int = 16, *, mp_context: str = "spawn") -> list[FleetResult]:
    """Process-parallel CPU decode driver (ratified R1: decoding never claims
    GPU). Deterministic by construction: fixed per-job chunking, per-shot
    independence, and ``Pool.map`` order preservation -- results align 1:1
    with the input job order. BUILD ONLY: this function is never invoked on
    the fleet during the build phase.
    """

    jobs = list(jobs)
    if not jobs:
        return []
    if int(n_workers) <= 1 or len(jobs) == 1:
        return [_run_decode_job(job) for job in jobs]
    ctx = multiprocessing.get_context(mp_context)
    with ctx.Pool(processes=min(int(n_workers), len(jobs))) as pool:
        return pool.map(_run_decode_job, jobs, chunksize=1)


__all__ = [
    "PYMATCHING_PIN",
    "PYMATCHING_WHEEL_FILENAME",
    "PYMATCHING_WHEEL_SHA256",
    "M4_SEED",
    "DEFAULT_CLAMP_EPS",
    "EXACT_TIE_TOL",
    "pymatching_provenance",
    "record_wheel_provenance",
    "as_dem",
    "build_matching",
    "decode_dem",
    "decode_with_weights",
    "dem_errors",
    "DemError",
    "ExactReference",
    "build_exact_reference",
    "all_syndromes",
    "exact_decoded_ler",
    "toy_chain_dem",
    "pin_p1a",
    "pin_p1b",
    "pin_p1b_units",
    "pin_p1d",
    "pin_p1e",
    "pin_p1f",
    "pin_p1g",
    "ObservableSpec",
    "observable_spec",
    "UnitObservableSpec",
    "unit_observable_spec",
    "unit_actual_observables",
    "P1eSampleResult",
    "jitter_control",
    "SimRoundTripResult",
    "sim_round_trip",
    "SIM_ROUND_TRIP_Z",
    "SIM_ROUND_TRIP_SECOND_SEED_OFFSET",
    "SIM_ROUND_TRIP_SANE_LER_BOUNDS",
    "SIM_ROUND_TRIP_RULE",
    "SimRoundTripCheck",
    "sim_round_trip_check",
    "SpaceEdgeGeometry",
    "space_edge_geometry",
    "two_pass_decode",
    "DecodeJob",
    "FleetResult",
    "decode_fleet",
]
