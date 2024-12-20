import ast
from dataclasses import dataclass
from datetime import datetime
from os import name

from naming import (
    get_column_file_name_key,
    get_column_mime_key,
    get_file_variable,
    get_mime_variable_name,
    get_static_file_name_key,
    get_static_mime_key,
    starlette_get_name,
    werkzeug_get_name,
)
from types_source import FileFields
from utils.ast_tools import (
    as_text_replace_content,
    get_attribute,
    get_attribute_index,
    get_property_setter,
    rename_decorator_setter,
)
import ast_comments


class TemplateException(Exception):
    pass


def property_werkzeug_getter_template(
    key_name: str, key: FileFields
) -> ast.FunctionDef:
    mime_key = f"self.{get_mime_variable_name(key,key_name)}" or "None"
    file_name = f"self.{get_file_variable(key,key_name)}" or "None"
    template = f"""
@property
def {werkzeug_get_name(key_name)}(self)->flask.Response:
    mime_type = {mime_key}
    file_name = {file_name}
    data = self.{key_name}
    return flask.send_file(data,attachment_filename=file_name,mimetype=mime_type)
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


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

        attribute = next(
            (
                decor
                for decor in _fn.decorator_list
                if isinstance(decor, ast.Attribute)
                and isinstance(decor.value, ast.Name)
                and decor.attr == "setter"
                and decor.value.id == self.key_name
            ),
            None,
        )

        if attribute:
            attribute.value = ast.Name(id=new_key_name)
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
                and self.is_file_mimetype(ass.value)
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
                and self.is_file_mimetype(ass.value)
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
        self.rename_function_base(new_key_name)
        self.rename_data_assign(new_key_name)
        self.rename_decorator(new_key_name)
        self.build_file_name_assign(new_key, new_key_name)
        self.rename_mime_assign(new_key_name, new_key)


def property_werkzeug_setter_template(
    key_name: str, key: FileFields
) -> ast.FunctionDef:
    mime_key = (
        f"self.{get_mime_variable_name(key,key_name)}"
        if key.get("mime_type_field_name")
        else None
    )
    file_name = (
        f"self.{get_file_variable(key,key_name)}"
        if key.get("file_name_field_name")
        else None
    )
    template = f"""
@{werkzeug_get_name(key_name)}.setter
def {werkzeug_get_name(key_name)}(self,file:werkzeug.FileStorage)->None:
    data = file.read()
    self.{key_name} = data
    {('self.'+mime_key+' = file.mimetype') if mime_key else ''}
    {('self.'+file_name+' = file.filename') if file_name else ''}
    
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def property_starlette_getter_template(
    key_name: str, key: FileFields
) -> ast.FunctionDef:
    mime_key = f"self.{get_mime_variable_name(key,key_name)}" or "None"
    file_name = f"self.{get_file_variable(key,key_name)}" or "None"
    template = f"""
@property
async def {starlette_get_name(key_name)}(self)->starlette.responses.FileResponse:
    mime_type = {mime_key}
    file_name = {file_name}
    return starlette.responses.FileResponse(
        self.{key_name},
        filename=file_name,
        media_type=mime_type
    )
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def property_starlette_setter_template(
    key_name: str, key: FileFields
) -> ast.FunctionDef:
    mime_key = (
        f"self.{get_mime_variable_name(key,key_name)}"
        if key.get("mime_type_field_name")
        else None
    )
    file_name = (
        f"self.{get_file_variable(key,key_name)}"
        if key.get("file_name_field_name")
        else None
    )
    template = f"""
@{starlette_get_name(key_name)}.setter
async def {starlette_get_name(key_name)}(self,file:starlette.datastructures.UploadFile)->None:
    mime_type = file.content_type
    file_name = file.filename
    data = await file.read()
    self.{key} = data
    {('self.'+mime_key+' = mime_type') if mime_key else ''}
    {('self.'+file_name+' = file_name') if file_name else ''}
    
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def mime_type_column_template(column_name: str) -> ast.AnnAssign:
    template = f"{get_column_mime_key(column_name)}:Mapped[str] = String('{get_column_mime_key(column_name)}')"

    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.AnnAssign):
        raise Exception(f"Somehow this is not a Assign {type(fun)}")

    return fun


def mime_type_getter_template(key_name: str, column_name: str) -> ast.FunctionDef:
    template = f"""@property
def {get_column_mime_key(key_name)}(self)->str:
    return self.{column_name}
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def mime_type_setter_template(key_name: str, column_name: str) -> ast.FunctionDef:
    template = f"""@{get_column_mime_key(key_name)}.setter
def {get_column_mime_key(key_name)}(self,value:str)->None:
    self.{column_name} = value
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def mime_type_static_template(key_name: str, static_mime: str) -> ast.AnnAssign:
    template = (
        f"{get_static_mime_key(key_name)}:Literal['{static_mime}'] = '{static_mime}'"
    )

    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.AnnAssign):
        raise Exception(f"Somehow this is not a Assign {type(fun)}")

    return fun


def file_type_column_template(property_name: str) -> ast.AnnAssign:
    template = f"{get_column_file_name_key(property_name)}:Mapped[str] = String('{get_column_file_name_key(property_name)}')"

    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.AnnAssign):
        raise Exception(f"Somehow this is not a Assign {type(fun)}")

    return fun


def file_name_static_template(key_name: str, static_name: str) -> ast.AnnAssign:
    template = f"{get_static_file_name_key(key_name)}:Literal['{static_name}'] = '{static_name}'"

    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.AnnAssign):
        raise Exception(f"Somehow this is not a Assign {type(fun)}")

    return fun


def file_name_getter_template(key_name: str, column_name: str) -> ast.FunctionDef:
    template = f"""@property
def {get_column_file_name_key(key_name)}(self)->str:
    return self.{column_name}
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def file_name_setter_template(key_name: str, column_name: str) -> ast.FunctionDef:
    template = f"""@{get_column_file_name_key(key_name)}.setter
def {get_column_file_name_key(key_name)}(self,value:str)->None:
    self.{column_name} = value
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun
