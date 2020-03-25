"""
    Support for vocularies with support for
    - aliases
    - automatic generate regular expression from aliases
    - NLP stemming
"""


import configparser
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Pattern, Union

from logging import info

import nltk  # type: ignore

from act.scio.alias import parse_aliases
import addict
import act.scio.aliasregex as aliasregex

DEFAULT_CONFIG = addict.Dict({
    "alias": None,
    "default": None,
    "regexfromalias": False,
    "primary": False,
    "key_mod": "lower",
    "regexmanual": "",
    "object_type": None
})


def identity(x: Any) -> Any:
    """ Identity function. Used as default to return same value as input """
    return x


def from_config(config_filename: str) -> addict.Dict:
    """
    Load vocabularies from config and return Dict
    with vocabulary-name as key and Vocabulary as value
    """
    cparser = configparser.ConfigParser()
    cparser.read(str(config_filename))

    vocabularies = addict.Dict()

    for vocabulary_name in cparser.sections():
        section = cparser[vocabulary_name]

        # Config
        config = addict.Dict()
        config.alias = section.get("alias", DEFAULT_CONFIG.alias)
        config.default = section.get("default", DEFAULT_CONFIG.default)
        config.regexfromalias = section.getboolean("regexfromalias")
        config.primary = section.getboolean("primary")
        config.key_mod = section.get("key_mod", DEFAULT_CONFIG.key_mod)
        config.regexmanual = section.get("regexmanual", DEFAULT_CONFIG.regexmanual)
        config.object_type = section.get("object_type", DEFAULT_CONFIG.object_type)
        vocabularies[vocabulary_name] = Vocabulary(config)

    return vocabularies


class IllegalVocabularyKeyType(Exception):
    """Non existing Vocabulary Key Type"""

    pass


class Vocabulary:
    """
        Support for vocularies with support for
        - aliases
        - automatic generate regular expression from aliases
        - NLP stemming
    """

    def __init__(self, config: Union[addict.Dict, Dict, configparser.SectionProxy]) -> None:
        """
        Args:
            config (addict.Dict):  addict.Dict with the following keys
                    * alias (str)            # Config filw with aliases
                    * primary (bool)         # Point aliases to primary name
                    * default (bool)         # Default value for if key does not exist
                    * regexfromalias (bool)  # Create regex from aliases?
                    * primary (bool)         # Use primary name as default return value
                    * key_mod (str)          # Default key_mod (default = "lower")
                    * regexmanual (str[])    # Extra regular expressions for regex search
                    * object_type (str)      # ACT object type applicable for this vocabulary
        """
        self.config = addict.Dict(DEFAULT_CONFIG)
        self.config.update(config)
        self.regex: List[Pattern] = []
        self.vocab: Dict[str, Dict[str, addict.Dict]] = addict.Dict(
            none=addict.Dict(),
            lower=addict.Dict(),
            stem=addict.Dict(),
            norm=addict.Dict()
        )

        self.stemmer = nltk.stem.PorterStemmer().stem

        if self.config.alias:
            self.load_alias(self.config.alias)  # type: ignore

        if self.config.regexmanual:
            self.regex = [re.compile(entry.strip(), re.I)
                          for entry in self.config.regexmanual.split("\n") if entry.strip()]
        else:
            self.regex = []

        if self.config.regexfromalias:
            for aliasre in aliasregex.get_reg_ex_set(self.config.alias):
                try:
                    self.regex.append(re.compile(aliasre, re.IGNORECASE))
                except re.error:
                    sys.stderr.write(f"ERROR in regex {aliasre}\n")
                    raise

    def load_alias(self, filename: str) -> None:
        """
        Load aliases from file.

        Args:
            filename (str): Filename to read aliases from
        """
        with open(filename, "r") as f:

            for line in f.readlines():
                # Remove comments (starting with '#'), unless they are escaped
                line = re.sub(r"(?<!\\)#.*", "", line)

                if not line.strip():
                    continue  # Skip empty lines

                # Get key and aliases
                primary, aliases = parse_aliases(line)

                for name in [primary] + aliases:
                    # Stor a separate entry for each type of key_mod
                    # For each entry, also store the value itself and the
                    # primary name

                    self.vocab["none"][name] = addict.Dict(value=name, primary=primary)
                    self.vocab["lower"][name.lower()] = addict.Dict(value=name, primary=primary)
                    self.vocab["stem"][self.stemmer(name)] = addict.Dict(value=name, primary=primary)

                    self.vocab["norm"][aliasregex.normalize(name)] = addict.Dict(
                        value=name,
                        primary=primary)

    def __getitem__(self, key: str) -> Optional[str]:
        """
        Return entry from vocabulary.
        """

        return self.get(key)

    def regex_search(self,
                     text,
                     key_mod: str = "DEFAULT",
                     normalize_result: Callable = identity,
                     debug: bool = False) -> List[str]:
        """
        Find all matches in vocabulary from regex search

        Args:
            text (str):       Input text
            key_mod (text):   Lookup using modifie key
        """

        key_mod = self.get_key_mod(key_mod)

        result = []
        for regex in self.regex:
            for match in regex.findall(text):
                if debug:
                    logging.info("%s found by regex %s", match, regex)
                result.append(normalize_result(match))

        return result

    def get_key_mod(self, key_mod: Optional[str]) -> str:
        """ Verify and get key_mod """

        # Get key modifier from config
        if key_mod == "DEFAULT":
            key_mod = self.config.key_mod

        elif key_mod is None:  # Use "none" modifier (the value itself)
            key_mod = "none"

        if key_mod not in self.vocab:
            raise IllegalVocabularyKeyType("Illegal key: {}".format(key_mod))
        return key_mod

    def get(self, key: str, key_mod: str = "DEFAULT", primary: Optional[bool] = None,
            default: Optional[str] = None) -> Optional[str]:
        """
        Search for entry in vocabulary

        Args:
            key (str):           Key to search for
            key_mod (str):       Key modifier ("lower", "stem" or "none"). If not set,
                                 use default value form self.config.key_mod.
            primary (bool|None): If True, return primary name, if not return the
                                 value itself from the vocabulary
            default (str|None):  Default value if key is not found. Default == None
        """

        key_mod = self.get_key_mod(key_mod)

        # If primary is not set, get from config whether we should retrieve the primary name
        if primary is None:
            primary = self.config.primary

        # If default is None, get default value from config
        if default is None:
            default = self.config.default

        if key_mod == "stem":
            key = self.stemmer(key)
        elif key_mod == "lower":
            key = key.lower()
        elif key_mod == "norm":
            key = aliasregex.normalize(key)

        value = self.vocab[key_mod].get(key)

        if not value:
            return default

        if primary:  # Return primary value
            return value.primary  # type: ignore

        # Return value ifself
        return value.value  # type: ignore
