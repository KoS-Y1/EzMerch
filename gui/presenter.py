import pathlib

from core.entity import EntityElements
from core.output_setting import FileFormat
from core.processor import Processor
from gui.main_window import MainWindow
from gui.dialogs.batch_result import BatchOperation
from gui.export_mode import ExportMode


class Presenter:
    def __init__(self, view: MainWindow, processor: Processor):
        self.__view = view
        self.__processor = processor

        view.get_import_panel().images_selected.connect(self.__handle_selection_changed)
        view.get_import_panel().load_requested.connect(self.__handle_load_requested)
        view.get_export_panel().export_requested.connect(self.__handle_export)

    def __handle_selection_changed(self, paths:list[pathlib.Path]) -> None:
        self.__processor.clear_entity_list()
        self.__view.get_import_panel().set_loaded_paths([])

    def __handle_load_requested(self, paths: list[pathlib.Path]) -> None:
        panel = self.__view.get_import_panel()
        panel.set_loaded_paths([])
        result = self.__processor.load_images(paths)
        panel.set_loaded_paths(result.succeeded)
        self.__view.show_batch_result(BatchOperation.LOAD, result)

    def __handle_export(self, destination: pathlib.Path | None, file_format: FileFormat) -> None:
        if destination is None:
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
        def export_individuals():
            return self.__processor.export_individuals(
                destination, file_format, elements,
                resize=page.get_resize_panel().is_resize_enabled(),
            )

        def export_kiss_cut():
            kiss_cut = page.get_kiss_settings().get_kiss_cut_data()
            self.__processor.set_kiss_cut_data(
                margin=kiss_cut.margin, spacing=kiss_cut.spacing, dpi=kiss_cut.dpi,
                margin_unit=kiss_cut.margin_unit, spacing_unit=kiss_cut.spacing_unit,
            )
            return self.__processor.export_kiss_cut(destination, file_format, elements)

        export_selector = {
            ExportMode.INDIVIDUAL: export_individuals,
            ExportMode.KISS_CUT: export_kiss_cut,
        }
        result = export_selector[mode]()
        self.__view.show_batch_result(BatchOperation.EXPORT, result)
