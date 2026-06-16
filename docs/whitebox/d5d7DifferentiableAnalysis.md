# d5 与 d7 白盒载体的可微性评估

## 执行结论

**结论：条件可行，但不应把“端到端精确可微”设为 d5/d7 白盒载体的成败标准。** 更可信的目标，是把 Harper 风格的纯态 stabilizer–TN 载体做成一个**可验证的局部响应引擎**：对连续相干参数走 pathwise 或 tangent propagation，对任何随参数变化的离散 Kraus / 测量分支补上 likelihood-ratio（score-function）项，并尽可能把最终或中间测量做 Rao–Blackwell 化，最后把得到的 Jacobian / Greeks 连同方差与截断偏差带一起导出给 GNN。Harper 论文已经证明了 `|ψ⟩ = C|MPS⟩` 这种“Clifford 主干在 `C`、非 Clifford 残差在 MPS、测量把残差塌缩回 Clifford frame”的前向 carrier 在表面码 coherent crosstalk 上是可扩展的，且 `χ_max = 32` 足以支撑其 d≤9 前向实验；但 Harper 自身是**前向仿真**而不是**逆向校准/可微推断**，这正是你这里未解决、也是研究价值最高的缺口。fileciteturn0file0 fileciteturn0file1

**prediction：** 在 d3 密集 oracle 已就位、d5/d7 又受限于单卡 32 GB / 内存 60 GB 的前提下，最有希望成功的路线不是“对完整 d7 syndrome likelihood 做干净的端到端 autograd”，而是“对局部 block/composite likelihood 做混合梯度估计 + 对 GNN 输出 provenance-tagged response object”。若 spike 结果正常，这条路线足以支持白盒参数恢复、识别/不可识别方向判定、局部 seam overlap 状态导出，以及有限维 counterfactual sensitivity；但若要求在 d7 全图上稳定、低方差地给出精确 `∇_θ log P_θ(s)`，我判断**风险偏高**。Harper 的前向结果、可微张量网络文献、以及近期可微量子轨迹工作都支持“局部响应对象”这一更保守也更可信的目标。fileciteturn0file0 citeturn12view0turn13view0

## 最难技术障碍

**exact：** 真正最难的，不是“张量网络 contraction 能不能微分”，而是“**被离散分支和截断共同边缘化后的 syndrome likelihood** 能不能给出你想要的梯度”。固定计算图上的张量网络 contraction 本身是可微的，自动微分也早已被系统化到张量网络算法；TDVP 还把固定秩 MPS 的演化写成了 tangent-space projector 问题。也就是说，**固定轨道、固定秩、固定图结构**时，可微性不是主障碍。citeturn12view0turn13view4turn13view5

**exact：** 令 `τ` 表示一条完整增广轨迹，包含所有被采样的 Kraus 分支、被采样的中间测量分支、以及任何随机化压缩步骤。则目标 syndrome 的概率可统一写成  
\[
P_\theta(s)=\sum_{\tau} q_\theta(\tau)\, w_\theta(s\mid \tau),
\]
其中 `q_θ(τ)` 是轨迹法的采样分布，`w_θ(s|τ)` 是在该轨迹条件下对目标 syndrome 的剩余权重；若你把最终 syndrome 也采样掉，则 `w` 退化成指示函数 `1\{s(\tau)=s\}`。于是  
\[
\nabla_\theta P_\theta(s)
= \mathbb E_{\tau\sim q_\theta}\!\left[
w_\theta(s\mid\tau)\nabla_\theta \log q_\theta(\tau)+\nabla_\theta w_\theta(s\mid\tau)
\right].
\]
这条式子是你最核心的“混合估计器”公式：第一项处理**离散**、第二项处理**连续**。问题在于，用户真正想要的是  
\[
\nabla_\theta \log P_\theta(s)=\frac{\nabla_\theta P_\theta(s)}{P_\theta(s)},
\]
而不是某条采样轨道的 pathwise 导数。**如果只对一条被采样轨道微分，而不补上 `\nabla \log q_\theta(\tau)` 的 score 项，也不做条件化/加权，你拿到的通常只是 surrogate objective 的梯度，不是目标 likelihood 的梯度。** 这正是 Option A 的单点失败模式。这个困难与近期可微量子轨迹论文里“必须用 score-function 穿过离散 jump sampling”是同一类问题。citeturn13view0turn13view1

