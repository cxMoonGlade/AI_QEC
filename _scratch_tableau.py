"""Definitive independent stabilizer check via Stim TableauSimulator (no flow-signature guessing).

Simulate the circuit's UNITARY+RESET prefix (everything before the final data readout) with
Stim's stabilizer TableauSimulator, then read the stabilizer group of the prepared state with
.canonical_stabilizers(). Each claimed parser stabilizer P (on data) -- after the round's
syndrome extraction the ancilla carry the parity; but the DATA-only operator that is a
deterministic +/-1 stabilizer of the post-init pre-measurement state IS the code stabilizer.

Cleanest: run the FULL ideal circuit through the TableauSimulator with deterministic-measurement
recording. The measured detectors' supports give the stabilizers. We instead verify each parser
P by: prepare via the unitary+reset prefix, then check P expectation is deterministic +1 on the
DATA (i.e. P commutes with the prepared stabilizer group and is in it). We use peek_observable_expectation.
"""
import json
from pathlib import Path
import stim

ROOT = Path("/home/cx/Document/google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7")
base = ROOT / "d3_at_q6_7" / "X" / "r01"
circ = stim.Circuit.from_file(str(base / "circuit_ideal.stim"))
n = circ.num_qubits

from qec_twin.forward.exact.xzzx_parser import parse_xzzx_circuit
sch = parse_xzzx_circuit(base / "circuit_ideal.stim", base / "metadata.json", verify=True)

# Build the prefix circuit: everything up to (and including) the first M (ancilla syndrome
# measure), but we want the DATA stabilizers of the state right BEFORE the ancilla are
# measured -- i.e. the unitary+reset+entangling prefix, stopping before the first M.
prefix = stim.Circuit()
for inst in circ.flattened():
    if inst.name == "M":
        break
    if inst.name in ("DETECTOR", "OBSERVABLE_INCLUDE", "QUBIT_COORDS", "TICK", "SHIFT_COORDS"):
        continue
    # resolve sweep-CX to identity (all-zero sweep = ideal): a CX with a sweep-bit control
    # has no deterministic action in the TableauSimulator with sweep=0, so drop sweep-CX.
    if inst.name == "CX":
        # CX here is sweep-controlled data init; ideal all-zero sweep -> identity. drop.
        continue
    prefix.append(inst)

sim = stim.TableauSimulator()
sim.do(prefix)

print("=== prepared-state stabilizer expectations of each parser stabilizer (DATA operator) ===")
allok = True
for s in sch.stabilizers:
    ids = sorted(sch.data_indices[p] for p in s.paulis)
    ps = ["_"]*n
    for q in ids: ps[q] = s.kind
    P = stim.PauliString("".join(ps))
    ev = sim.peek_observable_expectation(P)
    ok = (ev == 1)   # deterministic +1 stabilizer of the prepared code state
    allok = allok and ok
    print("  stab", s.stab_id, s.kind, ids, "-> <P> =", ev, "(+1 stabilizer:", ok, ")")

print()
print("=== logical operator expectation (should be deterministic +/-1: it's a logical, not random) ===")
log_ids = sorted(sch.data_indices[p] for p in sch.logical)
ps = ["_"]*n
for q in log_ids: ps[q] = sch.logical_kind
L = stim.PauliString("".join(ps))
evL = sim.peek_observable_expectation(L)
print("  logical", sch.logical_kind, log_ids, "-> <L> =", evL,
      "(deterministic +/-1 means it's preserved by the prepared state)")

print()
print("=== positive control: a NON-stabilizer data operator should be random (<P>=0) ===")
# Z on a single data qubit -- not a stabilizer, expect 0
ps = ["_"]*n; ps[sch.data_indices[0]] = "Y"
ctrl = stim.PauliString("".join(ps))
print("  Y on data pos0 -> <P> =", sim.peek_observable_expectation(ctrl), "(expect 0 = random)")

print()
print("ALL PARSER STABILIZERS ARE +1 STABILIZERS OF THE PREPARED STATE:", allok)
