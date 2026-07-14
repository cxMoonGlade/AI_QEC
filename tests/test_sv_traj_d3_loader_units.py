"""CPU-only ABI guards for the fused d3 trajectory loader."""

from __future__ import annotations

import pytest
import torch

from _support.faithfulness import assert_raises_exact


def _call_kwargs(entrypoint: str) -> dict[str, object]:
    complex_dtype = torch.complex128
    common: dict[str, object] = {
        "codestate": torch.zeros(3 ** 9, dtype=complex_dtype),
        "R": 1,
        "gate_unitaries": torch.eye(3, dtype=complex_dtype).unsqueeze(0),
        "stab_supp_len": torch.tensor([1], dtype=torch.int32),
        "stab_supp": torch.tensor([[0]], dtype=torch.int32),
        "stab_supp_isx": torch.tensor([[0]], dtype=torch.int32),
        "log_supp": torch.tensor([0], dtype=torch.int32),
        "log_supp_isx": torch.tensor([0], dtype=torch.int32),
        "arm": 0,
        "b": 1.0,
        "readout_conv": 0,
        "logical_m": 0,
        "N": 1,
        "base_seed": 7,
        "shot_id_offset": 0,
        "wave": 1,
        "urandom": None,
        "urandom_stride": 0,
        "dtype": "c128",
    }
    if entrypoint == "sv_traj_d3":
        common.update({
            "round_gptr": torch.tensor([0, 1], dtype=torch.int32),
            "gate_uid": torch.tensor([0], dtype=torch.int32),
            "gate_site": torch.tensor([0], dtype=torch.int32),
            "kraus": torch.eye(3, dtype=complex_dtype).unsqueeze(0),
        })
    else:
        common.update({
            "round_op_ptr": torch.tensor([0, 1, 1], dtype=torch.int32),
            "op_kind": torch.tensor([0], dtype=torch.int32),
            "op_uid": torch.tensor([0], dtype=torch.int32),
            "op_site": torch.tensor([0], dtype=torch.int32),
            "leak_kraus": torch.eye(3, dtype=complex_dtype).unsqueeze(0),
        })
    return common


