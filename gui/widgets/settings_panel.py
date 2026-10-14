#
# Created by y1 on 2026-10-13
#

from PySide6.QtWidgets import QGroupBox

from gui.ui_translations import UiTranslations


class SettingsPanel(QGroupBox):
    """Settings lifecycle contract; subclasses own state and notifications."""

    def __init__(self, title_key: str, parent=None):
        super().__init__(parent)
        self.__translations = UiTranslations()
        self.__translations.bind_text(self.setTitle, title_key)

    @property
    def _translations(self) -> UiTranslations:
        return self.__translations

    def retranslate_ui(self) -> None:
        self.__translations.retranslate()

    def _changed(self) -> None:
        raise NotImplementedError('Settings panels must implement _changed()')

    def _refresh(self) -> None:
        raise NotImplementedError('Settings panels must implement _refresh()')
