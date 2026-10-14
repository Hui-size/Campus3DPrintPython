"""成员三：预约条件检查，本函数不修改容量或订单。"""


def check_booking(day: int, minutes: int, remaining: int, maintenance: int) -> str:
    if not (0 <= day <= 7 and 1 <= minutes <= 600 and 0 <= remaining <= 600):
        return "ERR_BOOKING_RANGE"
    if maintenance not in (0, 1):
        return "ERR_MAINTENANCE"
    # 同时处于维护中、容量不足时，维护拒绝优先。
    if maintenance == 1:
        return "REJECT_MAINTENANCE"
    if minutes > remaining:
        return "REJECT_CAPACITY"
    return "BOOKING_OK"
