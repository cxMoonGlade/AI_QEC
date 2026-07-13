# Production RTN 与静态 qutrit leakage：拆分后的 bridge literature closure（2026-07-13）

> **Workflow:** `theory-fix -> close-literature -> local RAG/KG + code audit -> AnySearch`。
> RAG/KG/搜索结果只用于发现；只有全文论文及其精读笔记可以关闭 literature row。
> 本文件是证据与对象边界审计，不是 preregistration，也不授权实验或实现。
>
> **Live-code snapshot audited:** Git
> `4a226b7914612766723a874651952b763ef3c925` on 2026-07-13; `src/**` was clean at audit time.
> Load-bearing symbol locators at that snapshot: `SourceCouplingConfig` / `source_to_params`
> (`source/coupling.py:105/258`), `per_round_axis1_params` / `trajectory_mean_instrument`
> (`noise_processes/coupled_cycle.py:392/412`), `ShotSet.to_det_obs`
> (`qec_twin/forward/scalable/sv_sampler.py:588`), `QutritDM.record_oracle`
> (`carrier/exact/qutrit_dm.py:975`), and `DMOracleAnchor.capability/answer`
> (`certify/anchors/dm_oracle.py:104/169`). These line numbers are snapshot locators, not stable API.
>
> **Current gate:**
>
> - `closure_status: open`
> - `downstream_gate: CODE_BLOCKED`
> - `preregister_claim_allowed: false`
> - `direct_published_full_bridge_papers_found_in_recorded_search_corpus(Charter_A): 0`
> - `direct_published_full_bridge_papers_found_in_recorded_search_corpus(Charter_B): 0`
> - `direct_published_full_bridge_papers_found_in_recorded_search_corpus(old_mixed_object): 0`，
>   而且旧对象本身是错误拼接
> - 允许的下一步只有：继续 literature closure、修正文档/对象命名、完成不带结果的形式化
>   specification；**不得 prereg，不得写 claim-bearing experiment code，不得把局部公式或内部测试
>   提升为完整物理桥。**

## 1. Executive correction：旧链条不是一个已存在对象

旧表述把下面五层写成了一条已存在且已被文献支持的链：

```text
finite RTN z_r
  -> ten-field Theta(z_r)
  -> per-CZ “quarter-slice” leakage
  -> XZZX measurement/reset instrument
  -> full multi-round detector/observable record
```

这条链在代码和文献中都不存在。它混合了两条不同的实现、不同的 Hilbert space、不同的
schedule、不同的 measurement object，也混合了 reduced-map 与 record-law 两个不同的
non-Markovianity 对象。必须拆成两个 charter：

| charter | 当前实际对象 | 当前不包含什么 | 本 closure 的问题 |
|---|---|---|---|
| **A — production dense-qubit** | memoryful source `z_r` -> `Theta(z_r)` 参数层 -> **实际只下沉的** dense-qubit Axis-1 参数 -> 显式小规模 ancilla measurement/reset branch enumeration -> `{det,obs}` | qutrit leakage、per-CZ `exp(L/4)`、9-data XZZX、完整 ten-field channel lowering | 当前 production path 的 cycle-boundary data-only unconditional reduced map 是什么；它与 horizon/path-conditioned instrument-policy record 各自是否有直接文献/精确桥 |
| **B — static qutrit XZZX** | 静态 `(theta,g_seep,g_heat)` -> project-normalized per-CZ-layer `exp(L/4)` -> 9-data-qutrit interleaved schedule -> data-side stabilizer POVM/backaction arm -> raw syndrome + terminal obs | memoryful RTN source、production `Theta` converter、显式 physical ancilla、trajectory-varying readout/reset、统一 production facade | 静态 qutrit channel、项目归一化、data-side instrument 与 XZZX raw/full record 之间哪些层有论文，哪些仍是项目构造 |

因此不得再问“完整 `z -> Theta -> quarter-slice -> instrument -> record` 是否 CP-divisible”或
“是否已有两篇论文直接支持”；该句先天没有固定同一个 dynamical object。正确做法是分别固定 A
的 notion-1/notion-2 对象，再单独审计 B 的静态 leakage-to-record reachability。

## 2. Frozen claim packets

### 2.1 Charter A — production dense-qubit source bridge

`decision/consequence:` 是否允许把当前 production dense-qubit teacher 当作 finite-RTN 的
notion-1 QEC map，并把其 horizon/path-conditioned instrument-policy record 当作该 notion-1 verdict
的观测证据。

`mechanism:` 每条 shot trajectory 由 `OneOverFDriftSource`（八个有限 RTN 的和）或单 RTN
产生 cycle-boundary `z_r`；`SourceCouplingConfig` 把同一 draw fan out 到十个参数字段。当前 dense
teacher 每轮真正下沉的 **source-derived modulation** 只有
`zz_zeta_radns -> zeta_rad_per_ns` 和 `gamma_phi_per_ns -> gamma_phi_per_ns`；其他 baseline channel
字段并非不存在，只是没有随 `Theta(z_r)` 调制。readout/reset 也不是逐轮下沉，而是先对完整
trajectory 取均值，再把同一 instrument 参数用于全部 rounds。

`observable/record object:` 由 sealed compiler schedule 的小规模 dense density-matrix branch
enumerator 产生的完整 measurement record，经公开 XOR layout 投影成 `{det,obs}`。当前默认 fixture
是 3 data + 2 ancilla、mixed-basis 两个 checks、`m=0`，不是 9-data-qutrit d3 XZZX leakage teacher。

`mechanism -> observable bridge:`

```text
z_0:R-1
 -> CoupledMechanismParams_0:R-1
 -> per-round source-modulated {zeta, gamma_phi}; other Theta-derived modulation absent/deferred
 -> one horizon/path-dependent trajectory-mean readout/reset policy
 -> exact small-N branch law P_A(det, obs | z_0:R-1)
 -> E_z[P_A(det, obs | z_0:R-1)]
```

`predicted direction/scale:` **missing**。free-induction diagnostic 的 BLP revival 不能预测 current
dense schedule 的 unconditional data map 或 full-record effect size。旧 zeta/gamma-phi record numbers
是 project diagnostics，不是可迁移的 literature prediction。

`alternative formulations/invariants:` continuous-CTMC FID lift、cycle-held FID lift、固定 source
trajectory conditional channel、trajectory-averaged unconditional channel、outcome-conditioned map、
source-independent fixed-instrument control law 与 current path-conditioned policy record必须分开。
RHP 与 BLP也必须分开。

`possible no-go:` CP-divisibility 不决定 multi-time process Markovianity；固定 instrument 的 record
memory不反推出 reduced-map CP-indivisibility；measurement/reset 可改变可见性；平均 source history
可能产生不可逆/非可逆 map，使 intermediate-map 测试需要明确 rank/support 约定。

`implementation target:` **仅作为待关闭对象**，不是当前获准实现：任意 data input 上、每 cycle
boundary 的 unconditional reduced data map，加上独立的完整 record instrument。当前代码只对固定
initial state 枚举 record；其 trajectory-mean policy 还依赖完整 horizon/path，尚未给出 causal、跨
horizon prefix-consistent 的 notion-1 map family。

### 2.2 Charter B — static qutrit leakage bridge

`decision/consequence:` 是否允许把静态 qutrit teacher 的 `exp(L/4)` siting、data-side POVM 与
raw syndrome/obs 输出描述为“物理 quarter-CZ XZZX leakage instrument”，并据此支持 full-record、
coherence-null/nonnull 或 truncation claim。

`mechanism:` 静态 `(theta,g_seep,g_heat)` 定义单-qutrit WG-style generator
`L(theta,g_seep,g_heat)`；在 data qutrit 参加的每个 CZ layer 位置插入同一个
`exp(L/4)` slice，并与 per-qutrit H/X/Y stream 交错。

`observable/record object:` 每轮依次应用 project-defined data-side stabilizer POVM/backaction arm
（A/C/B1/B2），输出 round-major **raw syndrome** `s_{r,j}`；terminal data POVM 输出 `obs`。显式
ancilla Hilbert space、physical ancilla-CZ leakage、ancilla measurement pulse 和 reset dynamics 不在此对象中。

