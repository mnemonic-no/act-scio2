#!/usr/bin/env python3

""" SCIO Analyze module """

import argparse
import asyncio
import datetime
import gzip
import json
import logging
import os.path
import re
import sys
from typing import Dict, List, Optional, Text

import addict
import caep
import greenstalk
import pytz
import requests

import act.scio.config
import act.scio.logsetup
from act.scio import plugin

DEFAULT_METADATA_DATE_FIELDS = [
    "Creation-Date",
    "Last-Modified",
    "Last-Save-Date",
    "article:modified_time",
    "article:published_time",
    "citation_publication_date",
    "created",
    "date",
    "dcterms:created",
    "dcterms:modified",
    "meta:creation-date",
    "meta:save-date",
    "modified",
    "og:updated_time",
    "pdf:docinfo:created",
    "pdf:docinfo:custom:date",
    "pdf:docinfo:modified",
    "xmpMM:History:When",
]

ISO8601_DATE_RE = re.compile(r"^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


def parse_args() -> argparse.Namespace:
    """Helper setting up the argsparse configuration"""

    arg_parser = act.scio.config.parse_args("Scio 2 Analyzer")
    arg_parser.add_argument("--plugins", dest="plugins", type=str)
    arg_parser.add_argument(
        "--metadata-date-fields", default=",".join(DEFAULT_METADATA_DATE_FIELDS)
    )
    arg_parser.add_argument("--proxy-string", help="Proxy to use webdump upload")
    arg_parser.add_argument(
        "--webdump", dest="webdump", type=str, help="URI to post result data"
    )

    args = caep.config.handle_args(arg_parser, "scio/etc", "scio.ini", "analyze")

    args.metadata_date_fields = [
        field.strip() for field in args.metadata_date_fields.split(",")
    ]

    return args  # type: ignore


def remove_non_iso_dates(
    metadata: Dict[Text, Text], isodate_fields: List[Text]
) -> Dict[Text, Text]:
    filtered = {}

    for key, value in metadata.items():

        if key in isodate_fields:
            if not isinstance(value, str):
                logging.warning("date value is not string %s:%s", key, value)
                continue
            if not ISO8601_DATE_RE.search(value):
                logging.warning("Illegal date value in %s:%s", key, value)
                continue
        filtered[key] = value

    return filtered


def get_input(beanstalk_client: Optional[greenstalk.Client] = None) -> addict.Dict:
    """Helper function to abstract away how we get the text to work on"""

    nlpdata = addict.Dict()
    if not beanstalk_client:
        logging.info("Waiting for work on stdin")
        data = sys.stdin.read()
        nlpdata.content = data
    else:
        # ADD BEANSTALK JOB CONSUMPTION
        logging.info("Waiting for work from beanstalk")
        job = beanstalk_client.reserve()
        try:
            nlpdata = addict.Dict(json.loads(gzip.decompress(job.body)))
            logging.info("Started work on %s", nlpdata.get("hexdigest", "No Hexdigest"))
        except OSError as e:
            # File not found - log error
            logging.error(e)
        finally:
            # Remove job, either on success or file not found
            beanstalk_client.delete(job)

    return nlpdata


async def analyze(
    plugins: List[plugin.BasePlugin],
    beanstalk_client: Optional[greenstalk.Client] = None,
) -> addict.Dict:
    """Main analyze loop running all plugins on the text"""

    loop = asyncio.get_event_loop()

    nlpdata: addict.Dict = get_input(beanstalk_client)
    if not nlpdata.content:
        logging.error("Missing content")
        return addict.Dict({})

    nlpdata["Analyzed-Date"] = (
        datetime.datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
    )

    # make sure we have a Creation-Date field even though the
    # document did not contain one. When missing, use current analyzed time.
    nlpdata["Creation-Date"] = nlpdata.get("metadata", {}).get(
        "Creation-Date", nlpdata["Analyzed-Date"]
    )

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

        await asyncio.gather(*tasks, return_exceptions=True)

        for task in tasks:
            if task.exception():
                logging.error("%s returned an exception: %s", task, task.exception())
            else:
                res = task.result()
                nlpdata[res.name] = res.result

        pipeline = []
        for candidate in staged[:]:
            if all(dep in nlpdata for dep in candidate.dependencies):
                pipeline.append(candidate)
                staged.remove(candidate)

    for candidate in staged:
        logging.warning(
            "Candidate %s did not run due to unmet dependency %s",
            candidate.name,
            candidate.dependencies,
        )

    return nlpdata


async def async_main() -> None:
    """Async version of main"""

    args = parse_args()

    act.scio.logsetup.setup_logging(args.loglevel, args.logfile, "scio-analyze")

    plugins = plugin.load_default_plugins()

    if args.plugins:
        try:
            logging.info("loading plugins from %s", args.plugins)
            plugins += plugin.load_external_plugins(args.plugins)
        except FileNotFoundError:
            logging.warning("Unable to load plugins from %s", args.plugins)

    # Inject config directory into each plugin
    for p in plugins:
        p.configdir = os.path.join(args.config_dir, "etc/plugins")

    beanstalk_client = act.scio.config.beanstalk_client(args, watch="scio_analyze")
    elasticsearch_client = act.scio.config.elasticsearch_client(args)

    loop = asyncio.get_event_loop()

    while True:
        task = loop.create_task(analyze(plugins, beanstalk_client))
        try:
            await task
        except LookupError:
            logging.error(
                "Got LookupError. If nltk data is missing, "
                "run scio-nltk-download, which should download "
                "all nltk data to ~/nltk_data."
            )
            raise

        result = task.result()
        if not result:
            continue
        result_json = json.dumps(result, indent="  ")

        if args.webdump:
            proxies = (
                {"http": args.proxy_string, "https": args.proxy_string}
                if args.proxy_string
                else None
            )

            r = requests.post(args.webdump, data=result_json, proxies=proxies)
            if r.status_code != 200:
                logging.error("Unable to post result data to webdump: %s", r.text)

        if elasticsearch_client:
            hexdigest = result.get("hexdigest")

            if not hexdigest:
                logging.error("Missing hexdigest, skipping elasticsearch storage")
            else:
                result["metadata"] = remove_non_iso_dates(
                    result["metadata"], args.metadata_date_fields
                )

                try:
                    elasticsearch_client.index(index="scio2", id=hexdigest, body=result)
                except Exception as e:
                    logging.error("Error storing %s to elasticsearch: %s", hexdigest, e)
                    raise

                logging.info("Stored %s to elasticsearch", hexdigest)

        if not (args.webdump or elasticsearch_client):
            # Print to stdout if we do not send to webdump or elasticsearch
            print(result_json)

        # If we are not listening on a beanstalk work queue, behave like a command line
        # utility and exit after one document.
        if not beanstalk_client:
            break


def main() -> None:
    """Main entry point"""

    loop = asyncio.get_event_loop()
    task = loop.create_task(async_main())
    loop.run_until_complete(task)


if __name__ == "__main__":
    main()
