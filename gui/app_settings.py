#
# Created by y1 on 2026-10-13
#

import logging

from PySide6.QtCore import QSettings

from gui.i18n import Language
from utils.app_paths import application_directory


SETTINGS_FILENAME = "settings.ini"
LANGUAGE_KEY = "language"
DEFAULT_LANGUAGE = Language.EN_US

logger = logging.getLogger(__name__)


class AppSettings:
    """Persistent application preferences, independent of image processing."""

    def __init__(self, settings: QSettings | None = None):
        self.__settings = settings if settings is not None else QSettings(
            str(application_directory() / SETTINGS_FILENAME), QSettings.Format.IniFormat,
        )

    def get_language(self) -> Language:
        value = self.__settings.value(LANGUAGE_KEY, DEFAULT_LANGUAGE.value)
        try:
            return Language(value)
        except (ValueError, TypeError):
            return DEFAULT_LANGUAGE

    def get_filename(self) -> str:
        return self.__settings.fileName()

    def set_language(self, language: Language) -> bool:
        self.__settings.setValue(LANGUAGE_KEY, language.value)
        self.__settings.sync()
        if self.__settings.status() != QSettings.Status.NoError:
            logger.warning("Failed to persist language preference: %s", self.__settings.status())
            return False
        return True
