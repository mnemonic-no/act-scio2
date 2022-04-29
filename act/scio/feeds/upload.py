"""All functions related to scio upload"""

import base64
import time
from logging import error, warning
from typing import IO, Dict, Text

import requests


def read_as_base64(obj: IO[bytes]) -> Text:
    """Create a base64 encoded string from a file like object"""

    encoded_bytes = base64.b64encode(obj.read())
    return encoded_bytes.decode("ascii")


def to_scio_submit_post_data(
    obj: IO[bytes], filemap: Dict[Text, Text], tlp: Text
) -> Dict[Text, Text]:
    """Take a file like object, and return a dictionary on the correct form for
    submitting to the SCIO API (https://github.com/mnemonic-no/act-scio-api)"""

    metadata = filemap.copy()
    metadata["content"] = read_as_base64(obj)
    metadata["tlp"] = tlp

    assert "content" in metadata
    assert "filename" in metadata
    assert "uri" in metadata
    assert "tlp" in metadata

    return metadata


def upload(url: Text, filemap: Dict[Text, Text], tlp: Text) -> None:
    """Upload a file to the Scio engine"""

    retry_codes = [429, None]

    with open(filemap["filename"], "rb") as file_h:
        post_data = to_scio_submit_post_data(file_h, filemap, tlp)

        # Disable all proxy settings from environment
        session = requests.Session()
        session.trust_env = False

        status_code = None
        while status_code in retry_codes:
            started = time.time()
            try:
                req = session.post(url, json=post_data)
            except requests.exceptions.ConnectionError as e:
                msg = (
                    f"Failed to upload to {url}. Time since upload started: "
                    + f"{time.time() - started} seconds. "
                    + f"Exception: {e}. post_data[filename]={post_data['filename']}, "
                    + f"post_data[uri]={post_data['uri']}"
                )
                error(msg)
                raise UploadError(msg)

            status_code = req.status_code

            if status_code not in retry_codes and status_code != 200:
                raise UploadError("Status {0}".format(req.status_code))

            if status_code in retry_codes:
                warning("%s: %s", status_code, req.text)
                time.sleep(1)


class UploadError(Exception):
    """Wrap all errors related to uploading data to scio"""
