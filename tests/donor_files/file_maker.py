from tempfile import _TemporaryFileWrapper
from typing import Any

from yaml import dump


def plan_file(temp_file: _TemporaryFileWrapper, data: Any) -> None:
    temp_file.seek(0)
    temp_file.write(dump(data))
