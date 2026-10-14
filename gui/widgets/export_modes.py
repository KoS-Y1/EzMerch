from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from gui.ui_translations import UiTranslations
from gui.widgets.bleed_setting import BleedSetting
from gui.widgets.dieline_setting import DielineSettingPanel
from gui.widgets.kiss_cut_setting import KissCutSettingPanel
from gui.widgets.resize import ResizePanel

PAGE_MARGIN = 0
COLUMN_STRETCH = 1
TOP_ROW = 0
BOTTOM_ROW = 1
LEFT_COLUMN = 0
RIGHT_COLUMN = 1
TWO_ROWS = 2
ONE_COLUMN = 1


class ModeSettingsStack(QStackedWidget):
    """Size the scrollable content for the active page only."""

    def sizeHint(self) -> QSize:
        page = self.currentWidget()
        return page.sizeHint() if page is not None else super().sizeHint()

    def minimumSizeHint(self) -> QSize:
        page = self.currentWidget()
        return page.minimumSizeHint() if page is not None else super().minimumSizeHint()


class IndividualSettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__resize = ResizePanel(self)
        self.__bleed = BleedSetting(self)
        self.__dieline = DielineSettingPanel(self)
        self.__layout = QGridLayout(self)
        self.__layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        self.__layout.addWidget(self.__resize, TOP_ROW, LEFT_COLUMN)
        self.__layout.addWidget(self.__bleed, BOTTOM_ROW, LEFT_COLUMN)
        self.__layout.addWidget(self.__dieline, TOP_ROW, RIGHT_COLUMN, TWO_ROWS, ONE_COLUMN)
        self.__layout.setColumnStretch(LEFT_COLUMN, COLUMN_STRETCH)
        self.__layout.setColumnStretch(RIGHT_COLUMN, COLUMN_STRETCH)

    def get_resize_panel(self) -> ResizePanel:
        return self.__resize

    def get_bleed_settings(self) -> BleedSetting:
        return self.__bleed

    def get_dieline_settings(self) -> DielineSettingPanel:
        return self.__dieline

    def set_output_dpi(self, dpi: int) -> None:
        resize = self.__resize.is_resize_enabled()
        self.__bleed.set_output_context(dpi, resize)
        self.__dieline.set_output_context(dpi, resize)

    def retranslate_ui(self) -> None:
        for panel in (self.__resize, self.__bleed, self.__dieline):
            panel.retranslate_ui()


class KissCutSettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__layout = QVBoxLayout(self)
        self.__layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        self.__kiss = KissCutSettingPanel(self)
        self.__effects = QGroupBox(self)
        self.__effects_layout = QHBoxLayout(self.__effects)
        self.__bleed = BleedSetting(self.__effects)
        self.__dieline = DielineSettingPanel(self.__effects)
        self.__effects_layout.addWidget(self.__bleed, stretch=COLUMN_STRETCH, alignment=Qt.AlignmentFlag.AlignTop)
        self.__effects_layout.addWidget(self.__dieline, stretch=COLUMN_STRETCH, alignment=Qt.AlignmentFlag.AlignTop)
        self.__layout.addWidget(self.__kiss)
        self.__layout.addWidget(self.__effects)
        self.__translations = UiTranslations()
        self.__translations.bind_text(self.__effects.setTitle, 'mode.sticker_settings')

    def get_kiss_settings(self) -> KissCutSettingPanel:
        return self.__kiss

    def get_bleed_settings(self) -> BleedSetting:
        return self.__bleed

    def get_dieline_settings(self) -> DielineSettingPanel:
        return self.__dieline

    def set_output_dpi(self, dpi: int) -> None:
        self.__kiss.set_output_dpi(dpi)
        self.__bleed.set_output_context(dpi, True)
        self.__dieline.set_output_context(dpi, True)

    def retranslate_ui(self) -> None:
        self.__translations.retranslate()
        for panel in (self.__kiss, self.__bleed, self.__dieline):
            panel.retranslate_ui()
