# 
# Created by y1 on 2026-09-30
#
# A standalone psd-tools demo to export image layers and a folder to .psd.
#
import pathlib

from PIL import Image, ImageDraw
from psd_tools import PSDImage


def main() -> None:
    size = (64, 64)
    document = PSDImage.new("RGB", size, depth=8)

    red_image = Image.new("RGBA", size, (255, 0, 0, 255))
    document.create_pixel_layer(red_image, name="Layer Red")

    green_image = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(green_image).rectangle((8, 8, 40, 40), fill=(0, 255, 0, 255))
    green_layer = document.create_pixel_layer(green_image, name="Layer Green")

    blue_image = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(blue_image).ellipse((24, 24, 56, 56), fill=(0, 0, 255, 255))
    blue_layer = document.create_pixel_layer(blue_image, name="Layer Blue", opacity=128)

    document.create_group(layer_list=[green_layer, blue_layer], name="Image Layers")
    document.save(pathlib.Path("./test.psd"))



if __name__ == "__main__":
    main()
