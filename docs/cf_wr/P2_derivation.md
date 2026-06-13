# CF-WR P2 (a)-basis —— 缝粘合 Choi-迹距离残差领头阶推导(G0 mean-field vs G1 Petz)

> 这是 `registration.md`(同目录)§5 P2 的 (a)-精确 / (b)-band 推导基础(reviewer-1 BLOCK-M2 要求:P2 不得断言,须有写下的推导)。
> 由 opus 理论代理推导(2026-06-14),对照本地 `composed.py`(G0 实现)、`D_package_derivations.md`(T-B 非unital 成员)、`metric_results.md` SEAM-TEST(实测 G0 指数 0.973)、Fawzi–Renner 1410.0664 / JRSWW(PMC4841654)。
> epistemic 图例:(a) 精确;(b) 推导得出的预测带;(c) 启发。每步标类,conjectural 处**加粗内联标注**。

## 0. Reviewer-2 binding corrections(覆盖正文相应处,2026-06-14)

正文是工作推导;下列 5 条为**绑定覆盖**,以此为准:

- **[B-1] `c<1` 是 (b),非 (a)。** §3.4/§4 的"`c_{G1}<c_{G0}` 严格不等式 (a)"**降级为 (b)**:`‖χ⁽¹⁾−Petz(χ⁽¹⁾)‖₁<‖χ⁽¹⁾‖₁` 一般不成立(迹范非 aligned-subtractive;旋转-Petz 可 over-rotate 使某分量更差;若 χ⁽¹⁾ 无 ρ_BC 支撑则 c=1)。无 `δ>0` 下界定理。⇒ **c<1 是 (b) 赌注,且与 GO 解耦(不作 GO 前提)**。c≥1=finding。
- **[B-5] bound 常数改 `√(I_nats)`。** 经 Fuchs–van de Graaf:`F²≥2^(−I_bits)=e^(−I_nats)`,`T²≤1−F²≤1−e^(−I_nats)≤I_nats` ⇒ **`D_Choi^{G1} ≤ √(I_nats)=√(ln2·I_bits)`**。正文/§3.1 的 `√(2ln2·I)` **多了 √2,作废**。τ_D 据此重算。
- **[B-2] 微扰坐标用带符号 asymmetry δ′=p10−p01(两侧)。** CMI 二次性的"一阶导消"仅当 λ=0 是**内点最小**;R−1 是单侧(R≥1,AM–GM),会落在端点。改用 δ′(两侧、I 在 δ′ 偶 ⇒ δ′=0 内点)⇒ I=O(δ′²) 严格。**且此 bound-标度不 gate 任何判据**(实际残差是测的),非 load-bearing。
- **[B-3] 2D:at-most-linear,非严格线性。** §5 (R-2D) 的"不交支撑 ⇒ ∝L"**对 2D 共角缝不成立**(相邻 2×2 窗共享角 qubit ⇒ 支撑相交 ⇒ 迹范 sub-additive)。改为 **单调 + O(L) 上界 (a),线性为 (b) 中心**。
- **[B-4] c_{G0} 细化。** `composed.py` 的 G0 经条件 reduction **捕获了 marginal-shift sector**,丢的只是**未捕获的连通部分**:`c_{G0}=½‖χ⁽¹⁾_未捕获连通‖₁ ≤ ½‖χ⁽¹⁾‖₁`。slope-1 不变;0.973<1 记作 band [0.90,1.10] 内 + O(λ²) admixture,非精确确认。

