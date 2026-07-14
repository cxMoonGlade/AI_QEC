"""Built-distribution regressions for the standalone simulator package."""

from __future__ import annotations

import shutil
import subprocess
import sys
import sysconfig
import tarfile
import textwrap
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _assert_success(probe: subprocess.CompletedProcess[str]) -> None:
    assert probe.returncode == 0, probe.stdout + probe.stderr


def _assert_no_repository_scratch_assets(members: list[str]) -> None:
    """External inputs and repository scratch trees must never be distributed."""

    forbidden_tree_names = {"outputs", "external", "legacy", "qec_twin", ".datasets"}
    offenders = []
    for member in members:
        path = Path(member)
        if forbidden_tree_names.intersection(path.parts):
            offenders.append(member)
            continue
        if path.suffix.lower() in {".b8", ".npz"}:
            offenders.append(member)
    assert offenders == []


def test_wheel_contains_only_the_active_runtime_package(tmp_path: Path) -> None:
    """The wheel must not publish the repo-local ``qec_twin`` compatibility tree."""

    fixture = tmp_path / "fixture"
    package_root = fixture / "src"
    active = package_root / "error_coupling_simulator"
    near_prefix = package_root / "error_coupling_simulator_legacy"
    legacy = package_root / "qec_twin"
    fixture_docs = fixture / "docs"
    wheelhouse = tmp_path / "wheelhouse"
    active.mkdir(parents=True)
    near_prefix.mkdir(parents=True)
    legacy.mkdir(parents=True)
    fixture_docs.mkdir()
    wheelhouse.mkdir()
    shutil.copy2(REPO_ROOT / "pyproject.toml", fixture / "pyproject.toml")
    shutil.copy2(REPO_ROOT / "MANIFEST.in", fixture / "MANIFEST.in")
    (active / "__init__.py").write_text("", encoding="utf-8")
    (active / "README.md").write_text("fixture package\n", encoding="utf-8")
    for name in (
        "SIMULATOR.md",
        "METRICS.md",
        "FAITHFULNESS_PROTOCOL.md",
        "NUMERICAL_PROVENANCE.md",
        "service_status.json",
        "CODE_MAP.md",
    ):
        (fixture_docs / name).write_text(f"fixture {name}\n", encoding="utf-8")
    (near_prefix / "__init__.py").write_text("", encoding="utf-8")
    (legacy / "__init__.py").write_text("", encoding="utf-8")

    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from setuptools.build_meta import build_wheel; "
                f"build_wheel({str(wheelhouse)!r})"
            ),
        ],
        cwd=fixture,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr

    wheels = list(wheelhouse.glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as wheel:
        members = wheel.namelist()
        top_level_member = next(
            name for name in members if name.endswith(".dist-info/top_level.txt")
        )
        top_levels = wheel.read(top_level_member).decode("utf-8").splitlines()
        entry_point_members = [
            name for name in members if name.endswith(".dist-info/entry_points.txt")
        ]
        entry_points = (
            wheel.read(entry_point_members[0]).decode("utf-8")
            if entry_point_members
            else ""
        )

    assert top_levels == ["error_coupling_simulator"]
    assert not any(name.startswith("qec_twin/") for name in members)
    assert "qec-twin-m4" not in entry_points
    assert "qec_twin" not in entry_points


def test_sdist_prunes_legacy_even_with_a_stale_manifest(tmp_path: Path) -> None:
    """An old broad ``SOURCES.txt`` must not leak ``qec_twin`` into the sdist."""

    fixture = tmp_path / "fixture"
    package_root = fixture / "src"
    active = package_root / "error_coupling_simulator"
    near_prefix = package_root / "error_coupling_simulator_legacy"
    legacy = package_root / "qec_twin"
    egg_info = package_root / "error_coupling_simulator.egg-info"
    fixture_docs = fixture / "docs"
    dist_dir = tmp_path / "sdist"
    active.mkdir(parents=True)
    near_prefix.mkdir(parents=True)
    legacy.mkdir(parents=True)
    egg_info.mkdir(parents=True)
    fixture_docs.mkdir()
    dist_dir.mkdir()
    shutil.copy2(REPO_ROOT / "pyproject.toml", fixture / "pyproject.toml")
    shutil.copy2(REPO_ROOT / "MANIFEST.in", fixture / "MANIFEST.in")
    (active / "__init__.py").write_text("", encoding="utf-8")
    (active / "README.md").write_text("fixture package\n", encoding="utf-8")
    for name in (
        "SIMULATOR.md",
        "METRICS.md",
        "FAITHFULNESS_PROTOCOL.md",
        "NUMERICAL_PROVENANCE.md",
        "service_status.json",
        "CODE_MAP.md",
    ):
        (fixture_docs / name).write_text(f"fixture {name}\n", encoding="utf-8")
    (near_prefix / "__init__.py").write_text("", encoding="utf-8")
    (legacy / "__init__.py").write_text("", encoding="utf-8")
    (egg_info / "SOURCES.txt").write_text(
        "pyproject.toml\n"
        "src/error_coupling_simulator/__init__.py\n"
        "src/error_coupling_simulator_legacy/__init__.py\n"
        "src/qec_twin/__init__.py\n",
        encoding="utf-8",
    )

    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from setuptools.build_meta import build_sdist; "
                f"build_sdist({str(dist_dir)!r})"
            ),
        ],
        cwd=fixture,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr

    archives = list(dist_dir.glob("*.tar.gz"))
    assert len(archives) == 1
    with tarfile.open(archives[0], mode="r:gz") as archive:
        members = archive.getnames()

    assert any("/src/error_coupling_simulator/__init__.py" in name for name in members)
    assert not any("/src/error_coupling_simulator_legacy/" in name for name in members)
    assert not any("/src/qec_twin/" in name for name in members)


