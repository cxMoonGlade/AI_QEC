# CF-WR —— 窗口化重建可行性判决(ADR 0008 C1 载体)

> **这一个文件就是 CF-WR 的入口。** build/分析子代理只需读本 README + `registration.md`
> (+ 需要时 `P2_derivation.md`),**不必碰 `metric_results.md` 的 M1–M4 历史**。
> 状态:**注册已冻结(2026-06-14),build 待启动。**

## 0. 一句话

精确 2×2 窗 + 有原则的粘合,能否把**精确全局噪声信道 Choi 态**重建出来;在 bunching 强度
R̂ 增长、2D 缝为线状时它在哪里崩——而 K1 的 ABSTAIN 墙,是**粘合规则选错(mean-field)还是基本极限**?
把 M4 的 PROVISIONAL 负结果路由成**出路(GO)**或**此关联类的 PROVISIONAL 天花板(NO-GO)**。无"白跑"分支。

## 1. 为什么是这个实验

- 真硬件 W1(反事实不可验)+ scale(精确 backend ≤15q,surface 装不下)双约束;Markov/bunching 被前沿抢占。
- 收敛到唯一未被占的位置:**有真值的受控验证 × 真数据 × 测 sim-to-real 缝**。
- CF-WR 是其第一块:在 ≤15q **有精确真值**处,判窗口化+粘合的可行性,**且把 K1 墙判成 artifact 还是基本极限**。

## 2. 规格速览(全文 → `registration.md`;冻结于 `docs/metric_results.md` `### CF-WR PRE-REGISTRATION`)

| 项 | 值 |
|---|---|
| **Teacher** | 12q 2D 最近邻格点 toy(3×4),逻辑距离≥2,**非 surface-忠实**(≤15q 装不下 d3=17q);捕捉 2D 缝几何 |
| **R̂ 旋钮** | **非unital 局部 CPTP** 沿 T-B 曲线(带符号 δ′=p10−p01,两侧);R̂∈{1,2,3,**5.3**,8,12}(5.3=硬件匹配核心) |
| **φ 旋钮(选)** | 独立相干边(R-EDGE),**不携 R̂** |
| **臂** | G0 mean-field · **G1 Petz(认证)** · G2 GNN-学习化-BP(锚 G1,(c)) |
| **co-primary** | D_Choi=½‖J−J_glue‖₁(bound `√(I_nats)`)**且** E_do=`knob_dler_error`;**τ_D=0.5√(I_nats)、τ_E=0.1\|ΔLER_true\|** |
| **sanity 闸** | S-markov(显式 ≤4q QMC)· S-impl(R̂=1≤1e-3)· S-trivial · S-monotone |
| **seed** | 20260614;**sim/teacher-only,零硬件/held-out/escrow** |

## 3. 预测结果(置信度;详见对话记录)

| 项 | 预测 | 置信 |
|---|---|---|
| sanity 闸 / P2.1 G0 slope-1 | 过 / 确认线性(K1 实测 0.973) | ~90–95% |
| P2.2 c<1(Petz 胜) | likely | ~75%;**c≤0.5 仅 ~40%** |
| 崩溃尾 R̂∈{8,12} | 两臂皆崩(定 ξ*) | ~90% |
| **头条 GO/NO-GO @ R̂≈5.3** | **~50/50,真不确定**(硬件点坐在不确定带) | —— |

最可能:**MIXED/有界**——重建到某 ξ*,Petz 小胜,崩溃在 R̂ 5–8。ξ* 在 5.3 之上=GO,之下=NO-GO(把 M4 钉成天花板)。

## 4. 报告纪律(防"好结果≠真能力")

- **原始数优先于门**:RESULTS 头条是**绝对 D_Choi(R̂)/ξ*/c**,GO/NO-GO 只是导出标签。
- **τ_D 是松上界的一半** ⇒ 过门 = 必要非充分;真质量看绝对 D_Choi 与 c。
- **有界声明钉死**:12q-GO 只证"粘合机械+误差律在可验处正确",**不证 d5/d7 载体 work**(toy 缺长边界+不可表征质量);GO 永不跨读到规模/硬件。

## 5. Build 计划(重活,待启动)

4 脚本各 **≥3 子代理 + reviewer,串行**,scripted-execution(断言+证据打印+spawn `__main__` guard)+ 65GB memguard,GPU-only 模型计算:
1. `outputs/cf_wr_teacher.py` —— 3×4 碎片 + 非unital T-B 噪声场 + δ′→R̂ 标定 + do() 靶点(断言 |ΔLER_true|≥5×地板)+ 精确 J(E)/ρ + sha256 冻结;
2. `outputs/cf_wr_windows.py` —— 2×2/2×3/条形窗切分 + 逐窗精确 Born-NLL 拟合(+ 选 A warm-start,bit-identical 闸);
3. `outputs/cf_wr_glue.py` —— G0 mean-field / G1 Petz / G2 GNN-BP(锚 G1);
4. `outputs/cf_wr_score.py` —— D_Choi / E_do / CMI / sanity 闸 / P1–P5 拟合。
跑 → `docs/cf_wr/RESULTS.md` + metric 审计 + rigor 审计。

## 6. 红线

sim/teacher-only(不碰硬件/held-out 05–09/escrow 15–19);白箱核心精确(G1 Petz),**G2/A 标 (c)、锚精确对象、绝不进 (a) 主干/前提**(ADR 0008);注册文本冻结(τ/c<1 as (b)/R̂网格/seed/teacher-sha256);理论先行(预测带 run 前冻结);完成即提交(不 push、无 co-author)。

## 7. 指针

- **本套**:[registration.md](registration.md)(全文设计)· [P2_derivation.md](P2_derivation.md)(P2 (a)-基础)· `RESULTS.md`(待产)。
- **of-record 桩 + 全局台账**:`docs/metric_results.md` `### CF-WR PRE-REGISTRATION`(桩)· `docs/METRICS.md`(D_Choi 行)。
- **上游**:`docs/adr/0008-scalable-carrier-feasibility-study.md`(C1 架构)· `docs/.reports/adr0008_panel/`(K1 seam ABSTAIN、T-B 定理、composed.py G0)· `metric_results.md` M3/M4(bunching R̂≈5.3、M4 负结果)。