## 1. setup
- 对象 (a):J(E)=(I⊗E)|Ω⟩⟨Ω|;一条缝分 **A—B—C**(B=重叠/buffer);glue 只是 measured marginals {ρ_AB, ρ_BC} 的函数。
- 微扰参量 (a):λ = 跨缝关联振幅。registered 旋钮 = **非unital 局部 CPTP** 沿 T-B 曲线(r=1.27e-2,R=5 成员 (p01,p10)=(6.7039e-3,0.120296);**非unital(p01≠p10)是携关联者**;unital 对称点 R=1)。相干伴随 teacher U_φ=exp(−iφZ⊗Z) 同框,λ↦φ。
- 残差 (a):D_Choi^G(λ)=½‖ρ(λ)−glue_G(ρ_AB,ρ_BC)‖₁。
- 关联展开 (a):ρ(λ)=ρ⁽⁰⁾+λρ⁽¹⁾+λ²ρ⁽²⁾+…;marginals 同展开。
- **(S1, a) 关键输入**:非unital ⇒ 一阶项 ρ⁽¹⁾ 含**非零 O(λ) 的 A:C 连通(cumulant)关联** χ⁽¹⁾≠0。证:非unital 破坏 parity/twirl 对称,奇 sector 一阶不消。(对照:unital-diagonal 耦合 twirl 成 Z⊗Z dephasing,连通关联为偶,一阶消——T-A/unital pin。)

## 2. G0(mean-field/条件积)领头阶
- G0 实现 (a, `composed.py:25–68`):**同步条件积(mean-field)**,strip 约束在 product manifold,seam 作用为对 partner branch-平均 marginal 的条件 reduction。**连通 A:C 关联恒为 0(product 约束,全阶)**。
- 领头残差 (a 阶 / b 系数):G0 无法表示的就是连通部分 χ。χ(λ)=λχ⁽¹⁾+O(λ²),χ⁽¹⁾≠0(S1)。
  **D_Choi^{G0}(λ)=c_{G0}·λ+O(λ²),c_{G0}=½‖χ⁽¹⁾‖₁>0 —— 线性,slope 1。**
- 与 K1 实测一致 (a 事后):实测 sandwich 指数 **0.973**、k2ry 0.858 ≈ 1 —— 本推导预测 slope 1,并解释旧二次 ansatz 为何被证伪(它把丢掉的项误当 O(λ²) 自洽误差,漏了 product 约束丢的是**一阶**连通关联)。
- 例外 (C0, a):**unital-diagonal/twirled 耦合 ⇒ χ⁽¹⁾=0 ⇒ D_Choi^{G0}=O(λ²)(slope 2)**。即"order = 领头连通关联的 parity"。非unital + un-twirled 相干 ∈ O(λ) 类。
- mean-field 自洽误差 (a):O(λ²),subleading。

## 3. G1(Petz)领头阶 —— crux
- Petz 普适旋转映射 (a, JRSWW):R_{B→BC}(X_B)=∫dt β₀(t) ρ_BC^{(1+it)/2}(ρ_B^{−(1+it)/2}X_Bρ_B^{−(1−it)/2}⊗I_C)ρ_BC^{(1−it)/2},**只依赖 ρ_BC**。
- bound (B1, a;常数见 §0 [B-5]):D_Choi^{G1} ≤ √(I_nats)=√(ln2·I_bits)(Fuchs–van de Graaf;**非 √(2ln2·I),已作废**)。
- CMI 二阶 ⇒ bound 线性 (a):I(A:C|B)=κλ²+O(λ³)(非负+解析+Markov 点取 0 ⇒ 一阶导消 ⇒ 二次);故 √I∝λ,**bound 本身线性**,且**线性 upper bound 不能定 actual 残差是 λ 还是 λ²**。
- 一阶展开 (a):glue_{G1}(λ)=R⁽⁰⁾(ρ_AB⁽⁰⁾)+λ[R⁽⁰⁾(ρ_AB⁽¹⁾)+R⁽¹⁾(ρ_AB⁽⁰⁾)]+O(λ²);Markov 点 R⁽⁰⁾(ρ_AB⁽⁰⁾)=ρ⁽⁰⁾(精确恢复)。一阶残差 Δ⁽¹⁾=ρ⁽¹⁾−[…]。
  - marginal-shift 部分:Petz 复现 ρ_AB⁽¹⁾、ρ_BC⁽¹⁾ 两个 measured 移位 ⇒ **该 sector Δ⁽¹⁾=0**。
  - 连通部分 χ⁽¹⁾:**(P-cond, a iff)** Δ⁽¹⁾=0(Petz 消一阶 ⇒ O(λ²))**当且仅当** χ⁽¹⁾ 由 ρ_BC 承载(B 屏蔽);否则一阶残差幸存(O(λ),系数更小)。