`mechanism -> observable bridge:`

```text
static (theta,g_seep,g_heat)
 -> L
 -> project-normalized slice E_1/4 = exp(L/4)
 -> real-circuit-derived data-side gate/CZ-layer token stream
 -> project-selected data-only stabilizer instrument
 -> raw syndrome s_1:R + terminal obs
 -> optional host XOR fold s -> detector d
```

`predicted direction/scale:` 论文支持 leakage coherence 的 record effect **schedule-dependent**，不支持
本项目 B 的固定方向或幅度。`theta/g_seep/b` 当前是 sweep/project-design 或 cross-paper composite，
不能支持 real-device magnitude。

`alternative formulations/invariants:` exact coherent channel、STA/GTA、subspace pinching、显式
data+ancilla circuit、data-only POVM representative、raw syndrome 与 detector fold必须分别报告。

`possible no-go:` 相同 `L1,L2` 不固定 channel 或 LER；相同 R=1 POVM 不固定 R>1 instrument；
data-side compiled POVM 不等于 physical ancilla process；内部 state/channel check 不等于 complete-record
law；局部 TN truncation score不控制 rare LER。

`implementation target:` 当前静态 B 仅作为一个 project-defined qutrit teacher。把 A 接到 B 是一个
**尚未定义的 prospective Charter C/integration object**，不属于当前 A 或 B：它需要显式
`CoupledMechanismParams -> per-round qutrit slice` converter、逐轮 instrument policy、统一 facade、
正确 detector semantics 和独立 full-joint oracle；当前一项都未形成 one-call production chain。

## 3. Charter A 的 notion-1 / notion-2 对象冻结

### 3.1 Notion-1：cycle-boundary、data-only、unconditional reduced map

文献所定义的 notion-1 **目标对象**是 data Hilbert space 上的 dynamical-map family。令 `D` 为
固定维数的 data register，并把完整一轮中 fresh ancilla 的准备、gate/channel、物理 measurement、
outcome-discard、reset/re-preparation 及 ancilla trace 都吸收到 data-only branch map
`J^A_{j,z_j,y_j}: L(H_D) -> L(H_D)`。定义 nonselective CPTP map
`C^A_{j,z_j} := sum_y J^A_{j,z_j,y}`。若 source path obeys 一个与 input state 无关的共同分布
`mu_r(z_0:r-1)`，则 causal、prefix-consistent 的候选 family 应写成

```text
Lambda^A_{r:0}(rho_D)
  := E_{z_0:r-1 ~ mu_r} [
       C^A_{r-1,z_{r-1}} o ... o C^A_{0,z_0}(rho_D)
     ].
```

这里要对**完整 correlated source path 一次性平均**，不能先逐轮平均再把单轮平均 map 相乘；两个
BLP inputs 必须使用同一个、input-independent source law。结果不以 observed outcomes 或某一 source
trajectory 条件化，也不保留 ancilla 或不断增长的 classical record tape。Cycle boundary、ancilla
preparation、reset 与 terminal readout 是否排除都必须唯一冻结。

但是当前 production code 不是上述局部 `C^A_{j,z_j}`。它先采完整 `R` 轮 path，再计算
`eta_R(z_0:R-1)`（trajectory-wide readout/reset mean），并让全部 rounds 共用该参数。若强行为当前
代码补一个任意-input map，只能写成 horizon-specific 的

```text
tilde Lambda^{A,(R)}_{r:0}(rho_D)
  := E_{z_0:R-1 ~ mu_R} [
       C^{A,(R)}_{r-1;z_{r-1},eta_R(z_0:R-1)} o ... o
       C^{A,(R)}_{0;z_0,eta_R(z_0:R-1)}(rho_D)
     ],    1 <= r <= R.
```

早轮 reset 参数因而依赖未来 source draws，且改变总 horizon 会重算 earlier-round instrument。经典
readout assignment 只在 branch enumeration 后重标 reported bits；没有 reported-bit feedback 时，对
outcome 求和会使它从 unconditional data map 中消失。post-reset preparation flip 则会改变下一轮 ancilla
状态，不能消去。故当前 code 至多定义一个 fixed-horizon record simulator；在另行冻结 causal/per-round
instrument policy 前，不能把它称为跨 horizon prefix-consistent 的 production dynamical-map family。

离散 cycle-boundary 的 RHP-style 问题是是否存在定义在**完整 data operator space**上的 CPTP
extension `V_{r:s}`，使 `Lambda^A_{r:0} = V_{r:s} o Lambda^A_{s:0}`。measurement/reset 使
`Lambda_s` 非可逆时，不能使用普通逆、伪逆或仅在 `Im Lambda_s` 上的 positivity test 冒充该条件；
应直接做全空间 CPTP-factor feasibility。BLP 在这些离散采样点上只能给 sampled revival witness；若只
搜 codespace inputs，更只是 restricted lower bound。无 sampled revival 不推出 CP-divisible。两者是
不同 gate，且都不是 record metric；定义来源见 [BLP note](../papers/reading_notes/blp_nonmarkovianity_measure_0908.0238.md)
与 [RHP note](../papers/reading_notes/rhp_nonmarkovianity_measure_0911.4270.md)。

当前代码没有构造任意 `rho_D` 上的 causal `Lambda^A_{r:0}`，所以 production notion-1 verdict 是
**undefined/open**。两个 finite-RTN FID diagnostic lift 的 positive BLP 只属于其声明的单-qubit
free-induction maps；见
[`finite_rtn_exact_cpdiv_literature_closure_2026-07-13.md`](finite_rtn_exact_cpdiv_literature_closure_2026-07-13.md)
与
[`finite_rtn_exact_cpdiv_result_2026-07-13.md`](finite_rtn_exact_cpdiv_result_2026-07-13.md)。

### 3.2 Notion-2：horizon/path-conditioned instrument policy 下的完整 record law

当前 production notion-2 也不是一个 source-independent 的固定数值 instrument。能被冻结的是
horizon-specific policy `I_A^{(R)}[z_0:R-1]`：它把完整 source path 映射为一套 trajectory-mean
readout/reset 参数。真实 record law 应另列为

```text
P_A^prod(y_1,...,y_R,obs)
  = E_{z_0:R-1 ~ mu_R} [
      P_A(y_1,...,y_R,obs | z_0:R-1, I_A^{(R)}[z_0:R-1])
    ].
```

其中 schedule 与 path-to-instrument **policy**可冻结，但 instrument probabilities 随 source path
变化。因此当前 record memory 混合了 source-conditioned channel modulation 与 source-conditioned
SPAM/tester modulation；不能把全部效应归因于被动系统动力学。若问题要求固定 tester 下的
notion-2，必须另设 source-independent instrument arm。record Markov order、full-history CMI、`G^2`
等性质仍既不等于也不识别 notion-1 的 RHP/BLP，反方向也不成立。该区分遵循
[`notion123_taxonomy_literature_closure_2026-07-13.md`](notion123_taxonomy_literature_closure_2026-07-13.md)。

Charter B 在本 closure 中不承载 production notion-1 verdict；它是另一个静态 qutrit
channel-to-project-instrument reachability 对象。把 B 的 coherence effect 移植给 A，或把 A 的 RTN
diagnostic 移植给 B，均为未支持 composition。

## 4. `exp(L/4)` 的强制语义纠正

`quarter-slice` 在 B 中只能表示：项目先声明一个**完整 cycle 的 dimensionless generator** `L`，再把
同一 generator 的四分之一指数放在四个 CZ-layer sites：

```text
E_cycle := exp(L),                 E_slice := exp(L/4),
(E_slice)^4 = E_cycle             (同一个 time-independent L 的代数恒等式).
```

它**不是**以下任一已获物理论文支持的说法：

