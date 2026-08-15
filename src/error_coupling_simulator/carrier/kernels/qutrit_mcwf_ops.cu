// Generic qutrit-statevector kernels for simulator MCWF workloads.
//
// State convention: psi has shape [B, 3^n], qutrit 0 is the most-significant
// trit: idx = sum_q t_q * 3^(n-1-q).  Qubit gates act on the {|0>, |1>}
// subspace of their target qutrits and leave any amplitude with a target qutrit
// in |2> unchanged.

#include <torch/extension.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAException.h>
#include <c10/util/complex.h>
#include <cuda_runtime.h>

#include <utility>
#include <vector>

using cplx = c10::complex<double>;

constexpr int MAX_GATE_ARITY = 3;
constexpr int MAX_PHASE_CONTROLS = 32;
constexpr int OP_H = 1;
constexpr int OP_X = 2;
constexpr int OP_ALL_ONES_PHASE = 3;
constexpr int OP_KRAUS_ALL_SITES = 4;
constexpr int OP_X_LAYER = 5;

static long long pow3_host(int n) {
  long long out = 1;
  for (int i = 0; i < n; ++i) out *= 3LL;
  return out;
}

__device__ long long pow3_device(int n) {
  long long out = 1;
  for (int i = 0; i < n; ++i) out *= 3LL;
  return out;
}

static void validate_sites(const std::vector<int64_t>& sites, int64_t n, int max_sites) {
  TORCH_CHECK(!sites.empty(), "sites must be non-empty");
  TORCH_CHECK((int)sites.size() <= max_sites, "too many sites for this kernel");
  for (size_t i = 0; i < sites.size(); ++i) {
    TORCH_CHECK(sites[i] >= 0 && sites[i] < n, "site out of range");
    for (size_t j = i + 1; j < sites.size(); ++j) {
      TORCH_CHECK(sites[i] != sites[j], "sites must be unique");
    }
  }
}

__global__ void qutrit_apply_qubit_gate_kernel(
    const cplx* __restrict__ psi,
    const cplx* __restrict__ U,
    cplx* __restrict__ out,
    long long B,
    long long D,
    int m,
    long long p0,
    long long p1,
    long long p2) {
  const long long tid = blockIdx.x * (long long)blockDim.x + threadIdx.x;
  const long long total = B * D;
  if (tid >= total) return;

  const long long basis = tid % D;
  const long long b = tid / D;
  const long long places[MAX_GATE_ARITY] = {p0, p1, p2};

  int row = 0;
  long long base = basis;
  bool leaked = false;
  for (int j = 0; j < m; ++j) {
    const int trit = (int)((basis / places[j]) % 3LL);
    if (trit == 2) leaked = true;
    row = (row << 1) | (trit & 1);
    base -= (long long)trit * places[j];
  }
  const cplx* in = psi + b * D;
  if (leaked) {
    out[tid] = in[basis];
    return;
  }

  const int dt = 1 << m;
  cplx acc(0.0, 0.0);
  for (int col = 0; col < dt; ++col) {
    long long src = base;
    for (int j = 0; j < m; ++j) {
      const int bit = (col >> (m - 1 - j)) & 1;
      src += (long long)bit * places[j];
    }
    acc += U[row * dt + col] * in[src];
  }
  out[tid] = acc;
}

__global__ void qutrit_apply_cached_1q_gate_kernel(
    const cplx* __restrict__ psi,
    cplx* __restrict__ out,
    long long B,
    long long D,
    long long place,
    int op_kind) {
  const long long tid = blockIdx.x * (long long)blockDim.x + threadIdx.x;
  const long long total = B * D;
  if (tid >= total) return;
  const long long basis = tid % D;
  const long long b = tid / D;
  const int row = (int)((basis / place) % 3LL);
  const long long base = basis - (long long)row * place;
  const cplx* in = psi + b * D;
  if (row == 2) {
    out[tid] = in[basis];
    return;
  }
  if (op_kind == OP_H) {
    const double inv = 0.7071067811865475244;
    const cplx a0 = in[base];
    const cplx a1 = in[base + place];
    out[tid] = (row == 0) ? (a0 + a1) * inv : (a0 - a1) * inv;
  } else {
    const int col = 1 - row;
    out[tid] = in[base + (long long)col * place];
  }
}

__global__ void qutrit_apply_x_layer_kernel(
    const cplx* __restrict__ psi,
    cplx* __restrict__ out,
    long long B,
    long long D,
    int m,
    long long p0,
    long long p1,
    long long p2,
    long long p3,
    long long p4,
    long long p5,
    long long p6,
    long long p7,
    long long p8,
    long long p9,
    long long p10,
    long long p11,
    long long p12,
    long long p13,
    long long p14,
    long long p15,
    long long p16,
    long long p17,
    long long p18,
    long long p19,
    long long p20,
    long long p21,
    long long p22,
    long long p23,
    long long p24,
    long long p25,
    long long p26,
    long long p27,
    long long p28,
    long long p29,
    long long p30,
    long long p31) {
  const long long tid = blockIdx.x * (long long)blockDim.x + threadIdx.x;
  const long long total = B * D;
  if (tid >= total) return;
  const long long basis = tid % D;
  const long long b = tid / D;
  const long long places[MAX_PHASE_CONTROLS] = {
      p0, p1, p2, p3, p4, p5, p6, p7,
      p8, p9, p10, p11, p12, p13, p14, p15,
      p16, p17, p18, p19, p20, p21, p22, p23,
      p24, p25, p26, p27, p28, p29, p30, p31};
  long long src = basis;
  for (int j = 0; j < m; ++j) {
    const long long place = places[j];
    const int row = (int)((basis / place) % 3LL);
    if (row == 0) {
      src += place;
    } else if (row == 1) {
      src -= place;
    }
  }
  out[tid] = psi[b * D + src];
}

