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


DEFAULT_DPI = 300
DEFAULT_UNIT_TYPE = UnitType.PX


@dataclass
class OutputData:
    dpi: int = DEFAULT_DPI
    unit: UnitType = UnitType.PX
    width: float = 0.0
    height: float = 0.0

    def clear(self) -> None:
        self.width = 0.0
        self.height = 0.0
        self.dpi = DEFAULT_DPI
        self.unit = DEFAULT_UNIT_TYPE

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


@dataclass
class DielineData:
    dpi: int = DEFAULT_DPI
    unit: UnitType = UnitType.PX
    thickness: float = 0.0
    distance: float = 0.0

    def clear(self):
        self.dpi = DEFAULT_DPI
        self.unit = UnitType.PX
        self.thickness = 0.0
        self.distance = 0.0

    def get_thickness_px(self) -> int:
        def unit_px() -> int:
            return round(self.thickness)

        def unit_mm() -> int:
            return mm_to_px(self.thickness, self.dpi)

        get_thickness_selector = {
            UnitType.PX: unit_px,
            UnitType.MM: unit_mm,
        }

        return get_thickness_selector[self.unit]()

    def get_distance_px(self) -> int:
        def unit_px() -> int:
            return round(self.distance)

        def unit_mm() -> int:
            return mm_to_px(self.distance, self.dpi)

        get_distance_selector = {
            UnitType.PX: unit_px,
            UnitType.MM: unit_mm,
        }

        return get_distance_selector[self.unit]()

    def is_valid(self):
        return self.distance > 0 and self.thickness > 0 and self.dpi > 0


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

        image = load_image(path)

        if image is None:
            raise ValueError(f"Failed to read image: {path}")

        self.__name = path.stem
        self.__output_data = OutputData() if output_data is None else replace(output_data)
        self.__image = crop_transparent()
        self.__need_recalculation = True
        self.__cached_resize = False
        self.__elements: dict[EntityElements, cv2.typing.MatLike | None] = {
            EntityElements.BASE: None,
            EntityElements.DIELINE: None,
            EntityElements.BLEED: None,
        }

        height, width = self.__image.shape[:2]
        self.__base_size = (width, height)
        self.__dieline_data = DielineData()

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

        # TODO: need to handle bleed line padding
        def pre_calculate_sizes() -> None:
            def base_padding() -> int:
                return 0

            def dieline_padding() -> int:
                return self.__dieline_data.get_thickness_px() + self.__dieline_data.get_distance_px() + 1

            # TODO
            def bleed_padding() -> int:
                return 0

            padding_selector = {
                EntityElements.BASE: base_padding,
                EntityElements.DIELINE: dieline_padding,
                EntityElements.BLEED: bleed_padding,
            }

            paddings: list[int] = []

            for element in elements:
                paddings.append(padding_selector[element]())

            max_padding = max(paddings)

            if resize:
                width, height = self.__output_data.get_size_px()
                self.__base_size = (width - 2 * max_padding, height - 2 * max_padding)
            else:
                width, height = self.__base_size
                output_width =

        def is_element_valid(e: EntityElements) -> bool:
            img = self.__elements[e]
            if img is None:
                return False

            out_width, out_height = self.__output_data.get_size_px()
            return img.shape[:2] == (out_height, out_width)

        element_selector: dict[EntityElements, Callable[[bool], cv2.typing.MatLike]] = {
            EntityElements.BASE: self.__calculate_base,
            EntityElements.DIELINE: self.__calculate_dieline,
            EntityElements.BLEED: self.__calculate_bleed,
        }

        output: list[tuple[cv2.typing.MatLike, str]] = []

        for element in iterate_order:
            if element not in elements:
                continue

            image = self.__elements[element]

            if image is None or not is_element_valid(element):
                try:
                    image = element_selector[element](resize)
                except ValueError:
                    logger.exception("Failed to calculate element")
                    raise
                self.__elements[element] = image

            output.append((image, element.name))

        return output

    def set_output_data(self, output_data: OutputData) -> None:
        if self.__output_data != output_data:
            self.__output_data = replace(output_data)
            self.__need_recalculation = True

    def set_output_size(self, width:float, height:float):
        self.__output_data.width = width
        self.__output_data.height = height

    def set_dieline_data(self, dieline_data: DielineData) -> None:
        if self.__dieline_data != dieline_data:
            self.__dieline_data = replace(dieline_data)
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

        logger.info(f"Successfully resize image from {width, height} to {out_width_px, out_height_px}")
        return uniform_scaled

    @staticmethod
    def __center_image(image: cv2.typing.MatLike, out_width: int, out_height: int) -> cv2.typing.MatLike:
        height, width = image.shape[:2]

        canvas = np.zeros((out_height, out_width, 4), dtype=image.dtype)

        x = (out_width - width) // 2
        y = (out_height - height) // 2
        canvas[y:y + height, x:x + width, :] = image

        return canvas

    def __calculate_base(self, resize: bool = False) -> cv2.typing.MatLike:
        image = self.__resize(self.__image, *self.__base_size) if resize else self.__image

        return self.__center_image(image, *self.__output_data.get_size_px())

    def __calculate_dieline(self, resize: bool = False) -> cv2.typing.MatLike:
        distance = self.__dieline_data.get_distance_px()
        thickness = self.__dieline_data.get_thickness_px()

        gaussian_blur_kernel = (5, 5)

        print(f"thickness{thickness}, distance{distance}")
        if not resize:
            padding = distance + thickness + 1
            _, mask = cv2.threshold(self.__image[:, :, 3], 0, 255, cv2.THRESH_BINARY)
            mask = cv2.copyMakeBorder(mask, padding, padding, padding, padding, cv2.BORDER_CONSTANT, value=0)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * distance + 1, 2 * distance + 1))
            expanded = cv2.dilate(mask, kernel)

            smoothed = cv2.GaussianBlur(expanded, gaussian_blur_kernel, sigmaX=0)
            _, smoothed = cv2.threshold(smoothed, 127, 255, cv2.THRESH_BINARY)
            cv2.imwrite("./smoothed.png", smoothed)
            contour, _ = cv2.findContours(smoothed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            stroke_alpha = np.zeros(mask.shape, dtype=np.uint8)
            cv2.drawContours(stroke_alpha, contour, -1, color=255, thickness=thickness, lineType=cv2.LINE_AA)
            dieline = np.zeros((*mask.shape, 4), dtype=np.uint8)
            dieline[:, :, 3] = stroke_alpha
            dieline_smoothed = cv2.medianBlur(dieline, 5)
            cv2.imwrite("./median1.png", dieline_smoothed)
            cv2.imwrite("./dieline1.png", dieline)
            return self.__center_image(dieline_smoothed, *self.__output_data.get_size_px())
        return self.__resize(self.__image, *self.__output_data.get_size_px())

    # TODO:
    def __calculate_bleed(self, resize: bool = False) -> cv2.typing.MatLike:
        if not resize:
            return self.__image
        return self.__resize(self.__image, *self.__output_data.get_size_px())
