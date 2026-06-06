> **⚑ ARCHIVED (ADR 0009, 2026-06-05).** This document is the retired **SCOPE**
> thesis (Symmetry-Compressed Orbit-Physical Emulator): the L2 orbit-compression
> field `θ = ρ(g)ϑ_ω + Uz` as a claimed identifiability/parameter-economy lever,
> and the six-axis physical-generation bar. It is **superseded by the current spec
> [`docs/TWIN.md`](TWIN.md)** and kept only for historical record. Why retired: the
> B-path obtained every identifiability win **without** any orbit field — what
> broke the observational alias was **probe richness (data)**, not parameter-tying;
> orbit-sharing shrinks variance, not a genuine observational alias. The
> *implementation substrate* described below (DEM/Bernoulli core, controlled
> catalog, Stage-3 visible discovery, the exact CPTP primitives) remains valid; the
> notation `ω(j)` survives in `TWIN.md` only as **known teacher structure**, never
> as a thesis. Do not cite this document's SCOPE/orbit framing as current.

### SCOPE-Twin: Symmetry-Compressed Orbit-Physical Emulator

SCOPE-Twin is the long-horizon target: a digital twin built by discovering
compact, auditable latent noise structure from QEC observations, then using
that structure for generation, interpretation, decoder-facing utility,
cross-context transfer, drift prediction, and identifiability tests.

The current code does not implement the full amortized physical parameter-field
object below. It implements the SCOPE-Static, controlled-catalog, and Stage 3
visible-discovery pieces that form the evidence ladder toward this target.

As of 2026-06, the exact CPTP physical substrate — Layer 3 (PhysDec) and Layer 4
(circuit-level likelihood) below — is an active, prioritized build (see *Current
Reprioritization* just before *Contributions*), pulled ahead of the visible
neural-discovery ordering because the operational target is the interventional
noise simulator with mechanism knobs.

##### Notation and Object Contract

This contract is part of the model specification. Before running or interpreting new
experiments, the implementation and writeup must use these names consistently.

###### Reserved symbols

| Object | Symbol | Meaning |
| --- | --- | --- |
| circuit context | \(c\) | hardware schedule, controls, code descriptor, drift context |
| template | \(t\in\mathcal T\) | type of local noise/channel module |
| time/window index | \(n\) or \(\tau\) | training example, shot window, or drift time |
| rounds | \(R\) | number of syndrome extraction rounds |
| residual rank | \(r_t\) | rank for residuals of template \(t\) |
| physical/circuit location | \(i\in\mathcal I_t\) | location where template \(t\) applies |
| DEM fault index | \(j\in\{1,\ldots,M\}\) | effective DEM fault used by Stage 1 |
| orbit index | \(\omega\in\Omega_t\) | symmetry class |
| orbit map | \(q_t(i)=\omega\) | maps physical location to orbit |
| DEM-fault orbit map | \(\omega(j)\in\Omega\) | maps DEM fault \(j\) to its known orbit |
| logical observable | \(m\) | logical observable bit or outcome; never \(o\) |
| observation | \(y=(s,m,\ldots)\) | syndrome plus logical observable and optional metadata |
| DEM parity map | \(\mathsf A\) | binary fault-to-observation map |
| learned soft assignment | \(S\) or \(\Pi\) | Discovery assignment matrix; never \(\mathsf A\) |
| circuit operation index | \(q\in\mathcal Q(c)\) | one ideal operation in circuit order |
| Stage-1 fault logit | \(\lambda_j\) | \(\operatorname{logit}(p_j)\); never \(\ell_j\) |
| fault-level features | \(\phi^{\mathrm{fault}}_j\) or \(\tilde\phi_j\) | features attached to DEM fault \(j\) |
| location-level features | \(\phi^{\mathrm{loc}}_{i,t}\) | features attached to physical location/template |
| orbit-level features | \(\phi^{\mathrm{orb}}_\omega\) | orbit prototype features |
| visible assignment unit | \(\xi\in\mathcal U_{\mathrm{vis}}\) | protocol-declared visible unit such as a probe batch or public syndrome-response signature |
| visible feature vector | \(x^{\mathrm{vis}}_\xi\) | frozen learner-visible features for visible unit \(\xi\) |
| visible prototype assignment | \(\Pi_{\xi k}\) | Stage 3 visible-surface assignment matrix when rows are not DEM faults or physical locations |

Do not use \(o\) for orbit or logical observable. Use \(\omega\) for orbit and
\(m\) for logical observable. Do not use \(\ell\) for both circuit operations and
logits. Use \(q\) for circuit operations and \(\lambda_j\) for Stage-1 fault
logits.

When the assignment rows are visible-surface units rather than DEM faults or
physical locations, use \(\xi\) for the row index and \(\Pi_{\xi k}\) for the
assignment. Reserve \(j\) for DEM faults and \(i\) for physical/circuit
locations inside this document.

###### Stage-1 DEM-fault contract

Stage 1 is fault-level logit learning over effective DEM faults, not a physical
location field. Let

$$
M=\text{number of effective DEM faults},
\qquad
B=\text{number of observation bits}
=\text{detectors}+\text{logical observables}.
$$

The DEM parity map is

$$
\mathsf A\in\mathbb F_2^{B\times M}.
$$

Column \(j\) is the detector/logical mask of fault \(j\):

$$
a_j=\mathsf A_{:,j}\in\mathbb F_2^B.
$$

