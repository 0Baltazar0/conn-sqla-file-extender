import ast

from template.werkzeug.werkzeug import Werkzeug
from types_source import FileFields


def apply_werkzeug(key: FileFields, key_name: str, _class: ast.ClassDef) -> None:
    Werkzeug(key_name, key, _class).build()
