// P4a state-vector Monte-Carlo (MCWF) leakage-teacher kernel  (Agent K).
//
// Block-per-trajectory quantum-trajectory sampler for the d3 XZZX qutrit teacher
// (9 data qutrits, 3^9 = 19683 amplitudes; LOCAL Wood-Gambetta leakage, no
// persistent ancilla).  One CUDA block evolves ONE shot's pure state vector; the
// block's threads cooperate over the 19683 amplitudes.  Per shot:
//
//   psi = |m>_L                                         (received, §8)
//   for r in 1..R:
//     (a) single-qutrit gate applies      (§2 gate_unitaries, strided subsystem)
//     (b) per-data-qutrit leakage Kraus-SAMPLING (§3, Born draw via curand)
//     (c) per-stabilizer measurement via the §4 ARM   (diagonal in the trit basis)
//   sampled terminal readout -> logical_flip = parity(data) XOR m   (§4 / Gate 3)
//
// Conventions (binding, see docs/nonpauli_teacher/p4a_build_contract.md):
//   * §1 index: qutrit 0 = MOST-significant trit, idx = sum_q t_q * 3^(8-q).  This
//     matches forward.exact.qutrit_dm._site_trit (place = 3^(n-1-site)).
//   * §4 arms are ALL DIAGONAL in the (Z-rotated) trit basis: X-supports are
//     Hadamard-rotated to Z first (|2> inert under H).  Each measurement is an
//     elementwise sqrt(E_s) on psi.  Arms A/B1/B2 differ only by the per-qutrit
//     |2>-parity weight d(|2>) (A=1-2b, B1=+1, B2=-1).  Arm C = a leak-flag
//     projection onto a sampled leakage pattern, then Arm-A's sqrt(E_s).
//   * §5 draw order is NORMATIVE: per round, (i) gates (no draws); (ii) q=0..8 one
//     leakage draw each; (iii) stab=0..7 the measurement draw(s) (C: leak-flag
//     draw(s) in supp order, THEN the outcome draw).  After round R: terminal-
//     readout draws (data-qutrit order).  The kernel consumes uniforms in EXACTLY
//     this order so a host-pre-generated stream reproduces it bit-for-bit (§9).
//
// dtype: complex128 default (this .cu is compiled per-precision via -DSV_REAL=...;
// the loader builds a c128 module and, gated, a c64 module).  No CPU fallback in
// the compute path (GPU-only rule).  Matches the JIT compile/load style of
// forward/accel.py + fused_kraus_local.cu.

#include <torch/extension.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAException.h>
#include <c10/util/complex.h>
#include <cuda_runtime.h>
#include <curand_kernel.h>

#include <vector>

// ---- precision switch (the loader sets SV_REAL; default complex128) ---------
#ifndef SV_REAL
#define SV_REAL double
#endif
using real_t = SV_REAL;
using cplx = c10::complex<real_t>;

// ---- fixed d3 dimensions (specialized circuit) ------------------------------
#ifndef SV_NDATA
#define SV_NDATA 9
#endif
#ifndef SV_DIM
#define SV_DIM 19683  // 3^9
#endif
constexpr int N_DATA = SV_NDATA;
constexpr long long DIM = SV_DIM;

// Max marshalling bounds (d3 fits well inside these; checked host-side).
constexpr int MAX_STAB = 16;        // 8 used
constexpr int MAX_SUPP = 8;         // stabilizer support fan (<=4 for d3)
constexpr int MAX_KRAUS = 8;        // WG channel rank 2..5
constexpr int MAX_GATES_PER_RND = 64;
constexpr int MAX_LOG_SUPP = 12;    // logical support (3 for d3)
constexpr int THREADS = 256;        // threads per block (per trajectory)

// 3^k powers (host+device); POW3[k] = 3^k.
__device__ __constant__ long long POW3[10] =
    {1, 3, 9, 27, 81, 243, 729, 2187, 6561, 19683};

// readout_conv codes
constexpr int RC_BIASED_B = 0;
constexpr int RC_HALF = 1;
// arm codes
constexpr int ARM_A = 0;
constexpr int ARM_C = 1;
constexpr int ARM_B1 = 2;
constexpr int ARM_B2 = 3;

// P4a WITHIN-CYCLE op kinds (the per-qutrit gate+leak CSR; Agent H's
// WithinCycleMarshalled format, sv_sampler.WC_OP_GATE / WC_OP_LEAK).  An op is
// either a single-qutrit GATE (apply gate_unitaries[op_uid] on op_site) or a
// LEAK sub-step (Kraus-sample the exp(L/4) leak_kraus on op_site; op_uid unused).
constexpr int WC_OP_GATE = 0;
constexpr int WC_OP_LEAK = 1;

// ----------------------------------------------------------------------------- //
//  Flat schedule passed once per launch (POD, no Python objects).               //
//  All arrays are device pointers; the host (Agent H) marshals them from        //
//  XZZXSchedule + leakage_kraus_torch (§2/§3).                                   //
// ----------------------------------------------------------------------------- //
struct SchedSpec {
  int R;
  int n_data;          // = 9
  int n_stab;          // = 8

  // gates: round_gates_flat is a concatenation; round_gptr[r] .. round_gptr[r+1]
  // index into (gate_uid[], gate_site[]).  gate_uid indexes gate_unitaries.
  // (LUMPED per-round model: gates -> ONE full-cycle leak -> measure.)
  const int* round_gptr;     // [R+1]
  const int* gate_uid;       // [n_gate_apply]
  const int* gate_site;      // [n_gate_apply]
  const cplx* gate_unitaries;// [n_gate, 3, 3]

  // P4a WITHIN-CYCLE per-qutrit gate+leak CSR (Agent H's WithinCycleMarshalled).
  // TWO op-segments per round split by the stabilizer measurement: round r's
  // PRE-measure ops = [round_op_ptr[2r], round_op_ptr[2r+1]); its POST-measure
  // ops = [round_op_ptr[2r+1], round_op_ptr[2r+2]).  Each op t is the triple
  // (op_kind[t], op_uid[t], op_site[t]) with op_kind in {WC_OP_GATE, WC_OP_LEAK}.
  // Used by sv_traj_wc_kernel; null on the lumped path.
  const int* round_op_ptr;   // [2R+1]
  const int* op_kind;        // [T]  WC_OP_GATE | WC_OP_LEAK
  const int* op_uid;         // [T]  gate-unitary index (GATE; 0 for LEAK)
  const int* op_site;        // [T]  data-qutrit site

  // stabilizers (in schedule order).  supp_len[s] sites in supp[s*MAX_SUPP + .],
  // is_x[s*MAX_SUPP + .] = 1 if that support site is X-type (needs H rotate).
  int stab_supp_len[MAX_STAB];
  int stab_supp[MAX_STAB * MAX_SUPP];
  int stab_supp_isx[MAX_STAB * MAX_SUPP];

  // leakage Kraus (§3): n_kraus (3,3) matrices, row-major.
  int n_kraus;
  const cplx* kraus;         // [n_kraus, 3, 3]

  // logical observable (§4 terminal readout).
  int log_supp_len;
  int log_supp[MAX_LOG_SUPP];
  int log_supp_isx[MAX_LOG_SUPP];

  // instrument
  int arm;                   // ARM_A/C/B1/B2
  real_t b;                  // leaked-readout bias (A/C only)
  int readout_conv;          // RC_BIASED_B / RC_HALF
  int logical_m;             // prepared logical value m in {0,1}

