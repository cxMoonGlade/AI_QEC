#include <torch/extension.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAException.h>
#include <cmath>
#include <c10/cuda/CUDAGuard.h>

__device__ inline bool parity_odd_i64(const int64_t value) {
  return (__popcll(static_cast<unsigned long long>(value)) & 1ULL) != 0ULL;
}

int threads_for_state_count(const int64_t state_count) {
  int threads = 32;
  while (threads < state_count && threads < 256) {
    threads <<= 1;
  }
  return threads;
}

__device__ inline void sync_active_state_threads(const int64_t state_count) {
  if (state_count > 32) {
    __syncthreads();
  } else {
    __syncwarp();
  }
}

__device__ inline void sync_reduction_threads() {
  if (blockDim.x > 32) {
    __syncthreads();
  } else {
    __syncwarp();
  }
}

template <typename scalar_t>
__device__ inline scalar_t likelihood_probability_floor();

template <>
__device__ inline float likelihood_probability_floor<float>() {
  return 1.0e-7f;
}

template <>
__device__ inline double likelihood_probability_floor<double>() {
  return 1.0e-12;
}

template <typename scalar_t>
__global__ void dem_step_kernel(
    const scalar_t* __restrict__ prev,
    scalar_t* __restrict__ next,
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ masks,
    const int64_t state_count,
    const int64_t fault) {
  const int64_t state = static_cast<int64_t>(blockIdx.x) * blockDim.x + threadIdx.x;
  if (state >= state_count) {
    return;
  }
  const scalar_t prob = probabilities[fault];
  const int64_t mask = masks[fault];
  next[state] = (static_cast<scalar_t>(1) - prob) * prev[state] + prob * prev[state ^ mask];
}

template <typename scalar_t>
__global__ void dem_backward_step_kernel(
    const scalar_t* __restrict__ grad_next,
    scalar_t* __restrict__ grad_prev,
    const scalar_t* __restrict__ q_prev,
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ masks,
    scalar_t* __restrict__ partials,
    const int64_t state_count,
    const int64_t fault) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* shared = reinterpret_cast<scalar_t*>(shared_raw);
  const int64_t state = static_cast<int64_t>(blockIdx.x) * blockDim.x + threadIdx.x;
  scalar_t dp_contribution = static_cast<scalar_t>(0);

  const scalar_t prob = probabilities[fault];
  const int64_t mask = masks[fault];
  if (state < state_count) {
    const int64_t xor_state = state ^ mask;
    const scalar_t grad_here = grad_next[state];
    dp_contribution = grad_here * (q_prev[xor_state] - q_prev[state]);
    grad_prev[state] =
        (static_cast<scalar_t>(1) - prob) * grad_here + prob * grad_next[xor_state];
  }

  shared[threadIdx.x] = dp_contribution;
  sync_reduction_threads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      shared[threadIdx.x] += shared[threadIdx.x + stride];
    }
    sync_reduction_threads();
  }
  if (threadIdx.x == 0) {
    partials[blockIdx.x] = shared[0];
  }
}

template <typename scalar_t>
__global__ void dem_finalize_logit_grad_kernel(
    const scalar_t* __restrict__ partials,
    const scalar_t* __restrict__ probabilities,
    scalar_t* __restrict__ grad_logits,
    const int64_t partial_count,
    const int64_t fault) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* shared = reinterpret_cast<scalar_t*>(shared_raw);
  scalar_t total = static_cast<scalar_t>(0);
  for (int64_t index = threadIdx.x; index < partial_count; index += blockDim.x) {
    total += partials[index];
  }

  shared[threadIdx.x] = total;
  sync_reduction_threads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      shared[threadIdx.x] += shared[threadIdx.x + stride];
    }
    sync_reduction_threads();
  }
  if (threadIdx.x == 0) {
    const scalar_t prob = probabilities[fault];
    grad_logits[fault] = shared[0] * prob * (static_cast<scalar_t>(1) - prob);
  }
}

