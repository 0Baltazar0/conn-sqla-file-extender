import importlib.util
import os
from pathlib import Path
from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper
from executor import (
    ACTION_TYPE_ERRORS,
    ApplyHistoryAction,
    Executor,
)
from logger import LOGGER
from runtime import AbortException, Runtime
from settings import SETTINGS


def find_py_files() -> list[str]:
    return [str(p.relative_to(os.getcwd())) for p in Path(".").rglob("*.[pP][yY]")]


def get_history_path() -> str:
    if SETTINGS.history_path:
        return SETTINGS.history_path
    search_history = next(Path(".").rglob("*csfe.[yY][aA]?[mM][lL]"), None)
    if search_history:
        return str(search_history.relative_to(os.getcwd()))
    else:
        return "./csfe.yaml"


def assert_file_exist(file_name: str):
    if not os.path.exists(file_name):
        with open(file_name, "w"):
            return
    else:
        return


if __name__ == "__main__":
    history_path = get_history_path()
    assert_file_exist(history_path)
    paths = find_py_files()
    for file in paths:
        spec = importlib.util.spec_from_file_location(file, file)
        if not spec or not spec.loader:
            LOGGER.warning("Skipping file, module is not loadable %s", file)
            continue
        else:
            LOGGER.info("Working on path %s", file)

        module = importlib.util.module_from_spec(spec)
        LOGGER.debug("Path loaded: %s", file)
        spec.loader.exec_module(module)
        LOGGER.debug("Path executed: %s", file)

        attributes = dir(module)
        for attribute_name in attributes:
            attribute = getattr(module, attribute_name)
            try:
                inspect(attribute)
                class_mapper(attribute)
                while True:
                    try:
                        Runtime(file, history_path, attribute_name)
                    except ACTION_TYPE_ERRORS as action:
                        Executor.handle_action(action)
                    except AbortException as e:
                        continue
                    except ApplyHistoryAction as aha:
                        Executor.handle_action(aha)
                        break
                    except Exception as e:
                        raise e
            except Exception as e:
                LOGGER.debug(
                    "Attribute rejected:%s, of error: %s", attribute_name, str(e)
                )
                continue
