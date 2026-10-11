# 
# Created by y1 on 2026-09-30
#
import pathlib
import logging

import cv2
import numpy as np
from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import BlendMode, Resource
from psd_tools.psd.image_resources import ImageResource, ResoulutionInfo

from core.document import Document
from core.output_setting import FileFormat, ColorFormat

logger = logging.getLogger(__name__)

PSD_FIXED_POINT_SCALE = 1 << 16


def export(path: pathlib.Path, document: Document, file_format: FileFormat) -> None:
    def export_png() -> None:
        image = cv2.cvtColor(document.flatten(), cv2.COLOR_BGRA2RGBA)
        dpi = document.get_output_data().dpi
        Image.fromarray(np.asarray(image)).save(path, format="PNG", dpi=(dpi, dpi))

    def export_psd() -> None:
        if document.get_output_data().color == ColorFormat.CMYK:
            raise ValueError("CMYK not supported")

        output_data = document.get_output_data()
        psd = PSDImage.new("RGBA", output_data.get_size_px(), depth=8)
        psd.background_color = None
        dpi_fixed = round(output_data.dpi * PSD_FIXED_POINT_SCALE)
        psd.image_resources[Resource.RESOLUTION_INFO] = ImageResource(
            key=Resource.RESOLUTION_INFO,
            data=ResoulutionInfo(
                horizontal=dpi_fixed,
                horizontal_unit=1,  # Pixels per inch.
                width_unit=1,  # Inches.
                vertical=dpi_fixed,
                vertical_unit=1,
                height_unit=1,
            ).tobytes(),
        )

        for folder in reversed(document.get_folders()):
            layers :list[PixelLayer] = []

            for layer in reversed(folder.layers):
                image = cv2.cvtColor(layer.data, cv2.COLOR_BGRA2RGBA)
                layers.append(psd.create_pixel_layer(Image.fromarray(np.asarray(image)), name=layer.name))

            psd.create_group(layer_list=layers, name=folder.name, blend_mode=BlendMode.NORMAL)

        # A negative layer count marks merged alpha as transparency, not a saved selection.
        layer_info = psd._record.layer_and_mask_information.layer_info
        if layer_info is not None:
            layer_info.layer_count = -abs(layer_info.layer_count)
        psd.save(path)

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
