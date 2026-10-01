#
# Created by y1 on 2026-09-30
#

import logging

import argparse
import pathlib

from core.processor import Processor
from utlis.format import FileType


def main():
    def init_logger():
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(
            "EzSticker.log",
            mode="w",
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    init_logger()
    logger = logging.getLogger(__name__)
    logger.info("---------- EzSticker started running ----------")

    def parse_args():
        logger.info("---------- Started parsing arguments ----------")
        parser = argparse.ArgumentParser()

        parser.add_argument("--src", "--s", nargs="+", type=pathlib.Path, help="Source images", required=True)
        parser.add_argument("--out", "--o", type=pathlib.Path, help="Output file path", required=True)
        parser.add_argument("--type", "--t", choices=["png", "psd"], default="png", help="Output file type")

        parsed_args = parser.parse_args()

        logger.info("Source images:")
        for src in parsed_args.src:
            logger.info(src)

        logger.info(f"Output file name {parsed_args.out}")
        logger.info(f"Output file type {parsed_args.type}")

        logger.info("---------- Finished parsing arguments ----------")
        return parsed_args

    args = parse_args()

    processor = Processor()
    processor.load_images(args.src)

    processor.output_all_cropped(args.out, FileType(args.type))


if __name__ == "__main__":
    main()