- 一个 physical CZ pulse 被时间上精确切成四段；
- `L/4` 来自真实 CZ pulse duration 的四分之一；
- 每个 CZ gate 独立测得同一个 leakage generator，而一轮恰好四次；
- boundary qubit 因只接触 2/3 个 layer 就物理地获得精确 `exp(2L/4)` / `exp(3L/4)`；
- `theta`、`g_seep` 是 per-CZ measured rates。

本轮已修正 `p4a_within_cycle_model.md`；仍存活的代码注释中把 `global_per_cz` 称为“physical”的语言
仍超过证据，作为待处理 documentation debt 保留。
准确措辞是：**`exp(L/4)` 是保持四次 composition 回到项目注册 per-cycle channel 的
project normalization / siting convention。** McEwen、Sung、Varbanov 等论文提供 leakage/reset/CZ
邻接对象，但没有定义本项目这个 normalization。AnySearch 的 exact query
`exp(L/4) leakage CZ surface code` 也没有找到直接来源。

## 5. Live code audit

### 5.1 Charter A：实际 production dense chain

| code surface | 已存在的实际行为 | load-bearing gap / implication |
|---|---|---|
| [`source/coupling.py`](../../src/error_coupling_simulator/source/coupling.py), `SourceCouplingConfig`, `source_to_params` | 同一个 `z` 被复制给十个 source keys；模块自述是 parameter layer，不是 channel assembler。manifest 明列 static-ZZ formula 为 (a)，constants/sensitivities 与 log-rate/logit maps 为 (c) | 不得把十字段 fan-out 当作 published physical transfer function；recorded search 未找到 `z -> (theta,g_seep)` 直接来源 |
| 同文件的 leakage defaults | `wg_theta_base_rad = wg_theta_sensitivity = wg_g_seep_base = wg_g_seep_sensitivity = 0` | 默认 `Theta -> leakage` **完全 inert**；默认 production run 没有 source-coupled leakage |
| [`noise_processes/coupled_cycle.py`](../../src/error_coupling_simulator/noise_processes/coupled_cycle.py), `per_round_axis1_params` | 每轮只 lower `zz_zeta_radns` 和 `gamma_phi_per_ns`；gamma1/up/readout-phi/drive/fSim held at baseline | 旧“完整 Theta 已进入 production channel”错误；detuning、drive、spillover、CZ depol 与 WG leakage 没进入 dense channel |
| 同文件的 `trajectory_mean_instrument` | 每条 trajectory 对 `readout_flip_p`、`reset_flip_p` 先取完整 horizon 的 cycle mean，再构造一个 symmetric readout/reset instrument | 逐轮 source modulation 被抹平，且 earlier rounds 依赖 whole path/horizon；只能称 class-(c) trajectory-mean policy，不能称 causal per-round instrument |
| [`axis1_record_evidence.py`](../../src/error_coupling_simulator/frontend/axis1_record_evidence.py) | 小-N dense DM 精确枚举 Pauli-basis measurement branches；readout assignment 是 branch 后 classical map；reset 是 ideal reset 后 preparation flip | 这是清楚但 project-defined 的 instrument。它可以给固定输入 record law，不能自动给任意输入 data-only dynamical map |
| `CoupledCycleNoiseProcess.emit` | 默认是 sealed 5q fixture、`m=0`、外层 source trajectories、内层 exact conditional tables，最终只返回 `{det,obs}`；实现还支持 4q、`d3_repz` 与 custom builder | A 的 notion-2 记录路径确实存在；默认对象不是 d3 XZZX qutrit path，也未产生 notion-1 map family |
| `CoupledCycleNoiseProcess.channels` | 只在 `Theta(0)` mean-field 点装配 channels，不是 per-shot channel mean | 该 API 不能作为 production unconditional map；Jensen gap 已在代码中声明 |

### 5.2 Charter B：实际 static qutrit chain

| code surface | 已存在的实际行为 | load-bearing gap / implication |
|---|---|---|
| [`qutrit_teachers.py`](../../src/error_coupling_simulator/mechanisms/qutrit_teachers.py) | 静态 `field` 是 time-constant full-cycle qutrit WG-style channel；WG `L1,L2` 与 `C_L` 是 evaluator diagnostics；参数和 leaked-readout `b` 是 sweep/project choice | 支持一个 declared synthetic channel，不是 source-coupled production physical cell；它与 `RunSpec + build_within_cycle_leak` 的 `exp(L/4)` 表示共享代数但不是同一运行入口；Miao/McEwen tuple 是 cross-paper composite |
| [`sv_sampler.py`](../../src/qec_twin/forward/scalable/sv_sampler.py), `build_within_cycle_leak` | `WC_LEAK_FRAC=0.25`，构造 `exp(L/4)`，检查 CPTP，再把 slice siting 到每个 touched CZ layer | 0.25 是 project normalization；没有 pulse-time/CZ calibration bridge |
| 同文件 `_leak_compose_residual` | composition gate 以单一 input state `rho=ket(1)bra(1)` 为 probe，比较 full channel 与四次 slice 后完整 `3x3` output matrix 的最大元素差；两臂共用同一 Lindbladian/Kraus machinery | **single-input, same-model self-consistency check** 不是独立 full-superoperator/Choi/diamond equality test；实现 bug 可藏在未探测 operator basis 或共享 machinery 中。代数恒等式成立不等于实现已被独立全通道验证 |
| [`mps_forward.py`](../../src/qec_twin/forward/scalable/mps_forward.py), `sample(..., leak_slices=...)` | 默认静态 slice；已有 caller-provided、每轮一个 CPTP Kraus table 的 seam | carrier seam 存在，但“从 `Theta` 生成 tables”明确是 caller job；仓库没有 production converter，也没有 one-call source-coupled leakage teacher |
| PEPS 与 CUDA qutrit paths | PEPS 与 within-cycle CUDA marshalling 仍消费单一静态 table；`SvSampler.sample()` 仍是 lumped full-cycle path，within-cycle CUDA 另有 loader/kernel 与 committed output-script callers | 没有 per-round source-coupled qutrit path；MPS seam 不能代表 PEPS/CUDA 已接通，也不能把 output-script caller提升成 unified facade |
| data-side measurement | 9 data qutrit 上直接应用 compiled stabilizer POVM/backaction arms，terminal 再做 data readout | 没有显式 ancilla/CZ/measurement/reset dynamics；不能称 physical ancilla instrument |
| exact qutrit oracle / certification router | 当前 `QutritDM.record_oracle` 仅在 `R=1` 返回 `full_joint`；**任意 register 的 `R>=2` 都只返回 moments**。router 却可能把小-register `R>=2 FULL_JOINT/SYNDROME_DIST` 报 feasible，`answer()` 随后读取不存在的 `res["joint"]` | 当前 API 没有任何 `R>=2` full-joint anchor，并存在 capability/answer contract bug；full-9q 还受 clone-stack memory wall。这不是数学上的“不可能”声明 |
| unified facade | code search 未找到 `trajectory_to_params` / `wg_theta_rad,wg_g_seep` 到 qutrit `leak_slices` 再到 PEPS/CUDA/facade 的连接 | A 与 B 仍是两条 disconnected implementation islands；旧 mixed object 不存在 |

### 5.3 Metric hazard：raw syndrome 被命名为 `det`

[`sv_sampler.py`](../../src/qec_twin/forward/scalable/sv_sampler.py) 的 packed buffer 先存
round-major raw syndrome `s[r,j]`。`ShotSet.to_det_obs()` 调用 `SvSampler.unpack_shots()` 后直接返回
`{"det": raw_s, "obs": obs}`；它**没有**做 detector fold。真正的 detector 定义在
[`seam.py`](../../src/qec_twin/forward/scalable/seam.py) 的 `teacher_shots_to_events()`：

```text
d[0,j] = s[0,j]
d[r,j] = s[r,j] XOR s[r-1,j],   r >= 1.
```

这不是 cosmetic naming issue。若把 `ShotSet.to_det_obs()["det"]` 直接送入 detection-event
fraction、detector marginals、`p_ij`、lag/Markov-order、有限阶 factorization、DEM/decoder 等 metric，
测到的是 raw parity history，不是声明的 detector-event record。`R=1` 时 `s=d`，所以 smoke test 会
掩盖错误；`R>=2` 才暴露。

