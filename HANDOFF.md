# HANDOFF — M4 负向结果分析交接（2026-06-13）

> 读者：接手的 Claude。M4 已完整关账并提交（git `28e2d65`，未 push）。本文件交接
> **M4 负向结果的科学分析与去向决策**——这不是 debug 任务，M4 没有崩，它产出了一个
> 干净、决定性、预注册的**负向结果**。读完先读 `CLAUDE.md`，再按 §2 顺序读。
> **本任务按重型任务办：用 `/teams` 或 `/ccg` 多代理/多模型推进（见 §3 末），≥3 视角 + reviewer，理论先行。**

## 0. 一句话现状

M4（解码器先验效用，d=29 rep-code，一次 held-out 通过 05–09 双基 d′\*=5）落在其
**预注册 fallback 分支**：**两个经验标定的 DEM 先验（自算 pij + M3 twin）解码比出厂
SI1000 先验差 ~40%**（GATE twin-vs-naive −40.3% X / −40.7% Z，注册带 [+2,+30]/[+1,+25]
——+10% 的赌注反转为 −40%），而 **headline twin-vs-pij 落在带内 ≈0**（−0.33%/−0.60%）。
含义：**M3 的 syndrome-NLL 优势（+56/+44 nats）和 located bunching 证书无法通过独立边
DEM 格式传导到 MWPM 解码**（covariation 两基皆 null）。这是 **PROVISIONAL、不归因机制**
的结论；S10 预注册路由 = GATE_FAIL_CALIBRATION_DIRECTION + COVARIATION_NULL_STRUCTURAL。

## 1. 这是什么 / 不是什么（先校准心态）

- **不是 bug，不是失败的里程碑。** PAPER1_STRATEGY 早把解码端列为 rearguard（"honest
  decode-end cost accounting"），头条是 M3 bunching 链（毫发无损）。M4 的任务就是诚实
  刻画解码端，它做到了。负向是预注册可报的（reverse-trap + S10）。
- **不是可以"修"的东西。** S10 明令：no rescue fitting either way。任何"调一下 DEM 让
  它解码更好再报"都**作废 held-out 一次性保证**（G2）。理解"为什么"靠 train 侧分析 /
  sim / 新注册在 escrow 上的实验——绝不偷偷重解 held-out。
- **数字是真的。** 三向闭合（(twin−pij)+(pij−naive)≈twin−naive，<0.2pp）、McNemar
  压倒性偏 naive（n01≈253k vs n10≈105k）、裁定 28 位同一证书（7 单元跨两次尝试/一次
  OOM/两次重启 sha256 逐位相同）、P1a–i 全过、漂移语境 01–04 复现 −40%。符号 bug、
  pipeline bug、泄露已被这些证据排除。

## 2. 阅读顺序（精确到节）

1. `CLAUDE.md` —— 项目主线 + Status 段（M4 行已更新）+ **硬约束**（见 §3）。
2. `docs/metric_results.md`：
   - **`### M4 RESULTS`（行 1711 起）** —— 判决/机械段/计分表/findings/G9 claim/
     **metric+rigor 双审计**。主交接源。
   - `### M4 PRE-REGISTRATION`（行 870）+ **S7 计分项**（行 1005）/ **S10 路由**（行 1071）。
   - **M4 amendment 3 = 裁定 19–28**（行 1337 起）—— 执行史（守卫误报、A3c 错键、外部
     OOM、部分提取重置、切片提速、位同一证书）。
   - 对照 `### M3 RESULTS`（行 611）+ `### M3 ADDENDUM RESULTS`（行 802）—— **头条
     bunching 证书 + P10 联合不可实现性（366–1116σ）**，即"独立边不可表达"的注册理由。
3. `outputs/m4_state/scored_table.json` —— 全部逐行原始数字（gitignored，本地在）。
4. `outputs/m4_a4_dmle_attempt_dossier.md` —— A4 dMLE documented-drop 全证据 + r≈101
   bracket 改向方案。
5. `docs/PAPER1_STRATEGY.md` —— rearguard 框架、四条合法对比路径、抢发时钟。
6. `docs/adr/0008-scalable-carrier-feasibility-study.md` + `docs/.reports/adr0008_panel/`
   —— **载体研究**（C1 组合架构：DEM/HMM bulk + 窗精确 CPTP 相干修正）；M4 现在是它
   的 LER 级动机。`K2_alias_quotient.md` / `T3_adversarial.md` 关 T-B 定理。
7. `docs/adr/0007-...md` 里程碑表后的"Outcomes as landed"注记。

## 3. 红线（违反任一即事故）

- **held-out 一次性 + G2 冻结不可碰**：05–09 已用掉那一次；escrow 15–19 永不打开
  （除非全新注册）；composition 源（`dem_compose.py`/`m4_decode.py`/M3 缓存）哈希钉死。
- **结论纪律**：findings 1–2 的"独立边 DEM 是解码瓶颈"是 **PROVISIONAL**（无定理、
  无机制归因）。不得在其上建定义/推导/设计，除非升级为定理级。沿用 M4 RESULTS 的
  rigor 审计 (a)/(b)/(c) 分类。
- **理论先行**：任何新实验先写下预测（方向/标度/阈值）再跑；预测带 miss = finding，
  不可事后合理化（记忆 `derive-predictions-before-preregister`）。