Fault bits and observations are

$$
e_j\sim\mathrm{Bernoulli}(p_j),
\qquad
y=\mathsf A e \pmod 2.
$$

The fault logit is

$$
\boxed{\lambda_j=\operatorname{logit}(p_j)}.
$$

Therefore Stage 1 must not write \(\ell_j\) for logits.

###### Stage-1 orbit contract

Let \(\omega(j)\in\Omega\) be the known orbit assignment of DEM fault \(j\), and

$$
\mathcal O_\omega=\{j:\omega(j)=\omega\}.
$$

The three Stage-1 hypotheses are:

**Local**

$$
\lambda_j=\gamma_j.
$$

**Hard orbit**

$$
\boxed{\lambda_j=\alpha_{\omega(j)}}.
$$

**Soft feature orbit**

$$
\boxed{
\lambda_j
=
\alpha_{\omega(j)}
+
\beta_{\omega(j)}^\top\tilde\phi_j
}.
$$

Here

$$
\tilde\phi_j\in\mathbb R^r
$$

is a fault-level residual feature. Parameter counts are

$$
P_{\mathrm{local}}=M,\qquad
P_{\mathrm{hard}}=\lvert\Omega\rvert,\qquad
P_{\mathrm{soft}}=\lvert\Omega\rvert(1+r).
$$

This is the precise experimental claim for whether soft residuals add value over
hard orbits.

###### Residual feature contract

The residual feature must be centered within each DEM-fault orbit:

$$
\tilde\phi_j
=
\phi^{\mathrm{raw}}_j
-
\frac{1}{\lvert\mathcal O_{\omega(j)}\rvert}
\sum_{k\in\mathcal O_{\omega(j)}}
\phi^{\mathrm{raw}}_k.
$$

Therefore

$$
\boxed{
\sum_{j\in\mathcal O_\omega}\tilde\phi_j=0
}.
$$

The key audit is nonzero centered rank for at least some non-singleton orbits:

$$
\boxed{
\operatorname{rank}
\left[
\left(
I_{\lvert\mathcal O_\omega\rvert}
-
\frac{1}{\lvert\mathcal O_\omega\rvert}
\mathbf 1\mathbf 1^\top
\right)
\Phi_\omega
\right]
>0
}
$$

for at least one \(\omega\) with \(\lvert\mathcal O_\omega\rvert>1\), where
\(\Phi_\omega\) stacks the raw or residual feature rows for faults in
\(\mathcal O_\omega\).

Every Stage-1 run must report:

```json
{
  "num_orbits": "...",
  "num_non_singleton_orbits": "...",
  "num_orbits_with_nonzero_centered_feature_rank": "...",
  "mean_centered_feature_rank": "...",
  "max_centered_feature_rank": "..."
}
```

If this diagnostic is zero, the soft-residual experiment is invalid.

The bug this prevents is:

$$
\lambda_j=\alpha_{\omega(j)}+\beta_{\omega(j)}^\top\phi_j.
$$

If the feature builder accidentally gives \(\phi_j=c_\omega\) for every
\(j\in\mathcal O_\omega\), then

$$
\lambda_j
=
\alpha_\omega+\beta_\omega^\top c_\omega
=
\tilde\alpha_\omega,
$$

so the soft orbit model collapses into the hard orbit model. That is a
specification failure, not evidence against the soft-residual model.

###### Implementation-level data contract

Every Stage-1 `FaultGraph` should explicitly store:

```python
FaultGraph:
    A: BoolTensor[B, M]                  # DEM parity map, mathsf A in the doc
    fault_ids: IntTensor[M]
    det_masks: BoolTensor[num_detectors, M]
    logical_masks: BoolTensor[num_observables, M]
    orbit_ids: IntTensor[M]              # omega(j)
    orbit_sizes: IntTensor[num_orbits]
    raw_features: FloatTensor[M, F]
    residual_features: FloatTensor[M, r] # centered within orbit
    feature_rank_by_orbit: Dict[int, int]
```

Stage-1 field classes should be level-explicit:

```python
LocalFaultLogitField
HardOrbitFaultLogitField
SoftFeatureOrbitFaultLogitField
```

Avoid generic names like `LocalField` or `SoftOrbitField` in Stage 1 because
they hide whether the field lives over physical locations, circuit operations,
or DEM faults.

Add these guardrail tests:

```python
def test_soft_features_not_orbit_constant(graph):
    phi = graph.residual_features
    orbit_ids = graph.orbit_ids

    valid = False
    for omega in orbit_ids.unique():
        idx = orbit_ids == omega
        if idx.sum() <= 1:
            continue
        centered = phi[idx] - phi[idx].mean(dim=0, keepdim=True)
        if torch.linalg.matrix_rank(centered).item() > 0:
            valid = True
            break

    assert valid, "soft residual features are orbit-constant; soft model collapses to hard orbit"
```

Also add a negative test that constructs \(\phi_j=c_\omega\) inside each orbit
and verifies that realized logits are constant inside every orbit.

###### Full SCOPE object contract

For the full SCOPE-Twin object, use:

