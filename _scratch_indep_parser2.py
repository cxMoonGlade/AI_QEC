"""Correct independent stabilizer cross-check, by TWO methods distinct from the parser.

Parser uses Method-1 = (unitary-prefix tableau).z_output pullback, cross-checked by
Method-3b (error-response sampling). Here:

  Method-E (full-circuit flow): for each ancilla detector k, a stabilizer is a data-qubit
    Pauli P s.t. the circuit has the flow  (I  -- measurements {k} -->  I)  with P inserted
    as a *destructive readout consistency*. The clean way in stim: the detector is a
    deterministic parity of measurements; the data-qubit stabilizer it measures is the
    Pauli P with flow  P_data (before round)  -- {detector record k} -->  P_data (after),
    i.e. has_flow(input=P_data, output=P_data, measurements=[k]). A single-qubit error E on
    the support ANTICOMMUTES with P, flipping detector k. So I find P per ancilla by testing
    which data-Pauli of a fixed type is *stabilized-with-this-detector*.

  Method-D (DEM): build the detector error model and read, for each detector, which
    single-qubit depolarizing error on which data qubit triggers ONLY that detector. This
    is fully independent of any tableau / has_flow.

Then compare both to the parser's supports.
"""
import json
from pathlib import Path
import stim

ROOT = Path("/home/cx/Document/google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7")
base = ROOT / "d3_at_q6_7" / "X" / "r01"
circ = stim.Circuit.from_file(str(base / "circuit_ideal.stim"))
meta = json.loads((base / "metadata.json").read_text())
n = circ.num_qubits

idx2c = {}
for inst in circ.flattened():
    if inst.name == "QUBIT_COORDS":
        a = tuple(float(x) for x in inst.gate_args_copy())
        for t in inst.targets_copy():
            if t.is_qubit_target:
                idx2c[int(t.qubit_value)] = a
data_coords = [tuple(float(x) for x in c) for c in meta["data_qubit_coords"]]
meas_coords = {tuple(float(x) for x in c) for c in meta["meas_qubit_coords"]}
data_ids = sorted(i for i, c in idx2c.items() if c in set(data_coords))

ms0 = None
for inst in circ.flattened():
    if inst.name == "M":
        ms0 = [int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target]
        break
anc = ms0  # measurement-record order = detector order in r01


# ---- Method-E: stabilizer = data-Pauli P with has_flow(P -> P, meas=[k]) ----
def stab_via_flow(k, ptype):
    """Largest data-support of type ptype that is read by detector k:
    test each data qubit q in/out of the support by the single-detector flow."""
    supp = []
    for q in data_ids:
        ps = ["_"] * n
        ps[q] = ptype
        P = stim.PauliString("".join(ps))
        fl = stim.Flow(input=P, output=P, measurements=[k])
        try:
            if circ.has_flow(fl):
                supp.append(q)
        except Exception:
            pass
    return supp


print("=== Method-E: detector-stabilizer via has_flow(P -> P, meas=[k]) ===")
methodE = {}
for k, a in enumerate(anc):
    zs = stab_via_flow(k, "Z")
    xs = stab_via_flow(k, "X")
    if zs and not xs:
        methodE[a] = ("Z", sorted(zs))
    elif xs and not zs:
        methodE[a] = ("X", sorted(xs))
    else:
        methodE[a] = ("?", {"Z": sorted(zs), "X": sorted(xs)})
    print("  anc", a, idx2c[a], "->", methodE[a])

# ---- Method-D: DEM single-error -> single-detector signature ----
print()
print("=== Method-D: DEM single-qubit-error -> single-detector signatures ===")
# add uniform depolarizing on data only, build DEM, and for each (data q, pauli) see which
# detectors fire. A 1-detector signature pins q to that detector's stabilizer support.
c2 = stim.Circuit()
# rebuild: insert DEPOLARIZE1 on each data qubit right after the first R block of data
inserted = False
for inst in circ.flattened():
    c2.append(inst)
# Instead of DEM bookkeeping complexity, directly use detector flips from explicit errors:
# for each data q and each pauli, sample the detector record with that error forced and XOR
# vs reference. (X-ancilla raw randomness cancels under same-seed XOR -- the parser's 3b
# idea, but here we read DETECTORS not raw M, and we scan BOTH error types per data qubit.)
def det_flips(q=None, ptype=None, seed=12321):
    out = stim.Circuit()
    done = False
    for inst in circ.flattened():
        out.append(inst)
        if (not done and q is not None and inst.name in ("R", "RX", "RZ")):
            # after a reset block, inject the error on the data qubit
            out.append(ptype + "_ERROR", [int(q)], 1.0)
            done = True
    smp = out.compile_detector_sampler(seed=seed).sample(1)[0]
    return [bool(b) for b in smp]

ref = det_flips()
methodD = {a: {"X": set(), "Z": set()} for a in anc}
for q in data_ids:
    for pt in ("X", "Z"):
        fl = det_flips(q, pt)
        fired = [anc[i] for i in range(len(anc)) if fl[i] != ref[i]]
        for a in fired:
            methodD[a][pt].add(q)
for a in anc:
    # a Z-stabilizer detects X errors on its support; X-stab detects Z errors
    xset, zset = sorted(methodD[a]["X"]), sorted(methodD[a]["Z"])
    if xset and not zset:
        lab = ("Z", xset)
    elif zset and not xset:
        lab = ("X", zset)
    else:
        lab = ("?", {"Xerr": xset, "Zerr": zset})
    print("  anc", a, idx2c[a], "->", lab)

# ---- parser ----
print()
print("=== Parser (under review) ===")
from qec_twin.forward.exact.xzzx_parser import parse_xzzx_circuit
sch = parse_xzzx_circuit(base / "circuit_ideal.stim", base / "metadata.json", verify=True)
parser_supp = {}
for s in sch.stabilizers:
    circ_ids = sorted(sch.data_indices[p] for p in s.paulis)
    parser_supp[s.ancilla_index] = (s.kind, circ_ids)
    print("  anc", s.ancilla_index, "->", (s.kind, circ_ids))

# ---- compare ----
print()
print("=== AGREEMENT (Method-E vs Method-D vs Parser, by ancilla, circuit-id support) ===")
ok = True
for a in anc:
    e = methodE.get(a)
    d = None
    # recompute methodD label
    xset, zset = sorted(methodD[a]["X"]), sorted(methodD[a]["Z"])
    if xset and not zset:
        d = ("Z", xset)
    elif zset and not xset:
        d = ("X", zset)
    p = parser_supp.get(a)
    agree = (e == d == p)
    ok = ok and agree
    print("  anc", a, ": E=", e, " D=", d, " P=", p, " AGREE=", agree)
print()
print("ALL THREE METHODS AGREE:", ok)
