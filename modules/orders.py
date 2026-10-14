"""成员四：完整订单与记录，调用前三个模块。"""

from dataclasses import dataclass
from typing import List, Tuple

from .size_check import check_size
from .pricing import quote, money
from .booking import check_booking


@dataclass(frozen=True)
class Order:
    id: int
    day: int
    grams: int
    minutes: int
    cents: int


class Service:
    def __init__(self) -> None:
        # 八个相对日分别拥有独立容量，重启程序会清空内存状态。
        self._remaining: List[int] = [600] * 8
        self._maintenance: List[int] = [0] * 8
        self._orders: List[Order] = []

    @property
    def orders(self) -> Tuple[Order, ...]:
        return tuple(self._orders)

    def remaining(self, day: int) -> int:
        if not 0 <= day <= 7:
            raise ValueError("提前天数必须为 0~7")
        return self._remaining[day]

    def set_maintenance(self, day: int, value: int) -> str:
        if not (0 <= day <= 7 and value in (0, 1)):
            return "ERR_MAINTENANCE_SETTING"
        self._maintenance[day] = value
        return "MAINTENANCE_UPDATED"

    def submit(self, length: int, width: int, height: int, grams: int,
               minutes: int, material: int, urgent: int, day: int) -> str:
        size_result = check_size(length, width, height)
        if size_result != "SIZE_OK":
            return size_result
        cost = quote(grams, minutes, material, urgent)
        if not cost.ok:
            return cost.text
        if not 0 <= day <= 7:
            return "ERR_BOOKING_RANGE"
        result = check_booking(day, minutes, self._remaining[day], self._maintenance[day])
        if result != "BOOKING_OK":
            return result

        # 所有校验通过后才修改状态。失败不消耗容量、编号或产生记录。
        order_id = len(self._orders) + 1
        self._orders.append(Order(order_id, day, grams, minutes, cost.cents))
        self._remaining[day] -= minutes
        return f"ORDER={order_id};PRICE={money(cost.cents)};REMAIN={self._remaining[day]}"
