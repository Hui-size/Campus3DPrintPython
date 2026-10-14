"""菜单和测试共用的输入校验，以及结果码的中文说明。"""

import re
from typing import List, Sequence

from modules.size_check import check_size
from modules.pricing import quote
from modules.booking import check_booking

INT_MIN = -(2 ** 31)
INT_MAX = 2 ** 31 - 1


def parse_integer(text: str) -> int:
    # 明确采用 32 位有符号整数输入规格，与原测试用例一致。
    if not re.fullmatch(r"[+-]?[0-9]+", text):
        raise ValueError("ERR_INTEGER")
    digits = text.lstrip("+-").lstrip("0") or "0"
    # 先限有效位数，避免超长字符串触发 Python int 的长度限制。
    if len(digits) > 10:
        raise ValueError("ERR_INTEGER")
    value = int(("-" if text.startswith("-") else "") + digits)
    if not INT_MIN <= value <= INT_MAX:
        raise ValueError("ERR_INTEGER")
    return value


def parse_values(args: Sequence[str], count: int) -> List[int]:
    if len(args) != count:
        raise ValueError("ERR_ARGUMENT_COUNT")
    return [parse_integer(value) for value in args]


def evaluate(module: str, args: Sequence[str]) -> str:
    if module not in ("size", "quote", "booking"):
        return "ERR_MODULE"
    try:
        values = parse_values(args, 3 if module == "size" else 4)
    except ValueError as error:
        return str(error)
    if module == "size":
        return check_size(*values)
    if module == "quote":
        return quote(*values).text
    return check_booking(*values)


MESSAGES = {
    "SIZE_OK": "尺寸合格", "BOOKING_OK": "允许预约（本次检查不扣减容量）",
    "ERR_SIZE": "尺寸越界，长宽高均需为 1~200 mm",
    "ERR_QUOTE_RANGE": "重量或时长越界，重量需为 1~500 g，时长需为 1~600 min",
    "ERR_MATERIAL": "材料只能为 0（PLA）或 1（PETG）",
    "ERR_URGENT": "加急状态只能为 0 或 1",
    "ERR_BOOKING_RANGE": "预约数值越界：提前天数 0~7，时长 1~600，剩余时间 0~600",
    "ERR_MAINTENANCE": "维护状态只能为 0 或 1",
    "REJECT_MAINTENANCE": "设备维护中，拒绝预约",
    "REJECT_CAPACITY": "剩余容量不足，拒绝预约",
    "ERR_INTEGER": "请输入 32 位有符号整数，不接受小数或字母",
    "ERR_ARGUMENT_COUNT": "参数个数不正确，请按提示输入，用空格分隔",
    "ERR_MAINTENANCE_SETTING": "设置失败，提前天数需为 0~7，维护状态需为 0/1",
    "MAINTENANCE_UPDATED": "维护状态已更新", "ERR_MODULE": "未知功能模块",
}


def explain(result: str) -> str:
    if result.startswith("PRICE="):
        return "打印费用：" + result[6:] + " 元"
    if result.startswith("ORDER="):
        fields = dict(item.split("=", 1) for item in result.split(";"))
        return f"订单提交成功，编号 {fields['ORDER']}，金额 {fields['PRICE']} 元，剩余 {fields['REMAIN']} 分钟"
    return MESSAGES.get(result, result)
