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


def normalize(name: Text,
        space_before_numbers=True,
        space_before_capitalized=True,
        remove_non_alphanumeric=True,
        remove_multiple_whitespace=True,
        lower=True,
        upper=False,
        capitalize=False,
        uppercase_abbr=None,
        ) -> str:
    """

    Args:
    space_before_numbers (bool): insert space before numbers
    space_beofre_capitalized (bool): insert space before capitalized letters
    remove_non_alphanumeric (bool): remove charactes except alphanumer and space
    remove_multiple_whitespace (bool): replace multiple whitespace with a single space
    lower (bool): lowercase
    upper (bool): uppercase
    capitalize (bool): uppercase all first characters in words
    uppercase_abbr (list[str]): list of abbrevations to uppercase

    The transformation in ran in the same order as the arguments are specified,
    so you can use lower=True and capitalize=True to transform sOmeThing -> Something
    """

    if not uppercase_abbr:
        uppercase_abbr = []

    if space_before_numbers:
        # Replace "APT27" with "APT 27"
        name = re.sub(r"([A-Za-z])(\d)", r"\1 \2", name)

    if space_before_capitalized:
        # Replace "winntiGroup" with "winnti group"
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

    if remove_non_alphanumeric:
        # Replace "APT-27" with "APT 27"
        name = re.sub(r"[^a-zA-Z0-9 ]+", " ", name, 0)

    if remove_multiple_whitespace:
        # Replace multiple whitespaces with a single whitespace
        name = re.sub(r"\s{2,}", " ", name)

    if lower:
        name = name.lower()

    if upper:
        name = name.upper()

    if capitalize:
        # https://stackoverflow.com/questions/6251463/regex-capitalize-first-letter-every-word-also-after-a-special-character-like-a
        name = re.sub(r'(((?<=\s)|^|-)[a-z])', lambda x: x.group().upper(), name)

    for abbr in uppercase_abbr:
        name = re.sub(abbr, abbr.upper(), name, 0, re.IGNORECASE)

    return name


def get_reg_ex_set(config_file_name: Text) -> Set[Text]:
    """Helper function to take a config file, parse it and create regular
    expressions from the aliases contained within. The aliases is returned in
    a set og regex strings"""

    regex_set = set()

    alias_set = alias_set_from_config(config_file_name)
    for alias in alias_set:
        if alias.isdigit():
            sys.stderr.write(f"WARNING: Unable to create regex from all digit alias {alias}\n")
            continue
        regex_set.add(regex_from_alias(alias))

    return regex_set


if __name__ == '__main__':
    for regex in sorted(list(get_reg_ex_set("aliases.cfg"))):
        print(regex)
