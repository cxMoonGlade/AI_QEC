#!/usr/bin/env python3
"""Backend-neutral canonical hash of a raw gauged PEPS carrier."""

from __future__ import annotations

import hashlib
import json
import numbers
import struct
from typing import Any, Mapping, Sequence

import numpy as np


HASH_SCHEMA = "gcapeps-finite-memory-final-carrier-hash.v1"
HASH_NAMESPACE = b"gcapeps-finite-memory-final-carrier-hash-v1\x00"
_HEX = frozenset("0123456789abcdef")


def _sha256(value: str, *, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(f"{name} must be 64 lowercase hex characters")
    return value


def _site(value: Any, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise TypeError(f"{name} must be an integer")
    checked = int(value)
    if checked < 0:
        raise ValueError(f"{name} must be nonnegative")
    return checked


def _canonical_edges(
    graph_edges: Sequence[Sequence[int]],
    *,
    sites: tuple[int, ...],
) -> tuple[tuple[int, int], ...]:
    allowed = set(sites)
    edges = []
    seen = set()
    for index, raw in enumerate(tuple(graph_edges)):
        edge = tuple(raw)
        if len(edge) != 2:
            raise ValueError(f"graph_edges[{index}] must have two endpoints")
        left = _site(edge[0], name=f"graph_edges[{index}][0]")
        right = _site(edge[1], name=f"graph_edges[{index}][1]")
        if left == right or left not in allowed or right not in allowed:
            raise ValueError("graph edge is invalid for site_order")
        ordered = (min(left, right), max(left, right))
        if ordered in seen:
            raise ValueError("graph edges contain a duplicate")
        seen.add(ordered)
        edges.append(ordered)
    return tuple(sorted(edges))


def _frame_payload(frame: Mapping[str, Any] | None, *, num_qubits: int):
    if frame is None:
        return None
    if not isinstance(frame, Mapping) or set(frame) != {
        "kind",
        "num_qubits",
        "x_images",
        "z_images",
    }:
        raise ValueError("GC frame has the wrong exact key set")
    if frame["kind"] != "stim_signed_images_v1":
        raise ValueError("GC frame kind is invalid")
    if frame["num_qubits"] != num_qubits:
        raise ValueError("GC frame width disagrees with the carrier")
    output = {
        "kind": frame["kind"],
        "num_qubits": num_qubits,
        "x_images": [],
        "z_images": [],
    }
    for family in ("x_images", "z_images"):
        images = frame[family]
        if not isinstance(images, Sequence) or isinstance(images, (str, bytes)):
            raise TypeError(f"frame {family} must be a sequence")
        if len(images) != num_qubits:
            raise ValueError(f"frame {family} has the wrong length")
        for index, image in enumerate(images):
            if not isinstance(image, Mapping) or set(image) != {"sign", "body"}:
                raise ValueError(f"frame {family}[{index}] has wrong keys")
            sign = image["sign"]
            body = image["body"]
            if isinstance(sign, bool) or sign not in (-1, 1):
                raise ValueError("frame image sign must be +/-1")
            if (
                not isinstance(body, str)
                or len(body) != num_qubits
                or any(character not in "IXYZ" for character in body)
            ):
                raise ValueError("frame image body is invalid")
            output[family].append({"sign": sign, "body": body})
    return output


def canonical_carrier_hash(
    *,
    lane: str,
    site_order: Sequence[int],
    graph_edges: Sequence[Sequence[int]],
    site_tensors: Mapping[int, Mapping[str, Any]],
    gauges: Mapping[tuple[int, int], np.ndarray],
    frame: Mapping[str, Any] | None,
    input_preparation_transcript_sha256: str,
    shared_evolution_transcript_sha256: str,
) -> dict[str, Any]:
    """Return the canonical digest and its fully auditable header.

    ``site_tensors[site]`` must contain the raw tensor, its physical-axis
    position, and a mapping from neighboring site id to virtual-axis position.
    Backend index names are intentionally absent.
    """

    if lane not in {"plain", "gcapeps"}:
        raise ValueError("lane must be plain or gcapeps")
    sites = tuple(_site(value, name="site_order") for value in site_order)
    if not sites or len(set(sites)) != len(sites) or sites != tuple(sorted(sites)):
        raise ValueError("site_order must be nonempty, unique, and ascending")
    edges = _canonical_edges(graph_edges, sites=sites)
    neighbors = {site: [] for site in sites}
    for left, right in edges:
        neighbors[left].append(right)
        neighbors[right].append(left)
    if set(site_tensors) != set(sites):
        raise ValueError("site tensor keys disagree with site_order")

    arrays: list[np.ndarray] = []
    site_headers = []
    for site in sites:
        record = site_tensors[site]
        if not isinstance(record, Mapping) or set(record) != {
            "tensor",
            "physical_axis",
            "virtual_axes",
        }:
            raise ValueError(f"site {site} tensor record has wrong keys")
        tensor = record["tensor"]
        if not isinstance(tensor, np.ndarray) or tensor.dtype.str != "<c16":
            raise TypeError(f"site {site} tensor must have dtype <c16")
        if not np.isfinite(tensor.real).all() or not np.isfinite(tensor.imag).all():
            raise ValueError(f"site {site} tensor is non-finite")
        physical_axis = _site(record["physical_axis"], name="physical_axis")
        virtual_axes = record["virtual_axes"]
        if not isinstance(virtual_axes, Mapping):
            raise TypeError("virtual_axes must be a mapping")
        expected_neighbors = tuple(sorted(neighbors[site]))
        if set(virtual_axes) != set(expected_neighbors):
            raise ValueError(f"site {site} virtual axes disagree with graph")
        canonical_axes = [physical_axis]
        for neighbor in expected_neighbors:
            canonical_axes.append(
                _site(virtual_axes[neighbor], name=f"virtual axis {site}-{neighbor}")
            )
        if sorted(canonical_axes) != list(range(tensor.ndim)):
            raise ValueError(f"site {site} axes do not cover tensor dimensions")
        canonical = np.ascontiguousarray(
            np.transpose(tensor, axes=canonical_axes),
            dtype=np.complex128,
        )
        ordinal = len(arrays)
        arrays.append(canonical)
        site_headers.append(
            {
                "site": site,
                "tensor_array_ordinal": ordinal,
                "dtype": canonical.dtype.str,
                "shape": list(canonical.shape),
                "axis_roles": [
                    "physical",
                    *[f"virtual:{neighbor}" for neighbor in expected_neighbors],
                ],
            }
        )

    normalized_gauges = {}
    for raw_edge, gauge in gauges.items():
        edge = tuple(raw_edge)
        if len(edge) != 2:
            raise ValueError("gauge edge must have two endpoints")
        ordered = (
            min(_site(edge[0], name="gauge edge"), _site(edge[1], name="gauge edge")),
            max(_site(edge[0], name="gauge edge"), _site(edge[1], name="gauge edge")),
        )
        if ordered not in edges or ordered in normalized_gauges:
            raise ValueError("gauge edge is absent or duplicated")
        if (
            not isinstance(gauge, np.ndarray)
            or gauge.dtype.str != "<f8"
            or gauge.ndim != 1
            or not gauge.flags.c_contiguous
        ):
            raise TypeError("gauge must be a C-contiguous one-dimensional <f8 array")
        if not np.isfinite(gauge).all() or np.any(gauge < 0.0):
            raise ValueError("gauge must be finite and nonnegative")
        normalized_gauges[ordered] = gauge

    edge_headers = []
    for edge in edges:
        gauge = normalized_gauges.get(edge)
        if gauge is None:
            edge_headers.append(
                {
                    "edge": list(edge),
                    "gauge_present": False,
                    "gauge_array_ordinal": None,
                    "dtype": None,
                    "shape": None,
                }
            )
        else:
            ordinal = len(arrays)
            arrays.append(gauge)
            edge_headers.append(
                {
                    "edge": list(edge),
                    "gauge_present": True,
                    "gauge_array_ordinal": ordinal,
                    "dtype": gauge.dtype.str,
                    "shape": list(gauge.shape),
                }
            )

    checked_frame = _frame_payload(frame, num_qubits=len(sites))
    if (lane == "plain") != (checked_frame is None):
        raise ValueError("plain requires null frame and gcapeps requires a frame")
    header = {
        "schema": HASH_SCHEMA,
        "lane": lane,
        "site_order": list(sites),
        "graph_edges": [list(edge) for edge in edges],
        "sites": site_headers,
        "edges": edge_headers,
        "frame": checked_frame,
        "input_preparation_transcript_sha256": _sha256(
            input_preparation_transcript_sha256,
            name="input preparation transcript",
        ),
        "shared_evolution_transcript_sha256": _sha256(
            shared_evolution_transcript_sha256,
            name="shared evolution transcript",
        ),
    }
    header_bytes = json.dumps(
        header,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(HASH_NAMESPACE)
    digest.update(struct.pack(">Q", len(header_bytes)))
    digest.update(header_bytes)
    array_byte_lengths = []
    for array in arrays:
        raw = array.tobytes(order="C")
        array_byte_lengths.append(len(raw))
        digest.update(struct.pack(">Q", len(raw)))
        digest.update(raw)
    return {
        "schema": HASH_SCHEMA,
        "sha256": digest.hexdigest(),
        "header": header,
        "header_byte_length": len(header_bytes),
        "array_byte_lengths": array_byte_lengths,
    }