torch::Tensor qutrit_apply_qubit_gate_cuda(
    torch::Tensor psi,
    torch::Tensor unitary,
    std::vector<int64_t> sites,
    int64_t n) {
  TORCH_CHECK(psi.is_cuda() && unitary.is_cuda(), "psi and unitary must be CUDA");
  TORCH_CHECK(psi.scalar_type() == torch::kComplexDouble, "psi must be complex128");
  TORCH_CHECK(unitary.scalar_type() == torch::kComplexDouble, "unitary must be complex128");
  TORCH_CHECK(psi.dim() == 2, "psi must have shape [B, 3^n]");
  validate_sites(sites, n, MAX_GATE_ARITY);
  const int m = (int)sites.size();
  const int dt = 1 << m;
  TORCH_CHECK(unitary.dim() == 2 && unitary.size(0) == dt && unitary.size(1) == dt,
              "unitary must have shape [2^arity, 2^arity]");
  const long long D = pow3_host((int)n);
  TORCH_CHECK(psi.size(1) == D, "psi second dimension must equal 3^n");
  const long long B = psi.size(0);

  long long places[MAX_GATE_ARITY] = {1, 1, 1};
  for (int j = 0; j < m; ++j) places[j] = pow3_host((int)(n - 1 - sites[j]));

  auto pc = psi.contiguous();
  auto uc = unitary.contiguous();
  auto out = torch::empty_like(pc);
  const long long total = B * D;
  const int threads = 256;
  const long long blocks = (total + threads - 1) / threads;
  qutrit_apply_qubit_gate_kernel<<<(unsigned int)blocks, threads, 0,
                                   at::cuda::getCurrentCUDAStream()>>>(
      reinterpret_cast<const cplx*>(pc.const_data_ptr<c10::complex<double>>()),
      reinterpret_cast<const cplx*>(uc.const_data_ptr<c10::complex<double>>()),
      reinterpret_cast<cplx*>(out.mutable_data_ptr<c10::complex<double>>()),
      B, D, m, places[0], places[1], places[2]);
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return out;
}

__global__ void qutrit_multi_controlled_phase_kernel(
    const cplx* __restrict__ psi,
    cplx* __restrict__ out,
    long long B,
    long long D,
    int m,
    cplx phase,
    long long p0,
    long long p1,
    long long p2,
    long long p3,
    long long p4,
    long long p5,
    long long p6,
    long long p7,
    long long p8,
    long long p9,
    long long p10,
    long long p11,
    long long p12,
    long long p13,
    long long p14,
    long long p15,
    long long p16,
    long long p17,
    long long p18,
    long long p19,
    long long p20,
    long long p21,
    long long p22,
    long long p23,
    long long p24,
    long long p25,
    long long p26,
    long long p27,
    long long p28,
    long long p29,
    long long p30,
    long long p31) {
  const long long tid = blockIdx.x * (long long)blockDim.x + threadIdx.x;
  const long long total = B * D;
  if (tid >= total) return;
  const long long basis = tid % D;
  const long long places[MAX_PHASE_CONTROLS] = {
      p0, p1, p2, p3, p4, p5, p6, p7,
      p8, p9, p10, p11, p12, p13, p14, p15,
      p16, p17, p18, p19, p20, p21, p22, p23,
      p24, p25, p26, p27, p28, p29, p30, p31};
  bool fire = true;
  for (int j = 0; j < m; ++j) {
    fire = fire && (((basis / places[j]) % 3LL) == 1LL);
  }
  cplx amp = psi[tid];
  out[tid] = fire ? amp * phase : amp;
}

torch::Tensor qutrit_multi_controlled_phase_cuda(
    torch::Tensor psi,
    std::vector<int64_t> sites,
    double phase_re,
    double phase_im,
    int64_t n) {
  TORCH_CHECK(psi.is_cuda(), "psi must be CUDA");
  TORCH_CHECK(psi.scalar_type() == torch::kComplexDouble, "psi must be complex128");
  TORCH_CHECK(psi.dim() == 2, "psi must have shape [B, 3^n]");
  validate_sites(sites, n, MAX_PHASE_CONTROLS);
  const long long D = pow3_host((int)n);
  TORCH_CHECK(psi.size(1) == D, "psi second dimension must equal 3^n");
  const long long B = psi.size(0);

  long long places[MAX_PHASE_CONTROLS];
  for (int i = 0; i < MAX_PHASE_CONTROLS; ++i) places[i] = 1;
  for (size_t j = 0; j < sites.size(); ++j) places[j] = pow3_host((int)(n - 1 - sites[j]));

  auto pc = psi.contiguous();
  auto out = torch::empty_like(pc);
  const long long total = B * D;
  const int threads = 256;
  const long long blocks = (total + threads - 1) / threads;
  qutrit_multi_controlled_phase_kernel<<<(unsigned int)blocks, threads, 0,
                                         at::cuda::getCurrentCUDAStream()>>>(
      reinterpret_cast<const cplx*>(pc.const_data_ptr<c10::complex<double>>()),
      reinterpret_cast<cplx*>(out.mutable_data_ptr<c10::complex<double>>()),
      B, D, (int)sites.size(), cplx(phase_re, phase_im),
      places[0], places[1], places[2], places[3], places[4], places[5], places[6], places[7],
      places[8], places[9], places[10], places[11], places[12], places[13], places[14], places[15],
      places[16], places[17], places[18], places[19], places[20], places[21], places[22], places[23],
      places[24], places[25], places[26], places[27], places[28], places[29], places[30], places[31]);
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return out;
}

