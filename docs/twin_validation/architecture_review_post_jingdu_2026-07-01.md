# Architecture Review — coupled-teacher post-精读 reassessment

**Date:** 2026-07-01
**Context:** 5 篇近期文献精读完成后，对 `coupled_teacher_architecture_synthesis.md` 的重新评估。
**Epistemic status:** 所有定量声明均基于 5 篇 certificate-grade 精读笔记中的方程和数据。

> **⚠ CORRECTION (2026-07-01, later same day) — this review OVER-CLAIMED 2D-iPEPO feasibility.**
> The feasibility claims below ("面积律 → d7/d9 可行", "完全在 MPS 能力范围内", "架构可行性 ✅ 已确认",
> "精读未发现任何架构上的缺陷") are **NOT supported by our own tePEPO 精读 note**
> (`docs/papers/reading_notes/tepepo_2d_open_system_tn_2512.01781.md`). That note establishes: **(1) tePEPO
> is MARKOVIAN-ONLY** (GKSL, time-local ≤2-body) — it carries NO bath memory, so our non-Markovian wedge
> requires ADDING explicit pseudomode/bath SITES (raises local dim + bond dim — NOT free); **(2) the itrSU
> truncation is UNCONTROLLED and already marginal at correlation length ξ≳2** (rank-1 environment) — and a
> SHARED bath induces LONGER ξ, so it likely BREAKS past that point; **(3) no certified error bound** off the
> exactly-solvable line. The 2^(2d) relief is real for the **state geometry ONLY**; the non-Markovian memory
> axis is orthogonal and unaddressed. **Corrected verdict: the direction (2D iPEPO) is right, but feasibility
> for OUR shared-bath non-Markovian physics is UNVERIFIED and at-risk. The blocking first gate is the itrSU
> truncation-stability test at the shared-bath ξ (§4 step 4, hereby ELEVATED to BLOCKING), not the SDP/n_max
> pilots.** Inline corrections are flagged **[CORRECTED]** below; the 5-paper assessment + pilots + baseline
> anchor content remains valid.

---

## 1. 地基验证

### Paper 1: Coupled-Lindblad Pseudomode (2506.10308, PRL 2026)

**精读确认：** ✅ 方法可靠，prerequisites 可测试。

| 声明 | 状态 | 证据 |
|-------|--------|----------|
| 增广系统是精确 CPTP GKSL (Eq. 2) | ✅ 定理级 | H=H†, Γ≥0 — 两个条件均被严格证明 |
| polylog(T/ε) 模式数标度 | ✅ 定理级 (条件性) | 定理 1 + Fig. 1a: N=O(log T), fixed ε=1e-6 |
| 凸 SDP 构造 (Eq. 8) | ✅ 可实现 | 凸最小二乘 + LMI 约束，替代非凸优化 |
| 矩阵值耦合 (SM Eq. S2-S4) | ✅ 显式给出 | g∈C^{N×n} 直接编码多量子比特共享浴 |
| 可行性条件 (Eq. 7) 是否在我们的 BCF 上满足？ | ⚠ 未测试 | 必须检验——这是阻塞性前置条件 |

**关键约束：** 高斯浴 (Fermi/Bose 二次型)；BCF 解析性 (继承自 ref [26])；可分离初始态。非高斯浴（如强耦合单 TLS）超出范围。

**对我们的更正：** 之前我描述为准-Lindblad → 耦合-Lindblad "转换"。准确的说法是：定理 1 是一个**规范变换** `(l, X) → g = l·X^{1/2}`, `K = X^{1/2}·K̃·X^{-1/2}`，当 SDP 可行性条件成立时，将准-Lindblad BCF 映射为具有**相同模式数 N** 的耦合-Lindblad BCF。

---

### Paper 2: Markovian Embeddings Unification (2602.21430, JCP 2026)

**精读确认：** ✅ 三个框架是同一对象的不同表示。