- **脚本化执行（HARD CONSTRAINT）**：所有跑项目逻辑的执行都写脚本文件（断言+证据打印
  +刷新+spawn `__main__` 守卫），不用内联 one-liner。范例 `outputs/m4_proc_ctl.py`、
  `outputs/m4_*surgery.py`。
- **预算化并发**：近临界进程跑并发用 `outputs/memguard.py`（树-RSS 硬上限）+ GPU 分数帽，
  别全禁也别裸跑（记忆 `budgeted-concurrency-not-prohibition`）。
- **标准度量**（METRICS.md 强制阶梯）；**基线原封**（`external/baselines/` 只读）；
  GPU-only 模型计算 / 解码用批准的 CPU evaluator。
- **多代理工作流（用户 2026-06-13 指定）**：重型分析用 oh-my-claude 的 `/teams`
  （N 个共享任务表的协调代理）或 `/ccg`（Claude-Codex-Gemini 三模型编排，`/ask codex`
  + `/ask gemini` 后由 Claude 综合）；契合既有"≥3 agent + reviewer"纪律
  （记忆 `feedback-heavy-tasks-multi-agent`）。诠释去混淆（§4 #1）这种竞争假设题最适合 `/ccg`。
- git：完成即提交（风格见近期 log），**不 push、无 co-author**。

## 4. 要解决的问题（按优先级）

1. **诠释去混淆（最高优先）：** S10 把负向同时路由到"calibration-direction"（P10 miss）
   和"structural"（covariation null）——两个原因目前**缠在一起**。需要 theory-first 的
   判别：(a) twin/pij 的**权重比结构**被独立边格式系统性扭曲（结构性，指向载体），还是
   (b) 绝对 LER 标定 / 组合的某个可改进环节（P10 MC 高估了 LER）？train 侧 + sim 可做，
   **不碰 held-out**。这决定论文措辞强度与载体论证。**建议 `/ccg` 跑竞争假设。**
   > **UPDATE 2026-06-13(owner 决定:先跑 N2):** 去混淆分析已完成,登记 v2 草案
   > `outputs/m4_deconf_registration_DRAFT.md`。owner 经策略会话把它**重聚焦成 N2 单根**
   > (砍 N1/LEG-3、§6 改单根、teacher 签字 R̂≈5.3@r̂≈0.013/q̂≈0.014 + R̂=1 强制零控制)
   > 并把 contribution 定位成"dMLE 的负空间"(刻画+机理,非'更好的解码标定')。
   > **完整执行简报 + 冻结前重聚焦编辑 + 强制前置序列 + 判决→论文路由:
   > `outputs/m4_deconf_N2_refocus_plan.md`。** N2 是整篇论文存废闸:
   > (a) 结构性 ⇒ 有意义、投 Quantum;(b) 可修 ⇒ 脚注、降级。改草案 → 最终 reviewer →
   > 折入 metric_results.md 冻结 → 4 脚本各 ≥3 代理串行 65GB memguard → 跑(只 sim/train)。
2. **A3c 正向线索：** two-pass 在高 R̂ 窗 +1.1%/+0.7%（99% 显著）——唯一解码端正向，正是
   "非独立边解码步能提取 bunching"的证据，是载体研究（C1 窗精确 CPTP 修正）最干净的前向
   指针。能否扩成建设性结果？
3. **论文一去向：** 确认 rearguard 框架（M3 头条 + M4 诚实负向 + 载体动机）是否仍是投
   *Quantum* 最优切分，还是 M4 负向需调整 RA 清单 / 抢发时钟。先分析，别自动改策略。
4. **载体研究（ADR 0008）排程：** M4 现银行了 LER 级动机；C3 缝合二读 / C1 原型 的触发
   是否前移？
5. **M5 漂移**（sample-indexed）：M3/M4 漂移发现是输入；可并行。

## 5. 关键文件地图（速查）

- 结果台账：`docs/metric_results.md`（M4 RESULTS 行 1711；裁定 19–28 行 1337+）。
- 原始分数：`outputs/m4_state/scored_table.json`、`state.json`。
- 工件：`outputs/m4_artifacts/`（per-window/per-rung twin `.dem`、tier0 带、拼接 DEM、
  seam 审计、Λ̂ 阶梯）。
- A4：`outputs/m4_a4_dmle_attempt_dossier.md` + `outputs/m4_a4_dmle_*.py` 探针脚本。
- 模块：`src/qec_twin/hardware/{dem_compose,m4_decode,m4_report}.py`；测试
  `tests/test_hardware_m4_*`（114 pass + 1 skip）。
- 进程控制 / 审计脚本范例：`outputs/m4_proc_ctl.py`、`outputs/m4_ruling26_bit_audit.py`、
  `outputs/memguard.py`。
- 记忆库：`/home/cx/.claude/projects/-home-cx-Document-AI-QEC-AI-QEC/memory/`（读 MEMORY.md 索引）。

## 6. 一句话总纲

M4 干净落地为预注册负向：经验标定的独立边 DEM 解码不如出厂 SI1000，bunching 优势
不传导。别"修"它（会作废一次性 held-out），去**理解它**（train/sim/新注册），把
"独立边瓶颈"从 PROVISIONAL 推向定理或证伪——那正是载体研究的入口。用 `/teams`/`/ccg`
多视角推进。
