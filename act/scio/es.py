from typing import Optional, Text, Tuple

import elasticsearch
from elasticsearch import Elasticsearch


def es_client(
        host: Text,
        port: int = 9200,
        url_prefix: Optional[Text] = None,
        username: Optional[Text] = None,
        password: Optional[Text] = None,
        timeout: int = 180) -> elasticsearch.client.Elasticsearch:
    """ Elasticsearch client """

    connection = {
        "host": host,
        "port": port
    }

    if url_prefix:
        connection["url_prefx"] = url_prefix

    if username or password:
        http_auth: Optional[Tuple[Optional[Text], Optional[Text]]] = (username, password)
    else:
        http_auth = None

    return Elasticsearch([connection], timeout=timeout, http_auth=http_auth)
