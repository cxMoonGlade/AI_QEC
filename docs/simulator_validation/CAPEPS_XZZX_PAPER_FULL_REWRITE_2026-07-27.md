# Clifford-Augmented PEPS for Coherent XZZX Syndrome Circuits: Untruncated Mechanics and a Record-Faithfulness Protocol

## 面向相干 XZZX 综合提取电路的 Clifford-Augmented PEPS：无截断机制与 Record 忠实性协议

作者：`[姓名]`
课程：`[课程名称]`
单位：`[院系/学校]`
日期：2026 年 7 月

> **稿件状态（2026-07-27）。** 本稿报告的是 all-qubit CAPEPS 的无截断
> complex128 mechanics 原型与待执行的 Record-faithfulness protocol，而不是
> 已经获得的 Record-faithful 或效率结论。当前实现具有十八项聚焦工程测试，
> 但全部 PEPS fixtures 都是 \(1\times N\) 或 \(N\times1\) strips，尚无包含
> plaquette 的真正二维验证。动态 residual layout、明确规定的 qubit
> disentangler candidate set、有限键维压缩、paired-norm certificate、
> terminal-frontier gate、canonical detector/observable Record fold 和 target
> resource experiment 均为 `PENDING`。既有 full-PEPS preregistration 不授权该
> target；CAPEPS-specific literature closure、metric registration 和 numerical
> preregistration 完成前，不得执行或传播目标结论。

配套架构图见
[`CAPEPS_XZZX_ARCHITECTURE_FINAL_2026-07-27.md`](CAPEPS_XZZX_ARCHITECTURE_FINAL_2026-07-27.md)；GCAMPS v2 的逐式来源、用途、项目推导和代码映射见
[`GCAMPS_2511_06672_FORMULA_IMPLEMENTATION_AUDIT_2026-07-27.md`](GCAMPS_2511_06672_FORMULA_IMPLEMENTATION_AUDIT_2026-07-27.md)。后者是
project mechanics audit，不是 CAPEPS scientific acceptance 或完整 Record
fidelity 证书。

> **记号约定。** 本稿用 \(q=2\) 表示 qubit 的局域 Hilbert 空间维数，用
> \(d_{\mathrm{code}}\) 表示 XZZX code distance；配套 GCAMPS 公式审计保留
> 原论文的 \(d\) 表示 qudit 局域维数。

## 摘要

本文提出 all-qubit Clifford-Augmented PEPS（CAPEPS）研究原型及其
Record-faithfulness 验证协议，用于含相干 non-Clifford 扰动的二维 XZZX
syndrome circuits。CAPEPS 用 stabilizer tableau 保存 Clifford frame，用
PEPS 保存未被该 frame 吸收的 operational residual。对未截断、精确收缩的
分支 \(h\)，其 formal physical ray 满足

\[
|\psi_h^\star\rangle\doteq C_h|\phi_h^\star\rangle,
\qquad
w_h^\star=P_{\mathrm{raw}}(h).
\]

有限键维实现只定义候选

\[
|\widetilde\psi_h\rangle=C_h|\widetilde\phi_h\rangle,
\qquad
\widetilde w_h=
\prod_k\widetilde p(b_k\mid h_{<k});
\]

它们与理想对象的接近程度必须由独立 reference 检验，不能由表示恒等式
推出。

本文提出、待注册的 state-and-Record acceptance object 为

\[
\mathcal O=
\left(
P_{\mathrm{raw}},P_{\mathrm{Record}},
\{\rho_h:h\in\mathcal H_{\mathrm{sel}}\},
\mathcal R_{\mathrm{reset}}
\right).
\]

它包含 population raw/Record laws、selected conditional states 和 reset
checks，不等于包含每个 terminal conditional state 的完整
classical--quantum instrument。“Record-faithful”只保留给 enumerated
population-law `PASS`。若 \(d_{\mathrm{code}}=3\) 只能逐 trajectory 采样并
比较 empirical Record law，则结果记为 provisional `PASS*`，不得声称完整
population-law Record faithfulness。

当前原型实现 Clifford 左合成、带符号 Pauli pullback、相干 residual update、
局域 physical-ray-exact Clifford refactor、Pauli measurement、outcome-specific
Born branch mass 和物理 Z measured reset，但只产生 ordered raw branch ledger，
尚不产生 canonical Record。待执行协议让 dense reference、full PEPS、CAPEPS
和 Pauli-twirled tableau 独立读取同一个 neutral instrument；另设
\(C|\mathrm{MPS}\rangle\) 作为 implementation-level topology-sensitive
mechanism control。full PEPS 与 CAPEPS 是唯一进入 primary same-channel
estimand 的 pair；primary endpoint 是 independent holdout 上、selection-aware
的 candidate-execution time-to-solution，peak host/device memory 是 secondary
outcome。twirled route 改变 channel，只报告 different-channel trade-off。
可枚举 tracer 负责 complete population law；\(d_{\mathrm{code}}=3\) 负责
selected states、branch mass、reset 以及 enumerated `PASS` 或 sampled
`PASS*`；\(d_{\mathrm{code}}=5\) 仅负责 provisional resource reachability。
现有 25-qubit full-PEPS pure-state 结果只保留为 baseline。

**关键词：** Clifford-Augmented PEPS；stabilizer tensor network；
XZZX surface code；中途测量；reset；Born branch mass；Record

## Abstract

We present an all-qubit Clifford-Augmented PEPS (CAPEPS) research prototype
and a Record-faithfulness protocol for two-dimensional XZZX syndrome circuits
with coherent non-Clifford perturbations. CAPEPS stores a Clifford frame in a
stabilizer tableau and the operational residual not absorbed by that frame in
a PEPS. For an untruncated, exactly contracted branch \(h\), the formal
physical ray and raw-history mass obey

\[
|\psi_h^\star\rangle\doteq C_h|\phi_h^\star\rangle,
\qquad
w_h^\star=P_{\mathrm{raw}}(h).
\]

A finite-bond implementation defines only a candidate
\(|\widetilde\psi_h\rangle=C_h|\widetilde\phi_h\rangle\) and mass estimate
\(\widetilde w_h=\prod_k\widetilde p(b_k\mid h_{<k})\); closeness to the ideal
objects must be established by an independent reference.

The proposed state-and-Record acceptance object, to be registered before target execution, is
\(\mathcal O=(P_{\mathrm{raw}},P_{\mathrm{Record}},
\{\rho_h:h\in\mathcal H_{\mathrm{sel}}\},\mathcal R_{\mathrm{reset}})\).
It contains population raw/Record laws, selected conditional states, and reset
checks; it is not the full classical--quantum instrument over every terminal
conditional state. We reserve “Record-faithful” for an enumerated
population-law `PASS`. A trajectory-sampled empirical Record comparison can
receive only provisional `PASS*`, not an unqualified complete-law verdict.

The current prototype implements Clifford-frame composition, signed Pauli
pullback, coherent residual updates, local physical-ray-exact Clifford
refactorization, Pauli measurement, outcome-specific branch masses, and
physical-Z measured reset. It emits an ordered raw branch ledger, not a
canonical Record. The planned experiment independently lowers one neutral
instrument into a dense reference, full PEPS, CAPEPS, and a Pauli-twirled
tableau, with a \(C|\mathrm{MPS}\rangle\) implementation-level
mechanism control. Full PEPS and CAPEPS are the only pair entering the primary
same-channel estimand. Its endpoint is selection-aware candidate-execution
time-to-solution on an independent holdout; peak host and device memory are
secondary. An enumerable tracer owns population-law evidence,
\(d_{\mathrm{code}}=3\) owns selected-state, branch-mass, reset, and either
enumerated `PASS` or sampled `PASS*` evidence, and \(d_{\mathrm{code}}=5\) owns
provisional reachability only. Existing 25-qubit full-PEPS data remain a
pure-state baseline.

## 1. Introduction

二维 syndrome-extraction circuit 同时包含三种结构：二维局域几何、以
Clifford 为主的 stabilizer skeleton，以及少量但相干的 non-Clifford
扰动。full PEPS 将整个条件态交给一般复张量，因此既承载 Clifford
stabilizer entanglement，也承载真正需要 non-stabilizer amplitudes 的部分。
由于前者已有 tableau 的多项式精确表示，一个可检验的资源假设是：full
PEPS 可能在重复表示 Clifford skeleton，而 hybrid representation 可以把
PEPS budget 留给 operational residual。这里的“可能”是实验假设，不是由
表示形式自动推出的效率结论。

把相干旋转 Pauli twirl 后交给 tableau 是另一条便宜路径，但它把 Pauli
amplitudes 的交叉项换成 classical mixture，从而改变量子 channel。带中途
measurement、reset 和跨轮 detector/observable fold 的电路要求比较声明的
\(\mathcal O\)，而不是仅比较一个 normalized endpoint。相似的终态、便宜的
tableau execution，甚至相似的一条 realized Record，都不能证明 coherent
raw/Record law 被保留。

Stabilizer tensor networks 和 GCAMPS 给出中间分工

\[
|\psi\rangle=C|\phi\rangle_{\mathrm{MPS}},
\]

