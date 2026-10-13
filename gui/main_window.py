#
# Created by y1 on 2026-10-11
#

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout

from gui.i18n import i18n
from gui.widgets.export import ExportPanel
from gui.widgets.import_images import ImportPanel
from gui.widgets.output_setting import OutputSettingPanel

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

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.__output_settings, stretch=PANEL_STRETCH)
        output_layout.addWidget(
            self.__export, stretch=PANEL_STRETCH,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        layout.addWidget(self.__import)
        layout.addLayout(output_layout)
        layout.addStretch()

        self.setCentralWidget(content)

    def get_import_panel(self)->ImportPanel:
        return self.__import

    def get_export_panel(self)->ExportPanel:
        return self.__export

    def get_output_settings(self) -> OutputSettingPanel:
        return self.__output_settings