__global__ void qutrit_kraus_norm_kernel(
    const cplx* __restrict__ psi,
    const cplx* __restrict__ kraus,
    double* __restrict__ norms,
    long long B,
    long long D,
    int K,
    long long place) {
  const int b = blockIdx.x;
  const int k = blockIdx.y;
  const int tid = threadIdx.x;
  extern __shared__ double scratch[];
  double acc = 0.0;
  const cplx* in = psi + (long long)b * D;
  const cplx* Kk = kraus + (long long)k * 9;
  for (long long basis = tid; basis < D; basis += blockDim.x) {
    const int row = (int)((basis / place) % 3LL);
    const long long base = basis - (long long)row * place;
    cplx v(0.0, 0.0);
    for (int col = 0; col < 3; ++col) {
      v += Kk[row * 3 + col] * in[base + (long long)col * place];
    }
    acc += v.real() * v.real() + v.imag() * v.imag();
  }
  scratch[tid] = acc;
  __syncthreads();
  for (int stride = blockDim.x >> 1; stride > 0; stride >>= 1) {
    if (tid < stride) scratch[tid] += scratch[tid + stride];
    __syncthreads();
  }
  if (tid == 0) norms[(long long)b * K + k] = scratch[0];
}

__global__ void qutrit_kraus_select_kernel(
    const double* __restrict__ norms,
    const double* __restrict__ rand,
    int64_t* __restrict__ selected,
    double* __restrict__ inv_norm,
    long long B,
    int K) {
  const long long b = blockIdx.x * (long long)blockDim.x + threadIdx.x;
  if (b >= B) return;
  const double* nb = norms + b * K;
  double total = 0.0;
  for (int k = 0; k < K; ++k) total += nb[k];
  const double u = rand[b] * total;
  double cdf = 0.0;
  int chosen = K - 1;
  for (int k = 0; k < K; ++k) {
    cdf += nb[k];
    if (u <= cdf) {
      chosen = k;
      break;
    }
  }
  selected[b] = (int64_t)chosen;
  const double p = nb[chosen] > 1e-300 ? nb[chosen] : 1e-300;
  inv_norm[b] = rsqrt(p);
}

__global__ void qutrit_kraus_apply_kernel(
    const cplx* __restrict__ psi,
    const cplx* __restrict__ kraus,
    const int64_t* __restrict__ selected,
    const double* __restrict__ inv_norm,
    cplx* __restrict__ out,
    long long B,
    long long D,
    long long place) {
  const long long tid = blockIdx.x * (long long)blockDim.x + threadIdx.x;
  const long long total = B * D;
  if (tid >= total) return;
  const long long basis = tid % D;
  const long long b = tid / D;
  const int row = (int)((basis / place) % 3LL);
  const long long base = basis - (long long)row * place;
  const cplx* in = psi + b * D;
  const cplx* Kk = kraus + selected[b] * 9;
  cplx v(0.0, 0.0);
  for (int col = 0; col < 3; ++col) {
    v += Kk[row * 3 + col] * in[base + (long long)col * place];
  }
  out[tid] = v * inv_norm[b];
}