  // RNG
  unsigned long long base_seed;
  long long shot_id_offset;

  // optional host-pre-generated uniform stream (§9 bit-faithful).  If non-null,
  // the kernel consumes uniforms from urandom[shot*urandom_stride + .] in the §5
  // order instead of curand.  urandom_stride is the per-shot stream length.
  const real_t* urandom;     // may be nullptr
  long long urandom_stride;
};

// ----------------------------------------------------------------------------- //
//  Device helpers                                                               //
// ----------------------------------------------------------------------------- //

// trit value of qutrit `site` (qutrit 0 = MSF) for basis index idx.
__device__ __forceinline__ int site_trit(long long idx, int site, int n) {
  return (int)((idx / POW3[n - 1 - site]) % 3);
}

// d_q(t): per-qutrit Z-parity weight for the diagonal POVM.  +1 (t=0), -1 (t=1),
// d2 (t=2) where d2 is arm-dependent (A/C: 1-2b, B1: +1, B2: -1).
__device__ __forceinline__ real_t parity_weight(int t, real_t d2) {
  return (t == 0) ? (real_t)1.0 : ((t == 1) ? (real_t)(-1.0) : d2);
}

// Terminal-readout POVM-Kraus diagonal weight sqrt(F_bit)[t] for the biased-b
// readout F1 = |1><1| + b|2><2|, F0 = |0><0| + (1-b)|2><2| (F0+F1=I).  The
// post-measurement collapse onto a SAMPLED bit is psi[c] <- sqrt(F_bit)[t_q] psi[c]
// (the proper square-root POVM instrument), NOT "keep |2> at full weight".  Per
// trit t and drawn `bit` (b_eff already folds the RC_HALF "half" convention, b=0.5):
//   t == bit (t in {0,1}) -> 1 ;  the other {0,1} value -> 0 ;
//   t == 2 -> sqrt(b_eff) if bit==1 else sqrt(1 - b_eff).
__device__ __forceinline__ real_t readout_sqrtF(int t, int bit, real_t b_eff) {
  if (t == 2) return sqrt(bit ? b_eff : ((real_t)1.0 - b_eff));
  return ((t & 1) == bit) ? (real_t)1.0 : (real_t)0.0;
}

// A per-shot uniform-draw stream: curand (production) OR a host-pre-generated
// buffer (the §9 bit-faithful test).  Draws are consumed in the §5 NORMATIVE
// order by the single call site sequence below — so the two modes are identical
// given the same uniform sequence.
struct DrawStream {
  curandStatePhilox4_32_10_t st;
  const real_t* buf;   // nullptr => curand mode
  long long pos;       // index into buf (host stream mode)
  long long cap;       // buf length (bounds check)
  __device__ __forceinline__ real_t next() {
    if (buf != nullptr) {
      // host-pre-generated stream: consume in order (clamp at cap-1 defensively).
      long long p = pos < cap ? pos : (cap - 1);
      pos++;
      return buf[p];
    }
    // curand uniform in (0,1].  Use the double generator for c128; for c64 a
    // single-precision draw keeps the stream length identical (one draw == one u).
    return (real_t)curand_uniform_double(&st);
  }
};

// Block-cooperative sum reduction of a per-thread partial into a shared scalar.
// Returns the full block sum to every thread.  `scratch` has >= THREADS reals.
__device__ __forceinline__ real_t block_reduce_sum(real_t v, real_t* scratch) {
  int tid = threadIdx.x;
  scratch[tid] = v;
  __syncthreads();
  for (int s = blockDim.x >> 1; s > 0; s >>= 1) {
    if (tid < s) scratch[tid] += scratch[tid + s];
    __syncthreads();
  }
  real_t total = scratch[0];
  __syncthreads();
  return total;
}

// ----------------------------------------------------------------------------- //
//  Single-qutrit gate apply on the state vector (strided subsystem).            //
//  psi[idx with trit a at site] <- sum_b U[a,b] psi[idx with trit b at site].    //
//  State-vector analog of qutrit_dm.apply_local_op's ket contraction.  Each      //
//  block thread owns a set of (high, low) outer indices; the 3 site-trits of a   //
//  fixed (high, low) form one length-3 fibre contracted by U.                    //
// ----------------------------------------------------------------------------- //
__device__ void apply_gate_block(cplx* psi, const cplx* U, int site, int n,
                                 cplx* psi_tmp) {
  // place = stride between consecutive trits of `site`; group = number of
  // (high,low) fibres = DIM/3.
  const long long place = POW3[n - 1 - site];
  const long long ngroup = DIM / 3;
  const int tid = threadIdx.x;
  const int nth = blockDim.x;
  // For each fibre f in [0,ngroup): high = f / place, low = f % place; the three
  // amplitudes live at base + t*place, base = high*(3*place) + low.
  for (long long f = tid; f < ngroup; f += nth) {
    const long long high = f / place;
    const long long low = f % place;
    const long long base = high * (3 * place) + low;
    const cplx a0 = psi[base + 0 * place];
    const cplx a1 = psi[base + 1 * place];
    const cplx a2 = psi[base + 2 * place];
    // out[a] = sum_b U[a,b] in[b]
#pragma unroll
    for (int arow = 0; arow < 3; ++arow) {
      cplx acc = U[arow * 3 + 0] * a0 + U[arow * 3 + 1] * a1 + U[arow * 3 + 2] * a2;
      psi_tmp[base + arow * place] = acc;
    }
  }
  __syncthreads();
  // copy back (psi_tmp holds the full updated state for this site's fibres; every
  // amplitude is written exactly once above, so a straight copy is correct).
  for (long long i = tid; i < DIM; i += nth) psi[i] = psi_tmp[i];
  __syncthreads();
}

// Renormalize psi to unit norm given the (already reduced) total squared-norm.
__device__ __forceinline__ void renorm_block(cplx* psi, real_t sqnorm) {
  const int tid = threadIdx.x;
  const int nth = blockDim.x;
  real_t inv = (sqnorm > (real_t)0) ? (real_t)1.0 / sqrt(sqnorm) : (real_t)1.0;
  for (long long i = tid; i < DIM; i += nth) psi[i] = psi[i] * inv;
  __syncthreads();
}

