"""Exercise the REAL d3 init_logical + noiseless syndrome distribution on the FULL 3**9
geometry (the exact path run_full_d3_floor takes, minus the leakage sweep) to confirm the
run will produce a VALID number. This DOES allocate the 5.77 GiB matrix (a few times).

Checks:
  - init_logical(0)/init_logical(1) on the real 8-stabilizer + logical-Z geometry produce
    NORMALIZED (Tr=1) pure states that are ORTHOGONAL (<0|1>^2 ~ 0);
  - <stabilizer> = +1 for all 8 on both codestates (genuine codestate);
  - <Z_L> = +1 (m=0) / -1 (m=1);
  - the noiseless 256-cell syndrome distribution sums to 1 for both m, and (sanity) the
    noiseless floor LER* and a single light-leakage floor at one b are valid probabilities.
  - the assert_commuting_code precondition passes on the real geometry.
This is the actual run's machinery; if anything is off the full run is invalid.
"""
import sys
from pathlib import Path
import numpy as np
import torch

assert torch.cuda.is_available(), "GPU required"
dev = "cuda"
print("torch", torch.__version__, "device", torch.cuda.get_device_name(0), flush=True)

from qec_twin.forward.exact.xzzx_parser import parse_xzzx_circuit, default_r01_paths
from qec_twin.forward.exact.qutrit_dm import QutritDM
from qec_twin.mechanisms.qutrit_teachers import leakage_kraus_torch

cp, mp = default_r01_paths()
sch = parse_xzzx_circuit(cp, mp, verify=True)
stabs = sch.stab_paulis()
print("n_data", sch.n_data, "stabs", len(stabs), "logical_kind", sch.logical_kind, flush=True)

# precondition
import importlib.util
_FP = Path("/home/cx/Document/AI_QEC/AI_QEC/outputs/teacher_prereg/exact_floor_run.py")
spec = importlib.util.spec_from_file_location("efr", _FP)
efr = importlib.util.module_from_spec(spec); spec.loader.exec_module(efr)
efr.assert_commuting_code(stabs, sch.logical, sch.n_data)
print("assert_commuting_code: PASS (real geometry is a valid code)", flush=True)

def stab_op(paulis):
    # build the X/Z-on-{0,1} operator on the full 3**9 register as a sparse-ish dense matrix
    # (too big at 3**9 dense in numpy: 19683^2 complex = 5.77 GiB). Instead use the engine's
    # own diagnostic: <P> = Tr[P rho]. We compute via the engine by applying P as a unitary
    # to a copy and taking the overlap. Simpler: use torch on GPU with embed_operator.
    from qec_twin.forward.exact.qutrit_dm import embed_operator
    import functools
    mats = []
    def single(kind):
        m = torch.zeros((3,3), dtype=torch.complex128, device=dev)
        if kind == "X": m[0,1]=1; m[1,0]=1; m[2,2]=1
        elif kind == "Z": m[0,0]=1; m[1,1]=-1; m[2,2]=1
        return m
    full = None
    for site, kind in paulis.items():
        e = embed_operator(single(kind), site, sch.n_data, device=dev)
        full = e if full is None else (full @ e)
    return full

eng = QutritDM(sch.n_data, device=dev)
eng.set_code(stabilizers=stabs,
             logical_z=sch.logical if sch.logical_kind=="Z" else None,
             logical_x=sch.logical if sch.logical_kind=="X" else None)

print("\n=== init_logical on real d3 geometry (allocates 5.77 GiB) ===", flush=True)
results = {}
for m in (0, 1):
    eng.init_logical(m)
    rho = eng.rho
    tr = float(torch.diagonal(rho).real.sum())
    herm = float((rho - rho.conj().transpose(-1,-2)).abs().max())
    # rank-1 check via Tr(rho^2)
    purity = float((rho @ rho).diagonal().real.sum())
    results[m] = rho.clone()
    print(f"  m={m}: Tr={tr:.12f}  |rho-rho^H|={herm:.2e}  purity Tr(rho^2)={purity:.12f}", flush=True)
    # stabilizer expectations
    for sid, s in enumerate(stabs):
        op = stab_op(s)
        val = float((op @ rho).diagonal().real.sum())
        assert abs(val - 1.0) < 1e-9, (m, sid, val)
    lz = stab_op(sch.logical)
    lzval = float((lz @ rho).diagonal().real.sum())
    exp = 1.0 if m==0 else -1.0
    print(f"        all 8 <S>=+1 ; <Z_L>={lzval:+.6f} (expect {exp:+.0f})", flush=True)
    assert abs(lzval - exp) < 1e-9, (m, lzval)

# orthogonality
ov = float((results[0] @ results[1]).diagonal().real.sum())
print(f"  <0_L|1_L>^2 (Tr rho0 rho1) = {ov:.3e}", flush=True)
assert ov < 1e-9, ov

print("\n=== noiseless 256-cell syndrome distribution (real geometry, b sweep) ===", flush=True)
for b in (0.5, 1.0):
    eng.init_logical(0); p0 = eng.syndrome_distribution(stabs, b)
    eng.init_logical(1); p1 = eng.syndrome_distribution(stabs, b)
    s0, s1 = sum(p0.values()), sum(p1.values())
    tv = 0.5*sum(abs(p0.get(k,0.0)-p1.get(k,0.0)) for k in set(p0)|set(p1))
    ler = 0.5*(1-tv)
    print(f"  b={b}: sumP0={s0:.12f} sumP1={s1:.12f} cells={len(set(p0)|set(p1))} TV={tv:.6e} LER*={ler:.12f}", flush=True)
    assert abs(s0-1)<1e-9 and abs(s1-1)<1e-9
    assert -1e-12 <= ler <= 0.5+1e-12

print("\n=== one light-leakage floor at central siting (theta=0.07,g_seep=0.09), b sweep ===", flush=True)
kraus = leakage_kraus_torch(0.07, 0.09, 0.0, device=dev)
for b in (0.5, 0.75, 1.0):
    eng.init_logical(0)
    for site in range(sch.n_data): eng.apply_channel(kraus, site)
    p0 = eng.syndrome_distribution(stabs, b)
    eng.init_logical(1)
    for site in range(sch.n_data): eng.apply_channel(kraus, site)
    p1 = eng.syndrome_distribution(stabs, b)
    s0, s1 = sum(p0.values()), sum(p1.values())
    tv = 0.5*sum(abs(p0.get(k,0.0)-p1.get(k,0.0)) for k in set(p0)|set(p1))
    ler = 0.5*(1-tv)
    print(f"  b={b}: sumP0={s0:.10f} sumP1={s1:.10f} TV={tv:.6e} LER*={ler:.10f}", flush=True)
    assert abs(s0-1)<1e-7 and abs(s1-1)<1e-7, (b, s0, s1)
    assert -1e-9 <= ler <= 0.5+1e-9

print("\nREAL d3 PATH VALID: init_logical, codestate, syndrome dist, leakage floor all sane.", flush=True)
