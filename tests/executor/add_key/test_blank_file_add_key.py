import ast
import os
import sys
from tempfile import NamedTemporaryFile
import unittest

from yaml import Loader, load
from executor import Executor, NewKeyAction
from ast_comments import parse as ast_parse, unparse as ast_unparse

from naming import get_static_file_name_key, get_static_mime_key, werkzeug_get_name
from utils.ast_tools import get_attribute, get_class, get_function

sys.path.append(os.path.join(os.getcwd(), "tests"))

from donor_files.file_maker import plan_ast_file, plan_file


class TestBlankFileHistory(unittest.TestCase):
    history_path = "./tests/history/empty.yaml"
    no_file_path = "./tests/donor_files/no_file.py"
    class_name = "TestClass"

    def test_add_key_unhandled(self):
        with open(self.no_file_path) as original_file_source:
            with NamedTemporaryFile("w+", delete=False) as file_source:
                original_ast = ast_parse(original_file_source.read())
                plan_ast_file(file_source, original_ast)
                file_source.close()
                with NamedTemporaryFile("w+", delete=False) as history_source:
                    plan_file(history_source, {})
                    history_source.close()
                    Executor.handle_action(
                        NewKeyAction(
                            "test_file",
                            {"unhandled": True},
                            file_source.name,
                            "TestClass",
                            history_source.name,
                        )
                    )
                    with open(file_source.name) as edited_file_source:
                        edited_ast = ast_parse(edited_file_source.read())
                        with open(history_source.name) as edited_history:
                            edited_history = load(edited_history, Loader)

                            self.assertEqual(
                                edited_history,
                                {"TestClass": {"test_file": {"unhandled": True}}},
                            )
                            self.assertEqual(
                                ast_unparse(edited_ast), ast_unparse(original_ast)
                            )

        os.remove(history_source.name)
        os.remove(file_source.name)

    def test_add_key_mime_static_file_static_werkzeug(self) -> None:
        key_name = "test_file"
        with open(self.no_file_path) as original_file_source:
            with NamedTemporaryFile("w+", delete=False) as file_source:
                original_ast = ast_parse(original_file_source.read())
                plan_ast_file(file_source, original_ast)
                file_source.close()
                with NamedTemporaryFile("w+", delete=False) as history_source:
                    plan_file(history_source, {})
                    history_source.close()
                    os.environ["mode"] = "flask"
                    Executor.handle_action(
                        NewKeyAction(
                            key_name,
                            {
                                "mime_type_fix": "application/octet-stream",
                                "file_name_fix": "binary.file",
                            },
                            file_source.name,
                            self.class_name,
                            history_source.name,
                        )
                    )
                    with open(file_source.name) as edited_file_source:
                        edited_ast: ast.Module = ast_parse(edited_file_source.read())  # type: ignore
                        with open(history_source.name) as edited_history:
                            edited_history = load(edited_history, Loader)
                            self.assertEqual(
                                edited_history,
                                {
                                    self.class_name: {
                                        key_name: {
                                            "mime_type_fix": "application/octet-stream",
                                            "file_name_fix": "binary.file",
                                        }
                                    }
                                },
                            )
                            self.assertNotEqual(
                                ast_unparse(edited_ast), ast_unparse(original_ast)
                            )
                            _class = get_class(self.class_name, edited_ast)

                            if _class is None:
                                self.assertIsNotNone(_class)
                                return

                            self.assertIsNotNone(
                                get_attribute(get_static_mime_key(key_name), _class)
                            )

                            self.assertIsNotNone(
                                get_attribute(
                                    get_static_file_name_key(key_name), _class
                                )
                            )
                            self.assertIsNotNone(
                                get_function(werkzeug_get_name(key_name), _class)
                            )

        os.remove(history_source.name)
        os.remove(file_source.name)
