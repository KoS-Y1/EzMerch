#
# Created by y1 on 2026-10-03
#

import logging

import argparse
import pathlib

from core.entity import EntityElements
from core.processor import Processor
from core.output_setting import FileFormat, UnitType, ColorFormat

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
        shared.add_argument("--color", choices=["RGB", "CMYK"], default="RGB",
                            help="Output color mode, rgb by default (psd only)")
        commands = self.parser.add_subparsers(dest="command", required=True)

        crop = commands.add_parser("crop", parents=[shared])
        crop.set_defaults(handler=self.__crop)

        dieline = commands.add_parser("dieline", parents=[shared])
        dieline.add_argument("--distance", type=float, default=20,
                             help="Dieline distance from original image, 20px by default")
        dieline.add_argument("--thickness", type=float, default=4, help="Dieline thickness, 4px by default")
        dieline.add_argument("--dieline_unit", choices=["px", "mm"], default="px", help="Dieline unit, px by default")
        dieline.set_defaults(handler=self.__dieline)

        bleed = commands.add_parser("bleed", parents=[shared])
        bleed.add_argument("--distance", type=float, default=20,
                           help="Bleed line distance from original image, 20px by default")
        bleed.add_argument("--bleed_unit", choices=["px", "mm"], default="px", help="Bleed line unit, px by default")
        bleed.set_defaults(handler=self.__bleed)

    def execute(self, processor: Processor):
        args = self.parser.parse_args()
        logger.info("---------- EzSticker running from CLI----------")

        processor.set_output_unit(UnitType(args.unit))
        processor.set_output_color(ColorFormat(args.color))
        if args.size is not None:
            processor.set_output_size(*args.size)
        if args.dpi is not None:
            processor.set_output_dpi(args.dpi)

        processor.load_images(args.src)

        args.handler(args, processor)

    @staticmethod
    def __crop(args, processor: Processor):
        resize = args.size is not None
        processor.export_all(args.dest, FileFormat(args.format), {EntityElements.BASE}, resize)

    @staticmethod
    def __dieline(args, processor: Processor):
        processor.set_dieline_thickness(args.thickness)
        processor.set_dieline_distance(args.distance)

        if args.dieline_unit is not None:
            processor.set_dieline_unit(UnitType(args.dieline_unit))

        resize = args.size is not None
        processor.export_all(args.dest, FileFormat(args.format), {EntityElements.BASE, EntityElements.DIELINE}, resize)

    @staticmethod
    def __bleed(args, processor: Processor):
        processor.set_bleed_distance(args.distance)
        processor.set_dieline_thickness(4)
        processor.set_dieline_distance(20)

        if args.bleed_unit is not None:
            processor.set_bleed_unit(UnitType(args.bleed_unit))

        resize = args.size is not None
        processor.export_all(args.dest, FileFormat(args.format),
                             {EntityElements.BASE, EntityElements.DIELINE, EntityElements.BLEED}, resize)
