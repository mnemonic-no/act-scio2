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
from typing import Dict, Optional, Text, Union

import act.scio.config
import act.scio.es
import caep
import elasticsearch
import greenstalk  # type: ignore
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, StrictInt, StrictStr
from pydantic.types import constr

XDG_CACHE = os.path.expanduser(os.environ.get("XDG_CACHE_HOME", "~/.cache"))

app = FastAPI()

# pylint: disable=too-few-public-methods


class Document(BaseModel):
    """ Document model """
    content: StrictStr
    filename: StrictStr


class LookupResponse(BaseModel):
    """ Response model for document search """
    filename: StrictStr
    content_type: StrictStr


class SubmitResponse(BaseModel):
    """ Response model for document submit """
    filename: StrictStr
    hexdigest: StrictStr
    count: StrictInt
    error: Optional[StrictStr]


# parse_args() is executed the first time and later the cached result
# is used. In this way, we use to configure settings in API endpoints
@lru_cache()
def parse_args() -> argparse.Namespace:
    """Helper setting up the argsparse configuration"""

    arg_parser = act.scio.config.parse_args("Scio API")
    arg_parser.add_argument('--port', type=int, default=3000,
                            help="API port to listen on (default=3000)")
    arg_parser.add_argument('--reload', action="store_true",
                            help="Reload web server on file change (dev mode)")
    arg_parser.add_argument('--document-path', default=caep.get_cache_dir("scio/documents"),
                            help=f"Storage path for documents = {XDG_CACHE}/scio/documents")
    arg_parser.add_argument('--host', dest='host', default='127.0.0.1',
                            help="Host interface (default=127.0.0.1)")

    args = caep.config.handle_args(arg_parser, "scio/etc", "scio.ini", "api")

    if not os.path.isdir(args.document_path):
        os.makedirs(args.document_path)
        logging.info("Created directory: %s", args.document_path)

    args.beanstalk_client = act.scio.config.beanstalk_client(args, use="scio_doc")
    args.elasticsearch_client = act.scio.config.elasticsearch_client(args)

    return args


def document_lookup(document_id: Text,
                    elasticsearch_client: elasticsearch.client.Elasticsearch) -> LookupResponse:
    """ Lookup document location and content type from document_id (hexdigest) """

    filename: Text = ""
    content_type: Text = ""

    try:
        res = elasticsearch_client.get(index="scio2", id=document_id.lower())
        filename = res["_source"].get("filename")
        content_type = res["_source"].get("metadata", {}).get("Content-Type")
    except elasticsearch.exceptions.NotFoundError:
        pass

    return LookupResponse(
        filename=filename,
        content_type=content_type
    )


@app.post("/submit")
async def submit(doc: Document, args: argparse.Namespace = Depends(parse_args)) -> SubmitResponse:
    # Depends on parse_args which are used for settings. The result
    # is cached the first time it is executed
    """ Submit document """
    filename = os.path.join(args.document_path, os.path.basename(doc.filename))
    content: bytes = base64.b64decode(doc.content)
    with open(filename, "bw") as f:
        f.write(content)

    response = SubmitResponse(
        filename=filename,
        hexdigest=hashlib.sha256(content).hexdigest(),
        count=len(content),
        error=None)

    args.beanstalk_client.put(response.json().encode("utf8"))
    return response


@ app.get("/indicators/{indicator_type}", response_class=PlainTextResponse)
def indicators(indicator_type: constr(regex=r"^(ipv4|ipv6|uri|email|fqdn|md5|sha1|sha256)$"),
             last: constr(regex=r'^\d+[yMwdhms]?$') = "90d",
             args: argparse.Namespace = Depends(parse_args)) -> PlainTextResponse:
    """ Download indicators

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
    format should be either be <NUM><TIME UNIT>, where TIME UNIT can be one of:

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

    if re.search(r"^\d+$", last):
        # Only digits - assume unix timestamp
        start = last
    else:
        start = f"now-{last}"

    term = f"indicators.{indicator_type}.keyword"

    res = act.scio.es.aggregation(
        args.elasticsearch_client,
        terms=[term],
        start=start,
        end="now",
    )

    return PlainTextResponse(
            "\n".join(row[0].get(term) for row in res)
    )


@ app.get("/download")
def download(id: constr(regex=r"^[0-9A-Fa-f]{64}$"),
             args: argparse.Namespace = Depends(parse_args)) -> Response:
    """ Download document as original content"""
    res = document_lookup(id, args.elasticsearch_client)

    if not os.path.isfile(res.filename):
        return Response(content="File not found", media_type="application/text")

    return FileResponse(
        res.filename,
        filename=os.path.basename(res.filename),
        media_type=res.content_type)


@ app.get("/download_json")
def download_json(id: constr(regex=r"^[0-9A-Fa-f]{64}$"),
                  args: argparse.Namespace = Depends(parse_args)) -> Union[Response, Dict]:
    """ Download document base64 decoded in json struct """
    res = document_lookup(id, args.elasticsearch_client)

    if not os.path.isfile(res.filename):
        return {
            "error": "File not found",
            "bytes": 0,
        }

    content = open(res.filename, "rb").read()

    return {
        "error": None,
        "bytes": len(content),
        "content": base64.b64encode(content),
        "encoding": "base64"
    }


def main() -> None:
    """ Main API loop """
    args = parse_args()

    uvicorn.run(
        "act.scio.api:app",
        host=args.host,
        port=args.port,
        log_level="info",
        reload=args.reload)


if __name__ == "__main__":
    main()
