"""All functions related to scio upload"""

from typing import IO, Text, Dict

import base64

import requests


def read_as_base64(obj: IO) -> Text:
    """Create a base64 encoded string from a file like object"""

    encoded_bytes = base64.b64encode(obj.read())
    return encoded_bytes.decode('ascii')


def to_scio_submit_post_data(obj: IO, file_name: Text) -> Dict[Text, Text]:
    """Take a file like object, and return a dictionary on the correct form for
    submitting to the SCIO API (https://github.com/mnemonic-no/act-scio-api)"""

    return {'content': read_as_base64(obj), 'filename': file_name}


def upload(url: Text, filename: Text) -> None:
    """Upload a file to the Scio engine"""

    with open(filename, "rb") as file_h:
        post_data = to_scio_submit_post_data(file_h, filename)

        # Disable all proxy settings from environment
        session = requests.Session()
        session.trust_env = False

        req = session.post(url, json=post_data)
        if req.status_code != 200:
            raise UploadError("Status {0}".format(req.status_code))


class UploadError(Exception):
    """Wrap all errors related to uploading data to scio"""
