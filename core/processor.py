#
# Created by y1 on {2026-09-30}
#

import logging
import pathlib
from dataclasses import dataclass, replace

import cv2

from .document import Document
from .entity import Entity, OutputData, EntityElements, DEFAULT_DPI, DielineData

from utils.format import FileFormat
from utils.file_io import export
from utils.units import UnitType

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """
    Passed to UI level
    """
    succeeded: list[pathlib.Path]
    failed: list[pathlib.Path]

    def clear_batch(self):
        self.succeeded.clear()
        self.failed.clear()


class Processor:
    """
    Core logic
    """

    def __init__(self):
        self.__load_batch = BatchResult(succeeded=[], failed=[])
        self.__export_batch = BatchResult(succeeded=[], failed=[])

        self.__output_data = OutputData(width=0, height=0, dpi=DEFAULT_DPI)
        self.__dieline_data = DielineData()

        self.__entities: list[Entity] = []

    def set_output_data(self, width: float, height: float, dpi: int = DEFAULT_DPI,
                        unit: UnitType = UnitType.PX):
        output_data =OutputData(width=width, height=height, dpi=dpi, unit=unit)
        if self.__output_data != output_data:
            self.__output_data = replace(output_data)

    def set_output_size(self, width: float, height: float) -> None:
        self.__output_data.width = width
        self.__output_data.height = height

    def set_output_dpi(self, dpi: int) -> None:
        self.__output_data.dpi = dpi
        self.__dieline_data.dpi = dpi

    def set_output_unit(self, unit: UnitType) -> None:
        self.__output_data.unit = unit

    def set_dieline_data(self, thickness: float, distance: float, dpi: int = DEFAULT_DPI,
                         unit: UnitType = UnitType.PX) -> None:
        dieline_data = DielineData(thickness=thickness, distance=distance, unit=unit, dpi=dpi)
        if self.__dieline_data != dieline_data:
            self.__dieline_data = replace(dieline_data)

    def set_dieline_distance(self, distance: float)->None:
        self.__dieline_data.distance = distance

    def set_dieline_thickness(self, thickness: float)->None:
        self.__dieline_data.thickness = thickness

    def set_dieline_unit(self, unit:UnitType)->None:
        self.__dieline_data.unit = unit


    def clear_entity_list(self) -> None:
        self.__entities.clear()

    def load_images(self, paths: list[pathlib.Path]) -> None:
        logger.info("---------- Start loading images ----------")

        self.__load_batch.clear_batch()
        self.clear_entity_list()

        for path in paths:
            try:
                entity = Entity(path)
            except (OSError, ValueError, cv2.error) as exc:
                logger.warning(f"Failed load image: {path}, {exc}")
                self.__load_batch.failed.append(path)
                continue

            self.__entities.append(entity)
            self.__load_batch.succeeded.append(path)

        succeeded = "\n".join(str(path.resolve()) for path in self.__load_batch.succeeded)
        failed = "\n".join(str(path.resolve()) for path in self.__load_batch.failed)
        logger.info(
            f"Finish loading:\n"
            f"Successfully loaded:\n{succeeded or '(none)'}\n"
            f"Failed to load:\n{failed or '(none)'}\n"
        )

    def export_all_cropped(self, dst_path: pathlib.Path, file_format: FileFormat, resize: bool = False) -> None:
        logger.info("---------- Start exporting all cropped images ----------")

        self.__export_batch.clear_batch()

        for entity in self.__entities:

            output_path = (dst_path / f"{entity.get_name()}_cropped").with_suffix(f".{file_format.value}")

            entity.set_output_data(self.__output_data)

            try:
                output_images = entity.get_elements({EntityElements.BASE}, resize)
            except (OSError, cv2.error, ValueError) as exc:
                logger.warning(f"Failed to get elements from {entity.get_name()}, {exc}")
                self.__export_batch.failed.append(output_path)
                continue

            doc = Document()
            doc.add_folder(output_images, entity.get_name())

            try:
                export(output_path, doc, file_format)
            except (OSError, cv2.error, ValueError) as exc:
                logger.warning(f"Failed to export {output_path}, {exc}")
                self.__export_batch.failed.append(output_path)
                continue

            self.__export_batch.succeeded.append(output_path)

        succeeded = "\n".join(str(path.resolve()) for path in self.__export_batch.succeeded)
        failed = "\n".join(str(path.resolve()) for path in self.__export_batch.failed)
        logger.info(
            f"Finish exporting:\n"
            f"Successfully exported:\n{succeeded or '(none)'}\n"
            f"Failed to export:\n{failed or '(none)'}\n"
        )

    def export_all_dieline(self, dst_path: pathlib.Path, file_format: FileFormat, resize: bool = False) -> None:
        logger.info("---------- Start exporting all cropped images ----------")

        self.__export_batch.clear_batch()

        for entity in self.__entities:
            output_path = (dst_path / f"{entity.get_name()}_dieline").with_suffix(f".{file_format.value}")

            entity.set_output_data(self.__output_data)
            entity.set_dieline_data(self.__dieline_data)

            try:
                output_images = entity.get_elements({EntityElements.BASE, EntityElements.DIELINE}, resize)
            except (OSError, cv2.error, ValueError) as exc:
                logger.warning(f"Failed to get elements from {entity.get_name()}, {exc}")
                self.__export_batch.failed.append(output_path)
                continue

            document = Document()
            document.add_folder(output_images, entity.get_name())

            try:
                export(output_path, document, file_format)
            except (OSError, cv2.error, ValueError) as exc:
                logger.warning(f"Failed to export {output_path}, {exc}")
                self.__export_batch.failed.append(output_path)
                continue

            self.__export_batch.succeeded.append(output_path)

            succeeded = "\n".join(str(path.resolve()) for path in self.__export_batch.succeeded)
            failed = "\n".join(str(path.resolve()) for path in self.__export_batch.failed)
            logger.info(
                f"Finish exporting:\n"
                f"Successfully exported:\n{succeeded or '(none)'}\n"
                f"Failed to export:\n{failed or '(none)'}\n"
            )