但 `s -> d` 在固定完整 layout 上是双射。若 reference 与 model 两边都一致 push-forward，exact
full-joint TV、KL 以及对应 exact distribution 的 per-sample NLL/cross-entropy 数值不变；不能笼统说
这些全记录距离被 fold “corrupt”。若只有一边 fold、所用近似模型族不对该变换封闭，或计算的是
factorized/finite-lag NLL，则数值仍会改变。故这里首先是 accessor/semantic contract bug，而不是每个
full-joint metric 都必然数值错误。已知脚本也可能显式调用 fold，必须逐 accessor 回查，不能把全部旧
B 结果一概判错。

在该 hazard 修正并由 `R>=2` positive/negative controls 锁死前，B 的任何“detector record”结果都必须
回查具体 accessor。允许的准确表述是“raw syndrome + terminal obs”，除非显式经过
`teacher_shots_to_events()` 或等价、被三方 pin 的 fold。

### 5.4 Current-HEAD live test snapshot（2026-07-13）

本轮在上述 snapshot 的同一工作树执行：

```text
conda run -n aiqec python -m pytest -q tests/
```

约 31 分 20 秒后，pytest 汇总为 **2560 passed、169 skipped、9 failed、56 warnings**；随后进程
发生 segmentation fault / core dump，最终 exit code 为 139。因此当前 HEAD 的准确状态不是“full
suite green”，也不能仅依据旧 handoff 把 teardown crash 预先归类为 benign。9 个 test failures 与
汇总后的 native crash 必须分开记录：

1. **8 个 failures 属于同一个 optional/restricted qutip-cuQuantum backend compatibility cluster。**
   `qutip 5.3.0` 与 repo-local `qutip-cuquantum 0.3.0.dev6+cedd225` 组合下，
   `external/baselines/qutip-cuquantum/src/qutip_cuquantum/qobjevo.py:24` 尝试写入只读
   `QobjEvo._dims`，抛出 `AttributeError`。代表测试
   `test_qutip_cuquantum_small_local_mcwf_smoke` 已单独稳定复现（1.60 s）。这不推翻 dense/MPS
   等其他 carrier tests，但它否定“当前 qutip-cuQuantum solver probe 可运行”。
2. **1 个 failure 是独立的 H2 crosstalk scientific/numerical gate miss。**
   `test_h2_phi_parity_and_sign_minima` 要求 flipped `KL(r=3) <= 1e-8`，实际为
   `8.15893408390167e-08`；单测复跑 342.14 s 后得到同一数值。它约为登记 floor 的 8.16 倍，
   在诊断模型、优化、metric 与 tolerance provenance 前不能降格为 rounding noise。
3. **summary 后的 exit-139 是第三个 unresolved stability defect。** 可能位于 native/CUDA teardown，
   但本轮没有最小化、stack trace 或 core analysis；“发生在 summary 后”只说明已收集 pytest
   assertions，不证明 crash harmless，也不等于可发布过程稳定。

该结果说明大量局部工程测试当前仍通过，但不关闭任何 literature bridge、full-record gate、有限键
truncation guarantee 或 d5/d7 production claim。代码可信度必须按 subsystem 报告，不能用单一 passed
总数覆盖以上三个失败面。

## 6. Literature coverage ledger

这里把“定义是否有 canonical primary source”和“是否已有至少两篇 independent direct sources
corroborate 同一 project-relevant row”分开。论文数不是正确性的替代品：单篇可关闭 canonical
definition，但不满足用户要求的 `>=2 direct-source` 强 gate；两篇各测不同 device/protocol 也不能自动
拼成一个 calibrated tuple。下表因此显式标出 one-source、two-source 与 complete-bridge 三层。

### 6.1 Charter A

| load-bearing row | required object | source / reading note | directness | status | implication |
|---|---|---|---|---|---|
| finite RTN rate convention + exact FID | symmetric RTN and exact free-induction coherence | [Bergli et al. note](../papers/reading_notes/bergli_galperin_altshuler_rtn_0904.4597.md), [Wold et al. note](../papers/reading_notes/wold_brox_galperin_classical_telegraph_1206.2174.md) | two direct sources for the diagnostic formula | closed **only for declared FID lifts** | 不支持 production `Theta`/QEC map |
| classical field -> CPTP map | trajectory-conditioned unitary and ensemble-averaged random-unitary map | [Crow–Joynt note](../papers/reading_notes/crow_joynt_classical_simulation_quantum_noise_1309.6383.md) | one direct source for stated single-qubit classes | canonical component closed; **not >=2 corroborated** | 不覆盖 nonunital reset/readout/leakage 或 project fan-out |
| stochastic Hamiltonian/control fields -> composite channels | time-correlated fields reduced to effective channels | [Oda et al./Quiroz note](../papers/reading_notes/quiroz_sparse_nonmarkovian_noise_modeling.md) | one direct adjacent source | single-source adjacent component; **not >=2 corroborated** | 无 RTN、QEC record、project `Theta` |
| random coherent/quasistatic params in QEC | parameter-drawn coherent errors propagated through stabilizer/surface-code calculations | [Clader et al. note](../papers/reading_notes/clader_correlations_heavytails_qec_2101.11631.md), [Pataki et al. note](../papers/reading_notes/quasistatic_phase_damping_stabilizer_2401.04530.md) | two published adjacent QEC sources | closed generic component | 不支持 current ten-field transfer 或 A 的 exact instrument |
| `z -> ten-field Theta` physical transfer | one fluctuator jointly modulates zeta, dephasing, detuning, drive, SPAM, CZ depol and leakage with current maps/values | no direct source found in recorded corpus | project construction | ours-inference-only | 不得当作 (a) premise；defaults/sensitivities 是 (c) |
| actual dense lowering | current two-field lowering + trajectory-mean readout/reset | code only | project implementation | ours-inference-only | 文献未验证这一 composite map |
| sequential instrument probabilities | multi-time process contracted with declared instruments | [Jorgensen–Pollock note](../papers/reading_notes/jorgensen_pollock_pt_tempo_1902.00315.md), [Gherardini et al. note](../papers/reading_notes/gherardini_transfer_tensor_multitime_2101.11662.md) | general process/instrument formalism | closed generic formal row | 没有 current QEC ancilla instantiation |
| stabilizer/QEC channel -> syndrome | arbitrary local CPTP followed by ideal syndrome projection | [Darmawan–Poulin note](../papers/reading_notes/darmawan_poulin_realistic_noise_1607.06460.md) | one direct source for single-round/perfect-measurement surface-code setting | single-source adjacent limit; **not >=2 corroborated** | 无 repeated noisy ancilla/reset、无 RTN fan-out |
| A cycle-boundary data-only unconditional map | arbitrary-input `Lambda^A_{r:0}` including actual gates, measurement-discard, reset and source average | BLP/RHP + [Jorgensen–Pollock](../papers/reading_notes/jorgensen_pollock_pt_tempo_1902.00315.md) + [Gherardini et al.](../papers/reading_notes/gherardini_transfer_tensor_multitime_2101.11662.md) ground the generic fixed-system map/instrument distinction; no current project map object | generic formalism only; no direct current-project instantiation | generic definition closed; project instance missing/open | production notion-1 verdict不存在；不得把 generic definition 当作 implementation bridge |
| A full record law bridge | exact current source -> actual lowering -> actual instrument -> full `{det,obs}` law, with published mechanism mapping | no direct source found in recorded corpus | complete-bridge found count = 0 in recorded corpus | missing/open | A 不得 prereg |

### 6.2 Charter B

