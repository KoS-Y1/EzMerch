#
# Created by y1 on 2026-10-13
#

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QAbstractSpinBox, QComboBox, QDoubleSpinBox, QFormLayout, QGridLayout

from core.output_setting import DEFAULT_DPI, MAX_OUTPUT_DIMENSION_PX, KissCutData, UnitType
from gui.i18n import i18n
from gui.widgets.settings_panel import SettingsPanel
from gui.unit_controls import (
    MILLIMETER_DECIMALS, MILLIMETER_STEP, PIXEL_DECIMALS, PIXEL_STEP, UnitFieldRow,
)
from utils.units import mm_to_px, px_to_mm

DEFAULT_KISS_MARGIN_MM = 3.0
DEFAULT_KISS_SPACING_MM = 3.0
MIN_KISS_DISTANCE_MM = 0.0
MAX_KISS_DISTANCE_PX = MAX_OUTPUT_DIMENSION_PX
KISS_COLUMN_STRETCH = 1


class KissCutSettingPanel(SettingsPanel):
    """Canvas-edge margin and spacing for the kiss-cut sheet."""

    def __init__(self, parent=None):
        super().__init__('kiss.title', parent)
        self.__layout = QGridLayout(self)
        self.__margin_layout = QFormLayout()
        self.__spacing_layout = QFormLayout()
        self.__layout.addLayout(self.__margin_layout, 0, 0)
        self.__layout.addLayout(self.__spacing_layout, 0, 1)
        for column in (0, 1):
            self.__layout.setColumnStretch(column, KISS_COLUMN_STRETCH)
        for layout in (self.__margin_layout, self.__spacing_layout):
            layout.setContentsMargins(0, 0, 0, 0)
        self.__margin_mm = DEFAULT_KISS_MARGIN_MM
        self.__spacing_mm = DEFAULT_KISS_SPACING_MM
        self.__dpi = DEFAULT_DPI
        self.__margin_unit = QComboBox()
        self.__spacing_unit = QComboBox()
        for combo in (self.__margin_unit, self.__spacing_unit):
            for unit in UnitType:
                combo.addItem(i18n.tr(f'unit.{unit.value}'), unit)
            combo.setCurrentIndex(combo.findData(UnitType.MM))

        self.__margin = QDoubleSpinBox()
        self.__spacing = QDoubleSpinBox()
        self.__field_rows = {
            self.__margin: UnitFieldRow(self.__margin),
            self.__spacing: UnitFieldRow(self.__spacing),
        }
        self.__margin_layout.addRow(i18n.tr('kiss.margin.unit'), self.__margin_unit)
        self.__margin_layout.addRow(i18n.tr('kiss.margin'), self.__field_rows[self.__margin])
        self.__spacing_layout.addRow(i18n.tr('kiss.spacing.unit'), self.__spacing_unit)
        self.__spacing_layout.addRow(i18n.tr('kiss.spacing'), self.__field_rows[self.__spacing])
        self.__bind_translations()
        self._refresh()
        self.__margin.valueChanged.connect(self.__margin_changed)
        self.__spacing.valueChanged.connect(self.__spacing_changed)
        self.__margin_unit.currentIndexChanged.connect(self._changed)
        self.__spacing_unit.currentIndexChanged.connect(self._changed)

    def get_kiss_cut_data(self) -> KissCutData:
        margin_unit = self.__margin_unit.currentData()
        spacing_unit = self.__spacing_unit.currentData()
        return KissCutData(
            dpi=self.__dpi,
            margin=self.__margin_mm if margin_unit == UnitType.MM else mm_to_px(self.__margin_mm, self.__dpi),
            margin_unit=margin_unit,
            spacing=self.__spacing_mm if spacing_unit == UnitType.MM else mm_to_px(self.__spacing_mm, self.__dpi),
            spacing_unit=spacing_unit,
        )

    def set_output_dpi(self, dpi: int) -> None:
        self.__dpi = dpi
        maximum_mm = px_to_mm(MAX_KISS_DISTANCE_PX, dpi)
        self.__margin_mm = min(self.__margin_mm, maximum_mm)
        self.__spacing_mm = min(self.__spacing_mm, maximum_mm)
        self._refresh()

    def __margin_changed(self, value: float) -> None:
        self.__margin_mm = (
            px_to_mm(value, self.__dpi)
            if self.__margin_unit.currentData() == UnitType.PX else value
        )
        self._changed()

    def __spacing_changed(self, value: float) -> None:
        self.__spacing_mm = (
            px_to_mm(value, self.__dpi)
            if self.__spacing_unit.currentData() == UnitType.PX else value
        )
        self._changed()

    def _changed(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        for field, value_mm, combo in (
            (self.__margin, self.__margin_mm, self.__margin_unit),
            (self.__spacing, self.__spacing_mm, self.__spacing_unit),
        ):
            unit = combo.currentData()
            millimeters = unit == UnitType.MM
            with QSignalBlocker(field):
                field.setKeyboardTracking(False)
                field.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
                field.setDecimals(MILLIMETER_DECIMALS if millimeters else PIXEL_DECIMALS)
                field.setRange(
                    MIN_KISS_DISTANCE_MM,
                    px_to_mm(MAX_KISS_DISTANCE_PX, self.__dpi) if millimeters else MAX_KISS_DISTANCE_PX,
                )
                field.setSingleStep(MILLIMETER_STEP if millimeters else PIXEL_STEP)
                field.setValue(value_mm if millimeters else mm_to_px(value_mm, self.__dpi))
            self.__field_rows[field].set_unit(unit)

    def __bind_translations(self) -> None:
        self._translations.bind_form_label(self.__margin_layout, self.__margin_unit, 'kiss.margin.unit')
        self._translations.bind_combo(self.__margin_unit, lambda unit: f'unit.{unit.value}')
        self._translations.bind_form_label(self.__spacing_layout, self.__spacing_unit, 'kiss.spacing.unit')
        self._translations.bind_combo(self.__spacing_unit, lambda unit: f'unit.{unit.value}')
        self._translations.bind_form_label(self.__margin_layout, self.__field_rows[self.__margin], 'kiss.margin')
        self._translations.bind_text(
            self.__field_rows[self.__margin].set_unit_text,
            lambda: f'unit.{self.__margin_unit.currentData().value}',
        )
        self._translations.bind_text(self.__field_rows[self.__margin].setToolTip, 'kiss.margin.tooltip')
        self._translations.bind_text(self.__margin_unit.setToolTip, 'kiss.margin.tooltip')
        label = self.__margin_layout.labelForField(self.__field_rows[self.__margin])
        if label is not None:
            self._translations.bind_text(label.setToolTip, 'kiss.margin.tooltip')
        self._translations.bind_form_label(self.__spacing_layout, self.__field_rows[self.__spacing], 'kiss.spacing')
        self._translations.bind_text(
            self.__field_rows[self.__spacing].set_unit_text,
            lambda: f'unit.{self.__spacing_unit.currentData().value}',
        )
        self._translations.bind_text(self.__field_rows[self.__spacing].setToolTip, 'kiss.spacing.tooltip')
        self._translations.bind_text(self.__spacing_unit.setToolTip, 'kiss.spacing.tooltip')
        label = self.__spacing_layout.labelForField(self.__field_rows[self.__spacing])
        if label is not None:
            self._translations.bind_text(label.setToolTip, 'kiss.spacing.tooltip')
