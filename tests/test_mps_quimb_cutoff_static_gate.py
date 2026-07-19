from __future__ import annotations

"""Static negative gate for implicit Quimb decomposition cutoffs."""

import ast
from dataclasses import dataclass
from pathlib import Path


_PACKAGE_ROOT = Path(__file__).parents[1] / "src" / "error_coupling_simulator"

# Quimb APIs whose operation can perform a rank-revealing decomposition or
# tensor-network compression. The registry is deliberately explicit: new APIs
# do not inherit coverage through name-pattern guessing.
_DECOMPOSITION_APIS = frozenset(
    {
        "compress",
        "compress_",
        "compress_all",
        "compress_all_",
        "compress_all_1d",
        "compress_all_1d_",
        "compress_all_simple",
        "compress_all_simple_",
        "compress_all_tree",
        "compress_all_tree_",
        "compress_between",
        "compress_between_",
        "compress_site",
        "compress_simplify",
        "compress_simplify_",
        "contract_compressed",
        "contract_compressed_",
        "from_dense",
        "gate_nonlocal",
        "gate_split",
        "gate_split_",
        "gate_with_submpo",
        "gate_with_submpo_",
        "gate_with_auto_swap",
        "insert_compressor_between_regions",
        "insert_compressor_between_regions_",
        "left_compress",
        "left_compress_site",
        "partial_trace_compress",
        "replace_section_with_svd",
        "replace_section_with_svd_",
        "replace_with_svd",
        "replace_with_svd_",
        "right_compress",
        "right_compress_site",
        "split",
        "split_simplify",
        "split_simplify_",
        "split_tensor",
        "swap_sites_with_compress",
        "swap_sites_with_compress_",
        "tensor_1d_compress",
        "tensor_2d_compress",
        "tensor_arbgeom_compress",
        "tensor_compress_bond",
        "tensor_network_1d_compress",
        "tensor_split",
    }
)
_GATE_APIS = frozenset({"gate", "gate_"})
_DECOMPOSING_GATE_CONTRACT_MODES = frozenset(
    {
        "auto-mps",
        "auto-split-gate",
        "nonlocal",
        "split-gate",
        "swap+split",
        "swap-split-gate",
    }
)
_NONDECOMPOSING_GATE_CONTRACT_MODES = frozenset({False})
_ONE_SITE_NAMES = frozenset({"site", "target"})


@dataclass(frozen=True)
class _Violation:
    filename: str
    line: int
    api: str
    reason: str

    def render(self) -> str:
        return f"{self.filename}:{self.line}: {self.api}: {self.reason}"


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    return next((item.value for item in call.keywords if item.arg == name), None)


def _has_named_keyword(call: ast.Call, name: str) -> bool:
    return any(item.arg == name for item in call.keywords)


def _literal_contract_modes(node: ast.expr) -> frozenset[str | bool] | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bool)):
        return frozenset({node.value})
    if isinstance(node, ast.IfExp):
        left = _literal_contract_modes(node.body)
        right = _literal_contract_modes(node.orelse)
        if left is None or right is None:
            return None
        return left | right
    return None


def _is_static_one_site_where(node: ast.expr | None) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, int) and not isinstance(node.value, bool)
    if isinstance(node, ast.Subscript):
        return True
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Name) and node.func.id == "int"
    if isinstance(node, ast.Name):
        return node.id in _ONE_SITE_NAMES
    return False


def _imports_quimb(tree: ast.AST) -> tuple[bool, frozenset[str], dict[str, str]]:
    module_aliases: set[str] = set()
    imported_apis: dict[str, str] = {}
    imports_quimb = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                if item.name == "quimb" or item.name.startswith("quimb."):
                    imports_quimb = True
                    module_aliases.add(item.asname or item.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "quimb" or node.module.startswith("quimb.")):
                imports_quimb = True
                imported_apis.update(
                    {item.asname or item.name: item.name for item in node.names}
                )
    return imports_quimb, frozenset(module_aliases), imported_apis


def _is_string_expr(node: ast.expr, string_names: frozenset[str]) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, bytes))
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.Name):
        return node.id in string_names
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in {"str", "bytes"}
    if isinstance(node, ast.Subscript):
        return _is_string_expr(node.value, string_names)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _is_string_expr(node.left, string_names) and _is_string_expr(
            node.right,
            string_names,
        )
    return False