**prediction：** d5/d7 上最危险的统计失稳，不在“常见 syndrome”，而在**低概率 syndrome** 或“完整 patch 级别的稀有联合模式”。当 `P_θ(s)` 很小时，不论你是分别估计 `P` 和 `∇P` 再相除，还是用自归一化比值估计，分母都在放大 Monte Carlo 误差。按 delta-method 的直觉，这类误差会以接近 `1/P_θ(s)` 甚至更差的速度被放大。因此，在 d5/d7 阶段，**直接瞄准 full-syndrome `∇ log P` 不现实；更合理的是瞄准 composite block likelihood、prefix-conditioned likelihood，或者有限维 counterfactual Greeks。** Harper 的设定里，中间测量会把 MPS 中的非 Clifford 误差塌缩回 tableau，这会缩短相干历史并降低部分方差，但不消除上述 rare-event 问题。fileciteturn0file0 citeturn13view0

## 候选方法排序

下表给出我认为最相关、也最适合你当前 build order 的排序。表中的 “exactness” 一列按你要求显式标注 **exact / prediction / heuristic**。

| 方法 | exactness | 偏差 | 方差 | 缩放 | 实现成本 | 结论 |
|---|---|---:|---:|---:|---:|---|
| **Option A：纯态轨迹 carrier + 离散 score-function + 连续 pathwise/tangent + Rao–Blackwellization** | **exact**（无截断、全部 θ-依赖分支都入 score、且 `w` 精确收缩时）；有截断后降为 **heuristic/controlled-bias** | 低到中 | 中到高 | 最有希望扩到 d5/d7 | 高 | **首选研究主线** |
| **同一 carrier 上做 CRN 有限差分 / SPSA** | FD 为 **heuristic**；SPSA 常近似无偏但仍是噪声估计 | 中 | 中 | 很好 | 低到中 | **强基线与兜底 response object** |
| **小角度扰动展开 `θ≈10^{-3}`** | 局部一阶为 **exact**；截断/高阶忽略后为 **controlled-bias** | 中 | 低 | 极好 | 中 | **适合先产出本地 Greeks** |
| **Pauli baseline + coherent correction / influence function / quasiprobability 校正** | 某些 observable 可 **exact**，但对 likelihood 本身不直接 | 低到中 | 可能很高，受 channel robustness 控制 | 中 | 中 | **适合做对照，不宜做主 carrier** |
| **局部纯化 TN / LPDO** | 正性与 trace-norm 误差控制是 **exact** 优点 | 压缩后仍有偏差 | 低到中 | 比纯态轨迹更重 | 高 | **可做中期备选，不适合 MVP** |
| **确定性 MPDO/MPO + 激进压缩** | 满 bond 时对 mixed-state likelihood 最干净，属 **exact** | 压缩偏差难控；正性问题突出 | 低 | 当前看差 | 高 | **当前应降级** |
| **对 <=13q dense oracle 训练 surrogate / neural ratio / neural score** | 近似器本身只是 **prediction/heuristic** | 中 | 低 | 推理快，但外推差 | 中到高 | **只做辅助手段，不替代白盒** |
| **仅在 d3 做隐式微分/精确梯度，d7 只给 stop-gradient 特征** | d3 局部是 **exact**，d7 为 **heuristic** | 低 | 低 | 工程最稳 | 低到中 | **项目层面最稳妥的 fallback** |
| **d3 精确梯度 + d7 近似 response bands 的混合方案** | 综合上是 **prediction**，但最可落地 | 低到中 | 中 | 很好 | 中 | **我最推荐的项目策略** |

