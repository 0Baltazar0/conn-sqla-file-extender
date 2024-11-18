import builtins
import os
import sys
from tempfile import NamedTemporaryFile
import unittest
from unittest import mock

from executor import (
    RemoveHistoryCleanAction,
    RemoveHistoryKeyAsIsAction,
    ReAddHistoryAction,
)
from runtime import Runtime

sys.path.append(os.path.join(os.getcwd(), "tests"))

from inputs.missing_key_inputs import get_missing_key_input
from donor_files.file_maker import plan_file

RENAME_ATTRIBUTES = [
    "old_key_name",
    "old_key",
]


class TestMissing(unittest.TestCase):
    file_path = "./tests/donor_files/no_file.py"

    def test_missing_clean(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(
                history_temp_file, {"TestClass": {"old_key": {"unhandled": True}}}
            )
            history_temp_file.close()
            user_inputs = get_missing_key_input("clean")
            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(RemoveHistoryCleanAction) as NKA:
                    Runtime(self.file_path, history_temp_file.name, "TestClass")
                exception = NKA.exception

                self.assertEqual(
                    {k: getattr(exception, k) for k in RENAME_ATTRIBUTES},
                    {
                        "old_key_name": "old_key",
                        "old_key": {"unhandled": True},
                    },
                )
        os.remove(history_temp_file.name)

    def test_missing_re_add(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(
                history_temp_file, {"TestClass": {"old_key": {"unhandled": True}}}
            )
            history_temp_file.close()
            user_inputs = get_missing_key_input("re_add")
            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(ReAddHistoryAction) as NKA:
                    Runtime(self.file_path, history_temp_file.name, "TestClass")
                exception = NKA.exception

                self.assertEqual(
                    {k: getattr(exception, k) for k in RENAME_ATTRIBUTES},
                    {
                        "old_key_name": "old_key",
                        "old_key": {"unhandled": True},
                    },
                )
        os.remove(history_temp_file.name)

    def test_missing_as_is(self) -> None:
        with NamedTemporaryFile("w+", delete=False) as history_temp_file:
            plan_file(
                history_temp_file, {"TestClass": {"old_key": {"unhandled": True}}}
            )
            history_temp_file.close()
            user_inputs = get_missing_key_input("as_is")
            with mock.patch.object(builtins, "input", lambda _: user_inputs.pop(0)):
                with self.assertRaises(RemoveHistoryKeyAsIsAction) as NKA:
                    Runtime(self.file_path, history_temp_file.name, "TestClass")
                exception = NKA.exception

                self.assertEqual(exception.old_key_name, "old_key")
        os.remove(history_temp_file.name)
