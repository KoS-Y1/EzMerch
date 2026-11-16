#
# Created by y1 on 2026-09-30
#

import logging
import pathlib
from dataclasses import dataclass, replace, astuple

import cv2
import numpy as np

from .document import Document
from .entity import Entity, EntityElements
from .output_setting import DEFAULT_DPI, OutputData, FileFormat, UnitType, ColorFormat, DielineData, BleedData, \
    KissCutData
from .kiss_cut import KissCut

from utils.file_io import export

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """
    Passed to UI level
    """
    succeeded: list[pathlib.Path]
    failed: list[pathlib.Path]

    def clear_batch(self):
        self.succeeded.clear()
        self.failed.clear()


class Processor:
    """
    Core logic
    """

    def __init__(self):
        self.__load_batch = BatchResult(succeeded=[], failed=[])
        self.__export_batch = BatchResult(succeeded=[], failed=[])

        self.__output_data = OutputData(width=0, height=0, dpi=DEFAULT_DPI)
        self.__dieline_data = DielineData()
        self.__bleed_data = BleedData()

        self.__kiss_cut_data = KissCutData()

        self.__entities: list[Entity] = []
        self.__kiss_cut_sheet_cache: KissCut | None = None
        self.__kiss_cut_sheet_key: tuple[object, ...] | None = None

    def set_output_data(self, width: float, height: float, dpi: int = DEFAULT_DPI,
                        unit: UnitType = UnitType.PX, color: ColorFormat = ColorFormat.RGB) -> None:
        self.__output_data = OutputData(width=width, height=height, dpi=dpi, unit=unit, color=color)

    def set_output_size(self, width: float, height: float) -> None:
        self.__output_data = replace(self.__output_data, width=width, height=height)

    def set_output_dpi(self, dpi: int) -> None:
        self.__output_data = replace(self.__output_data, dpi=dpi)
        self.__dieline_data = replace(self.__dieline_data, dpi=dpi)
        self.__bleed_data = replace(self.__bleed_data, dpi=dpi)
        self.__kiss_cut_data = replace(self.__kiss_cut_data, dpi=dpi)

    def set_output_unit(self, unit: UnitType) -> None:
        self.__output_data = replace(self.__output_data, unit=unit)

    def set_output_color(self, color: ColorFormat) -> None:
        self.__output_data = replace(self.__output_data, color=color)

    def set_dieline_data(self, thickness: float, distance: float, dpi: int = DEFAULT_DPI,
                         unit: UnitType = UnitType.PX) -> None:
        self.__dieline_data = DielineData(thickness=thickness, distance=distance, unit=unit, dpi=dpi)

    def set_dieline_distance(self, distance: float) -> None:
        self.__dieline_data = replace(self.__dieline_data, distance=distance)

    def set_dieline_thickness(self, thickness: float) -> None:
        self.__dieline_data = replace(self.__dieline_data, thickness=thickness)

    def set_dieline_unit(self, unit: UnitType) -> None:
        self.__dieline_data = replace(self.__dieline_data, unit=unit)

    def set_bleed_data(self, distance: float, dpi: int = DEFAULT_DPI, unit: UnitType = UnitType.PX) -> None:
        self.__bleed_data = BleedData(distance=distance, dpi=dpi, unit=unit)

    def set_bleed_distance(self, distance: float) -> None:
        self.__bleed_data = replace(self.__bleed_data, distance=distance)

    def set_bleed_unit(self, unit: UnitType) -> None:
        self.__bleed_data = replace(self.__bleed_data, unit=unit)

    def set_kiss_cut_data(self, margin: float, spacing: float, dpi: int = DEFAULT_DPI,
                          spacing_unit: UnitType = UnitType.MM, margin_unit: UnitType = UnitType.MM) -> None:
        self.__kiss_cut_data = KissCutData(margin=margin, spacing=spacing, dpi=dpi, margin_unit=margin_unit,
                                           spacing_unit=spacing_unit)

    def set_kiss_cut_margin(self, margin: float) -> None:
        self.__kiss_cut_data = replace(self.__kiss_cut_data, margin=margin)

    def set_kiss_cut_margin_unit(self, margin_unit) -> None:
        self.__kiss_cut_data = replace(self.__kiss_cut_data, margin_unit=margin_unit)

    def set_kiss_cut_spacing(self, spacing: float) -> None:
        self.__kiss_cut_data = replace(self.__kiss_cut_data, spacing=spacing)

    def set_kiss_cut_spacing_unit(self, spacing_unit: UnitType) -> None:
        self.__kiss_cut_data = replace(self.__kiss_cut_data, spacing_unit=spacing_unit)

    def clear_entity_list(self) -> None:
        self.__entities.clear()
        self.__kiss_cut_sheet_cache = None

    def load_images(self, paths: list[pathlib.Path]) -> BatchResult:
        self.__kiss_cut_sheet_cache = None
        logger.info("---------- Start loading images ----------")

        self.__load_batch.clear_batch()
        self.clear_entity_list()

        for path in paths:
            try:
                entity = Entity(path)
            except (OSError, ValueError, cv2.error) as exc:
                logger.warning(f"Failed load image: {path}, {exc}")
                self.__load_batch.failed.append(path)
                continue

            self.__entities.append(entity)
            self.__load_batch.succeeded.append(path)

        succeeded = "\n".join(str(path.resolve()) for path in self.__load_batch.succeeded)
        failed = "\n".join(str(path.resolve()) for path in self.__load_batch.failed)
        logger.info(
            f"Finish loading:\n"
            f"Successfully loaded:\n{succeeded or '(none)'}\n"
            f"Failed to load:\n{failed or '(none)'}\n"
        )

        return BatchResult(self.__load_batch.succeeded.copy(), self.__load_batch.failed.copy())

    def export_individuals(self, dst_path: pathlib.Path, file_format: FileFormat, elements: set[EntityElements],
                           resize: bool = False) -> BatchResult:
        def set_base_data(e: Entity) -> None:
            return

        def set_dieline_data(e: Entity) -> None:
            e.set_dieline_data(self.__dieline_data)

        def set_bleed_data(e: Entity) -> None:
            e.set_bleed_data(self.__bleed_data)

        set_data_selector = {
            EntityElements.BASE: set_base_data,
            EntityElements.DIELINE: set_dieline_data,
            EntityElements.BLEED: set_bleed_data,
        }

        element_strs = ",".join(sorted(e.value for e in elements))
        logger.info(f"---------- Start exporting all images with {element_strs}")

        self.__export_batch.clear_batch()

        element_strs = element_strs.replace(",", "_")
        element_strs = "_" + element_strs

        for entity in self.__entities:
            output_path = (dst_path / f"{entity.get_name()}{element_strs}").with_suffix(f".{file_format.value}")

            entity.set_output_data(self.__output_data)

            for e in elements:
                set_data_selector[e](entity)

            try:
                output_images, (width, height) = entity.get_elements(elements, resize)
            except (OSError, cv2.error, ValueError) as exc:
                logger.warning(f"Failed to get elements from {entity.get_name()}, {exc}")
                self.__export_batch.failed.append(output_path)
                continue

            document_output = replace(self.__output_data, width=width, height=height, unit=UnitType.PX)
            doc = Document(output_data=document_output)
            doc.add_folder(output_images, entity.get_name())

            try:
                export(output_path, doc, file_format)
            except (OSError, cv2.error, ValueError) as exc:
                logger.warning(f"Failed to export {output_path}, {exc}")
                self.__export_batch.failed.append(output_path)
                continue

            self.__export_batch.succeeded.append(output_path)

        succeeded = "\n".join(str(path.resolve()) for path in self.__export_batch.succeeded)
        failed = "\n".join(str(path.resolve()) for path in self.__export_batch.failed)
        logger.info(
            f"Finish exporting:\n"
            f"Successfully exported:\n{succeeded or '(none)'}\n"
            f"Failed to export:\n{failed or '(none)'}\n"
        )
        return BatchResult(self.__export_batch.succeeded.copy(), self.__export_batch.failed.copy())

    def prepare_kiss_cut_sheet(self, elements: set[EntityElements]) -> KissCut:
        key = (tuple(id(e) for e in self.__entities), astuple(self.__output_data),
               astuple(self.__kiss_cut_data), frozenset(elements),
               astuple(self.__dieline_data) if EntityElements.DIELINE in elements else None,
               astuple(self.__bleed_data) if EntityElements.BLEED in elements else None)
        if self.__kiss_cut_sheet_cache is not None and key == self.__kiss_cut_sheet_key:
            return self.__kiss_cut_sheet_cache
        sheet = KissCut()
        sheet.generate(self.__entities, elements, self.__output_data,
                       self.__kiss_cut_data, self.__dieline_data, self.__bleed_data)
        self.__kiss_cut_sheet_cache = sheet
        self.__kiss_cut_sheet_key = key
        return sheet

    def update_kiss_cut_sheet(self, sheet: KissCut) -> None:
        snapshot = sheet.copy()
        self.__kiss_cut_sheet_cache = snapshot

    def export_kiss_cut(self, dst_path: pathlib.Path, file_format: FileFormat,
                        elements: set[EntityElements]) -> BatchResult:
        def build_document(sheet: KissCut) -> Document:
            output = sheet.get_output_data()
            document = Document(output)
            width, height = output.get_size_px()

            for sticker in sheet.get_stickers():
                x = sticker.geometry.x
                y = sticker.geometry.y
                layers = []
                for layer in sticker.layers:
                    image = layer.image
                    canvas = np.zeros((height, width, 4), dtype=np.uint8)
                    left = max(0, x)
                    top = max(0, y)
                    right = min(width, x + image.shape[1])
                    bottom = min(height, y + image.shape[0])
                    if right > left and bottom > top:
                        canvas[top:bottom, left:right] = image[top-y:bottom-y, left-x:right-x]
                    layers.append((canvas, layer.name))
                document.add_folder(layers, sticker.name)

            return document

        element_strs = ",".join(sorted(e.value for e in elements))
        logger.info(f"---------- Start exporting kiss cut with stickers with {element_strs}")

        self.__export_batch.clear_batch()

        try:
            sheet = self.prepare_kiss_cut_sheet(elements)
            doc = build_document(sheet)
        except (OSError, cv2.error, ValueError) as exc:
            logger.warning(f"Failed to generate kiss cut: {exc}")
            self.__export_batch.failed.append(dst_path)
            return BatchResult([], self.__export_batch.failed.copy())

        try:
            export(dst_path, doc, file_format)
        except (OSError, cv2.error, ValueError) as exc:
            logger.warning(f"Failed to export {dst_path}, {exc}")
            self.__export_batch.failed.append(dst_path)
            return BatchResult(self.__export_batch.succeeded.copy(), self.__export_batch.failed.copy())

        self.__export_batch.succeeded.append(dst_path)

        succeeded = "\n".join(str(path.resolve()) for path in self.__export_batch.succeeded)
        failed = "\n".join(str(path.resolve()) for path in self.__export_batch.failed)
        logger.info(
            f"Finish exporting:\n"
            f"Successfully exported:\n{succeeded or '(none)'}\n"
            f"Failed to export:\n{failed or '(none)'}\n"
        )
        return BatchResult(self.__export_batch.succeeded.copy(), self.__export_batch.failed.copy())
