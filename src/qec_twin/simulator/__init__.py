"""Simulator frontend package.

This package is intentionally separate from `qec_twin.forward`: it owns the
user-facing circuit/artifact surface, while `forward` owns carrier/substrate
evolution.
"""

from qec_twin.simulator.circuit_ir import (
    CircuitBuilder,
    CircuitIR,
    DetectorDef,
    GateOp,
    MeasureOp,
    ObservableDef,
    Tick,
)
from qec_twin.simulator.code_spec import (
    CodeQubit,
    CodeSpec,
    LogicalObservableSpec,
    PauliTerm,
    StabilizerCheck,
)
from qec_twin.simulator.compiler import compile_code_spec, compile_code_spec_to_compiled
from qec_twin.simulator.cudaq_grover import (
    CudaQGroverResult,
    build_cudaq_grover_kernel,
    simulate_cudaq_grover_noiseless,
)
from qec_twin.simulator.mcwf_grover import (
    McwfGroverResult,
    compile_mcwf_grover_program,
    simulate_mcwf_qutrit_grover_leakage,
)
from qec_twin.simulator.mcwf_program import (
    CompiledMcwfProgram,
    McwfAllOnesPhaseOp,
    McwfCachedQubitGateOp,
    McwfKrausAllSitesOp,
    McwfQubitGateOp,
)
from qec_twin.simulator.mcwf_backend import (
    DenseQutritMcwfBackend,
    QutritMcwfMeasurementBatch,
)
from qec_twin.simulator.mcwf_executor import (
    BlockTrajectoryMcwfExecutor,
    DenseQutritMcwfExecutor,
    GraphCapturedMcwfExecutor,
    McwfExecutionResult,
    McwfExecutionTiming,
    NativeOpStreamMcwfExecutor,
)
from qec_twin.simulator.noise_spec import (
    NoiseBuilder,
    StimNoiseRule,
    StimPauliNoiseSpec,
    TargetedStimNoiseSpec,
    apply_stim_pauli_noise,
)
from qec_twin.simulator.noise import (
    Noise,
    depolarizing_noise,
    no_noise,
    targeted_noise,
)
from qec_twin.simulator.operation import OperationSet, OperationSpec, default_memory_operations
from qec_twin.simulator.qutrit_leakage import (
    QutritLeakageResult,
    index_from_qutrit_string,
    qutrit_string_from_index,
    simulate_qutrit_wg_leakage,
)
from qec_twin.simulator.ququart_transport import (
    QuquartTransportResult,
    index_from_ququart_string,
    ququart_string_from_index,
    simulate_ququart_transport_smoke,
)
from qec_twin.simulator.qutip_cuquantum_backend import (
    QutipCuQuantumLocalMcwfProbeResult,
    QutipCuQuantumSymbolicCollapseSummary,
    local_qutrit_operator_qobj,
    probe_qutip_cuquantum_local_mcwf,
    qutip_cuquantum_symbolic_collapse_summary,
    wg_seep_collapse_matrix,
    zero_hamiltonian_qobj,
)
from qec_twin.simulator.record_layout import (
    RecordLayout,
    build_repeated_memory_record_layout,
)
from qec_twin.simulator.record_schema import RecordSchema
from qec_twin.simulator.schedule import (
    ScheduleTemplate,
    repeated_memory_schedule,
    resolve_schedule_template,
)
from qec_twin.simulator.simulator import SimulationResult, Simulator, simulate_noiseless
from qec_twin.simulator.stim_source import (
    CircuitIRSource,
    CompiledCircuit,
    CompiledCircuitSource,
    StimCircuitSource,
)
from qec_twin.simulator.xzzx_code import XZZXCodeSpec, make_xzzx_3x3_compiler_smoke_spec

__all__ = [
    "CircuitBuilder",
    "CircuitIRSource",
    "CircuitIR",
    "CodeQubit",
    "CodeSpec",
    "BlockTrajectoryMcwfExecutor",
    "CompiledMcwfProgram",
    "CompiledCircuit",
    "CompiledCircuitSource",
    "CudaQGroverResult",
    "DenseQutritMcwfBackend",
    "DenseQutritMcwfExecutor",
    "DetectorDef",
    "GateOp",
    "GraphCapturedMcwfExecutor",
    "LogicalObservableSpec",
    "MeasureOp",
    "McwfGroverResult",
    "McwfExecutionResult",
    "McwfExecutionTiming",
    "NativeOpStreamMcwfExecutor",
    "Noise",
    "NoiseBuilder",
    "McwfAllOnesPhaseOp",
    "McwfCachedQubitGateOp",
    "McwfKrausAllSitesOp",
    "McwfQubitGateOp",
    "OperationSet",
    "OperationSpec",
    "ObservableDef",
    "PauliTerm",
    "QutritLeakageResult",
    "QutritMcwfMeasurementBatch",
    "QutipCuQuantumLocalMcwfProbeResult",
    "QutipCuQuantumSymbolicCollapseSummary",
    "QuquartTransportResult",
    "RecordLayout",
    "RecordSchema",
    "ScheduleTemplate",
    "SimulationResult",
    "Simulator",
    "StabilizerCheck",
    "StimPauliNoiseSpec",
    "StimNoiseRule",
    "StimCircuitSource",
    "TargetedStimNoiseSpec",
    "Tick",
    "apply_stim_pauli_noise",
    "depolarizing_noise",
    "no_noise",
    "targeted_noise",
    "XZZXCodeSpec",
    "build_repeated_memory_record_layout",
    "build_cudaq_grover_kernel",
    "compile_mcwf_grover_program",
    "compile_code_spec",
    "compile_code_spec_to_compiled",
    "default_memory_operations",
    "index_from_qutrit_string",
    "index_from_ququart_string",
    "local_qutrit_operator_qobj",
    "make_xzzx_3x3_compiler_smoke_spec",
    "probe_qutip_cuquantum_local_mcwf",
    "qutip_cuquantum_symbolic_collapse_summary",
    "qutrit_string_from_index",
    "ququart_string_from_index",
    "repeated_memory_schedule",
    "resolve_schedule_template",
    "simulate_noiseless",
    "simulate_cudaq_grover_noiseless",
    "simulate_mcwf_qutrit_grover_leakage",
    "simulate_qutrit_wg_leakage",
    "simulate_ququart_transport_smoke",
    "wg_seep_collapse_matrix",
    "zero_hamiltonian_qobj",
]
