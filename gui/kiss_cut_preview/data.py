#
# Created by y1 on 2026-11-15
#

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from core.entity import EntityElements
from core.kiss_cut import KissCut, SheetLayer, SheetSticker


@dataclass
class KissCutStickerPreviewData:
    image: NDArray[np.uint8]
    x: int
    y: int
    name: str
    padding: int


@dataclass
class KissCutPreviewData:
    width: int
    height: int
    stickers: list[KissCutStickerPreviewData]
    sheet: KissCut


@dataclass
class KissCutStickerPreviewUpdate:
    sheet: KissCut
    index: int
    sticker: KissCutStickerPreviewData


def _composite_layers(layers: list[SheetLayer]) -> NDArray[np.uint8]:
    shape = layers[0].image.shape
    color = np.zeros(shape[:2] + (3,), dtype=np.float32)
    alpha = np.zeros(shape[:2] + (1,), dtype=np.float32)
    for layer in reversed(layers):
        image = layer.image.astype(np.float32) / 255
        source_alpha = image[..., 3:4]
        color = image[..., :3] * source_alpha + color * (1 - source_alpha)
        alpha = source_alpha + alpha * (1 - source_alpha)
    color = np.divide(color, alpha, out=np.zeros_like(color), where=alpha > 0)
    return np.clip(np.rint(np.concatenate((color, alpha), axis=2) * 255), 0, 255).astype(np.uint8)


def _build_sticker_preview(sticker: SheetSticker, elements: frozenset[EntityElements]) -> KissCutStickerPreviewData:
    geometry = sticker.geometry
    padding = sticker.source.get_required_paddings(set(elements))
    return KissCutStickerPreviewData(_composite_layers(sticker.layers), geometry.x, geometry.y,
                          sticker.name, padding)


def build_sheet_preview(sheet: KissCut) -> KissCutPreviewData:
    width, height = sheet.get_output_data().get_size_px()
    stickers = []
    for sticker in sheet.get_stickers():
        stickers.append(_build_sticker_preview(sticker, sheet.get_elements()))
    return KissCutPreviewData(width, height, stickers, sheet)


def regenerate_sticker_preview(sheet: KissCut, index: int) -> KissCutStickerPreviewUpdate:
    sheet.regenerate_sticker_layers(index)
    sticker = _build_sticker_preview(sheet.get_sticker(index), sheet.get_elements())
    return KissCutStickerPreviewUpdate(sheet, index, sticker)
