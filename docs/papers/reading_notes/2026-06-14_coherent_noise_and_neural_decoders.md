# 综述 / Overview hub（双语 CN/EN）— 相干噪声 × 神经解码器：四篇外部论文 vs `qec_twin`
# Overview hub (bilingual CN/EN) — Coherent noise × neural decoders: four external papers vs `qec_twin`

> **结构 / Structure**：本篇是**综述枢纽**——双语地图 + 跨论文综合 + 引用建议；四篇的**逐篇深度笔记**已拆成独立英文 peer-review note（见下表链接），与现有语料对齐。
> This is the **overview hub** — bilingual map + cross-paper synthesis + citation guidance; the **per-paper deep notes** are split into standalone English peer-review notes (links below), aligned with the corpus.
>
> 日期 / Date 2026-06-14 · 证据 / evidence：4 个并行子代理 digest + 论文 1 摘要经 WebFetch 直接核对 / four sub-agent digests + paper-1 abstract verified directly.
> **可信度 / Confidence**：论文 1（Harper 2605.29514）**原文全文已读 2026-06-15 / paper-1 full-text read**（method/numbers verified, `harper_..._2605.29514.md`）；论文 2/3/4 具体数字=一手 *digest*（进 registration/paper 前回查 PDF）；我们自己的数字（M3/M4/R̂）来自 `../../metric_results.md`。**二手 digest 层，不得作为任何 (a)/(b) 条目的依据 / secondary-digest tier, never a basis for any (a)/(b) item.**

## 各篇深度笔记 / Per-paper deep notes
| # | Note | 一句话 / One line |
|---|---|---|
| 1 | [harper_nonclifford_crosstalk_surface_2605.29514](harper_nonclifford_crosstalk_surface_2605.29514.md) | hybrid **stabilizer–TN** 仿真**相干** crosstalk：抬 LER、压 threshold、空间分布 matters / coherent crosstalk sim — raises LER, lowers threshold, distribution matters **【原文全文已读 2026-06-15 / full-text read】** |
| 2 | [darmawan_decoder_adaptation_local_noise_2403.08706](darmawan_decoder_adaptation_local_noise_2403.08706.md) | PRA：**selective mischaracterization**，**少数关键参数**主导；Pauli-adapted **仅**非关联/小相干时近最优 / few critical params; Pauli-adapted near-optimal only uncorrelated |
| 3 | [sparse_mamba_decoder_2605.17156](sparse_mamba_decoder_2605.17156.md) | **Sparse Mamba** O(k) 解码器，Sycamore 上压 MWPM、延迟暴降 / sparse-defect Mamba, big latency win |
| 4 | [scalable_neural_decoder_realtime_2510.22724](scalable_neural_decoder_realtime_2510.22724.md) | **Mamba O(d²)** 替 Transformer O(d⁴)，计入延迟噪声后 threshold 反超 / O(d²) beats Transformer once latency counted |

## 0. 速览地图 / Map（两簇 + 我们卡在缝里 / two clusters, our wedge in the gap）

```
簇 A / Cluster A：相干/关联噪声"有后果"            簇 B / Cluster B：静态 Pauli-DEM 上的高效神经解码器
  coherent/correlated noise has consequence          efficient neural decoders on a static Pauli DEM
  论文1 (仿真 crosstalk → 抬 LER)                      论文3 (Sparse Mamba, Sycamore)
  论文2 (解码器对噪声的适配上限)                       论文4 (Mamba O(d²), 实时 / real-time)
        \                                                   /
         \   我们的 wedge 正好在缝里 / our wedge in the gap /
          从真实 syndrome 学一个"能承载相干"的结构化噪声对象
          learn a coherent-capable structured noise object from real syndromes
          (M3 NLL 胜 / win) + 诚实解码代价 (M4 −40%) + 漂移预测 (未建, 头条 / unbuilt headline) + honest bands
```

- 簇 A / Cluster A：**相干/关联噪声有 QEC 级后果**，Pauli-adapted 解码器**只在"非关联+小相干"时近最优** / coherent & correlated noise has QEC-level consequence; Pauli-adapted decoders near-optimal **only** for uncorrelated + small coherence.
- 簇 B / Cluster B：在**同一个 Sycamore 数据族**上，神经 Mamba 是"匹配 SOTA 精度 + 高效"的前沿——但**全部**把 XEB→DEM→Stim 的 **independent-edges DEM 当 oracle**，**全部静态、全部 Pauli**，**没人碰相干、没人碰漂移** / same Sycamore family, efficient SOTA-matching frontier — all treat the independent-edges DEM as oracle, all static, all Pauli, none touch coherence or drift.
- 我们 / Us（plan3 tool-first）：不是再造解码器，而是**质疑/校准噪声模型本身**（coherent-capable CPTP window field）+ 把**漂移预测**做头条 / not another decoder — we calibrate/question the noise model itself + make drift prediction the headline.

## 5. 跨论文综合 / Cross-paper synthesis：拼到我们现在的方向 / mapping to our direction

