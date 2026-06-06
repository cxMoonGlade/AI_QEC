# Teacher and Learner

In the twin (`docs/TWIN.md`), "teacher" and "learner" are:

- **Teacher** — a controlled, known mechanism source
  (`experiments.twin.mechanisms`): a small, exactly-simulable system (e.g. a
  coherent over-rotation rep-code teacher) whose true channels and true
  `do() -> ΔLER` are **known**. It is the counterfactual ground truth — the only
  thing that can validate a knob, since calibration fit alone cannot (ADR 0002/0003).
- **Learner** — label-free calibration
  (`experiments.twin.calibration`): recovers the local CPTP channel field
  `E` by exact multi-context Born-rule observation-NLL over the probe-richness
  ladder `C_cal(r)`, seeing only observations `p(s,m | c)`.

## Isolation contract

The learner consumes **only observations**. The teacher's true channels,
parameters, axis, and labels are evaluator-only: they are used to *score*
counterfactual validity (`B_LER`, `B_obs` = the gap between the teacher's true
`do()` effect and the twin's predicted effect), never fed to the learner. A twin
that fits the data is not trusted until its knobs match the teacher's ground truth.

## Object and notation

The twin's object is the CPTP channel field `E` with

```
p(y | c) = Tr[ M_y · C(c)(rho0) ],   C(c) = ∏_q (E_q ∘ G_q)
```

A DEM parity model (`e_j ~ Bernoulli(p_j)`, `y = A e mod 2`, `A ∈ F_2^{B×M}`)
survives only as the **frozen decoder** substrate (`dem.stim_dem`,
`dem.fault_graph`), not as a learned object. Full notation: `docs/TWIN.md`.

## History

The earlier catalog teacher/learner packages (`data_preparation`, `teacher`,
`learner`) and the DEM fault-logit / discovery program were retired and removed
(ADR 0005). The teacher-learner *method* — a controlled teacher for ground truth +
a label-free learner — survives in the twin B-path.
