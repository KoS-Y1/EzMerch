#
# Created by y1 on {2026-09-30}
#

import logging
import pathlib
from dataclasses import dataclass

import cv2
import numpy as np

from .entity import Entity, OutputData, EntityElements

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

        self.__output_data = OutputData(width=0, height=0, dpi=OutputData.DEFAULT_DPI)

        self.__entities : list[Entity]=[]

    def set_output_data(self, width: float, height: float, dpi: int = OutputData.DEFAULT_DPI,
                        unit: UnitType = UnitType.PX):
        self.__output_data = OutputData(width=width, height=height, dpi=dpi, unit=unit)

    def set_output_size(self, width: float, height: float) -> None:
        self.__output_data.width = width
        self.__output_data.height = height

    def set_output_dpi(self, dpi: int) -> None:
        self.__output_data.dpi = dpi

    def set_output_unit(self, unit: UnitType) -> None:
        self.__output_data.unit = unit

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
        #
        # for entity in self.__entities:
        #     file_path = dst_path / f"{entity.get_name()}_cropped"
        #     output_path = pathlib.Path(f"{file_path}.{file_format.value}")
        #
        #     output_image = entity.get_image()
        #
        #     if resize:
        #         logger.info(f"Resizing image:{file_path}")
        #         output_image = self.__resize_to_output(output_image)
        #
        #     try:
        #         export(file_path, output_image, file_format)
        #     except (OSError, ValueError, cv2.error) as exc:
        #         logger.warning(f"Failed to export {file_path}, {exc}")
        #         self.__export_batch.failed.append(output_path)
        #         continue

            # self.__export_batch.succeeded.append(output_path)
        for entity in self.__entities:
            file_path = dst_path / f"{entity.get_name()}_cropped"
            output_path = file_path.with_suffix(file_format.value)

            entity.set_output_data(self.__output_data)
            output_image = entity.get_elements({EntityElements.BASE})

        succeeded = "\n".join(str(path.resolve()) for path in self.__export_batch.succeeded)
        failed = "\n".join(str(path.resolve()) for path in self.__export_batch.failed)
        logger.info(
            f"Finish exporting:\n"
            f"Successfully exported:\n{succeeded or '(none)'}\n"
            f"Failed to export:\n{failed or '(none)'}\n"
        )