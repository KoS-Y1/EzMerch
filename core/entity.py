# 
# Created by y1 on 2026-09-30
#

import pathlib
import logging
from dataclasses import dataclass, replace
from enum import Enum

import numpy as np

import cv2

from utils.file_io import load_image
from utils.units import UnitType, mm_to_px

logger = logging.getLogger(__name__)


class EntityElements(Enum):
    BASE = "base"
    DIELINE = "dieline"
    BLEED = "bleed"


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


class Entity:
    """
    Entity of image structs.

    Contains extracted cropped original image, contour
    """

    def __init__(self, path: pathlib.Path, output_data: OutputData | None = None):
        def crop_transparent():
            alpha = image[:, :, 3]

            coords = np.column_stack(np.where(alpha > 0))

            if coords.size == 0:
                raise ValueError(f"Image {path} is completely transparent")

            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)

            cropped_image = image[y_min:y_max + 1, x_min:x_max + 1]

            logger.info(f"Successfully read and crop image: {path}")
            return cropped_image

        def extract_contour():
            alpha = self.__image[:, :, 3]
            _, thresh = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            return contours

        image = load_image(path)

        if image is None:
            raise ValueError(f"Failed to read image: {path}")

        self.__name = path.stem
        self.__output_data = OutputData() if output_data is None else replace(output_data)
        self.__image = crop_transparent()
        self.__contours = extract_contour()
        self.__need_recalculation = True
        self.__elements = {
            EntityElements.BASE: None,
            EntityElements.DIELINE: None,
            EntityElements.BLEED: None,
        }

    def get_name(self) -> str:
        return self.__name

    def get_elements(self, elements: set[EntityElements]) -> list[tuple[cv2.typing.MatLike, str]]:
        # TODO: should return resized image based on the request output size
        def calculate_base_image() -> cv2.typing.MatLike:
            return self.__image

        # TODO
        def calculate_dieline() -> cv2.typing.MatLike:
            return self.__image

        # TODO
        def calculate_bleed() -> cv2.typing.MatLike:
            return self.__image

        # TODO: verify if element's size matches
        def is_element_valid(e: EntityElements) -> bool:
            return False

        element_selector = {
            EntityElements.BASE: calculate_base_image,
            EntityElements.DIELINE: calculate_dieline,
            EntityElements.BLEED: calculate_bleed,
        }

        iterate_order = [
            EntityElements.BASE,
            EntityElements.DIELINE,
            EntityElements.BLEED,
        ]

        output = []

        for element in iterate_order:
            if element not in elements:
                continue

            image = self.__elements[element]

            if image is None or self.__need_recalculation or not is_element_valid(element):
                try:
                    image = element_selector[element]()
                except ValueError as exc:
                    raise exc

            output.append([image, element.name])

        return output

    def __resize(self, image: cv2.typing.MatLike) -> cv2.typing.MatLike:
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