| 声明 | 状态 | 证据 |
|-------|--------|----------|
| HEOM ⇔ Lindblad-PM ⇔ Thermofield-MPS 等价 | ✅ 定理级 | Eq. 14 Bogoliubov 变换是规范自由度 |
| Keldysh/三角嵌入 (Eq. 33) 给出显式 GKSL | ✅ 显式 | 应馈入我们载体的嵌入方式 |
| 截断 HEOM 发散 → Bogoliubov 变换修复 | ✅ 数值验证 | 变换与截断的不可交换性 |
| 多站点共享浴 | ❌ 未解决 | "可分离项之和"，不耦合 |

**对我们的关键启示：** Keldysh 嵌入 (Eq. 33) 是应该**编码**的形式。它给出显式的 H, Γ 矩阵，可直接插入 MCWF/2D-iPEPO 载体。与耦合-Lindblad 论文的关系：2602.21430 提供了**统一框架**，2506.10308 提供了最优模式数的**构造算法** (SDP)。两者互补。

---

### Paper 3: Correlated Noise Embedding (2509.19685)

**精读确认：** ✅ 单量子比特原始配方已确认。RWA 破坏成本是关键开放问题。

| 声明 | 状态 | 证据 |
|-------|--------|----------|
| 极点→赝模式→精确 Lindblad 配方 (Eq. 14-21) | ✅ 显式 | 5 步构造序列 |
| 闭式真值验证 (Eq. 40-45) | ✅ 独立预言机 | Rule-I 锚点 |
| CP-可分性破坏 (γ₀/λ > 1/2) | ✅ 定量 | 非马尔可夫优势来源 |
| RWA 破坏 n_max 成本 | ⚠ 关键缺口 | 仅对 JC 模型给出上界，QEC 门未测试 |

**RWA 成本估算（基于论文参数 + 我们的 QEC 数值）：**

```
QEC 参数范围：g/ω₀ ~ 10⁻² 至 10⁻³（门时间 ~10-100 ns, ω₀ ~ GHz）
截断误差标度：O((g/ω₀)^(n_max))（微扰体系）
预估：n_max = 2-4 可能足够，但需数值收敛测试
```

**对我们的更正：** 之前说"RWA 破坏 → 成本未量化"。准确的说法是：成本标度**已知** (O((g/ω₀)^(n_max)))，但**数值系数未知**——需要进行收敛测试。

---

### Paper 4: PT-Aware TN Decoder (2412.13739)

**精读确认：** ✅ 工程上可复用。关键限制已明确。

| 声明 | 状态 | 证据 |
|-------|--------|----------|
| 链接积 ⊗ TN 收缩正确 (Eq. 4/17/20) | ✅ 定理级 | Choi 态 + 双狄拉克形式 |
| LER 从单次收缩得出 (Eq. 45/49) | ✅ 显式 | 对所有症候 + 逻辑操作求和 |
| MPS 截断诊断 (BEE, p_est/p_perf) | ✅ 工程方法 | 可迁移到我们的实现 |
| 私有浴 only（无共享潜在变量） | ❌ 限制 | 必须推广到共享浴 |
| HS 度量相干盲 | ❌ 限制 | 必须替换为相干敏感度量 |
| 无 MWPM 基线对比 | ❌ 缺口 | 我们的贡献点 |

**对我们的关键启示：** 链接积框架 + quimb/cotengra 工程栈可直接复用。核心推广需求：(a) 私有浴 → 共享潜在浴，(b) HS → 相干敏感度量，(c) 单轮 → 多轮。这三个推广解决了论文明确承认的局限，构成了我们解码器贡献的技术核心。

---

### Paper 5: Exact Correlated Threshold (2510.24181)

**精读确认：** ✅ 定理级基线。闭合形式边规则是 class-(a) 精确锚点。

| 声明 | 状态 | 证据 |
|-------|--------|----------|
| 闭合形式 p̄₂ = 2(1−p₂)p₂ + RBIM 映射 | ✅ 定理级 (class-a) | Eq. 推导，p₂→0 极限已验证 |
| 精确阈值 ~3% (p1=p2=p) | ⚠ 数值 (b) — **非定理级** | MC+FSS (L≤24, ~1 sig-fig, 无误差棒); 精读笔记: "阈值数值是 MC 推导的，非闭合形式" |
| 关联盲 MWPM ~1.8-1.9% | ✅ 数值 | PyMatching 2.0 |
| 关联感知 Stim-DEM ~2.4% | ✅ 数值 | Stim + 关联感知 DEM |
| 净空 0.5-0.6% | ⚠ 数值 (~1 sig-fig, 精度受限于 3% 的 MC 不确定性) | Δ_threshold = 3.0% − 2.4% |

