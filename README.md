# 校园 3D 打印服务系统 Python 版

这是软件测试实验使用的控制台模拟项目。四个功能模块分别为模型尺寸检查、打印费用计算、预约条件检查、完整订单与记录。实验二在四个模块上执行等价类测试，实验三在预约条件检查模块上执行决策表测试。使用 Python 3.8 或以上版本，仅使用标准库，无需 pip 安装依赖。

## 在 VS Code 运行

1. 将整个压缩包解压到普通文件夹，不要在压缩包里运行。
2. 在 VS Code 选择“文件 → 打开文件夹”，打开包含 `main.py` 的项目文件夹（本提交包中为 `03_项目代码`）。左侧应能直接看到 `main.py`、`run_tests.py`、`decision_table_runner.py`、`modules` 和 `data`。
3. 选择“终端 → 新建终端”，先运行 `python --version`，确认显示 Python 3.8 或以上版本。
4. 运行以下命令打开系统：

```powershell
python main.py
```

先输入功能编号并回车，再按提示输入该功能的数字，数字之间用空格隔开。输入 `0` 退出。

一次运行全部测试，直接查看每条结果和汇总：

```powershell
python run_tests.py
```

也可以运行 `python main.py --test`，或者在系统菜单中选择 `7`。测试使用独立实例，不改变菜单中已提交的订单。

如果提示找不到 `main.py`，请确认终端当前目录是包含它的文件夹。如果 `python --version` 无法显示 Python 版本，需要先安装 Python 并使终端能识别 `python` 命令；安装后重新打开 VS Code。该项目无需 Visual Studio 编译器或批处理文件。

项目已带 `.vscode` 配置：解释器固定为 `D:\Python312\python.exe`（Python 3.12.8），文件按 UTF-8 打开。按 `F5` 可选择“实验三：决策表全部用例”“实验三：单条用例”“实验二：等价类测试”“实验一：回归测试”“交互系统 main.py”等调试配置；按 `Ctrl+Shift+B` 直接运行决策表测试；`Ctrl+Shift+P` 执行“Tasks: Run Task”可选择单条用例或生成 Excel 用例表。安装了 Python 扩展后，`decision_table_runner.py` 中的断点、变量查看和单步调试均可直接使用。

## 可以直接照着输入的例子

| 功能编号 | 下一行输入 | 预期结果 |
| --- | --- | --- |
| 1 | `200 100 100` | 尺寸合格 |
| 1 | `201 100 100` | 尺寸越界 |
| 2 | `100 120 1 1` | 54.00 元 |
| 2 | `1 1 0 1` | 0.38 元，最终四舍五入 |
| 3 | `3 120 120 0` | 允许预约 |
| 3 | `3 121 120 0` | 容量不足，拒绝预约 |
| 3 | `3 120 120 1` | 维护中，拒绝预约 |
| 4 | `100 100 100 100 120 0 0 0` | 新运行中编号 1，26.00 元，当天剩余 480 分钟 |
| 5 | 无需再输入参数 | 查看已提交订单与八个相对日剩余容量 |
| 6 | `1 1` | 将提前 1 天的设备设为维护中 |
| 7 | 无需再输入参数 | 执行全部自动测试 |

菜单 3 中的剩余时间是手动输入的测试条件，它只判断条件，不修改订单容量。菜单 4 使用系统内真实的剩余容量与维护状态。重复提交成功订单会使编号递增、容量减少；表中的订单示例针对新启动的系统。

也可以单独执行某个检查，例如：

```powershell
python main.py --eval size 200 100 100
python main.py --eval quote 1 1 0 1
python main.py --eval booking 3 121 120 0
python main.py --integration
```

## 实验二等价类测试

实验二使用 `equivalence_test_runner.py` 对四个模块执行弱一般、强一般和弱健壮等价类测试，同时检查输入格式和完整订单状态变化。

```powershell
python equivalence_test_runner.py
```

执行后会生成：

- `results/equivalence/classes.tsv`：等价类划分与覆盖方法
- `results/equivalence/cases.tsv`：58 条正式用例及执行结果
- `results/equivalence/supplementary_cases.tsv`：15 条补充检查结果
- `results/equivalence/run_log.txt`：完整执行日志
- `results/equivalence/screenshots/`：73 张逐用例执行截图
- `results/equivalence/evidence_manifest.json`：报告和用例表使用的结构化结果