- 非unital 情形 (a 结构 / b 系数):缝关联在 B–C 界面一轮内本地生成、经 ρ_AB/ρ_BC 传到 A ⇒ B-mediated。**但非unital 使 [ρ_BC,ρ_B⊗I_C]≠0,阻碍旋转-Petz 在一阶精确求逆**,故**一阶残差一般幸存**:
  **D_Choi^{G1}=c_{G1}·λ+O(λ²),0≤c_{G1}<c_{G0} 严格。**
- **§3.5 referee-proofing (a flag)**:干净 O(λ²) 须 χ⁽¹⁾ 恰好 Petz-可恢复(一阶严格 Markov),非unital 界面**不可证**。故**不注册 slope-difference(G0=1,G1=2)**,注册**系数比**。

## 4. FROZEN P2
- **P2.1 (a)**:D_Choi^{G0}=c_{G0}λ+O(λ²),slope **1**(band [0.90,1.10];实测 0.973 retro-确认)。unital/twirled ⇒ slope **2**。
- **P2.2 (b) registered discriminator**:D_Choi^{G1}=c_{G1}λ+O(λ²),**c≡c_{G1}/c_{G0}∈[0,1) 严格 (a),方向赌注 c ≤ 0.5 (b)**。c≥1 证伪(finding);c≈0(G1 slope 实测≈2)= **bonus** 确认更强 O(λ²) 子假设,不预设。within-run 比较(同 teacher/functional/grid,归一化抵消)⇒ c 比单独 slope 更稳。
- **P2.3 (a) pin**:unital 点(p01=p10)c_{G0},c_{G1} 一阶皆 →0,残差 O(λ²)。违反=build bug。

## 5. 2D seam-length L 标度(修正:线性 L,非 √L)
- **(R-2D, a 正交支撑)**:局部场 ⇒ L 个界面 cell 的 χ⁽¹⁾_ℓ 支撑不交 ⇒ 迹范可加 ⇒ **D_Choi∝L 线性**。
- **为何 L 非 √L (a)**:迹距离是算子直和的 L₁ 范,贡献按**幅度**相加(非 quadrature);√L 是**涨落/方差**律,不适用 L₁ Choi 残差。(度量依赖:若测 fidelity 或涨落 functional 的标准误,√L 才回来。)
- **沿缝关联情形 (b)**:仍 ∝L,系数吸收 ξ。
- **P2.4 (b)**:per-seam Choi 残差**单调增、渐近线性于 L**(指数 band [0.85,1.15],**非** [0.4,0.6])。诚实 caveat:精确-DM oracle 只够 L∈{1,2,3},**仅 sign+monotone 可测**,L-指数 direction-only(指数 miss=finding,不证伪 sign/monotone)。**c(P2.2)对 L 一阶无关 ⇒ c<1 是稳健 2D-可迁移判据**,绝对残差的 L 律仅 direction-only。

## 6. 一个 referee flag
"CMI 在 λ 二阶"(§3.2)Fawzi–Renner/JRSWW **未明述**,本推导由 非负+解析+Markov 点取零 严格导出 —— 注册须作 **derived corollary** 引用,非papers 原话。

## 源
Fawzi–Renner CMP 340(2015), [1410.0664](https://arxiv.org/abs/1410.0664);Sutter–Fawzi–Renner Proc.R.Soc.A 472(2016), [PMC4841654](https://pmc.ncbi.nlm.nih.gov/articles/PMC4841654/);本地 `composed.py`、`D_package_derivations.md` §D5、`T1_requirements.md`、`metric_results.md` SEAM-TEST(实测 0.973/0.858、证伪二次、φ² 跨窗质量 ×8.7/×3)。
