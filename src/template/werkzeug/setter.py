import ast
from dataclasses import dataclass
from naming import get_file_variable, get_mime_variable_name, werkzeug_get_name
from template.exceptions import TemplateException
from templates import property_werkzeug_setter_template
from types_source import FileFields
from utils.ast_tools import get_attribute_index, get_property_setter


@dataclass
class WerkzeugSetterTemplate:
    key_name: str
    key: FileFields
    _class: ast.ClassDef
    _fn: ast.FunctionDef | ast.AsyncFunctionDef | None

    def __post_init__(self):
        self._fn = get_property_setter(werkzeug_get_name(self.key_name), self._class)

    def find_fn(self) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        return get_property_setter(werkzeug_get_name(self.key_name), self._class)

    def resolve(self) -> ast.FunctionDef:
        return property_werkzeug_setter_template(self.key_name, self.key)

    def build_decorator(self, _key_name: str | None = None) -> ast.Attribute:
        key_name = _key_name or self.key_name

        return ast.Attribute(value=ast.Name(id=key_name), attr="setter")

    def rename_decorator(self, new_key_name: str) -> None:
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        decorator = next(
            (
                decor
                for decor in _fn.decorator_list
                if isinstance(decor, ast.Attribute)
                and isinstance(decor.value, ast.Name)
                and decor.attr == "setter"
                and decor.value.id == werkzeug_get_name(self.key_name)
            ),
            None,
        )

        if decorator:
            decorator.value = ast.Name(id=werkzeug_get_name(new_key_name))
        else:
            _fn.decorator_list.append(self.build_decorator(new_key_name))

    def build_function_base(self, _key_name: str | None = None) -> ast.FunctionDef:
        key_name = _key_name or self.key_name

        _fn = ast.parse(
            f"def {werkzeug_get_name(key_name)}(self,file:werkzeug.FileStorage)->None:\n\tpass"
        ).body[0]

        if not isinstance(_fn, ast.FunctionDef):
            raise TemplateException()

        _fn.body = []
        return _fn

    def rename_function_base(self, new_key_name: str) -> None:
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        _fn.name = new_key_name

    @staticmethod
    def is_file_read_call(expr: ast.expr) -> bool:
        if not isinstance(expr, ast.Call):
            return False

        return (
            isinstance(expr.func, ast.Attribute)
            and isinstance(expr.func.value, ast.Name)
            and expr.func.value.id == "file"
            and expr.func.attr == "read"
        )

    def build_data_assign(self, _key_name: str | None = None) -> ast.Assign:
        key_name = _key_name or self.key_name
        return ast.Assign(
            targets=[ast.Attribute(value=ast.Name(id=key_name), attr="self")],
            value=ast.Call(
                args=[],
                keywords=[],
                func=ast.Attribute(value=ast.Name(id="file"), attr="read"),
            ),
        )

    def rename_data_assign(self, new_key_name: str) -> None:
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        assign = next(
            (
                ass
                for ass in self._class.body
                if isinstance(ass, ast.Assign)
                and isinstance(ass.targets[0], ast.Attribute)
                and ass.targets[0].attr == self.key_name
                and isinstance(ass.targets[0].value, ast.Name)
                and ass.targets[0].value.id == "self"
                and WerkzeugSetterTemplate.is_file_read_call(ass.value)
            ),
            None,
        )

        if assign:
            attr = assign.targets[0]
            if not isinstance(attr, ast.Attribute):
                raise TemplateException()

            attr.attr = new_key_name

        else:
            _fn.body.insert(0, self.build_data_assign(new_key_name))

    @staticmethod
    def is_file_mimetype(expr: ast.expr) -> bool:
        if not isinstance(expr, ast.Attribute):
            return False

        if not isinstance(expr.value, ast.Name):
            return False

        if not expr.value.id == "mimetype":
            return False

        if not expr.attr == "file":
            return False
        return True

    @staticmethod
    def is_file_file_name(expr: ast.expr) -> bool:
        if not isinstance(expr, ast.Attribute):
            return False

        if not isinstance(expr.value, ast.Name):
            return False

        if not expr.value.id == "filename":
            return False

        if not expr.attr == "file":
            return False
        return True

    def build_mime_assign(
        self, _key: FileFields | None = None, _key_name: str | None = None
    ) -> ast.Assign | None:
        key = _key or self.key
        key_name = _key_name or self.key_name
        mime_key = get_mime_variable_name(key, key_name)
        if not mime_key or not key.get("mime_type_field_name"):
            return None
        return ast.Assign(
            targets=[ast.Attribute(value=ast.Name(id=mime_key), attr="self")],
            value=ast.Attribute(value=ast.Name(id="mimetype"), attr="file"),
        )

    def rename_mime_assign(self, new_key_name: str, key: FileFields) -> None:
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        mime_ass = next(
            (
                ass
                for ass in self._class.body
                if isinstance(ass, ast.Assign)
                and isinstance(ass.targets[0], ast.Attribute)
                and ass.targets[0].attr
                == get_mime_variable_name(self.key, self.key_name)
                and isinstance(ass.targets[0].value, ast.Name)
                and ass.targets[0].value.id == "self"
                and WerkzeugSetterTemplate.is_file_mimetype(ass.value)
            ),
            None,
        )

        mime_key = get_mime_variable_name(key, new_key_name)
        if mime_ass:
            if key.get("mime_type_field_name") and mime_key:
                attr = mime_ass.targets[0]
                if not isinstance(attr, ast.Attribute):
                    raise TemplateException()

                attr.attr = mime_key

                return None
            else:
                _fn.body.remove(mime_ass)
        else:
            mime = self.build_mime_assign(key, new_key_name)
            if mime:
                _fn.body.insert(0, mime)

    def build_file_name_assign(
        self, _key: FileFields | None = None, _key_name: str | None = None
    ) -> ast.Assign | None:
        key = _key or self.key
        key_name = _key_name or self.key_name
        file_ass = get_file_variable(key, key_name)
        if not file_ass or not key.get("file_name_field_name"):
            return None
        return ast.Assign(
            targets=[ast.Attribute(value=ast.Name(id=file_ass), attr="self")],
            value=ast.Attribute(value=ast.Name(id="mimetype"), attr="file"),
        )

    def rename_file_name_assign(self, new_key_name: str, key: FileFields) -> None:
        _fn = self._fn
        if not _fn:
            raise TemplateException()

        file_ass = next(
            (
                ass
                for ass in self._class.body
                if isinstance(ass, ast.Assign)
                and isinstance(ass.targets[0], ast.Attribute)
                and ass.targets[0].attr
                == get_mime_variable_name(self.key, self.key_name)
                and isinstance(ass.targets[0].value, ast.Name)
                and ass.targets[0].value.id == "self"
                and WerkzeugSetterTemplate.is_file_file_name(ass.value)
            ),
            None,
        )

        file_name = get_file_variable(key, new_key_name)
        if file_ass:
            if key.get("file_name_field_name") and file_name:
                attr = file_ass.targets[0]
                if not isinstance(attr, ast.Attribute):
                    raise TemplateException()

                attr.attr = file_name

                return None
            else:
                _fn.body.remove(file_ass)
        else:
            mime = self.build_mime_assign(key, new_key_name)
            if mime:
                _fn.body.insert(0, mime)

    def build(self) -> None:
        exists = self.find_fn()
        if exists:
            return

        key = get_attribute_index(self.key_name, self._class) or 0

        fun = self.build_function_base()
        self._fn = fun

        self.build_data_assign()
        self.build_decorator()
        self.build_file_name_assign()
        self.build_mime_assign()

        self._class.body.insert(key, fun)

    def change(self, new_key_name: str, new_key: FileFields) -> None:
        if not self._fn:
            self._fn = self.build_function_base(new_key_name)
        self.rename_function_base(new_key_name)
        self.rename_data_assign(new_key_name)
        self.rename_decorator(new_key_name)
        self.build_file_name_assign(new_key, new_key_name)
        self.rename_mime_assign(new_key_name, new_key)

    def purge(self) -> None:
        if self._fn:
            self._class.body.remove(self._fn)
