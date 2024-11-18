import ast
from execute.apply.file_name import apply_file_name
from execute.apply.mime import apply_mime
from execute.apply.starlette import apply_starlette
from execute.apply.werkzeug import apply_werkzeug
from logger import LOGGER
from naming import (
    get_column_file_name_key,
    get_column_mime_key,
    get_static_file_name_key,
    get_static_mime_key,
    starlette_get_name,
    werkzeug_get_name,
)
from settings import SETTINGS
from templates import (
    file_name_getter_template,
    file_name_setter_template,
    file_name_static_template,
    file_type_column_template,
    mime_type_getter_template,
    mime_type_setter_template,
    mime_type_static_template,
)
from types_source import FileFields
from utils.ast_tools import (
    add_attribute_if_not_exists,
    as_text_replace_content,
    purge_attribute,
    purge_property,
    rename_property_key_name,
    rename_property_key_reference,
    switch_attributes,
    turn_attribute_into_property,
    turn_property_to_attribute,
)

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
            if is_old_static == is_new_static:
                as_text_replace_content(
                    get_static_mime_key(old_key_name),
                    get_static_mime_key(new_key_name),
                    _class,
                )
            else:
                switch_attributes(
                    get_static_mime_key(old_key_name),
                    mime_type_static_template(new_key_name, is_new_static),
                    _class,
                )
                as_text_replace_content(
                    get_static_mime_key(old_key_name),
                    get_static_mime_key(new_key_name),
                    _class,
                )
                return
        if is_old_static:
            if is_new_dynamic:
                turn_attribute_into_property(
                    get_static_mime_key(old_key_name),
                    mime_type_getter_template(new_key_name, is_new_dynamic),
                    mime_type_setter_template(new_key_name, is_new_dynamic),
                    _class,
                )
                as_text_replace_content(
                    get_static_mime_key(old_key_name),
                    get_column_mime_key(new_key_name),
                    _class,
                )
                return
            if is_new_unhandled:
                if SETTINGS.purge_on_unhandled_mime is False:
                    return
                purge_attribute(get_static_mime_key(old_key_name), _class)
                return
            raise Exception(
                "Unexpected Runtime, old_key is static, new key is not static, dynamic or unhandled."
            )
    if is_old_dynamic:
        if is_new_static:
            turn_property_to_attribute(
                get_column_mime_key(old_key_name),
                mime_type_static_template(new_key_name, is_new_static),
                _class,
            )
            as_text_replace_content(
                get_column_mime_key(old_key_name),
                get_static_mime_key(new_key_name),
                _class,
            )
            return
        if is_new_dynamic:
            if is_new_dynamic == is_old_dynamic:
                rename_property_key_name(
                    get_column_mime_key(old_key_name),
                    get_column_mime_key(new_key_name),
                    _class,
                )
                as_text_replace_content(
                    get_column_mime_key(old_key_name),
                    get_column_mime_key(new_key_name),
                    _class,
                )
                return
            else:
                rename_property_key_reference(
                    get_column_mime_key(old_key_name),
                    is_old_dynamic,
                    is_new_dynamic,
                    _class,
                )
                rename_property_key_name(
                    get_column_mime_key(old_key_name),
                    get_column_mime_key(new_key_name),
                    _class,
                )
                as_text_replace_content(
                    get_column_mime_key(old_key_name),
                    get_column_mime_key(new_key_name),
                    _class,
                )
                return
        if is_new_unhandled:
            if SETTINGS.purge_on_unhandled_mime is False:
                return
            purge_property(get_column_mime_key(old_key_name), _class)
            purge_attribute(is_old_dynamic, _class)
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
            if is_old_static == is_new_static:
                as_text_replace_content(
                    get_static_file_name_key(old_key_name),
                    get_static_file_name_key(new_key_name),
                    _class,
                )
                return
            else:
                switch_attributes(
                    get_static_file_name_key(old_key_name),
                    file_name_static_template(new_key_name, is_new_static),
                    _class,
                )
                as_text_replace_content(
                    get_static_file_name_key(old_key_name),
                    get_static_file_name_key(new_key_name),
                    _class,
                )
                return
        if is_old_static:
            if is_new_dynamic:
                turn_attribute_into_property(
                    get_static_file_name_key(old_key_name),
                    file_name_getter_template(new_key_name, is_new_dynamic),
                    file_name_setter_template(new_key_name, is_new_dynamic),
                    _class,
                )
                as_text_replace_content(
                    get_static_file_name_key(old_key_name),
                    get_column_file_name_key(new_key_name),
                    _class,
                )
                add_attribute_if_not_exists(
                    is_new_dynamic, file_type_column_template(is_new_dynamic), _class
                )
                return
            if is_new_unhandled:
                if SETTINGS.purge_on_unhandled_file is False:
                    return
                purge_attribute(get_static_file_name_key(old_key_name), _class)
                return
            raise Exception(
                "Unexpected Runtime, old_key is static, new key is not static, dynamic or unhandled."
            )
    if is_old_dynamic:
        if is_new_static:
            turn_property_to_attribute(
                get_column_file_name_key(old_key_name),
                file_name_static_template(new_key_name, is_new_static),
                _class,
            )
            as_text_replace_content(
                get_column_file_name_key(old_key_name),
                get_static_file_name_key(new_key_name),
                _class,
            )
            purge_attribute(is_old_dynamic, _class)
            return
        if is_new_dynamic:
            if is_new_dynamic == is_old_dynamic:
                rename_property_key_name(
                    get_column_file_name_key(old_key_name),
                    get_column_file_name_key(new_key_name),
                    _class,
                )
                as_text_replace_content(
                    get_column_file_name_key(old_key_name),
                    get_column_file_name_key(new_key_name),
                    _class,
                )
                return
            else:
                rename_property_key_reference(
                    get_column_file_name_key(old_key_name),
                    is_old_dynamic,
                    is_new_dynamic,
                    _class,
                )
                rename_property_key_name(
                    get_column_file_name_key(old_key_name),
                    get_column_file_name_key(new_key_name),
                    _class,
                )
                as_text_replace_content(is_old_dynamic, is_new_dynamic, _class)
                as_text_replace_content(
                    get_column_file_name_key(old_key_name),
                    get_column_file_name_key(new_key_name),
                    _class,
                )
                return
        if is_new_unhandled:
            if SETTINGS.purge_on_unhandled_file is False:
                return
            purge_property(get_column_mime_key(old_key_name), _class)
            purge_attribute(is_old_dynamic, _class)
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
    if new_key.get("unhandled"):
        if SETTINGS.purge_on_unhandled_werkzeug is False:
            return
        purge_property(werkzeug_get_name(old_key_name), _class)
        return
    rename_property_key_name(
        werkzeug_get_name(old_key_name), werkzeug_get_name(new_key_name), _class
    )
    as_text_replace_content(
        werkzeug_get_name(old_key_name), werkzeug_get_name(new_key_name), _class
    )
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
        purge_property(starlette_get_name(old_key_name), _class)
        return
    rename_property_key_name(
        starlette_get_name(old_key_name), starlette_get_name(new_key_name), _class
    )
    as_text_replace_content(
        starlette_get_name(old_key_name), starlette_get_name(new_key_name), _class
    )
    return


def rename(
    old_key: FileFields,
    old_key_name: str,
    new_key: FileFields,
    new_key_name: str,
    target_file: str,
    class_name: str,
) -> None:
    with open(target_file) as infile:
        module: ast.Module = parse(infile.read())  # type:ignore
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
        LOGGER.warning("Renamming failed, %s", e)