// ----------------------------------------------------------------------------- //
//  Leakage Kraus-sampling on data qutrit `site` (§3).                           //
//  Born: p_k = ||K_k psi_sub||^2 over the WHOLE state (K_k acts on `site`).      //
//  Draw k ~ p_k, set psi <- K_k psi / sqrt(p_k).  K_k is (3,3); the sub-apply is //
//  the same strided fibre contraction as a gate (single Kraus), then renorm.     //
//  NOTE: sum_k p_k = <psi| sum_k K_k^dag K_k |psi> = 1 (CPTP), so the draw is a   //
//  proper categorical over the n_kraus branches.                                 //
// ----------------------------------------------------------------------------- //
__device__ void leakage_sample_block(cplx* psi, const SchedSpec* sp, int site,
                                     DrawStream* rng, cplx* psi_tmp,
                                     real_t* scratch) {
  const int tid = threadIdx.x;
  const int nth = blockDim.x;
  const int nk = sp->n_kraus;
  const long long place = POW3[sp->n_data - 1 - site];
  const long long ngroup = DIM / 3;

  // 1) per-branch squared norm p_k = sum_idx |(K_k psi)[idx]|^2, all in one pass
  //    over the fibres (compute the 3-vector K_k @ (a0,a1,a2) and accumulate).
  //    We need all p_k before drawing, so accumulate into a per-thread array then
  //    block-reduce each.  nk <= MAX_KRAUS.
  real_t pk[MAX_KRAUS];
#pragma unroll
  for (int k = 0; k < MAX_KRAUS; ++k) pk[k] = (real_t)0.0;

  for (long long f = tid; f < ngroup; f += nth) {
    const long long high = f / place;
    const long long low = f % place;
    const long long base = high * (3 * place) + low;
    const cplx a0 = psi[base + 0 * place];
    const cplx a1 = psi[base + 1 * place];
    const cplx a2 = psi[base + 2 * place];
    for (int k = 0; k < nk; ++k) {
      const cplx* Kk = sp->kraus + (long long)k * 9;
#pragma unroll
      for (int arow = 0; arow < 3; ++arow) {
        cplx out = Kk[arow * 3 + 0] * a0 + Kk[arow * 3 + 1] * a1 + Kk[arow * 3 + 2] * a2;
        pk[k] += out.real() * out.real() + out.imag() * out.imag();
      }
    }
  }
  // block-reduce each p_k into a shared value visible to all threads
  real_t pk_full[MAX_KRAUS];
  for (int k = 0; k < nk; ++k) pk_full[k] = block_reduce_sum(pk[k], scratch);

  // 2) draw k ~ pk_full (cumulative).  ONE uniform consumed (§5: one leakage draw
  //    per data qutrit per round).  Drawn by thread 0, broadcast via shared.
  __shared__ int chosen_k;
  __shared__ real_t chosen_norm;
  if (tid == 0) {
    real_t u = rng->next();
    real_t tot = (real_t)0.0;
    for (int k = 0; k < nk; ++k) tot += pk_full[k];
    real_t target = u * tot;  // guard against tot != 1 by FP roundoff
    real_t cum = (real_t)0.0;
    int sel = nk - 1;
    for (int k = 0; k < nk; ++k) {
      cum += pk_full[k];
      if (target <= cum) { sel = k; break; }
    }
    chosen_k = sel;
    chosen_norm = pk_full[sel];
  }
  __syncthreads();

  // 3) apply K_chosen on `site` (single-Kraus strided apply) then renorm by
  //    sqrt(chosen_norm) (== ||K_k psi||).
  const cplx* Kk = sp->kraus + (long long)chosen_k * 9;
  for (long long f = tid; f < ngroup; f += nth) {
    const long long high = f / place;
    const long long low = f % place;
    const long long base = high * (3 * place) + low;
    const cplx a0 = psi[base + 0 * place];
    const cplx a1 = psi[base + 1 * place];
    const cplx a2 = psi[base + 2 * place];
#pragma unroll
    for (int arow = 0; arow < 3; ++arow) {
      cplx acc = Kk[arow * 3 + 0] * a0 + Kk[arow * 3 + 1] * a1 + Kk[arow * 3 + 2] * a2;
      psi_tmp[base + arow * place] = acc;
    }
  }
  __syncthreads();
  for (long long i = tid; i < DIM; i += nth) psi[i] = psi_tmp[i];
  __syncthreads();
  renorm_block(psi, chosen_norm);
}

// ----------------------------------------------------------------------------- //
//  Hadamard on the {0,1} block (|2> inert), used to rotate X-supports to Z.      //
//  H = (1/sqrt2)[[1,1,0],[1,-1,0],[0,0,sqrt2]].                                  //
// ----------------------------------------------------------------------------- //
__device__ void hadamard_block(cplx* psi, int site, int n, cplx* psi_tmp) {
  const real_t inv2 = (real_t)(0.7071067811865475244);  // 1/sqrt(2)
  cplx H[9];
#pragma unroll
  for (int i = 0; i < 9; ++i) H[i] = cplx((real_t)0, (real_t)0);
  H[0] = cplx(inv2, 0); H[1] = cplx(inv2, 0);
  H[3] = cplx(inv2, 0); H[4] = cplx(-inv2, 0);
  H[8] = cplx((real_t)1.0, 0);
  apply_gate_block(psi, H, site, n, psi_tmp);
}

