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
    color: ColorFormat = ColorFormat.RGB
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


@dataclass
class DielineData:
    dpi: int = DEFAULT_DPI
    unit: UnitType = UnitType.PX
    thickness: float = 0.0
    distance: float = 0.0

    def clear(self):
        self.dpi = DEFAULT_DPI
        self.unit = UnitType.PX
        self.thickness = 0.0
        self.distance = 0.0

    def get_thickness_px(self) -> int:
        def unit_px() -> int:
            return round(self.thickness)

        def unit_mm() -> int:
            return mm_to_px(self.thickness, self.dpi)

        get_thickness_selector = {
            UnitType.PX: unit_px,
            UnitType.MM: unit_mm,
        }

        return get_thickness_selector[self.unit]()

    def get_distance_px(self) -> int:
        def unit_px() -> int:
            return round(self.distance)

        def unit_mm() -> int:
            return mm_to_px(self.distance, self.dpi)

        get_distance_selector = {
            UnitType.PX: unit_px,
            UnitType.MM: unit_mm,
        }

        return get_distance_selector[self.unit]()

    def is_valid(self):
        return self.distance >= 0 and self.thickness > 0 and self.dpi > 0


@dataclass
class BleedData:
    dpi: int = DEFAULT_DPI
    unit: UnitType = UnitType.PX
    distance: float = 0.0

    def clear(self):
        self.dpi = DEFAULT_DPI
        self.unit = UnitType.PX
        self.distance = 0.0

    def get_distance_px(self) -> int:
        def unit_px() -> int:
            return round(self.distance)

        def unit_mm() -> int:
            return mm_to_px(self.distance, self.dpi)

        get_distance_selector = {
            UnitType.PX: unit_px,
            UnitType.MM: unit_mm,
        }

        return get_distance_selector[self.unit]()

    def is_valid(self):
        return self.distance >= 0 and self.dpi > 0


@dataclass
class KissCutData:
    dpi: int = DEFAULT_DPI
    margin_unit: UnitType = UnitType.MM
    margin: float = 0.0
    spacing_unit: UnitType = UnitType.MM
    spacing: float = 0.0

    def clear(self):
        self.dpi = DEFAULT_DPI
        self.margin_unit = UnitType.MM
        self.margin = 0.0
        self.spacing_unit = UnitType.MM
        self.spacing = 0.0

    def get_margin_px(self):
        def unit_px() -> int:
            return round(self.margin)

        def unit_mm() -> int:
            return mm_to_px(self.margin, self.dpi)

        get_margin_selector = {
            UnitType.PX: unit_px,
            UnitType.MM: unit_mm,
        }

        return get_margin_selector[self.margin_unit]()

    def get_spacing_px(self):
        def unit_px() -> int:
            return round(self.spacing)

        def unit_mm() -> int:
            return mm_to_px(self.spacing, self.dpi)

        get_spacing_selector = {
            UnitType.PX: unit_px,
            UnitType.MM: unit_mm,
        }

        return get_spacing_selector[self.spacing_unit]()

    def is_valid(self):
        return self.spacing >= 0.0 and self.margin >= 0.0 and self.dpi > 0
