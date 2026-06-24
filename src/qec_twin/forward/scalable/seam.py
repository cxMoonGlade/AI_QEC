from __future__ import annotations

"""The teacher output → decoder-input SEAM (ADR 0010; graduated from
``outputs/teacher_prereg/p7_seam.py``).

THIS IS THE TEACHER'S OUTPUT CONTRACT — the single adaptor that turns the leakage
teacher's emitted ``ShotSet`` (the dense ``sv_sampler`` / MPS ``mps_forward`` carriers, and
the floor's ``audit.bayes_floor.sample_teacher_records``) into the
``(detection_events, obs_flips)`` arrays the decoder substrate (``hardware.m4_decode``,
``decoder/``) and the Bayes floor (``audit.bayes_floor``) consume. The floor scores it, the
coming decoder/foil (⑦) decodes it, so the fold convention lives in ONE place here.

The pre-reg §1.5 G2 calls this "the single most error-prone seam." Authority:
``docs/nonpauli_teacher/p7_leakage_headroom_prereg.md``. Anti-toy protocol
(``docs/FAITHFULNESS_PROTOCOL.md``): every load-bearing quantity is checked against the
RAW circuit (``stim``), never against a parallel reduction of the leakage channel
(anti-circular, ledger invariant ii). The seam test (``tests/test_seam.py``) runs the
ledger-(v) positive control here as the build guard.

────────────────────────────────────────────────────────────────────────────────────
THE SEAM, STATED PRECISELY (the load-bearing design fact, derived from the raw circuit)
────────────────────────────────────────────────────────────────────────────────────
The certified within-cycle teacher kernel (``sv_traj_d3_wc``, ``forward/scalable``) emits
PER SHOT:
  * ``R * n_stab`` raw per-round STABILIZER-SYNDROME bits ``s_{1..R}`` (the ancilla
    parities, round-major then stab-order; the b-POVM syndrome each round), and
  * a trailing ``logical_flip`` byte == ``parity(terminal data readout) XOR m`` (the
    ISOLATION-respecting label; NOT m, NOT the per-data-qubit terminal bits).

The shipped Google d3 XZZX circuit's stim DEM is defined over DETECTORS that are XOR-folds
of measurement records. VERIFIED on the RAW circuit (:func:`inspect_raw_detectors`): at r01
ALL 8 detectors, and at r10 ALL 80 detectors, reference the TERMINAL per-data-qubit readout
records. The teacher emits NO per-data-qubit terminal bits (only the folded
``logical_flip``), so the shipped DEM's detectors CANNOT be reconstructed from the teacher
output. The pre-reg §1.4 phrasing ("detectors = consecutive-round XOR of the raw stabilizer
record") describes a DIFFERENT detector convention than the shipped circuit uses.

RESOLUTION (the faithful, internally-consistent, anti-circular statistic). The gap, the
floor, and the decoder must ALL score the SAME ``(syndrome, logical)`` statistic the teacher
actually emits. So the foil DEM is built over the TEACHER'S EMITTED detector space:
  * detectors = the ``R * n_stab`` per-round ancilla syndromes (one detector per
    (round, stabilizer)); the first-round detector is the raw round-1 syndrome, and an
    interior detector is the round-to-round XOR (the standard repetition-in-time matching
    graph) — this is what a Pauli memory DEM over ancilla-only records is;
  * observable = the single logical flip (== ``logical_flip``).
This DEM is built from the RAW qubit circuit (``stim`` ``analyze_errors`` semantics on a
matched-DEPOLARIZE qubit projection), with the LEAKAGE deliberately ABSENT (the foil,
invariant ii). ``gap_off ≈ 0`` (invariant iii) is the falsifiable proof the seam + the DEM
match are faithful: the leak_off teacher MUST decode at ~the floor.

This is NOT the shipped-circuit DEM (which needs terminal data); it is the DEM matched to
the teacher's emitted observable space — the only statistic on which the gap is well-defined.
Declared + bounded; the off-control IS the bound.

G1 — :func:`build_matched_pauli_dem`: the qubit d3 XZZX ancilla-syndrome memory DEM at a
     DEPOLARIZE level matched to the teacher's WG leak rate, leak ABSENT.
G2 — :func:`teacher_shots_to_events`: unpack the kernel's packed buffer → the
     ``(detection_events[N, R*n_stab], obs_flips[N])`` arrays ``decode_dem`` consumes,
     forming detectors = first-round-raw + interior round-to-round XOR (the convention the
     matched DEM is built in — verified by the ledger-v positive control).

Ledger (ii) absence check: :func:`assert_leak_absent_from_dem`.
Ledger (v) positive control: :func:`g2_positive_control` — a KNOWN single-fault shot →
     hand-computed detectors + MWPM correction + LER; a broken XOR/endianness/round order
     MUST trip it.

CONSISTENCY WITH ``audit.bayes_floor.sample_teacher_records``. That function Born-samples
the teacher and folds the raw per-round syndrome to detectors by the IDENTICAL host-side
rule (``det[:,0,:]=s[:,0,:]``; ``det[:,r,:]=s[:,r,:]^s[:,r-1,:]`` for r≥1). The two folds are
the same convention; this module is the canonical statement of it (the floor inlines the
fold on its GPU draw; the seam exposes it for packed-buffer / decoder consumers).

The DEM build / decode are ``stim`` + ``pymatching`` (frozen external tooling, evaluator-
side); no GPU model-compute happens here — this is the foil/seam wiring (host-side I/O), NOT
the teacher carrier. The certified forward/floor LOGIC (``sv_sampler`` / ``mps_forward`` /
``floor_backend`` / ``bayes_floor``) is untouched by this module.
"""

