#
# Created by y1 on 2026-10-12
#
import pathlib

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog, QGroupBox, QVBoxLayout, QComboBox, QLabel,
    QLineEdit, QPushButton,
)

from core.output_setting import FileFormat
from gui.i18n import i18n


class ExportPanel(QGroupBox):
    export_requested = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(i18n.tr("export.title"), parent)

        self.__layout = QVBoxLayout(self)

        self.__file_format = QComboBox()
        for file_format in FileFormat:
            self.__file_format.addItem(i18n.tr(f"format.{file_format.value}"), file_format)
        self.__file_format.setCurrentIndex(self.__file_format.findData(FileFormat.PNG))

        self.__export = QPushButton(i18n.tr("export.export"))
        self.__export.clicked.connect(self.__request_export)
        self.__directory = QLineEdit()
        self.__directory.setPlaceholderText(i18n.tr("export.directory.placeholder"))
        self.__browse = QPushButton(i18n.tr("export.directory.browse"))
        self.__browse.clicked.connect(self.__select_directory)

        self.__layout.addWidget(QLabel(i18n.tr("export.format")))
        self.__layout.addWidget(self.__file_format)
        self.__layout.addWidget(QLabel(i18n.tr("export.directory")))
        self.__layout.addWidget(self.__directory)
        self.__layout.addWidget(self.__browse)
        self.__layout.addWidget(self.__export)

    def get_export_directory(self) -> pathlib.Path | None:
        text = self.__directory.text()
        return pathlib.Path(text) if text.strip() else None

    def __select_directory(self) -> None:
        directory = self.get_export_directory()
        initial = str(directory) if directory is not None and directory.is_dir() else ""
        selected = QFileDialog.getExistingDirectory(
            self, i18n.tr("export.directory.dialog.title"), initial,
        )
        if selected:
            self.__directory.setText(str(pathlib.Path(selected).absolute()))

    def __request_export(self) -> None:
        self.export_requested.emit(
            self.get_export_directory(), self.__file_format.currentData(),
        )
