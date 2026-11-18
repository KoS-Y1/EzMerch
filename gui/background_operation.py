"""Execute core operations without accessing widgets from a worker thread."""
from collections.abc import Callable
import logging

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class OperationWorker(QObject):
    completed = Signal(object)
    failed = Signal()
    finished = Signal()

    def __init__(self, task: Callable[[], object]) -> None:
        super().__init__()
        self.__task = task

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(self.__task())
        except Exception:
            logger.exception('Background processing failed')
            self.failed.emit()
        finally:
            self.finished.emit()