torch::Tensor dem_parity_distribution_cuda(torch::Tensor logits, torch::Tensor masks, int64_t num_bits) {
  const c10::cuda::CUDAGuard device_guard(logits.device());
  const int64_t state_count = int64_t{1} << num_bits;
  auto probabilities = torch::sigmoid(logits).contiguous();
  auto current = torch::zeros({state_count}, logits.options());
  auto next = torch::empty_like(current);
  current.index_put_({0}, 1);

  const int threads = threads_for_state_count(state_count);
  const int blocks = static_cast<int>((state_count + threads - 1) / threads);
  cudaStream_t stream = at::cuda::getCurrentCUDAStream();

  AT_DISPATCH_FLOATING_TYPES(logits.scalar_type(), "dem_parity_distribution_cuda", [&] {
    for (int64_t fault = 0; fault < logits.size(0); ++fault) {
      dem_step_kernel<scalar_t><<<blocks, threads, 0, stream>>>(
          current.data_ptr<scalar_t>(),
          next.data_ptr<scalar_t>(),
          probabilities.data_ptr<scalar_t>(),
          masks.data_ptr<int64_t>(),
          state_count,
          fault);
      std::swap(current, next);
    }
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return current;
}

std::tuple<torch::Tensor, torch::Tensor, torch::Tensor> dem_parity_distribution_forward_with_history_cuda(
    torch::Tensor logits,
    torch::Tensor masks,
    int64_t num_bits) {
  const c10::cuda::CUDAGuard device_guard(logits.device());
  const int64_t state_count = int64_t{1} << num_bits;
  const int64_t fault_count = logits.size(0);
  auto probabilities = torch::sigmoid(logits).contiguous();
  auto history = torch::zeros({fault_count + 1, state_count}, logits.options());
  history.index_put_({0, 0}, 1);

  const int threads = threads_for_state_count(state_count);
  const int blocks = static_cast<int>((state_count + threads - 1) / threads);
  cudaStream_t stream = at::cuda::getCurrentCUDAStream();

  AT_DISPATCH_FLOATING_TYPES(logits.scalar_type(), "dem_parity_distribution_forward_with_history_cuda", [&] {
    for (int64_t fault = 0; fault < fault_count; ++fault) {
      auto prev = history.select(0, fault);
      auto next = history.select(0, fault + 1);
      dem_step_kernel<scalar_t><<<blocks, threads, 0, stream>>>(
          prev.data_ptr<scalar_t>(),
          next.data_ptr<scalar_t>(),
          probabilities.data_ptr<scalar_t>(),
          masks.data_ptr<int64_t>(),
          state_count,
          fault);
    }
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return std::make_tuple(history.select(0, fault_count), history, probabilities);
}

torch::Tensor dem_parity_distribution_backward_cuda(
    torch::Tensor grad_output,
    torch::Tensor history,
    torch::Tensor probabilities,
    torch::Tensor masks,
    int64_t num_bits) {
  const c10::cuda::CUDAGuard device_guard(grad_output.device());
  const int64_t state_count = int64_t{1} << num_bits;
  const int64_t fault_count = probabilities.size(0);
  auto grad_logits = torch::empty_like(probabilities);
  if (fault_count == 0) {
    return grad_logits;
  }

  auto grad_current = grad_output.contiguous();
  auto grad_previous = torch::empty_like(grad_current);
  const int threads = threads_for_state_count(state_count);
  const int blocks = static_cast<int>((state_count + threads - 1) / threads);
  auto partials = torch::empty({blocks}, grad_output.options());
  cudaStream_t stream = at::cuda::getCurrentCUDAStream();

  AT_DISPATCH_FLOATING_TYPES(grad_output.scalar_type(), "dem_parity_distribution_backward_cuda", [&] {
    const size_t shared_bytes = threads * sizeof(scalar_t);
    for (int64_t fault = fault_count - 1; fault >= 0; --fault) {
      auto q_prev = history.select(0, fault);
      dem_backward_step_kernel<scalar_t><<<blocks, threads, shared_bytes, stream>>>(
          grad_current.data_ptr<scalar_t>(),
          grad_previous.data_ptr<scalar_t>(),
          q_prev.data_ptr<scalar_t>(),
          probabilities.data_ptr<scalar_t>(),
          masks.data_ptr<int64_t>(),
          partials.data_ptr<scalar_t>(),
          state_count,
          fault);
      dem_finalize_logit_grad_kernel<scalar_t><<<1, threads, shared_bytes, stream>>>(
          partials.data_ptr<scalar_t>(),
          probabilities.data_ptr<scalar_t>(),
          grad_logits.data_ptr<scalar_t>(),
          blocks,
          fault);
      std::swap(grad_current, grad_previous);
    }
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return grad_logits;
}

template <typename scalar_t>
__global__ void local_window_forward_kernel(
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ flat_fault_ids,
    const int64_t* __restrict__ flat_masks,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ window_num_bits,
    scalar_t* __restrict__ history,
    const int64_t max_faults_per_window,
    const int64_t max_state_count) {
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t fault_count = fault_end - fault_begin;
  const int64_t num_bits = window_num_bits[window];
  const int64_t state_count = int64_t{1} << num_bits;
  scalar_t* window_history = history + window * (max_faults_per_window + 1) * max_state_count;

  for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
    window_history[state] = state == 0 ? static_cast<scalar_t>(1) : static_cast<scalar_t>(0);
  }
  sync_active_state_threads(state_count);

  for (int64_t local_fault = 0; local_fault < fault_count; ++local_fault) {
    const int64_t flat_index = fault_begin + local_fault;
    const int64_t global_fault = flat_fault_ids[flat_index];
    const int64_t mask = flat_masks[flat_index];
    const scalar_t prob = probabilities[global_fault];
    const scalar_t* prev = window_history + local_fault * max_state_count;
    scalar_t* next = window_history + (local_fault + 1) * max_state_count;
    for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
      next[state] = (static_cast<scalar_t>(1) - prob) * prev[state] + prob * prev[state ^ mask];
    }
    sync_active_state_threads(state_count);
  }
}

template <typename scalar_t>
__global__ void local_window_forward_shared_kernel(
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ flat_fault_ids,
    const int64_t* __restrict__ flat_masks,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ window_num_bits,
    scalar_t* __restrict__ history,
    const int64_t max_faults_per_window,
    const int64_t max_state_count) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* current = reinterpret_cast<scalar_t*>(shared_raw);
  scalar_t* next = current + max_state_count;

  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t fault_count = fault_end - fault_begin;
  const int64_t num_bits = window_num_bits[window];
  const int64_t state_count = int64_t{1} << num_bits;
  scalar_t* window_history = history + window * (max_faults_per_window + 1) * max_state_count;

  for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
    const scalar_t value = state == 0 ? static_cast<scalar_t>(1) : static_cast<scalar_t>(0);
    current[state] = value;
    window_history[state] = value;
  }
  sync_active_state_threads(state_count);

  for (int64_t local_fault = 0; local_fault < fault_count; ++local_fault) {
    const int64_t flat_index = fault_begin + local_fault;
    const int64_t global_fault = flat_fault_ids[flat_index];
    const int64_t mask = flat_masks[flat_index];
    const scalar_t prob = probabilities[global_fault];
    for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
      next[state] = (static_cast<scalar_t>(1) - prob) * current[state] + prob * current[state ^ mask];
    }
    sync_active_state_threads(state_count);

    scalar_t* next_history = window_history + (local_fault + 1) * max_state_count;
    for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
      next_history[state] = next[state];
    }
    scalar_t* tmp = current;
    current = next;
    next = tmp;
  }
}

