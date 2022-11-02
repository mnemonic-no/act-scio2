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
SCIO API
"""

import argparse
import base64
import hashlib
import logging
import os
import re
from functools import lru_cache
from pathlib import Path, PurePath
from typing import Dict, List, Text, Union, cast

import caep
import elasticsearch
import greenstalk
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import ConstrainedStr

import act.scio.config
import act.scio.es
from act.scio.models import Document, LookupResponse, SubmitResponse

XDG_CACHE = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()

app = FastAPI()

# pylint: disable=too-few-public-methods


class IndicatorTypeRegex(ConstrainedStr):
    regex = re.compile(r"^(ipv4|ipv6|uri|email|fqdn|md5|sha1|sha256)$")


class PeriodRegex(ConstrainedStr):
    regex = re.compile(r"^\d+[yMwdhms]?$")


class SHA256Regex(ConstrainedStr):
    regex = re.compile(r"^[0-9A-Fa-f]{64}$")


def max_current_jobs_ready(client: greenstalk.Client, tubes: List[Text]) -> int:
    """Get max current-jobs-ready from tubes specified"""
    max_jobs = 0
    for tube in tubes:
        # We need to check for the existense of a beanstalk tube
        # to avoid "NOT_FOUND" exceptions in the case where the tubes
        # are empty before first init
        if tube not in client.tubes():
            continue
        stats = client.stats_tube(tube)

        if stats:
            max_jobs = max(max_jobs, stats.get("current-jobs-ready", 0))

    return max_jobs


def create_path_if_not_exists(path: Path) -> None:
    if not path.is_dir():
        path.mkdir()
        logging.info("Created directory: %s", path)


# parse_args() is executed the first time and later the cached result
# is used. In this way, we use to configure settings in API endpoints
@lru_cache()
def parse_args() -> argparse.Namespace:
    """Helper setting up the argsparse configuration"""

    arg_parser = act.scio.config.parse_args("Scio API")
    arg_parser.add_argument(
        "--port", type=int, default=3000, help="API port to listen on (default=3000)"
    )
    arg_parser.add_argument(
        "--max-jobs",
        type=int,
        default=10,
        help="Max jobs in queue before submit responds " + "with backpressure (429)",
    )
    arg_parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload web server on file change (dev mode)",
    )
    arg_parser.add_argument(
        "--document-path",
        default=caep.get_cache_dir("scio/documents"),
        type=Path,
        help=f"Storage path for documents = {XDG_CACHE}/scio/documents",
    )
    arg_parser.add_argument(
        "--host",
        dest="host",
        default="127.0.0.1",
        help="Host interface (default=127.0.0.1)",
    )

    args = caep.config.handle_args(arg_parser, "scio/etc", "scio.ini", "api")

    nostore_path = args.document_path / "NOSTORE"

    create_path_if_not_exists(args.document_path)
    create_path_if_not_exists(nostore_path)

    args.beanstalk_client = act.scio.config.beanstalk_client(args, use="scio_doc")
    args.elasticsearch_client = act.scio.config.elasticsearch_client(args)

    return args  # type: ignore


def document_lookup(
    document_id: Text, elasticsearch_client: elasticsearch.Elasticsearch
) -> LookupResponse:
    """Lookup document location and content type from document_id (hexdigest)"""

    filename: Text = ""
    content_type: Text = ""

    try:
        res = elasticsearch_client.get(index="scio2", id=document_id.lower())
        filename = res["_source"].get("filename")
        content_type = res["_source"].get("metadata", {}).get("Content-Type")
    except elasticsearch.exceptions.NotFoundError:
        pass

    return LookupResponse(filename=filename, content_type=content_type)


@app.post("/submit")  # type: ignore
async def submit(
    doc: Document, args: argparse.Namespace = Depends(parse_args)
) -> SubmitResponse:
    # Depends on parse_args which are used for settings. The result
    # is cached the first time it is executed
    """Submit document"""

    max_jobs = max_current_jobs_ready(
        args.beanstalk_client, ["scio_doc", "scio_analyze"]
    )

    if max_jobs >= args.max_jobs:
        logging.warning("%s jobs in queue", max_jobs)
        raise HTTPException(
            status_code=429, detail="To many jobs in queue, try again later"
        )

    path = args.document_path if doc.store else args.document_path / "NOSTORE"

    filename = path / PurePath(doc.filename).name
    content: bytes = base64.b64decode(doc.content)
    with open(filename, "bw") as f:
        f.write(content)

    response = SubmitResponse(
        filename=str(filename),
        hexdigest=hashlib.sha256(content).hexdigest(),
        count=len(content),
        tlp=doc.tlp,
        error=None,
        uri=doc.uri,
        store=doc.store,
        owner=doc.owner,
    )

    args.beanstalk_client.put(response.json().encode("utf8"))
    return response


@app.get("/indicators/{indicator_type}", response_class=PlainTextResponse)  # type: ignore
def indicators(
    indicator_type: IndicatorTypeRegex,
    last: PeriodRegex,
    args: argparse.Namespace = Depends(parse_args),
) -> PlainTextResponse:
    """Download indicators

    Allowed indicator types:
    * ipv4
    * ipv6
    * uri
    * email
    * fqdn
    * md5
    * sha1
    * sha256

    You can also specify the maximum age of the document you want to
    get indicators from with the `last` argument (default=90d). The
    format should be either <NUM><TIME UNIT>, where TIME UNIT can be one of:

    y (year)
    M (month)
    w (week)
    d (day)
    h (hour)
    m (minute)
    s (second)

    OR <EPOC> (only digits) where the EPOC is a unix timestamp in milliseconds

    """

    if not args.elasticsearch_client:
        raise HTTPException(status_code=412, detail="Elasticsearch is not configured")

    if re.search(r"^\d+$", cast(Text, last)):
        # Only digits - assume unix timestamp
        start = last
    else:
        start = f"now-{last}"  # type: ignore

    term = f"indicators.{indicator_type}.keyword"

    res = act.scio.es.aggregation(
        args.elasticsearch_client,
        term=term,
        start=start,
        end="now",
    )

    return PlainTextResponse("\n".join(row[0] for row in res))


@app.get("/download")  # type: ignore
def download(
    id: SHA256Regex,
    args: argparse.Namespace = Depends(parse_args),
) -> Response:
    """Download document as original content"""
    res = document_lookup(id, args.elasticsearch_client)

    if not Path(res.filename).is_file():
        return Response(content="File not found", media_type="application/text")

    return FileResponse(
        res.filename,
        filename=PurePath(res.filename).name,
        media_type=res.content_type,
    )


@app.get("/download_json")  # type: ignore
def download_json(
    id: SHA256Regex,
    args: argparse.Namespace = Depends(parse_args),
) -> Union[Response, Dict[Text, Text]]:
    """Download document base64 decoded in json struct"""
    res = document_lookup(id, args.elasticsearch_client)

    if not Path(res.filename).is_file():
        return {
            "error": "File not found",
            "bytes": 0,
        }

    content = open(res.filename, "rb").read()

    return {
        "error": None,
        "bytes": len(content),
        "content": base64.b64encode(content),
        "encoding": "base64",
    }


def main() -> None:
    """Main API loop"""
    args = parse_args()

    uvicorn.run(
        "act.scio.api:app",
        host=args.host,
        port=args.port,
        log_level="info",
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
