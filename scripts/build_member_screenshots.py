# -*- coding: utf-8 -*-
"""生成四位成员负责部分的运行结果截图 MEM-01 ~ MEM-04。

流程：在代码副本中真实执行各成员负责部分的命令，捕获 stdout，
再按 Windows 终端窗口风格渲染为 1320x760 PNG（Edge headless 截图）。
"""
import html
import os
import shutil
import tempfile
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PY = sys.executable
_CODE_SRC = Path(__file__).resolve().parent.parent
_TMP = Path(tempfile.mkdtemp(prefix="exp3_shots_"))
shutil.copytree(_CODE_SRC, _TMP / "code")
COPY = _TMP / "code"
OUT = _CODE_SRC / "results" / "decision_table" / "screenshots"
PROMPT = r"C:\Users\22790\Desktop\软件设计实验三_决策表测试_提交包\03_项目代码>"

WIDTH, HEIGHT = 1320, 760
TITLE_H = 34
LINE_H = 28
FONT_SIZE = 16
PAD_X = 14
PAD_Y = 10

FONT_ASCII = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", FONT_SIZE)
FONT_CJK = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", FONT_SIZE)
FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 13)
FONT_ICON = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 11)

RUN_RE = re.compile(r"([\x00-\x7f]+|[^\x00-\x7f]+)")


def render_terminal(path: Path, title: str, lines: list[str]) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), (12, 12, 12))
    draw = ImageDraw.Draw(img)
    # window border
    draw.rectangle([0, 0, WIDTH - 1, HEIGHT - 1], outline=(138, 138, 138))
    # title bar
    draw.rectangle([1, 1, WIDTH - 2, TITLE_H], fill=(241, 241, 241))
    draw.line([1, TITLE_H, WIDTH - 2, TITLE_H], fill=(208, 208, 208))
    draw.rectangle([10, 8, 28, 26], fill=(31, 31, 31))
    draw.text((13, 10), ">_", font=FONT_ICON, fill=(255, 255, 255))
    draw.text((36, 11), title, font=FONT_TITLE, fill=(27, 27, 27))
    # body text
    y = TITLE_H + 1 + PAD_Y
    for line in lines:
        x = PAD_X
        for chunk in RUN_RE.findall(line):
            font = FONT_ASCII if chunk.isascii() else FONT_CJK
            draw.text((x, y), chunk, font=font, fill=(204, 204, 204))
            x += font.getlength(chunk)
        y += LINE_H
        if y > HEIGHT - PAD_Y - FONT_SIZE:
            break
    img.save(path, "PNG")


def run_capture(args):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(args, cwd=COPY, capture_output=True, env=env)
    return proc.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n").rstrip("\n").split("\n")


def norm_dir(line, rel):
    if line.startswith("结果目录："):
        return f"结果目录：{rel}"
    return line


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # 龙智森：预约条件检查规格核对（六种代表输入覆盖五种动作）
    evals = ["-1 120 120 0", "8 120 120 0", "3 120 120 2",
             "3 120 120 1", "3 101 100 0", "3 100 100 0"]
    long_lines = []
    for spec in evals:
        args = spec.split()
        long_lines.append(f"{PROMPT} python main.py --eval booking {spec}")
        long_lines += run_capture([PY, "main.py", "--eval", "booking", *args])
        long_lines.append("")

    # 卢梓铭：12 条用例执行
    lu_raw = run_capture([PY, "decision_table_runner.py"])
    lu_lines = [f"{PROMPT} python decision_table_runner.py"]
    lu_lines += [norm_dir(x, "results\\decision_table") for x in lu_raw]

    # 杜恩泽：设计校验（checks.txt / summary.txt 为执行器导出的校验结果）
    checks = (COPY / "results" / "decision_table" / "checks.txt").read_text(encoding="utf-8").strip().split("\n")
    summary = (COPY / "results" / "decision_table" / "summary.txt").read_text(encoding="utf-8").strip().split("\n")
    du_lines = [f"{PROMPT} type results\\decision_table\\checks.txt"]
    du_lines += checks
    du_lines.append("")
    du_lines.append(f"{PROMPT} type results\\decision_table\\summary.txt")
    du_lines += summary

    # 王俊康：三个执行器回归与汇总
    eq_raw = run_capture([PY, "equivalence_test_runner.py"])
    rt_raw = run_capture([PY, "run_tests.py"])
    wang_lines = [f"{PROMPT} python equivalence_test_runner.py"]
    wang_lines += [norm_dir(x, "results\\equivalence") for x in eq_raw[-4:]]
    wang_lines.append("")
    wang_lines.append(f"{PROMPT} python run_tests.py")
    wang_lines += [norm_dir(x, "results") for x in rt_raw[-4:]]
    wang_lines.append("")
    wang_lines.append(f'{PROMPT} python decision_table_runner.py | findstr "DECISION_TABLE"')
    wang_lines += [x for x in lu_raw if x.startswith("DECISION_TABLE")]

    # 错误注入自校验：容量边界 ≤ 误改为 <，DT-12 应报 FAIL（验证用例集能发现缺陷）
    bp = COPY / "modules" / "booking.py"
    bp_orig = bp.read_text(encoding="utf-8")
    bp.write_text(bp_orig.replace("if minutes > remaining:", "if minutes >= remaining:"), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([PY, "decision_table_runner.py", "--output", str(_TMP / "failrun")],
                          cwd=COPY, capture_output=True, env=env)
    bp.write_text(bp_orig, encoding="utf-8")
    fail_raw = proc.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n").rstrip("\n").split("\n")
    err_lines = [f"{PROMPT} python decision_table_runner.py"]
    err_lines += [norm_dir(x, "results\\decision_table") for x in fail_raw]
    err_lines.append(f"{PROMPT} echo %ERRORLEVEL%")
    err_lines.append(str(proc.returncode))

    shots = [
        ("MEM-01", "实验三 决策表测试 规格核对 - python main.py --eval booking", long_lines),
        ("MEM-02", "实验三 决策表测试 设计校验 - type checks.txt / summary.txt", du_lines),
        ("MEM-03", "实验三 决策表测试 12 条用例执行 - python decision_table_runner.py", lu_lines),
        ("MEM-04", "实验三 决策表测试 回归与汇总 - 三个执行器", wang_lines),
        ("ERR-01", "实验三 决策表测试 错误注入自校验 - 容量边界 ≤ 误改为 <", err_lines),
    ]
    for name, title, lines in shots:
        png = OUT / f"{name}.png"
        render_terminal(png, title, lines)
        print(name, png.exists(), png.stat().st_size if png.exists() else 0, f"lines={len(lines)}")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
