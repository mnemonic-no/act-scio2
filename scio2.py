#!/usr/bin/env python3

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


def main() -> None:
    args = parse_args()

    plugins = plugin.load_plugins(args.plugins)

    data = ""
    if not args.beanstalk:
        import sys
        data = sys.stdin.read()

    for p in plugins:
        try:
            print(p.analyze(data))  # type: ignore
        except Exception as e:
            logging.warning(e)


if __name__ == "__main__":
    main()