实验二报告、PDF 和可筛选 Excel 用例表位于 `实验二` 目录。实验一原始版本保存在 Git 标签 `experiment1-baseline`，实验二测试位于分支 `experiment2-equivalence-testing`。

实验二交付文件：

- [实验二 等价类测试报告](实验二/实验二_等价类测试报告.docx)
- [实验二 等价类测试报告 PDF](实验二/实验二_等价类测试报告.pdf)
- [实验二 等价类测试用例表](实验二/实验二_等价类测试用例.xlsx)
- [实验二 交付说明](实验二/实验二_交付说明.md)

## 实验三 决策表测试

实验三选取预约条件检查模块：提前天数、请求时长、剩余容量和维护状态共同决定是否允许预约，并且维护拒绝优先于容量拒绝，适合用决策表描述。`decision_table_runner.py` 把决策表固化为可执行代码，生成 16 种理论组合、检查可达性、把动作相同的组合化简为 5 条规则，再执行 12 条正式用例并核对实际输出。

```powershell
python decision_table_runner.py
python decision_table_runner.py --case DT-01
```

执行器本身只使用标准库。重新生成 Excel 用例表需要 openpyxl：

```powershell
python -m pip install openpyxl
python scripts/build_decision_table_workbook.py
```

条件桩与动作桩：

| 编号 | 条件桩 | 条件项 |
| --- | --- | --- |
| C1 | 三个数值输入均在规定范围内 | Y/N |
| C2 | 维护编码为 0 或 1 | Y/N |
| C3 | 设备处于维护状态（维护编码=1） | Y/N |
| C4 | 请求时长不超过剩余容量 | Y/N |

| 编号 | 动作桩 | 动作含义 |
| --- | --- | --- |
| A1 | `ERR_BOOKING_RANGE` | 输入范围错误 |
| A2 | `ERR_MAINTENANCE` | 维护编码错误 |
| A3 | `REJECT_MAINTENANCE` | 设备维护中，拒绝预约 |
| A4 | `REJECT_CAPACITY` | 剩余容量不足，拒绝预约 |
| A5 | `BOOKING_OK` | 允许预约 |

化简后的 5 条规则：

| 规则 | 条件摘要 | 动作 | 原始组合数 |
| --- | --- | --- | --- |
| R1 | C1=N；C2、C3、C4 无关 | `ERR_BOOKING_RANGE` | 6 |
| R2 | C1=Y，C2=N，C3=N；C4 无关 | `ERR_MAINTENANCE` | 2 |
| R3 | C1=Y，C2=Y，C3=Y；C4 无关 | `REJECT_MAINTENANCE` | 2 |
| R4 | C1=Y，C2=Y，C3=N，C4=N | `REJECT_CAPACITY` | 1 |
| R5 | C1=Y，C2=Y，C3=N，C4=Y | `BOOKING_OK` | 1 |

4 个二值条件理论上有 16 种组合。维护编码非法时 C2=N，此时设备不可能同时处于维护中，所以 C2=N 且 C3=Y 的 4 种组合（RC03、RC04、RC11、RC12）不可达；其余 12 种组合均由具体输入触发，并各对应一条用例。R1 至 R5 的覆盖计数为 6+2+2+1+1=12。

执行后会生成：

- `results/decision_table/combinations.tsv`：16 种理论组合、可达性、动作、规则归属和覆盖用例
- `results/decision_table/rules.tsv`：5 条化简规则及覆盖计数
- `results/decision_table/cases.tsv`：12 条用例的条件项、输入、预计结果、实际结果和判定
- `results/decision_table/checks.txt`：完备性、可达性、一致性、规则覆盖和用例覆盖检查结果
- `results/decision_table/run_log.txt`、`summary.txt`、`design_review.txt`
- `results/decision_table/evidence_manifest.json`：报告、用例表和截图使用的结构化结果

全部通过时终端显示：

```text
决策表理论组合=16 可行组合=12 不可行组合=4 化简规则=5
DECISION_TABLE total=12 passed=12 failed=0
```

