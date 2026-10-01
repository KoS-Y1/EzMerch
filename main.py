#
# Created by y1 on 2026-09-30
#

import logging

import argparse
import pathlib


def main():
    def init_logger():
        logging.basicConfig(level=logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler("EzSticker.log", "w")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        logging.getLogger('').addHandler(console_handler)
        logging.getLogger('').addHandler(file_handler)

    init_logger()
    logger = logging.getLogger(__name__)
    logger.info("---------- EzSticker started running ----------")
    logger.debug("test debug")

    def parse_args():
        logger.info("---------- Started parsing arguments ----------")
        parser = argparse.ArgumentParser()

        parser.add_argument("--src", "--s", nargs="+", type=pathlib.Path, help="Source images", required=True)
        parser.add_argument("--out", "--o", type=pathlib.Path, help="Output file path", required=True)
        parser.add_argument("--type", "--t", choices=["png", "psd"], default="png",help="Output file type")

        args = parser.parse_args()

        logger.info("Source images:")
        for src in args.src:
            logger.info(src)

        logger.info(f"Output file name {args.out}")
        logger.info(f"Output file type {args.type}")

        logger.info("---------- Finished parsing arguments ----------")
        return args

    args = parse_args()


if __name__ == "__main__":
    main()