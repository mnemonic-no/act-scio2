#!/usr/bin/env python3

""" SCIO Analyze module """

from typing import Any, Dict, List
import argparse
import asyncio
import logging
import sys

from act.scio import plugin


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scio 2")

    parser.add_argument('--beanstalk', dest='beanstalk', type=str, default=None,
                        help="Connect to beanstalk server. If not specified, read from stdin")
    parser.add_argument('--plugins', dest='plugins', type=str)

    return parser.parse_args()


async def analyze(plugins: List[Any], beanstalk: bool) -> dict:
    loop = asyncio.get_event_loop()

    data = ""
    if not beanstalk:
        data = sys.stdin.read()

    staged = []  # for plugins with dependencies
    pipeline = []  # for plugins to be run now

    for p in plugins:
        if len(p.dependencies) > 0:
            staged.append(p)
        else:
            pipeline.append(p)

    result: Dict = {}
    while pipeline:
        tasks = []
        for p in pipeline:
            tasks.append(loop.create_task(p.analyze(data, result)))

        for task in tasks:
            await task

        for task in tasks:
            if task.exception():
                logging.warning("%s return an exception: %s", task, task.exception())
            else:
                res = task.result()
                result[res.name] = res.result

        pipeline = []
        for candidate in staged[:]:
            if all(dep in result for dep in candidate.dependencies):
                pipeline.append(candidate)
                staged.remove(candidate)

    if len(staged) > 0:
        for candidate in staged:
            logging.warning("Candidate %s did not run due to unmet dependency %s",
                            candidate.name,
                            candidate.dependencies)

    return result


async def async_main() -> None:
    args = parse_args()

    plugins = plugin.load_default_plugins()

    if args.plugins:
        try:
            plugins += plugin.load_external_plugins(args.plugins)
        except FileNotFoundError:
            logging.warning("Unable to load plugins from %s", args.plugins)

    loop = asyncio.get_event_loop()
    task = loop.create_task(analyze(plugins, args.beanstalk))
    await task
    print(task.result())


def main() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([async_main()]))
    #asyncio.run(async_main())  # type: ignore
    #await main_task


if __name__ == "__main__":
    main()
