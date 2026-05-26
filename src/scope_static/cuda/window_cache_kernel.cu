#include <torch/extension.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAException.h>
#include <c10/cuda/CUDAGuard.h>

__device__ inline void atomic_add_i64(int64_t* address, int64_t value) {
  atomicAdd(reinterpret_cast<unsigned long long int*>(address), static_cast<unsigned long long int>(value));
}

__global__ void window_state_histogram_kernel(
    const bool* __restrict__ observations,
    const int64_t num_observations,
    const int64_t num_observation_bits,
    const int64_t* __restrict__ flat_window_bits,
    const int64_t* __restrict__ window_offsets,
    const int64_t* __restrict__ window_num_bits,
    const int64_t max_state_count,
    int64_t* __restrict__ dense_counts) {
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t shot = static_cast<int64_t>(blockIdx.y) * blockDim.x + threadIdx.x;
  if (shot >= num_observations) {
    return;
  }

  const int64_t bit_begin = window_offsets[window];
  const int64_t num_bits = window_num_bits[window];
  int64_t state = 0;
  for (int64_t local = 0; local < num_bits; ++local) {
    const int64_t bit = flat_window_bits[bit_begin + local];
    if (observations[shot * num_observation_bits + bit]) {
      state |= int64_t{1} << local;
    }
  }
  atomic_add_i64(dense_counts + window * max_state_count + state, 1);
}

__global__ void compact_window_counts_kernel(
    const int64_t* __restrict__ dense_counts,
    const int64_t* __restrict__ active_prefix,
    const int64_t* __restrict__ state_offsets,
    const int64_t window_count,
    const int64_t max_state_count,
    int64_t* __restrict__ flat_states,
    int64_t* __restrict__ flat_counts) {
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t state = static_cast<int64_t>(blockIdx.y) * blockDim.x + threadIdx.x;
  if (window >= window_count || state >= max_state_count) {
    return;
  }
  const int64_t index = window * max_state_count + state;
  const int64_t count = dense_counts[index];
  if (count == 0) {
    return;
  }
  const int64_t flat_index = state_offsets[window] + active_prefix[index] - 1;
  flat_states[flat_index] = state;
  flat_counts[flat_index] = count;
}

std::tuple<torch::Tensor, torch::Tensor, torch::Tensor> window_observation_state_counts_cuda(
    torch::Tensor observations,
    torch::Tensor flat_window_bits,
    torch::Tensor window_offsets,
    torch::Tensor window_num_bits,
    int64_t max_state_count) {
  const c10::cuda::CUDAGuard device_guard(observations.device());
  const int64_t num_observations = observations.size(0);
  const int64_t num_observation_bits = observations.size(1);
  const int64_t window_count = window_num_bits.size(0);
  auto options = torch::TensorOptions().dtype(torch::kInt64).device(observations.device());
  auto dense_counts = torch::zeros({window_count, max_state_count}, options);

  cudaStream_t stream = at::cuda::getCurrentCUDAStream();
  const int threads = 256;
  if (num_observations > 0 && window_count > 0) {
    const dim3 blocks(
        static_cast<unsigned int>(window_count),
        static_cast<unsigned int>((num_observations + threads - 1) / threads));
    window_state_histogram_kernel<<<blocks, threads, 0, stream>>>(
        observations.data_ptr<bool>(),
        num_observations,
        num_observation_bits,
        flat_window_bits.data_ptr<int64_t>(),
        window_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        max_state_count,
        dense_counts.data_ptr<int64_t>());
    C10_CUDA_KERNEL_LAUNCH_CHECK();
  }

  auto active = dense_counts.ne(0).to(torch::kInt64);
  auto per_window = active.sum(1);
  auto state_offsets = torch::cat({torch::zeros({1}, options), torch::cumsum(per_window, 0)});
  const int64_t total_active_states = state_offsets.index({window_count}).item<int64_t>();
  auto flat_states = torch::empty({total_active_states}, options);
  auto flat_counts = torch::empty({total_active_states}, options);
  if (total_active_states > 0) {
    auto active_prefix = torch::cumsum(active, 1).contiguous();
    const dim3 compact_blocks(
        static_cast<unsigned int>(window_count),
        static_cast<unsigned int>((max_state_count + threads - 1) / threads));
    compact_window_counts_kernel<<<compact_blocks, threads, 0, stream>>>(
        dense_counts.data_ptr<int64_t>(),
        active_prefix.data_ptr<int64_t>(),
        state_offsets.data_ptr<int64_t>(),
        window_count,
        max_state_count,
        flat_states.data_ptr<int64_t>(),
        flat_counts.data_ptr<int64_t>());
    C10_CUDA_KERNEL_LAUNCH_CHECK();
  }

  return std::make_tuple(flat_states, flat_counts, state_offsets);
}