template <typename scalar_t>
__global__ void local_window_loss_and_dist_grad_kernel(
    const scalar_t* __restrict__ history,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ flat_states,
    const int64_t* __restrict__ flat_counts,
    const int64_t* __restrict__ state_offsets,
    const int64_t* __restrict__ window_num_bits,
    const int64_t* __restrict__ window_total_counts,
    scalar_t* __restrict__ window_losses,
    scalar_t* __restrict__ grad_current,
    const int64_t window_count,
    const int64_t max_faults_per_window,
    const int64_t max_state_count) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* shared_loss = reinterpret_cast<scalar_t*>(shared_raw);
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t fault_count = fault_offsets[window + 1] - fault_offsets[window];
  const int64_t state_begin = state_offsets[window];
  const int64_t state_end = state_offsets[window + 1];
  const int64_t state_count = int64_t{1} << window_num_bits[window];
  const scalar_t* dist =
      history + (window * (max_faults_per_window + 1) + fault_count) * max_state_count;
  scalar_t* grad = grad_current + window * max_state_count;

  for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
    grad[state] = static_cast<scalar_t>(0);
  }
  sync_active_state_threads(state_count);

  const scalar_t total_count = static_cast<scalar_t>(window_total_counts[window]);
  if (total_count <= static_cast<scalar_t>(0)) {
    if (threadIdx.x == 0) {
      window_losses[window] = static_cast<scalar_t>(0);
    }
    return;
  }

  scalar_t loss_sum = static_cast<scalar_t>(0);
  const scalar_t tiny = likelihood_probability_floor<scalar_t>();
  for (int64_t index = state_begin + threadIdx.x; index < state_end; index += blockDim.x) {
    const int64_t state = flat_states[index];
    const scalar_t count = static_cast<scalar_t>(flat_counts[index]);
    const scalar_t prob = dist[state] > tiny ? dist[state] : tiny;
    loss_sum += -count * log(prob);
    atomicAdd(
        grad + state,
        -count / (total_count * static_cast<scalar_t>(window_count) * prob));
  }
  shared_loss[threadIdx.x] = loss_sum;
  sync_reduction_threads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      shared_loss[threadIdx.x] += shared_loss[threadIdx.x + stride];
    }
    sync_reduction_threads();
  }
  if (threadIdx.x == 0) {
    window_losses[window] = shared_loss[0] / total_count;
  }
}

template <typename scalar_t>
__global__ void local_window_backward_kernel(
    const scalar_t* __restrict__ history,
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ flat_fault_ids,
    const int64_t* __restrict__ flat_masks,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ window_num_bits,
    scalar_t* __restrict__ grad_current,
    scalar_t* __restrict__ grad_previous,
    scalar_t* __restrict__ grad_logits,
    const int64_t max_faults_per_window,
    const int64_t max_state_count) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* shared = reinterpret_cast<scalar_t*>(shared_raw);
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t fault_count = fault_end - fault_begin;
  const int64_t num_bits = window_num_bits[window];
  const int64_t state_count = int64_t{1} << num_bits;
  const scalar_t* window_history = history + window * (max_faults_per_window + 1) * max_state_count;
  scalar_t* grad_a = grad_current + window * max_state_count;
  scalar_t* grad_b = grad_previous + window * max_state_count;
  bool flipped = false;

  for (int64_t local_fault = fault_count - 1; local_fault >= 0; --local_fault) {
    const int64_t flat_index = fault_begin + local_fault;
    const int64_t global_fault = flat_fault_ids[flat_index];
    const int64_t mask = flat_masks[flat_index];
    const scalar_t prob = probabilities[global_fault];
    const scalar_t* q_prev = window_history + local_fault * max_state_count;
    scalar_t* grad_next = flipped ? grad_b : grad_a;
    scalar_t* grad_prev = flipped ? grad_a : grad_b;
    scalar_t dp_sum = static_cast<scalar_t>(0);

    for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
      const int64_t xor_state = state ^ mask;
      const scalar_t grad_here = grad_next[state];
      dp_sum += grad_here * (q_prev[xor_state] - q_prev[state]);
      grad_prev[state] =
          (static_cast<scalar_t>(1) - prob) * grad_here + prob * grad_next[xor_state];
    }

    shared[threadIdx.x] = dp_sum;
    sync_reduction_threads();
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
      if (threadIdx.x < stride) {
        shared[threadIdx.x] += shared[threadIdx.x + stride];
      }
      sync_reduction_threads();
    }
    if (threadIdx.x == 0) {
      atomicAdd(
          grad_logits + global_fault,
          shared[0] * prob * (static_cast<scalar_t>(1) - prob));
    }
    flipped = !flipped;
    sync_active_state_threads(state_count);
  }
}

template <typename scalar_t>
__global__ void local_window_backward_shared_kernel(
    const scalar_t* __restrict__ history,
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ flat_fault_ids,
    const int64_t* __restrict__ flat_masks,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ window_num_bits,
    scalar_t* __restrict__ grad_current,
    scalar_t* __restrict__ grad_logits,
    const int64_t max_faults_per_window,
    const int64_t max_state_count) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* grad_a = reinterpret_cast<scalar_t*>(shared_raw);
  scalar_t* grad_b = grad_a + max_state_count;
  scalar_t* reduction = grad_b + max_state_count;

  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t fault_count = fault_end - fault_begin;
  const int64_t num_bits = window_num_bits[window];
  const int64_t state_count = int64_t{1} << num_bits;
  const scalar_t* window_history = history + window * (max_faults_per_window + 1) * max_state_count;
  const scalar_t* window_grad_current = grad_current + window * max_state_count;
  bool flipped = false;

  for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
    grad_a[state] = window_grad_current[state];
  }
  sync_active_state_threads(state_count);

  for (int64_t local_fault = fault_count - 1; local_fault >= 0; --local_fault) {
    const int64_t flat_index = fault_begin + local_fault;
    const int64_t global_fault = flat_fault_ids[flat_index];
    const int64_t mask = flat_masks[flat_index];
    const scalar_t prob = probabilities[global_fault];
    const scalar_t* q_prev = window_history + local_fault * max_state_count;
    scalar_t* grad_next = flipped ? grad_b : grad_a;
    scalar_t* grad_prev = flipped ? grad_a : grad_b;
    scalar_t dp_sum = static_cast<scalar_t>(0);

    for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
      const int64_t xor_state = state ^ mask;
      const scalar_t grad_here = grad_next[state];
      dp_sum += grad_here * (q_prev[xor_state] - q_prev[state]);
      grad_prev[state] =
          (static_cast<scalar_t>(1) - prob) * grad_here + prob * grad_next[xor_state];
    }

    reduction[threadIdx.x] = dp_sum;
    sync_reduction_threads();
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
      if (threadIdx.x < stride) {
        reduction[threadIdx.x] += reduction[threadIdx.x + stride];
      }
      sync_reduction_threads();
    }
    if (threadIdx.x == 0) {
      atomicAdd(
          grad_logits + global_fault,
          reduction[0] * prob * (static_cast<scalar_t>(1) - prob));
    }
    flipped = !flipped;
  }
}

