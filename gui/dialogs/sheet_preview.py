"""Temporary sticker editing in the generated sheet preview."""
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from gui.sheet_preview_data import SheetPreviewData
from gui.widgets.preview_sticker import PreviewStickerItem
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
    def __init__(self, data: SheetPreviewData, parent: QWidget | None=None) -> None:
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

        def add_stickers_to_scene(scene: QGraphicsScene) -> None:
            for index, sticker in enumerate(data.stickers):
                image = sticker.image
                image_height, image_width = image.shape[:2]
                owned = QImage(image.data, image_width, image_height, image.strides[0],
                               QImage.Format.Format_ARGB32).copy()
                item = PreviewStickerItem(QPixmap.fromImage(owned))
                item.setPos(sticker.x, sticker.y)
                item.setToolTip(sticker.name)
                item.setZValue(len(data.stickers) - index)
                scene.addItem(item)

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

        add_stickers_to_scene(scene)

        pen = QPen(QColor(SHEET_BORDER_COLOR))
        pen.setCosmetic(True)
        border = scene.addRect(0, 0, width, height, pen)
        border.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        scene.setSceneRect(0, 0, width, height)

        view = SheetView(scene, self)
        view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(view)
