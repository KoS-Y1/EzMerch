"""Independent display data derived from the cached sheet."""
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from core.document import Document


@dataclass
class PreviewSticker:
    image: NDArray[np.uint8]
    x: int
    y: int
    name: str


@dataclass
class SheetPreviewData:
    width: int
    height: int
    stickers: list[PreviewSticker]


def build_sheet_preview(document: Document) -> SheetPreviewData:
    width, height = document.get_output_data().get_size_px()
    stickers = []
    for folder in document.get_folders():
        sticker = Document(document.get_output_data())
        sticker.add_folder([(layer.data, layer.name) for layer in folder.layers], folder.name)
        image = sticker.flatten()
        rows, columns = np.nonzero(image[..., 3])
        if not rows.size:
            continue

        x = int(columns.min())
        y = int(rows.min())
        cropped = image[y:int(rows.max()) + 1, x:int(columns.max()) + 1].copy()
        stickers.append(PreviewSticker(cropped, x, y, folder.name))

    return SheetPreviewData(width, height, stickers)
