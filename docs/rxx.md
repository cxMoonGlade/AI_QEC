The more direct fix is to **stop treating RXX/RZZ/RYY recovery as a generic multiclass classification problem** and instead formulate it as a **local generator-identification problem**.

The current path is:

```text
features → classifier → mechanism label
```

The more physical/mathematical path is:

```text
chosen probes → local Pauli/Lindblad response matrix → estimate generator coefficients
```

## 1. Reparameterize the problem in a physics basis

For the RZZ-family ambiguity, do not ask the learner to distinguish labels like:

```text
M1 coherent RZZ
M7 depolarizing after RZZ
M8 coherent RXX/RYY
M10 correlated relaxation
```

Instead, fit a local two-qubit generator:

```math
\mathcal L(\rho)
=
-i[h_{XX}XX+h_{YY}YY+h_{ZZ}ZZ,\rho]
+
\gamma_{XX}(XX\rho XX-\rho)
+
\gamma_{YY}(YY\rho YY-\rho)
+
\gamma_{ZZ}(ZZ\rho ZZ-\rho)
+
\mathcal L_{\mathrm{relax}}(\rho).
```

Then the question becomes:

```text
Can we estimate h_XX, h_YY, h_ZZ, γ_XX, γ_YY, γ_ZZ, and relaxation terms?
```

This is much cleaner than asking a classifier to infer a hidden mechanism ID from compressed final-shot features.

This direction is standard in spirit: gate set tomography is designed for detailed, predictive, self-consistent characterization of gate operations, and pyGSTi explicitly supports parameterizations such as Hamiltonian + stochastic + affine or Hamiltonian + depolarization error models. ([Quantum][1])

## 2. Use observability rank, not classifier accuracy, as the first test

Define a small parameter vector:

```math
\theta =
(h_{XX}, h_{YY}, h_{ZZ}, \gamma_{XX}, \gamma_{YY}, \gamma_{ZZ}, \gamma_{\mathrm{relax}}, \ldots).
```

For each probe condition (a), circuit (c), and observable/feature (f), compute a local sensitivity:

```math
J_{(a,c,f),k}
=
\frac{\partial}{\partial \theta_k}
\mathbb E[f \mid a,c,\theta]
\bigg|_{\theta=0}.
```

Then check:

```math
\operatorname{rank}(J_{\mathrm{RZZ-family}})
```

If this rank is deficient, no classifier can reliably separate those mechanisms. The data are mathematically non-identifying.

So the direct S2D.8e/S2D.9 test should be:

```text
Does the learner-visible response Jacobian have independent columns for XX, YY, ZZ, depolarizing, and relaxation directions?
```

This converts the problem from “try stronger probes” into:

```text
construct probes until the Fisher/sensitivity matrix has full useful rank.
```

That is the mathematically direct solution.

## 3. Use the commutator rule to design probes

For a small coherent Pauli error

```math
U_P(\epsilon)=e^{-i\epsilon P/2},
```

the first-order response of observable (O) is controlled by:

```math
\frac{d}{d\epsilon}\langle O\rangle_{\epsilon}\bigg|_{\epsilon=0}
=
\frac{i}{2}\langle [P,O]\rangle.
```

So:

```text
If [P, O] = 0, that observable is first-order blind to coherent P.
If [P, O] ≠ 0, that observable can see coherent P.
```

This is probably the core physics reason your current final-shot features fail. Many detector/syndrome-style observables are effectively parity-like and may commute with parts of the RXX/RYY/RZZ family after aggregation.

For example:

```text
XX, YY, ZZ commute with each other as two-qubit Pauli products.
```

So measuring only two-qubit parity-style quantities can fail to separate them. You need observables that anticommute differently with each generator.

Examples:

```text
Observable ZI:
  sensitive to XX and YY,
  not first-order sensitive to ZZ.

Observable XI:
  sensitive to YY and ZZ,
  not first-order sensitive to XX.

Observable YI:
  sensitive to XX and ZZ,
  not first-order sensitive to YY.
```

This suggests a direct probe design:

```text
prepare local Pauli eigenstates
apply target layer / perturbed layer
measure local X/Y/Z marginals and two-body correlators
estimate the local response Jacobian
```

This is closer to local tomography/Ramsey-style generator identification than to classification.

