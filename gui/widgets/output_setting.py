#
# Created by y1 on 2026-10-12
#

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox

from core.output_setting import DEFAULT_DPI, MAX_OUTPUT_DIMENSION_PX, OutputData, UnitType

from gui.i18n import i18n
from gui.unit_controls import (
    DEFAULT_OUTPUT_DIMENSION_PX, MIN_OUTPUT_DIMENSION_PX, OUTPUT_DPI_OPTIONS,
    configure_pixel_field, read_pixel_value,
)

class OutputSettingPanel(QGroupBox):
    settings_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(i18n.tr("output.title"), parent)

        self.__form_layout = QFormLayout(self)

        self.__width_px = DEFAULT_OUTPUT_DIMENSION_PX
        self.__height_px = DEFAULT_OUTPUT_DIMENSION_PX
        self.__resize_unit = UnitType.PX
        self.__resize_dpi = DEFAULT_DPI

        self.__resize_enabled = False
        self.__unit = QComboBox()
        for unit in UnitType:
            self.__unit.addItem(i18n.tr(f"unit.{unit.value}"), unit)

        self.__resolution = QComboBox()
        for dpi in OUTPUT_DPI_OPTIONS:
            self.__resolution.addItem(i18n.tr(f"output.resolution.{dpi}"), dpi)
        self.__resolution.setCurrentIndex(self.__resolution.findData(DEFAULT_DPI))

        self.__width = QDoubleSpinBox()
        self.__height = QDoubleSpinBox()
        self.__form_layout.addRow(i18n.tr("output.width"), self.__width)
        self.__form_layout.addRow(i18n.tr("output.height"), self.__height)
        self.__form_layout.addRow(i18n.tr("output.unit"), self.__unit)
        self.__form_layout.addRow(i18n.tr("output.resolution"), self.__resolution)

        self.__refresh_dimensions()
        self.__width.valueChanged.connect(self.__width_changed)
        self.__height.valueChanged.connect(self.__height_changed)
        self.__unit.currentIndexChanged.connect(self.__preferences_changed)
        self.__resolution.currentIndexChanged.connect(self.__preferences_changed)

    def set_resize_enabled(self, enabled: bool) -> None:
        self.__resize_enabled = enabled
        self.__display_changed()

    def get_output_data(self) -> OutputData:
        return OutputData(
            width=self.__width_px, height=self.__height_px,
            dpi=self.__resize_dpi if self.__resize_enabled else DEFAULT_DPI,
            unit=UnitType.PX,
        )

    def __to_pixels(self, value: float) -> int:
        return read_pixel_value(
            value, self.__unit.currentData(), self.__resolution.currentData(),
            MIN_OUTPUT_DIMENSION_PX, MAX_OUTPUT_DIMENSION_PX,
        )

    def __width_changed(self, value: float) -> None:
        self.__width_px = self.__to_pixels(value)
        self.__display_changed()

    def __height_changed(self, value: float) -> None:
        self.__height_px = self.__to_pixels(value)
        self.__display_changed()

    def __display_changed(self, *_args) -> None:
        self.__refresh_dimensions()
        self.settings_changed.emit(self.get_output_data())

    def __preferences_changed(self, *_args) -> None:
        if self.__resize_enabled:
            self.__resize_unit = self.__unit.currentData()
            self.__resize_dpi = self.__resolution.currentData()
        self.__display_changed()

    def __refresh_dimensions(self) -> None:
        enabled = self.__resize_enabled
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

        for field, pixels in (
            (self.__width, self.__width_px), (self.__height, self.__height_px),
        ):
            configure_pixel_field(
                field, pixels, unit, dpi,
                MIN_OUTPUT_DIMENSION_PX, MAX_OUTPUT_DIMENSION_PX,
            )
