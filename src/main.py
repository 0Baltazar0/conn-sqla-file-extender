import importlib.util
import os
import sys
from typing import Any
from pathlib import Path
from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper
import yaml
from logger import logger


def find_py_files() -> list[str]:
    return [str(p.relative_to(os.getcwd())) for p in Path(".").rglob("*.[pP][yY]")]


def load_history() -> dict[str, Any]:
    loc = os.getcwd()
    for item in os.listdir(loc):
        if item == "csfe.yaml":
            with open(item) as infile:
                data = yaml.load(infile, yaml.Loader)
            return data
    return {}


if __name__ == "__main__":
    history = load_history()
    paths = find_py_files()
    for file in paths:
        spec = importlib.util.spec_from_file_location(file, file)
        if not spec or not spec.loader:
            logger.warning("Skipping file, module is not loadable %s", file)
            continue
        else:
            logger.info("Working on path %s", file)

        module = importlib.util.module_from_spec(spec)
        logger.debug("Path loaded: %s", file)
        spec.loader.exec_module(module)
        logger.debug("Path executed: %s", file)

        attributes = dir(module)
        for attribute_name in attributes:
            attribute = getattr(module, attribute_name)
            try:
                inspect(attribute)
                class_mapper(attribute)
            except Exception as e:
                logger.debug(
                    "Attribute rejected:%s, of error: %s", attribute_name, str(e)
                )
                continue