**对我们的关键启示：** 这是**空间-马尔可夫基线**的定理级锚点。净空 0.5-0.6% 量化了"可移除马尔可夫部分"——我们从非马尔可夫楔形中声称的任何 ΔLER 必须超过此值才具有解码相关性。

**认证协议（来自精读）：** 5 步接缝认证：(1) 验证 p̄₂ = 2(1−p₂)p₂ 在我们的模拟中精确成立；(2) 在两组 (p1, p2) 上测试；(3) 验证陪集等价性；(4) 确认解码器差距模式随 d 保持；(5) 在非对称 (p1≠p2) 点上交叉检验。

---

## 2. 架构重新评估

### 2.1 成立的部分（高置信度）

**I. 耦合-Lindblad-赝模式嵌入。** 方法已发表 (PRL)，polylog 标度已被证明，CPTP 已被保证，多量子比特推广已在 SM 中给出。**这是架构最稳固的支柱。**

**II. 预言机层。** 三个独立方法 (ACE, chain-mapping, T-TEDOPA) 现在都有精读笔记支撑。每个都具有**方法学**独立性（路径积分 vs MPS vs chain-mapping — 不同的数学家族，满足反循环 Rule I 的方法层面），覆盖 2-6 量子比特范围，涵盖玻色子浴 (ACE/T-TEDOPA) 和离散浴 (chain-mapping)。

> ⚠ **共享盲点披露（2026-07-01 审计）：独立性是方法层面的，不是假设层面的。** 载体（赝模式=高斯）和
> 全部三个预言机（ACE 集体耦合=自旋玻色子高斯、chain-mapping=玻色子、T-TEDOPA=高斯/谐振子）共享
> **高斯浴假设**（浴完全由 2-点 BCF 表征）。非高斯 / 离散 TLS 电报饱和区域 = 载体和所有预言机的
> **共享盲点**——在该区域，预言机无法认证载体（两者都看不见）。ACE 的 `add_single_mode` 非高斯
> 能力是独立非谐振模式构造，**不是**集体耦合共享浴构造——不能作为非高斯共享浴预言机。反循环
> 证书仅在高斯区域内有效；非高斯区域必须显式括号或使用不同预言机。

**III. 解码器 + 可观测量。** PT 感知解码器链路积框架可复用。PT-vs-Markov ΔLER 是明确定义的标题指标。相干敏感度量替换需求已明确识别。

**IV. 基线锚点。** 闭合形式 p̄₂ = 2(1−p₂)p₂ 是 class-(a) 精确锚点。净空 ~0.6%（来自 ~3% MC 数值阈值，精度 ~1 sig-fig）设定了解码相关性的**大致标度**（非精确基线）。

### 2.2 修改的部分（精读后更正）

**I. 构建方法：** 之前描述为"准-Lindblad + 启发式转换"。正确的是：**凸 SDP** (Eq. 8) —— 确定性的、可证明最优的、可复现的。不需要启发式方法。

**II. 嵌入选择：** 之前列举了多种选项而不作推荐。正确的是：使用 **Keldysh/三角嵌入** (2602.21430 Eq. 33)，馈入耦合-Lindblad SDP (2506.10308 Eq. 8)。两者是互补的：2602.21430 给了我们正确的高斯 unraveling 框架，2506.10308 给了我们 CPTP + polylog 构造。

**III. RWA 风险：** 之前说"成本未量化"。正确的是：标度已知 (O((g/ω₀)^(n_max))) 在微扰理论中，但**确切标度是模型依赖的**，且 `[2509.19685]` 论文**显式推迟了非激发数守恒情况的分析**（"leave the analysis of the more general scenario for the future work"）。对于我们的 QEC 参数窗口 (g/ω₀ ~ 10⁻² 至 10⁻³)，n_max=2-4 是一个**合理猜测但无来源支持**——必须通过 2509.19685 的 Eq. 40-45 闭式真值进行数值收敛测试；**论文本身未为 QEC 门提供 n_max 估算**。这是一个 (c) 级启发式估计，不是 (b) 级有依据的预测。