| Object | Symbol | Meaning |
| --- | --- | --- |
| location set | \(\mathcal I_t\) | all locations where template \(t\) applies |
| location | \(i\in\mathcal I_t\) | physical/circuit location |
| orbit index | \(\omega\in\Omega_t\) | symmetry class for template \(t\) |
| orbit map | \(q_t(i)=\omega\) | maps location to orbit |
| orbit | \(\mathcal O_{\omega,t}\) | \(\{i:q_t(i)=\omega\}\) |
| local parameter | \(\theta_{i,t}(c)\) | channel/noise parameter at location \(i\), template \(t\) |
| orbit prototype | \(\vartheta_{\omega,t}(c)\) | shared parameter for orbit \(\omega\) |
| residual basis | \(U_{\omega,t}(c)\) | low-rank residual basis |
| residual coordinate | \(z_{i,t}(c)\) | location-level symmetry-breaking coordinate |
| physical channel | \(\mathcal E_{i,t}\) | CPTP/GKSL local noise channel |

The field equation is

$$
\boxed{
\theta_{i,t}(c)
=
\rho_t(g_{i\leftarrow\omega})
\vartheta_{\omega,t,\psi}(c)
+
U_{\omega,t,\psi}(c)z_{i,t,\psi}(c),
\qquad
\omega=q_t(i).
}
$$

If \(\theta_{i,t}\in\mathbb R^{d_t}\), then
\(\vartheta_{\omega,t,\psi}\in\mathbb R^{d_t}\),
\(U_{\omega,t,\psi}\in\mathbb R^{d_t\times r_t}\), and
\(z_{i,t,\psi}\in\mathbb R^{r_t}\).

###### Discovery notation contract

For SCOPE-Discovery, \(\mathsf A\) remains reserved for the DEM parity map. Use
\(S^{(t)}\) or \(\Pi^{(t)}\) for learned soft assignment:

$$
S^{(t)}\in[0,1]^{\lvert\mathcal I_t\rvert\times K_t},
\qquad
\sum_{k=1}^{K_t}S^{(t)}_{ik}=1.
$$

The Discovery field is

$$
\boxed{
\theta_{i,t}(c)
=
\sum_{k=1}^{K_t}
S^{(t)}_{ik,\psi}(c)
\left[
\vartheta_{k,t,\psi}(c)
+
U_{k,t,\psi}(c)z_{i,t,\psi}(c)
\right].
}
$$

Thus:

- \(\mathsf A\): DEM parity matrix.
- \(S\) or \(\Pi\): learned soft assignment.
- \(K_t\): number of discovered prototypes for template \(t\).

##### Definition: SCOPE-Twin

Let \(c=(H_{\mathrm{sched}},u,\kappa,\tau)\) be a QEC
circuit/control context, and let \(y=(s,m,\ldots)\in\mathcal Y\) be a
syndrome/logical observation.

A SCOPE-Twin is a structured probabilistic model

$$
p_\psi(y\mid c)
=
p_{\Theta_\psi(c)}(y\mid c),
$$

where the neural component is an amortized parameter-field map

$$
f_\psi:
c
\mapsto
\Theta_\psi(c)
\in
\Theta_{\Gamma,r}^{\mathrm{phys}}.
$$

The constrained physical family is

$$
\Theta_{\Gamma,r}^{\mathrm{phys}}
=
\Theta_{\mathrm{phys}}
\cap
\Theta_{\mathrm{cov}}
\cap
\Theta_{\mathrm{orb},r}.
$$

For each template \(t\), location \(i\in\mathcal I_t\), and orbit
\(\omega=q_t(i)\), SCOPE-Twin constructs

$$
\theta_{i,t}(c)
=
\rho_t(g_{i\leftarrow\omega})
\vartheta_{\omega,t,\psi}(c)
+
U_{\omega,t,\psi}(c)z_{i,t,\psi}(c),
\qquad
z_{i,t,\psi}(c)\in\mathbb R^{r_t}.
$$

The local channel is produced by a physical decoder:

$$
\mathcal E_{i,t}
=
\mathrm{PhysDec}_t(\theta_{i,t})
\in\mathrm{CPTP},
$$

or equivalently by a GKSL generator:

$$
\mathcal E_{i,t}
=
\exp(\Delta\tau_t\,\mathcal L_{\theta_{i,t}}).
$$

Let \(q\in\mathcal Q(c)\) index ideal operations in circuit order, and let
\(i(q)\) and \(t(q)\) denote the physical location and template associated with
operation \(q\). Define

$$
\mathcal E_q(c)
=
\mathrm{PhysDec}_{t(q)}
\left(\theta_{i(q),t(q)}(c)\right).
$$

Under a post-gate noise convention,

$$
\mathcal N_{q,\Theta}(c)
=
\mathcal E_q(c)
\circ
\mathcal G_q.
$$

The noisy circuit channel induced by context \(c\) and noise field
\(\Theta_\psi(c)\) is

$$
\mathcal C_{\Theta_\psi(c)}(c)
=
\prod_{q\in\mathcal Q(c)}^{\mathrm{circuit\ order}}
\left(
\mathcal E_q(c)
\circ
\mathcal G_q
\right).
$$

The final output distribution is

$$
p_\psi(y\mid c)
=
\operatorname{Tr}
\left[
M_y
\mathcal C_{\Theta_\psi(c)}(c)(\rho_0)
\right].
$$

Training:

$$
\min_\psi
-
\sum_{n=1}^{N}\log p_{\psi}(y_n\mid c_n)
+
\lambda_r R_{\mathrm{rank}}
+
\lambda_s R_{\mathrm{sparse}}
+
\lambda_g R_{\mathrm{gauge}}
+
\lambda_p R_{\mathrm{phys}}.
$$

