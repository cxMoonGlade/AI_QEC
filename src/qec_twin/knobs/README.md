# knobs — [MANIPULATE]

The "noise simulator with knobs": channel-level, parameterization-independent
`do()` operations on the recovered channel field, scored by their observable
consequence ΔLER under a **frozen** decoder.

- `intervention.py` — do() operators (Tier-0 remove `E→I`; Tier-1 CPTP-safe weaken
  `(1-a)I + aE`) + ΔLER scoring (`B_LER` / `B_obs`).
- `reference.py` — reference / nominal decoder + DEM setup.

**Boundary.** Applies knobs and measures their effect. Does not calibrate
(→ `calibration`) or quantify uncertainty on the answer (→ `audit/bands`). A knob
is a transform of the channel itself, never an edit of a teacher-native parameter.
Uses `decoder` (frozen MWPM) + `forward`. Spec: `docs/TWIN.md`.
