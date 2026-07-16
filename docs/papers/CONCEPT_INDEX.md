# Current literature concept index

Generated from the explicit current corpus manifest. Only source-reviewed `paper_fact`
relationships appear here. This is routing metadata; the cited PDF and locator remain
the evidence.

- corpus status: active
- sources: 9
- concept nodes: 13
- source-located relationships: 13
- dangling relationships: 0

## DLM twirl (limitation)

- **limits** — Quantification and Characterization of Leakage Errors — `Sec. VI.A.3, Eq. (49) and its preceding paragraph`, PDF p. 8 — The printed DLM twirl introduces independent leakage-subspace unitaries `U_2,V_2` and sums over both, while Eq. (49) divides by only one factor of `|P_2|`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## leakage randomized benchmarking decay model (limitation)

- **limits** — Quantification and Characterization of Leakage Errors — `Sec. III, assumptions (i)--(ii)`, PDF p. 3 — The leakage randomized benchmarking decay model requires computational-subspace twirling to average cross-subspace coherence and the leakage-subspace population to be depolarized. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## depolarizing leakage extension (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.A.2, Eqs. (46)--(47)`, PDF p. 8 — The depolarizing leakage extension of a computational-subspace channel is the model in Eq. (46), parameterized by leakage and seepage rates and completely depolarizing maps between the two subspaces. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## depolarizing leakage model (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.A.3, Eq. (48)`, PDF p. 8 — The depolarizing leakage model is the DLE special case in Eq. (48) whose computational-subspace component is depolarizing. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## Lindblad leakage model (model)

- **uses** — Quantification and Characterization of Leakage Errors — `Sec. VI.C, Eqs. (69)--(70)`, PDF p. 10 — A Lindblad leakage model is written as `E = exp[t(mathcal H + mathcal D)]`, where superoperator `mathcal H` acts as `mathcal H(rho) = -i[H,rho]` for Hamiltonian `H` and `mathcal D` is presented as the dissipative generator. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## simple dissipative leakage model (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.C.1, Eq. (72)`, PDF p. 11 — The simple dissipative leakage model uses jump `A_21 = |2><1|` with rate `gamma_1` for leakage and jump `A_12 = |1><2|` with rate `gamma_2` for seepage. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## unitary leakage model (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.B, Eqs. (57)--(58), first equality`, PDF p. 9 — The unitary leakage model starts from `H = (|1><2| + |2><1|)/2` and defines its propagator by `U(t) = exp(-i t H)`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## channel coherent leakage and seepage rates (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. V.B, Eqs. (42)--(43)`, PDF p. 7 — The channel coherent leakage and seepage rates are Haar averages of `C_L(E(|psi_j><psi_j|))` over rank-one projectors formed from all Haar-distributed pure states in subspaces `X_j`, for `j=1,2`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## coherence of leakage (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. V.A, Eqs. (30)--(34)`, PDF p. 6 — The coherence of leakage of a state is `C_L(rho) = ||P_C(rho)||_1`, where `P_C(rho) = 1_1 rho 1_2 + 1_2 rho 1_1` is the cross-subspace block. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## leakage rate (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. II, Eq. (2)`, PDF p. 2 — For a CPTP map `E`, the leakage rate is `L_1(E) = L(E(1_1/d_1))` and the seepage rate is `L_2(E) = 1 - L(E(1_2/d_2))`, equal to Haar averages over input states in the respective subspaces. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## seepage rate (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. II, Eq. (2)`, PDF p. 2 — For a CPTP map `E`, the leakage rate is `L_1(E) = L(E(1_1/d_1))` and the seepage rate is `L_2(E) = 1 - L(E(1_2/d_2))`, equal to Haar averages over input states in the respective subspaces. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## state leakage (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. II, Eq. (1)`, PDF p. 2 — State leakage is the population outside computational subspace `X_1`, defined by `L(rho) = Tr[1_2 rho] = 1 - Tr[1_1 rho]` on the direct sum `X = X_1 direct-sum X_2`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## Proposition 2 bound (theorem)

- **supports** — Quantification and Characterization of Leakage Errors — `Sec. V.B, Proposition 2`, PDF p. 7 — The Proposition 2 bound states `C_Lj(E) <= 2 sqrt(L_j(E)(1-L_j(E)))` for the channel coherent leakage and seepage quantities. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))
