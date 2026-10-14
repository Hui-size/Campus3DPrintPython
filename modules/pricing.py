"""成员二：打印费用计算。金额以整数分存储，避免浮点误差。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    ok: bool
    cents: int
    text: str


def money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def quote(grams: int, minutes: int, material: int, urgent: int) -> Quote:
    if not (1 <= grams <= 500 and 1 <= minutes <= 600):
        return Quote(False, 0, "ERR_QUOTE_RANGE")
    if material not in (0, 1):
        return Quote(False, 0, "ERR_MATERIAL")
    if urgent not in (0, 1):
        return Quote(False, 0, "ERR_URGENT")

    # PLA 为 20 分/g，PETG 为 30 分/g，机时费为 5 分/min。
    base = grams * (20 if material == 0 else 30) + minutes * 5
    # 加急乘 1.5，最终四舍五入至整数分；不用 Python round 的偶数舍入。
    total = (base * 150 + 50) // 100 if urgent else base
    return Quote(True, total, "PRICE=" + money(total))