// ----------------------------------------------------------------------------- //
//  One stabilizer measurement (§4).  Diagonal in the trit basis after X-supports //
//  are rotated to Z.  Builds P(c) = prod_{q in supp} d_q(t_q); E_0[c]=1/2(1+P),   //
//  E_1[c]=1/2(1-P).  Samples s ~ p(s)=sum_c E_s[c]|psi[c]|^2, then               //
//  psi[c] <- sqrt(E_s[c]) psi[c], renorm.  Arm C additionally projects onto a     //
//  sampled leak-flag pattern L before the sqrt(E_s) step.                        //
//  Returns the sampled syndrome bit (0/1) on thread 0 (broadcast via shared).    //
// ----------------------------------------------------------------------------- //
__device__ int measure_stab_block(cplx* psi, const SchedSpec* sp, int s_idx,
                                  DrawStream* rng, cplx* psi_tmp,
                                  real_t* scratch) {
  const int tid = threadIdx.x;
  const int nth = blockDim.x;
  const int n = sp->n_data;
  const int slen = sp->stab_supp_len[s_idx];
  const int* supp = sp->stab_supp + s_idx * MAX_SUPP;
  const int* isx = sp->stab_supp_isx + s_idx * MAX_SUPP;

  // arm-dependent d_q(2)
  real_t d2;
  if (sp->arm == ARM_B1) d2 = (real_t)1.0;
  else if (sp->arm == ARM_B2) d2 = (real_t)(-1.0);
  else d2 = (real_t)1.0 - (real_t)2.0 * sp->b;   // A and C

  // rotate X-type support sites into the Z basis (H; |2> inert)
  for (int j = 0; j < slen; ++j)
    if (isx[j]) hadamard_block(psi, supp[j], n, psi_tmp);

  // ---- Arm C: leak-flag projection onto a sampled leakage pattern L ⊆ supp ----
  // For each support qutrit q (in supp order) sample whether it is leaked (|2>)
  // with prob = leaked-population there; project psi onto the chosen pattern.
  // This collapses |0>/|2> and |1>/|2> coherence on the support (keeps {0,1}
  // coherence).  §5: the leak-flag draw(s) come BEFORE the outcome draw, in supp
  // order.  Implemented as a per-site projection: draw l_q in {0,1}, then zero all
  // amplitudes whose trit at q is (==2) != l_q  (l_q=1 keeps only t==2; l_q=0
  // keeps only t in {0,1}).  The per-site leaked prob is the current population.
  __shared__ int leakflag[MAX_SUPP];
  if (sp->arm == ARM_C) {
    for (int j = 0; j < slen; ++j) {
      int q = supp[j];
      // population of |2> at q over the current (normalized) psi
      real_t p2 = (real_t)0.0;
      for (long long i = tid; i < DIM; i += nth) {
        if (site_trit(i, q, n) == 2) {
          cplx a = psi[i];
          p2 += a.real() * a.real() + a.imag() * a.imag();
        }
      }
      real_t p2_full = block_reduce_sum(p2, scratch);
      if (tid == 0) {
        real_t u = rng->next();          // one leak-flag draw per support site
        leakflag[j] = (u < p2_full) ? 1 : 0;
      }
      __syncthreads();
      // project: keep trit==2 iff leakflag, else keep trit in {0,1}
      int lf = leakflag[j];
      real_t keepnorm = (real_t)0.0;
      for (long long i = tid; i < DIM; i += nth) {
        int t = site_trit(i, q, n);
        bool keep = lf ? (t == 2) : (t != 2);
        if (!keep) psi[i] = cplx((real_t)0, (real_t)0);
        else { cplx a = psi[i]; keepnorm += a.real() * a.real() + a.imag() * a.imag(); }
      }
      real_t kn = block_reduce_sum(keepnorm, scratch);
      renorm_block(psi, kn);
    }
  }

  // ---- diagonal outcome probabilities p(s) = sum_c E_s[c] |psi[c]|^2 -----------
  // E_0[c] = 1/2(1 + P(c)), E_1 = 1/2(1 - P(c)).  Compute w0 = sum_c E_0[c]|psi|^2.
  real_t w0 = (real_t)0.0, wtot = (real_t)0.0;
  for (long long i = tid; i < DIM; i += nth) {
    cplx a = psi[i];
    real_t amp2 = a.real() * a.real() + a.imag() * a.imag();
    real_t P = (real_t)1.0;
    for (int j = 0; j < slen; ++j) P *= parity_weight(site_trit(i, supp[j], n), d2);
    real_t e0 = (real_t)0.5 * ((real_t)1.0 + P);
    w0 += e0 * amp2;
    wtot += amp2;
  }
  real_t w0_full = block_reduce_sum(w0, scratch);
  real_t wt_full = block_reduce_sum(wtot, scratch);

  // ---- sample s (one outcome draw) --------------------------------------------
  __shared__ int sbit;
  if (tid == 0) {
    real_t u = rng->next();              // one outcome draw per stabilizer
    real_t p0 = (wt_full > (real_t)0) ? (w0_full / wt_full) : (real_t)0.5;
    sbit = (u < p0) ? 0 : 1;
  }
  __syncthreads();

  // ---- post-measurement update psi[c] <- sqrt(E_s[c]) psi[c], renorm ----------
  const real_t sgn = (sbit == 0) ? (real_t)1.0 : (real_t)(-1.0);
  real_t newnorm = (real_t)0.0;
  for (long long i = tid; i < DIM; i += nth) {
    real_t P = (real_t)1.0;
    for (int j = 0; j < slen; ++j) P *= parity_weight(site_trit(i, supp[j], n), d2);
    real_t es = (real_t)0.5 * ((real_t)1.0 + sgn * P);
    real_t se = sqrt(es > (real_t)0 ? es : (real_t)0);
    cplx a = psi[i] * se;
    psi[i] = a;
    newnorm += a.real() * a.real() + a.imag() * a.imag();
  }
  real_t nn = block_reduce_sum(newnorm, scratch);
  renorm_block(psi, nn);

  // rotate X-type supports back (H is its own inverse on {0,1})
  for (int j = 0; j < slen; ++j)
    if (isx[j]) hadamard_block(psi, supp[j], n, psi_tmp);

  return sbit;
}

// ----------------------------------------------------------------------------- //
//  Terminal transversal data readout (§4 / Gate 3).                             //
//  Sample each data qutrit's computational bit (the leaked convention: biased-b  //
//  or 50/50) by collapsing the state qutrit-by-qutrit, then compute the logical  //
//  parity over the logical support and return parity XOR m.                      //
//  Logical X-supports are rotated to Z first (read parity in the Z basis).       //
//  §5: terminal-readout draws in data-qutrit order (q=0..8).                     //
// ----------------------------------------------------------------------------- //
__device__ int terminal_readout_block(cplx* psi, const SchedSpec* sp,
                                      DrawStream* rng, cplx* psi_tmp,
                                      real_t* scratch) {
  const int tid = threadIdx.x;
  const int nth = blockDim.x;
  const int n = sp->n_data;

  // rotate logical X-supports into the Z basis (so the logical parity is a Z
  // parity over the sampled trit bits).
  for (int j = 0; j < sp->log_supp_len; ++j)
    if (sp->log_supp_isx[j]) hadamard_block(psi, sp->log_supp[j], n, psi_tmp);

  // Biased-b readout POVM F1=|1><1|+b|2><2|, F0=|0><0|+(1-b)|2><2| (F0+F1=I).
  // The RC_HALF "half" convention is b=0.5-equivalent (|2> reads 0/1 evenly), so
  // fold it into a single effective bias b_eff used for BOTH the sampling weight
  // pb = <psi|F_1|psi> and the post-measurement sqrt(F_bit) collapse — keeping the
  // draw and the instrument consistent.
  const real_t b_eff = (sp->readout_conv == RC_HALF) ? (real_t)0.5 : sp->b;

  // sample a definite bit for every data qutrit in order (§5 draw order: all 9).
  // bit(t): t==0 -> 0, t==1 -> 1, t==2 -> leaked convention (biased-b or half).
  // We collapse qutrit q onto a sampled bit with the proper sqrt(F_bit) POVM-Kraus
  // update so later qutrits' marginals are conditioned (the canonical product-POVM
  // terminal readout; sequential sqrt(F) over disjoint sites == prod_q F_bit_q).
  __shared__ int qbit[16];
  for (int q = 0; q < n; ++q) {
    // P(bit=1) at q = <psi|F_1|psi> = sum_c (|psi[c]|^2 * F1_weight(t_q)); the
    // F1 diagonal weight is [t==1] + b_eff*[t==2] (and 0 for t==0).
    real_t w1 = (real_t)0.0, wt = (real_t)0.0;
    for (long long i = tid; i < DIM; i += nth) {
      cplx a = psi[i];
      real_t amp2 = a.real() * a.real() + a.imag() * a.imag();
      int t = site_trit(i, q, n);
      real_t pr1 = (t == 1) ? (real_t)1.0 : ((t == 2) ? b_eff : (real_t)0.0);
      w1 += pr1 * amp2;
      wt += amp2;
    }
    real_t w1f = block_reduce_sum(w1, scratch);
    real_t wtf = block_reduce_sum(wt, scratch);
    if (tid == 0) {
      real_t u = rng->next();            // one terminal draw per data qutrit
      real_t p1 = (wtf > (real_t)0) ? (w1f / wtf) : (real_t)0.5;
      qbit[q] = (u < p1) ? 1 : 0;
    }
    __syncthreads();
    // post-measurement collapse: psi[c] <- sqrt(F_bit)[t_q] psi[c], then renorm.
    // For the drawn bit, a {0,1} trit matching the bit survives (weight 1), the
    // other {0,1} trit is killed (weight 0), and a leaked |2> is kept at weight
    // sqrt(b_eff) (bit==1) / sqrt(1-b_eff) (bit==0) — NOT full weight.  This is the
    // biased-b product-POVM instrument (reproduces the canonical terminal readout
    // to FP round-off, including b=1 where |2> survives ONLY in the bit==1 branch).
    int bq = qbit[q];
    real_t kn = (real_t)0.0;
    for (long long i = tid; i < DIM; i += nth) {
      int t = site_trit(i, q, n);
      real_t w = readout_sqrtF(t, bq, b_eff);
      cplx a = psi[i] * w;
      psi[i] = a;
      kn += a.real() * a.real() + a.imag() * a.imag();
    }
    real_t knf = block_reduce_sum(kn, scratch);
    renorm_block(psi, knf);
  }

  // logical parity = XOR of the sampled bits over the logical support.
  int parity = 0;
  if (tid == 0) {
    for (int j = 0; j < sp->log_supp_len; ++j) parity ^= (qbit[sp->log_supp[j]] & 1);
  }
  // broadcast parity via shared
  __shared__ int sh_parity;
  if (tid == 0) sh_parity = parity;
  __syncthreads();
  return (sh_parity ^ (sp->logical_m & 1)) & 1;
}