If the physical decoder uses reparameterization to force CPTP/GKSL, then
\(R_{\mathrm{phys}}\) can be omitted.

Equivalently, the ML model learns a mapping from circuit/control context \(c\)
to a physically valid noise-model parameter field:

$$
f_{\psi}: c \mapsto \Theta_{\psi}(c) \in \Theta_{\Gamma,r}^{\mathrm{phys}}.
$$

The physical model family transforms the parameter field into an observation
distribution:

$$
\begin{aligned}
\mathcal F:\Theta^{\mathrm{phys}}_{\Gamma,r}\times\mathcal C
&\mapsto \Delta(\mathcal Y), \\
\mathcal F(\Theta,c)
&=p_{\Theta}(\cdot\mid c), \\
p_{\psi}(\cdot\mid c)
&= \mathcal F(\Theta_\psi(c),c), \\
p_{\psi}(y\mid c)
&= p_{\Theta_{\psi}(c)}(y\mid c) \\
&= \operatorname{Tr}
\left[
M_y
\mathcal C_{\Theta_{\psi}(c)}(c)(\rho_0)
\right].
\end{aligned}
$$

If there is latent drift, use \(n\) for the sequence index:

$$
\begin{aligned}
h_n &\sim p_{\psi}(h_n\mid h_{n-1},c_n), \\
\Theta_n &= f_{\psi}(c_n,h_n)\in\Theta_{\Gamma,r}^{\mathrm{phys}}, \\
p_\psi(y_n\mid c_n)
&=
\int
p_{\Theta_n}(y_n\mid c_n)
p_\psi(h_n\mid c_{\le n},y_{<n})
\,dh_n.
\end{aligned}
$$

Key objects:

- \(\Theta_\psi(c)\): predicted global noise-twin parameter field.
- \(c=(H_{\mathrm{sched}},u,\kappa,\tau)\): circuit/control context.
- \(y=(s,m,\ldots)\): syndrome/logical observation.
- \(\mathcal C_{\Theta}(c)\): full noisy QEC circuit channel or instrument.
- \(\rho_0\): initial state.
- \(\psi\): learnable parameters of SCOPE-Twin.
- \(M_y\): POVM/effect corresponding to observation \(y\).
- \(g_{i\leftarrow\omega}\): canonical group element mapping orbit
  representative \(i_\omega\) to location \(i\).

##### Preprocessing

###### Input

Raw QEC experiment/simulation description:

hardware layout, circuit schedule, gate types, measurements, rounds,
calibration metadata, timestamps, and related context.

###### Output

$$
c=(H_{\mathrm{sched}},u,\kappa,\tau).
$$

where:

- \(H_{\mathrm{sched}}\): colored hardware-schedule hypergraph.
- \(u\): control/calibration metadata.
- \(\kappa\): code/circuit descriptor.
- \(\tau\): optional time/drift context.

Training data:

$$
\mathcal D=\{(c_n,y_n)\}_{n=1}^{N},
\qquad
y_n=(s_n,m_n,\ldots).
$$

- \(s_n\): syndrome or detector-event trajectory.
- \(m_n\): logical observable flip or logical outcome.
- The tuple may also include analog readout, calibration probes, timestamps, or
  window IDs.

Preprocessing converts raw QEC data into a structured learning object.

##### Layer 1: Context-to-Orbit Field Encoder

###### Input

$$
c=(H_{\mathrm{sched}},u,\kappa,\tau).
$$

###### Output

Embeddings:

$$
\mathrm{Enc}_{\psi}(c)
=
\{e_{\omega,t}(c),\ e_{i,t}(c),\ e_{\mathrm{global}}(c)\}.
$$

where:

- \(e_{\omega,t}(c)\): orbit-level embedding for generating the orbit
  prototype \(\vartheta_{\omega,t,\psi}(c)\) and residual basis
  \(U_{\omega,t,\psi}(c)\).
- \(e_{i,t}(c)\): location-level embedding for generating the residual
  coordinate \(z_{i,t,\psi}(c)\).
- \(e_{\mathrm{global}}(c)\): circuit/global embedding for global drift,
  code distance, noise regime, temperature, or calibration window.

Possible implementation:

$$
\begin{aligned}
e_{i,t} &= \phi^{\mathrm{loc}}(x_{i,t},u,\kappa,\tau), \\
e_{\omega,t} &= \operatorname{Pool}_{i\in\mathcal O_{\omega,t}} e_{i,t}, \\
e_{\mathrm{global}} &= \operatorname{Pool}_{t,\omega} e_{\omega,t}.
\end{aligned}
$$

Later we may instantiate \(\phi^{\mathrm{loc}}\) using motif features, message
passing, attention, spectral encodings, or handcrafted descriptors. GNN,
Transformer, and diffusion encoders are possible choices.

##### Layer 2: Orbit-Parameter Field

###### Input

$$
\{e_{\omega,t}\},\ \{e_{i,t}\},\ e_{\mathrm{global}}.
$$

###### Output

For each template \(t\) and orbit \(\omega\), the model outputs residual bases:

$$
U_{\omega,t,\psi}(c)
=
h_t^{U}(e_{\omega,t},e_{\mathrm{global}}).
$$

For each template \(t\) and orbit \(\omega\), the model outputs an orbit
prototype:

