# H3 + H5 pre-registration — substep `dt` bracket + the G2 composed-vs-joint predicted bands

**Status:** theory-first pre-registration (predict-before-measure), the last two pre-build items before the
first `src/` module (`forward/joint_lindbladian.py` + the G2 gate). Pure derivation + numbers, **no `src/`**.
Binds to `qec_coupling_simulator_build_contract.md` (G2 is now the HEADLINE fidelity gate under the
faithful-infrastructure positioning) and `full_error_coupling_prereg.md` §4 (the commutator predictions).
H3 (`dt`) and H5 (G2 band) are COUPLED: the composed-vs-joint error scales as `dt²`, so the `dt` bracket
propagates into the G2 band.

**Epistemic frame (METRICS.md).** (a)-exact: the commutator identities + the exact-zero positive controls.
(b)-band: the nonzero-pair composed-vs-joint magnitudes (registered falsifiable bets). (c)-decision: the
`dt` brackets (device-value design constants) + the in-band tolerance.

---

## H3 — substep `dt` provenance (class-(c) bracket + sensitivity)

The parsed `XZZXSchedule` (`xzzx_parser.py`) gives layer ORDER only — **no absolute durations** ("Stim
timing = structure-only"). The per-substep duration `dt` for `expm(L_substep·dt)` is therefore a class-(c)
design constant. To avoid a `(c)` constant laundering an unknown physical param (toy-generator risk), it is
**bracketed from typical superconducting / Google-device values and SWEPT, with the joint-L output's
sensitivity reported** — never a frozen magic number.

| substep | `dt` bracket (ns) | source (c) | slice #1 relevance |
|---|---|---|---|
| 1q-gate layer | **[20, 30]** (nominal 25) | Google/transmon 1q ~25 ns | DR×ZZ (the G2 headline nonzero pair) |
| CZ layer | **[25, 45]** (nominal 30) | Google CZ ~25–34 ns | ZZ, T1/T2 during CZ |
| idle | **[0, 300]** (schedule-dependent) | dead-time, dense schedules → small | T2/ZZ accumulation |
| readout | [100, 1000] | dispersive RO | slice #2 (RD/MI) |
| reset | [100, 500] | ancilla reset | not slice #1 |

**Sensitivity propagation — TWO sweeps with DIFFERENT power laws (the load-bearing distinction).** The
leading composed-vs-joint error is `ε_ij ≈ ½‖[H_i,H_j]‖·dt²`, and for DR×ZZ `‖[H_DR,H_ZZ]‖ = (Ω/2)·ζ` ⇒
`ε = (Ω ζ/4)·dt²`. The `dt` scaling depends on WHAT is held fixed (this was a real bug in v1 of this doc —
"`1−F ∝ dt⁴`" alone is WRONG when the gate is a real π-pulse):

| sweep | what varies | `ε` law | `1−F` law | meaning |
|---|---|---|---|---|
| **(i) area-preserving physical 1q gate** (`Ω = π/dt`, real π-pulse over a varying duration) | `Ω∝1/dt` | `ε = (πζ/4)·dt ∝ dt` | **`1−F ∝ dt²`** | the PHYSICAL dependence the teacher must reproduce |
| **(ii) fixed-Ω diagnostic** (`Ω` held constant, vary `dt`) | `Ω` fixed | `ε = (Ωζ/4)·dt² ∝ dt²` | **`1−F ∝ dt⁴`** | a structural diagnostic of the `[H,H]·dt²` BCH term |

**The G2 build MUST run BOTH sweeps and confirm the measured `1−F` tracks the CORRECT power law for each**
(`dt²` area-preserving, `dt⁴` fixed-Ω). Reporting only one power, or the wrong one, is a finding (the
assembler is not doing `expm(L·dt)` with the right `Ω(dt)` coupling). The PHYSICAL band (sweep i) is the
registered headline; the fixed-Ω diagnostic (sweep ii) is the structural cross-check.

---

## H5 — G2 composed-vs-joint predicted bands (class-(b), registered BEFORE the G2 run)

The G2 gate (now the HEADLINE fidelity gate) checks, per within-substep pair: exact-zero ⇒ `composed==joint`;
nonzero ⇒ the measured infidelity lands in the predicted band with the predicted scaling. These bands are
registered from `full_error_coupling_prereg.md` §4 (predict-before-measure) — NOT measured-then-fit.

**FIDELITY-METRIC CONVENTION (theory-first, field-standard, METRICS.md ladder — declared BEFORE the run).**
The G2 metric is the **PROCESS (entanglement) INFIDELITY `1−F_e` between the composed and joint CPTP
channels** — the field-standard channel-distinguishability measure (Schumacher 1996; Nielsen, *Phys. Lett. A*
**303**, 249 (2002)), computed as the Uhlmann fidelity between the two trace-normalised **Choi states**
(`J = (1/d)Σ_{pq} E(|p⟩⟨q|)⊗|p⟩⟨q|`) — the SAME Choi/process-fidelity convention the project's
`qutip_*_channels` gtchecks use. Added to `docs/METRICS.md` (forward-fidelity ledger).
**Leading order (the CORRECT constant — corrects a v1 `/d²` error caught in review):** the composed and joint
unitaries differ (BCH) by `V = exp(−iG)` with the Hermitian defect
```
G = (i/2)[H_A,H_B]·dt²        (Hermitian: i × the anti-Hermitian commutator; the i was missing in v1)
```
and for traceless `G` the entanglement infidelity is
```
1 − F_e ≈ Tr(G²)/d = ‖G‖²_F / d = ‖½[H_A,H_B]·dt²‖²_Frobenius / d     (d = window Hilbert dim; the /d NOT /d²)
```
[Derivation: `F_e = |Tr(V)/d|²`; `Tr(V)/d = 1 − (i/d)Tr G − (1/2d)Tr(G²)`; traceless G ⇒
`1−F_e ≈ Tr(G²)/d`.] The CODE (`joint_lindbladian.composed_vs_joint_infidelity_leading`) uses `‖G‖²/D`
(= `/d`) — CORRECT; this doc's earlier `/d²` was the error. The average-gate infidelity (the RB-standard) is
`1−F_avg = d/(d+1)·(1−F_e) ≈ ‖G‖²_F/(d+1)`; worst-case/FT would use the diamond norm (Kitaev) — both reported
only if needed, the registered G2 metric is `1−F_e`. The §4 `ε ≈ ½‖[H,H]‖·dt²` is the OPERATOR-norm magnitude;
the registered `1−F_e` bands below carry the **Frobenius norm + the `1/d` factor**; the POWER LAWS (dt²/dt⁴/ζ²)
are metric-constant-independent and are the sharp tests.

### H5.1 — slice #1 exact-zero POSITIVE CONTROL (a)-exact

**ZZ × T2** (slice #1's two co-modulated mechanisms): both diagonal in `n` ⇒ `[ζ n_a n_b, √(2γφ)n_a] = 0`
EXACTLY. **Registered (TWO witnesses, per Falsifying-tests §1):** the TIGHT STRUCTURAL witness — the
Liouvillian commutator `‖[L_ZZ,L_T2]‖_fro ≤ NUMERICAL_ZERO = 1e-12` (expm-free, the analytic reason
composed==joint) — AND the channel-level superoperator Frobenius distance `‖S_composed−S_joint‖_F ≤ 1e-10` (the declared torch-c128
`matrix_exp` floor), both **dt-INDEPENDENT in structure**. (The process-infidelity `1−F_e` itself + the
Choi-state-from-Kraus distance — which floors at ~6e-12 at dt=20 from the Kraus reconstruction — are REPORTED
diagnostics, NOT the gate; the registered exact-zero witnesses are the two above.) A genuinely-nonzero result
on BOTH is an assembler BUG (broken-check-must-fail-loudly), NOT physics. This is the load-bearing positive
control of the G2 gate — it MUST be able to FAIL (the deliberately sign-flipped assembler fails the channel
witness by ~9 orders).

### H5.2 — slice #1 nonzero-pair BAND (b) — the HEADLINE check

**DR × ZZ** (1q-gate-layer: the single-qubit gate drive `(Ω/2)σx_a` during the static-ZZ `ζ n_a n_b`).
Commutator core `[σx_a, n_a n_b] = iσy_a n_b` ⇒ `‖[H_DR,H_ZZ]‖ ≈ (Ω/2)·ζ`. With a π-pulse `Ω = π/t_1q` and
`ζ ≈ 2π·0.37 MHz = 2.3e-3 rad/ns`:

`ε = (Ω ζ/4)·dt²`. At nominal `dt=25 ns`, `Ω=π/25=0.126 rad/ns`, `ζ=2.3e-3 rad/ns` ⇒ `ε ≈ 0.045 rad`,
`1−F_pro ~ O(ε²)·(metric const) ~ 1e-3` (the §4 nominal band `5e-4–2e-3` reflects the ζ/Ω/metric spread).

| sweep | `ε` law | `1−F_pro` law | band over `dt∈[20,30]` (rel. to nominal `~1e-3`) |
|---|---|---|---|
| **(i) area-preserving** (`Ω=π/dt`) — REGISTERED HEADLINE | `ε ∝ dt` | `1−F ∝ dt²` | `(20/25)²…(30/25)² = 0.64…1.44` ⇒ **`1−F ∈ [6e-4, 3e-3]`** |
| **(ii) fixed-Ω** diagnostic | `ε ∝ dt²` | `1−F ∝ dt⁴` | `0.41…2.07` ⇒ `1−F ∈ [4e-4, 4e-3]` |

**Registered (b)-band:** the PHYSICAL (area-preserving, sweep i) DR×ZZ composed-vs-joint
`1−F_pro ∈ [6e-4, 3e-3]` across `dt∈[20,30]`, tracking **`dt²`** (exact-channel slope ≈2.0); the fixed-Ω
diagnostic tracks **`dt⁴` in the SMALL-`dt` limit** (exact-channel slope→4 as `dt→0`; at device `dt≈25` the
EXACT slope is ~2.87 = a higher-order-BCH finding, see Falsifying-tests §2).
The measured value MUST land in band AND match the CORRECT power law PER SWEEP, plus the `ζ²` scaling
(sweep ζ, confirm `1−F ∝ ζ²`). A measured `1−F` **outside** band, or with the **wrong power law for the
sweep**, is a registered FINDING (not silently re-fit). [The wide-ish band absorbs the operator-vs-Frobenius
+ the `1/d` process-fidelity constant declared above; the POWER LAWS are the sharp, metric-independent
predictions.]

### H5.3 — the other nonzero pairs (b)-band (registered for completeness; later slices)

From §4.2, at their nominal `dt`: SP×ZZ `1−F ~1e-6` (`c_x²`×DR×ZZ); TLS×DR `~1.4e-4`; T1×DR `~7e-6`;
LK×CZ/FS non-perturbative (slice #2, leakage); MI×RD `~1e-4` (slice #2, readout). Each registered with its
§4.2 scaling; measured-vs-band on the slice where the pair is active.

---

## Falsifying tests (registered before the G2 run)

1. **(a) exact-zero positive control:** ZZ×T2 (and every §4.1 pair active in the slice) → `composed==joint`,
   witnessed TWO ways: **(structural, tight, expm-free)** the Liouvillian commutator `‖[L_ZZ,L_T2]‖_fro ≤ 1e-12`
   — this is the ANALYTIC reason composed==joint (the BCH leading term `½[L_A,L_B]dt²` vanishes); **(channel-level)**
   the superop distance `‖S_composed − S_joint‖_fro ≤ 1e-10` (the declared **torch c128 `matrix_exp` floor** —
   observed worst 2.5e-11 at dt=20; numpy `scipy.expm` gives 0, confirming it is INSTRUMENT precision, not a real
   difference; dt=25/30 are machine-zero ~1e-16). The Choi-state-from-Kraus distance has a separate benign ~1e-11
   reconstruction floor (reported as a diagnostic). A deliberately-broken (sign-flipped) assembler must FAIL the
   CHANNEL witness loudly (broken superop distance ~2e-1 ≫ 1e-10; note the sign-flip keeps the pair commuting, so
   it is the channel distance — not the Liouvillian commutator — that catches it).
2. **(b) DR×ZZ band — TWO sweeps (matches §H5.2; the power laws are the sharp metric-independent tests):**
   - **physical area-preserving sweep** (`Ω=π/dt`): EXACT-channel `1−F_pro ∈ [6e-4, 3e-3]` over `dt∈[20,30]`,
     tracking **`dt²`** (measured exact-channel slope ≈ 2.0) and **`ζ²`** — the REGISTERED HEADLINE.
   - **fixed-Ω diagnostic sweep** (`Ω` const): `1−F_pro ∈ [4e-4, 4e-3]`; **`dt⁴` holds in the SMALL-`dt`
     limit** (verify the EXACT-channel slope → 4 as `dt→0`, e.g. `dt∈[2,8]` ns) — at device `dt≈25` the
     EXACT slope is **~2.87**, a registered HIGHER-ORDER-BCH FINDING (`dt⁴` is the leading-order law;
     `[[H_DR,H_ZZ],H_DR]dt³→dt⁶` corrections bend it at finite `dt`). Gating the leading-order `‖G‖²/D`
     proxy at slope 4 alone would be near-vacuous (it is `dt⁴` by construction) — so the gated fixed-Ω test
     is the EXACT-channel small-`dt` convergence, and the device-`dt` slope is reported, not gated.
   Any **wrong power law for the sweep**, or an **out-of-band** result, is a registered FINDING (not re-fit).
3. **(c) dt sensitivity:** the G2 result is reported across the full `dt` bracket (not a single frozen `dt`);
   the headline number carries its `dt`-bracket band.

**These bands are the predict-before-measure contract for the G2 headline gate. The
`forward/joint_lindbladian.py` build is gated on reproducing §H5.1 (exact-zero, machine-precision) first,
then landing §H5.2 (DR×ZZ) in the registered band with the predicted scaling.**
