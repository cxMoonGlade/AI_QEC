"""Static guard for the simulator/retired-inference ownership boundary."""

from __future__ import annotations

import ast
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = TEST_ROOT.parent / "src" / "error_coupling_simulator"
RETIRED_IMPORTS = (
    "qec_twin.calibration.nll",
    "qec_twin.calibration.cptp_recovery",
    "qec_twin.contexts.ladder",
    "qec_twin.audit.bands",
    "qec_twin.audit.gating",
    "qec_twin.audit.validity",
    "qec_twin.forward.exact.rep_code",
)
RETIRED_SYMBOLS = ("RepCodeTwin", "CoupledRepCodeTwin")


def test_retired_twin_programs_do_not_reenter_active_collection() -> None:
    assert list(TEST_ROOT.glob("test_twin_*.py")) == []


def test_active_tests_do_not_import_retired_inference_stack() -> None:
    offenders: list[str] = []
    for path in sorted(TEST_ROOT.glob("test_*.py")):
        if path == Path(__file__).resolve():
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imported = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        imported.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        matched = [needle for needle in RETIRED_IMPORTS if needle in imported]
        matched.extend(symbol for symbol in RETIRED_SYMBOLS if symbol in names)
        if matched:
            offenders.append(f"{path.name}: {', '.join(matched)}")
    assert offenders == [], "retired inference dependencies in active tests:\n" + "\n".join(offenders)


def test_legacy_m_id_catalog_does_not_drive_active_simulator_construction() -> None:
    """Keep M0--M34 behind its frozen adapter instead of reviving it in the mainline."""

    compatibility_files = {
        PACKAGE_ROOT / "carrier" / "channels.py",
        PACKAGE_ROOT / "mechanisms" / "catalog.py",
    }
    offenders: list[str] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        if path in compatibility_files:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        catalog_imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.endswith("mechanisms.catalog")
        }
        catalog_imports.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
            if alias.name.endswith("mechanisms.catalog")
        )
        adapter_calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"MechanismSpec", "mechanism_channel"}
        }
        adapter_calls.update(
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"MechanismSpec", "mechanism_channel"}
        )
        matched = sorted({*catalog_imports, *adapter_calls})
        if matched:
            offenders.append(f"{path.relative_to(PACKAGE_ROOT)}: {', '.join(matched)}")
    assert offenders == [], (
        "legacy M-ID construction re-entered the simulator mainline:\n"
        + "\n".join(offenders)
    )


def test_public_package_description_matches_simulator_contract() -> None:
    import error_coupling_simulator

    doc = (error_coupling_simulator.__doc__ or "").lower()
    assert "teacher simulator" not in doc
    assert "product is ler" not in doc
    assert "emits a multi-time syndrome record" in doc


def test_neutral_names_preserve_historical_api_identity() -> None:
    from error_coupling_simulator.certify import certify_noise_process, certify_teacher
    from error_coupling_simulator.mechanisms.qutrit_teachers import (
        qutrit_leakage_process,
        qutrit_leakage_process_heterogeneous,
        qutrit_leakage_teacher,
        qutrit_leakage_teacher_heterogeneous,
        calibrate_theta_for_wg_l1,
        solve_theta_for_wg_l1,
    )
    from error_coupling_simulator.mechanisms.seam_teachers import (
        coherent_seam_noise_process,
        coherent_seam_teacher,
        seam_noise_process_arms,
        seam_teacher_arms,
    )
    from error_coupling_simulator.mechanisms.teachers import (
        coupled_mixed_noise_fields,
        coupled_mixed_teacher,
    )
    from error_coupling_simulator.noise_processes import (
        COUPLED_PROCESS_REPRESENTABILITY,
        COUPLED_PROCESS_SCHEMA,
        COUPLED_TEACHER_REPRESENTABILITY,
        COUPLED_TEACHER_SCHEMA,
    )

    assert certify_noise_process is certify_teacher
    assert solve_theta_for_wg_l1 is calibrate_theta_for_wg_l1
    assert qutrit_leakage_process is qutrit_leakage_teacher
    assert qutrit_leakage_process_heterogeneous is qutrit_leakage_teacher_heterogeneous
    assert coherent_seam_noise_process is coherent_seam_teacher
    assert seam_noise_process_arms is seam_teacher_arms
    assert coupled_mixed_noise_fields is coupled_mixed_teacher
    assert COUPLED_PROCESS_REPRESENTABILITY == COUPLED_TEACHER_REPRESENTABILITY
    assert COUPLED_PROCESS_SCHEMA == COUPLED_TEACHER_SCHEMA
