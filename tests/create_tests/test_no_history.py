import unittest
from unittest import mock
import builtins
from executor import NewKeyAction
from runtime import NoActionRequired, Runtime


class TestNoFile(unittest.TestCase):
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
