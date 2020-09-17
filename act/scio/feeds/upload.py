"""All functions related to scio upload"""

from typing import IO, Text, Dict
from logging import warning

import base64
import time

import requests


def read_as_base64(obj: IO) -> Text:
    """Create a base64 encoded string from a file like object"""

    encoded_bytes = base64.b64encode(obj.read())
    return encoded_bytes.decode('ascii')


def to_scio_submit_post_data(obj: IO, filemap: Dict) -> Dict[Text, Text]:
    """Take a file like object, and return a dictionary on the correct form for
    submitting to the SCIO API (https://github.com/mnemonic-no/act-scio-api)"""

    metadata = filemap.copy()
    metadata['content'] = read_as_base64(obj)

    assert 'content' in metadata
    assert 'filename' in metadata
    assert 'uri' in metadata

    return metadata


def upload(url: Text, filemap: Dict) -> None:
    """Upload a file to the Scio engine"""

    retry_codes = [429, None]

    with open(filemap['filename'], "rb") as file_h:
        post_data = to_scio_submit_post_data(file_h, filemap)

        # Disable all proxy settings from environment
        session = requests.Session()
        session.trust_env = False

        status_code = None
        while status_code in retry_codes:
            req = session.post(url, json=post_data)
            status_code = req.status_code

            if status_code not in retry_codes and status_code != 200:
                raise UploadError("Status {0}".format(req.status_code))

            if status_code in retry_codes:
                warning("%s: %s", status_code, req.text)
                time.sleep(1)


class UploadError(Exception):
    """Wrap all errors related to uploading data to scio"""