Harper 载体之所以成为首选，不是因为它已经证明了“可微推断”，而是因为它已经证明了“**可扩展的前向表征**”：Clifford bulk 放进 `C`，相干残差放进 MPS，并且过强截断会把逻辑误差率往下偏，这个“lower-bound”行为至少给了你一个可解释的偏差方向。相反，确定性 mixed-state 路线在 open-system 文献里长期受到 MPDO 正性检查 NP-hard、局部截断破坏正定性、以及 mixedness 直接把 bond 推高的限制；LPDO 通过 purification 保住正性与 trace-norm 误差控制，但资源增长依旧是它的核心代价。fileciteturn0file0 citeturn17view0turn13view2turn13view3

**prediction：** 若你的内部 Spike A 所见“framed MPDO 在真实 13q d3 子系统上已到 `χ≈162`”有代表性，那么确定性 MPDO/MPO 路线在你给出的单卡预算下应视为**暂时不可行**；即使 forward 勉强可跑，其反向图和压缩偏差校验也大概率不在“几小时而非几周”的窗口内。与之相比，纯态轨迹 carrier 把 mixedness 变成 sampling overhead，把 memory blow-up 改写为 variance problem；对于你这个项目，这是更好管理的失败模式。LPDO 可以保留为中期探索，因为它的正性和误差控制确实有理论吸引力，但不是当前最小可行路线。citeturn13view2turn13view3turn17view0

**exact：** 需要单独指出一个替代方向：quasiprobability 仿真在 coherent surface-code 仿真里可以给某些目标量的**无偏估计器**，其采样成本由 channel robustness 控制；但它更自然地服务于逻辑误差率等前向 observable，而不是你这里要的“窗口 white-box likelihood / composite likelihood 的梯度对象”。因此它适合作为校核基线，不适合作为主 inferential carrier。citeturn16view0turn16view1

## 最优候选的梯度构造

**exact：** 在无截断、固定 carrier 规则下，Option A 最好的数学形态不是“完全 pathwise”，而是**混合估计器**。把轨迹记为  
\[
\tau=(b_{1:T},m_{1:T},u_{1:T}),
\]
其中 `b_t` 是被采样的 Kraus/噪声分支，`m_t` 是被采样的中间测量结果，`u_t` 表示决定连续态演化的其余信息。轨迹分布写成  
\[
q_\theta(\tau)=\prod_t p_\theta(b_t\mid h_t)\prod_{t\in \mathcal M_{\rm samp}}\pi_\theta(m_t\mid h_t,b_t),
\]
而不被采样、而是被解析收缩的末端或局部 syndrome 权重写成 `w_\theta(s\mid\tau)`。则  
\[
\nabla_\theta P_\theta(s)
=\mathbb E_{q_\theta}\!\left[w_\theta A_\theta(\tau)+\dot w_\theta\right],
\quad
A_\theta(\tau)=\nabla_\theta\log q_\theta(\tau)
=\sum_t \nabla_\theta\log p_\theta(b_t\mid h_t)+\sum_{t\in \mathcal M_{\rm samp}}\nabla_\theta\log \pi_\theta(m_t\mid h_t,b_t).
\]
这条式子回答了你的问题一：**离散 Kraus / 测量分支用 likelihood-ratio，连续相干参数用 pathwise / tangent。** 近期可微量子轨迹工作也是用 score-function 穿过离散 jump sampling；而可微张量网络文献则表明，只要图结构固定，连续 contraction 与局部张量更新做 AD 没有根本障碍。citeturn13view0turn13view1turn12view0

