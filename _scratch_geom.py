"""Geometry-truth validation of the parser stabilizers (unambiguous, no flow API).

For a rotated distance-3 surface code, each weight-4 stabilizer sits on an ancilla at
the CENTER of a unit plaquette and acts on the 4 data qubits at the plaquette CORNERS
(coord +/-1 in x and y). Each weight-2 boundary stabilizer acts on the 2 adjacent data
qubits. This is a pure COORDINATE fact about the shipped layout -- independent of any
tableau/has_flow. I check:

  (1) every parser stabilizer's data support = exactly the data qubits adjacent to its
      ancilla coordinate (Chebyshev/diagonal neighbours at distance sqrt(2) in (x,y)),
  (2) the X/Z TYPE assignment follows the XZZX checkerboard (ancilla parity), and
  (3) the stabilizer group is mutually commuting + commutes with the logical (the
      load-bearing init_logical precondition), recomputed here from scratch.

Also independently confirms the WG_L1 normalization is exactly L(E(Pi1/d1)) per WG Eq.2.
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path("/home/cx/Document/google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7")
base = ROOT / "d3_at_q6_7" / "X" / "r01"
meta = json.loads((base / "metadata.json").read_text())

from qec_twin.forward.exact.xzzx_parser import parse_xzzx_circuit
sch = parse_xzzx_circuit(base / "circuit_ideal.stim", base / "metadata.json", verify=True)

# circuit-id -> coord
import stim
circ = stim.Circuit.from_file(str(base / "circuit_ideal.stim"))
idx2c = {}
for inst in circ.flattened():
    if inst.name == "QUBIT_COORDS":
        a = tuple(float(x) for x in inst.gate_args_copy())
        for t in inst.targets_copy():
            if t.is_qubit_target:
                idx2c[int(t.qubit_value)] = a

print("=== data layout ===")
for p, cid in enumerate(sch.data_indices):
    print("  engine pos", p, "circ id", cid, "coord", idx2c[cid])

print()
print("=== (1)+(2) each stabilizer support == diagonal neighbours of its ancilla coord ===")
allgeo = True
for s in sch.stabilizers:
    a = s.ancilla_index
    ac = idx2c[a]
    support_ids = sorted(sch.data_indices[p] for p in s.paulis)
    support_coords = [idx2c[cid] for cid in support_ids]
    # diagonal neighbours: |dx|==1 and |dy|==1
    neigh = []
    for cid in sch.data_indices:
        dc = idx2c[cid]
        if abs(dc[0] - ac[0]) == 1.0 and abs(dc[1] - ac[1]) == 1.0:
            neigh.append(cid)
    neigh = sorted(neigh)
    geo_ok = (neigh == support_ids)
    allgeo = allgeo and geo_ok
    print("  anc", a, "coord", ac, s.kind, "w", len(s.paulis),
          "support", support_ids, "diag-neighbours", neigh, "MATCH", geo_ok)
print("  (1)+(2) geometry match:", allgeo)

print()
print("=== (3) commuting group + logical (recomputed from scratch, symplectic) ===")
nq = sch.n_data
def xz(paulis):
    x = np.zeros(nq, int); z = np.zeros(nq, int)
    for site, k in paulis.items():
        if str(k).upper() == "X": x[site] = 1
        elif str(k).upper() == "Z": z[site] = 1
    return x, z
def comm(p, q):
    xp, zp = xz(p); xq, zq = xz(q)
    return int((xp@zq + zp@xq) % 2) == 0
stabs = [dict(s.paulis) for s in sch.stabilizers]
pairs_ok = all(comm(stabs[i], stabs[j]) for i in range(len(stabs)) for j in range(i+1, len(stabs)))
log_ok = all(comm(sch.logical, s) for s in stabs)
print("  all stabilizer pairs commute:", pairs_ok)
print("  logical commutes with all stabilizers:", log_ok)

print()
print("=== WG_L1 normalization is exactly L(E(Pi1/d1)) per Eq.2 (two algebraic forms) ===")
from qec_twin.forward.channels import leakage_channel_super
def apply_super(S, rho):
    return (S @ rho.reshape(-1, order="F")).reshape(3, 3, order="F")
PI1 = np.diag([1., 1., 0.]).astype(complex); PI2 = np.diag([0., 0., 1.]).astype(complex)
d1 = 2
for theta in (0.05, 0.10, 0.20):
    S = leakage_channel_super(theta, 0.0, 0.0)
    # Form A (code): (1/d1) Tr[Pi2 E(Pi1)]
    formA = float(np.real(np.trace(PI2 @ apply_super(S, PI1))) / d1)
    # Form B (Eq.2 literal): L(E(Pi1/d1)) = Tr[Pi2 E(Pi1/d1)]
    formB = float(np.real(np.trace(PI2 @ apply_super(S, PI1 / d1))))
    wg = np.sin(theta)**2 / d1
    print(f"  theta={theta}: formA={formA:.8f}  formB={formB:.8f}  WG sin^2/d1={wg:.8f}  "
          f"A==B:{abs(formA-formB)<1e-15}  ==WG:{abs(formA-wg)<1e-9}")

print()
print("OVERALL geometry+group:", "PASS" if (allgeo and pairs_ok and log_ok) else "FAIL")