正式用例数据在 `data/decision_table_cases.tsv`，每行依次为用例编号、原始组合、化简规则、提前天数、时长、剩余容量、维护编码、预计结果和说明。执行器会校验用例与 12 种可行组合一一对应；如果数据或决策表被改动导致遗漏、重复或动作不一致，会直接报告错误而不执行。

实验三报告、Excel 用例表和逐用例截图位于提交包的 `01_实验报告`、`02_测试用例` 和 `04_测试结果` 目录。实验三只新增测试代码和数据，不修改实验二的业务模块。

## 四人分工和文件位置

| 组员 | 负责模块 | 主要文件 | 对应菜单 |
| --- | --- | --- | --- |
| 成员一 | 模型尺寸检查与尺寸边界用例 | `modules/size_check.py` | 1 |
| 成员二 | 费用计算、材料和加急、金额舍入用例 | `modules/pricing.py` | 2 |
| 成员三 | 预约范围、容量关系、维护条件用例 | `modules/booking.py` | 3 |
| 成员四 | 完整订单、状态更新、记录与连续流程测试 | `modules/orders.py` | 4、5、6 |

`main.py` 是统一入口；`input_utils.py` 负责共用输入校验与中文说明；`test_runner.py` 和 `run_tests.py` 负责运行固定期望值的测试数据；`equivalence_test_runner.py` 和 `decision_table_runner.py` 分别执行实验二、实验三的测试。组员可各自修改对应模块，通过同一个入口运行与测试。

## 业务规则

- 所有输入按整数处理。输入规格规定为 32 位有符号整数（-2147483648 至 2147483647），小数、字母、超范围整数返回 `ERR_INTEGER`。此限制是本项目输入规格，Python 本身支持更大的整数。
- 长、宽、高各为 1~200 mm；重量为 1~500 g；任务时长为 1~600 min；提前天数为 0~7；剩余时间为 0~600 min。
- 材料编码：0=PLA、1=PETG；加急和维护编码：0=否、1=是。
- PLA 为 0.20 元/g，PETG 为 0.30 元/g，机时费为 0.05 元/min；加急为基础价的 1.5 倍，最终四舍五入至分。这些是实验制定的价格规则。
- 预约依次检查输入范围、维护状态、剩余容量。时长等于剩余容量时允许预约；超过时拒绝。维护与容量不足同时发生时优先返回维护拒绝。
- 完整订单依次通过尺寸、报价和预约检查，成功后才写入记录并扣减对应日期的容量。失败不修改记录、容量或订单编号。
- 八个相对日分别初始拥有 600 分钟容量，互相独立；相对日索引不会随真实时间滚动。
- 订单和维护状态存放在内存中，退出后清空。项目模拟业务流程，未连接真实打印机或数据库。

## 测试数据与结果

`data/test_cases.tsv` 保留原项目的 115 条尺寸、报价、预约模块用例。`data/order_boundary_cases.tsv` 有 22 次订单边界检查（9 条普通边界、13 条健壮边界，每条从新的 Service 实例开始）。另外执行 15 项连续订单流程检查。

普通与健壮边界组包含重复输入，因此共 152 次检查不等于 152 个不同输入。期望结果预先固定在数据文件或连续流程检查中，不由被测函数生成。

运行 `python run_tests.py` 后应出现：

```text
MODULE total=115 passed=115 failed=0
ORDER_BOUNDARY total=22 passed=22 failed=0
INTEGRATION total=15 passed=15 failed=0
```

生成的逐条结果和日志在 `results` 目录：

- `module_results.tsv` 和 `module_results.log.txt`
- `order_boundary_results.tsv` 和 `order_boundary_results.log.txt`
- `integration_log.txt` 和 `summary.txt`

TSV 可用 VS Code 或 Excel 打开。测试退出码为 0=全部通过、1=结果不一致、2=文件或数据格式错误。包内结果来自 Python 3.12.8 在交付环境的真实执行；请在自己的 Windows/VS Code 终端再运行并截图。

把整个文件夹或压缩包发给组员即可。项目内使用相对于脚本位置的路径，自动测试数据不依赖某个人电脑的盘符。本仓库提供项目代码、测试数据、运行说明，以及实验二、实验三的报告、用例表和逐用例证据。
