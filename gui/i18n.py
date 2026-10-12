#
# Created by y1 on 2026-10-11
#

import json
import pathlib
from enum import Enum
from typing import Any


class Language(Enum):
    EN_US = "en_US"
    ZH_CN = "zh_CN"


class I18n:
    def __init__(self, language: Language = Language.EN_US):
        self.__language = language
        self.__localizations :dict[str, str]= {}

        self.load(self.__language)

    def load(self, language: Language)->None:
        path = (pathlib.Path(__file__).parent.parent / "localizations" / f"{language.value}.json")

        with open(path,"r",encoding="utf-8") as f:
            self.__localizations = json.load(f)

        self.__language = language

    def tr(self,key:str, **kwargs:Any )->str:
        text = self.__localizations.get(key, key)

        if kwargs:
            text = text.format(**kwargs)

        return text

i18n = I18n()