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

    for resource_dir in ["etc", "etc/plugins", "vendor"]:
        if resource_exists(PKG_NAME, resource_dir) and resource_isdir(PKG_NAME, resource_dir):
            for fname in [x for x in resource_listdir(PKG_NAME, resource_dir)
                          if resource_isfile(PKG_NAME, x)]:
                try:
                    files.append((f"{resource_dir}/{fname}",
                                  resource_string(
                                      PKG_NAME,
                                      f"{resource_dir}/" + fname).decode("utf-8")))
                except UnicodeDecodeError as err:
                    sys.stderr.write(f"WARNING: Skipping file {fname} [{err}]\n")

    return files


def make_path(configdir: Text, path: Text) -> None:
    """ Make sure the config directories exists before storing files. """
    plugin_path = os.path.join(configdir, path)
    try:
        os.mkdir(plugin_path)
        print(f"creating directory {plugin_path}")
    except FileExistsError:
        print(f"WARNING: config path allready exists {plugin_path}")
    except PermissionError:
        sys.stderr.write(f"ERROR: Permission denied when creating {plugin_path}\n")
        sys.exit(2)


def save_config(configdir: Text) -> None:
    """ Save config to specified directory """

    # Make sure the config directories exists before storing files.
    make_path(configdir, "etc")
    make_path(configdir, "etc/plugins")
    make_path(configdir, "vendor")

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
