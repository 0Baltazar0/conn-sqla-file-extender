import ast

from template.starlette.starlette import Starlette
from types_source import FileFields


def apply_starlette(key: FileFields, key_name: str, _class: ast.ClassDef) -> None:
    Starlette(key_name, key, _class).build()
