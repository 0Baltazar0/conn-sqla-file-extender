import ast
from dataclasses import dataclass

from naming import get_column_mime_key
from template.exceptions import TemplateException
from types_source import FileFields
from utils.ast_tools import get_ann_or_assign, get_property_getter, get_property_setter


@dataclass
class MimeGetter:
    """Manages the getter for the mime type, if the mime type is dynamic

        Raises:
            TemplateException: Any unexpected runtime error

    The expected code format is:
    ...
    @property
    ...
    def {key_name}_mime_type(self)->#str|None#:
        ...
        mime_type = self.{key["mime_type_field_name"]}
        ...
        return mime_type
    """

    key_name: str
    key: FileFields
    _class: ast.ClassDef
    _fn: ast.FunctionDef | ast.AsyncFunctionDef | None

    def __post_init__(self) -> None:
        self._fn = get_property_getter(get_column_mime_key(self.key_name), self._class)

    def build_function_base(self, _key_name: str | None = None) -> ast.FunctionDef:
        key_name = _key_name or self.key_name

        return ast.FunctionDef(
            name=get_column_mime_key(key_name),
            args=ast.arguments([], [ast.arg("self")], None, [], [], None, []),
            returns=ast.BinOp(
                left=ast.Name("str"), right=ast.Name("None"), op=ast.BitOr()
            ),
            body=[],
            decorator_list=[],
        )

    def rename_function_base(self, key_name: str) -> None:
        if not self._fn:
            self._fn = self.build_function_base(key_name)
        else:
            self._fn.name = get_column_mime_key(key_name)

    def build_assign(self, _key: FileFields | None = None) -> ast.AnnAssign:
        key = _key or self.key
        return ast.AnnAssign(
            target=ast.Name("mime_type"),
            annotation=ast.Name("str"),
            value=ast.Attribute(
                value=ast.Name("self"), attr=key.get("mime_type_field_name", "")
            ),
            simple=1,
        )

    def rename_assign(self, key: FileFields) -> None:
        mime_field = key.get("mime_type_field_name")
        if not self._fn or not mime_field:
            raise TemplateException("")

        ann = get_ann_or_assign("mime_type", self._class, True)

        if not ann:
            self._fn.body.insert(0, self.build_assign(key))
        else:
            ann.value = ast.Attribute(value=ast.Name("self"), attr=mime_field)

    def build_decorator(self) -> ast.Name:
        return ast.Name("property")

    def rename_decorator(self) -> None:
        if not self._fn:
            raise TemplateException("")

        has_prop_dec = next(
            (
                dec
                for dec in self._fn.decorator_list
                if isinstance(dec, ast.Name) and dec.id == "property"
            ),
            None,
        )
        if not has_prop_dec:
            self._fn.decorator_list.append(self.build_decorator())

    def build_return(self) -> ast.Return:
        return ast.Return(value=ast.Name("mime_type"))

    def rename_return(self) -> None:
        if not self._fn:
            raise TemplateException("")
        else:
            has_ret = next(
                (k for k in self._fn.body if isinstance(k, ast.Return)), None
            )
            if has_ret:
                return
            else:
                self._fn.body.append(self.build_return())

    def build(self):
        self._fn = self._fn or self.build_function_base()
        self.rename_assign(self.key)
        self.rename_return()
        self.rename_decorator()

        if self._fn not in self._class.body:
            target = get_property_setter(
                get_column_mime_key(self.key_name), self._class
            )
            index = self._class.body.index(target) if target else 0

            self._class.body.insert(index, self._fn)

    def change(self, key_name: str, key: FileFields) -> None:
        if not self._fn:
            has_current_name = get_property_getter(
                get_column_mime_key(key_name), self._class
            )
            if not has_current_name:
                self._fn = self.build_function_base(key_name)
            else:
                self._fn = has_current_name

        self.rename_function_base(key_name)
        self.rename_assign(key)
        self.rename_return()
        self.rename_decorator()

    def purge(self) -> None:
        if self._fn:
            self._class.body.remove(self._fn)


