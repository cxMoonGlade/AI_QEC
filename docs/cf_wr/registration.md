# CF-WR 预注册草案 v2 —— 12q Teacher 窗口化重建可行性判决

> 状态:**FROZEN 2026-06-14**(3 轮对抗 review 通过:R1/R2 BLOCK→修、R3 MINOR→修;of-record 桩在 `docs/metric_results.md`)。
> **Pre-run Amendment 1(2026-06-14,build scout 发现 G1):** D_Choi 改 **per-seam reduced-block Choi 迹距离** —— 全 2²⁴ 信道 Choi 不可行,改每缝 ≤6q 支撑的 reduced-channel Choi 块(≤2¹² dim,feasible);**全局 2²⁴ 不材料化**,全局=缝聚合(=P4 L-标度);GO 门用 R̂≈5.3 处 per-seam 值对 per-seam √(I_nats) bound。**G2(无 2D 衬底):直接 build**(3×4 几何/2D detector map/线缝 glue/2D decoder 全新建,先建冻结 `cf_wr_geom` 契约)。
> owner 三决定(2026-06-14):**(i) 直接 P2(2D 碎片)**;**(ii) D_Choi + E_do co-primary**;**(iii) G2(GNN-BP)纳入**。
> v2 关键修正(reviewer-1):**①R̂ 旋钮改非unital CPTP(unital coherent ZZ 被 T-B 定理钉在 R=1,产不出 R̂>1)②P2 改系数比判据(Petz 残差是线性,非二次;K1 已证伪二次)③补量子 Markov 链精确恢复闸(替被砍的 1D Petz 正确性校准)④τ_D 重钉到 bound 之下 ⑤D_Choi 入 METRICS 台账 ⑥P4 弱化为符号+单调,移出 GO 门**。
> 理论先行:§5 预测带在任何 run 前冻结;miss = finding,不事后加宽容差。

---

## 0. 对象与问题(一句话)

**精确局部窗(2×2)+ 有原则的粘合(Petz/BP),能否把精确全局噪声信道对象重建出来;在 bunching 强度 R̂(=非unital 关联)增长、2D 缝为线状时它在哪里崩——而 K1 的 ABSTAIN 墙,是粘合规则选错(mean-field)还是基本极限?**

- **判决对象(信息侧)**:噪声信道场 E 的 **Choi 态** J(E)。
- **能力侧对象**:经**冻结解码器**的 **do()-ΔLER**(沙盒内可验,§6 W1 注记)。
- ADR 0008 **C1 载体可行性判决**:M4 的 PROVISIONAL 负结果 → **出路(GO)** 或 **此-teacher 关联类的 PROVISIONAL 天花板(NO-GO)**。无"白跑"分支。

---

## 1. Teacher(直接 P2:2D,全精确,≤15q)

### 几何(m8 修正:诚实重标)
**没有任何 ≤15q 的精确-backend teacher 能是"完整 surface code"**——连 d3 旋转 surface 都是 17q > 15q 墙(数据集 note 已证)。故 teacher **重标为**:

> **12q 二维最近邻格点 toy(3×4),带一条已定义逻辑串 + 完整 stabilizer 子集**——目的不是 surface-忠实,而是**复刻 surface 窗口化真正难的那部分:2D 连接性 + 线状缝 + O(L) boundary 惩罚**。

冻结前在**注册文本里**钉死(非仅 code+hash):显式 stabilizer 清单、`OBSERVABLE_INCLUDE` 支撑、**断言逻辑距离 ≥2 且所有 check 完整(无悬挂半-plaquette)**——否则 LER/E_do 无定义。精确布局在 `cf_wr_teacher.py` 钉定 + sha256,且哈希 inline 进注册块(m11)。

### 噪声场(M1 修正:R̂ 旋钮换非unital CPTP)
全精确密度矩阵模拟,持有完整 J(E) 真值:
1. **局部边际** —— 逐 qubit 单比特 CPTP,r̂ ≈ 0.013, q̂_eff ≈ 0.014(N2 plan 已签);
2. **R̂ 旋钮(主)= 非unital 局部 CPTP 场**,沿**注册的 T-B 曲线**用 {p01,p10} 参数化(`D_package_derivations.md`:r≈0.013 处 R∈{2,5,17} 的 Kraus 成员已预算,R=5⇒(6.7039e-3, 1.20296e-1),上限 R≤1/(2r̂)≈39.4 覆盖全网格)。**绝不用 unital coherent ZZ**(T-B 定理:unital-diagonal iid 钉在 R=1,产不出 bunching)。非unital CPTP 非 Pauli ⇒ stim 做不了 ⇒ **仍需精确密度矩阵 backend**(实验存在理由保住)。
3. **可选相干边旋钮 φ(R-EDGE slot)** —— 独立于 R̂,**显式不携带 R̂**;仅用于测"相干修正的粘合"(载体的 coherent-correction 槽)。默认关;开时单独扫、单独报。