def _forbid_jit(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls: list[str] = []

    def forbidden(precision: str):
        calls.append(precision)
        pytest.fail("_load_ext was reached before ABI validation")

    monkeypatch.setattr(loader, "_load_ext", forbidden)
    return calls


def _support_kwargs() -> dict[str, object]:
    return {
        "stab_supp_len": torch.tensor([1], dtype=torch.int32),
        "stab_supp": torch.tensor([[0]], dtype=torch.int32),
        "stab_supp_isx": torch.tensor([[0]], dtype=torch.int32),
        "log_supp": torch.tensor([0], dtype=torch.int32),
        "log_supp_isx": torch.tensor([0], dtype=torch.int32),
        "codestate": None,
    }


def _shared_kwargs(kraus_name: str = "kraus") -> dict[str, object]:
    complex_dtype = torch.complex128
    values: dict[str, object] = {
        "precision": "c128",
        "codestate": torch.zeros(3 ** 9, dtype=complex_dtype),
        "R": 1,
        "N": 1,
        "arm": 0,
        "b": 1.0,
        "readout_conv": 0,
        "logical_m": 0,
        "shot_id_offset": 0,
        "wave": 1,
        "gate_unitaries": torch.eye(3, dtype=complex_dtype).unsqueeze(0),
        "kraus_name": kraus_name,
        "kraus": torch.eye(3, dtype=complex_dtype).unsqueeze(0),
        **_support_kwargs(),
        "urandom": None,
        "urandom_stride": 0,
    }
    values["codestate"] = torch.zeros(3 ** 9, dtype=complex_dtype)
    return values


def _assert_call_tuple(
    actual: tuple[object, ...], expected: tuple[object, ...],
) -> None:
    assert len(actual) == len(expected)
    for index, (got, want) in enumerate(zip(actual, expected, strict=True)):
        if isinstance(want, torch.Tensor):
            assert got is want, f"extension ABI argument {index} changed tensor identity"
        else:
            assert type(got) is type(want), f"extension ABI argument {index} changed type"
            assert got == want, f"extension ABI argument {index} changed value"


def _assert_keyword_call(
    actual: dict[str, object], expected: dict[str, object],
) -> None:
    assert list(actual) == list(expected)
    for name, want in expected.items():
        got = actual[name]
        if isinstance(want, torch.Tensor):
            assert got is want, f"validator field {name} changed tensor identity"
        else:
            assert type(got) is type(want), f"validator field {name} changed type"
            assert got == want, f"validator field {name} changed value"


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_cpu_input_is_rejected_before_jit(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls = _forbid_jit(monkeypatch)
    with pytest.raises(RuntimeError, match="codestate must be CUDA"):
        getattr(loader, entrypoint)(**_call_kwargs(entrypoint))
    assert calls == []


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_precision_mismatch_is_rejected_before_jit(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls = _forbid_jit(monkeypatch)
    kwargs = _call_kwargs(entrypoint)
    kwargs["dtype"] = "c64"
    with pytest.raises(TypeError, match="codestate.*complex64.*complex128"):
        getattr(loader, entrypoint)(**kwargs)
    assert calls == []


@pytest.mark.parametrize(
    ("entrypoint", "index_name"),
    [("sv_traj_d3", "round_gptr"), ("sv_traj_d3_wc", "round_op_ptr")],
)
def test_index_dtype_is_rejected_before_jit(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str, index_name: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls = _forbid_jit(monkeypatch)
    kwargs = _call_kwargs(entrypoint)
    kwargs[index_name] = kwargs[index_name].to(torch.int64)  # type: ignore[union-attr]
    with pytest.raises(TypeError, match=rf"{index_name}.*int32.*int64"):
        getattr(loader, entrypoint)(**kwargs)
    assert calls == []


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_complex_stack_shape_is_rejected_before_jit(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls = _forbid_jit(monkeypatch)
    kwargs = _call_kwargs(entrypoint)
    kwargs["gate_unitaries"] = torch.zeros((1, 2, 2), dtype=torch.complex128)
    with pytest.raises(ValueError, match=r"gate_unitaries.*\[K, 3, 3\]"):
        getattr(loader, entrypoint)(**kwargs)
    assert calls == []


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_scalar_contract_is_rejected_before_jit(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls = _forbid_jit(monkeypatch)
    kwargs = _call_kwargs(entrypoint)
    kwargs["wave"] = 0
    with pytest.raises(ValueError, match="wave must be >= 1"):
        getattr(loader, entrypoint)(**kwargs)
    assert calls == []


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_urandom_real_dtype_is_rejected_before_jit(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls = _forbid_jit(monkeypatch)
    kwargs = _call_kwargs(entrypoint)
    kwargs["urandom"] = torch.zeros((1, 1), dtype=torch.float32)
    kwargs["urandom_stride"] = 1
    with pytest.raises(TypeError, match="urandom.*float64.*float32"):
        getattr(loader, entrypoint)(**kwargs)
    assert calls == []


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_bad_csr_content_is_rejected_before_jit_under_device_mock(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls = _forbid_jit(monkeypatch)
    monkeypatch.setattr(loader, "_require_cuda_same_device", lambda *_args: None)
    kwargs = _call_kwargs(entrypoint)
    ptr_name = "round_gptr" if entrypoint == "sv_traj_d3" else "round_op_ptr"
    kwargs[ptr_name] = torch.zeros_like(kwargs[ptr_name])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="terminal entry must equal item count"):
        getattr(loader, entrypoint)(**kwargs)
    assert calls == []


def test_wc_leak_uid_is_not_treated_as_gate_table_index() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    loader._validate_wc_schedule_values(
        round_op_ptr=torch.tensor([0, 1, 1], dtype=torch.int32),
        op_kind=torch.tensor([1], dtype=torch.int32),
        op_uid=torch.tensor([2_147_483_647], dtype=torch.int32),
        op_site=torch.tensor([0], dtype=torch.int32),
        n_gate=1,
    )


def test_cuda_launchers_pin_codestate_device_and_stream() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    source = (loader._kernels_dir() / "sv_traj_d3.cu").read_text()
    assert source.count(
        "const c10::cuda::CUDAGuard device_guard(codestate.device());"
    ) == 2
    assert source.count(
        "at::cuda::getCurrentCUDAStream(codestate.get_device())"
    ) == 2


def test_available_forwards_loader_result(monkeypatch: pytest.MonkeyPatch) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    monkeypatch.setattr(loader, "_load_ext", lambda precision: object())
    assert loader.available("c64") is True
    monkeypatch.setattr(loader, "_load_ext", lambda precision: None)
    assert loader.available("c128") is False


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_valid_abi_forwards_to_bound_extension_without_hidden_casts(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls: list[tuple[object, ...]] = []

    class FakeExtension:
        def sv_traj_d3(self, *args):
            calls.append(args)
            return "lumped-ok"

        def sv_traj_d3_wc(self, *args):
            calls.append(args)
            return "within-cycle-ok"

    monkeypatch.setattr(loader, "_require_cuda_same_device", lambda *_args: None)
    monkeypatch.setattr(loader, "_load_ext", lambda _precision: FakeExtension())
    kwargs = _call_kwargs(entrypoint)

    expected = "lumped-ok" if entrypoint == "sv_traj_d3" else "within-cycle-ok"
    assert getattr(loader, entrypoint)(**kwargs) == expected
    assert calls[-1][-2].numel() == 0
    assert calls[-1][-2].dtype == torch.float64

    supplied = torch.full((1, 1), 0.25, dtype=torch.float64)
    kwargs["urandom"] = supplied
    kwargs["urandom_stride"] = 1
    assert getattr(loader, entrypoint)(**kwargs) == expected
    assert calls[-1][-2] is supplied


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_valid_abi_reports_intentionally_unavailable_kernel(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    monkeypatch.setattr(loader, "_require_cuda_same_device", lambda *_args: None)
    monkeypatch.setattr(loader, "_load_ext", lambda _precision: None)
    with pytest.raises(RuntimeError, match="kernel.*unavailable"):
        getattr(loader, entrypoint)(**_call_kwargs(entrypoint))


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_public_entrypoint_pins_every_validator_and_extension_abi_argument(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    kwargs = _call_kwargs(entrypoint)
    for name in ("codestate", "gate_unitaries", "kraus", "leak_kraus"):
        if name in kwargs:
            kwargs[name] = kwargs[name].to(torch.complex64)  # type: ignore[union-attr]
    kwargs.update({
        "arm": 3,
        "b": 0.375,
        "readout_conv": 1,
        "logical_m": 1,
        "base_seed": 913,
        "shot_id_offset": 19,
        "wave": 23,
        "urandom": torch.full((1, 4), 0.25, dtype=torch.float32),
        "urandom_stride": 4,
        "dtype": "c64",
    })

    precision_calls: list[str] = []
    structure_calls: list[dict[str, object]] = []
    shared_calls: list[dict[str, object]] = []
    device_calls: list[tuple[object, dict[str, object]]] = []
    value_calls: list[dict[str, object]] = []
    load_calls: list[str] = []
    extension_calls: list[tuple[object, ...]] = []

    def precision_spy(value: str):
        precision_calls.append(value)
        return torch.complex64, torch.float32

    def structure_spy(**values):
        structure_calls.append(values)

    def shared_spy(**values):
        shared_calls.append(values)
        return torch.complex64, torch.float32

    def device_spy(codestate, **values):
        device_calls.append((codestate, values))

    def value_spy(**values):
        value_calls.append(values)

    class FakeExtension:
        def sv_traj_d3(self, *args):
            extension_calls.append(args)
            return "lumped-exact"

        def sv_traj_d3_wc(self, *args):
            extension_calls.append(args)
            return "within-cycle-exact"

    def load_spy(precision: str):
        load_calls.append(precision)
        return FakeExtension()

    monkeypatch.setattr(loader, "_precision_dtypes", precision_spy)
    monkeypatch.setattr(loader, "_validate_shared_inputs", shared_spy)
    monkeypatch.setattr(loader, "_validate_schedule_devices", device_spy)
    monkeypatch.setattr(loader, "_load_ext", load_spy)
    if entrypoint == "sv_traj_d3":
        monkeypatch.setattr(loader, "_validate_lumped_schedule_structure", structure_spy)
        monkeypatch.setattr(loader, "_validate_lumped_schedule_values", value_spy)
    else:
        monkeypatch.setattr(loader, "_validate_wc_schedule_structure", structure_spy)
        monkeypatch.setattr(loader, "_validate_wc_schedule_values", value_spy)

    expected_result = "lumped-exact" if entrypoint == "sv_traj_d3" else "within-cycle-exact"
    assert getattr(loader, entrypoint)(**kwargs) == expected_result
    assert precision_calls == ["c64"]
    assert load_calls == ["c64"]

    if entrypoint == "sv_traj_d3":
        schedule_names = ("round_gptr", "gate_uid", "gate_site")
        kraus_name = "kraus"
    else:
        schedule_names = ("round_op_ptr", "op_kind", "op_uid", "op_site")
        kraus_name = "leak_kraus"

    _assert_keyword_call(
        structure_calls[0],
        {"R": kwargs["R"], **{name: kwargs[name] for name in schedule_names}},
    )
    _assert_keyword_call(
        shared_calls[0],
        {
            "precision": "c64",
            "codestate": kwargs["codestate"],
            "R": 1,
            "N": 1,
            "arm": 3,
            "b": 0.375,
            "readout_conv": 1,
            "logical_m": 1,
            "shot_id_offset": 19,
            "wave": 23,
            "gate_unitaries": kwargs["gate_unitaries"],
            "kraus_name": kraus_name,
            "kraus": kwargs[kraus_name],
            "stab_supp_len": kwargs["stab_supp_len"],
            "stab_supp": kwargs["stab_supp"],
            "stab_supp_isx": kwargs["stab_supp_isx"],
            "log_supp": kwargs["log_supp"],
            "log_supp_isx": kwargs["log_supp_isx"],
            "urandom": kwargs["urandom"],
            "urandom_stride": 4,
        },
    )
    assert device_calls[0][0] is kwargs["codestate"]
    _assert_keyword_call(
        device_calls[0][1], {name: kwargs[name] for name in schedule_names},
    )
    _assert_keyword_call(
        value_calls[0],
        {
            **{name: kwargs[name] for name in schedule_names},
            "n_gate": 1,
        },
    )

    common_extension = (
        kwargs["codestate"],
        1,
        *(kwargs[name] for name in schedule_names),
        kwargs["gate_unitaries"],
        kwargs["stab_supp_len"],
        kwargs["stab_supp"],
        kwargs["stab_supp_isx"],
        kwargs[kraus_name],
        kwargs["log_supp"],
        kwargs["log_supp_isx"],
        3,
        0.375,
        1,
        1,
        1,
        913,
        19,
        23,
        kwargs["urandom"],
        4,
    )
    _assert_call_tuple(extension_calls[0], common_extension)


@pytest.mark.parametrize("entrypoint", ["sv_traj_d3", "sv_traj_d3_wc"])
def test_omitted_public_defaults_are_exact_c128_kernel_defaults(
    monkeypatch: pytest.MonkeyPatch, entrypoint: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    kwargs = _call_kwargs(entrypoint)
    for name in ("shot_id_offset", "wave", "urandom", "urandom_stride", "dtype"):
        del kwargs[name]

    precision_calls: list[str] = []
    shared_calls: list[dict[str, object]] = []
    load_calls: list[str] = []
    extension_calls: list[tuple[object, ...]] = []

    monkeypatch.setattr(
        loader,
        "_precision_dtypes",
        lambda value: precision_calls.append(value) or (torch.complex128, torch.float64),
    )
    monkeypatch.setattr(loader, "_validate_lumped_schedule_structure", lambda **_kw: None)
    monkeypatch.setattr(loader, "_validate_wc_schedule_structure", lambda **_kw: None)
    monkeypatch.setattr(
        loader,
        "_validate_shared_inputs",
        lambda **values: shared_calls.append(values) or (torch.complex128, torch.float64),
    )
    monkeypatch.setattr(loader, "_validate_schedule_devices", lambda *_args, **_kw: None)
    monkeypatch.setattr(loader, "_validate_lumped_schedule_values", lambda **_kw: None)
    monkeypatch.setattr(loader, "_validate_wc_schedule_values", lambda **_kw: None)

    class FakeExtension:
        def sv_traj_d3(self, *args):
            extension_calls.append(args)
            return "ok"

        def sv_traj_d3_wc(self, *args):
            extension_calls.append(args)
            return "ok"

    def load_spy(precision: str):
        load_calls.append(precision)
        return FakeExtension()

    monkeypatch.setattr(loader, "_load_ext", load_spy)
    assert getattr(loader, entrypoint)(**kwargs) == "ok"
    assert precision_calls == ["c128"]
    assert load_calls == ["c128"]
    assert shared_calls[0]["precision"] == "c128"
    assert shared_calls[0]["shot_id_offset"] == 0
    assert shared_calls[0]["wave"] == 256
    assert shared_calls[0]["urandom"] is None
    assert shared_calls[0]["urandom_stride"] == 0

    forwarded = extension_calls[0]
    assert forwarded[-4] == 0
    assert forwarded[-3] == 256
    empty_rng = forwarded[-2]
    assert isinstance(empty_rng, torch.Tensor)
    assert empty_rng.numel() == 0
    assert empty_rng.dtype == torch.float64
    assert empty_rng.device == kwargs["codestate"].device  # type: ignore[union-attr]
    assert forwarded[-1] == 0


def test_available_default_precision_and_forwarding_are_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    calls: list[object] = []
    sentinel = object()
    monkeypatch.setattr(loader, "_load_ext", lambda precision: calls.append(precision) or sentinel)
    assert loader.available() is True
    assert calls == ["c128"]


def test_precision_and_primitive_validation_labels_are_exact() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    assert loader._precision_dtypes("c128") == (torch.complex128, torch.float64)
    assert loader._precision_dtypes("c64") == (torch.complex64, torch.float32)
    assert_raises_exact(
        ValueError,
        "precision must be 'c128' or 'c64' (got 'fp32')",
        lambda: loader._precision_dtypes("fp32"),
    )
    assert_raises_exact(
        TypeError,
        "codestate must be a torch.Tensor",
        lambda: loader._require_tensor("codestate", object()),
    )
    assert_raises_exact(
        ValueError,
        "round_gptr must be 1D (got shape (1, 1))",
        lambda: loader._require_1d(
            "round_gptr", torch.zeros((1, 1), dtype=torch.int32),
        ),
    )
    assert_raises_exact(
        ValueError,
        "gate_unitaries must have shape [K, 3, 3] with K >= 1 (got (0, 3, 3))",
        lambda: loader._require_complex_stack(
            "gate_unitaries", torch.zeros((0, 3, 3), dtype=torch.complex128),
            torch.complex128,
        ),
    )


def test_device_validation_labels_and_boundaries_are_exact() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    cpu = torch.zeros(1)
    assert_raises_exact(
        RuntimeError,
        "codestate must be CUDA",
        lambda: loader._require_cuda_same_device("codestate", cpu, cpu),
    )

    class FakeCudaTensor:
        def __init__(self, index: int):
            self.is_cuda = True
            self.device = torch.device(f"cuda:{index}")

    cuda0 = FakeCudaTensor(0)
    cuda1 = FakeCudaTensor(1)
    loader._require_cuda_same_device("gate_unitaries", cuda0, cuda0)  # type: ignore[arg-type]
    assert_raises_exact(
        RuntimeError,
        "gate_unitaries must be on cuda:0 (got cuda:1)",
        lambda: loader._require_cuda_same_device(  # type: ignore[arg-type]
            "gate_unitaries", cuda1, cuda0,
        ),
    )
    assert_raises_exact(
        RuntimeError,
        "stab_supp must be CPU or CUDA (got meta)",
        lambda: loader._require_host_copyable_index(
            "stab_supp", torch.empty(1, device="meta"),
        ),
    )
    loader._require_host_copyable_index("stab_supp", cpu, cuda0)  # type: ignore[arg-type]
    assert_raises_exact(
        RuntimeError,
        "stab_supp must be CPU or on cuda:0 (got cuda:1)",
        lambda: loader._require_host_copyable_index(  # type: ignore[arg-type]
            "stab_supp", cuda1, cuda0,
        ),
    )


def test_csr_validation_pins_empty_start_order_and_terminal_guards() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    assert_raises_exact(
        ValueError,
        "round_gptr must start at 0",
        lambda: loader._validate_csr(
            "round_gptr", torch.empty(0, dtype=torch.int32), 0,
        ),
    )
    assert_raises_exact(
        ValueError,
        "round_gptr must start at 0",
        lambda: loader._validate_csr(
            "round_gptr", torch.tensor([1, 1], dtype=torch.int32), 1,
        ),
    )
    assert_raises_exact(
        ValueError,
        "round_gptr must be nondecreasing",
        lambda: loader._validate_csr(
            "round_gptr", torch.tensor([0, 2, 1], dtype=torch.int32), 1,
        ),
    )
    assert_raises_exact(
        ValueError,
        "round_gptr terminal entry must equal item count 2 (got 1)",
        lambda: loader._validate_csr(
            "round_gptr", torch.tensor([0, 0, 1], dtype=torch.int32), 2,
        ),
    )
    loader._validate_csr(
        "round_gptr", torch.tensor([0, 0, 2], dtype=torch.int32), 2,
    )


@pytest.mark.parametrize(
    "field",
    ["stab_supp_len", "stab_supp", "stab_supp_isx", "log_supp", "log_supp_isx"],
)
def test_support_table_tensor_and_dtype_field_labels_are_exact(field: str) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    kwargs = _support_kwargs()
    kwargs[field] = object()
    assert_raises_exact(
        TypeError,
        f"{field} must be a torch.Tensor",
        lambda: loader._validate_support_tables(**kwargs),
    )

    kwargs = _support_kwargs()
    kwargs[field] = kwargs[field].to(torch.int64)  # type: ignore[union-attr]
    assert_raises_exact(
        TypeError,
        f"{field} must have dtype torch.int32 (got torch.int64)",
        lambda: loader._validate_support_tables(**kwargs),
    )


def test_support_table_host_copy_dispatch_pins_all_field_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    kwargs = _support_kwargs()
    codestate = object()
    kwargs["codestate"] = codestate
    calls: list[tuple[object, object, object]] = []
    monkeypatch.setattr(
        loader,
        "_require_host_copyable_index",
        lambda name, tensor, reference=None: calls.append((name, tensor, reference)),
    )
    loader._validate_support_tables(**kwargs)
    names = ("stab_supp_len", "stab_supp", "stab_supp_isx", "log_supp", "log_supp_isx")
    assert [call[0] for call in calls] == list(names)
    for call, name in zip(calls, names, strict=True):
        assert call[1] is kwargs[name]
        assert call[2] is codestate


def test_support_table_shape_and_capacity_guards_are_exact() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    cases: list[tuple[dict[str, object], str]] = []

    kwargs = _support_kwargs()
    kwargs["stab_supp_len"] = torch.tensor([[1]], dtype=torch.int32)
    cases.append((kwargs, "stab_supp_len must be 1D (got shape (1, 1))"))

    kwargs = _support_kwargs()
    kwargs.update({
        "stab_supp_len": torch.zeros(17, dtype=torch.int32),
        "stab_supp": torch.zeros((17, 1), dtype=torch.int32),
        "stab_supp_isx": torch.zeros((17, 1), dtype=torch.int32),
    })
    cases.append((kwargs, "stab_supp_len has 17 stabilizers; maximum is 16"))

    kwargs = _support_kwargs()
    kwargs["stab_supp"] = torch.zeros(1, dtype=torch.int32)
    cases.append((kwargs, "stab_supp must be 2D (got shape (1,))"))

    kwargs = _support_kwargs()
    kwargs["stab_supp"] = torch.zeros((2, 1), dtype=torch.int32)
    cases.append((kwargs, "stab_supp must have shape [n_stab, K] with K <= 8 (got (2, 1))"))

    kwargs = _support_kwargs()
    kwargs["stab_supp"] = torch.zeros((1, 9), dtype=torch.int32)
    cases.append((kwargs, "stab_supp must have shape [n_stab, K] with K <= 8 (got (1, 9))"))

    kwargs = _support_kwargs()
    kwargs["stab_supp_isx"] = torch.zeros((1, 2), dtype=torch.int32)
    cases.append((kwargs, "stab_supp_isx shape must equal stab_supp shape (got (1, 2) vs (1, 1))"))

    kwargs = _support_kwargs()
    kwargs["log_supp"] = torch.zeros((1, 1), dtype=torch.int32)
    cases.append((kwargs, "log_supp must be 1D (got shape (1, 1))"))

    kwargs = _support_kwargs()
    kwargs.update({
        "log_supp": torch.zeros(13, dtype=torch.int32),
        "log_supp_isx": torch.zeros(13, dtype=torch.int32),
    })
    cases.append((kwargs, "log_supp has 13 sites; maximum is 12"))

    kwargs = _support_kwargs()
    kwargs["log_supp_isx"] = torch.zeros(2, dtype=torch.int32)
    cases.append((kwargs, "log_supp_isx shape must equal log_supp shape (got (2,) vs (1,))"))

    for case, message in cases:
        assert_raises_exact(
            ValueError, message, lambda case=case: loader._validate_support_tables(**case),
        )

    maximum = {
        "stab_supp_len": torch.zeros(16, dtype=torch.int32),
        "stab_supp": torch.full((16, 8), 99, dtype=torch.int32),
        "stab_supp_isx": torch.full((16, 8), 99, dtype=torch.int32),
        "log_supp": torch.full((12,), 8, dtype=torch.int32),
        "log_supp_isx": torch.ones(12, dtype=torch.int32),
        "codestate": None,
    }
    loader._validate_support_tables(**maximum)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("stab_supp_len", -1, "stab_supp_len[0]=-1 is outside [0,1]"),
        ("stab_supp_len", 2, "stab_supp_len[0]=2 is outside [0,1]"),
        ("stab_supp", -1, "stab_supp[0,0]=-1 is outside [0,9)"),
        ("stab_supp", 9, "stab_supp[0,0]=9 is outside [0,9)"),
        ("stab_supp_isx", -1, "stab_supp_isx[0,0] must be 0 or 1"),
        ("stab_supp_isx", 2, "stab_supp_isx[0,0] must be 0 or 1"),
        ("log_supp", -1, "log_supp[0]=-1 is outside [0,9)"),
        ("log_supp", 9, "log_supp[0]=9 is outside [0,9)"),
        ("log_supp_isx", -1, "log_supp_isx[0] must be 0 or 1"),
        ("log_supp_isx", 2, "log_supp_isx[0] must be 0 or 1"),
    ],
)
def test_support_value_boundaries_and_labels_are_exact(
    field: str, value: int, message: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    kwargs = _support_kwargs()
    kwargs[field] = torch.tensor([value], dtype=torch.int32)
    if field in ("stab_supp", "stab_supp_isx"):
        kwargs[field] = kwargs[field].reshape(1, 1)  # type: ignore[union-attr]
    assert_raises_exact(
        ValueError, message, lambda: loader._validate_support_tables(**kwargs),
    )

    if field == "stab_supp_len":
        zero_length = _support_kwargs()
        zero_length["stab_supp_len"] = torch.tensor([0], dtype=torch.int32)
        zero_length["stab_supp"] = torch.tensor([[99]], dtype=torch.int32)
        zero_length["stab_supp_isx"] = torch.tensor([[99]], dtype=torch.int32)
        loader._validate_support_tables(**zero_length)


def test_urandom_none_and_empty_streams_skip_external_rng_validation() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    codestate = torch.zeros(3 ** 9, dtype=torch.complex128)
    loader._validate_urandom(
        None,
        expected_dtype=torch.float64,
        codestate=codestate,
        N=3,
        urandom_stride=0,
    )
    loader._validate_urandom(
        torch.empty((0, 7, 2), dtype=torch.int64),
        expected_dtype=torch.float64,
        codestate=codestate,
        N=3,
        urandom_stride=-4,
    )


def test_urandom_type_dtype_shape_and_device_guards_are_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    codestate = torch.zeros(3 ** 9, dtype=torch.complex128)
    common = {
        "expected_dtype": torch.float64,
        "codestate": codestate,
        "N": 2,
        "urandom_stride": 2,
    }
    assert_raises_exact(
        TypeError,
        "urandom must be a torch.Tensor",
        lambda: loader._validate_urandom(object(), **common),
    )
    assert_raises_exact(
        TypeError,
        "urandom must have dtype torch.float64 (got torch.float32)",
        lambda: loader._validate_urandom(torch.zeros((2, 2)), **common),
    )

    shape_cases = [
        (
            torch.zeros(4, dtype=torch.float64),
            4,
            2,
            "urandom must have shape [N, urandom_stride] with urandom_stride > 0 "
            "(got (4,), N=4, urandom_stride=2)",
        ),
        (
            torch.zeros((1, 2), dtype=torch.float64),
            2,
            2,
            "urandom must have shape [N, urandom_stride] with urandom_stride > 0 "
            "(got (1, 2), N=2, urandom_stride=2)",
        ),
        (
            torch.zeros((2, 2), dtype=torch.float64),
            2,
            0,
            "urandom must have shape [N, urandom_stride] with urandom_stride > 0 "
            "(got (2, 2), N=2, urandom_stride=0)",
        ),
        (
            torch.zeros((2, 3), dtype=torch.float64),
            2,
            2,
            "urandom must have shape [N, urandom_stride] with urandom_stride > 0 "
            "(got (2, 3), N=2, urandom_stride=2)",
        ),
    ]
    for stream, N, stride, message in shape_cases:
        assert_raises_exact(
            ValueError,
            message,
            lambda stream=stream, N=N, stride=stride: loader._validate_urandom(
                stream,
                expected_dtype=torch.float64,
                codestate=codestate,
                N=N,
                urandom_stride=stride,
            ),
        )

    valid = torch.zeros((2, 2), dtype=torch.float64)
    assert_raises_exact(
        RuntimeError,
        "urandom must be CUDA",
        lambda: loader._validate_urandom(valid, **common),
    )

    calls: list[tuple[object, object, object]] = []
    monkeypatch.setattr(
        loader,
        "_require_cuda_same_device",
        lambda name, tensor, reference: calls.append((name, tensor, reference)),
    )
    loader._validate_urandom(valid, **common)
    assert calls == [("urandom", valid, codestate)]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("R", 0, "R must be >= 1 (got 0)"),
        ("N", 0, "N must be >= 1 (got 0)"),
        ("arm", 4, "arm must be in {0,1,2,3} (got 4)"),
        ("b", -0.25, "b must be in [0,1] (got -0.25)"),
        ("b", 1.25, "b must be in [0,1] (got 1.25)"),
        ("readout_conv", 2, "readout_conv must be 0 or 1 (got 2)"),
        ("logical_m", 2, "logical_m must be 0 or 1 (got 2)"),
        ("shot_id_offset", -1, "shot_id_offset must be >= 0 (got -1)"),
        ("wave", 0, "wave must be >= 1 (got 0)"),
    ],
)
def test_shared_scalar_guards_are_exact(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object, message: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    monkeypatch.setattr(loader, "_require_cuda_same_device", lambda *_args: None)
    kwargs = _shared_kwargs()
    kwargs[field] = value
    assert_raises_exact(
        ValueError, message, lambda: loader._validate_shared_inputs(**kwargs),
    )


def test_shared_codestate_gate_and_kraus_contract_labels_are_exact() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    kwargs = _shared_kwargs()
    kwargs["codestate"] = object()
    assert_raises_exact(
        TypeError,
        "codestate must be a torch.Tensor",
        lambda: loader._validate_shared_inputs(**kwargs),
    )

    kwargs = _shared_kwargs()
    kwargs["codestate"] = kwargs["codestate"].to(torch.complex64)  # type: ignore[union-attr]
    assert_raises_exact(
        TypeError,
        "codestate must have dtype torch.complex128 (got torch.complex64)",
        lambda: loader._validate_shared_inputs(**kwargs),
    )

    for shape in ((3 ** 9, 1), (3 ** 9 - 1,)):
        kwargs = _shared_kwargs()
        kwargs["codestate"] = torch.zeros(shape, dtype=torch.complex128)
        assert_raises_exact(
            ValueError,
            f"codestate must have shape [19683] (got {shape})",
            lambda kwargs=kwargs: loader._validate_shared_inputs(**kwargs),
        )

    kwargs = _shared_kwargs()
    kwargs["gate_unitaries"] = object()
    assert_raises_exact(
        TypeError,
        "gate_unitaries must be a torch.Tensor",
        lambda: loader._validate_shared_inputs(**kwargs),
    )

    kwargs = _shared_kwargs()
    kwargs["gate_unitaries"] = torch.zeros((0, 3, 3), dtype=torch.complex128)
    assert_raises_exact(
        ValueError,
        "gate_unitaries must have shape [K, 3, 3] with K >= 1 (got (0, 3, 3))",
        lambda: loader._validate_shared_inputs(**kwargs),
    )

    for kraus_name in ("kraus", "leak_kraus"):
        kwargs = _shared_kwargs(kraus_name)
        kwargs["kraus"] = object()
        assert_raises_exact(
            TypeError,
            f"{kraus_name} must be a torch.Tensor",
            lambda kwargs=kwargs: loader._validate_shared_inputs(**kwargs),
        )

        kwargs = _shared_kwargs(kraus_name)
        kwargs["kraus"] = torch.eye(3, dtype=torch.complex128).repeat(9, 1, 1)
        assert_raises_exact(
            ValueError,
            f"{kraus_name} has 9 operators; maximum is 8",
            lambda kwargs=kwargs: loader._validate_shared_inputs(**kwargs),
        )


def test_shared_scalar_and_kraus_capacity_boundaries_are_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    monkeypatch.setattr(loader, "_require_cuda_same_device", lambda *_args: None)
    for arm in (0, 1, 2, 3):
        kwargs = _shared_kwargs()
        kwargs["arm"] = arm
        assert loader._validate_shared_inputs(**kwargs) == (
            torch.complex128, torch.float64,
        )
    for field, values in (
        ("b", (0.0, 1.0)),
        ("readout_conv", (0, 1)),
        ("logical_m", (0, 1)),
    ):
        for value in values:
            kwargs = _shared_kwargs()
            kwargs[field] = value
            loader._validate_shared_inputs(**kwargs)

    kwargs = _shared_kwargs()
    kwargs["kraus"] = torch.eye(3, dtype=torch.complex128).repeat(8, 1, 1)
    loader._validate_shared_inputs(**kwargs)


def test_shared_validator_dispatch_pins_every_dependency_argument(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    kwargs = _shared_kwargs("leak_kraus")
    urandom = object()
    kwargs["urandom"] = urandom
    kwargs["urandom_stride"] = 11
    support_calls: list[dict[str, object]] = []
    urandom_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    cuda_calls: list[tuple[object, object, object]] = []
    monkeypatch.setattr(
        loader, "_validate_support_tables", lambda **values: support_calls.append(values),
    )
    monkeypatch.setattr(
        loader,
        "_validate_urandom",
        lambda *args, **values: urandom_calls.append((args, values)),
    )
    monkeypatch.setattr(
        loader,
        "_require_cuda_same_device",
        lambda name, tensor, reference: cuda_calls.append((name, tensor, reference)),
    )
    assert loader._validate_shared_inputs(**kwargs) == (
        torch.complex128, torch.float64,
    )
    _assert_keyword_call(
        support_calls[0],
        {
            "stab_supp_len": kwargs["stab_supp_len"],
            "stab_supp": kwargs["stab_supp"],
            "stab_supp_isx": kwargs["stab_supp_isx"],
            "log_supp": kwargs["log_supp"],
            "log_supp_isx": kwargs["log_supp_isx"],
            "codestate": kwargs["codestate"],
        },
    )
    assert urandom_calls[0][0] == (urandom,)
    _assert_keyword_call(
        urandom_calls[0][1],
        {
            "expected_dtype": torch.float64,
            "codestate": kwargs["codestate"],
            "N": 1,
            "urandom_stride": 11,
        },
    )
    assert [call[0] for call in cuda_calls] == [
        "codestate", "gate_unitaries", "leak_kraus",
    ]
    assert cuda_calls[0][1] is kwargs["codestate"]
    assert cuda_calls[0][2] is kwargs["codestate"]
    assert cuda_calls[1][1] is kwargs["gate_unitaries"]
    assert cuda_calls[1][2] is kwargs["codestate"]
    assert cuda_calls[2][1] is kwargs["kraus"]
    assert cuda_calls[2][2] is kwargs["codestate"]


@pytest.mark.parametrize(
    ("helper_name", "fields"),
    [
        (
            "_validate_lumped_schedule_structure",
            ("round_gptr", "gate_uid", "gate_site"),
        ),
        (
            "_validate_wc_schedule_structure",
            ("round_op_ptr", "op_kind", "op_uid", "op_site"),
        ),
    ],
)
def test_schedule_structure_field_type_dtype_and_dimension_labels_are_exact(
    helper_name: str, fields: tuple[str, ...],
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    if helper_name == "_validate_lumped_schedule_structure":
        base = {
            "R": 1,
            "round_gptr": torch.tensor([0, 1], dtype=torch.int32),
            "gate_uid": torch.tensor([0], dtype=torch.int32),
            "gate_site": torch.tensor([0], dtype=torch.int32),
        }
    else:
        base = {
            "R": 1,
            "round_op_ptr": torch.tensor([0, 1, 1], dtype=torch.int32),
            "op_kind": torch.tensor([0], dtype=torch.int32),
            "op_uid": torch.tensor([0], dtype=torch.int32),
            "op_site": torch.tensor([0], dtype=torch.int32),
        }
    helper = getattr(loader, helper_name)
    for field in fields:
        kwargs = dict(base)
        kwargs[field] = object()
        assert_raises_exact(
            TypeError,
            f"{field} must be a torch.Tensor",
            lambda kwargs=kwargs: helper(**kwargs),
        )

        kwargs = dict(base)
        kwargs[field] = kwargs[field].to(torch.int64)  # type: ignore[union-attr]
        assert_raises_exact(
            TypeError,
            f"{field} must have dtype torch.int32 (got torch.int64)",
            lambda kwargs=kwargs: helper(**kwargs),
        )

        kwargs = dict(base)
        kwargs[field] = kwargs[field].reshape(1, -1)  # type: ignore[union-attr]
        shape = tuple(kwargs[field].shape)  # type: ignore[union-attr]
        assert_raises_exact(
            ValueError,
            f"{field} must be 1D (got shape {shape})",
            lambda kwargs=kwargs: helper(**kwargs),
        )


def test_schedule_structure_pointer_and_parallel_length_guards_are_exact() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    assert_raises_exact(
        ValueError,
        "round_gptr must have shape [R+1] (got (3,), R=1)",
        lambda: loader._validate_lumped_schedule_structure(
            R=1,
            round_gptr=torch.tensor([0, 0, 1], dtype=torch.int32),
            gate_uid=torch.tensor([0], dtype=torch.int32),
            gate_site=torch.tensor([0], dtype=torch.int32),
        ),
    )
    assert_raises_exact(
        ValueError,
        "gate_uid and gate_site must have equal length (got 2 and 1)",
        lambda: loader._validate_lumped_schedule_structure(
            R=1,
            round_gptr=torch.tensor([0, 2], dtype=torch.int32),
            gate_uid=torch.tensor([0, 1], dtype=torch.int32),
            gate_site=torch.tensor([0], dtype=torch.int32),
        ),
    )
    assert_raises_exact(
        ValueError,
        "round_op_ptr must have shape [2R+1] (got (2,), R=1)",
        lambda: loader._validate_wc_schedule_structure(
            R=1,
            round_op_ptr=torch.tensor([0, 1], dtype=torch.int32),
            op_kind=torch.tensor([0], dtype=torch.int32),
            op_uid=torch.tensor([0], dtype=torch.int32),
            op_site=torch.tensor([0], dtype=torch.int32),
        ),
    )
    assert_raises_exact(
        ValueError,
        "op_kind, op_uid, and op_site must have equal length (got 2, 1, 1)",
        lambda: loader._validate_wc_schedule_structure(
            R=1,
            round_op_ptr=torch.tensor([0, 2, 2], dtype=torch.int32),
            op_kind=torch.tensor([0, 1], dtype=torch.int32),
            op_uid=torch.tensor([0], dtype=torch.int32),
            op_site=torch.tensor([0], dtype=torch.int32),
        ),
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("gate_uid", -1, "gate_uid[1]=-1 is outside [0,2)"),
        ("gate_uid", 2, "gate_uid[1]=2 is outside [0,2)"),
        ("gate_site", -1, "gate_site[1]=-1 is outside [0,9)"),
        ("gate_site", 9, "gate_site[1]=9 is outside [0,9)"),
    ],
)
def test_lumped_schedule_value_boundaries_and_offsets_are_exact(
    field: str, value: int, message: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    kwargs = {
        "round_gptr": torch.tensor([0, 2], dtype=torch.int32),
        "gate_uid": torch.tensor([0, 1], dtype=torch.int32),
        "gate_site": torch.tensor([0, 8], dtype=torch.int32),
        "n_gate": 2,
    }
    kwargs[field] = torch.tensor(
        [int(kwargs[field][0]), value], dtype=torch.int32,  # type: ignore[index]
    )
    assert_raises_exact(
        ValueError,
        message,
        lambda: loader._validate_lumped_schedule_values(**kwargs),
    )


def test_lumped_schedule_accepts_exact_uid_and_site_boundaries() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    loader._validate_lumped_schedule_values(
        round_gptr=torch.tensor([0, 0, 2], dtype=torch.int32),
        gate_uid=torch.tensor([0, 1], dtype=torch.int32),
        gate_site=torch.tensor([0, 8], dtype=torch.int32),
        n_gate=2,
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("op_kind", -1, "op_kind[2] must be 0 or 1 (got -1)"),
        ("op_kind", 2, "op_kind[2] must be 0 or 1 (got 2)"),
        ("op_uid", -1, "op_uid[2]=-1 is outside [0,2)"),
        ("op_uid", 2, "op_uid[2]=2 is outside [0,2)"),
        ("op_site", -1, "op_site[2]=-1 is outside [0,9)"),
        ("op_site", 9, "op_site[2]=9 is outside [0,9)"),
    ],
)
def test_wc_schedule_value_boundaries_and_offsets_are_exact(
    field: str, value: int, message: str,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    kwargs = {
        "round_op_ptr": torch.tensor([0, 3, 3], dtype=torch.int32),
        "op_kind": torch.tensor([0, 1, 0], dtype=torch.int32),
        "op_uid": torch.tensor([0, 2_147_483_647, 1], dtype=torch.int32),
        "op_site": torch.tensor([0, 4, 8], dtype=torch.int32),
        "n_gate": 2,
    }
    updated = kwargs[field].clone()  # type: ignore[union-attr]
    updated[2] = value
    kwargs[field] = updated
    assert_raises_exact(
        ValueError,
        message,
        lambda: loader._validate_wc_schedule_values(**kwargs),
    )


def test_wc_schedule_accepts_gate_leak_and_site_boundaries() -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    loader._validate_wc_schedule_values(
        round_op_ptr=torch.tensor([0, 0, 3], dtype=torch.int32),
        op_kind=torch.tensor([0, 1, 0], dtype=torch.int32),
        op_uid=torch.tensor([0, 2_147_483_647, 1], dtype=torch.int32),
        op_site=torch.tensor([0, 4, 8], dtype=torch.int32),
        n_gate=2,
    )


def test_schedule_device_dispatch_pins_field_names_order_and_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.carrier.kernels import sv_traj_d3_loader as loader

    codestate = object()
    values = {"round_op_ptr": object(), "op_kind": object(), "op_uid": object(), "op_site": object()}
    calls: list[tuple[object, object, object]] = []
    monkeypatch.setattr(
        loader,
        "_require_cuda_same_device",
        lambda name, tensor, reference: calls.append((name, tensor, reference)),
    )
    loader._validate_schedule_devices(codestate, **values)
    assert [call[0] for call in calls] == list(values)
    for call, (name, tensor) in zip(calls, values.items(), strict=True):
        assert call[0] == name
        assert call[1] is tensor
        assert call[2] is codestate