| load-bearing row | required object | source / reading note | directness | status | implication |
|---|---|---|---|---|---|
| leakage/seepage channel descriptors | computational/leakage sectors, `L1,L2,C_L` | [Wood–Gambetta note](../papers/reading_notes/wood_gambetta_leakage_characterization_1704.03081.md) | one canonical direct source | definition closed; **not >=2 corroborated** | 不固定 project `theta,g_seep` values或 siting |
| qutrit leakage + explicit repeated ancilla-instrument component family | leaked qutrit modifies gate/measurement; the outcome and conditional postmeasurement/reset/feedback map are explicit | [Ghosh note](../papers/reading_notes/ghosh_leakage_ancilla_measurement_1306.0925.md), [Battistel note](../papers/reading_notes/battistel_hardware_efficient_lru_2102.08336.md), [Varbanov note](../papers/reading_notes/varbanov_leakage_detection_surface_2002.07119.md) | >=2 published direct component sources, but heterogeneous instruments | component corroborated | Ghosh is one `sigma_z` reset–CZ–measure cycle; Battistel is conventional Surface-17 qutrit declaration + conditional pi-LRU, not unconditional `ket(0)` reset；均不支持 project static generator/XZZX full chain |
| leakage/reset scale anchors | measured leakage or seepage/reset scales | [Miao note](../papers/reading_notes/miao_overcoming_leakage_scalable_2211.04728.md), [McEwen note](../papers/reading_notes/mcewen_removing_leakage_correlated_2102.06131.md) | direct for their devices/protocols | closed only as separate scales | 当前 tuple 是 cross-paper composite，不是 physical cell |
| coherent leakage reaches QEC observables | exact versus incoherent surrogate can differ, but schedule can also null it | [Marshall–Kafri note](../papers/reading_notes/marshall_kafri_incoherent_leakage_sta_2312.10277.md), [Varbanov note](../papers/reading_notes/varbanov_leakage_detection_surface_2002.07119.md), [Manabe et al. note](../papers/reading_notes/manabe_suzuki_darmawan_leakage_tn_2308.08186.md) | published direct counterexamples/boundaries in other schedules | closed as schedule-dependence/no-universal-null boundary | 不给 B 的方向/幅度，也不许可 per-slice pinching |
| `exp(L/4)` physical meaning | measured per-CZ generator or quarter-pulse derivation | no direct source found in recorded corpus/local exact-term check | project normalization | ours-inference-only | 只能称 project siting convention |
| XZZX stabilizer + repeated detector/circuit shell | XZZX check geometry, repeated syndrome and ancilla circuit boundary | [Bonilla Ataides note](../papers/reading_notes/bonilla_ataides_xzzx_surface_code_2009.07851.md), [Darmawan Kerr-cat note](../papers/reading_notes/darmawan_xzzx_kerr_cat_2104.09539.md) | two published direct XZZX component sources | component corroborated | Bonilla simulation is phenomenological and gives only a leading circuit sketch；Darmawan gives explicit circuit/conditional X-state re-preparation but uses Kerr-cat and deletes residual leakage |
| XZZX + time-correlated gate noise | gate-resolved XZZX under 1/f noise | [Gravier et al. note](../papers/reading_notes/nonmarkovian_noise_resilience_silicon_spin_2507.08713.md) | closest exact-topic source but arXiv preprint、silicon-spin、不同 noise/instrument | missing for published-premise gate | 不支持 transmon leakage/SPAM/reset 或本项目 slice |
| explicit transmon-qutrit XZZX ancilla instrument | qutrit data+ancilla CZ sequence, fixed reset/re-preparation, repeated XZZX record | no direct source found in recorded corpus | component papers do not share the target carrier/instrument | missing/open | Ghosh/Battistel 非 XZZX；Darmawan 非 transmon 且不是 branch-erasing fixed reset；data-side POVM不得冒充 physical ancilla |
| leakage-induced multi-round record signature | detector-fraction/correlation/tail changes in repeated QEC | [McEwen note](../papers/reading_notes/mcewen_removing_leakage_correlated_2102.06131.md), [Miao note](../papers/reading_notes/miao_overcoming_leakage_scalable_2211.04728.md) | two direct device/protocol-specific sources | closed for marginal/pairwise/tail existence only | 不给 full joint law、project direction/scale 或 universal Markov order |
| literature-fixed finite temporal cutoff | a safe finite history/Markov-order bound for the target record | Ghosh/Battistel/McEwen/Miao show schedule-dependent multi-cycle tails; no direct target cutoff source found | counterevidence to an untested short cutoff, not a no-finite-memory theorem | missing/open | 必须 sweep cutoff并对 full-record/rare-LER sensitivity；不得从 one lifetime estimate固定 truncation |
| raw syndrome -> detector coordinate transform | fixed layout 上的 exact bijection `d_0=s_0`, `d_r=s_r XOR s_{r-1}` | `seam.py` implementation + algebra | exact project identity, not a literature claim | closed for transform only | 不关闭 physical full-record law；accessor naming仍须修正/锁定 |
| B complete multi-round record law | exact joint law after the declared instrument and consistent coordinate transform | current R>=2 oracle returns moments only; no direct B source found in recorded corpus | missing | missing/open | moments/marginals不得冒充 full joint |
| static B complete bridge | `(theta,g_seep)` -> project slice -> exact XZZX instrument -> full detector/obs law | no direct source found in recorded corpus | complete-bridge found count = 0 in recorded corpus | missing/open | B 不得 prereg |

### 6.3 Long-range truncation row（继承，不重写）

本 closure 引用并继承
[`coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md`](../nonpauli_teacher/coherent_leakage_longrange_truncation_literature_closure_2026-07-13.md)
的完整 search-exhaustion record：

- `C2_local_truncation_to_full_record_or_rare_LER: confirmed-literature-gap`；
- direct bridge paper found count in that closure's recorded search corpus = **0**；
- Evenbly/McKeever/Sokolov 只支持 WTG/FET/ZMT algorithm boundaries；Werner/Gutoski 只支持不同
  assumptions 下的 global/strategy distance machinery；Piveteau/BSV/Manabe 只给经验 QEC convergence；
- 该 closure 的记录检索面未找到从 local PEPS/FET/WTG/ZMT score 推导本项目 complete multi-round
  record TV/KL/NLL 或 rare fixed-decoder LER guarantee 的论文。

这个 component row 已达到 skill 意义下的 `confirmed-literature-gap`；它不把本文件的 A/B rows 自动
升级为同一状态。A/B 最新 search 仍有 route/provenance 与 full-text gaps，所以本文件整体保持
`closure_status: open`。该结论同时阻止用 B 的局部 channel/composition test 为 PEPS truncation
faithfulness 背书。

## 7. Anomaly ledger

