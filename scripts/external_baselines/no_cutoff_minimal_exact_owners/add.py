"""Direct dynamic exact-ADD micro-owner.

The update path compiles an exact relation independently of the current root,
then performs recursive ADD multiplication and input-bit sum abstraction.  It
never materializes or iterates the sparse pair frontier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .model import (
    MICRO_SCOPE,
    SOLVER_PERMISSION,
    TARGET_LOWERING,
    Codec,
    Event,
    PairAddProgram,
    Qsqrt2i,
    ZERO,
    canonical_json_bytes,
    sha256_json,
    validate_frozen_pair_add_program,
)


_TERMINAL_LEVEL = 1 << 30


class _ADDManager:
    """A small reduced ordered ADD manager with exact, unweighted terminals."""

    def __init__(self) -> None:
        self._nodes: list[tuple[object, ...]] = []
        self._terminal_unique: dict[Qsqrt2i, int] = {}
        self._internal_unique: dict[tuple[int, int, int], int] = {}

    @property
    def allocated_node_count(self) -> int:
        return len(self._nodes)

    def terminal(self, value: Qsqrt2i) -> int:
        existing = self._terminal_unique.get(value)
        if existing is not None:
            return existing
        edge = len(self._nodes)
        self._nodes.append(("T", value))
        self._terminal_unique[value] = edge
        return edge

    def node(self, level: int, low: int, high: int) -> int:
        if type(level) is not int or level < 0:
            raise ValueError("ADD level must be a nonnegative integer")
        if low == high:
            return low
        for child in (low, high):
            child_level = self.level(child)
            if child_level <= level:
                raise ValueError("ADD child does not respect the fixed order")
        key = (level, low, high)
        existing = self._internal_unique.get(key)
        if existing is not None:
            return existing
        edge = len(self._nodes)
        self._nodes.append(("N", level, low, high))
        self._internal_unique[key] = edge
        return edge

    def is_terminal(self, edge: int) -> bool:
        return self._nodes[edge][0] == "T"

    def value(self, edge: int) -> Qsqrt2i:
        node = self._nodes[edge]
        if node[0] != "T":
            raise TypeError("internal ADD node has no terminal value")
        value = node[1]
        assert isinstance(value, Qsqrt2i)
        return value

    def level(self, edge: int) -> int:
        node = self._nodes[edge]
        return _TERMINAL_LEVEL if node[0] == "T" else int(node[1])

    def children(self, edge: int) -> tuple[int, int]:
        node = self._nodes[edge]
        if node[0] != "N":
            raise TypeError("terminal ADD node has no children")
        return int(node[2]), int(node[3])

    def _apply(
        self,
        operation: Literal["add", "mul"],
        left: int,
        right: int,
        cache: dict[tuple[str, int, int], int],
    ) -> int:
        if left > right:
            left, right = right, left
        key = (operation, left, right)
        cached = cache.get(key)
        if cached is not None:
            return cached
        if self.is_terminal(left) and self.is_terminal(right):
            if operation == "add":
                result = self.terminal(self.value(left) + self.value(right))
            else:
                result = self.terminal(self.value(left) * self.value(right))
            cache[key] = result
            return result

        top = min(self.level(left), self.level(right))
        if self.level(left) == top:
            left_low, left_high = self.children(left)
        else:
            left_low = left_high = left
        if self.level(right) == top:
            right_low, right_high = self.children(right)
        else:
            right_low = right_high = right
        low = self._apply(operation, left_low, right_low, cache)
        high = self._apply(operation, left_high, right_high, cache)
        result = self.node(top, low, high)
        cache[key] = result
        return result

    def add(self, left: int, right: int) -> int:
        return self._apply("add", left, right, {})

    def multiply(self, left: int, right: int) -> int:
        return self._apply("mul", left, right, {})

    def indicator(self, bits: tuple[int, ...], value: Qsqrt2i) -> int:
        if any(type(bit) is not int or bit not in (0, 1) for bit in bits):
            raise ValueError("ADD indicator requires bits")
        zero = self.terminal(ZERO)
        root = self.terminal(value)
        for level in range(len(bits) - 1, -1, -1):
            if bits[level] == 0:
                root = self.node(level, root, zero)
            else:
                root = self.node(level, zero, root)
        return root

    def import_root(self, source: _ADDManager, root: int, *, shift: int = 0) -> int:
        memo: dict[int, int] = {}

        def visit(edge: int) -> int:
            cached = memo.get(edge)
            if cached is not None:
                return cached
            if source.is_terminal(edge):
                result = self.terminal(source.value(edge))
            else:
                low, high = source.children(edge)
                result = self.node(source.level(edge) + shift, visit(low), visit(high))
            memo[edge] = result
            return result

        return visit(root)

    def sum_abstract_level(self, root: int, target_level: int) -> int:
        memo: dict[int, int] = {}

        def visit(edge: int) -> int:
            cached = memo.get(edge)
            if cached is not None:
                return cached
            level = self.level(edge)
            if level > target_level:
                result = self.add(edge, edge)
            elif level == target_level:
                low, high = self.children(edge)
                result = self.add(low, high)
            else:
                low, high = self.children(edge)
                result = self.node(level, visit(low), visit(high))
            memo[edge] = result
            return result

        return visit(root)

    def evaluate(self, root: int, bits: tuple[int, ...]) -> Qsqrt2i:
        edge = root
        while not self.is_terminal(edge):
            level = self.level(edge)
            if level >= len(bits):
                raise ValueError("assignment is shorter than an ADD level")
            low, high = self.children(edge)
            edge = high if bits[level] else low
        return self.value(edge)

    def reachable_edges(self, root: int) -> set[int]:
        seen: set[int] = set()
        stack = [root]
        while stack:
            edge = stack.pop()
            if edge in seen:
                continue
            seen.add(edge)
            if not self.is_terminal(edge):
                stack.extend(self.children(edge))
        return seen


@dataclass(frozen=True, slots=True)
class ADDState:
    """Opaque root plus a manager containing only root-reachable nodes."""

    _manager: _ADDManager
    _root: int
    width: int
    codec_sha256: str

    def evaluate(self, bits: tuple[int, ...]) -> Qsqrt2i:
        if len(bits) != self.width:
            raise ValueError("assignment width disagrees with ADD state")
        return self._manager.evaluate(self._root, bits)

    @property
    def allocated_node_count(self) -> int:
        return self._manager.allocated_node_count


@dataclass(frozen=True, slots=True)
class RelationADD:
    state: ADDState
    event_name: str
    input_width: int
    output_width: int
    input_codec_sha256: str
    output_codec_sha256: str
    combined_order: tuple[str, ...]


def _copy_reachable(state: ADDState) -> ADDState:
    manager = _ADDManager()
    root = manager.import_root(state._manager, state._root)
    return ADDState(manager, root, state.width, state.codec_sha256)


def _build_clause_function(
    *,
    width: int,
    codec_sha256: str,
    clauses: tuple[tuple[tuple[int, ...], Qsqrt2i], ...],
) -> ADDState:
    manager = _ADDManager()
    root = manager.terminal(ZERO)
    for bits, coefficient in clauses:
        if len(bits) != width:
            raise ValueError("clause width disagrees with ADD function")
        root = manager.add(root, manager.indicator(bits, coefficient))
    return _copy_reachable(ADDState(manager, root, width, codec_sha256))


def compile_transition_relation(
    event: Event,
    input_codec: Codec,
    output_codec: Codec,
) -> RelationADD:
    """Compile literal rows without receiving or inspecting a current root."""

    combined_order = tuple(f"in:{x}" for x in input_codec.fields) + tuple(
        f"out:{x}" for x in output_codec.fields
    )
    clauses = tuple(
        (
            input_codec.encode(row.input_key) + output_codec.encode(row.output_key),
            row.weight,
        )
        for row in event.rows
    )
    identity = sha256_json(
        {
            "combined_order": list(combined_order),
            "event": event.to_data(input_codec, output_codec),
        }
    )
    state = _build_clause_function(
        width=input_codec.width + output_codec.width,
        codec_sha256=identity,
        clauses=clauses,
    )
    return RelationADD(
        state=state,
        event_name=event.name,
        input_width=input_codec.width,
        output_width=output_codec.width,
        input_codec_sha256=input_codec.sha256,
        output_codec_sha256=output_codec.sha256,
        combined_order=combined_order,
    )


def _rename_output_root(
    manager: _ADDManager,
    root: int,
    *,
    input_width: int,
    output_width: int,
    output_codec_sha256: str,
) -> ADDState:
    output_manager = _ADDManager()
    memo: dict[int, int] = {}

    def visit(edge: int) -> int:
        cached = memo.get(edge)
        if cached is not None:
            return cached
        if manager.is_terminal(edge):
            result = output_manager.terminal(manager.value(edge))
        else:
            level = manager.level(edge)
            if level < input_width or level >= input_width + output_width:
                raise ValueError("sum abstraction left a non-output ADD level")
            low, high = manager.children(edge)
            result = output_manager.node(level - input_width, visit(low), visit(high))
        memo[edge] = result
        return result

    output_root = visit(root)
    return ADDState(output_manager, output_root, output_width, output_codec_sha256)


def advance(
    current: ADDState,
    input_codec: Codec,
    output_codec: Codec,
    relation: RelationADD,
) -> ADDState:
    """Apply relation_root * current_root and sum-abstract all input bits."""

    if current.width != input_codec.width or current.codec_sha256 != input_codec.sha256:
        raise ValueError("current ADD root does not match the input codec")
    if (
        relation.input_width != input_codec.width
        or relation.output_width != output_codec.width
        or relation.input_codec_sha256 != input_codec.sha256
        or relation.output_codec_sha256 != output_codec.sha256
    ):
        raise ValueError("relation ADD does not match the advance codecs")
    expected_order = tuple(f"in:{field}" for field in input_codec.fields) + tuple(
        f"out:{field}" for field in output_codec.fields
    )
    if relation.combined_order != expected_order:
        raise ValueError("relation ADD combined order does not match the codecs")
    if relation.state.width != input_codec.width + output_codec.width:
        raise ValueError("relation ADD state width does not match the combined order")

    manager = _ADDManager()
    current_root = manager.import_root(current._manager, current._root)
    relation_root = manager.import_root(relation.state._manager, relation.state._root)
    root = manager.multiply(current_root, relation_root)
    for level in range(input_codec.width):
        root = manager.sum_abstract_level(root, level)
    return _rename_output_root(
        manager,
        root,
        input_width=input_codec.width,
        output_width=output_codec.width,
        output_codec_sha256=output_codec.sha256,
    )


def _snapshot(label: str, state: ADDState) -> dict[str, object]:
    manager = state._manager
    reachable = manager.reachable_edges(state._root)
    terminal_edges = [edge for edge in reachable if manager.is_terminal(edge)]
    terminal_edges.sort(key=lambda edge: canonical_json_bytes(manager.value(edge).to_data()))
    canonical_ids: dict[int, int] = {}
    table: list[dict[str, object]] = []
    for edge in terminal_edges:
        canonical_id = len(table)
        canonical_ids[edge] = canonical_id
        table.append(
            {
                "id": canonical_id,
                "kind": "terminal",
                "value": manager.value(edge).to_data(),
            }
        )

    levels = sorted(
        {manager.level(edge) for edge in reachable if not manager.is_terminal(edge)},
        reverse=True,
    )
    internal_count = 0
    for level in levels:
        edges = [
            edge
            for edge in reachable
            if not manager.is_terminal(edge) and manager.level(edge) == level
        ]
        edges.sort(
            key=lambda edge: tuple(canonical_ids[child] for child in manager.children(edge))
        )
        for edge in edges:
            low, high = manager.children(edge)
            canonical_id = len(table)
            canonical_ids[edge] = canonical_id
            table.append(
                {
                    "high": canonical_ids[high],
                    "id": canonical_id,
                    "kind": "internal",
                    "level": level,
                    "low": canonical_ids[low],
                }
            )
            internal_count += 1

    if set(canonical_ids) != reachable:
        raise AssertionError("canonical ADD renumbering missed a reachable node")
    return {
        "allocated_node_count": manager.allocated_node_count,
        "codec_sha256": state.codec_sha256,
        "internal_count": internal_count,
        "label": label,
        "node_table": table,
        "node_table_sha256": sha256_json(table),
        "reachable_node_count": len(reachable),
        "root_id": canonical_ids[state._root],
        "terminal_count": len(terminal_edges),
    }


def build_total_function_from_fixture_clauses(
    codec: Codec,
    clauses: tuple[tuple[tuple[int, ...], Qsqrt2i], ...],
) -> ADDState:
    """Compile fixture clauses; this is not used by dynamic ``advance``."""

    return _build_clause_function(width=codec.width, codec_sha256=codec.sha256, clauses=clauses)


def snapshot_add_state(label: str, state: ADDState) -> dict[str, object]:
    return _snapshot(label, state)


def run_dynamic_add_owner(program: PairAddProgram) -> dict[str, object]:
    validate_frozen_pair_add_program(program)
    relations = tuple(
        compile_transition_relation(event, program.codecs[index], program.codecs[index + 1])
        for index, event in enumerate(program.events)
    )
    initial_clauses = tuple(
        (program.codecs[0].encode(key), coefficient) for key, coefficient in program.initial
    )
    current = _build_clause_function(
        width=program.codecs[0].width,
        codec_sha256=program.codecs[0].sha256,
        clauses=initial_clauses,
    )
    checkpoints = [_snapshot("A0", current)]
    for index, relation in enumerate(relations):
        current = advance(current, program.codecs[index], program.codecs[index + 1], relation)
        checkpoints.append(_snapshot(program.events[index].name, current))

    history = [int(checkpoint["reachable_node_count"]) for checkpoint in checkpoints]
    peak = max(history)
    peak_index = history.index(peak)
    relation_receipts = []
    for relation in relations:
        relation_snapshot = _snapshot(relation.event_name, relation.state)
        relation_receipts.append(
            {
                "combined_order": list(relation.combined_order),
                "event": relation.event_name,
                "node_table_sha256": relation_snapshot["node_table_sha256"],
                "reachable_node_count": relation_snapshot["reachable_node_count"],
            }
        )
    return {
        "checkpoints": checkpoints,
        "headline_semantics": "DYNAMIC_PAIR_MAP_NOT_FINAL_RECORD_PMF",
        "history_sha256": sha256_json(history),
        "n_exact_pair_add_nodes_history_micro": history,
        "n_exact_pair_add_nodes_peak_micro": peak,
        "peak_event": "INITIAL" if peak_index == 0 else program.events[peak_index - 1].name,
        "program_sha256": program.sha256,
        "relation_receipts": relation_receipts,
        "scope": MICRO_SCOPE,
        "solver_permission": SOLVER_PERMISSION,
        "target_lowering": TARGET_LOWERING,
    }
