#
# Created by y1 on {2026-09-30}
#

import logging
import pathlib
from dataclasses import dataclass

import cv2
import numpy as np

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

        for entity in self.__entities:
            file_path = dst_path / f"{entity.get_name()}_cropped"
            output_path = pathlib.Path(f"{file_path}.{file_format.value}")

            output_image = entity.get_image()

            if resize:
                logger.info(f"Resizing image:{file_path}")
                output_image = self.__resize_to_output(output_image)

            try:
                export(file_path, output_image, file_format)
            except (OSError, ValueError, cv2.error) as exc:
                logger.warning(f"Failed to export {file_path}, {exc}")
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

    def __resize_to_output(self, image: cv2.typing.MatLike) -> cv2.typing.MatLike:
        if not self.__output_data.is_valid():
            logger.warning("Invalid output data to resize, return original image")
            return image

        height, width = image.shape[:2]
        out_width_px, out_height_px = self.__output_data.get_size_px()

        ratio_width = out_width_px / width
        ratio_height = out_height_px / height
        ratio = ratio_width if ratio_width < ratio_height else ratio_height

        try:
            uniform_scaled = cv2.resize(
                image,
                (round(width * ratio), round(height * ratio)),
                interpolation=cv2.INTER_LINEAR
            )
        except cv2.error as exc:
            logger.warning(f"Failed to resize image: {exc}, return original image")
            return image

        if uniform_scaled is None:
            logger.warning(
                f"Failed to resize image from {width, height} to {out_width_px, out_height_px}, return original image")
            return image

        scaled_height, scaled_width = uniform_scaled.shape[:2]

        out = np.zeros(
            (out_height_px, out_width_px, image.shape[2]),
            dtype=image.dtype
        )

        # Center the resized image
        x = (out_width_px - scaled_width) // 2
        y = (out_height_px - scaled_height) // 2
        out[y:y + scaled_height, x:x + scaled_width, :] = uniform_scaled

        logger.info(f"Successfully resize image from {width, height} to {out_width_px, out_height_px}")
        return out
