#!/usr/bin/env python3

""" SCIO Analyze module """

from act.scio.attrdict import AttrDict
from act.scio import plugin
from caep import get_config_dir
from typing import List
import argparse
import asyncio
import json
import logging
import os.path
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scio 2")

    parser.add_argument('--beanstalk', dest='beanstalk', type=str, default=None,
                        help="Connect to beanstalk server. If not specified, read from stdin")
    parser.add_argument('--config-dir', dest='configdir', type=str, default=get_config_dir("scio"),
                        help="Default config dir with configurations for scio and plugins")
    parser.add_argument('--plugins', dest='plugins', type=str)

    return parser.parse_args()


async def analyze(plugins: List[plugin.BasePlugin], beanstalk: bool) -> dict:
    loop = asyncio.get_event_loop()

    data = ""
    if not beanstalk:
        data = sys.stdin.read()

    staged = []  # for plugins with dependencies
    pipeline = []  # for plugins to be run now

    for p in plugins:
        if p.dependencies:
            staged.append(p)
        else:
            pipeline.append(p)

    nlpdata: AttrDict = AttrDict()
    nlpdata.text = data
    while pipeline:
        tasks = []
        for p in pipeline:
            tasks.append(loop.create_task(p.analyze(nlpdata)))

        for task in tasks:
            await task

        for task in tasks:
            if task.exception():
                logging.warning("%s return an exception: %s", task, task.exception())
            else:
                res = task.result()
                nlpdata[res.name] = res.result

        pipeline = []
        for candidate in staged[:]:
            if all(dep in nlpdata for dep in candidate.dependencies):
                pipeline.append(candidate)
                staged.remove(candidate)

    for candidate in staged:
        logging.warning("Candidate %s did not run due to unmet dependency %s",
                        candidate.name,
                        candidate.dependencies)

    return nlpdata


async def async_main() -> None:
    args = parse_args()

    plugins = plugin.load_default_plugins()

    if args.plugins:
        try:
            plugins += plugin.load_external_plugins(args.plugins)
        except FileNotFoundError:
            logging.warning("Unable to load plugins from %s", args.plugins)

    # Inject config directory into each plugin
    for p in plugins:
        p.configdir = os.path.join(args.configdir, "etc/plugins")

    loop = asyncio.get_event_loop()
    task = loop.create_task(analyze(plugins, args.beanstalk))
    await task
    print(json.dumps(task.result(), indent="  "))


def main() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([async_main()]))


if __name__ == "__main__":
    main()
