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


@dataclass
class WerkzeugGetterTemplate:
    """
    ...
    @property
    def {werkzeug_get_name(key_name)}(#self#)->#flask.Response#:
        ...
        mime_type = {mime_key}
        ...
        file_name = {file_name}
        ...
        data = self.{key_name}
        ...
        return flask.send_file(data,attachment_filename=file_name,mimetype=mime_key)

    """

    key_name: str
    key: FileFields
    _class: ast.ClassDef
    _fn: ast.FunctionDef | ast.AsyncFunctionDef | None

    def __post_init__(self) -> None:
        self._fn = get_property_getter(werkzeug_get_name(self.key_name), self._class)

    def add_if_not_present(self, new_key_name: str | None = None) -> None:
        if not self._fn:
            return
        if self._fn not in self._class.body:
            if new_key_name:
                has_setter = get_property_getter(
                    werkzeug_get_name(new_key_name), self._class
                )
                if has_setter:
                    self._class.body.insert(
                        self._class.body.index(has_setter), self._fn
                    )
                    return
            has_old_setter = get_property_getter(
                werkzeug_get_name(self.key_name), self._class
            )
            if has_old_setter:
                self._class.body.insert(
                    self._class.body.index(has_old_setter), self._fn
                )
                return
            else:
                self._class.body.insert(0, self._fn)

    def build_function_base(
        self,
        _key_name: str | None = None,
    ) -> ast.FunctionDef:
        "def {werkzeug_get_name(key_name)}(#self#)->#flask.Response#:"
        "return flask.send_file(data,attachment_filename=file_name,mimetype=mime_key)"
        key_name = _key_name or self.key_name
        return ast.FunctionDef(
            werkzeug_get_name(key_name),
            ast.arguments([], [ast.arg("self")], None, [], [], None, []),
            [
                ast.Return(
                    ast.Call(
                        ast.Attribute(
                            ast.Name("flask"),
                            "send_file",
                        ),
                        [ast.Name("data")],
                        [
                            ast.keyword("filename", ast.Name("file_name")),
                            ast.keyword("media_type", ast.Name("mime_type")),
                        ],
                    )
                )
            ],
            [ast.Name("property")],
            ast.Attribute(
                ast.Name("flask"),
                "Response",
            ),
        )

    def rename_function_base(self, new_key_name: str) -> None:
        "def {werkzeug_get_name(key_name)}(#self#)->#flask.Response#:"
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        _fn.name = werkzeug_get_name(new_key_name)

    @staticmethod
    def _mime_value(key_name: str, key: FileFields) -> ast.Attribute | ast.Constant:
        mime_key = get_mime_variable_name(key, key_name)
        print(key, mime_key)
        return (
            ast.Attribute(ast.Name("self"), mime_key)
            if mime_key
            else ast.Constant(None)
        )

    def build_mime(
        self, _key_name: str | None = None, _key: FileFields | None = None
    ) -> ast.Assign:
        "mime_type = {mime_key}"
        key_name = _key_name or self.key_name
        key = _key or self.key

        return ast.Assign(
            targets=[ast.Name(id="mime_type")],
            value=WerkzeugGetterTemplate._mime_value(key_name, key),
        )

    def rename_mime(self, new_key_name: str, new_key: FileFields) -> None:
        "mime_type = {mime_key}"
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
        if ass:
            ass.value = WerkzeugGetterTemplate._mime_value(new_key_name, new_key)
            print(ast.unparse(ass.value))
        else:
            _fn.body.insert(0, self.build_mime(new_key_name, new_key))

    @staticmethod
    def _file_name_value(
        key_name: str, key: FileFields
    ) -> ast.Attribute | ast.Constant:
        file_name_key = get_file_variable(key, key_name)

        return (
            ast.Attribute(ast.Name("self"), file_name_key)
            if file_name_key
            else ast.Constant(None)
        )

    def build_file_name(
        self, _key_name: str | None = None, _key: FileFields | None = None
    ) -> ast.Assign:
        "file_name = {file_name}"
        key_name = _key_name or self.key_name
        key = _key or self.key

        return ast.Assign(
            targets=[ast.Name(id="file_name")],
            value=WerkzeugGetterTemplate._file_name_value(key_name, key),
        )

    def rename_file_name(self, new_key_name: str, new_key: FileFields) -> None:
        "file_name = {file_name}"
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

        if ass:
            ass.value = WerkzeugGetterTemplate._file_name_value(new_key_name, new_key)
        else:
            _fn.body.insert(0, self.build_file_name(new_key_name, new_key))

    def build_data(self, _key_name: str | None = None) -> ast.Assign:
        "data = self.{key_name}"
        key_name = _key_name or self.key_name
        return ast.Assign(
            targets=[ast.Name(id="data")],
            value=ast.Attribute(ast.Name(id="self"), key_name),
        )

    def rename_data(self, new_key_name: str) -> None:
        "data = self.{key_name}"
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
            ass.value = ast.Attribute(ast.Name(id="self"), new_key_name)
        else:
            _fn.body.insert(0, self.build_data(new_key_name))

    def build(self) -> None:
        _fn = self._fn

        if _fn:
            return

        self._fn = self.build_function_base()
        self.rename_data(self.key_name)
        self.rename_mime(self.key_name, self.key)
        self.rename_file_name(self.key_name, self.key)

        self.add_if_not_present()

    def change(self, new_key_name: str, new_key: FileFields) -> None:
        if not self._fn:
            self._fn = self.build_function_base(new_key_name)
        self.rename_function_base(new_key_name)
        self.rename_data(new_key_name)
        self.rename_mime(new_key_name, new_key)
        self.rename_file_name(new_key_name, new_key)

        self.add_if_not_present(new_key_name)

    def purge(self) -> None:
        if self._fn:
            self._class.body.remove(self._fn)