// ----------------------------------------------------------------------------- //
//  The trajectory kernel: one block per shot.                                   //
//  codestate is the SHARED |m>_L pure SV (same for every shot in the launch);    //
//  each block copies it into a per-block working buffer in global scratch.       //
//  Output: packed bits per shot (§6) — R*n_stab syndrome bits + 1 logical_flip,  //
//  written by thread 0 into out_bits[shot * out_stride + .].  norm_drift[shot]    //
//  records |1 - <psi|psi>| just before the terminal readout (diag).              //
// ----------------------------------------------------------------------------- //
__global__ void sv_traj_kernel(
    const cplx* __restrict__ codestate,   // [DIM]
    cplx* __restrict__ work,              // [num_blocks * DIM] scratch state
    cplx* __restrict__ worktmp,           // [num_blocks * DIM] scratch tmp
    const SchedSpec sp,                   // by value (POD; arrays are device ptrs)
    unsigned char* __restrict__ out_bits, // [num_shots * out_stride]
    long long out_stride,
    real_t* __restrict__ norm_drift,      // [num_shots] diag
    long long num_shots) {
  const long long shot = blockIdx.x;      // wave maps block -> local shot
  if (shot >= num_shots) return;
  const long long shot_id = sp.shot_id_offset + shot;
  const int tid = threadIdx.x;
  const int nth = blockDim.x;

  extern __shared__ real_t scratch[];     // [THREADS] reduction scratch

  cplx* psi = work + shot * DIM;
  cplx* psi_tmp = worktmp + shot * DIM;

  // load |m>_L
  for (long long i = tid; i < DIM; i += nth) psi[i] = codestate[i];
  __syncthreads();

  // RNG: one stream per block, keyed by hash(base_seed, shot_id) — independent of
  // launch/wave layout (§5).  Philox is counter-based: seed=base_seed, subsequence
  // = shot_id gives a per-shot-deterministic stream.
  DrawStream rng;
  rng.buf = sp.urandom;
  rng.cap = sp.urandom_stride;
  rng.pos = 0;
  if (sp.urandom != nullptr) {
    rng.buf = sp.urandom + shot * sp.urandom_stride;
  } else {
    // hash(base_seed, shot_id): fold shot_id into both seed and subsequence so the
    // stream depends on the GLOBAL shot index, not the block index.
    curand_init(sp.base_seed ^ (unsigned long long)(shot_id * 0x9E3779B97F4A7C15ULL),
                (unsigned long long)shot_id, 0ULL, &rng.st);
  }

  long long bitpos = 0;  // running index into this shot's syndrome bit-array

  for (int r = 0; r < sp.R; ++r) {
    // (a) gate applies for round r
    const int g0 = sp.round_gptr[r];
    const int g1 = sp.round_gptr[r + 1];
    for (int g = g0; g < g1; ++g) {
      const int uid = sp.gate_uid[g];
      const int site = sp.gate_site[g];
      const cplx* U = sp.gate_unitaries + (long long)uid * 9;
      apply_gate_block(psi, U, site, sp.n_data, psi_tmp);
    }
    // (b) per-data-qutrit leakage Kraus-sampling (q = 0..n_data-1)
    for (int q = 0; q < sp.n_data; ++q)
      leakage_sample_block(psi, &sp, q, &rng, psi_tmp, scratch);
    // (c) per-stabilizer measurement (schedule order)
    for (int s = 0; s < sp.n_stab; ++s) {
      int bit = measure_stab_block(psi, &sp, s, &rng, psi_tmp, scratch);
      if (tid == 0) {
        long long byte = bitpos >> 3;
        int off = (int)(bitpos & 7);
        // set/clear the bit (out_bits pre-zeroed host-side; we OR in 1s)
        if (bit) out_bits[shot * out_stride + byte] |= (unsigned char)(1u << off);
      }
      bitpos++;
    }
  }

  // norm drift diagnostic (squared-norm just before terminal readout)
  real_t sq = (real_t)0.0;
  for (long long i = tid; i < DIM; i += nth) {
    cplx a = psi[i];
    sq += a.real() * a.real() + a.imag() * a.imag();
  }
  real_t sqf = block_reduce_sum(sq, scratch);
  if (tid == 0) norm_drift[shot] = fabs((real_t)1.0 - sqf);

  // terminal readout -> logical flip (Gate 3)
  int flip = terminal_readout_block(psi, &sp, &rng, psi_tmp, scratch);
  if (tid == 0) {
    // logical_flip stored in the trailing bit-plane: one bit per shot, at the byte
    // right after the syndrome bits.  out_stride is sized host-side to include it.
    long long sbits = (long long)sp.R * sp.n_stab;
    long long flip_byte = (sbits + 7) >> 3;  // first byte past the syndrome bits
    out_bits[shot * out_stride + flip_byte] = (unsigned char)(flip & 1);
  }
}

