// Fused subsystem-Kraus application on batched density matrices.
//
// out[b, x, y] = sum_k sum_{u,v} K[k, tx, u] * rho[b, sub(x,u), sub(y,v)] * conj(K[k, ty, v])
//
// where tx/ty are the target-qubit bits of x/y (qubit 0 = most-significant bit,
// matching the package exact circuit simulator), and sub(x, u) replaces the target
// bits of x by the bits of u. Raw sum only — the caller hermitianizes (matching
// apply_kraus). Replaces embed_operator (kron + permute + contiguous) + einsum.

#include <torch/extension.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAException.h>
#include <c10/util/complex.h>
#include <cuda_runtime.h>

#include <vector>

using cplx = c10::complex<double>;

constexpr int MAX_TARGETS = 4;

__global__ void fused_local_kraus_kernel(
    const cplx* __restrict__ rho,    // [B, D, D] contiguous
    const cplx* __restrict__ kraus,  // [K, dt, dt] contiguous
    cplx* __restrict__ out,          // [B, D, D]
    const long long B,
    const long long D,
    const int K,
    const int m,
    const int dt,
    const long long s0,
    const long long s1,
    const long long s2,
    const long long s3) {
  const long long idx = blockIdx.x * (long long)blockDim.x + threadIdx.x;
  const long long total = B * D * D;
  if (idx >= total) return;
  const long long y = idx % D;
  const long long x = (idx / D) % D;
  const long long b = idx / (D * D);

  const long long shifts[MAX_TARGETS] = {s0, s1, s2, s3};

  long long tx = 0, ty = 0, xc = x, yc = y;
  for (int j = 0; j < m; ++j) {
    const long long s = shifts[j];
    tx = (tx << 1) | ((x >> s) & 1LL);
    ty = (ty << 1) | ((y >> s) & 1LL);
    xc &= ~(1LL << s);
    yc &= ~(1LL << s);
  }

  const cplx* rb = rho + b * D * D;
  cplx acc(0.0, 0.0);
  for (int k = 0; k < K; ++k) {
    const cplx* Kk = kraus + (long long)k * dt * dt;
    for (int u = 0; u < dt; ++u) {
      const cplx a = Kk[tx * dt + u];
      if (a.real() == 0.0 && a.imag() == 0.0) continue;
      long long xu = xc;
      for (int j = 0; j < m; ++j) xu |= (((long long)(u >> (m - 1 - j)) & 1LL) << shifts[j]);
      const cplx* row = rb + xu * D;
      for (int v = 0; v < dt; ++v) {
        const cplx c = Kk[ty * dt + v];
        if (c.real() == 0.0 && c.imag() == 0.0) continue;
        long long yv = yc;
        for (int j = 0; j < m; ++j) yv |= (((long long)(v >> (m - 1 - j)) & 1LL) << shifts[j]);
        const cplx cc(c.real(), -c.imag());  // conj
        acc += a * row[yv] * cc;
      }
    }
  }
  out[idx] = acc;
}

torch::Tensor fused_local_kraus_cuda(
    torch::Tensor rho, torch::Tensor kraus, std::vector<int64_t> targets, int64_t n) {
  TORCH_CHECK(rho.is_cuda() && kraus.is_cuda(), "fused_local_kraus: tensors must be CUDA");
  TORCH_CHECK(rho.scalar_type() == torch::kComplexDouble, "rho must be complex128");
  TORCH_CHECK(kraus.scalar_type() == torch::kComplexDouble, "kraus must be complex128");
  TORCH_CHECK(kraus.dim() == 3, "kraus must be [K, dt, dt]");
  const int m = (int)targets.size();
  TORCH_CHECK(m >= 1 && m <= MAX_TARGETS, "1..4 target qubits supported");
  const int dt = 1 << m;
  TORCH_CHECK(kraus.size(1) == dt && kraus.size(2) == dt, "kraus dims must match targets");

  auto rho3 = rho.dim() == 2 ? rho.unsqueeze(0) : rho;
  TORCH_CHECK(rho3.dim() == 3, "rho must be [D,D] or [B,D,D]");
  const long long D = rho3.size(-1);
  TORCH_CHECK(D == (1LL << n), "rho dim must be 2^n");
  const long long B = rho3.size(0);

  auto rc = rho3.contiguous();
  auto kc = kraus.contiguous();
  auto out = torch::empty_like(rc);

  long long sh[MAX_TARGETS] = {0, 0, 0, 0};
  for (int j = 0; j < m; ++j) {
    TORCH_CHECK(targets[j] >= 0 && targets[j] < n, "target out of range");
    sh[j] = (long long)(n - 1 - targets[j]);
  }

  const long long total = B * D * D;
  const int threads = 256;
  const long long blocks = (total + threads - 1) / threads;
  fused_local_kraus_kernel<<<(unsigned int)blocks, threads, 0,
                             at::cuda::getCurrentCUDAStream()>>>(
      reinterpret_cast<const cplx*>(rc.const_data_ptr<c10::complex<double>>()),
      reinterpret_cast<const cplx*>(kc.const_data_ptr<c10::complex<double>>()),
      reinterpret_cast<cplx*>(out.mutable_data_ptr<c10::complex<double>>()),
      B, D, (int)kraus.size(0), m, dt, sh[0], sh[1], sh[2], sh[3]);
  C10_CUDA_KERNEL_LAUNCH_CHECK();
  return rho.dim() == 2 ? out.squeeze(0) : out;
}
