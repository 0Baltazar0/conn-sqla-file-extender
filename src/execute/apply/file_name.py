import ast
from naming import get_column_file_name_key, get_static_file_name_key
from templates import (
    file_name_getter_template,
    file_name_setter_template,
    file_name_static_template,
    file_type_column_template,
)
from types_source import FileFields
from utils.ast_tools import (
    add_attribute_if_not_exists,
    add_properties_if_not_exist,
    switch_attributes,
)


def apply_file_name(key: FileFields, key_name: str, _class: ast.ClassDef) -> None:
    if key.get("name_unhandled"):
        return

    is_static = key.get("file_name_fix")
    is_dynamic = key.get("file_name_field_name")

    if is_static:
        switch_attributes(
            get_static_file_name_key(key_name),
            file_name_static_template(key_name, is_static),
            _class,
        )
        return
    if is_dynamic:
        add_properties_if_not_exist(
            get_column_file_name_key(key_name),
            file_name_getter_template(key_name, is_dynamic),
            file_name_setter_template(key_name, is_dynamic),
            _class,
        )
        add_attribute_if_not_exists(
            is_dynamic, file_type_column_template(is_dynamic), _class
        )
    return
