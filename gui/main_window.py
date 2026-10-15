#
# Created by y1 on 2026-10-11
#

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QFrame, QLayout, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout,
    QScrollArea, QTabBar, QSizePolicy, QMessageBox, QLabel,
)

from gui.i18n import i18n, Language
from gui.app_settings import AppSettings
from gui.ui_translations import UiTranslations
from core.processor import BatchResult
from gui.dialogs.batch_result import BatchOperation, BatchResultDialog
from gui.dialogs.processing import ProcessingDialog
from gui.widgets.export import ExportPanel
from gui.widgets.import_images import ImportPanel
from gui.widgets.output_setting import OutputSettingPanel
from gui.widgets.resize import ResizePanel
from gui.widgets.dieline_setting import DielineSettingPanel
from gui.widgets.bleed_setting import BleedSetting
from gui.export_mode import ExportMode
from gui.widgets.export_modes import IndividualSettingsPage, KissCutSettingsPage, ModeSettingsStack

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 720
PANEL_STRETCH = 1
CENTRAL_MARGIN = 0
MODE_INDIVIDUAL_INDEX = 0
MODE_KISS_CUT_INDEX = 1

class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings):
        super().__init__()
        self.__settings = settings
        self.__processing_dialog = None

        self.setWindowTitle(i18n.tr("app.title"))
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.__import = ImportPanel(self)
        self.__output_settings = OutputSettingPanel(self)
        self.__export = ExportPanel(self)
        self.__individual_page = IndividualSettingsPage()
        self.__kiss_page = KissCutSettingsPage()
        self.__mode_stack = ModeSettingsStack()
        self.__mode_stack.addWidget(self.__individual_page)
        self.__mode_stack.addWidget(self.__kiss_page)
        self.__mode_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.__tabs = QTabBar()
        self.__tabs.addTab(i18n.tr('mode.individual'))
        self.__tabs.setTabData(MODE_INDIVIDUAL_INDEX, ExportMode.INDIVIDUAL)
        self.__tabs.addTab(i18n.tr('mode.kiss_cut'))
        self.__tabs.setTabData(MODE_KISS_CUT_INDEX, ExportMode.KISS_CUT)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.__output_settings, stretch=PANEL_STRETCH)
        output_layout.addWidget(
            self.__export, stretch=PANEL_STRETCH,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        layout.addWidget(self.__import)
        layout.addWidget(self.__mode_stack)
        layout.addLayout(output_layout)
        layout.addStretch()

        self.__scroll_area = QScrollArea(self)
        self.__scroll_area.setWidgetResizable(True)
        self.__scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.__scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.__scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.__scroll_area.setWidget(content)
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(CENTRAL_MARGIN, CENTRAL_MARGIN, CENTRAL_MARGIN, CENTRAL_MARGIN)
        central_layout.addWidget(self.__tabs)
        central_layout.addWidget(self.__scroll_area)
        self.setCentralWidget(central)
        self.__individual_page.get_resize_panel().resize_toggled.connect(self.__sync_mode)
        self.__output_settings.settings_changed.connect(self.__sync_effect_context)
        self.__tabs.currentChanged.connect(self.__mode_changed)
        self.__sync_mode()

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
        self.__about_action = self.menuBar().addAction(i18n.tr('menu.about'))
        self.__about_action.triggered.connect(self.__show_about)
        self.__translations = UiTranslations()
        self.__translations.bind_text(self.setWindowTitle, 'app.title')
        self.__translations.bind_text(self.__settings_menu.setTitle, 'menu.settings')
        self.__translations.bind_text(self.__about_action.setText, 'menu.about')
        self.__translations.bind_text(self.__language_menu.setTitle, 'menu.settings.language')
        self.__translations.bind_text(
            lambda text: self.__tabs.setTabText(MODE_INDIVIDUAL_INDEX, text), 'mode.individual',
        )
        self.__translations.bind_text(
            lambda text: self.__tabs.setTabText(MODE_KISS_CUT_INDEX, text), 'mode.kiss_cut',
        )

    def __show_about(self) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle(i18n.tr('about.title'))
        dialog.setTextFormat(Qt.TextFormat.RichText)
        dialog.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByKeyboard
        )
        dialog.setText(
            '<h3>EzMerch</h3>'
            f'<p>{i18n.tr("about.version", version="0.1.0")}<br>'
            f'{i18n.tr("about.author", author="KoS-Y1")}</p>'
            '<p><a href="https://github.com/KoS-Y1/EzMerch">'
            'https://github.com/KoS-Y1/EzMerch</a></p>'
        )
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.button(QMessageBox.StandardButton.Ok).setText(i18n.tr('about.ok'))
        for label in dialog.findChildren(QLabel):
            label.setOpenExternalLinks(True)
        dialog.exec()

    def __change_language(self, action: QAction) -> None:
        language = action.data()
        if language == i18n.get_language():
            return
        position = self.__scroll_area.verticalScrollBar().value()
        i18n.load(language)
        self.retranslate_ui()
        QTimer.singleShot(0, lambda: self.__scroll_area.verticalScrollBar().setValue(position))
        if not self.__settings.set_language(language):
            self.show_storage_error(self.__settings.get_filename())

    def show_storage_error(self, path: str) -> None:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle(i18n.tr('storage.error.title'))
        dialog.setTextFormat(Qt.TextFormat.PlainText)
        dialog.setText(i18n.tr('storage.error', path=path))
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.button(QMessageBox.StandardButton.Ok).setText(i18n.tr('about.ok'))
        dialog.exec()

    def retranslate_ui(self) -> None:
        self.__translations.retranslate()
        for panel in (
            self.__import, self.__individual_page, self.__kiss_page,
            self.__output_settings, self.__export,
        ):
            panel.retranslate_ui()

    def show_batch_result(self, operation: BatchOperation, result: BatchResult) -> None:
        dialog = BatchResultDialog(operation, result, self)
        dialog.exec()

    def set_processing(self, operation: BatchOperation | None) -> None:
        if operation is not None:
            self.centralWidget().setEnabled(False)
            self.menuBar().setEnabled(False)
            self.__processing_dialog = ProcessingDialog(operation, self)
            self.__processing_dialog.show()
        elif self.__processing_dialog is not None:
            self.__processing_dialog.done(0)
            self.__processing_dialog.deleteLater()
            self.__processing_dialog = None
            self.centralWidget().setEnabled(True)
            self.menuBar().setEnabled(True)

    def show_processing_error(self, message: str) -> None:
        QMessageBox.critical(
            self, i18n.tr('processing.error.title'),
            i18n.tr('processing.error', message=message),
        )

    def closeEvent(self, event) -> None:
        if self.__processing_dialog is not None:
            event.ignore()
        else:
            super().closeEvent(event)

    def get_export_mode(self) -> ExportMode:
        return self.__tabs.tabData(self.__tabs.currentIndex())

    def get_individual_page(self) -> IndividualSettingsPage:
        return self.__individual_page

    def get_kiss_cut_page(self) -> KissCutSettingsPage:
        return self.__kiss_page

    def __mode_changed(self) -> None:
        self.__mode_stack.setCurrentIndex(self.__tabs.currentIndex())
        self.__mode_stack.updateGeometry()
        self.__output_settings.set_export_mode(self.get_export_mode())
        self.__sync_mode()

    def __sync_mode(self) -> None:
        resize_selector = {
            ExportMode.INDIVIDUAL: self.get_resize_panel().is_resize_enabled,
            ExportMode.KISS_CUT: lambda: True,
        }
        enabled = resize_selector[self.get_export_mode()]()
        self.__output_settings.set_resize_enabled(enabled)
        self.__export.set_export_mode(self.get_export_mode())

    def __sync_effect_context(self, output) -> None:
        dpi_selector = {
            ExportMode.INDIVIDUAL: self.__individual_page.set_output_dpi,
            ExportMode.KISS_CUT: self.__kiss_page.set_output_dpi,
        }
        dpi_selector[self.get_export_mode()](output.dpi)

    def get_bleed_settings(self) -> BleedSetting:
        return self.__individual_page.get_bleed_settings()

    def get_resize_panel(self) -> ResizePanel:
        return self.__individual_page.get_resize_panel()

    def get_dieline_settings(self) -> DielineSettingPanel:
        return self.__individual_page.get_dieline_settings()

    def get_import_panel(self)->ImportPanel:
        return self.__import

    def get_export_panel(self)->ExportPanel:
        return self.__export

    def get_output_settings(self) -> OutputSettingPanel:
        return self.__output_settings
