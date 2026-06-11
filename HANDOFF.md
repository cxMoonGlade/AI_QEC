# HANDOFF — M4 held-out 执行交接（2026-06-11，自 Windows 侧会话移交 WSL 内原生会话）

> 读者：接手的 Claude（Fable 5，WSL 原生）。本文件是唯一交接源；读完先读
> `CLAUDE.md`，再读 `docs/metric_results.md` 的 M4 注册节 + 三个修正案。
> 用户已手动终止上一会话的全部运行进程。git HEAD = `6362eab`（工作树干净，
> `outputs/` 为 gitignored 工作目录）。

## 0. 你比前任天然多的优势

前任在 Windows 侧经 `wsl.exe` RPC 边界操作，吃了一整天的边界病：孤儿进程
（跨边界杀不死）、守卫误报、包装进程之死传杀一次性任务、完成通知丢失。
**你在 WSL 原生运行，进程树语义正常，这些病理全部消失**——
`outputs/wsl_guard.sh` 对你无用（勿用）；直接前台跑或 `setsid`+日志即可。

## 1. 当下状态（精确事实）

**M4 顺序冻结状态机**（`outputs/m4_state/state.json`）：

| 阶段 | 状态 |
|---|---|
| pins | ✅（P1e 位精确 0/600,000：{00,50,99}×{X,Z}） |
| freeze | ✅ G2 manifest `f63845ef…`；P1h 结构组件过；±0.5% (b) 带 miss 已按裁定 14(ii) 记为注册发现（twin 9372/9559、pij 6382/5194 位点） |
| pilot | ✅（实测阶梯：d′≥17 零事件；hot 分段 pij 比 naive 差 13× 的预览信号在 d′=11） |
| select_rung | ✅ **d′\* = 5**（资格窗内、双基一致、无旗标） |
| p10_forecast | ✅ GPU MC 预测已存档钉死（`p10_forecast_20260611T080050Z.json`） |
| floor_check | ✅ 不扩展；held-out 样本 = **[5,6,7,8,9]** |
| **heldout** | ❌ **尝试 #4 被用户手动终止**：`begin_heldout` 已持久化（started ~05:24Z）、payload null、**npz = 0（零统计产出）**——见 §2 第一步 |
| score / artifacts | 未跑 |

**held-out 的三次失败史 + 修复（全部已入账为 M4 修正案 3，裁定 19–22）**：
1. 尝试 #2：G4 理智上沿 (0,0.5) 在饱和探针上必然误触发 → 裁定 19 改为
   `0.5 + 5·√(0.25/n)`；裁定 20 重置（守卫先于任何读卷，源码验证）。
2. 尝试 #3a：A3c 几何按设备坐标错键撞崩 → 裁定 21：发射 DEM 强制
   `with_grid_coordinates`、新增提交前几何守卫、`begin_heldout` 移到全部
   train 侧守卫之后；train 侧零泄露证明存档（`outputs/m4_a3c_geometry_repro.py`）。
3. 尝试 #3b：外部基础设施杀（Windows GPU 驱动事件，dxg ioctl 风暴）→
   裁定 22：解码进程屏蔽 CUDA（`CUDA_VISIBLE_DEVICES=`）+ 缓存
   `map_location="cpu"`。**两次实跑中全部守卫已通过**（G4 四臂、A3c 几何
   双基为空）——管线本身已被证实健康，死因全是外部。

**系统残留**：dxg ioctl 风暴可能仍在刷内核日志（Windows 侧坏句柄轮询）；
VM 里可能还有上一会话的 ~4 个 python 残影进程。

## 2. 你的第一批动作（按序）

1. **建议先让用户做一次 `wsl --shutdown` 再开你的会话**（当前无任何在跑任务，
   重启免费，顺带清掉 dxg 风暴与残影进程）。若已开会话，先清扫：
   `ps -eo pid,etime,args | grep -E 'python|pytest' | grep -v grep`，杀掉非己进程。
2. **裁定 23 手术（重置尝试 #4）**：先在 `docs/metric_results.md` 的
   "M4 PRE-RUN AMENDMENT 3" 下追加裁定 23——用户手动终止、npz=0、payload null、
   零信息提取（同裁定 21/22 依据）——然后仿照 `outputs/m4_ruling22_surgery.py`
   写 ruling23 手术脚本（弹出 `stages.heldout`、追加 surgery_log）。**先记账后手术**。
3. **重启 held-out（尝试 #5，原生直跑）**：
   ```bash
   cd /home/cx/Document/AI_QEC/AI_QEC
   QEC_TWIN_HW_DATA=/home/cx/Document CUDA_VISIBLE_DEVICES= \
     timeout 10800 conda run -n aiqec python -m qec_twin.hardware.m4_report heldout --workers 16 \
     2>&1 | tee outputs/m4_state/heldout_attempt5.log
   ```
   （conda 在交互 shell 可用；非交互用 `/home/cx/miniconda3/envs/aiqec/bin/python`。）
   预期 1–2 小时；**进度条 = `outputs/m4_state/heldout_*_s*.npz` 数量（共 10 个）**，
   逐 (基,样本) 增量落盘。每 ~30 分钟给用户一个 ALIVE/进度回执（用户明确要求）。