$$
\vartheta_{\omega,t,\psi}(c)
=
h^{\vartheta}_{t}(e_{\omega,t},e_{\mathrm{global}}).
$$

For each location \(i\), the model outputs a low-rank residual coordinate:

$$
z_{i,t,\psi}(c)
=
h^{z}_{t}
\left(
e_{i,t},
e_{\omega,t},
e_{\mathrm{global}}
\right),
\qquad
\omega=q_t(i).
$$

Then

$$
\theta_{i,t}(c)
=
\rho_t(g_{i\leftarrow\omega})
\vartheta_{\omega,t,\psi}(c)
+
U_{\omega,t,\psi}(c)
z_{i,t,\psi}(c),
\qquad
\omega=q_t(i).
$$

This is a learned symmetry-broken parameter field, not an unconstrained neural
vector.

- \(\vartheta_{\omega,t}\): prototype parameters for orbit \(\omega\) and
  template \(t\).
- \(z_{i,t}\): residual coordinate vector for location \(i\), template \(t\).
- \(U_{\omega,t}\): low-rank residual basis for orbit \(\omega\), template
  \(t\).
- \(g_{i\leftarrow\omega}\): chosen group element that maps the canonical
  representative \(i_\omega\) of orbit \(\omega\) to location \(i\). If several
  such elements exist, a canonical representative is chosen as gauge fixing:

$$
g_{i\leftarrow\omega}\cdot i_{\omega}=i.
$$

The intermediate output is

$$
\Theta_\psi(c)=\{\theta_{i,t}(c)\}_{i,t},
$$

a physically valid, symmetry-compressed noise parameter field.

##### Layer 3: Physical Channel Decoder

Mapping \(\theta_{i,t}(c)\) to a local physical noise module:

$$
\mathcal E_{i,t}
=
\mathrm{PhysDec}_t(\theta_{i,t})
\in
\mathrm{CPTP}.
$$

In Choi form:

$$
J_{i,t}
=
\mathrm{TPNormalize}_t
\left[
\bigoplus_{\chi}
\left(X_{\chi,i,t}\otimes I_{d_{\chi}}\right)
\right],
\qquad
X_{\chi,i,t}\succeq 0.
$$

In Lindblad form:

$$
\mathcal L_{\theta}(\rho)
=
-i[H_{\theta},\rho]
+
\sum_{\mu,\nu}
C_{\mu\nu}^{(\theta)}
\left(
F_\mu\rho F_\nu^\dagger
-
\frac{1}{2}\{F_\nu^\dagger F_\mu,\rho\}
\right),
\qquad
C^{(\theta)}\succeq 0.
$$

Then

$$
\mathcal E_{i,t}
=
\exp(\Delta\tau_t\,\mathcal L_{\theta_{i,t}}).
$$

This layer restricts the ML output to a physically valid noise channel rather
than an arbitrary vector.

##### Layer 4: Observation Likelihood Layer

The final output is

$$
p_{\psi}(y\mid c)
=
\operatorname{Tr}
\left[
M_y
\mathcal C_{\Theta_{\psi}(c)}(c)(\rho_0)
\right],
$$

or

$$
p_{\psi}(y\mid c)=p_{\Theta_{\psi}(c)}(y\mid c).
$$

When code distance \(d\) increases, for example \(d=7,9\), we may use a
surrogate likelihood, but this definition remains the target object.

##### Core Problem: Six-Axis Physical Generation

SCOPE-Twin is aimed at the project-level physical generation problem. The
scientific ceiling is not set by saying that the output is CPTP/GKSL; it is set
by whether the physically constrained generation model can be validated
simultaneously along six axes:

1. **Generation fidelity**: held-out observations are explained by the generated
   noise model, under the target likelihood or a declared surrogate.
2. **Interpretability**: learned parameters and mechanisms map to auditable
   physical structure rather than opaque labels.
3. **Decoder utility**: the generated model improves decoder-facing tasks such
   as logical prediction, calibration, or threshold-relevant decisions.
4. **Cross-context generalization**: the same learned structure transfers across
   circuit contexts, schedules, rounds, distances, or related devices.
5. **Drift prediction**: latent or observed temporal variation is forecast before
   it is fitted post hoc.
6. **Identifiability**: the relevant quotient, mechanism, or parameter field is
   recovered up to declared symmetries, gauges, and observational limits.

CPTP/GKSL constraints are therefore necessary physical structure for this
contract, but they are not sufficient evidence for the SCOPE-Twin claim.

##### Operational Target: A Noise Simulator With Mechanism Knobs

The ideal endpoint is not merely a generator that produces samples similar to
held-out syndrome data. Under the target assumption that mechanisms, locations,
and strengths are recovered accurately, SCOPE-Twin should act as a controllable
QEC noise simulator with mechanism-level knobs.

In that setting, the recovered object can support questions such as:

- What happens to visible syndrome statistics and logical error if a specific
  mechanism is reduced, amplified, or removed?
- Which physical location, gate family, patch, basis, or drift component is the
  current bottleneck for logical performance?
- Which rare but decoder-relevant failure modes should be generated for
  augmentation or stress testing?
- Which calibration, layout, schedule, or probe change should be tried first
  because the model predicts the largest downstream improvement?
- How will a decoder or decoder prior behave under forecast drift rather than
  only under the distribution already observed?