torch::Tensor qutrit_apply_kraus_site_cuda(
    torch::Tensor psi,
    torch::Tensor kraus,
    torch::Tensor rand,
    int64_t site,
    int64_t n) {
  TORCH_CHECK(psi.is_cuda() && kraus.is_cuda() && rand.is_cuda(), "psi, kraus, and rand must be CUDA");
  TORCH_CHECK(psi.scalar_type() == torch::kComplexDouble, "psi must be complex128");
  TORCH_CHECK(kraus.scalar_type() == torch::kComplexDouble, "kraus must be complex128");
  TORCH_CHECK(rand.scalar_type() == torch::kFloat64, "rand must be float64");
  TORCH_CHECK(psi.dim() == 2, "psi must have shape [B, 3^n]");
  TORCH_CHECK(kraus.dim() == 3 && kraus.size(1) == 3 && kraus.size(2) == 3,
              "kraus must have shape [K, 3, 3]");
  TORCH_CHECK(site >= 0 && site < n, "site out of range");
  const long long D = pow3_host((int)n);
  TORCH_CHECK(psi.size(1) == D, "psi second dimension must equal 3^n");
  const long long B = psi.size(0);
  const int K = (int)kraus.size(0);
  TORCH_CHECK(rand.numel() == B, "rand must have shape [B]");

  auto pc = psi.contiguous();
  auto kc = kraus.contiguous();
  auto rc = rand.contiguous();
  auto opts_r = torch::TensorOptions().dtype(torch::kFloat64).device(psi.device());
  auto norms = torch::empty({B, K}, opts_r);
  auto inv_norm = torch::empty({B}, opts_r);
  auto opts_i = torch::TensorOptions().dtype(torch::kInt64).device(psi.device());
  auto selected = torch::empty({B}, opts_i);
  auto out = torch::empty_like(pc);

  const long long place = pow3_host((int)(n - 1 - site));
  const int red_threads = 256;
  qutrit_kraus_norm_kernel<<<dim3((unsigned int)B, (unsigned int)K), red_threads,
                             red_threads * sizeof(double), at::cuda::getCurrentCUDAStream()>>>(
      reinterpret_cast<const cplx*>(pc.const_data_ptr<c10::complex<double>>()),
      reinterpret_cast<const cplx*>(kc.const_data_ptr<c10::complex<double>>()),
      norms.mutable_data_ptr<double>(), B, D, K, place);
  C10_CUDA_KERNEL_LAUNCH_CHECK();

  const int threads = 256;
  const long long select_blocks = (B + threads - 1) / threads;
  qutrit_kraus_select_kernel<<<(unsigned int)select_blocks, threads, 0,
                               at::cuda::getCurrentCUDAStream()>>>(
      norms.const_data_ptr<double>(), rc.const_data_ptr<double>(),
      selected.mutable_data_ptr<int64_t>(), inv_norm.mutable_data_ptr<double>(), B, K);
  C10_CUDA_KERNEL_LAUNCH_CHECK();

  const long long total = B * D;
  const long long apply_blocks = (total + threads - 1) / threads;
  qutrit_kraus_apply_kernel<<<(unsigned int)apply_blocks, threads, 0,
                              at::cuda::getCurrentCUDAStream()>>>(
      reinterpret_cast<const cplx*>(pc.const_data_ptr<c10::complex<double>>()),
      reinterpret_cast<const cplx*>(kc.const_data_ptr<c10::complex<double>>()),
      selected.const_data_ptr<int64_t>(), inv_norm.const_data_ptr<double>(),
      reinterpret_cast<cplx*>(out.mutable_data_ptr<c10::complex<double>>()),
      B, D, place);
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return out;
}

torch::Tensor qutrit_apply_kraus_all_sites_cuda(
    torch::Tensor psi,
    torch::Tensor kraus,
    torch::Tensor rand,
    std::vector<int64_t> sites,
    int64_t n) {
  TORCH_CHECK(psi.is_cuda() && kraus.is_cuda() && rand.is_cuda(), "psi, kraus, and rand must be CUDA");
  TORCH_CHECK(psi.scalar_type() == torch::kComplexDouble, "psi must be complex128");
  TORCH_CHECK(kraus.scalar_type() == torch::kComplexDouble, "kraus must be complex128");
  TORCH_CHECK(rand.scalar_type() == torch::kFloat64, "rand must be float64");
  TORCH_CHECK(psi.dim() == 2, "psi must have shape [B, 3^n]");
  TORCH_CHECK(kraus.dim() == 3 && kraus.size(1) == 3 && kraus.size(2) == 3,
              "kraus must have shape [K, 3, 3]");
  validate_sites(sites, n, (int)n);
  const long long D = pow3_host((int)n);
  TORCH_CHECK(psi.size(1) == D, "psi second dimension must equal 3^n");
  const long long B = psi.size(0);
  const int K = (int)kraus.size(0);
  const long long S = (long long)sites.size();
  TORCH_CHECK(rand.dim() == 2 && rand.size(0) == S && rand.size(1) == B,
              "rand must have shape [num_sites, B]");

  auto current = psi.contiguous().clone();
  auto kc = kraus.contiguous();
  auto rc = rand.contiguous();
  auto tmp = torch::empty_like(current);
  auto opts_r = torch::TensorOptions().dtype(torch::kFloat64).device(psi.device());
  auto norms = torch::empty({B, K}, opts_r);
  auto inv_norm = torch::empty({B}, opts_r);
  auto opts_i = torch::TensorOptions().dtype(torch::kInt64).device(psi.device());
  auto selected = torch::empty({B}, opts_i);

  const int red_threads = 256;
  const int threads = 256;
  const long long select_blocks = (B + threads - 1) / threads;
  const long long total = B * D;
  const long long apply_blocks = (total + threads - 1) / threads;

  for (long long si = 0; si < S; ++si) {
    const int64_t site = sites[(size_t)si];
    const long long place = pow3_host((int)(n - 1 - site));
    qutrit_kraus_norm_kernel<<<dim3((unsigned int)B, (unsigned int)K), red_threads,
                               red_threads * sizeof(double), at::cuda::getCurrentCUDAStream()>>>(
        reinterpret_cast<const cplx*>(current.const_data_ptr<c10::complex<double>>()),
        reinterpret_cast<const cplx*>(kc.const_data_ptr<c10::complex<double>>()),
        norms.mutable_data_ptr<double>(), B, D, K, place);
    C10_CUDA_KERNEL_LAUNCH_CHECK();

    qutrit_kraus_select_kernel<<<(unsigned int)select_blocks, threads, 0,
                                 at::cuda::getCurrentCUDAStream()>>>(
        norms.const_data_ptr<double>(), rc.const_data_ptr<double>() + si * B,
        selected.mutable_data_ptr<int64_t>(), inv_norm.mutable_data_ptr<double>(), B, K);
    C10_CUDA_KERNEL_LAUNCH_CHECK();

    qutrit_kraus_apply_kernel<<<(unsigned int)apply_blocks, threads, 0,
                                at::cuda::getCurrentCUDAStream()>>>(
        reinterpret_cast<const cplx*>(current.const_data_ptr<c10::complex<double>>()),
        reinterpret_cast<const cplx*>(kc.const_data_ptr<c10::complex<double>>()),
        selected.const_data_ptr<int64_t>(), inv_norm.const_data_ptr<double>(),
        reinterpret_cast<cplx*>(tmp.mutable_data_ptr<c10::complex<double>>()),
        B, D, place);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
    std::swap(current, tmp);
  }
  return current;
}

