import pathlib

from core.entity import EntityElements
from core.output_setting import FileFormat
from core.processor import Processor
from gui.main_window import MainWindow


class Presenter:
    def __init__(self, view: MainWindow, processor: Processor):
        self.__view = view
        self.__processor = processor

        view.get_import_panel().images_selected.connect(self.__handle_import)
        view.get_export_panel().export_requested.connect(self.__handle_export)

    def __handle_import(self, paths:list[pathlib.Path]) -> None:
        if paths:
            self.__processor.load_images(paths)
        else:
            self.__processor.clear_entity_list()

    def __handle_export(self, destination: pathlib.Path, file_format:FileFormat, elements:set[EntityElements]) -> None:

        panel = self.__view.get_output_settings()
        output = panel.get_output_data()
        self.__processor.set_output_data(
            output.width, output.height, output.dpi, output.unit, output.color,
        )
        self.__processor.set_output_dpi(output.dpi)
        self.__processor.export_all(destination, file_format, elements, resize=panel.is_resize_enabled())
