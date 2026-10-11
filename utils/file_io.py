# 
# Created by y1 on 2026-09-30
#
import pathlib
import logging

import cv2
import numpy as np
from PIL import Image

from core.document import Document
from format import FileFormat

logger = logging.getLogger(__name__)


def export(path: pathlib.Path, document: Document, file_format: FileFormat) -> None:
    def export_png():
        image = cv2.cvtColor(document.flatten(), cv2.COLOR_BGRA2RGBA)
        Image.fromarray(np.asarray(image)).save(path, format="PNG", dpi=(document.dpi, document.dpi))
    def export_psd():
        # TODO: placeholder for now
        raise ValueError(f"Failed to write image: {path}, currently .psd not supported")

    export_selector = {
        FileFormat.PNG: export_png,
        FileFormat.PSD: export_psd
    }

    export_selector[file_format]()
    logger.info(f"Successfully export image: {path}")

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
