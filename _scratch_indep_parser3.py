"""Independent VALIDATION (not re-derivation) of the parser's stabilizers + logical.

Two robust, parser-independent tests:

  Test-1 (stabilizer flow): each claimed stabilizer P (on data, at the START of the
    circuit) must be a *measured* stabilizer, i.e. the circuit has the flow
    P_data --[detector k]--> P_data  for its ancilla detector k. This is stim's own
    has_flow with the time-correct signature (Pauli before == Pauli after, parity in the
    detector record). If TRUE for the parser's support+kind, the support is genuinely the
    stabilizer that detector measures. I scan the detector index space to confirm a UNIQUE
    detector matches each parser stabilizer (so it is THE stabilizer, not just commuting).

  Test-2 (independent error-response with the CORRECT injection point): mirror the parser's
    Method-3b but injecting after the SWEEP-CX data-init (the parser's own placement), and
    confirm a Z-stab detects exactly its support's X-errors (and no Z error). This is the
    SAME cross-check the parser self-runs internally, so reproducing it here just confirms
    the self-check is live, not a second independent method -- Test-1 is the independent one.
"""
import json
from pathlib import Path
import stim

ROOT = Path("/home/cx/Document/google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7")
base = ROOT / "d3_at_q6_7" / "X" / "r01"
circ = stim.Circuit.from_file(str(base / "circuit_ideal.stim"))
meta = json.loads((base / "metadata.json").read_text())
n = circ.num_qubits

from qec_twin.forward.exact.xzzx_parser import parse_xzzx_circuit
sch = parse_xzzx_circuit(base / "circuit_ideal.stim", base / "metadata.json", verify=True)
parser = []
for s in sch.stabilizers:
    supp = {sch.data_indices[p]: k for p, k in s.paulis.items()}
    parser.append((s.stab_id, s.ancilla_index, s.kind, supp))

ndet = circ.num_detectors


def pstring(supp, kind):
    ps = ["_"] * n
    for q in supp:
        ps[q] = kind
    return stim.PauliString("".join(ps))


print("=== Test-1: each parser stabilizer is a measured stabilizer (has_flow P->P, unique detector) ===")
allok = True
for sid, a, kind, supp in parser:
    P = pstring(supp, kind)
    matching_dets = []
    for k in range(ndet):
        fl = stim.Flow(input=P, output=P, measurements=[k])
        try:
            if circ.has_flow(fl):
                matching_dets.append(k)
        except Exception:
            pass
    # also confirm P with NO measurement is NOT a flow (i.e. it really needs the detector)
    bare = stim.Flow(input=P, output=P, measurements=[])
    bare_ok = False
    try:
        bare_ok = circ.has_flow(bare)
    except Exception:
        bare_ok = False
    uniq = (len(matching_dets) == 1)
    allok = allok and uniq and (not bare_ok)
    print("  stab", sid, "anc", a, kind, "support(circ ids)", sorted(supp),
          "-> matching detectors", matching_dets, "| needs-detector(bare flow false)=", not bare_ok,
          "| UNIQUE+MEASURED=", uniq and not bare_ok)
print("  Test-1 PASS:", allok)

print()
print("=== Test-2: independent error-response (inject after sweep-CX init; parser's placement) ===")
# build records of the 8 detectors with a single forced error after the first CX (sweep init)
def det_record(q=None, etype=None, seed=4242):
    out = stim.Circuit()
    done = False
    for inst in circ.flattened():
        out.append(inst)
        if (not done and q is not None and inst.name == "CX"):
            out.append(etype + "_ERROR", [int(q)], 1.0)
            done = True
    return [bool(b) for b in out.compile_detector_sampler(seed=seed).sample(1)[0]]

# detector k corresponds to ancilla measurement order; map detector -> ancilla
ms0 = None
for inst in circ.flattened():
    if inst.name == "M":
        ms0 = [int(t.qubit_value) for t in inst.targets_copy() if t.is_qubit_target]
        break
anc_order = ms0
ref = det_record()
data_ids = list(sch.data_indices)
resp = {a: {"X": set(), "Z": set()} for a in anc_order}
for q in data_ids:
    for et in ("X", "Z"):
        rec = det_record(q, et)
        for i, a in enumerate(anc_order):
            if rec[i] != ref[i]:
                resp[a][et].add(q)

t2ok = True
for sid, a, kind, supp in parser:
    sites = set(supp)
    xf, zf = resp[a]["X"], resp[a]["Z"]
    if kind == "Z":
        good = (xf == sites and not zf)   # Z-stab detects X errors on support, no Z
    else:
        good = (zf == sites and not xf)   # X-stab detects Z errors on support, no X
    t2ok = t2ok and good
    print("  stab", sid, "anc", a, kind, ": X-flips", sorted(xf), "Z-flips", sorted(zf),
          "support", sorted(sites), "OK=", good)
print("  Test-2 PASS:", t2ok)

print()
print("=== Logical: independent has_flow ===")
# logical data circuit ids + kind
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
parser_logical_ids = sorted(sch.data_indices[p] for p in sch.logical)
print("  parser logical kind/ids =", sch.logical_kind, parser_logical_ids)
print("  independent OBSERVABLE_INCLUDE data ids =", obs_data, " match:", obs_data == parser_logical_ids)
for cand in ("Z", "X"):
    ps = ["_"] * n
    for q in obs_data:
        ps[q] = cand
    fl = stim.Flow(input=stim.PauliString("_" * n), output=stim.PauliString("".join(ps)), measurements=sorted(obs_recs))
    print("  has_flow(1 ->", cand, ") =", circ.has_flow(fl))

print()
print("OVERALL:", "PASS" if (allok and t2ok) else "FAIL")
