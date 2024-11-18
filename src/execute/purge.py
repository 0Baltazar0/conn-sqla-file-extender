import ast
from logger import LOGGER
from naming import (
    get_column_mime_key,
    get_static_file_name_key,
    get_static_mime_key,
    starlette_get_name,
    werkzeug_get_name,
)
from types_source import FileFields
from ast_comments import parse, unparse

from utils.ast_tools import purge_attribute, purge_property


def purge_mime(old_key_name: str, old_key: FileFields, _class: ast.ClassDef) -> None:
    if old_key.get("mime_unhandled"):
        return

    if old_key.get("mime_type_fix"):
        purge_attribute(get_static_mime_key(old_key_name), _class)
        return

    if old_key.get("mime_type_field_name"):
        purge_attribute(get_static_mime_key(old_key_name), _class)
        purge_property(get_column_mime_key(old_key_name), _class)
        return


def purge_file(old_key_name: str, old_key: FileFields, _class: ast.ClassDef) -> None:
    if old_key.get("name_unhandled"):
        return

    if "file_name_fix" in old_key:
        purge_attribute(get_static_file_name_key(old_key_name), _class)
        return

    if "file_name_field_name" in old_key:
        purge_attribute(get_static_mime_key(old_key_name), _class)
        purge_attribute(old_key["file_name_field_name"], _class)
        purge_property(get_column_mime_key(old_key_name), _class)
        return


def purge_werkzeug(old_key_name: str, _class: ast.ClassDef) -> None:
    purge_property(werkzeug_get_name(old_key_name), _class)


def purge_starlette(old_key_name: str, _class: ast.ClassDef) -> None:
    purge_property(starlette_get_name(old_key_name), _class)


def purge(
    old_key_name: str, old_key: FileFields, file_name: str, class_name: str
) -> None:
    with open(file_name) as in_file:
        module: ast.Module = parse(in_file.read())  # type: ignore
        _class = next(
            (
                entry
                for entry in module.body
                if isinstance(entry, ast.ClassDef) and entry.name == class_name
            ),
            None,
        )
        if not _class:
            raise Exception("Class object is not found, can't execute apply")

    try:
        purge_mime(old_key_name, old_key, _class)
        purge_file(old_key_name, old_key, _class)
        purge_werkzeug(old_key_name, _class)
        purge_starlette(old_key_name, _class)
        textified = unparse(module)
        with open(file_name, "w") as out_file:
            out_file.write(textified)
    except Exception as e:
        LOGGER.warning("Purging failed, %s", e)
