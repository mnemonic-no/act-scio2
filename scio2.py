#!/usr/bin/env python3

import asyncio
import plugin
import argparse
import logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scio 2")

    parser.add_argument('--beanstalk', dest='beanstalk', type=str, default=None,
                        help="Connect to beanstalk server. If not specified, read from stdin")
    parser.add_argument('--plugins', dest='plugins', type=str,
                        default='plugins/')

    return parser.parse_args()


async def analyze(doc) -> dict:
    args = parse_args()

    plugins = plugin.load_plugins(args.plugins)

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

    result = {}
    while pipeline:
        tasks = []
        for p in pipeline:
            tasks.append(asyncio.create_task(p.analyze(data, result)))

        for task in tasks:
            await task

        for task in tasks:
            res = task.result()
            result[res["name"]] = res

        pipeline = []
        for candidate in staged[:]:
            if all(dep in res for dep in candidate.dependencies):
                pipeline.append(candidate)
                staged.remove(candidate)

    if len(staged) > 0:
        for candidate in staged:
            logging.warning("Candidate %s did not run due to unmet dependency %s",
                            candidate.name,
                            candidate.dependencies)

    return res

async def main() -> None:
    pass


if __name__ == "__main__":
    asyncio.run(main())  # type: ignore