This makes the intended artifact a noise-engineering tool rather than only a
distributional replay model. NLL, first-moment MAE, covariance Frobenius
distance, and two-sample tests remain useful fidelity checks, but they are not
the final use case. Their engineering value appears when the learned mechanism
field supports counterfactual interventions, decoder-facing utility tests,
drift forecasts, and action ranking.

This target should also discipline claim wording. A Google visible-surface model
that replays public syndrome-response statistics may be strong evidence for
distributional fidelity on that surface, but it is not by itself evidence that
Google physical mechanisms, locations, strengths, decoder utility, or drift
control have been recovered.

##### Current Implementation Bridge

The implemented repository currently covers three pieces of the SCOPE-Twin
evidence ladder.

1. **SCOPE-Static DEM/Bernoulli learning**

   The fixed-context DEM object learns fault logits over
   \(e_j\sim\mathrm{Bernoulli}(p_j)\) and \(y=\mathsf A e\bmod 2\). This tests
   compression, likelihood, and orbit/residual hypotheses over effective DEM
   faults, not a full physical parameter field.

2. **Controlled physical-mechanism catalog**

   The data-preparation teacher generates observations from declared catalog
   mechanisms whose local modules are implemented as unitary channels, Kraus
   channels, or stochastic readout maps embedded into valid measurement models.
   The emitted physicality/guardrail artifacts audit the generating modules.
   This validates controlled observation generation and no-leakage learner
   replay under a declared catalog protocol; it does not make the learner an
   arbitrary CPTP/GKSL parameter-field optimizer.

3. **Stage 3 visible-structure discovery and replay**

   Stage 3 removes direct mechanism-label supervision and learns assignments,
   prototypes, and visible replay models from frozen learner-visible features.
   For Google hardware data, the V2 public visible surface constructs
   \(x^{\mathrm{vis}}_\xi\) from public syndrome-response signatures:

   ```text
   raw__marginal
   raw__spatial_corr
   raw__temporal_corr
   raw__logical_coupling
   raw__stability
   meta__public_geometry
   ```

   The current Google Stage 3 closeout supports this bounded statement:

   ```text
   V2 raw syndrome-response replay beats global/mean-only,
   assignment-shuffle, feature-scramble, and public-stratified-null controls
   under no-oracle rules.
   ```

   This is evidence that public syndrome-response observations contain
   assignment-aligned latent structure. It is not yet a learned
   \(\Theta_\psi(c)\), not a physical channel decoder, and not a decoder-utility
   or drift-prediction result.

One discovery track is **S4 neural syndrome-response discovery** (in parallel,
and now prioritized, is the exact CPTP physical substrate of *Current
Reprioritization* below): learn a neural representation over
\(x^{\mathrm{vis}}_\xi\) with an auditable prototype or VQ bottleneck
\(\Pi_{\xi k}\), preserve the no-oracle and no-surrogate-ID controls from
Stage 3, and require raw-target-only plus block-normalized improvements over the
Stage 3 prototype mixture. S4 remains a visible-observation discovery stage
unless and until its latent variables are connected to a physical decoder
\(\mathrm{PhysDec}_t\) and circuit-level observation distribution
\(p_{\Theta}(y\mid c)\).

##### Current Reprioritization (2026-06): Exact CPTP Substrate First

The written ladder above reaches the physical channel decoder (Layer 3) and the
circuit-level observation likelihood (Layer 4) only after visible neural
discovery is stable. That ordering is reprioritized: because the operational
target is the interventional noise simulator with mechanism knobs, the **exact
CPTP physical substrate is being built now**, in high-precision small-scale
(\(\le\sim 10\) qubit) form, in parallel with rather than after the visible
discovery track.

Built and tested:

- \(\mathrm{PhysDec}_t\) in Kraus/Stinespring form: a CPTP-by-construction
  channel decoder \(\theta\mapsto\mathcal E\in\mathrm{CPTP}\) with differentiable
  recovery (`scope_static.primitives.diff_cptp_channel`). Because it is
  CPTP-by-construction, \(R_{\mathrm{phys}}\) is omitted.
- the Layer 4 forward map \(\mathcal C_\Theta(c)=\prod_q(\mathcal E_q\circ
  \mathcal G_q)\) and the exact likelihood \(p_\Theta(y\mid c)=\operatorname{Tr}
  [M_y\,\mathcal C_\Theta(c)(\rho_0)]\) for non-Clifford gates and non-Pauli
  channels (`scope_static.primitives.diff_circuit_sim`).

Not yet built and not yet claimed: the Layer 2 orbit-compression field
\(\theta_{i,t}=\rho_t(g_{i\leftarrow\omega})\vartheta_{\omega,t}+U_{\omega,t}
z_{i,t}\); the GKSL form of \(\mathrm{PhysDec}\); the multi-round mid-circuit
measurement instrument likelihood; the amortized context map
\(f_\psi:c\mapsto\Theta_\psi(c)\); and, critically, any counterfactual,
decoder-utility, drift, or cross-context result. This is a capability substrate,
not a validated twin: recovery is still only up to the observational alias
quotient, and interventional (knob) validity is unproven, since observational
equivalence need not be interventional equivalence.

##### Contributions

1. **New model class**

   SCOPE-Twin is a symmetry-compressed physical parameter-field model for QEC
   noise digital twins. Unlike black-box sequence models, SCOPE-Twin maps
   circuit/control contexts into a physically valid CPTP/GKSL noise family with
   orbit-shared prototypes and low-rank symmetry-breaking residuals.

