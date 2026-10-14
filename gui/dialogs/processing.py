"""A busy indicator that cannot be dismissed during processing."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout

from gui.i18n import i18n


class ProcessingDialog(QDialog):
    def __init__(self, operation, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.tr('processing.title'))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setMinimumWidth(300)
        layout = QVBoxLayout(self)
        label = QLabel(i18n.tr(f'processing.{operation.value}'))
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label)
        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        layout.addWidget(progress)

    def reject(self):
        # Escape must not hide the indicator or allow another operation.
        pass

    def closeEvent(self, event):
        event.ignore()