| contrary fact / ambiguity | evidence | affected object | action |
|---|---|---|---|
| finite-RTN FID lift BLP-positive，但 production path 不施加该 FID Hamiltonian | finite-RTN closure/result + `source/coupling.py` | A notion-1 | 禁止 transfer verdict |
| `Theta` 声称十字段，actual dense lowering 只有 zeta/gamma-phi；WG defaults inert | live code audit | old mixed chain | 拆 A/B；不说“full Theta channel exists” |
| readout/reset 每轮参数被 whole-horizon trajectory mean 替代 | `trajectory_mean_instrument` | A notion-1 family + notion-2 policy | 写成 horizon/path-dependent class-(c) policy；不得称 causal per-round 或 source-independent fixed instrument |
| `exp(L/4)` composition 是代数/项目归一化，不是 physical quarter-CZ | code + AnySearch q18 | B mechanism siting | 修正文档语言；寻求 pulse/gate-specific derivation，否则保持 (c) |
| composition implementation只以 `rho=ket(1)bra(1)` 为一个 input，虽比较完整 output matrix，且两臂共享 machinery | `_leak_compose_residual` | B channel correctness | 独立 full-superoperator/Choi corruption check缺失；当前 single-input same-model self-check不足 |
| same `L1,L2` 可给显著不同 LER | Manabe Fig. 8；Marshall exact-vs-STA | B surrogate/rate premise | rates 不能闭合 record law |
| Miao `~5e-3/cycle` 是 DQLR leakage-population source estimate，不是 project Wood–Gambetta `WG_L1` | Miao Fig. 3c + metric-definition audit | B numerical target | `WG_L1_target=5e-3` 只能称 paper-scale-inspired project target；identity transform与 `paper-measured` 标签错误 |
| cited Miao/McEwen sources不支持 binary leaked-readout direction `b>0.5`；McEwen hard outcome为 random `0.5` | full-text notes | B measurement nuisance | `b` 的方向、幅度、sweep endpoints均为 project design，不能称 device-grounded |
| Varbanov 特定 Surface-17 schedule 中去 coherence 不改变报告结果 | Varbanov App. B | universal coherence-necessary claim | 只允许 schedule-dependent wording |
| same R=1 POVM 可有不同 R>1 backaction | general instrument formalism + project A/C arms | B multi-round law | 必须冻结 instrument，不可只给 effects |
| `ShotSet.to_det_obs()["det"]` 实际是 raw syndrome | `sv_sampler.py` vs `seam.py` | B metrics | R>=2 前显式 fold并逐 accessor 复核；同步 push-forward 下 full-joint TV/KL/NLL 不变，不一概判旧结果错误 |
| `QutritDM.record_oracle` 的 full-joint 输出只到 `R=1`；`R>=2` 只给 moments，但 router仍可能宣告 FULL_JOINT feasible并读取 `res["joint"]` | live API + `dm_oracle.py` + tests | B record certificate | capability/answer contract bug；不能用 moments/marginals冒充 full joint，也不把未实现写成数学不可能 |
| Gravier closest XZZX/1-f source仍是 preprint且平台/噪声不同 | reading note | A/B external support | 不能单独关闭 published premise |
| local TN score没有 full-record/rare-LER theorem | long-range closure C2 | truncation propagation | `confirmed-literature-gap`; STOP truncation claim |

## 8. AnySearch external acquisition ledger（2026-07-13）

### 8.1 Routing/provenance

- Query 1–10：handoff 只保留 exact query text；route、hit list、snippet/URL 均未保留。它们只能记为
  `query attempted; results unavailable in handoff`，不能支持 rejection 或 search-exhaustion claim。
- Query 11–25：先运行 `get_sub_domains --domain academic`，再用 `academic.search`；参数为
  `category=Physics`, `type=JournalArticle`, `max_results=5`。下表保留的是 selected candidate，非完整
  hit list，故只用于 discovery/disposition，不用于穷尽性证明。
- Query 26–33：hostile audit 后补做；同样先确认 `academic.search` schema，参数为
  `category=Physics`, `type=JournalArticle`, `max_results=10`（26/27/33）或 `5`（28–32）。保留 exact
  query 与 top relevant candidate/disposition。
- 所有 AnySearch hit/snippet 都是 discovery artifacts。未进入本地 full-text reading note 的候选不能
  关闭 row；JournalArticle filter 也不能代替 DOI/version/correction/full-text verification。

### 8.2 Exact query log and dispositions

| # | route | exact query | candidate/disposition |
|---:|---|---|---|
| 1 | route/results not preserved | `random telegraph fluctuator modulates transmon leakage seepage rate transfer function experiment` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 2 | route/results not preserved | `random telegraph noise modulation transmon leakage seepage QEC` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 3 | route/results not preserved | `classical stochastic time-dependent parameters quantum circuit CPTP measurement reset instrument non-Markovianity` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 4 | route/results not preserved | `CP-divisibility BLP under measurements/interventions` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 5 | route/results not preserved | `coherent leakage quarter CZ XZZX syndrome record measurement reset` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 6 | route/results not preserved | `transmon frequency drift modulates CZ leakage probability experiment` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 7 | route/results not preserved | `TLS T1 fluctuations leakage switching telegraph` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 8 | route/results not preserved | `RTN qutrit leakage dynamical map` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 9 | route/results not preserved | `quantum instrument sequence syndrome measurement reset theorem` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 10 | route/results not preserved | `non-Markovianity QEC repeated syndrome measurements CP-divisibility BLP` | query attempted；results unavailable in handoff，不能作 rejection evidence |
| 11 | academic Physics JournalArticle, max 5 | `random telegraph noise surface code syndrome extraction repeated measurements` | returned/selected candidates 中无 direct bridge；RTN 与 surface-code repeated record未被同一来源闭合 |
| 12 | academic Physics JournalArticle, max 5 | `1/f noise rotated surface code circuit-level coherent detuning` | 无可关闭的 direct JournalArticle candidate；本地 closest Gravier `2507.08713` 是 preprint、silicon-spin、不同 instrument |
| 13 | academic Physics JournalArticle, max 5 | `classical stochastic Hamiltonian quantum error correction syndrome record` | 无 source-to-full-record direct candidate；Clader/Pataki仅关闭 generic random-parameter QEC component |
| 14 | academic Physics JournalArticle, max 5 | `quantum instrument stabilizer measurement ancilla reset non-Markovian` | Andersen et al. ancilla parity experiment, DOI `10.1038/s41534-019-0185-4`: 显式 repeated ZZ/XX parity，但无 RTN、无 leakage、无 notion-1/data-map bridge；reject as full bridge |
| 15 | academic Physics JournalArticle, max 5 | `CP-divisibility quantum error correction measurement reset` | Milz–Modi process-tensor tutorial, DOI `10.1103/PRXQuantum.2.030201`: 支持 map/process/instrument 对象区分，非 project QEC bridge；adjacent formal source only |
| 16 | academic Physics JournalArticle, max 5 | `coherent leakage XZZX surface code stabilizer measurement` | XZZX Kerr-cat candidate DOI `10.1103/PRXQuantum.2.030345`；另一个 hit DOI `10.1103/PhysRevX.13.041013` 实为 neutral-atom biased-erasure surface-code paper，**不是 XZZX paper**。均不直接覆盖 target transmon coherent-leakage instrument；reject as full bridge |
| 17 | academic Physics JournalArticle, max 5 | `subspace twirling approximation full joint syndrome distribution` | 无 direct full-joint bridge；结果多数关键词污染。Marshall STA 可定义 surrogate/给 counterexample，但不支持 project per-slice pinching或 full joint |
| 18 | academic Physics JournalArticle, max 5 | `exp(L/4) leakage CZ surface code` | McEwen DOI `10.1038/s41467-021-21982-y` 与 Sung DOI `10.1103/PhysRevX.11.021058`；分别支持 leakage reset/可调耦合 CZ 邻接事实，均不定义 `exp(L/4)`；reject as normalization support |
| 19 | academic Physics JournalArticle, max 5 | `per-CZ leakage channel qutrit stabilizer circuit` | Varbanov DOI `10.1038/s41534-020-00330-w` + leakage-reduction-unit paper DOI `10.1103/PRXQuantum.2.030314`；显式 qutrit/Surface-17 或 LRU，但不支持四分片 normalization、XZZX full record；partial adjacency only |
| 20 | academic Physics JournalArticle, max 5 | `ancilla-mediated stabilizer instrument leakage qutrit` | 无同时覆盖 explicit qutrit leakage、ancilla measurement/reset 与 target XZZX full record 的 direct candidate；多数污染 |
| 21 | academic Physics JournalArticle, max 5 | `measurement instrument changes non-Markovianity CP divisibility` | Milz–Modi DOI `10.1103/PRXQuantum.2.030201`：支持 instrument/process distinction；不是 QEC schedule bridge，也不能从 fixed record反推 CP-divisibility |
| 22 | academic Physics JournalArticle, max 5 | `classical noise QEC full syndrome record temporal correlations` | belief-matching decoder paper DOI `10.1103/PhysRevX.13.031007`：decoder/circuit-noise object，不是 classical temporal source -> complete record dynamical bridge；reject |
| 23 | academic Physics JournalArticle, max 5 | `leakage coherence detector correlations joint distribution` | 无 direct bridge；现有 Marshall/Varbanov/Manabe只给 DEF/LER、schedule-specific effects或 rate-matched counterexample，不给 target full joint law |
| 24 | academic Physics JournalArticle, max 5 | `XZZX coherent leakage` | 同 q16：Kerr-cat XZZX 与 neutral-atom biased-erasure surface-code hits；noise/Hilbert objects不同，无 target transmon qutrit coherent-leakage bridge；reject as full bridge |
| 25 | academic Physics JournalArticle, max 5 | `tensor network truncation full syndrome record logical error bound` | 无新增 direct theorem；由既有长程 closure 的 41 queries、exact-title/DOI 与 citation-chain search 判定该特定 row 为 `confirmed-literature-gap` |
| 26 | academic Physics JournalArticle, max 10 | `random telegraph noise repeated quantum error correction syndrome measurement` | top relevant hits为 broad NISQ review `10.1007/s11467-022-1249-z` 与 hybrid QEC `10.1103/PhysRevA.108.022403`；无 RTN + repeated-syndrome full bridge in returned set |
| 27 | academic Physics JournalArticle, max 10 | `classical stochastic Hamiltonian ancilla measurement reset reduced dynamical map` | Milz–Modi `10.1103/PRXQuantum.2.030201` 是 map/process/instrument generic formal candidate；无 current QEC/source path instantiation |
| 28 | academic Physics JournalArticle, max 5 | `random telegraph noise stabilizer measurement repeated syndrome record` | returned relevant item仍是 hybrid QEC `10.1103/PhysRevA.108.022403`，不含 RTN/full-record bridge |
| 29 | academic Physics JournalArticle, max 5 | `transmon telegraph noise readout reset error correlated syndrome` | closest returned item是 2026 bistable-qubit preprint `arXiv:2605.03187`；它是 frequency-feedback experiment，不是 published repeated-QEC instrument bridge |
| 30 | academic Physics JournalArticle, max 5 | `non-Markovian noise quantum error correction repeated syndrome process tensor` | returned set为 broad QEC/NISQ/mitigation sources；无 process-tensor repeated-syndrome target bridge |
| 31 | academic Physics JournalArticle, max 5 | `correlated temporal noise syndrome extraction quantum instrument` | returned set无 target direct candidate；top physics hits是 processor/FT architecture adjacency，不能关闭 source/instrument row |
| 32 | academic Physics JournalArticle, max 5 | `random unitary noise quantum error correction repeated measurement record` | real-time repeated QEC `10.1103/PhysRevX.11.041058` 与 four-qubit parity detection `10.1038/ncomms7979` 支持 repeated-measurement adjacency，不含 random-unitary/RTN full bridge |
| 33 | academic Physics JournalArticle, max 10 | `CP divisibility measurement reset quantum error correction dynamical map` | Milz–Modi `10.1103/PRXQuantum.2.030201` 与 non-Markovian RB `10.1103/PRXQuantum.2.040351` 是 generic/diagnostic adjacency；无 target post-reset QEC data-map bridge |

