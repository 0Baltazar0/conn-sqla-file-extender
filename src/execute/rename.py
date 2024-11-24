import ast
from execute.apply.file_name import apply_file_name
from execute.apply.mime import apply_mime
from execute.apply.starlette import apply_starlette
from execute.apply.werkzeug import apply_werkzeug
from logger import LOGGER

from settings import SETTINGS
from template.file_name.dynamic import DynamicFileName
from template.file_name.static import StaticFileName
from template.mime.dynamic import DynamicMimeType
from template.mime.static import StaticMimeType

from template.starlette.starlette import Starlette

from template.werkzeug.werkzeug import Werkzeug
from types_source import FileFields

from ast_comments import unparse, parse


def rename_mime_fields(
    old_key: FileFields,
    old_key_name: str,
    new_key_name: str,
    new_key: FileFields,
    _class: ast.ClassDef,
) -> None:
    if old_key.get("mime_unhandled"):
        if new_key.get("mime_unhandled") is not None:
            apply_mime(new_key, new_key_name, _class)
        return

    is_old_static = old_key.get("mime_type_fix")
    is_new_static = new_key.get("mime_type_fix")
    is_old_dynamic = old_key.get("mime_type_field_name")
    is_new_dynamic = new_key.get("mime_type_field_name")
    is_new_unhandled = new_key.get("mime_unhandled")

    if is_old_static or is_new_static:
        if is_old_static and is_new_static:
            StaticMimeType(old_key_name, old_key, _class).change(new_key_name, new_key)
            return
        if is_old_static:
            if is_new_dynamic:
                StaticMimeType(old_key_name, old_key, _class).purge()
                DynamicMimeType(new_key_name, new_key, _class).build()
                return
            if is_new_unhandled:
                if SETTINGS.purge_on_unhandled_mime is False:
                    return
                StaticMimeType(old_key_name, old_key, _class).purge()
                return
            raise Exception(
                "Unexpected Runtime, old_key is static, new key is not static, dynamic or unhandled."
            )
    if is_old_dynamic:
        if is_new_static:
            DynamicMimeType(old_key_name, old_key, _class).purge()
            StaticMimeType(new_key_name, new_key, _class).build()
            return
        if is_new_dynamic:
            DynamicMimeType(old_key_name, old_key, _class).change(new_key_name, new_key)
            return
        if is_new_unhandled:
            if SETTINGS.purge_on_unhandled_mime is False:
                return
            DynamicMimeType(old_key_name, old_key, _class).purge()
            return


def rename_file_name_fields(
    old_key: FileFields,
    old_key_name: str,
    new_key_name: str,
    new_key: FileFields,
    _class: ast.ClassDef,
) -> None:
    if old_key.get("name_unhandled"):
        if new_key.get("name_unhandled") is not None:
            apply_file_name(new_key, new_key_name, _class)
        return

    is_old_static = old_key.get("file_name_fix")
    is_new_static = new_key.get("file_name_fix")
    is_old_dynamic = old_key.get("file_name_field_name")
    is_new_dynamic = new_key.get("file_name_field_name")
    is_new_unhandled = new_key.get("name_unhandled")

    if is_old_static or is_new_static:
        if is_old_static and is_new_static:
            StaticFileName(old_key_name, old_key, _class).change(new_key_name, new_key)
            return
        if is_old_static:
            if is_new_dynamic:
                StaticFileName(old_key_name, old_key, _class).purge()
                DynamicFileName(new_key_name, new_key, _class).build()
                return

            if is_new_unhandled:
                if SETTINGS.purge_on_unhandled_file is False:
                    return
                StaticFileName(old_key_name, old_key, _class).purge()
                return
            raise Exception(
                "Unexpected Runtime, old_key is static, new key is not static, dynamic or unhandled."
            )
    if is_old_dynamic:
        if is_new_static:
            DynamicFileName(old_key_name, old_key, _class).purge()
            StaticFileName(new_key_name, new_key, _class).build()
            return
        if is_new_dynamic:
            DynamicMimeType(old_key_name, old_key, _class).change(new_key_name, new_key)
            return
        if is_new_unhandled:
            if SETTINGS.purge_on_unhandled_file is False:
                return
            DynamicFileName(old_key_name, old_key, _class).purge()
            return


def rename_werkzeug_properties(
    old_key: FileFields,
    old_key_name: str,
    new_key_name: str,
    new_key: FileFields,
    _class: ast.ClassDef,
) -> None:
    if old_key.get("unhandled"):
        if SETTINGS.mode == "flask" and new_key.get("unhandled") is not None:
            apply_werkzeug(new_key, new_key_name, _class)
        return
    if new_key.get("unhandled"):
        if SETTINGS.purge_on_unhandled_werkzeug is False:
            return
        Werkzeug(old_key_name, old_key, _class).purge()
        return
    Werkzeug(old_key_name, old_key, _class).change(new_key_name, new_key)

    return


def rename_starlette_properties(
    old_key: FileFields,
    old_key_name: str,
    new_key_name: str,
    new_key: FileFields,
    _class: ast.ClassDef,
) -> None:
    if old_key.get("unhandled"):
        if SETTINGS.mode == "asyncio" and new_key.get("unhandled") is not None:
            apply_starlette(new_key, new_key_name, _class)
    if new_key.get("unhandled"):
        if SETTINGS.purge_on_unhandled_werkzeug is False:
            return
        Starlette(old_key_name, old_key, _class).purge()
        return
    Starlette(old_key_name, old_key, _class).change(new_key_name, new_key)

    return


def rename(
    old_key: FileFields,
    old_key_name: str,
    new_key: FileFields,
    new_key_name: str,
    target_file: str,
    class_name: str,
) -> None:
    with open(target_file) as in_file:
        module: ast.Module = parse(in_file.read())  # type:ignore
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
        rename_mime_fields(old_key, old_key_name, new_key_name, new_key, _class)
        rename_file_name_fields(old_key, old_key_name, new_key_name, new_key, _class)
        rename_werkzeug_properties(old_key, old_key_name, new_key_name, new_key, _class)
        rename_starlette_properties(
            old_key, old_key_name, new_key_name, new_key, _class
        )

    try:
        textified = unparse(module)
        with open(target_file, "w") as out_file:
            out_file.write(textified)
    except Exception as e:
        LOGGER.warning("Renaming failed, %s", e)
