"""SCOPE-Twin feasibility build (the B step of ADR 0006).

A controlled, exactly-simulable loop on the repetition-code substrate
(:mod:`scope_static.primitives.diff_rep_code`) that asks whether a label-free
CPTP twin yields trustworthy counterfactual ("knob") answers, validated against
controlled-teacher ground truth (ADR 0006 / 0007, project memory
``qec-digital-twin-goal``).

Modules build up the loop:
  * ``contexts`` (B2) -- the probe-richness ladder ``C_cal(r)`` and held-out eval;
  * ``calibration`` (B3) -- label-free fit via exact observation-NLL;
  * ``intervention`` (B4) -- channel-level ``do()`` + frozen decoder + ``B_*``;
  * ``validity`` (B5) -- the counterfactual-validity-vs-richness curve.
"""