> v2 澄清:**bunching(R̂,非unital)与 coherence(φ,非 Pauli)是两根独立轴**。M4 关心的是 bunching 传导,故主判据走 R̂;φ 是次要的相干-槽探针。

---

## 2. 旋钮与强制控制

- **扫 R̂ ∈ {1, 2, 3, 5.3, 8, 12}**(经 {p01,p10} 沿 T-B 曲线实现;**用带符号的 asymmetry δ′=p10−p01 作微扰坐标**,两侧、δ′=0 为内点 —— 见推导 §3.2):**R̂=5.3 = 硬件匹配点(M3 P11),判决核心**;{8,12} 测崩溃尾;{2,3} 测单调方向。
- **do() 靶点 + eval context 钉死(C-1,为 τ_E 可复现)**:`do()` = 单边错误率 ×k(k、目标边、eval context 在 `cf_wr_teacher.py` 钉定 + inline);ΔLER_true 由冻结 teacher 算出 → τ_E 绝对数冻结时 inline。**实质性断言(防 E_do 退化成测噪声)**:所选 do() 必须满足 **|ΔLER_true| ≥ 5×地板**(否则 τ_E=0.1×|ΔLER_true| 退化);冻结前在 teacher 上验证此下限,不达标则换 do() 靶点(在所有臂运行前)。
- **R̂=1 强制零控制 = unital 点**(p01=p10),与 P2.3 同一 context:D(R=1)=g(r)+g(q)≈−7.43e-4 是**边际项地板,非缝残差**(C-2);G1 重建误差必须 ≤ 地板(§4 S-impl)。显著超出边际地板 ⇒ 污染 ⇒ 作废重查,不进判决。
- **seed = 20260614**。

---

## 3. 粘合臂

| 臂 | 规则 | epistemic | 角色 |
|---|---|---|---|
| **G0** | mean-field/乘积粘合(= K1 `composed.py` 用法) | (c) | 零阶规则——被疑为 K1 artifact |
| **G1** | **Petz 恢复映射**(JRSWW twirled 普适式,只依赖 ρ_BC),2D 边界-MPS 收缩 | (a) 构造 + (b) 误差界 | **理论最优,认证结果** |
| **G2** | **GNN 学习化 BP**:detector graph message-passing,**初始化在 G1**、Markov-CMI 正则、**以 G1 为界**,只在与 G1 一致处采信 | (c) | 测"学习化 BP 能否同代价扛更多关联";不动 G1 认证地位 |

**白箱核心 = 逐窗精确 Born-NLL 拟合(LBFGS,≤4q 窗精确)+ G1 Petz 粘合。**
**A(可选 warm-start)**:给逐窗 LBFGS 提初值;**(a) 闸(m7):逐窗拟合须 {cold init, A warm-start} 跨初值 bit-identical(≤地板),否则 A 悄移"精确"拟合,作废 A**。
G2、A 全程标 (c),锚精确对象,绝不进 (a) 主干/前提(ADR 0008:学习型代理无 exactness class)。

---

## 4. 度量(M4+M5 修正)

### 入台账(M5,已做)
- **D_Choi = per-seam reduced-block Choi–Jamiołkowski 迹距离**(amendment 1):**已增行** `docs/METRICS.md` Ledger(J_s=(I⊗E_s)|Ω⟩⟨Ω| 在每缝 ≤6q 支撑、Choi 块 ≤2¹² dim feasible、半迹范 ∈[0,1]、per-seam bound `√(I_nats)=√(ln2·I_bits)`);**全局 2²⁴ 信道 Choi 不材料化**,全局=缝聚合;
- **E_do 不新造度量**:映射到**已在台账**的 `knob_dler_error = |ΔLER_twin−ΔLER_teacher|`(绝对 LER 单位,counterfactual-validity error)——这正是载体 do()-保真对照 teacher 真值的场标准度量;相对-% 仅作**flagged project-defined 次要描述**。

