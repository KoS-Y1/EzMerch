#
# Created by y1 on 2026-10-11
#

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout

from gui.i18n import i18n
from gui.widgets.export import ExportPanel
from gui.widgets.import_images import ImportPanel
from gui.widgets.output_setting import OutputSettingPanel
from gui.widgets.resize import ResizePanel
from gui.widgets.dieline_setting import DielineSettingPanel

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 720
PANEL_STRETCH = 1

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(i18n.tr("app.title"))
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        content = QWidget()
        layout = QVBoxLayout(content)

        self.__import = ImportPanel(self)
        self.__output_settings = OutputSettingPanel(self)
        self.__export = ExportPanel(self)
        self.__resize = ResizePanel(self)
        self.__dieline = DielineSettingPanel(self)

        operation_layout = QHBoxLayout()
        operation_layout.addWidget(
            self.__resize, stretch=PANEL_STRETCH, alignment=Qt.AlignmentFlag.AlignTop,
        )
        operation_layout.addWidget(self.__dieline, stretch=PANEL_STRETCH)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.__output_settings, stretch=PANEL_STRETCH)
        output_layout.addWidget(
            self.__export, stretch=PANEL_STRETCH,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        layout.addWidget(self.__import)
        layout.addLayout(operation_layout)
        layout.addLayout(output_layout)
        layout.addStretch()

        self.setCentralWidget(content)
        self.__resize.resize_toggled.connect(self.__output_settings.set_resize_enabled)
        self.__output_settings.settings_changed.connect(self.__sync_dieline_context)
        self.__output_settings.set_resize_enabled(self.__resize.is_resize_enabled())

    def __sync_dieline_context(self, output) -> None:
        self.__dieline.set_output_context(output.dpi, self.__resize.is_resize_enabled())

    def get_resize_panel(self) -> ResizePanel:
        return self.__resize

    def get_dieline_settings(self) -> DielineSettingPanel:
        return self.__dieline

    def get_import_panel(self)->ImportPanel:
        return self.__import

    def get_export_panel(self)->ExportPanel:
        return self.__export

    def get_output_settings(self) -> OutputSettingPanel:
        return self.__output_settings
