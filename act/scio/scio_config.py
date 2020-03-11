#!/usr/bin/env python3
""" Handle worker config"""


from pkg_resources import resource_exists, resource_isdir, Requirement
from pkg_resources import resource_string, resource_listdir
from typing import Text, List, Union, Tuple
import argparse
import caep
import os
import sys


CONFIG_ID = "scio"
CONFIG_NAME = "scio.ini"

PKG_NAME = "act.scio"


# there is no isfile in the pkg_resources.resource_* so we use the inverse of isdir
def resource_isfile(*x: Union[str, Requirement]) -> bool:
    return not resource_isdir(*x)  # type: ignore


def parseargs() -> argparse.Namespace:
    """ Parse arguments """

    parser = argparse.ArgumentParser("ACT SCIO config", epilog="""
    show - Print default config
    user - Copy default config to {0}/{1}
    system - Copy default config to /etc/{1}
""".format(caep.get_config_dir(CONFIG_ID), CONFIG_NAME),
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('action', nargs=1, choices=["show", "user", "system"])

    return parser.parse_args()


def default_ini() -> List[Tuple[Text, Text]]:
    "Get content of default ini file"

    files: List[Tuple[Text, Text]] = []
    if resource_exists(PKG_NAME, "etc") and resource_isdir(PKG_NAME, "etc"):
        for fname in [x for x in resource_listdir(PKG_NAME, "etc") if resource_isfile(PKG_NAME, x)]:
            files.append((f"{fname}",
                         resource_string(PKG_NAME, "etc/" + fname).decode("utf-8")))

        if resource_exists(PKG_NAME, "etc/plugins") and resource_isdir(PKG_NAME, "etc/plugins"):
            for fname in [x for x in resource_listdir(PKG_NAME, "etc/plugins")
                          if resource_isfile(PKG_NAME, x)]:
                files.append((f"plugins/{fname}",
                             resource_string(PKG_NAME, "etc/plugins/" + fname).decode("utf-8")))

    return files


def save_config(configdir: Text) -> None:
    """ Save config to specified directory """

    # Make sure the config directories exists before storing files.
    plugin_path = os.path.join(configdir, "plugins")
    try:
        os.mkdir(plugin_path)
        print(f"creating directory {plugin_path}")
    except FileExistsError:
        print(f"WARNING: config path allready exists {plugin_path}")
        pass
    except PermissionError:
        sys.stderr.write(f"ERROR: Permission denied when creating {plugin_path}\n")
        sys.exit(2)

    for filename, content in default_ini():
        full_filename = os.path.join(configdir, filename)
        if os.path.isfile(full_filename):
            sys.stderr.write("WARNING: Config already exists: {}\n".format(full_filename))
            continue
        try:
            with open(full_filename, "w") as f:
                f.write(content)
            print("Config copied to {}".format(full_filename))
        except PermissionError as err:
            sys.stderr.write("{}\n".format(err))
            sys.exit(2)


def main() -> None:
    "main function"
    args = parseargs()

    if "show" in args.action:
        for filename, content in default_ini():
            print(f"-- {filename}\n{content}\n")

    if "user" in args.action:
        config_dir = caep.get_config_dir(CONFIG_ID, create=True)
        print("Config dir:", config_dir)
        save_config(config_dir)

    if "system" in args.action:
        save_config("/etc/")


if __name__ == '__main__':
    main()