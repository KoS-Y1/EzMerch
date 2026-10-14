"""Execute core operations without accessing widgets from a worker thread."""
import logging

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class OperationWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, task):
        super().__init__()
        self.__task = task

    @Slot()
    def run(self):
        try:
            self.completed.emit(self.__task())
        except Exception as exc:
            logger.exception('Background processing failed')
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()
