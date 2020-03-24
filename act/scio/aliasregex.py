#!/usr/bin/env python3
"""
This module contains function to convert an alias config file an/or an alias into
regular expressions for matching purposes"""

from typing import Set, Text
import re
import sys


def alias_set_from_config(config_file_name: Text) -> Set[Text]:
    """Read and parse a alias config file, add all aliases to a flat set"""

    alias_set = set()
    for line in open(config_file_name):
        pri, rest = re.split(r'(?<!\\):', line, maxsplit=1)
        aliases = re.split(r'(?<!\\),', rest)
        aliases.append(pri)
        aliases = [alias.strip() for alias in aliases if alias.strip() != '']
        for alias in aliases:
            alias_set.add(alias)
    return alias_set


def regex_from_alias(alias: Text) -> Text:
    """convert a alias to a more general form using regex. All "breaks" in the
    alias (camlecase, numbers, underscores etc) is allowed to be "as is", a set
    of whitespace (one or more) and also -_/. to allow for different
    conventions in writing aliases"""

    def camel_case_break(alias: Text, i: int) -> bool:
        """Detect transistion from lower case to uppper case"""

        if i < 0:
            raise ValueError("Negative index not allowed")
        if i == 0:
            return False
        if not alias[i].isupper():
            return False
        if not alias[i - 1].islower():
            return False
        return True

    def alpha_to_digit_break(alias: Text, i: int) -> bool:
        """Detect transistion from letters to digist"""

        if i < 0:
            raise ValueError("Negative index not allowed")
        if i == 0:
            return False
        if not alias[i].isdigit():
            return False
        if not alias[i - 1].isalpha():
            return False
        return True

    tmp_re: Text = r"\b("  # start with word boundry
    for i, c in enumerate(alias):
        # transistions from lower to upper case and from letter to number may
        # also be written with a space.
        if camel_case_break(alias, i) or alpha_to_digit_break(alias, i):
            tmp_re += r"\s?[- _.]?"
        # Any space may or may not be there in text (som concat and use lower
        # to upper)
        if c.isspace():
            tmp_re += r"\s?[- _.]?"
        elif c.isdigit():
            tmp_re += r"\d"
        else:
            tmp_re += c.lower()

    tmp_re += r")\b"

    return tmp_re


def normalize(name: Text) -> Text:
    """
    Return normalized version of name:
    - Space inserted between alphanumeric characters and digits
    - Space inserted between lowercase and upperchase characters
    - Characters other than alphanumeric, digits and space are changed to space
    """

    # Replace "APT27" with "APT 27"
    name = re.sub(r"([A-Za-z])(\d)", r"\1 \2", name)

    # Replace "winntiGroup" with "winnti group"
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

    # Replace "APT-27" with "APT 27"
    name = re.sub(r"[^a-zA-Z0-9 ]+", " ", name, 0)

    # Replace multiple whitespaces with a single whitespace
    name = re.sub(r"\s{2,}", " ", name)

    return name.lower()


def get_reg_ex_set(config_file_name: Text) -> Set[Text]:
    """Helper function to take a config file, parse it and create regular
    expressions from the aliases contained within. The aliases is returned in
    a set og regex strings"""

    regex_set = set()

    alias_set = alias_set_from_config(config_file_name)
    for alias in alias_set:
        if alias.isdigit():
            sys.stderr.write(f"WARNING: Unable to create regex from all digit alais {alias}\n")
            continue
        regex_set.add(regex_from_alias(alias))

    return regex_set


if __name__ == '__main__':
    for regex in sorted(list(get_reg_ex_set("aliases.cfg"))):
        print(regex)
