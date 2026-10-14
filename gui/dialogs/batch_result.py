#
# Created by y1 on 2026-10-13
#

from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from core.processor import BatchResult
from gui.i18n import i18n


class BatchOperation(Enum):
    LOAD = "load"
    EXPORT = "export"


class BatchResultDialog(QMessageBox):
    """Present a completed batch without coupling processing to Qt widgets."""

    def __init__(self, operation: BatchOperation, result: BatchResult, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.tr(f"batch.{operation.value}.title"))
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setIcon(
            QMessageBox.Icon.Warning if result.failed else QMessageBox.Icon.Information,
        )
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.button(QMessageBox.StandardButton.Ok).setText(i18n.tr("batch.ok"))
        if not result.succeeded and not result.failed:
            self.setText(i18n.tr("batch.empty"))
            return

        self.setText(i18n.tr(
            "batch.summary", succeeded=len(result.succeeded), failed=len(result.failed),
        ))
        succeeded = "\n".join(str(path.resolve()) for path in result.succeeded)
        failed = "\n".join(str(path.resolve()) for path in result.failed)
        self.setDetailedText(
            f"{i18n.tr('batch.succeeded')}:\n{succeeded or i18n.tr('batch.none')}\n\n"
            f"{i18n.tr('batch.failed')}:\n{failed or i18n.tr('batch.none')}"
        )