**exact：** 连续相干门的 tangent propagation 可以写得很直接。若某一步在 Clifford frame 中的非 Clifford 更新是  
\[
|\psi_t\rangle = U_t(\theta)\,|\psi_{t-1}\rangle,
\]
则一阶切向量满足  
\[
|\dot\psi_t\rangle
=
\dot U_t(\theta)|\psi_{t-1}\rangle + U_t(\theta)|\dot\psi_{t-1}\rangle.
\]
若 `U_t(\theta)=e^{-i\theta G_t}`，则  
\[
\dot U_t(\theta)=-iG_tU_t(\theta).
\]
若在 stabilizer frame 里把 `U_t` 展开成共轭后的 Pauli 串之和  
\[
U_t(\theta)=\sum_a c_a(\theta)\,\widetilde P_a,
\]
则  
\[
\dot U_t(\theta)=\sum_a \dot c_a(\theta)\,\widetilde P_a.
\]
这意味你可以沿着**固定采样轨迹**同时推进 `|ψ_t⟩` 和 `| \dot ψ_t⟩`，最终通过同一套 contraction 得到 `\dot w_\theta`。用户问题里提到的 forward-mode/tangent propagation、adjoint/backprop through MPS contractions，本质上都落在这条框架之内。citeturn12view0turn13view4turn13view5

**exact：** 可实际实现的 mini-batch 估计器可写成  
\[
\widehat P_\theta(s)=\frac1N\sum_{i=1}^N w_i,\qquad
\widehat G_\theta(s)=\frac1N\sum_{i=1}^N \left(w_iA_i+\dot w_i\right),
\]
然后构造  
\[
\widehat g_\theta(s)=\frac{\widehat G_\theta(s)}{\max(\widehat P_\theta(s),\varepsilon)}.
\]
其中 `\widehat G` 在无截断、无近似时是 `\nabla_\theta P_\theta(s)` 的无偏估计；但 `\widehat g` 作为比值，在有限样本下通常**有偏但一致**。因此，若你执意要“无偏的 `∇ log P`”，就必须进一步采样条件分布 `q_\theta(\tau\mid s)` 或做等价的精确加权；这在 rare syndrome 下通常不现实。更务实的做法，是把白盒输出定义为“`∇P`、`∇ log P` 的一致估计、CRN 有限差分 Greeks、以及对应的不确定度/偏差带”，而不是执着于某个单一的无偏 `∇ log P`。citeturn13view0turn13view1

**heuristic：** 方差控制的优先级应是：先 Rao–Blackwellization，再共同随机数（CRN），再控制变量/基线，最后才考虑 Gumbel/relaxation 一类替代物。对你的问题，最关键的 Rao–Blackwell 化不是“美化离散采样”，而是**尽量不采样能解析收缩的那一部分测量**：例如不要把整个目标 syndrome 都变成 one-hot 指示函数，而应在轨迹 prefix 或局部 branch 条件下，把某个 block syndrome 的条件概率直接 contraction 出来。这比把离散测量硬塞进 straight-through 或 Gumbel-softmax 更接近真正的目标梯度。Rao–Blackwellization 确实被反复证明可以降低离散梯度估计的均方误差。citeturn13view8

**prediction：** 对你这个 AI-QEC twin，我不看好“直接估计稀有 full-syndrome `∇ log P`”；但我看好以下较弱对象：`block/composite log-likelihood` 的梯度、对少量物理参数的定向 Greeks、以及对 seam overlap / residual budgets 的响应。也就是说，**Option A 足以为 inference 和 GNN 提供“有用的梯度对象”，但未必足以支撑“全图真 likelihood 的端到端可微训练”。** fileciteturn0file1

## 截断与可微性的处理