**IV. 解码器缺口：** 精读确认了三个缺口（无共享浴、相干盲度量、无 MWPM 基线），之前仅有推测。现在已记录为明确的技术需求。

### 2.3 新风险（精读后浮现）

**I. SDP 可行性是阻塞性前置条件。** 如果我们的 QEC BCF 不满足 Eq. 7 可行性条件，则 polylog 标度不成立。**缓解措施：** 在试点第一阶段就测试 SDP；使用 2506.10308 SM Eq. S1 的备用频域构造方法。

**II. 高斯浴假设。** 真实 1/f 噪声来自 TLS 缺陷（非高斯）。**缓解措施：** Lorentzian 求和近似（2602.21430 Eq. 18）在物理上对 TLS 系综是忠实的。ACE 提供非高斯回退。**残余风险：** 需要强耦合单 TLS → 可能超出范围。

**III. RWA 破坏成本被低估。** QEC 门 (X, Y, CZ) 强烈破坏激发数守恒。精读后：标度已知，但系数可能很大。**缓解措施：** 试点阶段 n_max=2-10 的收敛测试；使用独立预言机验证。

**IV. 复合可行性。** 赝模式 + iPEPO 简单更新截断在 ξ≳2 时已经不稳定——加入赝模式站点可能使其恶化。**缓解措施：** 先测试纯 iPEPO 基准，再逐步添加赝模式；如果简单更新失败，考虑完整更新/VUMPS 收缩。

### 2.4 不变的部分

**核心架构方向保持不变：** 赝模式-on-2D-iPEPO, 预言机验证。**[CORRECTED]** ~~精读未发现任何架构上的缺陷~~ —
这句是错的。tePEPO 精读**确实发现了一个决定性限制**：tePEPO 本身是 **Markovian-only**（不携带记忆），
我们的非马尔可夫楔形必须**额外添加赝模式站点**（提高 local dim + bond），而 itrSU 截断**在 ξ≳2 已经不受控**，
共享浴的更长 ξ 很可能突破它。方向没问题，但**载体可行性对我们的物理未经验证**。

**我们的贡献仍然有效：** (1) 耦合-Lindblad 的 QEC 应用，(2) 独立预言机认证方法论，(3) 非马尔可夫楔形（CP-可分性破坏 + 相干复苏）。

---

## 3. 与旧 MPS+MCWF 的对比（更新版）

| 维度 | 旧 MPS+MCWF | 新 赝模式+iPEPO | 精读后变化 |
|----------|----------------|---------------------|-----------------|
| 载体标度 | 1D 蛇形: χ ~ 2^(2d) | 2D iPEPO: χ ~ 面积律（**几何**上） | **[CORRECTED]** tePEPO 精读只确认了**几何**的 2^(2d) 缓解；itrSU 截断在 ξ≳2 不受控（共享浴 ξ 更长→有风险），且 tePEPO 是 Markovian-only（记忆轴未处理）|
| 非马尔可夫性 | 未处理 | 通过赝模式精确嵌入 | 定理级 (PRL 2026) |
| 共享浴/关联 | 因子化 (每个量子比特私有浴) | 矩阵值 g∈C^{N×n} | 已在 SM 中显式给出 |
| CPTP 保证 | 轨迹级 (量子跳跃) | 生成器级 (GKSL) | 两个条件均已证明 |
| 模式数标度 | N/A | polylog(T/ε) | 定理级证明 |
| 独立性验证 | 无 (循环) | 三个独立预言机 (方法层面；共享高斯盲点——见 §2.1-II) | 方法独立已确认；非高斯盲点需括号 |
| 构造方法 | N/A | 凸 SDP (确定性) | 已验证 |
| 主要风险 | 受困于 d=3 | RWA n_max + SDP 可行性 | 已量化 + 可测试 |

