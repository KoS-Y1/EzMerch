#
# Created by y1 on 2026-11-15
#

from PySide6.QtCore import Qt, QPointF, QRectF, QObject, Signal
from PySide6.QtGui import QColor, QPen, QPixmap, QPainter
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget,
)

from gui.kiss_cut_preview.utils import calculate_resize_scale

HANDLE_SIZE = 20
RESIZE_ARROW_INSET = 5
RESIZE_ARROW_HEAD_LENGTH = 5
RESIZE_ARROW_STROKE_WIDTH = 1.5
RESIZE_ARROW_COLOR = '#2878d0'
SELECTION_COLOR = '#2878d0'
HANDLE_COLOR = '#ffffff'
MIN_ARTWORK_SIZE = 1


class _StickerSignals(QObject):
    gesture_started = Signal(bool)
    gesture_finished = Signal()
    geometry_changed = Signal()


class _ResizeHandle(QGraphicsRectItem):
    def __init__(self, sticker: 'KissCutPreviewStickerItem') -> None:
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
        self.__sticker.signals.gesture_started.emit(True)
        self.__start_vector = event.scenePos() - self.__sticker.scenePos()
        self.__start_scale = self.__sticker.scale()
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        vector = event.scenePos() - self.__sticker.scenePos()
        start = self.__start_vector
        bounds = self.__sticker.boundingRect()
        minimum = MIN_ARTWORK_SIZE / min(bounds.width(), bounds.height())
        scale = calculate_resize_scale(
            (start.x(), start.y()), (vector.x(), vector.y()), self.__start_scale, minimum,
        )
        self.__sticker.setScale(scale)
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.__sticker.signals.gesture_finished.emit()
        event.accept()


class KissCutPreviewStickerItem(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap) -> None:
        super().__init__(pixmap)
        self.signals = _StickerSignals()
        self.__conflicting = False
        self.__tint = QPixmap()
        self.__update_tint()
        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        # Bounding box
        self.__outline = QGraphicsRectItem(self.boundingRect(), self)
        pen = QPen(QColor(SELECTION_COLOR))
        pen.setCosmetic(True)
        self.__outline.setPen(pen)
        self.__outline.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.__outline.hide()

        self.__handle = _ResizeHandle(self)
        self.__handle.setPos(self.boundingRect().bottomRight())
        self.__handle.hide()

    def update_image(self, pixmap: QPixmap) -> None:
        self.setPixmap(pixmap)
        self.__update_tint()
        self.setScale(1.0)
        self.__outline.setRect(self.boundingRect())
        self.__handle.setPos(self.boundingRect().bottomRight())

    def image_scene_bounds(self) -> QRectF:
        size = self.pixmap().deviceIndependentSize()
        return self.mapRectToScene(QRectF(self.offset(), size))

    def set_conflicting(self, conflicting: bool) -> None:
        if self.__conflicting != conflicting:
            self.__conflicting = conflicting
            self.update()

    def __update_tint(self) -> None:
        self.__tint = self.pixmap().copy()
        painter = QPainter(self.__tint)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
        painter.fillRect(self.__tint.rect(), QColor(255, 48, 48, 102))
        painter.end()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
              widget: QWidget | None = None) -> None:
        if self.__conflicting:
            painter.drawPixmap(self.offset(), self.__tint)
        else:
            super().paint(painter, option, widget)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.__outline.setVisible(bool(value))
            self.__handle.setVisible(bool(value))
        elif change in (QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged,
                        QGraphicsItem.GraphicsItemChange.ItemScaleHasChanged):
            self.signals.geometry_changed.emit()
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.signals.gesture_started.emit(False)
            self.scene().clearSelection()
            self.setSelected(True)
            event.setModifiers(Qt.KeyboardModifier.NoModifier)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.signals.gesture_finished.emit()