// ----------------------------------------------------------------------------- //
//  P4a WITHIN-CYCLE trajectory kernel: one block per shot.                       //
//                                                                                //
//  Replaces sv_traj_kernel's LUMPED per-round body                               //
//      [all single-qutrit gates] -> [ONE full-cycle leak per qutrit] -> [measure]//
//  with the circuit-faithful WITHIN-CYCLE op-schedule (Agent H's CSR):           //
//      for r in 0..R-1:                                                          //
//        for op in PRE-ops[r] (round_op_ptr[2r]..[2r+1], in order):              //
//          GATE: apply gate_unitaries[op_uid] on op_site  (reuse apply_gate_block)//
//          LEAK: Kraus-sample leak_kraus (= exp(L/4)) on op_site                  //
//                (reuse leakage_sample_block — same logic; the matrix is the      //
//                 exp(L/4) slice, applied once per LEAK op, so a qutrit in n_cz    //
//                 CZ layers leaks exp(L*n_cz/4) total)                            //
//        measure all 8 stabilizers      (UNCHANGED — measure_stab_block with      //
//                                         stab_supp_isx as before)                //
//        for op in POST-ops[r] (round_op_ptr[2r+1]..[2r+2], in order):            //
//          GATE: apply gate_unitaries[op_uid] on op_site  (the post-M Y; the      //
//                terminal round's POST segment is EMPTY -> no-op)                  //
//      sampled terminal readout -> logical_flip = parity(data) XOR m (UNCHANGED)  //
//                                                                                //
//  §5 RNG NORMATIVITY (updated for the op-schedule): one uniform per categorical  //
//  draw, in op-schedule order — (i) each LEAK op's Kraus draw, consumed AS the     //
//  pre-segment is walked (so a LEAK at op-index t draws before a later op's draw); //
//  (ii) each stabilizer's measurement draw(s) (Arm C: supp_len leak-flag draws in  //
//  support order THEN the outcome draw; else one outcome draw); POST-segment GATEs //
//  draw NOTHING.  After round R: 9 terminal-readout draws (data-qutrit order).     //
//  The DrawStream consumes uniforms in EXACTLY this call order so the host-pre-    //
//  generated urandom stream reproduces it bit-for-bit (§9).                        //
// ----------------------------------------------------------------------------- //
__global__ void sv_traj_wc_kernel(
    const cplx* __restrict__ codestate,   // [DIM]
    cplx* __restrict__ work,              // [num_blocks * DIM] scratch state
    cplx* __restrict__ worktmp,           // [num_blocks * DIM] scratch tmp
    const SchedSpec sp,                   // by value (POD; arrays are device ptrs)
    unsigned char* __restrict__ out_bits, // [num_shots * out_stride]
    long long out_stride,
    real_t* __restrict__ norm_drift,      // [num_shots] diag
    long long num_shots) {
  const long long shot = blockIdx.x;      // wave maps block -> local shot
  if (shot >= num_shots) return;
  const long long shot_id = sp.shot_id_offset + shot;
  const int tid = threadIdx.x;
  const int nth = blockDim.x;

  extern __shared__ real_t scratch[];     // [THREADS] reduction scratch

  cplx* psi = work + shot * DIM;
  cplx* psi_tmp = worktmp + shot * DIM;

  // load |m>_L
  for (long long i = tid; i < DIM; i += nth) psi[i] = codestate[i];
  __syncthreads();

  // RNG: identical keying to the lumped kernel (§5; per-shot stream keyed by the
  // GLOBAL shot index, wave-layout-independent).  The host-pre-generated stream
  // path is bit-faithful given the op-schedule draw order documented above.
  DrawStream rng;
  rng.buf = sp.urandom;
  rng.cap = sp.urandom_stride;
  rng.pos = 0;
  if (sp.urandom != nullptr) {
    rng.buf = sp.urandom + shot * sp.urandom_stride;
  } else {
    curand_init(sp.base_seed ^ (unsigned long long)(shot_id * 0x9E3779B97F4A7C15ULL),
                (unsigned long long)shot_id, 0ULL, &rng.st);
  }

  long long bitpos = 0;  // running index into this shot's syndrome bit-array

  for (int r = 0; r < sp.R; ++r) {
    // ---- PRE-measure op segment: interleaved GATE + LEAK ops, in CSR order ----
    const int pre0 = sp.round_op_ptr[2 * r];
    const int pre1 = sp.round_op_ptr[2 * r + 1];
    for (int t = pre0; t < pre1; ++t) {
      const int kind = sp.op_kind[t];
      const int site = sp.op_site[t];
      if (kind == WC_OP_GATE) {
        const int uid = sp.op_uid[t];
        const cplx* U = sp.gate_unitaries + (long long)uid * 9;
        apply_gate_block(psi, U, site, sp.n_data, psi_tmp);  // no RNG draw
      } else {  // WC_OP_LEAK: exp(L/4) Kraus-sample (one uniform; §5 order)
        leakage_sample_block(psi, &sp, site, &rng, psi_tmp, scratch);
      }
    }
    // ---- measure all 8 stabilizers (UNCHANGED — schedule order) ----------------
    for (int s = 0; s < sp.n_stab; ++s) {
      int bit = measure_stab_block(psi, &sp, s, &rng, psi_tmp, scratch);
      if (tid == 0) {
        long long byte = bitpos >> 3;
        int off = (int)(bitpos & 7);
        if (bit) out_bits[shot * out_stride + byte] |= (unsigned char)(1u << off);
      }
      bitpos++;
    }
    // ---- POST-measure op segment: the transversal Y (GATE ops; no RNG draw).
    // EMPTY for the terminal round (Agent H drops the post-M Y there) -> no-op.
    const int post0 = sp.round_op_ptr[2 * r + 1];
    const int post1 = sp.round_op_ptr[2 * r + 2];
    for (int t = post0; t < post1; ++t) {
      // post-M ops are GATEs (the transversal Y); a LEAK here would be a marshal
      // bug — handle both kinds defensively so the schedule is honored verbatim.
      const int kind = sp.op_kind[t];
      const int site = sp.op_site[t];
      if (kind == WC_OP_GATE) {
        const int uid = sp.op_uid[t];
        const cplx* U = sp.gate_unitaries + (long long)uid * 9;
        apply_gate_block(psi, U, site, sp.n_data, psi_tmp);
      } else {
        leakage_sample_block(psi, &sp, site, &rng, psi_tmp, scratch);
      }
    }
  }

  // norm drift diagnostic (squared-norm just before terminal readout)
  real_t sq = (real_t)0.0;
  for (long long i = tid; i < DIM; i += nth) {
    cplx a = psi[i];
    sq += a.real() * a.real() + a.imag() * a.imag();
  }
  real_t sqf = block_reduce_sum(sq, scratch);
  if (tid == 0) norm_drift[shot] = fabs((real_t)1.0 - sqf);

  // terminal readout -> logical flip (Gate 3; UNCHANGED)
  int flip = terminal_readout_block(psi, &sp, &rng, psi_tmp, scratch);
  if (tid == 0) {
    long long sbits = (long long)sp.R * sp.n_stab;
    long long flip_byte = (sbits + 7) >> 3;
    out_bits[shot * out_stride + flip_byte] = (unsigned char)(flip & 1);
  }
}

