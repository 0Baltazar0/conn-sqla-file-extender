import ast

from template.file_name.dynamic import DynamicFileName
from template.file_name.static import StaticFileName
from types_source import FileFields


def apply_file_name(key: FileFields, key_name: str, _class: ast.ClassDef) -> None:
    if key.get("name_unhandled"):
        return

    is_static = key.get("file_name_fix")
    is_dynamic = key.get("file_name_field_name")

    if is_static:
        static = StaticFileName(key_name, key, _class)
        static.build()
    if is_dynamic:
        dynamic = DynamicFileName(key_name, key, _class)
        dynamic.build()
    return
