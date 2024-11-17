import ast
from naming import get_column_mime_key, get_static_mime_key
from templates import (
    mime_type_column_template,
    mime_type_getter_template,
    mime_type_setter_template,
    mime_type_static_template,
)
from types_source import FileFields
from utils.ast_tools import (
    add_attribute_if_not_exists,
    add_properties_if_not_exist,
    switch_attributes,
)


def apply_mime(key: FileFields, key_name: str, _class: ast.ClassDef) -> None:
    if key.get("mime_unhandled"):
        return

    is_static = key.get("mime_type_fix")
    is_dynamic = key.get("mime_type_field_name")

    if is_static:
        switch_attributes(
            get_static_mime_key(key_name),
            mime_type_static_template(key_name, is_static),
            _class,
        )
        return
    if is_dynamic:
        add_properties_if_not_exist(
            get_column_mime_key(key_name),
            mime_type_getter_template(key_name, is_dynamic),
            mime_type_setter_template(key_name, is_dynamic),
            _class,
        )
        add_attribute_if_not_exists(
            is_dynamic, mime_type_column_template(is_dynamic), _class
        )

    return