@dataclass
class MimeSetter:
    """Manages the getter for the mime type, if the mime type is dynamic

        Raises:
            TemplateException: Any unexpected runtime error

    The expected code format is:
    ...
    @{key_name}_mime_type.setter
    ...
    def {key_name}_mime_type(self,value:str)->None:
        ...
        self.{key["mime_type_field_name"]} = value
        ...
    """

    key_name: str
    key: FileFields
    _class: ast.ClassDef
    _fn: ast.FunctionDef | ast.AsyncFunctionDef | None

    def __post_init__(self) -> None:
        self._fn = get_property_setter(get_column_mime_key(self.key_name), self._class)

    def build_function_base(self, _key_name: str | None = None) -> ast.FunctionDef:
        key_name = _key_name or self.key_name
        return ast.FunctionDef(
            get_column_mime_key(key_name),
            args=ast.arguments(
                [],
                [ast.arg("self"), ast.arg("value", ast.Name("str"))],
                None,
                [],
                [],
                None,
                [],
            ),
            body=[],
            decorator_list=[],
            returns=ast.Name("None"),
        )

    def rename_function_base(self, key_name: str) -> None:
        if not self._fn:
            raise TemplateException("")

        self._fn.name = get_column_mime_key(key_name)

    def build_decorator(self, _key_name: str | None = None) -> ast.Attribute:
        key_name = _key_name or self.key_name
        return ast.Attribute(ast.Name(key_name), attr="setter")

    def rename_decorator(self, key_name: str) -> None:
        if not self._fn:
            raise TemplateException("")

        setter = next(
            (
                dec
                for dec in self._fn.decorator_list
                if isinstance(dec, ast.Attribute) and dec.attr == "setter"
            ),
            None,
        )

        if not setter:
            self._fn.decorator_list.append(self.build_decorator(key_name))

        else:
            setter.value = ast.Name(key_name)

    def build_assign(self, _key: FileFields) -> ast.Assign:
        key = _key or self.key
        mime_field = key.get("mime_type_field_name")
        if not mime_field:
            raise TemplateException("")

        return ast.Assign(
            [ast.Attribute(ast.Name("self"), mime_field)], ast.Name("value")
        )

    @staticmethod
    def _is_annassign(ass: ast.AnnAssign, key: FileFields) -> bool:
        mime_field = key.get("mime_type_field_name")
        if not mime_field:
            raise TemplateException("")
        if not isinstance(ass.target, ast.Attribute):
            return False
        if not ass.target.attr == mime_field:
            return False
        if not isinstance(ass.target.value, ast.Name) or ass.target.value.id != "self":
            return False

        return True

    @staticmethod
    def _is_assign(ass: ast.Assign, key: FileFields) -> bool:
        mime_field = key.get("mime_type_field_name")
        if not mime_field:
            raise TemplateException("")
        if len(ass.targets) != 1 or not isinstance(ass.targets[0], ast.Attribute):
            return False
        if not ass.targets[0].attr == mime_field:
            return False
        if (
            not isinstance(ass.targets[0].value, ast.Name)
            or ass.targets[0].value.id != "self"
        ):
            return False

        return True

    def rename_assign(self, key: FileFields) -> None:
        mime_field = key.get("mime_type_field_name")
        if not self._fn or not mime_field:
            raise TemplateException("")
        ass = next(
            (
                _as
                for _as in self._fn.body
                if (
                    isinstance(_as, ast.AnnAssign)
                    and MimeSetter._is_annassign(_as, key)
                )
                or (isinstance(_as, ast.Assign) and MimeSetter._is_assign(_as, key))
            )
        )
        if not ass:
            self._fn.body.insert(0, self.build_assign(key))
        else:
            if isinstance(ass, ast.AnnAssign):
                if not isinstance(ass.target, ast.Attribute):
                    raise TemplateException("")
                ass.target.attr = mime_field
            else:
                if len(ass.targets) != 1 or not isinstance(
                    ass.targets[0], ast.Attribute
                ):
                    raise TemplateException("")
                ass.targets[0].attr = mime_field

    def build(self) -> None:
        self._fn = self._fn or self.build_function_base()
        self.rename_assign(self.key)
        self.rename_decorator(self.key_name)

        if self._fn not in self._class.body:
            target = get_property_getter(
                get_column_mime_key(self.key_name), self._class
            )
            index = self._class.body.index(target) + 1 if target else 0
            self._class.body.insert(index, self._fn)

    def change(self, key_name: str, key: FileFields) -> None:
        if not self._fn:
            has_current_name = get_property_setter(
                get_column_mime_key(key_name), self._class
            )
            if not has_current_name:
                self._fn = self.build_function_base(key_name)
            else:
                self._fn = has_current_name
        self.rename_assign(key)
        self.rename_decorator(key_name)

    def purge(self) -> None:
        if self._fn:
            self._class.body.remove(self._fn)


@dataclass
class DynamicMimeType:
    key_name: str
    key: FileFields
    _class: ast.ClassDef

    def __post_init__(self) -> None:
        self.setter = MimeSetter(self.key_name, self.key, self._class, None)
        self.getter = MimeGetter(self.key_name, self.key, self._class, None)

    def build(self) -> None:
        self.getter.build()
        self.setter.build()

    def change(self, new_key_name: str, new_key: FileFields) -> None:
        self.getter.change(new_key_name, new_key)
        self.setter.change(new_key_name, new_key)

    def purge(self) -> None:
        self.getter.purge()
        self.setter.purge()
