#include <torch/extension.h>

torch::Tensor dem_parity_distribution_cuda(torch::Tensor logits, torch::Tensor masks, int64_t num_bits);
std::tuple<torch::Tensor, torch::Tensor, torch::Tensor> dem_parity_distribution_forward_with_history_cuda(
    torch::Tensor logits,
    torch::Tensor masks,
    int64_t num_bits);
torch::Tensor dem_parity_distribution_backward_cuda(
    torch::Tensor grad_output,
    torch::Tensor history,
    torch::Tensor probabilities,
    torch::Tensor masks,
    int64_t num_bits);

void check_forward_inputs(const torch::Tensor& logits, const torch::Tensor& masks, int64_t num_bits) {
  TORCH_CHECK(logits.is_cuda(), "logits must be a CUDA tensor");
  TORCH_CHECK(masks.is_cuda(), "masks must be a CUDA tensor");
  TORCH_CHECK(logits.device() == masks.device(), "logits and masks must be on the same CUDA device");
  TORCH_CHECK(logits.dim() == 1, "logits must be rank-1");
  TORCH_CHECK(masks.dim() == 1, "masks must be rank-1");
  TORCH_CHECK(logits.size(0) == masks.size(0), "logits and masks must agree on M");
  TORCH_CHECK(logits.is_floating_point(), "logits must be floating point");
  TORCH_CHECK(masks.scalar_type() == torch::kInt64, "masks must have dtype int64");
  TORCH_CHECK(num_bits >= 0 && num_bits < 63, "num_bits must be in [0, 63)");
}

torch::Tensor dem_parity_distribution(torch::Tensor logits, torch::Tensor masks, int64_t num_bits) {
  check_forward_inputs(logits, masks, num_bits);
  return dem_parity_distribution_cuda(logits.contiguous(), masks.contiguous(), num_bits);
}

std::tuple<torch::Tensor, torch::Tensor, torch::Tensor> dem_parity_distribution_forward_with_history(
    torch::Tensor logits,
    torch::Tensor masks,
    int64_t num_bits) {
  check_forward_inputs(logits, masks, num_bits);
  return dem_parity_distribution_forward_with_history_cuda(logits.contiguous(), masks.contiguous(), num_bits);
}

torch::Tensor dem_parity_distribution_backward(
    torch::Tensor grad_output,
    torch::Tensor history,
    torch::Tensor probabilities,
    torch::Tensor masks,
    int64_t num_bits) {
  TORCH_CHECK(grad_output.is_cuda(), "grad_output must be a CUDA tensor");
  TORCH_CHECK(history.is_cuda(), "history must be a CUDA tensor");
  TORCH_CHECK(probabilities.is_cuda(), "probabilities must be a CUDA tensor");
  TORCH_CHECK(masks.is_cuda(), "masks must be a CUDA tensor");
  TORCH_CHECK(
      grad_output.device() == history.device() && grad_output.device() == probabilities.device() &&
          grad_output.device() == masks.device(),
      "all tensors must be on the same CUDA device");
  TORCH_CHECK(grad_output.dim() == 1, "grad_output must be rank-1");
  TORCH_CHECK(history.dim() == 2, "history must have shape [M + 1, 2^B]");
  TORCH_CHECK(probabilities.dim() == 1, "probabilities must be rank-1");
  TORCH_CHECK(masks.dim() == 1, "masks must be rank-1");
  TORCH_CHECK(probabilities.size(0) == masks.size(0), "probabilities and masks must agree on M");
  TORCH_CHECK(history.size(0) == probabilities.size(0) + 1, "history first dimension must be M + 1");
  TORCH_CHECK(num_bits >= 0 && num_bits < 63, "num_bits must be in [0, 63)");
  const int64_t state_count = int64_t{1} << num_bits;
  TORCH_CHECK(grad_output.size(0) == state_count, "grad_output must have shape [2^B]");
  TORCH_CHECK(history.size(1) == state_count, "history second dimension must be 2^B");
  TORCH_CHECK(grad_output.scalar_type() == probabilities.scalar_type(), "grad_output/probabilities dtype mismatch");
  TORCH_CHECK(grad_output.scalar_type() == history.scalar_type(), "grad_output/history dtype mismatch");
  TORCH_CHECK(masks.scalar_type() == torch::kInt64, "masks must have dtype int64");
  return dem_parity_distribution_backward_cuda(
      grad_output.contiguous(), history.contiguous(), probabilities.contiguous(), masks.contiguous(), num_bits);
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def("dem_parity_distribution", &dem_parity_distribution, "Exact DEM parity distribution (CUDA)");
  m.def(
      "dem_parity_distribution_forward_with_history",
      &dem_parity_distribution_forward_with_history,
      "Exact DEM parity distribution with DP history (CUDA)");
  m.def(
      "dem_parity_distribution_backward",
      &dem_parity_distribution_backward,
      "Adjoint gradient for exact DEM parity distribution (CUDA)");
}
