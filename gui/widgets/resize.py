from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QGroupBox, QVBoxLayout

from gui.i18n import i18n


class ResizePanel(QGroupBox):
    resize_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(i18n.tr('resize.title'), parent)
        self.__layout = QVBoxLayout(self)
        self.__resize = QCheckBox(i18n.tr('resize.enable'))
        self.__layout.addWidget(self.__resize)
        self.__resize.toggled.connect(self.resize_toggled.emit)

    def is_resize_enabled(self) -> bool:
        return self.__resize.isChecked()

    def retranslate_ui(self) -> None:
        self.setTitle(i18n.tr('resize.title'))
        self.__resize.setText(i18n.tr('resize.enable'))
