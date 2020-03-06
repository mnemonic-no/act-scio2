#!/usr/bin/env python3
from typing import Text, Dict
import argparse
import asyncio
import logging

from act.scio import plugin


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scio 2")

    parser.add_argument('--beanstalk', dest='beanstalk', type=str, default=None,
                        help="Connect to beanstalk server. If not specified, read from stdin")
    parser.add_argument('--plugins', dest='plugins', type=str,
                        default='plugins/')

    return parser.parse_args()


async def analyze(doc: Text) -> dict:
    args = parse_args()

    plugins = plugin.load_default_plugins()
    plugins += plugin.load_external_plugins(args.plugins)

    data = ""
    if not args.beanstalk:
        import sys
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
            tasks.append(asyncio.create_task(p.analyze(data, result)))

        for task in tasks:
            await task

        for task in tasks:
            if task.exception():
                logging.warning("%s return an exception: %s", task.get_name(), task.exception())
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
    task = asyncio.create_task(analyze("test document"))
    await task
    print(task.result())


def main() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([async_main()]))
    #asyncio.run(async_main())  # type: ignore
    #await main_task


if __name__ == "__main__":
    main()
