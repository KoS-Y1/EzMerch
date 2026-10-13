#
# Created by y1 on 2026-10-11
#

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QFrame, QLayout, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout,
    QGridLayout, QScrollArea,
)

from gui.i18n import i18n, Language
from gui.app_settings import AppSettings
from gui.widgets.export import ExportPanel
from gui.widgets.import_images import ImportPanel
from gui.widgets.output_setting import OutputSettingPanel
from gui.widgets.resize import ResizePanel
from gui.widgets.dieline_setting import DielineSettingPanel
from gui.widgets.bleed_setting import BleedSetting

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 720
PANEL_STRETCH = 1
RESIZE_ROW = 0
BLEED_ROW = 1
LEFT_OPERATION_COLUMN = 0
RIGHT_OPERATION_COLUMN = 1
DIELINE_ROW_SPAN = 2
OPERATION_COLUMN_SPAN = 1

class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings):
        super().__init__()
        self.__settings = settings

        self.setWindowTitle(i18n.tr("app.title"))
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.__import = ImportPanel(self)
        self.__output_settings = OutputSettingPanel(self)
        self.__export = ExportPanel(self)
        self.__resize = ResizePanel(self)
        self.__dieline = DielineSettingPanel(self)
        self.__bleed = BleedSetting(self)

        operation_layout = QGridLayout()
        operation_layout.addWidget(self.__resize, RESIZE_ROW, LEFT_OPERATION_COLUMN)
        operation_layout.addWidget(self.__bleed, BLEED_ROW, LEFT_OPERATION_COLUMN)
        operation_layout.addWidget(
            self.__dieline, RESIZE_ROW, RIGHT_OPERATION_COLUMN,
            DIELINE_ROW_SPAN, OPERATION_COLUMN_SPAN,
        )
        operation_layout.setColumnStretch(LEFT_OPERATION_COLUMN, PANEL_STRETCH)
        operation_layout.setColumnStretch(RIGHT_OPERATION_COLUMN, PANEL_STRETCH)

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

        self.__scroll_area = QScrollArea(self)
        self.__scroll_area.setWidgetResizable(True)
        self.__scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.__scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.__scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.__scroll_area.setWidget(content)
        self.setCentralWidget(self.__scroll_area)
        self.__resize.resize_toggled.connect(self.__output_settings.set_resize_enabled)
        self.__output_settings.settings_changed.connect(self.__sync_effect_context)
        self.__output_settings.set_resize_enabled(self.__resize.is_resize_enabled())

        self.__settings_menu = self.menuBar().addMenu(i18n.tr("menu.settings"))
        self.__language_menu = self.__settings_menu.addMenu(i18n.tr("menu.settings.language"))
        self.__language_group = QActionGroup(self)
        self.__language_group.setExclusive(True)
        self.__language_actions = {}
        for language, name in ((Language.EN_US, "English"), (Language.ZH_CN, "简体中文")):
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(language == i18n.get_language())
            action.setData(language)
            self.__language_group.addAction(action)
            self.__language_menu.addAction(action)
            self.__language_actions[language] = action
        self.__language_group.triggered.connect(self.__change_language)

    def __change_language(self, action: QAction) -> None:
        language = action.data()
        if language == i18n.get_language():
            return
        position = self.__scroll_area.verticalScrollBar().value()
        i18n.load(language)
        self.setWindowTitle(i18n.tr("app.title"))
        self.__settings_menu.setTitle(i18n.tr("menu.settings"))
        self.__language_menu.setTitle(i18n.tr("menu.language"))
        for panel in (
            self.__import, self.__resize, self.__bleed,
            self.__dieline, self.__output_settings, self.__export,
        ):
            panel.retranslate_ui()
        QTimer.singleShot(0, lambda: self.__scroll_area.verticalScrollBar().setValue(position))
        self.__settings.set_language(language)

    def __sync_effect_context(self, output) -> None:
        self.__dieline.set_output_context(output.dpi, self.__resize.is_resize_enabled())
        self.__bleed.set_output_context(output.dpi, self.__resize.is_resize_enabled())

    def get_bleed_settings(self) -> BleedSetting:
        return self.__bleed

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