**改进量化 [CORRECTED]：** 旧方法在 d=5 时被指数墙阻挡 (χ~2^10≈1024 最小，实际需要更多)。2D iPEPO **在几何上**
把 codestate 的 2^(2d) 纠缠换成面积律 bond D——这一部分是真实的缓解。**但"将 d=7,9 纳入可行范围 / 完全在 MPS
能力范围内"是未经验证的过度声明**：(a) 上面的 `2^d × n_max^p ≈ 288 维`是**边界局部希尔伯特空间**，不是收缩成本 /
bond dim；(b) 真正的成本瓶颈是 itrSU 截断的 bond D，而 tePEPO 精读证明它在 ξ≳2 已经不受控，**共享浴诱导的更长
关联长度正是最危险的情形**；(c) 还要为非马尔可夫记忆**额外添加赝模式站点**，进一步抬高 D。**结论：几何墙的缓解是真的，
但对我们共享浴非马尔可夫物理的整体可行性 = 未验证，取决于 itrSU 截断能否在共享浴 ξ 下保持有界（= 被 ELEVATED 的首要门）。**

---

## 4. 决策建议

**YES — 架构应继续推进。** 5 篇精读夯实了地基：核心方法已发表 (PRL)，polylog 标度已被证明，预言机层已确认，基线锚点已闭合形式。架构设计不存在根本性缺陷。

**但在扩展前强制进行试点：**

| 步骤 | 内容 | 阻塞性？ |
|-----|---------|-----------|
| 1 | SDP 可行性测试 (我们的 QEC BCF) | 是 — 如果失败，必须使用频域备用方案 |
| 2 | n_max 收敛测试 (RWA 破坏，2-4 量子比特) | 是 — 如果 n_max≫10，大型载体成本激增 |
| 3 | 预言机交集验证 (ACE vs chain-mapping vs T-TEDOPA) | 是 — 反循环证书 |
| 4 | **[CORRECTED] 纯 iPEPO 基线 + itrSU 截断在共享浴 ξ 下的稳定性** | **是 — 首要阻塞门（原标"否"是错的）**：tePEPO 精读证明 itrSU 在 ξ≳2 已失效；若共享浴诱导的 ξ 已 >2，则整个 2D-简单更新路线不成立，SDP/n_max 试点都无意义。**廉价前置代理：先在小型 exact DM 上测共享浴诱导的关联长度 ξ，与阈值 2 比较。** |
| 5 | 赝模式+iPEPO 复合试点 (d=3, 1-2 赝模式) | 否 — 按 1-4 的条件 |

**如果 1-3 全部通过：** 大规模架构可行。在 d=7,9 表面码上实现。撰写方法学论文（独立预言机 + PT-vs-Markov ΔLER）。

**如果 1 失败：** 使用 2506.10308 SM §S1 的备用频域构造方法。仍可获得 CPTP，但 polylog 标度不保证 — 需经验性评估。

**如果 2 失败 (n_max 需求大)：** 限制于弱耦合体系。或者探索替代截断方法 (矩阵积态压缩、自适应基组)。

---

## 5. 最终评估

| 标准 | 评估 |
|----------|-------|
| 架构**方向** | ✅ 确认（2D 破 1D 几何墙的方向对） |
| 架构**可行性** | **[CORRECTED] ⚠ 未验证** — itrSU 截断在共享浴 ξ 下能否有界是**未测的首要门**（原标"✅已确认"是错的）|
| 关键风险 | ⚠ 已量化 — **itrSU 截断@共享浴 ξ（首要）** + SDP 可行性 + RWA n_max + tePEPO Markovian-only（需加赝模式站点）|
| 与旧方法的优势 | **几何**面积律缓解已确认；polylog/CPTP/反循环对**生成器**成立；**载体整体可行性未证** |
| 实现准备度 | 方程/构造/验证协议已知；但 2D-iPEPO 载体**尚未存在**（新基建），且核心截断风险未测 |
| 知识状态 | 生成器层 = 定理级精确；**载体可行性层 = 推测性（PROVISIONAL），待 §4 首要门验证** |