其中 Clifford gate 更新 \(C\)，non-Clifford operator 经 \(C\) 共轭后作用于
residual MPS [1,2]。近期相邻工作已经把这一 \(C|\mathrm{MPS}\rangle\)
表示用于 repeated rotated-surface-code syndrome extraction 中的 coherent
crosstalk 和 projective measurement [8]；该工作还明确报告没有启用 Clifford
optimization，并把 PEPS/TTN 列为未来布局。它的 noise model 包含 reset-error
rate，但没有定义本文的 `MR_Z` Kraus transaction、完整 branch-mass law 或
absolute detector/observable Record-faithfulness protocol。相对于 [8]，本稿
计划检验的 design differences 是 residual PEPS mechanics、显式 paired
measurement/reset mass transaction、terminal Record protocol 和 matched
full-PEPS comparator；这不是 field-wide novelty 结论。本文也不把 hybrid
QEC、GCAMPS measurement 或 coherent surface-code simulation 本身作为 novelty。

本文将表示写为

\[
\boxed{|\psi\rangle=C|\phi\rangle_{\mathrm{PEPS}}}.
\]

这不意味着二维 residual 必然优于一维，也不意味着 CAPEPS 必然优于 full
PEPS。物理局域 Pauli 经过 frame pullback 后可能形成跨越多条 residual cuts
的 coherent operator sum；全数据 \(R_Y\) 层也可能使这种 cut complexity
快速扩散。中心问题因此被写成 fixture-bounded、可证伪命题：

\[
\boxed{
\text{在保持完整 }P_{\mathrm{raw}}\text{ 与 }P_{\mathrm{Record}}
\text{，并通过 selected-state、branch-mass 与 reset gates 的前提下，}
C|\mathrm{PEPS}\rangle
\text{ 能否比 full PEPS 更高效？}
}
\]

该问题对应 enumerated population-law `PASS`；若只能获得 sampled `PASS*`，
结论必须明确降为 sampled-certification 下的 provisional performance。“更
高效”不使用 “runtime 或 memory” 的事后析取。full PEPS 与 CAPEPS 必须先
通过同一状态/质量/reset/Record gates；配置在 pilot 上以 selection-valid rule
冻结，随后以 independent holdout 上的 candidate-execution time-to-solution
为 primary endpoint。peak host/device memory 和 completion 是 secondary
outcomes。若任一路径没有 passing configuration，estimand 未定义，而不是
infinite speedup。

本文贡献严格限定为三项：

1. 把 GCAMPS-inspired frame/residual 分解定义为
   \(C|\mathrm{PEPS}\rangle\)，给出 qubit physical factor 与 PEPS site 的
   显式双射、两个 GCAMPS state cycles、带符号 pullback 和 physical-ray-exact
   paired refactor；当前证据只覆盖 qubit、无截断的小系统 mechanics，尚未
   建立 genuine-2D 或 finite-bond correctness。
2. 定义 paired measurement--reset transaction：两个 projector branches
   来自同一 immutable parent，在归一化和可选压缩之前计算 Born mass；
   enumerated route 通过 terminal-frontier gate 后把 complete raw law push
   forward 为 detector/observable Record law，sampled route 则逐 trajectory
   fold 并只接受 provisional statistical verdict。当前实现止于 ordered raw
   ledger，atomic paired certificate 和 Record reducer 尚待实现。
3. 定义 independent dense correctness protocol 和 selection-aware resource
   protocol：full PEPS 是 primary same-channel comparator，Pauli-twirled
   tableau 是 different-channel approximation，\(C|\mathrm{MPS}\rangle\) 是
   implementation-level mechanism control。target experiment 尚未
   preregister 或执行，因此本文不报告效率胜负。

本文不使用 first、unique 或“首个 CAPEPS”等 field-wide priority 表述。
CAPEPS-specific literature closure 目前仍为 `OPEN`；相邻工作 [8] 已经实质
收窄 design claim，但不能替代完整外部文献与软件 closure。

## 2. Background

### 2.1 Stabilizer tensor networks、GCAMPS 与相邻 QEC 工作

Stabilizer-basis tensor-network 方法把一般量子态表示为 Clifford/stabilizer
basis 与 coefficient tensor network 的组合。对 Clifford gate \(G\)，只更新
frame；对

\[
U=\sum_j\alpha_jP_j,
\]

则把每个 Pauli \(P_j\) 连同其 sign 拉回 coefficient state。Masot-Llima 与
Garcia-Saez 给出了该表示和 Born projective measurement 的形式规则 [1]。
GCAMPS 把 leading Clifford 与 MPS residual 组合为
\(C|\mathrm{MPS}\rangle\)，并提出用 Clifford disentangler 降低 residual
entanglement [2]。

本文可直接继承的 source-supported algebraic spine [2, Eq. (5) and Fig. 3]
只有：

- 物理 Clifford 的左合成 \(C\leftarrow GC\)；
- non-Clifford Pauli expansion 的 signed pullback \(C^\dagger P_jC\)；
- 生成元与 phase ledger；
- physical-ray-exact refactor
  \((C,\phi)\mapsto(CQ^\dagger,Q\phi)\)。

GCAMPS [2] 没有给出可直接执行的 optimizer catalogue、canonical key、
objective、tie-break 或 stopping rule，也没有给出 PEPS、reset、跨轮 Record
或 finite-bond fidelity-transfer theorem。它报告的 20 和 90 个 two-site
entangling equivalence classes 分别属于局域维数 \(q=2\) 和 \(q=3\)；本文是
all-qubit 工作，90 不是实现或实验目标。配套公式审计据此验证了项目的
qubit untruncated mechanics，但不把该原型称为完整 GCAMPS reproduction。

更直接的相邻工作已经使用 GCAMPS \(C|\mathrm{MPS}\rangle\) 模拟 repeated
rotated-surface-code syndrome extraction 中的 coherent crosstalk [8]。该方法
把 projective-measurement Pauli sum 穿过 \(C\) 后作用于 MPS，并研究 MPS
truncation；作者报告 Clifford optimization 的开销超过其 bond reduction，
所以没有启用该优化，并把 PEPS 或 tree tensor network 列为未来方向
[8, Sec. IV.A and Conclusion]。
[8] 同时包含 reset-error rate 和 repeated rounds，因此本稿不从该文“没有
reset”作推论。相对于 [8]，这里计划检验的设计差异是 residual PEPS
mechanics、显式 `MR_Z`/paired-mass transaction、population-versus-sampled
Record protocol，以及 selection-aware full-PEPS comparator。该比较只是
source-specific positioning，不是 field-wide novelty closure。

### 2.2 PEPS 与正确性边界

PEPS 的二维 connectivity 可以匹配局域二维相关，但有限 PEPS 的更新和
收缩必须指定 environment、routing、gauge、truncation 与误差控制 [3]；
一般 exact PEPS contraction 还存在最坏复杂度障碍 [4]。因此，“residual
bond 较小”既不自动推出 Born probability 更便宜，也不自动推出 conditional
state 或 Record law 正确。

本文把 PEPS 视为一个有显式责任边界的 residual carrier：

- untruncated local update 或 algebraic direct sum 只证明代数 mechanics；
- finite-\(D_{\mathrm{res}}\) compression 定义的是候选近似；
- contraction environment 会同时影响 norm、Born mass 和条件态；
- local discarded weight、裸 bond dimension 或 gauge-dependent tensor norm
  都不是 Record-TV bound；
- 只有独立 dense state/law 才能担任小系统 correctness referee。

PEPS edge 是 virtual contraction index，不是额外 physical factor。每个 circuit
qubit 必须始终对应一个且仅一个 PEPS physical leg；若算法重排 tensor-factor
order，必须与 Clifford frame 和 qubit-to-site map 做 paired update。

### 2.3 XZZX measurement--reset--Record instrument

XZZX syndrome extraction 不是单一终态演化，而是有序 quantum instrument。
每轮包含 data--ancilla gates、ancilla measurement、measured reset，以及把
不同轮 raw measurement columns 通过声明的 XOR rows 折叠为 detector 和
observable Records [5,6]。

记完整 raw bit string 为 \(m\)，冻结 classical fold 为

\[
r=f_{\mathrm{fold}}(m)=Fm\oplus r_0 .
\]

量子后端必须先定义 raw law \(P_{\mathrm{raw}}(m)\)，再做确定性
push-forward：

\[
P_{\mathrm{Record}}(r)
=
\sum_{m:f_{\mathrm{fold}}(m)=r}P_{\mathrm{raw}}(m).
\]

这里的 Record 必须绑定 absolute raw columns、detector/observable XOR rows
及 offsets，而不能简化为“相邻两轮 syndrome 做 XOR”。一条 realized row
不是 Record distribution；selected histories 的正确条件态也不是完整
classical--quantum instrument。本文因此分别检查 conditional state、branch
mass、reset、complete raw law 和 folded Record law。

## 3. Method

### 3.1 Exact branch object、finite-bond candidate 与 residual layout

令物理 qubit 集合为 \(\mathcal Q=\{0,\ldots,n-1\}\)。branch \(h\) 的
residual PEPS graph 为 \(G_h=(V_h,E_h)\)，并要求显式双射

