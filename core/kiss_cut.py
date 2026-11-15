#
# Created by y1 on 2026-10-13
#
from dataclasses import replace

import cv2
import numpy as np
from rectpack import newPacker, MaxRectsBssf, SORT_AREA

from core.entity import EntityElements, Entity
from core.output_setting import KissCutData, OutputData, BleedData, DielineData, UnitType


def generate_kiss_cut(entities: list[Entity], elements: set[EntityElements], output_data: OutputData,
                      kiss_cut_data: KissCutData, dieline_data: DielineData | None, bleed_data: BleedData | None) -> \
        list[
            tuple[list[tuple[cv2.typing.MatLike, str]], str]]:
    """ Note that this will change the output size of the entity"""

    def layout_attempt(sizes: list[tuple[int, int]], width: int, height: int, margin: int, spacing: int) -> \
            list[tuple[int, int, int, int]] | None:
        """
        Attempt packing with given element sizes
        Return a list of top left corner location on canvas sheet and its size of each element
        """
        available_width = width - 2 * margin
        available_height = height - 2 * margin

        if available_width <= 0 or available_height <= 0:
            raise ValueError("Invalid margin, spacing, or canvas size")

        packer = newPacker(
            pack_algo=MaxRectsBssf,
            sort_algo=SORT_AREA,
            rotation=False
        )

        # Add space as padding for elements at the last row / column, so that we can group space with element size for calculation
        packer.add_bin(available_width + spacing, available_height + spacing, count=1)

        for index, (w, h) in enumerate(sizes):
            packer.add_rect(w + spacing, h + spacing, rid=index)

        packer.pack()
        packed = packer.rect_list()

        if len(packed) != len(sizes):
            return None

        placements: list[tuple[int, int, int, int]] = []
        for _, x, y, _, _, index in sorted(packed, key=lambda rect: rect[5]):
            w, h = sizes[index]
            placements.append((margin + x, margin + y, w, h))

        return placements

    def calculate_scaled_size(entity: Entity, target_length: int) -> tuple[int, int]:
        w, h = entity.get_image_size()

        scale = target_length / max(w, h)

        width = max(MIN_SIZE_PX, round(w * scale))
        height = max(MIN_SIZE_PX, round(h * scale))

        padding = entity.get_required_paddings(elements)

        return width + padding * 2, height + padding * 2

    def get_sticker_elements(entity: Entity, placement: tuple[int, int, int, int]) -> list[
        tuple[cv2.typing.MatLike, str]]:
        x, y, width, height = placement

        entity.set_output_data(replace(output_data, width=width, height=height, unit=UnitType.PX))

        placed_elements: list[tuple[cv2.typing.MatLike, str]] = []

        sticker_elements, _ = entity.get_elements(elements, True)
        for element, layer_name in sticker_elements:
            height, width = element.shape[:2]

            canvas = np.zeros((canvas_height, canvas_width, 4), dtype=np.uint8)
            canvas[y:y + height, x:x + width] = element

            placed_elements.append((canvas, layer_name))

        return placed_elements

    canvas_width, canvas_height = output_data.get_size_px()
    margin_px = kiss_cut_data.get_margin_px()
    spacing_px = kiss_cut_data.get_spacing_px()

    if len(entities) <= 0:
        raise ValueError("Sticker count must be positive")
    if 0 > margin_px or spacing_px < 0:
        raise ValueError("Margin and spacing must be non negative")

    for e in entities:
        if EntityElements.DIELINE in elements and dieline_data is not None:
            e.set_dieline_data(dieline_data)
        if EntityElements.BLEED in elements and bleed_data is not None:
            e.set_bleed_data(bleed_data)

    # trial longest side target
    MIN_SIZE_PX = 1
    low = MIN_SIZE_PX
    high = max(canvas_width - 2 * margin_px, canvas_height - 2 * margin_px)

    best_layout = None

    while high >= low:
        trial_length = (low + high) // 2

        scaled_size: list[tuple[int, int]] = []
        for e in entities:
            scaled_size.append(calculate_scaled_size(e, trial_length))

        layout = layout_attempt(scaled_size, canvas_width, canvas_height, margin_px, spacing_px)

        if layout is None:
            high = trial_length - 1
        else:
            low = trial_length + 1
            best_layout = layout

    if best_layout is None:
        raise ValueError("Sheet cannot fit the stickers with the settings")

    stickers: list[tuple[list[tuple[cv2.typing.MatLike, str]], str]] = []

    for entity_index, placement in enumerate(best_layout):
        e = entities[entity_index]
        stickers.append((get_sticker_elements(e, placement), e.get_name()))

    return stickers
