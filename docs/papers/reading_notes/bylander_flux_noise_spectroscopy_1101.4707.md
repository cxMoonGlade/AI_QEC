# Full-text review — Bylander et al., "Dynamical decoupling and noise spectroscopy with a superconducting flux qubit" (arXiv:1101.4707)

> **Provenance (2026-07-01): FULL-TEXT read (精读).** PDF `outputs/papers/1101.4707.pdf`
> -> txt `outputs/papers/1101.4707.txt` (PyMuPDF). This note is written for the bath-spectrum row used by
> `docs/twin_validation/error_budget_sourced_table.md`. Figures were not pixel-extracted; figure facts below
> are captions and stated fit parameters.

## Metadata [paper]
- Authors / affiliation: Jonas Bylander, Simon Gustavsson, Fei Yan, Fumiki Yoshihara, Khalil Harrabi,
  George Fitch, David G. Cory, Yasunobu Nakamura, Jaw-Shen Tsai, William D. Oliver; MIT / NEC / RIKEN-related
  flux-qubit collaboration.
- Venue / status: arXiv:1101.4707; Nature Physics 7, 565 (2011).
- Type: superconducting flux-qubit dynamical-decoupling experiment and noise spectroscopy.

## Executive summary [paper]
The paper uses Ramsey, Hahn echo, CPMG, UDD, driven dynamics, and relaxation measurements to infer noise
spectral densities for a persistent-current superconducting flux qubit. It reports `T1 = 12 us`, CPMG with up
to 200 pulses, a 50-fold improvement in coherence time, and `T2,CPMG = 23 us` approaching `2 T1` in the abstract
block (`txt:20-38`). For the simulator table, the load-bearing facts are the 1/f-like flux-noise shape and the
CPMG-extracted exponent `alpha = 0.9` over roughly 0.2-20 MHz.

## Method (deep) [paper]
The device is a persistent-current flux qubit, with flux bias near half a flux quantum and a two-level
Hamiltonian of the form

```text
H = -hbar/2 * [(epsilon + delta epsilon) sigma_x + (Delta + delta Delta) sigma_z]
```

as described in the device/model section (`txt:53-60`, `txt:743-760`). The paper defines noise spectra via
the autocorrelation Fourier transform `S_lambda(omega)` (`txt:92-98`) and uses dynamical-decoupling filter
functions to convert measured decay under pulse sequences into an estimated PSD (`txt:215-219`,
`txt:300-323`).

## The MECHANISM (for implementation) [paper -> ours]
- [paper] Longitudinal flux noise produces dephasing whose effect changes with flux bias; Ramsey and echo
  dephasing rates grow away from the sweet spot due to increased longitudinal sensitivity (`txt:238-249`).
- [paper] CPMG acts as a frequency-selective probe and reconstructs the flux-noise spectrum over the MHz band
  (`txt:300-323`, `txt:431-437`).
- [ours] The paper supports a 1/f^alpha bath-shape prior for a superconducting flux-noise dephasing channel.
  It does not provide a Google-transmon amplitude; any amplitude transfer into our coupled simulator must be
  declared as device-crossing calibration or share calibration.

## The OBSERVABLE / metric [paper]
The observable is coherence decay under pulse sequences. The metric inferred from that decay is a flux-noise
PSD, not a surface-code detector rate. For AI_QEC, this is therefore a bath-spectrum input candidate for
`J(omega) -> BCF -> fit`, not a direct error-budget number.

## Findings + numbers [paper]
| Quantity | Value | Source locus |
|---|---:|---|
| Baseline relaxation | `T1 = 12 +/- 1 us` | `txt:78-91` |
| Echo coherence at sweet spot | `T2,E = 23 us` | `txt:78-91` |
| Ramsey coherence | `T2* = 2.5 us` | `txt:78-91` |
| Rabi decay time | `T_R = 13 us` | `txt:78-91` |
| Low-frequency flux-noise amplitude from Ramsey/echo fit | `A_Phi = (1.7 uPhi0)^2`, assuming `alpha = 1` | `txt:238-249` |
| CPMG PSD band | approximately 0.2-20 MHz | `txt:431-437`, `txt:671-681` |
| CPMG PSD exponent | `alpha = 0.9` | `txt:431-437`, `txt:671-681` |
| CPMG amplitude line | `(0.8 uPhi0)^2` in the figure-caption fit | `txt:671-681` |

## Limitations [paper]
- This is a flux-qubit spectroscopy paper, not a Google Sycamore/Willow transmon calibration.
- The amplitude values are device-specific. They should not be copied as Google device parameters.
- The paper supports a spectral-shape bracket for flux-noise dephasing; it does not prove a universal exponent
  for all tunable transmons or all operating points.

## Relevance to AI_QEC [ours]
Use this paper as a cited source for a 1/f^alpha flux-noise spectral shape, especially `alpha ~= 0.9` in the
MHz CPMG band. Do not use its amplitude as a Google-device cited fact. In the composed simulator table, the
honest mapping is: shape sourced from Bylander; amplitude calibrated to the Google error-budget share.

## How to use / trust + open questions [ours]
Trust level: high for the paper's own flux-qubit PSD fits and coherence numbers. Open question: a
device-matched transmon flux-noise spectroscopy source would be needed to replace the current bracket with a
direct Google-device PSD input.
