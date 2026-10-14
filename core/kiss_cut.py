#
# Created by y1 on 2026-10-13
#
from dataclasses import replace
from math import ceil, floor

import cv2
import numpy as np

from core.entity import EntityElements, Entity
from core.output_setting import KissCutData, OutputData, BleedData, DielineData, UnitType


def generate_kiss_cut( entities: list[Entity], elements: set[EntityElements], output_data: OutputData,
             kiss_cut_data: KissCutData, dieline_data: DielineData | None, bleed_data: BleedData | None) -> list[
    tuple[list[tuple[cv2.typing.MatLike, str]], str]]:
    """ Note that this will change the output size of the entity"""

    def calculate_layout(width: int, height: int, count: int, margin: int, spacing: int) -> tuple[
        int, int, int]:
        """
        Brutal force enumeration

        return [size, columns, rows]
        """
        if count <= 0:
            raise ValueError("Sticker count must be positive")
        if 0 > margin or spacing < 0:
            raise ValueError("Margin and spacing must be non negative")

        best_size = 0
        best_columns = 0
        best_rows = 0
        best_empty = count + 1

        for cs in range(1, count + 1):
            rs = ceil(count / cs)

            available_width = width - 2 * margin - (cs - 1) * spacing
            available_height = height - 2 * margin - (rs - 1) * spacing

            squared_size = floor(min(available_width / cs, available_height / rs))
            empty = cs * rs - count

            if squared_size > best_size or (squared_size == best_size and squared_size > 0 and empty < best_empty):
                best_size = squared_size
                best_columns = cs
                best_rows = rs
                best_empty = empty

        if best_size < 1:
            raise ValueError("Sheet cannot fit the stickers with the settings")

        return best_size, best_columns, best_rows

    def get_sticker_elements(column: int, row: int, e: Entity) -> list[tuple[cv2.typing.MatLike, str]]:
        e.set_output_data(replace(output_data, width=size, height=size, unit=UnitType.PX))

        if EntityElements.DIELINE in elements and dieline_data is not None:
            e.set_dieline_data(dieline_data)
        if EntityElements.BLEED in elements and bleed_data is not None:
            e.set_bleed_data(bleed_data)

        x = margin_px + column * (size + spacing_px)
        y = margin_px + row * (size + spacing_px)

        placed_elements: list[tuple[cv2.typing.MatLike, str]] = []

        sticker_elements, _ = e.get_elements(elements, True)
        for element, layer_name in sticker_elements:
            height, width = element.shape[:2]

            canvas = np.zeros((canvas_height, canvas_width, 4), dtype=np.uint8)
            canvas[y:y + height, x:x + width] = element

            placed_elements.append((canvas, layer_name))

        return placed_elements

    canvas_width, canvas_height = output_data.get_size_px()
    margin_px = kiss_cut_data.get_margin_px()
    spacing_px = kiss_cut_data.get_spacing_px()

    size, columns, rows = calculate_layout(canvas_width, canvas_height, len(entities), margin_px, spacing_px)

    entity_index = 0
    stickers: list[tuple[list[tuple[cv2.typing.MatLike, str]], str]] = []

    for c in range(0, columns):
        for r in range(0, rows):
            if entity_index >= len(entities):
                break

            entity = entities[entity_index]
            stickers.append((get_sticker_elements(c, r, entity), entity.get_name()))

            entity_index += 1

    return stickers


