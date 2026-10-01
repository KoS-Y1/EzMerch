#
# Created by y1 on {2026-09-30}
#

import logging
import pathlib
from enum import Enum

from entity import Entity

logger = logging.getLogger(__name__)

class OutputType(Enum):
    PNG = 0
    PSD = 1

class Processor:
    """
    Core logic
    """

    def __init__(self, src_paths: [pathlib.Path], out_path:pathlib.Path, out_type:OutputType):
        self._entities = [Entity(src) for src in src_paths]


    def clear_entity_list(self):
        self._entities.clear()