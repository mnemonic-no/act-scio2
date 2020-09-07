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
Elasticsearch utilities for scio
"""

from logging import debug
from typing import Dict, Generator, List, Optional, Text, Tuple

import elasticsearch
import elasticsearch_dsl
from elasticsearch import Elasticsearch
from elasticsearch_dsl import A, Search


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


def query(client: elasticsearch.client.Elasticsearch,
          start: Text,
          end: Text,
          index: Text = "scio2",
          size: int = 100) -> Search:
    """ Return elasticsearch query """

    search = Search(using=client, index=index) \
        .extra(size=size)

    # pylint: disable=no-member
    search = search.query("range", **{
        "Analyzed-Date": {
            "gte": start,
            "lte": end,
        }})

    debug("ES-query: {}".format(search.to_dict()))

    return search


def composite_aggs(
        search: Search,
        terms: List[Text],
        size: int = 100,
        missing: bool = False) -> Generator[elasticsearch_dsl.response.aggs.Bucket,
                                            None,
                                            None]:
    """
    Helper function used to iterate over all possible bucket combinations of
    fields, using composite aggregation.
    """

    def run_search(**kwargs: Dict) -> Search:
        s = search[:0]

        s.aggs.bucket(
            'comp', 'composite',
            sources=[{field: A("terms", field=field, missing_bucket=missing)}
                     for i, field
                     in enumerate(terms)],
            size=size, **kwargs)

        return s.execute()

    response = run_search()
    while response.aggregations.comp.buckets:
        for b in response.aggregations.comp.buckets:
            yield b
        if 'after_key' in response.aggregations.comp:
            after = response.aggregations.comp.after_key
        else:
            after = response.aggregations.comp.buckets[-1].key
        response = run_search(after=after)


def aggregation(
        client: elasticsearch.client.Elasticsearch,
        terms: List[Text],
        start: Text,
        end: Text,
        missing:
        bool = False) -> Generator[Tuple, None, None]:
    """ Aggregation """
    search = query(client, start, end, size=0)

    res = composite_aggs(search, terms, missing=missing)

    for hit in res:
        path = hit.key.to_dict()

        path["path"] = "/".join(path.values())

        yield (path, hit.doc_count)
