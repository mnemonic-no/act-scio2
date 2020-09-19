from typing import List, Dict, Optional, Tuple, Text


def noun_frase(token_tags: List[Tuple[Text, Text]],
               idx: int) -> Tuple[int, Optional[List]]:
    """Check if a noun frase starts at this index, and if so
    returns the frase and the idx of the first element _after_
    the frase"""

    if idx >= len(token_tags):
        return idx, None
    col = []
    for token, tag in token_tags[idx:]:
        if tag.startswith("N") or tag == "DT" or tag == "JJ":
            col.append((token, tag))
            idx += 1
        else:
            if not col:
                return idx, None
            return idx, col
    return idx, col


def find_ttype(token_tags, idx, types, reverse=False):
    """Generalized search for token tags, return idx and
    token_tag if found, else idx and None"""

    if idx < 0 or idx >= len(token_tags):
        return idx, None
    stop = -1 if reverse else len(token_tags)
    step = -1 if reverse else 1
    for i in range(idx, stop, step):
        if token_tags[i][1] in types:
            return i, token_tags[i]
    return (0, None) if reverse else (len(token_tags), None)


def next_cc(token_tags, idx):
    """Search for next connecting words (AND, OR, ...)

, last_idx    return (idx, (token, tag))
    return (idx, None) if not found"""

    return find_ttype(token_tags, idx, ["CC"])


connectors = [",", ";"]


def next_connector(token_tags, idx):
    """Find next connector from an index. If there is a connector _at_
    the current index, this will be returned.

    returns (idx, (token, tag))"""

    return find_ttype(token_tags, idx, connectors)


def prev_connector(token_tags, idx):
    """Find previous connector from an index. If there is a connector
    _at_ the current index, this will be returned.

    return (idx, (token, tag))"""

    return find_ttype(token_tags, idx, connectors, reverse=True)


def find_noun_frase_list(token_tags: List[Tuple[Text, Text]],
                         idx: int) -> Tuple[int, Optional[List]]:
    """Find the next list of noun frases.

    returns {idx of first element after last frase}, [[(token, tag), ....], ...]"""

    if idx < 0 or idx >= len(token_tags):
        return idx, None

    mylist = []
    cc_idx, _ = next_cc(token_tags, idx)

    last_idx, nf = noun_frase(token_tags, cc_idx + 1)

    if not nf:
        return find_noun_frase_list(token_tags, cc_idx + 1)

    mylist.append(nf)

    idx = cc_idx
    while True:
        idx, con = prev_connector(token_tags, idx - 1)
        if con:
            _, nf = noun_frase(token_tags, idx + 1)
            if nf:
                mylist.insert(0, nf)
            else:
                return last_idx, mylist
        elif idx == 0:
            _, nf = noun_frase(token_tags, 0)
            if nf:
                mylist.insert(0, nf)
            else:
                return last_idx, mylist
        else:
            return last_idx, mylist
