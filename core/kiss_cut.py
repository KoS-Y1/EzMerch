#
# Created by y1 on 2026-10-13
#
from copy import deepcopy
from dataclasses import dataclass, field, replace

import cv2.typing
from rectpack import newPacker, MaxRectsBssf, SORT_AREA

from core.entity import Entity, EntityElements
from core.output_setting import KissCutData, OutputData, BleedData, DielineData, UnitType


@dataclass(frozen=True)
class SheetGeometry:
    x: int
    y: int
    width: int
    height: int


@dataclass
class SheetLayer:
    image: cv2.typing.MatLike
    name: str


@dataclass
class SheetSticker:
    name: str
    geometry: SheetGeometry
    source: Entity = field(compare=False, repr=False)
    layers: list[SheetLayer] = field(default_factory=list, compare=False, repr=False)


class KissCut:
    def __init__(self) -> None:
        self.__output: OutputData | None = None
        self.__elements: frozenset[EntityElements] = frozenset()
        self.__stickers: list[SheetSticker] = []

    def get_output_data(self) -> OutputData:
        if self.__output is None:
            raise ValueError("Kiss-cut sheet has not been generated")
        return replace(self.__output)

    def get_elements(self) -> frozenset[EntityElements]:
        return self.__elements

    def get_stickers(self) -> list[SheetSticker]:
        return deepcopy(self.__stickers)

    def get_sticker(self, index: int) -> SheetSticker:
        self.__validate_sticker_index(index)
        return deepcopy(self.__stickers[index])

    def __validate_sticker_index(self, index: int) -> None:
        if index < 0 or index >= len(self.__stickers):
            raise IndexError("Sticker index is out of range")

    def get_sticker_geometry(self, index: int) -> SheetGeometry:
        self.__validate_sticker_index(index)
        return self.__stickers[index].geometry

    def get_sticker_geometries(self) -> list[SheetGeometry]:
        return [sticker.geometry for sticker in self.__stickers]

    def set_sticker_geometry(self, index: int, geometry: SheetGeometry) -> None:
        self.__validate_sticker_index(index)
        if geometry.width < 1 or geometry.height < 1:
            raise ValueError("Sticker dimensions must be positive")
        self.__stickers[index].geometry = geometry

    def copy(self) -> 'KissCut':
        return deepcopy(self)

    def generate(self, entities: list[Entity], elements: set[EntityElements], output_data: OutputData,
                 kiss_cut_data: KissCutData, dieline_data: DielineData | None,
                 bleed_data: BleedData | None) -> None:
        """Generate an automatically packed sheet with independent sticker sources."""

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

        def get_sticker_elements(entity: Entity,
                                 placement: tuple[int, int, int, int]) -> SheetSticker:
            x, y, width, height = placement
            padding = entity.get_required_paddings(elements)
            entity.set_output_data(replace(output_data, width=width, height=height, unit=UnitType.PX))
            layers, _ = entity.get_elements(elements, True)

            geometry = SheetGeometry(x, y, width - 2 * padding, height - 2 * padding)
            source = deepcopy(entity)
            sticker_layers = [SheetLayer(image.copy(), name) for image, name in layers]
            return SheetSticker(entity.get_name(), geometry, source, sticker_layers)

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


        stickers = []
        for index, placement in enumerate(best_layout):
            stickers.append(get_sticker_elements(entities[index], placement))

        self.__output = replace(output_data)
        self.__elements = frozenset(elements)
        self.__stickers = stickers

    def regenerate_sticker_layers(self, index: int) -> None:
        output = self.get_output_data()
        self.__validate_sticker_index(index)

        sticker = self.__stickers[index]
        source = deepcopy(sticker.source)
        geometry = sticker.geometry
        padding = source.get_required_paddings(set(self.__elements))
        source.set_output_data(replace(output, width=geometry.width + 2 * padding,
                                       height=geometry.height + 2 * padding, unit=UnitType.PX))
        layers, _ = source.get_elements(set(self.__elements), True)
        sticker_layers = [SheetLayer(image.copy(), name) for image, name in layers]

        sticker.source = source
        sticker.layers = sticker_layers