### Co-primary(owner ii;M4:声明各自独立失败模 + 去 headline-S + τ_D 重钉)
| 度量 | 对象 | 唯一捕捉的失败模 | 阈值(c) |
|---|---|---|---|
| **D_Choi** = ½‖J_s−J_glue,s‖₁(**per-seam reduced block**,amendment 1) | reduced 信道 Choi 块(≤6q 支撑,≤2¹² dim) | **全信道重建误差,含解码器看不见的方向**(逐缝) | τ_D = **0.5 × √(I_nats)**(per-seam bound;**钉在 bound 之下** ⇒ 过 τ_D 蕴含 bound 成立);GO 用 R̂≈5.3 处 per-seam 值 |
| **E_do** = `knob_dler_error` = \|ΔLER_glue(do)−ΔLER_true(do)\|(绝对 LER 单位,台账度量) | do()-ΔLER | **决策相关投影 = M4 传导 gap**(解码器对哪些 Choi 方向不敏感) | τ_E = **绝对常数,= 0.1×\|ΔLER_true\|** 其中 ΔLER_true 由**冻结 teacher**(evaluator-侧,§2 钉死 do() 靶点+eval context)算出,**冻结时 inline 成一个绝对数**(C-1:非 glue-run 数据,故可复现、非移动靶) |

- **为何两者都要(非冗余)**:E_do 是 J_glue 经 frozen 解码器的 pushforward,一般是 D_Choi 的函数;**唯在解码器对"粘合污染的特定 Choi 方向"不敏感处二者解耦**——这正是 **M4 的教训**(Choi/NLL 赢但 MWPM 独立边 DEM 看不见)。M4 是二者解耦的经验证据。
- **GO = 两者各自独立达标(AND 门)**;**取消加权 headline S**(AND 门已是决策规则;跨不可通约单位求平均无决策作用且招"伪平权"批评)。

### 次要(报告,不进 GO 门)
I_bits(A:C\|B)=S(AB)+S(BC)−S(B)−S(ABC)(von Neumann,bit)——order parameter,精确;LER 绝对误差;syndrome KL/TV(对照 spacetime Markov length)。

### Sanity 闸(M3 修正:补量子 Markov 链精确恢复闸)
被砍的 1D 的"Petz 正确性"角色,旧两闸**在 Petz 机制上退化**(λ=0 时 Petz 退化为恒等、从不动用恢复旋转;全窗时无缝可粘)——bug 在二者皆隐形却腐蚀 2D 判决。补:
- **S-markov(新,核心;C-4:显式构造已钉)**:一个**显式 ≤4q 量子 Markov 链点**,在 `cf_wr_teacher.py` 钉定,满足三断言:**(1) I(A:C\|B)=0 到地板**(Petz 定理 ⇒ G1 精确 D_Choi≤地板);**(2) D_Choi^{G0} ≥ 10×地板**(G0 product 必不精确 ⇒ 闸非空、不会放过 no-op Petz);**(3) ρ_BC 与 ρ_B⊗I_C 不对易**(动用量子旋转 ⇒ 抓得住 transposed/错序 Petz 实现 bug)。
  - **worked baseline 实例(证 (1)+(2))**:3q 经典-Markov 混合 ρ_ABC=½(|000⟩⟨000|+|111⟩⟨111|)(A,B,C 序):给 B=b 则 A=C=b 确定 ⇒ I(A:C\|B)=0;但 ρ_AC=½(|00⟩⟨00|+|11⟩⟨11|)≠ρ_A⊗ρ_C ⇒ ρ_AC−ρ_A⊗ρ_C=diag(¼,−¼,−¼,¼)、迹范=1 ⇒ **D_Choi^{G0}=½‖·‖₁=½>0**(≥10×地板 ✓)。Petz 从 ρ_AB,ρ_BC 精确重建。
  - **non-commuting 伴随(满足 (3),抓旋转 bug)**:在 A、C 上各施一固定共轭基局部幺正,使 ρ_BC 非对角 ⇒ 旋转-Petz 的 [·]^{(1±it)/2} 被真正动用。
  **被砍 1D 的最小替代;冻结前必过三断言**。
- **S-impl**:G1@R̂=1 的 D_Choi ≤ 1e-3(实现+零控制双用);
- **S-trivial**:窗=全碎片 ⇒ D_Choi ≤ 地板(recover+score 恒等);
- **S-monotone**:D_Choi 随 R̂ 单调非降。

---

## 5. 理论先行预测带(跑前冻结,(b),miss=finding)

