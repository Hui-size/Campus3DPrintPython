"""读取预先固定的期望值，测试结果写入项目自身的 results 目录。"""

import csv
from pathlib import Path

from input_utils import evaluate, parse_values
from modules.orders import Service

ROOT = Path(__file__).resolve().parent
FIELDS = ["id", "group", "module", "inputs", "expected", "actual", "status", "error"]


def read_cases(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        for line_no, row in enumerate(csv.reader(source, delimiter="\t"), 1):
            if not row or row[0].startswith("#"):
                continue
            if len(row) != 5:
                raise ValueError(f"{path.name} 第 {line_no} 行必须有 5 列")
            yield row


def order_boundary_actual(args):
    day, minutes = parse_values(args, 2)
    service = Service()  # 每条单独边界用例从初始容量 600 开始。
    result = service.submit(100, 100, 100, 100, minutes, 0, 0, day)
    # 非法日期的用例检查基准日 0 未被改动。
    checked_day = day if 0 <= day <= 7 else 0
    return f"{result};COUNT={len(service.orders)};CAPACITY={service.remaining(checked_day)}"


def run_fixture(path: Path, output: Path, label: str, order_mode: bool = False) -> int:
    try:
        cases = list(read_cases(path))
        if not cases:
            raise ValueError(f"{path.name} 没有测试用例")
        if order_mode and any(row[2] != "order" for row in cases):
            raise ValueError("订单边界文件的 module 必须为 order")
        output.parent.mkdir(parents=True, exist_ok=True)
        total = passed = 0
        log = []
        with output.open("w", encoding="utf-8-sig", newline="") as destination:
            writer = csv.writer(destination, delimiter="\t")
            writer.writerow(FIELDS)
            for case_id, group, module, inputs, expected in cases:
                args = inputs.split(",")
                actual = order_boundary_actual(args) if order_mode else evaluate(module, args)
                ok = actual == expected
                total += 1
                passed += int(ok)
                status = "PASS" if ok else "FAIL"
                writer.writerow([case_id, group, module, inputs, expected, actual,
                                 status, "NONE" if ok else "OUTPUT_MISMATCH"])
                text = f"[{status}] {case_id} {module}({inputs}) => {actual}"
                if not ok:
                    text += f" | expected={expected}"
                print(text)
                log.append(text)
        summary = f"{label} total={total} passed={passed} failed={total - passed}"
        print(summary)
        log.append(summary)
        output.with_suffix(".log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
        return 0 if total == passed else 1
    except (OSError, ValueError) as error:
        print(f"测试文件错误：{error}")
        return 2


def run_integration(output_dir: Path) -> int:
    service = Service()
    rows = []

    def check(name, actual, expected):
        status = "PASS" if actual == expected else "FAIL"
        text = f"[{status}] {name} | expected={expected} | actual={actual}"
        print(text)
        rows.append((status, text))

    check("I01 first order", service.submit(100, 100, 100, 100, 120, 0, 0, 0),
          "ORDER=1;PRICE=26.00;REMAIN=480")
    check("I02 invalid size", service.submit(201, 100, 100, 100, 120, 0, 0, 0), "ERR_SIZE")
    check("I03 failed order preserves state", f"{service.remaining(0)},{len(service.orders)}", "480,1")
    check("I04 invalid quote", service.submit(100, 100, 100, 0, 120, 0, 0, 0), "ERR_QUOTE_RANGE")
    check("I05 invalid day", service.submit(100, 100, 100, 100, 120, 0, 0, 8), "ERR_BOOKING_RANGE")
    check("I06 overflow capacity", service.submit(100, 100, 100, 100, 481, 0, 0, 0), "REJECT_CAPACITY")
    check("I07 exact capacity", service.submit(100, 100, 100, 100, 480, 1, 1, 0),
          "ORDER=2;PRICE=81.00;REMAIN=0")
    check("I08 full day", service.submit(100, 100, 100, 100, 1, 0, 0, 0), "REJECT_CAPACITY")
    check("I09 maintenance on", service.set_maintenance(1, 1), "MAINTENANCE_UPDATED")
    check("I10 reject maintenance", service.submit(100, 100, 100, 100, 120, 0, 0, 1), "REJECT_MAINTENANCE")
    check("I11 maintenance preserves capacity", str(service.remaining(1)), "600")
    check("I12 maintenance off", service.set_maintenance(1, 0), "MAINTENANCE_UPDATED")
    check("I13 other day independent", service.submit(100, 100, 100, 1, 1, 0, 1, 1),
          "ORDER=3;PRICE=0.38;REMAIN=599")
    check("I14 invalid maintenance day", service.set_maintenance(8, 1), "ERR_MAINTENANCE_SETTING")
    check("I15 final state", f"{len(service.orders)},{service.remaining(0)},{service.remaining(1)}", "3,0,599")
    passed = sum(status == "PASS" for status, _ in rows)
    summary = f"INTEGRATION total={len(rows)} passed={passed} failed={len(rows) - passed}"
    print(summary)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "integration_log.txt").write_text(
            "\n".join(text for _, text in rows) + "\n" + summary + "\n", encoding="utf-8")
    except OSError as error:
        print(f"保存流程测试日志失败：{error}")
        return 2
    return 0 if passed == len(rows) else 1


def run_all() -> int:
    output_dir = ROOT / "results"
    codes = [
        run_fixture(ROOT / "data/test_cases.tsv", output_dir / "module_results.tsv", "MODULE"),
        run_fixture(ROOT / "data/order_boundary_cases.tsv", output_dir / "order_boundary_results.tsv",
                    "ORDER_BOUNDARY", order_mode=True),
        run_integration(output_dir),
    ]
    result = max(codes)
    text = "全部测试通过：115 条模块用例 + 22 次订单边界检查 + 15 项连续流程检查 = 152 次检查。" if result == 0 else "测试未全部通过，请查看日志中的 FAIL 或测试文件错误。"
    print("\n" + text)
    print("结果目录：" + str(output_dir))
    try:
        (output_dir / "summary.txt").write_text(text + "\n", encoding="utf-8")
    except OSError as error:
        print(f"保存汇总失败：{error}")
        return 2
    return result
