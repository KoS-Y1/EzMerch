#
# Created by y1 on 2026-10-13
#

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QWidget

from gui.i18n import i18n

TranslationKey = str | Callable[[], str]


class UiTranslations:
    def __init__(self):
        self.__bindings: list[Callable[[], None]] = []

    def bind_text(self, setter: Callable[[str], None], key: TranslationKey) -> None:
        def update() -> None:
            setter(i18n.tr(key() if callable(key) else key))
        self.__bindings.append(update)
        update()

    def bind_combo(self, combo: QComboBox, key_for_data: Callable[[Any], str]) -> None:
        def update() -> None:
            with QSignalBlocker(combo):
                for index in range(combo.count()):
                    combo.setItemText(index, i18n.tr(key_for_data(combo.itemData(index))))
        self.__bindings.append(update)
        update()

    def bind_form_label(self, layout: QFormLayout, field: QWidget, key: str) -> None:
        label = layout.labelForField(field)
        if not isinstance(label, QLabel):
            raise TypeError('Translation binding requires a QLabel form label')
        self.bind_text(label.setText, key)

    def retranslate(self) -> None:
        for update in self.__bindings:
            update()
