"""成员一：模型尺寸检查，单位为毫米。"""


def check_size(length: int, width: int, height: int) -> str:
    """三个尺寸均在闭区间 [1, 200] 内才合格。"""
    if not all(1 <= value <= 200 for value in (length, width, height)):
        return "ERR_SIZE"
    return "SIZE_OK"
