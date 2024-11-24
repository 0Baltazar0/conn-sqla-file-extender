import ast
from dataclasses import dataclass
from naming import (
    get_file_variable,
    get_mime_variable_name,
    starlette_get_name,
)
from template.exceptions import TemplateException
from templates import property_werkzeug_setter_template
from types_source import FileFields
from utils.ast_tools import (
    get_assign,
    get_property_getter,
    get_property_setter,
)


@dataclass
class StarletteSetterTemplate:
    """
    @{starlette_get_name(key_name)}.setter
    ...
    async def {starlette_get_name(key_name)}(#self,file:starlette.datastructures.UploadFile#)->#None#:
        ...
        mime_type = file.content_type
        ...
        file_name = file.filename
        ...
        data = await file.read()
        ...
        self.{key} = data
        ...
        {('self.'+mime_key+' = mime_type') if mime_key else ''}
        ...
        {('self.'+file_name+' = file_name') if file_name else ''}


    """

    key_name: str
    key: FileFields
    _class: ast.ClassDef
    _fn: ast.FunctionDef | ast.AsyncFunctionDef | None

    def __post_init__(self):
        self._fn = get_property_setter(starlette_get_name(self.key_name), self._class)

    def find_fn(self) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        return get_property_setter(starlette_get_name(self.key_name), self._class)

    def add_if_not_present(self, new_key_name: str | None = None) -> None:
        if not self._fn:
            raise TemplateException("")
        if self._fn not in self._class.body:
            if new_key_name:
                has_setter = get_property_getter(
                    starlette_get_name(new_key_name), self._class
                )
                if has_setter:
                    self._class.body.insert(
                        self._class.body.index(has_setter) + 1, self._fn
                    )
                    return
            has_old_setter = get_property_getter(
                starlette_get_name(self.key_name), self._class
            )
            if has_old_setter:
                self._class.body.insert(
                    self._class.body.index(has_old_setter) + 1, self._fn
                )
                return
            else:
                self._class.body.insert(0, self._fn)

    def build_decorator(self, _key_name: str | None = None) -> ast.Attribute:
        "@{starlette_get_name(key_name)}.setter"
        key_name = _key_name or self.key_name
        return ast.Attribute(ast.Name(starlette_get_name(key_name)), "setter")

    def rename_decorator(self, new_key_name: str) -> None:
        "@{starlette_get_name(key_name)}.setter"
        if not self._fn:
            raise TemplateException("")

        dec = next(
            (
                dec
                for dec in self._fn.decorator_list
                if isinstance(dec, ast.Attribute)
                and isinstance(dec.value, ast.Name)
                and dec.value.id == starlette_get_name(new_key_name)
                and dec.attr == "setter"
            ),
            None,
        )
        if not dec:
            self._fn.decorator_list.append(self.build_decorator(new_key_name))

        else:
            if self._fn.decorator_list.index(dec) != len(self._fn.decorator_list) - 1:
                raise TemplateException("")
            dec.value = ast.Name(starlette_get_name(new_key_name))

    def build_function_base(self, _key_name: str | None = None) -> ast.AsyncFunctionDef:
        "async def {starlette_get_name(key_name)}(#self,file:starlette.datastructures.UploadFile#)->#None#:"
        key_name = _key_name or self.key_name

        return ast.AsyncFunctionDef(
            starlette_get_name(key_name),
            ast.arguments(
                [],
                [
                    ast.arg("self"),
                    ast.arg(
                        "file",
                        ast.Attribute(
                            ast.Attribute(ast.Name("starlette"), "datastructures"),
                            "UploadFile",
                        ),
                    ),
                ],
                None,
                [],
                [],
                None,
                [],
            ),
            [],
            [],
            ast.Constant(None),
        )

    def rename_function_base(self, new_key_name: str) -> None:
        "async def {starlette_get_name(key_name)}(#self,file:starlette.datastructures.UploadFile#)->#None#:"
        if not self._fn:
            raise TemplateException("")

        self._fn.name = starlette_get_name(new_key_name)

    def build_static_mime_definition(self) -> ast.Assign:
        "mime_type = file.content_type"
        return ast.Assign(
            [ast.Name("mime_type")], ast.Attribute(ast.Name("file"), "content_type")
        )

    def rename_static_mime_definition(self) -> None:
        "mime_type = file.content_type"
        if not self._fn:
            raise TemplateException("")

        ass = get_assign("mime_type", self._fn, True)
        if not ass:
            self._fn.body.insert(0, self.build_static_mime_definition())
        else:
            return

    def build_static_file_name_definition(self) -> ast.Assign:
        "file_name = file.filename"
        return ast.Assign(
            [ast.Name("file_name")], ast.Attribute(ast.Name("file"), "filename")
        )

    def rename_static_file_name_definition(self) -> None:
        "file_name = file.filename"
        if not self._fn:
            raise TemplateException("")

        ass = get_assign("file_name", self._fn, True)
        if not ass:
            self._fn.body.insert(0, self.build_static_file_name_definition())
        else:
            return

    def build_data_assign(self) -> ast.Assign:
        "data = await file.read()"
        return ast.Assign(
            [ast.Name("data")],
            ast.Await(ast.Call(ast.Attribute(ast.Name("file"), "read"), [], [])),
        )

    def rename_data_assign(self) -> None:
        "data = await file.read()"
        if not self._fn:
            raise TemplateException("")
        ass = get_assign("data", self._fn, True)

        if not ass:
            self._fn.body.insert(0, self.build_data_assign())
        else:
            return

    def build_key_name_assign(self, _key_name: str) -> ast.Assign:
        "self.{key_name} = data"
        key_name = _key_name or self.key_name
        return ast.Assign([ast.Attribute(ast.Name("self"), key_name)], ast.Name("data"))

    def rename_key_name_assign(self, new_key_name: str) -> None:
        "self.{key_name} = data"
        if not self._fn:
            raise TemplateException("")
        ass = next(
            (
                _ass
                for _ass in self._fn.body
                if isinstance(_ass, ast.Assign)
                and isinstance(_ass.targets[0], ast.Attribute)
                and isinstance(_ass.targets[0].value, ast.Name)
                and _ass.targets[0].value.id == "self"
                and _ass.targets[0].attr in [new_key_name, self.key_name]
                and isinstance(_ass.value, ast.Name)
                and _ass.value.id == "data"
            ),
            None,
        )
        if ass:
            ass.targets[0] = ast.Attribute(ast.Name("self"), new_key_name)
        else:
            self._fn.body.append(self.build_key_name_assign(new_key_name))

    def build_optional_mime(
        self, _key_name: str | None, _key: FileFields | None
    ) -> ast.Assign | None:
        "{('self.'+mime_key+' = mime_type') if mime_key else ''}"
        key_name = _key_name or self.key_name
        key = _key or self.key
        mime_key = get_mime_variable_name(key, key_name)
        if not mime_key:
            return None
        return ast.Assign(
            [ast.Attribute(ast.Name("self"), mime_key)], ast.Name("mime_type")
        )

    def rename_optional_mime(self, new_key_name: str, new_key: FileFields) -> None:
        "{('self.'+mime_key+' = mime_type') if mime_key else ''}"
        if not self._fn:
            raise TemplateException("")
        ass = next(
            (
                _ass
                for _ass in self._fn.body
                if isinstance(_ass, ast.Assign)
                and isinstance(_ass.targets[0], ast.Attribute)
                and isinstance(_ass.targets[0].value, ast.Name)
                and _ass.targets[0].value.id == "self"
                and _ass.targets[0].attr
                in [
                    get_mime_variable_name(new_key, new_key_name),
                    get_mime_variable_name(self.key, new_key_name),
                    get_mime_variable_name(new_key, self.key_name),
                    get_mime_variable_name(self.key, self.key_name),
                ]
            ),
            None,
        )
        mime_key = get_mime_variable_name(new_key, new_key_name)
        if ass:
            if not mime_key:
                self._fn.body.remove(ass)
            else:
                ass.targets[0] = ast.Attribute(ast.Name("self"), mime_key)
        else:
            should = self.build_optional_mime(new_key_name, new_key)
            if should:
                self._fn.body.append(should)

    def build_optional_file_name(
        self, _key_name: str | None, _key: FileFields | None
    ) -> ast.Assign | None:
        "{('self.'+file_name+' = file_name') if file_name else ''}"
        key_name = _key_name or self.key_name
        key = _key or self.key
        file_name_key = get_file_variable(key, key_name)
        if not file_name_key:
            return None
        return ast.Assign(
            [ast.Attribute(ast.Name("self"), file_name_key)], ast.Name("file_name")
        )

    def rename_optional_file_name(self, new_key_name: str, new_key: FileFields) -> None:
        "{('self.'+file_name+' = file_name') if file_name else ''}"
        if not self._fn:
            raise TemplateException("")
        ass = next(
            (
                _ass
                for _ass in self._fn.body
                if isinstance(_ass, ast.Assign)
                and isinstance(_ass.targets[0], ast.Attribute)
                and isinstance(_ass.targets[0].value, ast.Name)
                and _ass.targets[0].value.id == "self"
                and _ass.targets[0].attr
                in [
                    get_file_variable(new_key, new_key_name),
                    get_file_variable(self.key, new_key_name),
                    get_file_variable(new_key, self.key_name),
                    get_file_variable(self.key, self.key_name),
                ]
            ),
            None,
        )
        file_name_key = get_file_variable(new_key, new_key_name)
        if ass:
            if not file_name_key:
                self._fn.body.remove(ass)
            else:
                ass.targets[0] = ast.Attribute(ast.Name("self"), file_name_key)
        else:
            should = self.build_optional_file_name(new_key_name, new_key)
            if should:
                self._fn.body.append(should)

    def build(self) -> None:
        exists = self.find_fn()
        if exists:
            return

        fun = self.build_function_base()
        self._fn = fun

        self.change(self.key_name, self.key)

    def change(self, new_key_name: str, new_key: FileFields) -> None:
        if not self._fn:
            self._fn = self.build_function_base(new_key_name)
        self.rename_decorator(new_key_name)
        self.rename_function_base(new_key_name)
        self.rename_static_mime_definition()
        self.rename_static_file_name_definition()
        self.rename_data_assign()
        self.rename_key_name_assign(new_key_name)
        self.rename_optional_mime(new_key_name, new_key)
        self.rename_optional_file_name(new_key_name, new_key)

        self.add_if_not_present(new_key_name)

    def purge(self) -> None:
        if self._fn:
            self._class.body.remove(self._fn)