torch::Tensor qutrit_run_cached_opstream_cuda(
    torch::Tensor psi,
    torch::Tensor op_kind,
    torch::Tensor op_site_ptr,
    torch::Tensor op_sites,
    torch::Tensor kraus,
    torch::Tensor rand,
    int64_t n) {
  TORCH_CHECK(psi.is_cuda() && kraus.is_cuda() && rand.is_cuda(), "psi, kraus, and rand must be CUDA");
  TORCH_CHECK(psi.scalar_type() == torch::kComplexDouble, "psi must be complex128");
  TORCH_CHECK(op_kind.scalar_type() == torch::kInt32, "op_kind must be int32");
  TORCH_CHECK(op_site_ptr.scalar_type() == torch::kInt32, "op_site_ptr must be int32");
  TORCH_CHECK(op_sites.scalar_type() == torch::kInt32, "op_sites must be int32");
  TORCH_CHECK(kraus.scalar_type() == torch::kComplexDouble, "kraus must be complex128");
  TORCH_CHECK(rand.scalar_type() == torch::kFloat64, "rand must be float64");
  TORCH_CHECK(psi.dim() == 2, "psi must have shape [B, 3^n]");
  TORCH_CHECK(op_kind.dim() == 1, "op_kind must have shape [O]");
  TORCH_CHECK(op_site_ptr.dim() == 1 && op_site_ptr.size(0) == op_kind.size(0) + 1,
              "op_site_ptr must have shape [O+1]");
  TORCH_CHECK(op_sites.dim() == 1, "op_sites must have shape [total_sites]");
  TORCH_CHECK(kraus.dim() == 3 && kraus.size(1) == 3 && kraus.size(2) == 3,
              "kraus must have shape [K, 3, 3]");
  const long long D = pow3_host((int)n);
  TORCH_CHECK(psi.size(1) == D, "psi second dimension must equal 3^n");
  const long long B = psi.size(0);
  const long long O = op_kind.size(0);
  const int K = (int)kraus.size(0);
  TORCH_CHECK(rand.dim() == 2 && rand.size(1) == B, "rand must have shape [num_kraus_site_draws, B]");

  auto current = psi.contiguous().clone();
  auto tmp = torch::empty_like(current);
  auto kinds = op_kind.contiguous();
  auto ptrs = op_site_ptr.contiguous();
  auto sites_t = op_sites.contiguous();
  auto kc = kraus.contiguous();
  auto rc = rand.contiguous();

  // Copy the tiny op stream to host so this host-side runner can launch kernels in order.
  auto kinds_h = kinds.is_cuda() ? kinds.cpu() : kinds;
  auto ptrs_h = ptrs.is_cuda() ? ptrs.cpu() : ptrs;
  auto sites_h = sites_t.is_cuda() ? sites_t.cpu() : sites_t;
  const int32_t* kinds_p = kinds_h.data_ptr<int32_t>();
  const int32_t* ptrs_p = ptrs_h.data_ptr<int32_t>();
  const int32_t* sites_p = sites_h.data_ptr<int32_t>();

  auto opts_r = torch::TensorOptions().dtype(torch::kFloat64).device(psi.device());
  auto norms = torch::empty({B, K}, opts_r);
  auto inv_norm = torch::empty({B}, opts_r);
  auto opts_i = torch::TensorOptions().dtype(torch::kInt64).device(psi.device());
  auto selected = torch::empty({B}, opts_i);

  const int red_threads = 256;
  const int threads = 256;
  const long long total = B * D;
  const long long blocks = (total + threads - 1) / threads;
  const long long select_blocks = (B + threads - 1) / threads;
  long long rand_row = 0;

  for (long long oi = 0; oi < O; ++oi) {
    const int kind = kinds_p[oi];
    const int start = ptrs_p[oi];
    const int end = ptrs_p[oi + 1];
    TORCH_CHECK(start >= 0 && end >= start && end <= op_sites.size(0), "invalid op site pointer");
    if (kind == OP_H || kind == OP_X) {
      TORCH_CHECK(end - start == 1, "H/X op must have exactly one site");
      const int site = sites_p[start];
      TORCH_CHECK(site >= 0 && site < n, "site out of range");
      const long long place = pow3_host((int)(n - 1 - site));
      qutrit_apply_cached_1q_gate_kernel<<<(unsigned int)blocks, threads, 0,
                                           at::cuda::getCurrentCUDAStream()>>>(
          reinterpret_cast<const cplx*>(current.const_data_ptr<c10::complex<double>>()),
          reinterpret_cast<cplx*>(tmp.mutable_data_ptr<c10::complex<double>>()),
          B, D, place, kind);
      C10_CUDA_KERNEL_LAUNCH_CHECK();
      std::swap(current, tmp);
    } else if (kind == OP_X_LAYER) {
      TORCH_CHECK(end > start && end - start <= MAX_PHASE_CONTROLS,
                  "X-layer op site count must be in [1, MAX_PHASE_CONTROLS]");
      long long places[MAX_PHASE_CONTROLS];
      for (int i = 0; i < MAX_PHASE_CONTROLS; ++i) places[i] = 1;
      for (int j = start; j < end; ++j) {
        const int site = sites_p[j];
        TORCH_CHECK(site >= 0 && site < n, "site out of range");
        places[j - start] = pow3_host((int)(n - 1 - site));
      }
      qutrit_apply_x_layer_kernel<<<(unsigned int)blocks, threads, 0,
                                    at::cuda::getCurrentCUDAStream()>>>(
          reinterpret_cast<const cplx*>(current.const_data_ptr<c10::complex<double>>()),
          reinterpret_cast<cplx*>(tmp.mutable_data_ptr<c10::complex<double>>()),
          B, D, end - start,
          places[0], places[1], places[2], places[3], places[4], places[5], places[6], places[7],
          places[8], places[9], places[10], places[11], places[12], places[13], places[14], places[15],
          places[16], places[17], places[18], places[19], places[20], places[21], places[22], places[23],
          places[24], places[25], places[26], places[27], places[28], places[29], places[30], places[31]);
      C10_CUDA_KERNEL_LAUNCH_CHECK();
      std::swap(current, tmp);
    } else if (kind == OP_ALL_ONES_PHASE) {
      TORCH_CHECK(end > start && end - start <= MAX_PHASE_CONTROLS,
                  "phase op site count must be in [1, MAX_PHASE_CONTROLS]");
      long long places[MAX_PHASE_CONTROLS];
      for (int i = 0; i < MAX_PHASE_CONTROLS; ++i) places[i] = 1;
      for (int j = start; j < end; ++j) {
        const int site = sites_p[j];
        TORCH_CHECK(site >= 0 && site < n, "site out of range");
        places[j - start] = pow3_host((int)(n - 1 - site));
      }
      qutrit_multi_controlled_phase_kernel<<<(unsigned int)blocks, threads, 0,
                                             at::cuda::getCurrentCUDAStream()>>>(
          reinterpret_cast<const cplx*>(current.const_data_ptr<c10::complex<double>>()),
          reinterpret_cast<cplx*>(tmp.mutable_data_ptr<c10::complex<double>>()),
          B, D, end - start, cplx(-1.0, 0.0),
          places[0], places[1], places[2], places[3], places[4], places[5], places[6], places[7],
          places[8], places[9], places[10], places[11], places[12], places[13], places[14], places[15],
          places[16], places[17], places[18], places[19], places[20], places[21], places[22], places[23],
          places[24], places[25], places[26], places[27], places[28], places[29], places[30], places[31]);
      C10_CUDA_KERNEL_LAUNCH_CHECK();
      std::swap(current, tmp);
    } else if (kind == OP_KRAUS_ALL_SITES) {
      TORCH_CHECK(end > start, "Kraus-all-sites op must have at least one site");
      for (int j = start; j < end; ++j) {
        TORCH_CHECK(rand_row < rand.size(0), "rand has too few rows for Kraus site draws");
        const int site = sites_p[j];
        TORCH_CHECK(site >= 0 && site < n, "site out of range");
        const long long place = pow3_host((int)(n - 1 - site));
        qutrit_kraus_norm_kernel<<<dim3((unsigned int)B, (unsigned int)K), red_threads,
                                   red_threads * sizeof(double), at::cuda::getCurrentCUDAStream()>>>(
            reinterpret_cast<const cplx*>(current.const_data_ptr<c10::complex<double>>()),
            reinterpret_cast<const cplx*>(kc.const_data_ptr<c10::complex<double>>()),
            norms.mutable_data_ptr<double>(), B, D, K, place);
        C10_CUDA_KERNEL_LAUNCH_CHECK();

        qutrit_kraus_select_kernel<<<(unsigned int)select_blocks, threads, 0,
                                     at::cuda::getCurrentCUDAStream()>>>(
            norms.const_data_ptr<double>(), rc.const_data_ptr<double>() + rand_row * B,
            selected.mutable_data_ptr<int64_t>(), inv_norm.mutable_data_ptr<double>(), B, K);
        C10_CUDA_KERNEL_LAUNCH_CHECK();

        qutrit_kraus_apply_kernel<<<(unsigned int)blocks, threads, 0,
                                    at::cuda::getCurrentCUDAStream()>>>(
            reinterpret_cast<const cplx*>(current.const_data_ptr<c10::complex<double>>()),
            reinterpret_cast<const cplx*>(kc.const_data_ptr<c10::complex<double>>()),
            selected.const_data_ptr<int64_t>(), inv_norm.const_data_ptr<double>(),
            reinterpret_cast<cplx*>(tmp.mutable_data_ptr<c10::complex<double>>()),
            B, D, place);
        C10_CUDA_KERNEL_LAUNCH_CHECK();
        std::swap(current, tmp);
        rand_row += 1;
      }
    } else {
      TORCH_CHECK(false, "unsupported op kind in qutrit_run_cached_opstream");
    }
  }
  TORCH_CHECK(rand_row == rand.size(0), "rand has unused rows after opstream execution");
  return current;
}

