from importlib import import_module

from act.scio import plugins
import pkgutil
from types import ModuleType
from typing import Text, List
import logging
import os


module_interface = ["name", "analyze", "info", "version", "dependencies"]


def load_default_plugins() -> List[ModuleType]:
    """load_default_plugins scans the package for internal plugins, loading
    them dynamically and checking for the presence of the attributes defined in
    module_interface"""

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


def load_external_plugins(directory: Text) -> List[ModuleType]:
    """load_external_plugins scans a directory for .py files, and attempts to
    import each file, adding them to the list of modules. The functions will
    only add the module to the returned list of modules if it has a dictionary
    describing the module_interface list"""

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