**exact：** SVD 截断是 d5/d7 carrier 的第二个硬问题。Harper 的前向结果已经说明：在他们的 surface-code coherent crosstalk 实验里，Schmidt 值快速衰减，`χ_max=32` 就能给出收敛的逻辑错误率趋势；但若截断太激进，逻辑错误率会被系统性压低，因而结果更像 lower bound。这个结论对 forward observable 已成立；对 gradient，只会更敏感。可微张量网络文献也把“稳定地穿过 SVD / tensor decomposition 求导”明确列为关键技术难点；而近期关于 truncacted SVD 导数的专门技术报告，以及机器学习里关于 duplicated singular values 导致 SVD 反传不稳定的工作，都说明“硬 top-χ + 近简并奇异值”是已知雷区。fileciteturn0file0 citeturn12view0turn12view8turn15academia0

**exact：** “forward 看起来收敛”并**不**推出“gradient 也收敛”。最简单的反例思路是：某条被截断掉的 tail 方向对概率质量的贡献是 `O(ε)`，所以 forward observable 的差异很小；但若该方向的参数敏感度是 `O(1)`，甚至在近简并点附近被局部条件数放大，那么 `∇_θ` 的误差可以保持在 `O(1)` 量级。也就是说，**梯度截断偏差会先于 forward 偏差暴露**。这正是为什么你不能沿用 Harper 那种“只看逻辑错误率收敛”的判据。这里的验证指标必须把 gradient angle、relative norm error、以及 sign stability 单独拿出来。这个判断与 TDVP 文献对 fixed-rank tangent-space 投影的强调是同方向的：只要你把固定秩 MPS 视为流形，真正稳定的“反向规则”不是随手截掉奇异方向，而是对 tangent space 做受控投影。citeturn13view4turn13view5

**heuristic：** 我建议把 truncation policy 分成两个层次。前向生产路径使用**固定 canonical gauge + 固定 `χ_fwd` + 确定性 top-χ**，保证 carrier 是可重复和可审计的；而梯度/诊断路径额外维护一个**更宽的 `χ_back ≥ χ_fwd`** 或者使用**软谱滤波**，例如对奇异值乘以平滑权重 `g_\tau(\sigma)`，再把 `τ→0` 当作验证极限。这样做的目的不是追求数学上无偏，而是给你一个**可测的偏差–方差旋钮**。在此框架下，straight-through 截断只适合做非常早期的工程排雷，不适合当科学结果；stop-gradient on truncation 只适合做 ablation，不适合输出给 GNN 的物理响应；随机化 SVD 若要用，必须把随机性也纳入轨迹分布并做 seed-固定的 CRN 诊断，否则你会把截断噪声和物理响应混在一起。citeturn12view8turn15academia0turn6academia1

**prediction：** 若 spike 发现“forward NLL 与 `P(s)` 在 `χ=16` 或 `32` 已基本收敛，但 gradient 方向在相邻 `χ` 间仍频繁翻转”，就应立即判定：**当前 truncation 规则不适合作为可微白盒的科学接口**。这时最稳妥的退路不是继续逼 autograd，而是切换到 CRN 有限差分 / SPSA 生成 response object，因为这些方法至少把截断偏差留在 forward oracle 层，而不是再叠一层不透明的 backward 偏差。

## 验证与脉冲实验

这些 spike 应全部先在 `<=13q` dense oracle 上做，因为那是你唯一能同时拿到“真 forward + 真 autograd + 精确 finite difference”的地方。Harper 解决的是前向可扩展性，不是反向正确性；而最近可微量子轨迹与可微张量网络论文给出的教训都一致：**先把 estimator correctness 与 truncation bias 钉死，再谈大规模。** fileciteturn0file0 citeturn12view0turn13view0