4. **score → artifacts**：
   ```bash
   ... python -m qec_twin.hardware.m4_report score
   ... python -m qec_twin.hardware.m4_report artifacts
   ```
   score 对 S7 注册带表打分（两 primary/基：gate twin-vs-naive @单侧99%、
   headline twin-vs-pij 双侧、协变偏 Spearman 双零、located 符号、P10 对照、
   漂移）；S10 路由按注册执行。dMLE A4 条件臂：score 阶段尝试
   run-unmodified-or-drop（vendored `external/baselines/DMLE-QEC`，原封、
   推荐配置；跑不起来就 drop-with-documentation）。
5. **M4 RESULTS 入台账**（`docs/metric_results.md`，对照
   "### ADR 0008 SEAM-TEST RESULTS" 一节的格式与严格度）：判决头条 → 机械段 →
   逐预测计分表（measured/registered/verdict + 类标）→ findings（located、
   不归因）→ claim 语言（G9 模板逐字）→ **metric audit + rigor audit**
   （工作环最后两环，缺一不可）。然后更新 CLAUDE.md 的 Status 段、
   ADR 0007 的 M4 行、提交 git（**不带 co-author，不 push**）。

## 3. 硬规则（违反任何一条都是事故）

- **held-out 纪律**：样本 05–09 只经 staged runner 的那一次通过；escrow
  15–19 永不打开；样本 01–04 仅 scoring 阶段作漂移语境。任何中途崩溃→
  先证明零信息提取（npz/payload/日志）→ 记裁定 → 手术 → 重启；
  **绝不静默重跑**。
- **G2 冻结**：`dem_compose.py`、`m4_decode.py`、`outputs/m3_fit_cache.pt`
  的 sha256 已钉（state.json `/freeze/source_hashes`）。改任何一个 =
  作废进 escrow，除非注册官裁定（守卫常数类先例 = 裁定 19/20）。
- **注册文本冻结**：S1–S12 与带表数字一个不许动；miss = finding，
  禁止改带、改容差、改组合。
- **GPU/CPU**：模型计算 GPU-only（M4 已无新拟合）；解码 = 批准的 CPU
  evaluator（R1）；held-out 进程保持 CUDA 屏蔽（裁定 22）。
- **零新拟合**：M4 永远只消费冻结的 M3 缓存。
- 种子：M4 新随机性一律 20260610。
- 重型任务 ≥3 agent + reviewer；理论先行；工作环含 metric/rigor 双审计；
  暂时性结论之上不许建任何东西。
- git：完成即提交（信息风格见近期 log），不 push、无 co-author。

## 4. M4 之后的待办队列（按底层优先）

1. **缝合第二读注册**（公开注册义务，触发门控）：缝跨 re-tiling——
   G-NLL(i) + 跨 tiling item-32 + determinism item 14 的重验
   （item 14 在首读 (a) 级 miss：gradcheck 2.171e-10 vs 1e-10、跨种子
   1.615e-6 vs 1e-6——挂起未卸除，禁止追溯放宽）。
2. **L0b 旁观比特机械分析**（spec 在 `docs/.reports/adr0008_panel/L0_circuit_audit.md`）；
   L1 足迹审计（任何硬件带之前）；L2/L3（surface 窗注册之前）。
3. K4 残项：D4 舰队枚举 + P4 t_eff 微基准。
4. M5（漂移，按样本索引切片）——M3/M4 的漂移发现是输入。
5. CLAUDE.md / AGENTS.md 状态段刷新。

## 5. 关键文件地图

- 注册与结果台账：`docs/metric_results.md`（M4 注册 + 修正案 1/2/3 =
  裁定 14–22；缝合注册 + 修正案 1–3 + **SEAM-TEST RESULTS（K1 首读
  ABSTAIN，已关账）**）。
- 状态机：`outputs/m4_state/`（state.json、pilot_table.json、P10 预测、
  守卫/钳位 payload）。手术脚本范例：`outputs/m4_ruling2{0,1,2}_surgery.py`。
- 面板/审查档案：`docs/.reports/m4_panel/`（注册蓝图、三建造报告、
  build_R_m4_review.md——含 run 计划与 §D P1h 诊断）、
  `docs/.reports/adr0008_panel/`（缝合全档案 + run_R3 计分审查）。
- 模块：`src/qec_twin/hardware/{dem_compose,m4_decode,m4_report}.py`
  + 测试 `tests/test_hardware_m4_*`（全绿基线：62+25+52）。
- 心跳脚本（可继续用）：`outputs/m4_heldout_watch.py`。
- ADR：0007（M4 行）、0008（K1 首读状态已写入 Status）。

## 6. 一句话总纲

M4 万事俱备：管线全绿、守卫全过、预测已钉死——只欠把那一次 held-out
完整跑完，然后按注册打分、入账、双审计、关账。别创新，按注册走。
