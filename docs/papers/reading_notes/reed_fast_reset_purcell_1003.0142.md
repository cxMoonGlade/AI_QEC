# Full-text 精读 — Reed et al., "Fast Reset and Suppressing Spontaneous Emission of a Superconducting Qubit" (arXiv:1003.0142)

> **Provenance (2026-06-30): full-text 精读.** Source `outputs/papers/1003.0142.txt` (PyMuPDF, 4 pp,
> ~16.7k chars). Published **Appl. Phys. Lett. 96, 203110 (2010)**; journal DOI 10.1063/1.3435463;
> arXiv:1003.0142. Authors: M. D. Reed, B. R. Johnson, A. A. Houck, L. DiCarlo, J. M. Chow,
> D. I. Schuster, L. Frunzio, R. J. Schoelkopf (Yale). Citation verified vs the arXiv abstract page
> (the earlier repo citation "PRL 105, 173601 (2010)" was WRONG — that is a different paper).

Epistemic tags: **[paper]** = stated/measured in the paper; **[twin]** = our application.

## Why load-bearing [twin]
The **2nd DIRECT-physical device reference for M17 (reset_to_1_bias)** — a measured superconducting-
qubit **active-reset infidelity = residual excited-state population**. Together with McEwen
2102.06131 (Sycamore reset, residual P(|1>) = dominant reset error), M17 clears the ≥2-DIRECT-physical
gate with two note-backed device measurements. (The carrier object is `reset_to_state_kraus`; this
note grounds the *magnitude/physics* of the reset imperfection, not the channel algebra.)

## Metadata [paper]
- Device: superconducting transmon in 3D/2D cQED; reset via a **Purcell-enhanced cavity decay channel**
  (tune the qubit toward the cavity to exploit the Purcell rate; a "Purcell filter" protects the qubit
  otherwise).
- Result: **"We realize qubit reset with 99.9%"** fidelity [paper]; "fast qubit reset to 99% (99.9%)
  fidelity" [paper]; Purcell decay rate tunable by a factor of ~50.

## Load-bearing content [paper] (verbatim-anchored)
- "Spontaneous emission through a coupled cavity can be a significant decay channel for" a qubit; the
  reset exploits this on demand (tune into the Purcell-enhanced regime to dump the excitation).
- **Reset fidelity 99.9%** ⇒ residual excited-state population ≈ **10⁻³** after reset — the physical
  magnitude of the reset-imperfection bias M17 models (`p ≈ 10⁻³` active-reset end of the (b)-band).
- The reset is fast (cavity-limited) and returns the qubit to |0>; the *imperfection* (incomplete
  depopulation / re-excitation) is exactly the residual-|1> bias surrogate.

## How M17 uses it [twin]
- **DIRECT-physical magnitude band (b):** `p ≈ 10⁻³` (active reset, Reed) up to `~10⁻²` (imperfect/
  passive); swept, not frozen.
- Pairs with McEwen 2102.06131 (`mcewen_removing_leakage_correlated_2102.06131.md`): McEwen measures
  residual P(|1>) as the *dominant* reset error on a QEC processor (measure qubits reset each round);
  Reed measures the active-reset fidelity floor (99.9% → 10⁻³ residual). Two independent device
  measurements of reset imperfection ⇒ M17 ≥2-DIRECT-physical, both now note-backed.

## Limitations / scope [twin]
- Reed's reset is a *reset-to-0* fidelity; M17's "reset-to-1 bias" is the failure direction (ending in
  |1> instead of |0>). The shared physical content is the **residual excited-state population** =
  reset infidelity; the carrier's `reset_to_state_kraus(p, target=1)` is the operator surrogate
  (certified separately in `cert_m17_reset_bias.py`).
- Magnitude is (b)-band; the Purcell-cavity mechanism is device-specific (not all resets are Purcell).
