from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location

from act.scio import plugins
import pkgutil
from typing import Text, List, Dict, Optional
import logging
import os
from pydantic import BaseModel, StrictStr


module_interface = ["name", "analyze", "info", "version", "dependencies"]


class Result(BaseModel):
    name: StrictStr
    version: StrictStr
    result: dict


class BasePlugin:

    def __init__(self: object):
        pass

    name = "BasePlugin"
    info = "This is the empty plugin of a plugin for Scio"
    version = "0.1"
    dependencies: List[Text] = []

    async def analyze(self, text: Text, prior_result: Dict) -> Result:
        return Result(name=self.name, version=self.version, result={"test": text})


def load_default_plugins() -> List[BasePlugin]:
    """load_default_plugins scans the package for internal plugins, loading
    them dynamically and checking for the presence of the attributes defined in
    module_interface"""

    myplugins: List[BasePlugin] = []

    prefix = plugins.__name__ + "."
    for _, modname, _ in pkgutil.iter_modules(plugins.__path__, prefix):

        p = load_plugin(modname)
        if p:
            myplugins.append(p)

    return myplugins


def load_external_plugins(directory: Text) -> List[BasePlugin]:
    """load_external_plugins scans a directory for .py files, and attempts to
    import each file, adding them to the list of modules. The functions will
    only add the module to the returned list of modules if it has a dictionary
    describing the module_interface list"""

    myplugins: List[BasePlugin] = []

    for plugin_file_name in os.listdir(directory):
        if plugin_file_name == "__init__.py":
            continue
        plugin_path = os.path.join(directory, plugin_file_name)
        if os.path.isfile(plugin_path) and plugin_path.endswith(".py"):

            p = load_plugin(plugin_path)
            if p:
                myplugins.append(p)

    return myplugins


def load_plugin(module_name: Text) -> Optional[BasePlugin]:
    if module_name.endswith(".py"):
        spec = spec_from_file_location("plugin_mod", module_name)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        try:
            module = import_module(module_name)
        except Exception as e:
            logging.warning(e)
            return None

    conform = True
    try:
        p = module.Plugin()  # type: ignore
    except AttributeError as err:
        logging.warning("Could not load plugin from module %s: %s", module_name, err)
        return None

    for mint in module_interface:
        if not hasattr(p, mint):
            logging.warning("%s does not have %s attribute", p.name, mint)
            conform = False

    if not conform:
        return None

    return p