__global__ void qutrit_block_traj_opstream_kernel(
    cplx* __restrict__ buf_a,
    cplx* __restrict__ buf_b,
    const int32_t* __restrict__ op_kind,
    const int32_t* __restrict__ op_site_ptr,
    const int32_t* __restrict__ op_sites,
    const cplx* __restrict__ kraus,
    const double* __restrict__ rand,
    long long B,
    long long D,
    int O,
    int K,
    int n) {
  const long long b = blockIdx.x;
  if (b >= B) return;
  const int tid = threadIdx.x;
  extern __shared__ double shared_d[];
  double* scratch = shared_d;
  double* norms = shared_d + blockDim.x;
  __shared__ int selected_s;
  __shared__ double inv_norm_s;

  cplx* current = buf_a + b * D;
  cplx* tmp = buf_b + b * D;
  long long rand_row = 0;

  for (int oi = 0; oi < O; ++oi) {
    const int kind = op_kind[oi];
    const int start = op_site_ptr[oi];
    const int end = op_site_ptr[oi + 1];
    if (kind == OP_H || kind == OP_X) {
      const int site = op_sites[start];
      const long long place = pow3_device(n - 1 - site);
      for (long long basis = tid; basis < D; basis += blockDim.x) {
        const int row = (int)((basis / place) % 3LL);
        const long long base = basis - (long long)row * place;
        if (row == 2) {
          tmp[basis] = current[basis];
        } else if (kind == OP_H) {
          const double inv = 0.7071067811865475244;
          const cplx a0 = current[base];
          const cplx a1 = current[base + place];
          tmp[basis] = (row == 0) ? (a0 + a1) * inv : (a0 - a1) * inv;
        } else {
          const int col = 1 - row;
          tmp[basis] = current[base + (long long)col * place];
        }
      }
      __syncthreads();
      cplx* old = current;
      current = tmp;
      tmp = old;
      __syncthreads();
    } else if (kind == OP_X_LAYER) {
      for (long long basis = tid; basis < D; basis += blockDim.x) {
        long long src = basis;
        for (int j = start; j < end; ++j) {
          const int site = op_sites[j];
          const long long place = pow3_device(n - 1 - site);
          const int row = (int)((basis / place) % 3LL);
          if (row == 0) {
            src += place;
          } else if (row == 1) {
            src -= place;
          }
        }
        tmp[basis] = current[src];
      }
      __syncthreads();
      cplx* old = current;
      current = tmp;
      tmp = old;
      __syncthreads();
    } else if (kind == OP_ALL_ONES_PHASE) {
      for (long long basis = tid; basis < D; basis += blockDim.x) {
        bool fire = true;
        for (int j = start; j < end; ++j) {
          const int site = op_sites[j];
          const long long place = pow3_device(n - 1 - site);
          fire = fire && (((basis / place) % 3LL) == 1LL);
        }
        if (fire) current[basis] = current[basis] * cplx(-1.0, 0.0);
      }
      __syncthreads();
    } else if (kind == OP_KRAUS_ALL_SITES) {
      for (int j = start; j < end; ++j) {
        const int site = op_sites[j];
        const long long place = pow3_device(n - 1 - site);
        for (int k = 0; k < K; ++k) {
          const cplx* Kk = kraus + (long long)k * 9;
          double acc = 0.0;
          for (long long basis = tid; basis < D; basis += blockDim.x) {
            const int row = (int)((basis / place) % 3LL);
            const long long base = basis - (long long)row * place;
            cplx v(0.0, 0.0);
            for (int col = 0; col < 3; ++col) {
              v += Kk[row * 3 + col] * current[base + (long long)col * place];
            }
            acc += v.real() * v.real() + v.imag() * v.imag();
          }
          scratch[tid] = acc;
          __syncthreads();
          for (int stride = blockDim.x >> 1; stride > 0; stride >>= 1) {
            if (tid < stride) scratch[tid] += scratch[tid + stride];
            __syncthreads();
          }
          if (tid == 0) norms[k] = scratch[0];
          __syncthreads();
        }
        if (tid == 0) {
          double total = 0.0;
          for (int k = 0; k < K; ++k) total += norms[k];
          const double u = rand[rand_row * B + b] * total;
          double cdf = 0.0;
          int chosen = K - 1;
          for (int k = 0; k < K; ++k) {
            cdf += norms[k];
            if (u <= cdf) {
              chosen = k;
              break;
            }
          }
          selected_s = chosen;
          const double p = norms[chosen] > 1e-300 ? norms[chosen] : 1e-300;
          inv_norm_s = rsqrt(p);
        }
        __syncthreads();
        const cplx* Kk = kraus + (long long)selected_s * 9;
        for (long long basis = tid; basis < D; basis += blockDim.x) {
          const int row = (int)((basis / place) % 3LL);
          const long long base = basis - (long long)row * place;
          cplx v(0.0, 0.0);
          for (int col = 0; col < 3; ++col) {
            v += Kk[row * 3 + col] * current[base + (long long)col * place];
          }
          tmp[basis] = v * inv_norm_s;
        }
        __syncthreads();
        cplx* old = current;
        current = tmp;
        tmp = old;
        rand_row += 1;
        __syncthreads();
      }
    }
  }
  if (current != buf_a + b * D) {
    for (long long basis = tid; basis < D; basis += blockDim.x) {
      buf_a[b * D + basis] = current[basis];
    }
  }
}