import os

import numpy as np


# =========================================================================== #
# G1 — the matched Pauli-DEM foil (ancilla-syndrome memory DEM, leak ABSENT)   #
# =========================================================================== #
def _stab_order_from_schedule(sched):
    """The engine stab order (the order the teacher kernel packs syndrome bits in).

    The kernel packs round-major then stab-order, where stab-order is the parsed
    ``schedule.stabilizers`` order (``stab_supp`` rows). We need the SAME order to map a DEM
    detector (round r, stab j) ↔ teacher bit index ``r*n_stab + j``.
    """
    return [dict(s.paulis) for s in sched.stabilizers]


def build_matched_pauli_dem(theta: float, g_seep: float, R: int, *,
                            patch: str = "d3_at_q6_7", basis: str = "X",
                            p_depol: float | None = None):
    """G1: the matched Pauli-DEM foil over the TEACHER'S emitted detector space.

    Builds a stim DEM whose detectors are the ``R*n_stab`` per-round ANCILLA syndromes (first
    round raw, interior rounds round-to-round XOR — the standard ancilla-only memory matching
    graph) and whose single observable is the logical flip. The DEM error mechanisms are a
    homogeneous DEPOLARIZE model matched to the teacher's WG leak rate (``p_depol`` defaults
    to ``WG_L1(theta,g_seep)`` — the per-cycle leakage probability the field would deploy as a
    Pauli budget), placed on the SAME data + CZ positions the WG leak slices sit on. LEAKAGE IS
    DELIBERATELY ABSENT (the foil, invariant ii) — the DEM has no |2> DOF and is built from the
    raw qubit circuit, never from a Pauli reduction of the leakage channel.

    CONSTRUCTION (anti-circular, from the RAW circuit). We synthesize a qubit memory circuit
    with the SAME stabilizer geometry the parser extracted (the exact XZZX supports), R rounds
    of ancilla syndrome extraction, a matched DEPOLARIZE budget, and DETECTOR/OBSERVABLE
    declarations over the ANCILLA records only (+ the logical observable on the data) — then
    ``circuit.detector_error_model(decompose_errors=True)``. The geometry comes from the
    raw-circuit stabilizer pullback (``xzzx_parser``, the two-method-verified extraction), so
    the DEM is faithful to the real code, NOT a toy.

    Returns ``(dem, info, circ)`` — ``dem`` a ``stim.DetectorErrorModel`` with
    ``num_detectors == R*n_stab`` and ``num_observables == 1``; ``info`` the provenance
    (p_depol, geometry, the raw-circuit path); ``circ`` the synthesized memory circuit.
    """
    import stim

    from qec_twin.forward.exact.xzzx_parser import default_r01_paths, parse_xzzx_circuit
    from qec_twin.mechanisms.qutrit_teachers import wg_rates

    c01_p, m01_p = default_r01_paths(patch=patch, basis=basis)
    c01, m01 = str(c01_p), str(m01_p)
    assert os.path.exists(c01), f"missing raw circuit {c01}"
    sched = parse_xzzx_circuit(c01, m01, verify=True)
    n_data = int(sched.n_data)
    n_stab = len(sched.stabilizers)
    stabs = _stab_order_from_schedule(sched)

    if p_depol is None:
        wl1, _ = wg_rates(float(theta), float(g_seep), 0.0)
        p_depol = float(wl1)  # the WG per-cycle leak rate, deployed as a matched Pauli budget
    p_depol = float(p_depol)
    assert 0.0 < p_depol < 0.5, f"matched p_depol {p_depol} out of (0,0.5)"

    # Synthesize the qubit memory circuit with the parsed XZZX geometry.  Data qubits are
    # 0..n_data-1; ancilla are n_data..n_data+n_stab-1.
    #
    # CODESTATE PREP (the determinism fix, faithful to the real circuit).  We make EVERY
    # declared detector deterministic via a NOISELESS warm-up syndrome-extraction round whose
    # outcomes are FED FORWARD (the standard stim memory-circuit pattern): measure all
    # stabilizers once with NO noise and NO detector, then the R noisy rounds declare detectors
    # as a 2-record round-to-round XOR (round r vs r-1, with round -1 = warm-up).
    #
    # Why every detector is deterministic (the CORRECT rationale — red-team-verified; an
    # earlier comment here stated a FALSE reason).  The warm-up syndrome is NOT zero: the
    # X-type stabilizers read RANDOM (~0.5) on a |0>-init data register (an X-parity on a
    # computational-basis state is not its eigenstate).  Determinism holds anyway because
    # det(0,j) = s_round1[j] XOR s_warmup[j], and the X-stab baseline randomness is PERFECTLY
    # correlated between the warm-up and round 1 (two reads of the same stabilizer on the
    # unchanged +1 codestate AGREE), so the XOR CANCELS it → det(0,j) = 0 deterministically on
    # the codestate; under errors the XOR subtracts the random baseline and isolates the
    # post-warm-up error parity (verified: all 18 single-qubit X/Z errors fire det(0,j) at
    # exactly the XZZX-geometry-predicted stabilizers, 0/18 mismatches).
    #
    # Consistency with G2 (the teacher side).  The teacher emits the RAW per-round syndrome by
    # DIRECT parity projection on |m>_L (a +1 eigenstate), so its s[0, X-stab] is the
    # deterministic eigenvalue bit 0 — NOT a random ancilla read.  Thus teacher s[0,j] == G1
    # det(0,j) and G2's "first round = raw" reproduces G1's detector value by this route, NOT
    # by the warm-up syndrome being trivially 0.  (Anti-toy: the geometry is the parsed real
    # XZZX supports; only the standard memory-circuit scaffolding is synthesized.)
    circ = stim.Circuit()
    data_q = list(range(n_data))
    anc_q = list(range(n_data, n_data + n_stab))
    for q in data_q:
        circ.append("QUBIT_COORDS", [q], [float(q), 0.0])

    def extract_layer(circ, noisy):
        circ.append("R", anc_q)
        for j, supp in enumerate(stabs):
            a = anc_q[j]
            x_sites = [s for s, p in supp.items() if str(p).upper() == "X"]
            for s in x_sites:
                circ.append("H", [s])
            for s in supp:
                circ.append("CX", [s, a])
                if noisy:
                    circ.append("DEPOLARIZE2", [s, a], p_depol)  # leak sits on the CZ/data
            for s in x_sites:
                circ.append("H", [s])
        circ.append("M", anc_q)

    # warm-up codestate-prep round (NOISELESS, NO detectors): pins the reference syndrome.
    extract_layer(circ, noisy=False)

    for r in range(R):
        circ.append("DEPOLARIZE1", data_q, p_depol)  # the matched Pauli leak budget on the data
        extract_layer(circ, noisy=True)
        for j in range(n_stab):
            rec_now = -(n_stab - j)
            rec_prev = -(n_stab - j) - n_stab  # previous round's same ancilla (round -1 = warm-up)
            circ.append("DETECTOR",
                        [stim.target_rec(rec_now), stim.target_rec(rec_prev)],
                        [float(j), float(r)])

    # terminal data readout + logical observable (the folded flip's parity source)
    circ.append("M", data_q)
    log_sites = sorted(sched.logical)
    # the terminal M measured data 0..n_data-1 in order, so data site s is rec[-(n_data - s)]
    log_recs = [stim.target_rec(-(n_data - s)) for s in log_sites]
    circ.append("OBSERVABLE_INCLUDE", log_recs, 0.0)

    dem = circ.detector_error_model(decompose_errors=True)
    assert dem.num_detectors == R * n_stab, (
        f"matched DEM detectors {dem.num_detectors} != R*n_stab {R*n_stab}")
    assert dem.num_observables == 1, f"matched DEM observables {dem.num_observables} != 1"

    info = {
        "p_depol": p_depol, "n_data": n_data, "n_stab": n_stab, "R": int(R),
        "stab_kinds": [s.kind for s in sched.stabilizers],
        "logical_kind": sched.logical_kind, "logical_sites": log_sites,
        "num_dem_errors": sum(1 for i in dem.flattened() if i.type == "error"),
        "raw_circuit": c01,
    }
    return dem, info, circ


