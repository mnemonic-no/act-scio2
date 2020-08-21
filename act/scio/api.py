""" SCIO API """

import argparse
import base64
import gzip
import logging
import os
from functools import lru_cache
from typing import Dict, Optional, Text

import caep
import greenstalk  # type: ignore
import uvicorn
from fastapi import Depends, FastAPI, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, StrictInt, StrictStr
from pydantic.types import constr

import act.scio.config

STORAGEDIR = "/tmp"

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
    count: StrictInt
    error: Optional[StrictStr]


@lru_cache()
def parse_args() -> argparse.Namespace:
    """Helper setting up the argsparse configuration"""

    arg_parser = act.scio.config.parse_args("Scio API")
    arg_parser.add_argument('--port', type=int, default=3000,
                            help="API port to listen on (default=3000)")
    arg_parser.add_argument('--reload', action="store_true",
                            help="Reload web server on file change (dev mode)")
    arg_parser.add_argument('--host', dest='host', default='127.0.0.1',
                            help="Host interface (default=127.0.0.1)")

    args = caep.config.handle_args(arg_parser, "scio/etc", "scio.ini", "api")

    args.beanstalk_client = None
    if args.beanstalk:
        logging.info("Connection to beanstalk")
        args.beanstalk_client = greenstalk.Client(
            args.beanstalk, args.beanstalk_port, encoding=None)
        args.beanstalk_client.use('scio_doc')

    return args


def document_lookup(document_id: Text) -> LookupResponse:
    """ Lookup document location and content type from document_id (hexdigest) """

    document_id = document_id.lower()

    # TODO - ES-lookup
    filename = "/tmp/ClearSky-Fox-Kitten-Campaign.pdf"
    content_type = "application/pdf"

    return LookupResponse(
        filename=filename,
        content_type=content_type
    )


@app.post("/submit")
async def submit(doc: Document, args: argparse.Namespace = Depends(parse_args)):
    """ Submit document """
    filename = os.path.join(STORAGEDIR, os.path.basename(doc.filename))
    content: bytes = base64.b64decode(doc.content)
    with open(filename, "bw") as f:
        f.write(content)

    response = SubmitResponse(
        filename=filename,
        count=len(doc.content),
        error=None)

    args.beanstalk_client.put(response.json().encode("utf8"))
    return response


@app.get("/download/{document_id}")
def download(document_id: constr(regex=r"^[0-9A-Fa-f]{64}$")) -> Response:
    """ Download document as original content"""
    res = document_lookup(document_id)

    if not os.path.isfile(res.filename):
        return Response(content="File not found", media_type="application/text")

    return FileResponse(
        res.filename,
        filename=os.path.basename(res.filename),
        media_type=res.content_type)


@app.get("/download_json/{document_id}")
def download_json(document_id: constr(regex=r"^[0-9A-Fa-f]{64}$")) -> Response:
    """ Download document base64 decoded in json struct """
    res = document_lookup(document_id)

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


def main():
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