template <typename scalar_t>
__global__ void local_window_forward_only_loss_kernel(
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ flat_fault_ids,
    const int64_t* __restrict__ flat_masks,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ flat_states,
    const int64_t* __restrict__ flat_counts,
    const int64_t* __restrict__ state_offsets,
    const int64_t* __restrict__ window_num_bits,
    const int64_t* __restrict__ window_total_counts,
    scalar_t* __restrict__ window_losses,
    const int64_t window_count,
    const int64_t max_state_count) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* current_base = reinterpret_cast<scalar_t*>(shared_raw);
  scalar_t* next_base = current_base + max_state_count;
  scalar_t* reduction = next_base + max_state_count;

  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t num_bits = window_num_bits[window];
  const int64_t state_count = int64_t{1} << num_bits;
  scalar_t* current = current_base;
  scalar_t* next = next_base;

  for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
    current[state] = state == 0 ? static_cast<scalar_t>(1) : static_cast<scalar_t>(0);
    next[state] = static_cast<scalar_t>(0);
  }
  sync_active_state_threads(state_count);

  for (int64_t flat_index = fault_begin; flat_index < fault_end; ++flat_index) {
    const int64_t global_fault = flat_fault_ids[flat_index];
    const int64_t mask = flat_masks[flat_index];
    const scalar_t prob = probabilities[global_fault];
    for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
      next[state] = (static_cast<scalar_t>(1) - prob) * current[state] + prob * current[state ^ mask];
    }
    sync_active_state_threads(state_count);
    scalar_t* tmp = current;
    current = next;
    next = tmp;
    sync_active_state_threads(state_count);
  }

  const int64_t state_begin = state_offsets[window];
  const int64_t state_end = state_offsets[window + 1];
  const scalar_t total_count = static_cast<scalar_t>(window_total_counts[window]);
  if (total_count <= static_cast<scalar_t>(0)) {
    if (threadIdx.x == 0) {
      window_losses[window] = static_cast<scalar_t>(0);
    }
    return;
  }

  scalar_t loss_sum = static_cast<scalar_t>(0);
  const scalar_t tiny = likelihood_probability_floor<scalar_t>();
  for (int64_t index = state_begin + threadIdx.x; index < state_end; index += blockDim.x) {
    const int64_t state = flat_states[index];
    const scalar_t count = static_cast<scalar_t>(flat_counts[index]);
    const scalar_t prob = current[state] > tiny ? current[state] : tiny;
    loss_sum += -count * log(prob);
  }
  reduction[threadIdx.x] = loss_sum;
  sync_reduction_threads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      reduction[threadIdx.x] += reduction[threadIdx.x + stride];
    }
    sync_reduction_threads();
  }
  if (threadIdx.x == 0) {
    window_losses[window] = reduction[0] / total_count;
  }
}

template <typename scalar_t>
__global__ void local_window_forward_only_loss_batched_kernel(
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ flat_fault_ids,
    const int64_t* __restrict__ flat_masks,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ flat_states,
    const int64_t* __restrict__ flat_counts,
    const int64_t* __restrict__ state_offsets,
    const int64_t* __restrict__ window_num_bits,
    const int64_t* __restrict__ window_total_counts,
    scalar_t* __restrict__ candidate_window_losses,
    const int64_t window_count,
    const int64_t fault_count,
    const int64_t max_state_count) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* current_base = reinterpret_cast<scalar_t*>(shared_raw);
  scalar_t* next_base = current_base + max_state_count;
  scalar_t* reduction = next_base + max_state_count;

  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t candidate = static_cast<int64_t>(blockIdx.y);
  const scalar_t* candidate_probabilities = probabilities + candidate * fault_count;
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t num_bits = window_num_bits[window];
  const int64_t state_count = int64_t{1} << num_bits;
  scalar_t* current = current_base;
  scalar_t* next = next_base;

  for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
    current[state] = state == 0 ? static_cast<scalar_t>(1) : static_cast<scalar_t>(0);
    next[state] = static_cast<scalar_t>(0);
  }
  sync_active_state_threads(state_count);

  for (int64_t flat_index = fault_begin; flat_index < fault_end; ++flat_index) {
    const int64_t global_fault = flat_fault_ids[flat_index];
    const int64_t mask = flat_masks[flat_index];
    const scalar_t prob = candidate_probabilities[global_fault];
    for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
      next[state] = (static_cast<scalar_t>(1) - prob) * current[state] + prob * current[state ^ mask];
    }
    sync_active_state_threads(state_count);
    scalar_t* tmp = current;
    current = next;
    next = tmp;
    sync_active_state_threads(state_count);
  }

  const int64_t state_begin = state_offsets[window];
  const int64_t state_end = state_offsets[window + 1];
  const scalar_t total_count = static_cast<scalar_t>(window_total_counts[window]);
  if (total_count <= static_cast<scalar_t>(0)) {
    if (threadIdx.x == 0) {
      candidate_window_losses[candidate * window_count + window] = static_cast<scalar_t>(0);
    }
    return;
  }

  scalar_t loss_sum = static_cast<scalar_t>(0);
  const scalar_t tiny = likelihood_probability_floor<scalar_t>();
  for (int64_t index = state_begin + threadIdx.x; index < state_end; index += blockDim.x) {
    const int64_t state = flat_states[index];
    const scalar_t count = static_cast<scalar_t>(flat_counts[index]);
    const scalar_t prob = current[state] > tiny ? current[state] : tiny;
    loss_sum += -count * log(prob);
  }
  reduction[threadIdx.x] = loss_sum;
  sync_reduction_threads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      reduction[threadIdx.x] += reduction[threadIdx.x + stride];
    }
    sync_reduction_threads();
  }
  if (threadIdx.x == 0) {
    candidate_window_losses[candidate * window_count + window] = reduction[0] / total_count;
  }
}

