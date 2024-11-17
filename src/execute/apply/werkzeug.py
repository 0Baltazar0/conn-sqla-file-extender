import ast
from naming import werkzeug_get_name
from templates import (
    property_werkzeug_getter_template,
    property_werkzeug_setter_template,
)
from types_source import FileFields
from utils.ast_tools import (
    get_attribute,
    get_attribute_index,
    get_property_getter,
    get_property_setter,
)


def apply_werkzeug(key: FileFields, key_name: str, _class: ast.ClassDef) -> None:
    has_werkzeug_get = get_property_getter(werkzeug_get_name(key_name), _class)
    has_werkzeug_set = get_property_setter(werkzeug_get_name(key_name), _class)
    key_attribute = get_attribute(key_name, _class)
    key_index = get_attribute_index(key_name, _class) or 0
    key_index = key_index if key_index == len(_class.body) - 1 else (key_index + 1)

    if not has_werkzeug_get:
        getter = property_werkzeug_getter_template(key_name, key)
        _class.body.insert(key_index, getter)

    if not has_werkzeug_set:
        has_werkzeug_get = get_property_getter(werkzeug_get_name(key_name), _class)
        key_index = (
            _class.body.index(key_attribute) if key_attribute else len(_class.body)
        )

        setter = property_werkzeug_setter_template(key_name, key)
        _class.body.insert(key_index + 1, setter)
