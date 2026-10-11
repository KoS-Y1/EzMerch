#
# Created by y1 on {2026-10-09}
#
from dataclasses import dataclass, replace

import cv2.typing
import numpy as np

from .output_setting import OutputData


class Document:
    """
    Storing exported file info
    Assuming folders and layers are from top to bottom order
    """

    @dataclass
    class Layer:
        name: str
        data: cv2.typing.MatLike

    @dataclass
    class Folder:
        name: str
        layers: list["Document.Layer"]

    def __init__(self, output_data: OutputData | None = None):
        self.__output_data = OutputData() if output_data is None else replace(output_data)
        self.__folders: list[Document.Folder] = []

    def set_output_data(self, output_data: OutputData) -> None:
        self.__output_data = replace(output_data)

    def get_output_data(self) -> OutputData:
        return replace(self.__output_data)

    def get_folders(self) -> list["Document.Folder"]:
        return self.__folders.copy()

    def flatten(self) -> cv2.typing.MatLike:
        layers = [
            layer
            for folder in reversed(self.__folders)
            for layer in reversed(folder.layers)
        ]

        if not layers:
            raise ValueError("Failed to flatten, empty document")

        shape = layers[0].data.shape

        color = np.zeros(shape[:2] + (3,), dtype=np.float32)
        alpha = np.zeros(shape[:2] + (1,), dtype=np.float32)

        for layer in layers:
            image = layer.data

            if image.shape != shape or image.dtype != np.uint8:
                raise ValueError("Failed to flatten, layer size does not match or not have uint8 data")

            source = image.astype(np.float32) / 255.0
            source_color = source[..., :3]
            source_alpha = source[..., 3:4]


            color = source_color * source_alpha + color * (1.0 - source_alpha)
            alpha = source_alpha + alpha * (1.0 - source_alpha)

        # to BGRA order
        color = np.divide(
            color,
            alpha,
            out=np.zeros_like(color),
            where=alpha > 0
        )

        result = np.concatenate((color, alpha), axis=2)
        return np.clip(np.rint(result * 255), 0, 255).astype(np.uint8)

    def add_folder(self, images: list[tuple[cv2.typing.MatLike, str]], name:str)->None:
        layers = [
            Document.Layer(name=layer_name, data=data)
            for data, layer_name in images
        ]

        self.__folders.append(Document.Folder(name=name, layers=layers))
