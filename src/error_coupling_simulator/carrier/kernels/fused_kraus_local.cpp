// Python binding for the fused subsystem-Kraus CUDA kernel (see fused_kraus_local.cu).

#include <torch/extension.h>

#include <vector>

torch::Tensor fused_local_kraus_cuda(
    torch::Tensor rho, torch::Tensor kraus, std::vector<int64_t> targets, int64_t n);

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def(
      "fused_local_kraus",
      &fused_local_kraus_cuda,
      "Fused subsystem Kraus application (raw sum; CUDA, complex128)",
      pybind11::arg("rho"),
      pybind11::arg("kraus"),
      pybind11::arg("targets"),
      pybind11::arg("n"));
}
