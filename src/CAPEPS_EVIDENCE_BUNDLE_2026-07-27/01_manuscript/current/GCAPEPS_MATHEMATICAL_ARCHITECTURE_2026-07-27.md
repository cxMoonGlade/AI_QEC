# GCAPEPS mathematical architecture

Date: 2026-07-27

Status: `CURRENT__MATHEMATICAL_FEASIBILITY_ONLY`

This is the architecture figure for the narrow GCAMPS-to-GCAPEPS result.  It
describes an exact representation calculus on a finite connected graph.  It is
not a simulator workflow, a contraction algorithm, or a QEC instrument model.

```mermaid
flowchart LR
    S["GCAPEPS pair (C,A)<br/>represents C|phi(A)>"]
    O{"physical operation"}

    S --> O

    O -->|"Clifford F"| F["frame update<br/>(C,A) -> (FC,A)<br/>D unchanged"]

    O -->|"k-site non-Clifford U"| P["Pauli expansion<br/>U = sum_alpha c_alpha P_alpha<br/>r <= d^(2k)"]
    P --> B["Clifford pullback<br/>C† U C = sum_alpha c_alpha eta_alpha P~_alpha<br/>same r product terms"]
    B --> T["tree-routed PEPO<br/>R_e <= r on routed edges<br/>R_e = 1 otherwise"]
    T --> X["fuse PEPO with PEPS<br/>D'_e <= D_e R_e"]
    X --> N["exact updated pair (C,A')<br/>U C|phi(A)> = C|phi(A')>"]

    S -. "optional paired refactor" .-> Q["choose Clifford Q<br/>(C,A) -> (CQ†,A_Q)<br/>|phi(A_Q)> = Q|phi(A)>"]
    Q -. "adjacent two-site Q" .-> R["operator-Schmidt rank rho <= d^2<br/>safe bound D'_e <= rho D_e"]
```

The load-bearing invariant is

\[
\mathcal R(C,A)=C|\phi(A)\rangle.
\]

The load-bearing closure bound is

\[
D'_e\le
\begin{cases}
rD_e,&e\text{ lies on the selected routing tree},\\
D_e,&e\text{ is not routed}.
\end{cases}
\]

For a nonidentity qubit Pauli rotation, \(r\le2\).  These are existence and
exact-representation statements only.  The figure deliberately omits
measurement/reset/Record loops, truncation, contraction environments, runtime,
memory, and application-specific benchmarks because none is needed to prove
GCAPEPS mathematical feasibility.