// ----------------------------------------------------------------------------- //
//  Host launcher.  Marshals the SchedSpec from torch tensors (device pointers    //
//  kept alive by the caller — the loader holds references), loops waves of <= W   //
//  blocks, returns the packed shot buffer + diagnostics.                         //
//                                                                                //
//  This matches the §7 signature (the loader exposes the Python `sv_traj_d3`).    //
// ----------------------------------------------------------------------------- //
std::vector<torch::Tensor> sv_traj_d3_cuda(
    torch::Tensor codestate,        // [DIM] complex (device)
    int64_t R,
    torch::Tensor round_gptr,       // int32 [R+1]
    torch::Tensor gate_uid,         // int32 [G]
    torch::Tensor gate_site,        // int32 [G]
    torch::Tensor gate_unitaries,   // complex [n_gate,3,3]
    torch::Tensor stab_supp_len,    // int32 [n_stab]
    torch::Tensor stab_supp,        // int32 [n_stab, MAX_SUPP]
    torch::Tensor stab_supp_isx,    // int32 [n_stab, MAX_SUPP]
    torch::Tensor kraus,            // complex [n_kraus,3,3]
    torch::Tensor log_supp,         // int32 [L]
    torch::Tensor log_supp_isx,     // int32 [L]
    int64_t arm,
    double b,
    int64_t readout_conv,
    int64_t logical_m,
    int64_t N,                      // total shots
    int64_t base_seed,
    int64_t shot_id_offset,
    int64_t wave,                   // blocks per wave (W)
    torch::Tensor urandom,          // complex/real [N, stride] or empty
    int64_t urandom_stride) {
  TORCH_CHECK(codestate.is_cuda(), "codestate must be CUDA");
  TORCH_CHECK(codestate.numel() == DIM, "codestate must have 3^9 amplitudes");
  const int n_stab = (int)stab_supp_len.numel();
  TORCH_CHECK(n_stab <= MAX_STAB, "too many stabilizers");
  const int n_gate = (int)gate_unitaries.size(0);
  (void)n_gate;

  auto cs = codestate.contiguous();
  auto gp = round_gptr.contiguous();
  auto gu = gate_uid.contiguous();
  auto gs = gate_site.contiguous();
  auto gmat = gate_unitaries.contiguous();
  auto sl = stab_supp_len.contiguous();
  auto ss = stab_supp.contiguous();
  auto sx = stab_supp_isx.contiguous();
  auto kr = kraus.contiguous();
  auto ls = log_supp.contiguous();
  auto lx = log_supp_isx.contiguous();

  // build the SchedSpec POD
  SchedSpec sp{};
  sp.R = (int)R;
  sp.n_data = N_DATA;
  sp.n_stab = n_stab;
  sp.round_gptr = gp.data_ptr<int>();
  sp.gate_uid = gu.data_ptr<int>();
  sp.gate_site = gs.data_ptr<int>();
  sp.gate_unitaries = reinterpret_cast<const cplx*>(gmat.const_data_ptr<cplx>());
  // copy small fixed arrays into the POD
  {
    auto slh = sl.cpu(); auto ssh = ss.cpu(); auto sxh = sx.cpu();
    auto* slp = slh.data_ptr<int>(); auto* ssp = ssh.data_ptr<int>(); auto* sxp = sxh.data_ptr<int>();
    for (int s = 0; s < n_stab; ++s) {
      sp.stab_supp_len[s] = slp[s];
      for (int j = 0; j < MAX_SUPP; ++j) {
        sp.stab_supp[s * MAX_SUPP + j] = (j < ss.size(1)) ? ssp[s * ss.size(1) + j] : 0;
        sp.stab_supp_isx[s * MAX_SUPP + j] = (j < sx.size(1)) ? sxp[s * sx.size(1) + j] : 0;
      }
    }
  }
  sp.n_kraus = (int)kr.size(0);
  TORCH_CHECK(sp.n_kraus <= MAX_KRAUS, "too many Kraus operators");
  sp.kraus = reinterpret_cast<const cplx*>(kr.const_data_ptr<cplx>());
  {
    auto lsh = ls.cpu(); auto lxh = lx.cpu();
    auto* lsp = lsh.data_ptr<int>(); auto* lxp = lxh.data_ptr<int>();
    sp.log_supp_len = (int)ls.numel();
    TORCH_CHECK(sp.log_supp_len <= MAX_LOG_SUPP, "logical support too large");
    for (int j = 0; j < sp.log_supp_len; ++j) { sp.log_supp[j] = lsp[j]; sp.log_supp_isx[j] = lxp[j]; }
  }
  sp.arm = (int)arm;
  sp.b = (real_t)b;
  sp.readout_conv = (int)readout_conv;
  sp.logical_m = (int)logical_m;
  sp.base_seed = (unsigned long long)base_seed;
  sp.shot_id_offset = (long long)shot_id_offset;

  const bool use_host_stream = urandom.defined() && urandom.numel() > 0;
  torch::Tensor ur;
  if (use_host_stream) {
    ur = urandom.contiguous();
    sp.urandom = reinterpret_cast<const real_t*>(ur.const_data_ptr<real_t>());
    sp.urandom_stride = (long long)urandom_stride;
  } else {
    sp.urandom = nullptr;
    sp.urandom_stride = 0;
  }

  // output sizing (§6): R*n_stab syndrome bits + 1 logical_flip byte.
  const long long sbits = (long long)sp.R * sp.n_stab;
  const long long flip_byte = (sbits + 7) >> 3;
  const long long out_stride = flip_byte + 1;  // syndrome bytes + 1 flip byte

  auto opts_u8 = torch::TensorOptions().dtype(torch::kUInt8).device(codestate.device());
  auto out_bits = torch::zeros({N, out_stride}, opts_u8);

  auto opts_r = torch::TensorOptions()
                    .dtype(sizeof(real_t) == 8 ? torch::kFloat64 : torch::kFloat32)
                    .device(codestate.device());
  auto norm_drift = torch::zeros({N}, opts_r);

  // per-wave global scratch state (work + worktmp), sized to the wave width.
  long long W = wave > 0 ? wave : 256;
  if (W > N) W = N;
  auto opts_c = torch::TensorOptions().dtype(codestate.scalar_type()).device(codestate.device());
  auto work = torch::empty({W, DIM}, opts_c);
  auto worktmp = torch::empty({W, DIM}, opts_c);

  const size_t shmem = (size_t)THREADS * sizeof(real_t);
  auto stream = at::cuda::getCurrentCUDAStream();

  for (long long start = 0; start < N; start += W) {
    long long nshot = (N - start) < W ? (N - start) : W;
    SchedSpec sp_wave = sp;
    sp_wave.shot_id_offset = sp.shot_id_offset + start;
    if (use_host_stream) {
      sp_wave.urandom = reinterpret_cast<const real_t*>(ur.const_data_ptr<real_t>())
                        + start * sp.urandom_stride;
    }
    unsigned char* out_ptr = out_bits.data_ptr<unsigned char>() + start * out_stride;
    real_t* nd_ptr = norm_drift.data_ptr<real_t>() + start;
    sv_traj_kernel<<<(unsigned int)nshot, THREADS, shmem, stream>>>(
        reinterpret_cast<const cplx*>(cs.const_data_ptr<cplx>()),
        reinterpret_cast<cplx*>(work.mutable_data_ptr<cplx>()),
        reinterpret_cast<cplx*>(worktmp.mutable_data_ptr<cplx>()),
        sp_wave, out_ptr, out_stride, nd_ptr, nshot);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
  }

  return {out_bits, norm_drift};
}

