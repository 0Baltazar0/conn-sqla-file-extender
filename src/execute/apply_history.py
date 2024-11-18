import ast
from execute.apply.file_name import apply_file_name
from execute.apply.mime import apply_mime
from execute.apply.starlette import apply_starlette
from execute.apply.werkzeug import apply_werkzeug
from logger import LOGGER
from settings import SETTINGS

from types_source import FileFields
from ast_comments import parse, unparse


def apply_history(
    key: FileFields, key_name: str, target_file: str, class_name: str
) -> None:
    if key.get("unhandled"):
        return
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
        apply_mime(key, key_name, _class)
        apply_file_name(key, key_name, _class)
        if SETTINGS.mode == "flask":
            apply_werkzeug(key, key_name, _class)
        else:
            apply_starlette(key, key_name, _class)

    try:
        textified = unparse(module)
        with open(target_file, "w") as out_file:
            out_file.write(textified)
    except Exception as e:
        LOGGER.warning("Applying history failed, %s", e)