template <typename scalar_t>
__global__ void spectral_prefix_kernel(
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ flat_fault_ids,
    const int64_t* __restrict__ flat_masks,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ window_num_bits,
    scalar_t* __restrict__ prefix,
    const int64_t max_state_count) {
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t fault_count = fault_end - fault_begin;
  const int64_t history_begin = fault_begin + window;
  const int64_t state_count = int64_t{1} << window_num_bits[window];

  for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
    prefix[(history_begin * max_state_count) + state] = static_cast<scalar_t>(1);
  }
  sync_active_state_threads(state_count);

  for (int64_t local_fault = 0; local_fault < fault_count; ++local_fault) {
    const int64_t flat_index = fault_begin + local_fault;
    const int64_t global_fault = flat_fault_ids[flat_index];
    const int64_t mask = flat_masks[flat_index];
    const scalar_t factor = static_cast<scalar_t>(1) - static_cast<scalar_t>(2) * probabilities[global_fault];
    const scalar_t* prev = prefix + (history_begin + local_fault) * max_state_count;
    scalar_t* next = prefix + (history_begin + local_fault + 1) * max_state_count;
    for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
      next[state] = prev[state] * (parity_odd_i64(state & mask) ? factor : static_cast<scalar_t>(1));
    }
    sync_active_state_threads(state_count);
  }
}

template <typename scalar_t>
__global__ void spectral_suffix_kernel(
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ flat_fault_ids,
    const int64_t* __restrict__ flat_masks,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ window_num_bits,
    scalar_t* __restrict__ suffix,
    const int64_t max_state_count) {
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t fault_count = fault_end - fault_begin;
  const int64_t history_begin = fault_begin + window;
  const int64_t state_count = int64_t{1} << window_num_bits[window];

  for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
    suffix[((history_begin + fault_count) * max_state_count) + state] = static_cast<scalar_t>(1);
  }
  sync_active_state_threads(state_count);

  for (int64_t local_fault = fault_count - 1; local_fault >= 0; --local_fault) {
    const int64_t flat_index = fault_begin + local_fault;
    const int64_t global_fault = flat_fault_ids[flat_index];
    const int64_t mask = flat_masks[flat_index];
    const scalar_t factor = static_cast<scalar_t>(1) - static_cast<scalar_t>(2) * probabilities[global_fault];
    const scalar_t* next = suffix + (history_begin + local_fault + 1) * max_state_count;
    scalar_t* current = suffix + (history_begin + local_fault) * max_state_count;
    for (int64_t state = threadIdx.x; state < state_count; state += blockDim.x) {
      current[state] = next[state] * (parity_odd_i64(state & mask) ? factor : static_cast<scalar_t>(1));
    }
    sync_active_state_threads(state_count);
  }
}

template <typename scalar_t>
__global__ void spectral_distribution_kernel(
    const scalar_t* __restrict__ prefix,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ window_num_bits,
    scalar_t* __restrict__ distributions,
    const int64_t max_state_count) {
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t y = static_cast<int64_t>(blockIdx.y) * blockDim.x + threadIdx.x;
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t fault_count = fault_end - fault_begin;
  const int64_t history_begin = fault_begin + window;
  const int64_t state_count = int64_t{1} << window_num_bits[window];
  if (y >= state_count) {
    return;
  }
  const scalar_t* moments = prefix + (history_begin + fault_count) * max_state_count;
  scalar_t total = static_cast<scalar_t>(0);
  for (int64_t spectral_state = 0; spectral_state < state_count; ++spectral_state) {
    const scalar_t sign = parity_odd_i64(spectral_state & y) ? static_cast<scalar_t>(-1) : static_cast<scalar_t>(1);
    total += sign * moments[spectral_state];
  }
  distributions[window * max_state_count + y] = total / static_cast<scalar_t>(state_count);
}

