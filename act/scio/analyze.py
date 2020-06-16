#!/usr/bin/env python3

""" SCIO Analyze module """

from act.scio import plugin
from caep import get_config_dir  # type: ignore
from typing import Optional, List
import addict  # type: ignore
import argparse
import asyncio
import greenstalk  # type: ignore
import gzip
import json
import logging
import os.path
import requests
import sys


def parse_args() -> argparse.Namespace:
    """Helper setting up the argsparse configuration"""

    parser = argparse.ArgumentParser(description="Scio 2")

    parser.add_argument('--beanstalk', dest='beanstalk', type=str, default=None,
                        help="Connect to beanstalk server. If not specified, read from stdin")
    parser.add_argument('--beanstalk_port', dest='beanstalk_port', type=int, default=11300,
                        help="Default 11300")
    parser.add_argument('--config-dir', dest='configdir', type=str, default=get_config_dir("scio"),
                        help="Default config dir with configurations for scio and plugins")
    parser.add_argument('--plugins', dest='plugins', type=str)
    parser.add_argument('--webdump', dest='webdump', type=str, help="URI to post result data")
    parser.add_argument('--logfile', dest='logfile', type=str, default="scio_analyze.log")

    return parser.parse_args()


def get_input(beanstalk_client: Optional[greenstalk.Client] = None) -> addict.Dict:
    """Helper function to abstract away how we get the text to work on"""

    nlpdata = addict.Dict()
    if not beanstalk_client:
        data = sys.stdin.read()
        nlpdata.content = data
    else:
        # ADD BEANSTALK JOB CONSUMPTION
        logging.info("Waiting for work")
        job = beanstalk_client.reserve()
        nlpdata = addict.Dict(json.loads(gzip.decompress(job.body)))
        logging.info(nlpdata.keys())
        beanstalk_client.delete(job)

    return nlpdata


async def analyze(plugins: List[plugin.BasePlugin],
                  beanstalk_client: Optional[greenstalk.Client] = None) -> addict.Dict:
    """Main analyze loop running all plugins on the text"""

    loop = asyncio.get_event_loop()

    nlpdata: addict.Dict = get_input(beanstalk_client)

    staged = []  # for plugins with dependencies
    pipeline = []  # for plugins to be run now

    for p in plugins:
        if p.dependencies:
            staged.append(p)
        else:
            pipeline.append(p)

    while pipeline:
        tasks = []
        for p in pipeline:
            tasks.append(loop.create_task(p.analyze(nlpdata)))

        await asyncio.gather(*tasks)

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
    """Async version of main"""

    args = parse_args()

    logging.basicConfig(filename=args.logfile, level=logging.DEBUG)

    plugins = plugin.load_default_plugins()

    if args.plugins:
        try:
            plugins += plugin.load_external_plugins(args.plugins)
        except FileNotFoundError:
            logging.warning("Unable to load plugins from %s", args.plugins)

    # Inject config directory into each plugin
    for p in plugins:
        p.configdir = os.path.join(args.configdir, "etc/plugins")

    beanstalk_client = None
    if args.beanstalk:
        logging.info("Connection to beanstalk")
        beanstalk_client = greenstalk.Client(args.beanstalk, args.beanstalk_port, encoding=None)
        beanstalk_client.watch('scio_analyze')

    loop = asyncio.get_event_loop()

    while True:
        task = loop.create_task(analyze(plugins, beanstalk_client))
        await task
        result = json.dumps(task.result(), indent="  ")
        if args.webdump:
            proxies = {
                'http': args.proxy_string,
                'https': args.proxy_string
            } if args.proxy_string else None

            r = requests.post(args.webdump, data=result, proxies=proxies)
            if r.status_code != 200:
                logging.error("Unable to post result data to webdump: %s", r.text)

        else:
            print(result)

        # If we are not listening on a beanstalk work queue, behave like a command line
        # utility and exit after one document.
        if not beanstalk_client:
            break


def main() -> None:
    """Main entry point"""

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([async_main()]))


if __name__ == "__main__":
    main()
