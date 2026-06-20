import json
from pathlib import Path
import stim

ROOT = Path("/home/cx/Document/google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7")
base = ROOT / "d3_at_q6_7" / "X" / "r01"
circ = stim.Circuit.from_file(str(base / "circuit_ideal.stim"))
meta = json.loads((base / "metadata.json").read_text())

print("=== A. raw-circuit facts (no parser) ===")
print("  num_qubits          =", circ.num_qubits)
print("  num_detectors       =", circ.num_detectors)
print("  num_observables     =", circ.num_observables)
print("  rounds (meta)        =", meta.get("rounds"))
print("  data_qubit_coords n =", len(meta["data_qubit_coords"]))
print("  meas_qubit_coords n =", len(meta["meas_qubit_coords"]))

ms = []
for inst in circ.flattened():
    if inst.name == "M":
        ms.append([int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target])
print("  number of M instrs  =", len(ms), "; sizes =", [len(m) for m in ms])
print("  first M (ancilla)   =", sorted(ms[0]))
if len(ms) > 1:
    print("  last  M (data)      =", sorted(ms[-1]))

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
meas_ids = sorted(i for i, c in idx2c.items() if c in meas_coords)
all_ids = sorted(idx2c)
surplus = [i for i in all_ids if i not in set(data_ids) and i not in set(meas_ids)]
print("  data ids (by coord) =", data_ids)
print("  meas ids (by coord) =", meas_ids)
print("  surplus ids         =", surplus)

print()
print("=== B. stabilizers via independent has_flow (P-on-data -> ancilla record) ===")
n = circ.num_qubits
anc = ms[0]


def single_flip_data(anc_rec_index, pauli):
    out = []
    for q in data_ids:
        ps = ["_"] * n
        ps[q] = pauli
        fl = stim.Flow(input=stim.PauliString("".join(ps)),
                       output=stim.PauliString("_" * n),
                       measurements=[anc_rec_index])
        try:
            if circ.has_flow(fl):
                out.append(q)
        except Exception:
            pass
    return out


supports = {}
for k, a in enumerate(anc):
    xsupp = single_flip_data(k, "X")
    zsupp = single_flip_data(k, "Z")
    if xsupp and not zsupp:
        supports[a] = ("Z-stab", sorted(xsupp))
    elif zsupp and not xsupp:
        supports[a] = ("X-stab", sorted(zsupp))
    else:
        supports[a] = ("MIXED?", {"X": sorted(xsupp), "Z": sorted(zsupp)})

nx = sum(1 for v in supports.values() if v[0] == "X-stab")
nz = sum(1 for v in supports.values() if v[0] == "Z-stab")
print("  ", nx, "X-type +", nz, "Z-type stabilizers (independent has_flow method)")
for a in anc:
    kind, supp = supports[a]
    w = len(supp) if isinstance(supp, list) else "?"
    print("    ancilla", a, "coord", idx2c[a], ":", kind, "on data ids", supp, "(weight", w, ")")

print()
print("=== C. logical observable (independent) ===")
meas_q = []
for inst in circ.flattened():
    if inst.name == "M":
        meas_q.extend(int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target)
obs_recs = []
for inst in circ.flattened():
    if inst.name == "OBSERVABLE_INCLUDE":
        for t in inst.targets_copy():
            if t.is_measurement_record_target:
                obs_recs.append(len(meas_q) + int(t.value))
obs_data = sorted({meas_q[r] for r in obs_recs if meas_q[r] in set(data_ids)})
print("  OBSERVABLE_INCLUDE data ids =", obs_data)
for cand in ("Z", "X"):
    ps = ["_"] * n
    for q in obs_data:
        ps[q] = cand
    fl = stim.Flow(input=stim.PauliString("_" * n), output=stim.PauliString("".join(ps)),
                   measurements=sorted(obs_recs))
    print("  has_flow(1 ->", cand, "on obs_data, recs) =", circ.has_flow(fl))

print()
print("=== D. parser output (the thing under review), for side-by-side ===")
from qec_twin.forward.exact.xzzx_parser import parse_xzzx_circuit
sch = parse_xzzx_circuit(base / "circuit_ideal.stim", base / "metadata.json", verify=True)
print("  n_data =", sch.n_data, " rounds =", sch.rounds, " surplus =", sch.surplus_dropped)
print("  data_indices (engine pos -> circuit id) =", sch.data_indices)
print("  logical kind =", sch.logical_kind, " logical (engine pos) =", dict(sch.logical))
pos_of = {cid: p for p, cid in enumerate(sch.data_indices)}
print("  logical data circuit ids =", sorted(sch.data_indices[p] for p in sch.logical))
for s in sch.stabilizers:
    circ_ids = {sch.data_indices[p]: k for p, k in s.paulis.items()}
    print("    stab", s.stab_id, "anc", s.ancilla_index, s.kind, "engine-pos", dict(s.paulis),
          "-> circuit-ids", circ_ids)
