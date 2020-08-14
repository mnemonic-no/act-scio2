#!/usr/bin/env python3
"""Copyright 2019,2020 mnemonic AS <opensource@mnemonic.no>

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
Program to check the feed output directory of feed_downloader.py
Any downloaded content not found in the cache is handled.
The .meta files associated with the .html files from the feed download is
kept to preserve information about source and original titles as well as
feed time and date stamps.
This files builds a document understood by SCIOs 'doc' work queue.
This utility is not meant to handle the files downloaded from links _in_ the
feed as these document does not share any of the meta-data associated with
the feed entries. These files need to be handled separately (using SCIOs own
submit utility.
"""

import logging
import sqlite3

from typing import (
    Dict,
    List,
    Text,
)


class Cache:
    """Cache handles the caching database logic"""

    def __init__(self, filename: Text = "upload.sqlite"):
        """Initiate database, creating connection to file"""

        logging.info("Connecting to %s", filename)
        self.conn = sqlite3.connect(filename)
        try:
            # create table if it does not exsit
            self.conn.execute("""CREATE TABLE upload (
                                              id integer PRIMARY KEY,
                                              filename text NOT NULL,
                                              sha256 text NOT NULL,
                                              description text);
                              """)
        except sqlite3.OperationalError:
            pass

    def contains(self, sha256: Text) -> bool:
        """Check if a particular digest is allready uploaded. Returns
        True/False"""

        sql = "SELECT * FROM upload WHERE sha256 = ?"

        cur = self.conn.execute(sql, (sha256,))

        if cur.fetchall():
            logging.debug("Query for %s returns True", sha256)
            return True

        logging.debug("Query for %s returns False", sha256)
        return False

    def insert(self, filename: Text, sha256: Text, description: Text = "") -> None:
        """insert a new file in the metadata cache"""

        sql = "INSERT INTO upload(filename, sha256, description) VALUES(?,?,?)"
        logging.debug("Inserting %s, %s, %s into database",
                      filename, sha256, description)
        self.conn.execute(sql, (filename, sha256, description))
        self.conn.commit()

    def info(self, sha256: Text) -> List[Dict]:
        """Get stored info about a digest. Returns a list of Dictionaries"""

        sql = "SELECT filename, sha256, description FROM upload WHERE sha256 = ?" # NOQA

        cur = self.conn.execute(sql, (sha256,))

        results = cur.fetchall()
        logging.debug("Found %d resultsults for %s", len(results), sha256)

        result_dictionaries = []

        for result in results:
            key_value_pairs = list(zip(["filename", "sha256", "description"],
                                       result))
            result_dictionaries.append(dict(key_value_pairs))

        return result_dictionaries