| Spike | 测什么 | 通过门槛 | 不通过意味着什么 |
|---|---|---|---|
| **梯度正确性基准** | dense autograd vs 中心差分 vs Option A 混合估计器 | 已识别方向上，cosine similarity 中位数 `>0.95`，相对范数误差 `<10%` | 估计器或实现有系统错 |
| **离散分支必要性检查** | 去掉 score 项后的“伪 pathwise”梯度 vs 正确混合梯度 | 去掉 score 后若方向明显偏离 dense，则证明离散项不可省 | 不能再宣称“轨迹可微” |
| **Rao–Blackwell 化收益** | indicator 版 `w` vs 条件概率版 `w` 的方差 | 方差至少下降 `3×`，或同方差下样本数降到原来的 `1/3` | 不适合做 rare-syndrome 梯度 |
| **截断偏差曲线** | `χ = full, 32, 16, 8` 下 forward 与 gradient 同时对比 | forward `ΔNLL/sample < 1e-3` 且 gradient cosine `>0.98` 才能算“可用 χ” | 仅 forward 收敛不够 |
| **CRN FD / SPSA 基线** | 同 wall-clock 下比较 mixed estimator 与 CRN FD/SPSA 的 MSE | 若 CRN FD/SPSA 在多数方向更稳，就把它升为主 response method | Option A 仅保留为研究线 |
| **Fisher / Godambe 稳定性** | 独立 mini-batch、独立 seed 下已识别子空间主角度 | top-k eigenspace 主角度 `<10°` | 问题本身识别性差，不是梯度器差 |
| **教师覆盖率** | synthetic teacher recovery 的 90% 区间覆盖 | 覆盖率在 `80%–98%` 之间，null 方向显著更宽 | 不确定度标定失败 |
| **d5/d7 资源门** | 单 window 前向+response 的时间、显存、内存 | 单 window `<2` 分钟、显存 `<24 GB`、整体 pilot `overnight` 可跑完 | 需要降级目标 |

**heuristic：** 我推荐把 pass/fail 再量化为一个简单的“三灯系统”。绿灯代表：dense oracle 上 correctness 过关，`χ` 稳定，CRN FD 与混合估计器至少有一个在 wall-clock 内实用；黄灯代表：只有方向对、范数不稳，那就只导出 sign / rank / coarse Greeks；红灯代表：seed 与 `χ` 一改，梯度就翻符号，这时就彻底放弃“可微白盒”叙事，退到 stop-gradient 特征 + provenance bands。

## 面向 GNN 的最小可用响应对象

**结论：弱于“端到端可微”，但强于“只有点估计”。** 换言之，最小可行对象不是 `θ_hat` 一项，而是**带 provenance 的局部响应包**。这与 composite likelihood 的 Godambe 视角一致：当你没有完整 likelihood，真正该输出的是“估计值 + 识别性 + 近似曲率 + 响应方向 + 近似误差来源”。citeturn11academia1turn11academia3

```text
Response_w = {
  theta_hat_w,
  objective_spec_w,           # block/composite likelihood 的定义
  Sigma_or_Godambe_w,
  identified_mask_w,
  null_space_basis_w,
  fisher_rank_w,
  rho_BC_w,
  coherence_budget_w,         # 例如 PTA distance, unitarity, coherent weight
  residual_budget_w,          # >4-stabilizer, long-range bunching, seam residual
  score_or_sensitivity_w,     # 对指定观测/摘要量的 score
  Jacobian_or_Greeks_w,       # 按方向给出 d obs / d theta
  variance_band_w,
  bias_proxy_w,               # truncation / solver / FD step / oracle gap
  unavailable_direction_mask_w,
  provenance_w = {
    estimator_type,           # dense / LR+pathwise / CRN-FD / SPSA / surrogate
    n_traj,
    chi_fwd,
    chi_back,
    truncation_policy,
    seed_policy,
    validation_status
  }
}
```

**exact：** 必须尽量“准确定义”的部分有四类。第一，`objective_spec_w`，因为 GNN 需要知道白盒到底拟合了什么，不然不同窗口不可比。第二，`identified_mask_w`、`null_space_basis_w`、`fisher_rank_w`，因为这决定了哪些方向可以被物理解释，哪些方向只能留给黑盒吸收。第三，`provenance_w`，因为一旦 Jacobian 来自轨迹估计器或 FD，它的统计性质必须显式暴露。第四，在 d3 或任何 `<=13q` dense 可达窗口上，凡是能由密集 oracle 精确输出的局部响应，都应标成“exact-dense”。citeturn11academia1turn11academia3

