# 
# Created by y1 on 2026-10-03
#

import logging

import argparse
import pathlib

from core.processor import Processor
from utils.format import FileFormat
from utils.units import UnitType

logger = logging.getLogger(__name__)


class CLIInterface:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        # Shared arguments
        shared = argparse.ArgumentParser(add_help=False)
        shared.add_argument("--src", nargs="+", type=pathlib.Path, help="Source images", required=True)
        shared.add_argument("--dest", type=pathlib.Path, help="Output path", required=True)
        shared.add_argument("--format", choices=["png", "psd"], default="png",
                            help="Output file format, png by default")
        shared.add_argument("--size", nargs=2, type=float, help="Output width and height, in px by default")
        shared.add_argument("--dpi", type=int, help="Output dpi")
        shared.add_argument("--unit", choices=["px", "mm"], default="px", help="Output unit, px by default")
        shared.add_argument("--color", choices=["rgb", "cmyk"], default="rgb",
                            help="Output color mode, rgb by default (psd only)")
        commands = self.parser.add_subparsers(dest="command", required=True)

        crop = commands.add_parser("crop", parents=[shared])
        crop.set_defaults(handler=self.__crop)

        dieline = commands.add_parser("dieline", parents=[shared])
        dieline.add_argument("--distant", type=float, default=20,
                             help="Dieline distant from original image, 20px by default")
        dieline.add_argument("--thickness", type=float, default=4, help="Dieline thickness, 4px by default")
        dieline.add_argument("--dieline_unit", choices=["px", "mm"], default="px", help="Dieline unit, px by default")


    def execute(self, processor: Processor):
        args = self.parser.parse_args()
        logger.info("---------- EzSticker running from CLI----------")

        processor.set_output_unit(UnitType(args.unit))
        if args.size is not None:
            processor.set_output_size(*args.size)
        if args.dpi is not None:
            processor.set_output_dpi(args.dpi)

        processor.load_images(args.src)

        args.handler(args, processor)

    @staticmethod
    def __crop(args, processor: Processor):
        resize = args.size is not None
        processor.export_all_cropped(args.dest, FileFormat(args.format), resize)
