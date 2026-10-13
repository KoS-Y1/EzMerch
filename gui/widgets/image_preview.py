#
# Created by y1 on 2026-10-12
#

import pathlib

from PySide6.QtCore import QPersistentModelIndex, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QImageReader, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QListView, QListWidget, QListWidgetItem, QStyle, QStyledItemDelegate

PREVIEW_WIDTH = 560
PREVIEW_HEIGHT = 200
THUMBNAIL_SIZE = 88
GRID_CELL_SIZE = 104
THUMBNAIL_SPACING = 4
PREVIEW_BACKGROUND_COLOR = "#b0b0b0"
REMOVE_CROSS_SIZE = 20
REMOVE_CROSS_INSET = 4
REMOVE_CROSS_PADDING = 5
REMOVE_CROSS_STROKE_WIDTH = 2
REMOVE_CROSS_COLOR = "#D32F2F"
LOADED_CHECK_SIZE = 20
LOADED_CHECK_INSET = 4
LOADED_CHECK_STROKE_WIDTH = 3
LOADED_CHECK_COLOR = "#2E7D32"
LOADED_CHECK_POINTS = ((3, 10), (8, 15), (17, 4))
LOADED_ROLE = Qt.ItemDataRole.UserRole + 1


class _PreviewDelegate(QStyledItemDelegate):
    def __init__(self, parent, *, allow_removal: bool):
        super().__init__(parent)
        self.__allow_removal = allow_removal

    @staticmethod
    def cross_rect(item_rect: QRect) -> QRect:
        return QRect(
            item_rect.right() - REMOVE_CROSS_INSET - REMOVE_CROSS_SIZE + 1,
            item_rect.top() + REMOVE_CROSS_INSET,
            REMOVE_CROSS_SIZE,
            REMOVE_CROSS_SIZE,
        )

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.data(LOADED_ROLE):
            origin = QPoint(
                option.rect.right() - LOADED_CHECK_INSET - LOADED_CHECK_SIZE + 1,
                option.rect.bottom() - LOADED_CHECK_INSET - LOADED_CHECK_SIZE + 1,
            )
            points = [origin + QPoint(x, y) for x, y in LOADED_CHECK_POINTS]
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor(LOADED_CHECK_COLOR), LOADED_CHECK_STROKE_WIDTH)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(points[0], points[1])
            painter.drawLine(points[1], points[2])
            painter.restore()
        if not self.__allow_removal or not option.state & QStyle.StateFlag.State_MouseOver:
            return
        cross = self.cross_rect(option.rect).adjusted(
            REMOVE_CROSS_PADDING, REMOVE_CROSS_PADDING,
            -REMOVE_CROSS_PADDING, -REMOVE_CROSS_PADDING,
        )
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(REMOVE_CROSS_COLOR), REMOVE_CROSS_STROKE_WIDTH))
        painter.drawLine(cross.topLeft(), cross.bottomRight())
        painter.drawLine(cross.topRight(), cross.bottomLeft())
        painter.restore()

class ImagePreview(QListWidget):
    """A fixed-size grid displaying the current selection independently of core."""

    remove_requested = Signal(object)

    def __init__(self, parent=None, *, allow_removal: bool = False):
        super().__init__(parent)
        self.__allow_removal = allow_removal
        self.__pressed_cross = QPersistentModelIndex()
        self.setItemDelegate(_PreviewDelegate(self, allow_removal=allow_removal))
        if allow_removal:
            self.setMouseTracking(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(PREVIEW_BACKGROUND_COLOR))
        self.setPalette(palette)
        self.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setMovement(QListView.Movement.Static)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setWrapping(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setIconSize(QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE))
        self.setGridSize(QSize(GRID_CELL_SIZE, GRID_CELL_SIZE))
        self.setSpacing(THUMBNAIL_SPACING)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def set_image_paths(self, paths: list[pathlib.Path]) -> None:
        self.__pressed_cross = QPersistentModelIndex()
        self.clear()
        for path in paths:
            item = QListWidgetItem(self.__thumbnail(path), "")
            item.setToolTip(str(path.resolve()))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.addItem(item)

    def set_loaded_paths(self, paths: list[pathlib.Path]) -> None:
        loaded = {path.resolve() for path in paths}
        for row in range(self.count()):
            item = self.item(row)
            item.setData(LOADED_ROLE, item.data(Qt.ItemDataRole.UserRole).resolve() in loaded)

    def __cross_index(self, position):
        index = self.indexAt(position)
        if (
            self.__allow_removal and index.isValid()
            and _PreviewDelegate.cross_rect(self.visualRect(index)).contains(position)
        ):
            return index
        return None

    def mousePressEvent(self, event):
        self.__pressed_cross = QPersistentModelIndex()
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.__cross_index(event.position().toPoint())
            if index is not None:
                self.__pressed_cross = QPersistentModelIndex(index)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.__pressed_cross.isValid():
            pressed = self.__pressed_cross
            self.__pressed_cross = QPersistentModelIndex()
            index = self.__cross_index(event.position().toPoint())
            event.accept()
            if index is not None and pressed == index:
                self.remove_requested.emit(index.data(Qt.ItemDataRole.UserRole))
            return
        super().mouseReleaseEvent(event)

    def __thumbnail(self, path: pathlib.Path) -> QIcon:
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        bounds = QSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        size = reader.size()
        if size.isValid():
            reader.setScaledSize(size.scaled(bounds, Qt.AspectRatioMode.KeepAspectRatio))
        image = reader.read()
        if image.isNull():
            return self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        pixmap = QPixmap.fromImage(image).scaled(
            bounds,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        return QIcon(pixmap)