\[
\ell_h:\mathcal Q\longleftrightarrow V_h .
\]

\(\ell_h(q)\) 的 physical leg 承载 circuit qubit \(q\) 的同一个 Hilbert
factor；\(E_h\) 只定义 residual 的 virtual connectivity，不承载额外 qubit。
因此 residual graph 可以不同于 XZZX hardware-interaction graph，但 physical
factors 不会变成 “tableau coordinates” 或映射到 PEPS edges。

对采用同一冻结 frame/refactor policy 的理想未截断对象，记

\[
\mathcal S_h^\star=
(C_h,|\phi_h^\star\rangle,w_h^\star,h,G_h,\ell_h),
\qquad
|\psi_h^\star\rangle\doteq C_h|\phi_h^\star\rangle,
\qquad
w_h^\star=P_{\mathrm{raw}}(h),
\]

其中 \(\doteq\) 表示相差 physical global phase。有限键候选另记为

\[
\widetilde{\mathcal S}_h=
(C_h,|\widetilde\phi_h\rangle,\widetilde w_h,h,G_h,\ell_h,\Lambda_h),
\qquad
|\widetilde\psi_h\rangle:=C_h|\widetilde\phi_h\rangle .
\]

\(\Lambda_h\) 是 operator construction、contraction、routing、compression、
discarded-information 和 peak-resource ledger。对候选不写
\(|\psi_h^\star\rangle=C_h|\widetilde\phi_h\rangle\)，也不写
\(\widetilde w_h=P_{\mathrm{raw}}(h)\)；二者都需要独立 reference。

若 dynamic relayout 以 unitary permutation \(R_h\) 改变 tensor-factor order，
必须原子地执行

