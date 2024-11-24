import ast
from logger import LOGGER

from template.file_name.dynamic import DynamicFileName
from template.file_name.static import StaticFileName
from template.mime.dynamic import DynamicMimeType
from template.mime.static import StaticMimeType
from template.starlette.starlette import Starlette
from template.werkzeug.werkzeug import Werkzeug
from types_source import FileFields
from ast_comments import parse, unparse


def purge_mime(old_key_name: str, old_key: FileFields, _class: ast.ClassDef) -> None:
    if old_key.get("mime_unhandled"):
        return

    if old_key.get("mime_type_fix"):
        static_mime = StaticMimeType(old_key_name, old_key, _class)
        static_mime.purge()
        return

    if old_key.get("mime_type_field_name"):
        dynamic_mime = DynamicMimeType(old_key_name, old_key, _class)
        dynamic_mime.purge()
        return


def purge_file(old_key_name: str, old_key: FileFields, _class: ast.ClassDef) -> None:
    if old_key.get("name_unhandled"):
        return

    if "file_name_fix" in old_key:
        static_file_name = StaticFileName(old_key_name, old_key, _class)
        static_file_name.purge()
        return

    if "file_name_field_name" in old_key:
        dynamic_file_name = DynamicFileName(old_key_name, old_key, _class)
        dynamic_file_name.purge()
        return


def purge_werkzeug(old_key_name: str, _class: ast.ClassDef) -> None:
    Werkzeug(old_key_name, {}, _class).purge()


def purge_starlette(old_key_name: str, _class: ast.ClassDef) -> None:
    Starlette(old_key_name, {}, _class).purge()


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