### 8.3 Candidate status summary

今日 acquisition 增加了有用的**候选与排除边界**，但没有 local full-text note 的条目只按
abstract/metadata-level discovery 处理：

- Andersen candidate 涉及 repeated ancilla parity experiment，但不是 RTN/leakage/notion-1 full bridge；
- Milz–Modi candidate 涉及 dynamical map、process、instrument 区分，但没有 current QEC instantiation；
- q16/q24 只有一篇 XZZX Kerr-cat candidate；`10.1103/PhysRevX.13.041013` 是 neutral-atom
  biased-erasure surface-code paper，不是第二篇 XZZX source；
- 已有本地全文 notes 的 McEwen/Sung/Varbanov 支持各自 leakage/reset/CZ/qutrit 局部对象；结合
  exact-term search，没有来源定义本项目 `exp(L/4)` normalization。LRU hit仍只作 discovery；
- belief-matching candidate 涉及 decoder/circuit-noise inference，不能承担 source-conditioned physical
  record-law 正向 row；
- q17/q20/q23/q25 没有找到 exact project bridge。

所以“候选多”不等于 closure。在本文件记录的检索 corpus 内，A/B complete bridge 的 direct
published source found count 仍为 **0**；这不是全领域论文总数或不存在定理。

### 8.4 Supplemental Charter-B discovery sweep（不计入 exhaustion）

后续又用 AnySearch 做了 44 条 B-oriented exact-query attempts，覆盖 CZ-resolved qutrit leakage、
explicit ancilla measurement/reset、XZZX circuit、full joint record 与 finite history cutoff，并对下列
核心 DOI 做 citation-chain discovery：

```text
10.1038/s41534-020-00330-w
10.1103/PhysRevApplied.23.054025
10.1088/1367-2630/ae1529
10.1038/s41567-023-02226-w
10.1038/s41467-021-21982-y
10.1038/s41467-021-22274-1
10.1103/PhysRevA.88.062329
10.1103/PRXQuantum.2.030314
10.1103/PRXQuantum.2.030345
10.1103/PhysRevX.13.041013
10.1103/PhysRevLett.130.250602
```

该 sweep 只保留了 exact query strings、selected candidates、核心 DOI full-text disposition 与 citation
walk；逐 query 的原始 CLI parameter key 和完整 hit list没有全部持久化。因此它**不能**支持
`confirmed-literature-gap` 或搜索穷尽性升级。它只用于发现来源；其中四篇承重候选随后脱离 snippet，
按 pinned full text + visual verification 建立了本地 deep notes：
[Ghosh](../papers/reading_notes/ghosh_leakage_ancilla_measurement_1306.0925.md)、
[Battistel](../papers/reading_notes/battistel_hardware_efficient_lru_2102.08336.md)、
[Bonilla Ataides](../papers/reading_notes/bonilla_ataides_xzzx_surface_code_2009.07851.md) 与
[Darmawan](../papers/reading_notes/darmawan_xzzx_kerr_cat_2104.09539.md)。上面的正向 component rows
由这些全文 notes承担，而不是由 AnySearch snippet 承担。

## 9. Search-exhaustion judgement

### 9.1 A/B rows

A/B 当前不能标 `confirmed-literature-gap`：

1. Query 1–10 的 route 与 results 均没有保留；
2. Query 11–33 是窄的 Physics/JournalArticle acquisition，虽然覆盖了关键同义词，但尚未对每个
   A/B row 做完整 backward/forward DOI citation walk；
3. Ghosh、Battistel、Bonilla Ataides 与 Darmawan 已建立 pinned-full-text deep notes，但只关闭彼此
   异质的 qutrit-instrument 或 XZZX-circuit component rows；Andersen、Milz–Modi 等其余 discovery
   candidates 仍无本地 full-text deep note，不能承担正向 row；
4. “没有命中”不是数学上的不存在证明。

故 A/B 的 load-bearing rows 保持 `missing/open` 或 `ours-inference-only`；允许动作是继续 closure，
不是把 gap 改写成 project theorem。

### 9.2 Long-range C2 row

长程 truncation row 已由引用 closure 中更广的 local RAG/KG、41 个 AnySearch queries、terminology
variants、exact-title acquisition 与 DOI forward/backward chains 达到 skill-level search exhaustion。
它保持 `confirmed-literature-gap`，但含义仅是“在已记录检索面上未找到 direct bridge”，不是全局
nonexistence theorem。

## 10. Closure verdict and propagation gate

- `closure_status: open`
- `Charter_A_complete_bridge: missing/open`
- `Charter_B_complete_bridge: missing/open`
- `C2_local_truncation_to_full_record_or_rare_LER: confirmed-literature-gap`（继承）
- `direct_published_full_bridge_papers_found_in_recorded_search_corpus_A: 0`
- `direct_published_full_bridge_papers_found_in_recorded_search_corpus_B: 0`
- `downstream_gate: CODE_BLOCKED`
- `preregister_claim_allowed: false`

### `>=2 independent direct sources` audit

- **Pass, but only for bounded component rows:** finite-RTN/FID convention (Bergli + Wold)；
  random/quasistatic parameters in adjacent QEC models (Clader + Pataki)；generic sequential
  process/instrument probabilities (Jorgensen–Pollock + Gherardini)；coherent-leakage
  schedule-dependence/counterexamples (Marshall + Varbanov + Manabe)；explicit repeated qutrit
  ancilla-instrument components (Ghosh + Battistel, but different reset targets)；XZZX
  stabilizer/detector circuit shell (Bonilla Ataides + Darmawan, but phenomenological versus
  Kerr-cat)；leakage-induced multi-round marginal/pairwise/tail signatures (McEwen + Miao)。