torch::Tensor qutrit_run_block_traj_opstream_cuda(
    torch::Tensor psi,
    torch::Tensor op_kind,
    torch::Tensor op_site_ptr,
    torch::Tensor op_sites,
    torch::Tensor kraus,
    torch::Tensor rand,
    int64_t n) {
  TORCH_CHECK(psi.is_cuda() && op_kind.is_cuda() && op_site_ptr.is_cuda() && op_sites.is_cuda()
                  && kraus.is_cuda() && rand.is_cuda(),
              "psi, op metadata, kraus, and rand must be CUDA");
  TORCH_CHECK(psi.scalar_type() == torch::kComplexDouble, "psi must be complex128");
  TORCH_CHECK(op_kind.scalar_type() == torch::kInt32, "op_kind must be int32");
  TORCH_CHECK(op_site_ptr.scalar_type() == torch::kInt32, "op_site_ptr must be int32");
  TORCH_CHECK(op_sites.scalar_type() == torch::kInt32, "op_sites must be int32");
  TORCH_CHECK(kraus.scalar_type() == torch::kComplexDouble, "kraus must be complex128");
  TORCH_CHECK(rand.scalar_type() == torch::kFloat64, "rand must be float64");
  TORCH_CHECK(psi.dim() == 2, "psi must have shape [B, 3^n]");
  TORCH_CHECK(op_kind.dim() == 1, "op_kind must have shape [O]");
  TORCH_CHECK(op_site_ptr.dim() == 1 && op_site_ptr.size(0) == op_kind.size(0) + 1,
              "op_site_ptr must have shape [O+1]");
  TORCH_CHECK(op_sites.dim() == 1, "op_sites must have shape [total_sites]");
  TORCH_CHECK(kraus.dim() == 3 && kraus.size(1) == 3 && kraus.size(2) == 3,
              "kraus must have shape [K, 3, 3]");
  const long long D = pow3_host((int)n);
  TORCH_CHECK(psi.size(1) == D, "psi second dimension must equal 3^n");
  const long long B = psi.size(0);
  const int K = (int)kraus.size(0);
  TORCH_CHECK(rand.dim() == 2 && rand.size(1) == B, "rand must have shape [num_kraus_site_draws, B]");

  auto current = psi.contiguous().clone();
  auto tmp = torch::empty_like(current);
  auto kinds = op_kind.contiguous();
  auto ptrs = op_site_ptr.contiguous();
  auto sites_t = op_sites.contiguous();
  auto kc = kraus.contiguous();
  auto rc = rand.contiguous();

  const int threads = 256;
  const size_t shared_bytes = (size_t)(threads + K) * sizeof(double);
  qutrit_block_traj_opstream_kernel<<<(unsigned int)B, threads, shared_bytes,
                                      at::cuda::getCurrentCUDAStream()>>>(
      reinterpret_cast<cplx*>(current.mutable_data_ptr<c10::complex<double>>()),
      reinterpret_cast<cplx*>(tmp.mutable_data_ptr<c10::complex<double>>()),
      kinds.const_data_ptr<int32_t>(),
      ptrs.const_data_ptr<int32_t>(),
      sites_t.const_data_ptr<int32_t>(),
      reinterpret_cast<const cplx*>(kc.const_data_ptr<c10::complex<double>>()),
      rc.const_data_ptr<double>(),
      B, D, (int)op_kind.size(0), K, (int)n);
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return current;
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def("qutrit_apply_qubit_gate", &qutrit_apply_qubit_gate_cuda,
        "Apply a 1/2/3-qubit unitary on qutrit computational subspace (CUDA)");
  m.def("qutrit_multi_controlled_phase", &qutrit_multi_controlled_phase_cuda,
        "Apply a multi-controlled phase firing only on qutrit level |1> (CUDA)");
  m.def("qutrit_apply_kraus_site", &qutrit_apply_kraus_site_cuda,
        "Sample/apply one-site qutrit Kraus branch for batched MCWF (CUDA)");
  m.def("qutrit_apply_kraus_all_sites", &qutrit_apply_kraus_all_sites_cuda,
        "Sample/apply one-site qutrit Kraus branches over multiple sites for batched MCWF (CUDA)");
  m.def("qutrit_run_cached_opstream", &qutrit_run_cached_opstream_cuda,
        "Run a cached H/X/phase/Kraus qutrit MCWF op stream (CUDA host runner)");
  m.def("qutrit_run_block_traj_opstream", &qutrit_run_block_traj_opstream_cuda,
        "Run a cached H/X/phase/Kraus qutrit MCWF op stream in one block per trajectory (CUDA)");
}
