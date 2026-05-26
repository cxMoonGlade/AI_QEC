#include <torch/extension.h>

std::tuple<torch::Tensor, torch::Tensor, torch::Tensor> window_observation_state_counts_cuda(
    torch::Tensor observations,
    torch::Tensor flat_window_bits,
    torch::Tensor window_offsets,
    torch::Tensor window_num_bits,
    int64_t max_state_count);

void check_window_cache_inputs(
    const torch::Tensor& observations,
    const torch::Tensor& flat_window_bits,
    const torch::Tensor& window_offsets,
    const torch::Tensor& window_num_bits,
    int64_t max_state_count) {
  TORCH_CHECK(observations.is_cuda(), "observations must be a CUDA tensor");
  TORCH_CHECK(flat_window_bits.is_cuda(), "flat_window_bits must be a CUDA tensor");
  TORCH_CHECK(window_offsets.is_cuda(), "window_offsets must be a CUDA tensor");
  TORCH_CHECK(window_num_bits.is_cuda(), "window_num_bits must be a CUDA tensor");
  TORCH_CHECK(
      observations.device() == flat_window_bits.device() && observations.device() == window_offsets.device() &&
          observations.device() == window_num_bits.device(),
      "all tensors must be on the same CUDA device");
  TORCH_CHECK(observations.dim() == 2, "observations must have shape [N, B]");
  TORCH_CHECK(flat_window_bits.dim() == 1, "flat_window_bits must be rank-1");
  TORCH_CHECK(window_offsets.dim() == 1, "window_offsets must be rank-1");
  TORCH_CHECK(window_num_bits.dim() == 1, "window_num_bits must be rank-1");
  TORCH_CHECK(observations.scalar_type() == torch::kBool, "observations must have dtype bool");
  TORCH_CHECK(flat_window_bits.scalar_type() == torch::kInt64, "flat_window_bits must have dtype int64");
  TORCH_CHECK(window_offsets.scalar_type() == torch::kInt64, "window_offsets must have dtype int64");
  TORCH_CHECK(window_num_bits.scalar_type() == torch::kInt64, "window_num_bits must have dtype int64");
  TORCH_CHECK(window_offsets.size(0) == window_num_bits.size(0) + 1, "window_offsets must have W + 1 entries");
  TORCH_CHECK(window_num_bits.size(0) > 0, "at least one window is required");
  TORCH_CHECK(max_state_count > 0, "max_state_count must be positive");
}

std::tuple<torch::Tensor, torch::Tensor, torch::Tensor> window_observation_state_counts(
    torch::Tensor observations,
    torch::Tensor flat_window_bits,
    torch::Tensor window_offsets,
    torch::Tensor window_num_bits,
    int64_t max_state_count) {
  check_window_cache_inputs(observations, flat_window_bits, window_offsets, window_num_bits, max_state_count);
  return window_observation_state_counts_cuda(
      observations.contiguous(),
      flat_window_bits.contiguous(),
      window_offsets.contiguous(),
      window_num_bits.contiguous(),
      max_state_count);
}
