import ast
import unittest

from naming import get_static_mime_key
from template.mime.static import StaticMimeType
from types_source import FileFields
from utils.ast_tools import get_attribute


class StaticFileNameTest(unittest.TestCase):
    def test_simple_build_command(self) -> None:
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {"mime_type_fix": "some_mime_type"}
        StaticMimeType(key_name, key, _class).build()

        attribute = get_attribute(get_static_mime_key(key_name), _class)

        self.assertIsNotNone(attribute, "New attribute has not been added")
        if not attribute:
            raise Exception("")
        self.assertIsInstance(attribute.value, ast.Name, "Assign value must be a Name")
        if not isinstance(attribute.value, ast.Name):
            raise Exception("")
        self.assertEqual(
            attribute.value.id, "some_mime_type", "Name id is not what expected"
        )

        self.assertEqual(
            len(_class.body), 1, "Class body has increased to more than expected"
        )

    def test_simple_rename_command_on_empty(self) -> None:
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {"mime_type_fix": "some_mime_type"}
        StaticMimeType("key_name", {}, _class).change(key_name, key)

        attribute = get_attribute(get_static_mime_key(key_name), _class)

        self.assertIsNotNone(attribute, "New attribute has not been added")
        if not attribute:
            raise Exception("")
        self.assertIsInstance(attribute.value, ast.Name, "Assign value must be a Name")
        if not isinstance(attribute.value, ast.Name):
            raise Exception("")
        self.assertEqual(
            attribute.value.id, "some_mime_type", "Name id is not what expected"
        )

        self.assertEqual(
            len(_class.body), 1, "Class body has increased to more than expected"
        )

    def test_simple_rename_command(self) -> None:
        old_key_name = "test_key"
        old_key: FileFields = {"mime_type_fix": "some_mime_type"}
        _class = ast.ClassDef(
            "TestClass",
            [],
            [],
            [
                ast.AnnAssign(
                    ast.Name(get_static_mime_key(old_key_name)),
                    ast.Name("str"),
                    ast.Name("some_mime_type"),
                    1,
                )
            ],
            [],
        )
        new_key_name = "renamed_key"
        StaticMimeType(old_key_name, old_key, _class).change(new_key_name, old_key)
        attribute = get_attribute(get_static_mime_key(new_key_name), _class)
        old_attribute = get_attribute(get_static_mime_key(old_key_name), _class)

        self.assertIsNone(old_attribute, "Old attribute has not been deleted")

        self.assertIsNotNone(attribute, "New attribute has not been added")
        if not attribute:
            raise Exception("")
        self.assertIsInstance(attribute.value, ast.Name, "Assign value must be a Name")
        if not isinstance(attribute.value, ast.Name):
            raise Exception("")
        self.assertEqual(
            attribute.value.id, "some_mime_type", "Name id is not what expected"
        )

        self.assertEqual(
            len(_class.body), 1, "Class body has increased to more than expected"
        )

    def test_simple_purge_command(self) -> None:
        key_name = "test_key"
        key: FileFields = {"mime_unhandled": True}
        _class = ast.ClassDef(
            "TestClass",
            [],
            [],
            [
                ast.AnnAssign(
                    ast.Name(get_static_mime_key(key_name)),
                    ast.Name("str"),
                    ast.Name("some_mime_type"),
                    1,
                )
            ],
            [],
        )
        StaticMimeType(key_name, key, _class).purge()

        attribute = get_attribute(get_static_mime_key(key_name), _class)
        self.assertIsNone(attribute, "Attribute is not deleted on purge")

        self.assertEqual(len(_class.body), 0, "Body length is not empty")

    def test_full_history(self):
        _class = ast.ClassDef("TestClass", [], [], [], [])
        key_name = "test_key"
        key: FileFields = {"mime_type_fix": "some_mime_type"}

        def get_and_assert(key_name: str) -> ast.AnnAssign:
            attribute = get_attribute(get_static_mime_key(key_name), _class)
            if not attribute:
                self.assertIsNotNone(attribute, "Attribute does not exist")
                raise Exception("")
            return attribute

        StaticMimeType(key_name, key, _class).build()

        atr = get_and_assert(key_name)
        self.assertIsInstance(atr.value, ast.Name)
        self.assertEqual(atr.value.id, "some_mime_type")  # type: ignore
        self.assertEqual(len(_class.body), 1)

        StaticMimeType(key_name, key, _class).change(
            key_name, {"mime_type_fix": "some_other_type"}
        )

        atr = get_and_assert(key_name)
        self.assertIsInstance(atr.value, ast.Name)
        self.assertEqual(atr.value.id, "some_other_type")  # type: ignore
        self.assertEqual(len(_class.body), 1)

        StaticMimeType(key_name, key, _class).change(
            "other_key_name", {"mime_type_fix": "some_other_type"}
        )

        atr = get_and_assert("other_key_name")
        self.assertIsInstance(atr.value, ast.Name)
        self.assertEqual(atr.value.id, "some_other_type")  # type: ignore
        self.assertEqual(len(_class.body), 1)

        StaticMimeType("other_key_name", key, _class).purge()

        self.assertEqual(len(_class.body), 0)