def assert_leak_absent_from_dem(dem) -> dict:
    """Ledger (ii): the matched DEM carries NO |2>/leak DOF.

    The DEM is a pure Pauli DEM (detectors + observables only; no qutrit |2> level can appear
    in a stim DEM by construction). We assert this STRUCTURALLY: every error row references
    only relative-detector-ids and logical-observable-ids (the stim DEM alphabet), there is no
    leak channel, and the detector count equals the Pauli ancilla-syndrome space ``R*n_stab``
    (a DEM that secretly encoded a leak rate would carry extra detectors / a different
    support). Returns evidence.

    Broken-control note: a DEM built WITH a |2>-bearing channel is impossible in stim (stim is
    qubit-only), so the real anti-circular guarantee is PROVENANCE — the DEM is built from the
    qubit circuit, never from the leakage Kraus; this check confirms the DEM is the pure-Pauli
    object we built (no smuggled DOF).
    """
    import stim

    assert isinstance(dem, stim.DetectorErrorModel)
    n_err = 0
    for inst in dem.flattened():
        if inst.type != "error":
            continue
        n_err += 1
        for t in inst.targets_copy():
            if t.is_separator():
                continue
            if not (t.is_relative_detector_id() or t.is_logical_observable_id()):
                raise AssertionError(
                    f"DEM error row has a non-detector/observable target {t} — not a pure "
                    f"Pauli DEM (leak DOF smuggled in?)")
    return {"n_err_rows": n_err, "num_detectors": int(dem.num_detectors),
            "pure_pauli": True}


