#
# Created by y1 on 2026-10-11
#
from PySide6.QtWidgets import QMainWindow

from gui.i18n import i18n
from gui.widgets.output_setting import OutputSettingPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(i18n.tr("app.title"))
        self.setFixedSize(640, 720)


        self.output_settings = OutputSettingPanel(self)
        self.setCentralWidget(self.output_settings)
