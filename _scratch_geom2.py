"""Decisive independent validation: (A) correct rotated-lattice adjacency (|dx|+|dy|==1),
(B) each parser stabilizer is a genuine measured stabilizer via the CORRECT stim flow
signature, found empirically.
"""
import json
from pathlib import Path
import numpy as np
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

from qec_twin.forward.exact.xzzx_parser import parse_xzzx_circuit
sch = parse_xzzx_circuit(base / "circuit_ideal.stim", base / "metadata.json", verify=True)

print("=== (A) adjacency |dx|+|dy|==1 (edge-adjacent on the rotated lattice) ===")
allgeo = True
for s in sch.stabilizers:
    a = s.ancilla_index; ac = idx2c[a]
    support_ids = sorted(sch.data_indices[p] for p in s.paulis)
    neigh = sorted(cid for cid in sch.data_indices
                   if abs(idx2c[cid][0]-ac[0]) + abs(idx2c[cid][1]-ac[1]) == 1.0)
    ok = (neigh == support_ids)
    allgeo = allgeo and ok
    print("  anc", a, ac, s.kind, "support", support_ids, "edge-neigh", neigh, "MATCH", ok)
print("  (A) PASS:", allgeo)

print()
print("=== XZZX checkerboard: X/Z type vs ancilla coord parity ===")
for s in sch.stabilizers:
    ac = idx2c[s.ancilla_index]
    par = int((ac[0] + ac[1]) % 2)
    print("  anc", s.ancilla_index, ac, "(x+y)%2 =", par, "-> kind", s.kind)

print()
print("=== (B) measured-stabilizer flow: find the working signature on stab 0, apply to all ===")
# Try several flow signatures on stab 0 (Z on circ-ids {3,6}) against detector 0..7;
# whichever yields a unique detector is the right convention, then apply to all.
def pstr(ids, kind):
    ps = ["_"]*n
    for q in ids: ps[q] = kind
    return stim.PauliString("".join(ps))

stab0 = sch.stabilizers[0]
s0_ids = sorted(sch.data_indices[p] for p in stab0.paulis)
P0 = pstr(s0_ids, stab0.kind)
ndet = circ.num_detectors
sigs = {
    "I->P meas=[k]": lambda P,k: stim.Flow(input=stim.PauliString("_"*n), output=P, measurements=[k]),
    "P->I meas=[k]": lambda P,k: stim.Flow(input=P, output=stim.PauliString("_"*n), measurements=[k]),
    "P->P meas=[k]": lambda P,k: stim.Flow(input=P, output=P, measurements=[k]),
    "I->I meas=[k] (det)": lambda P,k: stim.Flow(input=stim.PauliString("_"*n), output=stim.PauliString("_"*n), measurements=[k]),
}
working = None
for name, mk in sigs.items():
    hits = [k for k in range(ndet) if circ.has_flow(mk(P0, k))]
    print("  signature", repr(name), "-> stab0 detectors", hits)
    if len(hits) == 1 and working is None:
        working = (name, mk)
print("  chosen working signature:", working[0] if working else None)

if working:
    name, mk = working
    print()
    print("  applying", repr(name), "to ALL parser stabilizers:")
    allflow = True
    for s in sch.stabilizers:
        ids = sorted(sch.data_indices[p] for p in s.paulis)
        P = pstr(ids, s.kind)
        hits = [k for k in range(ndet) if circ.has_flow(mk(P, k))]
        ok = (len(hits) == 1)
        allflow = allflow and ok
        print("    stab", s.stab_id, s.kind, ids, "-> detectors", hits, "UNIQUE", ok)
    print("  (B) PASS (every parser stabilizer is a unique measured stabilizer):", allflow)
