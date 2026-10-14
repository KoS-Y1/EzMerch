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
from gui.ui_translations import UiTranslations


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

        self.__format_label = QLabel(i18n.tr("export.format"))
        self.__directory_label = QLabel(i18n.tr("export.directory"))
        self.__layout.addWidget(self.__format_label)
        self.__layout.addWidget(self.__file_format)
        self.__layout.addWidget(self.__directory_label)
        self.__layout.addWidget(self.__directory)
        self.__layout.addWidget(self.__browse)
        self.__layout.addWidget(self.__export)
        self.__mode_notice = QLabel()
        self.__mode_notice.setWordWrap(True)
        self.__mode_notice.hide()
        self.__layout.addWidget(self.__mode_notice)
        self.__translations = UiTranslations()
        for setter, key in (
            (self.setTitle, 'export.title'),
            (self.__format_label.setText, 'export.format'),
            (self.__directory_label.setText, 'export.directory'),
            (self.__directory.setPlaceholderText, 'export.directory.placeholder'),
            (self.__browse.setText, 'export.directory.browse'),
            (self.__export.setText, 'export.export'),
        ):
            self.__translations.bind_text(setter, key)
        self.__translations.bind_combo(self.__file_format, lambda fmt: f'format.{fmt.value}')
        self.__translations.bind_text(self.__mode_notice.setText, 'export.sheet.unavailable')

    def set_export_available(self, available: bool) -> None:
        self.__export.setEnabled(available)
        self.__mode_notice.setVisible(not available)

    def get_export_directory(self) -> pathlib.Path | None:
        text = self.__directory.text()
        return pathlib.Path(text) if text.strip() else None

    def retranslate_ui(self) -> None:
        self.__translations.retranslate()

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