def _assigned_string_names(tree: ast.AST) -> frozenset[str]:
    names: set[str] = set()
    assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    changed = True
    while changed:
        changed = False
        for node in assignments:
            value = node.value
            if value is None or not _is_string_expr(value, frozenset(names)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id not in names:
                    names.add(target.id)
                    changed = True
    return frozenset(names)


def _call_api(
    call: ast.Call,
    *,
    quimb_surface: bool,
    module_aliases: frozenset[str],
    imported_apis: dict[str, str],
    string_names: frozenset[str],
) -> tuple[str, str] | None:
    """Return ``(kind, api)`` only for a statically covered Quimb call."""

    func = call.func
    if isinstance(func, ast.Name):
        canonical = imported_apis.get(func.id)
        if canonical in _DECOMPOSITION_APIS:
            return "decomposition", canonical
        if canonical in _GATE_APIS:
            return "gate", canonical
        return None
    if not isinstance(func, ast.Attribute):
        return None
    api = func.attr
    explicit_quimb_module = isinstance(func.value, ast.Name) and func.value.id in module_aliases
    if api in _DECOMPOSITION_APIS:
        if api == "split" and _is_string_expr(func.value, string_names):
            return None
        if quimb_surface or explicit_quimb_module:
            return "decomposition", api
    if api in _GATE_APIS and (quimb_surface or explicit_quimb_module):
        return "gate", api
    return None


def _scan_source(source: str, *, filename: str) -> tuple[_Violation, ...]:
    tree = ast.parse(source, filename=filename)
    imports_quimb, module_aliases, imported_apis = _imports_quimb(tree)
    string_names = _assigned_string_names(tree)
    stem = Path(filename).stem.lower()
    quimb_surface = imports_quimb or "mps" in stem
    violations: list[_Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        covered = _call_api(
            node,
            quimb_surface=quimb_surface,
            module_aliases=module_aliases,
            imported_apis=imported_apis,
            string_names=string_names,
        )
        if covered is None:
            continue
        kind, api = covered
        if kind == "decomposition":
            if not _has_named_keyword(node, "cutoff"):
                violations.append(
                    _Violation(
                        filename,
                        node.lineno,
                        api,
                        "decomposition/compression call requires explicit named cutoff=",
                    )
                )
            continue

        contract = _keyword(node, "contract")
        if contract is None:
            if any(item.arg is None for item in node.keywords):
                violations.append(
                    _Violation(
                        filename,
                        node.lineno,
                        api,
                        "dynamic contract mode is unresolved on a Quimb/MPS surface",
                    )
                )
                continue
            # Quimb's literal default is contract=False and performs no split.
            continue
        modes = _literal_contract_modes(contract)
        if modes is None:
            violations.append(
                _Violation(
                    filename,
                    node.lineno,
                    api,
                    "dynamic contract mode is unresolved on a Quimb/MPS surface",
                )
            )
            continue
        unknown = (
            modes
            - _DECOMPOSING_GATE_CONTRACT_MODES
            - _NONDECOMPOSING_GATE_CONTRACT_MODES
            - {True}
        )
        if unknown:
            violations.append(
                _Violation(
                    filename,
                    node.lineno,
                    api,
                    f"unregistered contract mode(s): {sorted(unknown, key=str)!r}",
                )
            )
            continue
        if modes == {True}:
            if not _is_static_one_site_where(_keyword(node, "where")):
                violations.append(
                    _Violation(
                        filename,
                        node.lineno,
                        api,
                        "contract=True is exempt only for a statically one-site where=",
                    )
                )
            continue
        if modes & _DECOMPOSING_GATE_CONTRACT_MODES and not _has_named_keyword(node, "cutoff"):
            violations.append(
                _Violation(
                    filename,
                    node.lineno,
                    api,
                    "decomposition-triggering gate contract requires explicit named cutoff=",
                )
            )
    return tuple(violations)


def test_quimb_split_requires_named_cutoff() -> None:
    source = """
def apply(joined):
    return joined.split(left_inds=['a'], max_bond=2)
"""
    violations = _scan_source(source, filename="restricted_mps_adapter.py")
    assert len(violations) == 1
    assert violations[0].api == "split"
    assert "explicit named cutoff=" in violations[0].reason


def test_only_a_direct_named_cutoff_satisfies_a_decomposition_call() -> None:
    explicit = """
def apply(joined):
    return joined.split(left_inds=["a"], max_bond=2, cutoff=0.0)
"""
    assert _scan_source(explicit, filename="restricted_mps_adapter.py") == ()

    implicit_cases = (
        """
def apply(joined, kwargs):
    return joined.split(left_inds=["a"], **kwargs)
""",
        """
def apply(joined, cutoff=0.0):
    return joined.split(left_inds=["a"])
""",
        """
def apply(state):
    return state.compress(None, False, 0.0)
""",
    )
    for source in implicit_cases:
        violations = _scan_source(source, filename="restricted_mps_adapter.py")
        assert len(violations) == 1
        assert "explicit named cutoff=" in violations[0].reason


def test_registered_decomposition_gate_modes_require_named_cutoff() -> None:
    for mode in sorted(_DECOMPOSING_GATE_CONTRACT_MODES):
        missing = (
            "def apply(state, gate):\n"
            f"    state.gate_(gate, where=(0, 1), contract={mode!r})\n"
        )
        violations = _scan_source(missing, filename="restricted_mps_execution.py")
        assert len(violations) == 1
        assert violations[0].api == "gate_"
        assert "explicit named cutoff=" in violations[0].reason

        explicit = missing.rstrip()[:-1] + ", cutoff=0.0)\n"
        assert _scan_source(explicit, filename="restricted_mps_execution.py") == ()


def test_dynamic_gate_contract_mode_fails_closed_on_mps_surface() -> None:
    source = """
def apply(state, gate, contract_mode):
    state.gate_(gate, where=(0, 1), contract=contract_mode, cutoff=0.0)
"""
    violations = _scan_source(source, filename="restricted_mps_execution.py")
    assert len(violations) == 1
    assert "dynamic contract mode is unresolved" in violations[0].reason

    resolved_conditional = """
def apply(state, gate, support):
    state.gate_(
        gate,
        where=support if len(support) > 1 else support[0],
        contract="auto-mps" if len(support) > 1 else True,
        cutoff=0.0,
    )
"""
    assert _scan_source(
        resolved_conditional,
        filename="restricted_mps_execution.py",
    ) == ()


def test_kwargs_only_gate_contract_propagation_fails_closed() -> None:
    source = """
def apply(state, gate, options):
    state.gate_(gate, where=(0, 1), **options)
"""
    violations = _scan_source(source, filename="restricted_mps_execution.py")
    assert len(violations) == 1
    assert "dynamic contract mode is unresolved" in violations[0].reason


def test_one_site_contract_true_and_non_quimb_names_are_outside_gate() -> None:
    one_site = """
import quimb.tensor as qtn

def apply(state, gate, support, target, site):
    "a,b".split(",")
    str("a,b").split(",")
    state.gate_(gate, where=support[0], contract=True)
    state.gate_(gate, where=int(target), contract=True)
    state.gate_(gate, where=site, contract=True)
"""
    assert _scan_source(one_site, filename="restricted_mps_execution.py") == ()

    multi_site = """
def apply(state, gate):
    state.gate_(gate, where=(0, 1), contract=True)
"""
    violations = _scan_source(multi_site, filename="restricted_mps_execution.py")
    assert len(violations) == 1
    assert "exempt only for a statically one-site" in violations[0].reason

    circuit_builder = """
def compile(builder):
    builder.gate("ISWAP", (0, 1))
"""
    assert _scan_source(circuit_builder, filename="circuit_ir.py") == ()


def test_quimb_import_aliases_remain_covered_package_wide() -> None:
    source = """
from quimb.tensor import tensor_split as decompose

def apply(tensor):
    return decompose(tensor, left_inds=["a"])
"""
    violations = _scan_source(source, filename="generic_tensor_adapter.py")
    assert len(violations) == 1
    assert violations[0].api == "tensor_split"


def test_scanner_self_mutation_removing_cutoff_turns_gate_red() -> None:
    representative = """
def apply(state, gate):
    state.gate_(
        gate,
        where=(0, 1),
        contract="auto-mps",
        max_bond=2,
        cutoff=0.0,
    )
"""
    assert _scan_source(
        representative,
        filename="restricted_mps_execution.py",
    ) == ()
    mutated = representative.replace("        cutoff=0.0,\n", "", 1)
    assert mutated != representative
    violations = _scan_source(mutated, filename="restricted_mps_execution.py")
    assert len(violations) == 1
    assert "explicit named cutoff=" in violations[0].reason


def test_mpo_from_dense_and_submpo_decompositions_require_named_cutoff() -> None:
    missing = """
import quimb.tensor as qtn

def apply(state, gate):
    mpo = qtn.MatrixProductOperator.from_dense(
        gate,
        dims=(2, 2, 2),
        sites=(0, 1, 2),
        L=3,
    )
    candidate = state.gate_with_submpo(
        mpo,
        where=(0, 1, 2),
        method="direct",
    )
    candidate.gate_with_submpo_(
        mpo,
        where=(0, 1, 2),
        method="direct",
    )
    return candidate
"""
    violations = _scan_source(missing, filename="uncapped_nonlocal.py")
    assert [item.api for item in violations] == [
        "from_dense",
        "gate_with_submpo",
        "gate_with_submpo_",
    ]
    assert all("explicit named cutoff=" in item.reason for item in violations)

    explicit = missing.replace(
        "        L=3,\n",
        "        L=3,\n        cutoff=0.0,\n",
        1,
    ).replace(
        '        method="direct",\n',
        '        method="direct",\n        cutoff=0.0,\n',
    )
    assert _scan_source(explicit, filename="uncapped_nonlocal.py") == ()


def test_mpo_and_submpo_cutoff_gate_self_corruption_turns_red() -> None:
    representative = """
import quimb.tensor as qtn

def apply(state, gate):
    mpo = qtn.MatrixProductOperator.from_dense(
        gate,
        dims=(2, 2, 2),
        sites=(0, 1, 2),
        L=3,
        cutoff=0.0,  # MPO_SPLIT_CUTOFF
    )
    candidate = state.gate_with_submpo(
        mpo,
        where=(0, 1, 2),
        method="direct",
        cutoff=0.0,  # SUBMPO_COMPRESS_CUTOFF
    )
    candidate.gate_with_submpo_(
        mpo,
        where=(0, 1, 2),
        method="direct",
        cutoff=0.0,  # SUBMPO_INPLACE_COMPRESS_CUTOFF
    )
    return candidate
"""
    assert _scan_source(representative, filename="uncapped_nonlocal.py") == ()

    mutations = (
        ("        cutoff=0.0,  # MPO_SPLIT_CUTOFF\n", "from_dense"),
        (
            "        cutoff=0.0,  # SUBMPO_COMPRESS_CUTOFF\n",
            "gate_with_submpo",
        ),
        (
            "        cutoff=0.0,  # SUBMPO_INPLACE_COMPRESS_CUTOFF\n",
            "gate_with_submpo_",
        ),
    )
    for removed_line, expected_api in mutations:
        mutated = representative.replace(removed_line, "", 1)
        assert mutated != representative
        violations = _scan_source(mutated, filename="uncapped_nonlocal.py")
        assert len(violations) == 1
        assert violations[0].api == expected_api
        assert "explicit named cutoff=" in violations[0].reason


def test_package_quimb_decomposition_calls_have_explicit_named_cutoff() -> None:
    violations: list[_Violation] = []
    scanned = sorted(_PACKAGE_ROOT.rglob("*.py"))
    assert scanned, f"no package sources found below {_PACKAGE_ROOT}"
    for path in scanned:
        source = path.read_text(encoding="utf-8")
        violations.extend(
            _scan_source(
                source,
                filename=str(path.relative_to(_PACKAGE_ROOT.parents[1])),
            )
        )
    rendered = "\n".join(item.render() for item in violations)
    assert not violations, (
        "Quimb decomposition/compression cutoff gate failed; every covered "
        "call requires a direct named cutoff= at the call site:\n"
        f"{rendered}"
    )
