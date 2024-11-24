import ast
import unittest

from naming import (
    get_column_file_name_key,
    get_column_mime_key,
    get_file_variable,
    get_mime_variable_name,
    get_static_file_name_key,
    get_static_mime_key,
    werkzeug_get_name,
)
from template.werkzeug.werkzeug import Werkzeug
from types_source import FileFields
from utils.ast_tools import get_assign, get_property_getter, get_property_setter


class WerkzeugTest(unittest.TestCase):
    def does_this_implement_getter(
        self,
        key_name: str,
        key: FileFields,
        getter: ast.FunctionDef | ast.AsyncFunctionDef,
    ):
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

        def validate_function():
            """def {werkzeug_get_name(key_name)}(#self#)->#flask.Response#:"""
            self.assertEqual(
                getter.name, werkzeug_get_name(key_name), "Function name is wrong"
            )
            self.assertEqual(len(getter.decorator_list), 1, "Decorator list is wrong")

        def validate_mime():
            """mime_type = {mime_key}"""

            mime_type = get_assign("mime_type", getter, True)

            self.assertIsNotNone(mime_type, "mime_type entry is not added")
            if mime_type:
                if key.get("mime_unhandled"):
                    self.assertIsInstance(mime_type.value, ast.Constant)
                    self.assertEqual(mime_type.value.value, None)  # type: ignore
                    return
                elif key.get("mime_type_field_name"):
                    self.assertIsInstance(mime_type.value, ast.Attribute)
                    self.assertEqual(
                        mime_type.value.attr,  # type: ignore
                        get_column_mime_key(key_name),
                    )
                    self.assertEqual(mime_type.value.value.id, "self")  # type: ignore
                    return
                elif key.get("mime_type_fix"):
                    self.assertIsInstance(mime_type.value, ast.Attribute)
                    self.assertEqual(
                        mime_type.value.attr,  # type: ignore
                        get_static_mime_key(key_name),
                    )
                    self.assertEqual(mime_type.value.value.id, "self")  # type: ignore
                    return
            raise Exception("Unexpected result")

        def validate_file_name():
            """file_name = {file_name}"""

            file_name = get_assign("file_name", getter, True)

            self.assertIsNotNone(file_name, "file_name entry is not added")
            if file_name is not None:
                if key.get("name_unhandled"):
                    self.assertIsInstance(file_name.value, ast.Constant)
                    self.assertEqual(file_name.value.value, None)  # type: ignore
                    return
                elif key.get("file_name_field_name"):
                    self.assertIsInstance(file_name.value, ast.Attribute)
                    self.assertEqual(
                        file_name.value.attr,  # type: ignore
                        get_column_file_name_key(key_name),
                    )
                    self.assertEqual(file_name.value.value.id, "self")  # type: ignore
                    return
                elif key.get("file_name_fix"):
                    self.assertIsInstance(file_name.value, ast.Attribute)
                    self.assertEqual(
                        file_name.value.attr,  # type: ignore
                        get_static_file_name_key(key_name),
                    )
                    self.assertEqual(file_name.value.value.id, "self")  # type: ignore
                    return
            raise Exception("Unexpected result")

        def validate_data():
            """data = self.{key_name}"""

            data = get_assign("data", getter, True)

            self.assertIsNotNone(data, "data entry is not added")
            if data is not None:
                self.assertIsInstance(data.value, ast.Attribute)
                self.assertEqual(
                    data.value.attr,  # type: ignore
                    key_name,
                )
                self.assertEqual(data.value.value.id, "self")  # type: ignore

        def validate_return():
            """#return flask.send_file(data,attachment_filename=file_name,mimetype=mime_key)#"""

            _return = next((_r for _r in getter.body if isinstance(_r, ast.Return)))

            self.assertIsNotNone(_return, "Return is not set")

            if _return:
                self.assertIsInstance(_return.value, ast.Call, "Return is not a call")
                if isinstance(_return.value, ast.Call):
                    self.assertIsInstance(
                        _return.value.func, ast.Attribute, "Func is not an attribute"
                    )
                    if isinstance(_return.value.func, ast.Attribute):
                        self.assertIsInstance(
                            _return.value.func.value,
                            ast.Name,
                            f"Func name format is not proper {ast.unparse(_return.value.func)}",
                        )
                        self.assertEqual(_return.value.func.attr, "send_file")
                        if isinstance(_return.value.func.value, ast.Name):
                            self.assertEqual(_return.value.func.value.id, "flask")
                            return
            raise Exception("Should happen")

        validate_function()
        validate_mime()
        validate_file_name()
        validate_data()
        validate_return()

    def does_this_implement_setter(
        self,
        key_name: str,
        key: FileFields,
        setter: ast.FunctionDef | ast.AsyncFunctionDef,
    ):
        """
        @{werkzeug_get_name(key_name)}.setter
        ...
        def {werkzeug_get_name(key_name)}(self,file:werkzeug.FileStorage)->None:
            ...
            mime_type = file.mimetype
            ...
            file_name = file.filename
            ...
            data = file.read()
            ...
            self.{key} = data
            ...
            {('self.'+mime_key+' = mime_type') if mime_key else ''}
            ...
            {('self.'+file_name+' = file_name') if file_name else ''}

        """

        def validate_decorator():
            """@{werkzeug_get_name(key_name)}.setter"""
            decorator = next(
                (
                    dec
                    for dec in setter.decorator_list
                    if isinstance(dec, ast.Attribute)
                    and isinstance(dec.value, ast.Name)
                    and dec.attr == "setter"
                    and dec.value.id == werkzeug_get_name(key_name)
                ),
                None,
            )
            self.assertIsNotNone(decorator, "The proper decorator has not been set")
            if decorator:
                self.assertEqual(
                    setter.decorator_list.index(decorator),
                    len(setter.decorator_list) - 1,
                    "The property decorator is not the last decorator",
                )
                return
            raise Exception("")

        def validate_function_values():
            """def {werkzeug_get_name(key_name)}(self,file:werkzeug.FileStorage)->None:"""

            self.assertEqual(
                setter.name,
                werkzeug_get_name(key_name),
                "Setter function name is improper",
            )
            self.assertEqual(
                len(setter.args.args), 2, "Setter arguments are of incorrect size"
            )
            first_arg = setter.args.args[0]
            self.assertEqual(first_arg.arg, "self", "Wrong first argument name")
            second_arg = setter.args.args[1]
            self.assertEqual(second_arg.arg, "file", "Wrong second argument name")
            self.assertIsInstance(
                second_arg.annotation,
                ast.Attribute,
                "Annotation is not properly defined",
            )
            if isinstance(second_arg.annotation, ast.Attribute):
                self.assertIsInstance(
                    second_arg.annotation.value,
                    ast.Name,
                    "Second argument annotation structure issue",
                )
                self.assertEqual(
                    second_arg.annotation.attr,
                    "FileStorage",
                    "Second argument annotation structure issue",
                )
                if isinstance(second_arg.annotation.value, ast.Name):
                    self.assertEqual(
                        second_arg.annotation.value.id,
                        "werkzeug",
                        "Second argument annotation structure issue",
                    )

                    return
            raise Exception("")

        def validate_mime_type_assign():
            """mime_type = file.content_type"""
            assign = get_assign("mime_type", setter, True)
            self.assertIsNotNone(assign, "Mime assign was not found")

            if assign:
                self.assertIsInstance(assign.targets[0], ast.Name)
                if isinstance(assign.targets[0], ast.Name):
                    self.assertEqual(assign.targets[0].id, "mime_type")
                self.assertEqual(len(assign.targets), 1)
                self.assertIsInstance(assign.value, ast.Attribute)
                if isinstance(assign.value, ast.Attribute):
                    self.assertIsInstance(assign.value.value, ast.Name)
                    if isinstance(assign.value.value, ast.Name):
                        self.assertEqual(assign.value.value.id, "file")
                        self.assertEqual(assign.value.attr, "mimetype")
                        return
            raise Exception("")

        def validate_file_name_assign():
            """file_name = file.filename"""
            assign = get_assign("file_name", setter, True)
            self.assertIsNotNone(assign, "File name assign was not found")

            if assign:
                self.assertIsInstance(assign.targets[0], ast.Name)
                if isinstance(assign.targets[0], ast.Name):
                    self.assertEqual(assign.targets[0].id, "file_name")
                self.assertEqual(len(assign.targets), 1)
                self.assertIsInstance(assign.value, ast.Attribute)
                if isinstance(assign.value, ast.Attribute):
                    self.assertIsInstance(assign.value.value, ast.Name)
                    if isinstance(assign.value.value, ast.Name):
                        self.assertEqual(assign.value.value.id, "file")
                        self.assertEqual(assign.value.attr, "filename")
                        return
            raise Exception("")

        def validate_data_assign():
            """data = await file.read()"""

            assign = get_assign("data", setter, True)

            self.assertIsNotNone(assign, "data = await file.read() is not set")
            if assign:
                self.assertIsInstance(assign.value, ast.Call)
                if isinstance(assign.value, ast.Call):
                    self.assertIsInstance(assign.value.func, ast.Attribute)
                    if isinstance(assign.value.func, ast.Attribute):
                        self.assertEqual(assign.value.func.attr, "read")
                        self.assertIsInstance(assign.value.func.value, ast.Name)
                        if isinstance(assign.value.func.value, ast.Name):
                            self.assertEqual(assign.value.func.value.id, "file")
                            return
            raise Exception("")

        def validate_key_assign():
            """self.{key} = data"""
            assign = next(
                (
                    _ass
                    for _ass in setter.body
                    if isinstance(_ass, ast.Assign)
                    and isinstance(_ass.targets[0], ast.Attribute)
                    and isinstance(_ass.targets[0].value, ast.Name)
                    and _ass.targets[0].value.id == "self"
                    and _ass.targets[0].attr == key_name
                ),
                None,
            )
            self.assertIsNotNone(assign, "Data assign was not found")

            if assign:
                self.assertIsInstance(assign.value, ast.Name)
                if isinstance(assign.value, ast.Name):
                    self.assertEqual(assign.value.id, "data")
                    return
            raise Exception("")

        def validate_optional_mime_type():
            """{('self.'+mime_key+' = mime_type') if mime_key else ''}"""
            mime_key = get_mime_variable_name(key, key_name)
            if not mime_key:
                return
            assign = next(
                (
                    _ass
                    for _ass in setter.body
                    if _ass
                    for _ass in setter.body
                    if isinstance(_ass, ast.Assign)
                    and isinstance(_ass.targets[0], ast.Attribute)
                    and isinstance(_ass.targets[0].value, ast.Name)
                    and _ass.targets[0].value.id == "self"
                    and _ass.targets[0].attr == mime_key
                ),
                None,
            )
            self.assertIsNotNone(assign, "Mime type setter is not proper")
            if assign:
                self.assertIsInstance(assign.value, ast.Name)
                if isinstance(assign.value, ast.Name):
                    self.assertEqual(assign.value.id, "mime_type")
                    return
            raise Exception("")

        def validate_optional_file_name():
            """{('self.'+file_name+' = file_name') if file_name else ''}"""
            file_name_key = get_file_variable(key, key_name)
            if not file_name_key:
                return
            assign = next(
                (
                    _ass
                    for _ass in setter.body
                    if _ass
                    for _ass in setter.body
                    if isinstance(_ass, ast.Assign)
                    and isinstance(_ass.targets[0], ast.Attribute)
                    and isinstance(_ass.targets[0].value, ast.Name)
                    and _ass.targets[0].value.id == "self"
                    and _ass.targets[0].attr == file_name_key
                ),
                None,
            )
            self.assertIsNotNone(assign, "Mime type setter is not proper")
            if assign:
                self.assertIsInstance(assign.value, ast.Name)
                if isinstance(assign.value, ast.Name):
                    self.assertEqual(assign.value.id, "file_name")
                    return
            raise Exception("")

        validate_decorator()
        validate_function_values()
        validate_mime_type_assign()
        validate_file_name_assign()
        validate_data_assign()
        validate_key_assign()
        validate_optional_mime_type()
        validate_optional_file_name()

    def test_build_no_file(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {"mime_type_fix": "some_mime_type", "name_unhandled": True}

        Werkzeug(key_name, key, _class).build()

        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore

        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(key_name, key, getter)
        self.does_this_implement_setter(key_name, key, setter)
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 5)
        self.assertEqual(len(_class.body), 2)

    def test_build_no_mime(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {
            "file_name_fix": "some_mime_type",
            "mime_unhandled": True,
        }

        Werkzeug(key_name, key, _class).build()

        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore

        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(key_name, key, getter)
        self.does_this_implement_setter(key_name, key, setter)
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 5)
        self.assertEqual(len(_class.body), 2)

    def test_build_full(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {
            "file_name_fix": "some_mime_type",
            "mime_type_fix": "some_mime_type",
        }

        Werkzeug(key_name, key, _class).build()

        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore

        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(key_name, key, getter)
        self.does_this_implement_setter(key_name, key, setter)
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 6)
        self.assertEqual(len(_class.body), 2)

    def test_build_full_change_no_diff(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {
            "file_name_fix": "some_mime_type",
            "mime_type_fix": "some_mime_type",
        }

        Werkzeug(key_name, key, _class).build()
        Werkzeug(key_name, key, _class).change(
            key_name,
            key,
        )

        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore

        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(key_name, key, getter)
        self.does_this_implement_setter(key_name, key, setter)
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 6)
        self.assertEqual(len(_class.body), 2)

    def test_build_full_multiple_times(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {
            "file_name_fix": "some_mime_type",
            "mime_type_fix": "some_mime_type",
        }

        Werkzeug(key_name, key, _class).build()
        Werkzeug(key_name, key, _class).build()
        Werkzeug(key_name, key, _class).build()

        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore

        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(key_name, key, getter)
        self.does_this_implement_setter(key_name, key, setter)
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 6)
        self.assertEqual(len(_class.body), 2)

    def test_build_none(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {"mime_unhandled": True, "name_unhandled": True}

        Werkzeug(key_name, key, _class).build()

        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore

        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(key_name, key, getter)
        self.does_this_implement_setter(key_name, key, setter)
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 4)
        self.assertEqual(len(_class.body), 2)

    def test_change_none_to_full(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {"mime_unhandled": True, "name_unhandled": True}

        Werkzeug(key_name, key, _class).build()

        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore

        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        # print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(key_name, key, getter)
        self.does_this_implement_setter(key_name, key, setter)
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 4)
        self.assertEqual(len(_class.body), 2)

        Werkzeug(key_name, key, _class).change(
            key_name,
            {
                "file_name_fix": "some_mime_type",
                "mime_type_fix": "some_mime_type",
            },
        )
        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore
        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(
            key_name,
            {
                "file_name_fix": "some_mime_type",
                "mime_type_fix": "some_mime_type",
            },
            getter,
        )
        self.does_this_implement_setter(
            key_name,
            {
                "file_name_fix": "some_mime_type",
                "mime_type_fix": "some_mime_type",
            },
            setter,
        )
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 6)
        self.assertEqual(len(_class.body), 2)

    def test_change_full_to_none(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {
            "file_name_fix": "some_mime_type",
            "mime_type_fix": "some_mime_type",
        }

        Werkzeug(key_name, key, _class).build()
        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore
        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        # print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(key_name, key, getter)
        self.does_this_implement_setter(key_name, key, setter)
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 6)
        self.assertEqual(len(_class.body), 2)

        Werkzeug(key_name, key, _class).change(
            key_name,
            {"mime_unhandled": True, "name_unhandled": True},
        )
        _class: ast.ClassDef = ast.parse(
            ast.unparse(ast.fix_missing_locations(_class))
        ).body[0]  # type: ignore
        getter = get_property_getter(werkzeug_get_name(key_name), _class)
        setter = get_property_setter(werkzeug_get_name(key_name), _class)

        print(ast.unparse(ast.fix_missing_locations(_class)))
        self.assertIsNotNone(getter)
        self.assertIsNotNone(setter)

        if not getter or not setter:
            raise Exception("")
        self.does_this_implement_getter(
            key_name,
            {"mime_unhandled": True, "name_unhandled": True},
            getter,
        )
        self.does_this_implement_setter(
            key_name,
            {"mime_unhandled": True, "name_unhandled": True},
            setter,
        )
        self.assertEqual(len(getter.body), 4)
        self.assertEqual(len(setter.body), 4)
        self.assertEqual(len(_class.body), 2)
