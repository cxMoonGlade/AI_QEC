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
std::tuple<torch::Tensor, torch::Tensor> local_window_nll_value_and_grad_cuda(
    torch::Tensor logits,
    torch::Tensor flat_fault_ids,
    torch::Tensor flat_masks,
    torch::Tensor fault_offsets,
    torch::Tensor flat_states,
    torch::Tensor flat_counts,
    torch::Tensor state_offsets,
    torch::Tensor window_num_bits,
    int64_t max_faults_per_window,
    int64_t max_state_count);

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

void check_local_window_inputs(
    const torch::Tensor& logits,
    const torch::Tensor& flat_fault_ids,
    const torch::Tensor& flat_masks,
    const torch::Tensor& fault_offsets,
    const torch::Tensor& flat_states,
    const torch::Tensor& flat_counts,
    const torch::Tensor& state_offsets,
    const torch::Tensor& window_num_bits,
    int64_t max_faults_per_window,
    int64_t max_state_count) {
  TORCH_CHECK(logits.is_cuda(), "logits must be a CUDA tensor");
  TORCH_CHECK(flat_fault_ids.is_cuda(), "flat_fault_ids must be a CUDA tensor");
  TORCH_CHECK(flat_masks.is_cuda(), "flat_masks must be a CUDA tensor");
  TORCH_CHECK(fault_offsets.is_cuda(), "fault_offsets must be a CUDA tensor");
  TORCH_CHECK(flat_states.is_cuda(), "flat_states must be a CUDA tensor");
  TORCH_CHECK(flat_counts.is_cuda(), "flat_counts must be a CUDA tensor");
  TORCH_CHECK(state_offsets.is_cuda(), "state_offsets must be a CUDA tensor");
  TORCH_CHECK(window_num_bits.is_cuda(), "window_num_bits must be a CUDA tensor");
  TORCH_CHECK(logits.dim() == 1, "logits must be rank-1");
  TORCH_CHECK(flat_fault_ids.dim() == 1, "flat_fault_ids must be rank-1");
  TORCH_CHECK(flat_masks.dim() == 1, "flat_masks must be rank-1");
  TORCH_CHECK(fault_offsets.dim() == 1, "fault_offsets must be rank-1");
  TORCH_CHECK(flat_states.dim() == 1, "flat_states must be rank-1");
  TORCH_CHECK(flat_counts.dim() == 1, "flat_counts must be rank-1");
  TORCH_CHECK(state_offsets.dim() == 1, "state_offsets must be rank-1");
  TORCH_CHECK(window_num_bits.dim() == 1, "window_num_bits must be rank-1");
  TORCH_CHECK(flat_fault_ids.size(0) == flat_masks.size(0), "flat_fault_ids and flat_masks must agree");
  TORCH_CHECK(flat_states.size(0) == flat_counts.size(0), "flat_states and flat_counts must agree");
  TORCH_CHECK(fault_offsets.size(0) == window_num_bits.size(0) + 1, "fault_offsets must have W + 1 entries");
  TORCH_CHECK(state_offsets.size(0) == window_num_bits.size(0) + 1, "state_offsets must have W + 1 entries");
  TORCH_CHECK(logits.is_floating_point(), "logits must be floating point");
  TORCH_CHECK(flat_fault_ids.scalar_type() == torch::kInt64, "flat_fault_ids must have dtype int64");
  TORCH_CHECK(flat_masks.scalar_type() == torch::kInt64, "flat_masks must have dtype int64");
  TORCH_CHECK(fault_offsets.scalar_type() == torch::kInt64, "fault_offsets must have dtype int64");
  TORCH_CHECK(flat_states.scalar_type() == torch::kInt64, "flat_states must have dtype int64");
  TORCH_CHECK(flat_counts.scalar_type() == torch::kInt64, "flat_counts must have dtype int64");
  TORCH_CHECK(state_offsets.scalar_type() == torch::kInt64, "state_offsets must have dtype int64");
  TORCH_CHECK(window_num_bits.scalar_type() == torch::kInt64, "window_num_bits must have dtype int64");
  TORCH_CHECK(max_faults_per_window >= 0, "max_faults_per_window must be non-negative");
  TORCH_CHECK(max_state_count > 0, "max_state_count must be positive");
}

std::tuple<torch::Tensor, torch::Tensor> local_window_nll_value_and_grad(
    torch::Tensor logits,
    torch::Tensor flat_fault_ids,
    torch::Tensor flat_masks,
    torch::Tensor fault_offsets,
    torch::Tensor flat_states,
    torch::Tensor flat_counts,
    torch::Tensor state_offsets,
    torch::Tensor window_num_bits,
    int64_t max_faults_per_window,
    int64_t max_state_count) {
  check_local_window_inputs(
      logits,
      flat_fault_ids,
      flat_masks,
      fault_offsets,
      flat_states,
      flat_counts,
      state_offsets,
      window_num_bits,
      max_faults_per_window,
      max_state_count);
  return local_window_nll_value_and_grad_cuda(
      logits.contiguous(),
      flat_fault_ids.contiguous(),
      flat_masks.contiguous(),
      fault_offsets.contiguous(),
      flat_states.contiguous(),
      flat_counts.contiguous(),
      state_offsets.contiguous(),
      window_num_bits.contiguous(),
      max_faults_per_window,
      max_state_count);
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
  m.def(
      "local_window_nll_value_and_grad",
      &local_window_nll_value_and_grad,
      "Batched exact local-window NLL value and first-order gradient (CUDA)");
}