- **P1**:G1 亚阈 D_Choi ∝ exp(−w/2ξ(R̂));拟 ξ(R̂) 确认对数线性 collapse。
- **P2(核心赌注,M2 修正:系数比,非斜率;(a)-基础推导已完成 → `docs/cf_wr/P2_derivation.md`)**:
  - **P2.1 (a)**:`D_Choi^{G0} = c_{G0}·λ + O(λ²)`,**slope 1**(band [0.90,1.10];K1 实测 0.973 retro-确认)。**定理化**:G0 product 约束丢的是**一阶连通关联** χ⁽¹⁾(非unital ⇒ χ⁽¹⁾≠0),c_{G0}=½‖χ⁽¹⁾‖₁。unital/twirled 点 ⇒ slope 2(parity)。
  - **P2.2 (b) 独立结论(非 GO 前提)= 系数比**:`D_Choi^{G1}=c_{G1}·λ+O(λ²)`,赌注 **c≡c_{G1}/c_{G0} < 1(方向 c ≤ 0.5)**。**全 (b)**:B-1 裁定 `c<1` **不是 (a)-定理**——`‖χ−Petz(χ)‖₁<‖χ‖₁` 一般不成立(迹范非 aligned-subtractive;旋转-Petz 可 over-rotate;若 χ⁽¹⁾ 无 ρ_BC 支撑则 c=1)。**c≥1 = finding(Petz 不胜),c<1 = 支持 artifact 叙事,c≈0(G1 slope≈2)= bonus**。**与 GO 解耦**(§6):GO 不以 c<1 为前提。within-run 比较 ⇒ c 比单独 slope 稳健。**取消 v1 的"G1 斜率≥1.8"**(Petz O(λ²) 对非unital 界面不可证)。
  - **P2.3 (a) pin**:unital 点(p01=p10)c_{G0},c_{G1} 一阶皆→0,残差 O(λ²)。违反=build bug。
- **P3**:阈值 ξ(R̂*)/w = 1 ± 0.3;越过两臂皆崩。
- **P4(2D,B-3 修正:at-most-linear,非严格线性、非 √L)**:G1 每缝 D_Choi 随 seam-length L **单调非降 + sub-additive 上界 O(L) (a)**;**线性为 (b) 中心**(指数 band [0.85,1.15])。**推导**:相邻 2×2 窗的缝 cell **共享角 qubit ⇒ 支撑相交 ⇒ 迹范 sub-additive**(`‖ΣAℓ‖₁≤Σ‖Aℓ‖₁`),故只能 ≤c·L 上界,不能断言 ∝L(角贡献或部分抵消 ⇒ 可 sub-linear);**√L 是涨落律,不适用 L₁ Choi 残差**。诚实 caveat:精确-DM oracle 只够 L∈{1,2,3},**仅 sign+monotone 可测**,L-指数 direction-only。**P4 不在 §6 GO 门**。**c(P2.2)对 L 一阶无关 ⇒ c<1 是稳健的 2D-可迁移结论**;绝对残差 L 律仅 direction-only。
- **P5(G2)**:R̂≤5.3 时 \|D_Choi^{G2}−D_Choi^{G1}\| ≤ τ_agree;R̂≥8 可能延 reach(探索,非赌注)。
- **零控制**:G1@R̂=1 ≤ 地板(=S-impl)。

---

## 6. GO / NO-GO(M4+m9+m10 修正)

**W1 注记(airtight)**:E_do 在**沙盒(teacher)内可验**——teacher 有可重跑真值,反事实可实现;它验**载体 do()-保真对照 teacher 真值**,**非**硬件 do() 主张(硬件 W1 阻断)。**本注册的任何数字、带、路由,一律不跨读到硬件**(对齐 K1 results 的 claim-scope 段)。

