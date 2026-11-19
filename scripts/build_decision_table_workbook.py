"""根据决策表测试结果生成可筛选的 Excel 用例表。

运行顺序：
    python decision_table_runner.py
    python scripts/build_decision_table_workbook.py

默认输出到提交包的 02_测试用例/实验三_决策表测试用例.xlsx。
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "decision_table"
DEFAULT_OUTPUT = ROOT.parent / "02_测试用例" / "实验三_决策表测试用例.xlsx"

TITLE_FONT = Font(name="微软雅黑", size=16, bold=True, color="1F3864")
SUBTITLE_FONT = Font(name="微软雅黑", size=10, color="44546A")
HEADER_FONT = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name="微软雅黑", size=10, color="1F2933")
NOTE_FONT = Font(name="微软雅黑", size=9, color="6B7A8C")
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_ALT_FILL = PatternFill("solid", fgColor="2E75B6")
ZEBRA_FILL = PatternFill("solid", fgColor="F2F6FA")
PASS_FILL = PatternFill("solid", fgColor="E2EFDA")
PASS_FONT = Font(name="微软雅黑", size=10, bold=True, color="1E6B34")
FAIL_FILL = PatternFill("solid", fgColor="FCE4E4")
FAIL_FONT = Font(name="微软雅黑", size=10, bold=True, color="B02418")
THIN = Side(style="thin", color="BFC9D4")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def read_tsv(name: str) -> list[dict[str, str]]:
    path = RESULTS / name
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def write_title(ws, title: str, subtitle: str, width: int) -> None:
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=width)
    cell = ws.cell(row=1, column=1, value=title)
    cell.font = TITLE_FONT
    cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 30

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=width)
    cell = ws.cell(row=2, column=1, value=subtitle)
    cell.font = SUBTITLE_FONT
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[2].height = 30


def write_header(ws, row: int, headers: list[str]) -> None:
    for column, text in enumerate(headers, 1):
        cell = ws.cell(row=row, column=column, value=text)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = BORDER
    ws.row_dimensions[row].height = 26


def write_body(
    ws,
    start_row: int,
    rows: list[list[object]],
    center_columns: set[int] | None = None,
) -> None:
    center_columns = center_columns or set()
    for offset, values in enumerate(rows):
        row_index = start_row + offset
        for column, value in enumerate(values, 1):
            cell = ws.cell(row=row_index, column=column, value=value)
            cell.font = BODY_FONT
            cell.alignment = CENTER if column in center_columns else LEFT
            cell.border = BORDER
            if offset % 2 == 1:
                cell.fill = ZEBRA_FILL
        ws.row_dimensions[row_index].height = 24


def set_widths(ws, widths: list[float]) -> None:
    for index, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(index)].width = width


def add_note(ws, row: int, text: str, width: int) -> None:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=width)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = NOTE_FONT
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)


def build(output: Path) -> Path:
    cases = read_tsv("cases.tsv")
    combinations = read_tsv("combinations.tsv")
    rules = read_tsv("rules.tsv")
    manifest = json.loads((RESULTS / "evidence_manifest.json").read_text(encoding="utf-8"))
    summary = manifest["summary"]
    executed_at = manifest["executed_at"]
    python_version = manifest.get("python", "")

    wb = Workbook()

    # ---------- 摘要 ----------
    ws = wb.active
    ws.title = "摘要"
    ws.sheet_view.showGridLines = False
    write_title(
        ws,
        "实验三 决策表测试结果",
        "校园 3D 打印服务系统｜预约条件检查模块｜输入顺序：提前天数、时长、剩余容量、维护编码",
        8,
    )
    add_note(
        ws, 3,
        "本工作簿记录 16 种理论条件组合、4 种不可达组合、12 种可行组合、5 条化简规则及 12 条正式测试用例，"
        "数据由 decision_table_runner.py 自动执行后导出。",
        8,
    )

    ws["A5"] = "执行指标"
    ws["B5"] = "数值"
    ws["C5"] = "说明"
    for cell in ("A5", "B5", "C5"):
        ws[cell].font = HEADER_FONT
        ws[cell].fill = HEADER_FILL
        ws[cell].alignment = CENTER
        ws[cell].border = BORDER
    ws.merge_cells("D5:H5")
    ws["D5"] = "结论"
    ws["D5"].font = HEADER_FONT
    ws["D5"].fill = HEADER_FILL
    ws["D5"].alignment = CENTER
    ws["D5"].border = BORDER
    ws.merge_cells("D6:H13")
    ws["D6"] = (
        "12 种可行条件组合均执行了决策表规定的动作，范围错误、维护编码错误、"
        "维护拒绝和容量拒绝的优先级与用例一致。本轮未发现业务代码缺陷；"
        "发现并修正的是决策表初稿对不可达组合的处理错误。"
    )
    ws["D6"].font = BODY_FONT
    ws["D6"].alignment = LEFT
    ws["D6"].border = BORDER

    metrics = [
        ("理论条件组合", "=COUNTA('决策表'!A6:A21)", "4 个二值条件共 16 种组合"),
        ("不可达组合", "=COUNTIF('决策表'!F6:F21,\"N\")", "维护编码非法时不可能同时处于维护中"),
        ("可行条件组合", "=COUNTIF('决策表'!F6:F21,\"Y\")", "不可达组合之外的 12 种组合"),
        ("化简规则", "=COUNTA('化简规则'!A6:A10)", "按动作与无关条件合并"),
        ("正式用例", "=COUNTA('测试用例'!A6:A17)", "每条可行组合对应一条用例"),
        ("通过", "=COUNTIF('测试用例'!L6:L17,\"PASS\")", "实际结果与决策表动作一致"),
        ("失败", "=COUNTIF('测试用例'!L6:L17,\"FAIL\")", "未发现失败项"),
    ]
    for offset, (name, formula, detail) in enumerate(metrics):
        row = 6 + offset
        ws.cell(row=row, column=1, value=name).font = BODY_FONT
        ws.cell(row=row, column=1).alignment = LEFT
        ws.cell(row=row, column=2, value=formula).font = BODY_FONT
        ws.cell(row=row, column=2).alignment = CENTER
        ws.cell(row=row, column=3, value=detail).font = BODY_FONT
        ws.cell(row=row, column=3).alignment = LEFT
        for column in (1, 2, 3, 4):
            ws.cell(row=row, column=column).border = BORDER
        ws.row_dimensions[row].height = 30

    write_header(ws, 15, ["规则", "条件摘要", "动作", "覆盖组合数", "用途"])
    write_body(
        ws,
        16,
        [[rule["rule_id"], rule["conditions"], rule["action"],
          int(rule["raw_count"]), rule["purpose"]] for rule in rules],
        {1, 4},
    )
    add_note(
        ws, 22,
        f"数据来源：decision_table_runner.py 自动执行结果，运行时间 {executed_at}，"
        f"Python {python_version}。判定列 PASS 表示实际结果与决策表动作一致。",
        8,
    )
    set_widths(ws, [18, 28, 36, 16, 12, 12, 12, 12])

    # ---------- 决策表 ----------
    ws = wb.create_sheet("决策表")
    ws.sheet_view.showGridLines = False
    write_title(
        ws,
        "完整决策表与可达性检查",
        "C1 三个数值输入均在规定范围内；C2 维护编码为 0 或 1；C3 设备处于维护状态；"
        "C4 请求时长不超过剩余容量。",
        10,
    )
    headers = ["组合编号", "C1", "C2", "C3", "C4", "可达", "动作", "化简规则", "对应用例", "可达性证明输入"]
    write_header(ws, 5, headers)
    write_body(
        ws,
        6,
        [[item["id"], item["C1"], item["C2"], item["C3"], item["C4"], item["possible"],
          item["action"], item["rule_id"] or "-", item["covered_by"] or "-",
          item["witness"] or "不可达"] for item in combinations],
        set(range(2, 11)),
    )
    for offset, item in enumerate(combinations):
        if item["possible"] == "N":
            for column in range(1, 11):
                ws.cell(row=6 + offset, column=column).fill = PatternFill("solid", fgColor="EDEDED")
    ws.auto_filter.ref = f"A5:J{5 + len(combinations)}"
    ws.freeze_panes = "A6"
    add_note(
        ws, 7 + len(combinations),
        "维护编码不是 0 或 1 时，输入不可能同时表示设备处于维护中，因此 C2=N 且 C3=Y 的"
        " RC03、RC04、RC11、RC12 不可达，不计入规则数和测试覆盖。证明输入为执行器构造的最小输入。",
        10,
    )
    set_widths(ws, [13, 7, 7, 7, 7, 8, 24, 11, 11, 22])

    # ---------- 化简规则 ----------
    ws = wb.create_sheet("化简规则")
    ws.sheet_view.showGridLines = False
    write_title(
        ws,
        "化简后的决策规则",
        "动作相同、仅无关条件不同的组合合并为一条规则；无关条件不计入规则匹配。",
        6,
    )
    write_header(ws, 5, ["规则", "条件摘要", "动作", "覆盖原始组合数", "规则说明"])
    write_body(
        ws,
        6,
        [[rule["rule_id"], rule["conditions"], rule["action"],
          int(rule["raw_count"]), rule["name"]] for rule in rules],
        {1, 4},
    )
    add_note(
        ws, 12,
        "R1 覆盖 6 种可达组合，R2 覆盖 2 种，R3 覆盖 2 种，R4 和 R5 各覆盖 1 种，合计 12，"
        "没有遗漏。规则之间没有相同的条件交集，也没有对同一可达组合给出不同动作。",
        6,
    )
    set_widths(ws, [10, 40, 26, 16, 18])

    # ---------- 测试用例 ----------
    ws = wb.create_sheet("测试用例")
    ws.sheet_view.showGridLines = False
    write_title(
        ws,
        "决策表测试用例与执行结果",
        "每一条可行条件组合对应一条用例；同一动作的多个组合保留不同输入，用于确认化简没有掩盖动作差异。",
        13,
    )
    headers = ["用例编号", "原始组合", "化简规则", "规则名称", "C1", "C2", "C3", "C4",
               "输入", "预计结果", "实际结果", "判定", "说明"]
    write_header(ws, 5, headers)
    write_body(
        ws,
        6,
        [[case["id"], case["raw_rule"], case["rule_id"], case["rule_name"],
          case["C1"], case["C2"], case["C3"], case["C4"], case["inputs"],
          case["expected"], case["actual"], case["status"], case["note"]] for case in cases],
        set(range(1, 9)) | {12},
    )
    for offset, case in enumerate(cases):
        row = 6 + offset
        status = ws.cell(row=row, column=12)
        if case["status"] == "PASS":
            status.fill = PASS_FILL
            status.font = PASS_FONT
        else:
            status.fill = FAIL_FILL
            status.font = FAIL_FONT
    ws.auto_filter.ref = f"A5:M{5 + len(cases)}"
    ws.freeze_panes = "A6"
    add_note(
        ws, 7 + len(cases),
        "DT-01 至 DT-06 把 C1 置为 N，验证范围错误优先；DT-07、DT-08 验证维护编码错误；"
        "DT-09、DT-10 验证维护拒绝优先于容量判断；DT-11、DT-12 验证容量边界。",
        13,
    )
    set_widths(ws, [12, 11, 10, 15, 6, 6, 6, 6, 16, 22, 22, 10, 32])

    # ---------- 证据索引 ----------
    ws = wb.create_sheet("证据索引")
    ws.sheet_view.showGridLines = False
    write_title(
        ws,
        "逐用例执行证据索引",
        "截图为 Windows 命令提示符中执行 decision_table_runner.py 后捕获的窗口；"
        "用例编号与报告一致。",
        6,
    )
    write_header(ws, 5, ["用例编号", "化简规则", "结果", "截图文件", "说明"])
    evidence_rows = [
        [case["id"], case["rule_id"], case["status"], f"{case['id']}.png", case["note"]]
        for case in cases
    ]
    evidence_rows.append(["SUMMARY", "R1~R5", "PASS", "SUMMARY.png", "全部 12 条用例汇总"])
    write_body(ws, 6, evidence_rows, {1, 2, 3})
    ws.auto_filter.ref = f"A5:E{5 + len(evidence_rows)}"
    add_note(
        ws, 8 + len(evidence_rows),
        "截图与 run_log.txt、cases.tsv 使用同一组用例编号；13 张图片位于 "
        "04_测试结果/results/decision_table/screenshots。",
        6,
    )
    set_widths(ws, [12, 11, 9, 17, 46])

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="生成实验三决策表测试用例工作簿")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    path = build(args.output)
    print(f"工作簿已生成：{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
