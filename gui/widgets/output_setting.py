#
# Created by y1 on 2026-10-12
#

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QAbstractSpinBox, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox

from core.output_setting import DEFAULT_DPI, MAX_OUTPUT_DIMENSION_PX, OutputData, UnitType

from gui.i18n import i18n
from utils.units import mm_to_px, px_to_mm

class OutputSettingPanel(QGroupBox):
    settings_changed = Signal(object, bool)

    def __init__(self, parent=None):
        super().__init__(i18n.tr("output.title"), parent)

        self.__form_layout = QFormLayout(self)

        self.__width_px = 1
        self.__height_px = 1
        self.__resize_unit = UnitType.PX
        self.__resize_dpi = DEFAULT_DPI

        self.__resize = QCheckBox(i18n.tr("output.resize"))
        self.__unit = QComboBox()
        for unit in UnitType:
            self.__unit.addItem(i18n.tr(f"unit.{unit.value}"), unit)

        self.__resolution = QComboBox()
        for dpi in (72, 144, 300, 350, 600):
            self.__resolution.addItem(i18n.tr(f"output.resolution.{dpi}"), dpi)
        self.__resolution.setCurrentIndex(self.__resolution.findData(DEFAULT_DPI))

        self.__width = QDoubleSpinBox()
        self.__height = QDoubleSpinBox()
        for field in (self.__width, self.__height):
            field.setKeyboardTracking(False)
            field.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)

        self.__form_layout.addRow(self.__resize)
        self.__form_layout.addRow(i18n.tr("output.width"), self.__width)
        self.__form_layout.addRow(i18n.tr("output.height"), self.__height)
        self.__form_layout.addRow(i18n.tr("output.unit"), self.__unit)
        self.__form_layout.addRow(i18n.tr("output.resolution"), self.__resolution)

        self.__refresh_dimensions()
        self.__width.valueChanged.connect(self.__width_changed)
        self.__height.valueChanged.connect(self.__height_changed)
        self.__unit.currentIndexChanged.connect(self.__preferences_changed)
        self.__resolution.currentIndexChanged.connect(self.__preferences_changed)
        self.__resize.toggled.connect(self.__display_changed)

    def is_resize_enabled(self) -> bool:
        return self.__resize.isChecked()

    def get_output_data(self) -> OutputData:
        return OutputData(
            width=self.__width_px, height=self.__height_px,
            dpi=self.__resize_dpi if self.__resize.isChecked() else DEFAULT_DPI,
            unit=UnitType.PX,
        )

    def __to_pixels(self, value: float) -> int:
        pixels = (
            mm_to_px(value, self.__resolution.currentData())
            if self.__unit.currentData() == UnitType.MM else round(value)
        )
        return max(1, min(MAX_OUTPUT_DIMENSION_PX, pixels))

    def __width_changed(self, value: float) -> None:
        self.__width_px = self.__to_pixels(value)
        self.__display_changed()

    def __height_changed(self, value: float) -> None:
        self.__height_px = self.__to_pixels(value)
        self.__display_changed()

    def __display_changed(self, *_args) -> None:
        self.__refresh_dimensions()
        self.settings_changed.emit(self.get_output_data(), self.__resize.isChecked())

    def __preferences_changed(self, *_args) -> None:
        if self.__resize.isChecked():
            self.__resize_unit = self.__unit.currentData()
            self.__resize_dpi = self.__resolution.currentData()
        self.__display_changed()

    def __refresh_dimensions(self) -> None:
        enabled = self.__resize.isChecked()
        unit = self.__resize_unit if enabled else UnitType.PX
        dpi = self.__resize_dpi if enabled else DEFAULT_DPI

        with QSignalBlocker(self.__unit), QSignalBlocker(self.__resolution):
            self.__unit.setCurrentIndex(self.__unit.findData(unit))

            self.__resolution.setCurrentIndex(self.__resolution.findData(dpi))
        for field in (self.__width, self.__height, self.__unit, self.__resolution):
            field.setEnabled(enabled)
            label = self.__form_layout.labelForField(field)
            if label is not None:
                label.setEnabled(enabled)

        millimeters = unit == UnitType.MM

        for field, pixels in (
                (self.__width, self.__width_px), (self.__height, self.__height_px),
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
