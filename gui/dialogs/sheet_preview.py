"""Read-only view of the generated export sheet."""
from numpy.typing import NDArray
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QWidget
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import QDialog, QVBoxLayout, QGraphicsView, QGraphicsScene

from gui.i18n import i18n


PREVIEW_WIDTH = 900
PREVIEW_HEIGHT = 700
PREVIEW_MIN_WIDTH = 320
PREVIEW_MIN_HEIGHT = 240
CHECKERBOARD_SQUARE_SIZE = 12
CHECKERBOARD_TILE_SIZE = CHECKERBOARD_SQUARE_SIZE * 2
CHECKERBOARD_LIGHT_COLOR = '#eeeeee'
CHECKERBOARD_DARK_COLOR = '#cccccc'
SHEET_BORDER_COLOR = '#666666'


class SheetView(QGraphicsView):
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class SheetPreviewDialog(QDialog):
    def __init__(self, image: NDArray[np.uint8], parent: QWidget | None=None) -> None:
        super().__init__(parent)

        def create_checkerboard_brush() -> QBrush:
            tile = QPixmap(CHECKERBOARD_TILE_SIZE, CHECKERBOARD_TILE_SIZE)
            tile.fill(QColor(CHECKERBOARD_LIGHT_COLOR))

            painter = QPainter(tile)
            square_size = CHECKERBOARD_SQUARE_SIZE
            dark_color = QColor(CHECKERBOARD_DARK_COLOR)
            painter.fillRect(0, 0, square_size, square_size, dark_color)
            painter.fillRect(square_size, square_size, square_size, square_size, dark_color)
            painter.end()

            return QBrush(tile)

        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setWindowTitle(i18n.tr('preview.title'))
        self.setModal(True)
        self.setMinimumSize(PREVIEW_MIN_WIDTH, PREVIEW_MIN_HEIGHT)
        available = self.screen().availableGeometry()
        self.resize(min(PREVIEW_WIDTH, available.width()), min(PREVIEW_HEIGHT, available.height()))

        layout = QVBoxLayout(self)
        scene = QGraphicsScene(self)

        height, width = image.shape[:2]
        owned = QImage(image.data, width, height, image.strides[0],
                       QImage.Format.Format_ARGB32).copy()

        scene.addRect(0, 0, width, height, QPen(Qt.PenStyle.NoPen), create_checkerboard_brush())
        scene.addPixmap(QPixmap.fromImage(owned))

        pen = QPen(QColor(SHEET_BORDER_COLOR))
        pen.setCosmetic(True)
        scene.addRect(0, 0, width, height, pen)
        scene.setSceneRect(0, 0, width, height)

        view = SheetView(scene, self)
        view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(view)
