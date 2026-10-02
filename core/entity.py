# 
# Created by y1 on 2026-09-30
#

import pathlib
import logging

import numpy as np

import cv2

from utlis.file_io import load_image

logger = logging.getLogger(__name__)


class Entity:
    """
    Entity of image structs.

    Contains extracted cropped original image, contour
    """

    def __init__(self, path: pathlib.Path):
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
        self.__image = crop_transparent()
        self.__contours = extract_contour()

        contours_image = np.zeros_like(self.__image)
        cv2.drawContours(contours_image, self.__contours, -1, (0, 255, 255, 255), 1)
        cv2.imwrite("contour.png", contours_image)

    def get_name(self) -> str:
        return self.__name

    def get_image(self) -> cv2.typing.MatLike:
        return self.__image