## 4. Be careful: twirling can erase the signal you want

Averaged Pauli twirling is useful when you want to convert or tailor general noise into stochastic Pauli noise; that is exactly why it helps simulation and benchmarking workflows. 

But for your goal, averaged twirling can be harmful:

```text
coherent RXX/RYY/RZZ identity
→ twirl average
→ stochastic Pauli-like channel
→ generator direction partly erased
```

So if you use twirls, do **not** only keep the averaged twirl result. Keep the **per-twirl response signature**. Otherwise you may deliberately destroy the coherent information needed to separate M1 from M8.

## 5. Separate coherent vs stochastic before separating XX vs ZZ

There are two different questions:

```text
coherent vs stochastic?
XX vs YY vs ZZ?
```

They should not be solved at the same time.

A coherent unitary error rotates states, while incoherent noise tends to shrink or translate the state representation; unitarity randomized benchmarking is built around this coherent-vs-incoherent distinction. ([Forest Benchmarking][2])

So a better decomposition is:

```text
Stage A:
  Is the response coherent/Hamiltonian-like or stochastic/dissipative?

Stage B:
  If coherent, which Hamiltonian direction: XX, YY, or ZZ?

Stage C:
  If stochastic, which Pauli/dissipative direction?

Stage D:
  If non-unital/asymmetric, classify relaxation-like structure.
```

This is much more physical than one global label classifier.

## 6. Use Pauli transfer matrix blocks instead of final-shot features

A Pauli transfer matrix representation directly describes how a quantum channel maps Pauli operators to Pauli operators. Recent Hamiltonian-learning work also frames channel/Hamiltonian learning through Pauli transfer matrices and short-time dynamics. ([arXiv][3])

For your case, you do not need full tomography. You only need a local two-qubit PTM subblock around the target interaction.

For a two-qubit subsystem, track response among a small Pauli set:

```text
XI, YI, ZI,
IX, IY, IZ,
XX, YY, ZZ,
XY, XZ, YZ,
YX, ZX, ZY
```

Then:

```text
coherent Hamiltonian errors
  appear as structured off-diagonal rotations in the PTM;

Pauli-stochastic errors
  appear mainly as diagonal contractions;

relaxation / amplitude-damping-like errors
  introduce non-unital / affine components.
```

This is a much more direct substrate for the RXX issue than final-shot detector summaries.

## Recommended next pivot

I would rename the next step away from “stronger probe” and toward:

```text
S2D.9_local_Pauli_Lindblad_observability
```

Core artifacts:

```text
generator_dictionary.json
  XX, YY, ZZ Hamiltonian generators
  XX, YY, ZZ stochastic generators
  relaxation / affine generators

probe_observable_schema.json
  preparation basis
  measurement basis
  observable list

response_jacobian.npy / response_jacobian.json
  sensitivity matrix J

observability_rank_metrics.json
  rank
  singular values
  condition number
  pairwise column angles

ptm_block_reconstruction.json
  local PTM response estimates

generator_recovery_metrics.json
  coefficient recovery error
  sign recovery
  coherent-vs-stochastic separation

summary.md
```

Success should be defined as:

```text
The response Jacobian has separated columns for h_XX, h_YY, h_ZZ, γ_XX, γ_YY, γ_ZZ, and relaxation terms after circuit_id residualization.
```

Not:

```text
classifier accuracy improves.
```

## Bottom line

The direct physics/math fix is:

```text
Do not chase RXX recovery through larger feature stacks.
Build a local Pauli/Lindblad generator model, design observables using commutator sensitivity, and verify identifiability by rank/Fisher analysis before training any classifier.
```

In one sentence:

```text
The RXX issue should be treated as a local Hamiltonian-generator observability problem, not as a black-box mechanism classification problem.
```

[1]: https://quantum-journal.org/papers/q-2021-10-05-557/ "Gate Set Tomography – Quantum"
[2]: https://forest-benchmarking.readthedocs.io/en/latest/examples/randomized_benchmarking_unitarity.html "Randomized Benchmarking: Unitarity RB — Forest-Benchmarking 0.6.0 documentation"
[3]: https://arxiv.org/abs/2212.04471 "[2212.04471] Learning Quantum Processes and Hamiltonians via the Pauli Transfer Matrix"
