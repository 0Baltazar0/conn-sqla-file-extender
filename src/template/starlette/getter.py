import ast
from dataclasses import dataclass

from naming import get_file_variable, get_mime_variable_name, werkzeug_get_name
from template.exceptions import TemplateException
from types_source import FileFields
from utils.ast_tools import (
    get_attribute_index,
    get_property_getter,
    get_property_setter,
)


"""
@property
def {werkzeug_get_name(key_name)}(self)->>starlette.responses.FileResponse:
    mime_type = {mime_key}
    file_name = {file_name}
    return flask.send_file(self.{key_name},attachment_filename={file_name},mimetype={mime_key})

"""


@dataclass
class StarletteGetterTemplate:
    key_name: str
    key: FileFields
    _class: ast.ClassDef
    _fn: ast.FunctionDef | ast.AsyncFunctionDef | None

    def __post_init__(self) -> None:
        self._fn = get_property_getter(werkzeug_get_name(self.key_name), self._class)

    def build_function_base(self, _key_name: str | None = None) -> ast.AsyncFunctionDef:
        key_name = _key_name or self.key_name
        _fn = ast.parse(
            f"@property\nasync def {werkzeug_get_name(key_name)}(self)->>starlette.responses.FileResponse:\n\treturn starlette.responses.FileResponse(self.{key_name},filename=file_name,media_type=mime_type)"
        ).body[0]

        if not isinstance(_fn, ast.AsyncFunctionDef):
            raise TemplateException()

        _fn.body = []
        return _fn

    def rename_function_base(self, new_key_name: str) -> None:
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        _fn.name = new_key_name

    def build_mime(
        self, _key_name: str | None = None, _key: FileFields | None = None
    ) -> ast.Assign:
        key_name = _key_name or self.key_name
        key = _key or self.key

        mime_key = f"self.{get_mime_variable_name(key,key_name)}" or "None"

        expr = ast.parse(mime_key).body[0]

        if not isinstance(expr, ast.expr):
            raise TemplateException()

        return ast.Assign(targets=[ast.Name(id="mime_type")], value=expr)

    def rename_mime(self, new_key_name: str, new_key: FileFields) -> None:
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        ass = next(
            (
                _ass
                for _ass in _fn.body
                if isinstance(_ass, ast.Assign)
                and isinstance(_ass.targets[0], ast.Name)
                and _ass.targets[0].id == "mime_type"
            ),
            None,
        )
        mime_key = f"self.{get_mime_variable_name(new_key,new_key_name)}" or "None"
        expr = ast.parse(mime_key).body[0]

        if not isinstance(expr, ast.expr):
            raise TemplateException()
        if ass:
            ass.value = expr
        else:
            _fn.body.insert(0, self.build_mime(new_key_name, new_key))

    def build_file_name(
        self, _key_name: str | None = None, _key: FileFields | None = None
    ) -> ast.Assign:
        key_name = _key_name or self.key_name
        key = _key or self.key

        file_name_key = f"self.{get_file_variable(key,key_name)}" or "None"

        expr = ast.parse(file_name_key).body[0]

        if not isinstance(expr, ast.expr):
            raise TemplateException()

        return ast.Assign(targets=[ast.Name(id="file_name")], value=expr)

    def rename_file_name(self, new_key_name: str, new_key: FileFields) -> None:
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        ass = next(
            (
                _ass
                for _ass in _fn.body
                if isinstance(_ass, ast.Assign)
                and isinstance(_ass.targets[0], ast.Name)
                and _ass.targets[0].id == "file_name"
            ),
            None,
        )
        file_name_key = f"self.{get_file_variable(new_key,new_key_name)}" or "None"
        expr = ast.parse(file_name_key).body[0]

        if not isinstance(expr, ast.expr):
            raise TemplateException()
        if ass:
            ass.value = expr
        else:
            _fn.body.insert(0, self.build_mime(new_key_name, new_key))

    def build_data(self, _key_name: str | None = None) -> ast.Assign:
        key_name = _key_name or self.key_name
        return ast.Assign(targets=[ast.Name(id="data")], value=ast.Name(id=key_name))

    def rename_data(self, new_key_name: str) -> None:
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        ass = next(
            (
                _ass
                for _ass in _fn.body
                if isinstance(_ass, ast.Assign)
                and isinstance(_ass.targets[0], ast.Name)
                and _ass.targets[0].id == "data"
            ),
            None,
        )

        if ass:
            ass.value = ast.Name(id=new_key_name)
        else:
            _fn.body.insert(0, self.build_data(new_key_name))

    def build(self) -> None:
        _fn = self._fn

        if _fn:
            return

        self._fn = self.build_function_base()
        self.build_mime()
        self.build_file_name()
        self.build_data()

        has_setter = get_property_setter(werkzeug_get_name(self.key_name), self._class)

        if not has_setter:
            index = get_attribute_index(self.key_name, self._class) or 0

            self._class.body.insert(index, self._fn)
        else:
            index = self._class.body.index(has_setter)

            self._class.body.insert(index, self._fn)

    def change(self, new_key_name: str, new_key: FileFields) -> None:
        if not self._fn:
            self._fn = self.build_function_base(new_key_name)
        self.rename_function_base(new_key_name)
        self.rename_data(new_key_name)
        self.rename_mime(new_key_name, new_key)
        self.rename_file_name(new_key_name, new_key)

    def purge(self) -> None:
        if self._fn:
            self._class.body.remove(self._fn)
