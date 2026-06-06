# forward — exact differentiable forward model (the physics engine)

Maps a context `c` and the local CPTP channel field `E` to the observation
distribution `p(s,m|c) = Tr[M_y C(c)(rho0)]`. **Backend-swappable** behind this
contract.

Backend-agnostic channel object (top level — survives a backend swap):
- `cptp_channel.py` — CPTP-by-construction parameterized channel (θ → Kraus).
- `channels.py` — channel constructions; `cptp_guardrail.py` — CPTP audit;
  `ptm.py` — PTM representation.

Backends:
- `exact/` — **density-matrix simulation. ⚠ FEASIBILITY-ONLY** (`2^n × 2^n`,
  unusable past ~15 qubits). Validates the B-path loop, then abandoned.
- `scalable/` — **placeholder** for the >50-qubit backend (target noise circuits);
  carrier deferred (ADR 0005).

**Boundary.** The channel object and the four capability modules do NOT depend on
the backend — swapping `exact → scalable` is a backend replacement, not a rewrite.
Spec: `docs/TWIN.md`.
