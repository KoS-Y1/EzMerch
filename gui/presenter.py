import pathlib

from PySide6.QtCore import QObject, QThread, Slot

from core.entity import EntityElements
from core.output_setting import FileFormat
from core.processor import Processor
from gui.main_window import MainWindow
from gui.dialogs.batch_result import BatchOperation
from gui.export_mode import ExportMode
from gui.background_operation import OperationWorker


class Presenter(QObject):
    def __init__(self, view: MainWindow, processor: Processor):
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

        def export_individuals():
            return self.__processor.export_individuals(
                destination, file_format, elements,
                resize=resize,
            )

        def export_kiss_cut():
            return self.__processor.export_kiss_cut(destination, file_format, elements)

        export_selector = {
            ExportMode.INDIVIDUAL: export_individuals,
            ExportMode.KISS_CUT: export_kiss_cut,
        }
        self.__start_operation(BatchOperation.EXPORT, export_selector[mode])

    def __start_operation(self, operation: BatchOperation, task) -> None:
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
    def __completed(self, result) -> None:
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
        else:
            if operation == BatchOperation.LOAD:
                self.__view.get_import_panel().set_loaded_paths(result.succeeded)
            self.__view.show_batch_result(operation, result)
