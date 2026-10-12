#
# Created by y1 on 2026-10-12
#

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QWidget,
)

from core.output_setting import (
    DEFAULT_DPI, MAX_OUTPUT_DIMENSION_PX, OutputData, UnitType,
)

from gui.i18n import i18n

from utils.units import mm_to_px, px_to_mm


class OutputSettingPanel(QWidget):
    settings_changed = Signal(object, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._width_px = 1
        self._height_px = 1

        self.resize = QCheckBox(i18n.tr("output.resize"))
        self.unit = QComboBox()
        for unit in UnitType:
            self.unit.addItem(i18n.tr(f"unit.{unit.value}"), unit)

        self.resolution = QComboBox()
        for dpi in (72, 144, 300, 350, 600):
            self.resolution.addItem(i18n.tr(f"output.resolution.{dpi}"), dpi)
        self.resolution.setCurrentIndex(self.resolution.findData(DEFAULT_DPI))

        self.width = QDoubleSpinBox()
        self.height = QDoubleSpinBox()
        for field in (self.width, self.height):
            field.setKeyboardTracking(False)
            field.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)

        layout = QFormLayout(self)
        layout.addRow(self.resize)
        layout.addRow(i18n.tr("output.width"), self.width)
        layout.addRow(i18n.tr("output.height"), self.height)
        layout.addRow(i18n.tr("output.unit"), self.unit)
        layout.addRow(i18n.tr("output.resolution"), self.resolution)

        self._refresh_dimensions()
        self.width.valueChanged.connect(self._width_changed)
        self.height.valueChanged.connect(self._height_changed)
        self.unit.currentIndexChanged.connect(self._display_changed)
        self.resolution.currentIndexChanged.connect(self._display_changed)
        self.resize.toggled.connect(self._display_changed)

    def get_output_data(self) -> OutputData:
        """Return a fresh snapshot suitable for Processor.set_output_data."""
        return OutputData(
            width=self._width_px, height=self._height_px,
            dpi=self.resolution.currentData(), unit=UnitType.PX,
        )

    def _to_pixels(self, value: float) -> int:
        pixels = (
            mm_to_px(value, self.resolution.currentData())
            if self.unit.currentData() == UnitType.MM else round(value)
        )
        return max(1, min(MAX_OUTPUT_DIMENSION_PX, pixels))

    def _width_changed(self, value: float) -> None:
        self._width_px = self._to_pixels(value)
        self._display_changed()

    def _height_changed(self, value: float) -> None:
        self._height_px = self._to_pixels(value)
        self._display_changed()

    def _display_changed(self, *_args) -> None:
        self._refresh_dimensions()
        self.settings_changed.emit(self.get_output_data(), self.resize.isChecked())

    def _refresh_dimensions(self) -> None:
        millimeters = self.unit.currentData() == UnitType.MM
        dpi = self.resolution.currentData()
        for field, pixels in (
                (self.width, self._width_px), (self.height, self._height_px),
        ):
            with QSignalBlocker(field):
                field.setDecimals(6 if millimeters else 0)
                field.setRange(
                    px_to_mm(1, dpi) if millimeters else 1,
                    px_to_mm(MAX_OUTPUT_DIMENSION_PX, dpi)
                    if millimeters else MAX_OUTPUT_DIMENSION_PX,
                )
                field.setSingleStep(0.1 if millimeters else 1)
                field.setSuffix(" mm" if millimeters else " px")
                field.setValue(px_to_mm(pixels, dpi) if millimeters else pixels)
                field.setEnabled(self.resize.isChecked())
