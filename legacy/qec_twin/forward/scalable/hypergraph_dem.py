"""Trainable hypergraph-DEM tensor-network likelihood for the scalable C1 bulk.

This is the production-shaped Layer-1 family for the post-Phase-3 fork:

* the base family is a detector-error-model hypergraph, parsed from a real
  ``stim.DetectorErrorModel``;
* Phase-3 Walsh residuals are support proposals only;
* every mechanism probability is represented by a trainable logit and learned
  by likelihood, never copied from a residual-to-probability adapter;
* arbitrary detector support arity is allowed, so promoted 3-body columns are
  native family members instead of Layer-2 leftovers.

The contraction is the standard dual/Walsh form of the DEM partition function.
For an observation vector ``y`` over ``B`` bits and independent mechanisms
``a`` with support ``S_a``:

    P_theta(y) = 2^-B sum_w (-1)^(w.y)
                 prod_a [(1-p_a) + p_a (-1)^(|w cap S_a| mod 2)].

Each mechanism is therefore a small parity tensor over the dual indices in its
support; a 3-body hyperedge is just a rank-3 tensor. ``opt_einsum`` supplies the
contraction path, while the tensor values are torch tensors, so gradients flow
to the logits.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import json
import math
from typing import Callable, Iterable, Sequence

import opt_einsum as oe
import torch

from qec_twin.numerics import NUMERICAL_ZERO


@dataclass(frozen=True)
class HypergraphMechanism:
    """One independent DEM-family mechanism.

    ``bits`` are indices in the declared observation vector. For syndrome-only
    hardware likelihoods this is detector indices ``0..num_detectors-1``. For a
    joint detector+logical law, logical observable ``m`` is indexed as
    ``num_detectors + m``.
    """

    bits: tuple[int, ...]
    initial_probability: float
    source: str
    trainable: bool = True

    def canonical(self) -> "HypergraphMechanism":
        return replace(self, bits=tuple(sorted(set(int(b) for b in self.bits))))


@dataclass(frozen=True)
class Phase3SupportSet:
    """Phase-3 support proposals, with no probability assignment."""

    basis: str
    scope: str
    gate: str
    pairs: tuple[tuple[int, int], ...]
    triples: tuple[tuple[int, int, int], ...]

    @property
    def supports(self) -> tuple[tuple[int, ...], ...]:
        return self.pairs + self.triples


@dataclass(frozen=True)
class TiltFeatureSet:
    """Low-dimensional visible-statistic features for observation-law tilts.

    ``matrix[b, k]`` is the contribution of observation bit ``b`` to feature
    ``k``. These are nuisance/exposure features of the observed detector field,
    not DEM mechanism supports.
    """

    matrix: torch.Tensor
    feature_names: tuple[str, ...]
    scheme: str

    def __post_init__(self) -> None:
        if self.matrix.ndim != 2:
            raise ValueError("TiltFeatureSet.matrix must have shape [num_bits, num_features]")
        if int(self.matrix.shape[1]) != len(self.feature_names):
            raise ValueError("feature_names must have one entry per matrix column")

    @property
    def num_bits(self) -> int:
        return int(self.matrix.shape[0])

    @property
    def num_features(self) -> int:
        return int(self.matrix.shape[1])

    def to(
        self,
        *,
        dtype: torch.dtype,
        device: str | torch.device,
    ) -> "TiltFeatureSet":
        return TiltFeatureSet(
            matrix=self.matrix.to(dtype=dtype, device=device),
            feature_names=self.feature_names,
            scheme=self.scheme,
        )


def _xor_combine_probabilities(probabilities: Sequence[float]) -> float:
    prod = 1.0
    for p in probabilities:
        prod *= 1.0 - 2.0 * float(p)
    return 0.5 * (1.0 - prod)


def _prob_to_logit(p: float, p_max: float) -> float:
    q = min(max(float(p) / float(p_max), NUMERICAL_ZERO), 1.0 - NUMERICAL_ZERO)
    return math.log(q / (1.0 - q))


def _target_bits_from_stim(
    targets: Iterable[object],
    *,
    num_detectors: int,
    include_observables: bool,
) -> tuple[int, ...]:
    bits: list[int] = []
    for target in targets:
        if target.is_separator():
            continue
        if target.is_relative_detector_id():
            bits.append(int(target.val))
        elif include_observables and target.is_logical_observable_id():
            bits.append(num_detectors + int(target.val))
    out: list[int] = []
    for bit in sorted(bits):
        if bit not in out:
            out.append(bit)
    return tuple(out)


def _ordered_unique(values: Sequence[str]) -> tuple[str, ...]:
    out: list[str] = []
    for value in values:
        if value not in out:
            out.append(value)
    return tuple(out)


def global_tilt_features(
    num_bits: int,
    *,
    dtype: torch.dtype = torch.float64,
    device: str | torch.device = "cpu",
) -> TiltFeatureSet:
    """Single exposure feature: total detector-event weight."""

    if int(num_bits) <= 0:
        raise ValueError("num_bits must be positive")
    return TiltFeatureSet(
        matrix=torch.ones((int(num_bits), 1), dtype=dtype, device=device),
        feature_names=("detector_weight",),
        scheme="global",
    )


def one_hot_tilt_features(
    labels_by_bit: Sequence[str],
    *,
    scheme: str,
    dtype: torch.dtype = torch.float64,
    device: str | torch.device = "cpu",
) -> TiltFeatureSet:
    """Build one linear visible feature per declared detector label."""

    labels = tuple(str(label) for label in labels_by_bit)
    if not labels:
        raise ValueError("labels_by_bit must be non-empty")
    feature_names = _ordered_unique(labels)
    feature_index = {name: idx for idx, name in enumerate(feature_names)}
    matrix = torch.zeros((len(labels), len(feature_names)), dtype=dtype, device=device)
    for bit, label in enumerate(labels):
        matrix[bit, feature_index[label]] = 1.0
    return TiltFeatureSet(matrix=matrix, feature_names=feature_names, scheme=str(scheme))


def _detector_coordinates(dem: object) -> tuple[tuple[float, ...], ...]:
    coords_by_detector = dem.get_detector_coordinates()
    out: list[tuple[float, ...]] = []
    for detector in range(int(dem.num_detectors)):
        coords = coords_by_detector.get(detector, ())
        out.append(tuple(float(x) for x in coords))
    return tuple(out)


def _coord_value(coords: tuple[float, ...], index: int) -> float:
    return float(coords[index]) if len(coords) > index else 0.0


def detector_coordinate_tilt_features(
    dem: object,
    *,
    scheme: str = "boundary_round",
    dtype: torch.dtype = torch.float64,
    device: str | torch.device = "cpu",
) -> TiltFeatureSet:
    """Declared d=3 surface-code exposure features from detector coordinates.

    Supported schemes:

    ``global``
        total detector-event weight.
    ``boundary_bulk``
        separate weights for boundary and bulk detectors.
    ``round_region``
        separate weights for first, interior, and final detector-time layers.
    ``boundary_round``
        the cross of boundary/bulk with the round-region labels.
    """

    num_detectors = int(dem.num_detectors)
    if scheme == "global":
        return global_tilt_features(num_detectors, dtype=dtype, device=device)
    coords = _detector_coordinates(dem)
    xs = [_coord_value(c, 0) for c in coords]
    ys = [_coord_value(c, 1) for c in coords]
    ts = [_coord_value(c, 2) for c in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_t, max_t = min(ts), max(ts)

    labels: list[str] = []
    for x, y, t in zip(xs, ys, ts):
        boundary = x == min_x or x == max_x or y == min_y or y == max_y
        boundary_label = "boundary" if boundary else "bulk"
        if min_t == max_t:
            round_label = "bulk_round"
        elif t == min_t:
            round_label = "prep"
        elif t == max_t:
            round_label = "final"
        else:
            round_label = "bulk_round"
        if scheme == "boundary_bulk":
            labels.append(boundary_label)
        elif scheme == "round_region":
            labels.append(round_label)
        elif scheme == "boundary_round":
            labels.append(f"{boundary_label}:{round_label}")
        else:
            raise ValueError(
                "unknown tilt feature scheme "
                f"{scheme!r}; expected global, boundary_bulk, round_region, or boundary_round"
            )
    return one_hot_tilt_features(labels, scheme=scheme, dtype=dtype, device=device)


def phase3_supports_from_json(
    phase3_path: Path | str,
    *,
    basis: str,
    scope: str = "cross_window_r13",
    gate: str = "promotable_beyond_si1000_corr",
    include_pairs: bool = True,
    include_triples: bool = True,
) -> Phase3SupportSet:
    """Load Phase-3 promoted supports from the real residual-spectrum artifact.

    This loader intentionally returns supports only. It does not read residual
    magnitudes and does not assign probabilities.
    """

    payload = json.loads(Path(phase3_path).read_text())
    records = payload["scopes"][str(basis)][str(scope)]["records"]
    pairs: list[tuple[int, int]] = []
    triples: list[tuple[int, int, int]] = []
    for rec in records:
        if not bool(rec.get(gate, False)):
            continue
        support = tuple(sorted(int(x) for x in rec["S"]))
        order = int(rec["order"])
        if order == 2 and include_pairs:
            pairs.append((support[0], support[1]))
        elif order == 3 and include_triples and bool(rec.get("genuine_hyperedge_3body", False)):
            triples.append((support[0], support[1], support[2]))
    return Phase3SupportSet(
        basis=str(basis),
        scope=str(scope),
        gate=str(gate),
        pairs=tuple(sorted(set(pairs))),
        triples=tuple(sorted(set(triples))),
    )


class HypergraphDemTNLikelihood:
    """Differentiable TN likelihood over a declared hypergraph DEM family."""

    def __init__(
        self,
        *,
        num_bits: int,
        mechanisms: Sequence[HypergraphMechanism],
        p_max: float = 0.5 - NUMERICAL_ZERO,
        dtype: torch.dtype = torch.float64,
        device: str | torch.device = "cpu",
        optimize: str = "auto",
    ) -> None:
        if int(num_bits) <= 0:
            raise ValueError("num_bits must be positive")
        self.num_bits = int(num_bits)
        self.p_max = float(p_max)
        self.dtype = dtype
        self.device = torch.device(device)
        self.mechanisms = self._canonicalize_mechanisms(mechanisms)
        if not self.mechanisms:
            raise ValueError("at least one non-empty mechanism is required")
        self._supports = tuple(m.bits for m in self.mechanisms)
        self._parity_masks = tuple(
            self._parity_mask(len(bits)).to(device=self.device)
            for bits in self._supports
        )
        init = [
            _prob_to_logit(m.initial_probability, self.p_max)
            for m in self.mechanisms
        ]
        self.logits = torch.tensor(init, dtype=self.dtype, device=self.device, requires_grad=True)
        self.initial_logits = self.logits.detach().clone()
        self._compile_path(optimize=optimize)

    @staticmethod
    def _parity_mask(rank: int) -> torch.Tensor:
        shape = (2,) * int(rank)
        if rank == 0:
            return torch.ones((), dtype=torch.bool)
        grids = torch.meshgrid(
            [torch.arange(2, dtype=torch.int64) for _ in range(rank)],
            indexing="ij",
        )
        parity = torch.zeros(shape, dtype=torch.int64)
        for grid in grids:
            parity = parity ^ grid
        return parity.to(dtype=torch.bool)

    def _canonicalize_mechanisms(
        self, mechanisms: Sequence[HypergraphMechanism]
    ) -> tuple[HypergraphMechanism, ...]:
        grouped: dict[tuple[int, ...], list[HypergraphMechanism]] = {}
        for mechanism in mechanisms:
            m = mechanism.canonical()
            if not m.bits:
                continue
            if any(bit < 0 or bit >= self.num_bits for bit in m.bits):
                raise ValueError(f"mechanism support {m.bits} outside num_bits={self.num_bits}")
            grouped.setdefault(m.bits, []).append(m)

        out: list[HypergraphMechanism] = []
        for bits, group in sorted(grouped.items()):
            p = _xor_combine_probabilities([g.initial_probability for g in group])
            trainable = any(g.trainable for g in group)
            sources = "+".join(sorted(set(g.source for g in group)))
            out.append(
                HypergraphMechanism(
                    bits=bits,
                    initial_probability=min(max(p, NUMERICAL_ZERO), self.p_max),
                    source=sources,
                    trainable=trainable,
                )
            )
        return tuple(out)

    @classmethod
    def from_stim_dem(
        cls,
        dem: object,
        *,
        include_observables: bool = False,
        promoted_supports: Iterable[Sequence[int]] = (),
        promoted_init_probability: float = 1e-4,
        dtype: torch.dtype = torch.float64,
        device: str | torch.device = "cpu",
        optimize: str = "auto",
    ) -> "HypergraphDemTNLikelihood":
        """Build a trainable family from a real Stim detector error model.

        ``promoted_supports`` are appended as additional trainable supports with
        a small initialization. They are support proposals only; the fit owns
        their final logits.
        """

        num_detectors = int(dem.num_detectors)
        num_observables = int(dem.num_observables) if include_observables else 0
        num_bits = num_detectors + num_observables
        mechanisms: list[HypergraphMechanism] = []
        for instruction in dem.flattened():
            if instruction.type != "error":
                continue
            bits = _target_bits_from_stim(
                instruction.targets_copy(),
                num_detectors=num_detectors,
                include_observables=include_observables,
            )
            if not bits:
                continue
            mechanisms.append(
                HypergraphMechanism(
                    bits=bits,
                    initial_probability=float(instruction.args_copy()[0]),
                    source="stim_dem",
                    trainable=True,
                )
            )
        for support in promoted_supports:
            mechanisms.append(
                HypergraphMechanism(
                    bits=tuple(int(x) for x in support),
                    initial_probability=float(promoted_init_probability),
                    source="phase3_support_proposal",
                    trainable=True,
                )
            )
        return cls(
            num_bits=num_bits,
            mechanisms=mechanisms,
            dtype=dtype,
            device=device,
            optimize=optimize,
        )

    def with_promoted_supports(
        self,
        supports: Iterable[Sequence[int]],
        *,
        init_probability: float = 1e-4,
        optimize: str = "auto",
    ) -> "HypergraphDemTNLikelihood":
        mechanisms = list(self.mechanisms)
        for support in supports:
            mechanisms.append(
                HypergraphMechanism(
                    bits=tuple(int(x) for x in support),
                    initial_probability=float(init_probability),
                    source="phase3_support_proposal",
                    trainable=True,
                )
            )
        return HypergraphDemTNLikelihood(
            num_bits=self.num_bits,
            mechanisms=mechanisms,
            p_max=self.p_max,
            dtype=self.dtype,
            device=self.device,
            optimize=optimize,
        )

    def probabilities(self) -> torch.Tensor:
        return self.p_max * torch.sigmoid(self.logits)

    def probabilities_from_logits(self, logits: torch.Tensor) -> torch.Tensor:
        return self.p_max * torch.sigmoid(logits.to(device=self.device, dtype=self.dtype))

    def _compile_path(self, *, optimize: str) -> None:
        dummy: list[object] = []
        for bits in self._supports:
            dummy.append(torch.ones((2,) * len(bits), dtype=self.dtype, device=self.device))
            dummy.append(list(bits))
        for bit in range(self.num_bits):
            dummy.append(torch.ones(2, dtype=self.dtype, device=self.device))
            dummy.append([bit])
        dummy.append([])
        self._path, info = oe.contract_path(*dummy, optimize=optimize)
        self.path_summary = {
            "num_bits": self.num_bits,
            "num_mechanisms": len(self.mechanisms),
            "max_mechanism_arity": max(len(bits) for bits in self._supports),
            "max_intermediate": int(max(info.size_list)) if info.size_list else 1,
            "opt_cost": float(info.opt_cost),
        }

    def _mechanism_tensor(self, index: int, probabilities: torch.Tensor) -> torch.Tensor:
        p = probabilities[index]
        odd = 1.0 - 2.0 * p
        return torch.where(
            self._parity_masks[index],
            odd.expand(self._parity_masks[index].shape),
            torch.ones(self._parity_masks[index].shape, dtype=self.dtype, device=self.device),
        )

    def _raw_contraction_with_vectors(
        self,
        dual_vectors: Sequence[torch.Tensor],
        probabilities: torch.Tensor,
    ) -> torch.Tensor:
        if len(dual_vectors) != self.num_bits:
            raise ValueError(f"dual_vectors must have length {self.num_bits}")
        operands: list[object] = []
        for idx, bits in enumerate(self._supports):
            operands.append(self._mechanism_tensor(idx, probabilities))
            operands.append(list(bits))
        for bit in range(self.num_bits):
            vector = torch.as_tensor(dual_vectors[bit], dtype=self.dtype, device=self.device)
            if tuple(vector.shape) != (2,):
                raise ValueError("each dual vector must have shape [2]")
            operands.append(vector)
            operands.append([bit])
        operands.append([])
        return oe.contract(*operands, optimize=self._path)

    def _raw_contraction(self, observation: torch.Tensor, probabilities: torch.Tensor) -> torch.Tensor:
        y = torch.as_tensor(observation, dtype=torch.bool, device=self.device).flatten()
        if int(y.numel()) != self.num_bits:
            raise ValueError(f"observation width {int(y.numel())} != num_bits={self.num_bits}")
        vectors = []
        for bit in range(self.num_bits):
            sign = -1.0 if bool(y[bit]) else 1.0
            vectors.append(torch.tensor([1.0, sign], dtype=self.dtype, device=self.device))
        return self._raw_contraction_with_vectors(vectors, probabilities)

    def log_prob(self, observations: torch.Tensor, *, logits: torch.Tensor | None = None) -> torch.Tensor:
        """Return log ``P_theta(y)`` for one or more observations."""

        obs = torch.as_tensor(observations, dtype=torch.bool, device=self.device)
        if obs.ndim == 1:
            obs = obs.unsqueeze(0)
        if obs.ndim != 2 or int(obs.shape[1]) != self.num_bits:
            raise ValueError(f"observations must have shape [N, {self.num_bits}]")
        probabilities = self.probabilities() if logits is None else self.probabilities_from_logits(logits)
        log_norm = self.num_bits * math.log(2.0)
        vals = []
        for row in obs:
            raw = self._raw_contraction(row, probabilities)
            vals.append(torch.log(raw.clamp_min(NUMERICAL_ZERO)) - log_norm)
        return torch.stack(vals)

    def negative_log_likelihood(self, observations: torch.Tensor, *, logits: torch.Tensor | None = None) -> torch.Tensor:
        return -self.log_prob(observations, logits=logits).mean()

    def audit_dict(self) -> dict[str, object]:
        sources: dict[str, int] = {}
        arities: dict[int, int] = {}
        for mechanism in self.mechanisms:
            sources[mechanism.source] = sources.get(mechanism.source, 0) + 1
            arity = len(mechanism.bits)
            arities[arity] = arities.get(arity, 0) + 1
        return {
            **self.path_summary,
            "mechanism_sources": sources,
            "arity_histogram": arities,
            "phase3_supports_are_probabilities": False,
            "probability_owner": "Layer-1 TN likelihood fit",
        }


def fit_hypergraph_dem_tn(
    family: HypergraphDemTNLikelihood,
    observations: torch.Tensor,
    *,
    steps: int = 50,
    lr: float = 0.05,
    l2_to_initial: float = 0.0,
) -> dict[str, object]:
    """Fit mechanism logits by differentiable TN syndrome NLL.

    This is intentionally generic and makes no decoder-utility claim. Use it on
    real d=3 surface-code observations or a declared train split; Phase-3
    residual magnitudes do not enter.
    """

    obs = torch.as_tensor(observations, dtype=torch.bool, device=family.device)
    initial = family.logits.detach().clone()
    opt = torch.optim.Adam([family.logits], lr=float(lr))
    history: list[float] = []
    for _ in range(int(steps)):
        opt.zero_grad(set_to_none=True)
        loss = family.negative_log_likelihood(obs)
        if l2_to_initial:
            loss = loss + float(l2_to_initial) * ((family.logits - initial) ** 2).mean()
        loss.backward()
        opt.step()
        history.append(float(loss.detach().cpu()))
    return {
        "steps": int(steps),
        "final_nll": history[-1] if history else float(family.negative_log_likelihood(obs).detach().cpu()),
        "history": history,
        "audit": family.audit_dict(),
    }


def _default_group_key(mechanism: HypergraphMechanism) -> str:
    if "phase3_support_proposal" in mechanism.source:
        return f"phase3_order{len(mechanism.bits)}"
    return "stim_dem"


def _source_label(mechanism: HypergraphMechanism) -> str:
    return "phase3" if "phase3_support_proposal" in mechanism.source else "stim_dem"


def normalization_group_labels(
    mechanisms: Sequence[HypergraphMechanism],
    *,
    scheme: str = "default",
) -> tuple[str, ...]:
    """Declared low-dimensional normalization partitions.

    Schemes are intentionally coarse; they are normalization stages, not the
    final per-mechanism fit.

    ``global``
        one offset for the entire DEM.
    ``arity``
        one offset per support arity.
    ``source``
        ``stim_dem`` vs Phase-3-proposed supports.
    ``source_order``
        source plus arity, e.g. ``stim_dem_order2`` and ``phase3_order3``.
    ``default``
        the current conservative default: one ``stim_dem`` offset plus
        Phase-3 offsets split by order.
    """

    scheme = str(scheme)
    labels: list[str] = []
    for mechanism in mechanisms:
        arity = len(mechanism.bits)
        source = _source_label(mechanism)
        if scheme == "global":
            labels.append("all")
        elif scheme == "arity":
            labels.append(f"order{arity}")
        elif scheme == "source":
            labels.append(source)
        elif scheme == "source_order":
            labels.append(f"{source}_order{arity}")
        elif scheme == "default":
            labels.append(_default_group_key(mechanism))
        else:
            raise ValueError(
                "unknown normalization scheme "
                f"{scheme!r}; expected global, arity, source, source_order, or default"
            )
    return tuple(labels)


class GroupedLogitNormalizer:
    """Low-dimensional normalization layer before per-mechanism fitting.

    The hypergraph support family is unchanged. The frozen initial logit vector
    receives only a small number of shared offsets:

        lambda_j = lambda_j^0 + group_offset[g(j)].

    This is the intended first optimizer stage for real d=3 data: calibrate
    global / source / arity scale before allowing high-variance individual DEM
    logits to move.
    """

    def __init__(
        self,
        family: HypergraphDemTNLikelihood,
        *,
        scheme: str = "default",
        group_labels: Sequence[str] | None = None,
        group_keys: Sequence[str] | None = None,
        group_key_fn: Callable[[HypergraphMechanism], str] | None = None,
    ) -> None:
        self.family = family
        if group_labels is not None and group_key_fn is not None:
            raise ValueError("pass group_labels or group_key_fn, not both")
        if group_labels is not None:
            labels = tuple(str(x) for x in group_labels)
            if len(labels) != len(family.mechanisms):
                raise ValueError("group_labels must have one entry per mechanism")
        elif group_key_fn is not None:
            labels = tuple(str(group_key_fn(m)) for m in family.mechanisms)
        else:
            labels = normalization_group_labels(family.mechanisms, scheme=scheme)
        if group_keys is None:
            group_keys = tuple(sorted(set(labels)))
        self.group_keys = tuple(str(k) for k in group_keys)
        group_index = {key: i for i, key in enumerate(self.group_keys)}
        design = torch.zeros(
            (len(family.mechanisms), len(self.group_keys)),
            dtype=family.dtype,
            device=family.device,
        )
        for row, _mechanism in enumerate(family.mechanisms):
            label = labels[row]
            if label not in group_index:
                raise ValueError(f"group label {label!r} missing from group_keys")
            design[row, group_index[label]] = 1.0
        self.labels = tuple(labels)
        self.scheme = str(scheme)
        self.design = design
        self.offsets = torch.zeros(
            (len(self.group_keys),),
            dtype=family.dtype,
            device=family.device,
            requires_grad=True,
        )

    def logits(self) -> torch.Tensor:
        return self.family.initial_logits + self.design @ self.offsets

    def negative_log_likelihood(self, observations: torch.Tensor) -> torch.Tensor:
        return self.family.negative_log_likelihood(observations, logits=self.logits())

    def audit_dict(self) -> dict[str, object]:
        counts: dict[str, int] = {}
        for label in self.labels:
            counts[label] = counts.get(label, 0) + 1
        return {
            "normalization": "grouped_logit_offsets",
            "scheme": self.scheme,
            "group_keys": list(self.group_keys),
            "group_counts": counts,
            "num_trainable_offsets": len(self.group_keys),
            "num_underlying_mechanisms": len(self.family.mechanisms),
        }


def fit_grouped_logit_normalizer(
    normalizer: GroupedLogitNormalizer,
    observations: torch.Tensor,
    *,
    steps: int = 50,
    lr: float = 0.05,
    l2_offsets: float = 0.0,
) -> dict[str, object]:
    """Fit only grouped logit offsets, not individual mechanism logits."""

    obs = torch.as_tensor(observations, dtype=torch.bool, device=normalizer.family.device)
    opt = torch.optim.Adam([normalizer.offsets], lr=float(lr))
    history: list[float] = []
    for _ in range(int(steps)):
        opt.zero_grad(set_to_none=True)
        loss = normalizer.negative_log_likelihood(obs)
        if l2_offsets:
            loss = loss + float(l2_offsets) * (normalizer.offsets ** 2).mean()
        loss.backward()
        opt.step()
        history.append(float(loss.detach().cpu()))
    return {
        "steps": int(steps),
        "final_nll": history[-1] if history else float(normalizer.negative_log_likelihood(obs).detach().cpu()),
        "history": history,
        "offsets": {k: float(v) for k, v in zip(normalizer.group_keys, normalizer.offsets.detach().cpu())},
        "audit": normalizer.audit_dict(),
    }


class ObservationTiltNormalizer:
    """Minimum-discrimination normalization of the visible observation law.

    This layer keeps the DEM/TN mechanism law fixed as ``P_0`` and fits only a
    low-dimensional exponential tilt over declared visible features:

        P_eta(y) = P_0(y) exp(eta.T T(y) - A(eta)).

    ``A(eta)`` is contracted exactly with the same dual/Walsh TN as the base
    likelihood. This makes the layer a proper normalized likelihood family,
    while keeping pair/triple mechanism supports out of the normalization stage.
    """

    def __init__(
        self,
        base: HypergraphDemTNLikelihood,
        features: TiltFeatureSet,
        *,
        base_logits: torch.Tensor | None = None,
    ) -> None:
        if features.num_bits != base.num_bits:
            raise ValueError(
                f"feature width {features.num_bits} != base.num_bits={base.num_bits}"
            )
        self.base = base
        self.features = features.to(dtype=base.dtype, device=base.device)
        if base_logits is None:
            base_logits = base.logits.detach().clone()
        self.base_logits = base_logits.detach().clone().to(dtype=base.dtype, device=base.device)
        if tuple(self.base_logits.shape) != tuple(base.logits.shape):
            raise ValueError("base_logits must have one entry per base mechanism")
        self.eta = torch.zeros(
            (self.features.num_features,),
            dtype=base.dtype,
            device=base.device,
            requires_grad=True,
        )

    def _as_observation_matrix(self, observations: torch.Tensor) -> torch.Tensor:
        obs = torch.as_tensor(observations, dtype=torch.bool, device=self.base.device)
        if obs.ndim == 1:
            obs = obs.unsqueeze(0)
        if obs.ndim != 2 or int(obs.shape[1]) != self.base.num_bits:
            raise ValueError(f"observations must have shape [N, {self.base.num_bits}]")
        return obs

    def feature_values(self, observations: torch.Tensor) -> torch.Tensor:
        obs = self._as_observation_matrix(observations)
        return obs.to(dtype=self.base.dtype) @ self.features.matrix

    def log_partition_for_eta(self, eta: torch.Tensor) -> torch.Tensor:
        alpha = self.features.matrix @ eta.to(dtype=self.base.dtype, device=self.base.device)
        weights = torch.exp(alpha)
        dual_vectors = [
            torch.stack((1.0 + weights[bit], 1.0 - weights[bit]))
            for bit in range(self.base.num_bits)
        ]
        probabilities = self.base.probabilities_from_logits(self.base_logits)
        raw = self.base._raw_contraction_with_vectors(dual_vectors, probabilities)
        return torch.log(raw.clamp_min(NUMERICAL_ZERO)) - self.base.num_bits * math.log(2.0)

    def log_partition(self) -> torch.Tensor:
        return self.log_partition_for_eta(self.eta)

    def log_prob(self, observations: torch.Tensor) -> torch.Tensor:
        obs = self._as_observation_matrix(observations)
        base_log_prob = self.base.log_prob(obs, logits=self.base_logits)
        tilt = self.feature_values(obs) @ self.eta
        return base_log_prob + tilt - self.log_partition()

    def negative_log_likelihood(self, observations: torch.Tensor) -> torch.Tensor:
        return -self.log_prob(observations).mean()

    def tilt_objective(self, observations: torch.Tensor) -> torch.Tensor:
        """Eta-dependent NLL part: ``A(eta) - eta.T mean[T(Y)]``.

        The frozen base term ``-mean log P_0(Y)`` is constant in ``eta``. Using
        this objective is exactly equivalent for fitting the normalization
        layer and avoids one TN contraction per shot.
        """

        mean_features = self.feature_values(observations).mean(dim=0)
        return self.log_partition() - mean_features @ self.eta

    def audit_dict(self) -> dict[str, object]:
        return {
            "normalization": "observation_exponential_tilt",
            "scheme": self.features.scheme,
            "feature_names": list(self.features.feature_names),
            "num_trainable_tilts": self.features.num_features,
            "num_observation_bits": self.base.num_bits,
            "num_underlying_mechanisms": len(self.base.mechanisms),
            "base_probability_owner": "frozen Layer-1 TN law",
            "pair_hyperedge_features": False,
        }


def fit_observation_tilt_normalizer(
    normalizer: ObservationTiltNormalizer,
    observations: torch.Tensor,
    *,
    steps: int = 50,
    lr: float = 0.05,
    l2_eta: float = 0.0,
) -> dict[str, object]:
    """Fit only visible-law tilt parameters ``eta``."""

    obs = torch.as_tensor(observations, dtype=torch.bool, device=normalizer.base.device)
    opt = torch.optim.Adam([normalizer.eta], lr=float(lr))
    history: list[float] = []
    for _ in range(int(steps)):
        opt.zero_grad(set_to_none=True)
        loss = normalizer.tilt_objective(obs)
        if l2_eta:
            loss = loss + float(l2_eta) * (normalizer.eta ** 2).mean()
        loss.backward()
        opt.step()
        history.append(float(loss.detach().cpu()))
    return {
        "steps": int(steps),
        "final_nll": history[-1] if history else float(normalizer.negative_log_likelihood(obs).detach().cpu()),
        "history": history,
        "eta": {
            name: float(value)
            for name, value in zip(
                normalizer.features.feature_names,
                normalizer.eta.detach().cpu(),
            )
        },
        "audit": normalizer.audit_dict(),
    }


class LatentMixtureObservationTilt:
    """Low-rank latent residual layer over the visible observation law.

    The latent state is a small mixture index, not a claimed hardware label:

        P(y) = sum_z pi_z P_0(y) exp(eta_z.T T(y) - A(eta_z)).

    Mixtures of low-dimensional tilts can create higher-order cumulants while
    avoiding one free parameter per pair or triple support.
    """

    def __init__(
        self,
        base: HypergraphDemTNLikelihood,
        features: TiltFeatureSet,
        *,
        num_components: int = 2,
        base_logits: torch.Tensor | None = None,
        init_scale: float = 1e-3,
    ) -> None:
        if int(num_components) < 1:
            raise ValueError("num_components must be positive")
        if features.num_bits != base.num_bits:
            raise ValueError(
                f"feature width {features.num_bits} != base.num_bits={base.num_bits}"
            )
        self.base = base
        self.features = features.to(dtype=base.dtype, device=base.device)
        if base_logits is None:
            base_logits = base.logits.detach().clone()
        self.base_logits = base_logits.detach().clone().to(dtype=base.dtype, device=base.device)
        if tuple(self.base_logits.shape) != tuple(base.logits.shape):
            raise ValueError("base_logits must have one entry per base mechanism")
        self.num_components = int(num_components)
        init = torch.zeros(
            (self.num_components, self.features.num_features),
            dtype=base.dtype,
            device=base.device,
        )
        if self.num_components > 1 and float(init_scale) != 0.0:
            offsets = torch.linspace(
                -float(init_scale),
                float(init_scale),
                self.num_components,
                dtype=base.dtype,
                device=base.device,
            )
            init = offsets[:, None].expand_as(init).clone()
        self.component_etas = init.detach().clone().requires_grad_(True)
        self.mixture_logits = torch.zeros(
            (self.num_components,),
            dtype=base.dtype,
            device=base.device,
            requires_grad=True,
        )

    def _as_observation_matrix(self, observations: torch.Tensor) -> torch.Tensor:
        obs = torch.as_tensor(observations, dtype=torch.bool, device=self.base.device)
        if obs.ndim == 1:
            obs = obs.unsqueeze(0)
        if obs.ndim != 2 or int(obs.shape[1]) != self.base.num_bits:
            raise ValueError(f"observations must have shape [N, {self.base.num_bits}]")
        return obs

    def feature_values(self, observations: torch.Tensor) -> torch.Tensor:
        obs = self._as_observation_matrix(observations)
        return obs.to(dtype=self.base.dtype) @ self.features.matrix

    def _log_partition_for_eta(self, eta: torch.Tensor) -> torch.Tensor:
        helper = ObservationTiltNormalizer(
            self.base,
            self.features,
            base_logits=self.base_logits,
        )
        return helper.log_partition_for_eta(eta)

    def log_partitions(self) -> torch.Tensor:
        return torch.stack([
            self._log_partition_for_eta(self.component_etas[k])
            for k in range(self.num_components)
        ])

    def component_log_terms(self, observations: torch.Tensor) -> torch.Tensor:
        values = self.feature_values(observations)
        log_weights = torch.log_softmax(self.mixture_logits, dim=0)
        log_z = self.log_partitions()
        return values @ self.component_etas.T + log_weights - log_z

    def tilt_log_factor(self, observations: torch.Tensor) -> torch.Tensor:
        return torch.logsumexp(self.component_log_terms(observations), dim=1)

    def posterior_responsibilities(self, observations: torch.Tensor) -> torch.Tensor:
        """Per-shot posterior over latent normalization states."""

        return torch.softmax(self.component_log_terms(observations), dim=1)

    def log_prob(self, observations: torch.Tensor) -> torch.Tensor:
        obs = self._as_observation_matrix(observations)
        base_log_prob = self.base.log_prob(obs, logits=self.base_logits)
        return base_log_prob + self.tilt_log_factor(obs)

    def negative_log_likelihood(self, observations: torch.Tensor) -> torch.Tensor:
        return -self.log_prob(observations).mean()

    def tilt_objective(self, observations: torch.Tensor) -> torch.Tensor:
        return -self.tilt_log_factor(observations).mean()

    def mixture_weights(self) -> torch.Tensor:
        return torch.softmax(self.mixture_logits, dim=0)

    def audit_dict(self) -> dict[str, object]:
        return {
            "normalization": "latent_mixture_observation_tilt",
            "signal_role": "learnable_normalization_signal",
            "scheme": self.features.scheme,
            "feature_names": list(self.features.feature_names),
            "num_components": self.num_components,
            "num_trainable_tilts": self.num_components * self.features.num_features,
            "num_trainable_mixture_logits": self.num_components,
            "num_observation_bits": self.base.num_bits,
            "num_underlying_mechanisms": len(self.base.mechanisms),
            "base_probability_owner": "frozen Layer-1 TN law",
            "pair_hyperedge_features": False,
        }


def fit_latent_mixture_observation_tilt(
    model: LatentMixtureObservationTilt,
    observations: torch.Tensor,
    *,
    steps: int = 50,
    lr: float = 0.05,
    l2_eta: float = 0.0,
) -> dict[str, object]:
    """Fit only latent mixture weights and low-dimensional tilt vectors."""

    obs = torch.as_tensor(observations, dtype=torch.bool, device=model.base.device)
    opt = torch.optim.Adam([model.component_etas, model.mixture_logits], lr=float(lr))
    history: list[float] = []
    for _ in range(int(steps)):
        opt.zero_grad(set_to_none=True)
        loss = model.tilt_objective(obs)
        if l2_eta:
            loss = loss + float(l2_eta) * (model.component_etas ** 2).mean()
        loss.backward()
        opt.step()
        history.append(float(loss.detach().cpu()))
    weights = model.mixture_weights().detach().cpu()
    etas = model.component_etas.detach().cpu()
    return {
        "steps": int(steps),
        "final_relative_nll": history[-1] if history else float(model.tilt_objective(obs).detach().cpu()),
        "history": history,
        "mixture_weights": [float(x) for x in weights],
        "component_etas": [
            {
                name: float(value)
                for name, value in zip(model.features.feature_names, etas[k])
            }
            for k in range(model.num_components)
        ],
        "audit": model.audit_dict(),
    }


__all__ = [
    "GroupedLogitNormalizer",
    "HypergraphDemTNLikelihood",
    "HypergraphMechanism",
    "LatentMixtureObservationTilt",
    "ObservationTiltNormalizer",
    "Phase3SupportSet",
    "TiltFeatureSet",
    "fit_latent_mixture_observation_tilt",
    "fit_grouped_logit_normalizer",
    "fit_hypergraph_dem_tn",
    "fit_observation_tilt_normalizer",
    "detector_coordinate_tilt_features",
    "global_tilt_features",
    "one_hot_tilt_features",
    "phase3_supports_from_json",
]
