# Deep research — scalable simulation of COUPLED (correlated + non-Markovian) errors

**Date 2026-06-30.** Cross-field deep-research (109 agents, 26 sources, 25 claims adversarially verified
23-confirmed/2-killed) on: methods that KEEP spatial correlation + non-Markovian memory (not factorize),
for the coupled QEC-noise teacher. Sources are external literature; candidates below must still be 精读
before building. arXiv ids inline.

## The structural verdict

**No single surveyed method satisfies all four requirements** (scalable + keeps correlation + full-2D +
independent-oracle). Methods split cleanly into **factorizing** (scale by dropping the coupling — the wrong
direction) vs **coupling-preserving** (keep it, but demonstrated only small-scale ≤6–21 sites, 1D/quasi-1D).
The full-2D + non-Markovian regime is a genuine open frontier.

## Coupling-PRESERVING candidates (ranked)

1. **Chain-mapping — Block-Lanczos / T-TEDOPA** `[arXiv:2407.10140 (PRA 112 013721, 2025); 2606.30569 (Chin,
   2026)]`. A Block-Lanczos map turns a **SHARED non-Markovian bath coupling multiple emitters** into a
   quasi-1D **ladder whose width = number of coupled emitters** — spatial correlation kept as **long-range
   chain couplings / ladder width**, NOT factored. Cross-correlated ("crossed") baths handled by a
   frequency-dependent T-TEDOPA (HEOM cannot). **Doubles as a quasi-exact small-patch oracle** for the
   coupled/non-Markovian regime within its constraints. CAVEAT: shown ≤6 emitters, bounded excitation,
   bond D≤20; **excitation-number conservation (the basis of its efficiency) collapses under projective
   syndrome measurement + reset (QEC wrapper — unverified)**; ladder width grows with #coupled sites →
   **small-scale oracle, not a full-2D carrier.** Matches our collective-Lindblad (shared-bath-across-qubits)
   requirement for the ≤6-qubit patch regime.
2. **Collisional tensor-network exact solver** `[arXiv:2202.04697 (Filippov & Luchnikov, PRA 105 062410)]`.
   EXACT for a **generally-correlated structured reservoir** — both classical/quantum bath correlations AND
   non-Markovian memory (derives a time-convolution ME linking memory to the bath correlation function).
   **An independent small-scale exact oracle.** CAVEAT: "correlated" = WITHIN-bath for a SINGLE colliding
   system, not correlated dissipation across many spatially-coupled sites; 1D/collisional demos.
3. **PT-MPO / process tensor — ACE, TEMPO** `[arXiv:2405.19319 (ACE); 2201.05529 (chains, PRR 5 033078);
   2603.06840 (time-invariant PT)]`. Numerically-exact non-Markovian by **compressing system-environment
   correlations into a process tensor BEFORE folding**; ACE is general (non-Gaussian), reuses one PT-MPO,
   handles multiple/**collective** environments (superradiance, 5 emitters). **FLAG — "secretly
   re-factorizes":** the linearly-scaling variant PT-TEBD couples **each environment to exactly one site**;
   shared/inter-site baths are **explicitly out of scope** (verbatim). ⇒ exact **small-network benchmark**,
   not the coupled carrier.

## Temporal-memory closure (for the 1/f / TLS memory specifically)

4. **Mori-Zwanzig / generalized Langevin** `[arXiv:1611.03311 (Parish-Duraisamy, PRF 2 014604); 2102.01377
   (EMZ)]`. A **DERIVED** (not ad-hoc) non-Markovian closure: memory kernel + orthogonal-dynamics noise from
   the coarse-graining math. Memory truncated by a finite-length heuristic (spectral-radius rule) —
   convergence, not a-priori.
5. **GLE memory-kernel LEARNING with an a-priori bound** `[SIAM 10.1137/24M1651101 = arXiv:2402.11705 (Lang
   & Lu, 2026)]`. Learn the kernel from trajectory data (Prony + RKHS regression). **UNIQUELY among all
   surveyed methods, an A-PRIORI error bound** (trajectory error ≤ ∝ kernel-estimation error). CAVEAT: 1D
   scalar kernel, single-observable; does not itself do spatial correlation or 2D.
- **Unifying theory** `[Nat. Commun. 2024, s41467-024-52081-3 = arXiv:2312.13233]`: Nakajima-Zwanzig memory
  kernel ⇔ influence functional (process tensor) are formally equivalent — but for a single N-level system +
  Gaussian baths.

## Also surfaced (QEC-native, already cached): quantum combs
`[arXiv:2603.05474]` "Spatiotemporal Pauli Processes: quantum combs for correlated QEC noise" — maps
multi-time, spatially-structured NON-Markovian device dynamics to a spatiotemporal Pauli **process tensor /
comb** via a multi-time twirl. Cached as `kam_spatiotemporal_pauli_processes_2603.05474.md` — the QEC-side
process-tensor bridge; re-read against the above.

## What this means for us (the actionable synthesis)

1. **The independent-oracle problem is ADDRESSABLE in bounded regimes** — and that is the biggest win. Chain-mapping (2407.10140)
   gives a quasi-exact small-oracle for the coupled/non-Markovian case **within its excitation-conservation +
   ≤6-emitter regime**; the collisional TN (2202.04697) gives an exact oracle for **within-bath** correlation
   (not cross-qubit shared-bath). Together they cover complementary pieces — but neither is a full solution
   for our cross-qubit shared-bath problem at QEC scale. **The remaining gap (shared-bath cross-qubit
   non-Markovian oracle) is the genuine methodological contribution.**
2. **The architecture is a COMPOSITION, not one method:** a **process-tensor / chain-mapping carrier** for
   the shared bath + spatial correlation, a **MZ/GLE learned memory kernel** for the temporal 1/f/TLS memory
   (the a-priori-bounded piece), a **2D geometry carrier** (PEPS/boundary-MPS — the open frontier) — each
   validated against the small-scale exact oracle.
3. **The open frontier = full-2D + non-Markovian** (PEPS-family + process-tensor influence functional). The
   research did NOT find this solved; it's the genuine research contribution if we can do it.

## Open questions the research raises (the sharp ones)
- Can chain-mapping compose with a 2D carrier so the ladder width scales with code **distance** (a locality
  bound on jointly-coupled sites per QEC window), not total qubit count?
- Faithfulness cost of a truncated MZ/GLE kernel vs the exact oracle at d3 — does it preserve the
  **coherence-revival** signature (our unforgeable non-Markovian wedge)?
- Spatial-coupling + temporal-memory: separate carriers composed, or joint — and what is the oracle for the
  JOINT regime?
- Do PEPS-family open-system carriers (iPEPO, tePEPO) admit non-Markovian process tensors, or are they
  structurally Markovian?

## Next (theory-first)
精读 the top candidates before any build: chain-mapping (2407.10140, 2606.30569), collisional-TN (2202.04697),
MZ/GLE-learning (2402.11705), quantum-comb QEC (2603.05474, cached), ACE/PT-MPO (2405.19319). Then a design
that COMPOSES an oracle-validated small-scale coupled carrier + memory-kernel closure + a 2D-geometry plan.
