"""Test the shared library for text extraction provided by scio"""

from act.scio.lib import search
import pytest


token_tags = [
    ['The', 'DT'],        # 0
    ['Noughty', 'NNP'],   # 1
    ['Noo-Noo', 'NNP'],   # 2
    ['threat', 'NN'],     # 3
    ['group', 'NN'],      # 4
    ['sucks', 'VBZ'],     # 5
    ['up', 'RP'],         # 6
    ['tubby', 'JJ'],      # 7
    ['toast', 'NN'],      # 8
    ['.', '.'],           # 9
    ['The', 'DT'],        # 10
    ['Tinky', 'NNP'],     # 11
    ['Winky', 'NNP'],     # 12
    [',', ','],           # 13
    ['Dipsy', 'NNP'],     # 14
    [',', ','],           # 15
    ['Laa-Laa', 'NNP'],   # 16
    ['and', 'CC'],        # 17
    ['Poo', 'NNP'],       # 18
    ['adversary', 'JJ'],  # 19
    ['groups', 'NNS'],    # 20
    ['looks', 'VBZ'],     # 21
    ['sketchy', 'NNS']]   # 22


@pytest.mark.asyncio
async def test_noun_phrase_search() -> None:
    """ test for plugins """

    i, nf = search.noun_frase(token_tags, 0)

    assert nf is not None
    assert i == 5  # at next element after noun frase

    i, nf = search.noun_frase(token_tags, i)
    assert nf is None
    assert i == 5

    i, nf = search.noun_frase(token_tags, 7)
    assert nf is not None
    assert i == 9

    i, nf= search.noun_frase(token_tags, 22)
    assert nf is not None
    assert i == 23

    
def test_next_cc():
    idx, token = search.next_cc(token_tags, 0)
    assert token
    assert idx == 17

    idx, token = search.next_cc(token_tags, 17)
    assert token
    assert idx == 17

    idx, token = search.next_cc(token_tags, 18)
    assert not token
    assert idx == len(token_tags)

    idx, token = search.next_cc(token_tags, 100)
    assert not token
    assert idx == 100


def test_next_connector():
    idx, token = search.next_connector(token_tags, 14)

    assert idx == 15
    assert token

def test_prev_connector():
    idx, token = search.prev_connector(token_tags, 14)
    assert idx == 13
    assert token

def test_find_list():
    idx, mylist = search.find_noun_frase_list(token_tags, 0)

    assert idx == 21
    assert len(mylist) == 4

    for e in mylist:
        i, nf = search.noun_frase(e, 0)
        assert nf
        assert i == len(e)
