import ast
from template.mime.dynamic import DynamicMimeType
from template.mime.static import StaticMimeType

from types_source import FileFields


def apply_mime(key: FileFields, key_name: str, _class: ast.ClassDef) -> None:
    if key.get("mime_unhandled"):
        return

    is_static = key.get("mime_type_fix")
    is_dynamic = key.get("mime_type_field_name")

    if is_static:
        static = StaticMimeType(key_name, key, _class)
        static.build()
    if is_dynamic:
        dynamic = DynamicMimeType(key_name, key, _class)
        dynamic.build()

    return
