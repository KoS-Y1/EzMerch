#
# Created by y1 on 2026-11-15
#

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import QObject, QThread
from PySide6.QtGui import QUndoCommand, QUndoStack, QKeySequence, QPixmap, QImage
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QMessageBox, QGraphicsScene, QGraphicsView, QDialog

from core.kiss_cut import KissCut, SheetGeometry
from gui.background_operation import OperationWorker
from gui.i18n import i18n
from gui.sheet_preview_data import SheetPreviewData, StickerPreviewUpdate
from gui.widgets.preview_sticker import PreviewStickerItem

PREVIEW_UNDO_LIMIT = 100
MIN_STICKER_DIMENSION = 1


class _GeometryCommand(QUndoCommand):
    def __init__(self, editor: 'PreviewEditor', index: int,
                 before: SheetGeometry, after: SheetGeometry) -> None:
        super().__init__()
        self.__editor = editor
        self.__index = index
        self.__before = before
        self.__after = after

    def undo(self) -> None:
        self.__editor._restore(self.__index, self.__before)

    def redo(self) -> None:
        self.__editor._restore(self.__index, self.__after)


class PreviewEditor(QObject):
    def __init__(self, dialog: QDialog, scene: QGraphicsScene, data: SheetPreviewData,
                 render: Callable[[KissCut, int], StickerPreviewUpdate],
                 apply: Callable[[KissCut], None]) -> None:
        super().__init__(dialog)
        self.__dialog = dialog
        self.__scene = scene
        self.__sheet = data.sheet
        self.__baseline = self.__sheet.get_sticker_geometries()
        self.__render = render
        self.__apply = apply
        self.__busy = False
        self.__thread = None
        self.__worker = None
        self.__result = None
        self.__error = None
        self.__applying = False
        self.__close_after_apply = False
        self.__selected = None
        self.__resizing = False
        self.__unresolved: set[int] = set()
        self.__items = []
        self.__data = data

        self.__stack = QUndoStack(self)
        self.__stack.setUndoLimit(PREVIEW_UNDO_LIMIT)
        self.controls = QHBoxLayout()
        self.__undo_action = self.__stack.createUndoAction(dialog, i18n.tr('preview.undo'))
        self.__redo_action = self.__stack.createRedoAction(dialog, i18n.tr('preview.redo'))
        self.__undo_action.setShortcuts(QKeySequence.StandardKey.Undo)
        self.__redo_action.setShortcuts(QKeySequence.StandardKey.Redo)
        dialog.addAction(self.__undo_action)
        dialog.addAction(self.__redo_action)
        self.__undo_button = QPushButton(i18n.tr('preview.undo'))
        self.__redo_button = QPushButton(i18n.tr('preview.redo'))
        self.__apply_button = QPushButton(i18n.tr('preview.apply'))
        self.__undo_button.clicked.connect(self.__stack.undo)
        self.__redo_button.clicked.connect(self.__stack.redo)
        self.__apply_button.clicked.connect(self.__apply_changes)
        self.controls.addWidget(self.__undo_button)
        self.controls.addWidget(self.__redo_button)
        self.controls.addStretch()
        self.controls.addWidget(self.__apply_button)
        self.__stack.indexChanged.connect(self.__update_controls)

        self.__create_sticker_items()
        self.__update_controls()

    def __dirty(self) -> bool:
        return self.__sheet.get_sticker_geometries() != self.__baseline

    def __update_controls(self, *_args: object) -> None:
        self.__undo_action.setEnabled(not self.__busy and self.__stack.canUndo())
        self.__redo_action.setEnabled(not self.__busy and self.__stack.canRedo())
        self.__undo_button.setEnabled(self.__undo_action.isEnabled())
        self.__redo_button.setEnabled(self.__redo_action.isEnabled())
        self.__apply_button.setEnabled(not self.__busy and not self.__unresolved and self.__dirty())
        self.__dialog.findChild(QGraphicsView).setEnabled(not self.__busy)

    def __create_sticker_items(self) -> None:
        for index, sticker in enumerate(self.__data.stickers):
            image = sticker.image
            height, width = image.shape[:2]
            owned = QImage(image.data, width, height, image.strides[0], QImage.Format.Format_ARGB32).copy()
            item = PreviewStickerItem(QPixmap.fromImage(owned))
            item.setPos(sticker.x, sticker.y)
            item.setToolTip(sticker.name)
            item.setZValue(len(self.__data.stickers) - index)
            self.__scene.addItem(item)
            self.__items.append(item)
            item.signals.gesture_started.connect(lambda resizing, index=index: self.__start_gesture(index, resizing))
            item.signals.gesture_finished.connect(lambda index=index: self.__finish_gesture(index))
            item.setSelected(index == self.__selected)

    def __start_gesture(self, index: int, resizing: bool) -> None:
        self.__selected = index
        self.__resizing = resizing

    def __finish_gesture(self, index: int) -> None:
        item = self.__items[index]
        before = self.__sheet.get_sticker_geometry(index)
        target_width = before.width
        target_height = before.height
        if self.__resizing and item.scale() != 1.0:
            padding = self.__data.stickers[index].padding
            target_width = max(MIN_STICKER_DIMENSION, round(item.boundingRect().width() * item.scale()) - 2 * padding)
            target_height = max(MIN_STICKER_DIMENSION, round(target_width * before.height / before.width))
        after = replace(before, x=round(item.pos().x()), y=round(item.pos().y()),
                        width=target_width, height=target_height)
        if after != before:
            self.__stack.push(_GeometryCommand(self, index, before, after))
        elif index in self.__unresolved:
            self.__start_task(False, index)
        else:
            item.setScale(1.0)
            item.setPos(before.x, before.y)

    def _restore(self, index: int, placement: SheetGeometry) -> None:
        before = self.__sheet.get_sticker_geometry(index)
        self.__sheet.set_sticker_geometry(index, placement)
        self.__selected = index
        self.__scene.clearSelection()
        self.__items[index].setSelected(True)
        self.__items[index].setPos(placement.x, placement.y)
        if (before.width, before.height) != (placement.width, placement.height):
            self.__unresolved.add(index)

        if index in self.__unresolved:
            self.__start_task(False, index)
        else:
            self.__update_controls()

    def __apply_changes(self) -> None:
        if not self.__busy and not self.__unresolved and self.__dirty():
            self.__start_task(True)

    def __start_task(self, applying: bool, index: int | None = None) -> None:
        if not applying and index is None:
            raise ValueError("Sticker index is required for regeneration")
        snapshot = self.__sheet.copy()
        self.__busy = True
        self.__applying = applying
        self.__result = None
        self.__error = None
        self.__update_controls()

        def task() -> object:
            if applying:
                self.__apply(snapshot)
                return snapshot
            return self.__render(snapshot, index)

        self.__thread = QThread(self)
        self.__worker = OperationWorker(task)
        self.__worker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__worker.run)
        self.__worker.completed.connect(self.completed)
        self.__worker.failed.connect(self.failed)
        self.__worker.finished.connect(self.__thread.quit)
        self.__thread.finished.connect(self.finished)
        self.__worker.finished.connect(self.__worker.deleteLater)
        self.__thread.start()

    def completed(self, result: object) -> None:
        self.__result = result

    def failed(self, message: str) -> None:
        self.__error = message

    def finished(self) -> None:
        self.__thread.wait()
        self.__thread.deleteLater()
        self.__thread = None
        self.__worker = None
        self.__busy = False
        if self.__error is not None:
            self.__close_after_apply = False
            QMessageBox.critical(self.__dialog, i18n.tr('processing.error.title'), self.__error)
        elif self.__applying:
            self.__baseline = self.__result.get_sticker_geometries()
        else:
            update = self.__result
            self.__sheet = update.sheet
            self.__data.stickers[update.index] = update.sticker

            image = update.sticker.image
            height, width = image.shape[:2]
            owned = QImage(image.data, width, height, image.strides[0], QImage.Format.Format_ARGB32).copy()
            item = self.__items[update.index]
            item.update_image(QPixmap.fromImage(owned))
            item.setPos(update.sticker.x, update.sticker.y)
            self.__unresolved.discard(update.index)
        self.__update_controls()
        if self.__close_after_apply:
            self.__close_after_apply = False
            self.__dialog.close()

    def can_close(self) -> bool:
        if self.__busy:
            return False
        if not self.__dirty():
            return True
        box = QMessageBox(self.__dialog)
        box.setWindowTitle(i18n.tr('preview.title'))
        box.setText(i18n.tr('preview.unapplied'))
        apply_button = box.addButton(i18n.tr('preview.apply'), QMessageBox.ButtonRole.AcceptRole)
        apply_button.setEnabled(not self.__unresolved)
        discard_button = box.addButton(i18n.tr('preview.discard'), QMessageBox.ButtonRole.DestructiveRole)
        cancel_button = box.addButton(i18n.tr('preview.cancel'), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(cancel_button)
        box.exec()
        if box.clickedButton() == discard_button:
            return True
        if box.clickedButton() == apply_button:
            self.__close_after_apply = True
            self.__apply_changes()
        return False
