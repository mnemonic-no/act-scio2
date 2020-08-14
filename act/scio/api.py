""" SCIO API """

import argparse
import base64
import os
from typing import Dict, Text

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, StrictStr
from pydantic.types import constr

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


def parse_args() -> argparse.Namespace:
    """ Parse arguments """
    parser = argparse.ArgumentParser(description="SCIO API")

    parser.add_argument('--port', type=int, default=3000,
                        help="API port to listen on (default=3000)")
    parser.add_argument('--reload', action="store_true",
                        help="Reload web server on file change (dev mode)")
    parser.add_argument('--host', dest='host', default='127.0.0.1',
                        help="Host interface (default=127.0.0.1)")

    return parser.parse_args()


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
async def submit(doc: Document):
    """ Submit document """
    filename = os.path.join(STORAGEDIR, os.path.basename(doc.filename))
    content: bytes = base64.b64decode(doc.content)
    with open(filename, "bw") as f:
        f.write(content)

    # TODO -> to beanstalk

    return {
        "filename": filename,
        "bytes": len(doc.content)
    }


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
