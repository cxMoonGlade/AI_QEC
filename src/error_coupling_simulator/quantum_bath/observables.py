from __future__ import annotations

r"""Multi-time record observables for the shared-bath dual-axis carrier.

Alphabet-agnostic statistics over a 3-round outcome distribution:
  * K_stat_joint  -- Milz/Budini Kolmogorov-consistency violation on the JOINT (X,Z) 4-ary record.
  * K_stat_binary -- the per-axis (binary) marginal K.
  * project_axis  -- marginalize a joint record dict onto the X (0) or Z (1) axis.
  * M_mem_stat    -- L1 distance to the Markov-1 factorization (a second memory statistic).
  * exact_cmi_bits-- exact conditional mutual information I(s1;s3|s2) in bits (beyond-Markov-1).
  * tv_distance / record_distance -- model-free record discrepancies (the discriminator metrics).

M_ALPHABET (the (sX,sZ) per-round alphabet) is CANONICALLY defined here; carrier imports it.

Extracted VERBATIM from:
  - K_stat_joint / K_stat_binary / project_axis / tv_distance / record_distance / M_ALPHABET
    <- outputs/twin_validation/notion3_relaxation_dualaxis_run.py
  - M_mem_stat  <- outputs/twin_validation/quantum_backaction_fairtest.py
  - exact_cmi_bits <- outputs/twin_validation/notion3_quantum_vs_classical_run.py

Teacher/evaluator-side; no physical ground truth (oracles are FORMAL).
"""

import math

M_ALPHABET = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (sX, sZ) per round


def K_stat_joint(P_all: dict, P_skip: dict, alphabet=M_ALPHABET) -> float:
    return float(sum(abs(sum(P_all[(m1, m2, m3)] for m2 in alphabet) - P_skip[(m1, m3)])
                     for m1 in alphabet for m3 in alphabet))


def project_axis(P: dict, which: int) -> dict:
    """Marginalize a joint record dict (keys = tuples of (sX,sZ)) onto axis `which` (0=X, 1=Z) -> binary keys."""
    out: dict = {}
    for key, v in P.items():
        nk = tuple(m[which] for m in key)
        out[nk] = out.get(nk, 0.0) + v
    return out


def K_stat_binary(P_all: dict, P_skip: dict) -> float:
    return float(sum(abs(sum(P_all[(s1, s2, s3)] for s2 in (0, 1)) - P_skip[(s1, s3)])
                     for s1 in (0, 1) for s3 in (0, 1)))


def M_mem_stat(P_all):
    def marg(idxs):
        d = {}
        for k, v in P_all.items():
            key = tuple(k[i] for i in idxs)
            d[key] = d.get(key, 0.0) + v
        return d
    P12, P23, P2 = marg([0, 1]), marg([1, 2]), marg([1])
    m = 0.0
    for (s1, s2, s3), p in P_all.items():
        denom = P2[(s2,)]
        m += abs(p - P12[(s1, s2)] * (P23[(s2, s3)] / denom if denom > 1e-15 else 0.0))
    return float(m)


def exact_cmi_bits(P_all: dict) -> float:
    """Exact I(s1;s3|s2) in BITS = sum P(s1,s2,s3) log2[ P(s1,s2,s3) P(s2) / (P(s1,s2) P(s2,s3)) ].

    Beyond-Markov-1 memory statistic (Cover & Thomas); the N->inf limit of pilotB _cmi_g2_order1 which reads
    I(m_r; m_{r-2} | m_{r-1}) on positions (r-2,r-1,r) == (s1,s2,s3) here.
    """
    def marg(idxs):
        d: dict = {}
        for k, v in P_all.items():
            key = tuple(k[i] for i in idxs)
            d[key] = d.get(key, 0.0) + v
        return d
    P12, P23, P2 = marg([0, 1]), marg([1, 2]), marg([1])
    c = 0.0
    for (s1, s2, s3), p in P_all.items():
        if p > 0.0:
            num = p * P2[(s2,)]
            den = P12[(s1, s2)] * P23[(s2, s3)]
            if den > 0.0 and num > 0.0:
                c += p * math.log2(num / den)
    return float(c)


def tv_distance(Pa1: dict, Pa2: dict) -> float:
    """Total-variation distance 0.5 * sum_k |Pa1[k]-Pa2[k]| over the shared 64-key joint P_all support."""
    return float(0.5 * sum(abs(Pa1[k] - Pa2[k]) for k in Pa1))


def record_distance(Pa1: dict, Pa2: dict) -> float:
    """max_k |Pa1[k] - Pa2[k]| over the shared 64-key joint P_all support (the model-free record discrepancy)."""
    return float(max(abs(Pa1[k] - Pa2[k]) for k in Pa1))