| 判决 | 条件(R̂≈5.3,G1) | 含义 |
|---|---|---|
| **GO(载体可行)** | D_Choi ≤ τ_D **且** E_do ≤ τ_E(R̂≈5.3,G1) —— **纯绝对重建质量,不含 c<1**(B-1:c<1 是 (b) 结果,非 (a) 前提,不进 GO 门) | **载体在硬件匹配关联处对着真值重建成功** ⇒ ADR 0008 C1 上马;dMLE-TN bulk + 窗精确 CPTP 缝槽路通。**若同时 P2.2 测得 c<1**(独立 (b) 结论)⇒ 进一步支持"M4 失败 = mean-field/独立边格式 artifact、K1 该用 Petz 重测";c<1 与 GO 解耦,各自报 |
| **NO-GO(此-teacher 关联类的 PROVISIONAL 天花板)** | 即便 G1 Petz,R̂≈5.3 仍 D_Choi/E_do 超阈 | 窗口化救不了此关联类 ⇒ 须换可扩展表示(Tsim/LPDO)或接受格式天花板。**但**:**NO-GO 不是定理级**(M1 的 teacher 关联类有限、Petz-bug 风险须先经 S-markov 排除)——**它不抵 K1 二读、不把 M4 升成定理,只是又一个 (b)/(c) 级数据点** |
| **MIXED** | Choi 与 do() 判据分歧 / 通过但崩溃尾过早 | 报 ξ* 与 boundary-penalty 标度,路由到"窗口化在 ξ<ξ* 有界可行" |

**GO/NO-GO 默认 PROVISIONAL**,除非升级定理级;不在其上建定义/设计。

**报告纪律(防"好结果≠真能力",owner 2026-06-14):**
- **原始数优先于门**:RESULTS 必须把 **绝对 D_Choi(R̂) 曲线、ξ*、c 的原始值**放最前;**GO/NO-GO 只是导出标签,不是头条数字**。
- **τ_D 是松上界的一半**:√(I_nats) 是 upper bound、本身松,故"D_Choi ≤ τ_D"是**必要非充分**;报告须明说"过门"不等于"重建好",真正的质量看绝对 D_Choi 与 c。
- **GO 的有界含义钉死**:12q toy 的 GO **只证"粘合机械+误差律在可验处正确"**,**不证 d5/d7 载体 work**(toy 缺长边界 O(L) 惩罚 + 缺真硬件的不可表征质量/model-class 失配);每个 GO 结论须带这句有界声明,不得跨读到规模或硬件。

---

## 7. 可行性 / 成本

12q 密度矩阵 2¹²×2¹² ~16.8M 复元;CMI/Petz 在 ≤4q 边际上是小线代 ⇒ **分钟级**;**纯 sim/teacher 侧,零真硬件、零 held-out(05–09)、零 escrow(15–19)触碰,exactness 全程保持**;GPU 跑精确演化+Choi(GPU-only 模型计算);65GB memguard;scripted-execution。

---

## 8. 冻结 / 搭建序列(理论先行)

1. **本 v2 → reviewer-2 pass**(只读;重审:T-B 旋钮参数化忠实性、Petz 残差领头阶推导是否写入、S-markov 闸的精确性、τ_D 是否真在 bound 之下、12q toy 的逻辑距离≥2、所有冻结常数 inline);
2. **两件 (a) 基础已补**:(α) Petz 残差领头阶推导 = `docs/cf_wr/P2_derivation.md`(✓);(β) METRICS.md Choi-迹距离行已增 + E_do 映射到台账 `knob_dler_error`(✓);
3. 折入 `docs/metric_results.md` 作 `### CF-WR PRE-REGISTRATION`(冻结,inline 全部 τ/比带/R̂网格/seed/teacher-sha256);
4. **4 脚本各 ≥3 子代理 + reviewer,串行**:`cf_wr_{teacher,windows,glue,score}.py`(断言+证据打印+刷新+spawn `__main__` guard);
5. 跑(seed 20260614,sim-only)→ `### CF-WR RESULTS` + metric 审计 + rigor 审计((a)/(b)/(c) 全标、theorem-backed vs PROVISIONAL)。

---

## 9. 红线(违反任一即事故)

- **sim/teacher-only**:不碰真硬件、held-out 05–09、escrow 15–19;
- **exactness 保持**:白箱核心=精确 Born-NLL + G1 Petz;G2/A 标 (c),锚精确对象,绝不进 (a) 主干/前提/推导基础;
- **注册文本冻结**:τ_D=0.5×√CMI-bound、τ_E=10%、P2 系数比 c<1、R̂网格、seed、teacher 哈希全 inline 钉死;miss=finding,不事后加宽容差;
- **R̂ 旋钮 = 非unital T-B CPTP**(绝不 unital coherent ZZ);**φ 相干旋钮独立、不携 R̂**;
- **结论纪律**:GO/NO-GO 默认 PROVISIONAL;NO-GO 非定理级;
- **理论先行**:§5 预测带 + Petz 领头阶推导在 run 前冻结;
- **scripted-execution + 65GB memguard + GPU-only 模型计算**;
- git:完成即提交(不 push、无 co-author)。
