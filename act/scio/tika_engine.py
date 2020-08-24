"""Tika/Scio integration. This module contains the scio tike server and service code"""

from tika import parser
from typing import Text, Optional, Any
import argparse
import asyncio
import greenstalk
import json
import logging
import os
import time
import tika
import gzip
import caep
import act.scio.logsetup
import act.scio.config

def parse_args() -> argparse.Namespace:
    """Helper setting up the argsparse configuration"""

    arg_parser = act.scio.config.parse_args("Scio 2 Tika server")
    return caep.config.handle_args(arg_parser, "scio/etc", "scio.ini", "tika")

class Server:
    """The server class listening for new work on beanstalk and sending it to
    Apache Tika for text extraction and den sending it to Scio for text analyzis."""

    def __init__(self,
                 beanstalk_host: Text = "127.0.0.1",
                 beanstalk_port: int = 11300):

        self.client: Optional[greenstalk.Client] = None
        self.connect(beanstalk_host, beanstalk_port)

        logging.info("initialize tika VM")
        tika.initVM()

    def client_ready(self) -> bool:
        """client_ready is a utility function checking whether the
        beanstalk client has a connection that works."""

        if not self.client:
            return False
        try:
            self.client.stats()
            return True
        except (OSError, BrokenPipeError, ConnectionError, ConnectionRefusedError):
            return False

    def connect(self,
                beanstalk_host: Text = "127.0.0.1",
                beanstalk_port: int = 11300) -> None:
        """Try to create a beanstalk connection"""

        if self.client:
            # close existing connection
            self.client.close()

        while not self.client_ready():
            try:
                logging.info("Trying to connect to beanstalkd on %s:%s",
                             beanstalk_host, beanstalk_port)
                self.client = greenstalk.Client((beanstalk_host, beanstalk_port))
            except ConnectionRefusedError as err:
                logging.warning("Server.connect: %s", err)
                logging.info("Server.connect: waiting 5 seconds")
                time.sleep(5)

        # We only want to receive messages specifically to scio. The default
        # beanstalk tube is ignored.
        self.client.watch('scio_doc')
        self.client.ignore('default')
        self.client.use('scio_analyze')

    async def reserve(self) -> Any:
        """Async reserve"""
        return self.client.reserve()  # type: ignore

    async def worker(self, worker_id: int) -> None:
        """Main worker code. Listening to the beanstalk client for ready work, sending it to the
        tika service and then posting the extracted document to the queue for consumption by
        the analyzis module"""

        while True:
            logging.info("Worker [%s] waiting for work.", worker_id)
            try:
                job = await self.reserve()
            except greenstalk.TimedOutError:
                continue

            logging.info("Worker [%s] got job.", worker_id)
            try:
                meta_data = json.loads(job.body)
            except json.decoder.JSONDecodeError as err:
                logging.warning("Unable to decode body %s [%s ...]", err, job.body[:25])
                self.client.delete(job)  # type: ignore
                continue

            if "filename" not in meta_data:
                logging.warning("No 'filename' field in meta data : %s", meta_data)
                self.client.delete(job)  # type: ignore
                continue

            if not os.path.isfile(meta_data['filename']):
                logging.warning("Could not find file '%s'", meta_data['filename'])
                self.client.delete(job)  # type: ignore
                continue

            with open(meta_data['filename'], 'rb') as buffer:
                data = parser.from_buffer(buffer)
                data.update(meta_data)

            self.client.delete(job)  # type: ignore
            logging.info("Worker [%s] waiting to post result.", worker_id)
            self.client.put(gzip.compress(json.dumps({**data, **meta_data}).encode('utf8')))  # type: ignore
            logging.info("Worker [%s] job done.", worker_id)

    async def _start(self, n: int) -> None:
        """Start the server, create n number of workers and wait for data on the queue"""

        loop = asyncio.get_event_loop()
        workers = []

        for i in range(n):
            logging.info("Starting worker [%s]", i)
            workers.append((n, loop.create_task(self.worker(i))))

        logging.info("Gather all workers")
        asyncio.gather(*[w for (_, w) in workers])

        for i, worker in workers:
            if worker.exception():
                logging.error("Worker [%s] ended with exception %s", i, worker.exception())

    def start(self, n: int = 4) -> None:
        """start the server"""

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait([self._start(n)]))

        logging.info("Server ended")


def main() -> None:
    """entry point"""

    args = parse_args()

    act.scio.logsetup.setup_logging(args.loglevel, args.logfile, "scio-tika-server")

    server = Server(args.beanstalk, args.beanstalk_port)

    logging.info("Starting Tika server")
    server.start()

    logging.info("Finnished Tika server")


if __name__ == "__main__":
    main()