- **One-source only:** Crow–Joynt random-unitary component；Oda et al. stochastic-channel reduction；
  Darmawan–Poulin ideal-syndrome adjacent limit；Wood–Gambetta leakage metric definitions。它们可承担
  canonical/adjacent component，**不通过** `>=2` corroboration gate。
- **Two papers but not one composite calibration:** Miao 与 McEwen 各自锚定不同 device/protocol scale；
  不能把它们拼成当前 `(theta,g_seep,b)` physical cell。
- **Complete A/B bridge:** recorded search corpus 中 direct source found count 均为 0；所以不存在“有两篇
  直接文献确认当前实现正确”的结论。

### Closed rows

- finite-RTN rate convention与 exact FID formula，仅限两个声明的 diagnostic lifts；
- classical stochastic field -> random-unitary/CPTP 的限定类（one canonical source）；
- stochastic Hamiltonian/composite-channel（one adjacent source）与 random-parameter QEC 邻接方法
  （two adjacent sources）；
- process/instrument 概率形式和 instrument-dependence（two general sources）；
- WG leakage metrics/form（one canonical source）；
- explicit repeated qutrit ancilla-instrument components（Ghosh + Battistel；target/reset 语义不同）；
- XZZX stabilizer、repeated detector 与 circuit shell（Bonilla Ataides + Darmawan；noise carrier不同）；
- repeated-QEC 中 leakage-induced marginal/pairwise/tail signatures（McEwen + Miao；不含 full joint）；
- coherent leakage record effect 的 schedule-dependence与 `L1,L2` 不充分反例；
- WTG/FET/ZMT/global-distance 的各自方法边界；
- `exp(L/4)^4=exp(L)` 作为同一 time-independent generator 的项目代数，不是 physical CZ claim。

### Remaining load-bearing gaps

1. A 的任意-input、cycle-boundary、data-only unconditional map `Lambda^A`；
2. A 当前 actual lowering + trajectory-mean readout/reset 的 published/independently exact bridge；
3. 从 finite RTN 到 current multi-field `Theta` 的 physical transfer functions；
4. prospective Charter C 的 `Theta -> per-round qutrit slice` production converter（当前 defaults inert，MPS只有 caller seam）；
5. `exp(L/4)` 的 physical per-CZ/pulse derivation，若项目仍要作该物理解读；
6. explicit data+ancilla XZZX qutrit leakage instrument，包括 measurement/reset；
7. raw syndrome 与 detector-event semantics 的单一、不可误用 API；
8. independent full-superoperator composition certification，而非 single-input same-model check；
9. 任意 `R>=2` independent full-joint record anchor；当前 qutrit API 只给 moments，router另有 capability/answer contract bug；production-sized full-9q 还受 memory wall，但不是已证明数学不可行；
10. prospective Charter C 到 unified facade/PEPS/CUDA 的 one-call source-coupled leakage teacher；
11. target record 的安全 finite temporal-history cutoff/Markov-order bound；现有 papers 只给
    schedule-dependent multi-cycle tails，不能固定 universal cutoff；
12. local TN truncation -> full record/rare LER bridge（当前 confirmed-literature-gap）。

### Allowed next action

只允许：继续 row-specific literature acquisition/deep-read；写不含 prediction band/result 的对象
specification；修正文档中“physical quarter-CZ”“full Theta already lowered”“det=raw syndrome”等错误
措辞。任何代码更改若只是未来设计，也必须等 literature rows 与 object definitions 关闭后另行授权。

### Explicit stop

在上述 rows 关闭前，**不得**：

- 进入 `preregister-claim`；
- 声称 production source/channel CP-indivisible 或 syndrome record 暴露 notion-1；
- 声称 static qutrit `exp(L/4)` 是 physical quarter-CZ；
- 把 data-side POVM称为 explicit ancilla measurement/reset instrument；
- 用 raw syndrome 上的 metric称 detector-record metric；
- 用 single-input same-model composition、`L1/L2` matching、state fidelity、bond convergence 或 local FET/WTG/ZMT
  score证明 full-record/LER faithfulness；
- 从单篇 leakage lifetime、steady population 或 pairwise correlation 选择一个不经 full-record
  sensitivity test 的 finite temporal cutoff；
- 删除 coherent leakage tail、选择新的 deterministic truncation，或把任何 provisional result 作为下游 premise。

## 11. Load-bearing local notes

- [Breuer–Laine–Piilo trace-distance measure](../papers/reading_notes/blp_nonmarkovianity_measure_0908.0238.md)
- [Rivas–Huelga–Plenio CP-divisibility measure](../papers/reading_notes/rhp_nonmarkovianity_measure_0911.4270.md)
- [Bergli–Galperin–Altshuler RTN](../papers/reading_notes/bergli_galperin_altshuler_rtn_0904.4597.md)
- [Wold–Brox–Galperin–Bergli RTN](../papers/reading_notes/wold_brox_galperin_classical_telegraph_1206.2174.md)
- [Crow–Joynt classical random fields](../papers/reading_notes/crow_joynt_classical_simulation_quantum_noise_1309.6383.md)
- [Oda et al./Quiroz stochastic channel model](../papers/reading_notes/quiroz_sparse_nonmarkovian_noise_modeling.md)
- [Clader et al. correlated coherent QEC noise](../papers/reading_notes/clader_correlations_heavytails_qec_2101.11631.md)
- [Pataki et al. quasistatic QEC](../papers/reading_notes/quasistatic_phase_damping_stabilizer_2401.04530.md)
- [Jorgensen–Pollock process tensor](../papers/reading_notes/jorgensen_pollock_pt_tempo_1902.00315.md)
- [Gherardini et al. stochastic transfer tensors](../papers/reading_notes/gherardini_transfer_tensor_multitime_2101.11662.md)
- [Darmawan–Poulin arbitrary local CPTP surface-code simulation](../papers/reading_notes/darmawan_poulin_realistic_noise_1607.06460.md)
- [Wood–Gambetta leakage characterization](../papers/reading_notes/wood_gambetta_leakage_characterization_1704.03081.md)
- [Miao et al. leakage scale](../papers/reading_notes/miao_overcoming_leakage_scalable_2211.04728.md)
- [McEwen et al. leakage removal/reset](../papers/reading_notes/mcewen_removing_leakage_correlated_2102.06131.md)
- [Ghosh et al. explicit qutrit ancilla measurement](../papers/reading_notes/ghosh_leakage_ancilla_measurement_1306.0925.md)
- [Battistel et al. qutrit Surface-17 LRU/instrument](../papers/reading_notes/battistel_hardware_efficient_lru_2102.08336.md)
- [Bonilla Ataides et al. XZZX stabilizer/detector](../papers/reading_notes/bonilla_ataides_xzzx_surface_code_2009.07851.md)
- [Darmawan et al. Kerr-cat XZZX circuit](../papers/reading_notes/darmawan_xzzx_kerr_cat_2104.09539.md)
- [Marshall–Kafri STA](../papers/reading_notes/marshall_kafri_incoherent_leakage_sta_2312.10277.md)
- [Varbanov et al. Surface-17 leakage](../papers/reading_notes/varbanov_leakage_detection_surface_2002.07119.md)
- [Manabe–Suzuki–Darmawan leakage TN](../papers/reading_notes/manabe_suzuki_darmawan_leakage_tn_2308.08186.md)
- [Gravier et al. XZZX + 1/f preprint](../papers/reading_notes/nonmarkovian_noise_resilience_silicon_spin_2507.08713.md)

Value-level claim boundaries additionally follow
[`NUMERICAL_PROVENANCE.md`](../NUMERICAL_PROVENANCE.md)：current leakage preset is a synthetic/
cross-paper composite benchmark, not a calibrated physical device cell。
