#
# Created by y1 on 2026-10-11
#

from dataclasses import dataclass
from enum import Enum

from utils.units import mm_to_px


class UnitType(Enum):
    PX = "px"
    MM = "mm"


class FileFormat(Enum):
    PNG = "png"
    PSD = "psd"


class ColorFormat(Enum):
    RGB = "RGB"
    CMYK = "CMYK"


DEFAULT_DPI = 300
MAX_OUTPUT_DIMENSION_PX = 50_000
DEFAULT_UNIT_TYPE = UnitType.PX


@dataclass
class OutputData:
    dpi: int = DEFAULT_DPI
    unit: UnitType = UnitType.PX
    color:ColorFormat=ColorFormat.RGB
    width: float = 0.0
    height: float = 0.0

    def clear(self) -> None:
        self.width = 0.0
        self.height = 0.0
        self.dpi = DEFAULT_DPI
        self.unit = DEFAULT_UNIT_TYPE
        self.color = ColorFormat.RGB

    def get_size_px(self) -> tuple[int, int]:
        def unit_px() -> tuple[int, int]:
            return round(self.width), round(self.height)

        def unit_mm() -> tuple[int, int]:
            return mm_to_px(self.width, self.dpi), mm_to_px(self.height, self.dpi)

        get_size_selector = {
            UnitType.PX: unit_px,
            UnitType.MM: unit_mm,
        }

        return get_size_selector[self.unit]()

    def is_valid(self) -> bool:
        return self.width > 0 and self.height > 0 and self.dpi > 0


