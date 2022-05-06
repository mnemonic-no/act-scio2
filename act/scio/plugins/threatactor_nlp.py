"""Plugin for finding possible threat actors based on sentences"""

from typing import List, Set, Text

import addict
import nltk
import nltk.stem

from act.scio.plugin import BasePlugin, Result


class Plugin(BasePlugin):
    """Plugin to detect threat actors"""

    name = "nlp_actors"
    info = "Extract actors based on language from a body of text"
    version = "0.1"
    dependencies: List[Text] = ["pos_tag"]

    async def analyze(self, nlpdata: addict.Dict) -> Result:

        res = addict.Dict()

        threat_stem_postfix = {
            "threat",  # threat
            "crimin",  # criminal, criminals
            "crime",  # crime
            "espionage",  # espionage
            "hack",  # hack, hacking,
            "hacker",  # hacker, hackers
            "crack",  # cracking, crack
            "cracker",  # cracker, crackers
            "adversari",  # adversary, adversaries
            "terrorist",  # terrorist, terrorists
        }

        group_stem_postfix = {
            "group",  # group, groups
            "actor",  # actor, actors
            "unit",  # unit, untis
            "agent",  # agent, agents
            "organ",  # organization, organizations
        }

        false_positive_filter = [
            "top",
            "unknown",
            "cyber",
        ]  # "top threat groups", "cyber threat actors" etc...

        possible_ta_tag_types = {"NNP", "NNPS", "NN", "NNS"}
        possible_tag_types = {"NNP", "NNPS", "NN", "NNS", "JJ", "JJS"}
        chain_tags = {",", ":", "CC"}
        lookbefore_tags: Set[Text] = set()
        lookbefore_tags.update(chain_tags)
        lookbefore_tags.update(possible_tag_types)

        ps = nltk.stem.PorterStemmer()

        first_stage_found = False

        pos_actors: List[Text] = []
        # Look through all tokens. If any token relating to a threat actors is
        # found, look-before and collect all nouns while the tokens are nouns
        # or part of a listing.
        for i, (token, tag) in enumerate(nlpdata.pos_tag.tokens):
            if first_stage_found:
                second_stage_found = bool(
                    tag in possible_tag_types and ps.stem(token) in group_stem_postfix
                )
                if not second_stage_found:
                    first_stage_found = False
                    continue

                if nlpdata.pos_tag.tokens[i - 2][1] not in possible_tag_types:
                    first_stage_found = False
                    continue
                n = i - 1
                while (
                    n > 0
                    and len(nlpdata.pos_tag.tokens[n]) == 2
                    and nlpdata.pos_tag.tokens[n][1] in lookbefore_tags
                ):
                    n -= 1

                current_actor: List[Text] = []
                for (subtoken, pos_tag) in nlpdata.pos_tag.tokens[
                    n : i - 1  # noqa: E203
                ]:
                    # check if we have reached a separator (comma, 'and' etc)
                    # if so, we need to create a result of what we have found thus
                    # far and look for more.
                    if pos_tag in chain_tags:
                        if current_actor:
                            if valid_actor(current_actor):
                                pos_actors.append(" ".join(current_actor))
                            current_actor = []
                    elif pos_tag in possible_ta_tag_types:
                        if subtoken in false_positive_filter:
                            continue
                        current_actor.append(subtoken)
                if current_actor:
                    pos_actors.append(" ".join(current_actor))

            # check wether the current tag is of a type and in the accepted list of
            # threat group postfixes.
            first_stage_found = bool(
                tag in possible_tag_types and ps.stem(token) in threat_stem_postfix
            )

        res.actors = pos_actors
        return Result(name=self.name, version=self.version, result=res)


def valid_actor(actor: List[Text]) -> bool:
    """Check that the list of elements are actualy
    valid formatted"""

    if not actor:
        return False
    for e in actor:
        # Check that all elements start with an upper case letter
        if e and not e[0].isupper():
            return False
    return True
