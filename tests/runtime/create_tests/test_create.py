import os
import sys
from tempfile import NamedTemporaryFile
import unittest
from unittest import mock
import builtins
from executor import NewKeyAction
from runtime import NoActionRequired, Runtime

sys.path.append(os.path.join(os.getcwd(), "tests"))

from donor_files.file_maker import plan_file
from inputs.new_file_name_inputs import get_file_name_input
from inputs.new_key_inputs import new_key_start
from inputs.new_mime_inputs import get_mime_input


class TestNoHistory(unittest.TestCase):
    history_path = "./tests/history/empty.yaml"

    def test_no_action(self) -> None:
        file_path = "./tests/donor_files/no_file.py"
        self.assertRaises(
            NoActionRequired, lambda: Runtime(file_path, self.history_path, "TestClass")
        )

    def test_create_unhandled_action(self) -> None:
        file_path = "./tests/donor_files/one_file.py"
        user_inputs = ["n", "y"]
        with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
            with self.assertRaises(NewKeyAction) as NKA:
                Runtime(file_path, self.history_path, "TestClass")
            exception: NewKeyAction = NKA.exception

            self.assertEqual(exception.new_key_name, "file")
            self.assertEqual(exception.new_key, {"unhandled": True})

    def test_create_all_unhandled_action(self) -> None:
        file_path = "./tests/donor_files/one_file.py"
        user_inputs = ["n", "n", "unhandled", "unhandled"]
        with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
            with self.assertRaises(NewKeyAction) as NKA:
                Runtime(file_path, self.history_path, "TestClass")
            exception: NewKeyAction = NKA.exception

            self.assertEqual(exception.new_key_name, "file")
            self.assertEqual(
                exception.new_key, {"mime_unhandled": True, "name_unhandled": True}
            )

    def test_create_mime_static_with_default(self) -> None:
        file_path = "./tests/donor_files/one_file.py"
        user_inputs = ["n", "n", "static", "", "unhandled"]

        with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
            with self.assertRaises(NewKeyAction) as NKA:
                Runtime(file_path, self.history_path, "TestClass")
            exception: NewKeyAction = NKA.exception

            self.assertEqual(exception.new_key_name, "file")
            self.assertEqual(
                exception.new_key,
                {"mime_type_fix": "application/octet-stream", "name_unhandled": True},
            )

    def test_create_mime_static_with_supplied(self) -> None:
        file_path = "./tests/donor_files/one_file.py"
        user_inputs = ["n", "n", "static", "test-mime", "unhandled"]

        with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
            with self.assertRaises(NewKeyAction) as NKA:
                Runtime(file_path, self.history_path, "TestClass")
            exception: NewKeyAction = NKA.exception
            self.assertEqual(exception.new_key_name, "file")
            self.assertEqual(
                exception.new_key,
                {"mime_type_fix": "test-mime", "name_unhandled": True},
            )

    def test_create_mime_dynamic_with_existing(self) -> None:
        file_path = "./tests/donor_files/one_file.py"
        user_inputs = ["n", "n", "dynamic", "y", "0", "unhandled"]

        with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
            with self.assertRaises(NewKeyAction) as NKA:
                Runtime(file_path, self.history_path, "TestClass")
            exception: NewKeyAction = NKA.exception
            self.assertEqual(exception.new_key_name, "file")
            self.assertEqual(
                exception.new_key,
                {"mime_type_field_name": "name", "name_unhandled": True},
            )

    def test_create_mime_dynamic_with_new_default(self) -> None:
        file_path = "./tests/donor_files/one_file.py"
        user_inputs = ["n", "n", "dynamic", "n", "", "unhandled"]

        with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
            with self.assertRaises(NewKeyAction) as NKA:
                Runtime(file_path, self.history_path, "TestClass")
            exception: NewKeyAction = NKA.exception
            self.assertEqual(exception.new_key_name, "file")
            self.assertEqual(
                exception.new_key,
                {"mime_type_field_name": "file_mime_col", "name_unhandled": True},
            )

    def test_create_mime_dynamic_with_new_supplied(self) -> None:
        file_path = "./tests/donor_files/one_file.py"
        user_inputs = (
            new_key_start(False)
            + get_mime_input("dynamic", value="mime_type_holder")
            + get_file_name_input("unhandled")
        )
        with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
            with self.assertRaises(NewKeyAction) as NKA:
                Runtime(file_path, self.history_path, "TestClass")
            exception: NewKeyAction = NKA.exception
            self.assertEqual(exception.new_key_name, "file")
            self.assertEqual(
                exception.new_key,
                {"mime_type_field_name": "mime_type_holder", "name_unhandled": True},
            )

    def test_create_mime_static_file_static(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(history_temp_file, {})
            file_path = "./tests/donor_files/one_file.py"
            user_inputs = (
                new_key_start(False)
                + get_mime_input("static")
                + get_file_name_input("static")
            )
            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(NewKeyAction) as NKA:
                    Runtime(file_path, history_temp_file.name, "TestClass")
                exception: NewKeyAction = NKA.exception
                self.assertEqual(exception.new_key_name, "file")
                self.assertEqual(
                    exception.new_key,
                    {
                        "mime_type_fix": "application/octet-stream",
                        "file_name_fix": "binary.file",
                    },
                )
        os.remove(history_temp_file.name)

    def test_create_mime_static_supplied_file_static_supplied(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(history_temp_file, {})
            file_path = "./tests/donor_files/one_file.py"
            user_inputs = (
                new_key_start(False)
                + get_mime_input("static", value="get_mime_input")
                + get_file_name_input("static", value="get_file_name_input")
            )
            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(NewKeyAction) as NKA:
                    Runtime(file_path, history_temp_file.name, "TestClass")
                exception: NewKeyAction = NKA.exception
                self.assertEqual(exception.new_key_name, "file")
                self.assertEqual(
                    exception.new_key,
                    {
                        "mime_type_fix": "get_mime_input",
                        "file_name_fix": "get_file_name_input",
                    },
                )
        os.remove(history_temp_file.name)

    def test_create_mime_dynamic_first_file_dynamic_first(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(history_temp_file, {})
            file_path = "./tests/donor_files/one_file.py"
            user_inputs = (
                new_key_start(False)
                + get_mime_input("dynamic", index=0)
                + get_file_name_input("dynamic", index=0)
            )
            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(NewKeyAction) as NKA:
                    Runtime(file_path, history_temp_file.name, "TestClass")
                exception: NewKeyAction = NKA.exception
                self.assertEqual(exception.new_key_name, "file")
                self.assertEqual(
                    exception.new_key,
                    {
                        "mime_type_field_name": "name",
                        "file_name_field_name": "name",
                    },
                )
        os.remove(history_temp_file.name)

    def test_create_mime_dynamic_default_file_dynamic_default(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(history_temp_file, {})
            file_path = "./tests/donor_files/one_file.py"
            user_inputs = (
                new_key_start(False)
                + get_mime_input("dynamic")
                + get_file_name_input("dynamic")
            )
            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(NewKeyAction) as NKA:
                    Runtime(file_path, history_temp_file.name, "TestClass")
                exception: NewKeyAction = NKA.exception
                self.assertEqual(exception.new_key_name, "file")
                self.assertEqual(
                    exception.new_key,
                    {
                        "mime_type_field_name": "file_mime_col",
                        "file_name_field_name": "file_file_name_col",
                    },
                )
        os.remove(history_temp_file.name)

    def test_create_mime_dynamic_supplied_file_dynamic_supplied(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(history_temp_file, {})
            file_path = "./tests/donor_files/one_file.py"
            user_inputs = (
                new_key_start(False)
                + get_mime_input("dynamic", "get_mime_input")
                + get_file_name_input("dynamic", "get_file_name_input")
            )
            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(NewKeyAction) as NKA:
                    Runtime(file_path, history_temp_file.name, "TestClass")
                exception: NewKeyAction = NKA.exception
                self.assertEqual(exception.new_key_name, "file")
                self.assertEqual(
                    exception.new_key,
                    {
                        "mime_type_field_name": "get_mime_input",
                        "file_name_field_name": "get_file_name_input",
                    },
                )
        os.remove(history_temp_file.name)