template <typename scalar_t>
__global__ void spectral_loss_and_moment_grad_kernel(
    const scalar_t* __restrict__ distributions,
    const int64_t* __restrict__ flat_states,
    const int64_t* __restrict__ flat_counts,
    const int64_t* __restrict__ state_offsets,
    const int64_t* __restrict__ window_num_bits,
    const int64_t* __restrict__ window_total_counts,
    scalar_t* __restrict__ window_losses,
    scalar_t* __restrict__ moment_grads,
    const int64_t window_count,
    const int64_t max_state_count) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* reduction = reinterpret_cast<scalar_t*>(shared_raw);
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t state_begin = state_offsets[window];
  const int64_t state_end = state_offsets[window + 1];
  const int64_t state_count = int64_t{1} << window_num_bits[window];

  const scalar_t total_count = static_cast<scalar_t>(window_total_counts[window]);
  if (total_count <= static_cast<scalar_t>(0)) {
    if (threadIdx.x == 0) {
      window_losses[window] = static_cast<scalar_t>(0);
    }
    for (int64_t spectral_state = threadIdx.x; spectral_state < state_count; spectral_state += blockDim.x) {
      moment_grads[window * max_state_count + spectral_state] = static_cast<scalar_t>(0);
    }
    return;
  }

  scalar_t loss_sum = static_cast<scalar_t>(0);
  const scalar_t tiny = likelihood_probability_floor<scalar_t>();
  for (int64_t index = state_begin + threadIdx.x; index < state_end; index += blockDim.x) {
    const int64_t observed_state = flat_states[index];
    const scalar_t count = static_cast<scalar_t>(flat_counts[index]);
    const scalar_t raw_prob = distributions[window * max_state_count + observed_state];
    const scalar_t prob = raw_prob > tiny ? raw_prob : tiny;
    loss_sum += -count * log(prob);
  }
  reduction[threadIdx.x] = loss_sum;
  sync_reduction_threads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      reduction[threadIdx.x] += reduction[threadIdx.x + stride];
    }
    sync_reduction_threads();
  }
  if (threadIdx.x == 0) {
    window_losses[window] = reduction[0] / total_count;
  }
  sync_reduction_threads();

  for (int64_t spectral_state = threadIdx.x; spectral_state < state_count; spectral_state += blockDim.x) {
    scalar_t grad = static_cast<scalar_t>(0);
    for (int64_t index = state_begin; index < state_end; ++index) {
      const int64_t observed_state = flat_states[index];
      const scalar_t count = static_cast<scalar_t>(flat_counts[index]);
      const scalar_t raw_prob = distributions[window * max_state_count + observed_state];
      const scalar_t prob = raw_prob > tiny ? raw_prob : tiny;
      const scalar_t sign =
          parity_odd_i64(spectral_state & observed_state) ? static_cast<scalar_t>(-1) : static_cast<scalar_t>(1);
      grad += -count * sign /
          (total_count * static_cast<scalar_t>(window_count) * prob * static_cast<scalar_t>(state_count));
    }
    moment_grads[window * max_state_count + spectral_state] = grad;
  }
}

template <typename scalar_t>
__global__ void spectral_fault_grad_kernel(
    const scalar_t* __restrict__ prefix,
    const scalar_t* __restrict__ suffix,
    const scalar_t* __restrict__ moment_grads,
    const scalar_t* __restrict__ probabilities,
    const int64_t* __restrict__ flat_fault_ids,
    const int64_t* __restrict__ flat_masks,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ window_num_bits,
    scalar_t* __restrict__ grad_logits,
    const int64_t max_state_count) {
  extern __shared__ unsigned char shared_raw[];
  scalar_t* reduction = reinterpret_cast<scalar_t*>(shared_raw);
  const int64_t window = static_cast<int64_t>(blockIdx.x);
  const int64_t local_fault = static_cast<int64_t>(blockIdx.y);
  const int64_t fault_begin = fault_offsets[window];
  const int64_t fault_end = fault_offsets[window + 1];
  const int64_t fault_count = fault_end - fault_begin;
  if (local_fault >= fault_count) {
    return;
  }
  const int64_t flat_index = fault_begin + local_fault;
  const int64_t global_fault = flat_fault_ids[flat_index];
  const int64_t mask = flat_masks[flat_index];
  const int64_t history_begin = fault_begin + window;
  const int64_t state_count = int64_t{1} << window_num_bits[window];
  const scalar_t prob = probabilities[global_fault];
  const scalar_t d_factor = static_cast<scalar_t>(-2) * prob * (static_cast<scalar_t>(1) - prob);
  const scalar_t* prefix_row = prefix + (history_begin + local_fault) * max_state_count;
  const scalar_t* suffix_row = suffix + (history_begin + local_fault + 1) * max_state_count;
  const scalar_t* window_moment_grads = moment_grads + window * max_state_count;

  scalar_t partial = static_cast<scalar_t>(0);
  for (int64_t spectral_state = threadIdx.x; spectral_state < state_count; spectral_state += blockDim.x) {
    if (parity_odd_i64(spectral_state & mask)) {
      partial += window_moment_grads[spectral_state] * prefix_row[spectral_state] * suffix_row[spectral_state] *
          d_factor;
    }
  }
  reduction[threadIdx.x] = partial;
  sync_reduction_threads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      reduction[threadIdx.x] += reduction[threadIdx.x + stride];
    }
    sync_reduction_threads();
  }
  if (threadIdx.x == 0) {
    atomicAdd(grad_logits + global_fault, reduction[0]);
  }
}