**(a) 我们的 wedge 在两簇缝隙里，且这缝是真空的 / our wedge is in the vacant gap between the clusters.**
- **CN**：簇 A（1+2）说相干/关联噪声**有后果**、Pauli 解码器**只在非关联/小相干时近最优**。我们在真硬件上把缝量了出来——M4：经 independent-edges DEM 解码差 ~40%（PROVISIONAL，结构主导待 N1/N2）；M3：twin 抓住 DEM 抓不住的 likelihood（+56/+44 nats）；P10：pij+marginals 被 independent edges **联合不可实现**（(a)-grade，366–1116σ）。Darmawan 的 selective-mischaracterization + "少数关键参数"给我们排 DOF、搭 M3↔M4 桥。簇 B（3+4）是解码精度前沿（恰恰**没暴露我们 NLL 胜**），且**全静态、全 Pauli、不碰漂移**。
- **EN**：Cluster A (1+2) says coherent/correlated noise **has consequence** and Pauli decoders are **near-optimal only for uncorrelated/small coherence**. We measured the gap on real hardware — M4: ~40% worse through the independent-edges DEM (PROVISIONAL, structural-dominance pending N1/N2); M3: the twin captures the likelihood the DEM cannot (+56/+44 nats); P10: pij+marginals **jointly unrealizable** by independent edges ((a)-grade, 366–1116σ). Darmawan's selective-mischaracterization + "few critical parameters" rank DOFs and bridge M3↔M4. Cluster B (3+4) is the decoder-accuracy frontier (which **does not surface our NLL win**) and is **all static, all Pauli, no drift**.

**(b) 我们的差异化轴：likelihood/coherent-slot + 漂移 / our differentiation axes.**
- **CN**：对簇 B 出**校准质量（NLL）+ 相干槽**的结果，而非又一个解码精度数字（更不易被 scoop，`../../plan3.md`）。漂移：四篇**无一**碰 temporal prediction → 与 2026-06-13 battlefield 裁决一致；但 **M5 尚未建**（`../../metric_results.md` 无 M5 块、无 `test_hardware_m5`），是 Paper-2/`predict` capstone，不是已成结果。
- **EN**：Against cluster B we deliver a **calibration-quality (NLL) + coherent-slot** result, not another accuracy number (harder to scoop, `../../plan3.md`). Drift: **none** of the four touches temporal prediction → consistent with the 2026-06-13 battlefield verdict; but **M5 is not built** (no M5 block in `../../metric_results.md`, no `test_hardware_m5`) — the Paper-2/`predict` capstone, not an achieved result.

**(c) 对 plan3 tool-first 三步的喂料 / feed to the plan3 tool-first steps.**
- **Component B（黑箱 GNN fusion-merger）** ← 论文 3/4 的 Mamba/SSM 神经摊销先例 / neural amortization precedent.
- **保相干可扩展 substrate / coherence-preserving scalable substrate** ← 论文 1 的 stabilizer-TN（`../../../src/qec_twin/forward/scalable/`、ADR 0008 保相干候选，区别于 Pauli-pinned dMLE-TN）。
- **有损 Pauli 导出打分 / scoring the lossy Pauli export** ← 论文 2 的 diamond-norm logical channel（`../../cf_wr/window_covering_architecture.md`：残差本身可报 / the residual is itself a reportable result）。

**(d) 共同诚实边界 = 我们的开口 / shared honest boundary = our opening**：四篇无一"从观测 syndrome 学一个能承载相干的结构化 channel 对象 + 跟踪其漂移 + 报 honest bands"——正是 `qec_twin` 的定义性任务 / none learns a coherent-capable structured channel object from observational syndromes, tracks its drift, and reports honest bands — precisely `qec_twin`'s defining task.

## 6. 引用 / 使用建议 / Citation & usage guidance

| 论文 / Paper | 归类 / Class | 在哪用 / Where & how |
|---|---|---|
| 2605.29514 | 必引 + carrier 参考 / must-cite + carrier ref | Paper-1 related work 相干误差簇；stabilizer-TN 作 ADR 0008 保相干 bulk 引擎候选参考 |
| 2403.08706 | 必引 + 可借方法 / must-cite + method | 解释 M4 的"Pauli 近最优只限非关联"；借 selective-mischaracterization 排 DOF、喂 N1/N2；PRA 实锤 |
| 2605.17156 | 必引 baseline | 解码精度前沿假想敌；Component-B 摊销先例；衬托 NLL 指标暴露不出的胜 |
| 2510.22724 | 必引 baseline | 实时解码 baseline；端到端诚实记账范式 |

**待办钩子（建议，未执行）/ TODO hooks (suggested)**：① 进 Paper-1 related work 前把论文 2/3/4 数字回查 PDF / re-check vs PDF; ② 论文 3/4 与 dMLE（`qec_differentiable_mle_noise_2602.19722`）一起进解码器 baseline 池 / pool with dMLE; ③ 论文 2 的 selective-mischaracterization 做成 N1/N2 受控实验的对照臂 / make it an N1/N2 control arm.

**PDF 未缓存 / PDFs not cached**：四篇均未落本地 PDF（论文 1 PDF 二进制、3/4 仅 HTML）。如需缓存按 `../README.md` 的 "How to add a paper" 配方下载 / not cached; cache via "How to add a paper" in `../README.md`.
