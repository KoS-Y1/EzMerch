#
# Created by y1 on 2026-09-30
#

import logging

from PySide6.QtWidgets import QApplication

from core.processor import Processor

from cli.cli_interface import CLIInterface
from gui.i18n import i18n
from gui.main_window import MainWindow
from gui.presenter import Presenter


def main() -> None:
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

    processor = Processor()


    # cli = CLIInterface()
    # cli.execute(processor)

    app = QApplication([])

    window = MainWindow()
    presenter = Presenter(window, processor)
    window.show()

    app.exec()

if __name__ == "__main__":
    main()
