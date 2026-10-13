#
# Created by y1 on 2026-10-13
#

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QGroupBox, QFormLayout, QCheckBox, QDoubleSpinBox, QComboBox

from core.entity import BleedData
from core.output_setting import MAX_OUTPUT_DIMENSION_PX, UnitType, DEFAULT_DPI
from gui.i18n import i18n
from gui.unit_controls import configure_pixel_field, read_pixel_value

DEFAULT_BLEED_DISTANCE_PX = 20
MIN_BLEED_DISTANCE_PX = 0
MAX_BLEED_DIMENSION_PX = MAX_OUTPUT_DIMENSION_PX


class BleedSetting(QGroupBox):
    settings_changed = Signal(object, bool)

    def __init__(self, parent=None):
        super().__init__(i18n.tr("bleed.title"), parent)

        self.__form_layout = QFormLayout(self)
        self.__distance_px = DEFAULT_BLEED_DISTANCE_PX
        self.__preferred_unit = UnitType.PX
        self.__dpi = DEFAULT_DPI
        self.__resize_enabled = False
        self.__enable = QCheckBox(i18n.tr("bleed.enable"))
        self.__distance = QDoubleSpinBox()
        self.__unit = QComboBox()
        for unit in UnitType:
            self.__unit.addItem(i18n.tr(f'unit.{unit.value}'), unit)
        self.__form_layout.addRow(self.__enable)
        self.__form_layout.addRow(i18n.tr("bleed.unit"), self.__unit)
        self.__form_layout.addRow(i18n.tr("bleed.distance"), self.__distance)

        self.__refresh()
        self.__enable.toggled.connect(self.__changed)
        self.__distance.valueChanged.connect(self.__distance_changed)
        self.__unit.currentIndexChanged.connect(self.__unit_changed)

    def set_output_context(self, dpi: int, resize_enabled: bool) -> None:
        self.__dpi = dpi
        self.__resize_enabled = resize_enabled
        self.__changed()

    def is_bleed_enabled(self) -> bool:
        return self.__enable.isChecked()

    def get_bleed_data(self) -> BleedData:
        return BleedData(
            distance=self.__distance_px,
            dpi=self.__dpi,
            unit=UnitType.PX
        )
    def __distance_changed(self, value: float) -> None:
        self.__distance_px = read_pixel_value(
            value, self.__unit.currentData(), self.__dpi,
            MIN_BLEED_DISTANCE_PX, MAX_BLEED_DIMENSION_PX,
        )
        self.__changed()

    def __unit_changed(self, *_args) -> None:
        if self.__resize_enabled:
            self.__preferred_unit = self.__unit.currentData()
        self.__changed()

    def __changed(self, *_args) -> None:
        self.__refresh()
        self.settings_changed.emit(self.get_bleed_data(), self.is_bleed_enabled())

    def __refresh(self) -> None:
        enabled = self.is_bleed_enabled()
        unit = self.__preferred_unit if self.__resize_enabled else UnitType.PX
        with QSignalBlocker(self.__unit):
            self.__unit.setCurrentIndex(self.__unit.findData(unit))
        configure_pixel_field(
            self.__distance, self.__distance_px, unit, self.__dpi,
            MIN_BLEED_DISTANCE_PX, MAX_BLEED_DIMENSION_PX,
        )
        self.__distance.setEnabled(enabled)
        self.__unit.setEnabled(enabled and self.__resize_enabled)
        for field in (self.__distance, self.__unit):
            label = self.__form_layout.labelForField(field)
            if label is not None:
                label.setEnabled(field.isEnabled())

    def retranslate_ui(self) -> None:
        self.setTitle(i18n.tr('bleed.title'))
        self.__enable.setText(i18n.tr('bleed.enable'))
        for field, key in (
            (self.__unit, 'bleed.unit'),
            (self.__distance, 'bleed.distance'),
        ):
            label = self.__form_layout.labelForField(field)
            if label is not None:
                label.setText(i18n.tr(key))
        with QSignalBlocker(self.__unit):
            for index in range(self.__unit.count()):
                unit = self.__unit.itemData(index)
                self.__unit.setItemText(index, i18n.tr(f'unit.{unit.value}'))