**prediction：** 可以接受估计的部分，是 `rho_BC_w`、局部 score、Greeks、coherence / residual budgets。这里的关键不是追求“无偏到最后一位”，而是**把 bias proxy 与 variance band 同时输出**。例如对某一物理方向 `v`，你导出的不应只是 `v^T J_w`，而应是  
\[
(v^\top J_w,\ \widehat{\mathrm{Var}},\ \widehat{\mathrm{BiasProxy}},\ \text{validated?})
\]
这样 GNN 可以把白盒响应当成“带测量误差的物理传感器”，而不是把它误当成 oracle。

**heuristic：** 必须显式标注 unavailable 的方向有三类：一是 Fisher / Godambe 明确判成未识别的方向；二是 truncation 验证未过的方向；三是 rare-syndrome 下方差爆炸、在 wall-clock 内无法稳定估计的方向。对这些方向，最好的科学做法不是硬报一个数，而是报“不可用”。这会让 downstream GNN 更容易学会何时信任白盒、何时退回 purely statistical fusion。

## 红旗与建议阅读

**应立即降级或放弃“可微 carrier”叙事的红旗**很明确。第一，dense oracle 上 gradient sign 在不同 seed 或不同 `χ` 下频繁翻转。第二，forward NLL 看似收敛，但 gradient angle 长期不收敛。第三，加入 Rao–Blackwellization 以后，方差仍随 syndrome 罕见度急剧爆炸，导致实际 wall-clock 下 `∇ log P` 完全不可用。第四，CRN finite difference / SPSA 在相同预算下持续优于混合估计器，那就说明你的“可微化”并没有带来工程收益。第五，identified subspace 本身跨 batch 不稳定，这说明根本瓶颈在可识别性，不在 carrier。第六，d7 pilot 需要的 `χ`、轨迹数、或缓存状态超出“单夜可跑完”的门槛，此时就应接受“d7 只输出 stop-gradient 特征与 response bands”的项目现实。citeturn12view0turn13view0turn13view2turn17view0

建议优先检查的参考文献与关键词如下。Harper 2026 给出你要用的前向 carrier 直觉与 truncation 经验；Liao 等 2019 给出“固定图张量网络是可微程序”的系统框架；Haegeman 等 2014 给出把固定秩 MPS 演化写成 tangent-space projector 的思路；Werner 等 2014 与 Godinez-Ramirez 等 2024/2026 给出 LPDO 的正性与误差控制及其资源瓶颈；Heinrich 与 Magorsch 2026 说明 score-function 可以确实穿过量子轨迹的离散跳变；Hakkaku 等 2021 给出 coherent QEC 的无偏 quasiprobability 基线；Bravyi 等 2018 则提醒你：大码距处相干物理噪声往往会被逻辑层面有效 Pauli 化，因此白盒响应对象应聚焦**局部窗口与 seam 级别**，而不是幻想全图都保留高保真 coherent sensitivity。关于离散梯度降方差，可看 Rao–Blackwellized straight-through 文献；关于 simulated likelihood 不可得时的近似比率/score，可看 neural ratio / neural score estimation。fileciteturn0file0 citeturn12view0turn13view4turn13view2turn17view0turn13view0turn16view0turn16view2turn13view8turn20academia0turn12view7

**最终判断可压缩成一句话：**  
**Option A 可以做成“足够可微”的 inference 载体，但这个“足够”应定义为“能导出经 dense oracle 验证过的局部 response object”，而不是“能在 d7 全图上对真实 marginal likelihood 做稳定、低方差、硬截断下的端到端 autograd”。** 如果前述 spikes 过关，就继续；如果不过关，就不要把项目绑死在可微白盒上，而应转向“d3 精确梯度 + d7 provenance-tagged response bands + stop-gradient GNN fusion”的混合架构。