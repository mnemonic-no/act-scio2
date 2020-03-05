from importlib import import_module
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

    for plugin_file_name in os.listdir(directory):
        if plugin_file_name == "__init__.py":
            continue
        plugin_path = os.path.join(directory, plugin_file_name)
        if os.path.isfile(plugin_path) and plugin_path.endswith(".py"):
            module_import = plugin_path.replace("/", ".")[:-3]

            try:
                module = import_module(module_import)
            except Exception as e:
                logging.warning(e)
                continue

            conform = True
            for mint in module_interface:
                if not hasattr(module, mint):
                    logging.warning(f"{plugin_path} does not have {mint} attribute")
                    conform = False
            if conform:
                modules.append(module)

    return modules
