"""LEAN real-d3 run validation: the exact path run_full_d3_floor takes, codestate verified
by cheap trace/purity (no dense stabilizer operators). Confirms the full run is valid."""
import torch
assert torch.cuda.is_available()
dev = "cuda"
print("torch", torch.__version__, torch.cuda.get_device_name(0), flush=True)
from qec_twin.forward.exact.xzzx_parser import parse_xzzx_circuit, default_r01_paths
from qec_twin.forward.exact.qutrit_dm import QutritDM
from qec_twin.mechanisms.qutrit_teachers import leakage_kraus_torch

cp, mp = default_r01_paths()
sch = parse_xzzx_circuit(cp, mp, verify=True)
stabs = sch.stab_paulis()
eng = QutritDM(sch.n_data, device=dev)
eng.set_code(stabilizers=stabs,
             logical_z=sch.logical if sch.logical_kind=="Z" else None,
             logical_x=sch.logical if sch.logical_kind=="X" else None)

print("=== codestate validity (trace/purity/orthogonality), real d3 3**9 ===", flush=True)
eng.init_logical(0); r0 = eng.rho.clone()
tr0=float(torch.diagonal(r0).real.sum()); pur0=float((r0@r0).diagonal().real.sum())
print(f"  m=0 Tr={tr0:.10f} purity={pur0:.10f}", flush=True)
eng.init_logical(1); r1 = eng.rho.clone()
tr1=float(torch.diagonal(r1).real.sum()); pur1=float((r1@r1).diagonal().real.sum())
print(f"  m=1 Tr={tr1:.10f} purity={pur1:.10f}", flush=True)
ov=float((r0@r1).diagonal().real.sum())
print(f"  <0|1>^2={ov:.3e}", flush=True)
assert abs(tr0-1)<1e-9 and abs(tr1-1)<1e-9 and abs(pur0-1)<1e-9 and abs(pur1-1)<1e-9 and ov<1e-9
del r0, r1; torch.cuda.empty_cache()

# logical readout determinism: p0/p1 from the engine's own logical_distribution
eng.init_logical(0); l0=eng.logical_distribution()
eng.init_logical(1); l1=eng.logical_distribution()
print(f"  logical_distribution m=0 -> {l0}  m=1 -> {l1}  (expect ~ (1,0) and (0,1))", flush=True)

print("=== noiseless + central-leakage floor, b sweep (the run's machinery) ===", flush=True)
def floor(kraus, b):
    eng.init_logical(0)
    if kraus is not None:
        for s in range(sch.n_data): eng.apply_channel(kraus, s)
    p0=eng.syndrome_distribution(stabs, b)
    eng.init_logical(1)
    if kraus is not None:
        for s in range(sch.n_data): eng.apply_channel(kraus, s)
    p1=eng.syndrome_distribution(stabs, b)
    tv=0.5*sum(abs(p0.get(k,0.0)-p1.get(k,0.0)) for k in set(p0)|set(p1))
    return sum(p0.values()), sum(p1.values()), tv, 0.5*(1-tv), len(set(p0)|set(p1))

for b in (0.5, 1.0):
    s0,s1,tv,ler,nc = floor(None, b)
    print(f"  noiseless b={b}: sumP0={s0:.10f} sumP1={s1:.10f} cells={nc} TV={tv:.3e} LER*={ler:.10f}", flush=True)
    assert abs(s0-1)<1e-7 and abs(s1-1)<1e-7 and -1e-9<=ler<=0.5+1e-9 and nc==256

kr = leakage_kraus_torch(0.07, 0.09, 0.0, device=dev)
lers={}
for b in (0.5, 0.75, 1.0):
    s0,s1,tv,ler,nc = floor(kr, b)
    lers[b]=ler
    print(f"  leak(0.07,0.09) b={b}: sumP0={s0:.8f} sumP1={s1:.8f} TV={tv:.3e} LER*={ler:.8f}", flush=True)
    assert abs(s0-1)<1e-6 and abs(s1-1)<1e-6 and -1e-9<=ler<=0.5+1e-9
br=[min(lers.values()), max(lers.values())]
print(f"  b-bracket LER* = [{br[0]:.8f}, {br[1]:.8f}] width={br[1]-br[0]:.2e}", flush=True)
print("REAL d3 RUN PATH VALID (codestate + 256-cell floor + leakage bracket all sane).", flush=True)
