from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QGroupBox, QVBoxLayout

from gui.i18n import i18n
from gui.widgets.settings_panel import SettingsPanel


class ResizePanel(SettingsPanel):
    resize_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__('resize.title', parent)
        self.__layout = QVBoxLayout(self)
        self.__resize = QCheckBox(i18n.tr('resize.enable'))
        self.__layout.addWidget(self.__resize)
        self.__resize.toggled.connect(self._changed)
        self._translations.bind_text(self.__resize.setText, 'resize.enable')
        self._translations.bind_text(self.__resize.setToolTip, 'resize.tooltip')

    def is_resize_enabled(self) -> bool:
        return self.__resize.isChecked()

    def _changed(self) -> None:
        self._refresh()
        self.resize_toggled.emit(self.is_resize_enabled())

    def _refresh(self) -> None:
        # This checkbox has no dependent controls within its own panel.
        pass
