#include <torch/extension.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAException.h>
#include <c10/cuda/CUDAGuard.h>

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
