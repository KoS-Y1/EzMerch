import pathlib
from collections.abc import Callable

from PySide6.QtCore import QObject, QThread, Slot

from core.entity import EntityElements
from core.kiss_cut import KissCut
from core.output_setting import FileFormat
from core.processor import BatchResult, Processor
from gui.background_operation import OperationWorker
from gui.dialogs.batch_result import BatchOperation
from gui.dialogs.kiss_cut_preview import KissCutPreviewDialog
from gui.export_mode import ExportMode
from gui.main_window import MainWindow
from gui.kiss_cut_preview.data import KissCutPreviewData, KissCutStickerPreviewUpdate, build_sheet_preview, regenerate_sticker_preview
from gui.kiss_cut_preview.data import sheet_sticker_bounds
from gui.kiss_cut_preview.utils import check_layout
from gui.i18n import i18n


class Presenter(QObject):
    def __init__(self, view: MainWindow, processor: Processor) -> None:
        super().__init__(view)
        self.__view = view
        self.__processor = processor
        self.__thread = None
        self.__worker = None
        self.__result = None
        self.__error = None
        self.__operation = None

        view.get_import_panel().images_selected.connect(self.__handle_selection_changed)
        view.get_import_panel().load_requested.connect(self.__handle_load_requested)
        view.get_export_panel().export_requested.connect(self.__handle_export)
        view.get_export_panel().preview_requested.connect(self.__handle_preview)

    def __handle_selection_changed(self, paths:list[pathlib.Path]) -> None:
        if self.__thread is not None:
            return
        self.__processor.clear_entity_list()
        self.__view.get_import_panel().set_loaded_paths([])

    def __handle_load_requested(self, paths: list[pathlib.Path]) -> None:
        if self.__thread is not None:
            return
        panel = self.__view.get_import_panel()
        panel.set_loaded_paths([])
        selected_paths = paths.copy()
        self.__start_operation(BatchOperation.LOAD, lambda: self.__processor.load_images(selected_paths))

    def __handle_export(self, destination: pathlib.Path | None, file_format: FileFormat) -> None:
        if destination is None or self.__thread is not None:
            return

        mode, elements, resize = self.__collect_settings()
        kiss_settings = self.__view.get_kiss_cut_page().get_kiss_settings().get_kiss_cut_data()
        invalid_message = i18n.tr('export.invalid_layout')

        def export_individuals() -> BatchResult:
            return self.__processor.export_individuals(
                destination, file_format, elements,
                resize=resize,
            )

        def export_kiss_cut() -> BatchResult:
            sheet = self.__processor.prepare_kiss_cut_sheet(elements)
            if check_layout(sheet_sticker_bounds(sheet), sheet.get_output_data().get_size_px(),
                            kiss_settings.get_margin_px(), kiss_settings.get_spacing_px()):
                raise ValueError(invalid_message)
            return self.__processor.export_kiss_cut(destination, file_format, elements)

        export_selector = {
            ExportMode.INDIVIDUAL: export_individuals,
            ExportMode.KISS_CUT: export_kiss_cut,
        }
        self.__start_operation(BatchOperation.EXPORT, export_selector[mode])

    def __collect_settings(self) -> tuple[ExportMode, set[EntityElements], bool]:
        panel = self.__view.get_output_settings()
        output = panel.get_output_data()
        self.__processor.set_output_data(
            output.width, output.height, output.dpi, output.unit, output.color,
        )
        self.__processor.set_output_dpi(output.dpi)
        mode = self.__view.get_export_mode()
        page_selector = {
            ExportMode.INDIVIDUAL: self.__view.get_individual_page,
            ExportMode.KISS_CUT: self.__view.get_kiss_cut_page,
        }
        page = page_selector[mode]()
        dieline_panel = page.get_dieline_settings()
        dieline = dieline_panel.get_dieline_data()
        self.__processor.set_dieline_data(
            dieline.thickness, dieline.distance, dieline.dpi, dieline.unit,
        )
        elements = {EntityElements.BASE}
        if dieline_panel.is_dieline_enabled():
            elements.add(EntityElements.DIELINE)
        bleed_panel = page.get_bleed_settings()
        bleed = bleed_panel.get_bleed_data()
        self.__processor.set_bleed_data(bleed.distance, bleed.dpi, bleed.unit)
        if bleed_panel.is_bleed_enabled():
            elements.add(EntityElements.BLEED)
        resize = mode == ExportMode.INDIVIDUAL and page.get_resize_panel().is_resize_enabled()
        if mode == ExportMode.KISS_CUT:
            kiss_cut = page.get_kiss_settings().get_kiss_cut_data()
            self.__processor.set_kiss_cut_data(
                margin=kiss_cut.margin, spacing=kiss_cut.spacing, dpi=kiss_cut.dpi,
                margin_unit=kiss_cut.margin_unit, spacing_unit=kiss_cut.spacing_unit,
            )

        return mode, elements, resize

    def __handle_preview(self) -> None:
        if self.__thread is not None:
            return
        mode, elements, _ = self.__collect_settings()
        if mode == ExportMode.KISS_CUT:
            settings = self.__view.get_kiss_cut_page().get_kiss_settings().get_kiss_cut_data()
            def prepare_preview() -> KissCutPreviewData:
                sheet = self.__processor.prepare_kiss_cut_sheet(elements).copy()
                return build_sheet_preview(sheet, settings.get_margin_px(), settings.get_spacing_px())

            self.__start_operation(BatchOperation.PREVIEW, prepare_preview)

    def __start_operation(self, operation: BatchOperation, task: Callable[[], object]) -> None:
        self.__operation = operation
        self.__result = None
        self.__error = None
        self.__thread = QThread(self)
        self.__worker = OperationWorker(task)
        self.__worker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__worker.run)
        self.__worker.completed.connect(self.__completed)
        self.__worker.failed.connect(self.__failed)
        self.__worker.finished.connect(self.__thread.quit)
        self.__worker.finished.connect(self.__worker.deleteLater)
        self.__thread.finished.connect(self.__finish_operation)
        self.__thread.finished.connect(self.__thread.deleteLater)
        self.__view.set_processing(operation)
        self.__thread.start()

    @Slot(object)
    def __completed(self, result: BatchResult | KissCutPreviewData) -> None:
        self.__result = result

    @Slot(str)
    def __failed(self, message: str) -> None:
        self.__error = message

    @Slot()
    def __finish_operation(self) -> None:
        operation, result, error = self.__operation, self.__result, self.__error
        # finished can arrive before deferred deletion and native thread teardown.
        self.__thread.wait()
        self.__worker = None
        self.__thread = None
        self.__view.set_processing(None)
        if error is not None:
            self.__view.show_processing_error(error)
        elif operation == BatchOperation.PREVIEW:
            def render_draft(sheet: KissCut, index: int) -> KissCutStickerPreviewUpdate:
                return regenerate_sticker_preview(sheet, index)

            def apply_draft(sheet: KissCut) -> None:
                self.__processor.update_kiss_cut_sheet(sheet)

            dialog = KissCutPreviewDialog(result, render_draft, apply_draft, self.__view)
            dialog.exec()
        else:
            if operation == BatchOperation.LOAD:
                self.__view.get_import_panel().set_loaded_paths(result.succeeded)
            self.__view.show_batch_result(operation, result)