\[
(C_h,|\phi_h\rangle,\ell_h)
\mapsto
(C_hR_h^\dagger,R_h|\phi_h\rangle,\ell_h')
\]

并验证 physical ray 不变。只改变 virtual graph 而不移动 physical axes，不得
称为 qubit permutation。当前实现只有固定 open-boundary rectangular graph
和 row-major 双射，qubit 0 对应 dense tensor order 的最高位；dynamic
relayout 尚未实现。

### 3.2 Upper state cycle：Clifford frame

若下一个物理操作为 Clifford \(G\)，则

\[
G C_h|\phi_h\rangle=(G C_h)|\phi_h\rangle,
\qquad
C_h\leftarrow G C_h .
\]

residual、\(G_h\) 和 \(\ell_h\) 不变。合成方向必须是左乘；错误的
\(C_h\leftarrow C_hG\) 会在非交换门序列中改变物理态。Upper cycle 到此
结束：它只接收 physical Clifford，Pauli expansion、signed pullback 和
residual update 都属于 lower cycle。

当前原型以 Stim 为默认 all-qubit frame owner，并保留一个显式、版本固定的
SDIM qubit adapter seam [7]。当前验收环境未执行 live SDIM path；只有 phase
translation 与缺包时 fail-closed 的工程证据。这既不是 generalized-qudit
结果，也不是 qutrit-leakage 证据。

### 3.3 Lower state cycle：coherent residual operator 与 cut complexity

对物理 non-Clifford operation

\[
U=\sum_j\alpha_jP_j,
\]

lower cycle 先由 tableau 计算带符号 pullback

\[
Q_{j,h}=C_h^\dagger P_jC_h,
\qquad
A_h=\sum_j\alpha_jQ_{j,h},
\]

再执行

\[
|\phi_h'\rangle=A_h|\phi_h\rangle .
\]

所有 tableau signs 和 complex amplitudes 必须逐项保留；不得把
\(\alpha_j\) 解释为 classical probabilities。对

\[
R_P(\theta)=e^{-i\theta P/2}
=\cos\frac{\theta}{2}I-i\sin\frac{\theta}{2}P,
\]

两项构成 coherent sum，而不是 twirled mixture。

Pauli weight 本身不是 bond-growth mechanism。单个 Pauli string 在任意
bipartition 上都是 product operator，operator-Schmidt rank 为 1。对 residual
cut \(e:A_e|B_e\)，写

\[
A_h=\sum_{\mu=1}^{\chi_e(A_h)}
L_{\mu,e}\otimes R_{\mu,e}.
\]

例如 \(I+\alpha Q\) 在任意 cut 上始终有 \(\chi_e\le2\)；当 \(Q\)
在 cut 两侧都非平凡且两项不成比例时，generically \(\chi_e=2\)。重复的、
非交换 coherent sums 及其作用后的 state
entanglement 才可能使相关 cut complexity 继续增长。因此 primary mechanism
ledger 应记录每条 cut 的 \(\chi_e(A_h)\) 或经验证 upper bound、被跨越 cut
的数目和几何，以及更新前后的 actual edge dimensions。support weight、
diameter 和 routing length 只是辅助诊断。

当前 Quimb 原型对 single-site operator 做 untruncated local absorption，对
multi-site coherent sum 使用 global PEPS algebraic direct sum。后者会同时
增大许多与 physical support 无关的 matching virtual bonds，所以只允许作为
tracer correctness construction。任何 efficiency target 都必须在执行前冻结
structured operator-network construction（例如明确的 PEPO 或 support tree）、
routing、contraction environment、compression points、中间 peak bond 与失败
策略；否则测到的是 naïve direct-sum implementation，而不是 CAPEPS
representation 的可归因效率。

### 3.4 Exact refactor、qubit candidate search 与 compression transaction

一次 exact Clifford refactor 为

\[
(C_h,|\phi_h\rangle)
\mapsto
(C_hQ_h^\dagger,Q_h|\phi_h\rangle),
\qquad Q_h\ \text{Clifford},
\]

因为

\[
(C_hQ_h^\dagger)(Q_h|\phi_h\rangle)=C_h|\phi_h\rangle.
\]

这里的 exact 指 physical-ray exact；Stim tableau 不保存 Clifford global
phase，因此验收使用 complete-vector ray fidelity。当前原型只实现 single-site
和 adjacent two-site 的 untruncated exact-refactor primitive，并以 separately formulated dense reference 和 PEPS regression fixtures 检查
右乘方向、physical ray 以及失败事务的原子性。

本文是 \(q=2\) all-qubit 工作，不使用 GCAMPS 的 \(q=3\) “90 candidates”。
GCAMPS [2] 报告 qubit 情形有 20 个 two-site entangling equivalence classes，
但没有给出 executable gate list、canonical key、objective、tie-break 或
stopping rule。因此，未来搜索器只有在这些对象被独立重构并 hash-frozen 后
才能称为 “GCAMPS 20-class reconstruction”；否则必须标为
project-defined qubit candidate set。

有环 PEPS 没有 MPS 式唯一 canonical Schmidt objective，裸 bond dimension
与 local tensor gauge 不能充当 entanglement objective。target optimizer
必须预先冻结：

- environment construction、gauge convention 与 gauge-aware objective
  \(J_e(Q)\)；
- candidate edges/set、cadence、tie-break、seed 与 stopping rule；
- identity/no-op control，以及等价 exact refactor 下 physical output 不变的
  falsifier；
- search、environment 和 rejected candidates 的全部 runtime/memory；
- 禁止访问 dense target、目标 branch 或 evaluator-only truth。

accepted update 必须分成两个阶段。首先

\[
(C_h,\phi_h)\mapsto(C_hQ_h^\dagger,Q_h\phi_h)
\]

是 physical-ray-exact refactor；随后 compression 才是独立近似 transaction。
compression 只有在 candidate finite、达到声明 bond target、所有相关 tensors
原子写入且 ledger 完整时才可提交；失败或部分吸收必须 rollback。norm
restoration 只服务 normalized conditional-state representation，不得改写此前
保存的 Born mass。local objective 和 discarded weight 都不是 Record-TV
bound。

### 3.5 Instrument route：validated paired Born transaction、`MR_Z` 与 terminal Record reducer

本文区分两种 typed operation：`M(P)` 是 Hermitian Pauli measurement、无
reset；`MR_Z(q)` 是测量 physical \(Z_q\)，再依 outcome 准备 \(|0\rangle\)。
本文不声称已实现 generic `MR`。

对 `M(P)` 或 `MR_Z(q)` 中相应的 physical Pauli \(P\)，令

\[
\Pi_b=\frac{I+(-1)^bP}{2},
\qquad
Q_h=C_h^\dagger PC_h,
\qquad
v_{hb}^\star=
\frac{I+(-1)^bQ_h}{2}|\phi_h^\star\rangle .
\]

exact conditional mass 为

\[
p_b^\star=
\frac{\langle v_{hb}^\star|v_{hb}^\star\rangle}
     {\langle\phi_h^\star|\phi_h^\star\rangle},
\qquad
p_0^\star+p_1^\star=1.
\]

projector 是 coherent Pauli sum，必须调用与 lower cycle 相同的 residual
operator-application kernel。finite-bond route 将一次 measurement 实现为一个
paired transaction：

1. 冻结同一个 immutable parent snapshot、layout 与 contraction policy；
2. 从该 parent 分别构造两个 unnormalized projector candidates，禁止 outcome
   0 的写入污染 outcome 1；
3. 在任何除法、branch normalization、refactor 或 compression 之前，原子保存
   contraction 返回的 raw parent estimate \(\widehat n_h\) 与 raw child
   estimates \(\widehat n_{h0},\widehat n_{h1}\)，包括可检测的 imaginary
   residual 和 provenance；
4. 先验证

   \[
   \widehat n_h\in\mathbb{R}_{>0},
   \qquad
   \widehat n_{h0},\widehat n_{h1}\in\mathbb{R}_{\ge0},
   \]

   且所有值 finite、imaginary residual 在预注册 certificate 内。NaN、Inf、
   non-negligible complex part、nonpositive parent 或 negative child 均返回
   typed `UNAVAILABLE`；只有通过后才定义

   \[
   \widehat p_b=\frac{\widehat n_{hb}}{\widehat n_h},
   \qquad
   \delta_{\mathrm{comp}}
   =
   \left|
   \frac{\widehat n_{h0}+\widehat n_{h1}}{\widehat n_h}-1
   \right|;
   \]
5. complement residual 超出注册 certificate 时 fail closed；不得 clipping，
   也不得以 \(\widehat p_b/(\widehat p_0+\widehat p_1)\) post-hoc repair；
6. exact structural zero 只能由 algebraic/symbolic certificate 或独立
   reachability evidence 判定。floating floor 不得删除正分支或制造质量；
7. 对正分支按保存的 unnormalized norm 归一化。对于 `MR_Z(q)`，再把
   \(X_q^b\) 作为 physical Clifford 左乘 frame，从而实现
   \(A_b=|0\rangle\langle b|=X^b\Pi_b\)；
8. 只有此后才运行共同的 lower-tail exact refactor 与 transactional
   compression，并将 compression norm change/discarded information 与 Born
   mass 分账。

候选质量为

\[
\widetilde w_{hb}=\widetilde w_h\widehat p_b .
\]

它是 mass estimate，不会因为 complement consistency 通过而自动等于
\(P_{\mathrm{raw}}(hb)\)。每次 measurement 只追加 ordered raw event：

\[
(\text{absolute column},b,\widehat p_b,
\log\widetilde w_{hb},\texttt{MR\_Z flag},\text{provenance}).
\]

**Enumerated population-law route.** 完成所有 quantum operations 后，必须先
保留 complete terminal branch frontier，再通过 global frontier gate：声明的
branch/column coverage 完整；所有 masses finite、real、nonnegative；total-mass
residual 在 band 内；structural-zero certificate 完整；没有 missing branch。
失败时只输出 typed `UNAVAILABLE` 与 candidate diagnostics，禁止 global
renormalization。只有 gate 通过后，terminal classical reducer 才按 frozen
absolute detector/observable XOR rows 与 offsets push forward raw population
law，并聚合同一 Record row 的质量。该路径才有资格获得 population-law
`PASS` 和 Record-faithfulness verdict。

**Trajectory-sampled route.** Sampling 不生成 complete frontier。每条 sampled
trajectory 只生成一个 ordered raw row，并逐 trajectory 应用同一个 frozen
fold；随后以 preregistered one-sample exact-reference 或 independent two-sample
设计比较 empirical Record output，显式包含 reference uncertainty、joint
support、coverage/excluded-mass policy 和 confidence allocation。它最多获得
provisional `PASS*`，不得声称 complete raw law、population TV 或 unqualified
Record faithfulness。

当前 `MeasurementEvent` 不是 `RecordBatch`；atomic paired certificate、global
frontier gate 和 terminal reducer 均尚未接入。

### 3.6 四个 headline routes 与一个 mechanism control

四条 headline routes 独立 lower 同一个 neutral scientific fixture：

1. **Dense exact reference**：小系统 complete state 和 complete raw/Record
   law 的 correctness referee；
2. **Full PEPS**：同一 coherent channel 的 comparator，一个 PEPS 承载完整
   physical conditional state；
3. **CAPEPS**：tableau 承载 \(C_h\)，PEPS 承载 residual，是本文 candidate；
4. **Pauli-twirled tableau**：把 coherent rotation 替换为

   \[
   \mathcal E_{\mathrm{twirl}}(\rho)
   =
   \cos^2\frac{\theta}{2}\rho
   +
   \sin^2\frac{\theta}{2}P\rho P,
   \]

   因而模拟不同 stochastic channel，只是 approximation baseline。

另设一个 planned **\(C|\mathrm{MPS}\rangle\) mechanism control**：它使用
同一个 coherent instrument，并预注册若干 1D qubit orderings、matched
frame/operator logic、accuracy gates 和 comparable compression/search budgets。
它不进入 dense referee，也不改变 primary full-PEPS-versus-CAPEPS estimand。
仓库现有 restricted MPS service 不是该 route；新 control 需要自己的 neutral
lowering、dense gates 和 provenance。即使 CAPEPS 与该 control 都通过，结果也
只是一项 implementation-level topology-sensitive ablation；ordering、
canonicalization 和 optimizer confounding 仍阻止单独的 topology causal claim。

各 route 只能共享 neutral specification，不能共享 candidate tensors、
tableaux、compiled projectors、contraction plans 或 evaluator-only diagnostics。
每条 route 应输出可审计 lowering trace，以验证 operation order、axis map、
measurement columns、reset semantics 和 Record fold 确实一致。

## 4. Correctness

### 4.1 Exact state invariant

本节的代数证明只适用于 starred、untruncated、exact-contraction object。初始时
\(C_0=I\)，residual 等于声明初态。对 physical Clifford \(G\)，

\[
G|\psi_h^\star\rangle
=(GC_h)|\phi_h^\star\rangle .
\]

对 coherent Pauli expansion，

\[
\begin{aligned}
U|\psi_h^\star\rangle
&=\sum_j\alpha_jP_jC_h|\phi_h^\star\rangle\\
&=C_h\sum_j\alpha_j(C_h^\dagger P_jC_h)
  |\phi_h^\star\rangle\\
&=C_h|\phi_h^{\star\prime}\rangle .
\end{aligned}
\]

该等式逐项保留 complex coefficients 和 tableau signs，所以没有 implicit
twirl。accepted exact refactor 满足

\[
(C_hQ_h^\dagger)(Q_h|\phi_h^\star\rangle)
=C_h|\phi_h^\star\rangle,
\]

而 paired axis relayout 同理保持 physical ray。finite-bond candidate 的
\(|\widetilde\psi_h\rangle=C_h|\widetilde\phi_h\rangle\) 只是其自身的表示定义，
不是它等于 ideal state 的证明。

### 4.2 Exact branch-mass conservation 与 approximate complement gate

对 starred parent，pullback projector 与 physical projector 具有相同 norm，
所以 residual norm ratio 正是 Born probability。由于

\[
\Pi_0+\Pi_1=I,
\qquad
\Pi_b\Pi_{1-b}=0,
\]

得到

\[
p_0^\star+p_1^\star=1,
\qquad
\sum_b w_{hb}^\star
=w_h^\star\sum_b p_b^\star
=w_h^\star .
\]

从 \(w_\emptyset^\star=1\) 归纳可得任意 complete exact branch frontier 的
总质量为 1。该证明要求所有正分支都保留，不能用 floating floor 代替
structural-zero semantics。

approximate contraction/compression 下没有同样的证明。候选只能报告
\(\widehat p_b\)、paired complement residual \(\delta_{\mathrm{comp}}\)、
parent-to-child mass residual 和相对 dense reference 的 branch-mass error。
\(\delta_{\mathrm{comp}}\) 是必要 numerical invariant，不是 independent
correctness oracle；禁止通过 clipping 或重新归一化
\((\widehat p_0,\widehat p_1)\) 人工制造 conservation。超出注册证书必须
fail closed。

### 4.3 Reset correctness

`MR_Z(q)` 对 outcome \(b\) 的 Kraus operator 为

\[
A_b=X_q^b\Pi_b=|0\rangle\langle b|_q .
\]

projector correctness 由同一 residual kernel 和 branch-mass proof 覆盖，
\(X_q^b\) 是 physical Clifford 左合成，因此 exact branch invariant 保持。
reset 还必须通过两类独立检查：structural operation trace 确认为 `MR_Z`，且
被 reset qubit 的 one-site reduced state 与 \(|0\rangle\langle0|\) 的 trace
distance 在注册 band 内。后续操作必须读取该 reset state，而不是原测量
本征态；post-hoc state repair 不计为通过。

### 4.4 Enumerated population law 与 sampled Record certification

complete exact raw population law 由 terminal leaf masses 定义：

\[
P_{\mathrm{raw}}^\star(m)=w_m^\star,
\qquad
\sum_m w_m^\star=1.
\]

冻结 fold 是 deterministic map，所以

\[
P_{\mathrm{Record}}^\star(r)
=
\sum_{m:f_{\mathrm{fold}}(m)=r}w_m^\star
\]

也保持总质量。对任一共同 support，

\[
\operatorname{TV}(p,q)=\frac12\sum_x|p(x)-q(x)|.
\]

finite-bond enumerated candidate 必须先通过 terminal-frontier validity gate，
才能把 candidate leaf masses 解释为 population-law estimate。raw-TV 与 joint
detector/observable Record-TV 是不同指标：fold 可以合并多个 raw histories，
因此任一指标都不能替代另一个。selected conditional-state fidelity、stepwise
probability 和 cumulative branch mass 也分别检查。population-law
Record-faithfulness 指的是 \(\mathcal O\) 中的 raw/Record gates，不把 selected
states 升级为完整 cq-instrument equivalence。

sampled route 不拥有 complete frontier 或 population TV。它逐 trajectory 生成
raw/Record rows，并在 preregistered reference/uncertainty design 下比较 empirical
outputs；通过时只记 provisional `PASS*`。因此 population `PASS` 与 sampled
`PASS*` 是不同 evidence classes，不能折叠成一个无条件 verdict。

### 4.5 当前 untruncated-mechanics 证据及其边界

当前聚焦测试命令为：

```bash
conda run -n ecs python -m pytest -q \
  tests/test_capeps_hybrid.py \
  tests/test_capeps_gcamps_formulas.py
```

2026-07-27 的 current worktree 结果为 `18 passed, 1 warning`。warning 来自
Quimb/cotengra 缺少 optional `kahypar`，不改变 test verdict。

| falsifier fixture | 当前观测 | 所防止的错误 |
|---|---|---|
| noncommuting two-qubit Clifford | physical \(Y_0\) pullback 为 \(+X_0X_1\) | frame 左/右合成错误；Pauli sign 丢失 |
| Eq. (5) reconstruction | GF(2)、ordered generators 与 direct Stim pullback 一致 | generator order 或 phase ledger 错误 |
| dense coherent \(R_Y(0.02)\) | 与 independent complex128 matrix 的 fidelity error \(\le10^{-12}\) | 把 coherent amplitudes 写成 twirl |
| arbitrary small-local unitary | Pauli reconstruction 与 independent dense matrix 一致 | 只实现 rotation 特例；系数共轭错误 |
| strip-shaped nonlocal Quimb update | untruncated direct sum，bond \(1\to2\)，fidelity error \(\le10^{-12}\) | 漏执行 residual 或错误 axis mapping |
| local Quimb update | bond 保持 1；input vector 不共享 | 不必要 bond growth；shallow copy |
| exact refactor | residual 与 frame paired update 后 physical ray 不变 | 错误右乘；只更新一端 |
| dense/Quimb measurement and reset | parent-isolated branches、Born mass、physical reset | 顺序污染 parent；`MR_Z` 退化为 `M` |
| tiny positive branch | \(p=10^{-28}>0\) 被保留 | threshold 制造 structural zero |
| SDIM seam | phase translation；缺包时 fail closed | silent fallback；phase 语义丢失 |

所有 PEPS fixtures 目前仍是 \(1\times N\) 或 \(N\times1\) strips；它们没有
plaquette、二维 loop 或同时覆盖 horizontal/vertical edge families 的 operator。
因此十八项测试只支持 bounded all-qubit untruncated mechanics，不支持真正
二维 CAPEPS、complete XZZX raw/Record law、finite-bond accuracy、runtime
advantage、\(d_{\mathrm{code}}=5\) correctness 或 scaling。贡献 1 从表示定义
提升为二维 mechanics evidence 前，至少需要 dense-checked \(2\times2\) 和
\(2\times3\) tracers。

### 4.6 Finite-bond state-and-Record acceptance gates

加入 approximate contraction 或 compression 后，每个 same-channel candidate
configuration 的 common gates 包括：

- selected histories 的 complete complex128 physical-vector fidelity；
- 每步 conditional-probability error、cumulative log-mass error 和 explicit
  structural-zero agreement；
- division 前的 real/finite/positive-parent and nonnegative-child norm gate，
  paired complement、parent isolation 与 parent-to-child mass checks；
- `MR_Z` structural trace 和 one-site reset trace distance；
- corruption controls：gate-order permutation、outcome flip、reset removal、
  fold-row shift、axis permutation、degraded contraction、twirl substitution、
  frame-disabled same-channel equivalence，以及 coherent-versus-twirled
  Record-level nondegeneracy。

**Enumerated `PASS`** 还要求 terminal-frontier branch/column completeness、
finite nonnegative masses、global mass residual、structural-zero certificate、
complete raw-law normalization/raw-TV，以及 frozen absolute coordinates 下的
joint detector/observable population Record-TV。

**Sampled `PASS*`** 不使用 complete-frontier 或 population-TV 语言。它必须
预注册 trajectory count、one-sample exact-reference 或 independent two-sample
设计、reference uncertainty、joint support、confidence allocation、
coverage/excluded mass、rare/adversarial paths、seeds、batching/reuse policy 和
stopping rule。

local discarded weight、bond dimension、operator-support weight 和 paired
complement residual 都不能替代 end-object state/law error。没有 enumerated
population `PASS` 时，不得使用 unqualified “Record-faithful”；sampled evidence
必须始终带 `PASS*`/provisional qualifier。

## 5. Experiments

### 5.1 Neutral instrument、frozen workload 与 independent lowering

实验输入是一份 hash-frozen、backend-neutral XZZX instrument specification，
至少包含：

- code distance、data/ancilla coordinates、boundary 与 physical-qubit order；
- 每轮完整 ordered operation list；
- coherent rotations 的 support、angle 与 half-angle convention；
- typed `M(P)`/`MR_Z(q)` operations 与 absolute raw-column order；
- detector/observable 的 absolute XOR rows 与 offsets；
- branch enumeration 或 sampling task、precision、sample count、seed/coupling
  policy、operation horizon 与 resource envelope。

另冻结 scientific workload \(W\)：circuit instances、acceptance coordinates、
support、output schema、operation horizon、target precision 和 statistical target；
各 route 的 enumeration/sampling/reference role 按预注册 reference design 冻结。
对 primary full-PEPS/CAPEPS pair 再冻结 resource protocol \(B\)：相同 candidate
execution task、pilot selection set、independent certification/timing holdout、
dtype、same hardware、configuration
grids、equal tuning budget、fresh-process policy、timing boundary、repetitions 和
selection-valid inference。prefix memoization、batching、branch/state reuse 和
contraction-plan reuse 均属于 workload definition。若 target 包含多于一个
fixture，suite 需覆盖 non-Clifford density、angle、rounds 和 pullback/cut
geometry；结果只对冻结点或预注册 aggregate 解释，不外推为 scaling law。

四条 headline routes 与一个 mechanism control 只能共享 neutral object，
不能共享 backend tensors、tableaux、compiled projectors、contraction plans
或 evaluator truth。每个 route 独立输出 lowering trace；trace 必须通过
operation order、axis map、absolute columns、reset semantics 和 fold rows 的
schema checks。每个 artifact 记录 spec/source hash、environment、hardware、
configuration、axis order、branch/sample seed 和 typed completion status。

### 5.2 Dense exact reference

Dense route 在可承受规模上保存 complete complex128 state vector，直接执行
ordered unitaries、projectors 和 reset Kraus operators，并独立实现
raw-to-Record fold。它负责：

- enumerable tracer 的 complete raw 和 joint detector/observable Record law；
- \(d_{\mathrm{code}}=3\) selected histories 的 complete physical vectors；
- 每步 \(p(b_k\mid h_{<k})\)、cumulative raw mass 与 structural zeros；
- reset reduced-state、forced-history absolute columns 和 expected folded rows；
- 若 \(d_{\mathrm{code}}=3\) 采用 sampled `PASS*`，预先指定 one-sample
  exact-population reference 或 independent two-sample dense-reference design，
  并计入 reference uncertainty、joint support 和 confidence allocation。

Dense reference 不能调用 CAPEPS/full-PEPS helper，也不进入 candidate runtime。

### 5.3 Full PEPS comparator

Full PEPS 把 complete physical conditional state 放入一个 PEPS，按同一
operation order 执行 Clifford/non-Clifford gates 和 projector/reset Kraus
operators。target 前必须 hash-freeze：

- initial graph/layout、gate routing 与 swap policy；
- structured gate/operator construction；
- bond grid、cutoff、environment 与 contraction optimizer；
- branch copy、Born contraction、normalization、compression 与 failure policy；
- route-specific lowering、warm-up、cache 和 resource-meter boundary。

Full PEPS 是同-channel comparator，不是 dense referee。它与 CAPEPS 获得相同
pilot tuning budget，之后在 held-out target 前冻结 grid 和选择规则。

### 5.4 CAPEPS candidate

CAPEPS 使用第 3 节的 two-cycle state machine 和 paired instrument
transaction。target implementation 还必须补齐并冻结：

- XZZX compiler、typed operations、absolute raw/Record schema 与 lowering
  trace；
- qubit-to-site map 以及任何 paired residual relayout；
- signed pulled-back coherent operator 的 PEPO/support-tree construction、
  routing 与 contraction environment；
- finite-\(D_{\mathrm{res}}\) compression transaction；
- gauge/environment-aware Clifford candidate search；
- paired Born-mass certificate、structural-zero policy、enumerated
  terminal-frontier validity gate 和 terminal Record reducer；
- complete approximation/work/resource ledger，包括 intermediate peaks 和
  rejected search candidates。

当前 global direct-sum prototype 只能作为 tracer correctness construction，
不能直接进入 efficiency target。

### 5.5 Pauli-twirled tableau approximation

Twirled route 使用相同 operation order、`M(P)`/`MR_Z(q)` schema、absolute
columns 和 Record fold，但把 coherent rotation 换成声明的 stochastic Pauli
channel。它改变 scientific channel，因此不参与 same-channel winner rule，
也不与 coherent conditional pure states 做 branchwise fidelity。它报告
coherent-versus-twirled Record-TV 和资源；若 law 通过 Monte Carlo 获得，则
资源任务必须定义为达到同一个 frozen precision/confidence，而不能把 raw
sample runtime 与 deterministic full-law enumeration 直接比较。

一个 Record-level nondegeneracy control 必须先证明冻结 fixture 的 Record
observable 能区分 coherent 与 twirled channel；否则“twirl Record-TV 小”可能
只是 observable 对 channel difference 不敏感。

### 5.6 \(C|\mathrm{MPS}\rangle\) implementation-level mechanism control

planned control 使用相同 coherent instrument、accuracy gates、matched
frame/operator logic、若干 preregistered 1D orderings，以及 comparable
compression/search budgets，只把 residual carrier 换为 MPS。它不进入 primary
full-PEPS-versus-CAPEPS estimand。该 control 当前未实现，且仓库 existing
restricted MPS service 不具备这里的 neutral lowering 或 Record evidence。即使
control 通过，ordering、canonicalization、compression 和 optimizer 仍是
confounders，所以只报告 topology-sensitive implementation ablation，不作
PEPS-topology causal attribution。

### 5.7 Scale-specific evidence duties

| scale | correctness role | resource role | 最大允许结论 |
|---|---|---|---|
| genuine 2D mechanics tracer | dense-checked \(2\times2\) and preferably \(2\times3\); both edge directions, a loop, relayout, measurement/reset | mechanics diagnostics only | genuine 2D untruncated mechanics on named fixtures |
| enumerable instrument tracer | all positive branches; complete raw and Record laws; structural zeros | mechanics cost only | complete-law correctness on that tracer |
| \(d_{\mathrm{code}}=3\) target | selected complete vectors, probability/log mass, reset, plus enumerated population law or sampled empirical Record certification | selection-aware full PEPS versus CAPEPS | population `PASS` result or explicitly provisional sampled `PASS*` result |
| \(d_{\mathrm{code}}=5\) target | selected checks only where an independent oracle is feasible | fixed-envelope completion, time, memory, work ledgers | provisional resource reachability only |
| existing 25-qubit pure state | dense complete-state fidelity | historical full-PEPS capacity baseline | non-QEC, non-Record, non-CAPEPS context |

\(d_{\mathrm{code}}=5\) does not enter matched-accuracy efficiency because no
independent complete-Record oracle is currently specified. Completion cannot be
promoted to distributional correctness, scaling or threshold evidence.

### 5.8 Accuracy metrics

For aligned same-channel branches, complete-vector fidelity is

\[
F(\psi,\phi)
=
\frac{|\langle\psi|\phi\rangle|^2}
     {\langle\psi|\psi\rangle\langle\phi|\phi\rangle}.
\]

Selected raw histories additionally report

\[
\epsilon_p
=
\max_k\left|
\widetilde p_k-p_k^\star
\right|,
\qquad
\epsilon_{\log W}
=
\left|
\sum_k\log\widetilde p_k-
\sum_k\log p_k^\star
\right|.
\]

The log-mass metric is evaluated only on a preregistered positive-probability
domain \(\mathcal H_{\log}\). Exact zeros are handled by structural-zero
agreement; excluded positive reference mass must be reported and bounded, not
silently dropped by a fixed numerical threshold. Enumerated population raw and
folded Record laws use TV distance on the union support after frontier
validation. Sampled outputs use the preregistered one- or two-sample confidence
construction and receive only `PASS*`; empirical TV is not population TV.
Reset uses both operation trace and one-site trace distance. Paired measurement
reports \(\delta_{\mathrm{comp}}\), but this diagnostic never replaces dense
probability/law error.

### 5.9 Selection-aware primary efficiency estimand

以下只是 protocol skeleton；accuracy bands、fixture suite、grids、repetition
count、confidence allocation 和 effect threshold 仍为 `OPEN`。未赋值并
hash-freeze 前，target 不可执行。

对每个 primary route
\(r\in\{\mathrm{full\ PEPS},\mathrm{CAPEPS}\}\)，冻结 pilot/selection set、
independent certification-and-timing holdout、grid \(\mathcal C_r\)、equal tuning
budget 和 deterministic selection rule。查看 pilot 前，为两条 primary routes
冻结同一个 evidence class
\(e\in\{\mathrm{PASS},\mathrm{PASS}^{\ast}\}\)：
\(e=\mathrm{PASS}\) 表示 enumerated population certification，
\(e=\mathrm{PASS}^{\ast}\) 表示 sampled provisional certification。pilot 上定义

\[
\mathcal C_{r,\mathrm{sel}}^{e}
=
\{c\in\mathcal C_r:\mathcal G_{\mathrm{sel}}^{e}(r,c)=e\},
\qquad
c_r^\dagger
=
\arg\min_{c\in\mathcal C_{r,\mathrm{sel}}^{e}}
\widehat\tau_{r,\mathrm{sel}}(c).
\]

并冻结 tie-break。grid-wide gate 和选择必须使用 simultaneous inference、
nested selection 或另一种预注册 selection-valid construction。evidence-class set 为空时 route 返回 typed `UNAVAILABLE`。选定 \(c_r^\dagger\) 后不得因 holdout
结果重新选择；若 \(\mathcal G_{\mathrm{hold}}^{e}(r,c_r^\dagger)\ne e\)，该 route 同样
`UNAVAILABLE`。

对 holdout evidence class 一致的 frozen configuration，run-protocol population
runtime target 为

\[
\tau_r
=
\operatorname{median}_{s\sim\Pi_{\mathrm{run}}}
T_r(W_{\mathrm{hold}},c_r^\dagger;s),
\qquad
\theta_T
=
\log\frac{\tau_{\mathrm{full\ PEPS}}}
          {\tau_{\mathrm{CAPEPS}}}.
\]

\(\Pi_{\mathrm{run}}\) 是 frozen fresh-process/run-order protocol，不是 observed
finite repeats。independent timing holdout 用 selection-independent procedure
估计 \(\tau_r\) 与 \(\theta_T\)。若 \(\delta_T\) 是最小有意义 fractional
speedup，则 log-time threshold 定义为

\[
\Delta_{\log T}=\log(1+\delta_T).
\]

只有 \(\theta_T\) lower confidence bound 超过 \(\Delta_{\log T}\)，才报告
bounded runtime advantage。population `PASS` 支持 population-law headline；
sampled `PASS*` 只支持明确带 provisional qualifier 的 performance result。

primary timing 是 **configuration selection 之后的 end-to-end candidate
execution**。它包括 route-specific lowering、tableau work、operator
construction/routing、tensor contractions、branch copies、measurement/reset、
internal candidate search 与 rejected candidates、compression、device
synchronization 和 Record aggregation。neutral-fixture construction、offline
pilot tuning 和 dense certification 被定义为 endpoint 外成本，但必须单独报告
并给出 amortization analysis；因此该 endpoint 不是 total research cost。

benchmark protocol 还必须冻结 warm-up、compilation/cache policy、CPU/thread
affinity、prefix memoization、batching、branch/state reuse、contraction-plan
reuse、GPU synchronization、randomized serial run order 与 fresh-process
boundary。peak process-tree host RSS 和 device high-water 是 secondary；
preregistration 必须指定 device-memory measurement owner，以及 allocated、
reserved、external workspace、child-process 与 cache memory 是否计入。memory
报告 primary-selected configurations 和 registered Pareto table，不得事后替代
runtime winner rule。maximum bond 只作 explanatory diagnostic，并伴随 edge
dimensions、tensor elements、effective rank/sparsity（若定义）、contraction
width 和 actual bytes。

### 5.10 Execution order

1. 关闭 CAPEPS-specific literature gap，修复 source-cache audit，并冻结 metrics
   与 preregistration。
2. 通过 algebra、schema、axis、lowering-trace、absolute-fold 和 corruption
   tests。
3. 通过 genuine \(2\times2\)/\(2\times3\) 2D mechanics gate。
4. 在 enumerable multi-step tracer 上完成 dense/full PEPS/CAPEPS complete
   raw/Record law。
5. 为 \(d_{\mathrm{code}}=3\) 冻结 enumerated `PASS` 或 sampled `PASS*`
   reference design，并完成 state/mass/reset/Record certification。
6. 在 pilot 上 selection-valid 地冻结 full PEPS/CAPEPS configurations，再在
   independent certification/timing holdout 上运行 primary comparison。
7. 单独运行 twirled-tableau Record approximation；若实现 mechanism control，
   只报告带 ordering/optimizer confounders 的 topology-sensitive ablation。
8. 只有所有必要 \(d_{\mathrm{code}}=3\) gates 通过后，才运行
   \(d_{\mathrm{code}}=5\) provisional reachability。

任何前置 gate 失败都停止下游结论传播；target 不得用当前 mechanics 结果或
full-PEPS legacy preregistration 越过该顺序。

## 6. Results

### 6.1 Completed bounded evidence：all-qubit untruncated mechanics

两组聚焦测试共十八项通过。它们在 named dense 和 strip-shaped PEPS fixtures
上支持以下工程事实：

- physical Clifford 按正确方向左合成到 tableau frame；
- GCAMPS Eq. (5) 的 GF(2) solve、ordered-generator reconstruction 和 direct
  Stim pullback 三路一致，并保留 Pauli sign；
- arbitrary small-local qubit unitary 可以重构为 coherent Pauli expansion；
  默认 \(k\le2\)，更大 support 需要显式 opt-in；
- coherent residual update 与 separately formulated complex128 dense construction
  一致；
- \((C,\phi)\mapsto(CQ^\dagger,Q\phi)\) 保持 physical ray，失败时不提交
  partial update；
- Pauli observable、paired measurement branches、Born mass、tiny positive
  branch 和 physical-Z measured reset 在这些 fixtures 上工作。

这回答的是“当前 untruncated qubit mechanics 是否在 bounded fixtures 上正确”，
不是“二维 CAPEPS 是否验证完成”或“CAPEPS 是否更高效”。所有 PEPS tests 都是
\(1\times N\) 或 \(N\times1\) strips。当前 multi-site coherent update 采用
global algebraic direct sum，并使多个 virtual bonds 同时增长；它暴露的是
tracer implementation 的瓶颈，而非 finite-bond CAPEPS 的性能结果。

### 6.2 Completed baseline：25-qubit full-PEPS pure state

现有数值来自 25-qubit、\(5\times5\)、open-boundary coherent pure-state
fixture。它没有 syndrome ancilla、中途 measurement、reset、raw branch law、
detector fold 或 logical observable，只能作为 historical full-PEPS capacity
baseline。

| implementation | \(D=1\) | \(D=2\) | \(D=4\) | \(D=8\) | \(D=16\) |
|---|---:|---:|---:|---|---|
| Quimb full PEPS | 0.0000851688316772 | 0.9998969172932962 | 0.9999999860634252 | `UNAVAILABLE`: CUDA OOM | `UNAVAILABLE`: CUDA OOM |
| Pepsy full PEPS | 0.0000851688316772 | 0.9998327620972642 | 0.9999995335988606 | `UNAVAILABLE`: CUDA OOM | `UNAVAILABLE`: predicted 4 TiB intermediate |

最佳已完成 \(D=4\) resource points 为：

| implementation | \(1-F\) | host peak | device peak | wall time |
|---|---:|---:|---:|---:|
| Quimb | \(1.39365748\times10^{-8}\) | 2.533 GB | 1.678 GB | 9.552 s |
| Pepsy | \(4.66401139\times10^{-7}\) | 2.509 GB | 1.678 GB | 6.536 s |

注册五点 sweep 的 verdict 仍是 `inconclusive_partial`，因为 \(D=8,16\) 未
完成。这些数字不得用于选择 CAPEPS target bands，也不能证明 full PEPS
相对 CAPEPS 浪费资源；二者尚未在同一个 instrument 上做 matched-correctness
比较。

### 6.3 `PENDING` correctness results

`PENDING` 表示尚未执行，不是零、失败或通过。

| output | dense | full PEPS | CAPEPS | twirled tableau | \(C\lvert\mathrm{MPS}\rangle\) control |
|---|---|---|---|---|---|
| genuine 2D mechanics tracer | reference | diagnostic | `PENDING` | n/a | n/a |
| multi-step tracer complete raw law | reference | `PENDING` | `PENDING` | separate channel | `PENDING` if built |
| multi-step tracer joint Record-TV | reference | `PENDING` | `PENDING` | `PENDING` approximation | `PENDING` if built |
| \(d_{\mathrm{code}}=3\) selected complete-vector fidelity | reference | `PENDING` | `PENDING` | not like-for-like | `PENDING` if built |
| \(d_{\mathrm{code}}=3\) probability/log-mass error | reference | `PENDING` | `PENDING` | separate stochastic law | `PENDING` if built |
| \(d_{\mathrm{code}}=3\) `MR_Z` check | reference | `PENDING` | `PENDING` | `PENDING` | `PENDING` if built |
| \(d_{\mathrm{code}}=3\) population `PASS` or sampled `PASS*` Record gate | protocol not yet CAPEPS-preregistered | `PENDING` | `PENDING` | `PENDING` approximation | `PENDING` if built |
| coherent-versus-twirled Record nondegeneracy | reference pair | n/a | n/a | `PENDING` | n/a |

因此当前不能声称 Record-faithfulness、complete cq-instrument equivalence、
finite-bond correctness 或 two-dimensional mechanics acceptance。

### 6.4 `PENDING` resource results

| scale | route | gate status | frozen \(c_r^\dagger\); \(\tau_r\) / CI | host peak | device high-water | completion |
|---|---|---|---|---|---|---|
| \(d_{\mathrm{code}}=3\) | full PEPS | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| \(d_{\mathrm{code}}=3\) | CAPEPS | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| \(d_{\mathrm{code}}=3\) | twirled tableau | different-channel diagnostic | separately defined | `PENDING` | `PENDING` | `PENDING` |
| \(d_{\mathrm{code}}=3\) | \(C\lvert\mathrm{MPS}\rangle\) control | planned mechanism control | not primary | `PENDING` | `PENDING` | not implemented |
| \(d_{\mathrm{code}}=5\) | full PEPS | reachability only | not in primary estimand | `PENDING` | `PENDING` | blocked on \(d_{\mathrm{code}}=3\) |
| \(d_{\mathrm{code}}=5\) | CAPEPS | reachability only | not in primary estimand | `PENDING` | `PENDING` | blocked on \(d_{\mathrm{code}}=3\) |

Maximum bonds、edge-direction dimensions、intermediate peaks、contraction width
和 search/compression costs 将进入 work ledger，而不是替代 frozen
configuration、\(\tau_r\) 与 \(\theta_T\) 的 headline columns。

### 6.5 Preregistered result interpretation

- 只有 full PEPS 与 CAPEPS 的 frozen configurations 都通过 independent
  holdout gates，且 \(\theta_T\) 的 lower confidence bound 超过
  \(\Delta_{\log T}=\log(1+\delta_T)\)，才报告冻结
  \(d_{\mathrm{code}}=3\) workload 上的 bounded runtime advantage。
- 若 CAPEPS memory 更低但 primary runtime criterion 未通过，只报告 secondary
  memory result，不改写 winner rule。
- 若任一路径没有 passing configuration，报告 typed `UNAVAILABLE`；不把缺失
  时间解释为 infinite speedup。
- 若 conditional fidelity 通过而 branch mass 或 Record gate 失败，该
  configuration 不通过。只有 enumerated population `PASS` 可写
  Record-faithful；sampled `PASS*` 必须写 provisional。
- 若 CAPEPS 正确但不更快，则 hybrid representation 在该 workload 上没有
  转化为 end-to-end runtime advantage；routing、Born contraction、search 或
  compression cost 是待分析机制。
- \(C|\mathrm{MPS}\rangle\) control 即使通过，也只支持带 ordering、
  canonicalization、compression 和 optimizer confounders 的
  implementation-level topology-sensitive ablation，不支持 topology causal
  attribution。
- cross-cut operator-Schmidt complexity 与 resource growth 的相关性是机制
  diagnostic，不是单凭相关性建立的因果证明。
- twirled tableau 只产生不同-channel approximation verdict。Record-TV 在 band
  内仅说明冻结 observable 未检测到超出 band 的 channel effect，不证明 channel
  相同。
- \(d_{\mathrm{code}}=5\) completion 只说明 fixed workload 在给定 envelope 下
  reachable，不代表 complete law、accuracy transfer、scaling、threshold 或
  production readiness。

## 7. Limitations

1. **尚无 genuine 2D CAPEPS evidence。** 当前 PEPS fixtures 全是 strips；
   horizontal/vertical updates、plaquette loop、2D contraction 与 relayout 的
   组合尚未经过 dense truth。
2. **bond-growth mechanism 是 cut complexity，不是 Pauli weight。** 单个
   Pauli string 的 operator-Schmidt rank 为 1；困难来自 coherent operator
   sums 跨 residual cuts 的 rank、cut geometry 及重复 composition。现有 ledger
   尚未完整测量这些对象。
3. **全数据 \(R_Y\) 可能扩散 residual。** 它不是 sparse-magic regime，可能
   快速耗尽任何 residual bond advantage。
4. **global direct sum 不可扩展。** 当前 construction 保留 coherence 以服务
   tracer correctness，却同时增加许多 virtual bonds；structured PEPO、routing
   与 finite-bond compression 尚未实现。
5. **PEPS optimizer 尚未定义。** 有环 PEPS 没有 MPS 式唯一 Schmidt objective；
   candidate catalogue、environment、gauge-aware objective、cadence、tie-break
   和 cost 都必须先冻结。GCAMPS 的 20-class source fact 不是 executable
   optimizer specification。
6. **measurement contraction 可能仍主导。** 把 Clifford entanglement 移出
   PEPS 不会自动解决 residual norm/environment contraction。paired complement
   只是一项 invariant，不是 accuracy oracle。
7. **structural zeros 未获完整证书。** 当前浮点路径能保留 tiny positive
   branches，但 algebraic cancellation 仍可能产生伪微正 mass；不能用统一
   threshold 掩盖。
8. **canonical Record backend 尚未接入。** 当前只有 ordered raw events，
   还没有 atomic paired certificate 或 global frontier gate。enumeration 随正
   分支数增长；sampling 不拥有 complete frontier，只能产生带 reference
   uncertainty 的 provisional `PASS*`。
9. **primary experiment 尚未 preregister。** accuracy bands、pilot/holdout
   split、configuration grids、selection-valid inference、tuning budget、
   \(\delta_T\)、CI 和 workload suite 仍为 `OPEN`；不得运行后再选择有利规则。
10. **mechanism control 仍有混杂。** 新的
    \(C|\mathrm{MPS}\rangle\) route 尚未实现；即使实现，1D ordering、
    canonicalization、compression 和 optimizer 差异仍阻止 topology-only
    causal claim。
11. **相邻工作显著收窄 design claim。** hybrid
    \(C|\mathrm{MPS}\rangle\) 已用于 repeated surface-code extraction 和
    projective measurement [8]，并包含 reset-error rate。本稿仅定位相对于 [8]
    待检验的 residual-PEPS、explicit transaction/Record protocol 与 comparator
    differences；novelty closure 仍为 `OPEN`，不作 priority claim。
12. **\(d_{\mathrm{code}}=3\) 与 \(d_{\mathrm{code}}=5\) 证据不可互换。** 前者承担独立 correctness；后者
    当前只承担 reachability。完成不等于 accuracy transfer。
13. **twirling 改变 channel。** twirled tableau 不是 coherent trajectory 的
    低精度版本；Record observable 还可能对 channel difference 退化不敏感。
14. **qutrit leakage 留作后续。** generalized-qudit tableau 不等于
    computational-qubit-plus-leakage direct sum；leakage 需要新的 basis、
    instrument 和 independent reference。
15. **没有 decoder、LER 或 threshold claim。** 本文不拟合 hardware 参数，
    不报告 logical-error threshold、\(d_{\mathrm{code}}=7\) 或 long-round scaling。

## 8. Conclusion

本文把论文主角明确为

\[
\boxed{
\text{GCAMPS-inspired CAPEPS}
+
\text{QEC instrument}
+
\text{Record correctness}
}.
\]

方法不是四个彼此独立的 quantum loops，而是两个 GCAMPS state-return cycles：
physical Clifford 只更新 tableau frame；coherent operator 经 signed pullback
后更新 residual，并进入共同的 exact-refactor/compression tail。measurement
与 `MR_Z` 形成 branch-producing route，调用同一个 residual kernel；raw norm
estimates 先通过 real/finite/positive-parent validation，才计算 paired Born
masses，且一切发生在 normalization 或 compression 之前。enumerated route
只有在 complete frontier 通过 global validity gate 后才产生 population Record
law；sampled route 逐 trajectory fold，只能获得 provisional `PASS*`。

当前证据只证明 all-qubit untruncated mechanics 在 dense 和 strip-shaped
fixtures 上工作。它没有证明 genuine-2D mechanics、finite-bond accuracy、
atomic paired certificate、canonical Record、population-law
Record-faithfulness 或 resource advantage。25-qubit full-PEPS pure-state 数字
继续保留为 historical baseline，不承担 QEC 结论。

中心科学问题仍然开放。下一步依次是：关闭 CAPEPS-specific literature gap；
赋值并冻结 metrics/preregistration；完成 genuine-2D 与 enumerated multi-step
tracers；为 \(d_{\mathrm{code}}=3\) 冻结 population `PASS` 或 sampled `PASS*`
reference design；在 pilot 上 selection-valid 地选择 full PEPS/CAPEPS
configurations；最后在 independent certification/timing holdout 上估计
\(\theta_T\)，并把 memory 作为 secondary outcome。\(d_{\mathrm{code}}=5\)
仍只承担 provisional reachability，twirled tableau 只承担 different-channel
trade-off。

若获得 enumerated population `PASS`，允许的正面结论只限于冻结
\(\mathcal O\) 和声明 hardware/resource envelope 下的 selected-state、
branch-mass、reset、raw-law 与 detector/observable Record population gates，
以及 full PEPS/CAPEPS 的 selection-aware timing/memory measurements。若只有
sampled `PASS*`，结论必须写成 “provisional performance under preregistered
sampled Record certification”。若 CAPEPS 因 all-data \(R_Y\)、cross-cut
coherent complexity、measurement contraction 或 optimizer cost 而没有优势，
该负结果同样回答本稿的可证伪问题。

## References

[1] S. Masot-Llima and A. Garcia-Saez, “Stabilizer Tensor Networks:
Universal Quantum Simulator on a Basis of Stabilizer States,” *Physical
Review Letters* **133**, 230601 (2024).
[arXiv:2403.08724](https://arxiv.org/abs/2403.08724)

[2] B. Harper, A. C. Nakhl, T. Quella, M. Sevior, and M. Usman, “GCAMPS:
A Scalable Classical Simulator for Qudit Systems,” SCA/HPCAsia 2026.
[arXiv:2511.06672](https://arxiv.org/abs/2511.06672)

[3] M. Lubasch, J. I. Cirac, and M.-C. Bañuls, “Algorithms for Finite
Projected Entangled Pair States,” *Physical Review B* **90**, 064425
(2014). [arXiv:1405.3259](https://arxiv.org/abs/1405.3259)

[4] N. Schuch, M. M. Wolf, F. Verstraete, and J. I. Cirac,
“Computational Complexity of Projected Entangled Pair States,” *Physical
Review Letters* **98**, 140506 (2007).

[5] J. P. Bonilla Ataides, D. K. Tuckett, S. T. Bartlett, S. T. Flammia,
and B. J. Brown, “The XZZX Surface Code,” *Nature Communications* **12**,
2172 (2021). [arXiv:2009.07851](https://arxiv.org/abs/2009.07851)

[6] A. S. Darmawan et al., “Practical Quantum Error Correction with the
XZZX Code and Kerr-Cat Qubits,” *PRX Quantum* **2**, 030345 (2021).
[arXiv:2104.09539](https://arxiv.org/abs/2104.09539)

[7] events555, “sdim: A d-dimensional stabilizer circuit simulator,”
[GitHub repository](https://github.com/events555/sdim), adapter target
inspected at commit `115c495b23ade35ef0f68b7299afef463129bf51`.

[8] B. Harper, A. C. Nakhl, M. Sevior, and M. Usman, “Non-Clifford
Crosstalk Noise in Surface Codes Using Hybrid Stabilizer-Tensor Network
Methods,” arXiv:2605.29514v1 (2026).
[arXiv:2605.29514](https://arxiv.org/abs/2605.29514)

## Evidence and reproducibility index

- CAPEPS implementation boundary:
  [`../../src/error_coupling_simulator/carrier/capeps/README.md`](../../src/error_coupling_simulator/carrier/capeps/README.md)
- GCAMPS formula ledger and implementation audit:
  [`GCAMPS_2511_06672_FORMULA_IMPLEMENTATION_AUDIT_2026-07-27.md`](GCAMPS_2511_06672_FORMULA_IMPLEMENTATION_AUDIT_2026-07-27.md)
- Focused mechanics tests:
  [`../../tests/test_capeps_hybrid.py`](../../tests/test_capeps_hybrid.py)
  and [`../../tests/test_capeps_gcamps_formulas.py`](../../tests/test_capeps_gcamps_formulas.py)
- Adjacent hybrid-QEC source that narrows novelty:
  [Harper et al., arXiv:2605.29514v1](https://arxiv.org/abs/2605.29514)
- Binding simulator contract:
  [`../SIMULATOR.md`](../SIMULATOR.md)
- Measurement--reset--Record literature closure:
  [`PEPS_XZZX_MEASUREMENT_RESET_RECORD_LITERATURE_CLOSURE_2026-07-26.md`](PEPS_XZZX_MEASUREMENT_RESET_RECORD_LITERATURE_CLOSURE_2026-07-26.md)
- Current full-PEPS instrument preregistration:
  [`PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_V2_2026-07-27.md`](PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_V2_2026-07-27.md)
- Completed 25-qubit baseline:
  [`PEPS_D5_COMPLETE_STATE_FIDELITY_RESULTS_2026-07-26.md`](PEPS_D5_COMPLETE_STATE_FIDELITY_RESULTS_2026-07-26.md)

The existing full-PEPS preregistration does not automatically authorize the
CAPEPS target. Residual layout, disentangler search, compression, paired-norm
certificate, terminal-frontier gate, CAPEPS correctness bands, population
`PASS`/sampled `PASS*` rules, four headline routes, the mechanism control, and
the selection-aware resource verdict require a CAPEPS-specific closure/addendum.
The current theory-fix disposition is `REPAIR`: source-cache audit, genuine-2D
mechanics, canonical Record, finite-bond algorithms, numerical gate values, and
statistical preregistration remain open, so target execution remains stopped.
