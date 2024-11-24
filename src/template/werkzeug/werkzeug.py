import ast
from dataclasses import dataclass

from naming import werkzeug_get_name
from template.werkzeug.getter import WerkzeugGetterTemplate
from template.werkzeug.setter import WerkzeugSetterTemplate
from types_source import FileFields
from utils.ast_tools import as_text_replace_content


@dataclass
class Werkzeug:
    key_name: str
    key: FileFields
    _class: ast.ClassDef

    def __post_init__(self) -> None:
        self.setter = WerkzeugSetterTemplate(self.key_name, self.key, self._class, None)
        self.getter = WerkzeugGetterTemplate(self.key_name, self.key, self._class, None)

    def build(self) -> None:
        self.getter.build()
        self.setter.build()

    def change(self, key_name: str, key: FileFields) -> None:
        self.getter.change(key_name, key)
        self.setter.change(key_name, key)

        as_text_replace_content(
            werkzeug_get_name(self.key_name),
            werkzeug_get_name(key_name),
            self._class,
        )

    def purge(self) -> None:
        self.getter.purge()
        self.setter.purge()