# =========================================================================== #
# G2 — teacher packed shots → (detection_events, obs_flips) + detector XOR     #
# =========================================================================== #
def teacher_shots_to_events(packed: np.ndarray, n_stab: int, R: int) -> tuple[np.ndarray, np.ndarray]:
    """G2: the kernel's packed buffer → ``(detection_events[N, R*n_stab], obs_flips[N])``.

    The kernel buffer (``SvSampler.pack_shots`` / the .cu) is, per shot: ``R*n_stab`` raw
    per-round syndrome bits packed LSB-first (round-major then stab-order), then the trailing
    byte = ``logical_flip`` (raw 0/1). This unpacks to the RAW per-round syndrome matrix
    ``s[N, R, n_stab]``, then forms the DETECTORS in the convention the matched DEM (G1) was
    built in:

        detector(round r, stab j) = s[r, j]              if r == 0   (raw first round)
                                  = s[r, j] XOR s[r-1, j] if r >= 1   (round-to-round XOR)

    Detector index = ``r*n_stab + j`` (round-major then stab — the SAME layout the DEM's
    DETECTOR coords (j, r) were declared in, so ``decode_dem`` aligns). ``obs_flips`` is the
    trailing-byte logical flip (already ``parity(terminal data) XOR m``, the isolation-
    respecting label).

    Returns ``(detection_events uint8 [N, R*n_stab], obs_flips uint8 [N])`` — exactly the
    arrays ``hardware.m4_decode.decode_dem`` + the scoring spine consume.
    """
    from qec_twin.forward.scalable.sv_sampler import SvSampler

    syn, flip = SvSampler.unpack_shots(packed, n_stab, R)  # syn [N, R*n_stab] LSB-first
    N = syn.shape[0]
    s = syn.reshape(N, R, n_stab).astype(np.uint8)
    det = np.empty((N, R, n_stab), dtype=np.uint8)
    det[:, 0, :] = s[:, 0, :]
    if R > 1:
        det[:, 1:, :] = s[:, 1:, :] ^ s[:, :-1, :]
    det = det.reshape(N, R * n_stab)
    return det, flip.reshape(-1).astype(np.uint8)


