# 
# Created by y1 on 2026-09-30
#

import pathlib
import logging
from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable

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
        self.__cached_resize = False
        self.__elements: dict[EntityElements, cv2.typing.MatLike | None] = {
            EntityElements.BASE: None,
            EntityElements.DIELINE: None,
            EntityElements.BLEED: None,
        }

    def get_name(self) -> str:
        return self.__name

    def get_elements(self, elements: set[EntityElements], resize: bool = False) -> list[tuple[cv2.typing.MatLike, str]]:
        if resize != self.__cached_resize:
            self.__need_recalculation = True

        if self.__need_recalculation:
            self.__elements = dict.fromkeys(self.__elements, None)
            self.__cached_resize = resize
            self.__need_recalculation = False

        iterate_order = [
            EntityElements.BASE,
            EntityElements.DIELINE,
            EntityElements.BLEED,
        ]

        # TODO: pre calculate size in px for each element before applying resizing or without resizing
        def pre_calculate_sizes() -> dict[EntityElements, tuple[int, int]]:
            if resize:
                return {
                    EntityElements.BASE: self.__output_data.get_size_px(),
                    EntityElements.DIELINE: self.__output_data.get_size_px(),
                    EntityElements.BLEED: self.__output_data.get_size_px(),
                }
            else:
                height, width = self.__image.shape[:2]
                return {
                    EntityElements.BASE: (width, height),
                    EntityElements.DIELINE: (width, height),
                    EntityElements.BLEED: (width, height),
                }

        def is_element_valid(e: EntityElements, width: int, height: int) -> bool:
            img = self.__elements[e]
            if img is None:
                return False

            h, w = img.shape[:2]
            if h == height and w == width:
                return True

            return False

        element_selector: dict[EntityElements, Callable[[int, int, bool], cv2.typing.MatLike]] = {
            EntityElements.BASE: self.__calculate_base,
            EntityElements.DIELINE: self.__calculate_dieline,
            EntityElements.BLEED: self.__calculate_bleed,
        }

        sizes = pre_calculate_sizes()
        output: list[tuple[cv2.typing.MatLike, str]] = []

        for element in iterate_order:
            if element not in elements:
                continue

            image = self.__elements[element]

            if image is None or not is_element_valid(element, *sizes[element]):
                try:
                    image = element_selector[element](*sizes[element], resize)
                except ValueError:
                    logger.exception("Failed to calculate element")
                    raise
                self.__elements[element] = image

            output.append((image, element.name))

        return output

    def set_output_data(self, output_data: OutputData):
        if self.__output_data != output_data:
            self.__output_data = replace(output_data)
            self.__need_recalculation = True

    def __can_resize(self, width: int, height: int) -> bool:
        return self.__output_data.is_valid() and width > 0 and height > 0

    def __resize(self, image: cv2.typing.MatLike, out_width_px: int, out_height_px: int) -> cv2.typing.MatLike:
        if not self.__can_resize(out_width_px, out_height_px):
            logger.warning("Invalid output data to resize, return original image")
            return image

        height, width = image.shape[:2]

        ratio_width = out_width_px / width
        ratio_height = out_height_px / height
        ratio = ratio_width if ratio_width < ratio_height else ratio_height

        try:
            uniform_scaled = cv2.resize(
                image,
                (max(1, round(width * ratio)), max(1, round(height * ratio))),
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

    def __calculate_base(self, width: int, height: int, resize: bool = False) -> cv2.typing.MatLike:
        if not resize:
            return self.__image
        return self.__resize(self.__image, width, height)

    # TODO: may need to apply other things
    def __calculate_dieline(self, width: int, height: int, resize: bool = False) -> cv2.typing.MatLike:
        if not resize:
            return self.__image
        return self.__resize(self.__image, width, height)

    # TODO:
    def __calculate_bleed(self, width: int, height: int, resize: bool = False) -> cv2.typing.MatLike:
        if not resize:
            return self.__image
        return self.__resize(self.__image, width, height)
