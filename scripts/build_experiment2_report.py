"""生成实验二等价类测试报告 DOCX。"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "实验二"
MANIFEST_PATH = ROOT / "results" / "equivalence" / "evidence_manifest.json"
SCREENSHOT_DIR = ROOT / "results" / "equivalence" / "screenshots"
OUTPUT_PATH = OUTPUT_DIR / "实验二_等价类测试报告.docx"

MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
FORMAL_CASES = MANIFEST["formal_cases"]
SUPPLEMENTARY_CASES = MANIFEST["supplementary_cases"]
CLASSES = MANIFEST["classes"]
FORMAL_BY_ID = {item["id"]: item for item in FORMAL_CASES}
SUPPLEMENTARY_BY_ID = {item["id"]: item for item in SUPPLEMENTARY_CASES}

FONT_BODY = "SimSun"
FONT_HEADING = "Microsoft YaHei"
FONT_MONO = "Consolas"
BLACK = RGBColor(0, 0, 0)
WHITE = RGBColor(255, 255, 255)
NAVY = "17324D"
BLUE = "2F6B8A"
PALE_BLUE = "EAF2F7"
PALE_GRAY = "F5F7F9"
MID_GRAY = "D9E0E5"
TEXT = RGBColor(30, 41, 51)
MUTED = RGBColor(97, 112, 126)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = tc_pr.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        tc_pr.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=90, bottom=90, end=90) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color=MID_GRAY, size="6") -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = borders.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), size)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)


def repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def prevent_row_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    cant_split.set(qn("w:val"), "true")
    tr_pr.append(cant_split)


def remove_paragraph_borders(paragraph_element) -> None:
    p_pr = paragraph_element.get_or_add_pPr()
    borders = p_pr.find(qn("w:pBdr"))
    if borders is not None:
        p_pr.remove(borders)


def set_run_font(run, name: str, size: float | None = None, bold: bool | None = None,
                 color: RGBColor | None = None) -> None:
    run.font.name = name
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    r_fonts.set(qn("w:ascii"), name)
    r_fonts.set(qn("w:hAnsi"), name)
    r_fonts.set(qn("w:eastAsia"), name)


def style_paragraph(style, font_name: str, size: float, bold: bool = False) -> None:
    style.font.name = font_name
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = BLACK
    style._element.rPr.rFonts.set(qn("w:ascii"), font_name)
    style._element.rPr.rFonts.set(qn("w:hAnsi"), font_name)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)


def add_text(doc: Document, text: str, *, style: str | None = None,
             bold_lead: str | None = None, align=None, indent=True,
             space_after=5, keep_with_next=False) -> object:
    paragraph = doc.add_paragraph(style=style)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.35
    paragraph.paragraph_format.keep_with_next = keep_with_next
    if align is not None:
        paragraph.alignment = align
    elif indent and style is None:
        paragraph.paragraph_format.first_line_indent = Pt(21)
    if bold_lead:
        lead = paragraph.add_run(bold_lead)
        set_run_font(lead, FONT_HEADING, 10.5, True, BLACK)
    run = paragraph.add_run(text)
    set_run_font(run, FONT_BODY, 10.5, False, TEXT)
    return paragraph


def add_heading(doc: Document, text: str, level: int) -> object:
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run(text)
    size = {1: 16, 2: 13, 3: 11.5}.get(level, 11)
    set_run_font(run, FONT_HEADING, size, True, BLACK)
    return paragraph


def add_caption(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(8)
    paragraph.paragraph_format.keep_with_next = False
    run = paragraph.add_run(text)
    set_run_font(run, FONT_HEADING, 8.5, False, MUTED)


def add_table_caption(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_before = Pt(7)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    set_run_font(run, FONT_HEADING, 8.8, True, MUTED)


def format_table(table, widths: list[float], font_size: float = 8.3,
                 center_cols: set[int] | None = None,
                 header_size: float | None = None) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    center_cols = center_cols or set()
    for row_index, row in enumerate(table.rows):
        prevent_row_split(row)
        for col_index, cell in enumerate(row.cells):
            cell.width = Inches(widths[col_index])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell)
            if row_index == 0:
                set_cell_shading(cell, NAVY)
            elif row_index % 2 == 0:
                set_cell_shading(cell, PALE_GRAY)
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.05
                if col_index in center_cols or row_index == 0:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    set_run_font(
                        run,
                        FONT_MONO if col_index == 0 else FONT_HEADING,
                        header_size if row_index == 0 and header_size else font_size,
                        row_index == 0,
                        WHITE if row_index == 0 else TEXT,
                    )
    repeat_table_header(table.rows[0])


def add_table(doc: Document, headers: list[str], rows: list[list[object]],
              widths: list[float], *, font_size=8.3,
              center_cols: set[int] | None = None) -> object:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        table.rows[0].cells[index].text = str(header)
    for values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cells[index].text = "" if value is None else str(value)
    format_table(table, widths, font_size=font_size, center_cols=center_cols)
    return table


def add_image_with_caption(doc: Document, image_path: Path, caption: str,
                           width_inches: float = 6.2) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run()
    inline_shape = run.add_picture(str(image_path), width=Inches(width_inches))
    doc_pr = inline_shape._inline.docPr
    doc_pr.set("descr", caption)
    doc_pr.set("title", caption)
    add_caption(doc, caption)


def add_page_break(doc: Document) -> None:
    paragraph = doc.add_paragraph()
    paragraph.add_run().add_break(WD_BREAK.PAGE)


def case_rows(method: str) -> list[list[str]]:
    rows = []
    for item in FORMAL_CASES:
        if item["method"] != method:
            continue
        actual = item["actual"] if item["status"] != "PASS" else "与预期一致"
        rows.append([
            item["id"],
            item["module_name"],
            item["inputs"],
            item["expected"],
            actual,
            item["status"],
            item["covers"],
        ])
    return rows


def build_document() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = Document()
    doc.core_properties.title = "实验二 等价类测试报告"
    doc.core_properties.subject = "校园 3D 打印服务系统等价类测试"
    doc.core_properties.author = "课程实验小组"
    doc.core_properties.keywords = "软件测试, 等价类, 弱一般, 强一般, 弱健壮"

    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    styles = doc.styles
    style_paragraph(styles["Normal"], FONT_BODY, 10.5)
    styles["Normal"].paragraph_format.line_spacing = 1.35
    styles["Normal"].paragraph_format.space_after = Pt(5)
    style_paragraph(styles["Title"], FONT_HEADING, 24, True)
    style_paragraph(styles["Heading 1"], FONT_HEADING, 16, True)
    style_paragraph(styles["Heading 2"], FONT_HEADING, 13, True)
    style_paragraph(styles["Heading 3"], FONT_HEADING, 11.5, True)
    remove_paragraph_borders(styles["Title"]._element)

    # Cover
    for _ in range(4):
        doc.add_paragraph()
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(10)
    set_run_font(title.add_run("实验二 等价类测试报告"), FONT_HEADING, 24, True, BLACK)
    remove_paragraph_borders(title._p)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(38)
    set_run_font(
        subtitle.add_run("校园 3D 打印服务系统"),
        FONT_HEADING,
        16,
        False,
        BLACK,
    )

    metadata = [
        ("课程名称", "软件测试实践与方法"),
        ("实验项目", "等价类测试"),
        ("专业班级", "________________"),
        ("小组编号", "________________"),
        ("成员姓名与学号", "________________"),
        ("完成日期", "2026 年 10 月 27 日"),
    ]
    meta_table = doc.add_table(rows=len(metadata), cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    for index, (label, value) in enumerate(metadata):
        left, right = meta_table.rows[index].cells
        left.width = Inches(1.8)
        right.width = Inches(3.6)
        left.text = label
        right.text = value
        for cell, bold in ((left, True), (right, False)):
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=125, bottom=125)
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs:
                    set_run_font(run, FONT_HEADING, 11, bold, BLACK)
    set_table_borders(meta_table, color="FFFFFF", size="0")
    repeat_table_header(meta_table.rows[0])
    add_page_break(doc)

    # Executive summary
    add_heading(doc, "摘要", 1)
    add_text(
        doc,
        "本报告记录校园 3D 打印服务系统的等价类测试过程。被测系统包含模型尺寸检查、"
        "打印费用计算、预约条件检查和完整订单四个功能模块。测试依据输入范围、离散编码"
        "和业务状态划分等价类，并分别采用弱一般、强一般和弱健壮等价类方法设计用例。",
    )
    add_text(
        doc,
        "测试共划分 57 个等价类，其中包括 24 个有效类和 33 个无效类。三类方法共设计"
        "58 条正式用例，并补充 5 条输入格式检查和 10 条跨模块流程检查。最终执行"
        "73 项检查，73 项全部通过；原有 152 项边界值检查也在修改后回归通过，"
        "合计 225 项检查全部通过。",
    )
    add_text(
        doc,
        "测试过程中发现两处新增流程用例的预期金额计算错误。核对业务公式后确认被测程序"
        "输出了正确的 45.00 元，原测试数据误写为 35.00 元。修正测试预期并重新执行后，"
        "所有检查通过。本轮测试未发现程序功能缺陷，未修改业务代码。",
    )
    add_text(doc, "关键词：等价类划分；弱一般等价类；强一般等价类；弱健壮等价类；软件测试", indent=False)

    add_heading(doc, "1 实验目的", 1)
    add_text(
        doc,
        "本次实验使用实验一已完成的 3D 打印服务系统，检查各功能模块对正常输入、边界外输入"
        "和异常编码的处理是否符合规格。测试重点不在重复执行边界值用例，而在依据规格识别"
        "有效与无效等价类，比较三种等价类方法在用例数量、输入组合和异常覆盖方面的差异。",
    )
    for text in [
        "掌握按输入范围、离散编码和业务状态划分等价类的方法。",
        "能够依据弱一般、强一般和弱健壮等价类方法构造可执行测试用例。",
        "能够记录输入、预期结果、实际结果和覆盖的等价类，并通过截图保留执行证据。",
        "能够区分程序缺陷与测试数据错误，完成修改前后的验证。",
    ]:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.line_spacing = 1.25
        set_run_font(paragraph.add_run(text), FONT_BODY, 10.5, False, TEXT)

    add_heading(doc, "2 被测系统与模块规格", 1)
    add_heading(doc, "2.1 系统入口与运行方式", 2)
    add_text(
        doc,
        "项目入口为 main.py，交互菜单提供尺寸检查、费用计算、预约条件检查、完整订单、"
        "查看订单及容量、设置维护状态和自动测试等功能。实验二的等价类测试通过新增的"
        "equivalence_test_runner.py 执行，不改变实验一原有的 run_tests.py。",
    )
    add_text(
        doc,
        "运行环境为 Windows、Python 3.14.6，仅使用 Python 标准库。正式测试命令为"
        "“python equivalence_test_runner.py”，原有回归测试命令为“python run_tests.py”。",
    )

    add_heading(doc, "2.2 模块规格", 2)
    add_table_caption(doc, "表 2-1 功能模块规格")
    spec_rows = [
        [
            "尺寸检查",
            "长、宽、高",
            "三个尺寸均为 1～200 mm",
            "SIZE_OK；越界返回 ERR_SIZE",
            "无状态变化",
        ],
        [
            "费用计算",
            "重量、时长、材料、加急",
            "重量 1～500 g；时长 1～600 min；材料 0/1；加急 0/1",
            "PRICE；分别返回 ERR_QUOTE_RANGE、ERR_MATERIAL、ERR_URGENT",
            "无状态变化",
        ],
        [
            "预约条件检查",
            "提前天数、时长、剩余容量、维护状态",
            "天数 0～7；时长 1～600；容量 0～600；维护 0/1",
            "BOOKING_OK；范围、维护或容量错误分别返回",
            "检查函数本身不扣减容量",
        ],
        [
            "完整订单",
            "八项订单输入及设备状态",
            "依次检查尺寸、报价、日期、维护和容量",
            "订单编号、金额和剩余容量；失败返回对应错误码",
            "成功后记录订单并扣减容量",
        ],
    ]
    add_table(
        doc,
        ["模块", "主要输入", "有效条件", "输出与异常", "状态影响"],
        spec_rows,
        [0.72, 1.35, 2.1, 2.05, 0.88],
        font_size=8.0,
        center_cols={0},
    )

    add_heading(doc, "2.3 业务状态与检查顺序", 2)
    add_text(
        doc,
        "系统为提前 0～7 天分别维护 600 分钟容量和维护状态。完整订单先检查尺寸，再检查"
        "重量、时长、材料和加急，随后检查提前天数，最后检查维护状态与剩余容量。订单失败"
        "不得改变容量、订单编号或订单记录。设备维护和容量不足同时发生时，系统优先返回维护拒绝。",
    )
    add_text(
        doc,
        "输入解析层要求数字为 32 位有符号整数。小数、字母、超范围整数和参数数量错误在"
        "进入业务函数前被拒绝。离散编码材料、加急和维护状态只接受 0 或 1。",
    )

    add_heading(doc, "3 等价类划分", 1)
    add_heading(doc, "3.1 划分原则", 2)
    add_text(
        doc,
        "对连续范围变量，以一个区间有效类、区间下方无效类和区间上方无效类进行划分。"
        "对只接受指定编码的离散变量，每个允许值单独作为有效类，其他整数归入一个无效类。"
        "完整订单沿用各模块变量，并增加订单状态的流程检查。",
    )
    add_text(
        doc,
        "每个等价类使用唯一编号。有效类以 V 开头，无效类以 I 开头；编号中的模块字母分别为"
        "S（尺寸）、Q（报价）、B（预约）和 O（订单）。测试用例覆盖关系记录在测试结果表和"
        "随附 Excel 中，避免只检查输出而遗漏覆盖依据。",
    )

    add_heading(doc, "3.2 无效等价类处理", 2)
    add_text(
        doc,
        "设计无效等价类用例时，每个用例只引入一个无效输入，其余变量保持有效。这样能够把"
        "失败原因归到唯一输入，符合弱健壮等价类“单缺陷”原则。多输入同时非法的检查只用于"
        "验证错误检查顺序，不纳入正式等价类用例数量。",
    )

    add_heading(doc, "3.3 等价类划分结果", 2)
    class_counts: dict[str, Counter] = {}
    for module in ("size", "quote", "booking", "order"):
        class_counts[module] = Counter(
            item["kind"] for item in CLASSES if item["module"] == module
        )
    add_table_caption(doc, "表 3-1 各模块等价类数量")
    module_names = {
        "size": "尺寸检查",
        "quote": "费用计算",
        "booking": "预约条件检查",
        "order": "完整订单",
    }
    rows = []
    for module in ("size", "quote", "booking", "order"):
        rows.append([
            module_names[module],
            class_counts[module]["有效"],
            class_counts[module]["无效"],
            class_counts[module]["有效"] + class_counts[module]["无效"],
        ])
    rows.append([
        "合计",
        sum(class_counts[m]["有效"] for m in class_counts),
        sum(class_counts[m]["无效"] for m in class_counts),
        len(CLASSES),
    ])
    add_table(
        doc,
        ["模块", "有效等价类", "无效等价类", "合计"],
        rows,
        [2.3, 1.25, 1.25, 1.1],
        font_size=9,
        center_cols={0, 1, 2, 3},
    )
    add_text(
        doc,
        "尺寸模块和预约模块都包含多个范围变量；报价模块和完整订单还包含材料、加急等离散编码。"
        "完整订单的直接输入等价类为 10 个有效类和 14 个无效类，另外通过流程测试验证"
        "维护状态和容量状态。",
    )

    add_heading(doc, "4 测试用例设计过程", 1)
    add_heading(doc, "4.1 弱一般等价类设计", 2)
    add_text(
        doc,
        "弱一般等价类只覆盖正常输入。对于 n 个变量，如果第 i 个变量的有效类数量为 m_i，"
        "最少用例数为 max(m_i)。尺寸模块三个变量各有一个有效类，只需 1 条用例；费用计算"
        "和预约检查因离散编码有两个有效值，各需 2 条用例；完整订单也需 2 条正常用例。",
    )
    add_text(
        doc,
        "这组用例用于确认正常流程能够产生规格要求的输出，不用于证明异常输入处理正确。"
        "例如费用计算分别使用 PLA+不加急、PETG+加急两个正常组合，以覆盖材料和加急的全部"
        "有效类。",
    )

    add_heading(doc, "4.2 强一般等价类设计", 2)
    add_text(
        doc,
        "强一般等价类覆盖所有变量的正常等价类组合。用例数为各变量有效类数量的乘积。"
        "尺寸检查只有 1 种正常组合；费用计算和完整订单各有 4 种材料×加急组合；预约检查"
        "有 2 种维护状态组合，因此正式用例总数为 11 条。",
    )
    add_text(
        doc,
        "该方法能发现变量交互引起的错误。例如某些报价只在 PETG 与加急组合时出现舍入或"
        "倍率错误，单靠弱一般用例不一定能触发。强一般方法仍不覆盖异常输入。",
    )

    add_heading(doc, "4.3 弱健壮等价类设计", 2)
    add_text(
        doc,
        "弱健壮等价类先保留覆盖全部有效类所需的正常用例，再为每个无效等价类增加一条"
        "单缺陷用例。用例数为最大有效类数量与各变量无效类数量之和。最终尺寸模块 7 条、"
        "费用计算 8 条、预约检查 9 条、完整订单 16 条，共 40 条。",
    )
    add_text(
        doc,
        "无效输入分别覆盖范围下方、范围上方和非法离散编码。完整订单另检查错误输入不会"
        "产生订单或改变容量。每个无效类仅在弱健壮用例集中出现一次，避免重复用例虚增覆盖数量。",
    )

    add_heading(doc, "4.4 覆盖检查", 2)
    method_rows = [
        [
            item["method_name"],
            item["total"],
            item["passed"],
            "全部有效类" if item["method"] != "weak_robust" else "全部有效类和无效类",
        ]
        for item in MANIFEST["method_summary"]
    ]
    add_table_caption(doc, "表 4-1 三类方法覆盖目标")
    add_table(
        doc,
        ["方法", "正式用例", "通过", "覆盖范围"],
        method_rows,
        [1.55, 1.0, 0.8, 2.4],
        font_size=9,
        center_cols={0, 1, 2},
    )
    add_text(
        doc,
        "执行器在设计阶段校验有效类覆盖集合、无效类覆盖集合和三类方法数量。弱一般、"
        "强一般都必须覆盖全部 24 个有效类；弱健壮必须覆盖全部 57 个等价类，且 33 个"
        "无效类各出现一次。覆盖校验失败时，执行器在运行测试前终止。",
    )

    add_heading(doc, "5 测试执行结果", 1)
    add_heading(doc, "5.1 执行环境", 2)
    env_rows = [
        ["被测项目", "校园 3D 打印服务系统 Python 版"],
        ["原始版本", "Git 标签 experiment1-baseline，提交 6c450bd"],
        ["实验分支", "experiment2-equivalence-testing"],
        ["运行环境", f"Windows；Python {MANIFEST['python']}"],
        ["执行时间", MANIFEST["executed_at"]],
        ["执行入口", "equivalence_test_runner.py"],
    ]
    add_table(doc, ["项目", "内容"], env_rows, [1.45, 5.05], font_size=9)

    add_heading(doc, "5.2 测试结果摘要", 2)
    totals = MANIFEST["totals"]
    result_rows = [
        [item["method_name"], item["total"], item["passed"], item["failed"]]
        for item in MANIFEST["method_summary"]
    ]
    result_rows.extend([
        ["输入格式补充检查", 5, 5, 0],
        ["跨模块流程补充检查", 10, 10, 0],
        ["合计", totals["all"], totals["all_passed"], totals["all"] - totals["all_passed"]],
    ])
    add_table_caption(doc, "表 5-1 新增测试执行汇总")
    add_table(
        doc,
        ["测试类别", "用例数", "通过", "失败"],
        result_rows,
        [3.0, 1.0, 1.0, 1.0],
        font_size=9,
        center_cols={0, 1, 2, 3},
    )
    add_text(
        doc,
        "58 条正式等价类用例全部通过，15 条补充检查也全部通过。原有回归测试的 115 条"
        "模块用例、22 次订单边界检查和 15 项连续流程检查均保持通过。",
    )

    add_heading(doc, "5.3 回归结果", 2)
    add_text(
        doc,
        "本轮没有修改业务代码，因此实验二新增测试和实验一原有测试可以共同证明当前版本"
        "行为一致。原测试覆盖边界值、订单状态和连续流程，新增测试覆盖正常类、正常组合和"
        "单缺陷异常类，两类证据相互补充。",
    )
    add_text(
        doc,
        "新增测试日志位于 results/equivalence/run_log.txt，逐用例截图位于"
        " results/equivalence/screenshots，测试用例与覆盖关系位于"
        " 实验二_等价类测试用例.xlsx。",
    )

    add_page_break(doc)
    add_heading(doc, "5.4 代表性执行截图", 2)
    selected = [
        ("WG-S-01", "弱一般正常尺寸用例"),
        ("SG-Q-04", "强一般 PETG 加急组合用例"),
        ("WR-B-09", "弱健壮维护编码无效用例"),
        ("WR-O-16", "弱健壮订单天数越界用例"),
        ("FLOW-04", "维护拒绝优先于容量不足"),
        ("FLOW-08", "失败订单保持容量与记录不变"),
    ]
    figure_number = 1
    for index, (case_id, title) in enumerate(selected):
        image_path = SCREENSHOT_DIR / f"{case_id}.png"
        add_image_with_caption(
            doc,
            image_path,
            f"图 5-{figure_number} {case_id} {title}执行证据",
            width_inches=5.9,
        )
        figure_number += 1
        if index in (1, 3):
            add_page_break(doc)
    add_text(
        doc,
        "本报告仅展示 6 张代表性截图。全部 73 张截图均按测试用例编号命名，并与"
        " “证据索引”工作表和执行结果逐项对应。",
    )

    add_heading(doc, "6 错误记录与修改验证", 1)
    add_text(
        doc,
        "首轮执行正式用例时，58 条正式用例全部通过；补充流程用例 FLOW-04 和 FLOW-05"
        " 出现失败。两条用例的实际首单金额均为 45.00 元，而测试数据预期为 35.00 元。",
    )
    error_rows = [
        [
            "FLOW-04",
            "首单预期 35.00 元，实际 45.00 元",
            "100 g PLA 为 20.00 元，500 min 机时为 25.00 元，合计 45.00 元；预期漏算机时费",
            "将预期改为 45.00 元，业务代码保持不变",
            "重跑后 PASS",
        ],
        [
            "FLOW-05",
            "首单预期 35.00 元，实际 45.00 元",
            "与 FLOW-04 相同的首单输入，测试预期计算错误",
            "将预期改为 45.00 元，业务代码保持不变",
            "重跑后 PASS",
        ],
    ]
    add_table_caption(doc, "表 6-1 测试执行中的错误记录")
    add_table(
        doc,
        ["用例", "现象", "原因分析", "修改方法", "验证"],
        error_rows,
        [0.7, 1.25, 2.1, 1.5, 0.9],
        font_size=7.8,
        center_cols={0},
    )
    add_text(
        doc,
        "上述问题属于测试预期计算错误，不属于被测程序缺陷。修正后重新执行新增测试，"
        "73 项全部通过；随后执行原有 run_tests.py，152 项检查全部通过。最终测试结论以"
        "修改后的测试数据为准。",
    )

    add_heading(doc, "7 方法比较与结论", 1)
    compare_rows = [
        ["弱一般", "7", "全部有效类", "只使用正常值", "用例最少，缺少异常输入验证"],
        ["强一般", "11", "全部正常组合", "覆盖材料与加急等组合", "能发现变量交互问题，数量高于弱一般"],
        ["弱健壮", "40", "全部有效类和无效类", "每个无效类对应一条单缺陷用例", "异常覆盖最完整，用例数量最大"],
    ]
    add_table_caption(doc, "表 7-1 三种等价类方法比较")
    add_table(
        doc,
        ["方法", "用例数", "输入覆盖", "组合方式", "适用判断"],
        compare_rows,
        [0.85, 0.75, 1.4, 1.7, 1.8],
        font_size=8.2,
        center_cols={0, 1},
    )
    add_text(
        doc,
        "从用例数量看，弱一般最少，强一般次之，弱健壮最多。从异常输入覆盖看，弱一般和"
        "强一般只覆盖正常类，弱健壮覆盖全部无效类。强一般的主要价值在于验证多个正常"
        "变量组合，弱健壮的主要价值在于验证范围外输入和非法编码的系统处理。",
    )
    add_text(
        doc,
        "本次测试最终结果为 57 个等价类全部覆盖，58 条正式用例和 15 条补充检查全部通过，"
        "未发现程序功能缺陷。测试数据错误已修正并完成回归，当前版本满足实验一的业务规格。",
    )

    add_heading(doc, "8 小组分工与协作", 1)
    division_rows = [
        ["成员一（姓名待填）", "尺寸检查", "划分尺寸变量等价类，设计尺寸三类方法用例，核对尺寸执行结果"],
        ["成员二（姓名待填）", "费用计算", "划分重量、时长、材料和加急等价类，校验报价公式与金额"],
        ["成员三（姓名待填）", "预约检查", "划分日期、时长、容量和维护状态等价类，验证拒绝优先级"],
        ["成员四（姓名待填）", "完整订单与汇总", "设计订单及流程用例，维护测试执行器，汇总日志、截图和报告"],
    ]
    add_table_caption(doc, "表 8-1 小组分工")
    add_table(
        doc,
        ["成员", "负责模块", "具体任务"],
        division_rows,
        [1.45, 1.2, 3.85],
        font_size=8.6,
        center_cols={0, 1},
    )
    add_text(
        doc,
        "各模块通过统一测试执行器合并。成员一至成员三分别核对自己模块的等价类、预期结果"
        "和执行日志，成员四核对订单状态变化及三类方法的覆盖数量。合并后的测试结果、"
        "Excel 用例表和逐项截图共同作为提交依据。",
    )

    add_heading(doc, "9 个人实验心得", 1)
    add_text(
        doc,
        "本页由各成员本人独立填写。每份心得应结合本人负责的模块、实际遇到的问题和与组员的"
        "讨论过程，不能复制其他成员的内容。以下保留四项独立填写区。",
    )
    reflections = [
        "成员一（姓名：________）：",
        "成员二（姓名：________）：",
        "成员三（姓名：________）：",
        "成员四（姓名：________）：",
    ]
    prompts = [
        "可填写：尺寸等价类划分中如何确定两个越界类、如何使用弱健壮用例验证尺寸下限和上限，以及本人对三个变量组合覆盖的理解。",
        "可填写：如何把材料、加急和费用公式转换为正常组合，如何核对加急费用和最终舍入，以及测试预期与程序输出不一致时的排查过程。",
        "可填写：如何区分日期、时长、剩余容量和维护状态，如何验证维护拒绝与容量不足的优先级，以及单缺陷用例的设计理由。",
        "可填写：如何把前三个模块组合到完整订单，如何验证失败后状态不变、容量扣减和订单编号递增，以及测试结果汇总中的协作经验。",
    ]
    for label, prompt in zip(reflections, prompts):
        add_heading(doc, label, 2)
        add_text(doc, prompt, indent=False)
        for _ in range(4):
            paragraph = doc.add_paragraph("＿" * 47)
            paragraph.paragraph_format.space_after = Pt(7)
            for run in paragraph.runs:
                set_run_font(run, FONT_BODY, 10, False, RGBColor(120, 130, 140))
        if label.startswith("成员二"):
            add_page_break(doc)

    # Appendix A: formal cases
    add_page_break(doc)
    add_heading(doc, "附录 A 正式等价类测试用例", 1)
    add_text(
        doc,
        "完整实际结果与截图按编号保存。表中“实际结果”为“与预期一致”时，表示实际输出"
        "与预期字符串完全相同。",
    )
    method_order = [
        ("weak_general", "A.1 弱一般等价类用例"),
        ("strong_general", "A.2 强一般等价类用例"),
        ("weak_robust", "A.3 弱健壮等价类用例"),
    ]
    for method, title_text in method_order:
        add_heading(doc, title_text, 2)
        rows = case_rows(method)
        add_table(
            doc,
            ["编号", "模块", "输入", "预期结果", "实际结果", "判定", "覆盖等价类"],
            rows,
            [0.58, 0.56, 1.0, 1.72, 0.8, 0.43, 1.31],
            font_size=6.9,
            center_cols={0, 1, 5},
        )
        if method != "weak_robust":
            add_page_break(doc)

    # Appendix B: equivalence classes
    add_page_break(doc)
    add_heading(doc, "附录 B 等价类划分清单", 1)
    class_rows = [
        [
            item["id"],
            item["module_name"],
            item["variable"],
            item["kind"],
            item["rule"],
            item["representative"],
            item["covered_by"]
            .replace("weak_general", "G")
            .replace("strong_general", "S")
            .replace("weak_robust", "R"),
        ]
        for item in CLASSES
    ]
    add_table(
        doc,
        ["编号", "模块", "变量", "类型", "划分规则", "代表值", "覆盖"],
        class_rows,
        [0.62, 0.64, 0.64, 0.45, 2.56, 0.58, 0.61],
        font_size=7.4,
        center_cols={0, 1, 2, 3, 5, 6},
    )
    add_text(
        doc,
        "覆盖列中 G 表示弱一般等价类，S 表示强一般等价类，R 表示弱健壮等价类。"
        "全部无效类均由弱健壮方法覆盖。",
    )

    # Appendix C: supplementary results
    add_page_break(doc)
    add_heading(doc, "附录 C 补充检查结果", 1)
    supplement_rows = [
        [
            item["id"],
            item["group"],
            item["description"],
            item["inputs"],
            item["expected"],
            item["actual"],
            item["status"],
        ]
        for item in SUPPLEMENTARY_CASES
    ]
    add_table(
        doc,
        ["编号", "类别", "说明", "输入或流程", "预期结果", "实际结果", "判定"],
        supplement_rows,
        [0.65, 0.62, 1.2, 1.3, 1.45, 1.45, 0.43],
        font_size=6.8,
        center_cols={0, 1, 6},
    )

    # Appendix D: evidence index
    add_page_break(doc)
    add_heading(doc, "附录 D 执行截图索引", 1)
    add_text(
        doc,
        "截图文件位于 results/equivalence/screenshots，文件名与用例编号一致。"
        "每张截图均包含输入、预期结果、实际结果、覆盖等价类和 PASS 判定。",
    )
    evidence_rows = []
    all_execution = [
        (item["id"], item["method_name"], f"{item['id']}.png", item["status"])
        for item in FORMAL_CASES
    ] + [
        (item["id"], item["group"], f"{item['id']}.png", item["status"])
        for item in SUPPLEMENTARY_CASES
    ]
    for case_id, group, file_name, status in all_execution:
        evidence_rows.append([case_id, group, file_name, status])
    add_table(
        doc,
        ["用例编号", "测试类别", "截图文件", "结果"],
        evidence_rows,
        [1.1, 2.15, 2.15, 0.9],
        font_size=8.0,
        center_cols={0, 2, 3},
    )

    add_page_break(doc)
    add_heading(doc, "附录 E 测试资产清单", 1)
    asset_rows = [
        ["equivalence_test_runner.py", "等价类测试执行器"],
        ["results/equivalence/classes.tsv", "57 个等价类及其覆盖方法"],
        ["results/equivalence/cases.tsv", "58 条正式用例及执行结果"],
        ["results/equivalence/supplementary_cases.tsv", "15 条补充检查结果"],
        ["results/equivalence/run_log.txt", "完整执行日志"],
        ["results/equivalence/screenshots", "73 张逐用例截图"],
        ["实验二_等价类测试用例.xlsx", "可筛选用例表与覆盖矩阵"],
        ["实验二_等价类测试报告.pdf", "报告便携版本"],
    ]
    add_table(
        doc,
        ["测试资产", "用途"],
        asset_rows,
        [3.6, 2.9],
        font_size=8.4,
    )

    doc.save(OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = build_document()
    print(path)
