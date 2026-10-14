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
from gui.export_mode import ExportMode
from gui.i18n import i18n
from gui.ui_translations import UiTranslations


class ExportPanel(QGroupBox):
    export_requested = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(i18n.tr("export.title"), parent)

        self.__mode = ExportMode.INDIVIDUAL
        self.__destinations = {mode: "" for mode in ExportMode}
        self.__layout = QVBoxLayout(self)

        self.__file_format = QComboBox()
        for file_format in FileFormat:
            self.__file_format.addItem(i18n.tr(f"format.{file_format.value}"), file_format)
        self.__file_format.setCurrentIndex(self.__file_format.findData(FileFormat.PNG))

        self.__export = QPushButton(i18n.tr("export.export"))
        self.__export.clicked.connect(self.__request_export)
        self.__destination = QLineEdit()
        self.__destination.setPlaceholderText(i18n.tr("export.directory.placeholder"))
        self.__browse = QPushButton(i18n.tr("export.directory.browse"))
        self.__browse.clicked.connect(self.__select_destination)

        self.__format_label = QLabel(i18n.tr("export.format"))
        self.__destination_label = QLabel(i18n.tr("export.directory"))
        self.__layout.addWidget(self.__format_label)
        self.__layout.addWidget(self.__file_format)
        self.__layout.addWidget(self.__destination_label)
        self.__layout.addWidget(self.__destination)
        self.__layout.addWidget(self.__browse)
        self.__layout.addWidget(self.__export)
        self.__translations = UiTranslations()
        for setter, key in (
            (self.setTitle, 'export.title'),
            (self.__format_label.setText, 'export.format'),
            (self.__destination_label.setText, lambda: self.__destination_key()),
            (self.__destination.setPlaceholderText, lambda: self.__destination_key() + '.placeholder'),
            (self.__browse.setText, 'export.directory.browse'),
            (self.__export.setText, 'export.export'),
        ):
            self.__translations.bind_text(setter, key)
        self.__translations.bind_combo(self.__file_format, lambda fmt: f'format.{fmt.value}')
        self.__file_format.currentIndexChanged.connect(self.__format_changed)

    def __destination_key(self) -> str:
        key_selector = {
            ExportMode.INDIVIDUAL: 'export.directory',
            ExportMode.KISS_CUT: 'export.file',
        }
        return key_selector[self.__mode]

    def set_export_mode(self, mode: ExportMode) -> None:
        if mode != self.__mode:
            self.__destinations[self.__mode] = self.__destination.text()
            self.__mode = mode
            self.__destination.setText(self.__destinations[mode])
            self.__normalize_destination()
        self.retranslate_ui()

    def get_export_destination(self) -> pathlib.Path | None:
        text = self.__destination.text()
        return pathlib.Path(text) if text.strip() else None

    def retranslate_ui(self) -> None:
        self.__translations.retranslate()

    def __normalize_destination(self) -> None:
        def normalize_directory() -> None:
            return

        def normalize_file() -> None:
            destination = self.get_export_destination()
            if destination is not None:
                suffix = '.' + self.__file_format.currentData().value
                self.__destination.setText(str(destination.with_suffix(suffix)))

        normalize_selector = {
            ExportMode.INDIVIDUAL: normalize_directory,
            ExportMode.KISS_CUT: normalize_file,
        }
        normalize_selector[self.__mode]()

    def __format_changed(self) -> None:
        self.__normalize_destination()

    def __select_destination(self) -> None:
        def select_directory() -> str:
            destination = self.get_export_destination()
            initial = str(destination) if destination is not None and destination.is_dir() else ""
            return QFileDialog.getExistingDirectory(
                self, i18n.tr("export.directory.dialog.title"), initial,
            )

        def select_file() -> str:
            self.__normalize_destination()
            destination = self.get_export_destination()
            file_format = self.__file_format.currentData()
            selected, _ = QFileDialog.getSaveFileName(
                self, i18n.tr("export.file.dialog.title"),
                str(destination) if destination is not None else "",
                f"{i18n.tr(f'format.{file_format.value}')} (*.{file_format.value})",
            )
            return selected

        destination_selector = {
            ExportMode.INDIVIDUAL: select_directory,
            ExportMode.KISS_CUT: select_file,
        }
        selected = destination_selector[self.__mode]()
        if selected:
            self.__destination.setText(str(pathlib.Path(selected).absolute()))
            self.__normalize_destination()

    def __request_export(self) -> None:
        self.__normalize_destination()
        destination = self.get_export_destination()
        if destination is not None:
            self.export_requested.emit(destination, self.__file_format.currentData())
