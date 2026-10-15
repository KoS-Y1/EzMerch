#
# Created by y1 on 2026-09-30
#

import logging
import pathlib
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.processor import Processor

from cli.cli_interface import CLIInterface
from gui.i18n import i18n
from gui.main_window import MainWindow
from gui.presenter import Presenter
from gui.app_settings import AppSettings
from utils.app_paths import application_directory

APP_NAME = "EzMerch"
ORGANIZATION_NAME = "KoS-Y1"
APP_VERSION = "0.1.0"

ASSET_FILE_PATH = "assets"
ICON_FILE_NAME = APP_NAME + ".ico"


def main() -> None:
    def init_logger():
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        if sys.stderr is not None:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        log_path = application_directory() / "EzMerch.log"
        try:
            file_handler = logging.FileHandler(
                log_path,
                mode="w",
                encoding="utf-8",
            )
        except OSError:
            # Avoid logging.lastResort attempting to use an absent console.
            root_logger.addHandler(logging.NullHandler())
            return log_path
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)
        return None

    app = QApplication([])
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationVersion(APP_VERSION)
    log_error_path = init_logger()
    app.setWindowIcon(QIcon(str(pathlib.Path(__file__).resolve().parent / ASSET_FILE_PATH / ICON_FILE_NAME)))

    settings = AppSettings()

    i18n.load(settings.get_language())
    settings_saved = settings.set_language(settings.get_language())

    processor = Processor()
    window = MainWindow(settings)
    presenter = Presenter(window, processor)
    window.show()
    if log_error_path is not None:
        window.show_storage_error(str(log_error_path))
    if not settings_saved:
        window.show_storage_error(settings.get_filename())

    app.exec()


if __name__ == "__main__":
    main()