std::tuple<torch::Tensor, torch::Tensor> local_window_nll_value_and_grad_cuda(
    torch::Tensor logits,
    torch::Tensor flat_fault_ids,
    torch::Tensor flat_masks,
    torch::Tensor fault_offsets,
    torch::Tensor flat_states,
    torch::Tensor flat_counts,
    torch::Tensor state_offsets,
    torch::Tensor window_num_bits,
    torch::Tensor window_total_counts,
    int64_t max_faults_per_window,
    int64_t max_state_count) {
  const c10::cuda::CUDAGuard device_guard(logits.device());
  const int64_t window_count = window_num_bits.size(0);
  auto probabilities = torch::sigmoid(logits).contiguous();
  auto history = torch::empty({window_count, max_faults_per_window + 1, max_state_count}, logits.options());
  auto window_losses = torch::empty({window_count}, logits.options());
  auto grad_current = torch::empty({window_count, max_state_count}, logits.options());
  auto grad_previous = torch::empty_like(grad_current);
  auto grad_logits = torch::zeros_like(logits);

  if (window_count == 0) {
    return std::make_tuple(torch::zeros({}, logits.options()), grad_logits);
  }

  const int threads = threads_for_state_count(max_state_count);
  cudaStream_t stream = at::cuda::getCurrentCUDAStream();
  AT_DISPATCH_FLOATING_TYPES(logits.scalar_type(), "local_window_nll_value_and_grad_cuda", [&] {
    const size_t reduction_shared_bytes = threads * sizeof(scalar_t);
    const bool use_shared_state =
        max_state_count <= (sizeof(scalar_t) == sizeof(float) ? int64_t{2048} : int64_t{1024});
    if (use_shared_state) {
      const size_t state_shared_bytes = 2 * max_state_count * sizeof(scalar_t);
      local_window_forward_shared_kernel<scalar_t><<<window_count, threads, state_shared_bytes, stream>>>(
          probabilities.data_ptr<scalar_t>(),
          flat_fault_ids.data_ptr<int64_t>(),
          flat_masks.data_ptr<int64_t>(),
          fault_offsets.data_ptr<int64_t>(),
          window_num_bits.data_ptr<int64_t>(),
          history.data_ptr<scalar_t>(),
          max_faults_per_window,
          max_state_count);
    } else {
      local_window_forward_kernel<scalar_t><<<window_count, threads, 0, stream>>>(
          probabilities.data_ptr<scalar_t>(),
          flat_fault_ids.data_ptr<int64_t>(),
          flat_masks.data_ptr<int64_t>(),
          fault_offsets.data_ptr<int64_t>(),
          window_num_bits.data_ptr<int64_t>(),
          history.data_ptr<scalar_t>(),
          max_faults_per_window,
          max_state_count);
    }
    local_window_loss_and_dist_grad_kernel<scalar_t><<<window_count, threads, reduction_shared_bytes, stream>>>(
        history.data_ptr<scalar_t>(),
        fault_offsets.data_ptr<int64_t>(),
        flat_states.data_ptr<int64_t>(),
        flat_counts.data_ptr<int64_t>(),
        state_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        window_total_counts.data_ptr<int64_t>(),
        window_losses.data_ptr<scalar_t>(),
        grad_current.data_ptr<scalar_t>(),
        window_count,
        max_faults_per_window,
        max_state_count);
    if (use_shared_state) {
      const size_t backward_shared_bytes = (2 * max_state_count + threads) * sizeof(scalar_t);
      local_window_backward_shared_kernel<scalar_t><<<window_count, threads, backward_shared_bytes, stream>>>(
          history.data_ptr<scalar_t>(),
          probabilities.data_ptr<scalar_t>(),
          flat_fault_ids.data_ptr<int64_t>(),
          flat_masks.data_ptr<int64_t>(),
          fault_offsets.data_ptr<int64_t>(),
          window_num_bits.data_ptr<int64_t>(),
          grad_current.data_ptr<scalar_t>(),
          grad_logits.data_ptr<scalar_t>(),
          max_faults_per_window,
          max_state_count);
    } else {
      local_window_backward_kernel<scalar_t><<<window_count, threads, reduction_shared_bytes, stream>>>(
          history.data_ptr<scalar_t>(),
          probabilities.data_ptr<scalar_t>(),
          flat_fault_ids.data_ptr<int64_t>(),
          flat_masks.data_ptr<int64_t>(),
          fault_offsets.data_ptr<int64_t>(),
          window_num_bits.data_ptr<int64_t>(),
          grad_current.data_ptr<scalar_t>(),
          grad_previous.data_ptr<scalar_t>(),
          grad_logits.data_ptr<scalar_t>(),
          max_faults_per_window,
          max_state_count);
    }
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return std::make_tuple(window_losses.mean(), grad_logits);
}

std::tuple<torch::Tensor, torch::Tensor> local_window_nll_value_and_grad_spectral_cuda(
    torch::Tensor logits,
    torch::Tensor flat_fault_ids,
    torch::Tensor flat_masks,
    torch::Tensor fault_offsets,
    torch::Tensor flat_states,
    torch::Tensor flat_counts,
    torch::Tensor state_offsets,
    torch::Tensor window_num_bits,
    torch::Tensor window_total_counts,
    int64_t max_faults_per_window,
    int64_t max_state_count,
    double spectral_min_abs_factor,
    int64_t spectral_memory_cap_bytes) {
  const c10::cuda::CUDAGuard device_guard(logits.device());
  const int64_t window_count = window_num_bits.size(0);
  auto probabilities = torch::sigmoid(logits).contiguous();
  auto window_losses = torch::empty({window_count}, logits.options());
  auto grad_logits = torch::zeros_like(logits);

  if (window_count == 0) {
    return std::make_tuple(torch::zeros({}, logits.options()), grad_logits);
  }
  if (flat_fault_ids.numel() > 0) {
    auto active_probabilities = probabilities.index_select(0, flat_fault_ids);
    const double min_abs_factor =
        (1 - 2 * active_probabilities).abs().min().item<double>();
    TORCH_CHECK(
        min_abs_factor >= spectral_min_abs_factor,
        "spectral_min_abs_factor guard failed: min |1 - 2p_j|=",
        min_abs_factor,
        " threshold=",
        spectral_min_abs_factor);
  }

  const int64_t history_rows = flat_fault_ids.size(0) + window_count;
  const int64_t scalar_bytes = logits.element_size();
  const int64_t history_bytes = 2 * history_rows * max_state_count * scalar_bytes;
  const int64_t dense_bytes = 2 * window_count * max_state_count * scalar_bytes;
  TORCH_CHECK(
      history_bytes + dense_bytes <= spectral_memory_cap_bytes,
      "spectral history memory cap exceeded: required_bytes=",
      history_bytes + dense_bytes,
      " cap_bytes=",
      spectral_memory_cap_bytes);

  auto prefix = torch::empty({history_rows, max_state_count}, logits.options());
  auto suffix = torch::empty_like(prefix);
  auto distributions = torch::empty({window_count, max_state_count}, logits.options());
  auto moment_grads = torch::empty_like(distributions);

  const int threads = threads_for_state_count(max_state_count);
  cudaStream_t stream = at::cuda::getCurrentCUDAStream();
  AT_DISPATCH_FLOATING_TYPES(logits.scalar_type(), "local_window_nll_value_and_grad_spectral_cuda", [&] {
    const size_t shared_bytes = threads * sizeof(scalar_t);
    spectral_prefix_kernel<scalar_t><<<window_count, threads, 0, stream>>>(
        probabilities.data_ptr<scalar_t>(),
        flat_fault_ids.data_ptr<int64_t>(),
        flat_masks.data_ptr<int64_t>(),
        fault_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        prefix.data_ptr<scalar_t>(),
        max_state_count);
    spectral_suffix_kernel<scalar_t><<<window_count, threads, 0, stream>>>(
        probabilities.data_ptr<scalar_t>(),
        flat_fault_ids.data_ptr<int64_t>(),
        flat_masks.data_ptr<int64_t>(),
        fault_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        suffix.data_ptr<scalar_t>(),
        max_state_count);
    const dim3 distribution_blocks(
        static_cast<unsigned int>(window_count),
        static_cast<unsigned int>((max_state_count + threads - 1) / threads));
    spectral_distribution_kernel<scalar_t><<<distribution_blocks, threads, 0, stream>>>(
        prefix.data_ptr<scalar_t>(),
        fault_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        distributions.data_ptr<scalar_t>(),
        max_state_count);
    spectral_loss_and_moment_grad_kernel<scalar_t><<<window_count, threads, shared_bytes, stream>>>(
        distributions.data_ptr<scalar_t>(),
        flat_states.data_ptr<int64_t>(),
        flat_counts.data_ptr<int64_t>(),
        state_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        window_total_counts.data_ptr<int64_t>(),
        window_losses.data_ptr<scalar_t>(),
        moment_grads.data_ptr<scalar_t>(),
        window_count,
        max_state_count);
    const dim3 grad_blocks(static_cast<unsigned int>(window_count), static_cast<unsigned int>(max_faults_per_window));
    spectral_fault_grad_kernel<scalar_t><<<grad_blocks, threads, shared_bytes, stream>>>(
        prefix.data_ptr<scalar_t>(),
        suffix.data_ptr<scalar_t>(),
        moment_grads.data_ptr<scalar_t>(),
        probabilities.data_ptr<scalar_t>(),
        flat_fault_ids.data_ptr<int64_t>(),
        flat_masks.data_ptr<int64_t>(),
        fault_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        grad_logits.data_ptr<scalar_t>(),
        max_state_count);
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return std::make_tuple(window_losses.mean(), grad_logits);
}

torch::Tensor local_window_nll_value_cuda(
    torch::Tensor logits,
    torch::Tensor flat_fault_ids,
    torch::Tensor flat_masks,
    torch::Tensor fault_offsets,
    torch::Tensor flat_states,
    torch::Tensor flat_counts,
    torch::Tensor state_offsets,
    torch::Tensor window_num_bits,
    torch::Tensor window_total_counts,
    int64_t max_faults_per_window,
    int64_t max_state_count) {
  const c10::cuda::CUDAGuard device_guard(logits.device());
  const int64_t window_count = window_num_bits.size(0);
  auto probabilities = torch::sigmoid(logits).contiguous();
  auto window_losses = torch::empty({window_count}, logits.options());

  if (window_count == 0) {
    return torch::zeros({}, logits.options());
  }

  const int threads = threads_for_state_count(max_state_count);
  cudaStream_t stream = at::cuda::getCurrentCUDAStream();
  AT_DISPATCH_FLOATING_TYPES(logits.scalar_type(), "local_window_nll_value_cuda", [&] {
    const size_t shared_bytes = (2 * max_state_count + threads) * sizeof(scalar_t);
    local_window_forward_only_loss_kernel<scalar_t><<<window_count, threads, shared_bytes, stream>>>(
        probabilities.data_ptr<scalar_t>(),
        flat_fault_ids.data_ptr<int64_t>(),
        flat_masks.data_ptr<int64_t>(),
        fault_offsets.data_ptr<int64_t>(),
        flat_states.data_ptr<int64_t>(),
        flat_counts.data_ptr<int64_t>(),
        state_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        window_total_counts.data_ptr<int64_t>(),
        window_losses.data_ptr<scalar_t>(),
        window_count,
        max_state_count);
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return window_losses.mean();
}

torch::Tensor local_window_nll_values_cuda(
    torch::Tensor logits_batch,
    torch::Tensor flat_fault_ids,
    torch::Tensor flat_masks,
    torch::Tensor fault_offsets,
    torch::Tensor flat_states,
    torch::Tensor flat_counts,
    torch::Tensor state_offsets,
    torch::Tensor window_num_bits,
    torch::Tensor window_total_counts,
    int64_t max_faults_per_window,
    int64_t max_state_count) {
  const c10::cuda::CUDAGuard device_guard(logits_batch.device());
  const int64_t candidate_count = logits_batch.size(0);
  const int64_t fault_count = logits_batch.size(1);
  const int64_t window_count = window_num_bits.size(0);
  auto probabilities = torch::sigmoid(logits_batch).contiguous();
  auto candidate_window_losses = torch::empty({candidate_count, window_count}, logits_batch.options());

  if (window_count == 0) {
    return torch::zeros({candidate_count}, logits_batch.options());
  }

  const int threads = threads_for_state_count(max_state_count);
  cudaStream_t stream = at::cuda::getCurrentCUDAStream();
  dim3 blocks(static_cast<unsigned int>(window_count), static_cast<unsigned int>(candidate_count));
  AT_DISPATCH_FLOATING_TYPES(logits_batch.scalar_type(), "local_window_nll_values_cuda", [&] {
    const size_t shared_bytes = (2 * max_state_count + threads) * sizeof(scalar_t);
    local_window_forward_only_loss_batched_kernel<scalar_t><<<blocks, threads, shared_bytes, stream>>>(
        probabilities.data_ptr<scalar_t>(),
        flat_fault_ids.data_ptr<int64_t>(),
        flat_masks.data_ptr<int64_t>(),
        fault_offsets.data_ptr<int64_t>(),
        flat_states.data_ptr<int64_t>(),
        flat_counts.data_ptr<int64_t>(),
        state_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        window_total_counts.data_ptr<int64_t>(),
        candidate_window_losses.data_ptr<scalar_t>(),
        window_count,
        fault_count,
        max_state_count);
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return candidate_window_losses.mean({1});
}
