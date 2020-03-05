from importlib import import_module

from act.scio import plugins
import pkgutil
from types import ModuleType
from typing import Text, List
import logging
import os


module_interface = ["name", "analyze", "info", "version", "dependencies"]


def load_plugins(directory: Text) -> List[ModuleType]:
    """load_plugins scans a directory for .py files, and attempts to import
    each file, adding them to the list of modules. The functions will only add
    the module to the returned list of modules if it has a dictionary
    describing the module in ".info" and an ".analyze()" function"""

    modules: List[ModuleType] = []

    prefix = plugins.__name__ + "."
    for _, modname, _ in pkgutil.iter_modules(plugins.__path__, prefix):
        try:
            module = import_module(modname)
        except Exception as e:
            logging.warning(e)
            continue

        conform = True
        for mint in module_interface:
            if not hasattr(module, mint):
                logging.warning(f"{modname} does not have {mint} attribute")
                conform = False
        if conform:
            modules.append(module)

    return modules
