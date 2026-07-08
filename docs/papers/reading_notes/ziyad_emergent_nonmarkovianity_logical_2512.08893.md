# 精读 — Ziyad, Blume-Kohout, Rudinger, "Emergent Non-Markovianity in Logical Qubit Dynamics" (arXiv:2512.08893)

> **Provenance (2026-07-03): FULL-TEXT 精读 of the core (§1 intro + headline, §2 logical-Markovianity
> definition, §3 opening = the gadget/effective-logical formalism).** PDF → txt `outputs/papers/2512.08893.txt`
> (PyMuPDF, 21 pages, arXiv v3 19 Feb 2026). §3 toy-model quantification + §4 general subsystem theory +
> appendices are in the txt for deeper reads (summarized below at the level the reconstruction needs).
> Tags: **[paper]** stated; **[ours]** our inference.

## Metadata [paper]
- **Authors.** Jalan A. Ziyad, Robin Blume-Kohout, Kenneth Rudinger (Sandia Quantum Performance Lab / UNM).
  High-trust — the GST authors.
- **Venue.** arXiv:2512.08893v3 (19 Feb 2026). Type: theory + small-code analysis.

## Executive summary [paper]
**Logical qubits can be non-Markovian even when the underlying PHYSICAL noise is perfectly Markovian.**
The authors define a "button-theoretic" (GST-style) Markovianity condition for programmable devices, apply
it to small codes, and PROVE: emergent logical non-Markovianity occurs **if and only if the physical data
qubits do not return to the code subspace after every round of QEC.** When that holds, the data-qubit
Hilbert space factors into (logical qubit) ⊗ (syndrome qubits), and **the syndrome qubits act as a
persistent ENVIRONMENT/MEMORY** for the logical qubit — carrying information of the recent past and feeding
it back, producing detectable non-Markovianity with a clear signature: **non-exponential decay of the
logical polarization ⟨Z̄⟩.** They give sufficient conditions for GST/RB to remain reliable on logical
qubits in early FT devices.

## Method (deep) — the exact objects [paper]
- **Button-theoretic Markovianity (§2, GST-model based).** A device satisfies it iff every time a given
  "button" (state-prep / gate / measurement) is pressed, the register undergoes the EXACT same CPTP
  transformation, regardless of context — so any sequence's map equals the composition `G_c G_b G_a`.
  This is exactly the assumption GST/RB rely on; its failure makes GST/RB-inferred models unreliable /
  non-predictive. (Depends on the assumed dimension — any NM process is the reduced dynamics of a
  Markovian process on a larger space; Def. 1, App. B.)
- **Gadget retraction Ω (§2, Eq. 2).** For an `[[n,k]]` code with encoder `E` and decoder `D`, the effective
  k-qubit logical process of an n-qubit operation `G` is `Ω[G] := D ∘ G ∘ E`. The noisy gate gadget `G̃_L`
  has effective logical process `Ω[G̃_L]`. Logical Markovianity = button-theoretic Markovianity for the set
  of ALL logical operations (incl. the logical idle), i.e. `Ω[G̃_b] Ω[G̃_a] = Ω[G̃_b G̃_a]` for all sequences.
- **The mechanism (§3–4).** If the QEC round does not project the data qubits back into the code subspace,
  the composition rule breaks: `Ω[G̃_b G̃_a] ≠ Ω[G̃_b] Ω[G̃_a]`, because the residual out-of-code-subspace
  amplitude (held in the syndrome-qubit factor) survives between logical operations and correlates them.
  The syndrome subsystem is the memory. Signature: non-exponential `⟨Z̄⟩(t)` (vs exponential for Markov).
- Physical qubits assumed Markovian (button-theoretic) + error-free prep/measure gadgets, to isolate the
  gate-gadget effect. Related: Ref. [30] (logical NM impacts logical RB); Endo et al. [35] (NM in QEC via
  CP-divisibility, error-mitigation focus).

## Findings [paper]
- **The iff theorem:** emergent logical NM ⟺ data qubits not returned to the code subspace each round.
- Small codes exhibit it "even for very simple physical noise models."
- Practical: sufficient conditions under which GST/RB on logical qubits stay reliable in early FT devices.

## Limitations [paper]
- Small codes / toy models; error-free prep+measure assumption; physical Markovianity assumed.
- Quantifies the effect in specific syndrome-extraction circuits, not a general-device bound.

## Relevance to the reconstruction [ours]
- **A second QEC-specific proof that non-Markovianity is a REAL, measurable feature of logical/syndrome
  dynamics** — reinforcing the retraction of "record-level NM is a faithful sub-floor." Here NM emerges
  intrinsically from the QEC structure (syndrome-as-memory), measurable via non-exponential `⟨Z̄⟩`.
- **Identifies the physical LOCUS of the record-level memory: the syndrome qubits (not returning to the
  code subspace).** This sharpens the reconstruction's source model — the memory carrier that matters is
  the syndrome/ancilla subsystem, exactly the "ancilla-no-reinitialization" pathway flagged in Gravier
  [[nonmarkovian_noise_resilience_silicon_spin_2507.08713]]. The teacher should model this, and the
  `qec_twin` learner should target the logical/syndrome effective process.
- **Button-theoretic Markovianity + the gadget retraction Ω** give the GST-side definition of the object we
  characterize (the effective logical process), complementary to White's process-tensor Υ
  [[white_pollock_process_tensor_tomography_2106.11722]] and Zheng's syndrome-learnability
  [[qec_learnable_logical_noise_2601.22286]]. The reconstruction's "coherent-vs-incoherent + memory"
  observables measure exactly the non-Markovianity of `Ω[G̃]`.
- **Honesty:** the effect can be "only a small amount" in realistic scenarios — so effect-size still
  matters (the reconstruction must size it on a realistic source), but it is NOT structurally zero /
  sub-floor. It is a genuine, GST-reliability-relevant signal.

## Related notes
[[white_pollock_process_tensor_tomography_2106.11722]], [[qec_learnable_logical_noise_2601.22286]],
[[nonmarkovian_noise_resilience_silicon_spin_2507.08713]] (Gravier — ancilla-memory pathway),
[[keeling_process_tensor_2509.07661]], [[qec_insitu_benchmarking_clifford_2601.21472]] (GST-adjacent).
