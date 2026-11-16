#
# Created by y1 on 2026-11-15
#

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QCloseEvent, QColor, QPainter, QPen, QPixmap, QResizeEvent
from PySide6.QtWidgets import QDialog, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget

from core.kiss_cut import KissCut
from gui.i18n import i18n
from gui.preview_editor import PreviewEditor
from gui.sheet_preview_data import SheetPreviewData, StickerPreviewUpdate


PREVIEW_WIDTH = 900
PREVIEW_HEIGHT = 700
PREVIEW_MIN_WIDTH = 320
PREVIEW_MIN_HEIGHT = 240
CHECKERBOARD_SQUARE_SIZE = 12
CHECKERBOARD_TILE_SIZE = CHECKERBOARD_SQUARE_SIZE * 2
CHECKERBOARD_LIGHT_COLOR = '#eeeeee'
CHECKERBOARD_DARK_COLOR = '#cccccc'
SHEET_BORDER_COLOR = '#666666'


class _SheetView(QGraphicsView):
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class SheetPreviewDialog(QDialog):
    def __init__(self, data: SheetPreviewData,
                 render: Callable[[KissCut, int], StickerPreviewUpdate],
                 apply: Callable[[KissCut], None], parent: QWidget | None = None) -> None:
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

        width = data.width
        height = data.height
        background = scene.addRect(0, 0, width, height, QPen(Qt.PenStyle.NoPen), create_checkerboard_brush())
        background.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        pen = QPen(QColor(SHEET_BORDER_COLOR))
        pen.setCosmetic(True)
        border = scene.addRect(0, 0, width, height, pen)
        border.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        scene.setSceneRect(0, 0, width, height)

        view = _SheetView(scene, self)
        view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(view)

        self.__editor = PreviewEditor(self, scene, data, render, apply)
        layout.addLayout(self.__editor.controls)

    def reject(self) -> None:
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self.__editor.can_close():
            event.ignore()
            return
        event.accept()
        QDialog.reject(self)
