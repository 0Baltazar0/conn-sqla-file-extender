import ast
import unittest

from naming import get_column_mime_key
from template.mime.dynamic import DynamicMimeType
from types_source import FileFields
from utils.ast_tools import get_property_getter, get_property_setter


class DynamicMimeTest(unittest.TestCase):
    def does_this_implement_setter(
        self, key_name: str, mime_type_field_name: str, setter: ast.FunctionDef
    ) -> None:
        self.assertEqual(setter.name, get_column_mime_key(key_name))
        arguments = setter.args

        self.assertEqual(
            len(arguments.args),
            2,
            f"Getter arguments are not 2 !={len(arguments.args)}",
        )
        first_arg: ast.arg = arguments.args[0]  # type: ignore

        self.assertIsInstance(
            first_arg, ast.arg, f"First argument is not proper type {type(first_arg)}"
        )
        self.assertEqual(
            first_arg.arg, "self", f"First argument is not self but is {first_arg.arg}"
        )
        second_arg: ast.arg = arguments.args[1]
        self.assertIsInstance(
            second_arg, ast.arg, f"First argument is not proper type {type(second_arg)}"
        )
        self.assertEqual(
            second_arg.arg,
            "value",
            f"First argument is not value but is {second_arg.arg}",
        )

        second_annotation: ast.Name = second_arg.annotation  # type: ignore
        self.assertIsInstance(
            second_annotation,
            ast.Name,
            f"Second argument annotation is not proper type {type(second_annotation)}",
        )

        self.assertEqual(
            second_annotation.id,
            "str",
            f"Second argument annotation is not str but is {second_arg.arg}",
        )

        attribute_setter = next(
            (
                atr
                for atr in setter.body
                if isinstance(atr, ast.Assign)
                and isinstance(atr.targets[0], ast.Attribute)
                and atr.targets[0].attr == mime_type_field_name
                and isinstance(atr.targets[0].value, ast.Name)
                and atr.targets[0].value.id == "self"
                and isinstance(atr.value, ast.Name)
                and atr.value.id == "value"
            ),
            None,
        )
        self.assertIsNotNone(attribute_setter, "No attribute setter present in setter")

    def does_this_implement_getter(
        self, key_name: str, mime_type_field_name: str, getter: ast.FunctionDef
    ):
        self.assertEqual(getter.name, get_column_mime_key(key_name))
        arguments = getter.args
        self.assertEqual(
            len(arguments.args),
            1,
            f"Getter arguments are not 1 !={len(arguments.args)}",
        )
        first_arg: ast.arg = arguments.args[0]  # type: ignore

        self.assertIsInstance(
            first_arg, ast.arg, f"First argument is not proper type {type(first_arg)}"
        )
        self.assertEqual(
            first_arg.arg, "self", f"First argument is not self but is {first_arg.arg}"
        )
        attribute_getter = next(
            (
                atr
                for atr in getter.body
                if isinstance(atr, ast.Assign)
                and isinstance(atr.value, ast.Attribute)
                and atr.value.attr == mime_type_field_name
                and isinstance(atr.value.value, ast.Name)
                and atr.value.value.id == "self"
                and isinstance(atr.targets[0], ast.Name)
                and atr.targets[0].id == "mime_type"
            ),
            None,
        )
        self.assertIsNotNone(attribute_getter, "Proper assign is not present")

        _return = next(
            (
                ret
                for ret in getter.body
                if isinstance(ret, ast.Return)
                and isinstance(ret.value, ast.Name)
                and ret.value.id == "mime_type"
            ),
            None,
        )
        self.assertIsNotNone(_return, "Proper return is not present")

    def does_this_implement_field_name(
        self, key_name: str, mime_type_field_name: str, _class: ast.ClassDef
    ) -> None:
        getter: ast.FunctionDef = get_property_getter(
            get_column_mime_key(key_name), _class
        )  # type: ignore
        self.assertIsNotNone(
            getter,
            f"Getter does not exists! {key_name=},{get_column_mime_key(key_name)} {mime_type_field_name=}",
        )

        setter: ast.FunctionDef = get_property_setter(
            get_column_mime_key(key_name), _class
        )  # type: ignore
        self.assertIsNotNone(
            setter,
            f"Setter does not exists! {key_name=},{get_column_mime_key(key_name)} {mime_type_field_name=}",
        )

        self.does_this_implement_getter(key_name, mime_type_field_name, getter)
        self.does_this_implement_setter(key_name, mime_type_field_name, setter)

    def test_simple_build_command(self) -> None:
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {"mime_type_field_name": "other_sub_key"}
        DynamicMimeType(key_name, key, _class).build()
        self.does_this_implement_field_name(key_name, "other_sub_key", _class)

    def test_simple_rename_command_on_empty(self) -> None:
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {"mime_type_field_name": "other_sub_key"}
        DynamicMimeType("key_name", {}, _class).change(key_name, key)
        self.does_this_implement_field_name(key_name, "other_sub_key", _class)

    def test_simple_rename_command(self) -> None:
        old_key_name = "test_key"
        old_key: FileFields = {"mime_type_field_name": "other_sub_key"}
        _class = ast.ClassDef(
            "TestClass",
            [],
            [],
            [
                ast.FunctionDef(
                    get_column_mime_key(old_key_name),
                    ast.arguments([], [ast.arg("self")], None, [], [], None, []),
                    [],
                    [ast.Name("property")],
                ),
                ast.FunctionDef(
                    get_column_mime_key(old_key_name),
                    ast.arguments(
                        [],
                        [ast.arg("self"), ast.arg("value", annotation=ast.Name("str"))],
                        None,
                        [],
                        [],
                        None,
                        [ast.Attribute(ast.Name(old_key_name), attr="setter")],
                    ),
                    [],
                    [
                        ast.Attribute(
                            ast.Name(get_column_mime_key(old_key_name)), "setter"
                        )
                    ],
                ),
            ],
            [],
        )
        new_key_name = "renamed_key"
        DynamicMimeType(old_key_name, old_key, _class).change(new_key_name, old_key)
        self.does_this_implement_field_name("renamed_key", "other_sub_key", _class)

    def test_simple_purge_command(self) -> None:
        key_name = "test_key"
        key: FileFields = {"mime_type_field_name": "other_sub_key"}
        _class = ast.ClassDef(
            "TestClass",
            [],
            [],
            [
                ast.FunctionDef(
                    get_column_mime_key(key_name),
                    ast.arguments([], [], None, [], [], None, []),
                    [],
                    [ast.Name("property")],
                ),
                ast.FunctionDef(
                    get_column_mime_key(key_name),
                    ast.arguments([], [], None, [], [], None, []),
                    [],
                    [ast.Attribute(ast.Name(get_column_mime_key(key_name)), "setter")],
                ),
            ],
            [],
        )
        DynamicMimeType(key_name, key, _class).purge()
        self.assertEqual(len(_class.body), 0, "Body is not empty after purging")

    def test_full_history(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {"mime_type_field_name": "other_sub_key"}

        DynamicMimeType(key_name, key, _class).build()
        self.does_this_implement_field_name("test_key", "other_sub_key", _class)

        DynamicMimeType(key_name, key, _class).change(
            key_name, {"mime_type_field_name": "other_sub_key_two"}
        )

        self.does_this_implement_field_name("test_key", "other_sub_key_two", _class)
        DynamicMimeType(key_name, key, _class).change(
            "other_key_name", {"mime_type_field_name": "other_sub_key_two"}
        )

        self.does_this_implement_field_name(
            "other_key_name", "other_sub_key_two", _class
        )

        DynamicMimeType("other_key_name", key, _class).purge()

        self.assertEqual(len(_class.body), 0)