// ----------------------------------------------------------------------------- //
//  P4a WITHIN-CYCLE host launcher.                                               //
//                                                                                //
//  Consumes Agent H's WithinCycleMarshalled CSR (round_op_ptr / op_kind /        //
//  op_uid / op_site) + the per-CZ leak slice exp(L/4) (`leak_kraus`), and drives //
//  sv_traj_wc_kernel.  Everything else (stabilizers, logical, instrument arms,   //
//  RNG keying, shot I/O, the §6 buffer layout) is IDENTICAL to sv_traj_d3_cuda — //
//  the MEASUREMENT IS UNCHANGED.  Same keyword-only call shape as §7 except the  //
//  gate CSR (round_gptr/gate_uid/gate_site) is replaced by the op-schedule CSR    //
//  and `kraus` carries the exp(L/4) slice.                                        //
// ----------------------------------------------------------------------------- //
std::vector<torch::Tensor> sv_traj_d3_wc_cuda(
    torch::Tensor codestate,        // [DIM] complex (device)
    int64_t R,
    torch::Tensor round_op_ptr,     // int32 [2R+1]  CSR row-pointer (pre|post per round)
    torch::Tensor op_kind,          // int32 [T]     WC_OP_GATE | WC_OP_LEAK
    torch::Tensor op_uid,           // int32 [T]     gate-unitary index (GATE; 0 for LEAK)
    torch::Tensor op_site,          // int32 [T]     data-qutrit site
    torch::Tensor gate_unitaries,   // complex [n_gate,3,3]
    torch::Tensor stab_supp_len,    // int32 [n_stab]
    torch::Tensor stab_supp,        // int32 [n_stab, MAX_SUPP]
    torch::Tensor stab_supp_isx,    // int32 [n_stab, MAX_SUPP]
    torch::Tensor leak_kraus,       // complex [n_kraus,3,3]  (= exp(L/4) slice)
    torch::Tensor log_supp,         // int32 [L]
    torch::Tensor log_supp_isx,     // int32 [L]
    int64_t arm,
    double b,
    int64_t readout_conv,
    int64_t logical_m,
    int64_t N,                      // total shots
    int64_t base_seed,
    int64_t shot_id_offset,
    int64_t wave,                   // blocks per wave (W)
    torch::Tensor urandom,          // complex/real [N, stride] or empty
    int64_t urandom_stride) {
  TORCH_CHECK(codestate.is_cuda(), "codestate must be CUDA");
  TORCH_CHECK(codestate.numel() == DIM, "codestate must have 3^9 amplitudes");
  TORCH_CHECK(round_op_ptr.numel() == 2 * R + 1,
              "round_op_ptr must have 2R+1 entries (two op-segments per round)");
  const int n_stab = (int)stab_supp_len.numel();
  TORCH_CHECK(n_stab <= MAX_STAB, "too many stabilizers");
  const int n_gate = (int)gate_unitaries.size(0);
  (void)n_gate;

  auto cs = codestate.contiguous();
  auto rop = round_op_ptr.contiguous();
  auto ok = op_kind.contiguous();
  auto ou = op_uid.contiguous();
  auto os = op_site.contiguous();
  auto gmat = gate_unitaries.contiguous();
  auto sl = stab_supp_len.contiguous();
  auto ss = stab_supp.contiguous();
  auto sx = stab_supp_isx.contiguous();
  auto kr = leak_kraus.contiguous();
  auto ls = log_supp.contiguous();
  auto lx = log_supp_isx.contiguous();

  // build the SchedSpec POD (within-cycle CSR; the lumped gate CSR is unused)
  SchedSpec sp{};
  sp.R = (int)R;
  sp.n_data = N_DATA;
  sp.n_stab = n_stab;
  // lumped gate CSR: NOT used by the within-cycle kernel.
  sp.round_gptr = nullptr;
  sp.gate_uid = nullptr;
  sp.gate_site = nullptr;
  sp.gate_unitaries = reinterpret_cast<const cplx*>(gmat.const_data_ptr<cplx>());
  // within-cycle op-schedule CSR
  sp.round_op_ptr = rop.data_ptr<int>();
  sp.op_kind = ok.data_ptr<int>();
  sp.op_uid = ou.data_ptr<int>();
  sp.op_site = os.data_ptr<int>();
  // copy small fixed stabilizer arrays into the POD (UNCHANGED measurement)
  {
    auto slh = sl.cpu(); auto ssh = ss.cpu(); auto sxh = sx.cpu();
    auto* slp = slh.data_ptr<int>(); auto* ssp = ssh.data_ptr<int>(); auto* sxp = sxh.data_ptr<int>();
    for (int s = 0; s < n_stab; ++s) {
      sp.stab_supp_len[s] = slp[s];
      for (int j = 0; j < MAX_SUPP; ++j) {
        sp.stab_supp[s * MAX_SUPP + j] = (j < ss.size(1)) ? ssp[s * ss.size(1) + j] : 0;
        sp.stab_supp_isx[s * MAX_SUPP + j] = (j < sx.size(1)) ? sxp[s * sx.size(1) + j] : 0;
      }
    }
  }
  sp.n_kraus = (int)kr.size(0);
  TORCH_CHECK(sp.n_kraus <= MAX_KRAUS, "too many Kraus operators");
  sp.kraus = reinterpret_cast<const cplx*>(kr.const_data_ptr<cplx>());
  {
    auto lsh = ls.cpu(); auto lxh = lx.cpu();
    auto* lsp = lsh.data_ptr<int>(); auto* lxp = lxh.data_ptr<int>();
    sp.log_supp_len = (int)ls.numel();
    TORCH_CHECK(sp.log_supp_len <= MAX_LOG_SUPP, "logical support too large");
    for (int j = 0; j < sp.log_supp_len; ++j) { sp.log_supp[j] = lsp[j]; sp.log_supp_isx[j] = lxp[j]; }
  }
  sp.arm = (int)arm;
  sp.b = (real_t)b;
  sp.readout_conv = (int)readout_conv;
  sp.logical_m = (int)logical_m;
  sp.base_seed = (unsigned long long)base_seed;
  sp.shot_id_offset = (long long)shot_id_offset;

  const bool use_host_stream = urandom.defined() && urandom.numel() > 0;
  torch::Tensor ur;
  if (use_host_stream) {
    ur = urandom.contiguous();
    sp.urandom = reinterpret_cast<const real_t*>(ur.const_data_ptr<real_t>());
    sp.urandom_stride = (long long)urandom_stride;
  } else {
    sp.urandom = nullptr;
    sp.urandom_stride = 0;
  }

  // output sizing (§6): R*n_stab syndrome bits + 1 logical_flip byte. UNCHANGED.
  const long long sbits = (long long)sp.R * sp.n_stab;
  const long long flip_byte = (sbits + 7) >> 3;
  const long long out_stride = flip_byte + 1;

  auto opts_u8 = torch::TensorOptions().dtype(torch::kUInt8).device(codestate.device());
  auto out_bits = torch::zeros({N, out_stride}, opts_u8);
  auto opts_r = torch::TensorOptions()
                    .dtype(sizeof(real_t) == 8 ? torch::kFloat64 : torch::kFloat32)
                    .device(codestate.device());
  auto norm_drift = torch::zeros({N}, opts_r);

  long long W = wave > 0 ? wave : 256;
  if (W > N) W = N;
  auto opts_c = torch::TensorOptions().dtype(codestate.scalar_type()).device(codestate.device());
  auto work = torch::empty({W, DIM}, opts_c);
  auto worktmp = torch::empty({W, DIM}, opts_c);

  const size_t shmem = (size_t)THREADS * sizeof(real_t);
  auto stream = at::cuda::getCurrentCUDAStream();

  for (long long start = 0; start < N; start += W) {
    long long nshot = (N - start) < W ? (N - start) : W;
    SchedSpec sp_wave = sp;
    sp_wave.shot_id_offset = sp.shot_id_offset + start;
    if (use_host_stream) {
      sp_wave.urandom = reinterpret_cast<const real_t*>(ur.const_data_ptr<real_t>())
                        + start * sp.urandom_stride;
    }
    unsigned char* out_ptr = out_bits.data_ptr<unsigned char>() + start * out_stride;
    real_t* nd_ptr = norm_drift.data_ptr<real_t>() + start;
    sv_traj_wc_kernel<<<(unsigned int)nshot, THREADS, shmem, stream>>>(
        reinterpret_cast<const cplx*>(cs.const_data_ptr<cplx>()),
        reinterpret_cast<cplx*>(work.mutable_data_ptr<cplx>()),
        reinterpret_cast<cplx*>(worktmp.mutable_data_ptr<cplx>()),
        sp_wave, out_ptr, out_stride, nd_ptr, nshot);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
  }

  return {out_bits, norm_drift};
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def("sv_traj_d3", &sv_traj_d3_cuda,
        "P4a state-vector MCWF leakage-teacher trajectory sampler (CUDA, LUMPED per-round)");
  m.def("sv_traj_d3_wc", &sv_traj_d3_wc_cuda,
        "P4a state-vector MCWF leakage-teacher trajectory sampler (CUDA, WITHIN-CYCLE op-schedule)");
}