2. **Constrained output-space learning**

   We formulate QEC noise learning as amortized learning into a constrained
   physical hypothesis class \(\Theta_{\Gamma,r}^{\mathrm{phys}}\), rather
   than direct prediction of detector events.

3. **Theory**

   We establish parameter compression, quotient identifiability, and
   soft-residual approximation results for symmetry-compressed physical inverse
   learning.

4. **Evaluation protocol**

   We propose a Pareto-front evaluation protocol organized around the six-axis
   physical generation bar: generation fidelity, interpretability, decoder
   utility, cross-context generalization, drift prediction, and identifiability.
   Held-out likelihood, sample efficiency, parameter count, quotient recovery,
   physical validity, and OOD transfer are supporting measurements for those
   axes.

5. **Empirical evidence**

   Across synthetic and QEC syndrome tasks, SCOPE-Twin should be evaluated for
   six-axis evidence against fully local, hard-sharing, black-box, and
   non-physical alternatives at matched parameter or compute budgets.

##### Experiments

All experiments must report splits, hyperparameters, minor experiment settings,
replication instructions, and the Stage-1 residual-feature diagnostics when the
experiment uses soft DEM-fault residuals.

###### Axis 1: Hypothesis Class ROI

1. Local: every location or DEM fault has independent parameters.
2. Hard orbit: only orbit prototypes.
3. Soft orbit: orbit prototype plus residual.
4. SCOPE: context-conditioned prototype plus residual.
5. SCOPE-no-phys: no physical channel decoder.
6. SCOPE-no-quotient: use a naive parameter loss.
7. Black-box generator: fit \(y\) directly under the same parameter budget.

###### Axis 2: Budget ROI

1. Fixed parameter budget:

$$
P_{\mathrm{model}}=\mathrm{constant}.
$$

Compare held-out NLL, TVD, and \(d_Q\).

2. Fixed sample budget:

$$
N_{\mathrm{shots}}=\mathrm{constant}.
$$

Compare time or epoch cost to the target NLL.

3. Fixed compute budget:

$$
\text{wall-clock or forward calls}=\mathrm{constant}.
$$

Compare NLL, runtime, and physical validity.

###### Axis 3: Symmetry-Breaking Sweep

Inject breaking strength:

$$
\epsilon_{\mathrm{break}}\in\{0,0.1,0.2,0.3,\ldots\}.
$$

Compare:

- When does hard sharing stop being effective?
- When does soft sharing become more effective?
- How large must \(r_t\) be?
- When does the residual overfit?

###### Axis 4: OOD Transfer

Train at \(d=3,5\), test at \(d=7\); or train on bulk-only circuits and test on
boundary/defect-heavy circuits.

Metrics:

- held-out NLL.
- TVD.
- detector-rate MAE.
- local correlation error.
- \(d_Q\).
- logical observable statistics.

If SCOPE-Twin wins on OOD, that is strong evidence for the model class.

##### Stage 1: First MVP, SCOPE-Static

Stage 1 uses fixed context

$$
c=c_0
$$

and learns DEM-fault logits

$$
\lambda_j=\operatorname{logit}(p_j),
\qquad
j=1,\ldots,M.
$$

The Stage-1 likelihood object is

$$
e_j\sim\mathrm{Bernoulli}(p_j),
\qquad
p_j=\sigma(\lambda_j),
\qquad
y=\mathsf A e\pmod 2.
$$

The MVP compares:

**Local**

$$
\lambda_j=\gamma_j.
$$

**Hard orbit**

$$
\lambda_j=\alpha_{\omega(j)}.
$$

**Soft feature orbit**

$$
\lambda_j
=
\alpha_{\omega(j)}
+
\beta_{\omega(j)}^\top\tilde\phi_j,
\qquad
\sum_{j\in\mathcal O_\omega}\tilde\phi_j=0.
$$

The MVP verifies:

- Does orbit sharing compress parameters?
- Does the soft residual improve held-out likelihood or calibration after the
  residual rank diagnostic passes?
- Is \(d_Q\) reasonable and stable?
- Does NLL/sample efficiency improve under matched budgets?

A soft-residual run is not valid unless at least one non-singleton orbit has
nonzero centered feature rank.

For the MVP04 rank sweep, the data-generating teacher is fixed at the selected
teacher residual rank, while fitted models sweep \(r\in\{0,1,2,5\}\). This keeps
the sampled observations and target logits comparable across ranks.

MVP05 introduces the scalable likelihood path. The global DEM parity map is
stored through sparse supports, and exact likelihood can be evaluated on local
windows \(W\) by replacing each fault mask with \(a_{j,W}=a_j|_W\). This keeps
the exact DP cost at \(2^{|W|}\) per window instead of \(2^B\). The first window
builders are detector singles, detector pairs, radius-1 detector-coordinate
neighborhoods, boundary/logical windows, template motifs, and known-orbit
windows.

##### Stage 2: Static SCOPE-Discovery

The implementation-facing Stage 2 static discovery MVP is specified in
`docs/SCOPE_STATIC_DISC.md`.

**Goal**:

> Can the model recover the quotient/orbit structure instead of receiving it by hand?

Still keep

$$
c=c_0.
$$

Use the same observation likelihood and physical decoder, but replace the fixed
orbit map

