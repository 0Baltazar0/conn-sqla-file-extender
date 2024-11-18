import builtins
import os
import sys
from tempfile import NamedTemporaryFile
import unittest
from unittest import mock

from executor import RenameAction
from runtime import Runtime

sys.path.append(os.path.join(os.getcwd(), "tests"))

from donor_files.file_maker import plan_file
from inputs.new_file_name_inputs import get_file_name_input
from inputs.new_key_inputs import new_key_rename, rename_keep_unhandled
from inputs.new_mime_inputs import get_mime_input

RENAME_ATTRIBUTES = [
    "old_key_name",
    "old_key",
    "new_key_name",
    "new_key",
]


class TestRename(unittest.TestCase):
    history_path = "./tests/history/empty.yaml"
    file_path = "./tests/donor_files/one_file.py"

    def test_rename_unhandled(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(
                history_temp_file, {"TestClass": {"old_key": {"unhandled": True}}}
            )
            history_temp_file.close()

            user_inputs = new_key_rename() + ["y"]

            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(RenameAction) as NKA:
                    Runtime(self.file_path, history_temp_file.name, "TestClass")
                exception = NKA.exception
                keys = [
                    "old_key_name",
                    "old_key",
                    "new_key_name",
                    "new_key",
                ]
                self.assertEqual(exception.new_key_name, "file")
                self.assertEqual(
                    {k: getattr(exception, k) for k in keys},
                    {
                        "old_key_name": "old_key",
                        "old_key": {"unhandled": True},
                        "new_key_name": "file",
                        "new_key": {"unhandled": True},
                    },
                )
        os.remove(history_temp_file.name)

    def test_rename_unhandled_to_handled_unhandled(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(
                history_temp_file, {"TestClass": {"old_key": {"unhandled": True}}}
            )
            history_temp_file.close()
            user_inputs = (
                new_key_rename()
                + rename_keep_unhandled(False)
                + get_mime_input("unhandled")
                + get_file_name_input("unhandled")
            )

            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(RenameAction) as NKA:
                    Runtime(self.file_path, history_temp_file.name, "TestClass")
                exception = NKA.exception

                self.assertEqual(exception.new_key_name, "file")
                self.assertEqual(
                    {k: getattr(exception, k) for k in RENAME_ATTRIBUTES},
                    {
                        "old_key_name": "old_key",
                        "old_key": {"unhandled": True},
                        "new_key_name": "file",
                        "new_key": {"mime_unhandled": True, "name_unhandled": True},
                    },
                )
        os.remove(history_temp_file.name)

    def test_rename_unhandled_to_static_static(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(
                history_temp_file, {"TestClass": {"old_key": {"unhandled": True}}}
            )
            history_temp_file.close()
            user_inputs = (
                new_key_rename()
                + rename_keep_unhandled(False)
                + get_mime_input("static")
                + get_file_name_input("static")
            )

            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(RenameAction) as NKA:
                    Runtime(self.file_path, history_temp_file.name, "TestClass")
                exception = NKA.exception

                self.assertEqual(exception.new_key_name, "file")
                self.assertEqual(
                    {k: getattr(exception, k) for k in RENAME_ATTRIBUTES},
                    {
                        "old_key_name": "old_key",
                        "old_key": {"unhandled": True},
                        "new_key_name": "file",
                        "new_key": {
                            "mime_type_fix": "application/octet-stream",
                            "file_name_fix": "binary.file",
                        },
                    },
                )
        os.remove(history_temp_file.name)