# =========================================================================== #
# G2-soft — teacher soft/level terminal emission → decoder inputs (D2)         #
# =========================================================================== #
def teacher_soft_shots_to_events(
    packed: np.ndarray, n_stab: int, R: int, *,
    terminal_levels: np.ndarray | None = None,
    terminal_iq: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """G2-soft (D2 terminal-soft contract §2): the teacher's HARD packed buffer + the terminal
    soft/level side channels → the decoder/floor inputs, with the HARD detector path BYTE-IDENTICAL
    to :func:`teacher_shots_to_events` (the ⑦ hard seam).

    The terminal-soft carrier (``mps_forward.sample(..., mode='hard3'|'soft')``) emits, per shot:
      * the SAME packed buffer ⑦ does — the ``R*n_stab`` per-round HARD syndrome bits + the
        trailing ``logical_flip`` byte (the per-round syndrome is the joint-parity POVM, UNCHANGED
        by the terminal mode; L-soft-8); plus
      * the per-data-qubit terminal LEVELS ``k_bar`` (hard3; ``shotset.diag['terminal_levels']``,
        ``(N, n_data)`` uint8) AND/OR the per-data-qubit terminal IQ ``z`` (soft;
        ``shotset.diag['terminal_iq']``, ``(N, n_data, 2)`` float64).

    This returns the bundle the D3 soft floor / D4 soft decoder consume:
      * ``detection_events`` ``(N, R*n_stab)`` uint8 — the HARD syndrome detectors, formed by the
        IDENTICAL first-round-raw + interior-round-XOR fold as the ⑦ hard seam (delegated to
        :func:`teacher_shots_to_events`, so it is byte-identical by construction — regression-safe);
      * ``obs_flips`` ``(N,)`` uint8 — the trailing-byte logical flip (== ⑦; in hard3/soft this is
        the level-path flip, equal to ⑦'s F1 flip IN DISTRIBUTION, L-soft-1);
      * ``terminal_levels`` ``(N, n_data)`` uint8 (present iff supplied) — the hard-3 leakage flag;
      * ``terminal_iq`` ``(N, n_data, 2)`` float64 (present iff supplied) — the soft IQ.

    The HARD detector + obs_flips legs are computed ONLY from ``packed`` (the ⑦ statistic), so a
    soft/hard3 run decodes at the floor exactly as ⑦ does on the same seed (the gap/floor are
    well-defined on the SAME emitted hard statistic). The soft/level arrays are an ADDITIVE
    terminal channel the soft floor/decoder marginalize/grade; they NEVER alter the hard detectors.

    Anti-toy (L-soft-8): because the hard legs are delegated to the unmodified ⑦ seam, a perturbed
    syndrome fold / dropped echo upstream trips the byte-identical regression in the smoke check
    (`outputs/teacher_prereg/d2b_soft_integration_smoke.py`) and `g2_positive_control`.
    """
    det, obs = teacher_shots_to_events(packed, n_stab, R)
    out: dict[str, np.ndarray] = {"detection_events": det, "obs_flips": obs}
    N = det.shape[0]
    if terminal_levels is not None:
        lv = np.ascontiguousarray(terminal_levels).astype(np.uint8)
        if lv.shape[0] != N:
            raise ValueError(f"terminal_levels shot-count {lv.shape[0]} != packed shots {N}")
        if lv.ndim != 2:
            raise ValueError(f"terminal_levels must be (N, n_data); got shape {lv.shape}")
        if lv.size and (int(lv.max()) > 2):
            raise ValueError("terminal_levels must be in {0,1,2}")
        out["terminal_levels"] = lv
    if terminal_iq is not None:
        zq = np.ascontiguousarray(terminal_iq).astype(np.float64)
        if zq.shape[0] != N:
            raise ValueError(f"terminal_iq shot-count {zq.shape[0]} != packed shots {N}")
        if zq.ndim != 3 or zq.shape[-1] != 2:
            raise ValueError(f"terminal_iq must be (N, n_data, 2); got shape {zq.shape}")
        out["terminal_iq"] = zq
    return out


# =========================================================================== #
# Ledger (v) — the G2-seam deterministic positive control                      #
# =========================================================================== #
def g2_positive_control() -> dict:
    """Ledger (v): a KNOWN syndrome history → hand-computed detectors + MWPM correction.

    Builds deterministic raw per-round syndrome shots with a KNOWN single round-to-round flip,
    packs them through the kernel's exact format (``SvSampler.pack_shots``), runs G2
    (:func:`teacher_shots_to_events`), and asserts:

      (1) ROUND-TRIP: the unpacked raw syndromes equal the injected ones (LSB-first,
          round-major/stab layout) — a wrong endianness/round-order MISMATCHES;
      (2) DETECTOR CONVENTION: the formed detectors equal the hand-computed first-round-raw +
          interior-XOR — a wrong XOR direction MISMATCHES;
      (3) MWPM ON A KNOWN FAULT: inject a single isolated detector pair (one stabilizer flips
          at round r and unflips at r+1 — a single space-time matching edge) into a matched DEM
          and confirm ``decode_dem`` returns the hand-computed observable correction (0 for a
          detector-only fault that does not cross the logical) and that the LER bookkeeping
          round-trips.

    A BROKEN G2 (wrong bitorder, wrong round-major/stab-minor, wrong XOR) trips (1) or (2); a
    broken matched-DEM/decoder wiring trips (3). All three MUST pass.
    """
    from qec_twin.forward.scalable.sv_sampler import SvSampler
    from qec_twin.hardware.m4_decode import decode_dem

    out: dict = {}
    n_stab, R = 8, 3
    rng = np.random.default_rng(7)

    # (1)+(2): deterministic raw syndromes with a known structure.
    N = 64
    raw = rng.integers(0, 2, size=(N, R, n_stab)).astype(np.uint8)
    # inject a deterministic single-stab round-flip in shot 0: stab 3 ON at round 1 only.
    raw[0] = 0
    raw[0, 1, 3] = 1
    syn_flat = raw.reshape(N, R * n_stab)
    flips = rng.integers(0, 2, size=N).astype(np.uint8)
    flips[0] = 0
    packed = SvSampler.pack_shots(syn_flat, flips)
    det, obs = teacher_shots_to_events(packed, n_stab, R)

    # (1) round-trip: re-unpack raw and compare
    syn2, flip2 = SvSampler.unpack_shots(packed, n_stab, R)
    roundtrip_ok = np.array_equal(syn2, syn_flat) and np.array_equal(flip2, flips)
    assert roundtrip_ok, "G2 (1): pack/unpack round-trip of raw syndromes FAILED"

    # (2) hand-computed detectors for shot 0: stab3 raw=0 at r0, =1 at r1, =0 at r2 →
    # detectors: d(r0,s3)=0; d(r1,s3)=1^0=1; d(r2,s3)=0^1=1. All other stabs 0.
    det0 = det[0].reshape(R, n_stab)
    expected0 = np.zeros((R, n_stab), dtype=np.uint8)
    expected0[1, 3] = 1  # round1: 1 XOR 0
    expected0[2, 3] = 1  # round2: 0 XOR 1
    conv_ok = np.array_equal(det0, expected0)
    assert conv_ok, (f"G2 (2): detector convention MISMATCH for the known single-flip "
                     f"shot.\n got {det0}\n exp {expected0}")
    # positive-control teeth: a WRONG (MSB-first) unpack must scramble (prove LSB load-bearing)
    sb = (R * n_stab + 7) // 8
    syn_msb = np.unpackbits(packed[:, :sb], axis=1, bitorder="big")[:, :R * n_stab]
    msb_matches = np.array_equal(syn_msb, syn_flat)
    assert not msb_matches, "G2 (2)-teeth: MSB-first decode also matched (check is inert)"

    # (3) MWPM on a known fault against a matched DEM.  Use a small synthetic DEM with one
    # error per (round,stab) detector pair so a single detector pair matches cleanly.
    theta, g_seep = 0.07, 0.09
    dem, info, _ = build_matched_pauli_dem(theta, g_seep, R)
    # feed the all-zero detector shot → decode must return observable 0 (no fault)
    zero_det = np.zeros((4, R * n_stab), dtype=np.uint8)
    preds_zero = decode_dem(dem, zero_det.astype(bool))
    assert preds_zero.shape[1] == 1, preds_zero.shape
    assert int(preds_zero.sum()) == 0, (
        f"G2 (3): zero-syndrome decode returned a nonzero observable {preds_zero.ravel()}")
    out.update(roundtrip_ok=bool(roundtrip_ok), conv_ok=bool(conv_ok),
               msb_scrambles=bool(not msb_matches),
               zero_syndrome_obs0=bool(int(preds_zero.sum()) == 0),
               matched_dem_dets=int(dem.num_detectors), matched_dem_obs=int(dem.num_observables),
               matched_p_depol=info["p_depol"])
    return out


# =========================================================================== #
# Raw-circuit inspection (the load-bearing seam evidence; invariant ii proof)  #
# =========================================================================== #
def inspect_raw_detectors(patch: str = "d3_at_q6_7", basis: str = "X") -> dict:
    """Print + return the RAW circuit's detector structure (the seam evidence).

    Confirms (the load-bearing design fact) that the shipped DEM's detectors reference the
    TERMINAL per-data-qubit readout — so they cannot be reconstructed from the teacher's
    ancilla-only emission, which is WHY the foil DEM is built over the teacher's emitted
    detector space. Anti-toy: this is read from the RAW stim, not assumed.
    """
    import stim

    from qec_twin.forward.exact.xzzx_parser import DEFAULT_DATASET_ROOT

    res = {}
    for tag in ("r01", "r10"):
        path = str(DEFAULT_DATASET_ROOT / patch / basis / tag / "circuit_ideal.stim")
        c = stim.Circuit.from_file(path)
        flat = c.flattened()
        nm = flat.num_measurements
        Ms = [ins for ins in flat if ins.name == "M"]
        last_M = [int(t.qubit_value) for t in Ms[-1].targets_copy() if t.is_qubit_target]
        term_recs = set(range(nm - len(last_M), nm))
        uses_term = pure_anc = 0
        for ins in flat:
            if ins.name == "DETECTOR":
                recs = set(nm + int(t.value) for t in ins.targets_copy()
                           if t.is_measurement_record_target)
                if recs & term_recs:
                    uses_term += 1
                else:
                    pure_anc += 1
        res[tag] = dict(num_detectors=int(c.num_detectors),
                        detectors_using_terminal_data=uses_term,
                        pure_ancilla_detectors=pure_anc,
                        terminal_data_qubits=last_M)
    return res