$$
\omega=q_t(i)
$$

with a learned soft assignment:

$$
S^{(t)}\in[0,1]^{\lvert\mathcal I_t\rvert\times K_t},
\qquad
\sum_{k=1}^{K_t}S_{ik}^{(t)}=1.
$$

Use:

$$
\theta_{i,t}
=
\sum_{k=1}^{K_t}
S_{ik}^{(t)}
\left[
\vartheta_{k,t}
+
U_{k,t}z_{i,t}
\right].
$$

This is the first SCOPE-Discovery prototype.

This stage answers:

> Can observations identify hidden sharing structure?

This should be tested first on synthetic teacher-generated data where the true
hidden partition is known. Then measure:

$$
\mathrm{ARI},\quad
\mathrm{NMI},\quad
d_Q,\quad
\text{held-out NLL},\quad
\text{TVD},\quad
\text{detector-rate MAE}.
$$

---


### Stage 3: Visible SCOPE-Discovery

Stage 3 is the current no-oracle visible-discovery layer. It does not yet learn
the full context-to-physical-field map \(f_\psi:c\mapsto\Theta_\psi(c)\).
Instead, it freezes a learner-visible surface and asks whether assignments and
prototypes can be recovered from observations alone.

For controlled catalog data, the visible unit may be a mechanism-condition or
probe-batch instance. For Google V2 data, the visible unit is a public
syndrome-response signature \(\xi\), and the learner sees
\(x^{\mathrm{vis}}_\xi\).

The visible assignment object is

$$
\Pi\in[0,1]^{|\mathcal U_{\mathrm{vis}}|\times K},
\qquad
\sum_{k=1}^{K}\Pi_{\xi k}=1.
$$

The Stage 3 visible replay model learns prototypes in visible-feature space:

$$
\hat x^{\mathrm{vis}}_\xi
=
g_\psi(\Pi_{\xi\cdot}),
$$

and is evaluated on heldout visible-generation quality plus falsification
controls. Evaluator-only labels, channels, PTMs, Kraus matrices, teacher IDs,
decoder correctness targets, and oracle prototypes are not learner inputs.

This stage answers:

$$
\boxed{
\text{Can visible observations support no-oracle latent assignment and replay?}
}
$$

### Stage 4: Neural Syndrome-Response Discovery

S4 is the next implementation step after the Stage 3 Google V2 closeout. It
keeps the visible-observation boundary, but replaces the shallow prototype
mixture with a neural representation and auditable bottleneck:

$$
x^{\mathrm{vis}}_\xi
\xrightarrow{\mathrm{Enc}_\psi}
h_\xi
\xrightarrow{\mathrm{prototype/VQ}}
\Pi_{\xi k}
\xrightarrow{\mathrm{Dec}_\psi}
\hat x^{\mathrm{vis}}_\xi.
$$

S4 must keep the same controls as Stage 3:

- no mechanism labels, channel objects, decoder correctness labels, or
  context/path/sample surrogate IDs in the learner path;
- raw-target-only and block-normalized scoring;
- assignment-shuffle and feature-scramble collapse checks;
- public-stratified-null comparison;
- seed/fold stability.

This stage answers:

$$
\boxed{
\text{Can a neural prototype bottleneck learn stronger public syndrome-response regimes?}
}
$$

### Later Stage: Amortized Physical SCOPE-Twin

The exact CPTP substrate (PhysDec plus fixed-context circuit likelihood) is being
built now; see *Current Reprioritization*. What remains genuinely later is the
**amortized context map** \(f_\psi:c\mapsto\Theta_\psi(c)\): only after the
visible neural discovery stage is stable should the project combine amortized
context-conditioning with latent quotient discovery into the amortized physical
field:

$$
f_\psi:c\mapsto\Theta_\psi(c).
$$

Start with known quotient/orbit structure before combining amortization with
latent quotient discovery:

$$
\theta_{i,t}(c)
=
\rho_t(g_{i\leftarrow \omega})
\vartheta_{\omega,t,\psi}(c)
+
U_{\omega,t,\psi}(c)z_{i,t,\psi}(c),
\qquad
\omega=q_t(i).
$$

This known-quotient amortized stage answers:

$$
\boxed{
\text{Can known-quotient SCOPE transfer across contexts?}
}
$$

The full amortized SCOPE-Discovery version then combines context-conditioned
parameter learning with latent quotient discovery:

$$
\Pi^{(t)}_\psi(c)
\in
[0,1]^{|\mathcal I_t|\times K_t},
\qquad
\sum_{k=1}^{K_t}\Pi^{(t)}_{ik,\psi}(c)=1.
$$

Then

$$
\theta_{i,t}(c)
=
\sum_{k=1}^{K_t}
\Pi^{(t)}_{ik,\psi}(c)
\left[
\vartheta_{k,t,\psi}(c)
+
U_{k,t,\psi}(c)z_{i,t,\psi}(c)
\right].
$$

This stage answers:

$$
\boxed{
\text{Can discovered quotient structure transfer across circuit, noise, and code contexts?}
}
$$

This is where OOD transfer should be tested, for example training at \(d=3,5\)
and testing at \(d=7\), or training on bulk-only circuits and testing on
boundary/defect-heavy circuits. Metrics include held-out likelihood, TVD,
detector-rate MAE, local-correlation error, \(d_Q\), logical observation
statistics, physical-validity audits, and decoder-facing utility.
