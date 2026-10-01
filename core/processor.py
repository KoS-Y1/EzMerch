#
# Created by y1 on {2026-09-30}
#

import logging
import pathlib
from dataclasses import dataclass

import cv2

from .entity import Entity
from utlis.format import FileType
from utlis.file_io import export

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

        self.__entities = []

    def load_images(self, paths: list[pathlib.Path]) -> None:
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

            for log in self.__load_batch.succeeded:
                print(f"Succeed {str(log)}")

            for log in self.__load_batch.failed:
                print(f"Failed {str(log)}")

    def clear_entity_list(self) -> None:
        self.__entities.clear()

    def output_all_cropped(self, dst_path: pathlib.Path, file_type: FileType):
        self.__export_batch.clear_batch()

        for entity in self.__entities:
            file_path = dst_path / f"{entity.get_name()}_cropped"

            try:
                export(file_path, entity.get_image(), file_type)
            except (OSError, ValueError, cv2.error) as exc:
                logger.warning(f"Failed to export {file_path}, {exc}")
                self.__export_batch.failed.append(file_path)
                continue

            self.__export_batch.succeeded.append(file_path)
