#
# Created by y1 on 2026-10-12
#

import pathlib

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout

from gui.i18n import i18n
from gui.ui_translations import UiTranslations
from gui.widgets.image_preview import ImagePreview


class ImportPanel(QGroupBox):
    images_selected = Signal(object)
    load_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(i18n.tr("import.title"), parent)

        self.__layout = QVBoxLayout(self)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__images: list[pathlib.Path] = []

        self.__preview = ImagePreview(self, allow_removal=True)
        self.__select = QPushButton(i18n.tr("import.select"))
        self.__load = QPushButton(i18n.tr("import.load"))
        self.__clear = QPushButton(i18n.tr("import.clear"))

        self.__layout.addWidget(self.__preview, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.__buttons_layout = QHBoxLayout()
        self.__buttons_layout.addWidget(self.__select)
        self.__buttons_layout.addWidget(self.__clear)
        self.__buttons_layout.addWidget(self.__load)
        self.__layout.addLayout(self.__buttons_layout)

        self.__select.clicked.connect(self.__select_images)
        self.__load.clicked.connect(self.__request_load)
        self.__clear.clicked.connect(self.__clear_images)
        self.images_selected.connect(self.__preview.set_image_paths)
        self.__preview.remove_requested.connect(self.__remove_image)
        self.__translations = UiTranslations()
        self.__translations.bind_text(self.setTitle, 'import.title')
        for button, key in (
            (self.__select, 'import.select'), (self.__clear, 'import.clear'),
            (self.__load, 'import.load'),
        ):
            self.__translations.bind_text(button.setText, key)
            self.__translations.bind_text(button.setToolTip, key + '.tooltip')

    def get_image_paths(self) -> list[pathlib.Path]:
        return self.__images.copy()

    def set_loaded_paths(self, paths: list[pathlib.Path]) -> None:
        self.__preview.set_loaded_paths(paths)

    def __request_load(self) -> None:
        self.load_requested.emit(self.get_image_paths())

    def __select_images(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            i18n.tr("import.dialog.title"),
            "",
            i18n.tr("import.dialog.filter"),
        )
        if not paths:
            return

        selected = {path.resolve() for path in self.__images}
        changed = False
        for filename in paths:
            path = pathlib.Path(filename).resolve()
            if path not in selected:
                self.__images.append(path)
                selected.add(path)
                changed = True
        if changed:
            self.images_selected.emit(self.get_image_paths())

    def __remove_image(self, path: pathlib.Path) -> None:
        if path in self.__images:
            self.__images.remove(path)
            self.images_selected.emit(self.get_image_paths())

    def __clear_images(self) -> None:
        self.__images.clear()
        self.images_selected.emit(self.get_image_paths())

    def retranslate_ui(self) -> None:
        self.__translations.retranslate()
