"""Movable sticker with a screen-sized proportional resize handle."""
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QPixmap, QPainter
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget,
)

HANDLE_SIZE = 20
RESIZE_ARROW_INSET = 5
RESIZE_ARROW_HEAD_LENGTH = 5
RESIZE_ARROW_STROKE_WIDTH = 1.5
RESIZE_ARROW_COLOR = '#2878d0'
SELECTION_COLOR = '#2878d0'
HANDLE_COLOR = '#ffffff'
MIN_ARTWORK_SIZE = 1


class ResizeHandle(QGraphicsRectItem):
    def __init__(self, sticker: 'PreviewStickerItem') -> None:
        super().__init__(-HANDLE_SIZE / 2, -HANDLE_SIZE / 2, HANDLE_SIZE, HANDLE_SIZE, sticker)
        self.__sticker = sticker
        self.__start_vector = QPointF()
        self.__start_scale = 1.0
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setBrush(QColor(HANDLE_COLOR))
        pen = QPen(QColor(SELECTION_COLOR))
        pen.setCosmetic(True)
        self.setPen(pen)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
              widget: QWidget | None = None) -> None:
        super().paint(painter, option, widget)

        extent = HANDLE_SIZE / 2 - RESIZE_ARROW_INSET
        start = QPointF(-extent, -extent)
        end = QPointF(extent, extent)
        head_length = RESIZE_ARROW_HEAD_LENGTH

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(RESIZE_ARROW_COLOR), RESIZE_ARROW_STROKE_WIDTH)
        pen.setCosmetic(True)
        painter.setPen(pen)

        painter.drawLine(start, end)
        painter.drawLine(start, start + QPointF(head_length, 0))
        painter.drawLine(start, start + QPointF(0, head_length))
        painter.drawLine(end, end - QPointF(head_length, 0))
        painter.drawLine(end, end - QPointF(0, head_length))
        painter.restore()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.__start_vector = event.scenePos() - self.__sticker.scenePos()
        self.__start_scale = self.__sticker.scale()
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        vector = event.scenePos() - self.__sticker.scenePos()
        start = self.__start_vector
        denominator = QPointF.dotProduct(start, start)
        if denominator > 0:
            scale = self.__start_scale * QPointF.dotProduct(vector, start) / denominator
            bounds = self.__sticker.boundingRect()
            minimum = MIN_ARTWORK_SIZE / min(bounds.width(), bounds.height())
            self.__sticker.setScale(max(minimum, scale))
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()


class PreviewStickerItem(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap) -> None:
        super().__init__(pixmap)
        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        self.__outline = QGraphicsRectItem(self.boundingRect(), self)
        pen = QPen(QColor(SELECTION_COLOR))
        pen.setCosmetic(True)
        self.__outline.setPen(pen)
        self.__outline.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.__outline.hide()

        self.__handle = ResizeHandle(self)
        self.__handle.setPos(self.boundingRect().bottomRight())
        self.__handle.hide()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.__outline.setVisible(bool(value))
            self.__handle.setVisible(bool(value))
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.scene().clearSelection()
            self.setSelected(True)
            event.setModifiers(Qt.KeyboardModifier.NoModifier)
        super().mousePressEvent(event)
