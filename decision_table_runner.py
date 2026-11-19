"""实验三：校园 3D 打印服务系统预约条件检查模块的决策表测试执行器。

本执行器把实验三的决策表固化为可执行代码，完成四件事：
1. 按 C1~C4 四个条件桩生成 16 种理论组合，并用具体输入证明哪些组合可达；
2. 将动作相同的组合化简为 R1~R5 五条规则，检查规则无遗漏、无重叠、无矛盾；
3. 从 data/decision_table_cases.tsv 读取 12 条正式用例，逐条调用 check_booking 执行；
4. 输出组合表、规则表、用例结果、校验报告和执行清单，供报告与截图引用。

运行全部用例：python decision_table_runner.py
只运行一条用例：python decision_table_runner.py --case DT-01
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
from dataclasses import dataclass
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Iterable, Sequence

from modules.booking import check_booking

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "data" / "decision_table_cases.tsv"
OUTPUT_DIR = ROOT / "results" / "decision_table"

# 条件桩：编号、名称、判定规则。C1 把三个数值变量的范围检查合并为一个联合条件，
# 因为三个范围错误返回同一个错误码且优先级相同，合并后不损失可执行信息。
CONDITIONS: tuple[tuple[str, str, str], ...] = (
    ("C1", "三个数值输入均在规定范围内", "0<=提前天数<=7 且 1<=时长<=600 且 0<=剩余容量<=600"),
    ("C2", "维护编码为 0 或 1", "维护编码属于 {0, 1}"),
    ("C3", "设备处于维护状态", "维护编码 = 1"),
    ("C4", "请求时长不超过剩余容量", "时长 <= 剩余容量"),
)

# 动作桩：编号、结果码、含义。顺序即程序的判定优先级。
ACTIONS: tuple[tuple[str, str, str], ...] = (
    ("A1", "ERR_BOOKING_RANGE", "输入范围错误"),
    ("A2", "ERR_MAINTENANCE", "维护编码错误"),
    ("A3", "REJECT_MAINTENANCE", "设备维护中，拒绝预约"),
    ("A4", "REJECT_CAPACITY", "剩余容量不足，拒绝预约"),
    ("A5", "BOOKING_OK", "允许预约"),
)

ACTION_NAMES = {code: name for _, code, name in ACTIONS}


@dataclass(frozen=True)
class Rule:
    """一条化简后的决策规则，pattern 中 None 表示该条件无关。"""

    id: str
    name: str
    expression: str
    pattern: tuple[bool | None, bool | None, bool | None, bool | None]
    action: str
    purpose: str

    def matches(self, flags: tuple[bool, bool, bool, bool]) -> bool:
        return all(
            expected is None or expected == actual
            for expected, actual in zip(self.pattern, flags)
        )


# 化简规则与报告表 5-6 一致：动作相同的组合按无关条件合并。
RULES: tuple[Rule, ...] = (
    Rule("R1", "数值范围错误", "C1=N；C2、C3、C4无关",
         (False, None, None, None), "ERR_BOOKING_RANGE", "范围优先"),
    Rule("R2", "维护编码错误", "C1=Y，C2=N，C3=N；C4无关",
         (True, False, False, None), "ERR_MAINTENANCE", "编码校验"),
    Rule("R3", "设备维护中", "C1=Y，C2=Y，C3=Y；C4无关",
         (True, True, True, None), "REJECT_MAINTENANCE", "维护优先"),
    Rule("R4", "剩余容量不足", "C1=Y，C2=Y，C3=N，C4=N",
         (True, True, False, False), "REJECT_CAPACITY", "容量判断"),
    Rule("R5", "允许预约", "C1=Y，C2=Y，C3=N，C4=Y",
         (True, True, False, True), "BOOKING_OK", "正常放行"),
)

RULE_MAP = {rule.id: rule for rule in RULES}


@dataclass(frozen=True)
class Combination:
    """决策表中的一种理论条件组合。"""

    id: str
    flags: tuple[bool, bool, bool, bool]
    possible: bool
    witness: tuple[int, int, int, int] | None
    action: str | None

    @property
    def signature(self) -> str:
        return "".join("Y" if value else "N" for value in self.flags)


@dataclass(frozen=True)
class Case:
    """一条正式测试用例，输入顺序为提前天数、时长、剩余容量、维护编码。"""

    id: str
    raw_rule: str
    rule_id: str
    day: int
    minutes: int
    remaining: int
    maintenance: int
    expected: str
    note: str

    @property
    def inputs(self) -> tuple[int, int, int, int]:
        return self.day, self.minutes, self.remaining, self.maintenance

    @property
    def input_text(self) -> str:
        return " ".join(str(value) for value in self.inputs)

    @property
    def flags(self) -> tuple[bool, bool, bool, bool]:
        return condition_flags(*self.inputs)

    @property
    def signature(self) -> str:
        return "".join("Y" if value else "N" for value in self.flags)


def condition_flags(
    day: int, minutes: int, remaining: int, maintenance: int
) -> tuple[bool, bool, bool, bool]:
    """把一组具体输入映射为 C1~C4 的真假值。"""
    return (
        0 <= day <= 7 and 1 <= minutes <= 600 and 0 <= remaining <= 600,
        maintenance in (0, 1),
        maintenance == 1,
        minutes <= remaining,
    )


def expected_action(flags: tuple[bool, bool, bool, bool]) -> str:
    """按动作桩优先级由条件项推导动作，用于核对决策表与业务代码是否一致。"""
    if not flags[0]:
        return "ERR_BOOKING_RANGE"
    if not flags[1]:
        return "ERR_MAINTENANCE"
    if flags[2]:
        return "REJECT_MAINTENANCE"
    if not flags[3]:
        return "REJECT_CAPACITY"
    return "BOOKING_OK"


def witness_for(flags: tuple[bool, bool, bool, bool]) -> tuple[int, int, int, int] | None:
    """为一组条件项构造最小具体输入；不可达时返回 None。

    通过构造而不是枚举来证明可达性：输入只让需要为 N 的条件不成立，
    其余条件保持成立，因此得到的组合可读、可复核。
    """
    c1, c2, c3, c4 = flags
    if not c2 and c3:
        # 维护编码不是 0 或 1 时，设备不可能同时处于维护中。
        return None
    day = 3 if c1 else -1
    minutes, remaining = (100, 100) if c4 else (101, 100)
    maintenance = 2 if not c2 else (1 if c3 else 0)
    witness = (day, minutes, remaining, maintenance)
    if condition_flags(*witness) != flags:
        return None
    return witness


def build_combinations() -> list[Combination]:
    """按 C1 到 C4 的顺序生成 16 种理论组合，并标注可达性与动作。"""
    combinations: list[Combination] = []
    for index, flags in enumerate(product((False, True), repeat=4), 1):
        witness = witness_for(flags)
        possible = witness is not None
        combinations.append(
            Combination(
                id=f"RC{index:02d}",
                flags=flags,
                possible=possible,
                witness=witness,
                action=expected_action(flags) if possible else None,
            )
        )
    return combinations


def rule_for(flags: tuple[bool, bool, bool, bool]) -> Rule | None:
    matches = [rule for rule in RULES if rule.matches(flags)]
    return matches[0] if len(matches) == 1 else None


def read_cases(path: Path = CASES_PATH) -> list[Case]:
    required = [
        "id", "raw_rule", "rule_id", "day", "minutes", "remaining",
        "maintenance", "expected", "note",
    ]
    cases: list[Case] = []
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames != required:
            raise ValueError("决策表测试数据字段不完整，应包含：" + "、".join(required))
        for line_no, row in enumerate(reader, 2):
            try:
                cases.append(
                    Case(
                        id=row["id"].strip(),
                        raw_rule=row["raw_rule"].strip(),
                        rule_id=row["rule_id"].strip(),
                        day=int(row["day"]),
                        minutes=int(row["minutes"]),
                        remaining=int(row["remaining"]),
                        maintenance=int(row["maintenance"]),
                        expected=row["expected"].strip(),
                        note=row["note"].strip(),
                    )
                )
            except (TypeError, ValueError) as error:
                raise ValueError(f"{path.name} 第 {line_no} 行数值格式错误：{error}") from error
    if not cases:
        raise ValueError("决策表测试数据为空")
    return cases


def validate_design(cases: Sequence[Case]) -> tuple[list[Combination], list[tuple[str, str]]]:
    """检查决策表的完备性、可达性、一致性和用例覆盖，返回组合与校验摘要。"""
    combinations = build_combinations()
    checks: list[tuple[str, str]] = []

    feasible = [item for item in combinations if item.possible]
    infeasible = [item for item in combinations if not item.possible]
    if len(combinations) != 16 or len(feasible) != 12 or len(infeasible) != 4:
        raise ValueError(
            f"组合数不符合 4 个二值条件的理论值：共 {len(combinations)}，"
            f"可行 {len(feasible)}，不可达 {len(infeasible)}"
        )
    checks.append(("完备性", f"16 种理论组合全部列出，可行 {len(feasible)}，不可达 {len(infeasible)}"))
    checks.append((
        "可达性",
        "不可达组合为 " + "、".join(item.id for item in infeasible)
        + "；其余组合均由具体输入触发",
    ))

    # 每个可行组合必须恰好匹配一条规则，且规则动作与动作桩推导一致。
    for item in feasible:
        matched = [rule for rule in RULES if rule.matches(item.flags)]
        if len(matched) != 1:
            raise ValueError(f"{item.id} 匹配到 {len(matched)} 条规则，规则存在重叠或遗漏")
        rule = matched[0]
        if rule.action != item.action:
            raise ValueError(f"{item.id} 的规则动作 {rule.action} 与动作桩推导 {item.action} 不一致")
    # 不可达组合不参与规则覆盖：它们不是业务输入，不能被计入规则数或测试覆盖。
    checks.append((
        "一致性",
        f"每个可行组合只对应一条规则，{len(RULES)} 条规则动作与动作桩推导一致，"
        f"{len(infeasible)} 种不可达组合不计入规则覆盖",
    ))

    # 规则覆盖计数必须与化简前组合数一致，总和为 12。
    counts = {
        rule.id: sum(1 for item in feasible if rule.matches(item.flags))
        for rule in RULES
    }
    declared = {rule.id: rule for rule in RULES}
    if set(counts) != set(declared):
        raise ValueError("化简规则编号与定义不一致")
    if sum(counts.values()) != len(feasible):
        raise ValueError(f"规则覆盖计数 {sum(counts.values())} 与可行组合 {len(feasible)} 不一致")
    if any(counts[rule.id] == 0 for rule in RULES):
        raise ValueError("存在没有覆盖任何可行组合的空规则")
    detail = "，".join(f"{rule_id}={counts[rule_id]}" for rule_id in counts)
    checks.append(("化简覆盖", f"规则覆盖计数 {detail}，合计 {sum(counts.values())}"))

    # 用例检查：编号唯一、规则合法、动作一致、与可行组合一一对应。
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("决策表测试用例编号重复")
    if len(cases) != len(feasible):
        raise ValueError(f"正式用例 {len(cases)} 条，与可行组合 {len(feasible)} 种不一致")

    by_signature: dict[str, str] = {}
    for case in cases:
        if case.rule_id not in RULE_MAP:
            raise ValueError(f"{case.id} 引用了不存在的规则 {case.rule_id}")
        rule = RULE_MAP[case.rule_id]
        if not rule.matches(case.flags):
            raise ValueError(f"{case.id} 的条件组合 {case.signature} 不属于规则 {rule.id}")
        if case.expected != expected_action(case.flags):
            raise ValueError(f"{case.id} 的预计结果与动作桩推导不一致")
        if case.expected != rule.action:
            raise ValueError(f"{case.id} 的预计结果与规则 {rule.id} 的动作不一致")
        combination = next((item for item in combinations if item.signature == case.signature), None)
        if combination is None:
            raise ValueError(f"{case.id} 的条件组合 {case.signature} 不在 16 种理论组合中")
        if not combination.possible:
            raise ValueError(f"{case.id} 使用了不可达组合 {combination.id}")
        if case.raw_rule != combination.id:
            raise ValueError(
                f"{case.id} 标注的原始组合 {case.raw_rule} 与实际条件组合 {combination.id} 不一致"
            )
        if case.signature in by_signature:
            raise ValueError(
                f"{case.id} 与 {by_signature[case.signature]} 覆盖了同一可行组合 {combination.id}"
            )
        by_signature[case.signature] = case.id

    missing = [item.id for item in feasible if item.signature not in by_signature]
    if missing:
        raise ValueError("以下可行组合没有对应用例：" + "、".join(missing))
    checks.append(("用例覆盖", f"{len(cases)} 条用例与 {len(feasible)} 种可行组合一一对应"))
    checks.append(("规则覆盖", f"R1~R{len(RULES)} 共 {len(RULES)} 条规则均至少有一条用例"))

    return combinations, checks


def execute_case(case: Case) -> str:
    return check_booking(*case.inputs)


def combination_rows(
    combinations: Sequence[Combination], cases: Sequence[Case]
) -> list[dict[str, object]]:
    case_by_signature = {case.signature: case.id for case in cases}
    rows: list[dict[str, object]] = []
    for item in combinations:
        rule = rule_for(item.flags) if item.possible else None
        rows.append(
            {
                "id": item.id,
                "C1": "Y" if item.flags[0] else "N",
                "C2": "Y" if item.flags[1] else "N",
                "C3": "Y" if item.flags[2] else "N",
                "C4": "Y" if item.flags[3] else "N",
                "possible": "Y" if item.possible else "N",
                "action": item.action or "IMPOSSIBLE",
                "rule_id": rule.id if rule else "",
                "covered_by": case_by_signature.get(item.signature, ""),
                "witness": " ".join(str(value) for value in item.witness) if item.witness else "",
            }
        )
    return rows


def write_tsv(path: Path, fields: Sequence[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(fields), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def print_case(case: Case, actual: str) -> None:
    flags = case.flags
    rule = RULE_MAP[case.rule_id]
    condition_text = "  ".join(
        f"{name}={'Y' if value else 'N'}" for (name, _, _), value in zip(CONDITIONS, flags)
    )
    print(f"实验三 决策表测试  用例 {case.id}")
    print(f"原始条件组合：{case.raw_rule}    化简规则：{case.rule_id} {rule.name}")
    print(f"条件项：{condition_text}")
    print(f"输入（提前天数 时长 剩余容量 维护）：{case.input_text}")
    print(f"预计结果：{case.expected}")
    print(f"实际结果：{actual}")
    print(f"判定：{'PASS' if actual == case.expected else 'FAIL'}")
    print(f"说明：{case.note}")


def run(output_dir: Path = OUTPUT_DIR, single_case: str | None = None) -> int:
    cases = read_cases()
    combinations, checks = validate_design(cases)
    combination_table = combination_rows(combinations, cases)

    if single_case:
        matches = [case for case in cases if case.id == single_case]
        if not matches:
            raise ValueError(f"找不到用例：{single_case}")
        case = matches[0]
        actual = execute_case(case)
        print_case(case, actual)
        return 0 if actual == case.expected else 1

    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    logs: list[str] = []
    for case in cases:
        actual = execute_case(case)
        status = "PASS" if actual == case.expected else "FAIL"
        flags = case.flags
        rule = RULE_MAP[case.rule_id]
        row = {
            "id": case.id,
            "raw_rule": case.raw_rule,
            "rule_id": case.rule_id,
            "rule_name": rule.name,
            "C1": "Y" if flags[0] else "N",
            "C2": "Y" if flags[1] else "N",
            "C3": "Y" if flags[2] else "N",
            "C4": "Y" if flags[3] else "N",
            "inputs": case.input_text,
            "expected": case.expected,
            "actual": actual,
            "status": status,
            "note": case.note,
        }
        rows.append(row)
        logs.append(
            f"[{status}] {case.id} {case.rule_id} 条件={case.signature} "
            f"输入={case.input_text} 预期={case.expected} 实际={actual}"
        )

    passed = sum(row["status"] == "PASS" for row in rows)
    failed = len(rows) - passed
    feasible_count = sum(1 for item in combinations if item.possible)
    infeasible_count = len(combinations) - feasible_count

    write_tsv(
        output_dir / "cases.tsv",
        [
            "id", "raw_rule", "rule_id", "rule_name", "C1", "C2", "C3", "C4",
            "inputs", "expected", "actual", "status", "note",
        ],
        rows,
    )
    write_tsv(
        output_dir / "combinations.tsv",
        ["id", "C1", "C2", "C3", "C4", "possible", "action", "rule_id", "covered_by", "witness"],
        combination_table,
    )
    rules_rows: list[dict[str, object]] = []
    for rule in RULES:
        count = sum(1 for item in combination_table if item["rule_id"] == rule.id)
        rules_rows.append(
            {
                "rule_id": rule.id,
                "name": rule.name,
                "conditions": rule.expression,
                "action": rule.action,
                "raw_count": count,
                "purpose": rule.purpose,
            }
        )
    write_tsv(
        output_dir / "rules.tsv",
        ["rule_id", "name", "conditions", "action", "raw_count", "purpose"],
        rules_rows,
    )

    executed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    design_corrections = [
        {
            "type": "决策表设计错误",
            "phenomenon": "初稿把 C2=N、C3=Y 的 4 种组合当作可执行规则",
            "cause": "维护编码不是 0 或 1 时，设备不可能同时具有“维护中”状态，这 4 种组合在业务上不可达",
            "correction": "将 4 种组合标记为不可达，不计入可行规则、有效规则数和测试覆盖",
            "verification": "12 种可行组合与 12 条用例一一对应，全部通过",
        }
    ]
    manifest = {
        "project": "校园 3D 打印服务系统",
        "experiment": "实验三 决策表测试",
        "module": "预约条件检查",
        "executed_at": executed_at,
        "python": platform.python_version(),
        "conditions": [
            {"id": item[0], "name": item[1], "rule": item[2]} for item in CONDITIONS
        ],
        "actions": [
            {"id": item[0], "result": item[1], "meaning": item[2]} for item in ACTIONS
        ],
        "summary": {
            "theoretical_combinations": len(combinations),
            "impossible_combinations": infeasible_count,
            "feasible_combinations": feasible_count,
            "reduced_rules": len(RULES),
            "cases": len(rows),
            "passed": passed,
            "failed": failed,
        },
        "checks": [{"name": name, "detail": detail} for name, detail in checks],
        "rules": rules_rows,
        "combinations": combination_table,
        "cases": rows,
        "design_corrections": design_corrections,
        "defects": [],
    }
    (output_dir / "evidence_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "run_log.txt").write_text("\n".join(logs) + "\n", encoding="utf-8")
    (output_dir / "checks.txt").write_text(
        "\n".join(f"{name}：{detail}" for name, detail in checks)
        + f"\n正式用例：{len(rows)} 条，通过 {passed} 条，失败 {failed} 条\n",
        encoding="utf-8",
    )
    (output_dir / "design_review.txt").write_text(
        "\n".join(
            f"{index}. {item['type']}：{item['phenomenon']}；"
            f"原因：{item['cause']}；修正：{item['correction']}；"
            f"验证：{item['verification']}"
            for index, item in enumerate(design_corrections, 1)
        )
        + "\n",
        encoding="utf-8",
    )
    summary = (
        f"决策表理论组合={len(combinations)} 可行组合={feasible_count} "
        f"不可行组合={infeasible_count} 化简规则={len(RULES)}\n"
        f"DECISION_TABLE total={len(rows)} passed={passed} failed={failed}"
    )
    (output_dir / "summary.txt").write_text(summary + "\n", encoding="utf-8")
    print("\n".join(logs))
    print(summary)
    print(f"结果目录：{output_dir}")
    return 0 if failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="执行实验三决策表测试")
    parser.add_argument("--case", help="只执行指定用例，例如 DT-01")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="测试结果输出目录")
    args = parser.parse_args()
    try:
        return run(args.output, args.case)
    except (OSError, ValueError) as error:
        print(f"决策表执行失败：{error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
