# 
# Created by y1 on 2026-09-30
#
import pathlib
import logging

import numpy as np

import cv2

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

            return image[y_min:y_max + 1, x_min:x_max + 1]

        image = cv2.imdecode(
            np.frombuffer(path.read_bytes(), dtype=np.uint8),
            cv2.IMREAD_UNCHANGED,
        )

        if image is None:
            raise ValueError(f"Failed to read image: {path}")

        self._image = crop_transparent()

        cv2.imwrite(f"extracted{path.stem}.png", self._image)
