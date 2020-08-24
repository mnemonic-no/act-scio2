"""Copyright 2020 mnemonic AS <opensource@mnemonic.no>

Permission to use, copy, modify, and/or distribute this software for
any purpose with or without fee is hereby granted, provided that the
above copyright notice and this permission notice appear in all
copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

---
Config utilities for scio
"""

import argparse
import logging
import os
from typing import Optional, Text

import caep
import elasticsearch
import greenstalk  # type: ignore

import act.scio.es


def parse_args(description: Text) -> argparse.ArgumentParser:
    """ Parse default arguments """
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--beanstalk',
                        help="Connect to beanstalk server. " +
                        "If not specified, read from stdin",
                        default="localhost")
    parser.add_argument('--beanstalk-port',
                        type=int,
                        default=11300,
                        help="Default 11300")
    parser.add_argument('--elasticsearch', help="Elasticsearch host to connect to.")
    parser.add_argument('--elasticsearch-user', help="Elasticsearch user")
    parser.add_argument('--elasticsearch-password', help="Elasticsearch password")
    parser.add_argument('--elasticsearch-port',
                        type=int,
                        default=9200,
                        help="Default 9200")
    parser.add_argument('--config-dir',
                        default=caep.get_config_dir("scio"),
                        help="Default config dir with configurations for scio and plugins")
    parser.add_argument('--logfile')
    parser.add_argument('--loglevel', default="info")

    return parser


def beanstalk_client(
        args: argparse.Namespace,
        use: Optional[Text] = None,
        watch: Optional[Text] = None) -> Optional[greenstalk.Client]:
    """ Return beanstalk client if args.beanstalk, otherwise, return None """
    client = None
    if args.beanstalk:
        logging.info("Connection to beanstalk")
        client = greenstalk.Client((args.beanstalk, args.beanstalk_port), encoding=None)
        if watch:
            client.watch(watch)
        if use:
            client.use(use)

    return client


def elasticsearch_client(args: argparse.Namespace) -> Optional[elasticsearch.client.Elasticsearch]:
    """ Return elasticsearch client if args.elasticsearch, otherwise, return None """
    if args.elasticsearch:
        logging.info("Connection to elasticsearch")
        return act.scio.es.es_client(
            host=args.elasticsearch,
            port=args.elasticsearch_port,
            username=args.elasticsearch_user,
            password=args.elasticsearch_password,
        )
    return None


def get_cache_dir(cache_id: str, create: bool = False) -> str:
    """
    Get cache dir.

    Honors $XDG_CACHE_HOME, but fallbacks to $HOME/.cache

Args:
    cache_id [str]: directory under CACHE that will be used
    create [bool]: create directory if not exists

Return path to cache_directory
    """

    home = os.environ["HOME"]

    cache_home = os.environ.get("XDG_CACHE_HOME", os.path.join(home, ".cache"))
    cache_dir = os.path.join(cache_home, cache_id)

    if create and not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    return cache_dir
