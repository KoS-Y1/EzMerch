# 
# Created by y1 on 2026-09-30
#
import pathlib
import logging

import cv2
import numpy as np

from .format import FileFormat

logger = logging.getLogger(__name__)


def export(path: pathlib.Path, image: cv2.typing.MatLike, file_type: FileFormat) -> None:
    output_path = pathlib.Path(f"{path}.{file_type.value}")

    def export_png():
        if not cv2.imwrite(output_path, image):
            raise ValueError(f"Failed to write image: {output_path}")

    def export_psd():
        # TODO: placeholder for now
        raise ValueError(f"Failed to write image: {output_path}, currently .psd not supported")

    export_selector = {
        FileFormat.PNG: export_png,
        FileFormat.PSD: export_psd
    }

    export_selector[file_type]()
    logger.info(f"Successfully export image: {output_path}")


def load_image(path: pathlib.Path):
    image_formats = {"png", "jpeg"}
    suffix = path.suffix.removeprefix(".").lower()

    if suffix not in image_formats:
        raise ValueError(f"Unsupported file extension: {path.suffix}")

    image = cv2.imdecode(
        np.frombuffer(path.read_bytes(), dtype=np.uint8),
        cv2.IMREAD_UNCHANGED,
    )

    if image is None:
        raise ValueError(f"Failed to read image: {path}")

    return image
