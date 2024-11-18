import ast
from tempfile import _TemporaryFileWrapper
from typing import Any
from ast_comments import unparse as ast_unparse
from yaml import dump


def plan_file(temp_file: _TemporaryFileWrapper, data: Any) -> None:
    temp_file.seek(0)
    temp_file.write(dump(data))


def plan_ast_file(temp_file: _TemporaryFileWrapper, data: ast.Module | ast.AST) -> None:
    temp_file.seek(0)
    temp_file.write(ast_unparse(data))
