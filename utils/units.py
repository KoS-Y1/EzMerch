# 
# Created by y1 on 2026-10-02
#

INCH_TO_MM = 25.4


def mm_to_px(mm: float, dpi: float) -> int:
    return round(mm * dpi / INCH_TO_MM)


def px_to_mm(px: float, dpi: float) -> float:
    return px * INCH_TO_MM / dpi
