#include <torch/extension.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAException.h>
#include <c10/cuda/CUDAGuard.h>
#include <limits>

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
  __syncthreads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      shared[threadIdx.x] += shared[threadIdx.x + stride];
    }
    __syncthreads();
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
  __syncthreads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      shared[threadIdx.x] += shared[threadIdx.x + stride];
    }
    __syncthreads();
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

  const int threads = 256;
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

  const int threads = 256;
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
  const int threads = 256;
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
  __syncthreads();

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
    __syncthreads();
  }
}

template <typename scalar_t>
__global__ void local_window_loss_and_dist_grad_kernel(
    const scalar_t* __restrict__ history,
    const int64_t* __restrict__ fault_offsets,
    const int64_t* __restrict__ flat_states,
    const int64_t* __restrict__ flat_counts,
    const int64_t* __restrict__ state_offsets,
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
  const scalar_t* dist =
      history + (window * (max_faults_per_window + 1) + fault_count) * max_state_count;
  scalar_t* grad = grad_current + window * max_state_count;

  int64_t total_count_i64 = 0;
  for (int64_t index = state_begin + threadIdx.x; index < state_end; index += blockDim.x) {
    total_count_i64 += flat_counts[index];
  }
  shared_loss[threadIdx.x] = static_cast<scalar_t>(total_count_i64);
  __syncthreads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      shared_loss[threadIdx.x] += shared_loss[threadIdx.x + stride];
    }
    __syncthreads();
  }
  const scalar_t total_count = shared_loss[0];
  __syncthreads();

  scalar_t loss_sum = static_cast<scalar_t>(0);
  const scalar_t tiny = std::numeric_limits<scalar_t>::min();
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
  __syncthreads();
  for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
    if (threadIdx.x < stride) {
      shared_loss[threadIdx.x] += shared_loss[threadIdx.x + stride];
    }
    __syncthreads();
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
    __syncthreads();
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
      if (threadIdx.x < stride) {
        shared[threadIdx.x] += shared[threadIdx.x + stride];
      }
      __syncthreads();
    }
    if (threadIdx.x == 0) {
      atomicAdd(
          grad_logits + global_fault,
          shared[0] * prob * (static_cast<scalar_t>(1) - prob));
    }
    flipped = !flipped;
    __syncthreads();
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
    int64_t max_faults_per_window,
    int64_t max_state_count) {
  const c10::cuda::CUDAGuard device_guard(logits.device());
  const int64_t window_count = window_num_bits.size(0);
  auto probabilities = torch::sigmoid(logits).contiguous();
  auto history = torch::zeros({window_count, max_faults_per_window + 1, max_state_count}, logits.options());
  auto window_losses = torch::empty({window_count}, logits.options());
  auto grad_current = torch::zeros({window_count, max_state_count}, logits.options());
  auto grad_previous = torch::empty_like(grad_current);
  auto grad_logits = torch::zeros_like(logits);

  if (window_count == 0) {
    return std::make_tuple(torch::zeros({}, logits.options()), grad_logits);
  }

  const int threads = 256;
  cudaStream_t stream = at::cuda::getCurrentCUDAStream();
  AT_DISPATCH_FLOATING_TYPES(logits.scalar_type(), "local_window_nll_value_and_grad_cuda", [&] {
    const size_t shared_bytes = threads * sizeof(scalar_t);
    local_window_forward_kernel<scalar_t><<<window_count, threads, 0, stream>>>(
        probabilities.data_ptr<scalar_t>(),
        flat_fault_ids.data_ptr<int64_t>(),
        flat_masks.data_ptr<int64_t>(),
        fault_offsets.data_ptr<int64_t>(),
        window_num_bits.data_ptr<int64_t>(),
        history.data_ptr<scalar_t>(),
        max_faults_per_window,
        max_state_count);
    local_window_loss_and_dist_grad_kernel<scalar_t><<<window_count, threads, shared_bytes, stream>>>(
        history.data_ptr<scalar_t>(),
        fault_offsets.data_ptr<int64_t>(),
        flat_states.data_ptr<int64_t>(),
        flat_counts.data_ptr<int64_t>(),
        state_offsets.data_ptr<int64_t>(),
        window_losses.data_ptr<scalar_t>(),
        grad_current.data_ptr<scalar_t>(),
        window_count,
        max_faults_per_window,
        max_state_count);
    local_window_backward_kernel<scalar_t><<<window_count, threads, shared_bytes, stream>>>(
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
  });
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return std::make_tuple(window_losses.mean(), grad_logits);
}
