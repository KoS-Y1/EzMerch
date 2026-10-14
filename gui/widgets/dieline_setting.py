from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout

from core.entity import DielineData
from core.output_setting import DEFAULT_DPI, MAX_OUTPUT_DIMENSION_PX, UnitType
from gui.i18n import i18n
from gui.widgets.settings_panel import SettingsPanel
from gui.unit_controls import UnitFieldRow, configure_pixel_field, read_pixel_value

DEFAULT_DIELINE_THICKNESS_PX = 4
DEFAULT_DIELINE_DISTANCE_PX = 20
MIN_DIELINE_THICKNESS_PX = 1
MIN_DIELINE_DISTANCE_PX = 0
MAX_DIELINE_DIMENSION_PX = MAX_OUTPUT_DIMENSION_PX


class DielineSettingPanel(SettingsPanel):
    settings_changed = Signal(object, bool)

    def __init__(self, parent=None):
        super().__init__('dieline.title', parent)
        self.__form_layout = QFormLayout(self)
        self.__form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__thickness_px = DEFAULT_DIELINE_THICKNESS_PX
        self.__distance_px = DEFAULT_DIELINE_DISTANCE_PX
        self.__preferred_unit = UnitType.PX
        self.__dpi = DEFAULT_DPI
        self.__resize_enabled = False
        self.__enable = QCheckBox(i18n.tr('dieline.enable'))
        self.__thickness = QDoubleSpinBox()
        self.__distance = QDoubleSpinBox()
        self.__field_rows = {
            self.__thickness: UnitFieldRow(self.__thickness),
            self.__distance: UnitFieldRow(self.__distance),
        }
        self.__unit = QComboBox()
        for unit in UnitType:
            self.__unit.addItem(i18n.tr(f'unit.{unit.value}'), unit)

        self.__form_layout.addRow(self.__enable)
        self.__form_layout.addRow(i18n.tr('dieline.unit'), self.__unit)
        self.__form_layout.addRow(i18n.tr('dieline.thickness'), self.__field_rows[self.__thickness])
        self.__form_layout.addRow(i18n.tr('dieline.distance'), self.__field_rows[self.__distance])

        self.__bind_translations()
        self._refresh()
        self.__enable.toggled.connect(self._changed)
        self.__thickness.valueChanged.connect(self.__thickness_changed)
        self.__distance.valueChanged.connect(self.__distance_changed)
        self.__unit.currentIndexChanged.connect(self.__unit_changed)

    def set_output_context(self, dpi: int, resize_enabled: bool) -> None:
        self.__dpi = dpi
        self.__resize_enabled = resize_enabled
        self._changed()

    def is_dieline_enabled(self) -> bool:
        return self.__enable.isChecked()

    def get_dieline_data(self) -> DielineData:
        return DielineData(
            thickness=self.__thickness_px, distance=self.__distance_px,
            dpi=self.__dpi, unit=UnitType.PX,
        )

    def __thickness_changed(self, value: float) -> None:
        self.__thickness_px = read_pixel_value(
            value, self.__unit.currentData(), self.__dpi,
            MIN_DIELINE_THICKNESS_PX, MAX_DIELINE_DIMENSION_PX,
        )
        self._changed()

    def __distance_changed(self, value: float) -> None:
        self.__distance_px = read_pixel_value(
            value, self.__unit.currentData(), self.__dpi,
            MIN_DIELINE_DISTANCE_PX, MAX_DIELINE_DIMENSION_PX,
        )
        self._changed()

    def __unit_changed(self, *_args) -> None:
        if self.__resize_enabled:
            self.__preferred_unit = self.__unit.currentData()
        self._changed()

    def _changed(self) -> None:
        self._refresh()
        self.settings_changed.emit(self.get_dieline_data(), self.is_dieline_enabled())

    def _refresh(self) -> None:
        enabled = self.is_dieline_enabled()
        unit = self.__preferred_unit if self.__resize_enabled else UnitType.PX
        with QSignalBlocker(self.__unit):
            self.__unit.setCurrentIndex(self.__unit.findData(unit))
        for field, pixels, minimum in (
            (self.__thickness, self.__thickness_px, MIN_DIELINE_THICKNESS_PX),
            (self.__distance, self.__distance_px, MIN_DIELINE_DISTANCE_PX),
        ):
            configure_pixel_field(field, pixels, unit, self.__dpi, minimum, MAX_DIELINE_DIMENSION_PX)
            self.__field_rows[field].set_unit(unit)
            (self.__field_rows[field] if isinstance(field, QDoubleSpinBox) else field).setEnabled(enabled)
            label = self.__form_layout.labelForField((self.__field_rows[field] if isinstance(field, QDoubleSpinBox) else field))
            if label is not None:
                label.setEnabled(enabled)
        self.__unit.setEnabled(enabled and self.__resize_enabled)
        label = self.__form_layout.labelForField(self.__unit)
        if label is not None:
            label.setEnabled(enabled and self.__resize_enabled)

    def __bind_translations(self) -> None:
        self._translations.bind_text(self.__enable.setText, 'dieline.enable')
        self._translations.bind_form_label(self.__form_layout, self.__unit, 'dieline.unit')
        self._translations.bind_combo(self.__unit, lambda unit: f'unit.{unit.value}')
        self._translations.bind_form_label(self.__form_layout, self.__field_rows[self.__thickness], 'dieline.thickness')
        self._translations.bind_text(
            self.__field_rows[self.__thickness].set_unit_text,
            lambda: f'unit.{self.__unit.currentData().value}',
        )
        self._translations.bind_form_label(self.__form_layout, self.__field_rows[self.__distance], 'dieline.distance')
        self._translations.bind_text(
            self.__field_rows[self.__distance].set_unit_text,
            lambda: f'unit.{self.__unit.currentData().value}',
        )
