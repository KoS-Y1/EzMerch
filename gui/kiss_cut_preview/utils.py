"""Pure geometry calculations for the kiss-cut preview."""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from core.kiss_cut import SheetGeometry


@dataclass(frozen=True)
class StickerBounds:
    """Padded image bounds in sheet-space pixels, excluding editor handles."""

    x: float
    y: float
    width: float
    height: float


def calculate_moved_geometry(original: SheetGeometry,
                             position: tuple[float, float]) -> SheetGeometry:
    return replace(original, x=round(position[0]), y=round(position[1]))


def calculate_resized_geometry(original: SheetGeometry, padded_width: float,
                               padding: int, scale: float) -> SheetGeometry:
    if scale == 1.0:
        return original
    width = max(1, round(padded_width * scale) - 2 * padding)
    height = max(1, round(width * original.height / original.width))
    return replace(original, width=width, height=height)


def calculate_resize_scale(start_vector: tuple[float, float],
                           current_vector: tuple[float, float],
                           start_scale: float, minimum_scale: float) -> float:
    start_x, start_y = start_vector
    denominator = start_x * start_x + start_y * start_y
    if denominator == 0:
        return start_scale
    dot_product = current_vector[0] * start_x + current_vector[1] * start_y
    return max(minimum_scale, start_scale * dot_product / denominator)


def check_layout(bounds_by_id: Mapping[int, StickerBounds],
                 sheet_size: tuple[float, float], margin: float,
                 spacing: float) -> set[int]:
    """Return all invalid IDs without changing geometry or retaining state.

    Inputs are pixels with positive bounds sizes and nonnegative margin/spacing.
    Exact margin/spacing contact is valid; positive-area overlap is always invalid.
    """
    def check_between_stickers() -> set[int]:
        invalid = set()
        stickers = list(bounds_by_id.items())
        for index, (first_id, a) in enumerate(stickers):
            for second_id, b in stickers[index + 1:]:
                overlap_x = min(a.x + a.width, b.x + b.width) - max(a.x, b.x)
                overlap_y = min(a.y + a.height, b.y + b.height) - max(a.y, b.y)
                gap_x = max(a.x - (b.x + b.width), b.x - (a.x + a.width), 0)
                gap_y = max(a.y - (b.y + b.height), b.y - (a.y + a.height), 0)
                if ((overlap_x > 0 and overlap_y > 0)
                        or gap_x * gap_x + gap_y * gap_y < spacing * spacing):
                    invalid.update((first_id, second_id))
        return invalid

    def check_boundaries() -> set[int]:
        width, height = sheet_size
        return {
            sticker_id for sticker_id, bounds in bounds_by_id.items()
            if (bounds.x < margin or bounds.y < margin
                or bounds.x + bounds.width > width - margin
                or bounds.y + bounds.height > height - margin)
        }

    return check_between_stickers() | check_boundaries()
