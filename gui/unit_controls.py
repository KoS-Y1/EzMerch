"""Shared display behavior for controls whose canonical values are pixels."""
from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QHBoxLayout, QLabel, QWidget

from core.output_setting import UnitType
from utils.units import mm_to_px, px_to_mm
from gui.i18n import i18n

PIXEL_DECIMALS = 0
MILLIMETER_DECIMALS = 2
PIXEL_STEP = 1
MILLIMETER_STEP = 0.1
MIN_OUTPUT_DIMENSION_PX = 1
DEFAULT_OUTPUT_DIMENSION_PX = 1
OUTPUT_DPI_OPTIONS = (72, 144, 300, 350, 600)
UNIT_ROW_MARGIN = 0
UNIT_LABEL_SPACING = 4


class UnitFieldRow(QWidget):
    """Keep the unit visible without making it part of editable numeric text."""

    def __init__(self, field: QDoubleSpinBox, parent=None):
        super().__init__(parent)
        self.__layout = QHBoxLayout(self)
        self.__layout.setContentsMargins(
            UNIT_ROW_MARGIN, UNIT_ROW_MARGIN, UNIT_ROW_MARGIN, UNIT_ROW_MARGIN,
        )
        self.__layout.setSpacing(UNIT_LABEL_SPACING)
        self.__unit_label = QLabel()
        field.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.__layout.addWidget(field)
        self.__layout.addWidget(self.__unit_label)
        self.set_unit(UnitType.PX)

    def set_unit(self, unit: UnitType) -> None:
        self.set_unit_text(i18n.tr(f"unit.{unit.value}"))

    def set_unit_text(self, text: str) -> None:
        self.__unit_label.setText(text)


def read_pixel_value(value: float, unit: UnitType, dpi: int, min_px: int, max_px: int) -> int:
    pixels = mm_to_px(value, dpi) if unit == UnitType.MM else round(value)
    return max(min_px, min(max_px, pixels))


def configure_pixel_field(
    field: QDoubleSpinBox, pixels: int, unit: UnitType, dpi: int,
    min_px: int, max_px: int,
) -> None:
    millimeters = unit == UnitType.MM
    context = (unit, dpi, min_px, max_px)
    # Keep a committed mm entry (e.g. 3.00) instead of snapping it to 3.05.
    preserve_entry = (
        getattr(field, '_unit_context', None) == context
        and read_pixel_value(field.value(), unit, dpi, min_px, max_px) == pixels
    )
    with QSignalBlocker(field):
        field.setKeyboardTracking(False)
        field.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        field.setDecimals(MILLIMETER_DECIMALS if millimeters else PIXEL_DECIMALS)
        field.setRange(
            px_to_mm(min_px, dpi) if millimeters else min_px,
            px_to_mm(max_px, dpi) if millimeters else max_px,
        )
        field.setSingleStep(MILLIMETER_STEP if millimeters else PIXEL_STEP)
        field.setSuffix('')
        if not preserve_entry:
            field.setValue(px_to_mm(pixels, dpi) if millimeters else pixels)
    field._unit_context = context
