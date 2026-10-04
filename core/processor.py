#
# Created by y1 on {2026-09-30}
#

import logging
import pathlib
from dataclasses import dataclass

import cv2

from .entity import Entity

from utils.format import FileFormat
from utils.file_io import export
from utils.units import UnitType, mm_to_px

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

    @dataclass
    class OutputData:
        DEFAULT_DPI = 300
        DEFAULT_UNIT_TYPE = UnitType.PX

        dpi: int = DEFAULT_DPI
        width: float = 0
        height: float = 0
        unit: UnitType = UnitType.PX

        def clear_output(self) -> None:
            self.width = 0
            self.height = 0
            self.dpi = self.DEFAULT_DPI
            self.unit = self.DEFAULT_UNIT_TYPE

        def get_size_px(self) -> tuple[int, int]:
            def unit_px() -> tuple[int, int]:
                return round(self.width), round(self.height)

            def unit_mm() -> tuple[int, int]:
                return mm_to_px(self.width, self.dpi), mm_to_px(self.height, self.dpi)

            get_size_selector = {
                UnitType.PX: unit_px,
                UnitType.MM: unit_mm,
            }

            return get_size_selector[self.unit]()

        def is_valid(self) -> bool:
            return self.width > 0 and self.height > 0 and self.dpi > 0

    def __init__(self):
        self.__load_batch = BatchResult(succeeded=[], failed=[])
        self.__export_batch = BatchResult(succeeded=[], failed=[])

        self.__output_data = self.OutputData(width=0, height=0, dpi=self.OutputData.DEFAULT_DPI)

        self.__entities = []

    def set_output_data(self, width: float, height: float, dpi: int = OutputData.DEFAULT_DPI,
                        unit: UnitType = UnitType.PX):
        self.__output_data = self.OutputData(width=width, height=height, dpi=dpi, unit=unit)

    def set_output_size(self, width: float, height: float) -> None:
        self.__output_data.width = width
        self.__output_data.height = height

    def set__output_dpi(self, dpi: int) -> None:
        self.__output_data.dpi = dpi

    def set_output_unit(self, unit: UnitType) -> None:
        self.__output_data.unit = unit

    def clear_entity_list(self) -> None:
        self.__entities.clear()

    def load_images(self, paths: list[pathlib.Path]) -> None:
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

            for log in self.__load_batch.succeeded:
                print(f"Succeed {str(log)}")

            for log in self.__load_batch.failed:
                print(f"Failed {str(log)}")

    def output_all_cropped(self, dst_path: pathlib.Path, file_format: FileFormat, resize: bool = False) -> None:
        self.__export_batch.clear_batch()

        for entity in self.__entities:
            file_path = dst_path / f"{entity.get_name()}_cropped"

            try:
                export(file_path, entity.get_image(), file_format)
            except (OSError, ValueError, cv2.error) as exc:
                logger.warning(f"Failed to export {file_path}, {exc}")
                self.__export_batch.failed.append(file_path)
                continue

            self.__export_batch.succeeded.append(file_path)

    def __resize_to_output(self, image: cv2.typing.MatLike) -> cv2.typing.MatLike:
        if not self.__output_data.is_valid():
            logger.warning("Invalid output data to resize, return original image")
            return image

        height, width = image.shape[:2]

        out_width_px, out_height_px = self.__output_data.get_size_px()

        out = cv2.resize(image, (out_width_px, out_height_px))

        if out is None:
            logger.warning(
                f"Failed to resize image from {width, height} to {out_width_px, out_height_px}, return original image")
            return image

        logger.info(f"Successfully resize image from {width, height} to {out_width_px, out_height_px}")
        return out