def test_real_sdist_wheel_installs_and_runs_without_the_repository(tmp_path: Path) -> None:
    """The real package must survive the complete standalone distribution path."""

    fixture = tmp_path / "fixture"
    package_parent = fixture / "src"
    fixture_docs = fixture / "docs"
    sdist_dir = tmp_path / "sdist"
    unpacked_dir = tmp_path / "unpacked"
    wheelhouse = tmp_path / "wheelhouse"
    install_root = tmp_path / "installed"
    isolated_cwd = tmp_path / "isolated-cwd"
    package_parent.mkdir(parents=True)
    fixture_docs.mkdir()
    sdist_dir.mkdir()
    unpacked_dir.mkdir()
    wheelhouse.mkdir()
    install_root.mkdir()
    isolated_cwd.mkdir()

    for name in ("pyproject.toml", "MANIFEST.in", "README.md"):
        shutil.copy2(REPO_ROOT / name, fixture / name)
    for name in (
        "SIMULATOR.md",
        "METRICS.md",
        "FAITHFULNESS_PROTOCOL.md",
        "NUMERICAL_PROVENANCE.md",
        "service_status.json",
        "CODE_MAP.md",
    ):
        shutil.copy2(REPO_ROOT / "docs" / name, fixture_docs / name)
    shutil.copytree(
        REPO_ROOT / "src" / "error_coupling_simulator",
        package_parent / "error_coupling_simulator",
    )

    sdist_probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from setuptools.build_meta import build_sdist; "
                f"build_sdist({str(sdist_dir)!r})"
            ),
        ],
        cwd=fixture,
        check=False,
        capture_output=True,
        text=True,
    )
    _assert_success(sdist_probe)
    archives = list(sdist_dir.glob("*.tar.gz"))
    assert len(archives) == 1

    with tarfile.open(archives[0], mode="r:gz") as archive:
        archive_members = archive.getmembers()
        sdist_members = [member.name for member in archive_members]
        _assert_no_repository_scratch_assets(sdist_members)
        for member in archive_members:
            member_path = Path(member.name)
            assert not member_path.is_absolute()
            assert ".." not in member_path.parts
        if sys.version_info >= (3, 12):
            archive.extractall(unpacked_dir, filter="data")
        else:  # pragma: no cover - compatibility with the declared Python 3.11 floor.
            archive.extractall(unpacked_dir)
    unpacked_sources = [path for path in unpacked_dir.iterdir() if path.is_dir()]
    assert len(unpacked_sources) == 1

    wheel_probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from setuptools.build_meta import build_wheel; "
                f"build_wheel({str(wheelhouse)!r})"
            ),
        ],
        cwd=unpacked_sources[0],
        check=False,
        capture_output=True,
        text=True,
    )
    _assert_success(wheel_probe)
    wheels = list(wheelhouse.glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as wheel:
        wheel_members = wheel.namelist()
    _assert_no_repository_scratch_assets(wheel_members)
    simulator_doc_members = [
        name
        for name in wheel_members
        if ".data/" in name
        and name.endswith("/share/doc/error-coupling-simulator/SIMULATOR.md")
    ]
    assert len(simulator_doc_members) == 1
    service_catalog_members = [
        name
        for name in wheel_members
        if ".data/" in name
        and name.endswith("/share/doc/error-coupling-simulator/service_status.json")
    ]
    code_map_members = [
        name
        for name in wheel_members
        if ".data/" in name
        and name.endswith("/share/doc/error-coupling-simulator/CODE_MAP.md")
    ]
    assert len(service_catalog_members) == 1
    assert len(code_map_members) == 1

    install_probe = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            "--no-index",
            "--target",
            str(install_root),
            str(wheels[0]),
        ],
        cwd=isolated_cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    _assert_success(install_probe)

    runtime_probe = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            textwrap.dedent(
                """
                import importlib
                import importlib.abc
                import importlib.metadata
                import importlib.resources
                import sys
                from pathlib import Path

                install_root = Path(sys.argv[1]).resolve()
                repository_src = Path(sys.argv[2]).resolve()
                dependency_root = Path(sys.argv[3]).resolve()
                sys.path[:0] = [str(install_root), str(dependency_root)]

                for entry in sys.path:
                    if not entry:
                        continue
                    resolved = Path(entry).resolve()
                    assert resolved != repository_src
                    assert repository_src not in resolved.parents

                class RejectLegacyImports(importlib.abc.MetaPathFinder):
                    def find_spec(self, fullname, path=None, target=None):
                        if fullname == "qec_twin" or fullname.startswith("qec_twin."):
                            raise AssertionError(
                                f"standalone package imported forbidden legacy module {fullname}"
                            )
                        return None

                sys.meta_path.insert(0, RejectLegacyImports())

                package = importlib.import_module("error_coupling_simulator")
                distribution = importlib.metadata.distribution("error-coupling-simulator")
                assert install_root in Path(package.__file__).resolve().parents
                assert install_root in Path(distribution.locate_file("")).resolve().parents or (
                    Path(distribution.locate_file("")).resolve() == install_root
                )
                assert package.__version__ == distribution.version

                from error_coupling_simulator.carrier.within_cycle import (
                    package_build_identity,
                )

                build_identity = package_build_identity()
                assert build_identity["version"] == distribution.version
                assert len(build_identity["package_tree_sha256"]) == 64
                int(build_identity["package_tree_sha256"], 16)
                assert build_identity["git_commit"] is None

                namespaces = (
                    "carrier",
                    "certify",
                    "frontend",
                    "mechanisms",
                    "noise_processes",
                    "quantum_bath",
                    "source",
                )
                for namespace in namespaces:
                    module = importlib.import_module(
                        f"error_coupling_simulator.{namespace}"
                    )
                    assert install_root in Path(module.__file__).resolve().parents

                package_files = importlib.resources.files(package)
                assets = (
                    "README.md",
                    "carrier/kernels/README.md",
                    "carrier/kernels/fused_kraus_local.cpp",
                    "carrier/kernels/fused_kraus_local.cu",
                    "carrier/kernels/qutrit_mcwf_ops.cu",
                    "carrier/kernels/sv_traj_d3.cu",
                )
                for relative_path in assets:
                    asset = package_files.joinpath(*Path(relative_path).parts)
                    assert asset.is_file(), relative_path
                    assert asset.read_bytes(), relative_path

                installed_binding_spec = (
                    install_root
                    / "share"
                    / "doc"
                    / "error-coupling-simulator"
                    / "SIMULATOR.md"
                )
                assert installed_binding_spec.is_file()
                assert installed_binding_spec.read_text(encoding="utf-8").startswith(
                    "# SIMULATOR.md"
                )

                installed_service_catalog = (
                    install_root
                    / "share"
                    / "doc"
                    / "error-coupling-simulator"
                    / "service_status.json"
                )
                installed_code_map = (
                    install_root
                    / "share"
                    / "doc"
                    / "error-coupling-simulator"
                    / "CODE_MAP.md"
                )
                assert installed_service_catalog.is_file()
                assert installed_code_map.is_file()
                import json
                service_catalog = json.loads(
                    installed_service_catalog.read_text(encoding="utf-8")
                )
                assert service_catalog["_schema"] == (
                    "error_coupling_simulator.service_status.v2"
                )
                assert len(service_catalog["services"]) == 27
                assert installed_code_map.read_text(encoding="utf-8").startswith(
                    "# CODE_MAP"
                )

                import numpy as np
                from error_coupling_simulator.carrier import PackedShotBatch

                packed = PackedShotBatch.from_raw_syndromes(
                    np.asarray([[0, 1, 1, 1], [1, 0, 1, 0]], dtype=np.uint8),
                    np.asarray([0, 1], dtype=np.uint8),
                    rounds=2,
                    num_stabilizers=2,
                )
                record = packed.to_record_batch()
                assert record.det.tolist() == [[0, 1, 1, 0], [1, 0, 0, 0]]
                assert record.obs.tolist() == [0, 1]
                assert record.provenance["record_semantics"] == "temporal_detector_events"

                # Public certification algebra: a generic two-qubit identity
                # channel has the 16-dimensional identity PTM.
                from error_coupling_simulator.certify import ptm_from_kraus

                two_qubit_identity = np.eye(4, dtype=np.complex128)
                identity_ptm = ptm_from_kraus(two_qubit_identity)
                assert identity_ptm.shape == (16, 16)
                assert np.allclose(identity_ptm, np.eye(16), atol=1e-12)

                # QuTiP is a core dependency because the public CZ deriver is
                # package-owned.  Exercise the public type without deriving a
                # channel, then run the ququart service from an explicit
                # in-memory identity channel on CPU.
                from error_coupling_simulator.mechanisms import CZParams
                from error_coupling_simulator import frontend

                assert CZParams().sim_levels == 5
                ququart_identity = np.eye(16, dtype=np.complex128)[None, :, :]
                ququart = frontend.simulate_ququart_transport_smoke(
                    initial_levels="12",
                    shots=4,
                    seed=7,
                    channel=ququart_identity,
                    device="cpu",
                )
                assert ququart.initial_state_probability == 1.0
                assert sum(ququart.counts.values()) == 4
                assert ququart.manifest["noise"]["source_kind"] == (
                    "in_memory_kraus_injection"
                )

                # Axis-2 sources and restricted 1D-MPS entries must be exposed
                # by their package facades.  Import only: no GPU execution.
                from error_coupling_simulator.source import (
                    OneOverFDriftSource,
                    PhaseBurstSource,
                    RTNSource,
                    TemporalStormSPPSource,
                    timeline_to_coupled_params,
                )
                from error_coupling_simulator.noise_processes import (
                    CoupledCycleNoiseProcess,
                )
                from error_coupling_simulator.frontend import (
                    CircuitBuilder,
                    CompiledMcwfProgram,
                    DenseQuditMcwfBackend,
                    SourceStimPauliProjectionSpec,
                    SourceStimPauliRule,
                    Simulator,
                    circuit_ir_to_substep_schedule,
                    compile_code_spec_to_substep_schedule,
                    stim_circuit_to_substep_schedule,
                    axis1_mcwf_mps_state_record_execution_manifest,
                    axis1_qt_mps_restricted_execution_manifest,
                )

                assert OneOverFDriftSource.__module__.startswith(
                    "error_coupling_simulator.source."
                )
                source = OneOverFDriftSource(n_fluctuators=3)
                timeline = source.sample(seed=13, n_cycles=8)
                coupled_params = timeline_to_coupled_params(timeline)
                permutation = timeline.independent_baseline(seed=17)
                assert len(coupled_params) == timeline.n_cycles == 8
                assert permutation.coupling_mode == "independent"
                assert np.allclose(
                    np.sort(permutation.payload_series("z_radns")),
                    np.sort(timeline.payload_series("z_radns")),
                )
                assert hasattr(
                    CoupledCycleNoiseProcess,
                    "matched_marginal_permutation_control",
                )
                assert hasattr(CoupledCycleNoiseProcess, "off_source")
                assert CircuitBuilder is frontend.CircuitBuilder
                assert Simulator is frontend.Simulator
                assert callable(axis1_mcwf_mps_state_record_execution_manifest)
                assert callable(axis1_qt_mps_restricted_execution_manifest)

                # Every newly catalogued core/research surface must at least be
                # importable from the isolated wheel.  Timeline primitives get
                # a deterministic CPU-light sample; GPU-only carriers are not
                # executed in this distribution-boundary test.
                assert RTNSource().sample(seed=19, n_cycles=4).n_cycles == 4
                assert PhaseBurstSource().sample(seed=23, n_cycles=4).n_cycles == 4
                assert TemporalStormSPPSource().sample(seed=29, n_cycles=4).n_cycles == 4
                assert callable(compile_code_spec_to_substep_schedule)
                assert callable(circuit_ir_to_substep_schedule)
                assert callable(stim_circuit_to_substep_schedule)
                assert SourceStimPauliProjectionSpec.__module__.startswith(
                    "error_coupling_simulator.frontend."
                )
                assert SourceStimPauliRule.__module__.startswith(
                    "error_coupling_simulator.frontend."
                )
                assert CompiledMcwfProgram.__module__.startswith(
                    "error_coupling_simulator.frontend."
                )
                assert DenseQuditMcwfBackend.__module__.startswith(
                    "error_coupling_simulator.frontend."
                )

                import torch
                from error_coupling_simulator.carrier.exact.circuit_sim import (
                    qubit_marginal_one,
                    zero_state,
                )
                from error_coupling_simulator.carrier.cptp_channel import (
                    StinespringChannel,
                    apply_kraus,
                )
                from error_coupling_simulator.carrier.channels import (
                    custom_non_pauli_kraus,
                    thermal_relaxation_kraus,
                )

                rho0 = zero_state(1, device="cpu")
                assert rho0.shape == (2, 2)
                assert float(qubit_marginal_one(rho0, 0, 1)) <= 1.1e-12
                assert StinespringChannel.__module__.startswith(
                    "error_coupling_simulator.carrier."
                )
                assert callable(apply_kraus)
                assert callable(custom_non_pauli_kraus)
                assert callable(thermal_relaxation_kraus)

                from error_coupling_simulator.certify import certify_noise_process
                from error_coupling_simulator.certify.anchors import (
                    ClosedFormAnchor,
                    CorruptStabControl,
                    DMOracleAnchor,
                    ShuffleControl,
                    StimCliffordAnchor,
                )
                from error_coupling_simulator.quantum_bath import (
                    axis_ad_null_point,
                    dual_point,
                    dual_point_qrt,
                    field_null_point,
                    min_tv_to_incoherent,
                    quantum_memory_witness,
                )

                for public_symbol in (
                    certify_noise_process,
                    ClosedFormAnchor,
                    CorruptStabControl,
                    DMOracleAnchor,
                    ShuffleControl,
                    StimCliffordAnchor,
                    axis_ad_null_point,
                    dual_point,
                    dual_point_qrt,
                    field_null_point,
                    min_tv_to_incoherent,
                    quantum_memory_witness,
                ):
                    assert callable(public_symbol)
                """
            ),
            str(install_root),
            str(REPO_ROOT / "src"),
            sysconfig.get_paths()["purelib"],
        ],
        cwd=isolated_cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    _assert_success(runtime_probe)
