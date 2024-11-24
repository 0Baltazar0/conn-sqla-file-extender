import ast
from dataclasses import dataclass

from naming import starlette_get_name

from template.starlette.getter import StarletteGetterTemplate
from template.starlette.setter import StarletteSetterTemplate
from types_source import FileFields
from utils.ast_tools import as_text_replace_content


@dataclass
class Starlette:
    key_name: str
    key: FileFields
    _class: ast.ClassDef

    def __post_init__(self) -> None:
        self.setter = StarletteSetterTemplate(
            self.key_name, self.key, self._class, None
        )
        self.getter = StarletteGetterTemplate(
            self.key_name, self.key, self._class, None
        )

    def build(self) -> None:
        self.getter.build()
        self.setter.build()

    def change(self, key_name: str, key: FileFields) -> None:
        self.getter.change(key_name, key)
        self.setter.change(key_name, key)

        as_text_replace_content(
            starlette_get_name(self.key_name),
            starlette_get_name(key_name),
            self._class,
        )

    def purge(self) -> None:
        self.getter.purge()
        self.setter.purge()
