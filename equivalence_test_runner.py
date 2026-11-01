"""实验二：校园 3D 打印服务系统等价类测试执行器。

正式用例只使用 Python 标准库。弱一般、强一般和弱健壮用例分别执行，
执行结果写入 results/equivalence，便于报告、复核和截图。
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Sequence

from input_utils import evaluate
from modules.orders import Service

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "results" / "equivalence"


@dataclass(frozen=True)
class EquivalenceClass:
    id: str
    module: str
    module_name: str
    variable: str
    kind: str
    rule: str
    representative: str


@dataclass(frozen=True)
class TestCase:
    id: str
    method: str
    module: str
    description: str
    inputs: tuple[str, ...]
    expected: str
    covers: tuple[str, ...]

    @property
    def input_text(self) -> str:
        return " ".join(self.inputs)


@dataclass(frozen=True)
class SupplementaryCase:
    id: str
    group: str
    description: str
    inputs: str
    expected: str
    execute: Callable[[], str]


MODULE_NAMES = {
    "size": "尺寸检查",
    "quote": "费用计算",
    "booking": "预约条件检查",
    "order": "完整订单",
}

METHOD_NAMES = {
    "weak_general": "弱一般等价类",
    "strong_general": "强一般等价类",
    "weak_robust": "弱健壮等价类",
}

EXPECTED_METHOD_COUNTS = {
    "weak_general": 7,
    "strong_general": 11,
    "weak_robust": 40,
}


def _ec(
    class_id: str,
    module: str,
    variable: str,
    kind: str,
    rule: str,
    representative: str,
) -> EquivalenceClass:
    return EquivalenceClass(
        class_id,
        module,
        MODULE_NAMES[module],
        variable,
        kind,
        rule,
        representative,
    )


CLASSES: tuple[EquivalenceClass, ...] = (
    _ec("V-S-L", "size", "长度", "有效", "1 <= 长度 <= 200", "100"),
    _ec("V-S-W", "size", "宽度", "有效", "1 <= 宽度 <= 200", "100"),
    _ec("V-S-H", "size", "高度", "有效", "1 <= 高度 <= 200", "100"),
    _ec("I-S-L0", "size", "长度", "无效", "长度 < 1", "0"),
    _ec("I-S-L1", "size", "长度", "无效", "长度 > 200", "201"),
    _ec("I-S-W0", "size", "宽度", "无效", "宽度 < 1", "0"),
    _ec("I-S-W1", "size", "宽度", "无效", "宽度 > 200", "201"),
    _ec("I-S-H0", "size", "高度", "无效", "高度 < 1", "0"),
    _ec("I-S-H1", "size", "高度", "无效", "高度 > 200", "201"),
    _ec("V-Q-G", "quote", "重量", "有效", "1 <= 重量 <= 500", "100"),
    _ec("V-Q-MIN", "quote", "时长", "有效", "1 <= 时长 <= 600", "120"),
    _ec("V-Q-MAT0", "quote", "材料", "有效", "材料 = 0（PLA）", "0"),
    _ec("V-Q-MAT1", "quote", "材料", "有效", "材料 = 1（PETG）", "1"),
    _ec("V-Q-URG0", "quote", "加急", "有效", "加急 = 0（否）", "0"),
    _ec("V-Q-URG1", "quote", "加急", "有效", "加急 = 1（是）", "1"),
    _ec("I-Q-G0", "quote", "重量", "无效", "重量 < 1", "0"),
    _ec("I-Q-G1", "quote", "重量", "无效", "重量 > 500", "501"),
    _ec("I-Q-MIN0", "quote", "时长", "无效", "时长 < 1", "0"),
    _ec("I-Q-MIN1", "quote", "时长", "无效", "时长 > 600", "601"),
    _ec("I-Q-MAT", "quote", "材料", "无效", "材料不是 0 或 1", "2"),
    _ec("I-Q-URG", "quote", "加急", "无效", "加急不是 0 或 1", "2"),
    _ec("V-B-DAY", "booking", "提前天数", "有效", "0 <= 提前天数 <= 7", "3"),
    _ec("V-B-MIN", "booking", "时长", "有效", "1 <= 时长 <= 600", "120"),
    _ec("V-B-REM", "booking", "剩余容量", "有效", "0 <= 剩余容量 <= 600", "120"),
    _ec("V-B-MAINT0", "booking", "维护状态", "有效", "维护状态 = 0（否）", "0"),
    _ec("V-B-MAINT1", "booking", "维护状态", "有效", "维护状态 = 1（是）", "1"),
    _ec("I-B-DAY0", "booking", "提前天数", "无效", "提前天数 < 0", "-1"),
    _ec("I-B-DAY1", "booking", "提前天数", "无效", "提前天数 > 7", "8"),
    _ec("I-B-MIN0", "booking", "时长", "无效", "时长 < 1", "0"),
    _ec("I-B-MIN1", "booking", "时长", "无效", "时长 > 600", "601"),
    _ec("I-B-REM0", "booking", "剩余容量", "无效", "剩余容量 < 0", "-1"),
    _ec("I-B-REM1", "booking", "剩余容量", "无效", "剩余容量 > 600", "601"),
    _ec("I-B-MAINT", "booking", "维护状态", "无效", "维护状态不是 0 或 1", "2"),
    _ec("V-O-L", "order", "长度", "有效", "1 <= 长度 <= 200", "100"),
    _ec("V-O-W", "order", "宽度", "有效", "1 <= 宽度 <= 200", "100"),
    _ec("V-O-H", "order", "高度", "有效", "1 <= 高度 <= 200", "100"),
    _ec("V-O-G", "order", "重量", "有效", "1 <= 重量 <= 500", "100"),
    _ec("V-O-MIN", "order", "时长", "有效", "1 <= 时长 <= 600", "120"),
    _ec("V-O-MAT0", "order", "材料", "有效", "材料 = 0（PLA）", "0"),
    _ec("V-O-MAT1", "order", "材料", "有效", "材料 = 1（PETG）", "1"),
    _ec("V-O-URG0", "order", "加急", "有效", "加急 = 0（否）", "0"),
    _ec("V-O-URG1", "order", "加急", "有效", "加急 = 1（是）", "1"),
    _ec("V-O-DAY", "order", "提前天数", "有效", "0 <= 提前天数 <= 7", "0"),
    _ec("I-O-L0", "order", "长度", "无效", "长度 < 1", "0"),
    _ec("I-O-L1", "order", "长度", "无效", "长度 > 200", "201"),
    _ec("I-O-W0", "order", "宽度", "无效", "宽度 < 1", "0"),
    _ec("I-O-W1", "order", "宽度", "无效", "宽度 > 200", "201"),
    _ec("I-O-H0", "order", "高度", "无效", "高度 < 1", "0"),
    _ec("I-O-H1", "order", "高度", "无效", "高度 > 200", "201"),
    _ec("I-O-G0", "order", "重量", "无效", "重量 < 1", "0"),
    _ec("I-O-G1", "order", "重量", "无效", "重量 > 500", "501"),
    _ec("I-O-MIN0", "order", "时长", "无效", "时长 < 1", "0"),
    _ec("I-O-MIN1", "order", "时长", "无效", "时长 > 600", "601"),
    _ec("I-O-MAT", "order", "材料", "无效", "材料不是 0 或 1", "2"),
    _ec("I-O-URG", "order", "加急", "无效", "加急不是 0 或 1", "2"),
    _ec("I-O-DAY0", "order", "提前天数", "无效", "提前天数 < 0", "-1"),
    _ec("I-O-DAY1", "order", "提前天数", "无效", "提前天数 > 7", "8"),
)

CLASS_MAP = {item.id: item for item in CLASSES}


def _case(
    case_id: str,
    method: str,
    module: str,
    description: str,
    inputs: Sequence[str],
    expected: str,
    covers: Sequence[str],
) -> TestCase:
    return TestCase(
        case_id,
        method,
        module,
        description,
        tuple(inputs),
        expected,
        tuple(covers),
    )


def weak_general_cases() -> list[TestCase]:
    return [
        _case("WG-S-01", "weak_general", "size", "三个尺寸变量均取有效类",
              ["100", "100", "100"], "SIZE_OK", ["V-S-L", "V-S-W", "V-S-H"]),
        _case("WG-Q-01", "weak_general", "quote", "PLA 且不加急的有效基线",
              ["100", "120", "0", "0"], "PRICE=26.00",
              ["V-Q-G", "V-Q-MIN", "V-Q-MAT0", "V-Q-URG0"]),
        _case("WG-Q-02", "weak_general", "quote", "PETG 且加急的有效基线",
              ["100", "120", "1", "1"], "PRICE=54.00",
              ["V-Q-G", "V-Q-MIN", "V-Q-MAT1", "V-Q-URG1"]),
        _case("WG-B-01", "weak_general", "booking", "设备未维护且容量足够",
              ["3", "120", "120", "0"], "BOOKING_OK",
              ["V-B-DAY", "V-B-MIN", "V-B-REM", "V-B-MAINT0"]),
        _case("WG-B-02", "weak_general", "booking", "维护状态的有效等价类",
              ["3", "120", "120", "1"], "REJECT_MAINTENANCE",
              ["V-B-DAY", "V-B-MIN", "V-B-REM", "V-B-MAINT1"]),
        _case("WG-O-01", "weak_general", "order", "PLA 且不加急的完整订单",
              ["100", "100", "100", "100", "120", "0", "0", "0"],
              "ORDER=1;PRICE=26.00;REMAIN=480;COUNT=1;CAPACITY=480",
              ["V-O-L", "V-O-W", "V-O-H", "V-O-G", "V-O-MIN",
               "V-O-MAT0", "V-O-URG0", "V-O-DAY"]),
        _case("WG-O-02", "weak_general", "order", "PETG 且加急的完整订单",
              ["100", "100", "100", "100", "120", "1", "1", "0"],
              "ORDER=1;PRICE=54.00;REMAIN=480;COUNT=1;CAPACITY=480",
              ["V-O-L", "V-O-W", "V-O-H", "V-O-G", "V-O-MIN",
               "V-O-MAT1", "V-O-URG1", "V-O-DAY"]),
    ]


def strong_general_cases() -> list[TestCase]:
    order_covers = ["V-O-L", "V-O-W", "V-O-H", "V-O-G", "V-O-MIN", "V-O-DAY"]
    return [
        _case("SG-S-01", "strong_general", "size", "尺寸有效类唯一组合",
              ["100", "100", "100"], "SIZE_OK", ["V-S-L", "V-S-W", "V-S-H"]),
        _case("SG-Q-01", "strong_general", "quote", "PLA 且不加急",
              ["100", "120", "0", "0"], "PRICE=26.00",
              ["V-Q-G", "V-Q-MIN", "V-Q-MAT0", "V-Q-URG0"]),
        _case("SG-Q-02", "strong_general", "quote", "PLA 且加急",
              ["100", "120", "0", "1"], "PRICE=39.00",
              ["V-Q-G", "V-Q-MIN", "V-Q-MAT0", "V-Q-URG1"]),
        _case("SG-Q-03", "strong_general", "quote", "PETG 且不加急",
              ["100", "120", "1", "0"], "PRICE=36.00",
              ["V-Q-G", "V-Q-MIN", "V-Q-MAT1", "V-Q-URG0"]),
        _case("SG-Q-04", "strong_general", "quote", "PETG 且加急",
              ["100", "120", "1", "1"], "PRICE=54.00",
              ["V-Q-G", "V-Q-MIN", "V-Q-MAT1", "V-Q-URG1"]),
        _case("SG-B-01", "strong_general", "booking", "维护状态为否",
              ["3", "120", "120", "0"], "BOOKING_OK",
              ["V-B-DAY", "V-B-MIN", "V-B-REM", "V-B-MAINT0"]),
        _case("SG-B-02", "strong_general", "booking", "维护状态为是",
              ["3", "120", "120", "1"], "REJECT_MAINTENANCE",
              ["V-B-DAY", "V-B-MIN", "V-B-REM", "V-B-MAINT1"]),
        _case("SG-O-01", "strong_general", "order", "PLA 且不加急",
              ["100", "100", "100", "100", "120", "0", "0", "0"],
              "ORDER=1;PRICE=26.00;REMAIN=480;COUNT=1;CAPACITY=480",
              order_covers + ["V-O-MAT0", "V-O-URG0"]),
        _case("SG-O-02", "strong_general", "order", "PLA 且加急",
              ["100", "100", "100", "100", "120", "0", "1", "0"],
              "ORDER=1;PRICE=39.00;REMAIN=480;COUNT=1;CAPACITY=480",
              order_covers + ["V-O-MAT0", "V-O-URG1"]),
        _case("SG-O-03", "strong_general", "order", "PETG 且不加急",
              ["100", "100", "100", "100", "120", "1", "0", "0"],
              "ORDER=1;PRICE=36.00;REMAIN=480;COUNT=1;CAPACITY=480",
              order_covers + ["V-O-MAT1", "V-O-URG0"]),
        _case("SG-O-04", "strong_general", "order", "PETG 且加急",
              ["100", "100", "100", "100", "120", "1", "1", "0"],
              "ORDER=1;PRICE=54.00;REMAIN=480;COUNT=1;CAPACITY=480",
              order_covers + ["V-O-MAT1", "V-O-URG1"]),
    ]


def weak_robust_cases() -> list[TestCase]:
    normal_size = _case(
        "WR-S-01", "weak_robust", "size", "有效基线",
        ["100", "100", "100"], "SIZE_OK", ["V-S-L", "V-S-W", "V-S-H"],
    )
    size_invalid = [
        _case("WR-S-02", "weak_robust", "size", "长度低于有效范围",
              ["0", "100", "100"], "ERR_SIZE", ["I-S-L0", "V-S-W", "V-S-H"]),
        _case("WR-S-03", "weak_robust", "size", "长度高于有效范围",
              ["201", "100", "100"], "ERR_SIZE", ["I-S-L1", "V-S-W", "V-S-H"]),
        _case("WR-S-04", "weak_robust", "size", "宽度低于有效范围",
              ["100", "0", "100"], "ERR_SIZE", ["I-S-W0", "V-S-L", "V-S-H"]),
        _case("WR-S-05", "weak_robust", "size", "宽度高于有效范围",
              ["100", "201", "100"], "ERR_SIZE", ["I-S-W1", "V-S-L", "V-S-H"]),
        _case("WR-S-06", "weak_robust", "size", "高度低于有效范围",
              ["100", "100", "0"], "ERR_SIZE", ["I-S-H0", "V-S-L", "V-S-W"]),
        _case("WR-S-07", "weak_robust", "size", "高度高于有效范围",
              ["100", "100", "201"], "ERR_SIZE", ["I-S-H1", "V-S-L", "V-S-W"]),
    ]

    normal_quote = [
        _case("WR-Q-01", "weak_robust", "quote", "PLA 正常基线",
              ["100", "120", "0", "0"], "PRICE=26.00",
              ["V-Q-G", "V-Q-MIN", "V-Q-MAT0", "V-Q-URG0"]),
        _case("WR-Q-02", "weak_robust", "quote", "PETG 加急正常基线",
              ["100", "120", "1", "1"], "PRICE=54.00",
              ["V-Q-G", "V-Q-MIN", "V-Q-MAT1", "V-Q-URG1"]),
    ]
    quote_invalid = [
        _case("WR-Q-03", "weak_robust", "quote", "重量低于有效范围",
              ["0", "120", "0", "0"], "ERR_QUOTE_RANGE",
              ["I-Q-G0", "V-Q-MIN", "V-Q-MAT0", "V-Q-URG0"]),
        _case("WR-Q-04", "weak_robust", "quote", "重量高于有效范围",
              ["501", "120", "0", "0"], "ERR_QUOTE_RANGE",
              ["I-Q-G1", "V-Q-MIN", "V-Q-MAT0", "V-Q-URG0"]),
        _case("WR-Q-05", "weak_robust", "quote", "时长低于有效范围",
              ["100", "0", "0", "0"], "ERR_QUOTE_RANGE",
              ["I-Q-MIN0", "V-Q-G", "V-Q-MAT0", "V-Q-URG0"]),
        _case("WR-Q-06", "weak_robust", "quote", "时长高于有效范围",
              ["100", "601", "0", "0"], "ERR_QUOTE_RANGE",
              ["I-Q-MIN1", "V-Q-G", "V-Q-MAT0", "V-Q-URG0"]),
        _case("WR-Q-07", "weak_robust", "quote", "材料编码无效",
              ["100", "120", "2", "0"], "ERR_MATERIAL",
              ["I-Q-MAT", "V-Q-G", "V-Q-MIN", "V-Q-URG0"]),
        _case("WR-Q-08", "weak_robust", "quote", "加急编码无效",
              ["100", "120", "0", "2"], "ERR_URGENT",
              ["I-Q-URG", "V-Q-G", "V-Q-MIN", "V-Q-MAT0"]),
    ]

    normal_booking = [
        _case("WR-B-01", "weak_robust", "booking", "维护状态为否的正常基线",
              ["3", "120", "120", "0"], "BOOKING_OK",
              ["V-B-DAY", "V-B-MIN", "V-B-REM", "V-B-MAINT0"]),
        _case("WR-B-02", "weak_robust", "booking", "维护状态为是的正常基线",
              ["3", "120", "120", "1"], "REJECT_MAINTENANCE",
              ["V-B-DAY", "V-B-MIN", "V-B-REM", "V-B-MAINT1"]),
    ]
    booking_invalid = [
        _case("WR-B-03", "weak_robust", "booking", "提前天数低于有效范围",
              ["-1", "120", "120", "0"], "ERR_BOOKING_RANGE",
              ["I-B-DAY0", "V-B-MIN", "V-B-REM", "V-B-MAINT0"]),
        _case("WR-B-04", "weak_robust", "booking", "提前天数高于有效范围",
              ["8", "120", "120", "0"], "ERR_BOOKING_RANGE",
              ["I-B-DAY1", "V-B-MIN", "V-B-REM", "V-B-MAINT0"]),
        _case("WR-B-05", "weak_robust", "booking", "时长低于有效范围",
              ["3", "0", "120", "0"], "ERR_BOOKING_RANGE",
              ["I-B-MIN0", "V-B-DAY", "V-B-REM", "V-B-MAINT0"]),
        _case("WR-B-06", "weak_robust", "booking", "时长高于有效范围",
              ["3", "601", "120", "0"], "ERR_BOOKING_RANGE",
              ["I-B-MIN1", "V-B-DAY", "V-B-REM", "V-B-MAINT0"]),
        _case("WR-B-07", "weak_robust", "booking", "剩余容量低于有效范围",
              ["3", "120", "-1", "0"], "ERR_BOOKING_RANGE",
              ["I-B-REM0", "V-B-DAY", "V-B-MIN", "V-B-MAINT0"]),
        _case("WR-B-08", "weak_robust", "booking", "剩余容量高于有效范围",
              ["3", "120", "601", "0"], "ERR_BOOKING_RANGE",
              ["I-B-REM1", "V-B-DAY", "V-B-MIN", "V-B-MAINT0"]),
        _case("WR-B-09", "weak_robust", "booking", "维护编码无效",
              ["3", "120", "120", "2"], "ERR_MAINTENANCE",
              ["I-B-MAINT", "V-B-DAY", "V-B-MIN", "V-B-REM"]),
    ]

    order_base = ["V-O-L", "V-O-W", "V-O-H", "V-O-G", "V-O-MIN", "V-O-DAY"]
    normal_order = [
        _case("WR-O-01", "weak_robust", "order", "PLA 不加急正常基线",
              ["100", "100", "100", "100", "120", "0", "0", "0"],
              "ORDER=1;PRICE=26.00;REMAIN=480;COUNT=1;CAPACITY=480",
              order_base + ["V-O-MAT0", "V-O-URG0"]),
        _case("WR-O-02", "weak_robust", "order", "PETG 加急正常基线",
              ["100", "100", "100", "100", "120", "1", "1", "0"],
              "ORDER=1;PRICE=54.00;REMAIN=480;COUNT=1;CAPACITY=480",
              order_base + ["V-O-MAT1", "V-O-URG1"]),
    ]
    order_invalid_specs = [
        ("WR-O-03", "长度低于有效范围", ["0", "100", "100", "100", "120", "0", "0", "0"],
         "ERR_SIZE", "I-O-L0", ["V-O-W", "V-O-H", "V-O-G", "V-O-MIN", "V-O-DAY",
                               "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-04", "长度高于有效范围", ["201", "100", "100", "100", "120", "0", "0", "0"],
         "ERR_SIZE", "I-O-L1", ["V-O-W", "V-O-H", "V-O-G", "V-O-MIN", "V-O-DAY",
                               "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-05", "宽度低于有效范围", ["100", "0", "100", "100", "120", "0", "0", "0"],
         "ERR_SIZE", "I-O-W0", ["V-O-L", "V-O-H", "V-O-G", "V-O-MIN", "V-O-DAY",
                               "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-06", "宽度高于有效范围", ["100", "201", "100", "100", "120", "0", "0", "0"],
         "ERR_SIZE", "I-O-W1", ["V-O-L", "V-O-H", "V-O-G", "V-O-MIN", "V-O-DAY",
                               "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-07", "高度低于有效范围", ["100", "100", "0", "100", "120", "0", "0", "0"],
         "ERR_SIZE", "I-O-H0", ["V-O-L", "V-O-W", "V-O-G", "V-O-MIN", "V-O-DAY",
                               "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-08", "高度高于有效范围", ["100", "100", "201", "100", "120", "0", "0", "0"],
         "ERR_SIZE", "I-O-H1", ["V-O-L", "V-O-W", "V-O-G", "V-O-MIN", "V-O-DAY",
                               "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-09", "重量低于有效范围", ["100", "100", "100", "0", "120", "0", "0", "0"],
         "ERR_QUOTE_RANGE", "I-O-G0", ["V-O-L", "V-O-W", "V-O-H", "V-O-MIN",
                                       "V-O-DAY", "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-10", "重量高于有效范围", ["100", "100", "100", "501", "120", "0", "0", "0"],
         "ERR_QUOTE_RANGE", "I-O-G1", ["V-O-L", "V-O-W", "V-O-H", "V-O-MIN",
                                       "V-O-DAY", "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-11", "时长低于有效范围", ["100", "100", "100", "100", "0", "0", "0", "0"],
         "ERR_QUOTE_RANGE", "I-O-MIN0", ["V-O-L", "V-O-W", "V-O-H", "V-O-G",
                                         "V-O-DAY", "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-12", "时长高于有效范围", ["100", "100", "100", "100", "601", "0", "0", "0"],
         "ERR_QUOTE_RANGE", "I-O-MIN1", ["V-O-L", "V-O-W", "V-O-H", "V-O-G",
                                         "V-O-DAY", "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-13", "材料编码无效", ["100", "100", "100", "100", "120", "2", "0", "0"],
         "ERR_MATERIAL", "I-O-MAT", ["V-O-L", "V-O-W", "V-O-H", "V-O-G",
                                     "V-O-MIN", "V-O-DAY", "V-O-URG0"]),
        ("WR-O-14", "加急编码无效", ["100", "100", "100", "100", "120", "0", "2", "0"],
         "ERR_URGENT", "I-O-URG", ["V-O-L", "V-O-W", "V-O-H", "V-O-G",
                                   "V-O-MIN", "V-O-DAY", "V-O-MAT0"]),
        ("WR-O-15", "提前天数低于有效范围", ["100", "100", "100", "100", "120", "0", "0", "-1"],
         "ERR_BOOKING_RANGE", "I-O-DAY0", ["V-O-L", "V-O-W", "V-O-H", "V-O-G",
                                           "V-O-MIN", "V-O-MAT0", "V-O-URG0"]),
        ("WR-O-16", "提前天数高于有效范围", ["100", "100", "100", "100", "120", "0", "0", "8"],
         "ERR_BOOKING_RANGE", "I-O-DAY1", ["V-O-L", "V-O-W", "V-O-H", "V-O-G",
                                           "V-O-MIN", "V-O-MAT0", "V-O-URG0"]),
    ]
    order_invalid = [
        _case(case_id, "weak_robust", "order", description, inputs,
              f"{expected};COUNT=0;CAPACITY=600", [invalid] + valid_covers)
        for case_id, description, inputs, expected, invalid, valid_covers
        in order_invalid_specs
    ]

    return [
        normal_size,
        *size_invalid,
        *normal_quote,
        *quote_invalid,
        *normal_booking,
        *booking_invalid,
        *normal_order,
        *order_invalid,
    ]


def all_cases() -> list[TestCase]:
    return [*weak_general_cases(), *strong_general_cases(), *weak_robust_cases()]


def execute_case(case: TestCase) -> str:
    if case.module != "order":
        return evaluate(case.module, case.inputs)

    values = [int(value) for value in case.inputs]
    service = Service()
    result = service.submit(*values)
    checked_day = values[-1] if 0 <= values[-1] <= 7 else 0
    return (
        f"{result};COUNT={len(service.orders)};"
        f"CAPACITY={service.remaining(checked_day)}"
    )


def _state(service: Service, day: int) -> str:
    return f"COUNT={len(service.orders)};CAPACITY={service.remaining(day)}"


def _scenario(
    case_id: str,
    description: str,
    inputs: str,
    expected: str,
    execute: Callable[[], str],
) -> SupplementaryCase:
    return SupplementaryCase(case_id, "流程补充", description, inputs, expected, execute)


def _input_case(
    case_id: str,
    description: str,
    module: str,
    inputs: str,
    expected: str,
) -> SupplementaryCase:
    return SupplementaryCase(
        case_id,
        "输入格式",
        description,
        inputs,
        expected,
        lambda module=module, inputs=inputs: evaluate(module, inputs.split()),
    )


def supplementary_cases() -> list[SupplementaryCase]:
    input_cases = [
        _input_case("INP-01", "尺寸输入使用小数", "size", "100.5 100 100", "ERR_INTEGER"),
        _input_case("INP-02", "尺寸输入包含字母", "size", "abc 100 100", "ERR_INTEGER"),
        _input_case("INP-03", "尺寸输入超出 32 位整数范围", "size",
                    "2147483648 100 100", "ERR_INTEGER"),
        _input_case("INP-04", "尺寸输入参数不足", "size", "100 100", "ERR_ARGUMENT_COUNT"),
        _input_case("INP-05", "报价输入使用双负号", "quote", "--1 120 0 0", "ERR_INTEGER"),
    ]

    def priority_size() -> str:
        service = Service()
        result = service.submit(201, 100, 100, 0, 0, 0, 0, 0)
        return f"{result};{_state(service, 0)}"

    def priority_quote() -> str:
        service = Service()
        result = service.submit(100, 100, 100, 0, 120, 0, 0, 8)
        return f"{result};{_state(service, 0)}"

    def priority_day() -> str:
        service = Service()
        result = service.submit(100, 100, 100, 100, 120, 0, 0, 8)
        return f"{result};{_state(service, 0)}"

    def booking_precedence() -> str:
        service = Service()
        first = service.submit(100, 100, 100, 100, 500, 0, 0, 1)
        service.set_maintenance(1, 1)
        second = service.submit(100, 100, 100, 100, 120, 0, 0, 1)
        return f"FIRST={first};SECOND={second};{_state(service, 1)}"

    def capacity_reject() -> str:
        service = Service()
        first = service.submit(100, 100, 100, 100, 500, 0, 0, 2)
        second = service.submit(100, 100, 100, 100, 101, 0, 0, 2)
        return f"FIRST={first};SECOND={second};{_state(service, 2)}"

    def exact_capacity() -> str:
        service = Service()
        first = service.submit(100, 100, 100, 100, 600, 0, 0, 3)
        second = service.submit(100, 100, 100, 100, 1, 0, 0, 3)
        return f"FIRST={first};SECOND={second};{_state(service, 3)}"

    def day_independent() -> str:
        service = Service()
        first = service.submit(100, 100, 100, 100, 120, 0, 0, 0)
        return (
            f"FIRST={first};DAY0={service.remaining(0)};"
            f"DAY1={service.remaining(1)};COUNT={len(service.orders)}"
        )

    def failure_preserves_state() -> str:
        service = Service()
        first = service.submit(100, 100, 100, 100, 120, 0, 0, 0)
        second = service.submit(201, 100, 100, 100, 120, 0, 0, 0)
        third = service.submit(100, 100, 100, 100, 481, 0, 0, 0)
        return f"FIRST={first};SECOND={second};THIRD={third};{_state(service, 0)}"

    def success_sequence() -> str:
        service = Service()
        first = service.submit(100, 100, 100, 100, 120, 0, 0, 0)
        second = service.submit(100, 100, 100, 100, 120, 0, 0, 0)
        return f"FIRST={first};SECOND={second};{_state(service, 0)}"

    def maintenance_recovery() -> str:
        service = Service()
        service.set_maintenance(4, 1)
        rejected = service.submit(100, 100, 100, 100, 120, 0, 0, 4)
        service.set_maintenance(4, 0)
        accepted = service.submit(100, 100, 100, 100, 120, 0, 0, 4)
        return f"REJECTED={rejected};ACCEPTED={accepted};{_state(service, 4)}"

    scenarios = [
        _scenario("FLOW-01", "尺寸错误优先于报价错误", "201 100 100 0 0 0 0 0",
                  "ERR_SIZE;COUNT=0;CAPACITY=600", priority_size),
        _scenario("FLOW-02", "报价错误优先于日期错误", "100 100 100 0 120 0 0 8",
                  "ERR_QUOTE_RANGE;COUNT=0;CAPACITY=600", priority_quote),
        _scenario("FLOW-03", "日期错误在预约检查中返回", "100 100 100 100 120 0 0 8",
                  "ERR_BOOKING_RANGE;COUNT=0;CAPACITY=600", priority_day),
        _scenario("FLOW-04", "维护拒绝优先于容量不足",
                  "第1单500分钟；设置维护；第2单120分钟",
                  "FIRST=ORDER=1;PRICE=45.00;REMAIN=100;"
                  "SECOND=REJECT_MAINTENANCE;COUNT=1;CAPACITY=100",
                  booking_precedence),
        _scenario("FLOW-05", "容量不足时拒绝且保留已有订单",
                  "第1单500分钟；第2单101分钟",
                  "FIRST=ORDER=1;PRICE=45.00;REMAIN=100;"
                  "SECOND=REJECT_CAPACITY;COUNT=1;CAPACITY=100",
                  capacity_reject),
        _scenario("FLOW-06", "剩余容量刚好等于预约时长时允许提交",
                  "第1单600分钟；第2单1分钟",
                  "FIRST=ORDER=1;PRICE=50.00;REMAIN=0;"
                  "SECOND=REJECT_CAPACITY;COUNT=1;CAPACITY=0",
                  exact_capacity),
        _scenario("FLOW-07", "不同相对日的容量互相独立", "第0天提交120分钟",
                  "FIRST=ORDER=1;PRICE=26.00;REMAIN=480;"
                  "DAY0=480;DAY1=600;COUNT=1", day_independent),
        _scenario("FLOW-08", "失败订单不改变编号、记录或容量",
                  "成功1单；尺寸失败；容量失败",
                  "FIRST=ORDER=1;PRICE=26.00;REMAIN=480;"
                  "SECOND=ERR_SIZE;THIRD=REJECT_CAPACITY;"
                  "COUNT=1;CAPACITY=480", failure_preserves_state),
        _scenario("FLOW-09", "连续成功订单递增编号并累计扣减容量",
                  "同一相对日连续提交两个120分钟订单",
                  "FIRST=ORDER=1;PRICE=26.00;REMAIN=480;"
                  "SECOND=ORDER=2;PRICE=26.00;REMAIN=360;"
                  "COUNT=2;CAPACITY=360", success_sequence),
        _scenario("FLOW-10", "关闭维护后可继续提交订单",
                  "第4天开启维护并提交；关闭维护后再提交",
                  "REJECTED=REJECT_MAINTENANCE;"
                  "ACCEPTED=ORDER=1;PRICE=26.00;REMAIN=480;"
                  "COUNT=1;CAPACITY=480", maintenance_recovery),
    ]
    return input_cases + scenarios


def validate_design(cases: Iterable[TestCase]) -> None:
    case_list = list(cases)
    ids = [case.id for case in case_list]
    if len(ids) != len(set(ids)):
        raise ValueError("测试用例编号重复")

    method_counts = Counter(case.method for case in case_list)
    if dict(method_counts) != EXPECTED_METHOD_COUNTS:
        raise ValueError(
            f"三类方法的用例数量不符合设计：{dict(method_counts)}"
        )

    valid_ids = {item.id for item in CLASSES if item.kind == "有效"}
    invalid_ids = {item.id for item in CLASSES if item.kind == "无效"}

    for method in ("weak_general", "strong_general"):
        covered = {class_id for case in case_list if case.method == method
                   for class_id in case.covers}
        if covered != valid_ids:
            raise ValueError(
                f"{method} 未完整覆盖有效等价类："
                f"缺少 {sorted(valid_ids - covered)}，多出 {sorted(covered - valid_ids)}"
            )

    robust_cases = [case for case in case_list if case.method == "weak_robust"]
    robust_covered = {class_id for case in robust_cases for class_id in case.covers}
    if robust_covered != valid_ids | invalid_ids:
        raise ValueError(
            "weak_robust 未完整覆盖全部等价类："
            f"缺少 {sorted((valid_ids | invalid_ids) - robust_covered)}"
        )

    invalid_occurrences = Counter(
        class_id for case in robust_cases for class_id in case.covers
        if class_id in invalid_ids
    )
    if set(invalid_occurrences) != invalid_ids:
        raise ValueError("弱健壮用例没有覆盖全部无效等价类")
    if any(count != 1 for count in invalid_occurrences.values()):
        raise ValueError("每个无效等价类在弱健壮用例中应仅出现一次")


def coverage_for(class_id: str, cases: Iterable[TestCase]) -> str:
    methods = [
        name for name in ("weak_general", "strong_general", "weak_robust")
        if any(case.method == name and class_id in case.covers for case in cases)
    ]
    return ",".join(methods) if methods else ""


def _write_tsv(path: Path, fields: Sequence[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def run(output_dir: Path = OUTPUT_DIR) -> int:
    cases = all_cases()
    validate_design(cases)
    supplements = supplementary_cases()
    output_dir.mkdir(parents=True, exist_ok=True)

    formal_rows: list[dict] = []
    for case in cases:
        actual = execute_case(case)
        status = "PASS" if actual == case.expected else "FAIL"
        formal_rows.append({
            "id": case.id,
            "method": case.method,
            "method_name": METHOD_NAMES[case.method],
            "module": case.module,
            "module_name": MODULE_NAMES[case.module],
            "description": case.description,
            "inputs": case.input_text,
            "expected": case.expected,
            "actual": actual,
            "status": status,
            "covers": ",".join(case.covers),
        })

    supplement_rows: list[dict] = []
    for case in supplements:
        actual = case.execute()
        status = "PASS" if actual == case.expected else "FAIL"
        supplement_rows.append({
            "id": case.id,
            "group": case.group,
            "description": case.description,
            "inputs": case.inputs,
            "expected": case.expected,
            "actual": actual,
            "status": status,
        })

    formal_passed = sum(row["status"] == "PASS" for row in formal_rows)
    supplement_passed = sum(row["status"] == "PASS" for row in supplement_rows)
    method_summary = []
    for method, method_name in METHOD_NAMES.items():
        rows = [row for row in formal_rows if row["method"] == method]
        passed = sum(row["status"] == "PASS" for row in rows)
        method_summary.append({
            "method": method,
            "method_name": method_name,
            "total": len(rows),
            "passed": passed,
            "failed": len(rows) - passed,
        })

    class_rows = []
    for item in CLASSES:
        class_rows.append({
            "id": item.id,
            "module": item.module,
            "module_name": item.module_name,
            "variable": item.variable,
            "kind": item.kind,
            "rule": item.rule,
            "representative": item.representative,
            "covered_by": coverage_for(item.id, cases),
        })

    case_fields = [
        "id", "method", "method_name", "module", "module_name", "description",
        "inputs", "expected", "actual", "status", "covers",
    ]
    class_fields = [
        "id", "module", "module_name", "variable", "kind", "rule",
        "representative", "covered_by",
    ]
    supplement_fields = [
        "id", "group", "description", "inputs", "expected", "actual", "status",
    ]
    _write_tsv(output_dir / "classes.tsv", class_fields, class_rows)
    _write_tsv(output_dir / "cases.tsv", case_fields, formal_rows)
    _write_tsv(output_dir / "supplementary_cases.tsv", supplement_fields, supplement_rows)
    _write_tsv(output_dir / "method_summary.tsv",
               ["method", "method_name", "total", "passed", "failed"], method_summary)

    executed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest = {
        "project": "校园 3D 打印服务系统",
        "experiment": "实验二 等价类测试",
        "executed_at": executed_at,
        "python": platform.python_version(),
        "formal_cases": formal_rows,
        "supplementary_cases": supplement_rows,
        "classes": class_rows,
        "method_summary": method_summary,
        "totals": {
            "formal": len(formal_rows),
            "formal_passed": formal_passed,
            "formal_failed": len(formal_rows) - formal_passed,
            "supplementary": len(supplement_rows),
            "supplementary_passed": supplement_passed,
            "supplementary_failed": len(supplement_rows) - supplement_passed,
            "all": len(formal_rows) + len(supplement_rows),
            "all_passed": formal_passed + supplement_passed,
        },
        "defects": [],
    }
    (output_dir / "evidence_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    log_lines = [
        ("[PASS]" if row["status"] == "PASS" else "[FAIL]")
        + f" {row['id']} {row['method_name']} {row['module_name']} "
        + f"输入={row['inputs']} 预期={row['expected']} 实际={row['actual']}"
        for row in formal_rows
    ]
    log_lines.extend(
        ("[PASS]" if row["status"] == "PASS" else "[FAIL]")
        + f" {row['id']} {row['group']} {row['description']} "
        + f"输入={row['inputs']} 预期={row['expected']} 实际={row['actual']}"
        for row in supplement_rows
    )
    summary_lines = [
        f"{row['method_name']} total={row['total']} "
        f"passed={row['passed']} failed={row['failed']}"
        for row in method_summary
    ]
    summary_lines.extend([
        f"FORMAL total={len(formal_rows)} passed={formal_passed} "
        f"failed={len(formal_rows) - formal_passed}",
        f"SUPPLEMENTARY total={len(supplement_rows)} "
        f"passed={supplement_passed} "
        f"failed={len(supplement_rows) - supplement_passed}",
        f"OVERALL total={len(formal_rows) + len(supplement_rows)} "
        f"passed={formal_passed + supplement_passed} "
        f"failed={len(formal_rows) + len(supplement_rows) - formal_passed - supplement_passed}",
    ])
    (output_dir / "run_log.txt").write_text(
        "\n".join(log_lines) + "\n",
        encoding="utf-8",
    )
    (output_dir / "summary.txt").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    print("\n".join(summary_lines))
    print(f"结果目录：{output_dir}")
    return 0 if formal_passed == len(formal_rows) and supplement_passed == len(supplement_rows) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="执行实验二等价类测试")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR,
                        help="测试结果输出目录")
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
